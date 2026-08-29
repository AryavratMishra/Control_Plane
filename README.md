# ControlPlane.ai

> **Real-time AI Governance & Control Layer**
>
> _Detect AI risk before it becomes a business incident._

## Quick Start

```bash
# 1. Clone and setup
git clone <repo>
cd control_plane
cp .env.example .env  # Edit if you have an OpenAI API key

# 2. Start with Docker Compose (recommended)
docker compose up --build

# 3. Open the Control Room
open http://localhost:3000

# 4. Run demo scenarios from the UI — or via API:
curl -X POST http://localhost:8000/api/v1/demo/run/hallucination
curl -X POST http://localhost:8000/api/v1/demo/run/pii
curl -X POST http://localhost:8000/api/v1/demo/run/cost_anomaly
curl -X POST http://localhost:8000/api/v1/demo/run/escalation
```

## Local Development (without Docker)

### Backend

```bash
# Requires Python 3.11+ and PostgreSQL running locally
cd backend
pip install -r requirements.txt
# Start PostgreSQL and update .env DATABASE_URL if needed
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev  # Starts at http://localhost:3000
```

## Architecture

```
AI Response + Telemetry
        │
        ▼
  ControlPlane Gateway
        │
        ├── Fast Risk Screen (< 50ms)
        │        ├── PII regex
        │        ├── Safety keywords
        │        ├── Cost telemetry
        │        └── Impact classification
        │
        └── Deep Evaluation (parallel)
                 ├── Performance Engine
                 │     ├── Evidence retrieval (pgvector)
                 │     ├── Contradiction detection
                 │     └── LLM-as-Judge (optional)
                 ├── Cost Engine
                 │     └── Baseline comparison
                 └── Responsibility Engine
                       ├── PII detection
                       ├── Policy rules
                       └── Safety / bias signals
                              │
                              ▼
                       Risk Engine
                       (weighted, non-naive)
                              │
                  ┌───────────┼───────────┐
                  ▼           ▼           ▼
                ALLOW       REPAIR     ESCALATE → BLOCK
```

## Demo Scenarios

| Scenario | Description | Expected Action |
|---|---|---|
| `safe` | Normal customer support query | ALLOW |
| `hallucination` | AI claims refund processed — it's PENDING | BLOCK → REPAIR |
| `pii` | Response exposes phone, email, PAN | BLOCK |
| `cost_anomaly` | 7.1× baseline, 9 tool calls, 3 retries | REPAIR/ESCALATE |
| `escalation` | Retirement savings advice without evidence | ESCALATE |

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript + Tailwind CSS + Recharts |
| Backend | Python + FastAPI (async) |
| Database | PostgreSQL + pgvector |
| PII Detection | Regex + pattern matching |
| Real-time | WebSockets |
| LLM (optional) | OpenAI gpt-4o-mini |
| Infrastructure | Docker Compose |

## API Endpoints

```
POST /api/v1/gateway/evaluate      — Main evaluation endpoint
GET  /api/v1/dashboard/summary     — KPI aggregates
GET  /api/v1/incidents             — Incident list
GET  /api/v1/incidents/{id}        — Incident detail
POST /api/v1/incidents/{id}/review — Human review
GET  /api/v1/policies              — Policy list
POST /api/v1/demo/run/{scenario}   — Demo scenarios
WS   /ws/control-room              — Live events
```

## Configuration

Copy `.env.example` to `.env` and configure:

- `LLM_API_KEY` — OpenAI API key (optional; demo works without it)
- `ENABLE_LLM_JUDGE=true` — Enable LLM-as-Judge deep evaluation
- `DATABASE_URL` — PostgreSQL connection string

## Running Tests

```bash
cd backend
pytest tests/ -v
```
