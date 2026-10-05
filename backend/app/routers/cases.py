import os
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.entities import Case, CaseImage, ExpertReview, HealthWorker, AuditLog
from backend.app.schemas.dtos import (
    CaseDetailResponse, ExpertReviewCreate, ExpertReviewResponse
)
from backend.app.routers.auth import get_current_worker, require_role

router = APIRouter(prefix="/cases", tags=["Clinical Cases & Expert Reviews"])

@router.get("", response_model=List[CaseDetailResponse])
def list_cases(
    urgency: Optional[str] = Query(None, description="Filtrer par urgence ('standard', 'prioritaire', 'urgente')"),
    indeterminate: Optional[bool] = Query(None, description="Filtrer les cas indéterminés nécessitant revue"),
    district: Optional[str] = Query(None, description="Filtrer par district sanitaire"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_worker: HealthWorker = Depends(get_current_worker),
    db: Session = Depends(get_db)
):
    query = db.query(Case)
    if urgency:
        query = query.filter(Case.urgency == urgency)
    if indeterminate is not None:
        query = query.filter(Case.indeterminate == indeterminate)
    
    # If filtered by district through facility
    if district:
        query = query.join(Case.facility).filter(Case.facility.has(district=district))
    
    cases = query.order_by(Case.created_at.desc()).offset(offset).limit(limit).all()
    return cases

@router.get("/{case_uuid}", response_model=CaseDetailResponse)
def get_case(
    case_uuid: str,
    current_worker: HealthWorker = Depends(get_current_worker),
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.uuid == case_uuid).first()
    if not case:
        raise HTTPException(status_code=404, detail="Cas introuvable")
    return case

@router.delete("/{case_uuid}")
def delete_case_right_to_erasure(
    case_uuid: str,
    current_worker: HealthWorker = Depends(require_role("supervisor", "district", "admin")),
    db: Session = Depends(get_db)
):
    """
    Droit à l'effacement (RGPD / Loi protection des données de santé).
    Supprime définitivement les données du cas et ses photos associées.
    """
    case = db.query(Case).filter(Case.uuid == case_uuid).first()
    if not case:
        raise HTTPException(status_code=404, detail="Cas introuvable")
    
    # Delete associated image files
    images = db.query(CaseImage).filter(CaseImage.case_uuid == case_uuid).all()
    for img in images:
        if img.file_path and os.path.exists(img.file_path):
            try:
                os.remove(img.file_path)
            except OSError:
                pass
    
    # Audit log entry for compliance
    log = AuditLog(
        user_id=current_worker.id,
        action="RIGHT_TO_ERASURE_DELETE",
        target_type="case",
        target_id=case_uuid,
        details=f"Dossier patient effacé par {current_worker.full_name} ({current_worker.role})"
    )
    db.add(log)
    
    db.delete(case)
    db.commit()
    return {"status": "success", "message": f"Dossier {case_uuid} supprimé conformément au droit à l'effacement."}

# ── Expert reviews router ───────────────────────────────────────────────────
reviews_router = APIRouter(prefix="/reviews", tags=["Expert Clinical Reviews"])

@reviews_router.post("", response_model=ExpertReviewResponse)
def submit_expert_review(
    review_in: ExpertReviewCreate,
    current_worker: HealthWorker = Depends(require_role("supervisor", "district", "admin")),
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.uuid == review_in.case_uuid).first()
    if not case:
        raise HTTPException(status_code=404, detail="Cas clinique introuvable")
    
    review = ExpertReview(
        case_uuid=review_in.case_uuid,
        expert_id=current_worker.id,
        validated_label=review_in.validated_label,
        confidence_level=review_in.confidence_level,
        clinical_comment=review_in.clinical_comment,
        suggested_action=review_in.suggested_action
    )
    db.add(review)
    
    # Update case worker_decision if validated
    case.worker_decision = f"Revue par expert: {review_in.validated_label}"
    
    db.commit()
    db.refresh(review)
    return review

@reviews_router.get("/{case_uuid}", response_model=List[ExpertReviewResponse])
def get_case_reviews(
    case_uuid: str,
    current_worker: HealthWorker = Depends(get_current_worker),
    db: Session = Depends(get_db)
):
    reviews = db.query(ExpertReview).filter(ExpertReview.case_uuid == case_uuid).all()
    return reviews
