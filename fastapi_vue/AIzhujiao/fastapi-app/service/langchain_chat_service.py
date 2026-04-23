from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from threading import Lock
from typing import Any, Generator, Optional, TYPE_CHECKING

from langchain.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from neo4j import Driver, GraphDatabase

if TYPE_CHECKING:
    from langchain_neo4j import Neo4jGraph

from dependences.config import get_settings


class LangChainChatService:
    def __init__(self) -> None:
        self.settings = get_settings()

        self._graph: "Neo4jGraph | None" = None
        self._graph_lock = Lock()

        self._driver: Optional[Driver] = None
        self._default_field = getattr(self.settings, "DEFAULT_GRAPH_COURSE", "知识工程")

    # =========================
    # 基础能力
    # =========================
    def _project_root(self) -> Path:
        return Path(__file__).resolve().parent.parent

    def _read_prompt(self, filename: str) -> str:
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

    def _get_graph(self) -> "Neo4jGraph":
        if bool(getattr(self.settings, "DISABLE_NEO4J", False)):
            raise RuntimeError("Neo4j 已在配置中禁用（DISABLE_NEO4J=true）")

        if self._graph is None:
            with self._graph_lock:
                if self._graph is None:
                    from langchain_neo4j import Neo4jGraph

                    self._graph = Neo4jGraph(
                        url=self.settings.NEO4J_URI,
                        username=self.settings.NEO4J_USERNAME,
                        password=self.settings.NEO4J_PASSWORD,
                        database=self.settings.NEO4J_DATABASE,
                    )
                    self._graph.refresh_schema()
        return self._graph

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
        params: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        driver = self._get_driver()
        with driver.session(database=self._get_database()) as session:
            result = session.run(query, params or {})
            return [dict(record) for record in result]

    @staticmethod
    def _sort_key(value: str) -> tuple[Any, ...]:
        parts = re.findall(r"\d+|[^\d]+", value or "")
        normalized: list[Any] = []
        for part in parts:
            normalized.append(int(part) if part.isdigit() else part)
        return tuple(normalized)

    # =========================
    # 路径规划同款：课程图谱缩域
    # =========================
    def _match_course_node(self, field: str) -> Optional[dict[str, str]]:
        rows = self._run_query(
            """
            MATCH (c:AbilityNode)
            RETURN c.id AS course_id, c.name AS course_name
            """
        )
        if not rows:
            return None

        raw_field = (field or "").strip().lower()

        def score(row: dict[str, str]) -> int:
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

        ranked = sorted(
            rows,
            key=lambda r: (score(r), self._sort_key(r.get("course_id") or "")),
            reverse=True,
        )
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

    def _load_course_graph(self, field: str) -> dict[str, Any]:
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

        first_map: dict[str, dict[str, Any]] = {}
        second_map: dict[str, dict[str, Any]] = {}

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

        first_abilities: list[dict[str, Any]] = []
        for first_node in first_map.values():
            first_node.pop("_second_ids", None)
            first_node["seconds"].sort(key=lambda x: self._sort_key(x["id"]))
            for second in first_node["seconds"]:
                second["knowledge_points"].sort(key=lambda x: self._sort_key(x["id"]))
            first_abilities.append(first_node)

        first_abilities.sort(key=lambda x: self._sort_key(x["id"]))

        second_edges: list[dict[str, str]] = []
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

    # =========================
    # 普通问答
    # =========================
    def _build_direct_messages(
        self,
        question: str,
        history: list[dict[str, Any]],
    ) -> list:
        system_prompt = self._read_prompt("answer_prompt.txt")
        messages = [SystemMessage(content=system_prompt)]

        for item in history[-6:]:
            if "role" in item and "content" in item:
                role = (item.get("role") or "").strip().lower()
                content = (item.get("content") or "").strip()
                if not content:
                    continue

                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
                continue

            q = (item.get("question") or "").strip()
            a = (item.get("answer") or "").strip()
            if q:
                messages.append(HumanMessage(content=q))
            if a:
                messages.append(AIMessage(content=a))

        messages.append(HumanMessage(content=question))
        return messages

    def _ask_direct_stream(
        self,
        question: str,
        history: list[dict[str, Any]],
    ) -> Generator[str, None, None]:
        messages = self._build_direct_messages(question=question, history=history)

        for chunk in self._get_llm(temperature=0.3).stream(messages):
            text = getattr(chunk, "content", "")
            if isinstance(text, str) and text:
                yield text

    # =========================
    # 图谱问答
    # =========================
    def _history_to_text(self, history: list[dict[str, Any]]) -> str:
        parts: list[str] = []

        for item in history[-6:]:
            if "role" in item and "content" in item:
                role = (item.get("role") or "").strip().lower()
                content = (item.get("content") or "").strip()
                if not content:
                    continue

                if role == "user":
                    parts.append(f"用户：{content}")
                elif role == "assistant":
                    parts.append(f"助手：{content}")
                continue

            q = (item.get("question") or "").strip()
            a = (item.get("answer") or "").strip()
            if q:
                parts.append(f"用户：{q}")
            if a:
                parts.append(f"助手：{a}")

        return "\n".join(parts)

    def _rewrite_question_for_graph(
        self,
        question: str,
        history: list[dict[str, Any]],
        field: str,
    ) -> str:
        if not history:
            return f"在“{field}”课程语境下，{question}"

        history_text = self._history_to_text(history)

        prompt = f"""
你是一个问题改写助手。
请根据对话历史，把用户当前问题改写成一个信息完整、可直接用于知识图谱查询的问题。
当前课程领域：{field}
只输出改写后的问题，不要解释。

对话历史：
{history_text}

当前问题：
{question}
""".strip()

        resp = self._get_llm(temperature=0).invoke(prompt)
        standalone_question = getattr(resp, "content", question)
        standalone_question = standalone_question.strip()

        return standalone_question or question

    def _extract_cypher(self, text: str) -> str:
        text = (text or "").strip()

        if "```" not in text:
            return text

        lines = text.splitlines()
        inside_code = False
        code_lines: list[str] = []

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("```"):
                if not inside_code:
                    inside_code = True
                    continue
                break

            if inside_code:
                code_lines.append(line)

        extracted = "\n".join(code_lines).strip()
        return extracted or text

    def _validate_readonly_cypher(self, cypher: str) -> None:
        normalized = re.sub(r"\s+", " ", (cypher or "")).strip().upper()

        forbidden_keywords = [
            "CREATE ",
            "MERGE ",
            "DELETE ",
            "DETACH DELETE ",
            "SET ",
            "REMOVE ",
            "DROP ",
            "LOAD CSV ",
            "FOREACH ",
            "CALL DBMS",
            "CALL APOC",
        ]
        for keyword in forbidden_keywords:
            if keyword in normalized:
                raise ValueError(f"检测到危险 Cypher 关键字：{keyword.strip()}")

        if not normalized.startswith(("MATCH ", "OPTIONAL MATCH ", "WITH ", "UNWIND ")):
            raise ValueError("Cypher 必须以只读查询语句开头")

        if " RETURN " not in f" {normalized} ":
            raise ValueError("Cypher 必须包含 RETURN")

    def _generate_cypher(
        self,
        graph: "Neo4jGraph",
        question: str,
        field: str,
        graph_payload: dict[str, Any],
    ) -> str:
        cypher_prompt = PromptTemplate(
            input_variables=["schema", "course_name", "graph_json", "question"],
            template=self._read_prompt("cypher_prompt.txt"),
        )

        course_name = (graph_payload.get("course") or {}).get("course_name") or field
        graph_json = json.dumps(graph_payload, ensure_ascii=False, indent=2)

        prompt_text = cypher_prompt.format(
            schema=graph.schema,
            course_name=course_name,
            graph_json=graph_json,
            question=question,
        )

        resp = self._get_llm(temperature=0).invoke(prompt_text)
        raw_text = getattr(resp, "content", str(resp)).strip()
        cypher = self._extract_cypher(raw_text)

        if not cypher:
            raise ValueError("未生成有效 Cypher")

        self._validate_readonly_cypher(cypher)
        return cypher

    def _query_graph(
        self,
        graph: "Neo4jGraph",
        cypher: str,
    ) -> list[dict[str, Any]]:
        records = graph.query(cypher)

        if not isinstance(records, list):
            return []

        top_k = max(int(getattr(self.settings, "GRAPH_TOP_K", 5)), 1)
        return records[:top_k]

    def _build_graph_qa_prompt(
        self,
        context: list[dict[str, Any]],
        question: str,
        field: str,
        graph_payload: dict[str, Any],
    ) -> str:
        qa_prompt = PromptTemplate(
            input_variables=["course_name", "graph_json", "context", "question"],
            template=self._read_prompt("graph_qa_prompt.txt"),
        )

        course_name = (graph_payload.get("course") or {}).get("course_name") or field
        graph_json = json.dumps(graph_payload, ensure_ascii=False, indent=2)

        return qa_prompt.format(
            course_name=course_name,
            graph_json=graph_json,
            context=json.dumps(context, ensure_ascii=False, indent=2),
            question=question,
        )

    def _ask_graph_stream(
        self,
        question: str,
        history: list[dict[str, Any]],
        field: Optional[str] = None,
    ) -> Generator[str, None, None]:
        final_field = (field or self._default_field).strip() or self._default_field

        graph = self._get_graph()
        graph_payload = self._load_course_graph(field=final_field)

        standalone_question = self._rewrite_question_for_graph(
            question=question,
            history=history,
            field=final_field,
        )

        cypher = self._generate_cypher(
            graph=graph,
            question=standalone_question,
            field=final_field,
            graph_payload=graph_payload,
        )

        context = self._query_graph(
            graph=graph,
            cypher=cypher,
        )

        if not context and graph_payload:
            # 查询为空时，至少把课程结构作为弱上下文给回答模型
            context = [
                {
                    "course": graph_payload.get("course", {}),
                    "first_abilities": graph_payload.get("first_abilities", [])[:5],
                    "second_ability_dependencies": graph_payload.get(
                        "second_ability_dependencies", []
                    )[:10],
                }
            ]

        prompt_text = self._build_graph_qa_prompt(
            context=context,
            question=standalone_question,
            field=final_field,
            graph_payload=graph_payload,
        )

        for chunk in self._get_llm(temperature=0.2).stream(prompt_text):
            text = getattr(chunk, "content", "")
            if isinstance(text, str) and text:
                yield text

    # =========================
    # 对外接口
    # =========================
    def chat_stream(
        self,
        question: str,
        history: list[dict[str, Any]] | None = None,
        field: Optional[str] = None,
    ) -> Generator[str, None, None]:
        question = question.strip()
        if not question:
            raise ValueError("question 不能为空")

        history = history or []

        if not getattr(self.settings, "ENABLE_GRAPH_QA", False):
            yield from self._ask_direct_stream(question, history)
            return

        try:
            yield from self._ask_graph_stream(question, history, field=field)
        except Exception:
            yield from self._ask_direct_stream(question, history)


@lru_cache
def get_langchain_chat_service() -> LangChainChatService:
    return LangChainChatService()