"""
integrer_ham10000.py
Crée un manifest pour les 9577 images HAM10000 locales.
Mapping : img_N.jpg → ligne N du CSV de métadonnées.
"""

from pathlib import Path

import pandas as pd


IMAGES_DIR = Path("ml/data/raw/fitzpatrick17k_hf/images")
METADATA = Path("ml/data/raw/fitzpatrick17k_hf/ham10000_metadata.csv")
MANIFEST_OUT = Path("ml/data/manifest_ham10000.csv")

# Mapping HAM10000 → classes DermIA
LABEL_MAPPING = {
    "melanocytic_Nevi": "naevus",
    "melanoma": "melanome",
    "benign_keratosis-like_lesions": "keratose_benigne",
    "basal_cell_carcinoma": "carcinome_basal",
    "actinic_keratoses": "keratose_actinique",
    "vascular_lesions": "lesion_vasculaire",
    "dermatofibroma": "dermatofibrome",
}

# Classes à garder pour l'entraînement (assez d'images)
CLASSES_GARDEES = {
    "naevus", "melanome", "keratose_benigne",
    "carcinome_basal", "keratose_actinique",
    "lesion_vasculaire", "dermatofibrome",
}


def main():
    print("=" * 60)
    print("INTEGRATION HAM10000")
    print("=" * 60)

    # 1. Charger les métadonnées
    print(f"\n[1/3] Chargement de {METADATA}...")
    df_meta = pd.read_csv(METADATA)
    print(f"  → {len(df_meta)} lignes")

    # 2. Vérifier les images locales
    print(f"\n[2/3] Vérification des images dans {IMAGES_DIR}...")
    images = list(IMAGES_DIR.glob("img_*.jpg"))
    print(f"  → {len(images)} images trouvées")

    # Créer un mapping {index: chemin}
    mapping_idx = {}
    for img in images:
        try:
            idx = int(img.stem.replace("img_", ""))
            mapping_idx[idx] = img
        except ValueError:
            continue

    print(f"  → {len(mapping_idx)} images avec index valide")

    if len(mapping_idx) != len(df_meta):
        print(f"  ⚠️  Écart : {len(mapping_idx)} images vs {len(df_meta)} lignes")
        print(f"      On garde le minimum des deux.")

    # 3. Construire le manifest
    print(f"\n[3/3] Construction du manifest...")
    rows = []
    non_mappes = 0

    for idx, row in df_meta.iterrows():
        if idx not in mapping_idx:
            non_mappes += 1
            continue

        img_path = mapping_idx[idx]
        dx_raw = str(row["dx"])
        label = LABEL_MAPPING.get(dx_raw, "autre")

        if label not in CLASSES_GARDEES:
            continue

        fst = None  # HAM10000 n'a pas de Fitzpatrick scale
        age = row.get("age")
        sex = row.get("sex")
        loc = row.get("localization")

        rows.append({
            "path": f"fitzpatrick17k_hf/images/{img_path.name}",
            "label": label,
            "label_brut": dx_raw,
            "group_id": f"HAM_{row.get('lesion_id', 'unknown')}",
            "source": "HAM10000",
            "license": "CC-BY-NC-4.0",
            "fst": fst,
            "dataset": "HAM10000",
            "age": age,
            "sex": sex,
            "localization": loc,
        })

    df_out = pd.DataFrame(rows)

    # 4. Sauvegarder
    MANIFEST_OUT.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(MANIFEST_OUT, index=False, encoding="utf-8")

    # 5. Résumé
    print("\n" + "=" * 60)
    print("RESULTAT")
    print("=" * 60)
    print(f"Fichier : {MANIFEST_OUT}")
    print(f"Total   : {len(df_out)} lignes")
    print(f"Non mappées : {non_mappes}")
    print(f"Patients uniques (lesion_id) : {df_out['group_id'].nunique()}")
    print()

    print("Répartition par classe DermIA :")
    for label, count in df_out["label"].value_counts().items():
        pct = 100 * count / len(df_out)
        print(f"  {label:<25} : {count:>5} ({pct:>5.1f}%)")

    print()
    print("Distribution par sexe :")
    if "sex" in df_out.columns:
        print(df_out["sex"].value_counts())

    print()
    print("Distribution par localisation :")
    if "localization" in df_out.columns:
        print(df_out["localization"].value_counts().head(10))


if __name__ == "__main__":
    main()