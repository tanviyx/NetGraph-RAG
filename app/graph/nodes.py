from langchain_groq import ChatGroq

from app.config import GROQ_API_KEY, GROQ_MODEL
from app.retrieval.hybrid_search import hybrid_search


def get_llm():
    if not GROQ_API_KEY:
        raise RuntimeError("Set GROQ_API_KEY in .env before querying.")

    return ChatGroq(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        temperature=0
    )



def retrieve(state):
    query = state.get("query") or state["question"]

    print(f"\nRetrieving evidence for: {query}")

    document_id = state.get("document_id")
    chapter_id = state.get("chapter_id")

    documents = hybrid_search(
        query,
        top_k=6,
        document_id=document_id,
        chapter_id=chapter_id
    )

    print(f"Documents retrieved: {len(documents)}")
    print(f"Document scope: {document_id or 'All documents'}")
    print(f"Chapter scope: {chapter_id or 'All chapters'}")

    return {
        "documents": documents,
        "attempts": state.get("attempts", 0) + 1
    }



def grade_evidence(state):
    documents = state.get("documents", [])

    if not documents:
        return {
            "sufficient": False,
            "grading_reason": "No documents were retrieved."
        }

    evidence = "\n\n".join(
        f"Evidence {i + 1}:\n{doc.get('text', '')[:1200]}"
        for i, doc in enumerate(documents[:5])
    )

    prompt = f"""
You are an evidence relevance evaluator for a textbook RAG system.

Question:
{state['question']}

Retrieved evidence:
{evidence}

Evaluate whether the retrieved evidence directly contains information
needed to answer the question.

Rules:
- Relevant definitions count as evidence.
- Relevant explanations and examples count as evidence.
- Do not require the exact wording of the question.
- Ignore documents that are unrelated to the question.
- Do not judge based on document length.
- If the evidence only partially answers the question, mark INSUFFICIENT.

Respond with exactly one of:

DECISION: SUFFICIENT
DECISION: INSUFFICIENT
"""

    try:
        response = get_llm().invoke(prompt)
        result = response.content.strip().upper()

        # Exact decision parsing
        if "DECISION: SUFFICIENT" in result:
            sufficient = True
        elif "DECISION: INSUFFICIENT" in result:
            sufficient = False
        else:
            sufficient = False

        reason = response.content.strip()

    except Exception as error:
        print(f"Evidence grading failed: {error}")

        sufficient = False
        reason = f"Evidence grading error: {error}"

    print(f"Evidence sufficient: {sufficient}")
    print(f"Grading reason: {reason}")

    return {
        "sufficient": sufficient,
        "grading_reason": reason
    }

def rewrite_query(state):
    llm = get_llm()

    original_question = state["question"]

    prompt = f"""
You are optimizing a search query for a computer networking textbook.

Original question:
{original_question}

Generate a concise search query to retrieve relevant textbook passages.

Rules:
- Preserve the original question's meaning.
- Do not introduce new topics.
- Do not introduce unrelated concepts.
- Do not combine multiple questions.
- Use relevant technical terminology.
- Keep the query under 15 words.
- Do not answer the question.
- Return only the search query.

Search query:
"""

    try:
        response = llm.invoke(prompt)

        rewritten_query = response.content.strip().replace("\n", " ")

        # Safety check: avoid excessively long rewrites
        words = rewritten_query.split()

        if len(words) > 15:
            rewritten_query = " ".join(words[:15])

        if not rewritten_query:
            rewritten_query = original_question

    except Exception as error:
        print(f"Query rewriting failed: {error}")
        rewritten_query = original_question

    print(f"\nOriginal query: {original_question}")
    print(f"Rewritten query: {rewritten_query}")

    return {
        "query": rewritten_query
    }

def answer(state):
    llm = get_llm()

    documents = state.get("documents", [])

    evidence_parts = []
    citations = []

    for i, document in enumerate(documents, start=1):

        chunk_id = document.get("id", "Unknown")

        chapter = document.get("chapter_title", "Unknown chapter")

        start_page = document.get("start_printed_page")
        end_page = document.get("end_printed_page")

        if start_page is not None:
            if end_page is not None and end_page != start_page:
                page_info = f"Pages {start_page}-{end_page}"
            else:
                page_info = f"Page {start_page}"
        else:
            start_pdf = document.get("start_pdf_page")
            end_pdf = document.get("end_pdf_page")

            if start_pdf is not None:
                page_info = f"PDF pages {start_pdf}-{end_pdf}"
            else:
                page_info = "Page unavailable"

        evidence_parts.append(
            f"""
[Source {i}]
Chunk ID: {chunk_id}
Chapter: {chapter}
Section: {document.get('section', 'Unknown')}
{page_info}

Text:
{document.get('text', '')}
"""
        )

        citations.append({
            "source": i,
            "chunk_id": chunk_id,
            "chapter": chapter,
            "section": document.get("section"),
            "start_printed_page": start_page,
            "end_printed_page": end_page,
            "start_pdf_page": document.get("start_pdf_page"),
            "end_pdf_page": document.get("end_pdf_page")
        })

    evidence = "\n\n".join(evidence_parts)

    prompt = f"""
You are a question-answering assistant for a computer networking textbook.

Answer the user's question using ONLY the retrieved textbook evidence.

Question:
{state['question']}

Retrieved evidence:
{evidence}

Instructions:
1. Answer clearly and directly.
2. Use the evidence, not outside knowledge.
3. Cite supporting evidence using [Source 1], [Source 2], etc.
4. Only cite sources that actually support the statement.
5. If evidence is insufficient, explicitly state what information is missing.
6. Do not invent facts, examples, definitions, or citations.
7. Use numbered lists when explaining multiple components or steps.
8. Preserve technical terminology from the textbook.
"""

    response = llm.invoke(prompt)

    return {
        "answer": response.content,
        "citations": citations
    }