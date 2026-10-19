from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration comes from environment variables (or a local .env file)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # MySQL/MariaDB in normal use. The SQLite default only exists so the app starts with zero setup.
    database_url: str = "sqlite:///./sentinel_dev.db"

    # Public testnet node (announced by the organizers on 2026-10-16). Not secrets.
    portaldot_substrate_http_url: str = "https://test-node-v3.portaldot.dev"
    network_window_blocks: int = Field(default=60, ge=10, le=100)
    network_min_refresh_seconds: float = Field(default=10, ge=0, le=3600)

    portaldot_evm_rpc_url: str = ""
    portaldot_chain_id: int | None = None
    portaldot_timeout_seconds: float = Field(default=10, gt=0, le=60)
    frontend_origin: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()
