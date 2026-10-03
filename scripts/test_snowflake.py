import os
import snowflake.connector
from dotenv import load_dotenv

# 1. Read the settings from .env
load_dotenv()

# 2. Log into Snowflake as PIPELINE_USER using the private key
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
cur = conn.cursor()

# 3. Ask Snowflake: who am I and where am I?
cur.execute("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_DATABASE(), CURRENT_SCHEMA()")
print("Connected as:", cur.fetchone())

# 4. Create a tiny test table, add one row, read it back
cur.execute("CREATE TABLE IF NOT EXISTS CONNECTION_TEST (message STRING)")
cur.execute("INSERT INTO CONNECTION_TEST VALUES ('Hello from my spine CT pipeline!')")
cur.execute("SELECT message FROM CONNECTION_TEST")
print("Read back:", cur.fetchall())

# 5. Close the connection
cur.close()
conn.close()
