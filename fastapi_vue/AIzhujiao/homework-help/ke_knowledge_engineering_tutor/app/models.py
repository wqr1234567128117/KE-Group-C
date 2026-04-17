from typing import List

from pydantic import BaseModel, Field


class QuestionItem(BaseModel):
    question_id: str = Field(default='')
    source_type: str = Field(default='text')
    source_name: str = Field(default='')
    recognized_question: str = Field(default='')


class QuestionResult(BaseModel):
    question_id: str = Field(default='')
    source_type: str = Field(default='text')
    source_name: str = Field(default='')
    recognized_question: str = Field(default='')
    topic_tags: List[str] = Field(default_factory=list)
    direct_answer: str = Field(default='')
    detailed_explanation: str = Field(default='')
    solving_outline: List[str] = Field(default_factory=list)
    key_points: List[str] = Field(default_factory=list)
    common_confusions: List[str] = Field(default_factory=list)
    relation_to_course: str = Field(default='')
    extension_questions: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0)


class BatchSolveResponse(BaseModel):
    course_name: str = Field(default='知识工程')
    total_questions: int = Field(default=0)
    question_list: List[QuestionItem] = Field(default_factory=list)
    results: List[QuestionResult] = Field(default_factory=list)


class SlideSummary(BaseModel):
    slide_no: int = Field(default=0)
    title: str = Field(default='')
    summary: str = Field(default='')
    knowledge_points: List[str] = Field(default_factory=list)


class PPTSummaryResult(BaseModel):
    course_theme: str = Field(default='')
    overall_summary: str = Field(default='')
    chapter_outline: List[str] = Field(default_factory=list)
    core_knowledge_points: List[str] = Field(default_factory=list)
    easy_confusions: List[str] = Field(default_factory=list)
    review_questions: List[str] = Field(default_factory=list)
    slide_summaries: List[SlideSummary] = Field(default_factory=list)
