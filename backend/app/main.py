import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.app.core.config import settings
from backend.app.core.database import engine, Base
from backend.app.routers import auth, sync, cases, surveillance, export_dhis2, releases

# Create database tables
Base.metadata.create_all(bind=engine)

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="DermIA: Système de Triage Dermatologique Intelligent et Surveillance Épidémiologique",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files if upload dir exists
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/storage/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include Routers with API prefix
api_v1 = settings.API_V1_STR
app.include_router(auth.router, prefix=api_v1)
app.include_router(sync.router, prefix=api_v1)
app.include_router(cases.router, prefix=api_v1)
app.include_router(cases.reviews_router, prefix=api_v1)
app.include_router(surveillance.router, prefix=api_v1)
app.include_router(export_dhis2.router, prefix=api_v1)
app.include_router(releases.router, prefix=api_v1)

@app.get("/")
def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs": "/docs",
        "api": settings.API_V1_STR
    }

@app.get("/health")
def healthcheck():
    return {"status": "healthy", "database": "connected"}
