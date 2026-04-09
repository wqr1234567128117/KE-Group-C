from __future__ import annotations

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    real_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    major: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)


class ChatRecord(Base):
    __tablename__ = "chat_records"

    record_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"), nullable=False)
    session_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    qa_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    question_content: Mapped[str] = mapped_column(Text, nullable=False)
    answer_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    knowledge_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    asked_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)


class HomeworkAssist(Base):
    __tablename__ = "homework_assists"

    assist_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"), nullable=False)
    assist_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_content: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    correction_suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    solving_hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)


class LearningPath(Base):
    __tablename__ = "learning_paths"

    path_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"), nullable=False)
    status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    current_task_point: Mapped[str | None] = mapped_column(String(255), nullable=True)
    goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    background_plan: Mapped[str | None] = mapped_column(String(255), nullable=True)
    level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    domain: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)


class PathTask(Base):
    __tablename__ = "path_tasks"

    task_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    path_id: Mapped[int] = mapped_column(Integer, ForeignKey("learning_paths.path_id"), nullable=False)
    progress_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("learning_progress.progress_id"), nullable=True)
    task_name: Mapped[str] = mapped_column(String(100), nullable=False)
    task_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_completed: Mapped[int | None] = mapped_column(Integer, nullable=True)  # tinyint in MySQL
    created_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)


class TaskQuestion(Base):
    __tablename__ = "task_questions"

    question_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("path_tasks.task_id"), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    correct_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_passed: Mapped[int | None] = mapped_column(Integer, nullable=True)  # tinyint
    user_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)


class LearningProgress(Base):
    __tablename__ = "learning_progress"

    progress_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    path_id: Mapped[int] = mapped_column(Integer, ForeignKey("learning_paths.path_id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"), nullable=False)
    progress_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    progress_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    progress_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)
