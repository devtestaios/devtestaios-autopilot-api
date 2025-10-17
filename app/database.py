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
}

if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    # Add SSL configuration for PostgreSQL/Supabase
    connect_args = {
        "sslmode": "require",
        "connect_timeout": 10,
    }
    
    # Check connection type and configure appropriately
    if "pooler.supabase.com" in DATABASE_URL:
        # Transaction pooler - use NullPool (no pooling)
        # NullPool doesn't accept pool_size/max_overflow arguments
        from sqlalchemy.pool import NullPool
        engine_args["poolclass"] = NullPool
        print("INFO: Using Supabase Transaction Pooler with NullPool")
    else:
        # Direct connection - use QueuePool with connection pooling
        from sqlalchemy.pool import QueuePool
        engine_args["poolclass"] = QueuePool
        engine_args["pool_size"] = 10
        engine_args["max_overflow"] = 20
        engine_args["pool_pre_ping"] = True
        engine_args["pool_recycle"] = 300
        print("INFO: Using Supabase Direct Connection with QueuePool")
    
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
