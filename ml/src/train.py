"""Entraînement de référence DermIA (image seule) : MobileNetV3 + calibration + rapport.

Usage (Colab/Kaggle, GPU) :
  python train.py --manifest manifest.csv --root /chemin/images --out runs/v0 --epochs 25
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import timm
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import transforms as T

from data_utils import check_no_leak, load_manifest, make_splits

MEAN, STD = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)


def tf_train(size: int):
    return T.Compose([
        T.RandomResizedCrop(size, scale=(0.6, 1.0)),
        T.RandomHorizontalFlip(), T.RandomVerticalFlip(),
        T.RandomRotation(25),
        T.ColorJitter(brightness=0.25, contrast=0.2, saturation=0.1, hue=0.0),  # pas de hue : préserve la teinte de peau
        T.GaussianBlur(3, sigma=(0.1, 1.5)),
        T.ToTensor(), T.Normalize(MEAN, STD),
    ])


def tf_eval(size: int):
    return T.Compose([T.Resize((size, size)), T.ToTensor(), T.Normalize(MEAN, STD)])


class SkinDS(Dataset):
    def __init__(self, df: pd.DataFrame, root: Path, classes: list[str], tf):
        self.df, self.root, self.tf = df.reset_index(drop=True), root, tf
        self.y = df["label"].map({c: i for i, c in enumerate(classes)}).to_numpy()

    def __len__(self):
        return len(self.df)

    def __getitem__(self, i):
        img = Image.open(self.root / self.df.loc[i, "path"]).convert("RGB")
        return self.tf(img), int(self.y[i])


@torch.no_grad()
def logits_of(model, loader, dev):
    model.eval()
    out, ys = [], []
    for x, y in loader:
        out.append(model(x.to(dev)).float().cpu())
        ys.append(y)
    return torch.cat(out), torch.cat(ys)


def fit_temperature(logits, y) -> float:
    """Mise à l'échelle par température (calibration) sur le jeu de validation."""
    log_t = torch.zeros(1, requires_grad=True)
    opt = torch.optim.LBFGS([log_t], lr=0.1, max_iter=100)

    def closure():
        opt.zero_grad()
        loss = F.cross_entropy(logits / log_t.exp(), y)
        loss.backward()
        return loss

    opt.step(closure)
    return float(log_t.exp())


def ece(probs: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    conf, pred = probs.max(1), probs.argmax(1)
    edges, total = np.linspace(0, 1, bins + 1), 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            total += m.mean() * abs((pred[m] == y[m]).mean() - conf[m].mean())
    return float(total)


def boot_recall_ci(y, pred, k, n=1000, seed=0):
    """IC 95 % (bootstrap) de la sensibilité de la classe k."""
    rng = np.random.default_rng(seed)
    idx = np.where(y == k)[0]
    if len(idx) == 0:
        return None
    vals = [(pred[rng.choice(idx, len(idx))] == k).mean() for _ in range(n)]
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", default="runs/v0")
    ap.add_argument("--arch", default="mobilenetv3_large_100")
    ap.add_argument("--img", type=int, default=224)
    ap.add_argument("--epochs", type=int, default=25)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    torch.manual_seed(a.seed)
    np.random.seed(a.seed)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    df = make_splits(load_manifest(a.manifest), seed=a.seed)
    check_no_leak(df)
    classes = sorted(df["label"].unique())
    evaluated = sorted(df[df.split.isin(["val", "test"])]["label"].unique())
    not_eval = sorted(set(classes) - set(evaluated))
    print("Classes :", classes, "| non évaluées (trop peu de patients) :", not_eval)

    root = Path(a.root)
    trn = df[df.split.isin(["train", "train_only"])]
    val, tst = df[df.split == "val"], df[df.split == "test"]
    ds_tr = SkinDS(trn, root, classes, tf_train(a.img))
    counts = np.bincount(ds_tr.y, minlength=len(classes)).astype(float)
    w = (1.0 / np.sqrt(np.maximum(counts, 1)))[ds_tr.y]
    sampler = WeightedRandomSampler(w, num_samples=len(ds_tr), replacement=True)
    dl_tr = DataLoader(ds_tr, a.batch, sampler=sampler, num_workers=2, drop_last=True)
    dl_va = DataLoader(SkinDS(val, root, classes, tf_eval(a.img)), 64, num_workers=2)
    dl_te = DataLoader(SkinDS(tst, root, classes, tf_eval(a.img)), 64, num_workers=2)

    model = timm.create_model(a.arch, pretrained=True, num_classes=len(classes), drop_rate=0.2).to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=1e-2)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, a.lr, total_steps=a.epochs * len(dl_tr))
    scaler = torch.amp.GradScaler(enabled=dev == "cuda")
    best_f1, best_state = -1.0, None

    for ep in range(a.epochs):
        model.train()
        for x, y in dl_tr:
            x, y = x.to(dev), y.to(dev)
            with torch.autocast(dev, enabled=dev == "cuda"):
                loss = F.cross_entropy(model(x), y, label_smoothing=0.1)
            opt.zero_grad()
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
            sched.step()
        lv, yv = logits_of(model, dl_va, dev)
        f1 = f1_score(yv, lv.argmax(1), average="macro", labels=[classes.index(c) for c in evaluated], zero_division=0)
        print(f"epoch {ep + 1}/{a.epochs}  loss {loss.item():.3f}  val macro-F1 {f1:.3f}")
        if f1 > best_f1:
            best_f1, best_state = f1, {k: v.cpu().clone() for k, v in model.state_dict().items()}

    model.load_state_dict(best_state)
    lv, yv = logits_of(model, dl_va, dev)
    temp = fit_temperature(lv, yv)
    lt, yt = logits_of(model, dl_te, dev)
    probs = F.softmax(lt / temp, 1).numpy()
    yt, pred = yt.numpy(), probs.argmax(1)

    rep = classification_report(yt, pred, labels=range(len(classes)), target_names=classes,
                                output_dict=True, zero_division=0)
    top3 = float(np.mean([yt[i] in np.argsort(-probs[i])[:3] for i in range(len(yt))]))
    metrics = {
        "classes": classes, "non_evaluees": not_eval, "temperature": temp,
        "macro_f1_test": float(f1_score(yt, pred, average="macro", labels=[classes.index(c) for c in evaluated], zero_division=0)),
        "top3_accuracy": top3, "ece": ece(probs, yt),
        "n_test": int(len(yt)), "per_class": rep,
        "recall_ic95": {c: boot_recall_ci(yt, pred, i) for i, c in enumerate(classes)},
        "confusion_matrix": confusion_matrix(yt, pred, labels=range(len(classes))).tolist(),
    }
    if tst["fst"].notna().any():  # équité : sensibilité par type de peau
        fst = pd.to_numeric(tst["fst"], errors="coerce").to_numpy()
        metrics["accuracy_par_fst"] = {
            str(int(f)): {"n": int((fst == f).sum()),
                          "accuracy": float((pred[fst == f] == yt[fst == f]).mean())}
            for f in sorted(np.unique(fst[~np.isnan(fst)]))
        }
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False))
    (out / "labels.json").write_text(json.dumps(classes, ensure_ascii=False))
    torch.save({"state": best_state, "arch": a.arch, "classes": classes,
                "temperature": temp, "img": a.img}, out / "best.pt")
    print(json.dumps({k: metrics[k] for k in ("macro_f1_test", "top3_accuracy", "ece", "n_test")}, indent=2))
    print("Non évaluées :", not_eval)


if __name__ == "__main__":
    main()
