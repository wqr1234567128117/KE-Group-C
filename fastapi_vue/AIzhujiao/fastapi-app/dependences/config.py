from functools import lru_cache
import json
from pathlib import Path

from pydantic import BaseModel, ValidationError


class Settings(BaseModel):
    ARK_API_KEY: str
    ARK_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    ARK_MODEL: str = "doubao-seed-2-0-pro-260215"

    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = ""
    NEO4J_DATABASE: str = "neo4j"

    ENABLE_GRAPH_QA: bool = False
    GRAPH_TOP_K: int = 10
    LANGCHAIN_VERBOSE: bool = False
    PROMPT_DIR: str = "../prompts"


def _load_json_config() -> dict:
    current_file = Path(__file__).resolve()
    config_path = current_file.parent / "env.json"

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"env.json 格式错误: {e}")


@lru_cache
def get_settings() -> Settings:
    data = _load_json_config()
    try:
        return Settings(**data)
    except ValidationError as e:
        raise ValueError(f"env.json 字段校验失败:\n{e}")