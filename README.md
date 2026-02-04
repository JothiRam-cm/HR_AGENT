# Ray - Intelligent HR Agent

**Ray** is a sophisticated, AI-powered HR assistant designed to streamline access to human resources information. It leverages **Retrieval Augmented Generation (RAG)** to provide accurate answers from your organization's internal documents and connects to the web for broader knowledge.

System Architecture: **FastAPI** (Backend) + **Streamlit** (Frontend) + **LangChain** (Orchestration).

---

## 🚀 Key Features

*   **📚 RAG for HR Documents**: Upload and ingest PDF, DOCX, CSV, Excel, and Markdown files. Ray remembers and can cite specific rows, pages, or sections.
*   **🌐 Smart Web Search**: Integrated privacy-focused web search (using DuckDuckGo) for questions outside internal policy.
*   **🧠 Multi-LLM Support**: flexible backend supporting:
    *   **Groq** (Llama 3, Mixtral) - High speed.
    *   **Ollama** (Local models like Mistral) - Privacy and offline capability.
    *   **Gemini** (Google) - High context window.
*   **🔐 User & Admin Roles**:
    *   **User**: Chat, history management.
    *   **Admin**: File ingestion, vector database management, system reset.
*   **🎨 Modern UI**: Sleek Streamlit interface with dark mode, sticky headers, and citation expansion.

---

## 📂 Project Structure

The project is organized into modular tools:

```text
d:\projects\HR_AGENT
├── README.md               # This documentation
├── requirements.txt        # Python dependencies
└── Tools
    ├── elevix_chat_agent   # Core Application (UI & API)
    │   ├── app.py          # Application Entry point / Logic
    │   ├── api.py          # FastAPI Backend Server
    │   ├── streamlit_app.py# Streamlit Frontend Interface
    │   └── src/            # Agent logic, Memory, Adapters
    ├── elevix_rag          # RAG Engine
    │   ├── loaders.py      # Universal File Loaders (PDF, Excel, etc.)
    │   ├── retriever.py    # Vector Store & Search Logic
    │   └── ingest.py       # Document Processing Script
    └── elevix_wesearch     # Web Search Experiments & Utilities
```

---

## 🛠️ Usage & Installation

### 1. Prerequisites
*   Python 3.10+
*   A virtual environment is recommended.

### 2. Setup
Install the required dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configuration
Ensure you have `.env` files set up in `Tools/elevix_chat_agent` and `Tools/elevix_rag` with necessary API keys (Groq, Google, etc.).

### 4. Running the Application
The easiest way to start the entire system (Backend API + Frontend UI) is using the launcher script:

**Windows**:
```bat
Tools\elevix_chat_agent\run_app.bat
```
*(This will launch the FastAPI backend on port 8000 and the Streamlit UI on port 8501)*

Alternatively, you can run them separately:
*   **Backend**: `Tools\elevix_chat_agent\start_backend.bat`
*   **Frontend**: `Tools\elevix_chat_agent\start_frontend.bat`

---

## 🤖 Interacting with Ray

1.  **Login/Register**: Create an account or use Admin credentials to access the system.
2.  **Select Provider**: Choose your preferred LLM (Groq, Ollama, Gemini) from the sidebar.
3.  **Upload Docs (Admin)**: Use the Admin Console to ingest HR policies, handbooks, or employee data.
4.  **Chat**: Ask questions like:
    *   *"What is the severance policy?"* (Uses RAG)
    *   *"What are the current labor laws in California?"* (Uses Web Search)

---

## � License
Proprietary. High-Performance Agentic Workflow.