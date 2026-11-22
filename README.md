# NetGraph-RAG
Adaptive, incremental knowledge-graph-enhanced RAG for textbook PDFs.

## Stack
- LangGraph workflow orchestration and SQLite checkpointing
- Neo4j graph database + vector index
- Local Sentence Transformers embeddings (`all-MiniLM-L6-v2`)
- Groq chat model (configured in `.env`)
- FastAPI backend and Streamlit frontend
- PyMuPDF PDF extraction

## 1. Prerequisites
Install Python 3.10+ and create a Neo4j database (Neo4j Desktop or Aura).
You need a Groq API key if you want LLM-powered answers and entity extraction.

## 2. Setup (Windows PowerShell)
```powershell
cd NetGraph-RAG
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```
Edit `.env` and enter your Neo4j connection details and Groq API key.

## 3. Start backend
```powershell
uvicorn app.backend.main:app --reload --port 8000
```
API docs: http://127.0.0.1:8000/docs

## 4. Start frontend (second terminal)
```powershell
.\.venv\Scripts\Activate.ps1
streamlit run app\frontend\streamlit_app.py
```

## 5. First ingestion
Upload a PDF in the UI. The starter currently ingests the whole PDF and detects chapter headings heuristically.
The ingestion is idempotent by document/chapter content hash. Re-uploading unchanged content skips processed chapters.

## Notes / limitations of this starter
- This is a working project scaffold, not a production deployment.
- Chapter detection is heuristic; textbooks with unusual layouts may need a custom detector.
- Entity/relationship extraction is LLM-assisted and depends on Groq availability.
- The first local embedding-model download requires internet access.
- Initial retrieval combines vector results with graph-linked source chunks. Adaptive retrieval is intentionally capped to avoid infinite loops.
- For numerical answers, the system prioritizes source evidence; it does not yet run arbitrary calculations automatically.
- Credentials must stay in `.env`, never commit them.
