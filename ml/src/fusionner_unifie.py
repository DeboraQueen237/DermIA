"""
fusionner_unifie.py
Combine AI-Leprosy (lèpre) + HAM10000 (7 classes) en un manifest unifié.
"""

from pathlib import Path

import pandas as pd


AI_LEPROSY = Path("ml/data/manifest_adapted.csv")
HAM10000 = Path("ml/data/manifest_ham10000_clean.csv")
OUT = Path("ml/data/manifest_unified.csv")


def main():
    print("=" * 60)
    print("FUSION UNIFIEE : MTN + DERMATOLOGIE")
    print("=" * 60)

    # 1. Charger AI-Leprosy
    print(f"\n[1/3] Chargement de {AI_LEPROSY}...")
    df_lep = pd.read_csv(AI_LEPROSY)
    print(f"  → {len(df_lep)} lignes")
    print(f"  → Labels : {df_lep['label'].value_counts().to_dict()}")

    # Renommer "autre" en "non_lepre" pour HAM10000
    # (mais on va plutôt l'exclure car AI-Leprosy "autre" = non-lèpre sans diagnostic précis)
    df_lep = df_lep[df_lep["label"] == "lepre"].copy()
    df_lep["label"] = "lepre"
    print(f"  → Filtre : {len(df_lep)} images de lèpre conservées")

    # 2. Charger HAM10000
    print(f"\n[2/3] Chargement de {HAM10000}...")
    df_ham = pd.read_csv(HAM10000)
    print(f"  → {len(df_ham)} lignes")
    print(f"  → Labels : {df_ham['label'].value_counts().to_dict()}")

    # 3. Harmoniser les colonnes
    print(f"\n[3/3] Harmonisation des colonnes...")

    # AI-Leprosy : garder path, label, group_id, source, license, fst
    df_lep = df_lep[["path", "label", "group_id", "source", "license", "fst"]].copy()
    df_lep["dataset"] = "AI-Leprosy"

    # HAM10000 : déjà au bon format
    df_ham = df_ham[["path", "label", "group_id", "source", "license", "fst"]].copy()
    df_ham["dataset"] = "HAM10000"

    # Concaténer
    df_unified = pd.concat([df_lep, df_ham], ignore_index=True)

    # Sauvegarder
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df_unified.to_csv(OUT, index=False, encoding="utf-8")

    # Résumé
    print("\n" + "=" * 60)
    print("RESULTAT")
    print("=" * 60)
    print(f"Fichier : {OUT}")
    print(f"Total : {len(df_unified)} lignes")
    print(f"Patients uniques : {df_unified['group_id'].nunique()}")
    print()

    print("Répartition par classe :")
    for label, count in df_unified["label"].value_counts().items():
        pct = 100 * count / len(df_unified)
        print(f"  {label:<25} : {count:>5} ({pct:>5.1f}%)")

    print()
    print("Répartition par dataset :")
    for ds, count in df_unified["dataset"].value_counts().items():
        print(f"  {ds:<15} : {count}")

    # Ratio de déséquilibre
    max_count = df_unified["label"].value_counts().max()
    min_count = df_unified["label"].value_counts().min()
    print(f"\nRatio déséquilibre : {max_count / min_count:.1f}x")


if __name__ == "__main__":
    main()