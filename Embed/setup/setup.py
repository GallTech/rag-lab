# setup.py
import os
import subprocess
from pathlib import Path

VENV_DIR = Path("venv")
REQUIREMENTS = [
    "fastapi",
    "uvicorn[standard]",
    "transformers",
    "torch",
    "pydantic",
    "python-dotenv",
    "sentence-transformers",
    "einops"
    ]

MODEL_NAME = "nomic-ai/nomic-embed-text-v1"

# Step 1: Create virtual environment
if not VENV_DIR.exists():
    print("🐍 Creating virtual environment...")
    subprocess.run(["python3", "-m", "venv", str(VENV_DIR)], check=True)

# Step 2: Install requirements
print("📦 Installing dependencies...")
pip_path = VENV_DIR / "bin" / "pip"
subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
subprocess.run([str(pip_path), "install"] + REQUIREMENTS, check=True)

# Step 3: Download model
print(f"⬇️  Downloading model '{MODEL_NAME}'...")
python_path = VENV_DIR / "bin" / "python"
subprocess.run([
    str(python_path),
    "-c",
    f"from sentence_transformers import SentenceTransformer; SentenceTransformer('{MODEL_NAME}', trust_remote_code=True)"
], check=True)

print("✅ Setup complete. To start the server: source venv/bin/activate && python setup/embed_server.py")