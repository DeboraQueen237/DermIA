"""Utilitaires de données DermIA : étiquettes, manifeste, découpage par patient."""
from __future__ import annotations

import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

REQUIRED = ["path", "label", "group_id", "source", "license"]

# Ordre important : le premier mot-clé trouvé gagne.
LABEL_KEYWORDS: list[tuple[str, list[str]]] = [
    ("buruli", ["buruli", "mycobacterium ulcerans"]),
    ("lepre", ["leprosy", "lepra", "hansen"]),
    ("pian", ["yaws"]),
    ("gale", ["scabies"]),
    ("tungiase", ["tungiasis"]),
    ("impetigo", ["impetigo"]),
    ("teigne_mycose", ["tinea", "ringworm", "fungal", "dermatophyt", "candid", "mycosis"]),
    ("eczema", ["eczema", "atopic dermatitis", "contact dermatitis"]),
]


def map_label(raw: str | None) -> str:
    """Convertit une étiquette brute d'un jeu public en classe DermIA ('autre' sinon)."""
    s = (raw or "").lower()
    for label, keys in LABEL_KEYWORDS:
        if any(k in s for k in keys):
            return label
    return "autre"


def load_manifest(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Colonnes manquantes dans le manifeste : {missing}")
    if "fst" not in df.columns:
        df["fst"] = pd.NA
    return df.drop_duplicates(subset="path").reset_index(drop=True)


def make_splits(df: pd.DataFrame, seed: int = 0, min_groups: int = 10) -> pd.DataFrame:
    """
    Ajoute une colonne 'split' (train/val/test/train_only), découpée PAR PATIENT.
    Utilise GroupShuffleSplit pour garantir des proportions 70/15/15 stables.
    """
    from sklearn.model_selection import GroupShuffleSplit

    df = df.copy()
    n_groups = df.groupby("label")["group_id"].nunique()
    rare = set(n_groups[n_groups < min_groups].index)
    df["split"] = "train_only"
    ok = df[~df["label"].isin(rare)]
    if ok.empty or ok["label"].nunique() < 2:
        return df

    # Étape 1 : train (70%) vs temp (30%)
    gss1 = GroupShuffleSplit(n_splits=1, test_size=0.30, random_state=seed)
    train_idx, temp_idx = next(gss1.split(ok, ok["label"], ok["group_id"]))

    train_df = ok.iloc[train_idx]
    temp_df = ok.iloc[temp_idx]

    # Étape 2 : temp → val (50%) / test (50%)
    gss2 = GroupShuffleSplit(n_splits=1, test_size=0.50, random_state=seed)
    val_idx, test_idx = next(gss2.split(temp_df, temp_df["label"], temp_df["group_id"]))

    df.loc[train_df.index, "split"] = "train"
    df.loc[temp_df.iloc[val_idx].index, "split"] = "val"
    df.loc[temp_df.iloc[test_idx].index, "split"] = "test"
    return df


def check_no_leak(df: pd.DataFrame) -> None:
    """Lève une erreur si un même patient apparaît dans plusieurs découpages évalués."""
    ev = df[df["split"].isin(["train", "val", "test"])]
    per_group = ev.groupby("group_id")["split"].nunique()
    leaked = per_group[per_group > 1]
    if len(leaked):
        raise AssertionError(f"{len(leaked)} patients présents dans plusieurs découpages")
