"""
Architecture de Fusion Multimodale DermIA :
Combine les caractéristiques visuelles (MobileNetV3) et les variables cliniques (Questionnaire)
avec modulation FiLM (Feature-wise Linear Modulation) et tête d'abstention (confiance).
"""
from __future__ import annotations
import torch
import torch.nn as nn
import torch.nn.functional as F
import timm

class ClinicalFeatureEncoder(nn.Module):
    """
    Encodeur pour le vecteur clinique tabulaire issu du questionnaire ASC.
    Entrées : [aspect, démangeaison, douleur, durée, foyer_familial, zone, âge]
    """
    def __init__(self, clinical_dim: int, hidden_dim: int = 64, out_dim: int = 128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(clinical_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, out_dim),
            nn.BatchNorm1d(out_dim),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class FiLMLayer(nn.Module):
    """
    Feature-wise Linear Modulation (FiLM) :
    Modifie les features visuelles par mise à l'échelle (gamma) et décalage (beta)
    conditionnés par les réponses cliniques du patient.
    """
    def __init__(self, clinical_dim: int, feature_dim: int):
        super().__init__()
        self.generator = nn.Linear(clinical_dim, feature_dim * 2)

    def forward(self, visual_feat: torch.Tensor, clinical_feat: torch.Tensor) -> torch.Tensor:
        # visual_feat: [B, D], clinical_feat: [B, C]
        gamma_beta = self.generator(clinical_feat)
        gamma, beta = torch.chunk(gamma_beta, 2, dim=-1)
        # FiLM operation: gamma * x + beta
        return (1.0 + gamma) * visual_feat + beta


class DermIAMultimodalNet(nn.Module):
    """
    Réseau multimodal complet DermIA :
    - Image : Backbone MobileNetV3-Small / Large (pré-entraîné ImageNet)
    - Clinique : MLP Encodeur
    - Fusion : FiLM conditionné + tête de classification avec score d'abstention
    """
    def __init__(
        self,
        num_classes: int = 8,
        clinical_dim: int = 16,
        backbone_name: str = "mobilenetv3_small_100",
        pretrained: bool = True,
        dropout_rate: float = 0.3
    ):
        super().__init__()
        # Backbone visuel
        self.backbone = timm.create_model(backbone_name, pretrained=pretrained, num_classes=0)
        with torch.no_grad():
            dummy = torch.zeros(1, 3, 224, 224)
            visual_dim = self.backbone(dummy).shape[-1]

        # Encodeur clinique
        self.clinical_encoder = ClinicalFeatureEncoder(clinical_dim=clinical_dim, out_dim=64)

        # Module de modulation FiLM
        self.film = FiLMLayer(clinical_dim=64, feature_dim=visual_dim)

        # Tête de classification finale
        self.classifier = nn.Sequential(
            nn.Dropout(dropout_rate),
            nn.Linear(visual_dim + 64, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout_rate / 2),
            nn.Linear(128, num_classes)
        )

        # Tête d'abstention (confiance / détection hors-distribution)
        self.abstention_head = nn.Sequential(
            nn.Linear(visual_dim + 64, 32),
            nn.ReLU(inplace=True),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

    def forward(self, img: torch.Tensor, clinical_vector: torch.Tensor):
        # Extraction visuelle
        vis_features = self.backbone(img) # [B, visual_dim]

        # Encodage clinique
        clin_features = self.clinical_encoder(clinical_vector) # [B, 64]

        # Modulation FiLM
        modulated_vis = self.film(vis_features, clin_features) # [B, visual_dim]

        # Fusion multimodale par concaténation
        fused = torch.cat([modulated_vis, clin_features], dim=-1) # [B, visual_dim + 64]

        # Sorties
        logits = self.classifier(fused)
        confidence = self.abstention_head(fused).squeeze(-1) # score [0, 1]

        return logits, confidence


def get_clinical_feature_encoder():
    """
    Vocabulaire de mapping pour encoder les réponses en one-hot / vecteur continu.
    """
    aspect_map = {"ulcère": 0, "nodule": 1, "tache": 2, "plaque": 3, "papule": 4, "autre": 5}
    demangeaison_map = {"non": 0, "moderee": 1, "intense_nuit": 2}
    douleur_map = {"non": 0, "oui": 1}
    duree_map = {"court": 0, "moyen": 1, "long": 2}
    
    return {
        "aspect": aspect_map,
        "demangeaison": demangeaison_map,
        "douleur": douleur_map,
        "duree": duree_map,
        "total_dim": 16
    }
