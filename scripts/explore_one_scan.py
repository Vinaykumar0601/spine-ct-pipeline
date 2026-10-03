import nibabel as nib
import numpy as np

# Open one CT scan and its mask
ct = nib.load("data/raw/dataset-verse19validation/rawdata/sub-verse030/sub-verse030_ct.nii.gz")
mask = nib.load("data/raw/dataset-verse19validation/derivatives/sub-verse030/sub-verse030_seg-vert_msk.nii.gz")

# Facts about the CT scan
print("CT shape (voxels):", ct.shape)
print("Voxel size (mm):", ct.header.get_zooms())

# Does the mask line up with the scan?
print("Mask same shape as CT:", mask.shape == ct.shape)

# Which labels (vertebrae) are in the mask?
labels = np.unique(np.asarray(mask.dataobj))
print("Labels in mask:", labels)