from __future__ import annotations

from enum import Enum          # Enum base — like 'enum' keyword in C#
from functools import lru_cache  # lru_cache = memoize / lazy singleton pattern

from pydantic_settings import BaseSettings, SettingsConfigDict


# ── Enum — C# equivalent: public enum ModelProvider { Foundry, Ollama }
# str is mixed in so the value IS the string ("foundry"), not just an int
class ModelProvider(str, Enum):
    FOUNDRY = "foundry"
    OLLAMA = "ollama"


# ── Settings class — auto-reads from .env file and environment variables
# C# equivalent: IOptions<Settings> populated by IConfiguration
# Each field below maps 1-to-1 to an env var (case-insensitive, _ separator)
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── Provider selection ──────────────────────────────────────────────────
    model_provider: ModelProvider = ModelProvider.FOUNDRY   # type annotation + default value

    # ── Microsoft Foundry — read by FoundryChatClient automatically ─────────
    foundry_project_endpoint: str = ""
    foundry_model: str = "gpt-4o"  # default; per-agent fields below override
    # When set, use key-based Azure OpenAI auth instead of DefaultAzureCredential
    foundry_api_key: str = ""

    foundry_model_menu_agent: str = ""
    foundry_model_order_agent: str = ""
    foundry_model_reservation_agent: str = ""
    foundry_model_inventory_agent: str = ""
    foundry_model_host_agent: str = ""

    # ── Ollama — read by OllamaChatClient automatically ─────────────────────
    ollama_endpoint: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"  # default; per-agent fields below override

    ollama_model_menu_agent: str = ""
    ollama_model_order_agent: str = ""
    ollama_model_reservation_agent: str = ""
    ollama_model_inventory_agent: str = ""
    ollama_model_host_agent: str = ""

    # ── Persistence ─────────────────────────────────────────────────────────
    # When set (and MODEL_PROVIDER=foundry), Azure Table Storage replaces SQLite
    table_storage_connection_string: str = ""

    # ── Observability ───────────────────────────────────────────────────────
    azure_monitor_connection_string: str = ""

    # ── App ─────────────────────────────────────────────────────────────────
    log_level: str = "INFO"
    app_host: str = "0.0.0.0"
    app_port: int = 8088

    # ── Derived helpers ─────────────────────────────────────────────────────
    def is_foundry(self) -> bool:
        return self.model_provider == ModelProvider.FOUNDRY

    def is_ollama(self) -> bool:
        return self.model_provider == ModelProvider.OLLAMA

    def use_table_storage(self) -> bool:
        return self.is_foundry() and bool(self.table_storage_connection_string)

    def get_model_for_agent(self, agent_name: str) -> str:
        """Return the per-agent model, falling back to the provider default."""
        # f-string: f"...{variable}..." — like $"...{variable}..." in C# interpolation
        per_agent_field = f"{self.model_provider.value}_model_{agent_name}"
        # getattr(obj, 'field_name', default) — like reflection: obj.GetType().GetProperty(...)
        per_agent = getattr(self, per_agent_field, "")
        if per_agent:
            return per_agent
        default_field = f"{self.model_provider.value}_model"
        return getattr(self, default_field, "gpt-4o")


# ── Singleton via lru_cache — C# equivalent: registered as Singleton in DI container
# maxsize=1 means only one Settings instance is ever created and reused
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
