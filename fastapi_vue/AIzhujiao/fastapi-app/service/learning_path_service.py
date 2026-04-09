from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_openai import ChatOpenAI

from dependences.config import get_settings


class LearningPathService:
    """
    学习路径生成服务

    职责：
    1. 读取 prompt 模板
    2. 拼接用户输入
    3. 调用大模型生成“阶段 + 任务”
    4. 解析 JSON 结果
    5. 调用题目生成桥接层，为每个任务补充题目
    6. 返回最终可直接给后端落库 / 给前端展示的数据结构
    """

    def __init__(
        self,
        prompt_file: Optional[str] = None,
        question_bridge: Optional[Any] = None,
    ) -> None:
        self.settings = get_settings()
        self.question_bridge = question_bridge
        self._prompt_file_override = Path(prompt_file).resolve() if prompt_file else None

    # =========================
    # 基础能力
    # =========================
    def _project_root(self) -> Path:
        # service/learning_path_service.py -> 项目根目录
        return Path(__file__).resolve().parent.parent

    def _read_prompt(self, filename: str) -> str:
        # 允许外部显式指定 prompt 文件，优先级最高
        if self._prompt_file_override is not None:
            path = self._prompt_file_override
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
        生成完整学习路径，并尝试为每个任务补充题目。

        :param field: 学习领域
        :param goal: 学习目标
        :param level: 用户自评学习水平
        :param background_plan: 学习背景描述与学习计划描述
        :param user_id: 用户 ID，可选，仅做透传
        :return: 最终打包后的结构化结果
        """
        prompt_text = self._build_prompt(
            field=field,
            goal=goal,
            level=level,
            background_plan=background_plan,
        )

        raw_output = self._call_llm(prompt_text)
        parsed_data = self._parse_llm_json(raw_output)
        normalized_data = self._normalize_path_result(
            parsed_data=parsed_data,
            field=field,
            goal=goal,
            level=level,
            background_plan=background_plan,
            user_id=user_id,
        )

        if self.question_bridge is not None:
            normalized_data = self._attach_questions(
                data=normalized_data,
                field=field,
                goal=goal,
                level=level,
            )

        return normalized_data

    # =========================
    # Prompt 构造
    # =========================
    def _build_prompt(
        self,
        field: str,
        goal: str,
        level: str,
        background_plan: str,
    ) -> str:
        """
        读取 prompt 模板，并将用户输入填入。
        """
        prompt_template = self._read_prompt("learning_path_prompt.txt")

        try:
            return prompt_template.format(
                field=field.strip(),
                goal=goal.strip(),
                level=level.strip(),
                background_plan=background_plan.strip(),
            )
        except KeyError as e:
            raise ValueError(f"Prompt 模板占位符缺失或错误: {e}") from e

    # =========================
    # 模型调用
    # =========================
    def _call_llm(self, prompt_text: str) -> str:
        """
        使用项目统一配置初始化 LLM，并调用生成学习路径。
        """
        resp = self._get_llm(temperature=0.2).invoke(prompt_text)
        return self._extract_text_from_llm_result(resp)

    @staticmethod
    def _extract_text_from_llm_result(result: Any) -> str:
        """
        兼容以下返回格式：
        - str
        - AIMessage(content="...")
        - 其他可转字符串对象
        """
        if isinstance(result, str):
            return result.strip()

        content = getattr(result, "content", None)
        if isinstance(content, str):
            return content.strip()

        return str(result).strip()

    # =========================
    # 输出解析
    # =========================
    def _parse_llm_json(self, raw_output: str) -> Dict[str, Any]:
        """
        从模型原始输出中提取 JSON。
        """
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
        """
        从混杂文本中提取第一个完整 JSON 对象。
        """
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
                "stage_order": stage.get("stage_order", s_idx),
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

                normalized_task: Dict[str, Any] = {
                    "task_order": task.get("task_order", t_idx),
                    "task_title": task.get("task_title") or task.get("title") or f"任务{t_idx}",
                    "task_description": task.get("task_description") or task.get("description") or "",
                    "estimated_minutes": task.get("estimated_minutes"),
                    "questions": task.get("questions", []),
                }

                if not isinstance(normalized_task["questions"], list):
                    normalized_task["questions"] = []

                normalized_tasks.append(normalized_task)

            normalized_stage["tasks"] = normalized_tasks
            normalized_stages.append(normalized_stage)

        result["stages"] = normalized_stages
        return result

    # =========================
    # 题目挂接
    # =========================
    def _attach_questions(
        self,
        data: Dict[str, Any],
        field: str,
        goal: str,
        level: str,
    ) -> Dict[str, Any]:
        stages = data.get("stages", [])
        if not isinstance(stages, list):
            return data

        for stage in stages:
            stage_title = stage.get("stage_title", "")
            stage_objective = stage.get("stage_objective", "")
            tasks = stage.get("tasks", [])

            if not isinstance(tasks, list):
                continue

            for task in tasks:
                task_title = task.get("task_title", "")
                task_description = task.get("task_description", "")

                try:
                    question_result = self.question_bridge.generate_questions(
                        field=field,
                        goal=goal,
                        level=level,
                        stage_title=stage_title,
                        stage_objective=stage_objective,
                        task_title=task_title,
                        task_description=task_description,
                    )
                except Exception as e:
                    task["questions"] = []
                    task["question_generate_error"] = str(e)
                    continue

                task["questions"] = self._normalize_question_result(question_result)

        return data

    @staticmethod
    def _normalize_question_result(question_result: Any) -> List[Dict[str, Any]]:
        if question_result is None:
            return []

        if isinstance(question_result, dict):
            questions = question_result.get("questions", [])
            return questions if isinstance(questions, list) else []

        if isinstance(question_result, list):
            return question_result

        return []


@lru_cache
def get_learning_path_service(
    prompt_file: Optional[str] = None,
    question_bridge: Optional[Any] = None,
) -> LearningPathService:
    return LearningPathService(
        prompt_file=prompt_file,
        question_bridge=question_bridge,
    )