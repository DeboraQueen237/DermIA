from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.entities import HealthWorker
from backend.app.routers.auth import get_current_worker, require_role
from backend.app.services.dhis2_service import export_dhis2_datavalueset

router = APIRouter(prefix="/export", tags=["National Health Interoperability (DHIS2)"])

@router.get("/dhis2")
def get_dhis2_export(
    period: Optional[str] = Query(None, description="Période ISO (ex: '2026W40')"),
    facility_id: Optional[str] = Query(None, description="Filtrer par structure de santé"),
    current_worker: HealthWorker = Depends(require_role("supervisor", "district", "admin")),
    db: Session = Depends(get_db)
):
    """
    Exporte le registre épidémiologique hebdomadaire au format d'échange officiel DHIS2
    pour intégration dans le Système National d'Information Sanitaire (SNIS).
    """
    export_payload = export_dhis2_datavalueset(db, year_week=period, facility_id=facility_id)
    return export_payload
