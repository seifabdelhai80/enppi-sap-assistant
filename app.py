import streamlit as st
import streamlit.components.v1 as components
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
  [data-testid="stSidebar"] { background: #0d1117; border-right: 1px solid #1e2533; }
  .main .block-container { padding-top: 1.2rem; max-width: 960px; }
  header[data-testid="stHeader"] { background: transparent; }
  footer { display: none !important; }

  .sidebar-logo {
    text-align: center; padding: 1rem 0 1.4rem;
    border-bottom: 1px solid #1e2533; margin-bottom: 1rem;
  }
  .sidebar-logo h2 { color: #e2e8f0; font-size: 1.05rem; margin: 0.3rem 0 0; font-weight: 700; }
  .sidebar-logo p  { color: #475569; font-size: 0.67rem; margin: 0; letter-spacing: 0.05em; text-transform: uppercase; }

  div[data-testid="stButton"] button {
    width: 100%; text-align: left; border-radius: 7px;
    border: 1px solid #1e2533 !important;
    background: #141921 !important; color: #94a3b8 !important;
    padding: 0.5rem 0.85rem; font-size: 0.83rem; transition: all 0.15s;
  }
  div[data-testid="stButton"] button:hover {
    background: #1a2540 !important; color: #e2e8f0 !important;
    border-color: #2a3a55 !important;
  }

  .msg-user {
    background: #1a2540; border: 1px solid #2a3a55;
    border-radius: 12px 12px 2px 12px;
    padding: 0.85rem 1rem; margin: 0.55rem 0; color: #e2e8f0;
    font-size: 0.88rem; line-height: 1.6; white-space: pre-wrap;
  }
  .msg-assistant {
    background: #111827; border: 1px solid #1e2533;
    border-radius: 2px 12px 12px 12px;
    padding: 0.85rem 1rem; margin: 0.55rem 0; color: #cbd5e1;
    font-size: 0.88rem; line-height: 1.7;
  }
  .msg-label {
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.07em;
    text-transform: uppercase; margin-bottom: 0.35rem;
  }
  .msg-label-user      { color: #60a5fa; }
  .msg-label-assistant { color: #34d399; }

  .welcome-card {
    background: #111827; border: 1px solid #1e2533;
    border-radius: 10px; padding: 1.6rem 1.8rem; margin-bottom: 1.2rem;
  }
  .welcome-card h2 { color: #e2e8f0; font-size: 1.1rem; margin: 0 0 0.35rem; }
  .welcome-card p  { color: #64748b; font-size: 0.85rem; margin: 0 0 0.9rem; }

  .sidebar-section {
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.09em;
    text-transform: uppercase; color: #334155; margin: 1rem 0 0.45rem;
  }
  .token-badge {
    background: #141921; border: 1px solid #1e2533;
    border-radius: 5px; padding: 0.32rem 0.55rem;
    font-size: 0.72rem; color: #64748b; text-align: center; margin-top: 0.4rem;
  }
  .stDownloadButton button {
    width: 100%; background: #141921 !important;
    border: 1px solid #1e2533 !important; color: #64748b !important;
    border-radius: 7px !important; font-size: 0.78rem !important;
  }
  /* Hide Streamlit's built-in warning/info boxes */
  [data-testid="stAlert"] { display: none !important; }
  /* Tighten mindmap container */
  iframe { border-radius: 8px; }
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

# ─── Load Mind Map HTML ───────────────────────────────────────────────────────
MINDMAP_HTML = ""
try:
    with open(os.path.join(os.path.dirname(__file__), "mindmap.html"), "r", encoding="utf-8") as f:
        MINDMAP_HTML = f.read()
except Exception:
    MINDMAP_HTML = "<p style='color:#64748b;padding:2rem;text-align:center'>Mind map file not found.</p>"

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
      <div style="font-size:1.9rem">🏭</div>
      <h2>ENPPI SAP Assistant</h2>
      <p>DBSS · S/4HANA On-Premise</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Mind Map button ──
    st.markdown('<div class="sidebar-section">Tools</div>', unsafe_allow_html=True)
    mindmap_active = st.session_state.active_mode == "__mindmap__"
    mm_prefix = "▶ " if mindmap_active else ""
    if st.button(f"{mm_prefix}🗺 Object Mind Map", key="btn_mindmap"):
        st.session_state.active_mode = "__mindmap__"
        st.rerun()

    # ── Chat modes ──
    st.markdown('<div class="sidebar-section">Chat Modes</div>', unsafe_allow_html=True)
    for mode_key, mode_cfg in MODES.items():
        prefix = "▶ " if st.session_state.active_mode == mode_key else ""
        if st.button(f"{prefix}{mode_cfg['label']}", key=f"btn_{mode_key}"):
            st.session_state.active_mode = mode_key
            st.rerun()

    st.markdown("---")
    st.markdown('<div class="sidebar-section">Session</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="token-badge">Tokens used: {st.session_state.total_tokens:,}</div>',
        unsafe_allow_html=True,
    )

    # Export / clear — only for chat modes
    if st.session_state.active_mode not in ("__mindmap__",):
        mode_cfg = MODES.get(st.session_state.active_mode, list(MODES.values())[0])
        history = st.session_state.histories.get(st.session_state.active_mode, [])
        if history:
            export_md = (
                f"# ENPPI SAP Assistant — {mode_cfg['label']}\n"
                f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n---\n\n"
            )
            for msg in history:
                label = "**You**" if msg["role"] == "user" else "**SAP Assistant**"
                export_md += f"{label}:\n\n{msg['content']}\n\n---\n\n"
            st.download_button(
                "⬇️ Export conversation",
                data=export_md,
                file_name=f"sap_{st.session_state.active_mode}_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
            )
        if st.button("🗑️ Clear conversation", key="clear"):
            st.session_state.histories[st.session_state.active_mode] = []
            st.rerun()

    # API key input (silent — no warning shown in main area)
    if not api_key:
        st.markdown("---")
        st.markdown('<div class="sidebar-section">Configuration</div>', unsafe_allow_html=True)
        api_key = st.text_input("API Key", type="password", placeholder="sk-ant-...",
                                label_visibility="collapsed")

# ═══════════════════════════════════════════════════════════════════
# ─── MIND MAP VIEW ───────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════
if st.session_state.active_mode == "__mindmap__":
    st.markdown("""
    <div style="display:flex;align-items:center;gap:0.7rem;margin-bottom:0.6rem;">
      <div style="font-size:1.5rem">🗺</div>
      <div>
        <div style="color:#e2e8f0;font-size:1.05rem;font-weight:700;">SAP S/4HANA Object Mind Map</div>
        <div style="color:#64748b;font-size:0.78rem;">Interactive reference — 5 modules · 45 object types · 1,200+ fields</div>
      </div>
    </div>
    <hr style="border-color:#1e2533;margin-bottom:0.6rem;">
    """, unsafe_allow_html=True)
    components.html(MINDMAP_HTML, height=750, scrolling=False)
    st.stop()

# ═══════════════════════════════════════════════════════════════════
# ─── CHAT VIEW ───────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════
mode_cfg = MODES[st.session_state.active_mode]
history  = st.session_state.histories[st.session_state.active_mode]

# Mode header
st.markdown(f"""
<div style="display:flex;align-items:center;gap:0.7rem;margin-bottom:0.9rem;">
  <div style="font-size:1.5rem">{mode_cfg['icon']}</div>
  <div>
    <div style="color:#e2e8f0;font-size:1.05rem;font-weight:700;">{mode_cfg['label']}</div>
    <div style="color:#64748b;font-size:0.78rem;">{mode_cfg['description']}</div>
  </div>
</div>
<hr style="border-color:#1e2533;margin-bottom:0.9rem;">
""", unsafe_allow_html=True)

# Welcome card
if not history:
    examples = [e.strip().lstrip("e.g. ").strip() for e in mode_cfg["placeholder"].split(". ") if e.strip()]
    chips = "".join(
        f'<span style="background:#141921;border:1px solid #2a3a55;border-radius:20px;'
        f'padding:0.22rem 0.65rem;color:#94a3b8;font-size:0.76rem;margin:0.2rem;display:inline-block;">💡 {e}</span>'
        for e in examples
    )
    st.markdown(f"""
    <div class="welcome-card">
      <h2>{mode_cfg['icon']} {mode_cfg['label'].split(' ', 1)[1]}</h2>
      <p>{mode_cfg['description']}</p>
      <div style="display:flex;flex-wrap:wrap;gap:0.25rem;">{chips}</div>
    </div>
    """, unsafe_allow_html=True)

# Chat history
for msg in history:
    if msg["role"] == "user":
        st.markdown(f"""
        <div class="msg-user">
          <div class="msg-label msg-label-user">You</div>
          {msg['content']}
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="msg-assistant"><div class="msg-label msg-label-assistant">SAP Assistant</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(msg["content"])

# Chat input — no warning shown; just disable quietly if no key
user_input = st.chat_input(
    mode_cfg["placeholder"],
    disabled=not bool(api_key)
)

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
                    '<div class="msg-assistant">'
                    '<div class="msg-label msg-label-assistant">SAP Assistant</div></div>',
                    unsafe_allow_html=True,
                )
                response_area.markdown(full_response + "▌")

        response_area.markdown(full_response)
        history.append({"role": "assistant", "content": full_response})
        st.session_state.histories[st.session_state.active_mode] = history
        st.session_state.total_tokens += len(user_input.split()) + len(full_response.split())

    except anthropic.AuthenticationError:
        st.error("❌ Invalid API key. Please check in the sidebar.")
    except anthropic.RateLimitError:
        st.error("⚠️ Rate limit reached — please wait a moment.")
    except Exception as e:
        st.error(f"❌ Error: {e}")

    st.rerun()
