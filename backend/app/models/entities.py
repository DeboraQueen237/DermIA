from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Facility(Base):
    __tablename__ = "facilities"
    
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    health_area = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=False, index=True)
    region = Column(String(100), nullable=False, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    
    workers = relationship("HealthWorker", back_populates="facility")
    cases = relationship("Case", back_populates="facility")

class HealthWorker(Base):
    __tablename__ = "health_workers"
    
    id = Column(String(50), primary_key=True, index=True)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    role = Column(String(50), default="asc")  # 'asc', 'supervisor', 'district', 'admin'
    facility_id = Column(String(50), ForeignKey("facilities.id"), nullable=True)
    active = Column(Boolean, default=True)
    phone_number = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    
    facility = relationship("Facility", back_populates="workers")
    cases = relationship("Case", back_populates="worker")
    expert_reviews = relationship("ExpertReview", back_populates="expert")

class Case(Base):
    __tablename__ = "cases"
    
    uuid = Column(String(36), primary_key=True, index=True)  # Client-generated UUID
    worker_id = Column(String(50), ForeignKey("health_workers.id"), nullable=True, index=True)
    facility_id = Column(String(50), ForeignKey("facilities.id"), nullable=True, index=True)
    
    created_at = Column(DateTime, nullable=False, default=utc_now)
    synced_at = Column(DateTime, default=utc_now)
    
    age_group = Column(String(50), nullable=True)  # '0-5', '6-15', '16-45', '45+'
    sex = Column(String(20), nullable=True)        # 'M', 'F'
    body_zone = Column(String(50), nullable=True)  # 'visage', 'jambes', 'bras', 'tronc', etc.
    
    # Clinical answers & ML metadata
    answers = Column(JSON, nullable=True)
    model_version = Column(String(50), nullable=True)
    model_prediction = Column(JSON, nullable=True) # list of top hypotheses with probabilities
    confidence = Column(Float, nullable=True)
    indeterminate = Column(Boolean, default=False)
    
    # Decisions
    worker_decision = Column(String(100), nullable=True)
    urgency = Column(String(30), default="standard", index=True) # 'standard', 'prioritaire', 'urgente'
    notes = Column(Text, nullable=True)
    
    # Relationships
    worker = relationship("HealthWorker", back_populates="cases")
    facility = relationship("Facility", back_populates="cases")
    images = relationship("CaseImage", back_populates="case", cascade="all, delete-orphan")
    reviews = relationship("ExpertReview", back_populates="case", cascade="all, delete-orphan")

class CaseImage(Base):
    __tablename__ = "case_images"
    
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_uuid = Column(String(36), ForeignKey("cases.uuid"), nullable=False, index=True)
    file_path = Column(String(255), nullable=False)
    sha256_hash = Column(String(64), nullable=True)
    research_consent = Column(Boolean, default=False)
    blur_score = Column(Float, nullable=True)
    is_valid = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    
    case = relationship("Case", back_populates="images")

class ExpertReview(Base):
    __tablename__ = "expert_reviews"
    
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_uuid = Column(String(36), ForeignKey("cases.uuid"), nullable=False, index=True)
    expert_id = Column(String(50), ForeignKey("health_workers.id"), nullable=False)
    
    validated_label = Column(String(100), nullable=False)
    confidence_level = Column(String(50), default="high") # 'high', 'moderate', 'low'
    clinical_comment = Column(Text, nullable=True)
    suggested_action = Column(String(150), nullable=True)
    reviewed_at = Column(DateTime, default=utc_now)
    
    case = relationship("Case", back_populates="reviews")
    expert = relationship("HealthWorker", back_populates="expert_reviews")

class EpidemicAlert(Base):
    __tablename__ = "epidemic_alerts"
    
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_type = Column(String(50), nullable=False) # 'CUSUM', 'EARS', 'CLUSTER'
    health_area = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=False, index=True)
    disease_id = Column(String(50), nullable=False, index=True)
    
    cases_observed = Column(Integer, default=0)
    cases_expected = Column(Float, default=0.0)
    signal_score = Column(Float, default=0.0)
    
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    status = Column(String(30), default="pending") # 'pending', 'investigating', 'confirmed', 'dismissed'
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

class ModelRelease(Base):
    __tablename__ = "model_releases"
    
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    version = Column(String(50), unique=True, nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    signature = Column(Text, nullable=True)
    metrics = Column(JSON, nullable=True)
    file_path = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)

class KBRelease(Base):
    __tablename__ = "kb_releases"
    
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    version = Column(String(50), unique=True, nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    manifest = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=False)
    target_id = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utc_now)
