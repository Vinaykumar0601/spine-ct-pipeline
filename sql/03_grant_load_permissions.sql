USE ROLE ACCOUNTADMIN;

-- Extra permissions needed by write_pandas to load a table
GRANT CREATE STAGE, CREATE FILE FORMAT ON SCHEMA SPINE_CT.RAW TO ROLE PIPELINE_ROLE;

-- Connect the custom role under SYSADMIN so admins can see its tables
GRANT ROLE PIPELINE_ROLE TO ROLE SYSADMIN;
