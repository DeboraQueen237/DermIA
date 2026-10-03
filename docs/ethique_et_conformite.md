# Éthique, conformité et sécurité clinique - DermIA

> Ce document est une base de travail, pas un avis juridique. Il doit être revu par un juriste et par le comité d'éthique avant toute collecte de données sur des patients.

## 1. Principes

1. **Ne pas nuire** : en cas de doute, orienter vers la référence.
2. **Autonomie et consentement** : le patient sait quelles données sont prises et pourquoi, et peut refuser sans perdre l'accès aux soins.
3. **Minimisation** : ne collecter que ce qui est nécessaire.
4. **Équité** : l'outil doit fonctionner aussi bien sur les peaux foncées, et ses performances par sous-groupe sont publiées.
5. **Transparence** : limites, taux d'erreur et incertitudes sont visibles pour l'utilisateur.
6. **Responsabilité humaine** : l'ASC et le soignant décident ; l'outil assiste.
7. **Respect des savoirs locaux** : consentement, reconnaissance et partage des bénéfices.

## 2. Cadre légal à vérifier

| Sujet | Point de départ | Action |
|---|---|---|
| Données personnelles | Loi n° 2024/017 du 23 décembre 2024, application effective depuis le 23 juin 2026. Elle prévoit une autorité de protection des données, des droits d'effacement et d'opposition, et une autorisation préalable pour héberger des données à l'étranger | Faire analyser par un juriste ; déterminer la qualité de responsable de traitement ; vérifier les décrets d'application et les formalités auprès de l'autorité |
| Cybersécurité | Loi n° 2010/012 sur la cybersécurité et la cybercriminalité | Respecter comme texte complémentaire |
| Recherche impliquant des personnes | Évaluation par un comité d'éthique et autorisation du Ministère de la Santé publique | Déposer le dossier dès la phase 0 |
| Dispositif médical / logiciel de santé | Régime à déterminer | Obtenir un avis des autorités sanitaires sur le statut de l'outil |
| Savoirs traditionnels | Principes du Protocole de Nagoya, droit national applicable | Accords avec les détenteurs de savoirs |
| Cadre africain | Convention de l'Union africaine sur la cybersécurité et la protection des données (2014) | Référence d'inspiration |

## 3. Consentement

- **Deux niveaux distincts** : (1) consentement aux soins et à l'utilisation de l'outil ; (2) consentement optionnel à l'usage de la photo pour la recherche et l'entraînement du modèle. Refuser le second ne change rien aux soins.
- **Forme** : écrit, ou oral enregistré (horodaté, avec témoin) quand la littératie est faible. Texte court, en langue comprise ; aide audio.
- **Mineurs** : consentement du parent ou tuteur, assentiment de l'enfant adapté à l'âge.
- **Retrait** : le patient peut demander la suppression de ses données ; la procédure est documentée et testée.
- **Zones sensibles** : pas de photos du visage identifiable ni de zones intimes dans le MVP ; si une lésion siège sur ces zones, l'application oriente vers un soignant formé.

## 4. Gestion des données

| Étape | Règle |
|---|---|
| Collecte | Identifiant de cas aléatoire ; pas de nom ni de numéro de téléphone dans l'application ; métadonnées EXIF/GPS supprimées dès la capture |
| Stockage local | Chiffrement SQLCipher, clés dans le Keystore, photos hors galerie |
| Synchronisation | Seuls les cas pseudonymisés sont envoyés ; images envoyées seulement avec consentement « recherche » |
| Localisation | Aire de santé ou commune ; jamais de coordonnées précises à l'extérieur du téléphone |
| Serveur | Accès par rôle, journal d'audit, sauvegardes chiffrées |
| Conservation | Durée définie dans le protocole ; suppression à l'issue ou sur demande |
| Partage | Accord écrit ; jeux de données non publiés sans base légale et consentement ; données agrégées préférées |
| Analyse d'impact | Réaliser une AIPD avant la phase de collecte |

Une photo de peau peut être identifiante (cicatrices, tatouages, contexte). Elle est traitée comme donnée de santé sensible.

## 5. Sécurité clinique

### 5.1 Ce que l'outil fait et ne fait pas
- **Fait** : propose des hypothèses d'orientation, indique le niveau d'urgence, donne des conseils de premiers soins issus de fiches validées, aide à décider de la référence.
- **Ne fait pas** : ne pose pas de diagnostic définitif ; ne génère pas de prescription ni de posologie à la volée ; ne remplace pas un examen clinique ni un test de confirmation.

