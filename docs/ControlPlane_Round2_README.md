# ControlPlane.ai — Round 2 Working Prototype Specification

> **Purpose:** This README is an implementation blueprint for an agentic coding AI or engineering team to build the **ControlPlane.ai** Round 2 prototype for the Accenture Reinvent with AI Hackathon.
>
> **Primary objective:** Build a convincing, working prototype of a real-time, model-agnostic AI governance/control layer that evaluates AI outputs and execution telemetry across **performance, cost, and responsibility**, then takes an appropriate action: **ALLOW, REPAIR, ESCALATE, or BLOCK**.
>
> **Important:** This is a hackathon prototype, not a production-certified governance platform. The implementation should be technically credible, demonstrable, modular, and honest about the limits of automated evaluation.

---

## 1. Executive Summary

### 1.1 Product

**ControlPlane.ai** is a middleware/control layer that sits around enterprise AI applications and intercepts AI requests, responses, and execution telemetry before the response is delivered or an AI-generated action is executed.

The platform continuously evaluates three dimensions:

1. **Performance / Trustworthiness** — Is the response supported by evidence, internally consistent, and free from obvious hallucination/unsupported claims?
2. **Cost / Efficiency** — Is the AI execution consuming disproportionate tokens, model calls, tool calls, retries, or latency relative to the expected value/cost for that use case?
3. **Responsibility / Safety** — Does the response violate privacy, security, safety, fairness, or enterprise policy controls?

The outputs of these checks are combined by a **risk engine** that considers severity, confidence, business impact, use-case risk profile, and policy context. The platform then selects one of four actions:

- **ALLOW** — response is acceptable.
- **REPAIR** — response can be safely modified or regenerated.
- **ESCALATE** — uncertain or high-impact case requires a human.
- **BLOCK** — response/action must not reach the user or downstream system.

### 1.2 Differentiating idea

The core differentiator is **risk-adaptive evaluation**:

> Do not perform expensive, deep AI evaluation on every response. Use fast deterministic checks first; increase scrutiny only when risk, uncertainty, or business impact warrants it.

This directly addresses the problem statement's latency challenge while reducing alert fatigue and unnecessary evaluation cost.

### 1.3 Primary prototype scenario

The prototype should use an **enterprise customer-support AI agent** as the main end-to-end demonstration because it naturally supports all three risk categories:

- A response can be factually wrong relative to trusted transaction data.
- The agent can incur excessive model/tool-call cost.
- The response can expose PII or violate company policy.
- High-impact/uncertain cases can be sent for human review.

The architecture must still be generalized enough to demonstrate that the same ControlPlane can protect customer-facing AI, internal copilots, and decision-support workflows.

---

# 2. Problem Statement — Operational Interpretation

The supplied challenge describes an enterprise environment in which multiple AI applications run simultaneously, with different risk tolerances, data sources, latency budgets, and regulatory/policy requirements.

The central gap is:

> Enterprises increasingly need to know **before an AI output causes a business consequence** whether the output is trustworthy, economically efficient, and responsible.

### 2.1 Performance risk

AI can be confidently wrong. There may be no direct, real-time ground truth for every claim, so the system must reason from available evidence and explicitly express uncertainty.

Examples:

- Hallucinated product information.
- Contradiction with a trusted database/document.
- Unsupported claim presented as fact.
- Incorrect answer generated from stale/irrelevant retrieval context.

### 2.2 Cost risk

AI can be correct but economically inefficient.

Examples:

- Too many LLM calls for a simple request.
- Excessive tool calls.
- Agent retry/loop behavior.
- Excess token generation.
- Expensive model invoked when a cheaper model would be sufficient.
- Human rework caused by poor AI output.

### 2.3 Responsibility risk

AI can be unsafe, unfair, privacy-invasive, or inconsistent with enterprise policy.

Examples:

- PII/financial/customer information leakage.
- Unsafe or disallowed content.
- Confidential internal information exposure.
- Policy violations.
- Potential bias signals.
- High-impact decisions made without adequate evidence or human oversight.

### 2.4 Real-world complexity that the prototype must acknowledge

The Round 2 brief introduces several important realities. The design must explicitly account for them rather than pretending they do not exist:

- Customer-facing, internal, batch, and decision-support AI require different risk tolerance and latency budgets.
- Bias, hallucination, and privacy risks can overlap.
- Ground truth may not be available in real time.
- Over-flagging creates alert fatigue; under-flagging creates risk.
- Multi-turn and agentic workflows produce compounding downstream risk.
- Regulations differ by geography/industry and evolve over time.
- Enterprises often consume foundation models through APIs, limiting access to model internals.

These constraints are why ControlPlane is designed as a **model-agnostic middleware and policy-driven control layer** rather than as a replacement foundation model.

---

# 3. Product Vision

## 3.1 One-line value proposition

> **ControlPlane.ai is a real-time control layer that helps enterprises detect, understand, and intervene on AI risk before that risk becomes a business incident.**

## 3.2 Positioning

Do not position the product as merely:

- an AI dashboard;
- a hallucination detector;
- a generic content safety filter;
- an LLM wrapper.

Position it as:

> **AI infrastructure that observes AI behavior and dynamically controls what is allowed to proceed.**

## 3.3 Product principles

1. **Model agnostic** — avoid hard dependence on one foundation model vendor.
2. **Evidence aware** — prefer trusted evidence over raw model confidence.
3. **Risk adaptive** — use deeper evaluation when risk or uncertainty warrants it.
4. **Policy driven** — behavior changes by use case, geography, business impact, and enterprise policy.
5. **Human centered** — escalation is a designed capability, not a failure state.
6. **Action oriented** — detection must lead to a clear action.
7. **Auditable** — every significant intervention should have a machine-readable reason trail.
8. **Honest about uncertainty** — no false claim that automated checks are perfect.

---

# 4. Target Users

### 4.1 Enterprise AI Platform / Engineering Team

Needs:

- One control layer across many AI applications.
- Telemetry and risk visibility.
- API/middleware integration.
- Cost and reliability monitoring.

### 4.2 Responsible AI / Governance Team

Needs:

- Policies.
- Incident review.
- Audit trail.
- Bias/privacy/safety signals.
- Human review workflow.

### 4.3 Business Owner / Operations Leader

Needs:

- Are AI systems safe enough to use?
- How often are interventions happening?
- How much cost is being saved?
- What types of failures are most common?

### 4.4 Human Reviewer

Needs:

- A concise explanation of why an AI output was escalated.
- Relevant evidence.
- AI response and conversation context.
- Ability to approve, reject, or override.

---

# 5. Prototype Scope

## 5.1 Must-have features

The Round 2 prototype must demonstrate the following:

### A. AI interception / gateway

The system accepts an AI response plus metadata/telemetry and routes it through ControlPlane before final delivery.

### B. Fast Risk Screen

Fast, low-latency checks that can run on every response:

- PII detection.
- Basic policy rules.
- Basic safety checks.
- High-impact use-case classification.
- Cost/telemetry anomaly signals.
- Presence/absence of evidence.

### C. Performance Engine

At minimum:

- Claim extraction or claim-level verification.
- Retrieval of relevant trusted evidence.
- Evidence/response consistency comparison.
- Contradiction detection.
- Unsupported claim detection.
- Uncertainty signal when evidence is weak or absent.

### D. Cost Engine

At minimum:

- Model name.
- Input/output tokens.
- Model calls.
- Tool calls.
- Retry count.
- Latency.
- Estimated cost.
- Expected/baseline cost.
- Cost multiplier.

### E. Responsibility Engine

At minimum:

- PII detection.
- Enterprise policy checks.
- Unsafe-content check.
- High-impact decision detection.
- Potential bias signal capability or clearly labeled limited prototype.

### F. Risk Engine

Combines:

- Performance risk.
- Cost risk.
- Responsibility risk.
- Business impact.
- Context / use-case policy.
- Detector confidence.

### G. Action Engine

Must support:

- ALLOW.
- REPAIR.
- ESCALATE.
- BLOCK.

### H. Human review queue

At minimum:

- Incident list.
- Incident detail.
- Evidence and reason.
- Approve/reject/override action.
- Audit trail.

### I. Real-time dashboard

At minimum:

- Requests processed.
- Allowed.
- Repaired.
- Escalated.
- Blocked.
- Current risk stream.
- Cost savings estimate.
- Incident drill-down.
- Risk trend charts.

### J. Configurable policy layer

Policies must be data/config-driven rather than deeply hard-coded.

---

# 6. Non-goals for the Hackathon Prototype

