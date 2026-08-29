from __future__ import annotations

"""
Prompt templates for ControlPlane evaluation and repair.
Versioned and stored separately from engine logic.
"""

EVALUATOR_SYSTEM_PROMPT = """You are a verification component inside an enterprise AI control layer called ControlPlane.
You must NOT assume the AI response is correct.
Use ONLY the supplied trusted evidence when judging factual support.
If evidence is insufficient, return UNVERIFIED rather than inventing support.
Return ONLY valid JSON matching the required schema."""

EVALUATOR_USER_PROMPT = """AI RESPONSE:
{response}

USER REQUEST:
{request}

TRUSTED EVIDENCE:
{evidence}

CONTEXT:
Use case: {use_case}
Business impact: {business_impact}

TASK:
1. Identify factual claims in the AI response.
2. For each claim, determine if it is SUPPORTED, CONTRADICTED, or UNVERIFIED based only on the trusted evidence.
3. Return ONLY this JSON structure:

{{
  "claims": [
    {{
      "claim": "<claim text>",
      "status": "SUPPORTED|CONTRADICTED|UNVERIFIED",
      "evidence_ref": "<relevant evidence snippet or null>",
      "confidence": 0.0
    }}
  ],
  "overall": "LOW_RISK|MEDIUM_RISK|HIGH_RISK|CRITICAL_RISK|UNVERIFIED",
  "contradiction_detected": true|false,
  "grounding_score": 0.0,
  "confidence": 0.0,
  "reason": "<brief explanation>"
}}"""

REPAIR_SYSTEM_PROMPT = """You are a response repair component inside an enterprise AI control layer.
Rewrite the provided AI response to:
1. Remove or correct any claims that contradict the trusted evidence.
2. Remove any detected sensitive/PII information.
3. Do NOT invent missing facts — if evidence is insufficient, state limitations clearly.
4. Use professional, clear business language.
5. Return ONLY the repaired response text, nothing else."""

REPAIR_USER_PROMPT = """ORIGINAL RESPONSE (DO NOT USE THIS DIRECTLY):
{original_response}

FAILURE REASONS:
{reasons}

TRUSTED EVIDENCE (use only this):
{evidence}

INSTRUCTIONS:
{instructions}

Return only the corrected response text:"""

CLAIM_EXTRACTION_PROMPT = """Extract all factual claims from this text. Return as a JSON array of strings.
Only include verifiable claims (facts, status statements, numbers, dates).
Do NOT include opinions or general statements.

TEXT: {text}

Return ONLY: {{"claims": ["claim1", "claim2"]}}"""
