import streamlit as st
import requests
import json
from datetime import datetime
import time
from pathlib import Path

# --- CONFIGURATION ---
BASE_URL = "http://localhost:8000"

# --- LOAD CUSTOM CSS ---
def load_css():
    """Load custom Office theme CSS based on selected theme"""
    # Get current theme from session state (default to light)
    theme = st.session_state.get('theme', 'light')
    
    # Select appropriate CSS file
    css_filename = "styles.css" if theme == "light" else "styles_dark.css"
    css_file = Path(__file__).parent / css_filename
    
    if css_file.exists():
        with open(css_file, encoding='utf-8') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def get_time_based_greeting(name: str = None):
    hour = datetime.now().hour
    if 5 <= hour < 12:
        period = "morning"
    elif 12 <= hour < 17:
        period = "afternoon"
    else:
        period = "evening"
    
    greeting = f"Good {period}"
    if name:
        greeting += f" {name}"
    
    return f"{greeting}, I am Ray. How can I assist you with HR policies and leave related queries?"

# --- STATE MANAGEMENT ---
# Initialize ALL session state variables at the start to avoid AttributeErrors
state_defaults = {
    "token": None,
    "role": None,
    "full_name": None,
    "show_login_animation": False,
    "conversation_id": None,
    "theme": "light",
}

for key, val in state_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

if "messages" not in st.session_state:
    # Initial greeting without name if not logged in yet
    initial_name = st.session_state.get("full_name")
    st.session_state.messages = [{
        "role": "assistant",
        "content": get_time_based_greeting(initial_name)
    }]

# ... (omitted config section matches original) ...

# ... (API helper updates not needed here as they digest JSON response automatically in typical requests usage, but let's check Login helper) ...

def api_login_user(email, password):
    """Endpoint: POST /auth/login"""
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
        if resp.status_code == 200:
            return resp.json()  # Returns {user_id, token, full_name}
    except: pass
    return None

# ... (omitted admin/chat helpers) ...

def api_get_user_history():
    """Endpoint: GET /user/chats"""
    token = st.session_state.token
    if not token: return {}
    
    try:
        resp = requests.get(
            f"{BASE_URL}/user/chats", 
            headers={"Authorization": f"Bearer {token}"}
        )
        if resp.status_code == 200:
            return resp.json()
    except: pass
    return {}

def api_user_chat(query, provider, model, conversation_id=None):
    """Endpoint: POST /chat"""
    token = st.session_state.token
    if not token: return {"answer": "Error: Not logged in"}
    
    payload = {
        "query": query,
        "provider": provider,
        "model": model,
        "conversation_id": conversation_id
    }
    
    try:
        resp = requests.post(
            f"{BASE_URL}/chat", 
            json=payload, 
            headers={"Authorization": f"Bearer {token}"}
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"answer": f"Error: {resp.text}"}
    except Exception as e:
        return {"answer": f"Connection Error: {e}"}

def api_get_chunk_context(chunk_id):
    """Endpoint: GET /context/{chunk_id}"""
    try:
        resp = requests.get(f"{BASE_URL}/context/{chunk_id}")
        if resp.status_code == 200:
            return resp.json()
    except: pass
    return None

def api_login_admin(username, password):
    """Endpoint: POST /admin/login"""
    try:
        resp = requests.post(f"{BASE_URL}/admin/login", json={"username": username, "password": password})
        if resp.status_code == 200:
            return resp.json()  # Returns {access_token}
    except: pass
    return None

def api_admin_upload(file_obj):
    """Endpoint: POST /admin/upload"""
    token = st.session_state.token
    if not token: return False
    
    try:
        files = {"file": (file_obj.name, file_obj, file_obj.type)}
        resp = requests.post(f"{BASE_URL}/admin/upload", files=files, params={"token": token})
        return resp.status_code == 200
    except:
        return False

def api_admin_get_files():
    """Endpoint: GET /admin/files"""
    token = st.session_state.token
    if not token: return []
    
    try:
        resp = requests.get(f"{BASE_URL}/admin/files", params={"token": token})
        if resp.status_code == 200:
            return resp.json().get("files", [])
    except: pass
    return []

