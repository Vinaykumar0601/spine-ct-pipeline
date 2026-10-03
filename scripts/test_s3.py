import os
import boto3
from dotenv import load_dotenv

# 1. Read the secrets from the .env file
load_dotenv()
bucket = os.getenv("S3_BUCKET")
region = os.getenv("AWS_REGION")

# 2. Log into AWS S3 using the pipeline-user keys
s3 = boto3.client(
    "s3",
    region_name=region,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

# 3. Upload a tiny test file
s3.put_object(
    Bucket=bucket,
    Key="tests/hello.txt",
    Body=b"Hello from my spine CT pipeline!",
)
print("Uploaded tests/hello.txt")

# 4. List what's in the bucket to confirm
response = s3.list_objects_v2(Bucket=bucket, Prefix="tests/")
for item in response.get("Contents", []):
    print("Found in bucket:", item["Key"], "-", item["Size"], "bytes")