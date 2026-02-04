import os
import glob
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from elevix_rag.config import Config
from elevix_rag.loaders import UnifiedLoader

def ingest_documents(input_path=None, vector_store_path=None):
    """
    Ingest documents from a file or directory into a FAISS vector store.
    Follows Unified File Ingestion Strategy.
    """
    data_path = input_path or Config.DATA_PATH
    store_path = vector_store_path or Config.VECTOR_STORE_PATH
    
    # Initialize the unified loader
    loader = UnifiedLoader()
    all_documents = []

    # 2. Unified File Ingestion Strategy: File -> Loader -> Normalized Documents
    if os.path.isdir(data_path):
        print(f"Scanning directory: {data_path}...")
        # Supported extensions
        extensions = {'.pdf', '.docx', '.csv', '.xlsx', '.xls', '.txt', '.text', '.md', '.html', '.htm'}
        
        for root, dirs, files in os.walk(data_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in extensions:
                    file_path = os.path.join(root, file)
                    print(f"Loading {file_path}...")
                    all_documents.extend(loader.load(file_path))
    elif os.path.isfile(data_path):
        print(f"Loading document from file: {data_path}...")
        all_documents.extend(loader.load(data_path))
    else:
        print(f"Error: Path not found at {data_path}")
        return

    if not all_documents:
        print("No documents were loaded or found.")
        return

    print(f"Loaded {len(all_documents)} initial document segments.")

    # 5. Chunking Rules (Do NOT improvise)
    # - Tables: No chunking across rows (handled in loaders.py)
    # - Text: 500-1000 tokens
    # - Headed docs: One section per chunk (handled in loaders.py)
    
    final_chunks = []
    
    # Use 800-1000 chars as proxy for tokens if Tiktoken is not available,
    # or just use RecursiveCharacterTextSplitter which is standard.
    # We only apply this to documents that are not rows or schemas and are too large.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        add_start_index=True,
    )

    for doc in all_documents:
        # Check if it's a table row or schema (should not be chunked further)
        is_table_data = "row_index" in doc.metadata or doc.metadata.get("type") == "schema"
        
        # If it's a heading-based section (DOCX, MD), it's already one semantic unit.
        # But if the section is huge, we might still want to split it while keeping metadata.
        # However, "Never chunk across: rows, headings, sections" is strict.
        
        if is_table_data:
            final_chunks.append(doc)
        else:
            # For unstructured text (PDF, TXT, HTML, or large DOCX/MD chunks)
            if len(doc.page_content) > 1200:
                print(f"Splitting large content from {doc.metadata.get('source_file')} ({len(doc.page_content)} chars)")
                chunks = text_splitter.split_documents([doc])
                final_chunks.extend(chunks)
            else:
                final_chunks.append(doc)

    print(f"Final chunk count: {len(final_chunks)}")

    # 7. Embeddings & Storage
    print("Creating/Updating embeddings and vector store...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    try:
        # Mixed documents are allowed in single index
        if os.path.exists(os.path.join(store_path, "index.faiss")):
            print(f"Loading existing vector store from {store_path}...")
            vectorstore = FAISS.load_local(store_path, embeddings, allow_dangerous_deserialization=True)
            print("Adding new documents to existing store...")
            vectorstore.add_documents(final_chunks)
        else:
            print("Creating new vector store...")
            vectorstore = FAISS.from_documents(final_chunks, embeddings)
    except Exception as e:
        print(f"Warning: Could not load/update existing store ({e}). Creating new one...")
        vectorstore = FAISS.from_documents(final_chunks, embeddings)
    
    vectorstore.save_local(store_path)
    print(f"Vector store saved to {store_path}")

if __name__ == "__main__":
    ingest_documents()
