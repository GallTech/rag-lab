# UI (lab-1-ui01)

This VM serves the user interface for the RAG lab. For now it runs a minimal Streamlit prototype that can later be replaced by a React/Next app. No state is stored here.

---

## Canonical paths

- Runtime code: /opt/rag-lab/UI
- Development clone (scratch work): ~/rag-lab/UI
- Python venv: /opt/venvs/ui
- Config (real values): /etc/ui/.env
- Logs: /var/log/ui/stdout.log and /var/log/ui/stderr.log
- Systemd unit: ui.service or ui@<user>.service

Only /opt, /etc, and /var are used at runtime. The repo under ~/rag-lab is safe to delete or reclone.

---

## Networking

- Streamlit HTTP: TCP 8501 (LAN only)
- Intended clients: browsers on your LAN; the app will call the Retrieval API when wired

---

## Configuration

Real runtime config lives in /etc/ui/.env. Example keys:
- UI_HOST=0.0.0.0
- UI_PORT=8501
- BACKEND_BASE_URL=http://lab-1-retrieval01:8001

Keep a template at UI/config/.env.example in the repo. Never commit the real /etc/ui/.env.

---

## Repository layout (this folder)

- config/ — templates (example .env)
- deploy/ — helpers to sync code to /opt and restart the service
- docs/ — runbooks and notes (optional)
- setup/ — one-time bootstrap scripts (optional)
- src/ — app.py and UI source code
- tests/ — smoke tests
- .gitignore
- README.md

---

## Service management

Status: systemctl status ui  (or systemctl status ui@<user>)  
Start: sudo systemctl start ui  (or ui@<user>)  
Stop: sudo systemctl stop ui  
Restart: sudo systemctl restart ui  

Logs (journal): journalctl -u ui -f  
Logs (files): tail -f /var/log/ui/stdout.log and /var/log/ui/stderr.log

---

## Health

Open http://<ui-vm-ip>:8501/  
If the page is blank, check stderr.log and confirm port 8501 is listening (ss -lntp | grep 8501).

---

## Update process

1) In the home clone (~/rag-lab), pull latest:
- cd ~/rag-lab
- git checkout dev
- git pull origin dev

2) Sync the UI module to runtime:
- rsync -a --delete ~/rag-lab/UI/ /opt/rag-lab/UI/

3) Restart and verify:
- sudo systemctl restart ui
- open http://<ui-vm-ip>:8501/

The deploy helper script UI/deploy/sync_and_restart.sh performs steps 2 and 3.

---

## Dependency management

- Virtual environment lives at /opt/venvs/ui
- To update dependencies:
  - source /opt/venvs/ui/bin/activate
  - pip install -r /opt/rag-lab/UI/requirements.txt
  - deactivate

Do not commit the venv. Keep requirements.txt in the repo.

---

## Guardrails

- Do not run the app manually; always use systemd.
- Do not serve from ~/rag-lab; that clone is for Git work only.
- Keep secrets and runtime config in /etc/ui/.env, never in Git.
- Treat this VM as stateless; backups are not required beyond the repo.
