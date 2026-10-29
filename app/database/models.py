import uuid
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Date, DateTime, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database.connection import Base

# Enums
class UserRole(str, enum.Enum):
    ADMIN = 'ADMIN'
    PARENT = 'PARENT'
    CHILD = 'CHILD'

class ChallengeType(str, enum.Enum):
    DAILY = 'DAILY'
    WEEKLY = 'WEEKLY'
    SPECIAL = 'SPECIAL'

class CultivationStatus(str, enum.Enum):
    SIEMBRA = 'SIEMBRA'
    CRECIMIENTO = 'CRECIMIENTO'
    COSECHA = 'COSECHA'
    DEVOLUCION = 'DEVOLUCION'

class RedemptionStatus(str, enum.Enum):
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    DELIVERED = 'DELIVERED'

# Models
class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    reset_code = Column(String(6), nullable=True) # Código de 6 dígitos
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ParentProfile(Base):
    __tablename__ = "parent_profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
class ChildProfile(Base):
    __tablename__ = "children_profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("parent_profiles.id", ondelete="SET NULL"), nullable=True)
    birth_date = Column(Date)
    avatar = Column(String(255))
    access_code = Column(String(50), unique=True, index=True, nullable=True) # Para login de niños
    pin_hash = Column(String(255), nullable=True) # PIN de 4 dígitos hasheado
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Challenge(Base):
    __tablename__ = "challenges"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    points = Column(Integer, default=0, nullable=False)
    type = Column(SQLEnum(ChallengeType), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ChildChallenge(Base):
    __tablename__ = "child_challenges"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id = Column(UUID(as_uuid=True), ForeignKey("children_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    challenge_id = Column(UUID(as_uuid=True), ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True))
    points_earned = Column(Integer, default=0)

class DailyConsumption(Base):
    __tablename__ = "daily_consumption"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id = Column(UUID(as_uuid=True), ForeignKey("children_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    day_number = Column(Integer, nullable=False)
    is_consumed = Column(Boolean, default=False)
    points_earned = Column(Integer, default=0)
    registered_at = Column(DateTime(timezone=True), server_default=func.now())

class Cultivation(Base):
    __tablename__ = "cultivations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id = Column(UUID(as_uuid=True), ForeignKey("children_profiles.id", ondelete="CASCADE"), nullable=False)
    crop_name = Column(String(100), nullable=False)
    status = Column(SQLEnum(CultivationStatus), default=CultivationStatus.SIEMBRA)
    water_points = Column(Integer, default=0)
    photo_siembra = Column(Text, nullable=True)
    photo_crecimiento = Column(Text, nullable=True)
    photo_cosecha = Column(Text, nullable=True)
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

class PointsHistory(Base):
    __tablename__ = "points_history"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id = Column(UUID(as_uuid=True), ForeignKey("children_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    points = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PukaCard(Base):
    __tablename__ = "puka_cards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, index=True)
    name = Column(String)
    description = Column(String)
    image_url = Column(String, nullable=True)
    rarity = Column(String) # COMMON, RARE, EPIC, LEGENDARY
    category = Column(String, default="NATURALEZA") # NATURALEZA, VALORES, CULTURA, HABILIDADES")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ChildCard(Base):
    __tablename__ = "child_cards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id = Column(UUID(as_uuid=True), ForeignKey("children_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    card_id = Column(UUID(as_uuid=True), ForeignKey("puka_cards.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Reward(Base):
    __tablename__ = "rewards"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    points_required = Column(Integer, nullable=False)
    image_url = Column(String(255))
    stock = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
