from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database.connection import get_db
from app.database.models import Challenge, User, UserRole
from app.schemas.challenge import ChallengeCreate, ChallengeUpdate, ChallengeResponse
from app.core.dependencies import get_current_user, RoleChecker

router = APIRouter(prefix="/challenges", tags=["Challenges"])

@router.get("/", response_model=List[ChallengeResponse])
def get_challenges(db: Session = Depends(get_db)):
    """Listar todos los retos. Público para usuarios autenticados (niños pueden verlos)."""
    return db.query(Challenge).order_by(Challenge.created_at.desc()).all()

@router.post("/", response_model=ChallengeResponse, status_code=status.HTTP_201_CREATED)
def create_challenge(
    challenge_in: ChallengeCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ADMIN.value]))
):
    """Crear un nuevo reto. Solo Administradores."""
    new_challenge = Challenge(**challenge_in.model_dump())
    db.add(new_challenge)
    db.commit()
    db.refresh(new_challenge)
    return new_challenge

@router.put("/{challenge_id}", response_model=ChallengeResponse)
def update_challenge(
    challenge_id: UUID,
    challenge_in: ChallengeUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ADMIN.value]))
):
    """Editar un reto existente. Solo Administradores."""
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Reto no encontrado")
    
    update_data = challenge_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(challenge, key, value)
        
    db.commit()
    db.refresh(challenge)
    return challenge

@router.delete("/{challenge_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_challenge(
    challenge_id: UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ADMIN.value]))
):
    """Eliminar un reto. Solo Administradores."""
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Reto no encontrado")
        
    db.delete(challenge)
    db.commit()
    return None
