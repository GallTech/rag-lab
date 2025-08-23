This runs the embedding service. It exposes a FastAPI app served by Uvicorn that generates embeddings with the model nomic-embed-text-v1.

Architecture
	•	Service: FastAPI app (embed_server.py)
	•	Model: nomic-embed-text-v1
	•	Process manager: systemd (embed.service)
	•	Network: TCP port 8000
	•	Clients: Ingestion (batch embedding), Retrieval (on-demand)

Paths
	•	Runtime code: /opt/rag-lab/EmbedGeneration
	•	Development clone: ~/rag-lab (scratch repo, safe to delete/reclone)
	•	Virtual environment: /opt/venvs/embed
	•	Config: /etc/embed/.env
	•	Logs: /var/log/embed/stdout.log and /var/log/embed/stderr.log
	•	Systemd unit: /etc/systemd/system/embed.service

Configuration

Runtime settings are in /etc/embed/.env. Example:

HOST=0.0.0.0
PORT=8000
QDRANT_URL=http://lab-1-db01:6333
PG_DSN=postgresql://user:pass@lab-1-db01:5432/dbname
EMBED_MODEL=nomic-embed-text-v1

Keep only a template (.env.example) in Git. Never commit real secrets.

Service management

Check status: systemctl status embed
Start: sudo systemctl start embed
Stop: sudo systemctl stop embed
Restart: sudo systemctl restart embed
Logs (journal): journalctl -u embed -f
Logs (files): tail -f /var/log/embed/stdout.log

Health check
	•	/docs = FastAPI auto docs
	•	/health = optional simple status
	•	Quick test: curl -s http://localhost:8000/health || curl -s http://localhost:8000/docs | head

Updating code
	1.	In ~/rag-lab, pull latest dev branch
cd ~/rag-lab
git checkout dev
git pull origin dev
	2.	Sync to runtime location
rsync -a –delete ~/rag-lab/EmbedGeneration/ /opt/rag-lab/EmbedGeneration/
	3.	Restart service
sudo systemctl restart embed
	4.	Verify
curl -s http://localhost:8000/health

Dependencies

Virtual environment lives at /opt/venvs/embed.
To update packages:
source /opt/venvs/embed/bin/activate
pip install -r /opt/rag-lab/EmbedGeneration/requirements.txt
deactivate