#!/bin/bash

set -e

# === Config ===
SERVICE_NAME="qdrant-docker"
CONTAINER_NAME="qdrant"
DATA_DIR="/home/mike/qdrant/storage"
PORT="6333"
QDRANT_VERSION="v1.9.1"

echo "📁 Creating storage directory..."
mkdir -p "$DATA_DIR"

echo "🐳 Pulling Qdrant Docker image..."
docker pull qdrant/qdrant:$QDRANT_VERSION

echo "🚀 Running Qdrant container..."
docker run -d \
  --name $CONTAINER_NAME \
  -p $PORT:6333 \
  -v "$DATA_DIR:/qdrant/storage" \
  --restart unless-stopped \
  qdrant/qdrant:$QDRANT_VERSION

echo "🛠️  Creating systemd service..."

sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=Qdrant Vector Search Engine (Docker)
After=network.target docker.service
Requires=docker.service

[Service]
Restart=always
ExecStart=/usr/bin/docker start -a $CONTAINER_NAME
ExecStop=/usr/bin/docker stop $CONTAINER_NAME

[Install]
WantedBy=multi-user.target
EOF

echo "🔁 Enabling and starting systemd service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

echo "✅ Qdrant is now running as a systemd service at http://localhost:$PORT"
