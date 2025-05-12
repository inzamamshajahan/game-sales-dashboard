
# src/config.py
import os
from dotenv import load_dotenv

# Load .env file primarily for local Docker Compose setup
# In deployed envs, these vars might be set directly or via other means
load_dotenv()

# Use consistent variable names, checking first for deployment-specific names,
# then local Docker Compose names (from .env), then defaults.
# Deployment env vars would be set by the CD script later (e.g., using AWS Secrets Manager)
DB_HOST = os.getenv("DB_HOST", os.getenv("DB_HOST_LOCAL", "db")) # Default to 'db' for compose
DB_NAME = os.getenv("DB_NAME", os.getenv("DB_NAME_LOCAL", "gamedb_local"))
DB_USER = os.getenv("DB_USER", os.getenv("DB_USER_LOCAL", "localuser"))
DB_PASSWORD = os.getenv("DB_PASSWORD", os.getenv("DB_PASSWORD_LOCAL", "localpass"))
DB_PORT = os.getenv("DB_PORT", os.getenv("DB_PORT_LOCAL", "5432"))

# Variable to distinguish environment (useful later)
APP_ENV = os.getenv("APP_ENV", "local") # Default to 'local' if not set

# Example of how you might use it elsewhere:
DATABASE_CONNECTION_PARAMS = {
    "host": DB_HOST,
    "database": DB_NAME,
    "user": DB_USER,
    "password": DB_PASSWORD,
    "port": DB_PORT,
}

print(f"--- Config Loaded ---") # Add print statements for debugging if needed
print(f"APP_ENV: {APP_ENV}")
print(f"DB_HOST: {DB_HOST}")
print(f"DB_NAME: {DB_NAME}")
print(f"DB_USER: {DB_USER}")
# Avoid printing password in real logs
# print(f"DB_PASSWORD: {'*' * len(DB_PASSWORD) if DB_PASSWORD else 'None'}")
print(f"DB_PORT: {DB_PORT}")
print(f"---------------------")

