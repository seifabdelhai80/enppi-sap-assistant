import streamlit as st
import anthropic
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from prompts.system_prompts import MODES

# ─── Session Persistence ─────────────────────────────────────────────────────
_SESSIONS_DIR = Path("sessions")
_SESSIONS_DIR.mkdir(exist_ok=True)

def _load_session(sid: str) -> dict:
    path = _SESSIONS_DIR / f"{sid}.json"
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for m in MODES:
                data["histories"].setdefault(m, [])
            return data
        except Exception:
            pass
    return {"histories": {m: [] for m in MODES}, "total_tokens": 0}

def _save_session(sid: str) -> None:
    path = _SESSIONS_DIR / f"{sid}.json"
    path.write_text(
        json.dumps({"histories": st.session_state.histories, "total_tokens": st.session_state.total_tokens}, ensure_ascii=False),
        encoding="utf-8",
    )

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ENPPI SAP Assistant",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Styling ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #f7f8fb; color: #111827; }
  [data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #d1d5db; }
  .main .block-container { padding-top: 1.5rem; max-width: 900px; }
  header[data-testid="stHeader"] { background: transparent; }

  .sidebar-logo {
    text-align: center; padding: 1rem 0 1.5rem;
    border-bottom: 1px solid #e5e7eb; margin-bottom: 1rem;
  }
  .sidebar-logo h2 { color: #111827; font-size: 1.1rem; margin: 0.3rem 0 0; font-weight: 700; }
  .sidebar-logo p  { color: #6b7280; font-size: 0.7rem; margin: 0; letter-spacing: 0.05em; text-transform: uppercase; }

  div[data-testid="stButton"] button {
    width: 100%; text-align: left; border-radius: 8px;
    border: 1px solid #d1d5db !important;
    background: #f8fafc !important; color: #111827 !important;
    padding: 0.55rem 0.9rem; font-size: 0.85rem; transition: all 0.15s;
  }
  div[data-testid="stButton"] button:hover {
    background: #e2e8f0 !important; color: #111827 !important;
    border-color: #cbd5e1 !important;
  }

  .msg-user {
    background: #ebf5ff; border: 1px solid #bfdbfe;
    border-radius: 12px 12px 2px 12px;
    padding: 0.9rem 1.1rem; margin: 0.6rem 0; color: #111827;
    font-size: 0.9rem; line-height: 1.6; white-space: pre-wrap;
  }
  .msg-assistant {
    background: #f8fafc; border: 1px solid #d1d5db;
    border-radius: 2px 12px 12px 12px;
    padding: 0.9rem 1.1rem; margin: 0.6rem 0; color: #111827;
    font-size: 0.9rem; line-height: 1.7;
  }
  .msg-label {
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.06em;
    text-transform: uppercase; margin-bottom: 0.4rem;
  }
  .msg-label-user { color: #2563eb; }
  .msg-label-assistant { color: #059669; }

  .welcome-card {
    background: #ffffff; border: 1px solid #d1d5db;
    border-radius: 12px; padding: 1.8rem 2rem; margin-bottom: 1.5rem;
  }
  .welcome-card h2 { color: #111827; font-size: 1.2rem; margin: 0 0 0.4rem; }
  .welcome-card p  { color: #4b5563; font-size: 0.87rem; margin: 0 0 1rem; }

  .sidebar-section {
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase; color: #6b7280; margin: 1.2rem 0 0.5rem;
  }
  .token-badge {
    background: #f8fafc; border: 1px solid #d1d5db;
    border-radius: 6px; padding: 0.35rem 0.6rem;
    font-size: 0.75rem; color: #4b5563; text-align: center; margin-top: 0.5rem;
  }
  .stDownloadButton button {
    width: 100%; background: #f8fafc !important;
    border: 1px solid #d1d5db !important; color: #111827 !important;
    border-radius: 8px !important; font-size: 0.8rem !important;
  }
  .stDownloadButton button:hover {
    background: #e2e8f0 !important; color: #111827 !important;
  }
</style>
""", unsafe_allow_html=True)

# ─── Session State ────────────────────────────────────────────────────────────
if "active_mode" not in st.session_state:
    st.session_state.active_mode = "general"
if "session_id" not in st.session_state:
    sid = st.query_params.get("sid", uuid.uuid4().hex[:12])
    st.session_state.session_id = sid
    st.query_params["sid"] = sid
    saved = _load_session(sid)
    st.session_state.histories = saved["histories"]
    st.session_state.total_tokens = saved["total_tokens"]

# ─── API Key Helper ───────────────────────────────────────────────────────────
def load_env_file_key() -> str:
    env_path = Path(".env")
    if not env_path.exists():
        return ""
    with env_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == "ANTHROPIC_API_KEY":
                return value.strip().strip('"').strip("'")
    return ""

# ─── API Key ──────────────────────────────────────────────────────────────────
if "api_key" not in st.session_state:
    st.session_state.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not st.session_state.api_key:
        try:
            st.session_state.api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
        except Exception:
            st.session_state.api_key = ""
    if not st.session_state.api_key:
        st.session_state.api_key = load_env_file_key()

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
      <h2>ENPPI SAP Assistant</h2>
      <p>DBSS Division · S/4HANA On-Premise</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">Mode</div>', unsafe_allow_html=True)
    for mode_key, mode_cfg in MODES.items():
        if st.button(mode_cfg['label'], key=f"btn_{mode_key}"):
            st.session_state.active_mode = mode_key
            st.rerun()

    st.markdown("---")
    st.markdown('<div class="sidebar-section">Session</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="token-badge">Approx. tokens used: {st.session_state.total_tokens:,}</div>',
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
            "Export conversation (.md)",
            data=export_md,
            file_name=f"sap_{st.session_state.active_mode}_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
        )
    if st.button("Clear conversation", key="clear"):
        st.session_state.histories[st.session_state.active_mode] = []
        _save_session(st.session_state.session_id)
        st.rerun()

    st.markdown("---")
    st.markdown('<div class="sidebar-section">API Key</div>', unsafe_allow_html=True)
    if st.session_state.api_key:
        st.markdown('<div style="color:#111827; font-size:0.9rem;">API key loaded automatically.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="color:#b91c1c; font-size:0.85rem;">Not configured. Ask an administrator to set ANTHROPIC_API_KEY.</div>', unsafe_allow_html=True)

api_key = st.session_state.api_key

# ─── Main ─────────────────────────────────────────────────────────────────────
mode_cfg = MODES[st.session_state.active_mode]
history  = st.session_state.histories[st.session_state.active_mode]

st.markdown("""
<div style="display:flex; align-items:center; gap:1rem; margin-bottom:1.5rem;">
  <div style="display:flex; align-items:center; justify-content:center; width:120px; height:52px; background:#ffcc00; color:#000; font-size:1.1rem; font-weight:900; clip-path: polygon(0 0, 100% 0, 80% 100%, 0% 100%);">SAP</div>
  <div style="display:flex; align-items:center; justify-content:center; width:120px; height:52px; background:#003b71; color:#fff; font-size:1.1rem; font-weight:900; border-radius:12px;">ENPPI</div>
</div>
""", unsafe_allow_html=True)

# Mode header
st.markdown(f"""
<div style="margin-bottom:1rem;">
  <div style="color:#e2e8f0; font-size:1.1rem; font-weight:700;">{mode_cfg['label']}</div>
  <div style="color:#64748b; font-size:0.8rem;">{mode_cfg['description']}</div>
</div>
<hr style="border-color:#1e2533; margin-bottom:1rem;">
""", unsafe_allow_html=True)

# Welcome card when empty
if not history:
    examples = [e.strip().lstrip("e.g. ").strip() for e in mode_cfg["placeholder"].split(". ") if e.strip()]
    chips = "".join(f'<span style="background:#1a2035;border:1px solid #2a3a50;border-radius:20px;padding:0.25rem 0.7rem;color:#94a3b8;font-size:0.78rem;margin:0.2rem;display:inline-block;">{e}</span>' for e in examples)
    st.markdown(f"""
    <div class="welcome-card">
      <h2>{mode_cfg['label']}</h2>
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

# OData Quick Reference
if st.session_state.active_mode == "odata":
    with st.expander("📋 OData Quick Reference", expanded=False):
        tab_std, tab_z = st.tabs(["Standard SAP APIs", "Z-Services"])
        with tab_std:
            st.markdown("""
| Service | Base Path | Key Operations |
|---|---|---|
| `API_PURCHASEORDER_PROCESS_SRV` | `/sap/opu/odata/sap/API_PURCHASEORDER_PROCESS_SRV` | Create / Read / Change PO |
| `API_SALES_ORDER_SRV` | `/sap/opu/odata/sap/API_SALES_ORDER_SRV` | Create / Read SO |
| `API_BUSINESS_PARTNER` | `/sap/opu/odata/sap/API_BUSINESS_PARTNER` | Read / Create Business Partner |
| `API_MATERIAL_STOCK_SRV` | `/sap/opu/odata/sap/API_MATERIAL_STOCK_SRV` | Read stock levels |
| `API_PROJECT_RESULTS_SRV` | `/sap/opu/odata/sap/API_PROJECT_RESULTS_SRV` | PS project data |
| `API_FINANCIALPLANDATA_SRV` | `/sap/opu/odata/sap/API_FINANCIALPLANDATA_SRV` | FI plan data |
| `API_SUPPLIER_INVOICE_SRV` | `/sap/opu/odata/sap/API_SUPPLIER_INVOICE_SRV` | Read / Post vendor invoices |
| `API_INSP_LOT_SRV` | `/sap/opu/odata/sap/API_INSP_LOT_SRV` | QM inspection lots |

> Activate any service via T-Code `/IWFND/MAINT_SERVICE`. Base URL: `https://<host>:<port><path>/`
""")
        with tab_z:
            st.markdown("""
| Service Name | Base Path | Description | Activated By |
|---|---|---|---|
| *(e.g. Z_MM_OPEN_PO_SRV)* | `/sap/opu/odata/sap/Z_MM_OPEN_PO_SRV` | *(Open POs by vendor)* | *(BASIS team)* |

> Add your Z-services to [`references/enppi_context.md`](references/enppi_context.md).
""")

# Input
if not api_key:
    st.warning("⚠️ No API key configured for this deployment. Contact an administrator.", icon="🔑")

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
            model="claude-sonnet-4-6",
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
            usage = stream.get_final_message().usage

        response_area.markdown(full_response)
        history.append({"role": "assistant", "content": full_response})
        st.session_state.histories[st.session_state.active_mode] = history
        st.session_state.total_tokens += usage.input_tokens + usage.output_tokens
        _save_session(st.session_state.session_id)

    except anthropic.AuthenticationError:
        st.error("❌ Invalid API key. Please check and try again.")
    except anthropic.RateLimitError:
        st.error("⚠️ Rate limit reached — please wait a moment.")
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")

    st.rerun()
