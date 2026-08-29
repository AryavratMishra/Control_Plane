# ControlPlane.ai — Task List

## Phase 1 — Infrastructure
- [ ] docker-compose.yml
- [ ] .env.example
- [ ] Makefile
- [ ] backend/Dockerfile
- [ ] frontend/Dockerfile

## Phase 2 — Backend Skeleton
- [ ] backend/requirements.txt
- [ ] backend/app/main.py
- [ ] backend/app/config.py
- [ ] backend/app/dependencies.py
- [ ] backend/app/db/session.py
- [ ] backend/app/db/models.py
- [ ] backend/alembic setup
- [ ] backend/app/schemas/

## Phase 3 — Core Engines
- [ ] backend/app/controlplane/fast_screen.py
- [ ] backend/app/privacy/pii_detector.py
- [ ] backend/app/privacy/redactor.py
- [ ] backend/app/controlplane/responsibility_engine.py
- [ ] backend/app/telemetry/cost_calculator.py
- [ ] backend/app/controlplane/cost_engine.py
- [ ] backend/app/ai/model_client.py
- [ ] backend/app/ai/judge.py
- [ ] backend/app/ai/embeddings.py
- [ ] backend/app/ai/prompts.py
- [ ] backend/app/retrieval/retriever.py
- [ ] backend/app/controlplane/performance_engine.py
- [ ] backend/app/controlplane/risk_engine.py
- [ ] backend/app/controlplane/action_engine.py
- [ ] backend/app/controlplane/repair_service.py
- [ ] backend/app/controlplane/policy_engine.py
- [ ] backend/app/controlplane/orchestrator.py

## Phase 4 — API Routes
- [ ] backend/app/api/routes_gateway.py
- [ ] backend/app/api/routes_incidents.py
- [ ] backend/app/api/routes_dashboard.py
- [ ] backend/app/api/routes_policies.py
- [ ] backend/app/api/routes_demo.py
- [ ] backend/app/api/routes_health.py
- [ ] backend/app/api/routes_ws.py (WebSocket)

## Phase 5 — Seed Data
- [ ] data/seed/orders.csv
- [ ] data/trusted_docs/ (policy documents)
- [ ] data/demo_scenarios/ (4 scenario definitions)
- [ ] backend/app/seed/seed_demo_data.py
- [ ] backend/app/seed/seed_policies.py

## Phase 6 — Frontend
- [ ] frontend/ Vite+React+TypeScript scaffold
- [ ] frontend design system (Tailwind config, globals)
- [ ] frontend/src/pages/Dashboard.tsx
- [ ] frontend/src/pages/Incidents.tsx
- [ ] frontend/src/pages/IncidentDetail.tsx
- [ ] frontend/src/pages/ReviewQueue.tsx
- [ ] frontend/src/pages/Policies.tsx
- [ ] frontend/src/components/DemoPanel.tsx
- [ ] frontend/src/components/* (all components)
- [ ] frontend/src/hooks/useWebSocket.ts
- [ ] frontend/src/services/api.ts

## Phase 7 — Tests
- [ ] backend/tests/unit/test_fast_screen.py
- [ ] backend/tests/unit/test_cost_engine.py
- [ ] backend/tests/unit/test_responsibility_engine.py
- [ ] backend/tests/unit/test_risk_engine.py
