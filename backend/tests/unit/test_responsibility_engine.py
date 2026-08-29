import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def test_pii_detector_email():
    from app.privacy.pii_detector import detect_pii
    entities = detect_pii("Contact me at john.doe@example.com for details.")
    assert any(e.entity_type == "EMAIL" for e in entities)


def test_pii_detector_phone():
    from app.privacy.pii_detector import detect_pii
    entities = detect_pii("My number is 9876543210.")
    assert any(e.entity_type == "PHONE_IN" for e in entities)


def test_pii_detector_pan():
    from app.privacy.pii_detector import detect_pii
    entities = detect_pii("PAN: ABCDE1234F")
    assert any(e.entity_type == "PAN" for e in entities)
    pan_entity = next(e for e in entities if e.entity_type == "PAN")
    assert pan_entity.policy_action == "block"


def test_redactor():
    from app.privacy.pii_detector import detect_pii
    from app.privacy.redactor import redact_pii
    text = "Email: rahul@test.com, Phone: 9876543210"
    entities = detect_pii(text)
    redacted = redact_pii(text, entities)
    assert "rahul@test.com" not in redacted
    assert "9876543210" not in redacted
    assert "[REDACTED:" in redacted


def test_responsibility_engine_pii():
    from app.controlplane.responsibility_engine import run_responsibility_engine
    result = run_responsibility_engine(
        response_text="Your number is 9876543210 and email is test@example.com. PAN: ABCDE1234F",
        request_text="What is my info?",
        context={"use_case": "customer_support", "business_impact": "high"},
        policy={"rules": {"critical_pii_exposure": "block", "pii_exposure": "redact"}},
    )
    assert result.pii_detected
    assert result.risk_level in ("HIGH", "CRITICAL")
    assert any(v.severity == "critical" for v in result.policy_violations)


def test_responsibility_engine_clean():
    from app.controlplane.responsibility_engine import run_responsibility_engine
    result = run_responsibility_engine(
        response_text="Our support team is available Monday to Saturday, 9 AM to 6 PM.",
        request_text="What are your hours?",
        context={"use_case": "customer_support", "business_impact": "low"},
        policy={"rules": {}},
    )
    assert not result.pii_detected
    assert result.risk_level == "LOW"
