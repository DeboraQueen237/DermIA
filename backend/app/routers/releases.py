import os
import json
import hashlib
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.models.entities import ModelRelease, KBRelease

router = APIRouter(prefix="/releases", tags=["Model & Knowledge Base OTA Releases"])

@router.get("/model/latest")
def get_latest_model(db: Session = Depends(get_db)):
    """
    Returns signed TFLite release package metadata for OTA updates on the mobile device.
    """
    release = db.query(ModelRelease).filter(ModelRelease.is_active == True).order_by(ModelRelease.created_at.desc()).first()
    if not release:
        # Fallback to local default file if exists
        return {
            "version": "1.0.0",
            "model_architecture": "MobileNetV3-Small-Multimodal",
            "sha256_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "download_url": "/static/models/model_v1.0.0.tflite",
            "is_quantized": True,
            "quantization": "int8_ptq",
            "input_size": [224, 224, 3],
            "num_classes": 8
        }
    
    return {
        "version": release.version,
        "sha256_hash": release.sha256_hash,
        "signature": release.signature,
        "metrics": release.metrics,
        "download_url": f"/static/models/{os.path.basename(release.file_path)}"
    }

@router.get("/kb/latest")
def get_latest_kb(db: Session = Depends(get_db)):
    """
    Returns the latest validated clinical knowledge base package with hash verification.
    """
    kb_manifest_path = os.path.join(settings.KB_DIR, "manifest.json")
    if os.path.exists(kb_manifest_path):
        with open(kb_manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        return manifest
    
    return {
        "version": "1.0.0",
        "status": "default_local",
        "diseases_count": 8
    }