Do **not** spend time on:

- Training a new foundation model.
- Full production-scale Kubernetes architecture.
- Full legal/regulatory compliance certification.
- Perfect automated bias detection.
- Perfect hallucination detection for arbitrary open-world questions.
- Building every enterprise connector.
- Full distributed tracing infrastructure if it compromises demo progress.
- Supporting every model provider.
- Building a visually accurate 3D/immersive enterprise environment.

A strong, narrow, demonstrable prototype is preferred over a broad but unreliable platform.

---

# 7. Recommended Technology Stack

## 7.1 Final stack

| Layer | Recommendation | Role |
|---|---|---|
| Frontend | **React + TypeScript** | Control Room, incident review, policy UI |
| UI | **Tailwind CSS** | Fast, consistent enterprise UI |
| Charts | **Recharts** | Risk/cost/latency visualizations |
| Backend | **Python + FastAPI** | API gateway and orchestration |
| AI/LLM | **OpenAI and/or Gemini API** | Primary model + evaluation |
| Performance verification | **RAG + LLM-as-a-Judge + deterministic signals** | Grounding/contradiction evaluation |
| Embeddings | Provider embeddings or open embedding model | Evidence retrieval |
| Vector store | **PostgreSQL + pgvector** | Trusted evidence retrieval |
| Database | **PostgreSQL** | Audit trail, configurations, telemetry, incidents |
| PII | **Microsoft Presidio + regex/rules** | Privacy detection |
| Policy | **JSON/YAML + Python policy evaluator** | Configurable use-case/policy controls |
| Real-time | **WebSockets** | Live control-room events |
| Telemetry | **OpenTelemetry** | Model/tool/latency traces where practical |
| Cache/queue | **Redis** (optional but recommended if needed) | Background/deep checks |
| Background tasks | **ARQ/Celery** or FastAPI BackgroundTasks for prototype | Deep evaluations |
| Containerization | **Docker / Docker Compose** | Repeatable local run |
| Testing | **Pytest + Playwright** | Backend + end-to-end UI |

### 7.2 Why Python/FastAPI

The intelligence layer needs access to NLP/AI tooling, retrieval, embeddings, PII detection, model SDKs, evaluation logic, and data science utilities. Python gives the strongest ecosystem for these tasks and FastAPI is lightweight enough for rapid API development.

### 7.3 Why React/TypeScript

The judges need to *see* the product working. The dashboard is a major part of the demonstration. React/TypeScript provides a flexible way to build a credible enterprise control room with real-time incident updates and interactive drill-downs.

### 7.4 Why PostgreSQL + pgvector

PostgreSQL provides a credible single source of truth for the prototype. pgvector allows the same database to store trusted evidence embeddings for retrieval-based verification.

### 7.5 Why Presidio + deterministic rules

Privacy detection should not rely exclusively on an LLM. Deterministic detection is faster, more reproducible, and easier to audit. Combine Presidio/NER/regex with semantic checks when required.

### 7.6 Why OpenTelemetry

The problem explicitly mentions AI cost, latency, agents, multiple tool calls, and multi-turn workflows. Telemetry should therefore capture an execution trace rather than only the final text response.

---

# 8. High-Level Architecture

```mermaid
flowchart LR
    A[Enterprise AI Application] --> B[ControlPlane Gateway]
    B --> C[Foundation Model / AI Agent]
    C --> D[AI Response + Execution Telemetry]
    D --> E[Fast Risk Screen]

    E --> F[Performance Engine]
    E --> G[Cost Engine]
    E --> H[Responsibility Engine]

    F --> I[Risk Engine]
    G --> I
    H --> I

    J[Policy Store] --> I
    K[Trusted Evidence Store] --> F

    I --> L[Action Engine]
    L --> M[ALLOW]
    L --> N[REPAIR]
    L --> O[ESCALATE]
    L --> P[BLOCK]

    O --> Q[Human Review Queue]
    Q --> L

    B --> R[Telemetry Store]
    I --> S[Audit Store]
    S --> T[Control Room Dashboard]
    R --> T
```

---

# 9. Where ControlPlane Sits

There are two acceptable prototype patterns.

## Pattern A — Inline gateway / proxy (preferred)

```text
AI Application
      |
      v
ControlPlane Gateway
      |
      v
Foundation Model / Agent
      |
      v
ControlPlane Evaluation
      |
      v
Final Response / Action
```

This is the strongest product story because ControlPlane behaves like enterprise middleware.

## Pattern B — SDK wrapper

```text
Application
   |
   +-- controlplane.generate(...)
             |
             +--> Model
             +--> Evaluate
             +--> Decide
             +--> Return final result
```

For a hackathon, a gateway and/or wrapper can coexist. The important point is that the AI application does not need to be rebuilt around a specific model provider.

---

# 10. Core Request Lifecycle

## 10.1 End-to-end workflow

```mermaid
sequenceDiagram
    participant U as User
    participant A as AI App
    participant M as Model/Agent
    participant C as ControlPlane
    participant V as Verifier
    participant R as Risk Engine
    participant H as Human Reviewer

    U->>A: User request
    A->>M: Generate response / execute workflow
    M-->>A: Response + execution telemetry
    A->>C: Submit response + context + telemetry
    C->>C: Fast Risk Screen

    alt Low risk
        C-->>A: ALLOW
        A-->>U: Response
    else Suspicious or high impact
        C->>V: Deep verification
        V-->>C: Evidence + evaluation signals
        C->>R: Risk scoring + policy evaluation

        alt Repairable
            R-->>C: REPAIR
            C->>M: Regenerate / rewrite with constraints
            M-->>C: Repaired response
            C->>C: Re-check
            C-->>A: ALLOW repaired response
            A-->>U: Safe response
        else Human review required
            R-->>C: ESCALATE
            C->>H: Review incident
            H-->>C: Approve / reject / override
            C-->>A: Human-approved action
            A-->>U: Final response/action
        else Severe violation
            R-->>C: BLOCK
            C-->>A: Blocked / safe fallback
            A-->>U: Safe fallback / review message
        end
    end
```

---

# 11. Fast Risk Screen

The Fast Risk Screen exists to solve the latency constraint.

### Principle

> **Fast deterministic checks on every response; expensive AI checks only when needed.**

### Fast checks

- PII regex/Presidio.
- Basic toxicity/safety keywords or lightweight classifier.
- Policy lookups.
- High-impact use-case classification from static application configuration.
- Token and model-cost calculations.
- Tool/retry count anomaly.
- Simple evidence-presence check.

### Output

```json
{
  "fast_risk_level": "MEDIUM",
  "triggers": [
    "financial_context",
    "claim_requires_verification"
  ],
  "needs_deep_check": true,
  "estimated_fast_latency_ms": 45
}
```

### Fast-path decisions

If the response is clearly low risk and all hard-block policies pass, it may be allowed without deep LLM evaluation.

If the response is high impact or a hard privacy/safety rule is triggered, it may be blocked/escalated immediately.

If risk is ambiguous, send the response to deep evaluation.

---

# 12. Performance Engine

## 12.1 Objective

Determine whether an AI response is sufficiently supported by evidence and whether there are signs of hallucination, contradiction, or unsupported claims.

## 12.2 Important limitation

The system must never assume that an answer is objectively true just because the evaluator LLM says it is true.

The engine should use a hierarchy of evidence:

1. Trusted structured enterprise data.
2. Trusted source documents.
3. Retrieved evidence with high relevance.
4. Explicitly provided conversation context.
5. Model evaluation.
6. Model self-reported confidence (lowest value; never treated as proof).

## 12.3 Pipeline

```mermaid
flowchart TD
    A[AI Response] --> B[Claim Extraction]
    B --> C[Evidence Retrieval]
    C --> D[Trusted DB / Documents / Vector Search]
    D --> E[Evidence Ranking]
    E --> F[Claim vs Evidence Comparison]
    F --> G[Deterministic Contradiction Checks]
    G --> H[LLM-as-a-Judge for Semantic Evaluation]
    H --> I[Performance Risk Result]
```

## 12.4 Suggested signals

- `grounding_score`
- `evidence_coverage`
- `contradiction_detected`
- `unsupported_claim_count`
- `source_reliability`
- `semantic_consistency`
- `evaluation_confidence`

## 12.5 Example

AI response:

> "Your ₹25,000 refund was processed yesterday."

Trusted transaction record:

```text
refund_status = PENDING
```

Result:

```json
{
  "performance_risk": "HIGH",
  "contradiction_detected": true,
  "grounding_score": 0.18,
  "evidence_coverage": 0.32,
  "reason": "AI claim contradicts trusted transaction data"
}
```

