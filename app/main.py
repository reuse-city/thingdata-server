from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime
import psutil
from pathlib import Path
from app.version import VERSION

from app.database import get_db, init_db
from app.models import Thing, Story, Relationship
from app.schemas import (
    ThingCreate, ThingResponse,
    StoryCreate, StoryResponse,
    RelationshipCreate, RelationshipResponse,
    HealthResponse, ComponentStatus
)
from app.health import HealthChecker
from app.logger import setup_logger

# Initialize logger first
logger = setup_logger(__name__)

# Initialize FastAPI app and health checker
app = FastAPI(
    title="ThingData Server",
    description="ThingData Protocol v1.0 Implementation",
    version=VERSION
)

health_checker = HealthChecker()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Favicon handling
app_dir = Path(__file__).parent
static_dir = app_dir / "static"
static_dir.mkdir(exist_ok=True)
favicon_path = static_dir / "favicon.ico"

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with API information."""
    return """
    <html>
        <head>
            <title>ThingData Server</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    max-width: 800px; 
                    margin: 40px auto; 
                    padding: 0 20px;
                    line-height: 1.6;
                    color: #333;
                }
                code { 
                    background: #f4f4f4; 
                    padding: 2px 5px; 
                    border-radius: 3px; 
                }
                .footer {
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    font-size: 0.9em;
                    color: #666;
                }
                h1 { color: #2c3e50; }
                h2 { color: #34495e; margin-top: 30px; }
                ul { padding-left: 20px; }
                li { margin: 10px 0; }
            </style>
        </head>
        <body>
            <h1>ThingData Server</h1>
            <p>Welcome to ThingData Server, an open protocol for sharing repair knowledge across communities worldwide.</p>
            
            <h2>Available Endpoints</h2>
            <ul>
                <li><code><a href="docs" title="docs">/docs</a></code> - Interactive API documentation</li>
                <li><code><a href="health" title="health">/health</a></code> - System health check</li>
                <li><code><a href="api/v1/things" title="things">/api/v1/things</a></code> - Thing management</li>
                <li><code><a href="api/v1/stories" title="stories">/api/v1/stories</a></code> - Story management</li>
            </ul>
            
            <div class="footer">
                <p>ThingData is an open-source project promoting sustainable practices and the right to repair.</p>
                <p>Version 0.1.0</p>
            </div>
        </body>
    </html>
    """

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

@app.get('/favicon.ico')
async def get_favicon():
    """Serve favicon."""
    return FileResponse(favicon_path)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check endpoint."""
    return await health_checker.check_health()

@app.post("/api/v1/things", response_model=ThingResponse)
async def create_thing(thing: ThingCreate, db: Session = Depends(get_db)):
    """Create a new thing."""
    try:
        # Convert the Pydantic model to dict explicitly
        thing_data = thing.model_dump(mode='json')

        db_thing = Thing(
            id=str(uuid.uuid4()),
            uri=f"thing:{thing_data['type']}/{thing_data['manufacturer']['name']}/{thing_data['name']['default']}",
            type=thing_data['type'],
            name=thing_data['name'],
            manufacturer=thing_data['manufacturer'],
            properties=thing_data.get('properties', {})
        )
        
        db.add(db_thing)
        db.commit()
        db.refresh(db_thing)
        
        logger.info(f"Created thing: {db_thing.id}")
        return db_thing.to_dict()
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
    return thing.to_dict()

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
    things = query.offset(skip).limit(limit).all()
    return [thing.to_dict() for thing in things]

@app.post("/api/v1/stories", response_model=StoryResponse)
async def create_story(story: StoryCreate, db: Session = Depends(get_db)):
    """Create a new repair story."""
    try:
        # Verify thing exists
        thing = db.query(Thing).filter(Thing.id == story.thing_id).first()
        if not thing:
            raise HTTPException(status_code=404, detail=f"Thing {story.thing_id} not found")

        # Convert procedure steps to list of dicts
        procedure_list = [step.model_dump() for step in story.procedure]
        
        story_db = Story(
            id=str(uuid.uuid4()),
            thing_id=story.thing_id,
            type=story.type,
            version={
                "number": "1.0.0",
                "date": datetime.utcnow().isoformat(),
                "history": []
            },
            procedure=procedure_list  # Now using the converted list
        )
        
        db.add(story_db)
        db.commit()
        db.refresh(story_db)
        
        logger.info(f"Created story {story_db.id} for thing {story.thing_id}")
        return story_db.to_dict()
    except Exception as e:
        logger.error(f"Failed to create story: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/stories", response_model=List[StoryResponse])
async def list_stories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all stories with optional pagination."""
    stories = db.query(Story).offset(skip).limit(limit).all()
    return [story.to_dict() for story in stories]

@app.get("/api/v1/stories/{story_id}", response_model=StoryResponse)
async def get_story(story_id: str, db: Session = Depends(get_db)):
    """Get a specific story."""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story.to_dict()

@app.get("/api/v1/things/{thing_id}/stories", response_model=List[StoryResponse])
async def get_thing_stories(thing_id: str, db: Session = Depends(get_db)):
    """Get all stories for a thing."""
    stories = db.query(Story).filter(Story.thing_id == thing_id).all()
    return [story.to_dict() for story in stories]

@app.get("/api/v1/things/{thing_id}/relationships", response_model=List[RelationshipResponse])
async def get_thing_relationships(thing_id: str, db: Session = Depends(get_db)):
    """Get all relationships for a thing."""
    relationships = db.query(Relationship).filter(Relationship.thing_id == thing_id).all()
    return [rel.to_dict() for rel in relationships]

@app.post("/api/v1/relationships", response_model=RelationshipResponse)
async def create_relationship(relationship: RelationshipCreate, db: Session = Depends(get_db)):
    """Create a new relationship between things."""
    try:
        # Verify source thing exists
        source_thing = db.query(Thing).filter(Thing.id == relationship.thing_id).first()
        if not source_thing:
            raise HTTPException(status_code=404, detail=f"Source Thing {relationship.thing_id} not found")

        # Verify target thing exists
        target_thing = db.query(Thing).filter(Thing.id == relationship.target_uri).first()
        if not target_thing:
            raise HTTPException(status_code=404, detail=f"Target Thing {relationship.target_uri} not found")

        relationship_db = Relationship(
            id=str(uuid.uuid4()),
            thing_id=relationship.thing_id,
            relationship_type=relationship.relationship_type,
            target_uri=relationship.target_uri,
            relation_metadata=relationship.relation_metadata if relationship.relation_metadata else None
        )
        
        db.add(relationship_db)
        db.commit()
        db.refresh(relationship_db)
        
        logger.info(f"Created relationship {relationship_db.id} between {relationship.thing_id} and {relationship.target_uri}")
        return relationship_db.to_dict()
    except Exception as e:
        logger.error(f"Failed to create relationship: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
