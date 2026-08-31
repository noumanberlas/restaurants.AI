from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

from agent_framework import Agent, AgentSession
from agent_framework.foundry import FoundryChatClient
from agent_framework.openai import OpenAIChatClient
from azure.identity import DefaultAzureCredential

from src.config import Settings, get_settings

logger = logging.getLogger(__name__)


def _resource_endpoint(project_endpoint: str) -> str:
    """Derive the base Cognitive Services endpoint from a Foundry project endpoint."""
    parsed = urlparse(project_endpoint)
    return f"{parsed.scheme}://{parsed.netloc}/"


# ── Module-level factory function (equivalent to a static helper method in C#) ─
def build_client(
    settings: Settings, model: str
) -> FoundryChatClient | OpenAIChatClient:   # union return type: like T1 | T2 in C# with 'or'
    """Return the correct AF chat client for the active provider."""
    if settings.is_ollama():
        endpoint = settings.ollama_endpoint.rstrip("/")
        if not endpoint.endswith("/v1"):
            endpoint = f"{endpoint}/v1"
        return OpenAIChatClient(
            model=model,
            base_url=endpoint,
            api_key="ollama",
        )
    if settings.foundry_api_key:
        # Key-based auth: hits the same resource's Azure OpenAI surface (FoundryChatClient
        # only supports Entra ID tokens, not API keys).
        return OpenAIChatClient(
            model=model,
            azure_endpoint=_resource_endpoint(settings.foundry_project_endpoint),
            api_key=settings.foundry_api_key,
        )
    # Foundry: DefaultAzureCredential covers CLI, managed identity, env vars
    return FoundryChatClient(
        project_endpoint=settings.foundry_project_endpoint,
        model=model,
        credential=DefaultAzureCredential(),
    )


# ── Base class — Python has no 'abstract' keyword; convention is raise NotImplementedError
# ── C# equivalent:  public abstract class BaseRestaurantAgent { ... }
class BaseRestaurantAgent:
    """Thin wrapper that composes an agent_framework.Agent.

    Subclasses declare *agent_name* and override *_system_prompt*, *_tools*,
    and optionally *_context_providers*. The framework handles schema generation and
    tool dispatch automatically from plain Python functions.
    """

    # Class-level attribute (like a field declaration in C#, but without a value here)
    # Each subclass sets this to a string, e.g.  agent_name = "menu_agent"
    agent_name: str

    def __init__(self) -> None:            # constructor — 'self' is 'this' in C#, always the first param
        settings = get_settings()          # no 'var' keyword; Python infers the type
        model = settings.get_model_for_agent(self.agent_name)
        client = build_client(settings, model)

        # self._agent — the leading underscore is the Python convention for 'private'
        # There is no true private/protected; _ = "don't use outside the class"
        self._agent = Agent(
            client=client,
            name=self.agent_name,
            instructions=self._system_prompt(),   # calling overridden method in ctor
            tools=self._tools(),
            context_providers=self._context_providers(),
            # Required by HandoffBuilder — prevents history mismatch on handoff tool calls
            require_per_service_call_history_persistence=True,
        )
        logger.info(
            "Agent '%s' ready | provider=%s | model=%s",
            self.agent_name,
            settings.model_provider.value,
            model,
        )

    # ── Template-method pattern: raise NotImplementedError = abstract in C# ───────
    # Subclasses MUST override this, otherwise calling it raises at runtime
    def _system_prompt(self) -> str:
        raise NotImplementedError

    # ── Virtual methods with default implementations (like 'virtual' in C#) ───────
    # Subclasses can override these; if not, the base default (empty list) is used
    def _tools(self) -> list[Any]:
        return []   # default: no tools; subclasses append their callables here

    def _context_providers(self) -> list[Any]:
        return []   # default: none; subclasses add SkillsProvider etc.

    # ── 'async' methods — like Task<string> in C# / async Task<string> ──────────
    # 'await' inside an async method suspends without blocking a thread
    async def run(self, message: str, session: AgentSession | None = None) -> str:
        result = await self._agent.run(message, session=session)
        return str(result)     # str() = ToString() in C#

    async def create_session(self) -> AgentSession:
        return await self._agent.create_conversation()