## 12.6 Handling no ground truth

When trusted evidence is unavailable:

- Do not mark the answer as “true.”
- Mark it as **unverified**.
- Increase uncertainty for high-impact contexts.
- Escalate when policy requires evidence.
- Allow low-impact answers according to policy if appropriate.

This is essential to align with the Round 2 requirement that ground truth may be unavailable.

---

# 13. Cost Engine

## 13.1 Objective

Detect AI executions that are unexpectedly expensive or inefficient.

## 13.2 Captured telemetry

```json
{
  "request_id": "cp-10482",
  "application_id": "customer-support",
  "model": "example-model",
  "input_tokens": 3421,
  "output_tokens": 1280,
  "llm_calls": 4,
  "tool_calls": 7,
  "retrieval_calls": 2,
  "retries": 1,
  "latency_ms": 3210,
  "estimated_cost": 1.42,
  "currency": "INR"
}
```

## 13.3 Baseline

Each use case should have an expected baseline, for example:

```yaml
use_case: customer_support
expected_cost_inr: 0.20
expected_latency_ms: 700
max_tool_calls: 3
max_retries: 1
```

## 13.4 Cost signals

- Absolute cost.
- Cost multiplier vs baseline.
- Token anomaly.
- Tool-call anomaly.
- Retry anomaly.
- Agent loop anomaly.
- Cost per successful task.
- Human rework indicator (when available).

## 13.5 Example

```text
Expected cost: ₹0.20
Actual cost:   ₹1.42
Multiplier:    7.1x
Tool calls:    7
Expected:      <=3

Cost risk: HIGH
```

## 13.6 Recommended optimization behavior

For a cost anomaly, ControlPlane should not automatically discard a valid response.

Potential actions:

- Route future similar requests to a cheaper model.
- Terminate runaway tool loop.
- Request concise regeneration.
- Flag workflow for engineering review.
- Escalate only when cost is coupled with poor outcome or severe agent behavior.

For the demo, the action can be simulated as **OPTIMIZE** internally, while the external ControlPlane action remains one of the four required categories. Recommended mapping: **REPAIR** for a request-level regeneration/optimization, or **ESCALATE** for repeated cost anomalies.

---

# 14. Responsibility Engine

## 14.1 Objective

Detect privacy, security, policy, safety, and potential fairness issues.

## 14.2 PII detection pipeline

```text
Response
   |
   +--> Regex / deterministic patterns
   |
   +--> Presidio / entity recognizer
   |
   +--> Optional semantic classifier
   |
   v
PII findings
```

### PII examples

- Email.
- Phone.
- Address.
- Customer ID.
- Account number.
- Credit-card-like pattern.
- Government ID patterns where relevant to the demo.

### Prototype behavior

PII findings should include:

- Type.
- Text span.
- Confidence.
- Policy classification.
- Recommended action: allow/redact/block.

## 14.3 Enterprise policy checks

Policies should be configuration-driven.

Example:

```yaml
policy_id: finance-high-impact
use_case: finance
rules:
  - type: pii
    action: block
  - type: unsupported_claim
    action: escalate
  - type: financial_recommendation
    action: escalate
  - type: confidential_data
    action: block
```

## 14.4 Safety checks

Use deterministic checks plus an optional classifier/LLM evaluation.

Important: the prototype should not claim perfect safety classification.

## 14.5 Bias signals

The prototype should demonstrate **potential bias signal detection**, not “perfect bias detection.”

Recommended approach:

1. Identify a decision/recommendation context where protected attributes may matter.
2. Generate controlled variants with the protected attribute changed while keeping other information constant.
3. Compare outputs.
4. Flag statistically/semantically meaningful differences.
5. Route high-confidence signals to human review.

Example:

```text
Variant A: Candidate profile + attribute A
Variant B: Same profile + attribute B

Outcome difference: Material
Potential bias signal: TRUE
Action: ESCALATE
```

---

# 15. Risk Engine

## 15.1 Objective

Convert multiple imperfect signals into a contextual overall risk decision.

## 15.2 Do not use a naive average

A simple average is not sufficient.

Example:

- Minor cost anomaly should not cancel out a critical PII leak.
- Moderate uncertainty can be acceptable in a low-impact chatbot but unacceptable in a financial decision-support workflow.

## 15.3 Suggested factors

Each factor should be normalized to 0–1:

- `performance_risk`
- `cost_risk`
- `responsibility_risk`
- `business_impact`
- `detector_confidence`
- `use_case_risk_level`
- `evidence_availability`
- `policy_severity`

## 15.4 Suggested decision logic

Example conceptual calculation:

```text
base_risk = max(
    performance_risk,
    responsibility_risk,
    cost_risk * 0.7
)

context_adjustment = business_impact * use_case_risk_level

confidence_adjustment = detector_confidence

final_risk = combine(base_risk, context_adjustment, confidence_adjustment)
```

The exact formula is implementation-specific. The key requirement is that the engine be **explainable and policy-configurable**.

## 15.5 Hard rules vs soft signals

### Hard rules

Examples:

- Confirmed PII leak under a “never expose” policy.
- Known disallowed content.
- Explicit secret/API-key leakage.

Hard rules can trigger immediate BLOCK.

### Soft signals

Examples:

- Weak evidence.
- Suspected hallucination.
- Potential bias.
- Cost anomaly.

Soft signals should combine into a context-aware risk decision.

---

# 16. Action Engine

## 16.1 Decision matrix

| Condition | Typical Action |
|---|---|
| Low risk, sufficient evidence | ALLOW |
| Minor/fixable issue | REPAIR |
| High-impact + uncertainty | ESCALATE |
| Severe privacy/safety/policy violation | BLOCK |
| Contradiction in critical workflow | BLOCK or ESCALATE depending policy |
| Cost anomaly only | REPAIR/OPTIMIZE or ESCALATE if repeated |
| Potential bias signal | ESCALATE |

## 16.2 Repair patterns

### PII redaction

```text
Raw response
  -> detect PII
  -> replace sensitive spans
  -> re-check
  -> allow if clean
```

### Constrained regeneration

```text
Bad response
  -> extract failure reason
  -> send regeneration instruction
  -> generate revised response
  -> re-run ControlPlane
  -> allow if safe
```

### Safe fallback

If regeneration fails:

> “I’m unable to provide a verified answer right now. Please contact a support representative.”

## 16.3 Escalation

An escalation should contain:

- User request.
- AI response.
- Conversation history relevant to the incident.
- Risk dimensions.
- Evidence.
- Policy triggered.
- Recommended human action.

## 16.4 Block

A blocked response should never reach the end user as originally generated.

For the prototype, return a safe fallback and create a logged incident.

---

# 17. Multi-Turn and Agent Risk

The Round 2 brief explicitly mentions multi-turn and agentic risk.

The system should model a conversation as:

```text
conversation_id
    |
    +-- turn 1
    +-- turn 2
    +-- turn 3
    +-- turn 4
```

For agent execution:

```mermaid
flowchart TD
    A[User Request] --> B[Agent]
    B --> C[LLM Call]
    C --> D[Tool Call]
    D --> E[Tool Result]
    E --> F[LLM Call]
    F --> G[Tool Call]
    G --> H[Action]
    H --> I[Final Response]
    I --> J[ControlPlane Evaluation]
```

The telemetry should preserve a trace/tree so that the ControlPlane can see if a questionable output caused additional downstream operations.

### Prototype requirement

At minimum, persist:

- `conversation_id`
- `turn_id`
- `parent_event_id`
- `tool_calls`
- `model_calls`
- `actions`
- `final_response`

---

# 18. Policy Layer

## 18.1 Why policy must be configurable

The Round 2 brief explicitly states that regulatory and enterprise requirements vary by geography and industry and can evolve.

Therefore, avoid deeply hard-coded rules.

## 18.2 Policy hierarchy

```text
Global defaults
      |
      +--> Industry policy
      |
      +--> Geography policy
      |
      +--> Use-case policy
      |
      +--> Application-specific overrides
```

## 18.3 Example policy model

```json
{
  "policy_id": "customer-support-india-v1",
  "version": 1,
  "use_case": "customer_support",
  "geography": "IN",
  "risk_level": "medium",
  "rules": {
    "pii_exposure": "redact",
    "financial_claim_without_evidence": "escalate",
    "hard_safety_violation": "block",
    "unsupported_low_impact_claim": "repair"
  }
}
```

## 18.4 Policy versioning

Policies should have:

