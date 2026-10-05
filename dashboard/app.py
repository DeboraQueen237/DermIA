import os
import sys
import json
from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import folium
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import st_folium

# Add root directory to python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from backend.app.models.entities import Case, Facility, EpidemicAlert, ExpertReview, HealthWorker
from backend.app.services.surveillance_service import detect_district_anomalies
from backend.app.services.dhis2_service import export_dhis2_datavalueset

# Page configuration
st.set_page_config(
    page_title="DermIA — Surveillance Épidémiologique & Triage",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for high-end aesthetics
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #0D9488 0%, #2563EB 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    
    .sub-title {
        font-size: 1rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(226, 232, 240, 0.2);
        border-radius: 16px;
        padding: 1.2rem;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.05);
        backdrop-filter: blur(8px);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px -4px rgba(0, 0, 0, 0.1);
    }
    
    .badge-urgent {
        background-color: #EF4444;
        color: white;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .badge-priority {
        background-color: #F59E0B;
        color: white;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .badge-standard {
        background-color: #10B981;
        color: white;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
#   FONCTION DE NORMALISATION DES DATES (CORRECTION DU BUG TZ-AWARE)
# ═══════════════════════════════════════════════════════════════════════════
def normaliser_date_naive(valeur):
    """
    Convertit une valeur de date en pandas Timestamp naïf (sans timezone).
    Cela évite les erreurs 'Cannot compare tz-naive and tz-aware datetime-like objects'.
    """
    if valeur is None:
        return None
    try:
        ts = pd.to_datetime(valeur)
        # Si la date est consciente d'un fuseau horaire, on le retire
        if ts.tzinfo is not None:
            ts = ts.tz_localize(None)
        return ts
    except Exception:
        return None


@st.cache_data(ttl=15)
def load_data():
    db = SessionLocal()
    try:
        cases = db.query(Case).all()
        facilities = db.query(Facility).all()
        alerts = db.query(EpidemicAlert).order_by(EpidemicAlert.created_at.desc()).all()
        workers = db.query(HealthWorker).all()
        
        fac_map = {f.id: f for f in facilities}
        
        case_rows = []
        for c in cases:
            fac = fac_map.get(c.facility_id)
            top_d = "Indéterminé"
            score = 0.0
            if c.model_prediction and len(c.model_prediction) > 0:
                top_d = c.model_prediction[0].get("nom", "Indéterminé")
                score = c.model_prediction[0].get("share", 0.0)
            elif c.worker_decision:
                top_d = c.worker_decision

            # ✅ CORRECTION : on normalise la date en naïf dès le chargement
            created_at_naive = normaliser_date_naive(c.created_at)

            case_rows.append({
                "uuid": c.uuid,
                "created_at": created_at_naive,
                "date": created_at_naive.strftime("%Y-%m-%d") if created_at_naive is not None else "Inconnue",
                "week": created_at_naive.strftime("%Y-W%W") if created_at_naive is not None else "Inconnue",
                "urgency": c.urgency,
                "disease": top_d,
                "confidence": c.confidence or 0.0,
                "indeterminate": c.indeterminate,
                "age_group": c.age_group or "Inconnu",
                "sex": c.sex or "Inconnu",
                "body_zone": c.body_zone or "Autre",
                "facility_id": c.facility_id,
                "facility_name": fac.name if fac else "Inconnu",
                "health_area": fac.health_area if fac else "Inconnu",
                "district": fac.district if fac else "Inconnu",
                "region": fac.region if fac else "Inconnu",
                "lat": fac.latitude if fac else None,
                "lon": fac.longitude if fac else None,
            })
            
        df_cases = pd.DataFrame(case_rows)
        
        alert_rows = []
        for a in alerts:
            # ✅ CORRECTION : normalisation des dates d'alertes aussi
            created_at_naive = normaliser_date_naive(a.created_at)
            period_start_naive = normaliser_date_naive(a.period_start)
            period_end_naive = normaliser_date_naive(a.period_end)

            alert_rows.append({
                "id": a.id,
                "alert_type": a.alert_type,
                "district": a.district,
                "health_area": a.health_area,
                "disease_id": a.disease_id,
                "cases_observed": a.cases_observed,
                "cases_expected": a.cases_expected,
                "signal_score": a.signal_score,
                "status": a.status,
                "period": (
                    f"{period_start_naive.strftime('%d/%m')} - {period_end_naive.strftime('%d/%m')}"
                    if period_start_naive is not None and period_end_naive is not None
                    else "Période inconnue"
                ),
                "notes": a.notes or "",
                "created_at": created_at_naive,
            })
        df_alerts = pd.DataFrame(alert_rows)
        
        return df_cases, df_alerts, facilities
    finally:
        db.close()


df_cases, df_alerts, facilities = load_data()

# ── Sidebar Filters ─────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/dermatology.png", width=64)
    st.markdown("## **DermIA Surveillance**")
    st.markdown("*Plateforme Nationale de Triage & Veille Sanitaire*")
    st.divider()
    
    # Filter by District
    all_districts = ["Tous"] + sorted(list(df_cases["district"].unique())) if not df_cases.empty else ["Tous"]
    selected_district = st.selectbox("📍 District Sanitaire", all_districts)
    
    # Filter by Urgency
    all_urgencies = ["Toutes", "urgente", "prioritaire", "standard"]
    selected_urgency = st.selectbox("🚨 Niveau d'Urgence", all_urgencies)
    
    # Filter by Disease
    all_diseases = ["Toutes"] + sorted(list(df_cases["disease"].unique())) if not df_cases.empty else ["Toutes"]
    selected_disease = st.selectbox("🔬 Pathologie", all_diseases)
    
    st.divider()
    st.markdown("### ⚙️ Actions Système")
    if st.button("🔄 Actualiser les données", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
        
    if st.button("⚡ Lancer Détection CUSUM / EARS", use_container_width=True, type="primary"):
        db = SessionLocal()
        try:
            new_alerts = detect_district_anomalies(db, lookback_days=28)
            st.cache_data.clear()
            if new_alerts:
                st.success(f"🔍 {len(new_alerts)} nouveaux signaux faibles détectés !")
            else:
                st.info("Aucune nouvelle anomalie statistique.")
            st.rerun()
        finally:
            db.close()

# Apply filters to dataframe
filtered_df = df_cases.copy()
if selected_district != "Tous":
    filtered_df = filtered_df[filtered_df["district"] == selected_district]
if selected_urgency != "Toutes":
    filtered_df = filtered_df[filtered_df["urgency"] == selected_urgency]
if selected_disease != "Toutes":
    filtered_df = filtered_df[filtered_df["disease"] == selected_disease]

# ── Header & KPI Metrics ───────────────────────────────────────────────────
st.markdown('<div class="main-title">DermIA — Surveillance Épidémiologique & Triage Clinique</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Surveillance en temps réel des maladies tropicales négligées cutanées et dermatoses prioritaires</div>', unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)
total_cases = len(filtered_df)
urgent_cases = len(filtered_df[filtered_df["urgency"] == "urgente"])
priority_cases = len(filtered_df[filtered_df["urgency"] == "prioritaire"])
indet_cases = len(filtered_df[filtered_df["indeterminate"] == True])
active_alerts = len(df_alerts[df_alerts["status"] == "pending"]) if not df_alerts.empty else 0

# ✅ CORRECTION : calcul du delta "cette semaine" avec des dates naïves
seuil_semaine = pd.Timestamp.now() - pd.Timedelta(days=7)
if not filtered_df.empty and "created_at" in filtered_df.columns:
    masque_recent = filtered_df["created_at"].notna() & (filtered_df["created_at"] >= seuil_semaine)
    nouveaux_cas = int(masque_recent.sum())
else:
    nouveaux_cas = 0

with col1:
    st.metric("Total Consultations", total_cases, delta=f"+{nouveaux_cas} cette semaine")
with col2:
    st.metric("Cas Prioritaires / Référence", priority_cases, delta_color="inverse")
with col3:
    st.metric("Urgences Vitales", urgent_cases, delta_color="inverse")
with col4:
    st.metric("Cas Indéterminés (Revue)", indet_cases)
with col5:
    st.metric("Alertes Actives (CUSUM/EARS)", active_alerts, delta="Signaux faibles")

st.markdown("<br>", unsafe_allow_html=True)

# ── Navigation Tabs ─────────────────────────────────────────────────────────
tab_map, tab_surv, tab_clinical, tab_reviews, tab_dhis2 = st.tabs([
    "🗺️ Carte Épidémique & Foyers",
    "📈 Analyse Statistique & CUSUM/EARS",
    "🩺 Profil Clinique & Démographie",
    "🔍 Portail de Revue d'Experts",
    "📋 Export National DHIS2"
])

# ── Tab 1: Map ──────────────────────────────────────────────────────────────
with tab_map:
    st.subheader("Cartographie des Consultations & Foyers Détectés")
    
    map_cases = filtered_df.dropna(subset=["lat", "lon"])
    
    if map_cases.empty:
        st.warning("Aucune coordonnée disponible pour les filtres sélectionnés.")
    else:
        # Center map on Ivory Coast / region
        center_lat = map_cases["lat"].mean()
        center_lon = map_cases["lon"].mean()
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=8, tiles="CartoDB positron")
        
        # Add heatmap layer
        heat_data = [[row["lat"], row["lon"], 1] for _, row in map_cases.iterrows()]
        HeatMap(heat_data, radius=20, blur=15, min_opacity=0.3).add_to(m)
        
        # Add markers with cluster
        marker_cluster = MarkerCluster().add_to(m)
        
        for _, r in map_cases.iterrows():
            color = "#EF4444" if r["urgency"] == "urgente" else ("#F59E0B" if r["urgency"] == "prioritaire" else "#10B981")
            popup_html = f"""
            <div style='font-family: sans-serif; width: 200px;'>
                <h4 style='margin:0 0 5px 0; color:#0F172A;'>{r['disease']}</h4>
                <b>Structure:</b> {r['facility_name']}<br>
                <b>Aire:</b> {r['health_area']} ({r['district']})<br>
                <b>Date:</b> {r['date']}<br>
                <b>Urgence:</b> <span style='color:{color}; font-weight:bold;'>{r['urgency'].upper()}</span><br>
                <b>Zone:</b> {r['body_zone']}
            </div>
            """
            folium.CircleMarker(
                location=[r["lat"], r["lon"]],
                radius=7,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.8,
                popup=folium.Popup(popup_html, max_width=250)
            ).add_to(marker_cluster)
            
        st_folium(m, width="100%", height=550)
        
        # Summary per facility table
        st.markdown("#### Synthèse par Structure Sanitaire")
        fac_summary = map_cases.groupby(["facility_name", "district", "health_area"]).agg(
            total_cases=("uuid", "count"),
            cas_prioritaires=("urgency", lambda x: (x.isin(["prioritaire", "urgente"])).sum()),
            taux_reference=("urgency", lambda x: f"{round(((x.isin(['prioritaire', 'urgente'])).sum() / len(x)) * 100, 1)} %")
        ).reset_index()
        st.dataframe(fac_summary, use_container_width=True, hide_index=True)

# ── Tab 2: Surveillance & Anomalies ─────────────────────────────────────────
with tab_surv:
    st.subheader("Courbes Épidémiques & Détection Précoce de Flambées")
    
    # Weekly epidemic curve
    if not filtered_df.empty:
        weekly = filtered_df.groupby(["week", "disease"]).size().reset_index(name="count")
        fig_curve = px.bar(
            weekly,
            x="week",
            y="count",
            color="disease",
            title="Courbe épidémiologique hebdomadaire par pathologie",
            labels={"week": "Semaine épidémiologique", "count": "Nombre de cas", "disease": "Pathologie"},
            barmode="stack",
            template="plotly_white"
        )
        fig_curve.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_curve, use_container_width=True)
    
    st.markdown("---")
    st.subheader("🚨 Signaux d'Alerte Actifs (Algorithmes CUSUM & EARS C2)")
    
    if df_alerts.empty:
        st.success("✅ Aucun signal d'anomalie statistique détecté pour l'instant.")
    else:
        # Display alerts table
        for _, al in df_alerts.iterrows():
            badge_color = "red" if al["status"] == "pending" else ("orange" if al["status"] == "investigating" else "green")
            with st.expander(f"⚠️ **{al['alert_type']}** : {al['disease_id'].upper()} à {al['health_area']} ({al['district']}) — Score: {al['signal_score']} σ [Statut: {al['status'].upper()}]"):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.write(f"**Période d'évaluation :** {al['period']}")
                    st.write(f"**Cas observés :** {al['cases_observed']} | **Cas attendus (baseline) :** {al['cases_expected']:.1f}")
                    st.write(f"**Note clinique / terrain :** {al['notes']}")
                with col_b:
                    st.write("**Action de Santé Publique :**")
                    new_status = st.selectbox(
                        "Mettre à jour le statut",
                        ["pending", "investigating", "confirmed", "dismissed"],
                        index=["pending", "investigating", "confirmed", "dismissed"].index(al["status"]),
                        key=f"status_{al['id']}"
                    )
                    if st.button("Enregistrer", key=f"btn_{al['id']}"):
                        db = SessionLocal()
                        try:
                            alert_obj = db.query(EpidemicAlert).filter(EpidemicAlert.id == al["id"]).first()
                            if alert_obj:
                                alert_obj.status = new_status
                                db.commit()
                                st.success("Statut mis à jour !")
                                st.cache_data.clear()
                                st.rerun()
                        finally:
                            db.close()

# ── Tab 3: Clinical & Demographics ──────────────────────────────────────────
with tab_clinical:
    st.subheader("Analyse Démographique & Anatomique")
    
    c1, c2 = st.columns(2)
    
    with c1:
        # Disease distribution
        d_counts = filtered_df["disease"].value_counts().reset_index()
        d_counts.columns = ["Maladie", "Cas"]
        fig_pie = px.pie(
            d_counts,
            values="Cas",
            names="Maladie",
            title="Distribution des diagnostics évocateurs",
            hole=0.45,
            template="plotly_white"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with c2:
        # Body zone distribution
        z_counts = filtered_df["body_zone"].value_counts().reset_index()
        z_counts.columns = ["Zone Anatomique", "Cas"]
        fig_bar_z = px.bar(
            z_counts,
            x="Zone Anatomique",
            y="Cas",
            title="Topographie des lésions cutanées",
            color="Cas",
            color_continuous_scale="Teal",
            template="plotly_white"
        )
        st.plotly_chart(fig_bar_z, use_container_width=True)
        
    c3, c4 = st.columns(2)
    with c3:
        # Age group pyramid
        age_counts = filtered_df.groupby(["age_group", "sex"]).size().reset_index(name="Cas")
        fig_age = px.bar(
            age_counts,
            x="age_group",
            y="Cas",
            color="sex",
            barmode="group",
            title="Pyramide des tranches d'âge par sexe",
            category_orders={"age_group": ["0-5", "6-15", "16-45", "45+"]},
            template="plotly_white"
        )
        st.plotly_chart(fig_age, use_container_width=True)
        
    with c4:
        # Urgency triage breakdown
        urg_counts = filtered_df["urgency"].value_counts().reset_index()
        urg_counts.columns = ["Niveau Urgence", "Consultations"]
        fig_urg = px.bar(
            urg_counts,
            x="Niveau Urgence",
            y="Consultations",
            color="Niveau Urgence",
            color_discrete_map={"urgente": "#EF4444", "prioritaire": "#F59E0B", "standard": "#10B981"},
            title="Triage et décisions d'orientation communautaire",
            template="plotly_white"
        )
        st.plotly_chart(fig_urg, use_container_width=True)

# ── Tab 4: Expert Reviews ───────────────────────────────────────────────────
with tab_reviews:
    st.subheader("Portail de Télédermatologie & Revue des Cas Incertains")
    st.info("Ce portail permet aux dermatologues référents de valider les cas étiquetés comme 'Indéterminé' par l'application mobile ou ayant une faible confiance diagnostique.")
    
    indet_cases_df = filtered_df[filtered_df["indeterminate"] == True]
    
    if indet_cases_df.empty:
        st.success("🎉 Tous les cas ont été résolus avec une concordance suffisante !")
    else:
        st.write(f"**{len(indet_cases_df)} cas nécessitent un avis d'expert :**")
        
        selected_case_uuid = st.selectbox(
            "Sélectionner un cas à expertiser",
            indet_cases_df["uuid"].tolist(),
            format_func=lambda u: f"Cas {u[:8]}... — {indet_cases_df.loc[indet_cases_df['uuid']==u, 'health_area'].values[0]} ({indet_cases_df.loc[indet_cases_df['uuid']==u, 'date'].values[0]})"
        )
        
        case_info = indet_cases_df[indet_cases_df["uuid"] == selected_case_uuid].iloc[0]
        
        col_c1, col_c2 = st.columns([1, 1])
        with col_c1:
            st.markdown("### 📋 Fiche Clinique Terrain")
            st.write(f"**UUID :** `{case_info['uuid']}`")
            st.write(f"**Structure Sanitaire :** {case_info['facility_name']} ({case_info['district']})")
            st.write(f"**Tranche d'âge :** {case_info['age_group']} | **Sexe :** {case_info['sex']}")
            st.write(f"**Zone anatomique :** {case_info['body_zone']}")
            st.write(f"**Orientation initiale ASC :** {case_info['disease']}")
            st.write(f"**Niveau de confiance IA :** {case_info['confidence']*100:.1f} % (Abstention déclenchée)")
            
        with col_c2:
            st.markdown("### 🩺 Décision de l'Expert Dermatologue")
            validated_diag = st.selectbox(
                "Diagnostic retenu après revue",
                [
                    "Ulcère de Buruli", "Lèpre (Maladie de Hansen)", "Pian",
                    "Gale (Scabiose)", "Teigne (dermatophytose)", "Impétigo",
                    "Eczéma / Dermatite", "Furoncle / Abcès", "Autre dermatose non ciblée"
                ]
            )
            confidence_level = st.select_slider("Confiance clinique", ["Faible", "Modérée", "Certaine (Haute)"], value="Certaine (Haute)")
            comment = st.text_area("Observations cliniques & Recommandation thérapeutique")
            
            if st.button("Valider et enregistrer l'expertise", type="primary"):
                db = SessionLocal()
                try:
                    case_db = db.query(Case).filter(Case.uuid == selected_case_uuid).first()
                    if case_db:
                        case_db.indeterminate = False
                        case_db.worker_decision = f"Validé par Expert: {validated_diag}"
                        
                        review = ExpertReview(
                            case_uuid=selected_case_uuid,
                            expert_id="USER_SUPERVISOR",
                            validated_label=validated_diag,
                            confidence_level=confidence_level,
                            clinical_comment=comment
                        )
                        db.add(review)
                        db.commit()
                        st.success(f"Cas validé avec succès ({validated_diag}). Intégré au registre d'entraînement continu !")
                        st.cache_data.clear()
                        st.rerun()
                finally:
                    db.close()

# ── Tab 5: DHIS2 Export ─────────────────────────────────────────────────────
with tab_dhis2:
    st.subheader("Interopérabilité & Registre National DHIS2")
    st.markdown("""
    Cette interface génère le paquet d'échange **DHIS2 DataValueSet JSON** standardisé,
    conforme aux directives de notification des maladies transmissibles et MTN de l'OMS.
    """)
    
    # ✅ CORRECTION : utilisation de pd.Timestamp.now() (naïf) au lieu de datetime.now(timezone.utc)
    iso_year, iso_week, _ = pd.Timestamp.now().isocalendar()
    default_period = f"{iso_year}W{iso_week:02d}"
    
    c_p1, c_p2 = st.columns([2, 1])
    with c_p1:
        period_input = st.text_input("Période ISO DHIS2 (Format YYYYWww)", default_period)
    with c_p2:
        export_btn = st.button("Générer l'export DHIS2", type="primary")
        
    db = SessionLocal()
    try:
        dhis2_payload = export_dhis2_datavalueset(db, year_week=period_input)
    finally:
        db.close()
        
    col_d1, col_d2 = st.columns([1, 1])
    with col_d1:
        st.markdown("#### 📄 Aperçu du Paquet DHIS2 DataValueSet")
        st.json(dhis2_payload)
        
    with col_d2:
        st.markdown("#### 💾 Téléchargements & Transmissions")
        st.download_button(
            label="📥 Télécharger le fichier JSON DHIS2",
            data=json.dumps(dhis2_payload, indent=2, ensure_ascii=False),
            file_name=f"dhis2_export_{period_input}.json",
            mime="application/json",
            use_container_width=True
        )
        
        # CSV Export
        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger le Registre Épidémiologique (CSV)",
            data=csv_data,
            file_name=f"registre_dermia_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        st.markdown("""
        > **Sécurité & Conformité Éthique :**
        > Conformément au cadre de gouvernance des données de santé, ce paquet contient
        > **exclusivement des agrégats statistiques** anonymisés par structure de santé.
        > Aucune donnée nominative de patient n'est exportée.
        """)