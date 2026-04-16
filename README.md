# ENPPI SAP Assistant

All-in-one SAP S/4HANA on-premise assistant for the DBSS team at ENPPI.
Powered by Claude (Anthropic) via Streamlit.

## Modes
| Mode | What it does |
|---|---|
| 💬 General SAP Q&A | T-Codes, tables, processes, config, authorizations |
| ⚙️ ABAP Developer | Write, explain, review ABAP with S/4HANA standards enforced |
| 📄 Spec Generator | Full Technical Spec (TS) and Functional Spec (FS) in Markdown |
| 🔗 Integration Designer | BAPI/RFC/IDoc/OData design with diagrams and sample code |
| 🔍 Error Analyzer | Diagnose ST22 dumps, SM21 logs, SU53 auth failures |

---

## Local Setup

```bash
# 1. Clone / copy this folder
cd sap_assistant

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set API key (choose one method)

# Option A — environment variable (recommended for server)
export ANTHROPIC_API_KEY="sk-ant-..."

# Option B — Streamlit secrets
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
# Edit secrets.toml and add your key

# 5. Run
streamlit run app.py
```

---

## Oracle Cloud Free Tier Deployment

This app is structured identically to the ENPPI Virtual Assistant deployment.

```bash
# On your Oracle Cloud VM (Ubuntu)

# 1. Copy files to server
scp -r sap_assistant/ opc@<VM_IP>:~/

# 2. SSH in
ssh opc@<VM_IP>

# 3. Install deps (if not already set up)
sudo apt update && sudo apt install -y python3-pip python3-venv

cd ~/sap_assistant
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Set API key
export ANTHROPIC_API_KEY="sk-ant-..."

# 5. Run in background
nohup streamlit run app.py --server.port 8501 --server.headless true &

# 6. Open firewall port (if not already open)
sudo firewall-cmd --permanent --add-port=8501/tcp
sudo firewall-cmd --reload
```

Access at: `http://<VM_IP>:8501`

For production, add Nginx as a reverse proxy with SSL (same pattern as your VA).

---

## Adding ENPPI-Specific Context

To make the assistant aware of ENPPI's specific Z-objects, config, or standards:

1. Create `references/enppi_context.md` with your custom content
2. Load it in `prompts/system_prompts.py` and append to relevant `system_prompt` strings:

```python
with open("references/enppi_context.md") as f:
    enppi_context = f.read()

# Then in the mode's system_prompt:
"system_prompt": base_prompt + "\n\n## ENPPI-Specific Context\n" + enppi_context
```

---

## File Structure
```
sap_assistant/
├── app.py                          # Main Streamlit app
├── requirements.txt
├── README.md
├── .streamlit/
│   ├── config.toml                 # Server & theme config
│   └── secrets.toml.template       # API key template
└── prompts/
    ├── __init__.py
    └── system_prompts.py           # All mode system prompts
```
