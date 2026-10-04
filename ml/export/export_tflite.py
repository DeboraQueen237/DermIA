"""Conversion PyTorch -> TFLite avec ai-edge-torch, calibration incluse, + test d'équivalence.

À exécuter sous Linux/WSL2, dans un environnement dédié :
  pip install ai-edge-torch timm torch
  python export_tflite.py --ckpt runs/v0/best.pt --out dermia_v0.tflite
Entrée du modèle : image 1x3xHxW (NCHW), float32, normalisée (moyenne/écart-type ImageNet).
Sortie : probabilités calibrées par classe (softmax avec température).
"""
import argparse
import json
from pathlib import Path

import numpy as np
import timm
import torch
import torch.nn as nn


class Calibrated(nn.Module):
    def __init__(self, net, temperature: float):
        super().__init__()
        self.net, self.t = net, temperature

    def forward(self, x):
        return torch.softmax(self.net(x) / self.t, dim=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--out", default="dermia_v0.tflite")
    a = ap.parse_args()

    ck = torch.load(a.ckpt, map_location="cpu")
    net = timm.create_model(ck["arch"], pretrained=False, num_classes=len(ck["classes"]))
    net.load_state_dict(ck["state"])
    model = Calibrated(net, ck["temperature"]).eval()

    sample = (torch.randn(1, 3, ck["img"], ck["img"]),)
    import ai_edge_torch  # import tardif : dépendance lourde

    edge = ai_edge_torch.convert(model, sample)
    edge.export(a.out)

    # Équivalence PyTorch vs TFLite sur plusieurs entrées aléatoires
    worst = 0.0
    for _ in range(5):
        x = (torch.randn(1, 3, ck["img"], ck["img"]),)
        ref = model(*x).detach().numpy()
        got = np.asarray(edge(*x))
        worst = max(worst, float(np.abs(ref - got).max()))
    size_mb = Path(a.out).stat().st_size / 1e6
    print(f"Taille : {size_mb:.1f} Mo | écart max PyTorch/TFLite : {worst:.2e}")
    assert worst < 1e-3, "Écart trop grand : conversion à vérifier"
    Path(a.out).with_suffix(".labels.json").write_text(json.dumps(ck["classes"], ensure_ascii=False))


if __name__ == "__main__":
    main()
