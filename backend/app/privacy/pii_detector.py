from __future__ import annotations

import re
from typing import Optional
from app.controlplane.types import PiiEntity

# ---------------------------------------------------------------------------
# Comprehensive PII detection patterns
# ---------------------------------------------------------------------------

_PATTERNS: dict[str, re.Pattern] = {
    "EMAIL": re.compile(
        r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
    ),
    "PHONE_IN": re.compile(
        r"\b(?:\+91[\-\s]?)?[6-9]\d{9}\b"
    ),
    "PHONE_GENERIC": re.compile(
        r"\b(?:\+?\d{1,3}[\s\-]?)?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}\b"
    ),
    "CREDIT_CARD": re.compile(
        r"\b(?:\d[ \-]?){13,16}\b"
    ),
    "ACCOUNT_NUMBER": re.compile(
        r"\b(?:account|acc|a/c)[\s:#]*\d{6,18}\b", re.IGNORECASE
    ),
    "PAN": re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),
    "AADHAAR": re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"),
    "IFSC": re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b"),
    "IP_ADDRESS": re.compile(
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    ),
    "CUSTOMER_ID": re.compile(
        r"\b(?:customer|cust|customer_id|cid)[\s:#]*[A-Z]?\d{4,10}\b", re.IGNORECASE
    ),
    "ORDER_ID": re.compile(
        r"\b(?:order|ord)[\s:#]*[A-Z]{0,4}\d{4,10}\b", re.IGNORECASE
    ),
}

# Confidence levels per entity type
_CONFIDENCE: dict[str, float] = {
    "EMAIL": 0.97,
    "PHONE_IN": 0.92,
    "PHONE_GENERIC": 0.75,
    "CREDIT_CARD": 0.85,
    "ACCOUNT_NUMBER": 0.88,
    "PAN": 0.96,
    "AADHAAR": 0.80,
    "IFSC": 0.93,
    "IP_ADDRESS": 0.70,
    "CUSTOMER_ID": 0.78,
    "ORDER_ID": 0.72,
}

# Policy actions per entity type
_POLICY_ACTION: dict[str, str] = {
    "EMAIL": "redact",
    "PHONE_IN": "redact",
    "PHONE_GENERIC": "redact",
    "CREDIT_CARD": "block",
    "ACCOUNT_NUMBER": "redact",
    "PAN": "block",
    "AADHAAR": "block",
    "IFSC": "redact",
    "IP_ADDRESS": "redact",
    "CUSTOMER_ID": "redact",
    "ORDER_ID": "allow",
}


def detect_pii(text: str, policy_rules: Optional[dict] = None) -> list[PiiEntity]:
    """
    Run all PII patterns against the text.
    Returns a list of PiiEntity findings sorted by start position.
    """
    entities: list[PiiEntity] = []
    seen_spans: set[tuple[int, int]] = set()

    for entity_type, pattern in _PATTERNS.items():
        for match in pattern.finditer(text):
            span = (match.start(), match.end())
            # Skip overlapping spans
            if any(s <= span[0] < e or s < span[1] <= e for s, e in seen_spans):
                continue
            
            # Exclude generic business emails
            if entity_type == "EMAIL":
                if match.group().lower() in ("support@example.com", "info@example.com"):
                    continue

            seen_spans.add(span)

            # Apply policy override if provided
            policy_action = _POLICY_ACTION.get(entity_type, "redact")
            if policy_rules:
                if entity_type in ("CREDIT_CARD", "PAN", "AADHAAR") and \
                        policy_rules.get("critical_pii_exposure") == "block":
                    policy_action = "block"

            entities.append(PiiEntity(
                entity_type=entity_type,
                text=match.group(),
                start=match.start(),
                end=match.end(),
                confidence=_CONFIDENCE.get(entity_type, 0.75),
                policy_action=policy_action,
            ))

    entities.sort(key=lambda e: e.start)
    return entities
