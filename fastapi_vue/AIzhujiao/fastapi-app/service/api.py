from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

# =========================
# 假数据区
# =========================

users = [
    {
        "user_id": 1,
        "username": "wqr",
        "password": "123456",
        "real_name": "翁启然",
        "major": "计算机科学与技术"
    },
    {
        "user_id": 2,
        "username": "test",
        "password": "123456",
        "real_name": "测试用户",
        "major": "软件工程"
    }
]

question_suggestions = [
    "什么是知识图谱？",
    "FastAPI 怎么入门？",
    "Vue 前后端如何联调？",
    "什么是 RAG？",
    "Neo4j 的基本概念有哪些？"
]

# 会话列表
conversations = [
    {
        "conversation_id": 1,
        "user_id": 1,
        "title": "知识图谱学习",
        "latest_question": "什么是知识图谱？",
        "created_at": "2026-03-29 10:00:00"
    }
]

# 会话中的消息记录（每条是一轮问答）
conversation_messages = [
    {
        "message_id": 1,
        "conversation_id": 1,
        "user_id": 1,
        "question": "什么是知识图谱？",
        "answer": "知识图谱是一种用图结构组织知识的方法。",
        "source": "知识图谱基础知识",
        "created_at": "2026-03-29 10:01:00"
    }
]

# 作业辅导记录
homework_assists = [
    {
        "assist_id": 1,
        "user_id": 1,
        "content": "这段 Python 代码为什么报错？",
        "submitted_code": "print(x)",
        "image_url": "",
        "error_info": "NameError: name 'x' is not defined",
        "suggestion": "变量 x 未定义，请先赋值后再使用。",
        "hint": "检查变量是否已声明或拼写是否正确。",
        "created_at": "2026-03-29 10:10:00"
    }
]

# 学习路径
learning_paths = [
    {
        "path_id": 1,
        "user_id": 1,
        "goal": "完成知识工程课程项目",
        "level": "初学者",
        "days": 7,
        "status": "第一阶段",
        "created_at": "2026-03-29 10:20:00"
    }
]

# 路径任务（一个路径下多个任务点）
path_tasks = [
    {
        "task_id": 1,
        "path_id": 1,
        "stage": "第一阶段",
        "task_name": "学习 FastAPI 基础",
        "description": "理解路由、请求与响应",
        "order_no": 1,
        "is_completed": True
    },
    {
        "task_id": 2,
        "path_id": 1,
        "stage": "第二阶段",
        "task_name": "理解前后端联调",
        "description": "学会前端调用后端接口",
        "order_no": 2,
        "is_completed": False
    }
]

# 题目数据
task_questions = [
    {
        "question_id": 1,
        "task_id": 1,
        "question_text": "FastAPI 中用于定义 GET 接口的装饰器是什么？",
        "answer": "@app.get",
        "is_passed": True,
        "user_answer": "@app.get"
    },
    {
        "question_id": 2,
        "task_id": 2,
        "question_text": "当前端调用后端接口时，常见的跨域问题需要在后端配置什么中间件？",
        "answer": "CORSMiddleware",
        "is_passed": False,
        "user_answer": ""
    }
]

# 学习进度记录
learning_progress = [
    {
        "progress_id": 1,
        "user_id": 1,
        "path_id": 1,
        "task_id": 1,
        "record_time": "2026-03-29 10:30:00"
    }
]

# =========================
# 工具函数
# =========================

def find_user_by_id(user_id: int):
    for user in users:
        if user["user_id"] == user_id:
            return user
    return None

def find_user_by_username(username: str):
    for user in users:
        if user["username"] == username:
            return user
    return None

def find_conversation_by_id(conversation_id: int):
    for c in conversations:
        if c["conversation_id"] == conversation_id:
            return c
    return None

def find_message_by_id(message_id: int):
    for m in conversation_messages:
        if m["message_id"] == message_id:
            return m
    return None

def find_homework_by_id(assist_id: int):
    for h in homework_assists:
        if h["assist_id"] == assist_id:
            return h
    return None

