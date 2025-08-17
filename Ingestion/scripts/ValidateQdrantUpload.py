import requests, uuid

Q = "http://192.168.0.11:6333"
COLL = "openalex"
DIM = 768

vec = [0.0]*DIM
cid = str(uuid.uuid4())
payload = {"work_id":"test://smoke", "chunk_id":cid, "chunk_index":0, "source":"openalex"}
requests.put(f"{Q}/collections/{COLL}/points",
             json={"points":[{"id": cid, "vector": vec, "payload": payload}]}).raise_for_status()

# ✅ count (POST with JSON body)
print(requests.post(f"{Q}/collections/{COLL}/points/count",
                    json={"exact": True}).json())

requests.post(f"{Q}/collections/{COLL}/points/delete", json={"points":[cid]}).raise_for_status()
print(requests.post(f"{Q}/collections/{COLL}/points/count",
                    json={"exact": True}).json())
