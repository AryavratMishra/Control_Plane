from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey,
    Integer, String, Text, Numeric, func, JSON
)
from sqlalchemy.orm import relationship

try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False

from app.db.session import Base


def gen_uuid():
    return str(uuid.uuid4())


class Application(Base):
    __tablename__ = "applications"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(200), nullable=False)
    use_case = Column(String(100), nullable=False)
    risk_level = Column(String(20), nullable=False, default="medium")
    geography = Column(String(10), nullable=False, default="IN")
    latency_budget_ms = Column(Integer, default=700)
    expected_cost_inr = Column(Numeric(10, 4), default=0.20)
    max_tool_calls = Column(Integer, default=5)
    max_retries = Column(Integer, default=2)
    controlplane_failure_mode = Column(String(20), default="fail_open")
    status = Column(String(20), default="active")
    created_at = Column(DateTime, server_default=func.now())

    conversations = relationship("Conversation", back_populates="application")
    policy_versions = relationship("PolicyVersion", back_populates="application")


class ModelConfig(Base):
    __tablename__ = "models"

    id = Column(String, primary_key=True, default=gen_uuid)
    provider = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    input_price_per_1k = Column(Numeric(10, 6), default=0.0)
    output_price_per_1k = Column(Numeric(10, 6), default=0.0)
    active = Column(Boolean, default=True)


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=gen_uuid)
    application_id = Column(String, ForeignKey("applications.id"), nullable=False)
    external_conversation_id = Column(String(200))
    created_at = Column(DateTime, server_default=func.now())

    application = relationship("Application", back_populates="conversations")
    requests = relationship("Request", back_populates="conversation")


class Request(Base):
    __tablename__ = "requests"

    id = Column(String, primary_key=True, default=gen_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    request_text = Column(Text, nullable=False)
    risk_context = Column(JSON, default={})
    created_at = Column(DateTime, server_default=func.now())

    conversation = relationship("Conversation", back_populates="requests")
    response = relationship("Response", back_populates="request", uselist=False)
    execution_events = relationship("ExecutionEvent", back_populates="request")


class Response(Base):
    __tablename__ = "responses"

    id = Column(String, primary_key=True, default=gen_uuid)
    request_id = Column(String, ForeignKey("requests.id"), nullable=False)
    response_text = Column(Text, nullable=False)
    repaired_response_text = Column(Text)
    model_name = Column(String(100))
    final_status = Column(String(20), default="pending")
    created_at = Column(DateTime, server_default=func.now())

    request = relationship("Request", back_populates="response")
    risk_assessment = relationship("RiskAssessment", back_populates="response", uselist=False)


class ExecutionEvent(Base):
    __tablename__ = "execution_events"

    id = Column(String, primary_key=True, default=gen_uuid)
    request_id = Column(String, ForeignKey("requests.id"), nullable=False)
    parent_event_id = Column(String, nullable=True)
    event_type = Column(String(50))
    model_name = Column(String(100))
    tool_name = Column(String(100))
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    latency_ms = Column(Integer)
    estimated_cost_inr = Column(Numeric(10, 4))
    extra_metadata = Column(JSON, default={})
    created_at = Column(DateTime, server_default=func.now())

    request = relationship("Request", back_populates="execution_events")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(String, primary_key=True, default=gen_uuid)
    response_id = Column(String, ForeignKey("responses.id"), nullable=False)
    performance_score = Column(Numeric(5, 4), default=0.0)
    performance_risk = Column(String(20))
    cost_score = Column(Numeric(5, 4), default=0.0)
    cost_risk = Column(String(20))
    responsibility_score = Column(Numeric(5, 4), default=0.0)
    responsibility_risk = Column(String(20))
    overall_risk_score = Column(Numeric(5, 4), default=0.0)
    overall_risk_level = Column(String(20))
    business_impact = Column(String(20))
    detector_confidence = Column(Numeric(5, 4))
    action = Column(String(20))
    reasoning = Column(JSON, default={})
    policy_version_id = Column(String, nullable=True)
    fast_screen_ms = Column(Integer)
    total_evaluation_ms = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())

    response = relationship("Response", back_populates="risk_assessment")
    incident = relationship("Incident", back_populates="risk_assessment", uselist=False)


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, default=gen_uuid)
    risk_assessment_id = Column(String, ForeignKey("risk_assessments.id"), nullable=False)
    incident_type = Column(String(50))
    severity = Column(String(20))
    action = Column(String(20))
    status = Column(String(20), default="open")
    reason = Column(Text)
    evidence = Column(JSON, default={})
    application_name = Column(String(200))
    request_text = Column(Text)
    response_text = Column(Text)
    repaired_response_text = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    resolved_at = Column(DateTime, nullable=True)

    risk_assessment = relationship("RiskAssessment", back_populates="incident")
    human_reviews = relationship("HumanReview", back_populates="incident")


class HumanReview(Base):
    __tablename__ = "human_reviews"

    id = Column(String, primary_key=True, default=gen_uuid)
    incident_id = Column(String, ForeignKey("incidents.id"), nullable=False)
    reviewer_name = Column(String(100), default="Reviewer")
    review_action = Column(String(20))
    comment = Column(Text)
    original_action = Column(String(20))
    final_action = Column(String(20))
    was_correct = Column(String(20))
    created_at = Column(DateTime, server_default=func.now())

    incident = relationship("Incident", back_populates="human_reviews")


class Policy(Base):
    __tablename__ = "policies"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    use_case = Column(String(100))
    geography = Column(String(10))
    created_at = Column(DateTime, server_default=func.now())

    versions = relationship("PolicyVersion", back_populates="policy")


class PolicyVersion(Base):
    __tablename__ = "policy_versions"

    id = Column(String, primary_key=True, default=gen_uuid)
    policy_id = Column(String, ForeignKey("policies.id"), nullable=False)
    application_id = Column(String, ForeignKey("applications.id"), nullable=True)
    version = Column(Integer, default=1)
    config = Column(JSON, default={})
    status = Column(String(20), default="active")
    effective_from = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())

    policy = relationship("Policy", back_populates="versions")
    application = relationship("Application", back_populates="policy_versions")


class TrustedDocument(Base):
    __tablename__ = "trusted_documents"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(200), nullable=False)
    source_type = Column(String(50))
    source_uri = Column(String(500))
    trust_level = Column(String(20), default="high")
    content = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    chunks = relationship("RetrievalChunk", back_populates="document")


class RetrievalChunk(Base):
    __tablename__ = "retrieval_chunks"

    id = Column(String, primary_key=True, default=gen_uuid)
    document_id = Column(String, ForeignKey("trusted_documents.id"), nullable=False)
    content = Column(Text, nullable=False)
    embedding_json = Column(JSON)
    extra_metadata = Column(JSON, default={})
    chunk_index = Column(Integer, default=0)

    document = relationship("TrustedDocument", back_populates="chunks")
