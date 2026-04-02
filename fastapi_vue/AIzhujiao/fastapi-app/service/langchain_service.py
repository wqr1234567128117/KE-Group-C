from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from threading import Lock
from typing import Any, Generator

from langchain.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_neo4j import Neo4jGraph

from dependences.config import get_settings


class LangChainChatService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._graph: Neo4jGraph | None = None
        self._graph_lock = Lock()

    # =========================
    # 基础能力
    # =========================
    def _project_root(self) -> Path:
        # service/langchain_service.py -> 项目根目录
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

    def _get_graph(self) -> Neo4jGraph:
        if self._graph is None:
            with self._graph_lock:
                if self._graph is None:
                    self._graph = Neo4jGraph(
                        url=self.settings.NEO4J_URI,
                        username=self.settings.NEO4J_USERNAME,
                        password=self.settings.NEO4J_PASSWORD,
                        database=self.settings.NEO4J_DATABASE,
                    )
                    self._graph.refresh_schema()
        return self._graph

    # =========================
    # 直接问答
    # =========================
    def _build_direct_messages(
        self,
        question: str,
        history: list[dict[str, Any]],
    ) -> list:
        system_prompt = self._read_prompt("answer_prompt.txt")
        messages = [SystemMessage(content=system_prompt)]

        # 兼容两种历史格式：
        # 1. {"question": "...", "answer": "..."}
        # 2. {"role": "user"/"assistant", "content": "..."}
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
    ) -> str:
        if not history:
            return question

        history_text = self._history_to_text(history)

        prompt = f"""
你是一个问题改写助手。
请根据对话历史，把用户当前问题改写成一个信息完整、可直接用于知识图谱查询的问题。
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
                else:
                    break

            if inside_code:
                code_lines.append(line)

        extracted = "\n".join(code_lines).strip()
        return extracted or text

    def _generate_cypher(
        self,
        graph: Neo4jGraph,
        question: str,
    ) -> str:
        cypher_prompt = PromptTemplate(
            input_variables=["schema", "question"],
            template=self._read_prompt("cypher_prompt.txt"),
        )

        prompt_text = cypher_prompt.format(
            schema=graph.schema,
            question=question,
        )

        resp = self._get_llm(temperature=0).invoke(prompt_text)
        raw_text = getattr(resp, "content", str(resp)).strip()
        cypher = self._extract_cypher(raw_text)

        if not cypher:
            raise ValueError("未生成有效 Cypher")

        return cypher

    def _query_graph(
        self,
        graph: Neo4jGraph,
        cypher: str,
    ) -> list[dict[str, Any]]:
        records = graph.query(cypher)

        if not isinstance(records, list):
            return []

        top_k = max(int(self.settings.GRAPH_TOP_K), 1)
        return records[:top_k]

    def _build_graph_qa_prompt(
        self,
        context: list[dict[str, Any]],
        question: str,
    ) -> str:
        qa_prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=self._read_prompt("graph_qa_prompt.txt"),
        )

        return qa_prompt.format(
            context=str(context),
            question=question,
        )

    def _ask_graph_stream(
        self,
        question: str,
        history: list[dict[str, Any]],
    ) -> Generator[str, None, None]:
        graph = self._get_graph()

        standalone_question = self._rewrite_question_for_graph(
            question=question,
            history=history,
        )

        cypher = self._generate_cypher(
            graph=graph,
            question=standalone_question,
        )

        context = self._query_graph(
            graph=graph,
            cypher=cypher,
        )

        prompt_text = self._build_graph_qa_prompt(
            context=context,
            question=standalone_question,
        )

        for chunk in self._get_llm(temperature=0.2).stream(prompt_text):
            text = getattr(chunk, "content", "")
            if isinstance(text, str) and text:
                yield text

    # =========================
    # 对外接口：只保留流式
    # =========================
    def chat_stream(
        self,
        question: str,
        history: list[dict[str, Any]] | None = None,
    ) -> Generator[str, None, None]:
        question = question.strip()
        if not question:
            raise ValueError("question 不能为空")

        history = history or []

        if not self.settings.ENABLE_GRAPH_QA:
            yield from self._ask_direct_stream(question, history)
            return

        try:
            yield from self._ask_graph_stream(question, history)
        except Exception:
            # 图谱失败自动降级到普通问答
            yield from self._ask_direct_stream(question, history)


@lru_cache
def get_langchain_chat_service() -> LangChainChatService:
    return LangChainChatService()