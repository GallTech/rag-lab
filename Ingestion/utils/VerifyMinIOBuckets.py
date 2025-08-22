import boto3, botocore
s3 = boto3.client(
    "s3",
    endpoint_url="http://192.168.0.17:9000",
    aws_access_key_id="admin",
    aws_secret_access_key="Thomas@8234",
    region_name="eu-west-1",
)
print("Buckets:", [b["Name"] for b in s3.list_buckets().get("Buckets", [])])
try:
    s3.head_bucket(Bucket="papers")
    print("OK: 'papers' exists")
    # sample list to prove contents
    resp = s3.list_objects_v2(Bucket="papers", MaxKeys=5)
    print("Sample keys:", [o["Key"] for o in resp.get("Contents", [])])
except botocore.exceptions.ClientError as e:
    print("ERROR:", e.response.get("Error",{}).get("Code"), e.response.get("Error",{}).get("Message"))
PY