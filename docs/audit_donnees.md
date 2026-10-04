# Audit des données publiques - DermIA

Date : 4 octobre 2026. Sources : pages officielles des jeux de données et publications (liens en bas). **Vérifiez chaque licence vous-même avant usage : ce document n'est pas un avis juridique.**

## 1. Jeux de données retenus

| Jeu | Taille | Peau | Contenu utile pour DermIA | Licence / accès | Points d'attention |
|---|---|---|---|---|---|
| **PASSION** | 4 901 images, 1 653 enfants (Madagascar, Guinée, Malawi, Tanzanie) | Fitzpatrick IV-VI | Eczéma, mycoses, **gale (MTN)**, impétigo (colonne binaire « impétiginisé »), autres | Licence PASSION : **usage non commercial**, attribution, **interdiction de ré-identifier**, **interdiction de reposter le jeu sur une autre plateforme et de partager le lien direct** | Le meilleur jeu pour votre contexte. Pédiatrique seulement. Ne pas le publier sur Kaggle : le télécharger sur votre machine ou un Drive privé |
| **Fitzpatrick17k** | 16 577 images, 114 maladies | Surtout claire : ~13 % de types V-VI | Beaucoup de dermatoses courantes. Présence de lèpre, pian, Buruli **à vérifier** dans le CSV | CC BY-NC-SA 3.0 ; le CSV fournit des URL, les images se téléchargent depuis les atlas d'origine | Étiquettes bruitées (des études estiment 16 à 30 % d'images problématiques), filigranes, liens parfois morts. Utile surtout comme complément |
| **SCIN** (Google) | 10 000+ images, contributions d'utilisateurs américains | Diversifiée (Fitzpatrick et Monk estimés) | Affections courantes (allergiques, inflammatoires, infectieuses), souvent débutantes | « SCIN Data Use License » (à lire) ; interdiction de ré-identifier | Photos de smartphone, proches de votre usage. Étiquettes de dermatologues. Peu de MTN |
| **DDI** (Stanford) | 656 images | I-VI équilibrée | Diagnostics confirmés par biopsie, surtout pour **évaluer** l'équité | Accès sur demande (à vérifier) | Trop petit pour entraîner ; utile en test d'équité |
| **PAD-UFES-20** | 2 298 images | Brésil (smartphone) | Lésions cutanées dont tumeurs | À vérifier | Peu de rapport avec les MTN |
| **HAM10000 / ISIC** | milliers | Majoritairement claire | Dermoscopie de lésions pigmentées | CC BY-NC 4.0 (HAM10000) | **Hors sujet** pour DermIA (dermoscopie, tumeurs) |

## 2. Résultat clé : la couverture des MTN prioritaires

- **Gale, mycoses, eczéma, impétigo** : bien couverts par des données de peau foncée (PASSION surtout).
- **Ulcère de Buruli, lèpre, pian** : **quasiment absents des jeux publics.** La catégorie Wikimedia Commons « Buruli ulcer » ne contient que 22 fichiers au total, cartes et schémas compris. Le seul travail publié que j'ai trouvé sur ces maladies sur peau foncée (Côte d'Ivoire et Ghana, 1 709 images) repose sur des données que l'on doit demander aux auteurs.
- Conséquence : **un modèle d'images fiable pour Buruli, lèpre et pian n'est pas atteignable avec des données publiques.** Les mesures de performance sur ces classes ne seraient pas crédibles. Voir la stratégie ci-dessous.

## 3. Stratégie retenue (à deux vitesses, honnête)

