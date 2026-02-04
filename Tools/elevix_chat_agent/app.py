import streamlit as st
import sys
import os
from dotenv import load_dotenv
import tempfile

# ------------------------------------------------------------------------------
# 1. Path Configuration
# ------------------------------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
rag_dir = os.path.join(project_root, "elevix_rag")

if rag_dir not in sys.path:
    sys.path.append(rag_dir)

# ------------------------------------------------------------------------------
# 2. Environment Setup
# ------------------------------------------------------------------------------
load_dotenv(os.path.join(current_dir, ".env"))
load_dotenv(os.path.join(rag_dir, ".env"))

# ------------------------------------------------------------------------------
# 3. Imports
# ------------------------------------------------------------------------------
from src.agent import ElevixAgent
from src.adapters import RAGToolAdapter, WebSearchToolAdapter
from llm_factory import get_llm
from ingest import ingest_documents

# ------------------------------------------------------------------------------
# 4. Page Configuration
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Ray",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------------------------
# 5. Custom CSS
# ------------------------------------------------------------------------------
st.markdown("""
<style>
    /* Main container styling */
    .main {
        padding: 2rem;
    }
    
    /* Header styling */
    .stTitle {
        color: #2c3e50;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    
    /* Chat message styling */
    .stChatMessage {
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    /* Sources expander */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #34495e;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        padding: 2rem 1rem;
    }
    
    /* Success/Info boxes */
    .element-container div[data-testid="stMarkdownContainer"] p {
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 6. Session State Initialization
# ------------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ------------------------------------------------------------------------------
# 7. Sidebar - Configuration & Document Upload
# ------------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Configuration")
    
    # LLM Provider Selection
    provider_options = ["groq", "olla", "gemini"] 
    provider_map = {
        "Groq (Fastest)": "groq",
        "Ollama (Local)": "ollama",
        "Gemini (Google)": "gemini"
    }
    
    selected_provider_label = st.selectbox(
        "Select LLM Provider",
        list(provider_map.keys()),
        index=0
    )
    selected_provider = provider_map[selected_provider_label]

    # Model Selection based on Provider
    selected_model = None
    if selected_provider == "groq":
        model_options = {
            "Llama 3.3 70B (Versatile)": "llama-3.3-70b-versatile",
            "Llama 3 8B (Fast)": "llama3-8b-8192",
            "Mixtral 8x7B": "mixtral-8x7b-32768"
        }
        selected_model_label = st.selectbox("Select Model", list(model_options.keys()), index=0)
        selected_model = model_options[selected_model_label]
        
    elif selected_provider == "gemini":
        model_options = {
            "Gemini 2.5 Flash": "gemini-2.5-flash",
            "Gemini 2.0 Flash": "gemini-2.0-flash",
            "Gemini 1.5 Pro": "gemini-1.5-pro"
        }
        selected_model_label = st.selectbox("Select Model", list(model_options.keys()), index=0)
        selected_model = model_options[selected_model_label]
        
    elif selected_provider == "ollama":
        # For Ollama we could list models, but sticking to default for now or simple input
        selected_model = st.text_input("Model Name", value="mistral")

    # Re-initialize agent if provider OR model changes
    config_key = f"{selected_provider}:{selected_model}"
    
    if "current_config" not in st.session_state:
        st.session_state.current_config = config_key
        
    if st.session_state.current_config != config_key:
        st.session_state.current_config = config_key
        st.session_state.agent_ready = False # Force re-init 
        st.rerun()

    if not st.session_state.get("agent_ready", False):
        with st.spinner(f"Initializing Ray with {selected_provider_label} ({selected_model})..."):
            try:
                if "rag_tool" not in st.session_state:
                     # Initialize tools once or re-init if needed? 
                     # RAG tool might need provider context if it uses LLM internally (it does for embeddings? No, embeddings are usually local or specific)
                     # But RAGToolAdapter takes `provider` in constructor.
                     st.session_state.rag_tool = RAGToolAdapter(provider=selected_provider)
                     st.session_state.web_tool = WebSearchToolAdapter()
                
                # Re-create LLM and Agent
                llm = get_llm(selected_provider, model_name=selected_model)
                st.session_state.agent = ElevixAgent(rag_tool=st.session_state.rag_tool, web_search_tool=st.session_state.web_tool, llm=llm)
                st.session_state.agent_ready = True
                st.success(f"Agent ready!")
            except Exception as e:
                st.error(f"Failed to initialize agent: {e}")
                st.session_state.agent_ready = False

    st.markdown("---")
    st.title("📁 Document Management")
    
    uploaded_file = st.file_uploader(
        "Upload HR Documents",
        type=["pdf"],
        help="Upload PDF documents to add to the knowledge base"
    )
    
    if uploaded_file is not None:
        if st.button("🚀 Ingest Document", use_container_width=True):
            with st.spinner("Processing document..."):
                try:
                    # Save uploaded file to temp location
                    upload_dir = os.path.join(rag_dir, "data", "uploaded")
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    file_path = os.path.join(upload_dir, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Ingest the document
                    ingest_documents(input_path=file_path)
                    
                    st.success(f"✅ Successfully ingested: {uploaded_file.name}")
                except Exception as e:
                    st.error(f"❌ Ingestion failed: {e}")
    
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.info("""
    **Ray** is your conversational HR assistant.
    
    - 📚 Ask HR policy questions
    - 🌐 Get general facts via web search
    - 💬 Engage in casual conversation
    """)
    
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ------------------------------------------------------------------------------
# 8. Main Content - Chat Interface
# ------------------------------------------------------------------------------
st.title("🤖 Ray")
st.markdown("Your intelligent HR assistant with document knowledge and web access")
st.markdown("---")

# Check if agent is ready
if not st.session_state.agent_ready:
    st.error("⚠️ Agent is not ready. Please check your configuration and restart the app.")
    st.stop()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Display sources if available
        if "sources" in message and message["sources"]:
            with st.expander("📄 View Sources"):
                for i, source in enumerate(message["sources"], 1):
                    if "file" in source:
                        # RAG source
                        st.markdown(f"**{i}. {source['file']}** (Page {source.get('page', 'N/A')})")
                        st.caption(source.get('content', ''))
                    elif "url" in source:
                        # Web search source
                        st.markdown(f"**{i}. [{source['title']}]({source['url']})**")
                        st.caption(source.get('snippet', ''))
                    st.markdown("---")

# Chat input
if prompt := st.chat_input("Ask me anything..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response_data = st.session_state.agent.handle_query(prompt)
                response_text = response_data.get("content", "")
                sources = response_data.get("sources", [])
                
                st.markdown(response_text)
                
                # Display sources
                if sources:
                    with st.expander("📄 View Sources"):
                        for i, source in enumerate(sources, 1):
                            if "file" in source:
                                # RAG source
                                st.markdown(f"**{i}. {source['file']}** (Page {source.get('page', 'N/A')})")
                                st.caption(source.get('content', ''))
                            elif "url" in source:
                                # Web search source
                                st.markdown(f"**{i}. [{source['title']}]({source['url']})**")
                                st.caption(source.get('snippet', ''))
                            st.markdown("---")
                
                # Add assistant message to chat
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "sources": sources
                })
                
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "sources": []
                })

# ------------------------------------------------------------------------------
# 9. Footer
# ------------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #7f8c8d; padding: 1rem;'>"
    "Powered by Ray | RAG + Web Search"
    "</div>",
    unsafe_allow_html=True
)
