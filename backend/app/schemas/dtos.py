from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# ── Auth & User ─────────────────────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    worker_id: str
    full_name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class HealthWorkerResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    facility_id: Optional[str] = None
    phone_number: Optional[str] = None
    active: bool

    class Config:
        from_attributes = True

# ── Facility ────────────────────────────────────────────────────────────────
class FacilityCreate(BaseModel):
    id: str
    name: str
    health_area: str
    district: str
    region: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class FacilityResponse(FacilityCreate):
    class Config:
        from_attributes = True

# ── Sync & Cases ────────────────────────────────────────────────────────────
class HypothesisDto(BaseModel):
    id: str
    nom: str
    score: Optional[float] = 0.0
    share: Optional[float] = 0.0

class CaseSyncItem(BaseModel):
    uuid: str
    created_at: datetime
    age_group: Optional[str] = None
    sex: Optional[str] = None
    body_zone: Optional[str] = None
    answers: Optional[Dict[str, Any]] = None
    model_version: Optional[str] = None
    model_prediction: Optional[List[Dict[str, Any]]] = None
    confidence: Optional[float] = None
    indeterminate: Optional[bool] = False
    worker_decision: Optional[str] = None
    urgency: Optional[str] = "standard"
    notes: Optional[str] = None
    facility_id: Optional[str] = None

class CaseSyncBatchRequest(BaseModel):
    cases: List[CaseSyncItem]

class CaseSyncBatchResponse(BaseModel):
    synced_count: int
    duplicates_ignored: int
    synced_uuids: List[str]

class CaseDetailResponse(BaseModel):
    uuid: str
    created_at: datetime
    synced_at: datetime
    worker_id: Optional[str] = None
    facility_id: Optional[str] = None
    age_group: Optional[str] = None
    sex: Optional[str] = None
    body_zone: Optional[str] = None
    answers: Optional[Dict[str, Any]] = None
    model_version: Optional[str] = None
    model_prediction: Optional[List[Dict[str, Any]]] = None
    confidence: Optional[float] = None
    indeterminate: bool = False
    worker_decision: Optional[str] = None
    urgency: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True

# ── Expert Reviews ──────────────────────────────────────────────────────────
class ExpertReviewCreate(BaseModel):
    case_uuid: str
    validated_label: str
    confidence_level: str = "high"
    clinical_comment: Optional[str] = None
    suggested_action: Optional[str] = None

class ExpertReviewResponse(ExpertReviewCreate):
    id: str
    expert_id: str
    reviewed_at: datetime

    class Config:
        from_attributes = True

# ── Epidemic Surveillance & Alerts ──────────────────────────────────────────
class EpidemicAlertResponse(BaseModel):
    id: str
    alert_type: str
    health_area: str
    district: str
    disease_id: str
    cases_observed: int
    cases_expected: float
    signal_score: float
    period_start: datetime
    period_end: datetime
    status: str
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AlertStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None

class SurveillanceStats(BaseModel):
    total_cases: int
    urgent_cases: int
    priority_cases: int
    standard_cases: int
    cases_last_7_days: int
    top_diseases: Dict[str, int]
    cases_by_district: Dict[str, int]
    active_alerts_count: int

# ── Releases (OTA) ──────────────────────────────────────────────────────────
class ReleaseInfo(BaseModel):
    version: str
    sha256_hash: str
    download_url: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None
