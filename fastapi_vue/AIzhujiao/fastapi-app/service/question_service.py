import importlib
import warnings
from functools import lru_cache
from typing import Any

from langchain_openai import ChatOpenAI
from neo4j import GraphDatabase

warnings.filterwarnings("ignore")


@lru_cache(maxsize=1)
def _load_settings() -> Any:
    """
    统一复用项目中的配置读取方式，避免在 service 内写死静态变量。
    优先尝试和 langchain_chat_service.py / learning_path_service.py 一致的配置入口。
    """
    candidate_modules = [
        "langchain_app.config",
        "config",
    ]

    last_error = None
    for module_name in candidate_modules:
        try:
            module = importlib.import_module(module_name)
            get_settings = getattr(module, "get_settings", None)
            if callable(get_settings):
                return get_settings()
        except Exception as exc:
            last_error = exc

    raise RuntimeError(
        "无法导入 get_settings()。请确认 question_service.py 与 "
        "langchain_chat_service.py / learning_path_service.py 使用的是同一个 config.py。"
    ) from last_error


def _pick_setting(settings: Any, *names: str, default: Any = None, required: bool = False) -> Any:
    """
    兼容不同 service 中可能存在的字段命名差异。
    例如：NEO4J_USER / NEO4J_USERNAME，API_KEY / ARK_API_KEY。
    """
    for name in names:
        if hasattr(settings, name):
            value = getattr(settings, name)
            if value is not None and value != "":
                return value

    if required:
        raise RuntimeError(f"配置缺失，未找到任一字段: {', '.join(names)}")
    return default


class QuestionService:
    def __init__(self) -> None:
        self.settings = _load_settings()

        self.api_key = _pick_setting(
            self.settings,
            "ARK_API_KEY",
            "VOLCENGINE_API_KEY",
            "LLM_API_KEY",
            "OPENAI_API_KEY",
            "API_KEY",
            required=True,
        )
        self.model = _pick_setting(
            self.settings,
            "ARK_MODEL",
            "LLM_MODEL",
            "CHAT_MODEL",
            "MODEL",
            required=True,
        )
        self.base_url = _pick_setting(
            self.settings,
            "ARK_BASE_URL",
            "LLM_BASE_URL",
            "OPENAI_BASE_URL",
            "BASE_URL",
            default="https://ark.cn-beijing.volces.com/api/v3",
        )
        self.temperature = _pick_setting(
            self.settings,
            "QUESTION_TEMPERATURE",
            "LLM_TEMPERATURE",
            "TEMPERATURE",
            default=0.7,
        )
        self.max_tokens = _pick_setting(
            self.settings,
            "QUESTION_MAX_TOKENS",
            "LLM_MAX_TOKENS",
            "MAX_TOKENS",
            default=2048,
        )

        self.neo4j_uri = _pick_setting(
            self.settings,
            "NEO4J_URI",
            required=True,
        )
        self.neo4j_user = _pick_setting(
            self.settings,
            "NEO4J_USERNAME",
            "NEO4J_USER",
            required=True,
        )
        self.neo4j_password = _pick_setting(
            self.settings,
            "NEO4J_PASSWORD",
            "NEO4J_PWD",
            required=True,
        )

        self.llm = ChatOpenAI(
            api_key=self.api_key,
            model=self.model,
            base_url=self.base_url,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        self.driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password),
        )

    def close(self) -> None:
        try:
            self.driver.close()
        except Exception:
            pass

    def generate_questions_for_path(self, path_json: dict) -> dict:
        """
        题目服务只做两件事：
        1. 基于已有学习路径 JSON 生成题目
        2. 把题目塞回对应任务点的 questions 字段中

        入参:
            path_json: learning_path_service 已生成好的完整路径 JSON
        出参:
            enriched_path_json: 补完题目的路径 JSON
        """
        if not isinstance(path_json, dict):
            raise ValueError("题目服务入参必须是路径 JSON 对象。")

        field = path_json.get("field") or path_json.get("domain") or ""
        goal = path_json.get("goal") or ""
        level = path_json.get("level") or ""
        background_plan = path_json.get("background_plan") or ""
        summary = path_json.get("summary") or ""

        enriched_result = self._enrich_path_with_questions(
            path_json=path_json,
            field=field,
            goal=goal,
            level=level,
            background_plan=background_plan,
            summary=summary,
        )

        if not isinstance(enriched_result, dict):
            raise ValueError("题目服务返回结果不是 JSON 对象。")

        return enriched_result

    def _enrich_path_with_questions(
        self,
        path_json: dict,
        field: str,
        goal: str,
        level: str,
        background_plan: str,
        summary: str,
    ) -> dict:
        """
        为路径中的每个任务补题，并将结果写回 task['questions']。
        """
        stages = path_json.get("stages", [])
        if not isinstance(stages, list):
            path_json["stages"] = []
            return path_json

        for stage in stages:
            if not isinstance(stage, dict):
                continue

            tasks = stage.get("tasks", [])
            if not isinstance(tasks, list):
                stage["tasks"] = []
                continue

            for task in tasks:
                if not isinstance(task, dict):
                    continue

                task_meta = task.get("task_meta", {})
                if not isinstance(task_meta, dict):
                    task_meta = {}

                knowledge_point_names = task_meta.get("knowledge_point_names", [])
                if not knowledge_point_names:
                    knowledge_point_names = task.get("knowledge_point_names", [])

                if not isinstance(knowledge_point_names, list):
                    knowledge_point_names = []

                task_name = (
                    task.get("task_title")
                    or task.get("task_name")
                    or task.get("title")
                    or ""
                )

                if not knowledge_point_names:
                    old_questions = task.get("questions", [])
                    task["questions"] = old_questions if isinstance(old_questions, list) else []
                    continue

                matched_knowledge = self._query_matched_knowledge(knowledge_point_names)
                questions = self._generate_questions_for_task(
                    matched_knowledge,
                    field,
                    goal,
                    level,
                    background_plan,
                    summary,
                    task_name,
                )
                task["questions"] = questions if isinstance(questions, list) else []

        return path_json

    def _query_matched_knowledge(self, knowledge_point_names: list[str]) -> list[str]:
        """
        从 Neo4j 查询与 knowledge_point_names 匹配的 KnowledgePoint。
        """
        try:
            matched: list[str] = []

            with self.driver.session() as session:
                for name in knowledge_point_names:
                    result = session.run(
                        """
                        MATCH (kp:KnowledgePoint {name: $name})
                        RETURN kp.name AS name
                        """,
                        name=name,
                    )
                    for record in result:
                        value = record.get("name")
                        if value:
                            matched.append(value)

            return matched

        except Exception as e:
            print("❌ Neo4j 查询错误：", e)
            return []

    def _generate_questions_for_task(
        self,
        knowledge_list: list,
        field: str,
        goal: str,
        level: str,
        background_plan: str,
        summary: str,
        task_name: str,
    ) -> list:
        """
        为单个任务生成题目，返回列表。
        这里不改原有生成逻辑，只改配置获取方式。
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
                parts = [p.strip() for p in line.split("|")]
                questions.append(
                    {
                        "question_text": parts[0] if parts else "",
                        "options": parts[1:] if len(parts) > 1 else [],
                        "correct_answer": "",
                    }
                )
            else:
                questions.append(
                    {
                        "question_text": line,
                        "correct_answer": "",
                    }
                )

        return questions


@lru_cache(maxsize=1)
def get_question_service() -> QuestionService:
    return QuestionService()
