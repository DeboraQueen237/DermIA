"""
evaluer_tta.py
Évaluation avec Test-Time Augmentation (TTA).
Applique 5 augmentations par image et moyenne les probabilités.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms as T
import timm

from data_utils import load_manifest, make_splits, check_no_leak


MEAN, STD = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)


def tf_tta(size: int, mode: int):
    """5 transformations TTA différentes."""
    if mode == 0:
        return T.Compose([T.Resize((size, size)), T.ToTensor(), T.Normalize(MEAN, STD)])
    elif mode == 1:
        return T.Compose([T.Resize((size, size)), T.RandomHorizontalFlip(p=1.0), T.ToTensor(), T.Normalize(MEAN, STD)])
    elif mode == 2:
        return T.Compose([T.Resize((size, size)), T.RandomVerticalFlip(p=1.0), T.ToTensor(), T.Normalize(MEAN, STD)])
    elif mode == 3:
        return T.Compose([T.Resize((int(size * 1.1), int(size * 1.1))), T.CenterCrop(size), T.ToTensor(), T.Normalize(MEAN, STD)])
    elif mode == 4:
        return T.Compose([T.Resize((size, size)), T.RandomRotation((15, 15)), T.ToTensor(), T.Normalize(MEAN, STD)])


class SkinDS(Dataset):
    def __init__(self, df, root, classes, tf):
        self.df = df.reset_index(drop=True)
        self.root = root
        self.tf = tf
        self.y = df["label"].map({c: i for i, c in enumerate(classes)}).to_numpy()

    def __len__(self):
        return len(self.df)

    def __getitem__(self, i):
        img = Image.open(self.root / self.df.loc[i, "path"]).convert("RGB")
        return self.tf(img), int(self.y[i])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--checkpoint", required=True, help="best.pt sauvegardé")
    ap.add_argument("--out", default="runs/tta")
    ap.add_argument("--n_tta", type=int, default=5)
    a = ap.parse_args()

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device : {dev}")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    # Charger le checkpoint
    print(f"\nChargement de {a.checkpoint}...")
    ckpt = torch.load(a.checkpoint, map_location=dev, weights_only=False)
    classes = ckpt["classes"]
    arch = ckpt["arch"]
    img_size = ckpt.get("img", 224)
    temperature = ckpt.get("temperature", 1.0)
    print(f"  Classes : {classes}")
    print(f"  Arch : {arch}")
    print(f"  Image size : {img_size}")
    print(f"  Température : {temperature:.4f}")

    # Charger le modèle
    model = timm.create_model(arch, pretrained=False, num_classes=len(classes)).to(dev)
    model.load_state_dict(ckpt["state"])
    model.eval()

    # Préparer les données
    df = make_splits(load_manifest(a.manifest), seed=0)
    check_no_leak(df)
    test_df = df[df.split == "test"]
    print(f"\nImages test : {len(test_df)}")

    # TTA : N forward passes avec transformations différentes
    all_probs = []
    y_true = None

    for mode in range(a.n_tta):
        print(f"\n[TTA {mode + 1}/{a.n_tta}] Transformation mode {mode}")
        ds = SkinDS(test_df, Path(a.root), classes, tf_tta(img_size, mode))
        dl = DataLoader(ds, batch_size=64, num_workers=2, shuffle=False)

        probs_list = []
        y_list = []
        with torch.no_grad():
            for x, y in dl:
                x = x.to(dev)
                logits = model(x)
                probs = F.softmax(logits / temperature, dim=1).cpu().numpy()
                probs_list.append(probs)
                y_list.append(y.numpy())

        probs = np.concatenate(probs_list, axis=0)
        all_probs.append(probs)
        if y_true is None:
            y_true = np.concatenate(y_list, axis=0)
        print(f"  Précision brute : {(probs.argmax(1) == y_true).mean():.4f}")

    # Moyenne des probabilités TTA
    avg_probs = np.mean(all_probs, axis=0)
    pred_tta = avg_probs.argmax(1)

    # Précision simple (sans TTA) pour comparaison
    pred_simple = all_probs[0].argmax(1)

    print("\n" + "=" * 60)
    print("RÉSULTATS")
    print("=" * 60)
    print(f"Sans TTA - macro-F1 : {f1_score(y_true, pred_simple, average='macro'):.4f}")
    print(f"Avec TTA - macro-F1 : {f1_score(y_true, pred_tta, average='macro'):.4f}")
    print(f"Gain TTA : {f1_score(y_true, pred_tta, average='macro') - f1_score(y_true, pred_simple, average='macro'):+.4f}")

    # Top-3 avec TTA
    top3 = np.mean([y_true[i] in np.argsort(-avg_probs[i])[:3] for i in range(len(y_true))])
    print(f"Top-3 accuracy : {top3:.4f}")

    # Rapport détaillé
    report = classification_report(
        y_true, pred_tta,
        labels=range(len(classes)),
        target_names=classes,
        output_dict=True,
        zero_division=0,
    )
    print("\nRapport par classe :")
    for c in classes:
        print(f"  {c:<25} F1={report[c]['f1-score']:.3f} "
              f"Préc={report[c]['precision']:.3f} Rappel={report[c]['recall']:.3f}")

    # Sauvegarder
    metrics = {
        "macro_f1_sans_tta": float(f1_score(y_true, pred_simple, average="macro")),
        "macro_f1_avec_tta": float(f1_score(y_true, pred_tta, average="macro")),
        "top3_accuracy": float(top3),
        "n_test": len(y_true),
        "n_tta": a.n_tta,
        "per_class": report,
        "confusion_matrix": confusion_matrix(y_true, pred_tta).tolist(),
    }
    (out / "metrics_tta.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False))
    print(f"\nMétriques sauvegardées : {out / 'metrics_tta.json'}")


if __name__ == "__main__":
    main()