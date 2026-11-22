
from typing import TypedDict, Any


class RAGState(TypedDict, total=False):
    question: str
    query: str

    # Optional retrieval scope
    document_id: str | None
    chapter_id: str | None

    documents: list[dict[str, Any]]
    answer: str
    citations: list[dict[str, Any]]

    attempts: int
    sufficient: bool
    grading_reason: str

    error: str
