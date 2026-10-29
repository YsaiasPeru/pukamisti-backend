import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database.connection import engine

with engine.begin() as conn:
    try:
        conn.execute(text("ALTER TABLE children_profiles ADD COLUMN IF NOT EXISTS access_code VARCHAR(50) UNIQUE;"))
        conn.execute(text("ALTER TABLE children_profiles ADD COLUMN IF NOT EXISTS pin_hash VARCHAR(255);"))
        print("Migración de base de datos exitosa.")
    except Exception as e:
        print(f"Error: {e}")
