"""
Analyse exploratoire du dataset Fitzpatrick17k.
Script réutilisable pour DermIA.
"""

import pandas as pd
from pathlib import Path

# Chemins
DATA_PATH = Path("ml/data/raw/fitzpatrick17k/fitzpatrick17k.csv")
REPORT_DIR = Path("ml/data/processed/fitzpatrick17k")
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def charger_donnees():
    """Charge le CSV dans un DataFrame pandas."""
    print(f"Chargement de {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    print(f"OK : {len(df)} lignes, {len(df.columns)} colonnes\n")
    return df


def analyser_repartition_peau(df):
    """Analyse la répartition par type de peau."""
    print("=== RÉPARTITION PAR TYPE DE PEAU (FITZPATRICK) ===")
    repartition = df["fitzpatrick_scale"].value_counts().sort_index()
    total = len(df)
    for peau, count in repartition.items():
        pct = 100 * count / total
        print(f"  Type {peau:>2} : {count:>6} images ({pct:>5.1f}%)")

    # Sous-ensemble peaux foncées
    peaux_foncees = df[df["fitzpatrick_scale"].isin([5, 6])]
    print(f"\n  >>> Peaux foncées (5-6) : {len(peaux_foncees)} images")
    print(f"  >>> Pourcentage : {100 * len(peaux_foncees) / total:.1f}%\n")
    return peaux_foncees


def analyser_repartition_categories(df):
    """Analyse la répartition par catégorie."""
    print("=== RÉPARTITION PAR CATÉGORIE ===")
    repartition = df["three_partition_label"].value_counts()
    total = len(df)
    for cat, count in repartition.items():
        pct = 100 * count / total
        print(f"  {cat:<20} : {count:>6} images ({pct:>5.1f}%)")
    print()


def chercher_maladies_cibles(df, cibles=None):
    """Cherche les maladies cibles dans le dataset."""
    if cibles is None:
        cibles = ["leprosy", "yaws", "buruli"]

    print("=== RECHERCHE DES MALADIES CIBLES ===")
    for terme in cibles:
        masque = df["label"].str.contains(terme, case=False, na=False)
        count = masque.sum()
        print(f"  {terme:<15} : {count} images")
    print()


def sauvegarder_sous_dataset_fonce(df, peaux_foncees):
    """Sauvegarde le sous-dataset de peaux foncées."""
    chemin = REPORT_DIR / "fitzpatrick17k_peaux_foncees.csv"
    peaux_foncees.to_csv(chemin, index=False)
    print(f"Sous-dataset peaux foncées sauvegardé : {chemin}\n")


def main():
    """Fonction principale."""
    df = charger_donnees()
    analyser_repartition_peau(df)
    analyser_repartition_categories(df)
    chercher_maladies_cibles(df)

    # Sauvegarder le sous-dataset peaux foncées
    peaux_foncees = df[df["fitzpatrick_scale"].isin([5, 6])]
    sauvegarder_sous_dataset_fonce(df, peaux_foncees)

    print("Analyse terminée.")


if __name__ == "__main__":
    main()