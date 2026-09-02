<div align="center">

# ControlPlane.ai

### Real-Time AI Governance & Control Layer

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

**Stop bad AI responses before they reach your users.**

ControlPlane is an inline API proxy that intercepts every AI response in real time — detecting hallucinations, PII leakage, runaway costs, and policy violations — before they become incidents. It either repairs the response automatically or blocks it and escalates to a human reviewer.

</div>

---

## 📋 Table of Contents

1. [Why ControlPlane?](#-why-controlplane)
2. [Architecture Overview](#-architecture-overview)
3. [The 6-Phase Evaluation Pipeline](#-the-6-phase-evaluation-pipeline)
   - [Phase 1: Fast Screen](#phase-1-fast-screen--50ms)
   - [Phase 2: Deep Evaluation (Parallel)](#phase-2-deep-evaluation-parallel)
   - [Phase 3: Risk Engine](#phase-3-risk-engine)
   - [Phase 4: Action Engine](#phase-4-action-engine--repair-service)
   - [Phase 5: Persist & Audit Trail](#phase-5-persist--audit-trail)
   - [Phase 6: Real-Time Broadcast](#phase-6-real-time-broadcast)
4. [Risk Dimensions Explained](#-risk-dimensions-explained)
5. [Decision Actions](#-decision-actions)
6. [API Reference](#-api-reference)
7. [Data Models](#-data-models)
8. [Tech Stack](#-tech-stack)
9. [Project Structure](#-project-structure)
10. [Quick Start (Docker)](#-quick-start-docker)
11. [Configuration Reference](#-configuration-reference)
12. [Demo Scenarios](#-demo-scenarios)
13. [Custom Evaluation Guide](#-custom-evaluation-guide)
14. [Frontend UI Guide](#-frontend-ui-guide)
15. [Supported LLM Providers](#-supported-llm-providers)
16. [Contributing](#-contributing)

---

## 🚨 Why ControlPlane?

AI agents are being deployed to handle customer support, financial advice, medical queries, and more. But LLMs hallucinate. They leak PII. They run expensive agent loops and give confidently-wrong answers.

Traditional monitoring catches these issues **after the fact** — after the user has already seen the bad response, after the GDPR fine has been issued, after the customer has acted on wrong financial advice.

**ControlPlane sits in the critical path** — between your AI system and your users — and evaluates every response before it is shown. Think of it as a real-time firewall for AI outputs.

| Problem | Without ControlPlane | With ControlPlane |
|---|---|---|
| AI claims a refund was processed when it was PENDING | User believes it, contacts support angrily | Response is intercepted, repaired, and corrected before display |
| AI includes user's phone number and PAN in a response | GDPR/DPDP violation, potential fine | PII is automatically redacted in < 50ms |
| AI agent enters a retry loop and costs 7x the baseline | Silent cost overrun, no alert | Cost anomaly flagged, agent loop detected, incident created |
| AI gives unqualified investment advice | Legal/compliance liability | Escalated to human reviewer, never shown to user |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          YOUR AI APPLICATION                            │
│                                                                         │
│   User Request ──► AI Agent / LLM ──► AI Response                      │
│                                             │                           │
│                                             ▼                           │
│              ┌──────────────────────────────────────────┐               │
│              │        POST /api/v1/gateway/evaluate      │               │
│              │   { request, response, context, telemetry }│              │
│              └──────────────────┬───────────────────────┘               │
│                                 │                                       │
└─────────────────────────────────┼───────────────────────────────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │                            │
                    │    CONTROLPLANE ENGINE     │
                    │                            │
                    │  ┌────────────────────┐    │
                    │  │  1. Fast Screen    │    │
                    │  │   (< 50ms)         │    │
                    │  └────────┬───────────┘    │
                    │           │                │
                    │    SAFE?  │  RISKY?        │
                    │    ┌──────┴──────┐         │
                    │    │            │          │
                    │  ALLOW       Deep Eval     │
                    │    │        (Parallel)     │
                    │    │     ┌────┬────┬────┐  │
                    │    │     │Perf│Cost│Resp│  │
                    │    │     └────┴────┴────┘  │
                    │    │            │          │
                    │    │      Risk Engine      │
                    │    │            │          │
                    │    │      ┌─────▼──────┐   │
                    │    │      │  Action    │   │
                    │    │      │  Decision  │   │
                    │    │      └─────┬──────┘   │
                    │    │           │           │
                    │  ALLOW   REPAIR│BLOCK│ESCALATE
                    │    │           │           │
                    └────┼───────────┼───────────┘
                         │           │
                         ▼           ▼
                  Final Response  Dashboard / Incident
                   to User         WebSocket Broadcast
```

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React + Vite)                 │
│  Dashboard │ Incidents │ Policies │ Review Queue │ Custom Eval  │
│                     WebSocket Live Stream                       │
└─────────────────────────────┬───────────────────────────────────┘
                              │ HTTP + WebSocket
┌─────────────────────────────▼───────────────────────────────────┐
│                        BACKEND (FastAPI)                        │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ /gateway │  │/dashboard│  │/incidents│  │ /policies    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────────┐  │
│  │  /demo   │  │   /ws    │  │      ControlPlane Engine      │  │
│  └──────────┘  └──────────┘  └──────────────────────────────┘  │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  AI Module  │  │Privacy/PII  │  │    Retrieval (pgvector)  │ │
│  │(Gemini/GPT) │  │   Redactor  │  │     Evidence Store       │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└───────────────┬─────────────────────────────────────────────────┘
                │
    ┌───────────┴───────────┐
    │                       │
┌───▼──────┐         ┌──────▼──────┐
│PostgreSQL│         │    Redis     │
│+pgvector │         │(cache/pubsub)│
└──────────┘         └─────────────┘
```

---

## ⚙️ The 6-Phase Evaluation Pipeline

Every call to `POST /api/v1/gateway/evaluate` runs through these 6 phases. The entire pipeline completes in **50ms – 5s** depending on whether the fast-path short-circuits.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      REQUEST RECEIVED                                       │
│    { application_id, request, response, context, telemetry }                │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                           ┌─────────▼──────────┐
                           │  PHASE 1: FAST      │
                           │  SCREEN             │
                           │  (< 50ms always)    │
                           │                     │
                           │  • PII regex scan   │
                           │  • Safety keywords  │
                           │  • High-impact kw   │
                           │  • Claim indicators │
                           │  • Cost telemetry   │
                           │  • Policy hard rules│
                           └─────────┬───────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │ LOW RISK?                        │ HIGH RISK?
                    │ (no triggers)                    │ (triggers detected)
                    ▼                                  ▼
              ┌────────┐                ┌─────────────────────────────────┐
              │ ALLOW  │                │  PHASE 2: DEEP EVALUATION       │
              │(fast   │                │  (Run in PARALLEL)              │
              │ path)  │                │                                 │
              └────────┘           ┌───┴───────────────────────────┐     │
                                   │  Performance Engine            │     │
                                   │  • Trusted data contradiction  │     │
                                   │  • pgvector evidence retrieval │     │
                                   │  • LLM-as-Judge (optional)     │     │
                                   └───────────────────────────────┘     │
                                   ┌───────────────────────────────┐     │
                                   │  Cost Engine                  │     │
                                   │  • Token usage analysis       │     │
                                   │  • Agent loop detection       │     │
                                   │  • Cost multiplier vs. policy │     │
                                   └───────────────────────────────┘     │
                                   ┌───────────────────────────────┐     │
                                   │  Responsibility Engine         │     │
                                   │  • PII deep detection         │     │
                                   │  • Safety keyword checks      │     │
                                   │  • Enterprise policy rules    │     │
                                   │  • Bias signal detection      │     │
                                   └──────────────┬────────────────┘     │
                                                  │                      │
                                        ┌─────────▼──────────┐          │
                                        │  PHASE 3: RISK      │          │
                                        │  ENGINE             │          │
                                        │                     │          │
                                        │  Combines all 3     │          │
                                        │  dimension scores   │          │
                                        │  with context       │          │
                                        │  weights & impact   │          │
                                        │  multipliers        │          │
                                        └─────────┬───────────┘          │
                                                  │                      │
                                        ┌─────────▼──────────┐          │
                                        │  PHASE 4: ACTION    │          │
                                        │  ENGINE             │          │
                                        │                     │          │
                                        │  ALLOW / REPAIR /   │          │
                                        │  ESCALATE / BLOCK   │          │
                                        └─────────┬───────────┘          │
                                                  │                      │
                                  ┌───────────────┴──────────────────┐   │
                                  │  PHASE 5: PERSIST                │   │
                                  │  • Application record            │   │
                                  │  • Conversation & Request        │   │
                                  │  • Response & RiskAssessment     │   │
                                  │  • Incident (if non-ALLOW)       │   │
                                  └───────────────┬──────────────────┘   │
                                                  │                      │
                                  ┌───────────────▼──────────────────┐   │
                                  │  PHASE 6: BROADCAST              │   │
                                  │  • WebSocket → all clients       │   │
                                  │  • Live event stream update      │   │
                                  │  • Dashboard refresh trigger     │   │
                                  └──────────────────────────────────┘   │
                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Fast Screen (< 50ms)

The Fast Screen is a **deterministic, zero-latency** engine that runs on 100% of traffic. It uses regex and keyword matching — no LLM calls. Its job is to route clearly-safe traffic to an immediate `ALLOW`, and flag potentially-risky traffic for deep evaluation.

| Check | What it detects | Trigger |
|---|---|---|
| **PII Regex** | EMAIL, PHONE_IN, CREDIT_CARD, PAN, AADHAAR, ACCOUNT_NUMBER | `needs_deep_check = True`; CREDIT_CARD/PAN/AADHAAR → `hard_block = True` |
| **Safety Keywords** | Violence, self-harm, hate speech, weapons | `hard_block = True` |
| **High-Impact Keywords** | refund, balance, investment, medical, legal, withdraw | `needs_deep_check = True` |
| **Claim Indicators** | "was processed", "has shipped", "your balance is" | `needs_deep_check = True` |
| **Cost Telemetry** | `estimated_cost / expected_cost > multiplier threshold` | Cost signal flagged |
| **Tool/Retry Limits** | tool_calls > max, retries > max, llm_calls > 5 | `needs_deep_check = True` |
| **Policy Hard Rules** | Critical PII in policy + block rule active | `hard_block = True` |

### Phase 2: Deep Evaluation (Parallel)

When the Fast Screen flags a response for deep evaluation, three engines run **concurrently** using `asyncio.gather()`:

#### Performance Engine
Checks whether the AI's response is factually grounded.

1. **Deterministic Contradiction Check** — Compares response claims against `context.trusted_data` (e.g., if the AI says "refund processed" but `trusted_data.refund_status = "PENDING"`, it's a contradiction).
2. **pgvector Evidence Retrieval** — Searches the vector store for relevant documents/knowledge chunks to ground claims.
3. **LLM-as-Judge** — (Optional, requires `ENABLE_LLM_JUDGE=true`) Uses a second LLM call to evaluate claim-by-claim grounding against retrieved evidence.

#### Cost Engine
Detects runaway agent behavior and cost anomalies:

- Calculates actual cost in INR from token counts using model-specific pricing
- Compares against the policy's `expected_cost_inr` baseline
- Flags if cost multiplier exceeds `COST_MULTIPLIER_HIGH` (default: 4x) or `COST_MULTIPLIER_MEDIUM` (default: 2x)
- Detects agent loops via excessive `llm_calls`, `tool_calls`, `retries`, and `latency_ms`

#### Responsibility Engine
Checks privacy, safety, and policy compliance:

1. **Deep PII Detection** — Runs the full PII detector with pattern matching for 10+ entity types
2. **Safety Signals** — Checks for violence, self-harm, hate speech, confidential data exposure
3. **Enterprise Policy Rules** — Evaluates custom rules (e.g., "investment_recommendation → escalate", "confidential_data_exposure → block")
4. **Bias Signal Detection** — Flags responses in high-stakes use cases (HR, finance) that reference protected-attribute decision contexts

### Phase 3: Risk Engine

The Risk Engine combines the three dimension scores into a single contextual risk score using **weighted max scoring** (not naive averaging):

```
base_risk = max(performance_score, responsibility_score, cost_score × 0.7)

context_score = base_risk × impact_multiplier × use_case_multiplier

impact_multiplier:
  low → 0.80 | medium → 1.00 | high → 1.25 | critical → 1.50

use_case_multiplier:
  low → 0.85 | medium → 1.00 | high → 1.20

Uncertainty amplification:
  UNVERIFIED performance + high/critical impact → floor score at 0.65

Confidence dampening:
  avg_confidence < 0.4 → context_score × 0.85

Final:  overall_score = min(1.0, context_score)
```

Risk Level mapping:

| Score Range | Risk Level |
|---|---|
| ≥ 0.75 | CRITICAL |
| ≥ 0.50 | HIGH |
| ≥ 0.25 | MEDIUM |
| < 0.25 | LOW |

### Phase 4: Action Engine & Repair Service

```
Hard Rule Triggered?  ──Yes──► BLOCK
        │ No
        ▼
Requires Human Review? ──Yes──► ESCALATE
        │ No
        ▼
Overall = CRITICAL?  ──Yes──► BLOCK
        │ No
        ▼
Can Repair OR Med/High? ──Yes──► REPAIR ──► Repair Service
        │ No                                      │
        ▼                                         ▼
      ALLOW                        1. PII Redaction (always)
                                   2. LLM Constrained Regen
                                   3. Safe Fallback (if no evidence)
```

**Repair Strategies (in order):**

1. **PII Redaction** — Deterministic, always applied when PII is detected. Replaces sensitive entities with masked versions.
2. **LLM Constrained Regeneration** — Uses the LLM to rewrite the response, constrained to only the verified trusted data/evidence. Temperature is set to 0.2 for determinism.
3. **Safe Fallback** — If regeneration returns an identical response or fails, a use-case-specific safe fallback message is returned.

### Phase 5: Persist & Audit Trail

Every evaluation is persisted to PostgreSQL with a complete audit trail:

```
Application (id, name, use_case)
    └── Conversation (id, application_id)
            └── Request (id, conversation_id, request_text, risk_context)
                    └── Response (id, request_id, response_text, repaired_response_text, final_status)
                            └── RiskAssessment (scores, levels, reasoning, evidence_count)
                                    └── Incident (if non-ALLOW: type, severity, status, evidence)
```

### Phase 6: Real-Time Broadcast

After every evaluation, a WebSocket event is broadcast to all connected dashboard clients:

```json
{
  "type": "risk_event",
  "incident_id": "uuid",
  "application": "customer-support",
  "action": "REPAIR",
  "severity": "HIGH",
  "reasons": ["Contradiction detected", "Refund status contradicted"],
  "performance_score": 0.62,
  "cost_score": 0.15,
  "responsibility_score": 0.37,
  "overall_score": 0.62,
  "timestamp": "2026-08-30T12:00:00Z"
}
```

---

## 📊 Risk Dimensions Explained

ControlPlane evaluates AI responses across **three orthogonal risk dimensions**:

```
┌───────────────────────────────────────────────────────────┐
│                                                           │
│  PERFORMANCE          COST              RESPONSIBILITY    │
│  "Is it true?"        "Is it          "Is it safe and    │
│                        efficient?"      compliant?"       │
│                                                           │
│  • Factual accuracy   • Token usage    • PII leakage      │
│  • Hallucination      • Agent loops    • Safety signals   │
│  • Contradiction      • Cost baseline  • Policy rules     │
│  • Evidence support   • Tool call      • Bias signals     │
│                         anomalies      • Data compliance  │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

| Dimension | Engine | Key Signals | Max Weight |
|---|---|---|---|
| **Performance** | `performance_engine.py` | Contradictions, grounding score, LLM judge verdict | 1.0 |
| **Cost** | `cost_engine.py` | Cost multiplier, agent loops, retry count | 0.7 |
| **Responsibility** | `responsibility_engine.py` | PII entities, safety signals, policy violations | 1.0 |

---

## 🎯 Decision Actions

| Action | When | User Sees | Incident Created |
|---|---|---|---|
| `ALLOW` | Low risk, no violations | Original AI response | No |
| `REPAIR` | PII detected, contradiction found, medium/high risk | Repaired/redacted response | Yes (status: resolved) |
| `ESCALATE` | High-impact unverified, financial advice, bias signal | Safe fallback message | Yes (status: open) |
| `BLOCK` | Critical PII, safety violation, hard rule triggered | Safe fallback message | Yes (status: open) |

---

## 📡 API Reference

### Core Evaluation Gateway

#### `POST /api/v1/gateway/evaluate`

The main evaluation endpoint. Submit an AI response for real-time risk assessment.

**Request Body:**
```json
{
  "application_id": "my-app",
  "conversation_id": "session-001",
  "request": {
    "text": "Customer question here"
  },
  "response": {
    "text": "AI response here"
  },
  "context": {
    "country": "IN",
    "use_case": "customer_support",
    "business_impact": "high",
    "trusted_data": {
      "order_id": "ORD-001",
      "refund_status": "PENDING",
      "order_status": "Shipped"
    }
  },
  "telemetry": {
    "model": "gpt-4o-mini",
    "input_tokens": 100,
    "output_tokens": 80,
    "llm_calls": 1,
    "tool_calls": 0,
    "retries": 0,
    "latency_ms": 300,
    "estimated_cost": 0.10
  }
}
```

**Response Body:**
```json
{
  "decision": "REPAIR",
  "final_response": "I'm unable to confirm the refund status right now...",
  "original_response": "Your refund was processed yesterday.",
  "risk": {
    "performance": { "score": 0.62, "level": "HIGH" },
    "cost": { "score": 0.15, "level": "LOW" },
    "responsibility": { "score": 0.37, "level": "MEDIUM" },
    "overall": { "score": 0.62, "level": "HIGH" }
  },
  "reasons": [
    "Contradiction detected: AI claims refund was processed but trusted data shows PENDING",
    "High-impact context with unverified response"
  ],
  "incident_id": "a1b2c3d4-...",
  "repair_applied": true,
  "fast_screen_ms": 2,
  "total_evaluation_ms": 847,
  "pii_entities": [],
  "evidence": [
    { "source": "trusted_transaction_data", "score": 1.0, "snippet": "..." }
  ]
}
```

### Dashboard & Analytics

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/dashboard/summary` | Aggregated stats: total evaluations, decision breakdown, risk scores |
| `GET` | `/api/v1/dashboard/recent-events` | Last N risk events with full details |
| `GET` | `/api/v1/incidents` | Paginated list of all incidents |
| `GET` | `/api/v1/incidents/{id}` | Full incident detail with evidence |
| `PATCH` | `/api/v1/incidents/{id}/resolve` | Resolve an open incident |
| `GET` | `/api/v1/policies` | List all active policies |
| `PUT` | `/api/v1/policies/{use_case}` | Update policy for a use case |

### Demo Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/demo/scenarios` | List all available demo scenarios |
| `POST` | `/api/v1/demo/run/{scenario}` | Run a random variant of a named scenario |

**Available scenarios:** `safe`, `hallucination`, `pii`, `cost_anomaly`, `escalation`

### WebSocket

| Endpoint | Protocol | Description |
|---|---|---|
| `ws://localhost:8000/ws/risk-stream` | WebSocket | Live risk event stream (real-time dashboard updates) |

### Health

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health + DB connectivity |

**Interactive API docs available at:** `http://localhost:8000/docs`

---

## 📐 Data Models

### EvaluateRequest

```
EvaluateRequest
├── application_id: str          # Your app identifier
├── conversation_id: str?        # Optional session tracking
├── request: RequestIn
│   └── text: str               # What the user asked
├── response: ResponseIn
│   └── text: str               # What your AI responded
├── context: ContextIn
│   ├── country: str            # "IN", "US", "GB", etc.
│   ├── use_case: str           # "customer_support", "financial_decision_support", etc.
│   ├── business_impact: str    # "low" | "medium" | "high" | "critical"
│   └── trusted_data: dict      # Ground truth from your DB (order status, amounts, etc.)
└── telemetry: TelemetryIn
    ├── model: str              # LLM model name
    ├── input_tokens: int
    ├── output_tokens: int
    ├── llm_calls: int          # Number of LLM calls made
    ├── tool_calls: int         # Number of tool/function calls
    ├── retrieval_calls: int    # Number of retrieval calls
    ├── retries: int
    ├── latency_ms: int
    └── estimated_cost: float   # Cost in your currency (INR by default)
```

### EvaluateResponse

```
EvaluateResponse
├── decision: str               # "ALLOW" | "REPAIR" | "ESCALATE" | "BLOCK"
├── final_response: str         # The safe response to show the user
├── original_response: str      # The raw AI response (before any repair)
├── risk: RiskSummary
│   ├── performance: { score, level }   # Factual accuracy dimension
│   ├── cost: { score, level }          # Cost/efficiency dimension
│   ├── responsibility: { score, level }# Privacy/safety/policy dimension
│   └── overall: { score, level }       # Combined contextual score
├── reasons: [str]              # Human-readable explanation of the decision
├── incident_id: str?           # UUID of created incident (if non-ALLOW)
├── repair_applied: bool
├── fast_screen_ms: int         # Latency of phase 1
├── total_evaluation_ms: int    # End-to-end latency
├── pii_entities: [{ type, text, confidence }]
└── evidence: [{ source, score, snippet }]
```

---

## 🛠️ Tech Stack

### Backend

| Layer | Technology | Purpose |
|---|---|---|
| **Framework** | FastAPI 0.111 | Async REST + WebSocket API |
| **ORM** | SQLAlchemy 2.0 (async) | Database models |
| **Database** | PostgreSQL 16 + pgvector | Persistent storage + vector similarity search |
| **Cache** | Redis 7 | Session cache, pub/sub |
| **LLM Clients** | google-genai, openai, anthropic | Multi-provider LLM support |
| **Logging** | structlog | Structured JSON logging |
| **Config** | pydantic-settings | Type-safe settings from .env |
| **Server** | Uvicorn | ASGI server |

### Frontend

| Layer | Technology | Purpose |
|---|---|---|
| **Framework** | React 18 + TypeScript | UI |
| **Build Tool** | Vite | Dev server + bundling |
| **Routing** | React Router v6 | Client-side routing |
| **Styling** | CSS Modules + custom design system | Dark theme, glassmorphism |
| **WebSocket** | Native WebSocket API | Real-time event stream |
| **HTTP Client** | Fetch API | REST calls to backend |

### Infrastructure

| Component | Technology |
|---|---|
| **Containerization** | Docker + Docker Compose |
| **CI/CD** | Makefile targets |
| **Vector DB** | pgvector (PostgreSQL extension) |
| **Database Migrations** | SQLAlchemy autogenerate |

---

## 📁 Project Structure

```
control_plane/
│
├── 📄 docker-compose.yml           # All services: postgres, redis, backend, frontend
├── 📄 .env                         # Environment config (copy from .env.example)
├── 📄 Makefile                     # Common dev commands
│
├── 📂 backend/
│   ├── 📄 Dockerfile
│   ├── 📄 requirements.txt
│   └── 📂 app/
│       ├── 📄 main.py              # FastAPI app + router registration + lifespan
│       ├── 📄 config.py            # Settings (pydantic-settings from .env)
│       │
│       ├── 📂 api/                 # HTTP route handlers
│       │   ├── routes_gateway.py   # POST /evaluate — main evaluation endpoint
│       │   ├── routes_dashboard.py # GET /summary, /recent-events, /incidents
│       │   ├── routes_policies.py  # CRUD /policies
│       │   ├── routes_demo.py      # POST /demo/run/{scenario}
│       │   ├── routes_ws.py        # WebSocket /ws/risk-stream
│       │   ├── routes_health.py    # GET /health
│       │   └── demo_data.py        # 300 randomised demo scenario configs
│       │
│       ├── 📂 controlplane/        # 🔥 The core evaluation engines
│       │   ├── orchestrator.py     # 6-phase pipeline orchestration
│       │   ├── fast_screen.py      # Phase 1: Deterministic risk screen
│       │   ├── performance_engine.py # Phase 2a: Factual accuracy + hallucination
│       │   ├── cost_engine.py      # Phase 2b: Cost + agent loop detection
│       │   ├── responsibility_engine.py # Phase 2c: PII + safety + policy
│       │   ├── risk_engine.py      # Phase 3: Combined risk scoring
│       │   ├── repair_service.py   # Phase 4: PII redaction + LLM repair
│       │   ├── policy_engine.py    # Policy lookup + defaults
│       │   └── types.py            # Dataclasses for engine results
│       │
│       ├── 📂 ai/                  # LLM integration
│       │   ├── model_client.py     # Provider-agnostic LLM client (OpenAI/Gemini/Anthropic)
│       │   ├── agent.py            # Demo scenario system prompts + call_agent()
│       │   ├── judge.py            # LLM-as-Judge evaluation prompts
│       │   └── prompts.py          # Repair + evaluation prompt templates
│       │
│       ├── 📂 privacy/             # PII handling
│       │   ├── pii_detector.py     # Deep PII detection (regex + policy rules)
│       │   └── redactor.py         # PII redaction/masking
│       │
│       ├── 📂 retrieval/           # Evidence retrieval
│       │   └── retriever.py        # pgvector + keyword evidence search
│       │
│       ├── 📂 db/                  # Database layer
│       │   ├── models.py           # SQLAlchemy ORM models
│       │   └── session.py          # Async engine + session factory
│       │
│       ├── 📂 schemas/             # Pydantic request/response schemas
│       │   └── gateway.py          # EvaluateRequest, EvaluateResponse, etc.
│       │
│       ├── 📂 ws/                  # WebSocket management
│       │   └── manager.py          # Connection manager + broadcast
│       │
│       ├── 📂 seed/                # Demo data seeding
│       │   └── seed_demo_data.py   # Seeds DB + in-memory evidence on startup
│       │
│       └── 📂 telemetry/           # Observability
│
└── 📂 frontend/
    ├── 📄 Dockerfile
    ├── 📄 vite.config.ts
    └── 📂 src/
        ├── 📄 App.tsx              # Root + routing
        │
        ├── 📂 pages/               # Full-page views
        │   ├── Dashboard.tsx       # Main dashboard with all panels
        │   ├── Incidents.tsx       # Incident log table
        │   ├── IncidentDetail.tsx  # Individual incident deep-dive
        │   ├── Policies.tsx        # Policy editor
        │   └── ReviewQueue.tsx     # Human review queue
        │
        └── 📂 components/          # Reusable UI components
            ├── CustomEvalPanel.tsx  # Interactive API testing UI
            ├── DemoPanel.tsx        # 5-scenario demo runner
            ├── LiveEventStream.tsx  # WebSocket real-time feed
            ├── Layout.tsx           # Navigation + page shell
            ├── IncidentTable.tsx    # Sortable incidents list
            ├── RiskScoreCard.tsx    # Score visualization
            └── DecisionBadge.tsx    # ALLOW/BLOCK/REPAIR/ESCALATE badge
```

---

## 🚀 Quick Start (Docker)

### Prerequisites

- [Docker Desktop](https://docs.docker.com/get-docker/) (includes Compose)
- A Gemini, OpenAI, or Anthropic API key

### 1. Clone the repo

```bash
git clone <your-repo-url> control_plane
cd control_plane
```

### 2. Create your `.env` file

```bash
cp .env.example .env
```

Edit `.env` and fill in your API key:

```env
# Choose your LLM provider
LLM_PROVIDER=gemini               # or: openai, anthropic
LLM_API_KEY=your-api-key-here
LLM_MODEL=gemini-3.6-flash        # or: gpt-4o-mini, claude-3-haiku-20240307

# Enable the LLM judge for deep evaluation
ENABLE_LLM_JUDGE=true
```

### 3. Start all services

```bash
docker compose up -d
```

This starts:
- `cp_postgres` — PostgreSQL 16 with pgvector
- `cp_redis` — Redis 7
- `cp_backend` — FastAPI on port 8000
- `cp_frontend` — React on port 3000

### 4. Open the Dashboard

- **Dashboard:** http://localhost:3000
- **API Docs (Swagger):** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

### 5. Run your first evaluation

```bash
curl -X POST http://localhost:8000/api/v1/gateway/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "application_id": "my-app",
    "request": { "text": "Where is my refund?" },
    "response": { "text": "Your refund was processed yesterday and credited to your account." },
    "context": {
      "use_case": "customer_support",
      "business_impact": "high",
      "trusted_data": { "refund_status": "PENDING" }
    },
    "telemetry": { "model": "gpt-4o-mini", "estimated_cost": 0.05 }
  }'
```

You should get back a `REPAIR` decision with `"Contradiction detected"` in the reasons.

### Useful Commands

```bash
# View live backend logs
docker compose logs -f backend

# Restart only the backend (after code changes)
docker compose build backend && docker compose up -d --no-deps backend

# Stop all services
docker compose down

# Full reset (removes database volumes)
docker compose down -v
```

---

## ⚙️ Configuration Reference

All settings are loaded from `.env` via pydantic-settings. The backend container reads `.env` from the project root (mounted via `env_file:` in `docker-compose.yml`).

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | Environment name |
| `BACKEND_PORT` | `8000` | Backend server port |
| `DATABASE_URL` | SQLite (dev) | Async PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| **LLM Settings** | | |
| `LLM_PROVIDER` | `openai` | `openai`, `gemini`, or `anthropic` |
| `LLM_API_KEY` | _(empty)_ | Your LLM API key |
| `LLM_MODEL` | `gpt-4o-mini` | Model name for the provider |
| **Feature Flags** | | |
| `ENABLE_DEMO_MODE` | `true` | Seed demo data on startup |
| `ENABLE_WEBSOCKETS` | `true` | Enable real-time event stream |
| `ENABLE_DEEP_CHECKS` | `true` | Run deep evaluation phases |
| `ENABLE_LLM_JUDGE` | `false` | Use LLM for claim-level grounding check (requires API key + quota) |
| **Risk Thresholds** | | |
| `RISK_LOW_THRESHOLD` | `0.25` | Score below this → LOW |
| `RISK_MEDIUM_THRESHOLD` | `0.50` | Score below this → MEDIUM |
| `RISK_HIGH_THRESHOLD` | `0.75` | Score below this → HIGH |
| **Cost Thresholds** | | |
| `DEFAULT_EXPECTED_COST_INR` | `0.20` | Baseline cost per request (INR) |
| `COST_MULTIPLIER_MEDIUM` | `2.0` | Cost alert threshold (2x baseline) |
| `COST_MULTIPLIER_HIGH` | `4.0` | Cost anomaly threshold (4x baseline) |
| `MAX_TOOL_CALLS_DEFAULT` | `5` | Max tool calls before flagging |
| `MAX_RETRIES_DEFAULT` | `2` | Max retries before flagging |
| `DEFAULT_LATENCY_BUDGET_MS` | `700` | Expected max latency |
| **PII** | | |
| `PII_ENGINE` | `regex` | PII detection engine (`regex`) |

---

## 🎭 Demo Scenarios

The Demo Panel (accessible from the dashboard) runs pre-configured scenarios that trigger live Gemini AI responses and then put them through the full ControlPlane pipeline.

Each scenario has **60 randomised variants**, so every click produces a unique prompt and response.

| Scenario | Trigger | Expected Decision | Key Risk |
|---|---|---|---|
| **Safe Response** | Simple customer service query | `ALLOW` | None — demonstrating the happy path |
| **Hallucination / Contradiction** | AI claims refund was processed but trusted_data says PENDING | `REPAIR` | Performance — contradiction detected |
| **PII Leakage** | AI response contains email, phone, PAN number | `REPAIR` | Responsibility — PII redacted |
| **Cost Anomaly / Agent Loop** | Telemetry shows 7x cost, 9 tool calls, 3 retries | `REPAIR` or `ESCALATE` | Cost — excessive agent execution |
| **High-Impact Escalation** | AI gives confident financial/investment advice | `ESCALATE` | Responsibility — policy violation, requires human review |

---

## 🔬 Custom Evaluation Guide

Use the **Custom Eval Panel** in the dashboard to test your own AI responses through the real pipeline.

### Triggering the Deep Evaluation Path

The fast screen will immediately ALLOW low-risk responses. To force deep evaluation and see the LLM API in action, include signals like these:

#### Test: Hallucination Detection
```
Request:  "What is the status of my order refund?"
Response: "Your refund of ₹15,000 was processed yesterday and credited to your account."

Trusted Data:
{
  "order_id": "ORD-12345",
  "refund_status": "PENDING",
  "expected_date": "Next week"
}
```
**Expected:** `REPAIR` — the response contradicts `refund_status: PENDING`

#### Test: PII Leakage
```
Request:  "Can you confirm my account details?"
Response: "Your account is linked to 9876543210 and email rahul@example.com. PAN: ABCDE1234F."

Trusted Data: {}
```
**Expected:** `REPAIR` — email, phone, and PAN are detected and redacted

#### Test: Dangerous Financial Advice
```
Request:  "Should I put my ₹10 lakh retirement savings into crypto?"
Response: "Yes! Crypto is the future. Put all ₹10 lakh in now. Guaranteed 30% returns in 3 months."

Trusted Data: {}
Use Case:  financial_decision_support
```
**Expected:** `ESCALATE` — financial recommendation policy violation triggers human review

#### Test: Cost Anomaly

Set the Telemetry section with extreme values:
- `llm_calls: 8`, `tool_calls: 11`, `retries: 4`, `estimated_cost: 1.80`, `latency_ms: 9000`

**Expected:** `REPAIR` or `ESCALATE` — agent loop and cost anomaly detected

---

## 🖥️ Frontend UI Guide

The dashboard is built with React + TypeScript and consists of 5 main pages:

### Dashboard (Home)
- **Risk Score Cards** — Live overview of performance, cost, and responsibility risk levels
- **Live Event Stream** — Real-time WebSocket feed showing the last 20 evaluations
- **AI Interaction Inspector** — Detailed panel showing most recent evaluation results
- **Custom Eval Panel** — Interactive form to evaluate any AI response
- **Demo Panel** — One-click scenario testing with live Gemini responses

### Incidents
- Sortable, filterable table of all flagged incidents
- Filter by type: `hallucination`, `pii_leakage`, `cost_anomaly`, `escalation`, `policy_violation`
- Filter by severity: LOW, MEDIUM, HIGH, CRITICAL
- Click any row to view the full incident detail

### Incident Detail
- Full request/response comparison (original vs. repaired)
- PII entities detected and redacted
- Evidence used for the evaluation
- Risk scores across all three dimensions
- Reasons for the decision
- One-click resolve for open incidents

### Policies
- View and edit risk policies per use-case
- Configurable thresholds, rules, and action overrides
- Changes take effect immediately on new evaluations

### Review Queue
- Open escalated incidents awaiting human review
- Approve or reject AI responses
- Full context for informed decisions

---

## 🤖 Supported LLM Providers

ControlPlane works with any of these providers. Set `LLM_PROVIDER` and `LLM_API_KEY` in your `.env`:

| Provider | `LLM_PROVIDER` | Recommended `LLM_MODEL` | Notes |
|---|---|---|---|
| **Google Gemini** | `gemini` | `gemini-3.6-flash` | Best speed/cost ratio; free tier available |
| **OpenAI** | `openai` | `gpt-4o-mini` | Best for LLM-as-Judge quality |
| **Anthropic** | `anthropic` | `claude-3-haiku-20240307` | Strong for safety evaluation |

The provider is used for:
1. **Demo scenario live responses** — `call_agent()` uses the configured LLM to generate a realistic AI response for each scenario
2. **LLM-as-Judge** (if `ENABLE_LLM_JUDGE=true`) — A second LLM call evaluates claim-level grounding
3. **Repair regeneration** — Constrained rewriting of unsafe/contradicted responses

> **Note on quotas:** If using the Gemini free tier, you are limited to 15 requests/minute. The demo scenarios count towards this quota. If you hit quota errors, wait 60 seconds and try again.

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Setup (without Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
cd backend
# Unit tests
pytest tests/

# E2E scenario test
python test_e2e.py
python test_all_scenarios.py
```

### Adding a New Risk Engine

1. Create your engine in `backend/app/controlplane/your_engine.py`
2. Add a result type to `types.py`
3. Import and run it in `orchestrator.py` Phase 2 (add to `asyncio.gather()`)
4. Incorporate the score in `risk_engine.py`

### Adding a New Demo Scenario

1. Add your scenario config to `backend/app/api/demo_data.py`
2. Add a system prompt in `backend/app/ai/agent.py`'s `SCENARIO_SYSTEM_PROMPTS`
3. Add the static template to `SCENARIOS` dict in `routes_demo.py`

---

<div align="center">

Built with ❤️ to make AI deployments safer, more transparent, and more accountable.

**[Live Demo](http://localhost:3000)** · **[API Docs](http://localhost:8000/docs)** · **[Report an Issue](#)**

</div>
