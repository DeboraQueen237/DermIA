from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.entities import Case, Facility, EpidemicAlert

def run_ears_c2(counts: List[int], k: float = 1.0, threshold: float = 2.0) -> Tuple[bool, float, float, float]:
    """
    EARS C2 algorithm (CDC standard aberration detection).
    Uses a 7-day baseline with a 2-day buffer period.
    Returns: (is_aberration, z_score, mean_baseline, std_baseline)
    """
    if len(counts) < 9: # need at least 7 days baseline + 1 buffer + 1 current day
        return False, 0.0, 0.0, 0.0
    
    current_val = counts[-1]
    baseline = counts[-9:-2] # 7 days baseline before the buffer
    
    mean = float(np.mean(baseline))
    std = float(np.std(baseline, ddof=1)) if len(baseline) > 1 else 0.0
    std = max(std, 0.5) # prevent division by zero
    
    z_score = (current_val - mean) / std
    is_aberration = z_score > threshold
    return is_aberration, float(z_score), mean, std

def run_cusum(counts: List[int], k: float = 0.5, h: float = 3.0) -> Tuple[bool, float, float]:
    """
    Standard tabular CUSUM algorithm for detecting small persistent upward shifts.
    S_t = max(0, S_{t-1} + (X_t - mu - k*sigma))
    Returns: (is_alarm, current_S, baseline_mean)
    """
    if len(counts) < 5:
        return False, 0.0, 0.0
    
    baseline = counts[:-1]
    current = counts[-1]
    
    mu = float(np.mean(baseline))
    sigma = float(np.std(baseline, ddof=1)) if len(baseline) > 1 else 1.0
    sigma = max(sigma, 0.5)
    
    # Calculate CUSUM
    s = 0.0
    for val in baseline + [current]:
        z = (val - mu) / sigma
        s = max(0.0, s + z - k)
        
    is_alarm = s > h
    return is_alarm, float(s), mu

def detect_district_anomalies(db: Session, lookback_days: int = 28) -> List[EpidemicAlert]:
    """
    Scans recent cases grouped by district, health area, and disease,
    applies EARS / CUSUM and generates new alert records in the database.
    """
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=lookback_days)
    
    # Fetch cases joined with facility
    cases = (
        db.query(Case, Facility)
        .join(Facility, Case.facility_id == Facility.id, isouter=True)
        .filter(Case.created_at >= start_date)
        .all()
    )
    
    # Group cases by (district, health_area, primary_disease, day_offset)
    grouped: Dict[Tuple[str, str, str], Dict[str, int]] = {}
    
    for case, fac in cases:
        district = fac.district if fac else "District Inconnu"
        health_area = fac.health_area if fac else "Aire Inconnue"
        
        # Primary disease identified
        disease = "indetermine"
        if case.model_prediction and isinstance(case.model_prediction, list) and len(case.model_prediction) > 0:
            disease = case.model_prediction[0].get("id", "indetermine")
            
        key = (district, health_area, disease)
        if key not in grouped:
            grouped[key] = {}
            
        day_str = case.created_at.strftime("%Y-%m-%d")
        grouped[key][day_str] = grouped[key].get(day_str, 0) + 1
        
    created_alerts = []
    
    # Generate daily sequences for the last 14 days
    date_sequence = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(lookback_days)]
    
    for (district, health_area, disease), date_counts in grouped.items():
        if disease == "indetermine":
            continue
            
        counts = [date_counts.get(d, 0) for d in date_sequence]
        recent_count = counts[-1]
        
        # Skip if very low absolute count
        if sum(counts[-3:]) < 3:
            continue
            
        # Run EARS
        is_ears, z_score, mean_b, _ = run_ears_c2(counts)
        is_cusum, s_score, mu_c = run_cusum(counts)
        
        if is_ears or is_cusum:
            # Check if alert already raised in the last 3 days
            recent_alert = (
                db.query(EpidemicAlert)
                .filter(
                    EpidemicAlert.district == district,
                    EpidemicAlert.health_area == health_area,
                    EpidemicAlert.disease_id == disease,
                    EpidemicAlert.created_at >= now - timedelta(days=3)
                )
                .first()
            )
            
            if not recent_alert:
                alert_type = "EARS_C2" if is_ears else "CUSUM"
                signal = max(z_score, s_score)
                alert = EpidemicAlert(
                    alert_type=alert_type,
                    health_area=health_area,
                    district=district,
                    disease_id=disease,
                    cases_observed=recent_count,
                    cases_expected=round(mean_b or mu_c, 2),
                    signal_score=round(signal, 2),
                    period_start=now - timedelta(days=7),
                    period_end=now,
                    status="pending",
                    notes=f"Signal statistique d'anomalie ({alert_type}) détecté. Ratio observé/attendu: {recent_count}/{(mean_b or mu_c):.1f}."
                )
                db.add(alert)
                created_alerts.append(alert)
                
    db.commit()
    return created_alerts
