# ControlPlane.ai — User Guide & Walkthrough

Welcome to **ControlPlane.ai**! This guide will explain exactly what the system does, how to interact with the dashboard, and what you should expect to see when you run the demo scenarios.

---

## 1. What is ControlPlane.ai?

Imagine you have an AI chatbot for customer support. Sometimes, LLMs (Large Language Models) make mistakes:
- They **hallucinate** facts (e.g., telling a user their refund is processed when it isn't).
- They **leak sensitive data** (e.g., showing another customer's PAN card or phone number).
- They **waste money** (e.g., getting stuck in a loop of expensive tool calls).

**ControlPlane.ai sits between your AI model and your end users.** 
Every time your AI generates a response, it is sent to ControlPlane.ai *first*. In under 50 milliseconds, ControlPlane evaluates the response across three dimensions: **Performance**, **Cost**, and **Responsibility**. 

If the response is safe, it is **ALLOWED**. If it contains risks, ControlPlane can automatically **REPAIR** it (e.g., redact the PII) or completely **BLOCK** it, creating an Incident for a human to review.

---

## 2. The Control Room (Dashboard)

When you open `http://localhost:3000`, you are looking at the **Control Room**.

### Why are the numbers static initially?
When you first boot up the project, you have a clean slate. The summary metrics (Total Requests, Cost Saved, Risk Rates) reflect a blank database. They will only change as traffic flows through the system.

### The Live Event Stream
Somewhere on your dashboard, you will see a **Live Event Stream** or "Live Tile". This is connected via WebSockets. Every time a request passes through the system, it will pop up here in real-time, showing you the decision made (`ALLOW`, `REPAIR`, `BLOCK`, `ESCALATE`).

---

## 3. How to Run the Demo Scenarios

Since you don't have a real AI chatbot hooked up to this right now, we built a **Demo Panel** into the UI. This panel simulates an AI sending a response to ControlPlane.ai.

When you click one of the demo buttons, watch the **Live Event Stream** and your **Dashboard Metrics** update instantly!

Here is what happens behind the scenes for each scenario:

### 🟢 Scenario 1: Safe Request
- **What happens:** The AI gives a standard, helpful answer that doesn't violate any policies.
- **The Result:** ControlPlane evaluates it, finds no PII, no contradictions, and normal cost. It marks the request as **ALLOWED** (or repaired if it lacked verifiable evidence but was safe).

### 🧠 Scenario 2: Hallucination
- **What happens:** A customer asks about their refund. The AI confidently replies: *"Your refund of ₹5000 has been successfully processed!"*
- **The Catch:** ControlPlane secretly checks your trusted database (the seed data) and sees that the `refund_status` is actually `PENDING`.
- **The Result:** The Performance Engine catches the contradiction. It assigns a High/Critical risk score and triggers a **REPAIR** or **BLOCK**, preventing the user from receiving false information.

### 🔒 Scenario 3: PII Leakage
- **What happens:** The AI accidentally includes a PAN card number and a personal phone number in the response.
- **The Result:** The FastScreen and Responsibility Engines immediately detect the sensitive strings using regex and NLP. The system applies a **BLOCK** (or redacts the text to **REPAIR** it, depending on the policy severity).

### 💸 Scenario 4: Cost Anomaly
- **What happens:** The AI got confused and made 9 internal tool calls and 3 retries before answering, burning a lot of expensive tokens.
- **The Result:** The Cost Engine compares the estimated INR cost against the expected baseline. Realizing it is 7x more expensive than normal, it flags the request. 

### 🚨 Scenario 5: Escalation (High Impact)
- **What happens:** The user asks for financial advice or a critical account change, and the AI gives an unverified response.
- **The Result:** Because the "business impact" context is marked as Critical, the Risk Engine refuses to let the AI handle it autonomously and marks it as **ESCALATE / BLOCK**.

---

## 4. Investigating Incidents

When a request is Blocked or Escalated, it becomes an **Incident**.

1. Navigate to the **Incidents** tab in the sidebar.
2. You will see a list of all the risky requests that were stopped.
3. Click on one to view the **Incident Details**.
4. Here you can see exactly *why* it was blocked. You'll see the AI's original text, the specific rules it broke, and the "Evidence" (e.g., the actual database row that proved the AI was hallucinating).
5. As an admin, you can use the **Review Queue** to manually *Approve*, *Reject*, or *Override* these incidents.

---

## Summary of your Workflow

To get a feel for the product:
1. Stay on the **Dashboard**.
2. Click the **Hallucination** demo button.
3. Watch the Live Stream tile update. Watch the "Intervention Rate" metric go up.
4. Go to the **Incidents** tab.
5. Find the Hallucination incident, click it, and read the reasoning to see how ControlPlane caught the AI in a lie.
