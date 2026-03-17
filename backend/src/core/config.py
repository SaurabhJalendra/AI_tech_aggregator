from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Environment
    environment: str = "development"
    debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://advisor:advisor_dev_password@localhost:5432/ai_advisor"
    database_url_sync: str = "postgresql://advisor:advisor_dev_password@localhost:5432/ai_advisor"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-20250514"
    use_claude_code: bool = True

    # OpenAI (for embeddings)
    openai_api_key: str = ""

    # Auth
    nextauth_secret: str = "dev-secret-change-in-production"
    nextauth_url: str = "http://localhost:3000"

    # Backend
    backend_url: str = "http://localhost:8000"
    cors_origins: str = "http://localhost:3000"

    # Rate limiting
    free_tier_conversations_per_day: int = 10
    free_tier_comparisons_per_day: int = 10
    free_tier_max_cost_per_session: float = 0.50

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