- ID.
- Version.
- Status.
- Effective timestamp.
- Created/updated metadata.

Every incident must store which policy version produced the decision.

---

# 19. Data Architecture

## 19.1 Core entities

```text
applications
models
conversations
requests
responses
execution_events
risk_assessments
incidents
policies
policy_versions
human_reviews
feedback
trusted_documents
retrieval_chunks
```

## 19.2 Suggested relational model

```mermaid
erDiagram
    APPLICATION ||--o{ CONVERSATION : owns
    CONVERSATION ||--o{ REQUEST : contains
    REQUEST ||--o| RESPONSE : generates
    REQUEST ||--o{ EXECUTION_EVENT : contains
    RESPONSE ||--o| RISK_ASSESSMENT : receives
    RISK_ASSESSMENT ||--o| INCIDENT : creates
    INCIDENT ||--o{ HUMAN_REVIEW : reviewed_by
    APPLICATION ||--o{ POLICY_VERSION : uses
    POLICY_VERSION ||--o{ INCIDENT : governs
    TRUSTED_DOCUMENT ||--o{ RETRIEVAL_CHUNK : contains
    REQUEST ||--o{ RETRIEVAL_CHUNK : retrieves
```

---

# 20. Suggested Database Schema

The exact SQL may be optimized during implementation, but the following structure is recommended.

## applications

```text
id UUID PK
name TEXT
use_case TEXT
risk_level TEXT
geography TEXT
latency_budget_ms INT
status TEXT
created_at TIMESTAMP
```

## models

```text
id UUID PK
provider TEXT
model_name TEXT
input_price_per_1k DECIMAL
output_price_per_1k DECIMAL
active BOOLEAN
```

## conversations

```text
id UUID PK
application_id UUID FK
external_conversation_id TEXT
created_at TIMESTAMP
```

## requests

```text
id UUID PK
conversation_id UUID FK
request_text TEXT
risk_context JSONB
created_at TIMESTAMP
```

## responses

```text
id UUID PK
request_id UUID FK
response_text TEXT
model_id UUID FK
final_status TEXT
created_at TIMESTAMP
```

## execution_events

```text
id UUID PK
request_id UUID FK
parent_event_id UUID NULL
 event_type TEXT
model_name TEXT NULL
tool_name TEXT NULL
input_tokens INT NULL
output_tokens INT NULL
latency_ms INT NULL
estimated_cost DECIMAL NULL
metadata JSONB
created_at TIMESTAMP
```

## risk_assessments

```text
id UUID PK
response_id UUID FK
performance_score DECIMAL
performance_risk TEXT
cost_score DECIMAL
cost_risk TEXT
responsibility_score DECIMAL
responsibility_risk TEXT
overall_risk_score DECIMAL
overall_risk_level TEXT
business_impact TEXT
detector_confidence DECIMAL
reasoning JSONB
policy_version_id UUID NULL
created_at TIMESTAMP
```

## incidents

```text
id UUID PK
risk_assessment_id UUID FK
incident_type TEXT
severity TEXT
action TEXT
status TEXT
reason TEXT
evidence JSONB
created_at TIMESTAMP
resolved_at TIMESTAMP NULL
```

## human_reviews

```text
id UUID PK
incident_id UUID FK
reviewer_name TEXT
review_action TEXT
comment TEXT
created_at TIMESTAMP
```

## policies

```text
id UUID PK
name TEXT
description TEXT
```

## policy_versions

```text
id UUID PK
policy_id UUID FK
version INT
config JSONB
status TEXT
effective_from TIMESTAMP
created_at TIMESTAMP
```

## trusted_documents

```text
id UUID PK
name TEXT
source_type TEXT
source_uri TEXT
trust_level TEXT
created_at TIMESTAMP
```

## retrieval_chunks

```text
id UUID PK
document_id UUID FK
content TEXT
embedding VECTOR
metadata JSONB
```

---

# 21. Backend Service Structure

Recommended backend structure:

```text
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   │
│   ├── api/
│   │   ├── routes_gateway.py
│   │   ├── routes_assessments.py
│   │   ├── routes_incidents.py
│   │   ├── routes_policies.py
│   │   ├── routes_dashboard.py
│   │   └── routes_health.py
│   │
│   ├── controlplane/
│   │   ├── orchestrator.py
│   │   ├── fast_screen.py
│   │   ├── performance_engine.py
│   │   ├── cost_engine.py
│   │   ├── responsibility_engine.py
│   │   ├── risk_engine.py
│   │   ├── action_engine.py
│   │   ├── policy_engine.py
│   │   ├── repair_service.py
│   │   ├── escalation_service.py
│   │   └── audit_service.py
│   │
│   ├── ai/
│   │   ├── model_client.py
│   │   ├── judge.py
│   │   ├── embeddings.py
│   │   └── prompts.py
│   │
│   ├── retrieval/
│   │   ├── chunker.py
│   │   ├── retriever.py
│   │   └── grounding.py
│   │
│   ├── privacy/
│   │   ├── pii_detector.py
│   │   └── redactor.py
│   │
│   ├── telemetry/
│   │   ├── tracer.py
│   │   ├── cost_calculator.py
│   │   └── metrics.py
│   │
│   ├── db/
│   │   ├── session.py
│   │   ├── models.py
│   │   └── repositories/
│   │
│   ├── schemas/
│   │   ├── gateway.py
│   │   ├── assessment.py
│   │   ├── incident.py
│   │   └── policy.py
│   │
│   └── seed/
│       ├── seed_demo_data.py
│       └── seed_policies.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── requirements.txt
├── Dockerfile
└── .env.example
```

### Architectural rule

Keep the risk engines modular. Each engine should have a clear input/output contract and should be testable independently.

---

# 22. Frontend Structure

```text
frontend/
├── src/
│   ├── app/
│   ├── components/
│   │   ├── RiskScoreCard.tsx
│   │   ├── LiveEventStream.tsx
│   │   ├── IncidentTable.tsx
│   │   ├── IncidentDrawer.tsx
│   │   ├── DecisionBadge.tsx
│   │   ├── ResponseInspector.tsx
│   │   ├── CostPanel.tsx
│   │   ├── EvidencePanel.tsx
│   │   ├── HumanReviewPanel.tsx
│   │   └── PolicyBadge.tsx
│   │
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── Incidents.tsx
│   │   ├── IncidentDetail.tsx
│   │   ├── Applications.tsx
│   │   ├── Policies.tsx
│   │   └── ReviewQueue.tsx
│   │
│   ├── hooks/
│   │   ├── useWebSocket.ts
│   │   └── useControlPlane.ts
│   │
│   ├── services/
│   │   └── api.ts
│   │
│   ├── types/
│   └── main.tsx
├── package.json
└── .env.example
```

---

# 23. Core API Contracts

The following REST endpoints are recommended.

## POST /api/v1/gateway/evaluate

Primary endpoint for submitting an AI response to ControlPlane.

### Request

```json
{
  "application_id": "customer-support",
  "conversation_id": "conv-001",
  "request": {
    "text": "Where is my refund?"
  },
  "response": {
    "text": "Your refund was processed yesterday."
  },
  "context": {
    "country": "IN",
    "use_case": "customer_support",
    "business_impact": "medium"
  },
  "telemetry": {
    "model": "demo-model",
    "input_tokens": 120,
    "output_tokens": 80,
    "llm_calls": 2,
    "tool_calls": 3,
    "retries": 0,
    "latency_ms": 640,
    "estimated_cost": 0.18
  }
}
```

### Response

```json
{
  "decision": "BLOCK",
  "final_response": "Your refund is currently being processed. We'll notify you once it has been completed.",
  "risk": {
    "performance": {
      "score": 0.89,
      "level": "HIGH"
    },
    "cost": {
      "score": 0.42,
      "level": "MEDIUM"
    },
    "responsibility": {
      "score": 0.91,
      "level": "HIGH"
    },
    "overall": {
      "score": 0.94,
      "level": "CRITICAL"
    }
  },
  "reasons": [
    "AI claim contradicts transaction status",
    "Sensitive account identifier detected"
  ],
  "incident_id": "CP-10482"
}
```

## GET /api/v1/dashboard/summary

Return:

- total_requests
- allowed
- repaired
- escalated
- blocked
- estimated_cost_saved
- average_latency
- risk_breakdown

## GET /api/v1/incidents

Support:

- status
- severity
- application
- risk type
- date range

## GET /api/v1/incidents/{id}

Return full forensic detail.

## POST /api/v1/incidents/{id}/review

### Request

