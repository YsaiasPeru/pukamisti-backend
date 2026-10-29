from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database.connection import get_db
from app.database.models import User, UserRole, ParentProfile
from app.schemas.user import UserResponse, UserCreate
from app.core.security import get_password_hash
from app.core.dependencies import get_current_user, RoleChecker

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ADMIN.value]))
):
    """Obtiene todos los usuarios del sistema. Solo Administradores."""
    return db.query(User).order_by(User.created_at.desc()).all()

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_by_admin(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ADMIN.value]))
):
    """Crea un nuevo usuario (Padre o Admin). Solo Administradores."""
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
        
    hashed_password = get_password_hash(user_in.password)
    new_user = User(
        name=user_in.name,
        email=user_in.email,
        password_hash=hashed_password,
        role=user_in.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Si crea un padre, le inicializamos su perfil
    if new_user.role == UserRole.PARENT:
        parent_profile = ParentProfile(user_id=new_user.id)
        db.add(parent_profile)
        db.commit()
        
    return new_user

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ADMIN.value]))
):
    """Elimina un usuario del sistema permanentemente."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    db.delete(user)
    db.commit()
    return None

from sqlalchemy.sql import func
from app.database.models import ChildProfile, PointsHistory, ChildChallenge

@router.get("/metrics")
def get_admin_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ADMIN.value]))
):
    """Obtener métricas globales para el dashboard de administración."""
    aventureros = db.query(ChildProfile).count()
    
    puntos_totales = db.query(func.sum(PointsHistory.points)).scalar() or 0
    
    retos_completados = db.query(ChildChallenge).filter(ChildChallenge.is_completed == True).count()
    
    return {
        "aventureros_activos": aventureros,
        "puntos_generados": puntos_totales,
        "retos_completados": retos_completados
    }
