# HR RAG Assistant

A strict, context-aware HR assistant using LangChain and RAG.

## Features
- **Strict Context**: Answers only from provided HR documents.
- **Provider Agnostic**: Supports Groq, Gemini, and Ollama.
- **Privacy**: Local vector store using FAISS.

## Setup

1. **Clone/Navigate** to the `elevix_rag` directory.
2. **Create Virtual Environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure Environment**:
   - Rename `.env.example` to `.env`.
   - specific API keys in `.env`.

## Usage

1. **Prepare Data**:
   - Place `hr_policy.pdf` in `data/` folder.
   - Or generate mock data:
     ```bash
     python mock_data_gen.py
     ```

2. **Ingest Documents**:
   ```bash
   python ingest.py
   ```

3. **Run Chat**:
   ```bash
   python chat.py
   ```
   Select your LLM provider when prompted.

## Architecture
- `ingest.py`: Loads PDF, splits text, creates FAISS index.
- `retriever.py`: Loads FAISS index.
- `rag_chain.py`: Connects LLM + Retriever + Strict Prompt.
- `chat.py`: User interface.
