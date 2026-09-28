"""
ShadowLink — SQLAlchemy engine & session setup.
Reads DATABASE_URL from backend/.env via python-dotenv.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# ── Load .env from the backend root ─────────────────────────
_env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=_env_path)

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/shadowlink",
)

# ── Engine ───────────────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # recycle stale connections
    pool_size=5,
    max_overflow=10,
    echo=False,               # set True for SQL debug logging
)

# ── Session factory ──────────────────────────────────────────
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ── Declarative base for ORM models ─────────────────────────
Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