```json
{
  "action": "APPROVE",
  "comment": "Reviewed evidence; response is acceptable under current policy."
}
```

## GET /api/v1/policies

List current policies.

## POST /api/v1/policies

Create policy.

## PUT /api/v1/policies/{id}

Update or create new version.

## WS /ws/control-room

Push real-time events:

```json
{
  "event": "risk_event",
  "incident_id": "CP-10482",
  "application": "customer-support",
  "action": "BLOCK",
  "severity": "CRITICAL",
  "timestamp": "2026-08-29T12:00:00Z"
}
```

---

# 24. Internal Engine Interfaces

Use typed Python interfaces/dataclasses/Pydantic models.

## FastScreenResult

```python
class FastScreenResult:
    risk_level: str
    triggers: list[str]
    hard_block: bool
    needs_deep_check: bool
    latency_ms: int
```

## PerformanceResult

```python
class PerformanceResult:
    risk_level: str
    grounding_score: float
    evidence_coverage: float
    contradiction_detected: bool
    unsupported_claim_count: int
    confidence: float
    reasons: list[str]
    evidence: list[dict]
```

## CostResult

```python
class CostResult:
    risk_level: str
    estimated_cost: float
    expected_cost: float
    cost_multiplier: float
    tool_calls: int
    model_calls: int
    retries: int
    latency_ms: int
    reasons: list[str]
```

## ResponsibilityResult

```python
class ResponsibilityResult:
    risk_level: str
    pii_detected: bool
    pii_entities: list[dict]
    policy_violations: list[dict]
    safety_signal: str | None
    bias_signal: str | None
    confidence: float
    reasons: list[str]
```

## RiskDecision

```python
class RiskDecision:
    overall_score: float
    overall_level: str
    action: str
    reasons: list[str]
    requires_human: bool
    can_repair: bool
```

---

# 25. Risk Scoring Conventions

Use a consistent scale.

### Score

`0.0 = minimal risk`

`1.0 = maximum risk`

### Suggested risk bands

```text
0.00 - 0.24   LOW
0.25 - 0.49   MEDIUM
0.50 - 0.74   HIGH
0.75 - 1.00   CRITICAL
```

These values are illustrative and should be easy to tune through configuration.

### Severity override

A hard policy violation may force `CRITICAL` even if another model-derived score is low.

---

# 26. Latency Strategy

Latency is an explicit requirement in the challenge.

## 26.1 Design target

For the hackathon demo, aim for:

- **Fast path:** ideally under ~200 ms of ControlPlane overhead for simple cases.
- **Deep path:** asynchronous or parallel where practical; can take longer for suspicious/high-risk cases.

Do not claim production-grade latency unless measured.

## 26.2 Parallel evaluation

Performance, cost, and responsibility checks should run in parallel when possible.

```mermaid
flowchart TD
    A[Response] --> B[Fast Screen]
    B --> C[Parallel Deep Checks]
    C --> D[Performance]
    C --> E[Cost]
    C --> F[Responsibility]
    D --> G[Risk Engine]
    E --> G
    F --> G
```

## 26.3 Caching

Potentially cache:

- Policy definitions.
- Repeated trusted evidence retrieval.
- Embeddings.
- Repeated evaluation of identical content where safe.

Avoid caching data that creates privacy or stale-data risk.

---

# 27. Alert Fatigue Strategy

The challenge explicitly calls out over-flagging.

Implement:

### Risk thresholds by use case

```yaml
customer_support:
  medium_action: repair
  high_action: escalate

finance:
  medium_action: escalate
  high_action: block

internal_knowledge:
  medium_action: repair
  high_action: escalate
```

### Confidence-aware alerts

If a detector is weakly confident and the business impact is low, do not create a high-severity incident unnecessarily.

### Deduplication

Repeated identical alerts should be grouped when possible.

### Incident suppression

Allow policy-based suppression for known benign patterns.

---

# 28. Uncertainty Handling

ControlPlane should have a first-class `UNKNOWN / UNVERIFIED` concept internally.

Do not force everything into true/false.

Example:

```text
Evidence available? NO
Risk context? HIGH
Answer impact? HIGH

=> UNVERIFIED + HIGH IMPACT
=> ESCALATE
```

This directly addresses the problem statement's lack of universal ground truth.

---

# 29. Human-in-the-Loop Workflow

```mermaid
flowchart TD
    A[Flagged Incident] --> B[Review Queue]
    B --> C[Reviewer opens incident]
    C --> D[Inspect AI response]
    D --> E[Inspect evidence]
    E --> F[Inspect policies]
    F --> G{Decision}
    G -->|Approve| H[Release / Allow]
    G -->|Reject| I[Block]
    G -->|Request revision| J[Repair]
    G -->|Override| K[Record override]
    H --> L[Audit Log]
    I --> L
    J --> L
    K --> L
```

## Human review record must capture

- Incident ID.
- Reviewer.
- Timestamp.
- Decision.
- Comment.
- Original action.
- Final action.

---

# 30. Feedback Loop

The challenge explicitly suggests feedback loops.

For the prototype, implement a simple mechanism:

```text
Incident
   |
Human decision
   |
Was ControlPlane correct?
   |
   +--> yes
   +--> false positive
   +--> false negative / missed risk
```

Record the feedback so future analysis can show:

- False-positive rate.
- Override rate.
- Detector-specific accuracy.
- Most common failure modes.

A future production system could use this feedback to tune thresholds/models/policies.

---

# 31. Metrics and Monitoring

## 31.1 Core product metrics

Dashboard metrics should include:

- AI interactions processed.
- Allow rate.
- Repair rate.
- Escalation rate.
- Block rate.
- Performance-risk rate.
- Cost-risk rate.
- Responsibility-risk rate.
- Average ControlPlane latency.
- Average total AI latency.
- Estimated cost saved.
- False-positive rate (when labeled data exists).
- Human override rate.

## 31.2 Quality metrics

### False-positive rate

```text
benign cases flagged as risky / all benign cases
```

### False-negative rate

```text
risky cases missed / all labeled risky cases
```

### Intervention precision

```text
correct interventions / all interventions
```

The prototype may use seeded demo labels instead of production ground truth.

---

# 32. Demo Dataset

Create a controlled synthetic dataset so the prototype is deterministic and easy to demonstrate.

## 32.1 Trusted data

Include at least:

### Customer orders

```csv
order_id,customer_id,status,delivery_date,refund_status,refund_amount
ORD1001,C1001,Delivered,2026-08-25,Pending,25000
ORD1002,C1002,Shipped,2026-08-30,None,0
```

### Enterprise policies

Documents such as:

- Refund policy.
- Privacy policy.
- Customer communication policy.
- Financial decision policy.
- Internal data handling policy.

### Cost baselines

A config table with expected cost/latency by use case.

---

# 33. Mandatory Demo Scenarios

The demo should have 4 polished scenarios.

## Scenario 1 — Hallucination / Contradiction

### Input

Customer asks:

> “Where is my ₹25,000 refund?”

### Bad AI response

> “Your ₹25,000 refund was successfully processed yesterday.”

### Trusted data

`refund_status = PENDING`

### ControlPlane

- Performance: HIGH.
- Contradiction: TRUE.
- Responsibility: possibly medium/high if account information is included.
- Action: BLOCK + REPAIR.

### Corrected response

> “Your refund is currently being processed. We’ll notify you once it has been completed.”

---

## Scenario 2 — PII Leakage

### Bad AI response

> “Your account ending 1234 is linked to 98XXXXXX12. Your current balance is …”

### ControlPlane

- PII detected.
- Policy violation.
- Action: REDACT/REPAIR or BLOCK depending policy.

### Show in UI

Highlight the sensitive span and the rule that fired.

---

## Scenario 3 — Cost Anomaly / Agent Loop

### Request

> “What is the status of order ORD1002?”

### Artificially inefficient execution

```text
LLM call -> DB -> LLM -> Search -> LLM -> DB -> LLM -> Retry
```

### ControlPlane

- Cost multiplier > baseline.
- Tool-call anomaly.
- Retry anomaly.
- Action: REPAIR/OPTIMIZE or ESCALATE if repeated.

### Show

```text
Expected: ₹0.20
Actual: ₹1.42
Multiplier: 7.1x
```

---

## Scenario 4 — High-Impact Uncertainty

### Input

> “Should I move my retirement savings into this financial product?”

### AI response

A plausible but insufficiently evidenced recommendation.

### ControlPlane

- Performance: UNVERIFIED.
- Responsibility: HIGH due to decision impact.
- Action: ESCALATE.

