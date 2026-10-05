from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import verify_password, create_access_token, decode_access_token, get_password_hash
from backend.app.models.entities import HealthWorker, Facility
from backend.app.schemas.dtos import Token, HealthWorkerResponse, LoginRequest

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)

def get_current_worker(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> HealthWorker:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token d'authentification manquant",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton d'authentification invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )
    worker_id: str = payload.get("sub")
    worker = db.query(HealthWorker).filter(HealthWorker.id == worker_id, HealthWorker.active == True).first()
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent de santé non trouvé ou inactif",
        )
    return worker

def require_role(*allowed_roles: str):
    def role_checker(current_worker: HealthWorker = Depends(get_current_worker)):
        if current_worker.role not in allowed_roles and current_worker.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action non autorisée pour le rôle '{current_worker.role}'. Rôles requis: {allowed_roles}"
            )
        return current_worker
    return role_checker

@router.post("/login", response_model=Token)
def login_json(credentials: LoginRequest, db: Session = Depends(get_db)):
    worker = db.query(HealthWorker).filter(HealthWorker.email == credentials.email).first()
    if not worker or not verify_password(credentials.password, worker.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects (email ou mot de passe invalide)",
        )
    if not worker.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte agent de santé désactivé",
        )
    
    access_token = create_access_token(subject=worker.id, role=worker.role)
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=worker.role,
        worker_id=worker.id,
        full_name=worker.full_name
    )

@router.post("/token", response_model=Token)
def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    worker = db.query(HealthWorker).filter(HealthWorker.email == form_data.username).first()
    if not worker or not verify_password(form_data.password, worker.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects",
        )
    access_token = create_access_token(subject=worker.id, role=worker.role)
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=worker.role,
        worker_id=worker.id,
        full_name=worker.full_name
    )

@router.get("/me", response_model=HealthWorkerResponse)
def read_current_worker(current_worker: HealthWorker = Depends(get_current_worker)):
    return current_worker
