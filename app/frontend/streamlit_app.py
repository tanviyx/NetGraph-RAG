
import sys
import json
import uuid
from pathlib import Path

# Add project root to Python import path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import streamlit.components.v1 as components
import requests

from app.config import API_BASE_URL


# =========================================================
# CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="NetGraph-RAG",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = API_BASE_URL.rstrip("/")


# =========================================================
# SESSION STATE
# =========================================================

if "conversations" not in st.session_state:
    st.session_state.conversations = {}

if "active_chat_id" not in st.session_state:

    chat_id = str(uuid.uuid4())

    st.session_state.conversations[chat_id] = {
        "id": chat_id,
        "title": "New Chat",
        "thread_id": str(uuid.uuid4()),
        "messages": [],
        "scope": None,
    }

    st.session_state.active_chat_id = chat_id

if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "graph_data" not in st.session_state:
    st.session_state.graph_data = None

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>
    .main {
        background-color: #f8fafc;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .app-header {
        padding: 1rem 0 1.5rem 0;
    }

    .app-subtitle {
        color: #64748b;
        font-size: 1rem;
    }

    .source-card {
        padding: 12px;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        margin-bottom: 8px;
        background-color: white;
    }

    /* Visible metric cards */
    div[data-testid="stMetric"] {
        background-color: #e2e8f0 !important;
        border: 1px solid #94a3b8 !important;
        border-radius: 12px;
        padding: 20px 18px;
        box-shadow: 0 2px 5px rgba(15, 23, 42, 0.08);
    }

    div[data-testid="stMetric"] label {
        color: #334155 !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
    }

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-size: 2rem !important;
        font-weight: 750 !important;
    }

    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
        color: #334155 !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# API CONNECTION
# =========================================================

def check_backend():
    try:
        response = requests.get(
            f"{API_URL}/health",
            timeout=5,
        )

        if response.ok:
            return True, response.json()

        return False, response.text

    except requests.exceptions.RequestException as error:
        return False, str(error)

def get_documents():
    try:
        response = requests.get(
            f"{API_URL}/documents",
            timeout=15,
        )
        response.raise_for_status()
        return response.json(), None

    except requests.exceptions.RequestException as error:
        return [], str(error)


def get_chapters(document_id):
    try:
        response = requests.get(
            f"{API_URL}/documents/{document_id}/chapters",
            timeout=15,
        )
        response.raise_for_status()
        return response.json(), None

    except requests.exceptions.RequestException as error:
        return [], str(error)

# =========================================================
# KNOWLEDGE GRAPH VISUALIZATION
# =========================================================

