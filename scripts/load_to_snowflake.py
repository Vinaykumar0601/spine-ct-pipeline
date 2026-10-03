import os

import pandas as pd
import snowflake.connector
from dotenv import load_dotenv
from snowflake.connector.pandas_tools import write_pandas

load_dotenv()

# 1. Read the three tables
log = pd.read_csv("logs/acquisition_log.csv")
meta = pd.read_csv("metadata/scan_metadata.csv")
s3 = pd.read_csv("logs/s3_manifest.csv")

# 2. Join them into one table, matching rows by scan_id
table = log.merge(meta.drop(columns=["patient_id"]), on="scan_id")
table = table.merge(s3, on="scan_id")

# Local Mac paths aren't useful in the cloud, so drop them
table = table.drop(columns=["ct_file", "mask_file"])

# Snowflake prefers UPPERCASE column names
table.columns = [c.upper() for c in table.columns]
print(f"Combined table: {len(table)} rows, {len(table.columns)} columns")

# 3. Connect to Snowflake as PIPELINE_USER
conn = snowflake.connector.connect(
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    user=os.getenv("SNOWFLAKE_USER"),
    authenticator="SNOWFLAKE_JWT",
    private_key_file=os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH"),
    role=os.getenv("SNOWFLAKE_ROLE"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    database=os.getenv("SNOWFLAKE_DATABASE"),
    schema=os.getenv("SNOWFLAKE_SCHEMA"),
)

# 4. Send the table (overwrite=True makes reruns safe)
success, _, nrows, _ = write_pandas(
    conn, table, "SCAN_METADATA", auto_create_table=True, overwrite=True
)
print(f"Loaded to Snowflake: {success}, rows sent: {nrows}")

# 5. Verify by counting rows inside Snowflake
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM SCAN_METADATA")
print(f"Rows in Snowflake table: {cur.fetchone()[0]}")

cur.close()
conn.close()