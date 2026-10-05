import os
import hashlib
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.models.entities import Case, CaseImage, HealthWorker, AuditLog
from backend.app.schemas.dtos import CaseSyncBatchRequest, CaseSyncBatchResponse
from backend.app.routers.auth import get_current_worker

router = APIRouter(prefix="/sync", tags=["Synchronization (Offline-First)"])

@router.post("/cases", response_model=CaseSyncBatchResponse)
def sync_cases_batch(
    payload: CaseSyncBatchRequest,
    current_worker: Optional[HealthWorker] = Depends(get_current_worker),
    db: Session = Depends(get_db)
):
    """
    Idempotent sync for clinical cases recorded offline by community health workers.
    Re-playing the same UUID is safe and will not create duplicate records.
    """
    synced_uuids = []
    duplicates_count = 0
    
    worker_id = current_worker.id if current_worker else None
    default_facility_id = current_worker.facility_id if current_worker else None
    
    for item in payload.cases:
        # Check if case UUID already exists
        existing = db.query(Case).filter(Case.uuid == item.uuid).first()
        if existing:
            duplicates_count += 1
            synced_uuids.append(item.uuid)
            continue
        
        # Insert new case
        new_case = Case(
            uuid=item.uuid,
            worker_id=worker_id,
            facility_id=item.facility_id or default_facility_id,
            created_at=item.created_at,
            age_group=item.age_group,
            sex=item.sex,
            body_zone=item.body_zone,
            answers=item.answers,
            model_version=item.model_version,
            model_prediction=item.model_prediction,
            confidence=item.confidence,
            indeterminate=item.indeterminate or False,
            worker_decision=item.worker_decision,
            urgency=item.urgency or "standard",
            notes=item.notes
        )
        db.add(new_case)
        synced_uuids.append(item.uuid)
    
    if synced_uuids:
        # Log action
        log = AuditLog(
            user_id=worker_id,
            action="SYNC_CASES_BATCH",
            target_type="cases",
            target_id=f"count:{len(synced_uuids)}",
            details=f"Synced {len(synced_uuids)} cases, {duplicates_count} duplicates skipped."
        )
        db.add(log)
    
    db.commit()
    
    return CaseSyncBatchResponse(
        synced_count=len(synced_uuids) - duplicates_count,
        duplicates_ignored=duplicates_count,
        synced_uuids=synced_uuids
    )

@router.post("/images")
async def sync_image(
    case_uuid: str = Form(...),
    research_consent: bool = Form(False),
    blur_score: Optional[float] = Form(None),
    file: UploadFile = File(...),
    current_worker: Optional[HealthWorker] = Depends(get_current_worker),
    db: Session = Depends(get_db)
):
    """
    Receives lesion photo linked to a case.
    Strict ethical compliance: images without research consent are flagged and strictly scoped.
    """
    case = db.query(Case).filter(Case.uuid == case_uuid).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cas avec UUID '{case_uuid}' introuvable. Veuillez synchroniser le cas avant l'image."
        )
    
    # Save file to storage
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    content = await file.read()
    
    # Compute sha256
    file_hash = hashlib.sha256(content).hexdigest()
    extension = os.path.splitext(file.filename)[1] or ".jpg"
    safe_filename = f"{case_uuid}_{file_hash[:10]}{extension}"
    target_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
    
    with open(target_path, "wb") as f:
        f.write(content)
    
    # Register image record
    image_record = CaseImage(
        case_uuid=case_uuid,
        file_path=target_path,
        sha256_hash=file_hash,
        research_consent=research_consent,
        blur_score=blur_score,
        is_valid=True
    )
    db.add(image_record)
    db.commit()
    db.refresh(image_record)
    
    return {
        "status": "success",
        "image_id": image_record.id,
        "case_uuid": case_uuid,
        "sha256": file_hash,
        "consent_recorded": research_consent
    }
