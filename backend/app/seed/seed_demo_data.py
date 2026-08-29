from __future__ import annotations

"""
Seed script: loads demo applications, policies, and trusted document evidence.
Runs at startup if tables are empty.
Safe to re-run (idempotent).
"""

import asyncio
import logging
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import get_settings
from app.db.session import AsyncSessionLocal
from app.db.models import Application, Policy, PolicyVersion, TrustedDocument, RetrievalChunk
from app.retrieval.retriever import add_mock_chunks

settings = get_settings()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Trusted document content for evidence retrieval
# ---------------------------------------------------------------------------

TRUSTED_DOCS = [
    {
        "name": "Refund Policy",
        "source_type": "policy",
        "content": """
REFUND POLICY v2.1 — Effective August 2026

1. Refund Eligibility: Products must be returned within 30 days of delivery.
2. Processing Time: Refunds are processed within 5-7 business days after return approval.
3. Status Definitions:
   - PENDING: Refund request received, under review or return not yet received.
   - PROCESSING: Return received, refund being initiated.
   - COMPLETED: Refund successfully credited to original payment method.
   - REJECTED: Refund request declined due to policy violation.
4. Credit Card refunds: 5-7 business days after processing.
5. Bank transfers: 3-5 business days after processing.
6. Customer Service must verify refund status using the order management system before communicating status to customer.
7. NEVER confirm a refund has been processed unless refund_status = COMPLETED in the system.
        """,
    },
    {
        "name": "Privacy and Data Handling Policy",
        "source_type": "policy",
        "content": """
PRIVACY POLICY v3.0 — Data Handling for Customer Service

1. Customer PII (Personally Identifiable Information) must NEVER be included in AI-generated responses.
2. Prohibited data types in responses: full account numbers, PAN numbers, Aadhaar numbers, 
   complete mobile numbers, email addresses, bank account details.
3. When referencing accounts: use last 4 digits only (e.g., "account ending in XXXX").
4. AI systems must not retrieve or display full financial account details.
5. Any response containing customer PII must be intercepted and redacted before delivery.
6. Violations of this policy trigger an immediate BLOCK action and incident creation.
        """,
    },
    {
        "name": "Financial Decision Policy",
        "source_type": "policy",
        "content": """
FINANCIAL RECOMMENDATIONS POLICY

1. AI systems are PROHIBITED from providing specific investment advice or recommendations.
2. Retirement savings, investment products, and high-value financial decisions require 
   qualified human financial advisors.
3. AI can provide general information about products but must not recommend specific 
   financial actions involving customer savings or investments.
4. Any response recommending investment of retirement funds or savings into specific 
   financial products must be ESCALATED for human review.
5. Unverified projected returns or financial predictions are not acceptable.
6. Risk warning: All investment decisions must include appropriate risk disclosures 
   reviewed by certified financial professionals.
        """,
    },
    {
        "name": "Customer Communication Standards",
        "source_type": "policy",
        "content": """
CUSTOMER COMMUNICATION STANDARDS

1. All factual claims about order status, refund status, and delivery dates must be 
   verified against the order management system before communicating to customers.
2. If status is uncertain or system data conflicts with expected outcome, 
   do NOT confirm a specific status — use: "Your [item] is currently being processed."
3. For refund inquiries where refund_status = PENDING:
   Use: "Your refund is currently being processed. We'll notify you once it has been completed."
   Do NOT say: "Your refund was processed" or "Your refund has been sent."
4. Response must be accurate, clear, and empathetic.
5. Do not speculate about timelines unless system data confirms them.
        """,
    },
    {
        "name": "Order Status Reference",
        "source_type": "database",
        "content": """
ORDER STATUS DEFINITIONS:
- Processing: Order confirmed, preparing for shipment.
- Shipped: Order dispatched, in transit.
- Delivered: Order received by customer.
- Cancelled: Order cancelled, refund initiated if paid.

SAMPLE ORDER DATA (for verification):
ORD1001: Status=Delivered, RefundStatus=PENDING, RefundAmount=₹25,000
ORD1002: Status=Shipped, RefundStatus=None, ExpectedDelivery=2026-08-30
ORD1003: Status=Delivered, RefundStatus=COMPLETED, RefundAmount=₹3,200
ORD1004: Status=Processing, RefundStatus=None
ORD1005: Status=Cancelled, RefundStatus=PENDING, RefundAmount=₹8,500
        """,
    },
]

# Chunked for retrieval
def _chunk_content(doc_name: str, content: str, source_type: str) -> list[dict]:
    """Split document into retrieval chunks."""
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    chunks = []
    for i, para in enumerate(paragraphs):
        if len(para) > 50:  # Skip very short paragraphs
            chunks.append({
                "source": doc_name,
                "content": para,
                "source_type": source_type,
                "chunk_index": i,
                "score": 0.0,
            })
    return chunks

