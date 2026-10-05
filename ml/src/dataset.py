"""
dataset.py
Classe Dataset PyTorch pour DermIA (classification Lèpre/Non-Lèpre).
"""

from pathlib import Path

import pandas as pd
import torch
from PIL import Image
from torch.utils.data import Dataset, WeightedRandomSampler
from torchvision import transforms


# ═══════════════════════════════════════════════════════════════════════════
#   TRANSFORMATIONS D'IMAGES
# ═══════════════════════════════════════════════════════════════════════════

# Pour l'entraînement : avec augmentation
TRAIN_TRANSFORMS = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    transforms.RandomRotation(30),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
    transforms.RandomAffine(degrees=15, translate=(0.1, 0.1), scale=(0.9, 1.1)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# Pour validation/test : sans augmentation
VAL_TRANSFORMS = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


# ═══════════════════════════════════════════════════════════════════════════
#   CLASSE DATASET
# ═══════════════════════════════════════════════════════════════════════════

class LeprosyDataset(Dataset):
    """
    Dataset binaire : Lèpre (1) vs Non-Lèpre (0).
    Utilise uniquement AI-Leprosy.
    """

    def __init__(self, manifest_path, split="train", transform=None):
        """
        Args:
            manifest_path: chemin vers manifest_global.csv
            split: "train", "valid" ou "test"
            transform: transformations torchvision à appliquer
        """
        self.transform = transform or (TRAIN_TRANSFORMS if split == "train" else VAL_TRANSFORMS)

        # Charger le manifest
        df = pd.read_csv(manifest_path)

        # Filtrer : AI-Leprosy uniquement + split demandé
        df = df[df["dataset"] == "AI-Leprosy"].copy()
        df = df[df["split"] == split].copy()

        # Filtrer : labels valides uniquement
        df = df[df["label"].isin(["leprosy", "non_leprosy"])].copy()

        # Encoder les labels en 0/1
        df["label_encoded"] = (df["label"] == "leprosy").astype(int)

        self.df = df.reset_index(drop=True)

        print(f"[{split}] {len(self.df)} images "
              f"({(self.df['label_encoded'] == 1).sum()} lèpre / "
              f"{(self.df['label_encoded'] == 0).sum()} non-lèpre)")

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_path = Path(row["image_path"])

        # Charger l'image
        try:
            image = Image.open(img_path).convert("RGB")
        except Exception as e:
            print(f"ERREUR lors du chargement de {img_path} : {e}")
            # Retourner une image noire en cas d'erreur
            image = Image.new("RGB", (224, 224), (0, 0, 0))

        # Appliquer les transformations
        if self.transform:
            image = self.transform(image)

        label = int(row["label_encoded"])
        return image, label

    def get_sampler(self):
        """Retourne un WeightedRandomSampler pour compenser le déséquilibre."""
        labels = self.df["label_encoded"].values
        class_counts = pd.Series(labels).value_counts().sort_index()
        class_weights = 1.0 / class_counts
        sample_weights = [class_weights[label] for label in labels]

        sampler = WeightedRandomSampler(
            weights=sample_weights,
            num_samples=len(sample_weights),
            replacement=True,
        )
        return sampler


# ═══════════════════════════════════════════════════════════════════════════
#   TEST RAPIDE
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    manifest = "ml/data/manifest_global.csv"

    print("=" * 60)
    print("TEST DU DATASET LEPROSY")
    print("=" * 60)

    for split in ["train", "valid", "test"]:
        ds = LeprosyDataset(manifest, split=split)
        if len(ds) > 0:
            img, label = ds[0]
            print(f"  Shape image : {img.shape}")
            print(f"  Label : {label}")
        print()