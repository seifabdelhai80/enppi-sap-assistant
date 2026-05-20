# ENPPI SAP S/4HANA Assistant — Deployment Guide

## Local Run (Quick Test)

```bash
pip install -r requirements.txt
streamlit run app.py
```
Open http://localhost:8501

---

## Oracle Cloud Free Tier Deployment (Same setup as ENPPI VA)

### 1. Upload files to your Oracle VM

```bash
scp -i ~/.ssh/your_key.pem app.py requirements.txt ubuntu@<YOUR_VM_IP>:~/sap-assistant/
```

### 2. SSH into the VM and set up

```bash
ssh -i ~/.ssh/your_key.pem ubuntu@<YOUR_VM_IP>
cd ~/sap-assistant
pip install -r requirements.txt
```

### 3. Run with PM2 (persistent, auto-restart)

```bash
# Install PM2 if not already installed
npm install -g pm2

# Start the app
pm2 start "streamlit run app.py --server.port 8501 --server.address 0.0.0.0" \
  --name sap-assistant

pm2 save
pm2 startup
```

### 4. Configure Oracle Cloud Security List

In OCI Console → VCN → Security Lists → Ingress Rules, add:
- Source: 0.0.0.0/0 (or restrict to your office IP)
- Protocol: TCP
- Destination Port: 8501

### 5. Access the app

```
http://<YOUR_VM_IP>:8501
```

---

## API Key Management Options

### Option A: Per-User (current approach)
Each team member enters their own Anthropic API key in the sidebar.
No server-side key storage needed.

### Option B: Shared Team Key (recommended for internal use)
Set as environment variable on the server, then modify app.py:

```python
# In app.py, replace API key input with:
import os
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
```

Set on server:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# Or add to /etc/environment for persistence
echo 'ANTHROPIC_API_KEY=sk-ant-...' | sudo tee -a /etc/environment
```

---

## Adding ENPPI-Specific Context

To personalize the assistant with ENPPI-specific data:
1. Add your Z-object catalog as a text block in `BASE_SYSTEM` in app.py.
2. Add ENPPI's chart of accounts / company code structure to the FI/CO mode system prompt.
3. Add ENPPI's plant codes, purchasing org, and storage locations to the MM mode.

This turns it from a generic SAP assistant into one that knows your landscape.

---

## Optional: Nginx Reverse Proxy (for port 80/443)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```