def find_path_by_id(path_id: int):
    for p in learning_paths:
        if p["path_id"] == path_id:
            return p
    return None

def find_task_by_id(task_id: int):
    for t in path_tasks:
        if t["task_id"] == task_id:
            return t
    return None

def find_question_by_id(question_id: int):
    for q in task_questions:
        if q["question_id"] == question_id:
            return q
    return None

def get_tasks_by_path_id(path_id: int):
    result = [t for t in path_tasks if t["path_id"] == path_id]
    result.sort(key=lambda x: x["order_no"])
    return result

def get_questions_by_task_id(task_id: int):
    return [q for q in task_questions if q["task_id"] == task_id]

def refresh_path_status(path_id: int):
    path = find_path_by_id(path_id)
    if not path:
        return

    tasks = get_tasks_by_path_id(path_id)
    current_task = None
    for t in tasks:
        if not t["is_completed"]:
            current_task = t
            break

    if current_task:
        path["status"] = current_task["stage"]
    elif tasks:
        path["status"] = "已完成"
    else:
        path["status"] = "未开始"

# =========================
# 数据模型
# =========================

class MessageResponse(BaseModel):
    message: str

# 用户
class RegisterRequest(BaseModel):
    username: str
    password: str
    real_name: str
    major: str

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
    real_name: str
    major: str

class UpdateUserRequest(BaseModel):
    real_name: str
    major: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

# 会话
class CreateConversationRequest(BaseModel):
    user_id: int
    title: str

class CreateConversationResponse(BaseModel):
    message: str
    conversation_id: int

class RenameConversationRequest(BaseModel):
    title: str

class ConversationItem(BaseModel):
    conversation_id: int
    user_id: int
    title: str
    latest_question: str
    created_at: str

class ConversationMessageItem(BaseModel):
    message_id: int
    conversation_id: int
    user_id: int
    question: str
    answer: str
    source: str
    created_at: str

# 问答
class AskRequest(BaseModel):
    user_id: int
    conversation_id: int
    question: str

class AskResponse(BaseModel):
    answer: str
    message_id: int

class HotQuestionItem(BaseModel):
    question: str
    count: int

# 作业辅导
class HomeworkHelpRequest(BaseModel):
    user_id: int
    content: str
    submitted_code: Optional[str] = ""
    image_url: Optional[str] = ""

class HomeworkHelpResponse(BaseModel):
    assist_id: int
    answer: str
    hint: str

class HomeworkRetryResponse(BaseModel):
    assist_id: int
    answer: str
    hint: str

class HomeworkHistoryItem(BaseModel):
    assist_id: int
    user_id: int
    content: str
    submitted_code: str
    image_url: str
    error_info: str
    suggestion: str
    hint: str
    created_at: str

# 路径规划
class LearningPathGenerateRequest(BaseModel):
    user_id: int
    goal: str
    level: str
    days: int

class LearningPathResponse(BaseModel):
    path_id: int
    user_id: int
    goal: str
    level: str
    days: int
    status: str
    created_at: str

class PathTaskItem(BaseModel):
    task_id: int
    path_id: int
    stage: str
    task_name: str
    description: str
    order_no: int
    is_completed: bool

class LearningPathDetailResponse(BaseModel):
    path_id: int
    user_id: int
    goal: str
    level: str
    days: int
    status: str
    created_at: str
    tasks: List[PathTaskItem]

class UpdateLearningPathStatusRequest(BaseModel):
    status: str

# 任务与题目
class TaskDetailResponse(BaseModel):
    task_id: int
    path_id: int
    stage: str
    task_name: str
    description: str
    order_no: int
    is_completed: bool

class TaskQuestionItem(BaseModel):
    question_id: int
    task_id: int
    question_text: str
    is_passed: bool
    user_answer: str

class QuestionDetailResponse(BaseModel):
    question_id: int
    task_id: int
    question_text: str
    answer: str
    is_passed: bool
    user_answer: str

