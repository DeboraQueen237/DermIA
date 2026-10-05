"""
recuperer_meta_api.py (v2 avec reprise automatique)
"""

import time
from pathlib import Path

import pandas as pd
import requests


OUT = Path("ml/data/raw/fitzpatrick17k_hf/ham10000_metadata.csv")

API_URL = (
    "https://datasets-server.huggingface.co/rows"
    "?dataset=marmal88%2Fskin_cancer"
    "&config=default"
    "&split=train"
    "&offset={offset}"
    "&length={length}"
)


def charger_existant():
    """Charge les lignes déjà téléchargées pour reprendre."""
    if OUT.exists():
        df = pd.read_csv(OUT)
        print(f"  Reprise depuis {len(df)} lignes existantes")
        return df.to_dict("records")
    return []


def main():
    print("=" * 60)
    print("RECUPERATION METADONNEES (v2 - avec reprise)")
    print("=" * 60)

    rows = charger_existant()
    offset = len(rows)
    length = 100
    max_retries = 10
    connecutive_fails = 0
    MAX_CONSECUTIVE_FAILS = 30  # abandon après 30 échecs consécutifs

    while connecutive_fails < MAX_CONSECUTIVE_FAILS:
        url = API_URL.format(offset=offset, length=length)

        success = False
        for attempt in range(max_retries):
            try:
                r = requests.get(url, timeout=60)
                if r.status_code == 200:
                    success = True
                    break
                elif r.status_code == 502:
                    time.sleep(3)
            except requests.exceptions.RequestException:
                time.sleep(3)

        if not success:
            connecutive_fails += 1
            print(f"  Echec ({connecutive_fails}/{MAX_CONSECUTIVE_FAILS}), pause 10s...")
            time.sleep(10)

            # Sauvegarde intermédiaire pour ne rien perdre
            if rows:
                pd.DataFrame(rows).to_csv(OUT, index=False, encoding="utf-8")
            continue

        connecutive_fails = 0
        data = r.json()
        batch = data.get("rows", [])
        if not batch:
            print("\n  Fin du dataset atteinte.")
            break

        for item in batch:
            row = item.get("row", {})
            rows.append({
                "image_id": row.get("image_id"),
                "lesion_id": row.get("lesion_id"),
                "dx": row.get("dx"),
                "dx_type": row.get("dx_type"),
                "age": row.get("age"),
                "sex": row.get("sex"),
                "localization": row.get("localization"),
            })

        offset += length

        # Sauvegarde tous les 500 nouveaux
        if offset % 500 == 0:
            pd.DataFrame(rows).to_csv(OUT, index=False, encoding="utf-8")
            print(f"  {len(rows)} lignes sauvegardées")

        time.sleep(0.5)

    # Sauvegarde finale
    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False, encoding="utf-8")
    print(f"\nTotal : {len(df)} lignes sauvegardées")

    print("\nRépartition des diagnostics :")
    for dx, count in df["dx"].value_counts().items():
        print(f"  {dx:<35} : {count}")


if __name__ == "__main__":
    main()