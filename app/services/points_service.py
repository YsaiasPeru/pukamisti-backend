from sqlalchemy.orm import Session
from app.database.models import PointsHistory, ChildProfile
from uuid import UUID

def add_points(db: Session, child_id: UUID, points: int, reason: str):
    # 1. Crear el registro en el historial
    history = PointsHistory(
        child_id=child_id,
        points=points,
        reason=reason
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    
    return history

def get_child_total_points(db: Session, child_id: UUID) -> int:
    from sqlalchemy.sql import func
    total = db.query(func.sum(PointsHistory.points)).filter(PointsHistory.child_id == child_id).scalar()
    return total or 0
