# embed_server.py
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import uvicorn

app = FastAPI()

print("🧠 Loading model 'nomic-ai/nomic-embed-text-v1'...")
model = SentenceTransformer("nomic-ai/nomic-embed-text-v1", trust_remote_code=True)
print("✅ Model loaded.")

class EmbedRequest(BaseModel):
    texts: list[str]

class EmbedResponse(BaseModel):
    embeddings: list[list[float]]

@app.post("/embed", response_model=EmbedResponse)
async def embed(req: EmbedRequest):
    embeddings = model.encode(req.texts, convert_to_numpy=True).tolist()
    return {"embeddings": embeddings}

if __name__ == "__main__":
    uvicorn.run("embed_server:app", host="0.0.0.0", port=8000, reload=False)