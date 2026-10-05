import sys
import os
import uvicorn

# Reconfigure stdout for Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if __name__ == "__main__":
    print("🚀 Démarrage du serveur DermIA FastAPI sur http://127.0.0.1:8000...")
    print("📖 Documentation interactive Swagger disponible sur http://127.0.0.1:8000/docs")
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
