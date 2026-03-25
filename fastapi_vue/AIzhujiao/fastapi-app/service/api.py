from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter()

# ========= 临时假数据 =========

# 用户数据
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

# 聊天记录
chat_records = [
    {
        "id": 1,
        "user_id": 1,
        "question": "什么是知识图谱？",
        "answer": "知识图谱是一种用图结构组织知识的方法。",
        "created_at": "2026-03-23 20:00:00"
    },
    {
        "id": 2,
        "user_id": 1,
        "question": "什么是大语言模型？",
        "answer": "大语言模型是基于海量文本训练得到的语言模型。",
        "created_at": "2026-03-23 20:05:00"
    },
    {
        "id": 3,
        "user_id": 2,
        "question": "什么是知识图谱？",
        "answer": "知识图谱是一种用图结构组织知识的方法。",
        "created_at": "2026-03-23 20:10:00"
    }
]

# 推荐问题
question_suggestions = [
    "什么是知识图谱？",
    "FastAPI 怎么入门？",
    "Vue 前后端如何联调？",
    "什么是 RAG？",
    "Neo4j 的基本概念有哪些？"
]

# 学习路径
learning_paths = {
    1: {
        "user_id": 1,
        "goal": "完成知识工程课程项目",
        "level": "初学者",
        "available_time_per_week": 10,
        "path": [
            "第一阶段：学习 FastAPI 基础",
            "第二阶段：理解前后端接口联调",
            "第三阶段：学习 MySQL 基本操作",
            "第四阶段：完成项目问答模块整合"
        ]
    }
}

# 学习进度
progress_data = {
    1: {
        "user_id": 1,
        "completed_tasks": 3,
        "total_tasks": 5,
        "study_hours": 12.0,
        "check_in_days": 4
    },
    2: {
        "user_id": 2,
        "completed_tasks": 1,
        "total_tasks": 4,
        "study_hours": 5.0,
        "check_in_days": 2
    }
}

# 打卡记录
check_in_records = {
    1: [
        {"date": "2026-03-21", "study_hours": 2.0},
        {"date": "2026-03-22", "study_hours": 1.5},
        {"date": "2026-03-23", "study_hours": 3.0},
        {"date": "2026-03-24", "study_hours": 2.5}
    ],
    2: [
        {"date": "2026-03-22", "study_hours": 2.0},
        {"date": "2026-03-23", "study_hours": 1.0}
    ]
}

# 任务完成情况
task_records = {
    1: [
        {"task_name": "学习 FastAPI 基础", "status": "completed"},
        {"task_name": "理解接口设计", "status": "completed"},
        {"task_name": "联调问答接口", "status": "completed"},
        {"task_name": "接入数据库", "status": "pending"},
        {"task_name": "完善学习进度模块", "status": "pending"}
    ]
}

# ========= 数据模型 =========

class AskRequest(BaseModel):
    user_id: int
    question: str

class AskResponse(BaseModel):
    answer: str
    record_id: int

class HistoryItem(BaseModel):
    id: int
    user_id: int
    question: str
    answer: str
    created_at: str

class HotQuestionItem(BaseModel):
    question: str
    count: int

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

class HomeworkHelpRequest(BaseModel):
    user_id: int
    question: str

class HomeworkHelpResponse(BaseModel):
    answer: str
    tips: List[str]

class LearningPathGenerateRequest(BaseModel):
    user_id: int
    goal: str
    level: str
    available_time_per_week: int

class LearningPathResponse(BaseModel):
    user_id: int
    goal: str
    path: List[str]

class ProgressResponse(BaseModel):
    user_id: int
    completed_tasks: int
    total_tasks: int
    study_hours: float
    check_in_days: int

class CheckInRequest(BaseModel):
    user_id: int
    date: str
    study_hours: float

class CheckInItem(BaseModel):
    date: str
    study_hours: float

class TaskUpdateRequest(BaseModel):
    user_id: int
    task_name: str
    status: str

class MessageResponse(BaseModel):
    message: str

# ========= 工具函数 =========

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

# ========= 根路由 =========

@router.get("/")
def root():
    return {"msg": "backend is running"}

# ========= 登录 / 注册相关接口 =========

