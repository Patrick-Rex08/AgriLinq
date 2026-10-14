from typing import Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# SQLAlchemy 2.0 Base Class
Base = declarative_base()

# SQLAlchemy Engine
# pool_pre_ping checks connection liveness before handing it out
db_url = settings.sync_database_url
connect_args = {}
if "sqlite" in db_url:
    connect_args = {"check_same_thread": False}
elif "psycopg" in db_url:
    connect_args = {"connect_timeout": 3}

try:
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        echo=False,
        connect_args=connect_args
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.warning(f"Could not initialize database engine at startup: {e}")
    engine = None
    SessionLocal = None


def get_db():
    """FastAPI Dependency for database session management."""
    if SessionLocal is None:
        raise RuntimeError("Database engine is not configured.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables defined in Base metadata and safely ensure columns exist."""
    if engine is not None:
        Base.metadata.create_all(bind=engine)
        # Safe column migration for SQLite fallback
        try:
            with engine.connect() as conn:
                cols_crops = [r[1] for r in conn.execute(text("PRAGMA table_info(crop_batches)")).fetchall()]
                if "category" not in cols_crops:
                    conn.execute(text("ALTER TABLE crop_batches ADD COLUMN category VARCHAR(64) DEFAULT 'Grains'"))
                    conn.commit()
                cols_orders = [r[1] for r in conn.execute(text("PRAGMA table_info(buyer_orders)")).fetchall()]
                if "batch_id" not in cols_orders:
                    conn.execute(text("ALTER TABLE buyer_orders ADD COLUMN batch_id VARCHAR(64)"))
                    conn.commit()
                if "total_price" not in cols_orders:
                    conn.execute(text("ALTER TABLE buyer_orders ADD COLUMN total_price FLOAT"))
                    conn.commit()
        except Exception as e:
            logger.debug(f"Column check notice: {e}")



def check_db_connection() -> Dict[str, Any]:
    """
    Safely tests live connectivity to the active database (PostgreSQL or SQLite).
    Returns status and diagnostic details without throwing unhandled exceptions.
    """
    db_target = "sqlite://local.db" if "sqlite" in settings.sync_database_url else f"{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    
    if engine is None:
        return {
            "connected": False,
            "message": "Database engine not initialized. Check your DATABASE_URL or POSTGRES configuration in .env.",
            "target": db_target
        }

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "connected": True,
            "message": f"Database connection verified successfully ({'SQLite' if 'sqlite' in settings.sync_database_url else 'PostgreSQL'}).",
            "target": db_target
        }
    except Exception as e:
        return {
            "connected": False,
            "message": (
                f"Database not reachable at {db_target}. Details: {str(e)}"
            ),
            "target": db_target
        }
