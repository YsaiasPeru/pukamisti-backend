from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.database.connection import get_db
from app.database.models import ChildProfile, User
from app.schemas.child import ChildProfileResponse, PlantPhotoUpload, RewardRedeemRequest
from app.services.points_service import get_child_total_points
from app.services.level_service import calculate_level

router = APIRouter(prefix="/children", tags=["Children"])

@router.get("/{id}", response_model=ChildProfileResponse)
def get_child_profile(id: UUID, db: Session = Depends(get_db)):
    profile = db.query(ChildProfile).filter(ChildProfile.id == id).first()
    if not profile:
        # Intenta buscar por user_id
        profile = db.query(ChildProfile).filter(ChildProfile.user_id == id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Perfil de niño no encontrado")
    
    # Calcular puntos y nivel en tiempo real
    total_points = get_child_total_points(db, profile.id)
    level_name = calculate_level(total_points)
    
    # Retornamos dict o seteamos los atributos virtuales (Pydantic los leerá)
    profile.total_points = total_points
    profile.level = level_name
    profile.league = "🥉 Liga Bronce" # Placeholder for league logic
    
    return profile

from app.database.models import Challenge, ChildChallenge, PointsHistory, UserRole
from app.core.dependencies import RoleChecker, get_current_user
from datetime import datetime, timezone

@router.get("/me/challenges")
def get_my_challenges(
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.CHILD.value]))
):
    child = db.query(ChildProfile).filter(ChildProfile.user_id == current_user.id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Perfil de niño no encontrado")
        
    # Get all active challenges
    active_challenges = db.query(Challenge).filter(Challenge.is_active == True).all()
    
    # Check which ones are completed
    completed_challenges = db.query(ChildChallenge.challenge_id).filter(
        ChildChallenge.child_id == child.id,
        ChildChallenge.is_completed == True
    ).all()
    completed_ids = {c[0] for c in completed_challenges}
    
    result = []
    for challenge in active_challenges:
        result.append({
            "id": challenge.id,
            "name": challenge.name,
            "description": challenge.description,
            "points": challenge.points,
            "type": challenge.type,
            "is_completed": challenge.id in completed_ids
        })
        
    return result

@router.post("/me/challenges/{challenge_id}/complete")
def complete_challenge(
    challenge_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.CHILD.value]))
):
    child = db.query(ChildProfile).filter(ChildProfile.user_id == current_user.id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
        
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id, Challenge.is_active == True).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Reto no encontrado o inactivo")
        
    # Check if already completed
    existing = db.query(ChildChallenge).filter(
        ChildChallenge.child_id == child.id,
        ChildChallenge.challenge_id == challenge.id
    ).first()
    
    if existing and existing.is_completed:
        raise HTTPException(status_code=400, detail="Ya completaste este reto")
        
    # Mark as completed
    new_completion = ChildChallenge(
        child_id=child.id,
        challenge_id=challenge.id,
        is_completed=True,
        completed_at=datetime.now(timezone.utc),
        points_earned=challenge.points
    )
    db.add(new_completion)
    
    # Add points history
    history = PointsHistory(
        child_id=child.id,
        points=challenge.points,
        reason=f"Completó el reto: {challenge.name}"
    )
    db.add(history)
    db.commit()
    
    return {"msg": "¡Reto completado!", "points_earned": challenge.points}

from app.database.models import Cultivation, CultivationStatus

