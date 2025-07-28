#!/bin/bash
set -e

echo "[*] Updating system..."
sudo apt update && sudo apt upgrade -y

echo "[*] Installing basic tools..."
sudo apt install -y wget unzip python3-pip

echo "[*] Installing DuckDB CLI..."
wget https://github.com/duckdb/duckdb/releases/download/v0.10.2/duckdb_cli-linux-amd64.zip
unzip duckdb_cli-linux-amd64.zip
sudo mv duckdb /usr/local/bin/
rm duckdb_cli-linux-amd64.zip

echo "[*] Installing DuckDB Python bindings..."
pip3 install duckdb --upgrade

echo "[*] Creating default metadata folder..."
mkdir -p ~/duckdb_data

echo "[*] Done! Test with: duckdb :memory:"