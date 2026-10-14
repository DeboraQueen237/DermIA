\# 🗺️ Roadmap DermIA



> Feuille de route du projet, mise à jour Octobre 2026.



\## ✅ Phase 1 : Prototype (Terminée - Octobre 2026)



| Composant | Statut | Détails |

| :--- | :--- | :--- |

| Backend FastAPI | ✅ | JWT, RBAC, sync idempotente, DHIS2 |

| Dashboard Streamlit | ✅ | 5 modules, CUSUM/EARS |

| Base de connaissances | ✅ | 8 fiches MTN |

| App mobile Flutter | ✅ | UI premium, offline-first |

| Modèle EfficientNet-B3 | ✅ | 8 classes, ONNX 43 Mo |



\*\*Métriques clés\*\* :

\- Rappel lèpre : 1.000

\- Top-3 accuracy : 98.0%

\- ECE : 0.027



\---



\## 🔄 Phase 2 : Consolidation (En cours - Q4 2026)



\### Objectifs



1\. \*\*Étendre le modèle aux 7 autres MTN\*\*

&#x20;  - Collecter des datasets Buruli, Pian, Gale, Teigne, Impétigo, Eczéma, Furoncle

&#x20;  - Entraîner un modèle MTN unifié (8 classes)



2\. \*\*Enrichir la base de connaissances\*\*

&#x20;  - Ajouter les 7 classes HAM10000 (melanome, naevus, etc.)

&#x20;  - Documenter le dépistage du cancer de la peau



3\. \*\*Tests terrain\*\*

&#x20;  - Former 5 ASC pilotes à Yaoundé

&#x20;  - Tester avec 50 patients réels

&#x20;  - Recueillir les retours



\### Livrables

\- Modèle MTN unifié (ONNX)

\- Base de connaissances 15 classes

\- Rapport de test terrain



\---



\## 🎯 Phase 3 : Validation Clinique (2027)



\### Objectifs



1\. \*\*Validation externe\*\*

&#x20;  - Partenariat Hôpital Central de Yaoundé

&#x20;  - 500 patients

&#x20;  - Comparaison avec dermatologues



2\. \*\*Modèle FiLM multimodal\*\*

&#x20;  - Entraîner l'architecture documentée (`fusion\_model.py`)

&#x20;  - Fusion image + questionnaire clinique

&#x20;  - Audit d'équité Fitzpatrick



3\. \*\*Publication scientifique\*\*

&#x20;  - Soumission à \*The Lancet Digital Health\* ou \*JAAD\*



\### Livrables

\- Étude clinique publiée

\- Modèle FiLM validé

\- Certification CE (dispositif médical)



\---



\## 🚀 Phase 4 : Déploiement National (2028)



\### Objectifs



1\. \*\*Déploiement à grande échelle\*\*

&#x20;  - 100 ASC dans 5 régions du Cameroun

&#x20;  - Partenariat Ministère de la Santé



2\. \*\*Extension Afrique\*\*

&#x20;  - Adaptation aux contextes locaux (Sénégal, Côte d'Ivoire, RDC)



3\. \*\*Cosmétique personnalisée (DermIA Care)\*\*

&#x20;  - Gamme de produits adaptés aux peaux africaines

&#x20;  - Validation scientifique



\### Livrables

\- 10 000 utilisateurs actifs

\- Gamme DermIA Care lancée

\- 5 pays couverts



\---



\## 📊 Indicateurs de Succès



| Phase | Indicateur | Cible |

| :--- | :--- | :--- |

| 1 | Top-3 accuracy | > 95% ✅ |

| 2 | Rappel lèpre | > 90% ✅ (100% actuel) |

| 3 | Rappel mélanome | > 80% |

| 3 | Validation clinique | 500 patients |

| 4 | Utilisateurs actifs | 10 000 |

| 4 | Pays couverts | 5 |



\---



\## 🎯 Priorités Actuelles (Octobre 2026)



1\. ⭐ \*\*Collecte de données MTN locales\*\* (priorité absolue)

2\. ⭐ \*\*Test terrain avec 5 ASC pilotes\*\*

3\. Amélioration du rappel mélanome (0.468 → 0.70+)

4\. Enrichissement de la base de connaissances

