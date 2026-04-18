from pathlib import Path
from typing import Literal
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Fail-fast configuration validator for CDD Orchestrator.
    All business logic constants must reside here.
    """
    # Infrastructure
    ENV: Literal["development", "production", "test"] = "development"
    TEMPORAL_ENDPOINT: str = Field(default="localhost:7233")
    DATABASE_URL: str = Field(default="sqlite:///./cdd_state.db")
    
    # LLM Settings (via LiteLLM)
    OPENAI_API_KEY: SecretStr
    ANTHROPIC_API_KEY: SecretStr
    DEFAULT_MODEL: str = "claude-3-opus-20240229"
    
    # Sandbox Settings
    DOCKER_IMAGE_PYTHON: str = "python:3.11-slim"
    SANDBOX_TIMEOUT_SECONDS: int = 300
    
    # Business Logic (No Magic Numbers in Code)
    PHASE1_PARALLELISM: int = 5
    RETRY_MAX_ATTEMPTS: int = 3
    RATE_LIMIT_LOGIN_PER_MIN: int = 5

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_db_url(cls, v: str) -> str:
        if not v.startswith("sqlite:///"):
            raise ValueError("Production CDD currently requires SQLite for Registry ACID compliance.")
        return v.strip()

# Initialize and validate immediately on import to Fail-Fast
try:
    settings = Settings()
except Exception as e:
    import sys
    print(f"CONFIGURATION ERROR: {e}")
    sys.exit(1)