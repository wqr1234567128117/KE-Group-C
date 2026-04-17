from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationChain
from langchain.prompts.prompt import PromptTemplate
import time
import warnings
import mysql.connector
from neo4j import GraphDatabase
from service.learning_path_service import get_learning_path_service
from repository.models import (
    User as DbUser,
    LearningPath as DbLearningPath,
    PathTask as DbPathTask,
    TaskQuestion as DbTaskQuestion,
    LearningProgress as DbLearningProgress,
)
from sqlalchemy.orm import Session
import datetime
from typing import List, Dict, Any

warnings.filterwarnings("ignore")

# ===================== 配置区 =====================
API_KEY = ""  # 你自己填
MODEL = ""
BASE_URL = ""
TYPE_SPEED = 0.03

MYSQL_HOST = "39.107.241.146"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PWD = "USTB@SH2026"
DB_NAME = "groub_c"

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PWD = "JMj!piFd2!mQGtW"
# ====================================================

class QuestionService:
    def __init__(self) -> None:
        self.llm = ChatOpenAI(
            api_key=API_KEY,
            model=MODEL,
            base_url=BASE_URL,
            temperature=0.7,
            max_tokens=2048
        )

    def generate_questions_for_path(self, req, db: Session, current_user: DbUser) -> dict:
        """
        完整实现生成学习路径、补题、写入数据库、返回增强 JSON 的流程。
        结合 api.py:777-931 的逻辑。
        """
        user_id = req.user_id or current_user.user_id
        if user_id != current_user.user_id:
            raise ValueError("禁止访问其他用户数据")

        try:
            learning_path_service = get_learning_path_service()

            # 1. 生成纯路径 JSON
            generated_result = learning_path_service.generate_learning_path(
                field=req.domain,
                goal=req.goal,
                level=req.level,
                background_plan=req.background_plan,
                user_id=user_id,
            )

            # 2. 提取路径上下文
            field = req.domain
            goal = req.goal
            level = req.level
            background_plan = req.background_plan
            summary = generated_result.get("summary", "")

            # 3. 为每个任务补题
            enriched_result = self._enrich_path_with_questions(
                generated_result, field, goal, level, background_plan, summary
            )

            if not isinstance(enriched_result, dict):
                raise ValueError("题目服务返回结果不是 JSON 对象。")

            flat_progresses = self._flatten_generated_progresses(enriched_result)
            flat_tasks = self._flatten_generated_tasks(enriched_result)

            if not flat_progresses:
                raise ValueError("未生成任何学习阶段。")
            if not flat_tasks:
                raise ValueError("未生成任何任务点。")

            now = datetime.datetime.now()

            first_stage_title = ""
            stages = enriched_result.get("stages", [])
            if isinstance(stages, list) and stages:
                first_stage = stages[0] if isinstance(stages[0], dict) else {}
                first_stage_title = (
                    first_stage.get("stage_title")
                    or first_stage.get("title")
                    or ""
                )

            # 4. 创建 learning_paths
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

            # 5. 创建 learning_progress
            created_progresses: List[DbLearningProgress] = []
            progress_order_to_id: Dict[int, int] = {}

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

            # 6. 创建 path_tasks
            created_tasks: List[DbPathTask] = []

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

            # 7. 创建 task_questions
            for db_task, task_payload in zip(created_tasks, flat_tasks):
                questions = task_payload.get("questions", [])
                if not isinstance(questions, list) or not questions:
                    continue

                for question in questions:
                    question_text, correct_answer = self._normalize_question_row(
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

            # 8. 返回增强 JSON
            enriched_result["path_id"] = path.path_id
            enriched_result["status"] = path.status or first_stage_title
            enriched_result["current_task_point"] = path.current_task_point
            enriched_result["created_at"] = (
                path.created_at.isoformat(sep=" ", timespec="seconds")
                if path.created_at
                else None
            )

            return enriched_result

        except Exception as e:
            db.rollback()
            raise e

    def _enrich_path_with_questions(self, path_json: dict, field: str, goal: str, level: str, background_plan: str, summary: str) -> dict:
        """
        为路径中的每个任务补题。
        """
        stages = path_json.get("stages", [])
        for stage in stages:
            if not isinstance(stage, dict):
                continue
            tasks = stage.get("tasks", [])
            for task in tasks:
                if not isinstance(task, dict):
                    continue
                knowledge_point_names = task.get("knowledge_point_names", [])
                if not knowledge_point_names:
                    continue

                # 从 Neo4j 查询匹配的 KnowledgePoint
                matched_knowledge = self._query_matched_knowledge(knowledge_point_names)

                # 生成题目
                questions = self._generate_questions_for_task(
                    matched_knowledge, field, goal, level, background_plan, summary, task.get("task_name", "")
                )

                # 嵌入题目
                task["questions"] = questions

        return path_json

    def _query_matched_knowledge(self, knowledge_point_names: list) -> list:
        """
        从 Neo4j 查询与 knowledge_point_names 匹配的 KnowledgePoint。
        """
        try:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PWD))
            matched = []

            with driver.session() as session:
                for name in knowledge_point_names:
                    result = session.run("""
                        MATCH (kp:KnowledgePoint {name: $name})
                        RETURN kp.name AS name
                    """, name=name)
                    for record in result:
                        matched.append(record.get("name"))

            driver.close()
            return matched

        except Exception as e:
            print("❌ Neo4j 查询错误：", e)
            return []

    def _generate_questions_for_task(self, knowledge_list: list, field: str, goal: str, level: str, background_plan: str, summary: str, task_name: str) -> list:
        """
        为单个任务生成题目，返回列表。
        """
        if not knowledge_list:
            return []

        prompt = f"""
你是《{field}》课程老师，根据以下上下文为任务“{task_name}”生成3道检验学习成果的题目。
上下文：
- 领域：{field}
- 目标：{goal}
- 级别：{level}
- 背景计划：{background_plan}
- 路径总结：{summary}
- 相关知识点：{knowledge_list}

要求：
1. 2道简答题 + 1道单选题
2. 单选题格式：题干|选项A|选项B|选项C|选项D
3. 每题一行
4. 只输出题目，不要多余内容

输出3道题：
"""
        response = self.llm.invoke(prompt).content
        lines = [line.strip() for line in response.splitlines() if line.strip()]
        questions = []
        for line in lines[:3]:
            if "|" in line:
                # 单选题
                parts = line.split("|", 1)
                questions.append({
                    "question_text": parts[0],
                    "options": parts[1].split("|") if len(parts) > 1 else [],
                    "correct_answer": ""  # 假设未提供答案
                })
            else:
                # 简答题
                questions.append({
                    "question_text": line,
                    "correct_answer": ""
                })
        return questions

    def _flatten_generated_progresses(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        stages = data.get("stages", [])
        if not isinstance(stages, list):
            return []

        flat_progresses: List[Dict[str, Any]] = []
        for idx, stage in enumerate(stages, start=1):
            if not isinstance(stage, dict):
                continue

            flat_progresses.append(
                {
                    "progress_order": self._coerce_int(stage.get("stage_order"), idx),
                    "progress_name": stage.get("stage_title") or stage.get("title") or f"阶段{idx}",
                    "progress_description": (
                        stage.get("stage_description")
                        or stage.get("description")
                        or stage.get("stage_objective")
                        or ""
                    ),
                }
            )

        return flat_progresses

    def _flatten_generated_tasks(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        stages = data.get("stages", [])
        if not isinstance(stages, list):
            return []

        flat_tasks: List[Dict[str, Any]] = []

        for s_idx, stage in enumerate(stages, start=1):
            if not isinstance(stage, dict):
                continue

            progress_order = self._coerce_int(stage.get("stage_order"), s_idx)
            tasks = stage.get("tasks", [])
            if not isinstance(tasks, list):
                continue

            for t_idx, task in enumerate(tasks, start=1):
                if not isinstance(task, dict):
                    continue

                questions = task.get("questions", [])
                if not isinstance(questions, list):
                    questions = []

                flat_tasks.append(
                    {
                        "progress_order": progress_order,
                        "task_order": self._coerce_int(task.get("task_order"), t_idx),
                        "task_name": task.get("task_title") or task.get("title") or f"任务{t_idx}",
                        "task_description": task.get("task_description") or task.get("description") or "",
                        "questions": questions,
                        "task_meta": task.get("task_meta", {}),
                    }
                )

        return flat_tasks

    def _normalize_question_row(self, question: dict, fallback_task_name: str) -> tuple[str, str]:
        if not isinstance(question, dict):
            return (f"请完成“{fallback_task_name}”相关练习。", "(待判定)")

        question_text = (
            question.get("question_text")
            or question.get("question_content")
            or question.get("content")
            or question.get("title")
            or f"请完成“{fallback_task_name}”相关练习。"
        )

        options = question.get("options", [])
        if isinstance(options, list) and options:
            option_lines = []
            for option in options:
                if option is None:
                    continue
                option_lines.append(str(option).strip())
            if option_lines:
                question_text = f"{question_text}\n" + "\n".join(option_lines)

        correct_answer = (
            question.get("correct_answer")
            or question.get("answer")
            or question.get("standard_answer")
            or "(待判定)"
        )

        return str(question_text).strip(), str(correct_answer).strip()

    def _coerce_int(self, value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

# ====================================================

def get_question_service():
    return QuestionService()

# ===================== 界面 =====================
def stream_print(text, delay=TYPE_SPEED):
    print("\n🎓 老师：", end="")
    for c in text:
        print(c, end="", flush=True)
        time.sleep(delay)
    print("\n")

def show_menu():
    print("\n" + "="*60)
    print("🎓 知识工程课程智能辅导机器人".center(60))
    print("="*60)
    print("  /menu    菜单")
    print("  /test    生成课程试题")
    print("  /exit    退出")
    print("="*60)

def run_test():
    service = get_question_service()
    stream_print("正在从本地知识图谱获取知识点...")

    knowledges = service.get_full_knowledge_path()
    if not knowledges:
        stream_print("未获取到知识点，请检查Neo4j数据。")
        return

    stream_print("正在生成《知识工程》题目...")
    questions = service.generate_questions(knowledges)
    stream_print(f"生成完成：\n{questions}")

    stream_print("正在保存到数据库...")
    if service.save_to_mysql(questions):
        stream_print("✅ 试题已成功保存！")
    else:
        stream_print("❌ 保存失败")

# ===================== 主程序 =====================
show_menu()

llm = ChatOpenAI(api_key=API_KEY, model=MODEL, base_url=BASE_URL, temperature=0.7)
template = """你是《知识工程》课程辅导老师。
对话历史：{history}
学生：{input}
老师："""
prompt = PromptTemplate(input_variables=["history", "input"], template=template)
memory = ConversationBufferWindowMemory(k=5)
chat_chain = ConversationChain(llm=llm, memory=memory, prompt=prompt, verbose=False)

while True:
    ipt = input("\n💬 你：")
    if not ipt:
        continue

    if ipt.startswith("/"):
        cmd = ipt.lower()
        if cmd == "/menu":
            show_menu()
        elif cmd == "/test":
            run_test()
        elif cmd == "/exit":
            print("👋 再见！")
            break
        continue

    try:
        res = chat_chain.predict(input=ipt)
        stream_print(res)
    except:
        stream_print("服务异常，请重试。")