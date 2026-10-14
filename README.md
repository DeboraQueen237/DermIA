# 🔬 DermIA — Triage Dermatologique Intelligent & Surveillance Épidémiologique

> **Plateforme d'aide au triage des maladies de peau tropicales et dermatoses prioritaires, 100 % opérationnelle hors ligne sur smartphone, complétée par un système de surveillance épidémiologique (CUSUM/EARS) et d'interopérabilité nationale (DHIS2).**

![Statut](https://img.shields.io/badge/statut-prototype--recherche-orange)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.14-blue)
![FastAPI](https://img.shields.io/badge/backend-FastAPI%20REST-009688)
![Streamlit](https://img.shields.io/badge/dashboard-Streamlit-FF4B4B)
![Flutter](https://img.shields.io/badge/mobile-Flutter%203-02569B)
![PyTorch](https://img.shields.io/badge/ML-PyTorch%20%2B%20ONNX-EE4C2C)
![Tests](https://img.shields.io/badge/tests-100%25%20passed-brightgreen)

> ⚠️ **Avertissement médical & éthique :** DermIA est un dispositif d'aide à la décision clinique et au triage communautaire. Il **ne pose pas de diagnostic médical définitif et ne se substitue pas à l'avis d'un médecin qualifié**. Il applique un principe d'abstention stricte (« je ne sais pas ») en cas d'ambiguïté ou de faible confiance, avec orientation vers un spécialiste.

---

## 📊 État du Projet (Octobre 2026)

### ✅ Réalisé et fonctionnel

| Composant | Statut | Détails |
| :--- | :--- | :--- |
| **Backend FastAPI** | ✅ Production-ready | JWT, RBAC, sync idempotente, DHIS2 |
| **Dashboard Streamlit** | ✅ Production-ready | 5 modules, CUSUM/EARS, portail experts |
| **Base de connaissances** | ✅ Validée par schéma | 8 fiches MTN, remèdes traditionnels OMS |
| **App mobile Flutter** | ✅ Prototype avancé | UI premium, consentement, contrôle qualité |
| **Modèle IA unifié** | ✅ Entraîné | EfficientNet-B3, 8 classes (voir ci-dessous) |
| **Export mobile** | ✅ ONNX 43 Mo | Intégré dans Flutter via onnxruntime |

### 📈 Métriques du modèle déployé

**Modèle unifié EfficientNet-B3** — 10 024 images, 8 classes :

| Métrique | Valeur |
| :--- | :--- |
| **Macro-F1 (test)** | 0.7246 |
| **Top-3 accuracy** | **98.0%** |
| **ECE (calibration)** | 0.0269 |
| **Rappel lèpre** | **1.000** (100% des cas détectés) |
| **Rappel mélanome** | 0.468 |

**Classes détectées** : `lepre` + 7 classes HAM10000 (melanome, naevus, carcinome_basal, keratose_actinique, keratose_benigne, lesion_vasculaire, dermatofibrome).

### 🔄 En cours

- Extension du modèle aux 7 autres MTN (Buruli, Pian, Gale, Teigne, Impétigo, Eczéma, Furoncle)
- Enrichissement de la base de connaissances avec les 7 classes HAM10000

### 🎯 Prévu (Roadmap)

Voir [`docs/ROADMAP.md`](docs/ROADMAP.md) pour la feuille de route détaillée.

**Court terme** :
- Collecte de données MTN locales (partenariat Hôpital Central de Yaoundé)
- Test terrain avec 5 ASC pilotes

**Moyen terme** :
- Entraînement du modèle FiLM multimodal (architecture documentée mais non entraînée)
- Validation clinique sur 500 patients

**Long terme** :
- Extension à la cosmétique personnalisée (DermIA Care)
- Publication scientifique

---

## 📑 Table des Matières

1. [Vue d'Ensemble & Innovations](#-vue-densemble--innovations)
2. [Architecture du Système](#-architecture-du-système)
3. [Composants Réalisés](#-composants-réalisés)
4. [Pipeline d'IA : Réalisé vs Prévu](#-pipeline-dia--réalisé-vs-prévu)
5. [Démarrage Rapide](#-démarrage-rapide)
6. [Tests Automatisés](#-tests-automatisés)
7. [Limites Actuelles](#-limites-actuelles)
8. [Gouvernance, Éthique & Données de Santé](#-gouvernance-éthique--données-de-santé)

---

## 🌟 Vue d'Ensemble & Innovations

En Afrique subsaharienne et dans les zones tropicales, les Maladies Tropicales Négligées (MTN) cutanées (**Ulcère de Buruli, Lèpre, Pian, Gale**) et les dermatoses courantes (**Teigne, Impétigo, Eczéma, Furoncles**) affectent gravement les populations rurales éloignées des centres spécialisés.

DermIA résout ce défi en combinant :

- **Une application mobile 100 % hors ligne** dotée d'une ergonomie moderne pour les Agents de Santé Communautaires (ASC).
- **Un modèle d'IA embarqué** (EfficientNet-B3, export ONNX) détectant la lèpre et 7 classes de lésions cutanées (dépistage cancer de peau).
- **Un moteur de triage déterministe** à base de règles cliniques pondérées couvrant 8 pathologies MTN.
- **Un protocole de synchronisation idempotent et résilient** permettant d'ingérer les cas dès qu'une connexion réseau est détectée sans créer de doublons.
- **Un moteur de surveillance épidémiologique avancé** basé sur les algorithmes statistiques **CUSUM** et **CDC EARS C2** pour détecter précocement les flambées locales.
- **Une interopérabilité directe avec le SNIS / DHIS2** via l'export officiel au format *DataValueSet*.
- **Un audit d'équité algorithmique rigoureux** sur les phototypes de Fitzpatrick (I à VI).

---

## 🏗️ Architecture du Système

```mermaid
flowchart TB
    subgraph Terrain["📱 Smartphone ASC (Terrain - 100% Hors Ligne)"]
        A[Capture Photo + Contrôle Flou/Lumière] --> M[Inférence ONNX + Abstention]
        Q[Questionnaire Clinique Adaptatif] --> R[Moteur de Règles Déterministe]
        M --> R
        R --> KB[(Base de Connaissances Locale)]
        R --> D[(SQLite Chiffré SQLCipher)]
    end

    D -->|"Sync idempotente (UUID client)"| S["⚡ API FastAPI (REST + JWT)"]

    subgraph Serveur["🖥️ Serveur Central & Surveillance"]
        S --> P[(PostgreSQL + PostGIS / SQLite)]
        P --> SURV[Algorithmes CUSUM & EARS C2]
        SURV --> DASH[📊 Tableau de Bord Streamlit]
        P --> DHIS2[📋 Export Officiel DHIS2]
        P -->|Cas Indéterminés| EXP[🩺 Portail Revue Experts]
        EXP -->|Données Validées| RETRAIN[🔄 Ré-entraînement PyTorch]
        RETRAIN -->|Modèles & KB Signés OTA| S
    end

    S -.->|Mises à jour OTA| Terrain