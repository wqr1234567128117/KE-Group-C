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
from service.langchain_chat_service import get_langchain_chat_service
from service.learning_path_service import get_learning_path_service

router = APIRouter()

bearer_scheme = HTTPBearer(auto_error=False)

def _normalize_question_row(question: dict, fallback_task_name: str) -> tuple[str, str]:
    """
    将题目对象转换为当前 DbTaskQuestion 可直接写入的字段：
        (question_text, correct_answer)

    兼容常见题目结构，例如：
    {
        "question_text": "...",
        "correct_answer": "A"
    }

    或：
    {
        "question_content": "...",
        "options": ["A. xxx", "B. xxx"],
        "answer": "A"
    }
    """
    if not isinstance(question, dict):
        return (f"请完成“{fallback_task_name}”相关练习。", "(待判定)")

    question_text = (
        question.get("question_text")
        or question.get("question_content")
        or question.get("content")
        or question.get("title")
        or f"请完成“{fallback_task_name}”相关练习。"
    )

    # 如果有选项，把选项拼到题干后面，适配你当前只有一个 question_text 字段的表结构
    options = question.get("options")
    if isinstance(options, list) and options:
        option_lines = [str(opt) for opt in options if str(opt).strip()]
        if option_lines:
            question_text = f"{question_text}\n" + "\n".join(option_lines)

    correct_answer = (
        question.get("correct_answer")
        or question.get("answer")
        or question.get("reference_answer")
        or "(待判定)"
    )

    return str(question_text), str(correct_answer)

def _build_progress_response_items(progresses, tasks) -> list[LearningProgressItem]:
    task_map: dict[int, list] = {}

    for task in tasks:
        if task.progress_id is None:
            continue
        task_map.setdefault(task.progress_id, []).append(task)

    resp_progresses: list[LearningProgressItem] = []

    for progress in progresses:
        current_tasks = task_map.get(progress.progress_id, [])
        current_tasks.sort(key=lambda x: ((x.task_order or 0), x.task_id))

        resp_progresses.append(
            LearningProgressItem(
                progress_id=progress.progress_id,
                progress_order=progress.progress_order or 0,
                progress_name=progress.progress_name or "",
                progress_description=progress.progress_description or "",
                tasks=[
                    PathTaskItem(
                        task_id=t.task_id,
                        task_name=t.task_name,
                        description=t.task_description or "",
                        order_no=idx,
                        is_completed=bool(t.is_completed),
                    )
                    for idx, t in enumerate(current_tasks, start=1)
                ],
            )
        )

    return resp_progresses

def _flatten_generated_progresses(generated_result: dict) -> list[dict]:
    stages = generated_result.get("stages", [])
    if not isinstance(stages, list):
        return []

    results: list[dict] = []

    for idx, stage in enumerate(stages, start=1):
        if not isinstance(stage, dict):
            continue

        progress_order = stage.get("stage_order", idx)
        progress_name = (
            stage.get("stage_title")
            or stage.get("title")
            or f"阶段{idx}"
        )

        # 你这张表里 progress_description 是 VARCHAR(255)
        # 所以建议优先放阶段目标，不够再放阶段说明，并截断
        progress_description = (
            stage.get("stage_objective")
            or stage.get("objective")
            or stage.get("stage_description")
            or stage.get("description")
            or ""
        ).strip()[:255]

        results.append(
            {
                "progress_order": int(progress_order),
                "progress_name": progress_name,
                "progress_description": progress_description,
            }
        )

    return results

def _flatten_generated_tasks(generated_result: dict) -> list[dict]:
    stages = generated_result.get("stages", [])
    if not isinstance(stages, list):
        return []

    flat_tasks: list[dict] = []
    global_order = 1

    for s_idx, stage in enumerate(stages, start=1):
        if not isinstance(stage, dict):
            continue

        progress_order = int(stage.get("stage_order", s_idx))
        raw_tasks = stage.get("tasks", [])
        if not isinstance(raw_tasks, list):
            raw_tasks = []

        for t_idx, task in enumerate(raw_tasks, start=1):
            if not isinstance(task, dict):
                continue

            task_title = (
                task.get("task_title")
                or task.get("title")
                or f"任务{t_idx}"
            )

            task_description = (
                task.get("task_description")
                or task.get("description")
                or ""
            )

            questions = task.get("questions", [])
            if not isinstance(questions, list):
                questions = []

            flat_tasks.append(
                {
                    "progress_order": progress_order,   # 关键：后面映射 progress_id
                    "task_order": global_order,         # 数据库里继续存全局顺序，兼容旧逻辑
                    "stage_task_order": t_idx,          # 前端展示时可用阶段内顺序
                    "task_name": task_title,            # 不再拼“阶段名 - 任务名”
                    "task_description": task_description,
                    "questions": questions,
                }
            )
            global_order += 1

    return flat_tasks

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
    session_title: Optional[str] = Field(
        default=None,
        description="自定义会话标题；为空则前端可用 latest_question 作为展示名",
    )
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
            session_title=(t.strip() if (t := getattr(r, "session_title", None) or "") else None),
            latest_asked_at=r.asked_at.isoformat(sep=" ", timespec="seconds") if r.asked_at else None,
        )
        for r in rows
        if r.session_id
    ]


