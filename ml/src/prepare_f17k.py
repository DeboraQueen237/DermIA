"""Prépare un sous-ensemble de Fitzpatrick17k pour DermIA.

1. Sélectionne les classes utiles (gale, eczéma, tungiase) + un échantillon "autre" varié.
2. Télécharge les images depuis les atlas d'origine (reprenable, 1 requête / seconde).
3. Regroupe les quasi-doublons par hachage perceptuel : ils reçoivent le MÊME group_id,
   car Fitzpatrick17k n'a pas d'identifiant patient (sinon : fuite entre entraînement et test).
4. Écrit manifest_f17k.csv.

Licence : annotations CC BY-NC-SA 3.0 ; les images restent la propriété des atlas d'origine.
Usage de recherche non commercial uniquement ; ne jamais republier les images.

Usage :
  pip install requests pillow imagehash
  python ml/src/prepare_f17k.py --csv ml/data/raw/fitzpatrick17k/fitzpatrick17k.csv \
      --root ml/data/raw/fitzpatrick17k/images --out ml/data/manifest_f17k.csv
"""
from __future__ import annotations

import argparse
import time
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from PIL import Image

from data_utils import map_label

# Étiquettes Fitzpatrick17k retenues explicitement (évite les faux amis, ex. seborrheic dermatitis).
KEEP = {
    "scabies": "gale",
    "eczema": "eczema",
    "dyshidrotic eczema": "eczema",
    "allergic contact dermatitis": "eczema",
    "tungiasis": "tungiase",
}
UA = "DermIA-research/0.1 (recherche non commerciale)"


def select_rows(df: pd.DataFrame, n_other: int, per_label_cap: int, seed: int) -> pd.DataFrame:
    df = df.copy()
    df["raw_label"] = df["label"].astype(str).str.lower().str.strip()
    kept = df[df["raw_label"].isin(KEEP)].copy()
    kept["label"] = kept["raw_label"].map(KEEP)
    others = df[(~df["raw_label"].isin(KEEP)) & (df["three_partition_label"] == "non-neoplastic")]
    # on écarte tout ce que map_label rattacherait à une de nos classes (sécurité)
    others = others[others["raw_label"].map(map_label) == "autre"]
    others = others.groupby("raw_label", group_keys=False).apply(
        lambda g: g.sample(min(len(g), per_label_cap), random_state=seed))
    if len(others) > n_other:
        others = others.sample(n_other, random_state=seed)
    others = others.assign(label="autre")
    out = pd.concat([kept, others], ignore_index=True)
    out["fst"] = pd.to_numeric(out["fitzpatrick_scale"], errors="coerce").where(lambda s: s > 0)
    return out


def download(rows: pd.DataFrame, root: Path, delay: float, retries: int = 2) -> pd.DataFrame:
    root.mkdir(parents=True, exist_ok=True)
    sess = requests.Session()
    sess.headers["User-Agent"] = UA
    ok_paths, failed = [], []
    for i, r in enumerate(rows.itertuples(), 1):
        dest = root / f"{r.md5hash}.jpg"
        if dest.exists():
            ok_paths.append(dest.name)
            continue
        done = False
        for _ in range(retries + 1):
            try:
                resp = sess.get(r.url, timeout=20)
                if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
                    im = Image.open(BytesIO(resp.content)).convert("RGB")
                    im.thumbnail((768, 768))
                    im.save(dest, "JPEG", quality=90)
                    done = True
                    break
            except Exception:
                pass
            time.sleep(delay)
        (ok_paths if done else failed).append(dest.name if done else r.md5hash)
        if i % 50 == 0:
            print(f"{i}/{len(rows)} traitées | {len(ok_paths)} ok | {len(failed)} échecs", flush=True)
        time.sleep(delay)
    print(f"Terminé : {len(ok_paths)} images, {len(failed)} liens morts ou refusés.")
    return rows[rows["md5hash"].apply(lambda h: f"{h}.jpg" in set(ok_paths))].copy()


def cluster_groups(hashes: np.ndarray, thr: int = 6) -> np.ndarray:
    """Regroupe (union-find) les hachages perceptuels 64 bits à distance de Hamming <= thr."""
    n = len(hashes)
    parent = list(range(n))

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for i in range(n - 1):
        x = np.bitwise_xor(hashes[i + 1:], hashes[i])
        d = np.unpackbits(x.view(np.uint8).reshape(-1, 8), axis=1).sum(axis=1)
        for j in np.nonzero(d <= thr)[0]:
            ra, rb = find(i), find(i + 1 + int(j))
            if ra != rb:
                parent[rb] = ra
    return np.array([find(i) for i in range(n)])


def add_groups(df: pd.DataFrame, root: Path) -> pd.DataFrame:
    import imagehash  # import tardif

    hs = []
    for h in df["md5hash"]:
        with Image.open(root / f"{h}.jpg") as im:
            hs.append(np.uint64(int(str(imagehash.phash(im)), 16)))
    roots = cluster_groups(np.array(hs, dtype=np.uint64))
    df = df.copy()
    df["group_id"] = [f"f17k-{r}" for r in roots]
    print(f"{len(df)} images -> {df['group_id'].nunique()} groupes (quasi-doublons fusionnés)")
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--root", required=True, help="dossier des images téléchargées")
    ap.add_argument("--out", default="ml/data/manifest_f17k.csv")
    ap.add_argument("--n_other", type=int, default=600)
    ap.add_argument("--per_label_cap", type=int, default=40)
    ap.add_argument("--delay", type=float, default=1.0, help="pause entre requêtes (s)")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    root = Path(a.root)
    rows = select_rows(pd.read_csv(a.csv), a.n_other, a.per_label_cap, a.seed)
    print(rows["label"].value_counts().to_string())
    rows = download(rows, root, a.delay)
    rows = add_groups(rows, root)
    man = pd.DataFrame({
        "path": rows["md5hash"] + ".jpg", "label": rows["label"], "raw_label": rows["raw_label"],
        "group_id": rows["group_id"], "source": "f17k",
        "license": "CC BY-NC-SA 3.0 (annotations) - usage recherche non commercial", "fst": rows["fst"],
    })
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    man.to_csv(a.out, index=False)
    print(man["label"].value_counts().to_string(), f"\nManifeste écrit : {a.out}")


if __name__ == "__main__":
    main()