### Human review screen

Show:

> “High-impact financial guidance requires human review when sufficient evidence is unavailable.”

This demonstrates that ControlPlane is **not trying to automate every decision**.

---

# 34. Optional Fifth Demo — Bias Signal

If time permits, demonstrate controlled A/B testing.

### Setup

Two nearly identical synthetic candidate profiles.

Only a controlled protected attribute changes.

Run the decision through the same model.

### Result

If the recommendation changes materially, show:

```text
Potential bias signal detected
Confidence: 0.78
Action: ESCALATE
```

Do not label it “proven discrimination.”

---

# 35. Control Room UI

The main dashboard should feel like an enterprise AI operations console.

## Page 1 — Overview

Top KPI cards:

```text
TOTAL REQUESTS     ALLOWED      REPAIRED
12,482             11,731       481

ESCALATED          BLOCKED      COST SAVED
107                163          ₹38,420
```

## Page 2 — Live Risk Stream

Real-time events:

```text
10:42:31  ✓ Customer AI   ALLOWED
10:42:32  ⚠ Sales AI      REPAIRED
10:42:33  🚨 Finance AI   BLOCKED
10:42:34  🟠 HR AI        ESCALATED
```

## Page 3 — Incident Inspector

Show four columns or cards:

- Original request.
- AI response.
- Evidence/policy findings.
- ControlPlane decision.

Example:

```text
PERFORMANCE      COST             RESPONSIBILITY
HIGH             MEDIUM           HIGH

Contradiction    7.1x baseline    PII detected
Evidence low     7 tool calls     Policy violation
```

Then:

```text
DECISION: BLOCK → REPAIR → ALLOW
```

## Page 4 — Policies

Display:

- Policy name.
- Version.
- Scope.
- Status.
- Rules.

## Page 5 — Human Review

Review queue with severity and action buttons.

---

# 36. UX Requirements

- Risk levels should be visually obvious.
- Do not overload the dashboard with tiny text.
- Clicking an incident must explain the decision.
- Every intervention needs a reason.
- Show evidence before showing score.
- Use plain business language beside technical details.
- Keep the main control room responsive in real time.

---

# 37. Seed Data and Demo Mode

Implement a **Demo Mode** so the judges can reproduce the exact scenarios without depending entirely on live model behavior.

Demo mode should support buttons such as:

```text
[Run Safe Response]
[Run Hallucination Scenario]
[Run PII Scenario]
[Run Cost Anomaly]
[Run Human Escalation]
```

Each demo run should create a real ControlPlane event and update the dashboard.

This is extremely important for hackathon reliability.

### Live LLM mode

Also support a real LLM API for credibility when configured.

Use an environment variable:

```text
LLM_PROVIDER=openai
LLM_MODEL=...
```

But the demo must still work when the live provider is unavailable by falling back to deterministic seeded scenarios.

---

# 38. Configuration

All environment-specific settings must be configurable.

## `.env.example`

```env
APP_ENV=development
BACKEND_PORT=8000
FRONTEND_PORT=3000

DATABASE_URL=postgresql://controlplane:controlplane@postgres:5432/controlplane
REDIS_URL=redis://redis:6379/0

LLM_PROVIDER=openai
LLM_API_KEY=
LLM_MODEL=
EMBEDDING_MODEL=

ENABLE_DEMO_MODE=true
ENABLE_WEBSOCKETS=true
ENABLE_DEEP_CHECKS=true

DEFAULT_LATENCY_BUDGET_MS=700
DEFAULT_EXPECTED_COST_INR=0.20

PII_ENGINE=presidio

LOG_LEVEL=INFO
```

Never commit API keys.

---

# 39. Docker Compose

Recommended local architecture:

```mermaid
flowchart LR
    F[React Frontend] --> B[FastAPI Backend]
    B --> P[(PostgreSQL)]
    P --> V[pgvector]
    B --> R[(Redis)]
    B --> L[LLM API]
```

Suggested services:

```yaml
services:
  frontend:
    ...
  backend:
    ...
  postgres:
    ...
  redis:
    ...
```

Redis may be omitted initially if BackgroundTasks are sufficient.

---

# 40. Security Requirements

Even for a prototype, show the right design principles.

## Must implement or document

- Never store API keys in source code.
- Protect sensitive logs.
- Avoid writing raw PII to console logs.
- Provide a data-retention configuration.
- Use least-privilege database credentials.
- Sanitize user-provided text before rendering in the UI.
- Escape HTML to prevent XSS.
- Validate Pydantic request schemas.
- Record policy versions for auditability.

## Prototype note

Full enterprise IAM, SSO, RBAC, encryption-at-rest architecture, and secret vault integration may be documented as future scope rather than fully implemented.

---

# 41. Responsible AI Guardrails for ControlPlane Itself

ControlPlane is itself an AI-enabled system. Its own mistakes matter.

Therefore:

### Never make irreversible action solely on weak model judgment

Use deterministic hard rules for critical cases and human review for high-impact ambiguity.

### Store evidence for AI-derived decisions

Every deep evaluation should record:

- evaluator version/model.
- evidence used.
- policy version.
- timestamp.
- decision.

### Avoid circular validation

Do not rely solely on the same model family judging its own output.

Use a mixture of:

- deterministic checks.
- trusted data.
- retrieval.
- independent evaluator model where practical.

---

# 42. Prompt Design

Prompt templates should be versioned and stored separately.

## Example evaluator prompt

```text
SYSTEM:
You are a verification component inside an enterprise AI control layer.
You must not assume the AI response is correct.
Use only the supplied evidence when judging factual support.
If evidence is insufficient, return UNVERIFIED rather than inventing support.

USER:
AI RESPONSE:
{{response}}

TRUSTED EVIDENCE:
{{evidence}}

TASK:
1. Identify factual claims.
2. Determine whether each claim is supported, contradicted, or unverified.
3. Return structured JSON.
```

## Example repair prompt

```text
You are repairing an enterprise AI response.
Use only verified evidence.
Do not expose sensitive personal information.
Do not invent missing facts.
If evidence is insufficient, clearly state that limitation.
Return only the revised response.
```

---

# 43. LLM Output Contracts

All evaluator prompts should return structured JSON where supported.

Example:

```json
{
  "claims": [
    {
      "claim": "refund was processed",
      "status": "CONTRADICTED",
      "evidence_ids": ["txn-1001"]
    }
  ],
  "overall": "HIGH_RISK",
  "confidence": 0.93,
  "reason": "Refund status is pending in trusted transaction data."
}
```

The backend must validate the structure before using it.

---

# 44. Error Handling

The system must degrade safely.

## If LLM evaluator fails

- Do not silently allow a high-impact response.
- Fall back to deterministic checks.
- If policy requires deep verification, escalate.

## If database/evidence source fails

- Mark evidence as unavailable.
- Increase uncertainty for high-impact workflows.
- Follow use-case policy.

## If ControlPlane itself is unavailable

The prototype should have a configurable fail-open/fail-closed mode.

Example:

```yaml
customer_support:
  controlplane_failure: fail_open

finance:
  controlplane_failure: fail_closed
```

For safety-critical or high-impact use cases, fail-closed is the safer conceptual default.

---

# 45. Testing Strategy

## 45.1 Unit tests

Test each engine independently.

### Performance

- Correctly identifies contradiction.
- Returns unverified when evidence is absent.
- Handles multiple claims.

### Cost

- Correct token-cost calculation.
- Correct multiplier.
- Detects tool-call anomaly.

### Responsibility

- Detects synthetic email/phone/account patterns.
- Applies policy correctly.
- Redaction works.

### Risk

- Critical PII rule overrides minor cost signal.
- High-impact uncertainty escalates.
- Low-risk response allows.

### Action

- Repair response is re-checked.
- Block prevents original response from being returned.
- Escalation creates incident.

## 45.2 Integration tests

Test:

```text
API -> Fast Screen -> Engines -> Risk -> Action -> DB
```

## 45.3 End-to-end tests

Use Playwright to verify:

- Dashboard loads.
- Demo scenario can be triggered.
- Incident appears.
- Incident details are visible.
- Human review updates the incident.

---

# 46. Acceptance Criteria

The prototype is considered successful when all of the following work end to end.

### Scenario A

A correct low-risk answer is allowed.

### Scenario B

A contradictory/high-risk answer is detected, blocked, repaired, rechecked, and allowed only after validation.

### Scenario C

A PII leakage is detected and redacted or blocked according to policy.

### Scenario D

An inefficient AI execution produces a visible cost anomaly.

