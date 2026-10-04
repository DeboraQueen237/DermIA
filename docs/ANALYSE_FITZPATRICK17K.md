\# Analyse du dataset Fitzpatrick17k



\## Résumé



\- \*\*Total images\*\* : 16 577

\- \*\*Maladies\*\* : \~120

\- \*\*Source\*\* : mattgroh/fitzpatrick17k (GitHub)

\- \*\*Licence\*\* : CC BY-NC-SA 4.0



\## Répartition par type de peau (Fitzpatrick)



| Type | Nombre | % |

| :--- | :--- | :--- |

| -1 (non classé) | 565 | 3,4% |

| 1 | 2 947 | 17,8% |

| 2 | 4 808 | 29,0% |

| 3 | 3 308 | 20,0% |

| 4 | 2 781 | 16,8% |

| 5 | 1 533 | 9,2% |

| 6 | 635 | 3,8% |



\*\*Constat\*\* : seulement 13,1% d'images de peaux foncées (5-6).

\*\*Implication\*\* : nécessité de compléter avec PASSION pour éviter les biais.



\## Répartition par catégorie (3-partition)



| Catégorie | Nombre | % |

| :--- | :--- | :--- |

| non-neoplastic | 12 080 | 72,9% |

| malignant | 2 263 | 13,6% |

| benign | 2 234 | 13,5% |



\## Maladies cibles de DermIA



| Maladie | Images dans Fitzpatrick17k |

| :--- | :--- |

| Lèpre | 0 |

| Pian | 0 |

| Ulcère de Buruli | 0 |



\*\*Conclusion\*\* : Fitzpatrick17k ne contient AUCUNE des 3 MTN cibles.



\## Décision stratégique



1\. Utiliser Fitzpatrick17k comme \*\*baseline\*\* sur les maladies communes (psoriasis, eczéma, gale, etc.).

2\. Filtrer les peaux foncées (5-6) pour étudier les biais.

3\. Compléter avec PASSION (en attente) et un dataset MTN dédié (à trouver).