class RenameConversationRequest(BaseModel):
    title: str = Field(
        "",
        max_length=255,
        description="新标题；全空白则清除自定义标题（列表仍用最新一问展示）",
    )


@router.patch("/api/conversation/{session_id}")
def rename_conversation(
    session_id: str,
    req: RenameConversationRequest,
    db: Session = Depends(get_db),
    current_user: DbUser = Depends(get_current_user),
):
    stripped = (req.title or "").strip()
    new_title: str | None = stripped if stripped else None

    n = db.execute(
        select(func.count(DbChatRecord.record_id)).where(
            DbChatRecord.session_id == session_id,
            DbChatRecord.user_id == current_user.user_id,
        )
    ).scalar_one()
    if int(n or 0) == 0:
        raise HTTPException(status_code=404, detail="会话不存在或无权访问")

    db.execute(
        update(DbChatRecord)
        .where(
            DbChatRecord.session_id == session_id,
            DbChatRecord.user_id == current_user.user_id,
        )
        .values(session_title=new_title)
    )
    db.commit()
    return {"message": "已更新", "session_id": session_id, "session_title": new_title}


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

    prev_title_raw = db.execute(
        select(DbChatRecord.session_title)
        .where(DbChatRecord.user_id == user_id, DbChatRecord.session_id == session_id)
        .order_by(DbChatRecord.record_id.desc())
        .limit(1)
    ).scalar_one_or_none()
    inherited_session_title: str | None = None
    if isinstance(prev_title_raw, str) and prev_title_raw.strip():
        inherited_session_title = prev_title_raw.strip()

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
        session_title=inherited_session_title,
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
class LearningProgressItem(BaseModel):
    progress_id: int
    progress_order: int
    progress_name: str
    progress_description: str = ""
    tasks: list[PathTaskItem]

class LearningPathGenerateRequest(BaseModel):
    user_id: Optional[int] = None
    domain: str
    level: str
    goal: str
    background_plan: str


class LearningPathResponse(BaseModel):
    path_id: int
    user_id: int
    goal: str = ""
    domain: str = ""
    level: str = ""
    background_plan: str
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
    progresses: list[LearningProgressItem]
    tasks: list[PathTaskItem]