@router.post("/api/register", response_model=RegisterResponse)
def register(req: RegisterRequest):
    existing_user = find_user_by_username(req.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")

    new_user_id = len(users) + 1
    new_user = {
        "user_id": new_user_id,
        "username": req.username,
        "password": req.password,
        "real_name": req.real_name,
        "major": req.major
    }
    users.append(new_user)

    progress_data[new_user_id] = {
        "user_id": new_user_id,
        "completed_tasks": 0,
        "total_tasks": 0,
        "study_hours": 0.0,
        "check_in_days": 0
    }
    check_in_records[new_user_id] = []
    task_records[new_user_id] = []

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

# ========= 智能问答相关接口 =========

@router.post("/api/ask", response_model=AskResponse)
def ask(req: AskRequest):
    user = find_user_by_id(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    answer = f"你问的是：{req.question}，这是一个示例回答。"

    new_id = len(chat_records) + 1
    new_record = {
        "id": new_id,
        "user_id": req.user_id,
        "question": req.question,
        "answer": answer,
        "created_at": "2026-03-23 21:00:00"
    }

    chat_records.append(new_record)

    return AskResponse(answer=answer, record_id=new_id)

@router.get("/api/history/{user_id}", response_model=List[HistoryItem])
def get_history(user_id: int):
    user = find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    result = [record for record in chat_records if record["user_id"] == user_id]
    result.reverse()
    return result

@router.delete("/api/history/{user_id}", response_model=MessageResponse)
def clear_history(user_id: int):
    user = find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    global chat_records
    chat_records = [record for record in chat_records if record["user_id"] != user_id]

    return MessageResponse(message="历史记录已清空")

@router.get("/api/hot-questions", response_model=List[HotQuestionItem])
def get_hot_questions():
    question_count = {}

    for record in chat_records:
        q = record["question"]
        if q in question_count:
            question_count[q] += 1
        else:
            question_count[q] = 1

    result = []
    for question, count in question_count.items():
        result.append({
            "question": question,
            "count": count
        })

    result.sort(key=lambda x: x["count"], reverse=True)

    return result[:5]

@router.get("/api/question-suggestions", response_model=List[str])
def get_question_suggestions():
    return question_suggestions

@router.post("/api/homework-help", response_model=HomeworkHelpResponse)
def homework_help(req: HomeworkHelpRequest):
    user = find_user_by_id(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    answer = f"针对你的问题“{req.question}”，建议先检查代码逻辑、变量定义和报错位置。"
    tips = [
        "先定位具体报错行",
        "检查变量名和函数名是否拼写正确",
        "确认输入输出类型是否匹配"
    ]

    return HomeworkHelpResponse(answer=answer, tips=tips)

# ========= 学习路径规划相关接口 =========

@router.post("/api/learning-path/generate", response_model=LearningPathResponse)
def generate_learning_path(req: LearningPathGenerateRequest):
    user = find_user_by_id(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    path = [
        f"第一阶段：明确目标 —— {req.goal}",
        f"第二阶段：根据当前水平（{req.level}）学习基础知识",
        "第三阶段：完成 2~3 个小练习巩固能力",
        f"第四阶段：每周投入 {req.available_time_per_week} 小时推进任务",
        "第五阶段：结合项目进行综合实践"
    ]

    learning_paths[req.user_id] = {
        "user_id": req.user_id,
        "goal": req.goal,
        "level": req.level,
        "available_time_per_week": req.available_time_per_week,
        "path": path
    }

    return LearningPathResponse(
        user_id=req.user_id,
        goal=req.goal,
        path=path
    )

@router.get("/api/learning-path/{user_id}", response_model=LearningPathResponse)
def get_learning_path(user_id: int):
    user = find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    path_info = learning_paths.get(user_id)
    if not path_info:
        raise HTTPException(status_code=404, detail="该用户暂无学习路径")

    return LearningPathResponse(
        user_id=path_info["user_id"],
        goal=path_info["goal"],
        path=path_info["path"]
    )

# ========= 学习进度相关接口 =========

@router.get("/api/progress/{user_id}", response_model=ProgressResponse)
def get_progress(user_id: int):
    user = find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    progress = progress_data.get(user_id)
    if not progress:
        raise HTTPException(status_code=404, detail="暂无学习进度数据")

    return ProgressResponse(
        user_id=progress["user_id"],
        completed_tasks=progress["completed_tasks"],
        total_tasks=progress["total_tasks"],
        study_hours=progress["study_hours"],
        check_in_days=progress["check_in_days"]
    )

@router.post("/api/progress/check-in", response_model=MessageResponse)
def add_check_in(req: CheckInRequest):
    user = find_user_by_id(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if req.user_id not in check_in_records:
        check_in_records[req.user_id] = []

    check_in_records[req.user_id].append({
        "date": req.date,
        "study_hours": req.study_hours
    })

    if req.user_id not in progress_data:
        progress_data[req.user_id] = {
            "user_id": req.user_id,
            "completed_tasks": 0,
            "total_tasks": 0,
            "study_hours": 0.0,
            "check_in_days": 0
        }

    progress_data[req.user_id]["study_hours"] += req.study_hours
    progress_data[req.user_id]["check_in_days"] = len(check_in_records[req.user_id])

    return MessageResponse(message="打卡成功")

@router.get("/api/progress/check-in/{user_id}", response_model=List[CheckInItem])
def get_check_in_records(user_id: int):
    user = find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return check_in_records.get(user_id, [])

@router.post("/api/progress/task-update", response_model=MessageResponse)
def update_task_status(req: TaskUpdateRequest):
    user = find_user_by_id(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if req.status not in ["pending", "completed"]:
        raise HTTPException(status_code=400, detail="status 只能是 pending 或 completed")

    if req.user_id not in task_records:
        task_records[req.user_id] = []

    found = False
    for task in task_records[req.user_id]:
        if task["task_name"] == req.task_name:
            task["status"] = req.status
            found = True
            break

    if not found:
        task_records[req.user_id].append({
            "task_name": req.task_name,
            "status": req.status
        })

    total_tasks = len(task_records[req.user_id])
    completed_tasks = len([t for t in task_records[req.user_id] if t["status"] == "completed"])

    if req.user_id not in progress_data:
        progress_data[req.user_id] = {
            "user_id": req.user_id,
            "completed_tasks": 0,
            "total_tasks": 0,
            "study_hours": 0.0,
            "check_in_days": 0
        }

    progress_data[req.user_id]["total_tasks"] = total_tasks
    progress_data[req.user_id]["completed_tasks"] = completed_tasks

    return MessageResponse(message="任务状态更新成功")