"""
Télécharge Fitzpatrick17k depuis Hugging Face (bien plus rapide que dermaamin.com).
"""

from datasets import load_dataset
from pathlib import Path
import pandas as pd

OUT_DIR = Path("ml/data/raw/fitzpatrick17k_hf")
OUT_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR = OUT_DIR / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

print("📥 Chargement du dataset depuis Hugging Face...")
ds = load_dataset("marmal88/skin_cancer", split="train")
# Alternative si celui-ci ne marche pas :
# ds = load_dataset("nateraw/fitzpatrick17k", split="train")

print(f"✅ {len(ds)} images trouvées")
print(f"📋 Colonnes : {ds.column_names}")

# Sauvegarder les images et créer un CSV
rows = []
for i, item in enumerate(ds):
    if i % 500 == 0:
        print(f"  {i}/{len(ds)}...")
    
    img = item["image"]
    label = item.get("label", item.get("lesion", "inconnu"))
    md5 = item.get("md5hash", f"img_{i}")
    
    # Sauvegarder l'image
    chemin = IMAGES_DIR / f"{md5}.jpg"
    img.save(chemin)
    
    rows.append({
        "md5hash": md5,
        "label": label,
        "chemin": str(chemin),
        "fitzpatrick_scale": item.get("fitzpatrick_scale", -1),
    })

# Créer le CSV
df = pd.DataFrame(rows)
df.to_csv(OUT_DIR / "metadata.csv", index=False)
print(f"\n✅ Terminé ! {len(df)} images dans {IMAGES_DIR}")
print(f"📄 CSV : {OUT_DIR / 'metadata.csv'}")