_SEED_APPLICATIONS = [
    {
        "id": "customer-support",
        "name": "Customer Support AI",
        "use_case": "customer_support",
        "risk_level": "medium",
        "geography": "IN",
        "latency_budget_ms": 700,
        "expected_cost_inr": 0.20,
        "max_tool_calls": 5,
        "max_retries": 2,
    },
    {
        "id": "finance-assistant",
        "name": "Finance Decision Assistant",
        "use_case": "financial_decision_support",
        "risk_level": "high",
        "geography": "IN",
        "latency_budget_ms": 1800,
        "expected_cost_inr": 0.50,
        "max_tool_calls": 8,
        "max_retries": 2,
    },
    {
        "id": "internal-knowledge",
        "name": "Internal Knowledge Assistant",
        "use_case": "internal_knowledge",
        "risk_level": "medium",
        "geography": "IN",
        "latency_budget_ms": 1200,
        "expected_cost_inr": 0.15,
        "max_tool_calls": 5,
        "max_retries": 2,
    },
]

_SEED_POLICIES = [
    {
        "id": "pol-customer-support",
        "name": "Customer Support Policy",
        "description": "Policy for customer-facing AI support interactions",
        "use_case": "customer_support",
        "geography": "IN",
        "version": 1,
        "config": {
            "risk_level": "medium",
            "expected_cost_inr": 0.20,
            "latency_budget_ms": 700,
            "max_tool_calls": 5,
            "max_retries": 2,
            "rules": {
                "pii_exposure": "redact",
                "critical_pii_exposure": "block",
                "contradicted_transaction_claim": "repair",
                "unresolved_high_impact_claim": "escalate",
                "severe_safety_violation": "block",
                "moderate_uncertainty": "repair",
            },
        },
    },
    {
        "id": "pol-finance",
        "name": "Finance High-Impact Policy",
        "description": "Strict policy for financial decision support AI",
        "use_case": "financial_decision_support",
        "geography": "IN",
        "version": 1,
        "config": {
            "risk_level": "high",
            "expected_cost_inr": 0.50,
            "latency_budget_ms": 1800,
            "max_tool_calls": 8,
            "max_retries": 2,
            "rules": {
                "pii_exposure": "block",
                "critical_pii_exposure": "block",
                "unsupported_financial_claim": "escalate",
                "investment_recommendation": "escalate",
                "severe_safety_violation": "block",
            },
        },
    },
    {
        "id": "pol-internal",
        "name": "Internal Knowledge Policy",
        "description": "Policy for internal AI knowledge assistants",
        "use_case": "internal_knowledge",
        "geography": "IN",
        "version": 1,
        "config": {
            "risk_level": "medium",
            "expected_cost_inr": 0.15,
            "latency_budget_ms": 1200,
            "max_tool_calls": 5,
            "max_retries": 2,
            "rules": {
                "confidential_data_exposure": "block",
                "unverified_low_impact_claim": "repair",
                "critical_internal_policy_conflict": "escalate",
            },
        },
    },
]


async def seed_in_memory_evidence():
    """Load document evidence into in-memory retrieval store."""
    all_chunks = []
    for doc in TRUSTED_DOCS:
        chunks = _chunk_content(doc["name"], doc["content"], doc["source_type"])
        all_chunks.extend(chunks)
    add_mock_chunks(all_chunks)
    logger.info(f"Loaded {len(all_chunks)} evidence chunks into memory")


async def seed_demo_data(db: AsyncSession):
    """Seed applications, policies, and trusted documents into DB."""
    # Check if already seeded
    existing = (await db.execute(select(Application).limit(1))).scalar_one_or_none()
    if existing:
        logger.info("Demo data already seeded, skipping")
        return

    logger.info("Seeding demo data...")

    # Applications
    for app_data in _SEED_APPLICATIONS:
        app = Application(**app_data)
        db.add(app)

    # Policies
    for pol_data in _SEED_POLICIES:
        pol = Policy(
            id=pol_data["id"],
            name=pol_data["name"],
            description=pol_data["description"],
            use_case=pol_data["use_case"],
            geography=pol_data["geography"],
        )
        db.add(pol)

        pv = PolicyVersion(
            policy_id=pol_data["id"],
            version=pol_data["version"],
            config=pol_data["config"],
            status="active",
        )
        db.add(pv)

    # Trusted documents and chunks
    for doc_data in TRUSTED_DOCS:
        doc = TrustedDocument(
            name=doc_data["name"],
            source_type=doc_data["source_type"],
            source_uri=f"internal://{doc_data['name'].lower().replace(' ', '_')}",
            trust_level="high",
            content=doc_data["content"],
        )
        db.add(doc)
        await db.flush()  # Get doc.id

        chunks = _chunk_content(doc_data["name"], doc_data["content"], doc_data["source_type"])
        for chunk in chunks:
            rc = RetrievalChunk(
                document_id=doc.id,
                content=chunk["content"],
                embedding_json=None,
                metadata={"source": doc_data["name"], "source_type": doc_data["source_type"]},
                chunk_index=chunk["chunk_index"],
            )
            db.add(rc)

    await db.commit()
    logger.info("Demo data seeded successfully")


async def main():
    """Run seed as a standalone script."""
    async with AsyncSessionLocal() as db:
        await seed_demo_data(db)
        await seed_in_memory_evidence()


if __name__ == "__main__":
    asyncio.run(main())