### Scenario E

A high-impact uncertain decision is escalated to a human reviewer.

### Dashboard

The UI updates after each scenario.

### Audit

Each intervention creates a persistent incident record.

### Explanation

Every decision has a human-readable reason.

### Latency

Fast-path evaluation is noticeably faster than deep evaluation in the demo and the difference is visible/traceable.

---

# 47. Implementation Sequence

Do not build everything at once.

## Phase 1 — Project skeleton

- Monorepo.
- Docker Compose.
- FastAPI.
- React.
- PostgreSQL.
- Basic health endpoints.

## Phase 2 — Core domain model

- Database schema.
- Pydantic schemas.
- Repository layer.

## Phase 3 — Gateway

- Implement `/gateway/evaluate`.
- Persist request/response/telemetry.
- Return basic decision.

## Phase 4 — Fast Risk Screen

- PII.
- Basic policies.
- High-impact use-case classification.
- Cost signals.

## Phase 5 — Responsibility Engine

- Presidio.
- Regex/rules.
- Redaction.
- Policy evaluator.

## Phase 6 — Cost Engine

- Telemetry calculation.
- Baseline comparison.
- Cost anomaly classification.

## Phase 7 — Performance Engine

- Seed trusted documents/data.
- pgvector retrieval.
- Claim extraction.
- Grounding/contradiction evaluation.
- LLM-as-Judge.

## Phase 8 — Risk + Action Engine

- Risk scoring.
- Policy-based decision matrix.
- Repair.
- Escalate.
- Block.

## Phase 9 — Real-time dashboard

- WebSocket events.
- KPI cards.
- Live feed.
- Incident inspector.

## Phase 10 — Human review

- Queue.
- Review endpoint.
- Audit trail.

## Phase 11 — Demo mode

- Four deterministic scenarios.
- One-click scenario execution.

## Phase 12 — Hardening

- Error handling.
- Tests.
- Seed scripts.
- README setup.
- Demo instructions.

---

# 48. Agentic Coding AI Instructions

The following section is intended to be fed directly to an agentic coding AI.

## 48.1 Role

You are the senior full-stack engineer responsible for implementing the ControlPlane.ai Round 2 prototype according to this README.

## 48.2 Primary objectives

1. Build a working end-to-end prototype.
2. Keep the architecture modular.
3. Make every key decision explainable.
4. Prioritize the four mandatory demo scenarios.
5. Do not over-engineer infrastructure that is not necessary for the demo.
6. Do not make claims that the implementation cannot substantiate.

## 48.3 Development rules

- Use Python 3.x and FastAPI for backend.
- Use React + TypeScript for frontend.
- Use PostgreSQL and pgvector.
- Use Docker Compose for local startup.
- Use Pydantic for validation.
- Use SQLAlchemy or SQLModel for ORM; select one and remain consistent.
- Use Alembic for migrations if ORM is used.
- Use typed interfaces between engines.
- Prefer async FastAPI patterns where appropriate.
- Keep provider-specific LLM code behind a provider interface.
- Keep detection engines independent of UI code.
- Keep policy configuration externalized.
- Add structured logging.
- Add tests for every core engine.

## 48.4 Do not

- Hard-code the final result of every scenario inside the dashboard.
- Build only a fake UI with no real backend logic.
- Build only an LLM chatbot.
- Treat LLM self-confidence as factual truth.
- Claim perfect hallucination or bias detection.
- Put API keys in source code.
- Introduce unnecessary microservices.
- Depend on internet access for core deterministic demo scenarios.

## 48.5 Demo reliability requirement

The product must have **Demo Mode** that works using seeded local data and deterministic simulation even if external LLM APIs are unavailable.

Live LLM integrations should improve realism but must not be a single point of demo failure.

---

# 49. Suggested Monorepo

```text
controlplane-ai/
├── backend/
├── frontend/
├── data/
│   ├── trusted_docs/
│   ├── demo_scenarios/
│   └── seed/
├── infra/
│   ├── docker/
│   └── postgres/
├── docs/
├── scripts/
├── .env.example
├── docker-compose.yml
├── Makefile
└── README.md
```

---

# 50. Local Development Commands

Recommended commands:

```bash
# start infrastructure
 docker compose up -d postgres redis

# backend
 cd backend
 python -m venv .venv
 # activate environment
 pip install -r requirements.txt
 uvicorn app.main:app --reload --port 8000

# frontend
 cd frontend
 npm install
 npm run dev
```

If Docker Compose is configured to start everything:

```bash
docker compose up --build
```

---

# 51. Demo Script for Judges

The demo should tell a story rather than show every API endpoint.

## 0:00–0:20 — Hook

Show a normal AI response:

> “Your ₹25,000 refund was processed yesterday.”

Ask:

> “What if this answer is confidently wrong?”

## 0:20–0:50 — Performance intervention

Show trusted transaction data:

> Refund = PENDING

ControlPlane:

```text
CONTRADICTION DETECTED
Performance Risk: HIGH
Action: BLOCK
```

Then show repaired response.

## 0:50–1:15 — Responsibility

Show PII leak.

ControlPlane detects sensitive information and redacts it.

## 1:15–1:40 — Cost

Show excessive model/tool calls and cost multiplier.

## 1:40–2:05 — Human escalation

Show high-impact financial question with insufficient evidence.

ControlPlane:

```text
UNVERIFIED + HIGH IMPACT
Action: ESCALATE
```

## 2:05–2:30 — Risk-adaptive architecture

Show:

```text
Fast checks first
       |
Low risk -> Allow
Suspicious -> Deep check
       |
Allow / Repair / Escalate / Block
```

## 2:30–2:50 — Business impact

Show control-room KPIs:

- incidents detected before delivery;
- cost anomalies identified;
- unsafe responses prevented;
- human review queue;
- audit trail.

## Closing line

> **“ControlPlane does not replace AI. It gives enterprises a control layer that helps them use AI safely, efficiently, and responsibly at scale.”**

---

# 52. Presentation Messaging

The prototype should reinforce five concepts consistently:

### Detect
Find risk in real time.

### Decide
Understand severity, context, and policy.

### Intervene
Allow, repair, escalate, or block.

### Explain
Show evidence and reasoning for the intervention.

### Learn
Use human feedback and incident data to improve thresholds/policies.

Suggested product statement:

> **Detect AI risk before it becomes a business incident.**

Suggested three-part framework:

> **Observe → Evaluate → Control**

Alternative:

> **Detect → Decide → Intervene**

---

# 53. Business Impact Model

The prototype should connect technical signals to enterprise outcomes.

## Risk reduction

- Fewer unsafe outputs reaching users.
- Reduced PII leakage risk.
- Reduced unsupported recommendations.

## Cost reduction

- Fewer unnecessary LLM calls.
- Reduced agent loops.
- Better model routing.
- Reduced human rework.

## Productivity

- Faster incident investigation.
- Automated first-line review.
- Centralized policy enforcement.

## Governance

- Audit trail.
- Policy versioning.
- Human review.
- Cross-application visibility.

Do not invent real-world ROI claims. Use clearly labeled prototype estimates if demonstrating savings.

---

# 54. Example Business Metric Formulas

## Cost saved

```text
estimated_cost_saved = baseline_expected_cost - actual_optimized_cost
```

Aggregate over requests.

## Cost multiplier

```text
cost_multiplier = actual_cost / expected_cost
```

## Allow rate

```text
allow_rate = allowed / total_requests
```

## Intervention rate

```text
intervention_rate = (repaired + escalated + blocked) / total_requests
```

## Human override rate

```text
override_rate = human_overrides / reviewed_incidents
```

---

# 55. Example ControlPlane Decision JSON

Use a consistent structure for all engines.

```json
{
  "request_id": "req-001",
  "response_id": "resp-001",
  "timestamp": "2026-08-29T12:00:00Z",
  "context": {
    "application": "customer-support",
    "use_case": "customer_support",
    "geography": "IN",
    "business_impact": "medium"
  },
  "risk": {
    "performance": {
      "score": 0.88,
      "level": "HIGH"
    },
    "cost": {
      "score": 0.72,
      "level": "HIGH"
    },
    "responsibility": {
      "score": 0.91,
      "level": "CRITICAL"
    },
    "overall": {
      "score": 0.95,
      "level": "CRITICAL"
    }
  },
  "signals": [
    {
      "type": "contradiction",
      "severity": "high",
      "confidence": 0.94
    },
    {
      "type": "pii",
      "severity": "high",
      "confidence": 0.98
    }
  ],
  "decision": {
    "action": "BLOCK",
    "reason": "High-confidence contradiction and PII violation",
    "requires_human": false,
    "repair_attempted": true,
    "recheck_passed": true
  }
}
```

