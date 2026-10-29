import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database.connection import SessionLocal
from app.database.models import User, UserRole
from app.core.security import get_password_hash

def seed_admin():
    db: Session = SessionLocal()
    try:
        admin_email = "admin@pukamiski.com"
        admin = db.query(User).filter(User.email == admin_email).first()
        
        if not admin:
            admin_user = User(
                name="Súper Administrador",
                email=admin_email,
                password_hash=get_password_hash("admin123"),
                role=UserRole.ADMIN
            )
            db.add(admin_user)
            db.commit()
            print("Administrador creado con exito (admin@pukamiski.com / admin123)")
        else:
            print("El administrador ya existe.")
    except Exception as e:
        print(f"Error al crear admin: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin()
