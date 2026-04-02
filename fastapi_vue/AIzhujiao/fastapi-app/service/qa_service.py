from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from threading import Lock
from typing import Any

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain

from dependences.config import get_settings


class QAService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._graph: Neo4jGraph | None = None
        self._graph_lock = Lock()

    def _read_prompt(self, filename: str) -> str:
        path = Path(self.settings.PROMPT_DIR) / filename
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

    def _ask_direct(self, question: str) -> dict[str, Any]:
        prompt = PromptTemplate(
            input_variables=["question"],
            template=self._read_prompt("direct_answer_prompt.txt"),
        )
        chain = prompt | self._get_llm(temperature=0.3)
        result = chain.invoke({"question": question})

        answer = getattr(result, "content", str(result))
        return {
            "mode": "direct",
            "answer": answer,
            "cypher": None,
            "context": None,
        }

    def _ask_graph(self, question: str, return_steps: bool = False) -> dict[str, Any]:
        graph = self._get_graph()

        cypher_prompt = PromptTemplate(
            input_variables=["schema", "question"],
            template=self._read_prompt("graph_cypher_prompt.txt"),
        )

        qa_prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=self._read_prompt("graph_qa_prompt.txt"),
        )

        chain = GraphCypherQAChain.from_llm(
            graph=graph,
            cypher_llm=self._get_llm(temperature=0),
            qa_llm=self._get_llm(temperature=0.2),
            cypher_prompt=cypher_prompt,
            qa_prompt=qa_prompt,
            validate_cypher=True,
            return_intermediate_steps=True,
            top_k=self.settings.GRAPH_TOP_K,
            verbose=self.settings.LANGCHAIN_VERBOSE,
            allow_dangerous_requests=True,
        )

        raw = chain.invoke({"query": question})

        answer = raw["result"] if isinstance(raw, dict) else str(raw)
        cypher = None
        context = None

        if isinstance(raw, dict):
            for step in raw.get("intermediate_steps", []):
                if isinstance(step, dict):
                    if cypher is None and isinstance(step.get("query"), str):
                        cypher = step["query"]
                    if context is None and "context" in step:
                        context = step["context"]

        return {
            "mode": "graph",
            "answer": answer,
            "cypher": cypher if return_steps else None,
            "context": context if return_steps else None,
        }

    def ask(self, question: str, return_steps: bool = False) -> dict[str, Any]:
        question = question.strip()
        if not question:
            raise ValueError("question 不能为空")

        if not self.settings.ENABLE_GRAPH_QA:
            return self._ask_direct(question)

        try:
            return self._ask_graph(question, return_steps=return_steps)
        except Exception:
            return self._ask_direct(question)


@lru_cache
def get_qa_service() -> QAService:
    return QAService()


def ask_question(question: str) -> str:
    return get_qa_service().ask(question)["answer"]