import streamlit as st
import requests
import time
from pathlib import Path
from dotenv import load_dotenv
import os

# Load env
load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Ray - Intelligent HR", 
    page_icon="🟢", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS ---
def load_css():
    css_file = Path(__file__).parent / "styles_dark.css"
    if css_file.exists():
        with open(css_file, encoding='utf-8') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# --- STATE ---
if "token" not in st.session_state: st.session_state.token = None
if "role" not in st.session_state: st.session_state.role = None
if "full_name" not in st.session_state: st.session_state.full_name = None
if "user_id" not in st.session_state: st.session_state.user_id = None
if "messages" not in st.session_state: st.session_state.messages = []
if "session_id" not in st.session_state: st.session_state.session_id = None

# --- API HELPERS ---
def api_login(email, password):
    try:
        resp = requests.post(f"{API_URL}/auth/login", json={"email": email, "password": password})
        if resp.status_code == 200: return resp.json()
    except: pass
    return None

def api_register(email, password, full_name):
    try:
        resp = requests.post(f"{API_URL}/auth/register", json={"email": email, "password": password, "full_name": full_name})
        if resp.status_code == 200: return resp.json()
    except: pass
    return None

def api_admin_login(username, password):
    try:
        resp = requests.post(f"{API_URL}/admin/login", json={"username": username, "password": password})
        if resp.status_code == 200: return resp.json()
    except: pass
    return None

def api_get_chats(token):
    try:
        resp = requests.get(f"{API_URL}/user/chats", headers={"Authorization": f"Bearer {token}"})
        if resp.status_code == 200: return resp.json().get("conversations", [])
    except: pass
    return []

# --- VIEWS ---

def auth_view():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; color: #00ff41;'>RAY SYSTEM ACCESS</h1>", unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["USER LOGIN", "REGISTER", "ADMIN ACCESS"])
        
        with tab1:
            email = st.text_input("EMAIL", key="l_email")
            password = st.text_input("PASSWORD", type="password", key="l_pass")
            if st.button("AUTHENTICATE", key="btn_login", use_container_width=True):
                data = api_login(email, password)
                if data:
                    st.session_state.token = data["access_token"]
                    st.session_state.role = data["role"]
                    st.session_state.full_name = data["full_name"]
                    st.session_state.user_id = data["user_id"]
                    st.session_state.messages = [] # Reset on login
                    st.rerun()
                else:
                    st.error("ACCESS DENIED")

        with tab2:
            r_name = st.text_input("FULL NAME")
            r_email = st.text_input("EMAIL", key="r_email")
            r_pass = st.text_input("PASSWORD", type="password", key="r_pass")
            if st.button("CREATE IDENTITY", key="btn_reg", use_container_width=True):
                data = api_register(r_email, r_pass, r_name)
                if data:
                    st.success("IDENTITY CREATED. PROCEED TO LOGIN.")
                else:
                    st.error("REGISTRATION FAILED")

        with tab3:
            a_user = st.text_input("USERNAME", key="a_user")
            a_pass = st.text_input("PASSWORD", type="password", key="a_pass")
            if st.button("ADMIN OVERRIDE", key="btn_admin", use_container_width=True):
                data = api_admin_login(a_user, a_pass)
                if data:
                    st.session_state.token = data["access_token"]
                    st.session_state.role = "admin"
                    st.rerun()
                else:
                    st.error("OVERRIDE REJECTED")

