from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from dependences.config import get_settings


def _build_mysql_url() -> str:
    s = get_settings()
    if getattr(s, "DATABASE_URL", None):
        return s.DATABASE_URL

    host = getattr(s, "MYSQL_HOST", "127.0.0.1")
    port = getattr(s, "MYSQL_PORT", 3306)
    user = getattr(s, "MYSQL_USER", "root")
    password = getattr(s, "MYSQL_PASSWORD", "")
    db = getattr(s, "MYSQL_DB", "groub_c")

    # 容错：有些人会把 "user@host" 误填到 MYSQL_HOST
    host_str = str(host).strip()
    if "@" in host_str and host_str.count("@") == 1:
        maybe_user, maybe_host = host_str.split("@", 1)
        if maybe_host and not maybe_host.startswith(("http://", "https://")):
            host_str = maybe_host.strip()
            if user in ("root", "", None) and maybe_user.strip():
                user = maybe_user.strip()

    user_enc = quote_plus(str(user))
    pwd_enc = quote_plus(str(password))
    host_enc = host_str
    db_enc = quote_plus(str(db))
    return f"mysql+pymysql://{user_enc}:{pwd_enc}@{host_enc}:{int(port)}/{db_enc}?charset=utf8mb4"


engine = create_engine(
    _build_mysql_url(),
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
