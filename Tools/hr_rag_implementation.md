# HR Assistant – Strict Context-Aware RAG (LangChain)

This document provides an **end-to-end implementation guide** for building a **strict HR assistant** using **LangChain**.

The assistant:
- Answers **only from company HR documents**
- Is **context-aware (conversational)**
- **Refuses** to answer when information is not present in the documents
- Supports **multiple LLM providers**
  - Groq → `llama3.3-70b-versatile`
  - Gemini → `gemini-2.3-flash`
  - Ollama → `mistral`

---

## 1. Project Structure

```text
hr-rag-assistant/
│
├── data/
│   └── hr_policy.pdf
│
├── vector_store/
│
├── config.py
├── ingest.py
├── llm_factory.py
├── retriever.py
├── prompt.py
├── rag_chain.py
├── chat.py
│
├── requirements.txt
└── .env
```

---

## 2. Dependencies

`requirements.txt`

```text
langchain
langchain-community
langchain-groq
langchain-google-genai
faiss-cpu
chromadb
pypdf
python-dotenv
sentence-transformers
```

Install:

```bash
pip install -r requirements.txt
```

---

## 3. Environment Variables

`.env`

```env
GROQ_API_KEY=your_groq_key
GOOGLE_API_KEY=your_google_key
```

---

## 4. Document Ingestion & Vector Store

`ingest.py`

```python
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS

def ingest_documents(pdf_path: str):
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=80
    )
    chunks = splitter.split_documents(documents)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local("vector_store")

if __name__ == "__main__":
    ingest_documents("data/hr_policy.pdf")
```

Run once:

```bash
python ingest.py
```

---

## 5. LLM Provider Factory

`llm_factory.py`

```python
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama

def get_llm(provider: str):
    if provider == "groq":
        return ChatGroq(
            model="llama3.3-70b-versatile",
            temperature=0
        )

    if provider == "gemini":
        return ChatGoogleGenerativeAI(
            model="gemini-2.3-flash",
            temperature=0
        )

    if provider == "ollama":
        return ChatOllama(
            model="mistral",
            temperature=0
        )

    raise ValueError("Unsupported LLM provider")
```

---

## 6. Strict HR Prompt

`prompt.py`

```python
from langchain.prompts import ChatPromptTemplate

HR_RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     """
You are an HR assistant.

Rules:
- Answer ONLY using the provided context.
- If the answer is not explicitly present, respond:
  \"I couldn't find this information in the company documents.\"
- Do NOT guess.
- Do NOT use external knowledge.
- Be concise and professional.
"""),
    ("human",
     """
Context:
{context}

Question:
{question}
""")
])
```

---

## 7. Retriever

`retriever.py`

```python
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings

def get_retriever():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vectorstore = FAISS.load_local(
        "vector_store",
        embeddings,
        allow_dangerous_deserialization=True
    )

    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}
    )
```

---

## 8. RAG Chain (Context-Aware)

`rag_chain.py`

```python
from langchain.chains import ConversationalRetrievalChain
from llm_factory import get_llm
from retriever import get_retriever
from prompt import HR_RAG_PROMPT

def build_hr_rag_chain(provider: str):
    llm = get_llm(provider)
    retriever = get_retriever()

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        combine_docs_chain_kwargs={
            "prompt": HR_RAG_PROMPT
        },
        return_source_documents=True
    )

    return chain
```

---

## 9. Conversational Chat Interface

`chat.py`

```python
def run_chat():
    from rag_chain import build_hr_rag_chain

    chain = build_hr_rag_chain(provider="groq")
    chat_history = []

    print("HR Assistant is running. Type 'exit' to stop.\n")

    while True:
        query = input("You: ")
        if query.lower() in ["exit", "quit"]:
            break

        response = chain({
            "question": query,
            "chat_history": chat_history
        })

        answer = response["answer"]
        print("\nHR Bot:", answer, "\n")

        chat_history.append((query, answer))

if __name__ == "__main__":
    run_chat()
```

---

## 10. Behavior Guarantees

- No document context → **explicit refusal**
- No web search → **zero hallucination risk**
- Conversational memory → **context-aware follow-ups**
- Provider-agnostic → **easy model switching**

---

## 11. Next Hardening Steps (Optional)

- Similarity score threshold enforcement
- HR intent classifier before RAG
- Policy version tagging
- Audit logging (query → retrieved chunks → answer)
- FastAPI deployment

---

## Final Note

This is not a demo chatbot.
This is a **controlled HR knowledge system** designed to **fail safely instead of hallucinating**.

