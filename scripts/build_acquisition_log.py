import hashlib
from datetime import date
from pathlib import Path

import pandas as pd

# ---------- Settings ----------
RAW_DIR = Path("data/raw/dataset-verse19validation")
LOG_PATH = Path("logs/acquisition_log.csv")

SOURCE = "VerSe 2019 validation set"
SOURCE_URL = "https://s3.bonescreen.de/public/VerSe-complete/dataset-verse19validation.zip"
LICENSE = "CC BY-SA 4.0"
DOWNLOAD_DATE = "2026-10-02"


# ---------- Helper: create a file fingerprint ----------
def sha256_of(path):
    """Read the file in 1 MB pieces and build its SHA-256 fingerprint."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------- Main: one row per CT scan ----------
rows = []
for ct_path in sorted(RAW_DIR.glob("rawdata/*/*_ct.nii.gz")):
    patient_id = ct_path.parent.name
    scan_id = ct_path.name.replace("_ct.nii.gz", "")
    mask_path = RAW_DIR / "derivatives" / patient_id / f"{scan_id}_seg-vert_msk.nii.gz"

    rows.append({
        "scan_id": scan_id,
        "patient_id": patient_id,
        "ct_file": str(ct_path),
        "mask_file": str(mask_path) if mask_path.exists() else "",
        "mask_found": mask_path.exists(),
        "ct_size_mb": round(ct_path.stat().st_size / 1_000_000, 2),
        "ct_sha256": sha256_of(ct_path),
        "source_dataset": SOURCE,
        "source_url": SOURCE_URL,
        "license": LICENSE,
        "download_date": DOWNLOAD_DATE,
        "deidentified": "Yes (provided anonymized as NIfTI)",
        "logged_at": date.today().isoformat(),
    })

# ---------- Save and summarize ----------
log = pd.DataFrame(rows)
LOG_PATH.parent.mkdir(exist_ok=True)
log.to_csv(LOG_PATH, index=False)

print(f"Scans logged: {len(log)}")
print(f"Unique patients: {log['patient_id'].nunique()}")
print(f"Scans missing a mask: {(~log['mask_found']).sum()}")
print(f"Duplicate files (same fingerprint): {log['ct_sha256'].duplicated().sum()}")
print(f"Saved to {LOG_PATH}")
