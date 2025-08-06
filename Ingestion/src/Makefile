# === Config ===
VENV_NAME := venv
PYTHON := $(VENV_NAME)/bin/python
PIP := $(VENV_NAME)/bin/pip

# === Python versions ===
REQS := langchain==0.2.1 pymupdf==1.24.4 psycopg2-binary==2.9.9

# === PostgreSQL ===
DB_NAME := raglab
DB_USER := mike
PSQL := psql -U $(DB_USER) -d $(DB_NAME)

# === Targets ===

all: venv install enable_pgcrypto

venv:
	@test -d $(VENV_NAME) || python3 -m venv $(VENV_NAME)
	@echo "✅ Virtualenv created."

install:
	@$(PIP) install --upgrade pip
	@$(PIP) install $(REQS)
	@echo "✅ Python packages installed."

enable_pgcrypto:
	@echo "🔐 Enabling pgcrypto extension in $(DB_NAME)..."
	@$(PSQL) -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
	@echo "✅ pgcrypto extension enabled."

run:
	@$(PYTHON) chunking_script.py

clean:
	@rm -rf $(VENV_NAME)
	@echo "🧹 Cleaned up virtual environment."