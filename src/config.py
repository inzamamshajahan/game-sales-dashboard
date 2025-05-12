# src/config.py
import os
from dotenv import load_dotenv
import json # For potential parsing of secrets from Secrets Manager

# Load .env file primarily for local Docker Compose setup via docker-compose.yml environment section
# In deployed envs, these vars might be set directly by CD script or instance profile for Secrets Manager
load_dotenv()

# For deployed environments, we'll aim to get DB_SECRET_NAME, and then fetch details
# from AWS Secrets Manager.
# For local Docker Compose, the DB_HOST_LOCAL etc. are set in docker-compose.yml

# Priority:
# 1. Specific deployment environment variables (e.g., set by CD script AFTER fetching from Secrets Manager)
# 2. Local Docker Compose environment variables (e.g., DB_HOST_LOCAL from .env via docker-compose.yml)
# 3. Hardcoded defaults (least desirable, mostly for 'db' service name or local testing)

APP_ENV = os.getenv("APP_ENV", "local") # 'local', 'test', 'prod'

def get_db_params_from_secrets_manager(secret_name_env_var="DB_SECRET_NAME_FROM_SM"):
    """
    Fetches DB connection parameters from AWS Secrets Manager.
    This function would be primarily used by the application running on EC2.
    """
    secret_name = os.getenv(secret_name_env_var)
    if not secret_name:
        return None

    try:
        import boto3 # Moved import here to avoid error if boto3 not needed/installed locally for other modes
        session = boto3.session.Session()
        client = session.client(service_name='secretsmanager', region_name=os.getenv("AWS_REGION", "us-east-1")) # Ensure AWS_REGION is set
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        if 'SecretString' in get_secret_value_response:
            secret = json.loads(get_secret_value_response['SecretString'])
            return {
                "host": secret.get("DB_HOST"),
                "database": secret.get("DB_NAME"),
                "user": secret.get("DB_USER"),
                "password": secret.get("DB_PASSWORD"),
                "port": secret.get("DB_PORT", 5432), # Default port if not in secret
            }
    except Exception as e:
        print(f"Error fetching secret from Secrets Manager ({secret_name}): {e}")
    return None


# Determine connection parameters
# In a real deployed scenario on EC2, the EC2 instance role would allow fetching the secret.
# The CD script would set DB_SECRET_NAME_FROM_SM.
secrets_manager_params = None
if APP_ENV != "local": # Attempt to use Secrets Manager if not explicitly local
    secrets_manager_params = get_db_params_from_secrets_manager()

if secrets_manager_params:
    DATABASE_CONNECTION_PARAMS = secrets_manager_params
    print(f"--- Config: Using DB parameters from AWS Secrets Manager for {APP_ENV} ---")
else:
    # Fallback to local .env-driven or docker-compose env vars for local/ETL script
    DATABASE_CONNECTION_PARAMS = {
        "host": os.getenv("DB_HOST_LOCAL", "db"), # 'db' for compose, 'localhost' if etl.py ran directly on host
        "database": os.getenv("DB_NAME_LOCAL", "gamedb_local"),
        "user": os.getenv("DB_USER_LOCAL", "localuser"),
        "password": os.getenv("DB_PASSWORD_LOCAL", "localpass"),
        "port": os.getenv("DB_PORT_LOCAL", "5432"),
    }
    print(f"--- Config: Using local/Compose DB parameters for {APP_ENV} ---")


# For debugging:
print(f"APP_ENV: {APP_ENV}")
print(f"DB_HOST: {DATABASE_CONNECTION_PARAMS.get('host')}")
print(f"DB_NAME: {DATABASE_CONNECTION_PARAMS.get('database')}")
print(f"DB_USER: {DATABASE_CONNECTION_PARAMS.get('user')}")
# Avoid printing password in real logs
print(f"DB_PORT: {DATABASE_CONNECTION_PARAMS.get('port')}")
print(f"---------------------")