import sys
import os
sys.path.insert(0, r"C:\Puka\pukamisti-backend")

from app.database.connection import SessionLocal
from app.database.models import User, UserRole, ParentProfile, ChildProfile, PointsHistory
from app.core.security import get_password_hash

db = SessionLocal()

print("Seeding demo parent and children accounts in Neon DB...")

# 1. Parent: ysaias@gmail.com
parent_user = db.query(User).filter(User.email == "ysaias@gmail.com").first()
if not parent_user:
    parent_user = User(
        name="Ysaias Godoy",
        email="ysaias@gmail.com",
        password_hash=get_password_hash("123456"),
        role=UserRole.PARENT
    )
    db.add(parent_user)
    db.commit()
    db.refresh(parent_user)
    print("Created parent user: ysaias@gmail.com")
else:
    parent_user.password_hash = get_password_hash("123456")
    db.commit()
    print("Updated parent password: ysaias@gmail.com")

parent_profile = db.query(ParentProfile).filter(ParentProfile.user_id == parent_user.id).first()
if not parent_profile:
    parent_profile = ParentProfile(user_id=parent_user.id)
    db.add(parent_profile)
    db.commit()
    db.refresh(parent_profile)
    print("Created parent profile")

# 2. Children
demo_children = [
    {
        "name": "Julieta Quispe",
        "code": "JULIETA-F602",
        "pin": "1234",
        "points": 350,
        "age": 8
    },
    {
        "name": "Junior Flores",
        "code": "JUNIOR-NCF3",
        "pin": "1234",
        "points": 420,
        "age": 10
    },
    {
        "name": "Mateo Condori",
        "code": "PUKA-19XY",
        "pin": "1234",
        "points": 280,
        "age": 7
    }
]

for child_info in demo_children:
    # Check if ChildProfile already exists by access_code
    profile = db.query(ChildProfile).filter(ChildProfile.access_code == child_info["code"]).first()
    if not profile:
        # Create Child User
        child_email = f"{child_info['code'].lower()}@pukamiski.local"
        child_user = db.query(User).filter(User.email == child_email).first()
        if not child_user:
            child_user = User(
                name=child_info["name"],
                email=child_email,
                password_hash=get_password_hash("childpassword"),
                role=UserRole.CHILD
            )
            db.add(child_user)
            db.commit()
            db.refresh(child_user)

        profile = ChildProfile(
            user_id=child_user.id,
            parent_id=parent_profile.id,
            access_code=child_info["code"],
            pin_hash=get_password_hash(child_info["pin"]),
            birth_date=None
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

        # Add initial points in PointsHistory
        history = PointsHistory(
            child_id=profile.id,
            points=child_info["points"],
            reason="Puntos iniciales de bienvenida Puka Miski"
        )
        db.add(history)
        db.commit()
        print(f"Created child: {child_info['name']} | Code: {child_info['code']} | PIN: {child_info['pin']}")
    else:
        profile.pin_hash = get_password_hash(child_info["pin"])
        db.commit()
        print(f"Updated PIN for child: {child_info['name']} ({child_info['code']})")

print("Seeding completed successfully!")
