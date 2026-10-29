from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Como usamos psycopg3 en vez de psycopg2 (por compatibilidad con Python 3.14),
# necesitamos ajustar el prefijo de la URL para que SQLAlchemy sepa qué driver usar.
DEFAULT_FALLBACK_URL = "postgresql://neondb_owner:npg_0mHtwgxsThR3@ep-steep-sunset-aesz7s5q-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require"
db_url = settings.DATABASE_URL or DEFAULT_FALLBACK_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(
    db_url,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency moved to core/dependencies.py, but get_db should be here
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
