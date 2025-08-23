# UI

Development workspace for the UI module.
Runtime code lives at /opt/rag-lab/UI (systemd service: ui or ui@<user>).

Update flow:
1) Edit here and commit.
2) ./deploy/sync_and_restart.sh
3) Check http://<vm-ip>:8501/