def render_knowledge_graph(graph_data):

    nodes = {}
    edges = []

    node_colors = {
        "Document": "#2563eb",
        "Chapter": "#16a34a",
        "Chunk": "#d97706",
        "Concept": "#9333ea",
        "Other": "#64748b",
    }

    for index, item in enumerate(graph_data):

        source_name = item.get("source")
        target_name = item.get("target")

        source_labels = item.get("sourceLabels") or ["Other"]
        target_labels = item.get("targetLabels") or ["Other"]

        relationship = item.get("relationship", "RELATED")

        if not source_name or not target_name:
            continue

        source_type = source_labels[0]
        target_type = target_labels[0]

        # Include node type in ID to avoid collisions
        source_id = f"{source_type}::{source_name}"
        target_id = f"{target_type}::{target_name}"

        if source_id not in nodes:

            nodes[source_id] = {
                "id": source_id,
                "label": str(source_name),
                "title": (
                    f"Type: {source_type}\n"
                    f"Name: {source_name}"
                ),
                "group": source_type,
                "color": node_colors.get(
                    source_type,
                    node_colors["Other"],
                ),
                "shape": "dot",
                "size": 22,
                "font": {
                    "color": "#1e293b",
                    "size": 15,
                },
            }

        if target_id not in nodes:

            nodes[target_id] = {
                "id": target_id,
                "label": str(target_name),
                "title": (
                    f"Type: {target_type}\n"
                    f"Name: {target_name}"
                ),
                "group": target_type,
                "color": node_colors.get(
                    target_type,
                    node_colors["Other"],
                ),
                "shape": "dot",
                "size": 22,
                "font": {
                    "color": "#1e293b",
                    "size": 15,
                },
            }

        edges.append({
            "from": source_id,
            "to": target_id,
            "label": relationship,
            "arrows": "to",
            "color": {
                "color": "#64748b",
                "highlight": "#2563eb",
            },
            "font": {
                "size": 11,
                "color": "#334155",
                "align": "middle",
                "background": "#ffffff",
            },
        })

    nodes_json = json.dumps(
        list(nodes.values())
    ).replace("</", "<\\/")

    edges_json = json.dumps(
        edges
    ).replace("</", "<\\/")

    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>

        <style>
            body {
                margin: 0;
                padding: 0;
                font-family: Arial, sans-serif;
                background: #ffffff;
            }

            #network {
                width: 100%;
                height: 650px;
                border: 1px solid #cbd5e1;
                border-radius: 12px;
                background: #f8fafc;
            }

            .legend {
                display: flex;
                flex-wrap: wrap;
                gap: 18px;
                padding: 12px;
                margin-bottom: 10px;
                background: #f1f5f9;
                border-radius: 8px;
            }

            .legend-item {
                display: flex;
                align-items: center;
                gap: 7px;
                font-size: 13px;
                color: #1e293b;
            }

            .dot {
                width: 12px;
                height: 12px;
                border-radius: 50%;
                display: inline-block;
            }
        </style>
    </head>

    <body>

        <div class="legend">

            <div class="legend-item">
                <span class="dot" style="background:#2563eb"></span>
                Document
            </div>

            <div class="legend-item">
                <span class="dot" style="background:#16a34a"></span>
                Chapter
            </div>

            <div class="legend-item">
                <span class="dot" style="background:#d97706"></span>
                Chunk
            </div>

            <div class="legend-item">
                <span class="dot" style="background:#9333ea"></span>
                Concept
            </div>

        </div>

        <div id="network"></div>

        <script>

            const nodes = new vis.DataSet(NODES_DATA);
            const edges = new vis.DataSet(EDGES_DATA);

            const container = document.getElementById("network");

            const data = {
                nodes: nodes,
                edges: edges
            };

            const options = {

                interaction: {
                    hover: true,
                    dragNodes: true,
                    dragView: true,
                    zoomView: true,
                    navigationButtons: true,
                    keyboard: true
                },

                physics: {
                    enabled: true,
                    stabilization: {
                        iterations: 150
                    },
                    barnesHut: {
                        gravitationalConstant: -5000,
                        centralGravity: 0.25,
                        springLength: 150,
                        springConstant: 0.04
                    }
                },

                nodes: {
                    borderWidth: 2,
                    borderWidthSelected: 4
                },

                edges: {
                    width: 1.5,
                    smooth: {
                        type: "continuous"
                    }
                }
            };

            const network = new vis.Network(
                container,
                data,
                options
            );

            network.on("click", function(params) {

                if (params.nodes.length > 0) {

                    const node = nodes.get(params.nodes[0]);

                    const connected = network.getConnectedNodes(
                        params.nodes[0]
                    );

                    console.log("Selected node:", node);
                    console.log("Connected nodes:", connected);
                }

            });

        </script>

    </body>
    </html>
    """

    html_code = (
        html_code
        .replace("NODES_DATA", nodes_json)
        .replace("EDGES_DATA", edges_json)
    )

    components.html(
        html_code,
        height=730,
        scrolling=False,
    )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.title("🕸️ NetGraph-RAG")

    st.caption("Textbook Intelligence System")

    st.divider()

    st.subheader("Backend Status")

    backend_connected, backend_info = check_backend()

    if backend_connected:

        st.success("Backend connected")

        if isinstance(backend_info, dict):
            st.caption(
                f"Neo4j: {backend_info.get('neo4j', 'Unknown')}"
            )

    else:

        st.error("Backend disconnected")
        st.caption(str(backend_info))

    st.caption(f"API: {API_URL}")

    st.divider()

    st.subheader("Navigation")

    selected_page = st.radio(
        "Select module",
        [
            "💬 Ask the textbook",
            "📚 Document ingestion",
            "🕸️ Knowledge graph",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    if st.button(
        "🗑️ Clear conversation",
        use_container_width=True,
    ):

        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())

        st.rerun()

    st.caption("Hybrid Vector + Knowledge Graph RAG")


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div class="app-header">
        <h1>🕸️ NetGraph-RAG</h1>
        <p class="app-subtitle">
            Intelligent textbook question answering powered by
            vector retrieval, knowledge graphs and LangGraph.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# PAGE 1: CHAT
# =========================================================

if selected_page == "💬 Ask the textbook":

    st.subheader("Ask your textbook")

    st.caption(
        "Ask questions about the indexed textbook and explore "
        "answers supported by retrieved passages."
    )
    # -----------------------------------------------------
    # DOCUMENT SELECTION
    # -----------------------------------------------------

    documents, document_error = get_documents()

    if document_error:
        st.error(f"Could not load documents: {document_error}")
        documents = []

    documents_by_id = {
        document["document_id"]: document
        for document in documents
    }

    selected_document_id = st.selectbox(
        "Select document",
        options=[None] + list(documents_by_id.keys()),
        format_func=lambda document_id: (
            "All documents"
            if document_id is None
            else documents_by_id[document_id].get(
                "title",
                document_id,
            )
        ),
        key="selected_document",
    )

    # -----------------------------------------------------
    # CHAPTER SELECTION
    # -----------------------------------------------------

    selected_chapter_id = None

    if selected_document_id is not None:

        chapters, chapter_error = get_chapters(
            selected_document_id
        )

        if chapter_error:
            st.error(f"Could not load chapters: {chapter_error}")
            chapters = []

        chapters_by_id = {
            chapter["chapter_id"]: chapter
            for chapter in chapters
        }

        selected_chapter_id = st.selectbox(
            "Select chapter",
            options=[None] + list(chapters_by_id.keys()),
            format_func=lambda chapter_id: (
                "All chapters"
                if chapter_id is None
                else (
                    f"Chapter "
                    f"{chapters_by_id[chapter_id].get('chapter_number', '')}: "
                    f"{chapters_by_id[chapter_id].get('title', chapter_id)}"
                )
            ),
            key="selected_chapter",
        )

    else:
        st.caption(
            "Select a document to filter questions by chapter."
        )

    # -----------------------------------------------------
    # RESET CHAT WHEN SCOPE CHANGES
    # -----------------------------------------------------

    current_scope = (
        selected_document_id,
        selected_chapter_id,
    )

    if st.session_state.get("active_scope") != current_scope:

        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.active_scope = current_scope

    st.divider()

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])

            if message["role"] == "assistant":

                sources = message.get("sources", [])

                if sources:

                    with st.expander(
                        f"📖 Sources ({len(sources)})"
                    ):

                        for i, source in enumerate(
                            sources,
                            start=1,
                        ):

                            chapter = source.get(
                                "chapter_title",
                                source.get(
                                    "chapter",
                                    "Unknown chapter",
                                ),
                            )

                            section = source.get("section") or "N/A"

                            start_page = source.get(
                                "start_printed_page"
                            )

                            end_page = source.get(
                                "end_printed_page"
                            )

                            if start_page is not None:

                                if (
                                    end_page is not None
                                    and end_page != start_page
                                ):
                                    pages = f"{start_page}-{end_page}"
                                else:
                                    pages = str(start_page)

                            else:

                                start_pdf = source.get(
                                    "start_pdf_page"
                                )

                                end_pdf = source.get(
                                    "end_pdf_page"
                                )

                                pages = (
                                    f"PDF {start_pdf}-{end_pdf}"
                                    if start_pdf is not None
                                    else "Unavailable"
                                )

                            st.markdown(
                                f"""
                                **Source {i}**

                                - Chapter: {chapter}
                                - Section: {section}
                                - Pages: {pages}
                                - Chunk ID: `{source.get('id', source.get('chunk_id', 'N/A'))}`
                                """
                            )

                            source_text = source.get("text")

                            if source_text:

                                with st.expander("View passage"):
                                    st.write(source_text)

                            st.divider()

    question = st.chat_input(
        "Ask a question about your textbook..."
    )

    if question:

        st.session_state.messages.append({
            "role": "user",
            "content": question,
        })

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):

            with st.spinner(
                "Searching vector database and knowledge graph..."
            ):

                try:

                    response = requests.post(
                        f"{API_URL}/query",
                        json={
                            "question": question,
                            "thread_id": st.session_state.thread_id,
                            "document_id": selected_document_id,
                            "chapter_id": selected_chapter_id,
                        },
                        timeout=300,
                    )

                    if response.ok:

                        data = response.json()

                        answer = data.get(
                            "answer",
                            "No answer was returned.",
                        )

                        sources = data.get("sources", [])

                        st.markdown(answer)

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer,
                            "sources": sources,
                        })

                        if sources:

                            with st.expander(
                                f"📖 Retrieved sources ({len(sources)})"
                            ):

                                for i, source in enumerate(
                                    sources,
                                    start=1,
                                ):

                                    st.markdown(f"**Source {i}**")

                                    st.write(
                                        "Chapter:",
                                        source.get(
                                            "chapter_title",
                                            "Unknown",
                                        ),
                                    )

                                    st.write(
                                        "Section:",
                                        source.get("section", "N/A"),
                                    )

                                    st.write(
                                        "Printed pages:",
                                        source.get(
                                            "start_printed_page",
                                            "N/A",
                                        ),
                                        "-",
                                        source.get(
                                            "end_printed_page",
                                            "N/A",
                                        ),
                                    )

                                    if source.get("text"):

                                        with st.expander(
                                            "View retrieved text"
                                        ):
                                            st.write(source["text"])

                                    st.divider()

                    else:

                        error_message = (
                            f"API error: {response.status_code}\n\n"
                            f"{response.text}"
                        )

                        st.error(error_message)

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_message,
                            "sources": [],
                        })

                except requests.exceptions.RequestException as error:

                    error_message = (
                        f"Backend connection failed: {error}"
                    )

                    st.error(error_message)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_message,
                        "sources": [],
                    })


# =========================================================
# PAGE 2: DOCUMENT INGESTION
# =========================================================

elif selected_page == "📚 Document ingestion":

    st.subheader("📚 Document ingestion")

    st.write(
        "Upload a networking textbook in PDF format "
        "to extract, chunk, embed and index its content."
    )

    uploaded_file = st.file_uploader(
        "Choose a PDF textbook",
        type=["pdf"],
    )

    if uploaded_file:

        st.info(f"Selected file: {uploaded_file.name}")

        st.write(
            f"File size: "
            f"{uploaded_file.size / (1024 * 1024):.2f} MB"
        )

        if st.button(
            "🚀 Start ingestion",
            type="primary",
            use_container_width=True,
        ):

            progress = st.status(
                "Processing document...",
                expanded=True,
            )

            progress.write("Uploading PDF to backend...")

            try:

                response = requests.post(
                    f"{API_URL}/documents/upload",
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "application/pdf",
                        )
                    },
                    timeout=1800,
                )

                if response.ok:

                    progress.update(
                        label="Ingestion completed!",
                        state="complete",
                    )

                    st.success(
                        "Document successfully processed."
                    )

                    st.json(response.json())

                else:

                    progress.update(
                        label="Ingestion failed",
                        state="error",
                    )

                    st.error(response.text)

            except requests.exceptions.RequestException as error:

                progress.update(
                    label="Backend connection failed",
                    state="error",
                )

                st.error(str(error))


# =========================================================
# PAGE 3: KNOWLEDGE GRAPH
# =========================================================

elif selected_page == "🕸️ Knowledge graph":

    st.subheader("🕸️ Knowledge graph explorer")

    st.write(
        "Explore the entities and relationships stored "
        "in your Neo4j knowledge graph."
    )

    if st.button(
        "🔄 Load graph data",
        type="primary",
    ):

        with st.spinner("Fetching graph data..."):

            try:

                response = requests.get(
                    f"{API_URL}/graph",
                    timeout=60,
                )

                if response.ok:

                    st.session_state.graph_data = response.json()

                else:

                    st.error(response.text)

            except requests.exceptions.RequestException as error:

                st.error(
                    f"Backend connection failed: {error}"
                )

    graph_data = st.session_state.graph_data

    if graph_data is not None:

        # Calculate unique nodes using both type and name
        unique_nodes = set()

        relationship_types = set()

        for item in graph_data:

            source = item.get("source")
            target = item.get("target")

            source_labels = item.get("sourceLabels") or ["Other"]
            target_labels = item.get("targetLabels") or ["Other"]

            if source:
                unique_nodes.add(
                    (source_labels[0], source)
                )

            if target:
                unique_nodes.add(
                    (target_labels[0], target)
                )

            if item.get("relationship"):
                relationship_types.add(
                    item["relationship"]
                )

        st.success(
            f"Loaded {len(graph_data)} relationships"
        )

        # METRIC CARDS
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="Relationships",
                value=len(graph_data),
            )

        with col2:
            st.metric(
                label="Unique Nodes",
                value=len(unique_nodes),
            )

        with col3:
            st.metric(
                label="Relationship Types",
                value=len(relationship_types),
            )

        st.divider()

        # INTERACTIVE GRAPH
        st.subheader("Interactive graph visualization")

        st.caption(
            "Drag nodes to rearrange the graph. "
            "Zoom and pan to explore. Click a node to inspect it."
        )

        if graph_data:

            render_knowledge_graph(graph_data)

        else:

            st.info("No graph relationships available.")

        st.divider()

        # RELATIONSHIP TABLE
        st.subheader("Relationship data")

        if graph_data:

            st.dataframe(
                graph_data,
                use_container_width=True,
                hide_index=True,
            )

            st.download_button(
                "⬇️ Download graph data as JSON",
                data=json.dumps(
                    graph_data,
                    indent=4,
                    ensure_ascii=False,
                ),
                file_name="netgraph_relationships.json",
                mime="application/json",
            )

        st.divider()

        # RELATIONSHIP TYPE SUMMARY
        st.subheader("Relationship summary")

        if relationship_types:

            for relationship in sorted(relationship_types):

                count = sum(
                    1
                    for item in graph_data
                    if item.get("relationship") == relationship
                )

                st.write(
                    f"**{relationship}** — {count} relationships"
                )


    else:

        st.info(
            "Click 'Load graph data' to retrieve "
            "relationships from Neo4j."
        )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "NetGraph-RAG | Hybrid Retrieval | Neo4j | LangGraph | FastAPI"
)
