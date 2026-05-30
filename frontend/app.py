import streamlit as st
import requests
from dashboard import render_dashboard

st.set_page_config(
    page_title="DevOpsBot — ChatOps AI",
    page_icon="🤖",
    layout="wide"
)

BACKEND_URL = "http://localhost:8000"

st.markdown("""
<style>
    .stApp { background-color: #1a1f2e; }
    [data-testid="stSidebar"] { background-color: #141824; border-right: 1px solid #2e3650; }
    [data-testid="stSidebar"] * { color: #c9d1e0 !important; }
    [data-testid="stSidebar"] button {
        background-color: #252c42 !important; color: #c9d1e0 !important;
        border: 1px solid #3a4460 !important; border-radius: 8px !important;
    }
    [data-testid="stSidebar"] button:hover { background-color: #4f6ef7 !important; color: #ffffff !important; }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background-color: #1e3358 !important; border: 1px solid #2a4a80 !important;
        border-radius: 12px !important; margin-bottom: 10px !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        background-color: #212840 !important; border: 1px solid #2e3a58 !important;
        border-radius: 12px !important; margin-bottom: 10px !important;
    }
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] span, [data-testid="stChatMessage"] strong,
    [data-testid="stChatMessage"] em, [data-testid="stChatMessage"] td,
    [data-testid="stChatMessage"] th {
        color: #dde3f0 !important; font-family: 'Segoe UI', sans-serif !important;
        font-size: 0.93rem !important; background: transparent !important;
        border: none !important; padding: 0 !important;
    }
    [data-testid="stChatMessage"] table { border-collapse: collapse !important; width: 100% !important; margin: 8px 0 !important; }
    [data-testid="stChatMessage"] th { background-color: #252c42 !important; color: #a0b0d0 !important; padding: 6px 12px !important; font-size: 0.82rem !important; text-transform: uppercase !important; border: 1px solid #2e3a58 !important; }
    [data-testid="stChatMessage"] td { padding: 6px 12px !important; border: 1px solid #2e3a58 !important; color: #dde3f0 !important; }
    [data-testid="stChatMessage"] tr:nth-child(even) td { background-color: #1e2538 !important; }
    [data-testid="stChatMessage"] code { color: #7eb8f7 !important; background-color: #161c2d !important; border: 1px solid #2e3a58 !important; border-radius: 4px !important; padding: 1px 5px !important; }
    [data-testid="stChatMessage"] pre { background-color: #161c2d !important; border: 1px solid #2e3a58 !important; border-radius: 8px !important; padding: 12px !important; }
    [data-testid="stChatMessage"] pre code { color: #7eb8f7 !important; background: transparent !important; border: none !important; padding: 0 !important; }
    [data-testid="stChatMessage"] div { background: transparent !important; border: none !important; color: #dde3f0 !important; }
    [data-testid="stChatInput"] textarea { background-color: #212840 !important; color: #dde3f0 !important; border: 1px solid #3a4460 !important; border-radius: 12px !important; font-size: 0.93rem !important; }
    [data-testid="stChatInput"] textarea::placeholder { color: #5a6a88 !important; }
    .stApp p, .stApp li { color: #c9d1e0; }
    .chatops-title { font-size: 1.7rem; font-weight: 700; color: #6b8ef5; margin-bottom: 0; }
    .chatops-subtitle { font-size: 0.88rem; color: #7a8aaa; margin-top: 2px; }
    hr { border-color: #2e3650 !important; }
    .stSuccess > div { background-color: #1a3326 !important; color: #5fcc8f !important; }
    .stError > div { background-color: #331a1a !important; color: #e07070 !important; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #1a1f2e; }
    ::-webkit-scrollbar-thumb { background: #3a4460; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "page" not in st.session_state:
    st.session_state.page = "chat"

def check_backend():
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False

with st.sidebar:
    st.markdown("## 🤖 DevOpsBot")
    st.markdown("*AI-Powered ChatOps Assistant*")
    st.divider()

    st.markdown("### 🗂️ Navigation")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("💬 Chat", use_container_width=True, key="nav_chat"):
            st.session_state.page = "chat"
    with col_b:
        if st.button("📊 Dashboard", use_container_width=True, key="nav_dash"):
            st.session_state.page = "dashboard"

    st.divider()

    if st.session_state.page == "chat":
        st.markdown("### 💡 Try asking:")
        suggestions = [
            "Show all service statuses",
            "What's wrong with order-service?",
            "Summarize incident INC-001",
            "Find incidents similar to Redis cache failure",
            "Restart payment-service",
            "Show all incidents for auth-service",
            "Analyze logs for root cause",
            "Scale order-service to 4 replicas",
        ]
        for s in suggestions:
            if st.button(s, key=f"btn_{s}", use_container_width=True):
                st.session_state["prefill"] = s
        st.divider()
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.history = []
            st.rerun()

    st.divider()
    st.markdown("### 🔌 System Status")
    if check_backend():
        st.success("Backend: Online ✅")
    else:
        st.error("Backend: Offline ❌")

    st.divider()
    st.caption("Dissertation Project · BITS Pilani · MTech SE")

# ── Page routing ──────────────────────────────────────────────────────────────
if st.session_state.page == "dashboard":
    render_dashboard()
else:
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        st.markdown('<p class="chatops-title">🤖 DevOpsBot</p>', unsafe_allow_html=True)
        st.markdown('<p class="chatops-subtitle">AI-Powered ChatOps System for DevOps Automation</p>', unsafe_allow_html=True)
        st.divider()

        if not st.session_state.messages:
            st.markdown("""
            <div style="text-align:center; padding: 60px 0;">
                <h2 style="color:#6b8ef5;">👋 Hello, DevOps Engineer!</h2>
                <p style="color:#7a8aaa; font-size:1rem;">I'm your AI-powered ChatOps assistant. I can help you with:</p>
                <p style="color:#8a9abf; margin-top:12px;">
                    🔍 <b style="color:#c9d1e0;">Service Health</b> &nbsp;|&nbsp;
                    📋 <b style="color:#c9d1e0;">Incident Analysis</b> &nbsp;|&nbsp;
                    🧠 <b style="color:#c9d1e0;">Root Cause Analysis</b> &nbsp;|&nbsp;
                    ⚡ <b style="color:#c9d1e0;">DevOps Actions</b> &nbsp;|&nbsp;
                    📚 <b style="color:#c9d1e0;">Knowledge Base</b>
                </p>
                <p style="font-size:0.85rem; color:#5a6a88; margin-top:16px;">Use the suggestions on the left or type your question below.</p>
            </div>
            """, unsafe_allow_html=True)

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
                st.markdown(msg["content"])

        st.markdown("""
            <div id="bottom-anchor"></div>
            <script>
                var main = window.parent.document.querySelector(".main");
                if (main) main.scrollTop = main.scrollHeight;
            </script>
        """, unsafe_allow_html=True)

        prefill_text = st.session_state.pop("prefill", None)
        user_input = st.chat_input("Ask me about services, incidents, deployments...") or prefill_text

        if user_input:
            with st.chat_message("user", avatar="👤"):
                st.markdown(user_input)
            st.session_state.messages.append({"role": "user", "content": user_input})

            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Thinking..."):
                    try:
                        response = requests.post(
                            f"{BACKEND_URL}/chat",
                            json={"message": user_input, "history": st.session_state.history},
                            timeout=30
                        )
                        reply = response.json()["reply"] if response.status_code == 200 else f"⚠️ Backend error: {response.status_code}"
                    except requests.exceptions.ConnectionError:
                        reply = "⚠️ Cannot connect to backend. Make sure it's running with:\n```\nuvicorn backend.main:app --reload\n```"
                    except Exception as e:
                        reply = f"⚠️ Error: {str(e)}"
                st.markdown(reply)

            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.session_state.history.append({"role": "user", "content": user_input})
            st.session_state.history.append({"role": "assistant", "content": reply})

            st.markdown("""
                <script>
                    var main = window.parent.document.querySelector(".main");
                    if (main) main.scrollTop = main.scrollHeight;
                </script>
            """, unsafe_allow_html=True)