import json
from pathlib import Path
import pytest
import jsonschema

def test_kb_schema_validation():
    kb_dir = Path("knowledge_base")
    schema_path = kb_dir / "schema.json"
    assert schema_path.exists()
    
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
        
    disease_files = [f for f in kb_dir.glob("*.json") if f.name not in ["schema.json", "manifest.json"]]
    assert len(disease_files) == 8, f"Expected 8 disease files, got {len(disease_files)}"
    
    for f in disease_files:
        with open(f, "r", encoding="utf-8") as dfile:
            data = json.load(dfile)
        # Validate against schema
        jsonschema.validate(instance=data, schema=schema)
