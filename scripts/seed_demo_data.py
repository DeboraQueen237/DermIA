import os
import sys
import uuid
import random
from datetime import datetime, timedelta, timezone

# Ensure UTF-8 stdout on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure project root in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal, Base, engine
from backend.app.models.entities import HealthWorker, Facility, Case, EpidemicAlert
from backend.app.core.security import get_password_hash

def seed_database():
    print("🌱 Initialisation des tables et alimentation des données de démonstration...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # 1. Structures de santé (District & Région en Côte d'Ivoire)
    facilities_data = [
        {"id": "FAC_SP_01", "name": "CSRéf San Pedro Centre", "health_area": "Bardot", "district": "San Pedro", "region": "Bas-Sassandra", "lat": 4.7561, "lon": -6.6433},
        {"id": "FAC_SP_02", "name": "CSU Grand-Béréby", "health_area": "Béréby Ouest", "district": "San Pedro", "region": "Bas-Sassandra", "lat": 4.6472, "lon": -6.9389},
        {"id": "FAC_SB_01", "name": "Hôpital Général Soubré", "health_area": "Soubré Urbain", "district": "Soubré", "region": "Nawa", "lat": 5.7856, "lon": -6.5931},
        {"id": "FAC_SB_02", "name": "CSCOM Méagui", "health_area": "Méagui Nord", "district": "Soubré", "region": "Nawa", "lat": 5.4050, "lon": -6.5542},
        {"id": "FAC_MN_01", "name": "CHR Man", "health_area": "Man Centre", "district": "Man", "region": "Tonkpi", "lat": 7.4125, "lon": -7.5538},
        {"id": "FAC_BK_01", "name": "CHU Bouaké", "health_area": "Air France", "district": "Bouaké", "region": "Gbêkê", "lat": 7.6903, "lon": -5.0300},
        {"id": "FAC_DL_01", "name": "CHR Daloa", "health_area": "Lobia", "district": "Daloa", "region": "Haut-Sassandra", "lat": 6.8774, "lon": -6.4502},
    ]
    
    for f in facilities_data:
        existing = db.query(Facility).filter(Facility.id == f["id"]).first()
        if not existing:
            fac = Facility(
                id=f["id"],
                name=f["name"],
                health_area=f["health_area"],
                district=f["district"],
                region=f["region"],
                latitude=f["lat"],
                longitude=f["lon"]
            )
            db.add(fac)
    
    db.commit()
    print(f"✅ {len(facilities_data)} structures de santé enregistrées.")
    
    # 2. Utilisateurs de test
    users_data = [
        {"id": "USER_ADMIN", "email": "admin@dermia.org", "name": "Dr. Amani Kouassi", "role": "admin", "fac": "FAC_SP_01"},
        {"id": "USER_SUPERVISOR", "email": "expert@dermia.org", "name": "Dr. Fatou Traoré (Dermatologue)", "role": "supervisor", "fac": "FAC_SP_01"},
        {"id": "USER_ASC_01", "email": "asc.yao@dermia.org", "name": "Yao Konan (ASC)", "role": "asc", "fac": "FAC_SP_01"},
        {"id": "USER_ASC_02", "email": "asc.koffi@dermia.org", "name": "Koffi Michel (ASC)", "role": "asc", "fac": "FAC_SB_01"},
    ]
    
    for u in users_data:
        existing = db.query(HealthWorker).filter(HealthWorker.email == u["email"]).first()
        if not existing:
            w = HealthWorker(
                id=u["id"],
                email=u["email"],
                hashed_password=get_password_hash("dermia2026"),
                full_name=u["name"],
                role=u["role"],
                facility_id=u["fac"],
                active=True
            )
            db.add(w)
            
    db.commit()
    print("✅ Utilisateurs de démonstration créés (mot de passe: 'dermia2026').")
    
    # 3. Génération de cas cliniques réalistes sur les 30 derniers jours
    diseases = [
        {"id": "buruli", "nom": "Ulcère de Buruli", "urg": "prioritaire", "zones": ["jambes", "bras"]},
        {"id": "gale", "nom": "Gale", "urg": "standard", "zones": ["mains", "corps", "aisselles"]},
        {"id": "teigne", "nom": "Teigne (dermatophytie)", "urg": "standard", "zones": ["tete", "corps"]},
        {"id": "pian", "nom": "Pian", "urg": "prioritaire", "zones": ["jambes", "pieds"]},
        {"id": "impetigo", "nom": "Impétigo", "urg": "standard", "zones": ["visage", "jambes"]},
        {"id": "eczema", "nom": "Eczéma / Dermatite", "urg": "standard", "zones": ["bras", "jambes", "visage"]},
        {"id": "furoncle", "nom": "Furoncle / Abcès", "urg": "standard", "zones": ["fesses", "cuisses", "nuque"]},
        {"id": "lepre", "nom": "Lèpre", "urg": "prioritaire", "zones": ["visage", "bras", "dos"]}
    ]
    
    now = datetime.now(timezone.utc)
    cases_count = db.query(Case).count()
    
    if cases_count < 20:
        print("Génération de 85 cas cliniques répartis sur 4 semaines...")
        random.seed(42)
        
        for i in range(85):
            d = random.choice(diseases)
            # Simuler un cluster épidémique de gale et de buruli à San Pedro
            if i % 3 == 0:
                fac = facilities_data[0] # San Pedro
                d = random.choice([diseases[0], diseases[1]]) # Buruli ou Gale
            else:
                fac = random.choice(facilities_data)
                
            days_ago = random.randint(0, 28)
            case_date = now - timedelta(days=days_ago, hours=random.randint(1, 12))
            
            top_hypotheses = [
                {"id": d["id"], "nom": d["nom"], "score": round(random.uniform(5.0, 9.0), 1), "share": round(random.uniform(0.65, 0.92), 2)},
                {"id": "autre", "nom": "Autre diagnostic", "score": round(random.uniform(1.0, 2.5), 1), "share": 0.15}
            ]
            
            is_indet = random.random() < 0.12 # 12% indeterminate cases for expert review
            
            case = Case(
                uuid=str(uuid.uuid4()),
                worker_id="USER_ASC_01" if fac["id"].startswith("FAC_SP") else "USER_ASC_02",
                facility_id=fac["id"],
                created_at=case_date,
                synced_at=case_date + timedelta(minutes=random.randint(5, 120)),
                age_group=random.choice(["0-5", "6-15", "16-45", "45+"]),
                sex=random.choice(["M", "F"]),
                body_zone=random.choice(d["zones"]),
                answers={
                    "aspect": random.choice(["ulcère", "nodule", "tache", "papule"]),
                    "demangeaison": "oui" if d["id"] == "gale" else "non",
                    "duree": random.choice(["court", "moyen", "long"])
                },
                model_version="1.0.0-mobilenetv3-quant",
                model_prediction=top_hypotheses,
                confidence=round(random.uniform(0.72, 0.98), 2) if not is_indet else 0.45,
                indeterminate=is_indet,
                worker_decision=f"Orientation {d['nom']}" if not is_indet else "Indéterminé - transmis pour revue",
                urgency=d["urg"],
                notes="Cas dépisté lors de la visite communautaire."
            )
            db.add(case)
            
        db.commit()
        print("✅ 85 cas cliniques synthétiques générés.")
        
    # 4. Générer des alertes de surveillance épidémique
    alert_count = db.query(EpidemicAlert).count()
    if alert_count == 0:
        a1 = EpidemicAlert(
            id=str(uuid.uuid4()),
            alert_type="EARS_C2",
            health_area="Bardot",
            district="San Pedro",
            disease_id="gale",
            cases_observed=18,
            cases_expected=4.2,
            signal_score=3.85,
            period_start=now - timedelta(days=7),
            period_end=now,
            status="pending",
            notes="Augmentation inhabituelle de cas de gale signalés dans le secteur scolaire Bardot (Ratio 4.3x)."
        )
        a2 = EpidemicAlert(
            id=str(uuid.uuid4()),
            alert_type="CUSUM",
            health_area="Méagui Nord",
            district="Soubré",
            disease_id="buruli",
            cases_observed=5,
            cases_expected=1.1,
            signal_score=3.20,
            period_start=now - timedelta(days=14),
            period_end=now,
            status="investigating",
            notes="Accumulation de nodules et ulcères indolores près des campements rizicoles de la rivière Sassandra."
        )
        db.add(a1)
        db.add(a2)
        db.commit()
        print("✅ 2 alertes épidémiologiques initialisées.")
        
    db.close()
    print("🚀 Base de données prête pour le backend et le tableau de bord !")

if __name__ == "__main__":
    seed_database()