def api_admin_delete(filename):
    """Endpoint: DELETE /admin/files/{filename}"""
    token = st.session_state.token
    if not token: return False
    
    try:
        resp = requests.delete(f"{BASE_URL}/admin/files/{filename}", params={"token": token})
        return resp.status_code == 200
    except:
        return False

def api_admin_reset():
    """Endpoint: DELETE /admin/reset"""
    token = st.session_state.token
    if not token: return False
    
    try:
        resp = requests.delete(f"{BASE_URL}/admin/reset", params={"token": token})
        return resp.status_code == 200
    except:
        return False

def api_admin_reset_db():
    """Endpoint: DELETE /admin/reset-db"""
    token = st.session_state.token
    if not token: return False
    
    try:
        resp = requests.delete(f"{BASE_URL}/admin/reset-db", params={"token": token})
        return resp.status_code == 200
    except:
        return False

# --- UI VIEWS ---

def login_view():
    # ... (header matches original) ...
    col1, col2 = st.columns([6, 1])
    with col1:
        st.title("🔐 Ray - Deterministic RAG System")
    with col2:
        theme_icon = "🌙" if st.session_state.theme == "light" else "☀️"
        if st.button(theme_icon, key="theme_toggle_login"):
            st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
            st.rerun()
    
    tab1, tab2, tab3 = st.tabs(["👤 User Login", "📝 User Register", "🛠️ Admin Login"])

    # 1. User Login
    with tab1:
        u_email = st.text_input("Email", key="u_email")
        u_pass = st.text_input("Password", type="password", key="u_pass")
        if st.button("User Login"):
            data = api_login_user(u_email, u_pass)
            if data:
                st.session_state.token = data["token"]
                st.session_state.role = "user"
                st.session_state.full_name = data.get("full_name") # Store name
                
                # clear messages and set animation flag
                st.session_state.messages = []
                st.session_state.show_login_animation = True
                st.rerun()
            else:
                st.error("Invalid user credentials")

    # 2. User Register
    with tab2:
        r_name = st.text_input("Full Name") # New Field
        r_email = st.text_input("New Email")
        r_pass = st.text_input("New Password", type="password")
        if st.button("Register"):
            if not r_name:
                st.error("Full Name is required")
            else:
                resp = requests.post(f"{BASE_URL}/auth/register", json={
                    "email": r_email, 
                    "password": r_pass,
                    "full_name": r_name
                })
                if resp.status_code == 200:
                    st.success("Account created! Please log in.")
                else:
                    st.error("Registration failed.")

    # 3. Admin Login
    with tab3:
        a_user = st.text_input("Username", key="a_user")
        a_pass = st.text_input("Password", type="password", key="a_pass")
        if st.button("Admin Login"):
            data = api_login_admin(a_user, a_pass)
            if data:
                st.session_state.token = data["access_token"]
                st.session_state.role = "admin"
                st.success("Welcome Admin!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Invalid admin credentials")

def reset_chat_with_greeting():
    st.session_state.conversation_id = None
    name = st.session_state.get("full_name")
    st.session_state.messages = [{
        "role": "assistant",
        "content": get_time_based_greeting(name)
    }]

