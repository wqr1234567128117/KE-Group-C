from langchain_openai import ChatOpenAI
import warnings
from neo4j import GraphDatabase

warnings.filterwarnings("ignore")

# ===================== 配置区 =====================
API_KEY = "39cee702-8839-47eb-b155-171825131a24"  # 你自己填
MODEL = "doubao-seed-2-0-pro-260215"
BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PWD = "12345678"
# ====================================================


class QuestionService:
    def __init__(self) -> None:
        self.llm = ChatOpenAI(
            api_key=API_KEY,
            model=MODEL,
            base_url=BASE_URL,
            temperature=0.7,
            max_tokens=2048,
        )

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
        为路径中的每个任务补题，并将结果写回 task["questions"]。
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

                # 兼容旧/新结构：
                # 新结构优先从 task_meta.knowledge_point_names 取
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

                # 没有知识点时，保持 questions 为列表，避免前端/后续逻辑报错
                if not knowledge_point_names:
                    old_questions = task.get("questions", [])
                    task["questions"] = old_questions if isinstance(old_questions, list) else []
                    continue

                # 从 Neo4j 查询匹配的 KnowledgePoint
                matched_knowledge = self._query_matched_knowledge(knowledge_point_names)

                # 生成题目（生成逻辑不动）
                questions = self._generate_questions_for_task(
                    matched_knowledge,
                    field,
                    goal,
                    level,
                    background_plan,
                    summary,
                    task_name,
                )

                # 塞回对应任务点
                task["questions"] = questions if isinstance(questions, list) else []

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
                    result = session.run(
                        """
                        MATCH (kp:KnowledgePoint {name: $name})
                        RETURN kp.name AS name
                        """,
                        name=name,
                    )
                    for record in result:
                        matched.append(record.get("name"))

            driver.close()
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
        这里不改你的生成逻辑。
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
                questions.append(
                    {
                        "question_text": parts[0].strip(),
                        "options": [x.strip() for x in parts[1].split("|")] if len(parts) > 1 else [],
                        "correct_answer": "",  # 生成逻辑不动，仍保持空
                    }
                )
            else:
                # 简答题
                questions.append(
                    {
                        "question_text": line,
                        "correct_answer": "",
                    }
                )

        return questions


def get_question_service():
    return QuestionService()