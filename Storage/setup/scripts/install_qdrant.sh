#!/bin/bash
set -e

echo "[*] Updating system..."
sudo apt update && sudo apt upgrade -y

echo "[*] Installing Docker & Docker Compose..."
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

echo "[*] Creating Qdrant data folder..."
sudo mkdir -p /opt/qdrant/data
sudo mkdir -p /opt/qdrant/config

echo "[*] Creating docker-compose.yml for Qdrant..."
cat <<EOF | sudo tee /opt/qdrant/docker-compose.yml
version: "3.9"
services:
  qdrant:
    image: qdrant/qdrant:v1.9.0
    container_name: qdrant
    restart: unless-stopped
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - /opt/qdrant/data:/qdrant/storage
EOF

echo "[*] Starting Qdrant..."
cd /opt/qdrant
sudo docker compose up -d

echo "[*] Qdrant should now be running on port 6333!"
echo "Test with: curl http://localhost:6333/collections"