---

# 56. What Makes This Prototype Different

The prototype should demonstrate that ControlPlane is not just a response-scoring dashboard.

### Differentiator 1 — Multi-dimensional evaluation

Performance + cost + responsibility.

### Differentiator 2 — Context-sensitive governance

Different applications have different risk tolerance.

### Differentiator 3 — Risk-adaptive evaluation

Cheap/fast checks first; expensive checks only when warranted.

### Differentiator 4 — Active intervention

The system can repair, block, or escalate rather than only report.

### Differentiator 5 — Evidence-backed decisions

Explain why an intervention happened.

### Differentiator 6 — Agent-aware telemetry

Evaluate not just the final text but the execution path.

### Differentiator 7 — Feedback loop

Human decisions are captured and can improve thresholds/policies.

---

# 57. Common Failure Modes to Avoid

## Failure 1 — “It is just another chatbot.”

Fix: emphasize the control layer and intervention workflow.

## Failure 2 — “We use one LLM to check another.”

Fix: combine deterministic checks, trusted evidence, retrieval, telemetry, and LLM evaluation.

## Failure 3 — “Our score says the answer is 95% accurate.”

Fix: use evidence-backed trust/risk signals and make uncertainty explicit.

## Failure 4 — “We detect bias perfectly.”

Fix: call it a bias signal and route ambiguous cases to human review.

## Failure 5 — “We check everything deeply.”

Fix: implement risk-adaptive evaluation.

## Failure 6 — “All use cases use the same policy.”

Fix: configure policy by use case/risk/context.

## Failure 7 — “Everything is always blocked when anything is suspicious.”

Fix: use tiered actions and business impact.

## Failure 8 — “The demo depends entirely on live APIs.”

Fix: deterministic Demo Mode.

## Failure 9 — “We built a beautiful dashboard but no real logic.”

Fix: every demo interaction must execute the actual backend decision pipeline.

## Failure 10 — “We claim production readiness.”

Fix: describe this honestly as a prototype demonstrating a production-oriented architecture.

---

# 58. Future Production Extensions

These are explicitly future scope, not core hackathon requirements.

- Multi-model routing.
- Enterprise SSO/RBAC.
- Cloud-native distributed deployment.
- Full OpenTelemetry backend.
- Kafka/event streaming.
- Data-loss prevention integration.
- External compliance policy packs.
- Geography-aware data residency.
- Large-scale model evaluation pipelines.
- Continuous threshold optimization.
- Advanced causal/bias analysis.
- Model-specific deep inspection where available.
- Fine-grained tool/action authorization.
- Cryptographic audit logging.

---

# 59. Definition of Done

The project is ready for the final Round 2 demonstration when:

- [ ] `docker compose up --build` starts the prototype.
- [ ] The frontend loads.
- [ ] The backend health endpoint passes.
- [ ] PostgreSQL initializes.
- [ ] Demo data seeds successfully.
- [ ] At least one live LLM provider can be configured.
- [ ] Demo Mode works without external AI dependencies.
- [ ] Safe response -> ALLOW works.
- [ ] Hallucination/contradiction -> BLOCK/REPAIR works.
- [ ] PII -> REDACT/REPAIR/BLOCK works.
- [ ] Cost anomaly -> visible risk works.
- [ ] High-impact uncertainty -> ESCALATE works.
- [ ] Human review updates an incident.
- [ ] WebSocket/live dashboard updates work.
- [ ] Audit trail is persisted.
- [ ] Policy versions are stored.
- [ ] Tests pass.
- [ ] No secrets are committed.
- [ ] The 2–3 minute demo can be run deterministically.

---

# 60. Final Build Philosophy

The winning prototype is not the one with the most technologies.

It is the one that makes the following flow obvious, real, and reliable:

```text
            AI generates something
                    |
                    v
             CONTROLPLANE
                    |
          +---------+---------+
          |         |         |
          v         v         v
      PERFORMANCE  COST  RESPONSIBILITY
          |         |         |
          +---------+---------+
                    |
                    v
              CONTEXT + POLICY
                    |
                    v
               RISK ENGINE
                    |
                    v
        +-----------+-----------+
        |           |           |
        v           v           v
      ALLOW       REPAIR     ESCALATE
                                |
                              HUMAN
                                |
                              /   \
                           APPROVE REJECT
                                |
                                v
                              BLOCK
```

The core product promise is:

> **AI should not be trusted simply because it produced an answer. AI should earn the right to act through evidence, context, policy, and risk-aware control.**

That is the core idea this prototype must make visible.

---

# Appendix A — Minimal API/Module Milestone Checklist

## Milestone 1

`POST /api/v1/gateway/evaluate` returns `ALLOW` for a clean response.

## Milestone 2

PII detection works.

## Milestone 3

Cost telemetry and anomaly calculation work.

## Milestone 4

Trusted evidence retrieval and contradiction detection work.

## Milestone 5

Risk engine combines all signals.

## Milestone 6

Action engine supports all four actions.

## Milestone 7

Incident persistence works.

## Milestone 8

Human review works.

## Milestone 9

WebSocket dashboard works.

## Milestone 10

All four demo scenarios work end-to-end.

---

# Appendix B — Suggested Initial Seed Policy Set

## Policy: Customer Support

```yaml
id: customer-support-default
rules:
  pii_exposure: redact
  critical_pii_exposure: block
  contradicted_transaction_claim: repair
  unresolved_high_impact_claim: escalate
  severe_safety_violation: block
  moderate_uncertainty: repair
```

## Policy: Finance Decision Support

```yaml
id: finance-high-impact
rules:
  pii_exposure: block
  unsupported_financial_claim: escalate
  investment_recommendation: escalate
  severe_safety_violation: block
```

## Policy: Internal Knowledge Assistant

```yaml
id: internal-knowledge
rules:
  confidential_data_exposure: block
  unverified_low_impact_claim: repair
  critical_internal_policy_conflict: escalate
```

---

# Appendix C — Suggested Seed Application Profiles

```yaml
applications:
  - id: customer-support
    use_case: customer_support
    risk_level: medium
    latency_budget_ms: 700

  - id: internal-knowledge
    use_case: internal_knowledge
    risk_level: medium
    latency_budget_ms: 1200

  - id: finance-assistant
    use_case: financial_decision_support
    risk_level: high
    latency_budget_ms: 1800
```

---

# Appendix D — Implementation Priorities by Value

| Priority | Feature | Reason |
|---|---|---|
| P0 | Gateway | Core architecture |
| P0 | Risk engines | Core PS requirements |
| P0 | Risk/action decisioning | Differentiating behavior |
| P0 | Four demo scenarios | Judge-facing proof |
| P0 | Incident/audit trail | Enterprise credibility |
| P0 | Dashboard | Visibility and demo |
| P1 | WebSockets | Real-time experience |
| P1 | pgvector/RAG | Evidence-based verification |
| P1 | Human review queue | Responsible AI workflow |
| P1 | Policy versioning | Enterprise governance |
| P1 | OpenTelemetry | Agent/cost observability |
| P2 | Advanced bias analysis | Useful but harder |
| P2 | Redis queue | Optimization, not core |
| P2 | Full multi-model routing | Future scope |
| P3 | Production IAM/Kubernetes/etc. | Not needed for hackathon |

---

# Appendix E — Recommended First Coding Task

Start by implementing only this vertical slice:

```text
Demo Scenario: Refund Hallucination

1. Seed customer transaction data.
2. Create a mock/LLM customer-support response.
3. Submit it to ControlPlane.
4. Run fast checks.
5. Retrieve trusted transaction evidence.
6. Detect contradiction.
7. Mark performance risk HIGH.
8. Apply policy.
9. BLOCK the original response.
10. Generate a repaired response.
11. Re-check the repaired response.
12. Return final response.
13. Store incident.
14. Push WebSocket event.
15. Display incident in dashboard.
```

Do not build the entire platform before this vertical slice works.

Once this path works reliably, replicate the framework for PII, cost, and escalation scenarios.

---

# Final Note

This README intentionally separates:

- **What the hackathon problem requires**
- **What the prototype should actually implement**
- **What is simulated for demonstration**
- **What should be presented as future production capability**

The implementation should preserve that distinction. A convincing prototype is one that **works end to end, explains its decisions, handles uncertainty honestly, and demonstrates why a real enterprise would place a ControlPlane around its AI systems.**
