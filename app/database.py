"""
Database Module - Stub Implementation
"""
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
import os

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# Configure SSL and connection args for Supabase
connect_args = {}
engine_args = {
    "echo": False,
    "pool_pre_ping": True,  # Verify connections before using them
    "pool_recycle": 300,     # Recycle connections after 5 minutes
}

if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    # Add SSL configuration for PostgreSQL/Supabase
    connect_args = {
        "sslmode": "require",
        "connect_timeout": 10,
    }
    
    # Disable prepared statements if using Supabase Transaction Pooler
    # Transaction pooler doesn't support PREPARE statements
    if "pooler.supabase.com" in DATABASE_URL:
        engine_args["pool_size"] = 5
        engine_args["max_overflow"] = 10
        # Use NullPool for transaction pooler to avoid connection issues
        from sqlalchemy.pool import NullPool
        engine_args["poolclass"] = NullPool
    
    engine_args["connect_args"] = connect_args

# Create engine with SSL support
engine = create_engine(DATABASE_URL, **engine_args)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Database dependency for FastAPI endpoints.
    Yields a SQLAlchemy session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
