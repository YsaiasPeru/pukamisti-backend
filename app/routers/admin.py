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
from app.database.models import ChildProfile, PointsHistory, ChildChallenge, PukaCard, Reward
from pydantic import BaseModel

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

class CreateCardRequest(BaseModel):
    name: str
    category: str = "NATURALEZA"
    rarity: str = "COMMON"
    description: str
    image_url: str = None

@router.post("/cards")
def create_card(
    payload: CreateCardRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ADMIN.value]))
):
    """Crea una nueva carta en el catálogo oficial de Puka Cards."""
    import random, string
    code = f"PUKA-{random.randint(100, 999)}-{''.join(random.choices(string.ascii_uppercase, k=2))}"
    new_card = PukaCard(
        code=code,
        name=payload.name,
        category=payload.category,
        rarity=payload.rarity,
        description=payload.description,
        image_url=payload.image_url
    )
    db.add(new_card)
    db.commit()
    db.refresh(new_card)
    return new_card

@router.delete("/cards/{card_id}")
def delete_card(
    card_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ADMIN.value]))
):
    """Elimina una carta del catálogo."""
    card = db.query(PukaCard).filter(PukaCard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Carta no encontrada")
    db.delete(card)
    db.commit()
    return {"message": "Carta eliminada con éxito"}

@router.get("/redemptions")
def get_admin_redemptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ADMIN.value]))
):
    """Obtiene el historial de canjes de recompensas realizados por los niños."""
    records = db.query(PointsHistory, ChildProfile, User).join(
        ChildProfile, PointsHistory.child_id == ChildProfile.id
    ).join(
        User, ChildProfile.user_id == User.id
    ).filter(PointsHistory.points < 0).order_by(PointsHistory.created_at.desc()).all()
    
    result = []
    for hist, child, user in records:
        is_delivered = hist.reason.startswith("[Entregado ✅]")
        clean_title = hist.reason.replace("[Entregado ✅] ", "").replace("Canjeó recompensa: ", "").replace("Abrió un sobre de Puka Cards", "Sobre de Puka Cards")
        result.append({
            "id": str(hist.id),
            "child_name": user.name or "Aventurero Puka",
            "access_code": child.access_code or "PUKA-CODE",
            "reward_title": clean_title,
            "points": abs(hist.points),
            "created_at": hist.created_at.isoformat() if hist.created_at else None,
            "status": "DELIVERED" if is_delivered else "PENDING"
        })
    return result

@router.post("/redemptions/{id}/deliver")
def mark_redemption_delivered(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ADMIN.value]))
):
    """Marca un canje como entregado en el stand de la feria."""
    hist = db.query(PointsHistory).filter(PointsHistory.id == id).first()
    if not hist:
        raise HTTPException(status_code=404, detail="Registro de canje no encontrado")
    if not hist.reason.startswith("[Entregado ✅] "):
        hist.reason = f"[Entregado ✅] {hist.reason}"
        db.commit()
    return {"message": "Canje marcado como entregado en stand", "status": "DELIVERED"}
