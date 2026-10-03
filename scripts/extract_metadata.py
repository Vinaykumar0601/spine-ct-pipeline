from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd

LOG_PATH = Path("logs/acquisition_log.csv")
OUT_PATH = Path("metadata/scan_metadata.csv")


def label_name(n):
    """Turn a mask number into a vertebra name, like 20 -> L1."""
    if 1 <= n <= 7:
        return f"C{n}"
    if 8 <= n <= 19:
        return f"T{n - 7}"
    if 20 <= n <= 25:
        return f"L{n - 19}"
    if n == 28:
        return "T13"
    return f"other_{n}"


# Use the acquisition log as our list of scans
log = pd.read_csv(LOG_PATH)

rows = []
for _, scan in log.iterrows():
    row = {"scan_id": scan["scan_id"], "patient_id": scan["patient_id"], "read_error": ""}
    try:
        ct = nib.load(scan["ct_file"])
        mask = nib.load(scan["mask_file"])

        x, y, z = ct.shape[:3]
        sx, sy, sz = [round(float(v), 2) for v in ct.header.get_zooms()[:3]]
        labels = [int(v) for v in np.unique(np.asarray(mask.dataobj)) if v != 0]
        names = [label_name(v) for v in labels]

        row.update({
            "width_voxels": x,
            "height_voxels": y,
            "num_slices": z,
            "voxel_x_mm": sx,
            "voxel_y_mm": sy,
            "slice_thickness_mm": sz,
            "mask_matches_ct": mask.shape == ct.shape,
            "num_vertebrae": len(names),
            "vertebrae": ",".join(names),
            "has_cervical": any(n.startswith("C") for n in names),
            "has_thoracic": any(n.startswith("T") for n in names),
            "has_lumbar": any(n.startswith("L") for n in names),
        })
    except Exception as e:
        row["read_error"] = str(e)

    rows.append(row)
    print(f"Done: {scan['scan_id']}")

# Save the table
meta = pd.DataFrame(rows)
OUT_PATH.parent.mkdir(exist_ok=True)
meta.to_csv(OUT_PATH, index=False)

# Summary
ok = meta[meta["read_error"] == ""]
print("\n--- Summary ---")
print(f"Scans processed: {len(meta)}")
print(f"Read errors: {len(meta) - len(ok)}")
print(f"Masks not lined up: {(ok['mask_matches_ct'] == False).sum()}")
print(f"Slice thickness: {ok['slice_thickness_mm'].min()} to {ok['slice_thickness_mm'].max()} mm")
print(f"Scans with lumbar: {ok['has_lumbar'].sum()}")
print(f"Scans with thoracic: {ok['has_thoracic'].sum()}")
print(f"Scans with cervical: {ok['has_cervical'].sum()}")
print(f"Saved to {OUT_PATH}")