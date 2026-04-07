from __future__ import annotations

import datetime
import hashlib
import uuid
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy import select, func, delete, update
from sqlalchemy.orm import Session

from dependences.db import get_db
from repository.models import (
    User as DbUser,
    ChatRecord as DbChatRecord,
    HomeworkAssist as DbHomeworkAssist,
    LearningPath as DbLearningPath,
    PathTask as DbPathTask,
    TaskQuestion as DbTaskQuestion,
    LearningProgress as DbLearningProgress,
)
from service.langchain_service import get_langchain_chat_service


router = APIRouter()

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> DbUser:
    """
    从 Authorization: Bearer fake-token-<user_id> 提取 user_id。
    前端 axios 拦截器已在请求头自动带 token。
    """
    if not credentials or not credentials.scheme or not credentials.credentials:
        raise HTTPException(status_code=401, detail="缺少 Authorization")

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authorization 格式错误")

    token = credentials.credentials.strip()
    prefix = "fake-token-"
    if not token.startswith(prefix):
        raise HTTPException(status_code=401, detail="token 无效")

    raw = token[len(prefix) :]
    try:
        user_id = int(raw)
    except ValueError:
        raise HTTPException(status_code=401, detail="token 无效")

    user = db.get(DbUser, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在或 token 已失效")
    return user


# =========================
# 通用 / 健康检查
# =========================


@router.get("/")
def root() -> dict:
    return {"msg": "backend is running"}


@router.get("/health/db")
def health_db(db: Session = Depends(get_db)) -> dict:
    try:
        db.execute(select(1))
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库连接失败: {e}")


# =========================
# 用户：注册 / 登录 / 信息
# =========================


class RegisterRequest(BaseModel):
    real_name: str
    major: str
    username: str
    password: str


class RegisterResponse(BaseModel):
    message: str
    user_id: int


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    message: str
    user_id: int
    token: str


class UserInfoResponse(BaseModel):
    user_id: int
    username: str
    real_name: str = ""
    major: str = ""


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@router.post("/api/register", response_model=RegisterResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.execute(select(DbUser).where(DbUser.username == req.username)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="对应用户已存在")

    user = DbUser(
        username=req.username,
        password_hash=_sha256(req.password),
        major=req.major,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )
    # 迁移脚本会补 users.real_name；这里用 setattr 兼容旧库
    setattr(user, "real_name", req.real_name)

    db.add(user)
    db.commit()
    db.refresh(user)
    return RegisterResponse(message="注册成功", user_id=user.user_id)


@router.post("/api/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(select(DbUser).where(DbUser.username == req.username)).scalar_one_or_none()
    if not user or user.password_hash != _sha256(req.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    return LoginResponse(message="登录成功", user_id=user.user_id, token=f"fake-token-{user.user_id}")


@router.get("/api/users/{user_id}", response_model=UserInfoResponse)
def get_user_info(user_id: int, db: Session = Depends(get_db)):
    user = db.get(DbUser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserInfoResponse(
        user_id=user.user_id,
        username=user.username,
        real_name=getattr(user, "real_name", "") or "",
        major=user.major or "",
    )


# =========================
# 智能问答：会话 / 记录 / 热门 / 推荐
# chat_records.session_id 作为“会话 id”
# =========================


class ConversationItem(BaseModel):
    session_id: str
    user_id: int
    latest_question: str
    latest_asked_at: Optional[str] = None


class ConversationMessageItem(BaseModel):
    record_id: int
    session_id: str
    user_id: int
    question: str
    answer: str = ""
    knowledge_source: str = ""
    asked_at: Optional[str] = None


@router.get("/api/conversations/{user_id}", response_model=List[ConversationItem])
def list_conversations(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: DbUser = Depends(get_current_user),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="禁止访问其他用户数据")

    # 每个 session_id 取最新一条 record
    subq = (
        select(
            DbChatRecord.session_id.label("session_id"),
            func.max(DbChatRecord.record_id).label("max_id"),
        )
        .where(DbChatRecord.user_id == user_id)
        .group_by(DbChatRecord.session_id)
        .subquery()
    )

    rows = (
        db.execute(
            select(DbChatRecord)
            .join(subq, DbChatRecord.record_id == subq.c.max_id)
            .order_by(DbChatRecord.record_id.desc())
        )
        .scalars()
        .all()
    )

    return [
        ConversationItem(
            session_id=r.session_id or "",
            user_id=r.user_id,
            latest_question=r.question_content,
            latest_asked_at=r.asked_at.isoformat(sep=" ", timespec="seconds") if r.asked_at else None,
        )
        for r in rows
        if r.session_id
    ]


@router.get("/api/conversation/{session_id}", response_model=List[ConversationMessageItem])
def get_conversation_detail(session_id: str, db: Session = Depends(get_db)):
    rows = (
        db.execute(
            select(DbChatRecord)
            .where(DbChatRecord.session_id == session_id)
            .order_by(DbChatRecord.record_id.asc())
        )
        .scalars()
        .all()
    )
    if not rows:
        return []

    return [
        ConversationMessageItem(
            record_id=r.record_id,
            session_id=r.session_id or "",
            user_id=r.user_id,
            question=r.question_content,
            answer=r.answer_content or "",
            knowledge_source=r.knowledge_source or "",
            asked_at=r.asked_at.isoformat(sep=" ", timespec="seconds") if r.asked_at else None,
        )
        for r in rows
    ]


class AskRequest(BaseModel):
    user_id: Optional[int] = Field(
        default=None,
        description="可选：不传则从 Authorization token 推断当前用户；传了也必须与 token 一致",
        examples=[None],
    )
    question: str = Field(description="用户提问内容", examples=["什么是知识图谱？"])
    session_id: Optional[str] = Field(
        default=None,
        description="可选：会话 ID；不传则自动创建新会话，返回的 session_id 用于续聊",
        examples=[None],
    )


class AskResponse(BaseModel):
    answer: str
    record_id: int
    session_id: str


@router.post("/api/ask", response_model=AskResponse)
def ask(
    req: AskRequest,
    db: Session = Depends(get_db),
    current_user: DbUser = Depends(get_current_user),
):
    user_id = req.user_id or current_user.user_id
    if user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="禁止访问其他用户数据")

    session_id = req.session_id or uuid.uuid4().hex

    recent = (
        db.execute(
            select(DbChatRecord)
            .where(DbChatRecord.user_id == user_id, DbChatRecord.session_id == session_id)
            .order_by(DbChatRecord.record_id.desc())
            .limit(6)
        )
        .scalars()
        .all()
    )
    recent.reverse()
    history = [{"question": r.question_content, "answer": (r.answer_content or "")} for r in recent]

    answer_parts: list[str] = []
    try:
        for chunk in get_langchain_chat_service().chat_stream(question=req.question, history=history):
            if chunk:
                answer_parts.append(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模型调用失败: {e}")

    full_answer = "".join(answer_parts).strip()
    record = DbChatRecord(
        user_id=user_id,
        session_id=session_id,
        question_content=req.question,
        answer_content=full_answer,
        knowledge_source="langchain",
        asked_at=datetime.datetime.now(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return AskResponse(answer=full_answer, record_id=record.record_id, session_id=session_id)


@router.get("/api/history/{user_id}")
def get_history(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: DbUser = Depends(get_current_user),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="禁止访问其他用户数据")

    records = (
        db.execute(select(DbChatRecord).where(DbChatRecord.user_id == user_id).order_by(DbChatRecord.record_id.desc()).limit(200))
        .scalars()
        .all()
    )
    return [
        {
            "record_id": r.record_id,
            "session_id": r.session_id,
            "question": r.question_content,
            "answer": r.answer_content,
            "knowledge_source": r.knowledge_source,
            "asked_at": r.asked_at.isoformat(sep=" ", timespec="seconds") if r.asked_at else None,
        }
        for r in records
    ]


@router.delete("/api/history/{user_id}")
def clear_history(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: DbUser = Depends(get_current_user),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="禁止访问其他用户数据")

    db.execute(delete(DbChatRecord).where(DbChatRecord.user_id == user_id))
    db.commit()
    return {"message": "历史记录已清空"}


class HotQuestionItem(BaseModel):
    question: str
    count: int


@router.get("/api/hot-questions", response_model=List[HotQuestionItem])
def get_hot_questions(db: Session = Depends(get_db)):
    rows = (
        db.execute(
            select(DbChatRecord.question_content, func.count(DbChatRecord.record_id).label("cnt"))
            .where(DbChatRecord.question_content.is_not(None))
            .group_by(DbChatRecord.question_content)
            .order_by(func.count(DbChatRecord.record_id).desc())
            .limit(5)
        )
        .all()
    )
    return [HotQuestionItem(question=q, count=int(c)) for (q, c) in rows if q]


@router.get("/api/question-suggestions", response_model=List[str])
def get_question_suggestions():
    return [
        "什么是知识图谱？",
        "FastAPI 怎么入门？",
        "Vue 前后端如何联调？",
        "什么是 RAG？",
        "Neo4j 的基本概念有哪些？",
    ]


# =========================
# 作业辅导：记录到 homework_assists
# =========================


class HomeworkHelpRequest(BaseModel):
    user_id: Optional[int] = None
    content: str = ""
    submitted_content: str = ""
    image_url: str = ""


class HomeworkHelpResponse(BaseModel):
    assist_id: int
    answer: str
    hint: str


@router.post("/api/homework-help", response_model=HomeworkHelpResponse)
def homework_help(
    req: HomeworkHelpRequest,
    db: Session = Depends(get_db),
    current_user: DbUser = Depends(get_current_user),
):
    user_id = req.user_id or current_user.user_id
    if user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="禁止访问其他用户数据")

    prompt = req.content or req.submitted_content or "请帮助分析该作业问题。"
    answer_parts: list[str] = []
    try:
        for chunk in get_langchain_chat_service().chat_stream(question=prompt, history=[]):
            if chunk:
                answer_parts.append(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模型调用失败: {e}")

    full_answer = "".join(answer_parts).strip()
    hint = "请对照题目要求与关键边界条件逐步排查。"

    rec = DbHomeworkAssist(
        user_id=user_id,
        assist_content=req.content or None,
        submitted_content=req.submitted_content or (req.content or ""),
        error_message=None,
        correction_suggestion=full_answer or None,
        solving_hint=hint,
        submitted_at=datetime.datetime.now(),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    return HomeworkHelpResponse(assist_id=rec.assist_id, answer=full_answer, hint=hint)


@router.get("/api/homework-history/{user_id}")
def homework_history(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: DbUser = Depends(get_current_user),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="禁止访问其他用户数据")

    rows = (
        db.execute(select(DbHomeworkAssist).where(DbHomeworkAssist.user_id == user_id).order_by(DbHomeworkAssist.assist_id.desc()).limit(200))
        .scalars()
        .all()
    )
    return [
        {
            "assist_id": r.assist_id,
            "user_id": r.user_id,
            "assist_content": r.assist_content,
            "submitted_content": r.submitted_content,
            "correction_suggestion": r.correction_suggestion,
            "solving_hint": r.solving_hint,
            "submitted_at": r.submitted_at.isoformat(sep=" ", timespec="seconds") if r.submitted_at else None,
        }
        for r in rows
    ]


# =========================
# 路径规划：生成 / 历史 / 详情
# =========================


class LearningPathGenerateRequest(BaseModel):
    user_id: Optional[int] = None
    domain: str
    level: str
    days: int = Field(ge=1, le=365)
    goal: str


class LearningPathResponse(BaseModel):
    path_id: int
    user_id: int
    goal: str = ""
    domain: str = ""
    level: str = ""
    days: int = 0
    status: str = ""
    created_at: Optional[str] = None


class PathTaskItem(BaseModel):
    task_id: int
    task_name: str
    description: str = ""
    order_no: int = 0
    is_completed: bool = False


class LearningPathDetailResponse(BaseModel):
    path: LearningPathResponse
    tasks: List[PathTaskItem]


@router.post("/api/learning-path/generate", response_model=LearningPathDetailResponse)
def generate_learning_path(
    req: LearningPathGenerateRequest,
    db: Session = Depends(get_db),
    current_user: DbUser = Depends(get_current_user),
):
    user_id = req.user_id or current_user.user_id
    if user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="禁止访问其他用户数据")

    # 先创建路径记录
    path = DbLearningPath(
        user_id=user_id,
        estimated_days=req.days,
        status="第一阶段",
        current_task_point=None,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )
    setattr(path, "goal", req.goal)
    setattr(path, "level", req.level)
    setattr(path, "domain", req.domain)

    db.add(path)
    db.commit()
    db.refresh(path)

    # 这里先用“最小可用模板”生成 tasks/questions，保证数据库链路打通。
    # 后续你们模型组固定输出格式后，再把这里替换为严格解析模型输出并写入。
    tasks_seed = [
        ("第一阶段：基础入门", "建立基础概念与环境，完成入门练习"),
        ("第二阶段：核心技能", "围绕目标系统学习核心技能并完成小项目"),
        ("第三阶段：综合实战", "综合项目演练与查漏补缺，准备验收"),
    ]

    created_tasks: list[DbPathTask] = []
    for idx, (name, desc) in enumerate(tasks_seed, start=1):
        t = DbPathTask(
            path_id=path.path_id,
            task_name=name,
            task_description=desc,
            task_order=idx,
            is_completed=0,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )
        db.add(t)
        created_tasks.append(t)

    db.commit()
    for t in created_tasks:
        db.refresh(t)

    # 每个 task 配 1 道题，写入 task_questions
    for t in created_tasks:
        q = DbTaskQuestion(
            task_id=t.task_id,
            question_text=f"请简要总结“{t.task_name}”你学到的关键点。",
            correct_answer="(开放题)",
            is_passed=0,
            user_answer="",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )
        db.add(q)
    db.commit()

    resp_path = LearningPathResponse(
        path_id=path.path_id,
        user_id=path.user_id,
        goal=getattr(path, "goal", "") or "",
        domain=getattr(path, "domain", "") or "",
        level=getattr(path, "level", "") or "",
        days=path.estimated_days or 0,
        status=path.status or "",
        created_at=path.created_at.isoformat(sep=" ", timespec="seconds") if path.created_at else None,
    )

    tasks = (
        db.execute(select(DbPathTask).where(DbPathTask.path_id == path.path_id).order_by(DbPathTask.task_order.asc(), DbPathTask.task_id.asc()))
        .scalars()
        .all()
    )
    resp_tasks = [
        PathTaskItem(
            task_id=t.task_id,
            task_name=t.task_name,
            description=t.task_description or "",
            order_no=t.task_order or 0,
            is_completed=bool(t.is_completed),
        )
        for t in tasks
    ]

    return LearningPathDetailResponse(path=resp_path, tasks=resp_tasks)


@router.get("/api/learning-path/{user_id}", response_model=List[LearningPathResponse])
def list_learning_paths(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: DbUser = Depends(get_current_user),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="禁止访问其他用户数据")

    rows = (
        db.execute(select(DbLearningPath).where(DbLearningPath.user_id == user_id).order_by(DbLearningPath.path_id.desc()).limit(200))
        .scalars()
        .all()
    )
    return [
        LearningPathResponse(
            path_id=p.path_id,
            user_id=p.user_id,
            goal=getattr(p, "goal", "") or "",
            domain=getattr(p, "domain", "") or "",
            level=getattr(p, "level", "") or "",
            days=p.estimated_days or 0,
            status=p.status or "",
            created_at=p.created_at.isoformat(sep=" ", timespec="seconds") if p.created_at else None,
        )
        for p in rows
    ]


@router.get("/api/learning-path/detail/{path_id}", response_model=LearningPathDetailResponse)
def get_learning_path_detail(path_id: int, db: Session = Depends(get_db)):
    path = db.get(DbLearningPath, path_id)
    if not path:
        raise HTTPException(status_code=404, detail="路径不存在")

    tasks = (
        db.execute(select(DbPathTask).where(DbPathTask.path_id == path_id).order_by(DbPathTask.task_order.asc(), DbPathTask.task_id.asc()))
        .scalars()
        .all()
    )

    resp_path = LearningPathResponse(
        path_id=path.path_id,
        user_id=path.user_id,
        goal=getattr(path, "goal", "") or "",
        domain=getattr(path, "domain", "") or "",
        level=getattr(path, "level", "") or "",
        days=path.estimated_days or 0,
        status=path.status or "",
        created_at=path.created_at.isoformat(sep=" ", timespec="seconds") if path.created_at else None,
    )
    resp_tasks = [
        PathTaskItem(
            task_id=t.task_id,
            task_name=t.task_name,
            description=t.task_description or "",
            order_no=t.task_order or 0,
            is_completed=bool(t.is_completed),
        )
        for t in tasks
    ]
    return LearningPathDetailResponse(path=resp_path, tasks=resp_tasks)


# =========================
# 学习进度：题目列表 / 作答判题 / 打卡统计
# =========================


@router.get("/api/tasks/{task_id}/questions")
def get_task_questions(task_id: int, db: Session = Depends(get_db)):
    task = db.get(DbPathTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    qs = (
        db.execute(select(DbTaskQuestion).where(DbTaskQuestion.task_id == task_id).order_by(DbTaskQuestion.question_id.asc()))
        .scalars()
        .all()
    )
    return [
        {
            "question_id": q.question_id,
            "task_id": q.task_id,
            "question_text": q.question_text,
            "is_passed": bool(q.is_passed),
            "user_answer": q.user_answer or "",
        }
        for q in qs
    ]


class SubmitAnswerRequest(BaseModel):
    user_id: Optional[int] = None
    question_id: int
    user_answer: str


@router.post("/api/tasks/answer")
def submit_answer(
    req: SubmitAnswerRequest,
    db: Session = Depends(get_db),
    current_user: DbUser = Depends(get_current_user),
):
    user_id = req.user_id or current_user.user_id
    if user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="禁止访问其他用户数据")

    q = db.get(DbTaskQuestion, req.question_id)
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")

    q.user_answer = req.user_answer
    # 开放题：correct_answer 为 "(开放题)" 时默认通过；否则严格比对
    correct = (q.correct_answer or "").strip()
    if correct == "(开放题)":
        is_correct = True
    else:
        is_correct = req.user_answer.strip() == correct
    q.is_passed = 1 if is_correct else 0
    q.updated_at = datetime.datetime.now()
    db.commit()

    # 如果该 task 下全部通过，则标记 task 完成
    task_id = q.task_id
    total = db.execute(select(func.count(DbTaskQuestion.question_id)).where(DbTaskQuestion.task_id == task_id)).scalar_one()
    passed = db.execute(
        select(func.count(DbTaskQuestion.question_id)).where(DbTaskQuestion.task_id == task_id, DbTaskQuestion.is_passed == 1)
    ).scalar_one()
    if int(total) > 0 and int(total) == int(passed):
        db.execute(update(DbPathTask).where(DbPathTask.task_id == task_id).values(is_completed=1, updated_at=datetime.datetime.now()))
        db.commit()

    return {"message": "提交成功", "is_correct": bool(is_correct)}


class CheckInRequest(BaseModel):
    user_id: Optional[int] = None
    date: str  # YYYY-MM-DD
    study_hours: int = Field(ge=0, le=24)


@router.post("/api/progress/check-in")
def progress_check_in(
    req: CheckInRequest,
    db: Session = Depends(get_db),
    current_user: DbUser = Depends(get_current_user),
):
    user_id = req.user_id or current_user.user_id
    if user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="禁止访问其他用户数据")
    try:
        dt = datetime.datetime.fromisoformat(req.date)
    except ValueError:
        raise HTTPException(status_code=400, detail="date 格式应为 YYYY-MM-DD")

    rec = DbLearningProgress(
        user_id=user_id,
        path_id=None,
        task_type="check_in",
        related_task_id=None,
        study_minutes=int(req.study_hours) * 60,
        record_time=dt,
        progress_note="check-in",
    )
    db.add(rec)
    db.commit()
    return {"message": "打卡成功"}


@router.get("/api/progress/{user_id}")
def get_progress_summary(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: DbUser = Depends(get_current_user),
):
    if user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="禁止访问其他用户数据")

    total_minutes = db.execute(
        select(func.coalesce(func.sum(DbLearningProgress.study_minutes), 0)).where(DbLearningProgress.user_id == user_id)
    ).scalar_one()

    distinct_days = db.execute(
        select(func.count(func.distinct(func.date(DbLearningProgress.record_time)))).where(
            DbLearningProgress.user_id == user_id, DbLearningProgress.record_time.is_not(None)
        )
    ).scalar_one()

    # 任务完成统计：按 path_tasks
    total_tasks = db.execute(
        select(func.count(DbPathTask.task_id)).join(DbLearningPath, DbPathTask.path_id == DbLearningPath.path_id).where(DbLearningPath.user_id == user_id)
    ).scalar_one()
    completed_tasks = db.execute(
        select(func.count(DbPathTask.task_id))
        .join(DbLearningPath, DbPathTask.path_id == DbLearningPath.path_id)
        .where(DbLearningPath.user_id == user_id, DbPathTask.is_completed == 1)
    ).scalar_one()

    return {
        "completed_tasks": int(completed_tasks),
        "total_tasks": int(total_tasks),
        "study_hours": int(total_minutes) // 60,
        "check_in_days": int(distinct_days),
    }

