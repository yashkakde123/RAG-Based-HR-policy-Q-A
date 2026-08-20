import os
import logging
import time
import streamlit as st

# ==========================================
# 1. PAGE CONFIGURATION & CUSTOM THEME (MUST BE FIRST)
# ==========================================
if "user_token" not in st.session_state or st.session_state.user_token is None:
    st.set_page_config(page_title="Secure Gateway Entry", page_icon="🛡️", layout="centered")
else:
    st.set_page_config(page_title="CDAC Policy Assistant", page_icon="📂", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    .title-banner {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 30px; border-radius: 12px; color: white; margin-bottom: 25px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    .login-container {
        background-color: white !important;
        padding: 40px; border-radius: 16px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        border: 1px solid #e5e7eb;
    }
    .citation-card {
        background-color: #f3f4f6; border-left: 4px solid #3b82f6;
        padding: 10px 16px; border-radius: 6px; margin-top: 8px;
        font-size: 0.88em; color: #374151;
    }
    section[data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e5e7eb; }
    .stButton>button { border-radius: 8px !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

# 3. Import Modular Classes safely
try:
    from modules.auth_service import LocalAuthService
    from modules.ingestion import DocumentProcessor
    from modules.database import VectorDatabase
    from modules.generation import LLMGenerator
except Exception as e:
    st.error(f"Critical error loading modular dependencies: {str(e)}")
    st.stop()

# 4. Setup Logging (REQ-08)
logging.basicConfig(filename='admin_secure.log', level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')

# 5. STREAMLIT OPTIMIZATION: RESOURCE CACHING
@st.cache_resource
def get_auth_service(): return LocalAuthService()
@st.cache_resource
def get_vector_database(): return VectorDatabase()
@st.cache_resource
def get_llm_generator(): return LLMGenerator()

# Instantiate Cached Modules
try:
    auth_service = get_auth_service()
    vector_db = get_vector_database()
    llm_gen = get_llm_generator()
except Exception as e:
    st.error(f"System initialization error: {str(e)}")
    st.stop()

doc_processor = DocumentProcessor()

# Init Session States
if "user_token" not in st.session_state: st.session_state.user_token = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []

# ==========================================
# AUTHENTICATION PORTAL (100% LOCAL & OFFLINE)
# ==========================================
if st.session_state.user_token is None:
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>🛡️ Corporate Security Gateway</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #6b7280; margin-bottom: 30px;'>RAG-Based Company Policy Q&A System (Offline Mode)</p>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔒 Employee Login", "📝 Register Local Account"])
        
        with tab1:
            st.markdown("<br>", unsafe_allow_html=True)
            login_email = st.text_input("Corporate Email Address:", placeholder="admin@cdac.in")
            login_pass = st.text_input("Security Account Password:", type="password", placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("Sign In", use_container_width=True, type="primary"):
                if not login_email.strip() or not login_pass.strip():
                    st.warning("Please fill in both fields.")
                else:
                    with st.spinner("Verifying credentials locally..."):
                        time.sleep(0.5)
                        res = auth_service.sign_in_user(login_email, login_pass)
                        if res["success"]:
                            st.session_state.user_token = res["user_info"]
                            # Timestamped audit record for the admin log file (REQ-08)
                            if res["user_info"]["role"] == "admin":
                                logging.info(f"ADMIN SIGNIN | {login_email} | registered_at: {res['user_info'].get('registered_at', '-')}")
                            else:
                                logging.info(f"USER SIGNIN | {login_email} | registered_at: {res['user_info'].get('registered_at', '-')}")
                            st.success("Identity Verified. Loading System Components...")
                            time.sleep(1)
                            st.rerun()
                        else:
                            # ---- Admin login diagnostic (helps on Streamlit Cloud) ----
                            # Guarded with getattr so a stale/out-of-sync auth_service
                            # (method missing on the deployed copy) can never crash the app.
                            diag_fn = getattr(auth_service, "admin_credentials_detected", None)
                            if callable(diag_fn):
                                diag = diag_fn()
                            else:
                                diag = {
                                    "admin_email_loaded": bool(getattr(auth_service, "admin_email", None)),
                                    "admin_password_loaded": bool(getattr(auth_service, "admin_password", None)),
                                    "invite_code_loaded": bool(getattr(auth_service, "invite_code", None)),
                                    "source": "diagnostic unavailable (stale auth_service deployed)",
                                }
                            admin_email = getattr(auth_service, "admin_email", None)
                            if login_email == admin_email:
                                if not (diag["admin_email_loaded"] and diag["admin_password_loaded"]):
                                    st.error(
                                        "⚠️ Admin credentials are NOT loaded on this server. "
                                        "Streamlit Cloud does not read the repo's .streamlit/secrets.toml. "
                                        "Paste the [admin] section into: App → ⋮ → Settings → Secrets, "
                                        "then Save and Restart the app."
                                    )
                                    logging.error(f"Admin login blocked - credentials source: {diag['source']}")
                                else:
                                    st.error("Invalid admin password. Check the admin_password set in Streamlit Secrets.")
                                    logging.error("Admin login failed (password mismatch) despite credentials being loaded.")
                            else:
                                st.error(res["error"])
                            
        with tab2:
            st.markdown("<br>", unsafe_allow_html=True)
            reg_email = st.text_input("New Employee Email Address:", placeholder="name@cdac.in")
            reg_pass = st.text_input("Create Account Password (Min 6 Characters):", type="password", placeholder="••••••••")
            invite_code = st.text_input("Corporate Invitation Passcode:", type="password", placeholder="Provided by HR/IT")
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("Register Account", use_container_width=True):
                if not reg_email.strip() or not reg_pass.strip() or not invite_code.strip():
                    st.warning("Please fill in all registration fields.")
                elif len(reg_pass) < 6:
                    st.warning("Password must be at least 6 characters.")
                else:
                    with st.spinner("Registering locally..."):
                        time.sleep(0.5)
                        res = auth_service.sign_up_user(reg_email, reg_pass, invite_code)
                        if res["success"]:
                            st.success(res["msg"])
                            logging.info(f"NEW REGISTRATION | {reg_email} | role: user")
                        else:
                            st.error(res["error"])
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# RAG APPLICATION WORKSPACE
# ==========================================
else:
    current_user = st.session_state.user_token

    # Sidebar workspace management
    with st.sidebar:
        st.markdown("<h3 style='color: #1e3a8a;'>👤 User Session</h3>", unsafe_allow_html=True)
        st.info(f"**Logged In:**\n{current_user['email']}\n\n**Role:** {current_user['role'].capitalize()}\n\n"
                f"**Registered:** {current_user.get('registered_at', '-')}\n"
                f"**Signed in:** {current_user.get('login_at', '-')}")
        
        # REQ-07: Offline Role Segregation & Admin Panel Access Gate
        is_admin = current_user['role'] == "admin"
        if is_admin:
            st.markdown("---")
            st.markdown("<h3 style='color: #1e3a8a;'>🔧 Admin Workspace</h3>", unsafe_allow_html=True)
            
            # SECURE DOCUMENT UPLOADER WIDGET
            st.markdown("##### 📤 Upload Policy PDFs")
            uploaded_files = st.file_uploader(
                "Drag and drop or select files:", 
                type=["pdf"], 
                accept_multiple_files=True,
                key="policy_uploader"
            )
            
            if uploaded_files:
                doc_dir = "data/documents"
                os.makedirs(doc_dir, exist_ok=True) 
                uploaded_count = 0
                
                for uploaded_file in uploaded_files:
                    target_path = os.path.join(doc_dir, uploaded_file.name)
                    file_exists = os.path.exists(target_path)
                    
                    try:
                        with open(target_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        if file_exists:
                            st.info(f"🔄 Updated/Overwrote existing file: `{uploaded_file.name}`")
                        else:
                            st.success(f"📥 Saved new file: `{uploaded_file.name}`")
                            
                        uploaded_count += 1
                    except Exception as e:
                        st.error(f"Failed to save {uploaded_file.name}: {str(e)}")
                
                if uploaded_count > 0:
                    st.caption("👉 Click 'Trigger Ingestion Pipeline' below to index changes.")
            
            st.markdown("---")
            st.caption("Click to index newly uploaded documents.")
            
            if st.button("Trigger Ingestion Pipeline", use_container_width=True, type="primary"):
                try:
                    with st.spinner("Scanning directory, applying PII masking, chunking, and embedding new PDFs..."):
                        chunks = doc_processor.extract_and_chunk()
                        if chunks:
                            count = vector_db.save_chunks_to_db(chunks)
                            st.success(f"Pipeline Executed! Indexed {count} new semantic blocks.")
                            logging.info(f"Admin {current_user['email']} indexed {count} new blocks.")
                        else:
                            st.info("No new or modified documents detected. Database is up to date.")
                except Exception as e:
                    st.error(f"Ingestion Pipeline Failed: {str(e)}")
                    logging.error(f"Ingestion crashed: {str(e)}")

                # ==========================================
            # ADMIN DASHBOARD: VIEW USERS & ACTIVITY LOGS
            # ==========================================
            st.markdown("---")
            st.markdown("##### 👥 Registered Users")
            users_result = auth_service.list_users()
            if users_result["ok"]:
                if users_result["users"]:
                    st.dataframe(users_result["users"], use_container_width=True, hide_index=True)
                    st.caption(f"Total: {len(users_result['users'])} registered user(s)")
                    users_csv = ("email,role\n" + "\n".join(
                        f"{u['email']},{u['role']}"
                        for u in users_result["users"]
                    ))
                    st.download_button(
                        "⬇️ Download registered users (CSV)",
                        users_csv,
                        file_name="registered_users.csv",
                        key="dl_users",
                    )
                else:
                    st.caption("No users registered yet.")
            else:
                st.error(f"Could not read users database: {users_result['error']}")

            with st.expander("🕵️ Admin Activity Logs"):
                log_result = auth_service.read_log_file(max_lines=300)
                if log_result["ok"]:
                    st.code(log_result["log"] or "(empty log so far)")
                    st.download_button(
                        "⬇️ Download full log",
                        log_result["log"],
                        file_name="admin_secure.log",
                        key="dl_log",
                    )
                else:
                    st.info(log_result["error"])
                st.caption("⚠️ Streamlit Cloud restarts wipe runtime files. "
                           "Download reports before a restart, or move storage to a cloud DB/Sheets.")

        st.markdown("---")
        if st.button("Secure Sign-Out", use_container_width=True):
            st.session_state.user_token = None
            st.session_state.chat_history = []
            st.rerun()

    # Branded Header Banner
    st.markdown("""
    <div class='title-banner'>
        <h1 style='margin:0; font-size: 2.2em;'>📂 Grounded Corporate Knowledge Portal</h1>
        <p style='margin:5px 0 0 0; opacity: 0.9;'>AI-Powered Document Intelligence | Group ID: 260250125G011 (BDA)</p>
    </div>
    """, unsafe_allow_html=True)

    # Render Chat Log Cache
    for interaction in st.session_state.chat_history:
        avatar = "👤" if interaction["role"] == "user" else "🤖"
        with st.chat_message(interaction["role"], avatar=avatar):
            st.markdown(interaction["content"])
            if "latency" in interaction:
                st.markdown(f"<p style='color: #9ca3af; font-size: 0.8em; margin-top: 5px; text-align: right;'>⚡ Processing Latency: {interaction['latency']:.2f}s</p>", unsafe_allow_html=True)
            if interaction["role"] == "assistant" and "citations" in interaction:
                for cit in interaction["citations"]:
                    st.markdown(f"""
                    <div class='citation-card'>
                        <span>📖 <b>Source:</b> {cit['source']} | <b>Page:</b> {cit['page']}</span>
                        <span style='background-color: #d1fae5; color: #065f46; padding: 2px 8px; border-radius: 9999px; font-weight: 600;'>Score: {cit['score']:.4f}</span>
                    </div>
                    """, unsafe_allow_html=True)

    # User query capture channel
    if user_query := st.chat_input("Ask a corporate policy or guidelines query..."):
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_query)
        st.session_state.chat_history.append({"role": "user", "content": user_query})

        if not os.path.exists("./chroma_db") or not os.listdir("./chroma_db"):
            st.error("Vector database is empty. Admin must trigger Ingestion first.")
        else:
            try:
                # 1. Rewrite Query
                with st.spinner("Analyzing conversational context..."):
                    search_query = llm_gen.rewrite_query(user_query, st.session_state.chat_history[:-1])
                    logging.info(f"Query: '{user_query}' | Contextualized Search Term: '{search_query}'")

                # 2. Retrieve Context (Returns real absolute best distance score)
                retrieved_docs_with_scores, ret_latency, absolute_best_distance = vector_db.retrieve_context_hybrid(search_query)
                
                with st.chat_message("assistant", avatar="🤖"):
                    # 3. Apply relevance thresholding
                    if absolute_best_distance > 1.15:
                        ai_response = "I do not know."
                        st.markdown(ai_response)
                        total_time = ret_latency
                    else:
                        # 4. Invoke LLM and stream response
                        stream_generator, citations = llm_gen.generate_response_stream(user_query, retrieved_docs_with_scores)
                        
                        start_gen_time = time.time()
                        ai_response = st.write_stream(stream_generator)
                        gen_latency = time.time() - start_gen_time
                        
                        if "I do not know" not in ai_response:
                            for cit in citations:
                                st.markdown(f"""
                                <div class='citation-card'>
                                    <span>📖 <b>Source:</b> {cit['source']} | <b>Page:</b> {cit['page']}</span>
                                    <span style='background-color: #d1fae5; color: #065f46; padding: 2px 8px; border-radius: 9999px; font-weight: 600;'>Score: {cit['score']:.4f}</span>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        total_time = ret_latency + gen_latency
                    
                    # Render Latency Badge
                    st.markdown(f"<p style='color: #9ca3af; font-size: 0.8em; margin-top: 5px; text-align: right;'>⚡ Processing Latency: {total_time:.2f}s</p>", unsafe_allow_html=True)
                    logging.info(f"User: {current_user['email']} | Query: '{user_query}' | Latency: {total_time:.4f}s")
                    
                    # Store in history
                    history_entry = {"role": "assistant", "content": ai_response, "latency": total_time}
                    if "I do not know" not in ai_response and absolute_best_distance <= 1.15:
                        history_entry["citations"] = citations
                    st.session_state.chat_history.append(history_entry)
                    
            except Exception as e:
                st.error(f"System Error: {str(e)}")
                logging.error(f"RAG Execution Failed: {str(e)}")
