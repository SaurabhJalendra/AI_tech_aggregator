from pathlib import Path

from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # Environment
    environment: str = "development"
    debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://advisor:advisor_dev_password@localhost:5433/ai_advisor"
    database_url_sync: str = "postgresql://advisor:advisor_dev_password@localhost:5433/ai_advisor"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-20250514"
    use_claude_code: bool = True

    # Embeddings (local BGE via sentence-transformers; see src/core/embeddings.py)
    embeddings_enabled: bool = True

    # Legacy — unused when using local BGE; kept for optional future API providers
    openai_api_key: str = ""

    # Semantic intent (embedding + exemplars; heuristic planner remains fallback)
    semantic_intent_enabled: bool = True
    semantic_intent_min_confidence: float = 0.32
    semantic_intent_override_confidence: float = 0.48
    semantic_intent_override_margin: float = 0.05
    semantic_intent_clarify_low: float = 0.38
    semantic_intent_clarify_margin: float = 0.03

    # Planner authority (Phase-1): restrict LLM panel commands when playbook is active
    planner_authority_strict: bool = True
    llm_fallback_enabled: bool = True
    # Planner rollout: off | shadow | on
    planner_mode: str = "on"

    # Claude Code CLI (shared with SSE keepalive budget — allow headroom over keepalive interval)
    claude_code_timeout_seconds: int = 180
    claude_code_windows_max_concurrent: int = 8
    sse_keepalive_interval_seconds: int = 15

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

    @property
    def planner_mode_normalized(self) -> str:
        mode = (self.planner_mode or "on").lower().strip()
        if mode not in ("off", "shadow", "on"):
            return "on"
        return mode


settings = Settings()
