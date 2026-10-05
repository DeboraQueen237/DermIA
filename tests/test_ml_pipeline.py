import pytest
import torch
import numpy as np
from ml.src.fusion_model import DermIAMultimodalNet, get_clinical_feature_encoder
from ml.src.evaluate_equity import compute_ece, evaluate_subgroup_metrics

def test_clinical_encoder_vocab():
    vocab = get_clinical_feature_encoder()
    assert "aspect" in vocab
    assert "demangeaison" in vocab
    assert "douleur" in vocab
    assert vocab["total_dim"] == 16

def test_multimodal_model_forward():
    model = DermIAMultimodalNet(num_classes=8, clinical_dim=16, pretrained=False)
    x_img = torch.randn(2, 3, 224, 224)
    x_clin = torch.randn(2, 16)
    
    logits, confidence = model(x_img, x_clin)
    
    assert logits.shape == (2, 8)
    assert confidence.shape == (2,)
    assert (confidence >= 0.0).all() and (confidence <= 1.0).all()

def test_compute_ece():
    # Perfect calibration: confidence equals accuracy
    probs = np.array([[0.9, 0.1], [0.8, 0.2], [0.1, 0.9]])
    y_true = np.array([0, 0, 1])
    ece = compute_ece(probs, y_true, n_bins=5)
    assert 0.0 <= ece <= 1.0
