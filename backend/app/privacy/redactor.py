from __future__ import annotations

from app.controlplane.types import PiiEntity


def redact_pii(text: str, entities: list[PiiEntity]) -> str:
    """
    Replace PII spans with [REDACTED:TYPE] placeholders.
    Process in reverse order to preserve character offsets.
    """
    if not entities:
        return text

    result = list(text)
    for entity in sorted(entities, key=lambda e: e.start, reverse=True):
        placeholder = f"[REDACTED:{entity.entity_type}]"
        result[entity.start:entity.end] = list(placeholder)

    return "".join(result)


def mask_pii_partial(text: str, entities: list[PiiEntity]) -> str:
    """
    Partially mask PII: show first 2 and last 2 chars only.
    e.g. 9876543210 → 98XXXXXX10
    """
    if not entities:
        return text

    result = list(text)
    for entity in sorted(entities, key=lambda e: e.start, reverse=True):
        span_text = entity.text
        if len(span_text) > 4:
            masked = span_text[:2] + "X" * (len(span_text) - 4) + span_text[-2:]
        else:
            masked = "X" * len(span_text)
        result[entity.start:entity.end] = list(masked)

    return "".join(result)
