"""
adapt_manifest.py
Convertit le manifest DermIA actuel au format attendu par data_utils.py.

Entrée  : ml/data/manifest_global.csv (généré par fusion_datasets.py)
Sortie  : ml/data/manifest_adapted.csv (format data_utils.py)
"""

import re
from pathlib import Path

import pandas as pd


MANIFEST_IN = Path("ml/data/manifest_global.csv")
MANIFEST_OUT = Path("ml/data/manifest_adapted.csv")


# Mapping des labels bruts vers les classes DermIA (aligné avec data_utils.LABEL_KEYWORDS)
LABEL_MAPPING = {
    # MTN cibles
    "leprosy": "lepre",
    "leprosy_wound": "lepre",  # Les plaies lépreuses = lèpre
    "non_leprosy": "autre",     # Négatifs = "autre" pour le multi-classe
    # Autres maladies
    "scabies": "gale",
    "impetigo": "impetigo",
    "tungiasis": "tungiase",
    "buruli": "buruli",
    "yaws": "pian",
    # Fitzpatrick17k : beaucoup de classes, on map "autre" par défaut
    "psoriasis": "autre",
    "eczema": "eczema",
    "atopic dermatitis": "eczema",
    "contact dermatitis": "eczema",
    "tinea": "teigne_mycose",
    "ringworm": "teigne_mycose",
    "dermatophytosis": "teigne_mycose",
}


def extraire_group_id(row):
    """
    Extrait un identifiant de patient à partir du chemin de l'image.
    
    Règles :
    - On cherche un nombre à 6 chiffres qui n'est PAS une date (YYMMDD).
    - Si aucun patient n'est trouvé, l'image devient son propre groupe.
    """
    path = str(row["image_path"]).replace("\\", "/")
    nom = Path(path).stem
    dataset = row["dataset"]

    if dataset == "AI-Leprosy":
        # Chercher tous les nombres à 6 chiffres
        matches = re.findall(r"\d{6}", nom)
        for m in matches:
            annee = int(m[:2])
            mois = int(m[2:4])
            jour = int(m[4:6])
            # Une date valide : année 20-30, mois 1-12, jour 1-31
            est_une_date = (20 <= annee <= 30 and 1 <= mois <= 12 and 1 <= jour <= 31)
            if not est_une_date:
                return f"AI-Leprosy_{m}"
        # Aucun patient identifié → chaque image = son propre groupe
        return f"AI-Leprosy_{nom}"

    elif dataset == "CO2Wounds":
        return f"CO2Wounds_{nom}"

    elif dataset == "Fitzpatrick17k":
        return f"Fitz17k_{nom[:12]}"

    return f"{dataset}_{nom}"


def extraire_chemin_relatif(chemin_absolu):
    """Convertit 'C:/Users/.../ml/data/raw/xxx' en 'xxx' (relatif à ml/data/raw/)."""
    chemin = str(chemin_absolu).replace("\\", "/")
    if "ml/data/raw/" in chemin:
        return chemin.split("ml/data/raw/", 1)[1]
    return chemin


def main():
    print("=" * 60)
    print("ADAPTATION DU MANIFEST")
    print("=" * 60)

    # Charger le manifest actuel
    df = pd.read_csv(MANIFEST_IN)
    print(f"Manifest source : {len(df)} lignes")

    # Ne garder que la classification (pas la segmentation pour l'instant)
    df_cls = df[(df["task"] == "classification") & (df["dataset"] == "AI-Leprosy")].copy()
    print(f"Après filtre classification : {len(df_cls)} lignes")

    # 1. Convertir le chemin en relatif
    df_cls["path"] = df_cls["image_path"].apply(extraire_chemin_relatif)

    # 2. Normaliser les labels
    df_cls["label_raw"] = df_cls["label"].str.lower().str.strip()
    df_cls["label"] = df_cls["label_raw"].map(LABEL_MAPPING).fillna("autre")

    # 3. Générer les group_id (patient)
    df_cls["group_id"] = df_cls.apply(extraire_group_id, axis=1)

    # 4. Source et licence (à remplir selon le dataset)
    license_map = {
        "AI-Leprosy": "CC-BY-4.0",
        "CO2Wounds": "CC-BY-4.0",
        "Fitzpatrick17k": "CC-BY-NC-SA-4.0",
    }
    df_cls["source"] = df_cls["dataset"]
    df_cls["license"] = df_cls["dataset"].map(license_map).fillna("unknown")

    # 5. Fitzpatrick (déjà présent ou NaN)
    if "fitzpatrick_scale" in df_cls.columns:
        df_cls["fst"] = pd.to_numeric(df_cls["fitzpatrick_scale"], errors="coerce")
    else:
        df_cls["fst"] = pd.NA

    # 6. Garder les colonnes finales
    df_out = df_cls[[
        "path", "label", "group_id", "source", "license", "fst", "dataset"
    ]].copy()

    # Sauvegarder
    MANIFEST_OUT.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(MANIFEST_OUT, index=False, encoding="utf-8")

    print("\n" + "=" * 60)
    print("RÉSULTAT")
    print("=" * 60)
    print(f"Manifest adapté : {MANIFEST_OUT}")
    print(f"Total lignes    : {len(df_out)}")
    print(f"Patients uniques: {df_out['group_id'].nunique()}")
    print()

    print("Répartition par label :")
    for label, count in df_out["label"].value_counts().items():
        print(f"  {label:<20} : {count}")

    print("\nRépartition par source :")
    for src, count in df_out["source"].value_counts().items():
        print(f"  {src:<20} : {count}")

    print("\nExemples de group_id :")
    for gid in df_out["group_id"].head(5):
        print(f"  {gid}")


if __name__ == "__main__":
    main()