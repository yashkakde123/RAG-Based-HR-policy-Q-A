import os
import logging
import time
import streamlit as st

# ==========================================
# 1. PAGE CONFIGURATION (MUST BE FIRST)
# ==========================================
if "user_token" not in st.session_state or st.session_state.user_token is None:
    st.set_page_config(
        page_title="Secure Gateway Entry", 
        page_icon="🛡️", 
        layout="centered"
    )
else:
    st.set_page_config(
        page_title="CDAC Policy Assistant", 
        page_icon="📂", 
        layout="wide"
    )

# ==========================================
# 2. INJECT TARGETED CSS (NO THEME CONFLICTS)
# ==========================================
st.markdown("""
<style>
    /* Elegant Title Banner */
    .title-banner {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 30px;
        border-radius: 12px;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .title-banner h1, .title-banner p {
        color: white !important;
    }
    
    /* Login Portal Container Card */
    .login-container {
        background-color: white !important;
        padding: 40px;
        border-radius: 16px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        border: 1px solid #e5e7eb;
    }
    
    /* Clean Citation Card Styling */
    .citation-card {
        background-color: #f3f4f6 !important;
        border-left: 4px solid #3b82f6 !important;
        padding: 10px 16px;
        border-radius: 6px;
        margin-top: 8px;
        color: #374151 !important;
    }
    
    /* Styled Buttons */
    .stButton>button {
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. Import Modular Classes
from modules.auth_service import FirebaseAuthService
from modules.ingestion import DocumentProcessor
from modules.database import VectorDatabase
from modules.generation import LLMGenerator

# 4. Setup Logging (REQ-08)
logging.basicConfig(filename='admin_secure.log', level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')

# ==========================================
# 5. STREAMLIT OPTIMIZATION: RESOURCE CACHING
# ==========================================
@st.cache_resource
def get_auth_service():
    return FirebaseAuthService()

@st.cache_resource
def get_vector_database():
    return VectorDatabase()

@st.cache_resource
def get_llm_generator():
    return LLMGenerator()

# Instantiate Cached Modules
auth_service = get_auth_service()
vector_db = get_vector_database()
llm_gen = get_llm_generator()

doc_processor = DocumentProcessor()

# Init Session States
if "user_token" not in st.session_state:
    st.session_state.user_token = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ==========================================
# AUTHENTICATION PORTAL
# ==========================================
if st.session_state.user_token is None:
    col1, col2, col3 = st.columns([1, 6, 1])
    
    with col2:
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        
        st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>🛡️ Corporate Security Gateway</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #6b7280; margin-bottom: 30px;'>RAG-Based Company Policy Q&A System</p>", unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["🔒 Employee Login", "📝 Register Account", "🔑 Forgot Password"])
        
        with tab1:
            st.markdown("<br>", unsafe_allow_html=True)
            login_email = st.text_input("Corporate Email Address:", placeholder="name@company.com")
            login_pass = st.text_input("Security Account Password:", type="password", placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("Sign In", use_container_width=True, type="primary"):
                with st.spinner("Verifying credentials with secure directory..."):
                    res = auth_service.sign_in_user(login_email, login_pass)
                if res["success"]:
                    st.session_state.user_token = res["user_info"]
                    st.success("Identity Verified. Loading System Components...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(res["error"])
                    
        with tab2:
            st.markdown("<br>", unsafe_allow_html=True)
            reg_email = st.text_input("New Employee Email Address:", placeholder="name@company.com")
            reg_pass = st.text_input("Create Account Password (Min 6 Characters):", type="password", placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("Register Account", use_container_width=True):
                with st.spinner("Registering new corporate profile..."):
                    res = auth_service.sign_up_user(reg_email, reg_pass)
                if res["success"]:
                    st.success(res["msg"])
                else:
                    st.error(res["error"])
                    
        with tab3:
            st.markdown("<br>", unsafe_allow_html=True)
            st.info("Enter your registered email address. Firebase will send you a secure link to reset your password.")
            reset_email = st.text_input("Registered Email Address:", placeholder="name@company.com")
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("Send Reset Link", use_container_width=True):
                if reset_email:
                    with st.spinner("Generating secure authentication token..."):
                        res = auth_service.reset_password(reset_email)
                    if res["success"]:
                        st.success(res["msg"])
                    else:
                        st.error(res["error"])
                else:
                    st.warning("Please enter an email address first.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# RAG APPLICATION WORKSPACE
# ==========================================
current_user = st.session_state.user_token

# Sidebar workspace management
with st.sidebar:
    st.markdown("<h3 style='color: #1e3a8a;'>👤 User Session</h3>", unsafe_allow_html=True)
    st.info(f"**Logged In:**\n{current_user['email']}")
    
    is_admin = current_user['email'].endswith('@cdac.in') or current_user['email'] == "admin@test.com"
    if is_admin:
        st.markdown("---")
        st.markdown("<h3 style='color: #1e3a8a;'>🔧 Admin Workspace</h3>", unsafe_allow_html=True)
        st.caption("Ingest and update corporate policy documents.")
        
        if st.button("Trigger Ingestion Pipeline", use_container_width=True, type="primary"):
            with st.spinner("Reading, chunking, and embedding PDF directories..."):
                chunks = doc_processor.extract_and_chunk()
                count = vector_db.save_chunks_to_db(chunks)
                
                if count > 0:
                    st.success(f"Pipeline Executed! Indexed {count} semantic blocks.")
                    logging.info(f"Admin {current_user['email']} indexed {count} blocks.")
                else:
                    st.warning("No PDFs found in data/documents/")
                
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

# Render Chat Log Cache (WITH AVATARS & LATENCY DISPLAY)
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

    # Retrieve from DB Module
    if not os.path.exists("./chroma_db") or not os.listdir("./chroma_db"):
        st.error("Vector database is empty. Admin must trigger Ingestion first.")
    else:
        # Retrieve context from local vector DB
        retrieved_docs, ret_latency = vector_db.retrieve_context(user_query)
        
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Analyzing corporate policy and formulating answer..."):
                ai_response, citations, gen_latency = llm_gen.generate_response(user_query, retrieved_docs)
                
            st.markdown(ai_response)
            
            # REQ-08: Audit Logging & Latency Calculation
            total_time = ret_latency + gen_latency
            logging.info(f"User: {current_user['email']} | Query: '{user_query}' | Latency: {total_time:.4f}s")
            
            # Render Latency Badge directly in chat bubble
            st.markdown(f"<p style='color: #9ca3af; font-size: 0.8em; margin-top: 5px; text-align: right;'>⚡ Processing Latency: {total_time:.2f}s</p>", unsafe_allow_html=True)
            
            # REQ-06: Visually Enhanced Citation Cards
            if "I do not know" not in ai_response:
                for cit in citations:
                    st.markdown(f"""
                    <div class='citation-card'>
                        <span>📖 <b>Source:</b> {cit['source']} | <b>Page:</b> {cit['page']}</span>
                        <span style='background-color: #d1fae5; color: #065f46; padding: 2px 8px; border-radius: 9999px; font-weight: 600;'>Score: {cit['score']:.4f}</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Store in history, including latency metrics!
            history_entry = {"role": "assistant", "content": ai_response, "latency": total_time}
            if "I do not know" not in ai_response:
                history_entry["citations"] = citations
            st.session_state.chat_history.append(history_entry)