def user_view():
    # --- SIDEBAR (Settings & History) ---
    with st.sidebar:
        st.header("Chat Settings")
        
        # Theme toggle at top of sidebar
        theme_icon = "🌙 Dark Mode" if st.session_state.theme == "light" else "☀️ Light Mode"
        if st.button(theme_icon, key="theme_toggle_user", use_container_width=True):
            st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
            st.rerun()
        
        st.divider()
        
        # Maps to backend.md "provider" and "model"
        provider = st.selectbox("Provider", ["ollama", "gemini"])
        
        # Dynamic model default based on provider (Visual polish)
        # Dynamic model default based on provider (Visual polish)
        default_model = "mistral:latest"
        if provider == "gemini": default_model = "gemini-2.5-flash"
        if provider == "ollama": default_model = "mistral:latest"
        
        model_name = st.text_input("Model Name", value=default_model)
        
        

        
        st.divider()
        st.subheader("History")
        if st.button("➕ New Chat"):
            reset_chat_with_greeting()
            st.rerun()

        # Load History (GET /user/chats)
        history_data = api_get_user_history()
        for chat in history_data.get("conversations", []):
            label = f"Chat {chat['conversation_id'][:8]}..."
            if st.button(label, key=chat['conversation_id']):
                # Load this chat into main view
                st.session_state.conversation_id = chat['conversation_id']
                
                # Parse messages from the API response
                loaded_messages = []
                for msg in chat.get('messages', []):
                    # Add user message
                    if msg.get('user'):
                        loaded_messages.append({
                            "role": "user",
                            "content": msg['user']
                        })
                    # Add assistant message with citations if available
                    if msg.get('assistant'):
                        loaded_messages.append({
                            "role": "assistant",
                            "content": msg['assistant'],
                            "citations": msg.get('citations', [])
                        })
                
                st.session_state.messages = loaded_messages
                st.rerun()

        st.divider()
        if st.button("Logout"):
            st.session_state.token = None
            st.session_state.role = None
            st.rerun()

    # --- MAIN CHAT AREA ---
    st.title("💬 Ray Assistant")

    # Initial Login Animation
    if st.session_state.show_login_animation:
        with st.spinner("Initiating AI Interface..."):
            time.sleep(1.5)
        
        greeting_text = get_time_based_greeting(st.session_state.full_name)
        
        def stream_text():
            import random
            for char in greeting_text:
                yield char
                time.sleep(random.uniform(0.01, 0.05))
        
        with st.chat_message("assistant"):
            st.write_stream(stream_text)
            
        st.session_state.messages.append({
            "role": "assistant", 
            "content": greeting_text
        })
        st.session_state.show_login_animation = False
        st.rerun()

    # Display Chat History
    for msg_idx, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            # If there are citations, show them
            if "citations" in msg and msg["citations"]:
                st.markdown("---")
                st.markdown("**📚 Sources:**")
                for idx, cit in enumerate(msg["citations"], 1):
                    source = cit.get('source', 'Unknown')
                    chunk_id = cit.get('chunk_id')
                    text_snippet = cit.get('text')
                    
                    with st.expander(f"[{idx}] {source}", expanded=False):
                        if chunk_id:
                            # RAG result - fetch full chunk context
                            context_data = api_get_chunk_context(chunk_id)
                            if context_data:
                                st.markdown(f"**Source:** {context_data.get('source', 'N/A')}")
                                st.markdown(f"**Chunk Index:** {context_data.get('chunk_index', 'N/A')}")
                                st.markdown("**Content:**")
                                st.text_area(
                                    "Context",
                                    value=context_data.get('content', 'No content available'),
                                    height=150,
                                    disabled=True,
                                    label_visibility="collapsed",
                                    key=f"context_{msg['role']}_{msg_idx}_{idx}_{chunk_id}"
                                )
                            else:
                                st.info("Context not available")
                        elif text_snippet:
                            # Web search result - show snippet
                            st.markdown(f"**URL:** {source}")
                            st.markdown("**Snippet:**")
                            st.text_area(
                                "Web Context",
                                value=text_snippet,
                                height=100,
                                disabled=True,
                                label_visibility="collapsed",
                                key=f"web_context_{msg['role']}_{msg_idx}_{idx}"
                            )
                        else:
                            st.markdown(f"**Source:** {source}")
                            st.info("No context available")

    # Input Area
    if prompt := st.chat_input("Ask about company policies..."):
        # 1. Show User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

            # 2. Get Bot Response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                resp_data = api_user_chat(prompt, provider, model_name, st.session_state.conversation_id)
                
                bot_text = resp_data.get("answer", "No response")
                citations = resp_data.get("citations", [])
                
                # Update conversation ID if started new
                if "conversation_id" in resp_data:
                    st.session_state.conversation_id = resp_data["conversation_id"]

                # STREAMING ANIMATION
                def stream_text():
                    import random
                    for char in bot_text:
                        yield char
                        time.sleep(random.uniform(0.005, 0.02))
                
                st.write_stream(stream_text)

                if citations:
                    st.markdown("---")
                    st.markdown("**📚 Sources:**")
                    for idx, cit in enumerate(citations, 1):
                        source = cit.get('source', 'Unknown')
                        chunk_id = cit.get('chunk_id')
                        text_snippet = cit.get('text')
                        
                        with st.expander(f"[{idx}] {source}", expanded=False):
                            if chunk_id:
                                # RAG result - fetch full chunk context
                                context_data = api_get_chunk_context(chunk_id)
                                if context_data:
                                    st.markdown(f"**Source:** {context_data.get('source', 'N/A')}")
                                    st.markdown(f"**Chunk Index:** {context_data.get('chunk_index', 'N/A')}")
                                    st.markdown("**Content:**")
                                    st.text_area(
                                        "Context",
                                        value=context_data.get('content', 'No content available'),
                                        height=150,
                                        disabled=True,
                                        label_visibility="collapsed",
                                        key=f"live_context_{idx}_{chunk_id}"
                                    )
                                else:
                                    st.info("Context not available")
                            elif text_snippet:
                                # Web search result - show snippet
                                st.markdown(f"**URL:** {source}")
                                st.markdown("**Snippet:**")
                                st.text_area(
                                    "Web Context",
                                    value=text_snippet,
                                    height=100,
                                    disabled=True,
                                    label_visibility="collapsed",
                                    key=f"live_web_context_{idx}"
                                )
                            else:
                                st.markdown(f"**Source:** {source}")
                                st.info("No context available")
        
        # 3. Save to state
        st.session_state.messages.append({
            "role": "assistant", 
            "content": bot_text,
            "citations": citations
        })

