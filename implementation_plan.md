# ControlPlane.ai — Round 2 Prototype Implementation Plan

## Overview

Build a full end-to-end working prototype of **ControlPlane.ai** — a real-time, model-agnostic AI governance middleware that intercepts AI responses and evaluates them across **Performance**, **Cost**, and **Responsibility** dimensions, then takes one of four actions: **ALLOW / REPAIR / ESCALATE / BLOCK**.

The stack: **FastAPI (Python)** backend + **React + TypeScript + Tailwind CSS** frontend + **PostgreSQL + pgvector** + **Docker Compose**.

---

## Open Questions

> [!IMPORTANT]
> **LLM API Key**: Do you have an OpenAI or Gemini API key to use for live LLM-as-Judge evaluation? The prototype will work without it (Demo Mode uses deterministic seeded scenarios), but a real key dramatically improves realism for the live demo.

> [!NOTE]
> **Currency**: The README uses INR (₹) throughout. All cost displays will use ₹. Confirmed?

> [!NOTE]
> **Deployment target**: Local Docker Compose only? Or do you also need a cloud deployment (e.g., Railway, Render, AWS)?

---

## Proposed Changes

### Monorepo Structure

```
control_plane/
├── backend/
├── frontend/
├── data/
│   ├── trusted_docs/
│   ├── demo_scenarios/
│   └── seed/
├── infra/
│   └── postgres/
├── .env.example
├── docker-compose.yml
├── Makefile
└── README.md
```

---

### Phase 1 — Project Skeleton & Infrastructure

#### [NEW] `docker-compose.yml`
Postgres + pgvector + Redis + Backend + Frontend services.

#### [NEW] `backend/requirements.txt`
fastapi, uvicorn, sqlalchemy, alembic, pydantic, presidio-analyzer, openai, httpx, asyncpg, pgvector, redis, websockets, python-dotenv, structlog, pytest.

#### [NEW] `backend/app/main.py`
FastAPI app with CORS, routers, lifespan events, WebSocket manager.

#### [NEW] `backend/app/config.py`
Pydantic Settings from .env.

#### [NEW] `backend/Dockerfile`

#### [NEW] `frontend/` (Vite + React + TypeScript + Tailwind)

---

### Phase 2 — Database Schema & ORM

#### [NEW] `backend/app/db/models.py`
SQLAlchemy models: Application, Model, Conversation, Request, Response, ExecutionEvent, RiskAssessment, Incident, HumanReview, Policy, PolicyVersion, TrustedDocument, RetrievalChunk.

#### [NEW] `backend/app/db/session.py`
Async SQLAlchemy engine + session factory.

#### [NEW] `backend/alembic/` migrations

#### [NEW] `backend/app/schemas/`
Pydantic schemas: gateway.py, assessment.py, incident.py, policy.py.

---

### Phase 3 — Gateway API

#### [NEW] `backend/app/api/routes_gateway.py`
`POST /api/v1/gateway/evaluate` — main evaluation endpoint.

#### [NEW] `backend/app/controlplane/orchestrator.py`
Coordinates fast screen → parallel deep checks → risk engine → action engine → persist → WebSocket broadcast.

---

### Phase 4 — Fast Risk Screen

#### [NEW] `backend/app/controlplane/fast_screen.py`
- PII regex patterns
- Basic safety keyword check
- High-impact use-case classification
- Cost/token anomaly signals
- Evidence presence check
- Output: `FastScreenResult`

---

### Phase 5 — Responsibility Engine

#### [NEW] `backend/app/privacy/pii_detector.py`
Microsoft Presidio + regex patterns for email, phone, account numbers, credit cards, government IDs.

#### [NEW] `backend/app/privacy/redactor.py`
Span-based redaction with `[REDACTED:TYPE]` placeholders.

#### [NEW] `backend/app/controlplane/responsibility_engine.py`
PII detection → policy check → safety check → bias signal → `ResponsibilityResult`.

---

### Phase 6 — Cost Engine

#### [NEW] `backend/app/telemetry/cost_calculator.py`
Token pricing, cost multiplier, anomaly thresholds.

#### [NEW] `backend/app/controlplane/cost_engine.py`
Telemetry comparison vs baseline → `CostResult`.

---

### Phase 7 — Performance Engine (RAG + LLM-as-Judge)

#### [NEW] `backend/app/ai/embeddings.py`
OpenAI embeddings (with mock fallback).

#### [NEW] `backend/app/retrieval/retriever.py`
pgvector cosine similarity search for trusted evidence.