def admin_view():
    with st.sidebar:
        st.title("ADMIN CONSOLE")
        if st.button("LOGOUT"):
            st.session_state.token = None
            st.rerun()
    
    st.title("RAY DATASET MANAGEMENT")
    uploaded = st.file_uploader("INGEST DOCUMENT", type=["pdf", "docx", "csv", "xlsx", "txt", "md", "html"])
    if uploaded and st.button("UPLOAD"):
        files = {"file": (uploaded.name, uploaded, uploaded.type)}
        try:
            r = requests.post(f"{API_URL}/admin/upload", files=files, params={"token": st.session_state.token})
            if r.status_code == 200: st.success("INGESTION COMPLETE")
            else: st.error("UPLOAD FAILED")
        except Exception as e: st.error(str(e))
    
    st.divider()
    st.subheader("SYSTEM FILES")
    try:
        r = requests.get(f"{API_URL}/admin/files", params={"token": st.session_state.token})
        
        # DEBUG LOGGING (Temporary)
        with st.expander("🔍 Debug API Response"):
            st.write(f"**Status Code:** {r.status_code}")
            st.write(f"**Raw Response:** {r.text}")
            
        files = r.json()
        if not files:
            st.info("No files found in database.")
            
        for f in files:
            c1, c2 = st.columns([4, 1])
            c1.code(f"{f['filename']} ({f['size_bytes']} bytes)")
            if c2.button("PURGE", key=f['filename']):
                requests.delete(f"{API_URL}/admin/files/{f['filename']}", params={"token": st.session_state.token})
                st.rerun()
    except Exception as e: 
        st.error(f"FAILED TO FETCH FILES: {str(e)}")
                
    st.divider()
    st.markdown("### ⚠️ DANGER ZONE")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("RESET FILES & VECTORS", type="primary"):
            try:
                requests.delete(f"{API_URL}/admin/reset", params={"token": st.session_state.token})
                st.success("SYSTEM RESET COMPLETE")
                time.sleep(1)
                st.rerun()
            except Exception as e: st.error(str(e))
    with c2:
        if st.button("PURGE VECTORS ONLY", type="primary", key="purge_vec"):
            try:
                requests.delete(f"{API_URL}/admin/vectors", params={"token": st.session_state.token})
                st.success("VECTOR INDEX CLEARED")
                time.sleep(1)
                st.rerun()
            except Exception as e: st.error(str(e))


