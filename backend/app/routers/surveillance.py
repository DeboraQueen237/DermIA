from typing import List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.core.database import get_db
from backend.app.models.entities import Case, Facility, EpidemicAlert, HealthWorker
from backend.app.schemas.dtos import (
    EpidemicAlertResponse, AlertStatusUpdate, SurveillanceStats
)
from backend.app.routers.auth import get_current_worker, require_role
from backend.app.services.surveillance_service import detect_district_anomalies

router = APIRouter(prefix="/surveillance", tags=["Epidemic Surveillance & Alerts"])

@router.get("/stats", response_model=SurveillanceStats)
def get_surveillance_stats(
    current_worker: HealthWorker = Depends(get_current_worker),
    db: Session = Depends(get_db)
):
    total = db.query(Case).count()
    urgent = db.query(Case).filter(Case.urgency == "urgente").count()
    priority = db.query(Case).filter(Case.urgency == "prioritaire").count()
    standard = db.query(Case).filter(Case.urgency == "standard").count()
    
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent = db.query(Case).filter(Case.created_at >= seven_days_ago).count()
    
    # Diseases breakdown
    cases = db.query(Case).all()
    disease_counts = {}
    for c in cases:
        if c.model_prediction and isinstance(c.model_prediction, list) and len(c.model_prediction) > 0:
            top_d = c.model_prediction[0].get("nom", "Autre / Non classé")
            disease_counts[top_d] = disease_counts.get(top_d, 0) + 1
        elif c.worker_decision:
            disease_counts[c.worker_decision] = disease_counts.get(c.worker_decision, 0) + 1
        else:
            disease_counts["Indéterminé"] = disease_counts.get("Indéterminé", 0) + 1
            
    # District breakdown
    district_counts = {}
    facilities = db.query(Facility).all()
    fac_map = {f.id: f.district for f in facilities}
    for c in cases:
        dist = fac_map.get(c.facility_id, "Non attribué")
        district_counts[dist] = district_counts.get(dist, 0) + 1
        
    active_alerts = db.query(EpidemicAlert).filter(EpidemicAlert.status == "pending").count()
    
    return SurveillanceStats(
        total_cases=total,
        urgent_cases=urgent,
        priority_cases=priority,
        standard_cases=standard,
        cases_last_7_days=recent,
        top_diseases=disease_counts,
        cases_by_district=district_counts,
        active_alerts_count=active_alerts
    )

@router.get("/alerts", response_model=List[EpidemicAlertResponse])
def list_alerts(
    status_filter: Optional[str] = Query(None, description="Filtrer ('pending', 'investigating', 'confirmed', 'dismissed')"),
    current_worker: HealthWorker = Depends(get_current_worker),
    db: Session = Depends(get_db)
):
    query = db.query(EpidemicAlert)
    if status_filter:
        query = query.filter(EpidemicAlert.status == status_filter)
    return query.order_by(EpidemicAlert.created_at.desc()).all()

@router.post("/detect-anomalies", response_model=List[EpidemicAlertResponse])
def trigger_anomaly_detection(
    lookback_days: int = Query(28, ge=7, le=90),
    current_worker: HealthWorker = Depends(require_role("supervisor", "district", "admin")),
    db: Session = Depends(get_db)
):
    """
    Exécute les algorithmes de détection de signaux faibles (CUSUM et EARS C2 de l'OMS/CDC)
    sur l'historique des consultations par aire de santé.
    """
    alerts = detect_district_anomalies(db, lookback_days=lookback_days)
    return alerts

@router.patch("/alerts/{alert_id}", response_model=EpidemicAlertResponse)
def update_alert_status(
    alert_id: str,
    update_data: AlertStatusUpdate,
    current_worker: HealthWorker = Depends(require_role("supervisor", "district", "admin")),
    db: Session = Depends(get_db)
):
    alert = db.query(EpidemicAlert).filter(EpidemicAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte introuvable")
    
    alert.status = update_data.status
    if update_data.notes:
        alert.notes = (alert.notes or "") + f" | MAJ ({current_worker.full_name}): {update_data.notes}"
        
    db.commit()
    db.refresh(alert)
    return alert

@router.get("/map-cases")
def get_map_cases(
    current_worker: HealthWorker = Depends(get_current_worker),
    db: Session = Depends(get_db)
):
    """
    Retourne les cas avec coordonnées géographiques de la structure de santé
    (principe de confidentialité : aucune coordonnée GPS brute de patient n'est exposée).
    """
    results = (
        db.query(Case, Facility)
        .join(Facility, Case.facility_id == Facility.id)
        .filter(Facility.latitude.isnot(None), Facility.longitude.isnot(None))
        .all()
    )
    
    points = []
    for case, fac in results:
        top_name = "Indéterminé"
        if case.model_prediction and len(case.model_prediction) > 0:
            top_name = case.model_prediction[0].get("nom", "Indéterminé")
            
        points.append({
            "uuid": case.uuid,
            "created_at": case.created_at.isoformat(),
            "facility_name": fac.name,
            "health_area": fac.health_area,
            "district": fac.district,
            "latitude": fac.latitude,
            "longitude": fac.longitude,
            "urgency": case.urgency,
            "disease": top_name,
            "indeterminate": case.indeterminate
        })
    return points