#### [NEW] `backend/app/ai/judge.py`
LLM-as-Judge prompt with structured JSON output.

#### [NEW] `backend/app/controlplane/performance_engine.py`
Claim extraction → evidence retrieval → deterministic contradiction check → LLM judge → `PerformanceResult`.

---

### Phase 8 — Risk Engine + Action Engine

#### [NEW] `backend/app/controlplane/risk_engine.py`
Non-naive weighted risk combination with hard-rule overrides → `RiskDecision`.

#### [NEW] `backend/app/controlplane/action_engine.py`
Decision matrix: ALLOW / REPAIR / ESCALATE / BLOCK.

#### [NEW] `backend/app/controlplane/repair_service.py`
PII redaction repair + constrained LLM regeneration.

#### [NEW] `backend/app/controlplane/policy_engine.py`
Load policy by use-case/geography from DB config.

---

### Phase 9 — Incident + Audit + Human Review

#### [NEW] `backend/app/api/routes_incidents.py`
`GET /api/v1/incidents`, `GET /api/v1/incidents/{id}`, `POST /api/v1/incidents/{id}/review`.

#### [NEW] `backend/app/api/routes_dashboard.py`
`GET /api/v1/dashboard/summary` — aggregated KPIs.

#### [NEW] `backend/app/api/routes_policies.py`
CRUD for policies.

---

### Phase 10 — WebSocket Real-Time Events

#### [NEW] `backend/app/api/routes_ws.py`
`WS /ws/control-room` — push `risk_event` on every evaluation.

---

### Phase 11 — Seed Data + Demo Mode

#### [NEW] `data/seed/orders.csv`
10 synthetic customer orders including ORD1001 (refund=PENDING) and ORD1002.

#### [NEW] `data/trusted_docs/`
Refund policy, privacy policy, financial decision policy documents.

#### [NEW] `backend/app/seed/seed_demo_data.py`
Seed applications, policies, trusted documents + embeddings into pgvector.

#### [NEW] `backend/app/api/routes_demo.py`
`POST /api/v1/demo/run/{scenario}` — 4 deterministic scenarios triggering the real pipeline.

---

### Phase 12 — Frontend Control Room

#### [NEW] `frontend/src/pages/Dashboard.tsx`
KPI cards (Total, Allowed, Repaired, Escalated, Blocked, Cost Saved) + Risk trend charts (Recharts) + Live event stream.

#### [NEW] `frontend/src/pages/Incidents.tsx`
Filterable incident table with severity badges.

#### [NEW] `frontend/src/pages/IncidentDetail.tsx`
4-column forensic view: Request | AI Response | Evidence | Decision.

#### [NEW] `frontend/src/pages/ReviewQueue.tsx`
Human review queue with Approve/Reject/Override buttons.

#### [NEW] `frontend/src/pages/Policies.tsx`
Policy list + version display.

#### [NEW] `frontend/src/components/`
RiskScoreCard, LiveEventStream, IncidentTable, DecisionBadge, ResponseInspector, CostPanel, EvidencePanel, HumanReviewPanel, PolicyBadge.

#### [NEW] `frontend/src/hooks/useWebSocket.ts`
WebSocket hook for live control-room events.

#### [NEW] `frontend/src/components/DemoPanel.tsx`
One-click demo scenario buttons: Safe / Hallucination / PII / Cost Anomaly / Human Escalation.

---

## Verification Plan

### Automated Tests
```bash
cd backend && pytest tests/ -v
```

### Manual Verification
1. `docker compose up --build` — all services start.
2. Frontend loads at `http://localhost:3000`.
3. Backend health at `http://localhost:8000/health`.
4. Run each of 4 demo scenarios from DemoPanel.
5. Each creates an incident visible in the dashboard.
6. WebSocket stream updates in real time.
7. Human review queue approves/rejects an escalated incident.
8. Audit trail persists correctly.

---

## Implementation Sequence

1. **Infra** — docker-compose, Dockerfile, .env.example
2. **Backend skeleton** — FastAPI + DB models + migrations + seed
3. **Engines** — fast_screen → responsibility → cost → performance → risk → action
4. **API routes** — gateway, incidents, dashboard, policies, demo, websocket
5. **Frontend** — Vite scaffold → design system → Dashboard → Incidents → ReviewQueue → DemoPanel
6. **End-to-end wiring** — demo mode runs all 4 scenarios deterministically
7. **Polish** — charts, live stream, animations, responsive layout
