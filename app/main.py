from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime
import psutil

from app.database import get_db, Base, engine
from app.models import Thing, Story, Relationship
from app.schemas import (
    ThingCreate, ThingResponse,
    StoryCreate, StoryResponse,
    RelationshipCreate, RelationshipResponse,
    HealthResponse, ComponentStatus
)
from app.logger import setup_logger

logger = setup_logger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ThingData Server",
    description="ThingData Protocol v1.0 Implementation - Federated Repair Knowledge Network",
    version="0.1.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Get API information and documentation links."""
    return {
        "name": "ThingData API",
        "version": "0.1.0",
        "description": "ThingData Protocol v1.0 Implementation - Federated Repair Knowledge Network",
        "documentation": "/docs",
        "openapi_schema": "/openapi.json",
        "redoc_documentation": "/redoc",
        "health": "/health",
        "endpoints": {
            "things": "/api/v1/things",
            "stories": "/api/v1/stories",
            "relationships": "/api/v1/relationships"
        },
        "repository": "https://github.com/reuse-city/thingdata-server",
        "contact": {
            "name": "ThingData Team",
            "website": "https://thingdata.org",
            "email": "contact@thingdata.org"
        }
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    try:
        # Check database
        db = next(get_db())
        db.execute("SELECT 1")
        db_status = ComponentStatus.HEALTHY
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = ComponentStatus.UNHEALTHY

    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent()

    return {
        "status": "healthy" if db_status == ComponentStatus.HEALTHY else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
        "components": {
            "database": db_status,
            "api": ComponentStatus.HEALTHY
        },
        "metrics": {
            "memory_usage": memory.percent,
            "cpu_usage": cpu_percent,
            "active_connections": 0
        }
    }

# Thing endpoints
@app.post("/api/v1/things", response_model=ThingResponse)
async def create_thing(thing: ThingCreate, db: Session = Depends(get_db)):
    """Create a new thing."""
    try:
        db_thing = Thing(
            id=str(uuid.uuid4()),
            uri=f"thing:{thing.type}/{thing.manufacturer.name}/{thing.name.default}",
            type=thing.type,
            name=thing.name.dict(),
            manufacturer=thing.manufacturer.dict(),
            properties=thing.properties.dict() if thing.properties else {},
            created_at=datetime.utcnow()
        )
        
        db.add(db_thing)
        db.commit()
        db.refresh(db_thing)
        
        logger.info(f"Created thing: {db_thing.id}")
        return db_thing
    except Exception as e:
        logger.error(f"Failed to create thing: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/things/{thing_id}", response_model=ThingResponse)
async def get_thing(thing_id: str, db: Session = Depends(get_db)):
    """Get a specific thing."""
    thing = db.query(Thing).filter(Thing.id == thing_id).first()
    if not thing:
        raise HTTPException(status_code=404, detail="Thing not found")
    return thing

@app.get("/api/v1/things", response_model=List[ThingResponse])
async def list_things(
    skip: int = 0,
    limit: int = 100,
    type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all things with optional filtering."""
    query = db.query(Thing)
    if type:
        query = query.filter(Thing.type == type)
    return query.offset(skip).limit(limit).all()

# Story endpoints
@app.post("/api/v1/stories", response_model=StoryResponse)
async def create_story(story: StoryCreate, db: Session = Depends(get_db)):
    """Create a new repair story."""
    try:
        thing = db.query(Thing).filter(Thing.id == story.thing_id).first()
        if not thing:
            raise HTTPException(status_code=404, detail=f"Thing {story.thing_id} not found")

        story_db = Story(
            id=str(uuid.uuid4()),
            thing_id=story.thing_id,
            type=story.type,
            version={
                "number": "1.0.0",
                "date": datetime.utcnow().isoformat(),
                "history": []
            },
            procedure=story.procedure.dict()
        )
        
        db.add(story_db)
        db.commit()
        db.refresh(story_db)
        
        logger.info(f"Created story {story_db.id} for thing {story.thing_id}")
        return story_db
    except Exception as e:
        logger.error(f"Failed to create story: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/stories/{story_id}", response_model=StoryResponse)
async def get_story(story_id: str, db: Session = Depends(get_db)):
    """Get a specific story."""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story

@app.get("/api/v1/things/{thing_id}/stories", response_model=List[StoryResponse])
async def get_thing_stories(thing_id: str, db: Session = Depends(get_db)):
    """Get all stories for a thing."""
    stories = db.query(Story).filter(Story.thing_id == thing_id).all()
    return stories

# Relationship endpoints
@app.post("/api/v1/relationships", response_model=RelationshipResponse)
async def create_relationship(relationship: RelationshipCreate, db: Session = Depends(get_db)):
    """Create a new relationship between things."""
    try:
        thing = db.query(Thing).filter(Thing.id == relationship.thing_id).first()
        if not thing:
            raise HTTPException(status_code=404, detail=f"Thing {relationship.thing_id} not found")

        db_relationship = Relationship(
            id=str(uuid.uuid4()),
            thing_id=relationship.thing_id,
            relationship_type=relationship.relationship_type,
            target_uri=relationship.target_uri,
            relation_metadata=relationship.relation_metadata,
            created_at=datetime.utcnow()
        )
        
        db.add(db_relationship)
        db.commit()
        db.refresh(db_relationship)
        
        logger.info(f"Created relationship {db_relationship.id}")
        return db_relationship
    except Exception as e:
        logger.error(f"Failed to create relationship: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/relationships/{relationship_id}", response_model=RelationshipResponse)
async def get_relationship(relationship_id: str, db: Session = Depends(get_db)):
    """Get a specific relationship."""
    relationship = db.query(Relationship).filter(Relationship.id == relationship_id).first()
    if not relationship:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return relationship

@app.get("/api/v1/things/{thing_id}/relationships", response_model=List[RelationshipResponse])
async def get_thing_relationships(thing_id: str, db: Session = Depends(get_db)):
    """Get all relationships for a thing."""
    relationships = db.query(Relationship).filter(Relationship.thing_id == thing_id).all()
    return relationships

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
