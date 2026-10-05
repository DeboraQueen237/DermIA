"""
Télécharge les images du dataset Fitzpatrick17k depuis les URLs du CSV.
Gère les erreurs réseau, les timeouts et reprend où il s'est arrêté.
"""

import pandas as pd
import requests
from pathlib import Path
from tqdm import tqdm
import time

# Chemins
CSV_PATH = Path("ml/data/raw/fitzpatrick17k/fitzpatrick17k.csv")
IMAGES_DIR = Path("ml/data/raw/fitzpatrick17k/images")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Configuration
TIMEOUT = 15  # secondes
DELAI_ENTRE_REQUETES = 0.5  # secondes (pour ne pas surcharger le serveur)


def telecharger_image(url, chemin_destination, session):
    """Télécharge une seule image. Retourne True si succès."""
    try:
        response = session.get(url, timeout=TIMEOUT, stream=True)
        if response.status_code == 200:
            with open(chemin_destination, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        return False
    except Exception:
        return False


def main():
    # Filtre : peaux foncées uniquement (5-6) pour commencer
    print(f"Chargement de {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)
    df_fonce = df[df["fitzpatrick_scale"].isin([5, 6])].copy()
    print(f"Images à télécharger (peaux foncées 5-6) : {len(df_fonce)}\n")

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (DermIA Research Project)"
    })

    succes = 0
    echecs = 0
    deja_presentes = 0

    for _, row in tqdm(df_fonce.iterrows(), total=len(df_fonce), desc="Téléchargement"):
        md5 = row["md5hash"]
        url = row["url"]
        chemin = IMAGES_DIR / f"{md5}.jpg"

        # Skip si déjà téléchargé
        if chemin.exists():
            deja_presentes += 1
            continue

        if telecharger_image(url, chemin, session):
            succes += 1
        else:
            echecs += 1

        time.sleep(DELAI_ENTRE_REQUETES)

    print(f"\n=== RÉSULTAT ===")
    print(f"  Succès          : {succes}")
    print(f"  Échecs          : {echecs}")
    print(f"  Déjà présentes  : {deja_presentes}")
    print(f"  Total           : {succes + echecs + deja_presentes}")
    print(f"  Dossier         : {IMAGES_DIR}")


if __name__ == "__main__":
    main()