class SubmitAnswerRequest(BaseModel):
    user_id: int
    question_id: int
    user_answer: str

class SubmitAnswerResponse(BaseModel):
    message: str
    is_correct: bool

class RetryAnswerRequest(BaseModel):
    user_id: int
    user_answer: str

class TaskAnswerStatusResponse(BaseModel):
    task_id: int
    total_questions: int
    passed_questions: int
    is_task_completed: bool

class QuestionSummaryResponse(BaseModel):
    path_id: int
    total_questions: int
    answered_questions: int
    passed_questions: int
    failed_questions: int

# 学习进度
class ProgressPathItem(BaseModel):
    path_id: int
    goal: str
    status: str

class ProgressSummaryResponse(BaseModel):
    user_id: int
    total_paths: int
    total_tasks: int
    completed_tasks: int
    total_questions: int
    passed_questions: int
    latest_record_time: str

class ProgressHistoryItem(BaseModel):
    progress_id: int
    user_id: int
    path_id: int
    task_id: int
    record_time: str

class CurrentTaskResponse(BaseModel):
    path_id: int
    current_task_id: int
    current_task_name: str
    stage: str

# 首页
class HomeOverviewResponse(BaseModel):
    user_id: int
    real_name: str
    conversation_count: int
    learning_path_count: int
    homework_assist_count: int
    current_learning_status: str

# =========================
# 根接口
# =========================

@router.get("/")
def root():
    return {"msg": "backend is running"}

# =========================
# 用户模块
# =========================

@router.post("/api/register", response_model=RegisterResponse)
def register(req: RegisterRequest):
    existing_user = find_user_by_username(req.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="对应用户已存在")

    new_user_id = len(users) + 1
    users.append({
        "user_id": new_user_id,
        "username": req.username,
        "password": req.password,
        "real_name": req.real_name,
        "major": req.major
    })

    return RegisterResponse(message="注册成功", user_id=new_user_id)

@router.post("/api/login", response_model=LoginResponse)
def login(req: LoginRequest):
    user = find_user_by_username(req.username)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    return LoginResponse(
        message="登录成功",
        user_id=user["user_id"],
        token=f"fake-token-{user['user_id']}"
    )

@router.get("/api/users/{user_id}", response_model=UserInfoResponse)
def get_user_info(user_id: int):
    user = find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return UserInfoResponse(
        user_id=user["user_id"],
        username=user["username"],
        real_name=user["real_name"],
        major=user["major"]
    )

@router.put("/api/users/{user_id}", response_model=UserInfoResponse)
def update_user_info(user_id: int, req: UpdateUserRequest):
    user = find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user["real_name"] = req.real_name
    user["major"] = req.major

    return UserInfoResponse(
        user_id=user["user_id"],
        username=user["username"],
        real_name=user["real_name"],
        major=user["major"]
    )

@router.put("/api/users/{user_id}/password", response_model=MessageResponse)
def change_password(user_id: int, req: ChangePasswordRequest):
    user = find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user["password"] != req.old_password:
        raise HTTPException(status_code=400, detail="旧密码错误")

    user["password"] = req.new_password
    return MessageResponse(message="密码修改成功")

@router.post("/api/logout", response_model=MessageResponse)
def logout():
    return MessageResponse(message="退出登录成功")

# =========================
# 会话模块
# =========================

