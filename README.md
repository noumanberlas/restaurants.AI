# Restaurant Management AI

A Python multi-agent restaurant management API powered by Microsoft Agent Framework. It routes menu, order, reservation, and inventory requests to specialist agents via a handoff workflow. Run it locally with Ollama, or configure Microsoft Foundry — either as a local dev API or as a hosted Foundry agent deployed with `azd`.

## Agents

| Agent | Responsibilities |
| --- | --- |
| `host_agent` | Coordinator — routes each request to the correct specialist |
| `menu_agent` | Menu items, prices, and availability |
| `order_agent` | Create, update, cancel, and track orders |
| `reservation_agent` | Create, update, and cancel reservations |
| `inventory_agent` | Stock levels and low-stock alerts |

## Requirements

- Python 3.11+
- Ollama for local inference, **or** a Microsoft Foundry project
- A pulled local Ollama model, such as `qwen3-coder:latest` (Ollama path only)

## Entry Points

| File | Purpose |
| --- | --- |
| `src/main.py` | FastAPI dev host — `/health`, `/chat`, `/chat/stream` (port 8088) |
| `agent_main.py` | Foundry hosted-agent entry point — serves the handoff workflow over the Responses protocol via `azd ai agent run` / `azd deploy` |

## Quick Start With Ollama

```powershell
git clone https://github.com/noumanberlas/restaurants.AI.git
cd restaurants.AI
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
ollama pull qwen3-coder:latest
```

Set these values in `.env`:

```dotenv
MODEL_PROVIDER=ollama
OLLAMA_ENDPOINT=http://localhost:11434
OLLAMA_MODEL=qwen3-coder:latest
```

Start the API:

```powershell
.venv\Scripts\python.exe -m src.main
```

The service listens on `http://localhost:8088`.

## API

### Health Check

```powershell
Invoke-RestMethod http://localhost:8088/health
```

Example response:

```json
{"status":"ok","provider":"ollama"}
```

### Chat

```powershell
Invoke-RestMethod http://localhost:8088/chat -Method Post -ContentType application/json -Body '{"message":"List the menu."}'
```

### Stream Chat Events

`POST /chat/stream` returns newline-delimited JSON events for agent output and handoffs.

## Microsoft Foundry

Set `MODEL_PROVIDER=foundry` in `.env`, then configure:

```dotenv
FOUNDRY_PROJECT_ENDPOINT=https://<your-project>.services.ai.azure.com/api/projects/<project-name>
FOUNDRY_MODEL=gpt-4o
```

Two authentication modes are supported:

- **Entra ID (default)** — leave `FOUNDRY_API_KEY` blank. Uses `DefaultAzureCredential` (Azure CLI login, managed identity, etc.) against `FoundryChatClient`.
- **API key** — set `FOUNDRY_API_KEY` to a Cognitive Services key for the Foundry resource. This routes inference through `OpenAIChatClient` against the resource's Azure OpenAI surface instead (`FoundryChatClient`/`AIProjectClient` only support Entra ID tokens, not API keys).

Per-agent model overrides (`FOUNDRY_MODEL_MENU_AGENT`, etc.) let each specialist use a different deployment; unset ones fall back to `FOUNDRY_MODEL`.

### Data Layer: Azure Table Storage

By default the app persists to a local SQLite file (`restaurant.db`). When `MODEL_PROVIDER=foundry` **and** `TABLE_STORAGE_CONNECTION_STRING` is set in `.env`, Azure Table Storage is used instead — each domain (menu, orders, reservations, inventory) gets its own table, auto-created on startup. Both entry points (`src/main.py` and `agent_main.py`) apply this check identically.

```dotenv
TABLE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net
```

### Hosted Agent (azd)

The coordinator's handoff workflow can be scaffolded and deployed as a Foundry hosted agent, defined in [azure.yaml](azure.yaml):

```powershell
azd auth login
azd up          # provision infra, then deploy
```

Local interactive testing without a full deploy:

```powershell
azd ai agent run              # starts agent_main.py + opens Agent Inspector chat UI
azd ai agent invoke "<msg>"   # one-shot invocation against the deployed/local agent
```

`azure.yaml` sets `startupCommand` to the Windows venv Python (`.venv/Scripts/python.exe agent_main.py`) for local `azd ai agent run`; remote deploys use `codeConfiguration.entryPoint: agent_main.py` instead, so this stays Windows-specific without affecting the deployed container.

Deploying requires the `Cognitive Services User` role (or equivalent) on the underlying `Microsoft.CognitiveServices/accounts` resource for the identity running `azd deploy`.

## Tests

```powershell
.venv\Scripts\python.exe -m pytest tests
```

Tests always run against SQLite (see `tests/conftest.py`, which clears `TABLE_STORAGE_CONNECTION_STRING`), never against live Azure Table Storage.

## Notes

- Runtime SQLite data is stored in `restaurant.db`, which is excluded from Git.
- The local Ollama client uses Ollama's OpenAI-compatible `/v1` API.
- Specialist agents use `SkillsProvider` (via `context_providers=`, not `middleware=`) to load business-rule skills (`src/skills/`) on demand.
- The menu specialist is instructed to act on add/update requests immediately when the required fields are present, rather than pausing to ask for confirmation — the confirm-then-resume round trip has rough edges in the current `agent-framework-foundry-hosting` beta and can misroute or fail on the follow-up turn.
