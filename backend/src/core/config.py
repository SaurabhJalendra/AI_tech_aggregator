from pathlib import Path

from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


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

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Prefer backend/.env for local dev so stale shell variables do not
        # accidentally switch the LLM backend from Claude Code to SDK mode.
        return init_settings, dotenv_settings, env_settings, file_secret_settings

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