@router.get("/me/plant")
def get_my_plant(
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.CHILD.value]))
):
    child = db.query(ChildProfile).filter(ChildProfile.user_id == current_user.id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
        
    plant = db.query(Cultivation).filter(Cultivation.child_id == child.id).first()
    if not plant:
        plant = Cultivation(
            child_id=child.id,
            crop_name="Puka Planta",
            status=CultivationStatus.SIEMBRA,
            water_points=0
        )
        db.add(plant)
        db.commit()
        db.refresh(plant)
        
    return {
        "id": plant.id,
        "crop_name": plant.crop_name,
        "status": plant.status.value,
        "water_points": plant.water_points,
        "photo_siembra": plant.photo_siembra,
        "photo_crecimiento": plant.photo_crecimiento,
        "photo_cosecha": plant.photo_cosecha
    }

@router.post("/me/plant/photo")
def upload_plant_photo(
    payload: PlantPhotoUpload,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.CHILD.value]))
):
    child = db.query(ChildProfile).filter(ChildProfile.user_id == current_user.id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
        
    plant = db.query(Cultivation).filter(Cultivation.child_id == child.id).first()
    if not plant:
        plant = Cultivation(
            child_id=child.id,
            crop_name="Puka Planta",
            status=CultivationStatus.SIEMBRA,
            water_points=0
        )
        db.add(plant)
        db.commit()
        db.refresh(plant)
        
    stage = payload.stage.lower().strip()
    points_awarded = 0
    STAGE_REWARD = 30
    
    if stage == "siembra":
        if not plant.photo_siembra:
            points_awarded = STAGE_REWARD
        plant.photo_siembra = payload.photo_data
    elif stage == "crecimiento":
        if not plant.photo_crecimiento:
            points_awarded = STAGE_REWARD
        plant.photo_crecimiento = payload.photo_data
        if plant.status == CultivationStatus.SIEMBRA:
            plant.status = CultivationStatus.CRECIMIENTO
    elif stage == "cosecha":
        if not plant.photo_cosecha:
            points_awarded = STAGE_REWARD
        plant.photo_cosecha = payload.photo_data
        plant.status = CultivationStatus.COSECHA
        plant.completed_at = datetime.now(timezone.utc)
    else:
        raise HTTPException(status_code=400, detail="Etapa inválida. Usa: siembra, crecimiento o cosecha")
        
    if points_awarded > 0:
        history = PointsHistory(
            child_id=child.id,
            points=points_awarded,
            reason=f"Subió foto del avance de su planta ({stage})"
        )
        db.add(history)
        
    db.commit()
    
    return {
        "msg": f"¡Foto de etapa '{stage}' registrada con éxito!" + (f" ¡Ganaste +{points_awarded} ⭐!" if points_awarded > 0 else ""),
        "points_earned": points_awarded,
        "status": plant.status.value,
        "photo_siembra": plant.photo_siembra,
        "photo_crecimiento": plant.photo_crecimiento,
        "photo_cosecha": plant.photo_cosecha
    }

@router.post("/me/plant/water")
def water_plant(
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.CHILD.value]))
):
    child = db.query(ChildProfile).filter(ChildProfile.user_id == current_user.id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
        
    total_points = get_child_total_points(db, child.id)
    WATER_COST = 10
    
    if total_points < WATER_COST:
        raise HTTPException(status_code=400, detail=f"Necesitas {WATER_COST} ⭐ para regar la planta.")
        
    plant = db.query(Cultivation).filter(Cultivation.child_id == child.id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Planta no encontrada")
        
    if plant.status == CultivationStatus.COSECHA:
        raise HTTPException(status_code=400, detail="¡Tu planta ya dio frutos! Misión cumplida.")
        
    # Deduct points
    history = PointsHistory(
        child_id=child.id,
        points=-WATER_COST,
        reason="Compró agua para su cultivo"
    )
    db.add(history)
    
    # Update plant
    plant.water_points += 1
    
    # Progress logic (3 waters = CRECIMIENTO, 6 waters = COSECHA)
    if plant.water_points >= 6:
        plant.status = CultivationStatus.COSECHA
        plant.completed_at = datetime.now(timezone.utc)
    elif plant.water_points >= 3:
        plant.status = CultivationStatus.CRECIMIENTO
        
    db.commit()
    
    return {
        "msg": "¡Planta regada!",
        "status": plant.status.value,
        "water_points": plant.water_points
    }

@router.get("/me/leaderboard")
def get_my_leaderboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.CHILD.value]))
):
    child = db.query(ChildProfile).filter(ChildProfile.user_id == current_user.id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
        
    my_points = get_child_total_points(db, child.id)
    
    # Calcular liga
    if my_points < 150:
        current_league = "Liga Bronce 🥉"
        league_level = 1
    elif my_points < 350:
        current_league = "Liga Plata 🥈"
        league_level = 2
    elif my_points < 650:
        current_league = "Liga Oro 🥇"
        league_level = 3
    elif my_points < 1000:
        current_league = "Liga Diamante 💎"
        league_level = 4
    else:
        current_league = "Liga Suprema Puka 👑"
        league_level = 5

    # Base de competidores amistosos inspirados en Duolingo
    competitors = [
        {"name": "Mateo Andino", "points": max(my_points + 60, 240), "avatar": "🦊", "is_me": False},
        {"name": "Valeria Nutri", "points": max(my_points + 30, 210), "avatar": "🦙", "is_me": False},
        {"name": current_user.name, "points": my_points, "avatar": "🌟", "is_me": True},
        {"name": "Thiago Cereal", "points": max(my_points - 20, 150), "avatar": "🐻", "is_me": False},
        {"name": "Camila Semilla", "points": max(my_points - 45, 120), "avatar": "🐰", "is_me": False},
        {"name": "Lucas Sangrecita", "points": max(my_points - 70, 95), "avatar": "🦁", "is_me": False},
        {"name": "Sofia Quinua", "points": max(my_points - 90, 80), "avatar": "🐼", "is_me": False},
        {"name": "Joaquín Kiwicha", "points": max(my_points - 110, 60), "avatar": "🐨", "is_me": False},
        {"name": "Mia Hierro", "points": max(my_points - 130, 45), "avatar": "🐯", "is_me": False},
        {"name": "Benjamín Andes", "points": max(my_points - 145, 30), "avatar": "🐵", "is_me": False},
    ]

    # Ordenar por puntos descendente
    competitors.sort(key=lambda x: x["points"], reverse=True)
    
    # Asignar puestos
    my_rank = 1
    for index, comp in enumerate(competitors):
        comp["rank"] = index + 1
        if comp["is_me"]:
            my_rank = index + 1

    return {
        "league": current_league,
        "league_level": league_level,
        "my_points": my_points,
        "my_rank": my_rank,
        "days_left": 3,
        "top_10": competitors
    }

@router.post("/me/rewards/redeem")
def redeem_reward(
    payload: RewardRedeemRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.CHILD.value]))
):
    child = db.query(ChildProfile).filter(ChildProfile.user_id == current_user.id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
        
    total_points = get_child_total_points(db, child.id)
    if total_points < payload.cost:
        raise HTTPException(status_code=400, detail=f"No tienes suficientes estrellas. Necesitas {payload.cost} ⭐ y tienes {total_points} ⭐.")
        
    history = PointsHistory(
        child_id=child.id,
        points=-payload.cost,
        reason=f"Canjeó recompensa: {payload.title}"
    )
    db.add(history)
    db.commit()
    
    new_total = get_child_total_points(db, child.id)
    return {
        "msg": f"¡Felicidades! Has canjeado '{payload.title}' con éxito.",
        "remaining_points": new_total,
        "reward_id": payload.reward_id
    }