def chat_view():
    with st.sidebar:
        st.markdown(f"### USER: {st.session_state.full_name}")
        
        # Model/Provider Selection
        st.markdown("### ⚙️ MODEL CONFIG")
        provider_map = {
            "Groq (Fast)": "groq",
            "Gemini (Google)": "gemini",
            "Ollama (Local)": "ollama"
        }
        selected_provider_label = st.selectbox(
            "Provider",
            list(provider_map.keys()),
            index=0,
            key="provider_select"
        )
        selected_provider = provider_map[selected_provider_label]
        
        # Model selection based on provider
        if selected_provider == "groq":
            model_options = {
                "Llama 3.3 70B": "llama-3.3-70b-versatile",
                "Llama 3 8B": "llama3-8b-8192"
            }
            selected_model = st.selectbox("Model", list(model_options.keys()), key="model_select")
            st.session_state.selected_model = model_options[selected_model]
        elif selected_provider == "gemini":
            model_options = {
                "Gemini 2.5 Flash": "gemini-2.5-flash",
                "Gemini 2.0 Flash": "gemini-2.0-flash"
            }
            selected_model = st.selectbox("Model", list(model_options.keys()), key="model_select")
            st.session_state.selected_model = model_options[selected_model]
        else:
            st.session_state.selected_model = st.text_input("Model Name", value="mistral", key="ollama_model")
        
        st.session_state.selected_provider = selected_provider
        
        st.divider()
        if st.button("NEW SESSION", use_container_width=True):
            st.session_state.session_id = None
            st.session_state.messages = [{"role": "assistant", "content": f"Greetings {st.session_state.full_name}. Systems Online."}]
            st.rerun()
            
        st.divider()
        st.markdown("### 📜 HISTORY")
        
        # Fetch and display chat history
        chats = api_get_chats(st.session_state.token)
        if chats:
            for i, chat in enumerate(chats):
                conv_id = chat.get("conversation_id")
                messages = chat.get("messages", [])
                
                # Create preview from first user message
                preview = "New Chat"
                for msg in messages:
                    if msg.get("role") == "user":
                        preview = msg.get("content", "")[:30] + "..."
                        break
                
                # Clickable history item
                if st.button(f"💬 {preview}", key=f"chat_{i}", use_container_width=True):
                    st.session_state.session_id = conv_id
                    st.session_state.messages = messages
                    st.rerun()
        else:
            st.info("No past conversations")
            
        st.divider()
        if st.button("DISCONNECT", use_container_width=True):
            st.session_state.token = None
            st.rerun()

    # --- STICKY HEADER & STARTUP ---
    
    # 1. Sticky Header CSS
    # 1. Sticky Header CSS
    st.markdown("""
        <style>
            .sticky-header {
                position: sticky; /* Sticky ensures it stays in flow and respects container width */
                top: 0;
                width: 100%; /* Relative to container, not viewport */
                z-index: 999;
                background-color: #0e1117; 
                padding: 1rem 0;
                text-align: center;
                border-bottom: 2px solid #00ff41;
                margin-bottom: 2rem; /* Add spacing below header */
            }
            .sticky-header h1 {
                margin: 0;
                color: #00ff41;
                font-family: 'Courier New', Courier, monospace;
                text-shadow: 0 0 10px rgba(0, 255, 65, 0.5);
                font-size: 2.5rem;
            }
            
            /* Hide default Streamlit header decoration */
            /* Make Streamlit header transparent but keep toggle accessible */
            header[data-testid="stHeader"] {
                background-color: transparent;
            }
        </style>
        <div class="sticky-header">
            <h1>Ray Intelligent Agent</h1>
        </div>
    """, unsafe_allow_html=True)

    # 2. Startup Logic (Spinner + Time-based Greeting)
    if not st.session_state.messages:
        with st.spinner("⚡ Turning on Ray..."):
            time.sleep(1.5) # Simulate boot time
        
        # Determine Greeting
        import datetime
        hour = datetime.datetime.now().hour
        if 5 <= hour < 12:
            greeting = "Good Morning"
        elif 12 <= hour < 17:
            greeting = "Good Afternoon"
        elif 17 <= hour < 21:
            greeting = "Good Evening"
        else:
            greeting = "Greetings"
            
        full_greeting = f"{greeting} {st.session_state.full_name}. Systems Online."
        
        # Stream the initial greeting
        placeholder = st.empty()
        display_text = ""
        import random
        for char in full_greeting:
            display_text += char
            placeholder.markdown(display_text)
            time.sleep(random.uniform(0.01, 0.05))
            
        # Save to history
        st.session_state.messages = [{"role": "assistant", "content": full_greeting}]
        # Clear placeholder effectively as it renders in the loop (rendered static below)
        placeholder.empty()

    # st.markdown("---") # Removed simple divider as header is now sticky

    # Display messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            # Show citations prominently if available
            if msg.get("citations"):
                with st.expander("📚 VIEW SOURCES"):
                    for i, cit in enumerate(msg["citations"], 1):
                        if cit.get("url"):
                            st.markdown(f"**{i}. [{cit.get('title', 'Web Source')}]({cit.get('url')})**")
                            if cit.get("snippet"):
                                st.caption(cit.get("snippet")[:200] + "...")
                        elif cit.get("file"):
                            location = cit.get("location", cit.get("page", "N/A"))
                            st.markdown(f"**{i}. {cit.get('file')}** ({location})")
                            if cit.get("text") or cit.get("content"):
                                st.caption((cit.get("text") or cit.get("content", ""))[:200] + "...")
                        else:
                            st.markdown(f"**{i}. {cit.get('source', 'Unknown')}**")
                        st.divider()
            elif msg["role"] == "assistant" and not any(greeting in msg["content"].lower() for greeting in ["greetings", "hello", "hi ", "systems online", "how can i assist"]):
                # Warn if citations are missing for non-greeting assistant messages
                st.caption("ℹ️ General response")

    # Chat input
    if prompt := st.chat_input("Input command..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): 
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            # Create placeholder for thoughts
            thoughts_placeholder = st.empty()
            answer_placeholder = st.empty()
            
            try:
                payload = {
                    "message": prompt, 
                    "session_id": st.session_state.session_id,
                    "provider": st.session_state.get("selected_provider", "groq"),
                    "model": st.session_state.get("selected_model", "llama-3.3-70b-versatile")
                }
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                
                # Show processing indicator
                with thoughts_placeholder.container():
                    st.markdown("**🤖 Agent Processing...**")
                    st.caption("⚙️ Analyzing query and determining approach...")
                
                r = requests.post(f"{API_URL}/chat", json=payload, headers=headers)
                
                if r.status_code == 200:
                    data = r.json()
                    st.session_state.session_id = data["session_id"]
                    
                    ans = data["answer"]
                    citations = data.get("citations", [])
                    thoughts = data.get("thoughts", [])
                    
                    # Display thoughts if available
                    if thoughts:
                        with thoughts_placeholder.expander("🧠 **Agent Reasoning Process**", expanded=False):
                            for thought in thoughts:
                                thought_type = thought.get("type", "")
                                timestamp = thought.get("timestamp", "")
                                
                                if thought_type == "thought":
                                    tool = thought.get("tool", "unknown")
                                    st.markdown(f"💭 **Thought** `[{timestamp}]`")
                                    st.caption(f"→ Decided to use: `{tool}`")
                                    
                                elif thought_type == "tool_start":
                                    tool = thought.get("tool", "unknown")
                                    tool_input = thought.get("input", "")
                                    st.markdown(f"⚙️ **Action** `[{timestamp}]`: `{tool}`")
                                    st.caption(f"📥 Input: {tool_input}")
                                    
                                elif thought_type == "tool_end":
                                    output = thought.get("output", "")
                                    st.caption(f"📤 Result: {output[:150]}...")
                                    
                                elif thought_type == "tool_error":
                                    error = thought.get("error", "")
                                    st.error(f"❌ Error: {error}")
                                    
                                elif thought_type == "finish":
                                    st.success(f"✅ **Final Answer Ready** `[{timestamp}]`")
                                
                                st.markdown("---")
                    else:
                        # Clear thoughts placeholder if no thoughts
                        thoughts_placeholder.empty()
                    
                    # Stream response
                    def stream():
                        import random
                        for char in ans:
                            yield char
                            time.sleep(random.uniform(0.005, 0.02))
                    
                    with answer_placeholder:
                        st.write_stream(stream)
                    
                    # Show citations
                    if citations:
                        with st.expander("📚 VIEW SOURCES"):
                            for i, cit in enumerate(citations, 1):
                                if cit.get("url"):
                                    st.markdown(f"**{i}. [{cit.get('title', 'Web Source')}]({cit.get('url')})**")
                                    if cit.get("snippet"):
                                        st.caption(cit.get("snippet"))
                                elif cit.get("file"):
                                    location = cit.get("location", cit.get("page", "N/A"))
                                    st.markdown(f"**{i}. {cit.get('file')}** - {location}")
                                    if cit.get("text") or cit.get("content"):
                                        st.caption(cit.get("text") or cit.get("content", ""))
                                else:
                                    st.markdown(f"**{i}. {cit.get('source', 'Unknown')}**")
                                st.divider()
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": ans, 
                        "citations": citations,
                        "thoughts": thoughts
                    })
                else:
                    error_msg = f"ERROR: {r.text}"
                    thoughts_placeholder.empty()
                    answer_placeholder.error(error_msg)
                    st.session_state.messages.append({"role":  "assistant", "content": error_msg, "citations": []})
            except Exception as e:
                error_msg = f"SYSTEM ERROR: {str(e)}"
                thoughts_placeholder.empty()
                answer_placeholder.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg, "citations": []})


if not st.session_state.token:
    auth_view()
elif st.session_state.role == "admin":
    admin_view()
else:
    chat_view()
