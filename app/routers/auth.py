from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from uuid import UUID

from app.database.connection import get_db
from app.database.models import User, ChildProfile
from app.schemas.user import UserCreate, UserResponse, Token
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserResponse)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
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
    
    # Si es niño, creamos su perfil automáticamente
    if new_user.role == 'CHILD':
        child_profile = ChildProfile(user_id=new_user.id)
        db.add(child_profile)
        db.commit()

    return new_user

@router.post("/login", response_model=Token)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

from pydantic import BaseModel

class ChildLoginRequest(BaseModel):
    access_code: str
    pin: str

@router.post("/login/child", response_model=Token)
def login_child(login_data: ChildLoginRequest, db: Session = Depends(get_db)):
    child = db.query(ChildProfile).filter(ChildProfile.access_code == login_data.access_code).first()
    if not child or not child.pin_hash:
        raise HTTPException(status_code=401, detail="Código de acceso incorrecto")
    
    if not verify_password(login_data.pin, child.pin_hash):
        raise HTTPException(status_code=401, detail="PIN incorrecto")
    
    user = db.query(User).filter(User.id == child.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

from app.core.dependencies import get_current_user

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

import random
import string

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    email: str
    code: str
    new_password: str

@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        # Por seguridad no revelamos que el correo no existe
        return {"msg": "Si el correo existe, se ha enviado un código de recuperación."}
    
    # Generar código numérico de 6 dígitos
    code = ''.join(random.choices(string.digits, k=6))
    user.reset_code = code
    db.commit()
    
    # IMPORTANTE: Como no tenemos SMTP, imprimimos el código en la consola del servidor
    # y lo devolvemos en el mensaje para facilitar el desarrollo
    print(f"!!! CÓDIGO DE RECUPERACIÓN PARA {user.email}: {code} !!!")
    
    return {"msg": f"Código generado: {code} (solo en desarrollo)"}

@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or user.reset_code != req.code:
        raise HTTPException(status_code=400, detail="Código inválido o correo incorrecto")
        
    user.password_hash = get_password_hash(req.new_password)
    user.reset_code = None # Invalida el código
    db.commit()
    
    return {"msg": "Contraseña actualizada exitosamente"}
