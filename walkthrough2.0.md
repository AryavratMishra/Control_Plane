# ControlPlane.ai — Walkthrough 2.0

> This is the definitive guide to using the ControlPlane.ai Control Room. It reflects the actual working behavior of the system after all bugs have been fixed.

---

## 🏗️ System Architecture (Plain English)

**ControlPlane.ai is AI middleware.** Every time an AI generates a response, that response is sent through ControlPlane before reaching the user. In under 50ms, ControlPlane runs a 3-engine evaluation:

| Engine | What It Checks |
|---|---|
| **Performance Engine** | Is the AI's answer actually true? Does it contradict trusted data? |
| **Cost Engine** | Did the AI use an abnormal number of tokens, retries, or tool calls? |
| **Responsibility Engine** | Does the response contain PII (personal data), unsafe content, or violate enterprise policy? |

After evaluation, the **Risk Engine** combines all signals and picks one of 4 actions:

| Action | Meaning |
|---|---|
| ALLOW | Response is safe. Send it to the user. |
| REPAIR | Response has issues but can be automatically fixed (e.g., PII redacted, fallback text). |
| ESCALATE | Too uncertain or high-impact for automation - send to human review queue. |
| BLOCK | Response must not reach the user. A safe fallback is returned instead. |

---

## The Control Room — Page by Page

### Page 1: Overview (Dashboard)

This is your real-time operations view at http://localhost:3000.

**Top KPI Cards:**
- **Total Requests** — Total number of AI responses evaluated by ControlPlane.
- **Allowed** — Responses that passed all checks cleanly.
- **Repaired** — Responses that were intercepted and automatically fixed before delivery.
- **Escalated** — Responses sent to the human review queue.
- **Blocked** — Responses that were completely stopped.

Note: When you first start, all values are 0. They only change when you run demo scenarios or send real traffic.

**Cost Saved card:** Estimates cost savings from intercepting expensive agent loops. In INR.

**Avg. Evaluation Time:** Shows how fast ControlPlane runs. Fast path is typically under 20ms. Deep evaluation (with contradiction detection) can take up to a few hundred ms.

**Risk Trend Chart:** Shows blocked and repaired counts per hour over the last 24 hours. Will fill in as you run scenarios.

**Action Breakdown (Pie chart):** Shows proportion of each action taken.

**Live Event Stream:** A real-time feed of every evaluation, fed via WebSocket. When you click a demo button, a new event appears here immediately.

**Demo Panel (bottom right):** Your controls for triggering the 5 test scenarios.

---

### Page 2: Incidents — /incidents

All flagged AI responses live here. Each incident card shows:
- Incident type (hallucination, pii_leakage, cost_anomaly, escalation, policy_violation)
- Severity (LOW / MEDIUM / HIGH / CRITICAL)
- Action taken (REPAIR / BLOCK / ESCALATE)
- Status (open = needs review | resolved = auto-handled)
- The user's original question
- When it happened

**Filters at the top:**
- Filter by Status: All | Open | Under Review | Resolved
- Filter by Type: All Types | Hallucination | PII Leakage | Cost Anomaly | Escalation
- Click Refresh to manually reload

Click on any row to open the **Incident Detail** page.

---

### Page 3: Incident Detail — /incidents/:id

This is the forensic view. It has 4 sections:

**Risk Score Cards (top):**
Three cards showing Performance, Cost, and Responsibility scores from 0.0 to 1.0 with color-coded risk levels.

**Forensic Grid (2x2):**

| Panel | Content |
|---|---|
| **User Request** | The original question the user asked |
| **Original AI Response** | What the AI generated (marked "Not Delivered" if intercepted) |
| **Evidence & Findings** | The reasons ControlPlane flagged it, PII entities found, evidence source chunks |
| **ControlPlane Decision** | The final action taken, and the repaired response if REPAIR was applied |

