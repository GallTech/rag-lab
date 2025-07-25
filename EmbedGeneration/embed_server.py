from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

# Load better-quality model
model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

app = FastAPI()

class EmbedRequest(BaseModel):
    text: str

@app.post("/embed")
def embed_text(req: EmbedRequest):
    vector = model.encode(req.text).tolist()
    return {"embedding": vector, "dim": len(vector)}