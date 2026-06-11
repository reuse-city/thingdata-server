from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

settings = get_settings()

connect_args = {}
engine_kwargs = {
    "pool_pre_ping": True
}

if settings.DATABASE_URL.startswith("postgresql"):
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 10
elif settings.DATABASE_URL.startswith("sqlite"):
    from sqlalchemy.pool import StaticPool
    connect_args["check_same_thread"] = False
    engine_kwargs["poolclass"] = StaticPool

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    **engine_kwargs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Check and dynamically add missing columns
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    
    # Check stories
    columns = [col['name'] for col in inspector.get_columns('stories')]
    with engine.begin() as conn:
        if 'author' not in columns:
            conn.execute(text("ALTER TABLE stories ADD COLUMN author JSON"))
        if 'metadata' not in columns:
            conn.execute(text("ALTER TABLE stories ADD COLUMN metadata JSON"))
        if 'prerequisites' not in columns:
            conn.execute(text("ALTER TABLE stories ADD COLUMN prerequisites JSON"))
            
    # Check guides
    columns = [col['name'] for col in inspector.get_columns('guides')]
    with engine.begin() as conn:
        if 'source' not in columns:
            conn.execute(text("ALTER TABLE guides ADD COLUMN source JSON"))
        if 'external_content' not in columns:
            conn.execute(text("ALTER TABLE guides ADD COLUMN external_content JSON"))