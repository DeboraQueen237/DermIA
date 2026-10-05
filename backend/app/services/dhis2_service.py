from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models.entities import Case, Facility

# WHO / ICD-11 mapping for dermatology conditions
DHIS2_DATA_ELEMENT_MAPPING = {
  "buruli": "DE_NTD_BURULI_CONFIRMED",
  "lepre": "DE_NTD_LEPROSY_NEW",
  "pian": "DE_NTD_YAWS_SUSPECT",
  "gale": "DE_SKIN_SCABIES",
  "teigne": "DE_SKIN_TINEA_CAPITIS",
  "impetigo": "DE_SKIN_IMPETIGO",
  "eczema": "DE_SKIN_ECZEMA",
  "furoncle": "DE_SKIN_FURUNCLE"
}

def export_dhis2_datavalueset(
    db: Session,
    year_week: str = None, # e.g. "2026W40"
    facility_id: str = None
) -> Dict[str, Any]:
    """
    Exports aggregated case notifications in DHIS2 DataValueSet JSON format
    for direct ingestion into national health information systems.
    """
    now = datetime.now(timezone.utc)
    if not year_week:
        iso_year, iso_week, _ = now.isocalendar()
        year_week = f"{iso_year}W{iso_week:02d}"
        
    query = db.query(Case, Facility).join(Facility, Case.facility_id == Facility.id, isouter=True)
    if facility_id:
        query = query.filter(Case.facility_id == facility_id)
        
    cases = query.all()
    
    # Aggregation: (facility_orgUnit, disease_id) -> count
    counts: Dict[str, Dict[str, int]] = {}
    
    for case, fac in cases:
        org_unit = fac.id if fac else "ORG_DEFAULT_DISTRICT"
        
        disease_id = "autre"
        if case.model_prediction and len(case.model_prediction) > 0:
            disease_id = case.model_prediction[0].get("id", "autre")
            
        if org_unit not in counts:
            counts[org_unit] = {}
        counts[org_unit][disease_id] = counts[org_unit].get(disease_id, 0) + 1
        
    data_values: List[Dict[str, Any]] = []
    
    for org_unit, disease_counts in counts.items():
        for disease_id, count in disease_counts.items():
            de_code = DHIS2_DATA_ELEMENT_MAPPING.get(disease_id, f"DE_SKIN_OTHER_{disease_id.upper()}")
            data_values.append({
                "dataElement": de_code,
                "period": year_week,
                "orgUnit": org_unit,
                "categoryOptionCombo": "DEFAULT",
                "attributeOptionCombo": "DEFAULT",
                "value": str(count),
                "storedBy": "DermIA_Automated_Pipeline",
                "created": now.isoformat(),
                "lastUpdated": now.isoformat(),
                "comment": "Agrégation automatique consultations DermIA terrain"
            })
            
    return {
        "dataSet": "DERM_SURV_WEEKLY_V1",
        "completeDate": now.strftime("%Y-%m-%d"),
        "period": year_week,
        "orgUnit": facility_id or "NATIONAL_LEVEL",
        "dataValues": data_values
    }
