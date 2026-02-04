from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from config import Config
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from typing import List

# Singleton instance holder
_global_retriever = None

class UnifiedRetriever(BaseRetriever):
    vectorstore: FAISS
    k: int = 5
    
    def reload_vectorstore(self):
        """Reloads the vectorstore from disk."""
        print("DEBUG: Reloading vectorstore from disk...")
        try:
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            new_vs = FAISS.load_local(
                Config.VECTOR_STORE_PATH,
                embeddings,
                allow_dangerous_deserialization=True
            )
            self.vectorstore = new_vs
            print("DEBUG: Vectorstore reloaded successfully.")
        except Exception as e:
            print(f"DEBUG: Failed to reload vectorstore: {e}")
            # If reload fails (e.g. index deleted), we might want to handle it.
            # For now, we log error.

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun = None
    ) -> List[Document]:
        # 8. Retrieval Logic: Prefer schema docs first, then content docs
        
        # Try to use metadata filter, fallback to post-processing if not supported
        schema_docs = []
        try:
            # 1. Search for schema documents (top 2) with filter
            schema_docs = self.vectorstore.similarity_search(
                query, 
                k=2, 
                filter={"type": "schema"}
            )
        except (TypeError, ValueError):
            # FAISS may not support filters, fallback to post-retrieval filtering
            all_docs = self.vectorstore.similarity_search(query, k=10)
            schema_docs = [d for d in all_docs if d.metadata.get("type") == "schema"][:2]
        
        # 2. Search for general content (top K)
        content_docs = self.vectorstore.similarity_search(
            query,
            k=self.k
        )
        
        # Combine: Schema docs first, then content (avoid duplicates)
        seen_contents = set()
        final_docs = []
        
        for doc in schema_docs:
            if doc.page_content not in seen_contents:
                final_docs.append(doc)
                seen_contents.add(doc.page_content)
                
        for doc in content_docs:
            if doc.page_content not in seen_contents:
                final_docs.append(doc)
                seen_contents.add(doc.page_content)
        
        return final_docs[:self.k+1]

def get_retriever():
    global _global_retriever
    
    if _global_retriever is not None:
        return _global_retriever
        
    print("DEBUG: Initializing Global Retriever")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    print("DEBUG: Embeddings initialized")

    try:
        vectorstore = FAISS.load_local(
            Config.VECTOR_STORE_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
        print("DEBUG: FAISS loaded successfully")
    except Exception as e:
        print(f"DEBUG: Failed to load FAISS: {e}. Creating empty store.")
        # Create empty store to prevent crash if index missing
        from langchain_core.documents import Document
        vectorstore = FAISS.from_documents(
            [Document(page_content="Empty Store", metadata={"source": "system"})], 
            embeddings
        )

    print("DEBUG: Instantiating UnifiedRetriever")
    try:
        _global_retriever = UnifiedRetriever(vectorstore=vectorstore, k=5)
        print("DEBUG: UnifiedRetriever instantiated")
        return _global_retriever
    except Exception as e:
        print(f"DEBUG: Failed to instantiate UnifiedRetriever: {e}")
        import traceback
        traceback.print_exc()
        raise e

def reload_retriever():
    """Helper to reload the global retriever's vectorstore"""
    global _global_retriever
    if _global_retriever:
        _global_retriever.reload_vectorstore()
    else:
        # If not initialized, get_retriever() will load fresh likely
        get_retriever()
