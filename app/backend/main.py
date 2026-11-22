
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from pathlib import Path
from typing import Optional
import shutil
import uuid

from app.config import UPLOAD_DIR

from app.database.neo4j_client import (
    verify_connection,
    ensure_schema,
    run_query
)

from app.ingestion.manager import ingest_pdf
from app.graph.workflow import run_question


app = FastAPI(
    title="NetGraph-RAG API",
    version="0.2.0"
)


# =========================================================
# REQUEST MODELS
# =========================================================

class QueryRequest(BaseModel):
    question: str
    thread_id: str = "default"

    document_id: Optional[str] = None
    chapter_id: Optional[str] = None


# =========================================================
# STARTUP
# =========================================================

@app.on_event("startup")
def startup():

    try:
        verify_connection()
        ensure_schema()

        print("Neo4j connected successfully.")

    except Exception as exc:
        print(f"Neo4j startup warning: {exc}")


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():

    try:
        verify_connection()

        return {
            "status": "ok",
            "neo4j": "connected"
        }

    except Exception as exc:

        return {
            "status": "degraded",
            "neo4j": str(exc)
        }


# =========================================================
# DOCUMENT UPLOAD
# =========================================================

@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_title: Optional[str] = Form(default=None),
    selected_chapters: Optional[str] = Form(default=None),
    standalone_chapter: bool = Form(default=False),
    standalone_chapter_title: Optional[str] = Form(default=None)
):

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF file."
        )

    Path(UPLOAD_DIR).mkdir(
        parents=True,
        exist_ok=True
    )

    # Generate a unique filename instead of trusting
    # the filename supplied by the user.
    upload_id = str(uuid.uuid4())

    destination = (
        Path(UPLOAD_DIR) / f"{upload_id}.pdf"
    )

    try:

        with destination.open("wb") as output:
            shutil.copyfileobj(file.file, output)

        chapters = None

        if selected_chapters:

            try:
                chapters = [
                    int(number.strip())
                    for number in selected_chapters.split(",")
                    if number.strip()
                ]

                if not chapters or any(number < 1 for number in chapters):
                    raise ValueError

            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "selected_chapters must contain "
                        "comma-separated positive chapter numbers."
                    )
                )

        result = ingest_pdf(
            path=str(destination),
            selected_chapters=chapters,
            document_title=document_title,
            standalone_chapter=standalone_chapter,
            standalone_chapter_title=standalone_chapter_title
        )

        return {
            "message": "Document ingested successfully.",
            "result": result
        }

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {exc}"
        )

    finally:
        await file.close()


# =========================================================
# LIST ALL DOCUMENTS
# =========================================================

@app.get("/documents")
def get_documents():

    try:

        rows = run_query("""
            MATCH (d:Document)

            OPTIONAL MATCH (ch:Chapter)-[:PART_OF]->(d)

            OPTIONAL MATCH (c:Chunk)-[:PART_OF]->(ch)

            RETURN
                d.id AS document_id,
                d.title AS title,
                count(DISTINCT ch) AS chapters,
                count(DISTINCT c) AS chunks

            ORDER BY title
        """)

        return [
            dict(row)
            for row in rows
        ]

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve documents: {exc}"
        )


# =========================================================
# LIST CHAPTERS OF A DOCUMENT
# =========================================================

@app.get("/documents/{document_id}/chapters")
def get_document_chapters(document_id: str):

    try:

        rows = run_query(
            """
            MATCH (d:Document {id: $document_id})

            MATCH (ch:Chapter)-[:PART_OF]->(d)

            OPTIONAL MATCH (c:Chunk)-[:PART_OF]->(ch)

            RETURN
                ch.id AS chapter_id,
                ch.chapter_number AS chapter_number,
                ch.title AS title,
                count(DISTINCT c) AS chunks

            ORDER BY chapter_number
            """,
            {
                "document_id": document_id
            }
        )

        return [
            dict(row)
            for row in rows
        ]

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve chapters: {exc}"
        )


# =========================================================
# QUESTION ANSWERING
# =========================================================

@app.post("/query")
def query(request: QueryRequest):

    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    try:

        result = run_question(
            question=request.question,
            thread_id=request.thread_id,
            document_id=request.document_id,
            chapter_id=request.chapter_id
        )

        return {
            "answer": result.get("answer", ""),
            "sources": result.get("documents", []),
            "citations": result.get("citations", [])
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )


# =========================================================
# KNOWLEDGE GRAPH
# =========================================================

@app.get("/graph")
def graph():

    try:

        rows = run_query("""
            MATCH (a)-[r]->(b)

            RETURN
                labels(a) AS sourceLabels,
                coalesce(a.name, a.title, a.id) AS source,
                type(r) AS relationship,
                labels(b) AS targetLabels,
                coalesce(b.name, b.title, b.id) AS target

            LIMIT 200
        """)

        return [
            dict(row)
            for row in rows
        ]

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve graph: {exc}"
        )
