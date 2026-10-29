from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

from app.routers import auth, children, consumption, parents, admin, challenges, cards

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API para la plataforma gamificada Puka Miski",
    version="1.0.0"
)

# Configurar CORS para React Frontend (Local y Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_origin_regex=r"https://.*\.vercel\.app.*|http://localhost:.*|http://127\.0\.0\.1:.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir las rutas (Endpoints)
app.include_router(auth.router)
app.include_router(children.router)
app.include_router(consumption.router)
app.include_router(parents.router)
app.include_router(admin.router)
app.include_router(challenges.router)
app.include_router(cards.router)

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de Puka Miski 🚀"}
