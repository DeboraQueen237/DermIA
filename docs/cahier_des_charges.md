# Cahier des charges - DermIA

Version 1.0 - document vivant, à réviser à chaque fin de phase.

---

## 1. Contexte et justification

Les maladies de peau tropicales négligées (MTN cutanées : ulcère de Buruli, lèpre, pian, gale, mycétome…) et les dermatoses courantes (teigne, impétigo, mycoses) pèsent lourdement sur les zones rurales du Cameroun. Les spécialistes sont rares et concentrés dans les grandes villes ; les agents de santé communautaires (ASC) sont en première ligne mais disposent de peu d'outils d'aide à la décision.

Un travail pilote publié en 2023 sur cinq MTN cutanées (ulcère de Buruli, lèpre, mycétome, gale, pian) a montré la faisabilité de modèles de vision sur peaux foncées, avec 1 709 images issues de 506 patients de Côte d'Ivoire et du Ghana (Yotsu et al., PLoS NTD, 2023). L'étude souligne aussi que les travaux sur peau foncée restent peu nombreux : **le goulot d'étranglement est la donnée, pas l'algorithme.**

> À sourcer avant diffusion : le nombre de dermatologues au Cameroun (l'ancienne version annonçait « moins de 50 »), les prévalences par maladie et par région, les protocoles nationaux en vigueur.

## 2. Problématique

Comment doter les ASC d'un outil numérique fonctionnant **sans réseau**, capable d'**orienter** vers la bonne conduite à tenir (soins de base, surveillance ou référence urgente) pour les maladies de peau les plus fréquentes et les plus graves, tout en alimentant une **surveillance épidémiologique** respectueuse de la vie privée et des savoirs locaux ?

## 3. Objectifs

**Objectif général.** Améliorer la détection précoce et l'orientation des patients atteints de maladies de peau tropicales au Cameroun grâce à une plateforme mobile hors ligne, inclusive et validée cliniquement.

**Objectifs spécifiques (SMART, cibles provisoires à confirmer après l'audit des données de la phase 0).**

| # | Objectif | Indicateur | Cible provisoire |
|---|---|---|---|
| O1 | Modèle de triage fiable sur peaux foncées | Sensibilité pour ulcère de Buruli et lèpre | ≥ 90 % (avec intervalle de confiance publié) |
| O2 | Pas de performance dégradée selon la peau | Écart de F1 macro entre Fitzpatrick IV-VI et I-III | ≤ 5 points |
| O3 | Exécution mobile hors ligne | Taille modèle ; latence sur téléphone milieu de gamme | < 25 Mo ; < 500 ms |
| O4 | Prudence du système | Taux de rejet correct des images hors périmètre ou de mauvaise qualité | ≥ 90 % |
| O5 | Base de connaissances validée | Fiches relues par ≥ 2 cliniciens | 100 % des fiches du MVP |
| O6 | Adoption | ASC utilisant l'outil sur ≥ 80 % de leurs cas cutanés (pilote) | ≥ 80 % |
| O7 | Détection précoce | Réduction du délai entre premier contact et référence | à mesurer en pilote (cible : -50 %) |
| O8 | Surveillance | Délai de détection d'un agrégat simulé | à définir en phase 4 |

> Remarque : l'ancien objectif « > 90 % de précision sur 10+ maladies » est remplacé par des cibles **par classe et par sous-groupe**. Une précision globale masque les erreurs sur les maladies rares mais graves, qui sont justement les plus importantes.

## 4. Parties prenantes et utilisateurs

| Acteur | Besoin | Rôle |
|---|---|---|
| ASC | Outil rapide, fiable, hors ligne, simple | Utilisateur principal |
| Infirmiers, médecins de centres de santé | Aide à la décision, confirmation | Utilisateur secondaire, référents |
| Dermatologues / experts | Relecture des cas incertains | Validateurs, producteurs de labels |
| Programmes nationaux (MTN, lèpre, Buruli), districts | Données de surveillance | Utilisateurs du tableau de bord |
| Patients et communautés | Diagnostic précoce, respect de la vie privée | Bénéficiaires |
| Tradipraticiens, ethnobotanistes | Reconnaissance, partage des bénéfices | Détenteurs de savoirs |
| Comité d'éthique, autorité de protection des données | Conformité | Garants |

## 5. Périmètre

### 5.1 Principe de phasage

L'ancienne version couvrait six modules et six profils en 14 mois. C'est trop pour un premier jalon. Le périmètre est donc découpé en **MVP** (utile seul) puis extensions.

| Module | MVP (phases 0-3) | Extension |
|---|---|---|
| M1 App mobile hors ligne | Oui | Suivi de lésion, langues locales (phase 6) |
| M2 Modèle d'IA multimodal | Oui | Explicabilité, apprentissage avec experts |
| M3 Base de connaissances | Soins modernes + référence | Savoirs traditionnels (phase 5) |
| M4 Backend et synchronisation | Non (export manuel possible) | Oui, phase 4 |
| M5 Tableau de bord | Non | Oui, phase 4 |
| M6 Documentation et formation | Oui | Continue |

### 5.2 Maladies couvertes (hiérarchisées par intérêt de santé publique)

| Niveau | Classes | Justification |
|---|---|---|
| A - MTN prioritaires | Ulcère de Buruli, lèpre, pian, gale ; mycétome si données suffisantes | Gravité, handicap évitable, programmes nationaux |
| B - Dermatoses courantes | Teigne, impétigo, mycoses superficielles, furoncle/abcès, dermatite/eczéma | Fréquence, traitement simple en première ligne |
| C - Faible priorité | Psoriasis, vitiligo | Peu urgents, non tropicaux ; ajoutés seulement si données disponibles |
| Classes « garde-fous » | **Peau saine**, **Autre ulcère ou plaie chronique** (diagnostic différentiel du Buruli), **Hors périmètre / indéterminé** | Évitent de forcer un diagnostic sur ce que le modèle ne connaît pas |

Le MVP vise les niveaux A et B et les trois classes garde-fous.

### 5.3 Hors périmètre

- Diagnostic définitif, prescription de médicaments avec posologie générée automatiquement, remplacement du spécialiste.
- Cancers cutanés (mélanome, etc.) et urgences vitales : l'application affiche des **signes d'alerte** et oriente, sans prétendre les diagnostiquer.
- Dépistage de maladies systémiques à partir de la peau : axe de **recherche** (phase ultérieure), non inclus dans le produit tant qu'aucune preuve et validation clinique n'existent.

## 6. Exigences fonctionnelles

Priorité : **M** = Must, **S** = Should, **C** = Could.

### 6.1 Application mobile

| ID | Exigence | Prio |
|---|---|---|
| F-M01 | Écran de consentement du patient (oral ou écrit, enregistré), avec option distincte « usage pour la recherche » | M |
| F-M02 | Capture photo guidée : gabarit de cadrage, aide à la distance, vérification du flou et de l'exposition avant analyse | M |
| F-M03 | Questionnaire clinique court et adaptatif (durée, douleur, démangeaisons, perte de sensibilité, atteinte du foyer, fièvre, localisation corporelle) | M |
| F-M04 | Inférence locale (photo + réponses) renvoyant les 3 hypothèses les plus probables avec confiance calibrée | M |
| F-M05 | Rejet explicite : « Image inexploitable » ou « Cas hors de ma connaissance : référer » | M |
| F-M06 | Affichage de la conduite à tenir : niveau d'urgence, signes d'alerte, premiers soins, critères de référence | M |
| F-M07 | Historique des cas chiffré, recherche par identifiant anonyme | M |
| F-M08 | Interface FR/EN, icônes, grandes polices, usage à une main | M |
| F-M09 | Aide audio des consignes (voix) | S |
| F-M10 | Suivi d'une lésion dans le temps (comparaison de photos, mesure avec marqueur de référence) | S |
| F-M11 | Étalon de référence (autocollant de couleur/échelle) pour calibrer la couleur et la taille | S |
| F-M12 | Rappels de suivi et de rendez-vous de référence | S |
| F-M13 | Langues locales et pidgin | C |
| F-M14 | Transfert de cas entre téléphones sans Internet (Wi-Fi Direct / Bluetooth / fichier chiffré) | C |
| F-M15 | Explicabilité visuelle (zones qui ont pesé dans la décision) | C |

### 6.2 Modèle d'IA

| ID | Exigence | Prio |
|---|---|---|
| F-I01 | Classification multi-classes selon le §5.2 | M |
| F-I02 | Fusion image + données cliniques | M |
| F-I03 | Calibration des probabilités (ex. température/Platt) et mesure de l'erreur de calibration | M |
| F-I04 | Détection hors distribution / seuil d'abstention | M |
| F-I05 | Évaluation par classe, par type de peau, par source de données et par appareil photo | M |
| F-I06 | Versionnement du modèle, des données et de la configuration | M |
| F-I07 | Quantification (int8 ou float16) et benchmark sur téléphones cibles | M |
| F-I08 | Mise à jour du modèle par paquet signé | S |
| F-I09 | Distillation d'un grand modèle (enseignant) vers un modèle mobile | S |

### 6.3 Base de connaissances

| ID | Exigence | Prio |
|---|---|---|
| F-K01 | Fiches maladies structurées : signes, diagnostics différentiels, urgence, conduite à tenir, références | M |
| F-K02 | Soins modernes alignés sur les protocoles nationaux et OMS, **règles déterministes validées** (pas de texte généré à la volée) | M |
| F-K03 | Chaque contenu porte : source, date, relecteurs, version | M |
| F-K04 | Avertissements et limites visibles sur chaque écran de résultat | M |
| F-K05 | Remèdes traditionnels avec **niveau de preuve** (A à D), contre-indications et message « ne retarde pas la référence » | S (phase 5) |
| F-K06 | Conseils de prévention (hygiène, eau, habitat, contacts) par maladie | S |

### 6.4 Backend, synchronisation, tableau de bord (phase 4)

| ID | Exigence | Prio |
|---|---|---|
| F-B01 | API REST sécurisée, authentification des ASC, rôles (ASC, superviseur, district, admin) | M |
| F-B02 | Synchronisation incrémentale par file d'envoi, idempotente, tolérante aux coupures | M |
| F-B03 | Anonymisation et généralisation de la localisation avant stockage central | M |
| F-B04 | Stockage PostgreSQL + PostGIS | M |
| F-B05 | File de revue : cas incertains envoyés à un spécialiste, retour du label validé | S |
| F-B06 | Export agrégé vers DHIS2 | S |
| F-D01 | Carte des cas, courbes de tendance, filtres par maladie et par zone | M |
| F-D02 | Alertes de signaux : détection d'agrégats spatio-temporels et d'anomalies, avec statut « à confirmer par un humain » | M |
| F-D03 | Prévision avec covariables (pluie, température) lorsque ≥ 12 mois de données existent | C |
| F-D04 | Export de rapports (PDF/CSV) | S |

## 7. Exigences non fonctionnelles

| Domaine | Exigence |
|---|---|
| Plateforme | Android 8.0+, 2 Go de RAM, appareil photo ≥ 8 Mpx |
| Performance | Inférence < 500 ms ; démarrage < 5 s ; consommation modérée de batterie |
| Taille | Modèle < 25 Mo (objectif), APK < 100 Mo |
| Hors ligne | 100 % des fonctions de capture, analyse, conseils et historique disponibles sans réseau |
| Sécurité | Chiffrement au repos (AES-256 via SQLCipher), clés dans l'Android Keystore, TLS 1.2+ en transit, verrouillage de l'app, effacement à distance ou local |
| Vie privée | Minimisation, pseudonymisation, suppression EXIF/GPS, droit d'effacement |
| Fiabilité | Aucune perte de cas en cas de coupure ; reprise de synchronisation |
| Accessibilité | Faible niveau de littératie, usage en plein soleil, gants possibles |
| Maintenabilité | Tests automatisés, intégration continue, journal de versions du modèle et de la base de connaissances |
| Interopérabilité | Formats ouverts, export DHIS2, schémas documentés |

## 8. Exigences relatives aux données

| Sujet | Exigence |
|---|---|
| Sources publiques | Utiliser des jeux de peau foncée (par ex. Fitzpatrick17k, DDI, SCIN) et les jeux de dermatologie générale pour le pré-entraînement. Les jeux centrés sur les lésions tumorales (HAM10000, ISIC) servent peu pour les MTN et sont majoritairement de peau claire. Vérifier chaque licence. |
| Données locales | Collecte prospective avec partenaires cliniques : photos + diagnostic de référence (PCR pour Buruli quand disponible, examen clinique expert pour la lèpre, etc.) |
| Étiquetage | Double lecture par deux experts ; arbitrage des désaccords ; mesure de l'accord inter-évaluateurs |
| Métadonnées | Fitzpatrick, âge (tranche), sexe, zone du corps, appareil, date, aire de santé |
| Découpage | **Par patient** (jamais par image) pour éviter les fuites entre apprentissage et test ; jeu de test externe d'un autre site |
| Équilibre | Rapports par classe ; rééquilibrage et pertes adaptées aux classes rares |
| Gouvernance | Accord de partage de données, plan de gestion, traçabilité |

## 9. Exigences éthiques, légales et cliniques

- **Protection des données.** Loi n° 2024/017 du 23 décembre 2024 relative à la protection des données à caractère personnel : application effective depuis le 23 juin 2026. Elle prévoit notamment que l'hébergement à l'étranger suppose de démontrer un niveau de protection équivalent et d'obtenir une autorisation préalable. **Conséquence : prévoir un hébergement au Cameroun ou obtenir l'autorisation avant d'utiliser un cloud étranger (AWS/GCP).** La loi n° 2010/012 sur la cybersécurité et la cybercriminalité, citée dans l'ancienne version, reste un texte voisin mais n'est plus la référence pour les données personnelles. Faire valider l'analyse par un juriste.
- **Données de santé** : traiter comme données sensibles ; analyse d'impact (AIPD) avant la collecte.
- **Éthique de la recherche** : protocole soumis à un comité d'éthique (national ou institutionnel) et aux autorisations du Ministère de la Santé avant toute collecte sur des patients.
- **Statut réglementaire** : analyser si l'outil relève d'un dispositif médical ; l'usage restreint à l'aide à l'orientation, avec avertissements, est la position de départ.
- **Non-substitution** : formulations validées (« orientation », « signes évocateurs »), jamais « vous avez X ».
- **Mineurs** : consentement parental, précautions supplémentaires ; pas de photo de zones intimes dans le périmètre MVP.
- **Savoirs traditionnels** : consentement préalable, reconnaissance des détenteurs, partage des bénéfices (principes du Protocole de Nagoya) ; aucun savoir publié sans accord.
- **Sécurité clinique** : registre des risques, procédure de signalement d'erreurs, désactivation à distance d'une version fautive du modèle.

## 10. Architecture et choix techniques (synthèse)

Voir [`architecture.md`](architecture.md). Décisions clés :

1. **Une seule application mobile : Flutter** (Android). Streamlit sert au prototypage du modèle et au tableau de bord, pas à l'application terrain (il demande un serveur et du réseau).
2. **Entraînement PyTorch, déploiement TFLite** via `ai-edge-torch` (conversion directe) ; solution de repli : ONNX Runtime Mobile. Éviter la chaîne PyTorch → ONNX → TensorFlow → TFLite, fragile et mal maintenue.
3. **Modèle compact** (MobileNetV3 ou EfficientNet-Lite) plutôt que ViT/ResNet-50 sur téléphone ; un grand modèle sert d'enseignant (distillation) ou d'extracteur de caractéristiques hors ligne.
4. **Moteur de recommandations à règles**, relu par des cliniciens, pas de génération libre de texte médical.
5. **Environnements Python séparés** pour l'IA, le backend et le tableau de bord (dépendances lourdes et conflictuelles : PyTorch, TensorFlow, ai-edge-torch).

## 11. Planning révisé

| Phase | Durée indicative | Contenu | Livrables et critères de sortie |
|---|---|---|---|
| 0 - Fondations | 2 mois | Partenaires cliniques, éthique, protocole de collecte, AIPD, audit des jeux publics | Protocole approuvé ; ≥ 1 site partenaire ; cahier des classes validé par un médecin |
| 1 - Prototype IA | 3 mois | Pré-entraînement, baseline, calibration, évaluation par peau | Rapport d'évaluation ; modèle de référence ; benchmark TFLite |
| 2 - MVP mobile | 3 mois | App hors ligne, questionnaire, KB moderne, historique chiffré | APK de test ; 100 % des fonctions hors ligne ; revue clinique des fiches |
| 3 - Validation terrain | 2-3 mois | Étude pilote avec ASC, comparaison à l'avis d'un expert | Sensibilité et spécificité sur données prospectives ; retours d'usage |
| 4 - Sync et surveillance | 3 mois | Backend, tableau de bord, détection de signaux, DHIS2 | Système pilote ; test sur agrégats simulés |
| 5 - Savoirs traditionnels | 3 mois (en parallèle possible) | Collecte éthique, niveaux de preuve, relecture | Module validé par ethnobotanistes et cliniciens |
| 6 - Échelle | continu | Langues locales, OTA, ré-entraînement avec experts | Déploiement régional |

Les phases 0 et 1 peuvent se chevaucher : le temps d'obtention des autorisations est le principal facteur de retard.

## 12. Ressources

- **Équipe minimale pour le MVP** : porteur de projet / IA, développeur mobile, un clinicien référent (dermatologue ou médecin de santé publique), un appui juridique/éthique à temps partiel. L'ethnobotaniste et le développeur backend rejoignent aux phases 4-5.
- **Matériel** : 4 à 6 smartphones Android de gamme basse à moyenne, un poste avec GPU (ou crédits de calcul), stockage chiffré pour les données.
- **Hébergement** : voir §9 (conformité avant le choix du fournisseur).
- **Financement** : bourses, subventions, partenariats (OMS, programmes nationaux, ONG, universités).

## 13. Risques et mesures

| Risque | Probabilité | Impact | Mesure |
|---|---|---|---|
| Données locales insuffisantes ou déséquilibrées | Élevée | Élevé | Partenariats précoces, collecte prospective, pré-entraînement sur jeux publics, classes regroupées si trop rares |
| Biais selon type de peau, appareil ou lumière | Élevée | Élevé | Évaluation stratifiée, augmentation ciblée, étalon de couleur, test sur appareils variés |
| Erreur sur une maladie grave (faux négatif) | Moyenne | Très élevé | Seuils orientés sensibilité, abstention, formulation prudente, référence en cas de doute |
| Excès de confiance des utilisateurs | Moyenne | Élevé | Formation, messages d'incertitude, audit des usages |
| Remède traditionnel retardant la prise en charge | Moyenne | Élevé | Niveaux de preuve, exclusion pour les maladies graves, message systématique de référence |
| Non-conformité légale (hébergement, consentement) | Moyenne | Élevé | Juriste dès la phase 0, hébergement local ou autorisation |
| Retard d'autorisations éthiques | Élevée | Moyen | Démarrer le dossier dès le premier mois |
| Fuite de données | Faible | Très élevé | Chiffrement, minimisation, contrôle d'accès, audits |
| Surcharge du périmètre | Élevée | Moyen | MVP strict, extensions conditionnées à des critères de sortie |
| Pas d'adoption sur le terrain | Moyenne | Élevé | Co-conception avec les ASC, tests d'utilisabilité, formation |
| Conversion mobile qui dégrade le modèle | Moyenne | Moyen | Benchmark systématique après quantification, tests d'équivalence |

## 14. Indicateurs de succès

| Catégorie | Indicateur |
|---|---|
| Modèle | Sensibilité/spécificité par classe avec IC 95 % ; F1 macro ; erreur de calibration ; écart par type de peau |
| Usage | Taux d'adoption ; nombre de cas analysés ; taux de rejet d'images ; temps par cas |
| Clinique | Concordance avec l'expert ; délai jusqu'à la référence ; proportion de cas graves détectés précocement |
| Satisfaction | Score ≥ 4/5 (ASC), retours qualitatifs |
| Surveillance | Délai de détection d'agrégats ; taux de fausses alertes |
| Conformité | 0 incident de données ; 100 % des cas avec consentement enregistré |

## 15. Critères d'acceptation du MVP

1. L'application fonctionne en mode avion pour tout le parcours capture → résultat → historique.
2. Le modèle respecte les cibles O1 à O4 sur un jeu de test externe et par patient.
3. 100 % des fiches du MVP ont été relues par au moins deux cliniciens.
4. Consentement, chiffrement et suppression des métadonnées vérifiés par audit.
5. L'étude pilote a été approuvée par un comité d'éthique et les ASC formés.

## 16. Glossaire

**ASC** : agent de santé communautaire. **MTN** : maladie tropicale négligée. **Fitzpatrick** : échelle de classification des phototypes de peau (I à VI). **Calibration** : concordance entre la confiance annoncée et la fréquence réelle de bonne réponse. **OOD** : hors distribution. **AIPD** : analyse d'impact relative à la protection des données. **PCR** : test moléculaire de confirmation. **DHIS2** : plateforme d'information sanitaire utilisée par de nombreux ministères de la santé. **OTA** : mise à jour à distance.
