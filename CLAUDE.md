# Restaurant Management System — CLAUDE.md

## Project

Multi-agent restaurant management system built with the **Microsoft Agent Framework**
(`agent-framework` on PyPI), hosted on Microsoft Foundry. Supports switching between
Foundry models and local Ollama models via `.env`.

**Language:** Python 3.11+  
**Virtual env:** `.venv/` at project root  
**Entry point:** `src/main.py` (FastAPI, port 8088)

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # then fill in credentials
```

## Run

```powershell
.venv\Scripts\python.exe -m src.main
```

## Test

```powershell
pytest tests/
```

## Key packages

| Package | Purpose |
|---|---|
| `agent-framework-foundry` | `FoundryChatClient`, `FoundryAgent`, `AgentSession` |
| `agent-framework-openai` | `OpenAIChatClient` for Ollama's OpenAI-compatible API |
| `agent-framework-core` | `Agent`, `AgentSession`, `HandoffOrchestration` |

## Key conventions

- `MODEL_PROVIDER=foundry` → `FoundryChatClient` (DefaultAzureCredential, env: `FOUNDRY_PROJECT_ENDPOINT` + `FOUNDRY_MODEL`)
- `MODEL_PROVIDER=ollama`  → `OpenAIChatClient` using `OLLAMA_ENDPOINT/v1` (env: `OLLAMA_ENDPOINT` + `OLLAMA_MODEL`)
- Tools are **plain Python functions** with `Annotated` type hints — AF generates the tool schema automatically
- Each agent extends `BaseRestaurantAgent` and lives in `src/agents/<domain>_agent.py`
- `HostAgent` uses AF `HandoffOrchestration` to route to specialist agents
- Never commit `.env`; commit only `.env.example`

## Agents

| Agent | Domain | File |
|---|---|---|
| HostAgent | Orchestrator / handoff router | `src/agents/host_agent.py` |
| MenuAgent | Menu items & availability | `src/agents/menu_agent.py` |
| OrderAgent | Order lifecycle | `src/agents/order_agent.py` |
| ReservationAgent | Table bookings | `src/agents/reservation_agent.py` |
| InventoryAgent | Stock & alerts | `src/agents/inventory_agent.py` |

## Adding a new agent

1. Create `src/agents/<name>_agent.py` extending `BaseRestaurantAgent`; set `agent_name = "<name>_agent"`
2. Implement `_system_prompt()` and `_tools()` (return plain callables with Annotated params)
3. Add tool functions in `src/tools/<name>_tools.py` with docstrings (used as tool descriptions)
4. Add model env vars to `.env.example` (`FOUNDRY_MODEL_<NAME>_AGENT`, `OLLAMA_MODEL_<NAME>_AGENT`)
5. Add model fields to `src/config/settings.py`
6. Register the agent as a `handoffs` target in `HostAgent.__init__`

## Jira
- Base REST URL: https://jira.culturatech.com/rest/api/2/
- Auth: Bearer token from `JIRA_PERSONAL_TOKEN` env var

## Confluence
- Base REST URL: https://culturatech.atlassian.net/wiki/rest/api/
- Auth: Basic — email nouman.berlas@culturatech.com + `CONFLUENCE_API_TOKEN` env var
