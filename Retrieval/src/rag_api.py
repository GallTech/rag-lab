import os
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="RAG Retrieval API", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok"}

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

@app.post("/search")
def search(req: SearchRequest):
    # TODO: wire to Qdrant + Postgres using env vars:
    # QDRANT_URL, PG_DSN, EMBED_ENDPOINT
    return {
        "query": req.query,
        "top_k": req.top_k,
        "results": [
            {"id": f"mock-{i+1}", "text": "Example passage …", "score": 0.75 - i*0.05}
            for i in range(req.top_k)
        ],
    }
