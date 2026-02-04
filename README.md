# Ray

**Ray** is a conversational HR assistant designed to help with policy questions, document ingestion, and general information retrieval.

## Features
- **HR Policy RAG**: Accurate answers from specific HR documents using Retrieval Augmented Generation.
- **Web Search**: General knowledge retrieval using privacy-focused search tools.
- **Document Ingestion**: Seamlessly upload and process PDF documents to expand the knowledge base.
- **Multi-LLM Support**: Configurable to use Groq, Ollama (local), or Gemini models.

## Usage
1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Application**:
    ```bash
    streamlit run Tools/elevix_chat_agent/app.py
    ```

3.  **Interact**:
    - Select your preferred LLM provider.
    - Upload HR documents in the sidebar.
    - Ask questions about policies or general topics.

## Project Structure
- `Tools/elevix_chat_agent`: Main Streamlit application and agent logic.
- `Tools/elevix_rag`: RAG system core implementation.
- `requirements.txt`: Consolidated project dependencies.

## License
Proprietary.