### 5.2 Vocabulaire
Utiliser « signes évocateurs de… », « à confirmer par un soignant », « référer ». Éviter « vous avez… », « diagnostic ». Sur chaque écran de résultat : mention de non-substitution et niveau de confiance.

### 5.3 Garde-fous du modèle
- Seuils réglés pour privilégier la **sensibilité** sur les maladies graves.
- **Abstention** : image de mauvaise qualité, cas hors distribution ou confiance faible → « référer ».
- **Signes d'alerte** affichés quel que soit le résultat (fièvre, extension rapide, atteinte profonde, perte de sensibilité, douleur intense, atteinte d'un enfant en bas âge…).
- Confusions dangereuses surveillées (ex. ulcère de Buruli confondu avec un autre ulcère).

### 5.4 Surveillance après déploiement
- Registre des erreurs signalées par les utilisateurs ; revue régulière par un clinicien.
- Possibilité de **désactiver à distance** une version fautive du modèle ou d'une fiche.
- Comité de revue clinique (réunion périodique) et journal des décisions.
- Mesure de la concordance avec les experts sur un échantillon de cas.

### 5.5 Savoirs traditionnels : règles de sécurité
- Tout remède est classé par niveau de preuve (A à D, voir `architecture.md`).
- Aucune recommandation traditionnelle **à la place** de la référence pour une maladie grave. Retarder le traitement est un risque réel, notamment pour l'ulcère de Buruli et la lèpre.
- Contre-indications et risques (substances caustiques, allergènes, interactions, application sur plaie ouverte) signalés.
- Pas de dosage ni de préparation détaillée sans validation par des pharmacologues et des cliniciens.
- Les propositions traditionnelles sont présentées comme **soins complémentaires** ou information, et séparées visuellement des soins médicaux.

## 6. Savoirs traditionnels : éthique et partage des bénéfices

1. **Consentement préalable** libre et éclairé des tradipraticiens et communautés.
2. **Attribution** : reconnaissance des détenteurs (avec leur accord).
3. **Partage des bénéfices** : accord écrit (retombées non monétaires possibles : formation, accès à l'outil, co-publication).
4. **Contrôle** : possibilité de retirer un savoir de la base.
5. **Validation scientifique** : revue par ethnobotanistes et pharmacologues ; recherche de sources publiées ; transparence sur ce qui n'est pas validé.
6. Les savoirs collectés ne sont pas publiés ni transférés à des tiers sans accord.

## 7. Équité et biais

- Évaluer systématiquement par type de peau (Fitzpatrick), âge, sexe, zone du corps, qualité d'image, appareil.
- Mesurer et publier les écarts ; corriger par collecte ciblée plutôt que seulement par pondération.
- Étalon de couleur pour limiter l'effet de l'éclairage.
- Ne pas déployer dans un sous-groupe où la performance n'a pas été mesurée.
- Impliquer les ASC et des représentants des communautés dans la conception et les tests.

## 8. Formation des utilisateurs

- Formation initiale : usage, limites, signes d'alerte, quand référer, conduite sur le consentement.
- Messages clés : l'outil peut se tromper ; en cas de doute, référer ; ne pas retarder une référence pour essayer un remède.
- Évaluation de la compréhension et suivi après déploiement.

## 9. Gouvernance

| Rôle | Responsabilité |
|---|---|
| Porteur du projet | Responsable du traitement (à confirmer juridiquement), pilotage |
| Référent clinique | Validation des fiches, des seuils, revue des erreurs |
| Référent éthique/juridique | Conformité, AIPD, consentements |
| Responsable des données | Accès, conservation, suppression |
| Comité consultatif | ASC, représentants communautaires, tradipraticiens, autorités |

## 10. Check-list avant la première collecte

- [ ] Avis du comité d'éthique obtenu
- [ ] Autorisation institutionnelle (Ministère, direction de l'hôpital/district)
- [ ] Analyse juridique de la loi n° 2024/017 réalisée ; formalités accomplies
- [ ] AIPD réalisée
- [ ] Formulaires de consentement validés (langues locales, versions audio)
- [ ] Procédure de suppression testée
- [ ] Hébergement conforme (local ou autorisé)
- [ ] Données de test synthétiques en développement
- [ ] Formation des enquêteurs et ASC
- [ ] Accord de partage de données avec les partenaires