def admin_view():
    with st.sidebar:
        st.title("🛠️ Admin")
        
        # Theme toggle
        theme_icon = "🌙 Dark Mode" if st.session_state.theme == "light" else "☀️ Light Mode"
        if st.button(theme_icon, key="theme_toggle_admin", use_container_width=True):
            st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
            st.rerun()
        
        st.divider()
        if st.button("Logout"):
            st.session_state.token = None
            st.session_state.role = None
            st.rerun()

    st.title("📂 Ray - Knowledge Base Management")
    
    tab_upload, tab_files, tab_danger = st.tabs(["⬆️ Upload", "🗃️ File List", "⚠️ Danger Zone"])

    # 1. Upload (POST /admin/upload)
    with tab_upload:
        st.header("Ingest Documents")
        uploaded_file = st.file_uploader("Choose PDF or DOCX", type=["pdf", "docx"])
        if uploaded_file and st.button("Upload & Embed"):
            with st.spinner("Processing..."):
                success = api_admin_upload(uploaded_file)
                if success:
                    st.success("File uploaded and vectorized successfully!")
                else:
                    st.error("Upload failed.")

    # 2. File List (GET /admin/files & DELETE /admin/files/{id})
    with tab_files:
        st.header("Current Knowledge Base")
        files = api_admin_get_files()
        
        if not files:
            st.info("No files found in database.")
        else:
            # Create a simple table layout
            for f in files:
                col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
                col1.write(f"📄 {f['filename']}")
                col2.write(f"{f['size_bytes']} b")
                col3.write(f.get("modified_at", ""))
                if col4.button("Delete", key=f['filename']):
                    if api_admin_delete(f['filename']):
                        st.success(f"Deleted {f['filename']}")
                        st.rerun()
                    else:
                        st.error("Delete failed")

    # 3. Danger Zone (DELETE /admin/reset)
    with tab_danger:
        st.error("This area is dangerous")
        st.write("ACTIONS HERE CANNOT BE UNDONE.")
        
        st.divider()
        st.subheader("1. System Reset (Files & Vector DB)")
        st.write("Deletes all uploaded documents and clears the search index.")
        if st.button("⚠️ RESET FILES & VECTORS", type="primary"):
            if api_admin_reset():
                st.success("System files and vectors wiped successfully.")
            else:
                st.error("Reset failed.")

        st.divider()
        st.subheader("2. User Database Reset (SQLite)")
        st.write("Deletes all Users, Credentials, Tokens, and Chat History.")
        if st.button("⚠️ RESET USER DATABASE", type="primary", key="btn_reset_db"):
            if api_admin_reset_db():
                st.success("User database wiped successfully.")
            else:
                st.error("Database reset failed.")

# --- MAIN ROUTER ---

def main():
    # Load custom CSS
    load_css()
    
    if not st.session_state.token:
        login_view()
    elif st.session_state.role == "user":
        user_view()
    elif st.session_state.role == "admin":
        admin_view()
    else:
        st.error("Unknown role state. Resetting.")
        st.session_state.token = None
        st.rerun()

if __name__ == "__main__":
    main()
