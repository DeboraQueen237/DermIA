"""
fusion_datasets.py
Fusionne les datasets AI-Leprosy, CO2Wounds et Fitzpatrick17k en un manifest unifié.
"""

import json
from pathlib import Path

import pandas as pd


ROOT = Path("ml/data/raw")
OUT_MANIFEST = Path("ml/data/manifest_global.csv")


def charger_co2wounds():
    """Charge CO2Wounds-V2 (segmentation de plaies lépreuses)."""
    base = ROOT / "CO2Wounds" / "CO2Wounds-V2 Extended Chronic Wounds Dataset From Leprosy Patients"
    imgs_dir = base / "imgs"
    masks_dir = base / "masks"

    if not imgs_dir.exists():
        print(f"ATTENTION : CO2Wounds introuvable : {imgs_dir}")
        return []

    rows = []
    for img in sorted(imgs_dir.glob("*")):
        if img.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
            continue
        mask = masks_dir / f"{img.stem}.png"
        rows.append({
            "dataset": "CO2Wounds",
            "image_path": str(img).replace("\\", "/"),
            "mask_path": str(mask).replace("\\", "/") if mask.exists() else None,
            "label": "leprosy_wound",
            "task": "segmentation",
            "split": "train",
            "source": "Mendeley",
        })
    print(f"OK CO2Wounds : {len(rows)} images")
    return rows


def charger_ai_leprosy():
    """Charge AI-Leprosy (classification + détection)."""
    base = ROOT / "AI_Leprosy"

    if not base.exists():
        print(f"ATTENTION : AI-Leprosy introuvable : {base}")
        return []

    rows = []
    for split in ["train", "valid", "test"]:
        split_dir = base / split
        ann_file = split_dir / "_annotations.coco.json"

        if not ann_file.exists():
            continue

        with open(ann_file, "r", encoding="utf-8") as f:
            coco = json.load(f)

        img_map = {img["id"]: img["file_name"] for img in coco["images"]}
        ann_map = {}
        for ann in coco["annotations"]:
            ann_map.setdefault(ann["image_id"], []).append(ann["category_id"])

        cat_names = {c["id"]: c["name"] for c in coco["categories"]}

        for img_id, filename in img_map.items():
            img_path = split_dir / filename
            cats = ann_map.get(img_id, [])
            label = cat_names.get(cats[0], "unknown") if cats else "unknown"

            # Normalisation du label
            label_lower = label.lower().strip()
            if label_lower in ["leprosy", "leprosy_positive", "lep"]:
                label_norm = "leprosy"
            elif "non" in label_lower or "nonlep" in label_lower:
                label_norm = "non_leprosy"
            else:
                label_norm = label_lower

            rows.append({
                "dataset": "AI-Leprosy",
                "image_path": str(img_path).replace("\\", "/"),
                "mask_path": None,
                "label": label_norm,
                "task": "classification",
                "split": split,
                "source": "Roboflow",
            })
    print(f"OK AI-Leprosy : {len(rows)} images")
    return rows


def charger_fitzpatrick17k():
    """Charge Fitzpatrick17k (métadonnées + images locales)."""
    csv_path = ROOT / "fitzpatrick17k" / "fitzpatrick17k.csv"
    imgs_dir = ROOT / "fitzpatrick17k" / "images"

    if not csv_path.exists():
        print(f"ATTENTION : Fitzpatrick17k CSV introuvable : {csv_path}")
        return []

    df = pd.read_csv(csv_path)
    rows = []

    # Créer un set des md5 présents
    md5_presents = {f.stem for f in imgs_dir.glob("*") if f.is_file()}

    for _, row in df.iterrows():
        md5 = str(row.get("md5hash", ""))
        if md5 not in md5_presents:
            continue  # Skip si l'image n'a pas été téléchargée

        rows.append({
            "dataset": "Fitzpatrick17k",
            "image_path": str(imgs_dir / f"{md5}.jpg").replace("\\", "/"),
            "mask_path": None,
            "label": row.get("label", "unknown"),
            "task": "classification",
            "split": "unknown",
            "source": "GitHub",
            "fitzpatrick_scale": row.get("fitzpatrick_scale", -1),
        })
    print(f"OK Fitzpatrick17k : {len(rows)} images (avec images présentes)")
    return rows


def main():
    print("=" * 60)
    print("FUSION DES DATASETS DERMIA")
    print("=" * 60)

    all_rows = []
    all_rows.extend(charger_co2wounds())
    all_rows.extend(charger_ai_leprosy())
    all_rows.extend(charger_fitzpatrick17k())

    if not all_rows:
        print("\nERREUR : Aucune donnée trouvée.")
        return

    df = pd.DataFrame(all_rows)
    OUT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_MANIFEST, index=False, encoding="utf-8")

    print("\n" + "=" * 60)
    print("RESUME")
    print("=" * 60)
    print(f"  Total entrées    : {len(df)}")
    print(f"  Datasets         : {df['dataset'].nunique()}")
    print(f"  Fichier manifest : {OUT_MANIFEST}")
    print()
    print("Répartition par dataset :")
    for ds, count in df["dataset"].value_counts().items():
        print(f"  {ds:<20} : {count}")
    print()
    print("Répartition par label :")
    for label, count in df["label"].value_counts().head(15).items():
        print(f"  {str(label):<30} : {count}")
    print()
    print("Répartition par tâche :")
    for task, count in df["task"].value_counts().items():
        print(f"  {task:<20} : {count}")


if __name__ == "__main__":
    main()