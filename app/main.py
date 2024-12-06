from fastapi import FastAPI, HTTPException, Depends, Request, status
from app.security import configure_security, SecurityValidator, SecurityException
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
from app.models import Thing, Story, Guide, Relationship
from app.schemas import (
    ThingCreate, ThingResponse,
    StoryCreate, StoryResponse,
    GuideCreate, GuideResponse,
    RelationshipCreate, RelationshipResponse,
    HealthResponse, ComponentStatus,
    EntityType
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

# Add security module
configure_security(app)

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
    return f"""
    <html>
        <head>
            <title>ThingData Server</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    max-width: 800px; 
                    margin: 40px auto; 
                    padding: 0 20px;
                    line-height: 1.6;
                    color: #333;
                }}
                code {{ 
                    background: #f4f4f4; 
                    padding: 2px 5px; 
                    border-radius: 3px; 
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    font-size: 0.9em;
                    color: #666;
                }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #34495e; margin-top: 30px; }}
                ul {{ padding-left: 20px; }}
                li {{ margin: 10px 0; }}
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
                <li><code><a href="api/v1/guides" title="guides">/api/v1/guides</a></code> - Guide management</li>
                <li><code><a href="api/v1/relationships" title="relationships">/api/v1/relationships</a></code> - Relationship management</li>
            </ul>
            
            <div class="footer">
                <p>ThingData is an open-source project promoting sustainable practices and the right to repair.</p>
                <p>Version {VERSION}</p>
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

# Add helper function
async def verify_entity_exists(db: Session, entity_type: str, entity_id: str) -> bool:
    """Verify that an entity exists in the database."""
    if entity_type == EntityType.THING:
        return db.query(Thing).filter(Thing.id == entity_id).first() is not None
    elif entity_type == EntityType.GUIDE:
        return db.query(Guide).filter(Guide.id == entity_id).first() is not None
    elif entity_type == EntityType.STORY:
        return db.query(Story).filter(Story.id == entity_id).first() is not None
    return False

@app.post("/api/v1/things", response_model=ThingResponse)
async def create_thing(thing: ThingCreate, db: Session = Depends(get_db)):
    """Create a new thing."""
    try:
        thing_data = thing.model_dump(mode='json')
        
        # Validate data
        SecurityValidator.validate_json_depth(thing_data)
        SecurityValidator.validate_thing_data(thing_data)
        
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
    except SecurityException as e:
        logger.error(f"Security validation failed: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Failed to create thing: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/things/{thing_id}", response_model=ThingResponse)
async def get_thing(thing_id: str, db: Session = Depends(get_db)):
    """Get a specific thing with its relationships."""
    thing = db.query(Thing).filter(Thing.id == thing_id).first()
    if not thing:
        raise HTTPException(status_code=404, detail="Thing not found")
    data = thing.to_dict()
    data['relationships'] = [r.to_dict() for r in thing.get_relationships(db)]
    return data

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
    return [{**thing.to_dict(), 'relationships': [r.to_dict() for r in thing.get_relationships(db)]} 
            for thing in things]

@app.post("/api/v1/stories", response_model=StoryResponse)
async def create_story(story: StoryCreate, db: Session = Depends(get_db)):
    """Create a new repair story."""
    try:
        if story.thing_id:
            thing = db.query(Thing).filter(Thing.id == story.thing_id).first()
            if not thing:
                raise HTTPException(status_code=404, detail=f"Thing {story.thing_id} not found")

        story_data = story.model_dump(mode='json')
        
        # Validate data
        SecurityValidator.validate_json_depth(story_data)
        SecurityValidator.validate_story_data(story_data)

        procedure_list = [step.model_dump() for step in story.procedure]
        
        story_db = Story(
            id=str(uuid.uuid4()),
            thing_id=story.thing_id,
            thing_category=story.thing_category.model_dump() if story.thing_category else None,
            version={
                "number": "1.0.0",
                "date": datetime.utcnow().isoformat(),
                "history": []
            },
            type=story.type,
            procedure=procedure_list
        )
        
        db.add(story_db)
        db.commit()
        db.refresh(story_db)
        
        logger.info(f"Created story {story_db.id}")
        return story_db.to_dict()
    except SecurityException as e:
        logger.error(f"Security validation failed: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Failed to create story: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/stories", response_model=List[StoryResponse])
async def list_stories(
    skip: int = 0,
    limit: int = 100,
    thing_id: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all stories with optional filtering."""
    query = db.query(Story)
    if thing_id:
        query = query.filter(Story.thing_id == thing_id)
    if category:
        query = query.filter(Story.thing_category['category'].astext == category)
    stories = query.offset(skip).limit(limit).all()
    return [{**story.to_dict(), 'relationships': [r.to_dict() for r in story.get_relationships(db)]} 
            for story in stories]

@app.get("/api/v1/stories/{story_id}", response_model=StoryResponse)
async def get_story(story_id: str, db: Session = Depends(get_db)):
    """Get a specific story with its relationships."""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    data = story.to_dict()
    data['relationships'] = [r.to_dict() for r in story.get_relationships(db)]
    return data

@app.get("/api/v1/things/{thing_id}/stories", response_model=List[StoryResponse])
async def get_thing_stories(thing_id: str, db: Session = Depends(get_db)):
    """Get all stories for a thing."""
    stories = db.query(Story).filter(Story.thing_id == thing_id).all()
    return [story.to_dict() for story in stories]

@app.post("/api/v1/relationships", response_model=RelationshipResponse)
async def create_relationship(relationship: RelationshipCreate, db: Session = Depends(get_db)):
    """Create a new relationship."""
    try:
        # Verify source exists
        if not await verify_entity_exists(db, relationship.source_type, relationship.source_id):
            raise HTTPException(
                status_code=404, 
                detail=f"{relationship.source_type} {relationship.source_id} not found"
            )

        # Verify target exists
        if not await verify_entity_exists(db, relationship.target_type, relationship.target_id):
            raise HTTPException(
                status_code=404, 
                detail=f"{relationship.target_type} {relationship.target_id} not found"
            )

        relationship_db = Relationship(
            id=str(uuid.uuid4()),
            source_type=relationship.source_type,
            source_id=relationship.source_id,
            target_type=relationship.target_type,
            target_id=relationship.target_id,
            relationship_type=relationship.relationship_type,
            direction=relationship.direction,
            metadata=relationship.metadata
        )
        db.add(relationship_db)
        db.commit()
        db.refresh(relationship_db)
        logger.info(f"Created relationship: {relationship_db.id}")
        return relationship_db.to_dict()
    except Exception as e:
        logger.error(f"Failed to create relationship: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/relationships", response_model=List[RelationshipResponse])
async def list_relationships(
    skip: int = 0,
    limit: int = 100,
    source_type: Optional[EntityType] = None,
    source_id: Optional[str] = None,
    target_type: Optional[EntityType] = None,
    target_id: Optional[str] = None,
    relationship_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List relationships with optional filtering."""
    query = db.query(Relationship)
    if source_type:
        query = query.filter(Relationship.source_type == source_type)
    if source_id:
        query = query.filter(Relationship.source_id == source_id)
    if target_type:
        query = query.filter(Relationship.target_type == target_type)
    if target_id:
        query = query.filter(Relationship.target_id == target_id)
    if relationship_type:
        query = query.filter(Relationship.relationship_type == relationship_type)
    relationships = query.offset(skip).limit(limit).all()
    return [rel.to_dict() for rel in relationships]

@app.get("/api/v1/relationships/{relationship_id}", response_model=RelationshipResponse)
async def get_relationship(relationship_id: str, db: Session = Depends(get_db)):
    """Get a specific relationship."""
    relationship = db.query(Relationship).filter(Relationship.id == relationship_id).first()
    if not relationship:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return relationship.to_dict()

@app.post("/api/v1/guides", response_model=GuideResponse)
async def create_guide(guide: GuideCreate, db: Session = Depends(get_db)):
    """Create a new guide."""
    try:
        if guide.thing_id:
            thing = db.query(Thing).filter(Thing.id == guide.thing_id).first()
            if not thing:
                raise HTTPException(status_code=404, detail=f"Thing {guide.thing_id} not found")

        guide_data = guide.model_dump(mode='json')
        
        # Validate data
        SecurityValidator.validate_json_depth(guide_data)
        SecurityValidator.validate_guide_data(guide_data)

        guide_db = Guide(
            id=str(uuid.uuid4()),
            thing_id=guide.thing_id,
            thing_category=guide.thing_category.model_dump() if guide.thing_category else None,
            type=guide.type.model_dump(),
            content=guide.content.model_dump()
        )
        
        db.add(guide_db)
        db.commit()
        db.refresh(guide_db)
        
        logger.info(f"Created guide: {guide_db.id}")
        return guide_db.to_dict()
    except SecurityException as e:
        logger.error(f"Security validation failed: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Failed to create guide: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/guides", response_model=List[GuideResponse])
async def list_guides(
    skip: int = 0,
    limit: int = 100,
    thing_id: Optional[str] = None,
    category: Optional[str] = None,
    type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all guides with optional filtering."""
    query = db.query(Guide)
    if thing_id:
        query = query.filter(Guide.thing_id == thing_id)
    if category:
        query = query.filter(Guide.thing_category['category'].astext == category)
    if type:
        query = query.filter(Guide.type['primary'].astext == type)
    guides = query.offset(skip).limit(limit).all()
    return [{**guide.to_dict(), 'relationships': [r.to_dict() for r in guide.get_relationships(db)]} 
            for guide in guides]
            
@app.get("/api/v1/guides/{guide_id}", response_model=GuideResponse)
async def get_guide(guide_id: str, db: Session = Depends(get_db)):
    """Get a specific guide with its relationships."""
    guide = db.query(Guide).filter(Guide.id == guide_id).first()
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")
    data = guide.to_dict()
    data['relationships'] = [r.to_dict() for r in guide.get_relationships(db)]
    return data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