**Human Review Panel (bottom):**
Appears only on ESCALATE incidents with status "open". You can:
- Add a comment explaining your decision
- Click **Approve & Allow** — you're satisfied, let this response through
- Click **Reject & Block** — you agree it should be blocked
- Click **Override & Repair** — you want it modified and sent

After you take action, the incident status changes to "resolved" and disappears from the review queue.

**Review History:**
Shows all previous decisions and comments on this incident.

---

### Page 4: Review Queue — /review

**This is the human-in-the-loop page.** Only ESCALATE incidents with status "open" appear here.

Each card shows:
- The ESCALATE badge and severity
- The user's original request
- The reason ControlPlane escalated it
- The application that generated it

Three action buttons:
- **View Details** — Goes to the full Incident Detail page (recommended before taking action)
- **Approve** — Quick-approve from the list
- **Reject** — Quick-reject from the list

When the queue is empty, you see "Queue is clear" — this means all escalated incidents have been reviewed.

---

### Page 5: Policies — /policies

This page shows the data-driven governance rules that control ControlPlane's behavior.

Each policy is associated with a **use case** (e.g., customer_support, financial_decision_support) and **geography** (e.g., IN).

Click on any policy to expand it and see its **Rules** — key-value pairs that map events to actions:

| Rule | Example Action |
|---|---|
| pii_exposure | REDACT |
| critical_pii_exposure | BLOCK |
| investment_recommendation | ESCALATE |
| contradicted_transaction_claim | REPAIR |
| safety_violation | BLOCK |
| excessive_cost_multiplier | REPAIR |

These rules are what ControlPlane evaluates during the Responsibility Engine and Risk Engine phases. Different use cases have different thresholds.

---

## The 5 Demo Scenarios — Detailed

### Scenario 1: Safe Response

**Click:** "Safe Response" button in the Demo Panel

**What it simulates:** A customer asks "What are your support hours?"
**AI says:** "Monday to Saturday, 9 AM to 6 PM IST. Reach us at support@example.com."

**What happens:**
- FastScreen runs (PII check, safety check, cost check) — all low risk
- Risk Engine: LOW/MEDIUM overall score
- Dashboard: +1 to "Allowed" or "Repaired"

Note: The system may show REPAIR even for "safe" responses when it detects an email in the response. This is intentional conservative behavior — ControlPlane errs on the side of caution.

---

### Scenario 2: Hallucination (Contradiction Detection)

**Click:** "Hallucination" button

**What it simulates:** A customer asks "Where is my 25,000 rupee refund?"
**AI says:** "Your refund was successfully processed yesterday..."

**The catch:** The trusted database record shows `refund_status = PENDING`

**What happens:**
- FastScreen: high-impact context detected, sends to Deep Evaluation
- Performance Engine: **CONTRADICTION DETECTED** — AI says "processed" but data says "PENDING"
- Risk Engine: HIGH performance risk → **REPAIR** action
- Repaired response: "I'm unable to provide a fully verified answer right now. Please contact our support team."
- Dashboard: +1 to "Repaired"

**Check in Incidents:** Find this incident, open it. Under "Evidence & Findings" you'll see: "AI claims refund was processed/completed, but trusted data shows refund_status=PENDING"

---

### Scenario 3: PII Leakage

**Click:** "PII Leakage" button

**What it simulates:** Customer asks "What is my account info?"
**AI says:** "Your account ending 4821 is linked to mobile 9876543210. PAN: ABCDE1234F."

**What happens:**
- FastScreen: PAN card and phone number patterns detected
- Responsibility Engine: CRITICAL PII detected (PAN = financial identity document)
- Risk Engine: hard_rule_triggered → **BLOCK**
- Dashboard: +1 to "Blocked"

**Check in Incidents:** Find this incident. Under "Evidence & Findings" you'll see PII entity tags: PAN_CARD, PHONE_NUMBER, EMAIL_ADDRESS

---

