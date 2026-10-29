import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database.connection import engine

with engine.begin() as conn:
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_code VARCHAR(6);"))
        print("Migración de tabla users (reset_code) exitosa.")
    except Exception as e:
        print(f"Error: {e}")
