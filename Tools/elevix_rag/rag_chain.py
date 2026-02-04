from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from llm_factory import get_llm
from retriever import get_retriever
from prompt import ELEVIX_RAG_PROMPT

def format_docs(docs):
    """Format retrieved documents into context string."""
    formatted = []
    for i, doc in enumerate(docs, 1):
        metadata = doc.metadata
        source = metadata.get('source_file', 'Unknown')
        section = metadata.get('section_heading') or metadata.get('section') or metadata.get('page_number', 'N/A')
        formatted.append(f"[Document {i}]\nSource: {source}\nSection: {section}\nContent: {doc.page_content}\n")
    return "\n---\n".join(formatted)

def build_hr_rag_chain(provider: str):
    """
    Build a RAG chain using LCEL (LangChain Expression Language).
    Returns a chain that accepts {"question": str, "chat_history": list}.
    """
    llm = get_llm(provider)
    
    try:
        retriever = get_retriever()
    except Exception as e:
        print(f"Error loading retriever: {e}")
        print("Ensure you have run ingest.py first.")
        raise e
    
    # Build the chain using LCEL
    # Chain flow: question -> retriever -> format_docs -> prompt -> llm -> parse
    chain = (
        {
            "context": lambda x: format_docs(retriever.get_relevant_documents(x["question"])),
            "question": lambda x: x["question"]
        }
        | ELEVIX_RAG_PROMPT
        | llm
        | StrOutputParser()
    )
    
    # Wrapper to match the old interface and include source documents
    def invoke_with_sources(inputs):
        question = inputs["question"]
        # Get source documents
        source_docs = retriever.get_relevant_documents(question)
        # Get answer
        answer = chain.invoke({"question": question})
        return {
            "answer": answer,
            "source_documents": source_docs
        }
    
    # Return a simple callable that mimics the old chain interface
    class ChainWrapper:
        def invoke(self, inputs):
            return invoke_with_sources(inputs)
    
    return ChainWrapper()
