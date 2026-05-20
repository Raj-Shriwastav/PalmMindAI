from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # PostgreSQL Configuration
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="palmmind_test_secure_pass_2026")
    POSTGRES_DB: str = Field(default="palmmind_db")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)

    # CORS Configuration
    CORS_ORIGINS: str = Field(default="*")

    # Redis Configuration
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)

    # Qdrant Configuration
    QDRANT_HOST: str = Field(default="localhost")
    QDRANT_PORT: int = Field(default=6333)
    QDRANT_COLLECTION_NAME: str = Field(default="palmmind_rag")

    # LLM (llama.cpp) Configuration
    LLM_BASE_URL: str = Field(default="http://localhost:12434/v1")
    LLM_API_KEY: str = Field(default="not-needed")
    LLM_MODEL_NAME: str = Field(default="Qwen3.5-4B-Q4_K_S.gguf")

    # Embeddings Configuration
    EMBEDDING_MODEL_NAME: str = Field(default="Snowflake/snowflake-arctic-embed-m")

    # SMTP Configuration (Optional Real Email triggers)
    SMTP_HOST: Optional[str] = Field(default=None)
    SMTP_PORT: int = Field(default=587)
    SMTP_USERNAME: Optional[str] = Field(default=None)
    SMTP_PASSWORD: Optional[str] = Field(default=None)
    SMTP_SENDER: Optional[str] = Field(default=None)

    @property
    def postgres_url(self) -> str:
        """Construct PostgreSQL connection DSN."""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()
