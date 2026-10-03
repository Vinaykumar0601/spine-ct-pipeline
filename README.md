# Spine CT Data Acquisition Pipeline

A small end-to-end data pipeline that acquires public spine CT scans, records provenance and licensing, extracts imaging metadata, stores files in AWS S3, loads a searchable metadata catalog into Snowflake, and runs SQL data quality checks.

I built this as a learning project to practice the data foundations work behind AI/ML development for surgical imaging: making sure data is complete, correctly labeled, legally usable, and traceable before anyone trains a model on it.

## Architecture

1. **Acquire:** VerSe spine CT scans downloaded into a read-only local raw zone
2. **Log and extract (Python):** acquisition log with provenance and fingerprints, then imaging metadata
3. **Store:** scans and masks in AWS S3, metadata catalog in Snowflake
4. **Check:** SQL quality checks on the Snowflake table

## Pipeline steps

| Step | Script | Output |
|---|---|---|
| 1. Acquisition log | `scripts/build_acquisition_log.py` | `logs/acquisition_log.csv`: scan and patient IDs, mask pairing, file size, SHA-256 fingerprint, source, license |
| 2. Metadata extraction | `scripts/extract_metadata.py` | `metadata/scan_metadata.csv`: dimensions, voxel spacing, slice thickness, mask alignment, vertebrae present |
| 3. Upload to S3 | `scripts/upload_to_s3.py` | `logs/s3_manifest.csv`: S3 path for each scan and mask, size-verified |
| 4. Load to Snowflake | `scripts/load_to_snowflake.py` | `SPINE_CT.RAW.SCAN_METADATA` table, joined by scan ID, idempotent overwrite |
| 5. Quality checks | `sql/04_quality_checks.sql` | One-table quality report |

## Results (VerSe 2019 validation set)

- 40 CT scans from 37 patients, each paired with its segmentation mask
- 0 read errors, 0 misaligned masks, 0 duplicate files, 40 of 40 uploads verified
- Slice thickness: 21 scans at 1.0 mm, 14 at 2.0 mm, 5 at 3.0 mm (one value stored as 2.001 mm was standardized to 2.0)
- Coverage: 31 scans include lumbar vertebrae, 32 thoracic, 13 cervical

### Quality report

| Check | Issues |
|---|---|
| Duplicate scan IDs | 0 |
| Missing required fields | 0 |
| Mask missing or misaligned | 0 |
| Upload not verified | 0 |
| Slice thickness out of range | 0 |
| Fewer than 3 vertebrae labeled | 1 |
| Patients with multiple scans | 3 |

## Known dataset notes

- Patients `sub-verse400`, `sub-verse404`, and `sub-verse412` each have two scans. Train and test splits should group by patient to avoid data leakage.
- `sub-verse116` has only one labeled vertebra (L5) and is flagged for annotation review.
- The cervical spine is underrepresented (13 of 40 scans).
- Slice thickness varies from 1 to 3 mm, so high-precision use cases may need to filter to 1 mm scans.

## Security and access design

- Separate service identities for the pipeline, never personal logins
  - AWS: an IAM user whose policy allows access to one bucket only
  - Snowflake: a service user (`TYPE = SERVICE`) whose role is limited to the `SPINE_CT.RAW` schema
- Snowflake key-pair authentication, so no passwords are used in code
- Credentials live in a local `.env` file excluded by `.gitignore`; `.env.example` lists the required variables
- The S3 bucket blocks all public access and uses default encryption
- Raw data is never modified; every derived output is written separately

## How to run

1. Create the environment: `conda create -n spinect python=3.12 -y`, then `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in your own values
3. Run `sql/01` to `sql/03` in Snowflake
4. Download the VerSe 2019 validation set into `data/raw/`
5. Run the scripts in order: acquisition log, metadata, S3 upload, Snowflake load
6. Run `sql/04_quality_checks.sql`

## What I would change for production

- Store credentials in a secrets manager with automatic rotation instead of a `.env` file
- Orchestrate the steps with a scheduler such as Airflow, with retries and failure alerts
- Verify uploads with checksums, not only file size
- Keep S3 and Snowflake in the same region (here, S3 is in us-east-1 and Snowflake in ca-central-1)
- Separate dev and production environments, and turn the quality checks into automated alerts

## Data source and license

Data: VerSe 2019 (Large Scale Vertebrae Segmentation Challenge), https://github.com/anjany/verse, provided under the CC BY-SA 4.0 license. This repository does not include any image data.

Citations:
1. Sekuboyina A et al., VerSe: A Vertebrae Labelling and Segmentation Benchmark for Multi-detector CT Images. Medical Image Analysis, 2021.
2. Löffler M et al., A Vertebral Segmentation Dataset with Fracture Grading. Radiology: Artificial Intelligence, 2020.