from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.database.connection import get_db
from app.database.models import DailyConsumption, ChildProfile
from app.schemas.child import DailyConsumptionCreate, DailyConsumptionResponse
from app.services.points_service import add_points

router = APIRouter(prefix="/consumption", tags=["Consumption & 30-Day Challenge"])

@router.post("/{child_id}", response_model=DailyConsumptionResponse)
def register_consumption(child_id: UUID, consumption_in: DailyConsumptionCreate, db: Session = Depends(get_db)):
    # 1. Validar que el niño exista
    child = db.query(ChildProfile).filter(ChildProfile.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Niño no encontrado")
        
    # 2. Validar que no haya consumido ese día
    existing = db.query(DailyConsumption).filter(
        DailyConsumption.child_id == child_id,
        DailyConsumption.day_number == consumption_in.day_number
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail=f"Ya se registró consumo para el día {consumption_in.day_number}")

    # 3. Registrar el consumo
    points_to_award = 10 # Puntos base por consumo diario
    new_consumption = DailyConsumption(
        child_id=child_id,
        day_number=consumption_in.day_number,
        is_consumed=consumption_in.is_consumed,
        points_earned=points_to_award if consumption_in.is_consumed else 0
    )
    db.add(new_consumption)
    
    # 4. Asignar los puntos si consumió
    if consumption_in.is_consumed:
        add_points(db, child_id, points=points_to_award, reason=f"Consumo diario completado: Día {consumption_in.day_number}")
    
    db.commit()
    db.refresh(new_consumption)
    
    return new_consumption

@router.get("/{child_id}")
def get_consumption_progress(child_id: UUID, db: Session = Depends(get_db)):
    consumptions = db.query(DailyConsumption).filter(DailyConsumption.child_id == child_id).order_by(DailyConsumption.day_number).all()
    return consumptions
