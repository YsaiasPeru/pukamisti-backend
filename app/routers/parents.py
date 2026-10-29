from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import random
import string

from app.database.connection import get_db
from app.database.models import User, ChildProfile, ParentProfile, UserRole
from app.schemas.child import ChildProfileResponse, ChildCreateByParent, ChildStatsResponse
from app.core.security import get_password_hash
from app.core.dependencies import get_current_user, RoleChecker
from app.services.points_service import get_child_total_points
from app.services.level_service import calculate_level

router = APIRouter(prefix="/parents", tags=["Parents"])

def generate_access_code(name: str) -> str:
    # Ejemplo: MATEO-A1B2
    base = name.strip().upper().split(" ")[0]
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{base}-{suffix}"

@router.get("/me/children", response_model=list[ChildProfileResponse])
def get_my_children(
    db: Session = Depends(get_db), 
    current_user: User = Depends(RoleChecker([UserRole.PARENT.value, UserRole.ADMIN.value]))
):
    from app.database.models import ChildCard, PukaCard, ChildChallenge
    # Encontrar perfil de padre
    parent = db.query(ParentProfile).filter(ParentProfile.user_id == current_user.id).first()
    if not parent:
        # Auto-crear el perfil de padre si no existe
        parent = ParentProfile(user_id=current_user.id)
        db.add(parent)
        db.commit()
        db.refresh(parent)
    
    children = db.query(ChildProfile).filter(ChildProfile.parent_id == parent.id).all()
    total_cards = db.query(PukaCard).count()
    
    for child in children:
        child.total_points = get_child_total_points(db, child.id)
        child.level = calculate_level(child.total_points)
        child.league = "🥉 Liga Bronce"
        
        child.cards_collected = db.query(ChildCard).filter(ChildCard.child_id == child.id).count()
        child.total_cards = total_cards
        child.challenges_completed = db.query(ChildChallenge).filter(ChildChallenge.child_id == child.id, ChildChallenge.is_completed == True).count()
        
    return children

@router.post("/me/children", response_model=ChildProfileResponse)
def create_child(
    child_in: ChildCreateByParent,
    db: Session = Depends(get_db), 
    current_user: User = Depends(RoleChecker([UserRole.PARENT.value, UserRole.ADMIN.value]))
):
    parent = db.query(ParentProfile).filter(ParentProfile.user_id == current_user.id).first()
    if not parent:
        parent = ParentProfile(user_id=current_user.id)
        db.add(parent)
        db.commit()
        db.refresh(parent)
        
    # Crear un Usuario genérico para el niño
    new_user = User(
        name=child_in.name,
        email=f"child_{current_user.id}_{random.randint(1000,9999)}@pukamiski.com", # Email dummy válido
        password_hash=get_password_hash(child_in.pin), # Contraseña por defecto
        role=UserRole.CHILD
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Crear el ChildProfile con código y PIN
    access_code = generate_access_code(child_in.name)
    # Validar unicidad (básico)
    while db.query(ChildProfile).filter(ChildProfile.access_code == access_code).first():
        access_code = generate_access_code(child_in.name)
        
    new_child = ChildProfile(
        user_id=new_user.id,
        parent_id=parent.id,
        access_code=access_code,
        pin_hash=get_password_hash(child_in.pin),
        birth_date=child_in.birth_date,
        avatar=child_in.avatar
    )
    db.add(new_child)
    db.commit()
    db.refresh(new_child)
    
    new_child.total_points = 0
    new_child.level = calculate_level(0)
    new_child.league = "🥉 Liga Bronce"
    
    return new_child

@router.delete("/me/children/{child_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_child(
    child_id: str,
    db: Session = Depends(get_db), 
    current_user: User = Depends(RoleChecker([UserRole.PARENT.value, UserRole.ADMIN.value]))
):
    parent = db.query(ParentProfile).filter(ParentProfile.user_id == current_user.id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Perfil de padre no encontrado")
        
    child = db.query(ChildProfile).filter(ChildProfile.id == child_id, ChildProfile.parent_id == parent.id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Hijo no encontrado o no pertenece a este padre")
        
    # Eliminar el usuario base, lo que en cascada eliminará el ChildProfile
    user = db.query(User).filter(User.id == child.user_id).first()
    if user:
        db.delete(user)
        db.commit()
        
    return None

@router.get("/me/children/{child_id}/stats", response_model=ChildStatsResponse)
def get_child_stats(
    child_id: str,
    db: Session = Depends(get_db), 
    current_user: User = Depends(RoleChecker([UserRole.PARENT.value, UserRole.ADMIN.value]))
):
    from app.database.models import ChildCard, PukaCard, ChildChallenge
    
    parent = db.query(ParentProfile).filter(ParentProfile.user_id == current_user.id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Perfil de padre no encontrado")
        
    child = db.query(ChildProfile).filter(ChildProfile.id == child_id, ChildProfile.parent_id == parent.id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Hijo no encontrado")
        
    total_points = get_child_total_points(db, child.id)
    level = calculate_level(total_points)
    league = "🥉 Liga Bronce"
    
    cards_collected = db.query(ChildCard).filter(ChildCard.child_id == child.id).count()
    total_cards = db.query(PukaCard).count()
    challenges_completed = db.query(ChildChallenge).filter(ChildChallenge.child_id == child.id, ChildChallenge.is_completed == True).count()
    
    return {
        "total_points": total_points,
        "level": level,
        "league": league,
        "cards_collected": cards_collected,
        "total_cards": total_cards,
        "challenges_completed": challenges_completed
    }
