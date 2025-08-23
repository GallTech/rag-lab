#!/usr/bin/env bash
set -euo pipefail
REPO="${1:-$HOME/rag-lab/UI}"
RUNTIME="/opt/rag-lab/UI"
rsync -a --delete "$REPO"/ "$RUNTIME"/
sudo systemctl restart ui || sudo systemctl restart "ui@$USER"
echo "Deployed from $REPO to $RUNTIME and restarted service."
