from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
import random

from app.database.connection import get_db
from app.database.models import User, ChildProfile, PukaCard, PointsHistory, UserRole, ChildCard
from app.schemas.puka_card import PukaCardResponse
from app.core.dependencies import get_current_user, RoleChecker
from app.services.points_service import get_child_total_points

router = APIRouter(prefix="/cards", tags=["Puka Cards"])

# Sistema Gacha: 70% Común, 20% Rara, 9% Épica, 1% Legendaria
RARITY_WEIGHTS = {
    "COMMON": 0.70,
    "RARE": 0.20,
    "EPIC": 0.09,
    "LEGENDARY": 0.01
}
DRAW_COST = 50 # Puntos requeridos para abrir un sobre

@router.get("/catalog", response_model=list[PukaCardResponse])
def get_card_catalog(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Devuelve todas las cartas existentes en el juego (el catálogo)."""
    return db.query(PukaCard).all()

@router.get("/me", response_model=list[PukaCardResponse])
def get_my_cards(
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.CHILD.value]))
):
    """Devuelve las cartas coleccionadas por el niño."""
    child = db.query(ChildProfile).filter(ChildProfile.user_id == current_user.id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
        
    owned_cards = db.query(PukaCard).join(ChildCard, PukaCard.id == ChildCard.card_id).filter(ChildCard.child_id == child.id).all()
    return owned_cards

@router.post("/me/draw", response_model=PukaCardResponse)
def draw_card(
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.CHILD.value]))
):
    """Abre un sobre de cartas gastando puntos (Sistema Gacha)."""
    child = db.query(ChildProfile).filter(ChildProfile.user_id == current_user.id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
        
    total_points = get_child_total_points(db, child.id)
    if total_points < DRAW_COST:
        raise HTTPException(status_code=400, detail=f"No tienes suficientes puntos. Necesitas {DRAW_COST} ⭐")
        
    # Deduct points
    history = PointsHistory(
        child_id=child.id,
        points=-DRAW_COST,
        reason="Abrió un sobre de Puka Cards"
    )
    db.add(history)
    db.commit()
    
    # Gacha Logic
    all_cards = db.query(PukaCard).all()
    if not all_cards:
        # Si no hay cartas creadas por el admin, creamos unas mock para la demo
        mock_card = PukaCard(code="MOCK-001", name="Guerrero Andino", rarity="COMMON", description="Una carta de prueba")
        db.add(mock_card)
        db.commit()
        db.refresh(mock_card)
        all_cards = [mock_card]

    rand = random.random()
    cumulative = 0.0
    selected_rarity = "COMMON"
    
    for rarity, weight in RARITY_WEIGHTS.items():
        cumulative += weight
        if rand <= cumulative:
            selected_rarity = rarity
            break
            
    # Filter cards by selected rarity
    rarity_cards = [c for c in all_cards if c.rarity == selected_rarity]
    if not rarity_cards:
        # Fallback if no cards of that rarity exist
        rarity_cards = all_cards
        
    drawn_card = random.choice(rarity_cards)
    
    # Guardar en la colección del niño
    child_card = ChildCard(child_id=child.id, card_id=drawn_card.id)
    db.add(child_card)
    db.commit()
    
    return drawn_card
