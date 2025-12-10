"""Application configuration settings."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App Settings
    app_name: str = "Enterprise Onboarding Copilot"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-this-in-production-use-long-random-string"
    
    # API Keys
    openai_api_key: str = ""
    
    # Database
    database_url: str = "sqlite:///./data/onboarding.db"
    
    # ChromaDB
    chroma_persist_directory: str = "./data/chroma_db"
    
    # MLflow
    mlflow_tracking_uri: str = "./mlruns"
    mlflow_experiment_name: str = "onboarding_router"
    
    # Rate Limiting
    rate_limit_requests: int = 60
    rate_limit_window: int = 60  # seconds
    
    # Authentication Settings
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    password_min_length: int = 8
    max_login_attempts: int = 5
    account_lockout_minutes: int = 30
    
    # Session Settings
    session_timeout_minutes: int = 60
    max_sessions_per_user: int = 5
    
    # Security Settings
    cors_origins: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    secure_cookies: bool = False  # Set to True in production with HTTPS
    
    # Model Settings
    embedding_model: str = "sentence-transformers/all-mpnet-base-v2"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.1
    
    # RAG Settings
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_retrieval: int = 5
    
    # Audit Settings
    audit_log_retention_days: int = 90
    
    # Paths
    base_dir: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = base_dir / "data"
    policies_dir: Path = data_dir / "policies"
    models_dir: Path = data_dir / "models"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Create directories if they don't exist
settings = get_settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.policies_dir.mkdir(parents=True, exist_ok=True)
settings.models_dir.mkdir(parents=True, exist_ok=True)
Path(settings.chroma_persist_directory).mkdir(parents=True, exist_ok=True)

