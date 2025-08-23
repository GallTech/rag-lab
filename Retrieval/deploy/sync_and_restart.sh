#!/usr/bin/env bash
set -euo pipefail
REPO="${1:-$HOME/rag-lab/Retrieval}"
RUNTIME="/opt/rag-lab/Retrieval"
rsync -a --delete "$REPO"/ "$RUNTIME"/
sudo systemctl restart retrieval
echo "Deployed from $REPO to $RUNTIME and restarted retrieval."