### Scenario 4: Cost Anomaly (Agent Loop)

**Click:** "Cost Anomaly" button

**What it simulates:** The AI answered correctly but it took:
- 7 LLM calls, 9 tool calls, 3 retries, 8.2 seconds, Rs. 1.42 cost

**Normal baseline for this use case:** ~Rs. 0.20

**What happens:**
- Cost Engine: 7.1x cost multiplier → HIGH cost risk
- Performance Engine: the actual answer is correct (matches trusted data)
- Risk Engine: cost anomaly, answer correct, repairable → **REPAIR**
- Response kept (it was correct) but incident logged
- Dashboard: +1 to "Repaired"

Note: The answer was correct so ControlPlane keeps it but logs a cost anomaly incident for the operations team.

---

### Scenario 5: Human Escalation (Financial Advice)

**Click:** "Human Escalation" button

**What it simulates:** User asks "Should I move my Rs.15 lakh retirement savings into this product?"
**AI says:** "Based on market trends, this appears to be a sound decision with 18% projected annual returns."

**What happens:**
- FastScreen: business_impact = critical, sends to Deep Evaluation
- Performance Engine: No trusted evidence for this financial claim → UNVERIFIED risk level
- Responsibility Engine: Policy rule `investment_recommendation = escalate` fires
- Risk Engine: requires_human = True → **ESCALATE**
- Incident created with status "open" (pending human review)
- Dashboard: +1 to "Escalated"
- **Review Queue gets a new item!**

**Go to Review Queue:** You should see this incident. Click "View Details" to see the full forensic analysis, then take an action.

---

## The Human Review Workflow (End-to-End)

1. AI gives an uncertain or high-stakes response → ControlPlane **ESCALATEs** it
2. The incident appears in the **Review Queue** with status `open`
3. Click **"View Details"** to read the full forensic breakdown
4. You read:
   - What the user asked
   - What the AI said (which was NOT delivered to the user)
   - Why ControlPlane wasn't sure (reasons and evidence)
5. Make a decision:
   - **Approve** — The AI response was actually fine, allow it
   - **Reject** — It was genuinely risky, keep it blocked
   - **Override & Repair** — Modify it and send a safe version
6. The incident status changes to `resolved` and it leaves the queue
7. The **Review History** section on the incident page shows your decision

---

## Running Scenarios Multiple Times

All 5 scenarios can be run **repeatedly** without any errors. Each run creates a new evaluation record. Watch the KPI numbers accumulate on the dashboard. This simulates ongoing AI traffic being continuously monitored.

---

## System Health & API Access

| What to Check | Where |
|---|---|
| Backend health | http://localhost:8000/health |
| Interactive API docs | http://localhost:8000/docs |
| All incidents (JSON) | http://localhost:8000/api/v1/incidents |
| Dashboard summary (JSON) | http://localhost:8000/api/v1/dashboard/summary |
| Open review queue (JSON) | http://localhost:8000/api/v1/incidents?status=open |

---

## Sending Custom Evaluations via API

You can evaluate any real AI response without using the demo panel:

```
POST http://localhost:8000/api/v1/gateway/evaluate

{
  "application_id": "my-app",
  "conversation_id": "session-001",
  "request": { "text": "Customer question here" },
  "response": { "text": "AI response here" },
  "context": {
    "country": "IN",
    "use_case": "customer_support",
    "business_impact": "high",
    "trusted_data": {
      "order_status": "Shipped",
      "refund_status": "PENDING"
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

The response will include:
- `decision` — ALLOW / REPAIR / BLOCK / ESCALATE
- `final_response` — The text to actually show the user
- `risk.performance` / `risk.cost` / `risk.responsibility` — Dimension scores (0.0 to 1.0)
- `reasons` — Why ControlPlane made this decision
- `incident_id` — ID of the created incident (if action != ALLOW)
- `pii_entities` — List of detected PII types
