import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from dotenv import load_dotenv

# NOTE:
# load_dotenv works locally
# In Docker, env vars come from docker-compose
load_dotenv()

# ===============================
# Environment variables
# ===============================
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "vehicle_tracking")
POSTGRES_USER = os.getenv("POSTGRES_USER", "tracking_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

# ===============================
# Database URL (psycopg v3 ✅)
# ===============================
DATABASE_URL = (
    f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# ===============================
# SQLAlchemy Engine
# ===============================
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False
)

# ===============================
# Session Factory
# ===============================
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ===============================
# FastAPI Dependency
# ===============================
def get_db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
