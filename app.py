import streamlit as st
import anthropic
import os
from datetime import datetime
from prompts.system_prompts import MODES

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ENPPI SAP Assistant",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Styling ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #0f1117; }
  [data-testid="stSidebar"] { background: #161b27; border-right: 1px solid #1e2533; }
  .main .block-container { padding-top: 1.5rem; max-width: 900px; }
  header[data-testid="stHeader"] { background: transparent; }

  .sidebar-logo {
    text-align: center; padding: 1rem 0 1.5rem;
    border-bottom: 1px solid #1e2533; margin-bottom: 1rem;
  }
  .sidebar-logo h2 { color: #e2e8f0; font-size: 1.1rem; margin: 0.3rem 0 0; font-weight: 700; }
  .sidebar-logo p  { color: #64748b; font-size: 0.7rem; margin: 0; letter-spacing: 0.05em; text-transform: uppercase; }

  div[data-testid="stButton"] button {
    width: 100%; text-align: left; border-radius: 8px;
    border: 1px solid #1e2533 !important;
    background: #1a2035 !important; color: #94a3b8 !important;
    padding: 0.55rem 0.9rem; font-size: 0.85rem; transition: all 0.15s;
  }
  div[data-testid="stButton"] button:hover {
    background: #1e2a45 !important; color: #e2e8f0 !important;
    border-color: #334155 !important;
  }

  .msg-user {
    background: #1e2a3a; border: 1px solid #2a3a50;
    border-radius: 12px 12px 2px 12px;
    padding: 0.9rem 1.1rem; margin: 0.6rem 0; color: #e2e8f0;
    font-size: 0.9rem; line-height: 1.6; white-space: pre-wrap;
  }
  .msg-assistant {
    background: #161b27; border: 1px solid #1e2533;
    border-radius: 2px 12px 12px 12px;
    padding: 0.9rem 1.1rem; margin: 0.6rem 0; color: #cbd5e1;
    font-size: 0.9rem; line-height: 1.7;
  }
  .msg-label {
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.06em;
    text-transform: uppercase; margin-bottom: 0.4rem;
  }
  .msg-label-user { color: #3b82f6; }
  .msg-label-assistant { color: #10b981; }

  .welcome-card {
    background: #161b27; border: 1px solid #1e2533;
    border-radius: 12px; padding: 1.8rem 2rem; margin-bottom: 1.5rem;
  }
  .welcome-card h2 { color: #e2e8f0; font-size: 1.2rem; margin: 0 0 0.4rem; }
  .welcome-card p  { color: #64748b; font-size: 0.87rem; margin: 0 0 1rem; }

  .sidebar-section {
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase; color: #475569; margin: 1.2rem 0 0.5rem;
  }
  .token-badge {
    background: #1a2035; border: 1px solid #1e2533;
    border-radius: 6px; padding: 0.35rem 0.6rem;
    font-size: 0.75rem; color: #64748b; text-align: center; margin-top: 0.5rem;
  }
  .stDownloadButton button {
    width: 100%; background: #1a2035 !important;
    border: 1px solid #2a3a50 !important; color: #94a3b8 !important;
    border-radius: 8px !important; font-size: 0.8rem !important;
  }
  .stDownloadButton button:hover {
    background: #1e2a45 !important; color: #e2e8f0 !important;
  }
</style>
""", unsafe_allow_html=True)

# ─── Session State ────────────────────────────────────────────────────────────
if "active_mode" not in st.session_state:
    st.session_state.active_mode = "general"
if "histories" not in st.session_state:
    st.session_state.histories = {m: [] for m in MODES}
if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = 0

# ─── API Key ──────────────────────────────────────────────────────────────────
api_key = os.environ.get("ANTHROPIC_API_KEY", "")
if not api_key:
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        api_key = ""

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
      <div style="font-size:2rem">🏭</div>
      <h2>ENPPI SAP Assistant</h2>
      <p>DBSS Division · S/4HANA On-Premise</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">Mode</div>', unsafe_allow_html=True)
    for mode_key, mode_cfg in MODES.items():
        prefix = "▶ " if st.session_state.active_mode == mode_key else ""
        if st.button(f"{prefix}{mode_cfg['label']}", key=f"btn_{mode_key}"):
            st.session_state.active_mode = mode_key
            st.rerun()

    st.markdown("---")
    st.markdown('<div class="sidebar-section">Session</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="token-badge">🔢 Approx. tokens used: {st.session_state.total_tokens:,}</div>',
        unsafe_allow_html=True,
    )

    history = st.session_state.histories[st.session_state.active_mode]
    mode_cfg = MODES[st.session_state.active_mode]
    if history:
        export_md = f"# ENPPI SAP Assistant — {mode_cfg['label']}\nExported: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n---\n\n"
        for msg in history:
            label = "**You**" if msg["role"] == "user" else "**SAP Assistant**"
            export_md += f"{label}:\n\n{msg['content']}\n\n---\n\n"
        st.download_button(
            "⬇️ Export conversation (.md)",
            data=export_md,
            file_name=f"sap_{st.session_state.active_mode}_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
        )
    if st.button("🗑️ Clear conversation", key="clear"):
        st.session_state.histories[st.session_state.active_mode] = []
        st.rerun()

    if not api_key:
        st.markdown("---")
        st.markdown('<div class="sidebar-section">API Key</div>', unsafe_allow_html=True)
        api_key = st.text_input("Anthropic API Key", type="password", placeholder="sk-ant-...")
        st.caption("Or set ANTHROPIC_API_KEY as an environment variable.")

# ─── Main ─────────────────────────────────────────────────────────────────────
mode_cfg = MODES[st.session_state.active_mode]
history  = st.session_state.histories[st.session_state.active_mode]

# Mode header
st.markdown(f"""
<div style="display:flex; align-items:center; gap:0.7rem; margin-bottom:1rem;">
  <div style="font-size:1.6rem">{mode_cfg['icon']}</div>
  <div>
    <div style="color:#e2e8f0; font-size:1.1rem; font-weight:700;">{mode_cfg['label']}</div>
    <div style="color:#64748b; font-size:0.8rem;">{mode_cfg['description']}</div>
  </div>
</div>
<hr style="border-color:#1e2533; margin-bottom:1rem;">
""", unsafe_allow_html=True)

# Welcome card when empty
if not history:
    examples = [e.strip().lstrip("e.g. ").strip() for e in mode_cfg["placeholder"].split(". ") if e.strip()]
    chips = "".join(f'<span style="background:#1a2035;border:1px solid #2a3a50;border-radius:20px;padding:0.25rem 0.7rem;color:#94a3b8;font-size:0.78rem;margin:0.2rem;display:inline-block;">💡 {e}</span>' for e in examples)
    st.markdown(f"""
    <div class="welcome-card">
      <h2>{mode_cfg['icon']} {mode_cfg['label'].split(' ', 1)[1]}</h2>
      <p>{mode_cfg['description']}</p>
      <div style="display:flex;flex-wrap:wrap;gap:0.3rem;">{chips}</div>
    </div>
    """, unsafe_allow_html=True)

# Render history
for msg in history:
    if msg["role"] == "user":
        st.markdown(f"""
        <div class="msg-user">
          <div class="msg-label msg-label-user">You</div>
          {msg['content']}
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="msg-assistant"><div class="msg-label msg-label-assistant">SAP Assistant</div></div>', unsafe_allow_html=True)
        st.markdown(msg["content"])

# Input
if not api_key:
    st.warning("⚠️ Add your Anthropic API key in the sidebar to start chatting.", icon="🔑")

user_input = st.chat_input(mode_cfg["placeholder"], disabled=not bool(api_key))

if user_input and api_key:
    history.append({"role": "user", "content": user_input})

    st.markdown(f"""
    <div class="msg-user">
      <div class="msg-label msg-label-user">You</div>
      {user_input}
    </div>""", unsafe_allow_html=True)

    client = anthropic.Anthropic(api_key=api_key)
    response_area = st.empty()
    full_response = ""

    try:
        with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=mode_cfg["system_prompt"],
            messages=[{"role": m["role"], "content": m["content"]} for m in history],
        ) as stream:
            for text in stream.text_stream:
                full_response += text
                response_area.markdown(
                    f'<div class="msg-assistant"><div class="msg-label msg-label-assistant">SAP Assistant</div></div>',
                    unsafe_allow_html=True,
                )
                response_area.markdown(full_response + "▌")

        response_area.markdown(full_response)
        history.append({"role": "assistant", "content": full_response})
        st.session_state.histories[st.session_state.active_mode] = history
        st.session_state.total_tokens += len(user_input.split()) + len(full_response.split())

    except anthropic.AuthenticationError:
        st.error("❌ Invalid API key. Please check and try again.")
    except anthropic.RateLimitError:
        st.error("⚠️ Rate limit reached — please wait a moment.")
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")

    st.rerun()