@router.post("/api/learning-path/generate", response_model=LearningPathDetailResponse)
def generate_learning_path(
    req: LearningPathGenerateRequest,
    db: Session = Depends(get_db),
    current_user: DbUser = Depends(get_current_user),
):
    # 测试阶段先固定用户；前端接好鉴权后再改回 Depends(get_current_user)
    user_id = req.user_id or current_user.user_id
    if user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="禁止访问其他用户数据")

    try:
        learning_path_service = get_learning_path_service()

        generated_result = learning_path_service.generate_learning_path(
            field=req.domain,
            goal=req.goal,
            level=req.level,
            background_plan=req.background_plan,
            user_id=user_id,
        )

        flat_progresses = _flatten_generated_progresses(generated_result)
        flat_tasks = _flatten_generated_tasks(generated_result)

        now = datetime.datetime.now()

        first_stage_title = ""
        stages = generated_result.get("stages", [])
        if isinstance(stages, list) and stages:
            first_stage = stages[0] if isinstance(stages[0], dict) else {}
            first_stage_title = (
                first_stage.get("stage_title")
                or first_stage.get("title")
                or ""
            )

        # 1. 创建 learning_paths
        path = DbLearningPath(
            user_id=user_id,
            goal=req.goal,
            domain=req.domain,
            level=req.level,
            background_plan=req.background_plan,
            status=first_stage_title,
            current_task_point=flat_tasks[0]["task_name"] if flat_tasks else None,
            created_at=now,
            updated_at=now,
        )
        db.add(path)
        db.flush()

        # 2. 创建 learning_progress
        created_progresses: list[DbLearningProgress] = []
        progress_order_to_id: dict[int, int] = {}

        for item in flat_progresses:
            progress = DbLearningProgress(
                user_id=user_id,
                path_id=path.path_id,
                progress_name=item["progress_name"],
                progress_description=item.get("progress_description", ""),
                progress_order=item.get("progress_order", 0),
                created_at=now,
            )
            db.add(progress)
            created_progresses.append(progress)

        db.flush()

        for progress in created_progresses:
            progress_order_to_id[progress.progress_order] = progress.progress_id

        # 3. 创建 path_tasks，并写 progress_id
        created_tasks: list[DbPathTask] = []

        for item in flat_tasks:
            progress_id = progress_order_to_id.get(item["progress_order"])
            if not progress_id:
                raise ValueError(f"未找到 progress_order={item['progress_order']} 对应的阶段记录")

            task = DbPathTask(
                path_id=path.path_id,
                progress_id=progress_id,
                task_name=item["task_name"],
                task_description=item.get("task_description", ""),
                task_order=item.get("task_order", 0),
                is_completed=0,
                created_at=now,
                updated_at=now,
            )
            db.add(task)
            created_tasks.append(task)

        db.flush()

        # 4. 创建 task_questions
        for db_task, task_payload in zip(created_tasks, flat_tasks):
            questions = task_payload.get("questions", [])
            if not isinstance(questions, list):
                questions = []

            if not questions:
                q = DbTaskQuestion(
                    task_id=db_task.task_id,
                    question_text="",
                    correct_answer="",
                    is_passed=0,
                    user_answer="",
                    created_at=now,
                    updated_at=now,
                )
                db.add(q)
                continue

            for question in questions:
                question_text, correct_answer = _normalize_question_row(
                    question=question,
                    fallback_task_name=db_task.task_name,
                )
                q = DbTaskQuestion(
                    task_id=db_task.task_id,
                    question_text=question_text,
                    correct_answer=correct_answer,
                    is_passed=0,
                    user_answer="",
                    created_at=now,
                    updated_at=now,
                )
                db.add(q)

        db.commit()
        db.refresh(path)

        # 5. 查回阶段和任务，按阶段树返回
        progresses = (
            db.execute(
                select(DbLearningProgress)
                .where(DbLearningProgress.path_id == path.path_id)
                .order_by(DbLearningProgress.progress_order.asc(), DbLearningProgress.progress_id.asc())
            )
            .scalars()
            .all()
        )

        tasks = (
            db.execute(
                select(DbPathTask)
                .where(DbPathTask.path_id == path.path_id)
                .order_by(DbPathTask.task_order.asc(), DbPathTask.task_id.asc())
            )
            .scalars()
            .all()
        )

        resp_path = LearningPathResponse(
            path_id=path.path_id,
            user_id=path.user_id,
            goal=path.goal or "",
            domain=path.domain or "",
            level=path.level or "",
            background_plan=path.background_plan or "",
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

        resp_progresses = _build_progress_response_items(
            progresses=progresses,
            tasks=tasks,
        )


        return LearningPathDetailResponse(
            path=resp_path,
            progresses=resp_progresses,
            tasks=resp_tasks,
        )

    except FileNotFoundError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Prompt 文件不存在: {str(e)}")
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"学习路径生成失败: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"学习路径生成异常: {str(e)}")


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
            background_plan=getattr(p, "background_plan", "") or "",
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

    progresses = (
        db.execute(
            select(DbLearningProgress)
            .where(DbLearningProgress.path_id == path_id)
            .order_by(DbLearningProgress.progress_order.asc(), DbLearningProgress.progress_id.asc())
        )
        .scalars()
        .all()
    )

    tasks = (
        db.execute(
            select(DbPathTask)
            .where(DbPathTask.path_id == path_id)
            .order_by(DbPathTask.task_order.asc(), DbPathTask.task_id.asc())
        )
        .scalars()
        .all()
    )

    resp_path = LearningPathResponse(
        path_id=path.path_id,
        user_id=path.user_id,
        goal=path.goal or "",
        domain=path.domain or "",
        level=path.level or "",
        background_plan=path.background_plan or "",
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

    resp_progresses = _build_progress_response_items(
        progresses=progresses,
        tasks=tasks,
    )

    return LearningPathDetailResponse(
        path=resp_path,
        progresses=resp_progresses,
        tasks=resp_tasks,
    )


@router.delete("/api/learning-path/{path_id}")
def delete_learning_path(
    path_id: int,
    db: Session = Depends(get_db),
    current_user: DbUser = Depends(get_current_user),
):
    """
    删除一条学习路径及其子数据：题目 → 任务 → 阶段(learning_progress) → 路径。
    仅删除 path_id 匹配的 learning_progress，不影响 path_id 为 NULL 的打卡等记录。
    """
    path = db.get(DbLearningPath, path_id)
    if not path:
        raise HTTPException(status_code=404, detail="路径不存在")
    if path.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="禁止删除其他用户的路径")

    task_ids = list(
        db.execute(select(DbPathTask.task_id).where(DbPathTask.path_id == path_id)).scalars().all()
    )
    if task_ids:
        db.execute(delete(DbTaskQuestion).where(DbTaskQuestion.task_id.in_(task_ids)))
    db.execute(delete(DbPathTask).where(DbPathTask.path_id == path_id))
    db.execute(delete(DbLearningProgress).where(DbLearningProgress.path_id == path_id))
    db.execute(delete(DbLearningPath).where(DbLearningPath.path_id == path_id))
    db.commit()
    return {"message": "学习路径已删除", "path_id": path_id}


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

