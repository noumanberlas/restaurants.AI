# Restaurant Management AI

A Python multi-agent restaurant management API powered by Microsoft Agent Framework. It routes menu, order, reservation, and inventory requests to specialist agents. Run it locally with Ollama or configure Microsoft Foundry.

## Agents

| Agent | Responsibilities |
| --- | --- |
| `menu_agent` | Menu items, prices, and availability |
| `order_agent` | Create, update, cancel, and track orders |
| `reservation_agent` | Create, update, and cancel reservations |
| `inventory_agent` | Stock levels and low-stock alerts |

## Requirements

- Python 3.11+
- Ollama for local inference
- A pulled local Ollama model, such as `qwen3-coder:latest`

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

Set `MODEL_PROVIDER=foundry`, then configure `FOUNDRY_PROJECT_ENDPOINT` and `FOUNDRY_MODEL` in `.env`. Authentication uses `DefaultAzureCredential`.

## Tests

```powershell
.venv\Scripts\python.exe -m pytest tests
```

## Notes

- Runtime SQLite data is stored in `restaurant.db`, which is excluded from Git.
- The local Ollama client uses Ollama's OpenAI-compatible `/v1` API.