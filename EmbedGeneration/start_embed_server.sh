#!/bin/bash
source /home/mike/embed-venv/bin/activate
exec uvicorn embed_server:app --host 0.0.0.0 --port 8000
