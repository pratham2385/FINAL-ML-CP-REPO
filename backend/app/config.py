"""
backend/app/config.py
Configuration settings for the FastAPI application with PostgreSQL database integration.
"""

import os
from typing import List
from urllib.parse import quote_plus
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from backend/.env if available, fallback to root .env
backend_env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
if os.path.exists(backend_env_path):
    load_dotenv(backend_env_path)
else:
    load_dotenv()

def get_default_database_url() -> str:
    """Builds a valid PostgreSQL connection string if DATABASE_URL is not set directly."""
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url
    
    user = os.getenv("DB_USER", "postgres")
    raw_pass = os.getenv("DB_PASSWORD", "")
    # URL-encode password to handle special characters like '@'
    password = quote_plus(raw_pass) if raw_pass else ""
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    dbname = os.getenv("DB_NAME", "phishing_detection_db")
    
    auth = f"{user}:{password}@" if password else f"{user}@"
    return f"postgresql+psycopg://{auth}{host}:{port}/{dbname}"

def get_default_test_database_url() -> str:
    """Builds a valid PostgreSQL test connection string."""
    test_db_url = os.getenv("TEST_DATABASE_URL")
    if test_db_url:
        return test_db_url
    
    user = os.getenv("DB_USER", "postgres")
    raw_pass = os.getenv("DB_PASSWORD", "")
    password = quote_plus(raw_pass) if raw_pass else ""
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    dbname = os.getenv("TEST_DB_NAME", "phishing_detection_test_db")
    
    auth = f"{user}:{password}@" if password else f"{user}@"
    return f"postgresql+psycopg://{auth}{host}:{port}/{dbname}"

class Settings(BaseModel):
    PROJECT_NAME: str = "Email Spam and Phishing Detection API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = (
        "Enterprise-grade REST API powering real-time email spam detection, "
        "hyperlink phishing analysis, composite threat assessment, and PostgreSQL history persistence."
    )
    API_PREFIX: str = "/api"
    
    # Paths
    BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    MODELS_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "outputs", "models"))
    
    # Database Settings
    DATABASE_URL: str = get_default_database_url()
    TEST_DATABASE_URL: str = get_default_test_database_url()
    
    # Server settings
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

    # File and Batch Upload Limits
    MAX_FILES_PER_BATCH: int = int(os.getenv("MAX_FILES_PER_BATCH", "100"))
    MAX_FILE_SIZE_BYTES: int = int(os.getenv("MAX_FILE_SIZE_BYTES", str(10 * 1024 * 1024)))
    MAX_BATCH_SIZE_BYTES: int = int(os.getenv("MAX_BATCH_SIZE_BYTES", str(100 * 1024 * 1024)))
    MAX_CONCURRENT_EMAIL_ANALYSIS: int = int(os.getenv("MAX_CONCURRENT_EMAIL_ANALYSIS", "5"))
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "*"
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

settings = Settings()
