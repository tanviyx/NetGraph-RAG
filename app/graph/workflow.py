
import sqlite3

from pathlib import Path

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

from app.config import CHECKPOINT_DIR

from app.graph.state import RAGState

from app.graph.nodes import (
    retrieve,
    grade_evidence,
    rewrite_query,
    answer
)


MAX_RETRIES = 2


def route_after_grading(state):

    sufficient = state.get("sufficient", False)

    attempts = state.get("attempts", 0)

    if sufficient:
        print("Evidence is sufficient. Proceeding to answer.")
        return "answer"

    if attempts >= MAX_RETRIES:
        print("Maximum retrieval attempts reached. Proceeding to answer.")
        return "answer"

    print("Evidence insufficient. Rewriting query.")
    return "rewrite"


def build_graph():

    Path(CHECKPOINT_DIR).mkdir(
        parents=True,
        exist_ok=True
    )

    database_path = (
        Path(CHECKPOINT_DIR) / "langgraph.sqlite"
    )

    conn = sqlite3.connect(
        str(database_path),
        check_same_thread=False
    )

    checkpointer = SqliteSaver(conn)

    graph = StateGraph(RAGState)

    graph.add_node("retrieve", retrieve)

    graph.add_node("grade", grade_evidence)

    graph.add_node("rewrite", rewrite_query)

    graph.add_node("answer", answer)

    graph.add_edge(START, "retrieve")

    graph.add_edge("retrieve", "grade")

    graph.add_conditional_edges(
        "grade",
        route_after_grading,
        {
            "rewrite": "rewrite",
            "answer": "answer"
        }
    )

    graph.add_edge("rewrite", "retrieve")

    graph.add_edge("answer", END)

    return graph.compile(
        checkpointer=checkpointer
    )


_graph = None


def get_graph():

    global _graph

    if _graph is None:
        _graph = build_graph()

    return _graph


def run_question(
    question: str,
    thread_id: str = "default",
    document_id: str | None = None,
    chapter_id: str | None = None
):

    initial_state = {
        "question": question,
        "query": question,
        "attempts": 0,
        "document_id": document_id,
        "chapter_id": chapter_id
    }

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    return get_graph().invoke(
        initial_state,
        config=config
    )
