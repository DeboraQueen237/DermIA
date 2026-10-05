\# Datasets MTN intégrés à DermIA



\## Inventaire au 5 octobre 2026



| Dataset | Images | Masques | JSON | Utilité |

| :--- | :--- | :--- | :--- | :--- |

| Fitzpatrick17k | 837 | - | 1 CSV | Dermatoses communes |

| CO2Wounds-V2 | 764 | 607 | 1 | Segmentation plaies lépreuses |

| AI-Leprosy (train) | 492 | - | 1 | Classification lèpre |

| AI-Leprosy (valid) | 61 | - | 1 | Validation |

| AI-Leprosy (test) | 61 | - | 1 | Test |

| \*\*TOTAL\*\* | \*\*\~2 200\*\* | \*\*607\*\* | \*\*5\*\* | |



\## Sources et Licences



\### Fitzpatrick17k

\- \*\*Source\*\* : github.com/mattgroh/fitzpatrick17k

\- \*\*Licence\*\* : CC BY-NC-SA 4.0

\- \*\*Chemin\*\* : `ml/data/raw/fitzpatrick17k/`



\### CO2Wounds-V2

\- \*\*Source\*\* : Mendeley Data (DOI: 10.17632/s2w7rjwz49.2)

\- \*\*Contenu\*\* : Plaies chroniques de patients lépreux

\- \*\*Chemin\*\* : `ml/data/raw/CO2Wounds/`



\### AI-Leprosy

\- \*\*Source\*\* : Roboflow Universe

\- \*\*Format\*\* : COCO JSON (bounding boxes)

\- \*\*Licence\*\* : CC BY 4.0

\- \*\*Chemin\*\* : `ml/data/raw/AI\_Leprosy/`



\## Utilisation dans DermIA



| Tâche | Dataset | Type |

| :--- | :--- | :--- |

| Classification binaire lèpre | AI-Leprosy | Classification |

| Segmentation plaies | CO2Wounds | Segmentation |

| Classification dermatoses | Fitzpatrick17k | Classification multi-classes |



\## Datasets à compléter



\- \[ ] Fitzpatrick17k complet (2 168 images attendues)

\- \[ ] Ulcère de Buruli (aucune image)

\- \[ ] Pian (aucune image)

\- \[ ] eSkinHealth (en attente de réponse)

\- \[ ] PASSION (en attente de réponse)

\- \[ ] AI4Leprosy (à télécharger - 1 456 images)