| Maladie | Approche pendant le prototype |
|---|---|
| Gale, teigne/mycoses, eczéma, impétigo | **Modèle d'images réel**, entraîné sur PASSION + Fitzpatrick17k + SCIN, évalué par type de peau |
| Buruli, lèpre, pian | **Questionnaire et règles cliniques** (déjà dans l'app) + faible modèle d'images **marqué « expérimental »** si assez d'images libres sont trouvées. Message affiché : « Cette maladie n'est pas détectée de façon fiable par l'image : référer en cas de signes évocateurs » |
| Tout cas inhabituel | Classe « autre / indéterminé » : référer |

Pistes pour les MTN rares, par ordre de réalisme :
1. **Contacter les auteurs de l'étude Côte d'Ivoire / Ghana** et le programme MTN de l'OMS pour un accès à des images, sur demande, avec un projet et un cadre éthique clairs.
2. **Images en accès libre** : articles de revues ouvertes (licences CC BY), Wikimedia Commons, bases d'images de l'OMS ou du CDC dont la licence autorise la réutilisation. Conserver la licence et l'attribution de **chaque** image dans le manifeste. Le volume restera de l'ordre de dizaines d'images.
3. **Modèle de fondation dermatologique** (Derm Foundation de Google, embeddings de 6 144 dimensions) : permet d'entraîner un classifieur léger à partir de peu d'images. Conditions d'usage « Health AI Developer Foundations » à lire avant de l'utiliser dans un produit.
4. **Collecte locale** avec partenaire clinique (la seule voie pour une validation réelle).

## 4. Règles d'usage des données

1. **Ne jamais mélanger les licences sans les noter** : chaque image a une ligne dans le manifeste avec `source`, `license`, `attribution`.
2. **Usage non commercial** (PASSION, Fitzpatrick17k, HAM10000) : compatible avec un prototype de recherche et une candidature à bourse. Cela **empêche un produit commercial** sans autre accord. À garder en tête pour le statut de l'équipe.
3. **Ne pas publier** les jeux ni les images dans votre dépôt (le `.gitignore` les exclut). **Les poids du modèle entraîné sur des données non commerciales peuvent hériter de ces restrictions** : ne pas les distribuer publiquement sans avis juridique.
4. **Aucune tentative de ré-identification**, aucun partage du lien de téléchargement direct (PASSION).
5. **Découpage par patient** (`group_id`), jamais par image : un même enfant ne doit pas être à la fois dans l'entraînement et le test.
6. **Doublons** : Fitzpatrick17k et d'autres jeux contiennent des quasi-doublons ; dédupliquer avant tout découpage.

## 5. Format du manifeste unifié (`ml/data/manifest.csv`)

| Colonne | Rôle |
|---|---|
| `path` | Chemin relatif de l'image |
| `label` | Classe DermIA (`gale`, `teigne_mycose`, `eczema`, `impetigo`, `buruli`, `lepre`, `pian`, `autre`) |
| `raw_label` | Étiquette d'origine du jeu |
| `group_id` | Identifiant patient (préfixé par la source) |
| `source` | `passion`, `f17k`, `scin`, `commons`… |
| `license` | Licence ou conditions |
| `fst` | Type de peau de Fitzpatrick (1-6) si connu |

## 6. Prochaines actions

1. Télécharger PASSION via son site (lire et accepter l'accord d'usage).
2. Télécharger `fitzpatrick17k.csv`, lister les conditions : chercher `lepro`, `yaws`, `buruli`, `scabies`, `tinea`, `impetigo`, `eczema`.
3. Récupérer SCIN (bucket Google Cloud ou Hugging Face) après lecture de sa licence.
4. M'envoyer l'en-tête des CSV et l'arborescence des dossiers : j'écrirai les adaptateurs qui produisent le manifeste.
5. Lancer l'entraînement de référence sur GPU (Colab ou Google Drive privé pour PASSION).

## Sources

- PASSION : passionderm.github.io et arXiv 2411.04584 (MICCAI 2024)
- Fitzpatrick17k : github.com/mattgroh/fitzpatrick17k ; qualité des étiquettes : arXiv 2505.11034
- SCIN : github.com/google-research-datasets/scin et Hugging Face `google/scin`
- Derm Foundation : developers.google.com/health-ai-developer-foundations/derm-foundation
- Étude pilote MTN cutanées (Côte d'Ivoire / Ghana) : PLoS NTD 2023, PMC10449179
- Panorama des jeux dermatologiques : arXiv 2601.00840
