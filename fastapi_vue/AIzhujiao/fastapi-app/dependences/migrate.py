from __future__ import annotations

from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine


def _has_column(engine: Engine, table: str, column: str) -> bool:
    insp = inspect(engine)
    cols = insp.get_columns(table)
    return any(c.get("name") == column for c in cols)


def run_migrations(engine: Engine) -> None:
    """
    仅做“向后兼容”的轻量迁移，保证业务逻辑所需字段存在。
    不做破坏性变更。
    """
    with engine.begin() as conn:
        # users.real_name（业务逻辑需要姓名，但 SQL dump 没有）
        if not _has_column(engine, "users", "real_name"):
            conn.execute(text("ALTER TABLE users ADD COLUMN real_name varchar(50) NULL DEFAULT NULL"))

        # learning_paths：补齐 goal / level / domain（路径规划页需要）
        if not _has_column(engine, "learning_paths", "goal"):
            conn.execute(text("ALTER TABLE learning_paths ADD COLUMN goal varchar(255) NULL DEFAULT NULL"))
        if not _has_column(engine, "learning_paths", "level"):
            conn.execute(text("ALTER TABLE learning_paths ADD COLUMN level varchar(50) NULL DEFAULT NULL"))
        if not _has_column(engine, "learning_paths", "domain"):
            conn.execute(text("ALTER TABLE learning_paths ADD COLUMN domain varchar(50) NULL DEFAULT NULL"))
