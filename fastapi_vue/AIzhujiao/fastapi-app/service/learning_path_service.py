from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from langchain_openai import ChatOpenAI
from neo4j import Driver, GraphDatabase

from dependences.config import get_settings


class LearningPathService:
    """
    学习路径生成服务（只负责路径，不负责题目）

    职责：
    1. 读取外部 prompt 模板
    2. 查询 Neo4j 课程能力图谱
    3. 基于图谱 + 用户信息调用 LLM 生成学习路径
    4. 当图谱不足时，调用 LLM 进行兜底生成
    5. 返回最终可直接给 API 层使用的结构化 JSON
    """

    def __init__(
        self,
        graph_prompt_file: Optional[str] = None,
        fallback_prompt_file: Optional[str] = None,
    ) -> None:
        self.settings = get_settings()
        self._driver: Optional[Driver] = None

        self._graph_prompt_file_override = Path(graph_prompt_file).resolve() if graph_prompt_file else None
        self._fallback_prompt_file_override = Path(fallback_prompt_file).resolve() if fallback_prompt_file else None

    # =========================
    # 基础能力
    # =========================
    def _project_root(self) -> Path:
        # 假设当前文件路径形如：.../service/learning_path_service.py
        # 项目根目录取 parent.parent
        return Path(__file__).resolve().parent.parent

    def _read_prompt(self, filename: str, override_path: Optional[Path] = None) -> str:
        if override_path is not None:
            path = override_path
        else:
            prompt_dir = Path(self.settings.PROMPT_DIR)
            if not prompt_dir.is_absolute():
                prompt_dir = self._project_root() / prompt_dir
            path = (prompt_dir / filename).resolve()

        if not path.exists():
            raise FileNotFoundError(f"Prompt 文件不存在: {path}")

        return path.read_text(encoding="utf-8")

    def _get_llm(self, temperature: float = 0.2) -> ChatOpenAI:
        return ChatOpenAI(
            model=self.settings.ARK_MODEL,
            api_key=self.settings.ARK_API_KEY,
            base_url=self.settings.ARK_BASE_URL,
            temperature=temperature,
        )

    def _get_driver(self) -> Driver:
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.settings.NEO4J_URI,
                auth=(self.settings.NEO4J_USERNAME, self.settings.NEO4J_PASSWORD),
            )
        return self._driver

    def _get_database(self) -> Optional[str]:
        db_name = getattr(self.settings, "NEO4J_DATABASE", None)
        return db_name or None

    def _run_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        driver = self._get_driver()
        with driver.session(database=self._get_database()) as session:
            result = session.run(query, params or {})
            return [dict(record) for record in result]

    # =========================
    # 对外主入口
    # =========================
    def generate_learning_path(
        self,
        field: str,
        goal: str,
        level: str,
        background_plan: str,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        优先走：Neo4j + LLM
        如果图谱内容不足：走 LLM fallback
        """
        graph_payload = self._load_course_graph(field=field)

        if self._is_graph_sufficient(graph_payload):
            try:
                prompt_text = self._build_graph_prompt(
                    field=field,
                    goal=goal,
                    level=level,
                    background_plan=background_plan,
                    graph_payload=graph_payload,
                )
                raw_output = self._call_llm(prompt_text)
                parsed_data = self._parse_llm_json(raw_output)

                return self._normalize_path_result(
                    parsed_data=parsed_data,
                    field=field,
                    goal=goal,
                    level=level,
                    background_plan=background_plan,
                    user_id=user_id,
                )
            except Exception:
                # 图谱存在但调用失败时，继续走兜底
                pass

        fallback_prompt = self._build_fallback_prompt(
            field=field,
            goal=goal,
            level=level,
            background_plan=background_plan,
        )
        raw_output = self._call_llm(fallback_prompt)
        parsed_data = self._parse_llm_json(raw_output)

        return self._normalize_path_result(
            parsed_data=parsed_data,
            field=field,
            goal=goal,
            level=level,
            background_plan=background_plan,
            user_id=user_id,
        )

    # =========================
    # Prompt 构造（外部文件）
    # =========================
    def _build_graph_prompt(
        self,
        field: str,
        goal: str,
        level: str,
        background_plan: str,
        graph_payload: Dict[str, Any],
    ) -> str:
        """
        读取图谱规划 prompt 模板。
        建议外部文件名：learning_path_graph_prompt.txt

        模板里建议至少包含：
        {field}
        {goal}
        {level}
        {background_plan}
        {graph_json}
        """
        prompt_template = self._read_prompt(
            "learning_path_graph_prompt.txt",
            override_path=self._graph_prompt_file_override,
        )

        graph_json = json.dumps(graph_payload, ensure_ascii=False, indent=2)

        try:
            return prompt_template.format(
                field=field.strip(),
                goal=goal.strip(),
                level=level.strip(),
                background_plan=background_plan.strip(),
                graph_json=graph_json,
            )
        except KeyError as e:
            raise ValueError(f"图谱规划 Prompt 模板占位符缺失或错误: {e}") from e

    def _build_fallback_prompt(
        self,
        field: str,
        goal: str,
        level: str,
        background_plan: str,
    ) -> str:
        """
        读取兜底 prompt 模板。
        建议外部文件名：learning_path_fallback_prompt.txt

        模板里建议至少包含：
        {field}
        {goal}
        {level}
        {background_plan}
        """
        prompt_template = self._read_prompt(
            "../prompts/learning_path_graph_prompt.txt",
            override_path=self._fallback_prompt_file_override,
        )

        try:
            return prompt_template.format(
                field=field.strip(),
                goal=goal.strip(),
                level=level.strip(),
                background_plan=background_plan.strip(),
            )
        except KeyError as e:
            raise ValueError(f"兜底 Prompt 模板占位符缺失或错误: {e}") from e

    # =========================
    # 模型调用
    # =========================
    def _call_llm(self, prompt_text: str) -> str:
        resp = self._get_llm(temperature=0.2).invoke(prompt_text)
        return self._extract_text_from_llm_result(resp)

    @staticmethod
    def _extract_text_from_llm_result(result: Any) -> str:
        if isinstance(result, str):
            return result.strip()

        content = getattr(result, "content", None)
        if isinstance(content, str):
            return content.strip()

        return str(result).strip()

    # =========================
    # 图谱查询
    # =========================
    def _load_course_graph(self, field: str) -> Dict[str, Any]:
        course = self._match_course_node(field=field)
        if not course:
            return {}

        course_id = course["course_id"]

        first_second_query = """
        MATCH (course:AbilityNode {id: $course_id})-[:CONTAINS]->(fa:FirstAbility)
        OPTIONAL MATCH (fa)-[:CONTAINS]->(sa:SecondAbility)
        RETURN
            course.id AS course_id,
            course.name AS course_name,
            fa.id AS first_id,
            fa.name AS first_name,
            sa.id AS second_id,
            sa.name AS second_name
        ORDER BY first_id, second_id
        """

        knowledge_query = """
        MATCH (course:AbilityNode {id: $course_id})-[:CONTAINS]->(:FirstAbility)-[:CONTAINS]->(sa:SecondAbility)
        OPTIONAL MATCH (sa)-[:NEED_SUPPORT_FROM]->(kp:KnowledgePoint)
        RETURN
            sa.id AS second_id,
            kp.id AS kp_id,
            kp.name AS kp_name
        ORDER BY second_id, kp_id
        """

        dependency_query = """
        MATCH (course:AbilityNode {id: $course_id})-[:CONTAINS]->(:FirstAbility)-[:CONTAINS]->(a:SecondAbility)
        MATCH (course)-[:CONTAINS]->(:FirstAbility)-[:CONTAINS]->(b:SecondAbility)
        MATCH (a)-[r:INFLUENCES|RELATED_TO]->(b)
        RETURN
            a.id AS from_id,
            type(r) AS rel_type,
            b.id AS to_id
        """

        first_second_rows = self._run_query(first_second_query, {"course_id": course_id})
        knowledge_rows = self._run_query(knowledge_query, {"course_id": course_id})
        dependency_rows = self._run_query(dependency_query, {"course_id": course_id})

        first_map: Dict[str, Dict[str, Any]] = {}
        second_map: Dict[str, Dict[str, Any]] = {}

        for row in first_second_rows:
            first_id = row.get("first_id")
            first_name = row.get("first_name")
            second_id = row.get("second_id")
            second_name = row.get("second_name")

            if not first_id:
                continue

            first_node = first_map.setdefault(
                first_id,
                {
                    "id": first_id,
                    "name": first_name or first_id,
                    "seconds": [],
                    "_second_ids": set(),
                },
            )

            if second_id and second_id not in first_node["_second_ids"]:
                second_node = {
                    "id": second_id,
                    "name": second_name or second_id,
                    "knowledge_points": [],
                }
                first_node["seconds"].append(second_node)
                first_node["_second_ids"].add(second_id)
                second_map[second_id] = second_node

        for row in knowledge_rows:
            second_id = row.get("second_id")
            kp_id = row.get("kp_id")
            kp_name = row.get("kp_name")

            if not second_id or second_id not in second_map:
                continue
            if not kp_id and not kp_name:
                continue

            second_map[second_id]["knowledge_points"].append(
                {
                    "id": kp_id or kp_name,
                    "name": kp_name or kp_id,
                }
            )

        first_abilities: List[Dict[str, Any]] = []
        for first_node in first_map.values():
            first_node.pop("_second_ids", None)
            first_node["seconds"].sort(key=lambda x: self._sort_key(x["id"]))
            for second in first_node["seconds"]:
                second["knowledge_points"].sort(key=lambda x: self._sort_key(x["id"]))
            first_abilities.append(first_node)

        first_abilities.sort(key=lambda x: self._sort_key(x["id"]))

        second_edges: List[Dict[str, str]] = []
        for row in dependency_rows:
            from_id = row.get("from_id")
            rel_type = row.get("rel_type")
            to_id = row.get("to_id")
            if from_id and rel_type and to_id:
                second_edges.append(
                    {
                        "from_id": from_id,
                        "rel_type": rel_type,
                        "to_id": to_id,
                    }
                )

        return {
            "course": course,
            "first_abilities": first_abilities,
            "second_ability_dependencies": second_edges,
        }

    def _match_course_node(self, field: str) -> Optional[Dict[str, str]]:
        rows = self._run_query(
            """
            MATCH (c:AbilityNode)
            RETURN c.id AS course_id, c.name AS course_name
            """
        )
        if not rows:
            return None

        raw_field = (field or "").strip().lower()

        def score(row: Dict[str, str]) -> int:
            cid = (row.get("course_id") or "").strip().lower()
            cname = (row.get("course_name") or "").strip().lower()

            if raw_field and raw_field == cid:
                return 100
            if raw_field and raw_field == cname:
                return 95
            if raw_field and raw_field in cname:
                return 80
            if raw_field and raw_field in cid:
                return 75
            if raw_field and cname in raw_field:
                return 60
            return 0

        ranked = sorted(rows, key=lambda r: (score(r), self._sort_key(r.get("course_id") or "")), reverse=True)
        best = ranked[0]

        if score(best) > 0:
            return {
                "course_id": best["course_id"],
                "course_name": best["course_name"],
            }

        if len(rows) == 1:
            return {
                "course_id": rows[0]["course_id"],
                "course_name": rows[0]["course_name"],
            }

        return None

    @staticmethod
    def _is_graph_sufficient(graph_payload: Dict[str, Any]) -> bool:
        if not graph_payload:
            return False

        first_abilities = graph_payload.get("first_abilities", [])
        if not isinstance(first_abilities, list) or not first_abilities:
            return False

        second_count = 0
        for first in first_abilities:
            seconds = first.get("seconds", [])
            if isinstance(seconds, list):
                second_count += len(seconds)

        return second_count > 0

    # =========================
    # 输出解析
    # =========================
    def _parse_llm_json(self, raw_output: str) -> Dict[str, Any]:
        if not raw_output or not raw_output.strip():
            raise ValueError("模型返回内容为空。")

        cleaned = raw_output.strip()

        cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^```\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            data = json.loads(cleaned)
            if not isinstance(data, dict):
                raise ValueError("模型输出 JSON 顶层不是对象。")
            return data
        except json.JSONDecodeError:
            pass

        json_text = self._extract_first_json_object(cleaned)
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"模型输出无法解析为 JSON。原始输出: {raw_output}") from e

        if not isinstance(data, dict):
            raise ValueError("模型输出 JSON 顶层不是对象。")

        return data

    @staticmethod
    def _extract_first_json_object(text: str) -> str:
        start = text.find("{")
        if start == -1:
            raise ValueError("未找到 JSON 起始字符 '{'。")

        brace_count = 0
        in_string = False
        escape = False

        for idx in range(start, len(text)):
            ch = text[idx]

            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue

            if ch == '"':
                in_string = True
            elif ch == "{":
                brace_count += 1
            elif ch == "}":
                brace_count -= 1
                if brace_count == 0:
                    return text[start: idx + 1]

        raise ValueError("未找到完整的 JSON 对象结束位置。")

    # =========================
    # 结果标准化
    # =========================
    def _normalize_path_result(
        self,
        parsed_data: Dict[str, Any],
        field: str,
        goal: str,
        level: str,
        background_plan: str,
        user_id: Optional[int],
    ) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "user_id": user_id,
            "field": parsed_data.get("field") or field,
            "goal": parsed_data.get("goal") or goal,
            "level": parsed_data.get("level") or level,
            "background_plan": parsed_data.get("background_plan") or background_plan,
            "summary": parsed_data.get("summary", ""),
            "stages": [],
        }

        raw_stages = parsed_data.get("stages", [])
        if not isinstance(raw_stages, list):
            raw_stages = []

        normalized_stages: List[Dict[str, Any]] = []

        for s_idx, stage in enumerate(raw_stages, start=1):
            if not isinstance(stage, dict):
                continue

            normalized_stage: Dict[str, Any] = {
                "stage_order": self._coerce_int(stage.get("stage_order"), s_idx),
                "stage_title": stage.get("stage_title") or stage.get("title") or f"阶段{s_idx}",
                "stage_objective": stage.get("stage_objective") or stage.get("objective") or "",
                "stage_description": stage.get("stage_description") or stage.get("description") or "",
                "tasks": [],
            }

            raw_tasks = stage.get("tasks", [])
            if not isinstance(raw_tasks, list):
                raw_tasks = []

            normalized_tasks: List[Dict[str, Any]] = []

            for t_idx, task in enumerate(raw_tasks, start=1):
                if not isinstance(task, dict):
                    continue

                questions = task.get("questions", [])
                if not isinstance(questions, list):
                    questions = []

                source_second_ability_id = (
                    task.get("source_second_ability_id")
                    or (task.get("task_meta") or {}).get("source_second_ability_id")
                    or ""
                )

                knowledge_point_ids = task.get("knowledge_point_ids", [])
                if not isinstance(knowledge_point_ids, list):
                    knowledge_point_ids = []

                knowledge_point_names = task.get("knowledge_point_names", [])
                if not isinstance(knowledge_point_names, list):
                    knowledge_point_names = []

                normalized_task: Dict[str, Any] = {
                    "task_order": self._coerce_int(task.get("task_order"), t_idx),
                    "task_title": task.get("task_title") or task.get("title") or f"任务{t_idx}",
                    "task_description": task.get("task_description") or task.get("description") or "",
                    "questions": questions,
                    "task_meta": {
                        "source_second_ability_id": source_second_ability_id,
                        "knowledge_point_ids": knowledge_point_ids,
                        "knowledge_point_names": knowledge_point_names,
                    },
                }

                normalized_tasks.append(normalized_task)

            normalized_stage["tasks"] = normalized_tasks
            normalized_stages.append(normalized_stage)

        result["stages"] = normalized_stages
        return result

    @staticmethod
    def _coerce_int(value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _sort_key(value: str) -> Tuple[Any, ...]:
        parts = re.findall(r"\d+|[^\d]+", value or "")
        normalized: List[Any] = []
        for part in parts:
            normalized.append(int(part) if part.isdigit() else part)
        return tuple(normalized)


@lru_cache
def get_learning_path_service(
    graph_prompt_file: Optional[str] = None,
    fallback_prompt_file: Optional[str] = None,
) -> LearningPathService:
    return LearningPathService(
        graph_prompt_file=graph_prompt_file,
        fallback_prompt_file=fallback_prompt_file,
    )