@router.post("/api/conversations", response_model=CreateConversationResponse)
def create_conversation(req: CreateConversationRequest):
    user = find_user_by_id(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    new_conversation_id = len(conversations) + 1
    conversations.append({
        "conversation_id": new_conversation_id,
        "user_id": req.user_id,
        "title": req.title,
        "latest_question": "",
        "created_at": "2026-03-29 11:00:00"
    })

    return CreateConversationResponse(
        message="会话创建成功",
        conversation_id=new_conversation_id
    )

@router.get("/api/conversations/{user_id}", response_model=List[ConversationItem])
def get_conversations(user_id: int):
    user = find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    result = [c for c in conversations if c["user_id"] == user_id]
    result.reverse()
    return result

@router.get("/api/conversation/{conversation_id}", response_model=List[ConversationMessageItem])
def get_conversation_detail(conversation_id: int):
    conversation = find_conversation_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")

    result = [m for m in conversation_messages if m["conversation_id"] == conversation_id]
    return result

@router.put("/api/conversations/{conversation_id}", response_model=MessageResponse)
def rename_conversation(conversation_id: int, req: RenameConversationRequest):
    conversation = find_conversation_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")

    conversation["title"] = req.title
    return MessageResponse(message="会话标题更新成功")

@router.delete("/api/conversations/{conversation_id}", response_model=MessageResponse)
def delete_conversation(conversation_id: int):
    conversation = find_conversation_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")

    global conversations, conversation_messages
    conversations = [c for c in conversations if c["conversation_id"] != conversation_id]
    conversation_messages = [m for m in conversation_messages if m["conversation_id"] != conversation_id]

    return MessageResponse(message="会话删除成功")

@router.delete("/api/conversations/user/{user_id}", response_model=MessageResponse)
def clear_user_conversations(user_id: int):
    user = find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    global conversations, conversation_messages
    user_conversation_ids = [c["conversation_id"] for c in conversations if c["user_id"] == user_id]
    conversations = [c for c in conversations if c["user_id"] != user_id]
    conversation_messages = [
        m for m in conversation_messages if m["conversation_id"] not in user_conversation_ids
    ]

    return MessageResponse(message="用户所有会话已清空")

# =========================
# 智能问答模块
# =========================

@router.post("/api/ask", response_model=AskResponse)
def ask(req: AskRequest):
    user = find_user_by_id(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    conversation = find_conversation_by_id(req.conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")

    answer = f"你问的是：{req.question}。这是当前演示版返回的示例回答。"

    new_message_id = len(conversation_messages) + 1
    conversation_messages.append({
        "message_id": new_message_id,
        "conversation_id": req.conversation_id,
        "user_id": req.user_id,
        "question": req.question,
        "answer": answer,
        "source": "演示版假数据来源",
        "created_at": "2026-03-29 11:05:00"
    })

    conversation["latest_question"] = req.question

    return AskResponse(answer=answer, message_id=new_message_id)

@router.get("/api/hot-questions", response_model=List[HotQuestionItem])
def get_hot_questions():
    question_count = {}
    for record in conversation_messages:
        q = record["question"]
        question_count[q] = question_count.get(q, 0) + 1

    result = [{"question": q, "count": c} for q, c in question_count.items()]
    result.sort(key=lambda x: x["count"], reverse=True)
    return result[:5]

@router.get("/api/question-suggestions", response_model=List[str])
def get_question_suggestions():
    return question_suggestions

@router.get("/api/chat-record/{message_id}", response_model=ConversationMessageItem)
def get_chat_record_detail(message_id: int):
    message = find_message_by_id(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="问答记录不存在")
    return message

# =========================
# 作业辅导模块
# =========================

@router.post("/api/homework-help", response_model=HomeworkHelpResponse)
def homework_help(req: HomeworkHelpRequest):
    user = find_user_by_id(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    error_info = "检测到可能存在变量未定义或逻辑错误"
    suggestion = "建议先检查报错行附近的变量定义、函数调用和输入输出类型。"
    hint = "优先查看报错提示中的行号与关键报错信息。"

    new_assist_id = len(homework_assists) + 1
    homework_assists.append({
        "assist_id": new_assist_id,
        "user_id": req.user_id,
        "content": req.content,
        "submitted_code": req.submitted_code or "",
        "image_url": req.image_url or "",
        "error_info": error_info,
        "suggestion": suggestion,
        "hint": hint,
        "created_at": "2026-03-29 11:10:00"
    })

    return HomeworkHelpResponse(
        assist_id=new_assist_id,
        answer=suggestion,
        hint=hint
    )

@router.get("/api/homework-history/{user_id}", response_model=List[HomeworkHistoryItem])
def get_homework_history(user_id: int):
    user = find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    result = [h for h in homework_assists if h["user_id"] == user_id]
    result.reverse()
    return result

@router.get("/api/homework-help/{assist_id}", response_model=HomeworkHistoryItem)
def get_homework_detail(assist_id: int):
    assist = find_homework_by_id(assist_id)
    if not assist:
        raise HTTPException(status_code=404, detail="作业辅导记录不存在")
    return assist

@router.delete("/api/homework-help/{assist_id}", response_model=MessageResponse)
def delete_homework_record(assist_id: int):
    assist = find_homework_by_id(assist_id)
    if not assist:
        raise HTTPException(status_code=404, detail="作业辅导记录不存在")

    global homework_assists
    homework_assists = [h for h in homework_assists if h["assist_id"] != assist_id]
    return MessageResponse(message="作业辅导记录删除成功")

@router.delete("/api/homework-history/{user_id}", response_model=MessageResponse)
def clear_homework_history(user_id: int):
    user = find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    global homework_assists
    homework_assists = [h for h in homework_assists if h["user_id"] != user_id]
    return MessageResponse(message="用户作业辅导历史已清空")

@router.post("/api/homework-help/{assist_id}/retry", response_model=HomeworkRetryResponse)
def retry_homework_help(assist_id: int):
    assist = find_homework_by_id(assist_id)
    if not assist:
        raise HTTPException(status_code=404, detail="作业辅导记录不存在")

    assist["suggestion"] = "重新分析后，建议重点检查变量作用域、输入参数以及边界条件。"
    assist["hint"] = "可先从最小可复现示例开始排查。"

    return HomeworkRetryResponse(
        assist_id=assist["assist_id"],
        answer=assist["suggestion"],
        hint=assist["hint"]
    )

# =========================
# 路径规划模块
# =========================

@router.post("/api/learning-path/generate", response_model=LearningPathResponse)
def generate_learning_path(req: LearningPathGenerateRequest):
    user = find_user_by_id(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    new_path_id = len(learning_paths) + 1
    new_path = {
        "path_id": new_path_id,
        "user_id": req.user_id,
        "goal": req.goal,
        "level": req.level,
        "days": req.days,
        "status": "第一阶段",
        "created_at": "2026-03-29 11:20:00"
    }
    learning_paths.append(new_path)

    new_task_id_1 = len(path_tasks) + 1
    new_tasks = [
        {
            "task_id": new_task_id_1,
            "path_id": new_path_id,
            "stage": "第一阶段",
            "task_name": "学习基础概念",
            "description": f"围绕目标“{req.goal}”学习核心基础知识",
            "order_no": 1,
            "is_completed": False
        },
        {
            "task_id": new_task_id_1 + 1,
            "path_id": new_path_id,
            "stage": "第二阶段",
            "task_name": "完成小练习",
            "description": "结合知识点完成练习题与小任务",
            "order_no": 2,
            "is_completed": False
        }
    ]

    for task in new_tasks:
        path_tasks.append(task)

    new_question_id = len(task_questions) + 1
    task_questions.append({
        "question_id": new_question_id,
        "task_id": new_tasks[0]["task_id"],
        "question_text": "请简要说明该学习主题中的一个核心概念。",
        "answer": "核心概念示例答案",
        "is_passed": False,
        "user_answer": ""
    })

    task_questions.append({
        "question_id": new_question_id + 1,
        "task_id": new_tasks[1]["task_id"],
        "question_text": "请完成一个与本阶段任务对应的小练习。",
        "answer": "练习题示例答案",
        "is_passed": False,
        "user_answer": ""
    })

    return LearningPathResponse(**new_path)

@router.get("/api/learning-path/{user_id}", response_model=List[LearningPathResponse])
def get_learning_paths(user_id: int):
    user = find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    result = [p for p in learning_paths if p["user_id"] == user_id]
    result.reverse()
    return result

@router.get("/api/learning-path/detail/{path_id}", response_model=LearningPathDetailResponse)
def get_learning_path_detail(path_id: int):
    path = find_path_by_id(path_id)
    if not path:
        raise HTTPException(status_code=404, detail="路径不存在")

    tasks = get_tasks_by_path_id(path_id)
    return LearningPathDetailResponse(
        path_id=path["path_id"],
        user_id=path["user_id"],
        goal=path["goal"],
        level=path["level"],
        days=path["days"],
        status=path["status"],
        created_at=path["created_at"],
        tasks=tasks
    )

@router.get("/api/learning-path/tasks/{path_id}", response_model=List[PathTaskItem])
def get_path_tasks_api(path_id: int):
    path = find_path_by_id(path_id)
    if not path:
        raise HTTPException(status_code=404, detail="路径不存在")

    return get_tasks_by_path_id(path_id)

@router.put("/api/learning-path/{path_id}/status", response_model=MessageResponse)
def update_learning_path_status(path_id: int, req: UpdateLearningPathStatusRequest):
    path = find_path_by_id(path_id)
    if not path:
        raise HTTPException(status_code=404, detail="路径不存在")

    path["status"] = req.status
    return MessageResponse(message="路径状态更新成功")

@router.delete("/api/learning-path/{path_id}", response_model=MessageResponse)
def delete_learning_path(path_id: int):
    path = find_path_by_id(path_id)
    if not path:
        raise HTTPException(status_code=404, detail="路径不存在")

    global learning_paths, path_tasks, task_questions, learning_progress
    task_ids = [t["task_id"] for t in path_tasks if t["path_id"] == path_id]

    learning_paths = [p for p in learning_paths if p["path_id"] != path_id]
    path_tasks = [t for t in path_tasks if t["path_id"] != path_id]
    task_questions = [q for q in task_questions if q["task_id"] not in task_ids]
    learning_progress = [p for p in learning_progress if p["path_id"] != path_id]

    return MessageResponse(message="学习路径删除成功")

@router.post("/api/learning-path/{path_id}/copy", response_model=LearningPathResponse)
def copy_learning_path(path_id: int):
    path = find_path_by_id(path_id)
    if not path:
        raise HTTPException(status_code=404, detail="路径不存在")

    new_path_id = len(learning_paths) + 1
    copied_path = {
        "path_id": new_path_id,
        "user_id": path["user_id"],
        "goal": path["goal"],
        "level": path["level"],
        "days": path["days"],
        "status": path["status"],
        "created_at": "2026-03-29 12:00:00"
    }
    learning_paths.append(copied_path)

    old_tasks = get_tasks_by_path_id(path_id)
    old_to_new_task_map = {}

    for old_task in old_tasks:
        new_task_id = len(path_tasks) + 1
        new_task = {
            "task_id": new_task_id,
            "path_id": new_path_id,
            "stage": old_task["stage"],
            "task_name": old_task["task_name"],
            "description": old_task["description"],
            "order_no": old_task["order_no"],
            "is_completed": False
        }
        path_tasks.append(new_task)
        old_to_new_task_map[old_task["task_id"]] = new_task_id

    for old_task in old_tasks:
        related_questions = get_questions_by_task_id(old_task["task_id"])
        for q in related_questions:
            task_questions.append({
                "question_id": len(task_questions) + 1,
                "task_id": old_to_new_task_map[old_task["task_id"]],
                "question_text": q["question_text"],
                "answer": q["answer"],
                "is_passed": False,
                "user_answer": ""
            })

    return LearningPathResponse(**copied_path)

# =========================
# 任务与题目模块
# =========================

@router.get("/api/path-task/{task_id}", response_model=TaskDetailResponse)
def get_task_detail(task_id: int):
    task = find_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task

@router.put("/api/path-task/{task_id}/complete", response_model=MessageResponse)
def mark_task_complete(task_id: int):
    task = find_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    task["is_completed"] = True
    refresh_path_status(task["path_id"])
    return MessageResponse(message="任务已标记为完成")

@router.get("/api/tasks/{task_id}/questions", response_model=List[TaskQuestionItem])
def get_task_questions_api(task_id: int):
    task = find_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return get_questions_by_task_id(task_id)

@router.get("/api/questions/{question_id}", response_model=QuestionDetailResponse)
def get_question_detail(question_id: int):
    question = find_question_by_id(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    return question

@router.post("/api/tasks/answer", response_model=SubmitAnswerResponse)
def submit_answer(req: SubmitAnswerRequest):
    user = find_user_by_id(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    question = find_question_by_id(req.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")

    question["user_answer"] = req.user_answer
    is_correct = req.user_answer.strip() == question["answer"].strip()
    question["is_passed"] = is_correct

    task = find_task_by_id(question["task_id"])
    if task and is_correct:
        task["is_completed"] = True

        learning_progress.append({
            "progress_id": len(learning_progress) + 1,
            "user_id": req.user_id,
            "path_id": task["path_id"],
            "task_id": task["task_id"],
            "record_time": "2026-03-29 11:30:00"
        })

        refresh_path_status(task["path_id"])

    return SubmitAnswerResponse(
        message="提交成功" if is_correct else "提交完成，但答案不正确",
        is_correct=is_correct
    )

@router.post("/api/questions/{question_id}/retry", response_model=SubmitAnswerResponse)
def retry_answer(question_id: int, req: RetryAnswerRequest):
    user = find_user_by_id(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    question = find_question_by_id(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")

    question["user_answer"] = req.user_answer
    is_correct = req.user_answer.strip() == question["answer"].strip()
    question["is_passed"] = is_correct

    task = find_task_by_id(question["task_id"])
    if task and is_correct:
        task["is_completed"] = True
        learning_progress.append({
            "progress_id": len(learning_progress) + 1,
            "user_id": req.user_id,
            "path_id": task["path_id"],
            "task_id": task["task_id"],
            "record_time": "2026-03-29 11:40:00"
        })
        refresh_path_status(task["path_id"])

    return SubmitAnswerResponse(
        message="重新作答成功" if is_correct else "重新作答完成，但答案不正确",
        is_correct=is_correct
    )

@router.get("/api/tasks/{task_id}/answer-status", response_model=TaskAnswerStatusResponse)
def get_task_answer_status(task_id: int):
    task = find_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    questions = get_questions_by_task_id(task_id)
    total_questions = len(questions)
    passed_questions = len([q for q in questions if q["is_passed"]])

    return TaskAnswerStatusResponse(
        task_id=task_id,
        total_questions=total_questions,
        passed_questions=passed_questions,
        is_task_completed=task["is_completed"]
    )

@router.get("/api/learning-path/{path_id}/question-summary", response_model=QuestionSummaryResponse)
def get_question_summary(path_id: int):
    path = find_path_by_id(path_id)
    if not path:
        raise HTTPException(status_code=404, detail="路径不存在")

    tasks = get_tasks_by_path_id(path_id)
    task_ids = [t["task_id"] for t in tasks]
    related_questions = [q for q in task_questions if q["task_id"] in task_ids]

    total_questions = len(related_questions)
    answered_questions = len([q for q in related_questions if q["user_answer"].strip() != ""])
    passed_questions = len([q for q in related_questions if q["is_passed"]])
    failed_questions = answered_questions - passed_questions

    return QuestionSummaryResponse(
        path_id=path_id,
        total_questions=total_questions,
        answered_questions=answered_questions,
        passed_questions=passed_questions,
        failed_questions=failed_questions
    )

# =========================
# 学习进度模块
# =========================

@router.get("/api/progress/paths/{user_id}", response_model=List[ProgressPathItem])
def get_progress_paths(user_id: int):
    user = find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    result = []
    for p in learning_paths:
        if p["user_id"] == user_id:
            result.append({
                "path_id": p["path_id"],
                "goal": p["goal"],
                "status": p["status"]
            })
    return result

@router.get("/api/progress/path/{path_id}", response_model=List[PathTaskItem])
def get_progress_path_detail(path_id: int):
    path = find_path_by_id(path_id)
    if not path:
        raise HTTPException(status_code=404, detail="路径不存在")

    return get_tasks_by_path_id(path_id)

@router.get("/api/progress/summary/{user_id}", response_model=ProgressSummaryResponse)
def get_progress_summary(user_id: int):
    user = find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user_paths = [p for p in learning_paths if p["user_id"] == user_id]
    path_ids = [p["path_id"] for p in user_paths]
    user_tasks = [t for t in path_tasks if t["path_id"] in path_ids]
    task_ids = [t["task_id"] for t in user_tasks]
    user_questions = [q for q in task_questions if q["task_id"] in task_ids]
    user_progress = [p for p in learning_progress if p["user_id"] == user_id]

    latest_record_time = ""
    if user_progress:
        latest_record_time = user_progress[-1]["record_time"]

    return ProgressSummaryResponse(
        user_id=user_id,
        total_paths=len(user_paths),
        total_tasks=len(user_tasks),
        completed_tasks=len([t for t in user_tasks if t["is_completed"]]),
        total_questions=len(user_questions),
        passed_questions=len([q for q in user_questions if q["is_passed"]]),
        latest_record_time=latest_record_time
    )

@router.get("/api/progress/history/{user_id}", response_model=List[ProgressHistoryItem])
def get_progress_history(user_id: int):
    user = find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    result = [p for p in learning_progress if p["user_id"] == user_id]
    result.reverse()
    return result

@router.get("/api/progress/current-task/{path_id}", response_model=CurrentTaskResponse)
def get_current_task(path_id: int):
    path = find_path_by_id(path_id)
    if not path:
        raise HTTPException(status_code=404, detail="路径不存在")

    tasks = get_tasks_by_path_id(path_id)
    for task in tasks:
        if not task["is_completed"]:
            return CurrentTaskResponse(
                path_id=path_id,
                current_task_id=task["task_id"],
                current_task_name=task["task_name"],
                stage=task["stage"]
            )

    if tasks:
        last_task = tasks[-1]
        return CurrentTaskResponse(
            path_id=path_id,
            current_task_id=last_task["task_id"],
            current_task_name=last_task["task_name"],
            stage="已完成"
        )

    raise HTTPException(status_code=404, detail="当前路径下无任务")

@router.post("/api/progress/reset/{path_id}", response_model=MessageResponse)
def reset_progress(path_id: int):
    path = find_path_by_id(path_id)
    if not path:
        raise HTTPException(status_code=404, detail="路径不存在")

    related_tasks = get_tasks_by_path_id(path_id)
    task_ids = [t["task_id"] for t in related_tasks]

    for task in related_tasks:
        task["is_completed"] = False

    for question in task_questions:
        if question["task_id"] in task_ids:
            question["is_passed"] = False
            question["user_answer"] = ""

    global learning_progress
    learning_progress = [p for p in learning_progress if p["path_id"] != path_id]
    path["status"] = "第一阶段"

    return MessageResponse(message="学习进度已重置")

# =========================
# 首页模块
# =========================

@router.get("/api/home/overview/{user_id}", response_model=HomeOverviewResponse)
def get_home_overview(user_id: int):
    user = find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user_conversations = [c for c in conversations if c["user_id"] == user_id]
    user_paths = [p for p in learning_paths if p["user_id"] == user_id]
    user_homework = [h for h in homework_assists if h["user_id"] == user_id]

    current_learning_status = "暂无路径"
    if user_paths:
        current_learning_status = user_paths[-1]["status"]

    return HomeOverviewResponse(
        user_id=user_id,
        real_name=user["real_name"],
        conversation_count=len(user_conversations),
        learning_path_count=len(user_paths),
        homework_assist_count=len(user_homework),
        current_learning_status=current_learning_status
    )