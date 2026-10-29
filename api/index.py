import sys
import os

# Asegurar que la raíz del backend esté en sys.path para Vercel
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
