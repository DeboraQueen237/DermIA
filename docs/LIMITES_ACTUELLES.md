\# ⚠️ Limites Actuelles de DermIA



> Document de transparence scientifique — Octobre 2026.



\## 1. Couverture MTN partielle



\*\*Constat\*\* : La base de connaissances couvre 8 MTN, mais le modèle d'IA d'image ne détecte \*\*que la lèpre\*\* parmi celles-ci.



| MTN | Détection IA | Détection questionnaire |

| :--- | :--- | :--- |

| Lèpre | ✅ Oui | ✅ Oui |

| Ulcère de Buruli | ❌ Non | ✅ Oui |

| Pian | ❌ Non | ✅ Oui |

| Gale | ❌ Non | ✅ Oui |

| Teigne | ❌ Non | ✅ Oui |

| Impétigo | ❌ Non | ✅ Oui |

| Eczéma | ❌ Non | ✅ Oui |

| Furoncle | ❌ Non | ✅ Oui |



\*\*Raison\*\* : Absence de datasets publics pour les 7 autres MTN.



\*\*Impact\*\* : Le diagnostic repose principalement sur le questionnaire clinique pour 7 pathologies.



\*\*Plan\*\* : Collecter des données locales via le partenariat avec l'Hôpital Central de Yaoundé.



\---



\## 2. Biais de dataset



\*\*Constat\*\* : Le modèle a été entraîné majoritairement sur HAM10000 (9 577 images, \*\*majoritairement peaux claires\*\*).



| Dataset | Images | Représentation peaux foncées |

| :--- | :--- | :--- |

| HAM10000 | 9 577 | \~13% (Fitzpatrick V-VI) |

| AI-Leprosy | 614 | Inconnue (non documentée) |



\*\*Impact\*\* : Risque de biais algorithmique sur les peaux foncées africaines.



\*\*Plan\*\* : Collecter des données locales + audit d'équité systématique.



\---



\## 3. Validation clinique externe



\*\*Constat\*\* : Aucune validation clinique externe n'a été réalisée. Les performances rapportées sont issues de tests sur données publiques.



\*\*Impact\*\* : Les métriques (Top-3 98%, rappel lèpre 1.00) sont sur données académiques, non représentatives de la réalité du terrain camerounais.



\*\*Plan\*\* : Étude clinique sur 500 patients à l'Hôpital Central de Yaoundé (Phase 3).



\---



\## 4. Modèle FiLM multimodal non entraîné



\*\*Constat\*\* : L'architecture FiLM (MobileNetV3 + Encodeur clinique + Modulation) est documentée dans `ml/src/fusion\_model.py` mais \*\*n'a jamais été entraînée\*\*.



\*\*Réalité\*\* : Le modèle déployé est un EfficientNet-B3 \*\*image-only\*\*.



\*\*Impact\*\* : Le questionnaire clinique ne contribue pas à l'apprentissage du modèle (il est utilisé uniquement dans le moteur de triage).



\*\*Plan\*\* : Entraîner le modèle FiLM une fois les datasets MTN collectés (Phase 3).



\---



\## 5. Rappel faible sur certaines classes



\*\*Constat\*\* : Certaines classes ont un rappel faible :



| Classe | Rappel | Raison |

| :--- | :--- | :--- |

| dermatofibrome | 0.375 | Seulement 110 images |

| mélanome | 0.468 | Confusion avec naevus |

| kératose\_actinique | 0.525 | Confusion avec kératose\_bénigne |



\*\*Impact\*\* : Le dépistage du mélanome est insuffisant pour un usage clinique.



\*\*Plan\*\* :

\- Collecter plus d'images de ces classes

\- Ajuster les seuils de décision cliniquement

\- Utiliser un ensemble de modèles



\---



\## 6. Test terrain non réalisé



\*\*Constat\*\* : L'application n'a pas été testée par des agents de santé communautaires en conditions réelles.



\*\*Impact\*\* : Ergonomie, rapidité, acceptabilité non validées.



\*\*Plan\*\* : Test pilote avec 5 ASC à Yaoundé (Phase 2).



\---



\## 7. Performance sur mobile non mesurée



\*\*Constat\*\* : Le temps d'inférence du modèle ONNX (43 Mo) sur smartphone n'a pas été mesuré.



\*\*Impact\*\* : Risque de latence sur téléphones d'entrée de gamme.



\*\*Plan\*\* : Benchmark sur 5 modèles de smartphones (Android 10-14).



\---



\## 🎯 Résumé



\*\*DermIA est un prototype de recherche\*\*, pas un dispositif médical validé. Les résultats actuels sont prometteurs mais nécessitent :



1\. Plus de données MTN

2\. Validation clinique externe

3\. Test terrain réel

4\. Audit d'équité approfondi



\*\*Ces limites sont documentées pour garantir la transparence scientifique et éthique.\*\*

