"""
integrer_fitzpatrick_hf.py (v2 - diagnostic inclus)
Intègre les 9577 images Fitzpatrick17k_hf au manifest DermIA.
"""

from pathlib import Path

import pandas as pd


ROOT_HF = Path("ml/data/raw/fitzpatrick17k_hf")
METADATA_HF = ROOT_HF / "metadata.csv"
CSV_ORIGINAL = Path("ml/data/raw/fitzpatrick17k/fitzpatrick17k.csv")
MANIFEST_OUT = Path("ml/data/manifest_fitzpatrick_hf.csv")

LABEL_MAPPING_FITZ = {
    "scabies": "gale",
    "tungiasis": "tungiase",
    "leprosy": "lepre",
    "buruli": "buruli",
    "yaws": "pian",
    "psoriasis": "psoriasis",
    "eczema": "eczema",
    "atopic dermatitis": "eczema",
    "contact dermatitis": "eczema",
    "vitiligo": "vitiligo",
    "impetigo": "impetigo",
    "tinea": "teigne_mycose",
    "ringworm": "teigne_mycose",
    "dermatophytosis": "teigne_mycose",
}


def mapper_label(raw_label: str) -> str:
    s = (raw_label or "").lower().strip()
    return LABEL_MAPPING_FITZ.get(s, "autre")


def main():
    print("=" * 60)
    print("INTEGRATION FITZPATRICK17K_HF (v2)")
    print("=" * 60)

    # ── Charger les deux CSV ───────────────────────────────────────────
    df_hf = pd.read_csv(METADATA_HF)
    df_orig = pd.read_csv(CSV_ORIGINAL)
    print(f"\nmetadata.csv  : {len(df_hf)} lignes")
    print(f"fitzpatrick17k.csv : {len(df_orig)} lignes")

    # ── DIAGNOSTIC : vérifier les md5hash ─────────────────────────────
    print("\n--- DIAGNOSTIC md5hash ---")
    md5_hf = set(df_hf["md5hash"].astype(str).str.strip().str.lower())
    md5_orig = set(df_orig["md5hash"].astype(str).str.strip().str.lower())
    print(f"  md5 uniques dans HF   : {len(md5_hf)}")
    print(f"  md5 uniques dans orig : {len(md5_orig)}")
    print(f"  Intersection          : {len(md5_hf & md5_orig)}")
    print(f"  Exemples HF    : {list(md5_hf)[:3]}")
    print(f"  Exemples orig  : {list(md5_orig)[:3]}")

    # ── Normaliser les md5hash ────────────────────────────────────────
    df_hf["md5_clean"] = df_hf["md5hash"].astype(str).str.strip().str.lower()
    df_orig["md5_clean"] = df_orig["md5hash"].astype(str).str.strip().str.lower()

    # ── Merge sur md5_clean ───────────────────────────────────────────
    print("\n--- Jointure ---")
    df_merged = df_hf.merge(
        df_orig[["md5_clean", "label", "fitzpatrick_scale"]],
        on="md5_clean",
        how="left",
        suffixes=("_hf", "_orig"),
    )
    print(f"  Colonnes après merge : {df_merged.columns.tolist()}")
    print(f"  Lignes : {len(df_merged)}")

    # ── Vérifier que label_orig existe et a des valeurs ───────────────
    if "label_orig" not in df_merged.columns:
        print("\nATTENTION : colonne 'label_orig' absente !")
        print("  → La jointure n'a probablement rien matché.")
        return

    n_labels_ok = df_merged["label_orig"].notna().sum()
    print(f"  label_orig non-null : {n_labels_ok} / {len(df_merged)}")

    if n_labels_ok == 0:
        print("\nERREUR : aucun label récupéré. Les md5hash ne matchent pas.")
        return

    # ── Construire les lignes ─────────────────────────────────────────
    rows = []
    labels_bruts = {}

    for _, row in df_merged.iterrows():
        # Chemin
        chemin = str(row["chemin"]).replace("\\", "/")
        if "fitzpatrick17k_hf/" in chemin:
            chemin_final = "fitzpatrick17k_hf/" + chemin.split("fitzpatrick17k_hf/", 1)[1]
        elif "fitzpatrick17k_hf\\" in chemin:
            chemin_final = "fitzpatrick17k_hf/" + chemin.split("fitzpatrick17k_hf\\", 1)[1]
        else:
            chemin_final = "fitzpatrick17k_hf/images/" + Path(chemin).name

        label_brut = str(row["label_orig"])
        labels_bruts[label_brut] = labels_bruts.get(label_brut, 0) + 1
        label_dermia = mapper_label(label_brut)

        # Fitzpatrick
        fst = row.get("fitzpatrick_scale_orig", row.get("fitzpatrick_scale_hf"))
        try:
            fst = float(fst) if pd.notna(fst) else None
        except (ValueError, TypeError):
            fst = None

        rows.append({
            "path": chemin_final,
            "label": label_dermia,
            "label_brut": label_brut,
            "group_id": f"Fitz17k_{str(row['md5_clean'])[:16]}",
            "source": "Fitzpatrick17k-HF",
            "license": "CC-BY-NC-SA-4.0",
            "fst": fst,
            "dataset": "Fitzpatrick17k-HF",
        })

    df_out = pd.DataFrame(rows)
    MANIFEST_OUT.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(MANIFEST_OUT, index=False, encoding="utf-8")

    # ── Résumé ────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("RESULTAT")
    print("=" * 60)
    print(f"Fichier : {MANIFEST_OUT}")
    print(f"Total   : {len(df_out)} lignes")
    print()

    print("Répartition par classe DermIA :")
    for label, count in df_out["label"].value_counts().items():
        pct = 100 * count / len(df_out)
        print(f"  {label:<20} : {count:>5} ({pct:>5.1f}%)")

    print()
    print("Top 20 labels bruts :")
    top_labels = sorted(labels_bruts.items(), key=lambda x: -x[1])[:20]
    for label, count in top_labels:
        print(f"  {label:<45} : {count:>5}")

    print()
    print("Distribution Fitzpatrick (FST) :")
    if df_out["fst"].notna().any():
        for fst_val, count in df_out["fst"].value_counts().sort_index().items():
            print(f"  Type {int(fst_val)} : {count:>5}")


if __name__ == "__main__":
    main()