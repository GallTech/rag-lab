from minio import Minio
from datetime import datetime
import subprocess

# === Config ===
MINIO_HOST = "192.168.0.17:9000"
ACCESS_KEY = "admin"
SECRET_KEY = "adminsecret"
PAPERS_BUCKET = "papers"
MC_ALIAS = "local"  # The alias name in your `mc` config

# === Connect ===
client = Minio(
    MINIO_HOST,
    access_key=ACCESS_KEY,
    secret_key=SECRET_KEY,
    secure=False
)

def bucket_stats(bucket_name):
    """Return (count, total_size_bytes) for a bucket."""
    count = 0
    total_size = 0
    for obj in client.list_objects(bucket_name, recursive=True):
        count += 1
        total_size += obj.size
    return count, total_size

print(f"=== MinIO Bucket Diagnostics ({datetime.now().isoformat(timespec='seconds')}) ===\n")

# List all buckets and sizes
buckets = client.list_buckets()
for b in buckets:
    count, size = bucket_stats(b.name)
    print(f"{b.name:<20} {count:>10,} objects   {size/1024/1024/1024:>10.2f} GB")

# Extra check for 'papers'
print(f"\n--- Extra checks for '{PAPERS_BUCKET}' ---")
count, size = bucket_stats(PAPERS_BUCKET)
print(f"{PAPERS_BUCKET} bucket: {count:,} objects, {size/1024/1024/1024:.2f} GB")

# Incomplete uploads using mc CLI
print("\n--- Incomplete uploads ---")
cmd = ["mc", "ls", "--incomplete", "-r", f"{MC_ALIAS}/{PAPERS_BUCKET}"]
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode == 0:
    if result.stdout.strip():
        print(result.stdout.strip())
    else:
        print("None found.")
else:
    print(f"Error running mc: {result.stderr.strip()}")
