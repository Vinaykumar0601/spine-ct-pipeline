import os
from pathlib import Path

import boto3
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
BUCKET = os.getenv("S3_BUCKET")
LOG_PATH = Path("logs/acquisition_log.csv")
OUT_PATH = Path("logs/s3_manifest.csv")

s3 = boto3.client(
    "s3",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)


def upload_and_verify(local_path, s3_key):
    """Upload one file, then check the cloud copy is the same size."""
    s3.upload_file(str(local_path), BUCKET, s3_key)
    cloud_size = s3.head_object(Bucket=BUCKET, Key=s3_key)["ContentLength"]
    local_size = Path(local_path).stat().st_size
    return cloud_size == local_size


log = pd.read_csv(LOG_PATH)
rows = []
for _, scan in log.iterrows():
    ct_key = f"verse19/validation/{scan['patient_id']}/{Path(scan['ct_file']).name}"
    mask_key = f"verse19/validation/{scan['patient_id']}/{Path(scan['mask_file']).name}"

    ct_ok = upload_and_verify(scan["ct_file"], ct_key)
    mask_ok = upload_and_verify(scan["mask_file"], mask_key)

    rows.append({
        "scan_id": scan["scan_id"],
        "s3_ct_path": f"s3://{BUCKET}/{ct_key}",
        "s3_mask_path": f"s3://{BUCKET}/{mask_key}",
        "upload_verified": ct_ok and mask_ok,
    })
    print(f"Uploaded: {scan['scan_id']}  verified={ct_ok and mask_ok}")

manifest = pd.DataFrame(rows)
manifest.to_csv(OUT_PATH, index=False)

print("\n--- Summary ---")
print(f"Scans uploaded: {len(manifest)}")
print(f"Failed verification: {(~manifest['upload_verified']).sum()}")
print(f"Saved to {OUT_PATH}")