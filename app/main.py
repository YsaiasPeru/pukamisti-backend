from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import traceback
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
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:4173",
        "https://pukamiski-frontend.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app.*|http://localhost:.*|http://127\.0\.0\.1:.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Manejador global de excepciones para asegurar que errores 500 no rompan CORS y muestren el detalle
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    response = JSONResponse(
        status_code=500,
        content={"detail": str(exc), "error_type": type(exc).__name__}
    )
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response

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
