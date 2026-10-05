"""
recuperer_labels_hf.py
Récupère les métadonnées HAM10000 depuis le dataset HF et les mappe
aux images locales img_N.jpg.
"""

from pathlib import Path

import pandas as pd


IMAGES_DIR = Path("ml/data/raw/fitzpatrick17k_hf/images")
METADATA_OUT = Path("ml/data/raw/fitzpatrick17k_hf/ham10000_metadata.csv")


def main():
    print("=" * 60)
    print("RECUPERATION DES LABELS HAM10000")
    print("=" * 60)

    # 1. Charger le dataset HF en streaming, SANS les images
    print("\n[1/3] Chargement du dataset HF en streaming (métadonnées seulement)...")
    from datasets import load_dataset

    ds = load_dataset("marmal88/skin_cancer", split="train", streaming=True)
    # Ne récupérer que les métadonnées (pas l'image)
    ds_meta = ds.select_columns(["image_id", "lesion_id", "dx", "dx_type", "age", "sex", "localization"])

    rows = []
    for i, item in enumerate(ds_meta):
        rows.append(item)
        if (i + 1) % 2000 == 0:
            print(f"  → {i + 1} lignes récupérées")

    print(f"  → {len(rows)} lignes au total")

    df = pd.DataFrame(rows)
    df.to_csv(METADATA_OUT, index=False, encoding="utf-8")
    print(f"\n[2/3] Métadonnées sauvegardées : {METADATA_OUT}")

    print("\nRépartition des diagnostics :")
    for dx, count in df["dx"].value_counts().items():
        print(f"  {dx:<30} : {count}")

    # 2. Vérifier les images locales
    print(f"\n[3/3] Vérification des images locales dans {IMAGES_DIR}...")
    if not IMAGES_DIR.exists():
        print(f"  ATTENTION : {IMAGES_DIR} n'existe pas")
        return

    images = sorted(
        [f for f in IMAGES_DIR.iterdir() if f.suffix.lower() in [".jpg", ".jpeg", ".png"]],
        key=lambda f: int(f.stem.replace("img_", "")) if f.stem.startswith("img_") else 0,
    )
    print(f"  → {len(images)} images trouvées")

    if len(images) > 0:
        print(f"  → Première : {images[0].name}")
        print(f"  → Dernière : {images[-1].name}")

        # Vérifier la numérotation
        indices = [int(f.stem.replace("img_", "")) for f in images if f.stem.startswith("img_")]
        if indices:
            print(f"  → Index min : {min(indices)}")
            print(f"  → Index max : {max(indices)}")

            # Vérifier si c'est séquentiel
            manquants = set(range(min(indices), max(indices) + 1)) - set(indices)
            if manquants:
                print(f"  ATTENTION : {len(manquants)} index manquants (premiers : {sorted(list(manquants))[:5]})")
            else:
                print("  Séquentiel : oui")


if __name__ == "__main__":
    main()