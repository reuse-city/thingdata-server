from fastapi import FastAPI, HTTPException, Depends, Request, status, Header
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
    ThingCreate, ThingUpdate, ThingResponse,
    StoryCreate, StoryUpdate, StoryResponse,
    GuideCreate, GuideUpdate, GuideResponse,
    RelationshipCreate, RelationshipUpdate, RelationshipResponse,
    HealthResponse, ComponentStatus,
    EntityType
)

from app.health import HealthChecker
from app.logger import setup_logger
from app.federation import FederationManager

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

# Initialize database and federation on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    app.state.federation = FederationManager()
    await app.state.federation.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    if hasattr(app.state, "federation"):
        await app.state.federation.shutdown()

def get_federation(request: Request) -> FederationManager:
    """Retrieve the federation manager from the application state."""
    return request.app.state.federation

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
        thing_payload = thing_data['data']
        
        # Validate data
        SecurityValidator.validate_json_depth(thing_data)
        SecurityValidator.validate_thing_data(thing_payload)
        
        db_thing = Thing(
            id=str(uuid.uuid4()),
            uri=f"thing:{thing_payload['type']}/{thing_payload['manufacturer']['name']}/{thing_payload['name']['default']}",
            type=thing_payload['type'],
            name=thing_payload['name'],
            manufacturer=thing_payload['manufacturer'],
            properties=thing_payload.get('properties', {})
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
        story_payload = story_data['data']
        
        # Validate data
        SecurityValidator.validate_json_depth(story_data)
        SecurityValidator.validate_story_data(story_payload)

        procedure_list = [step.model_dump() for step in story.data.procedure.steps]
        
        story_db = Story(
            id=str(uuid.uuid4()),
            thing_id=story.thing_id,
            thing_category=story.thing_category.model_dump() if story.thing_category else None,
            version=story_payload.get('version', {
                "number": "1.0.0",
                "date": datetime.utcnow().isoformat(),
                "history": []
            }),
            type=story_payload['type'],
            author=story_payload.get('author'),
            story_metadata=story_payload.get('metadata'),
            prerequisites=story_payload.get('prerequisites'),
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
        guide_payload = guide_data['data']
        
        # Validate data
        SecurityValidator.validate_json_depth(guide_data)
        SecurityValidator.validate_guide_data(guide_payload)

        guide_db = Guide(
            id=str(uuid.uuid4()),
            thing_id=guide.thing_id,
            thing_category=guide.thing_category.model_dump() if guide.thing_category else None,
            type=guide_payload['type'],
            content=guide_payload['content'],
            source=guide_payload.get('source'),
            external_content=guide_payload.get('external_content')
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

# --- Sub-resource Relationships Endpoints ---

@app.get("/api/v1/things/{thing_id}/relationships", response_model=List[RelationshipResponse])
async def get_thing_relationships(thing_id: str, db: Session = Depends(get_db)):
    """Get all relationships for a thing."""
    thing = db.query(Thing).filter(Thing.id == thing_id).first()
    if not thing:
        raise HTTPException(status_code=404, detail="Thing not found")
    return [r.to_dict() for r in thing.get_relationships(db)]

@app.get("/api/v1/stories/{story_id}/relationships", response_model=List[RelationshipResponse])
async def get_story_relationships(story_id: str, db: Session = Depends(get_db)):
    """Get all relationships for a story."""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return [r.to_dict() for r in story.get_relationships(db)]

@app.get("/api/v1/guides/{guide_id}/relationships", response_model=List[RelationshipResponse])
async def get_guide_relationships(guide_id: str, db: Session = Depends(get_db)):
    """Get all relationships for a guide."""
    guide = db.query(Guide).filter(Guide.id == guide_id).first()
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")
    return [r.to_dict() for r in guide.get_relationships(db)]

# --- DELETE Endpoints ---

@app.delete("/api/v1/things/{thing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thing(
    thing_id: str,
    x_confirm_delete: bool = Header(..., alias="X-Confirm-Delete"),
    db: Session = Depends(get_db)
):
    """Delete a thing and its associated relationships."""
    if not x_confirm_delete:
        raise HTTPException(status_code=400, detail="Must confirm delete with X-Confirm-Delete header")
    thing = db.query(Thing).filter(Thing.id == thing_id).first()
    if not thing:
        raise HTTPException(status_code=404, detail="Thing not found")
    
    # Delete associated relationships
    db.query(Relationship).filter(
        ((Relationship.source_type == 'thing') & (Relationship.source_id == thing_id)) |
        ((Relationship.target_type == 'thing') & (Relationship.target_id == thing_id))
    ).delete(synchronize_session=False)

    db.delete(thing)
    db.commit()
    logger.info(f"Deleted thing: {thing_id}")

@app.delete("/api/v1/stories/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_story(
    story_id: str,
    x_confirm_delete: bool = Header(..., alias="X-Confirm-Delete"),
    db: Session = Depends(get_db)
):
    """Delete a story and its associated relationships."""
    if not x_confirm_delete:
        raise HTTPException(status_code=400, detail="Must confirm delete with X-Confirm-Delete header")
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # Delete associated relationships
    db.query(Relationship).filter(
        ((Relationship.source_type == 'story') & (Relationship.source_id == story_id)) |
        ((Relationship.target_type == 'story') & (Relationship.target_id == story_id))
    ).delete(synchronize_session=False)

    db.delete(story)
    db.commit()
    logger.info(f"Deleted story: {story_id}")

@app.delete("/api/v1/guides/{guide_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_guide(
    guide_id: str,
    x_confirm_delete: bool = Header(..., alias="X-Confirm-Delete"),
    db: Session = Depends(get_db)
):
    """Delete a guide and its associated relationships."""
    if not x_confirm_delete:
        raise HTTPException(status_code=400, detail="Must confirm delete with X-Confirm-Delete header")
    guide = db.query(Guide).filter(Guide.id == guide_id).first()
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")
    
    # Delete associated relationships
    db.query(Relationship).filter(
        ((Relationship.source_type == 'guide') & (Relationship.source_id == guide_id)) |
        ((Relationship.target_type == 'guide') & (Relationship.target_id == guide_id))
    ).delete(synchronize_session=False)

    db.delete(guide)
    db.commit()
    logger.info(f"Deleted guide: {guide_id}")

@app.delete("/api/v1/relationships/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relationship(
    relationship_id: str,
    x_confirm_delete: bool = Header(..., alias="X-Confirm-Delete"),
    db: Session = Depends(get_db)
):
    """Delete a relationship."""
    if not x_confirm_delete:
        raise HTTPException(status_code=400, detail="Must confirm delete with X-Confirm-Delete header")
    relationship = db.query(Relationship).filter(Relationship.id == relationship_id).first()
    if not relationship:
        raise HTTPException(status_code=404, detail="Relationship not found")
    db.delete(relationship)
    db.commit()
    logger.info(f"Deleted relationship: {relationship_id}")

# --- PUT Update Endpoints ---

@app.put("/api/v1/things/{thing_id}", response_model=ThingResponse)
async def update_thing(thing_id: str, thing_update: ThingUpdate, db: Session = Depends(get_db)):
    """Update an existing thing."""
    db_thing = db.query(Thing).filter(Thing.id == thing_id).first()
    if not db_thing:
        raise HTTPException(status_code=404, detail="Thing not found")
    
    update_data = thing_update.model_dump(exclude_unset=True)
    if 'data' in update_data and update_data['data'] is not None:
        data_payload = update_data['data']
        if 'type' in data_payload:
            db_thing.type = data_payload['type']
        if 'name' in data_payload:
            db_thing.name = data_payload['name']
        if 'manufacturer' in data_payload:
            db_thing.manufacturer = data_payload['manufacturer']
        if 'properties' in data_payload:
            db_thing.properties = data_payload['properties']
            
        # Regenerate URI if name/manufacturer/type changed
        db_thing.uri = f"thing:{db_thing.type}/{db_thing.manufacturer['name']}/{db_thing.name['default']}"
        
    db_thing.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_thing)
    return db_thing.to_dict()

@app.put("/api/v1/stories/{story_id}", response_model=StoryResponse)
async def update_story(story_id: str, story_update: StoryUpdate, db: Session = Depends(get_db)):
    """Update an existing story."""
    db_story = db.query(Story).filter(Story.id == story_id).first()
    if not db_story:
        raise HTTPException(status_code=404, detail="Story not found")
        
    update_data = story_update.model_dump(exclude_unset=True)
    if 'data' in update_data and update_data['data'] is not None:
        data_payload = update_data['data']
        if 'type' in data_payload:
            db_story.type = data_payload['type']
        if 'version' in data_payload:
            db_story.version = data_payload['version']
        if 'author' in data_payload:
            db_story.author = data_payload['author']
        if 'metadata' in data_payload:
            db_story.story_metadata = data_payload['metadata']
        if 'prerequisites' in data_payload:
            db_story.prerequisites = data_payload['prerequisites']
        if 'procedure' in data_payload:
            proc = data_payload['procedure']
            if isinstance(proc, dict) and 'steps' in proc:
                db_story.procedure = proc['steps']
            else:
                db_story.procedure = proc
                
    db_story.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_story)
    return db_story.to_dict()

@app.put("/api/v1/guides/{guide_id}", response_model=GuideResponse)
async def update_guide(guide_id: str, guide_update: GuideUpdate, db: Session = Depends(get_db)):
    """Update an existing guide."""
    db_guide = db.query(Guide).filter(Guide.id == guide_id).first()
    if not db_guide:
        raise HTTPException(status_code=404, detail="Guide not found")
        
    update_data = guide_update.model_dump(exclude_unset=True)
    if 'data' in update_data and update_data['data'] is not None:
        data_payload = update_data['data']
        if 'type' in data_payload:
            db_guide.type = data_payload['type']
        if 'content' in data_payload:
            db_guide.content = data_payload['content']
        if 'source' in data_payload:
            db_guide.source = data_payload['source']
        if 'external_content' in data_payload:
            db_guide.external_content = data_payload['external_content']
            
    db_guide.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_guide)
    return db_guide.to_dict()

@app.put("/api/v1/relationships/{relationship_id}", response_model=RelationshipResponse)
async def update_relationship(relationship_id: str, relationship_update: RelationshipUpdate, db: Session = Depends(get_db)):
    """Update an existing relationship."""
    db_rel = db.query(Relationship).filter(Relationship.id == relationship_id).first()
    if not db_rel:
        raise HTTPException(status_code=404, detail="Relationship not found")
        
    update_data = relationship_update.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        if key == 'metadata':
            db_rel.relation_metadata = val
        else:
            setattr(db_rel, key, val)
            
    db_rel.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_rel)
    return db_rel.to_dict()

# --- Guide External Content & Archival Sub-resources ---

@app.get("/api/v1/guides/{guide_id}/external-content")
async def get_guide_external_content(guide_id: str, db: Session = Depends(get_db)):
    """Get the external content metadata associated with a guide."""
    guide = db.query(Guide).filter(Guide.id == guide_id).first()
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")
    return guide.external_content or {}

@app.get("/api/v1/guides/{guide_id}/archive")
async def get_guide_archive(guide_id: str, db: Session = Depends(get_db)):
    """Get Internet Archive status for a guide's external content."""
    guide = db.query(Guide).filter(Guide.id == guide_id).first()
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")
    ext = guide.external_content
    if not ext:
        return {"status": "FAILED", "detail": "No external content associated"}
    if isinstance(ext, list):
        return [e.get("url", {}).get("archive", {}) for e in ext if "url" in e]
    return ext.get("url", {}).get("archive", {})

# --- Federation Endpoints ---

@app.get("/.well-known/webfinger")
async def webfinger_discovery(
    resource: Optional[str] = None,
    db: Session = Depends(get_db),
    federation: FederationManager = Depends(get_federation)
):
    """Handle WebFinger discovery requests."""
    if resource:
        # Check if resource is a local Thing URI (e.g. thing:...)
        if resource.startswith("thing:"):
            thing = db.query(Thing).filter(Thing.uri == resource).first()
            if thing:
                from app.config import get_settings
                settings = get_settings()
                return {
                    "subject": resource,
                    "links": [
                        {
                            "rel": "self",
                            "href": f"{settings.INSTANCE_URI}/api/v1/things/{thing.id}",
                            "type": "application/activity+json"
                        }
                    ]
                }
    return await federation.handle_webfinger()

@app.post("/api/v1/federation/connect")
async def connect_peer(
    payload: dict,
    db: Session = Depends(get_db),
    federation: FederationManager = Depends(get_federation)
):
    """Register/connect a new federation peer instance."""
    uri = payload.get("instance_uri") or payload.get("uri")
    if not uri:
        raise HTTPException(status_code=400, detail="Missing instance_uri or uri")
        
    public_key = payload.get("public_key")
    if not public_key:
        raise HTTPException(status_code=400, detail="Missing public_key")
        
    instance_data = {
        "id": payload.get("id") or str(uuid.uuid4()),
        "uri": uri,
        "name": payload.get("name") or payload.get("instance_name") or uri.split("//")[-1],
        "type": payload.get("type") or payload.get("instance_type") or "peer",
        "endpoints": payload.get("endpoints") or {
            "api": f"{uri}/api/v1",
            "health": f"{uri}/health",
            "status": f"{uri}/api/v1/federation/status"
        },
        "public_key": public_key,
        "capabilities": payload.get("capabilities") or ["sync"],
        "languages": payload.get("languages") or ["en"]
    }
    
    try:
        instance = await federation.connect_instance(instance_data, db)
        return {
            "status": "connected",
            "instance": instance.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error connecting instance: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/federation/announce")
async def announce_event(payload: dict):
    """Receive an announcement of new content from a federation peer."""
    logger.info(f"Received federation announcement: {payload}")
    return {"status": "announced", "message": "Announcement received"}

@app.post("/api/v1/federation/sync")
async def sync_resources(payload: dict, db: Session = Depends(get_db)):
    """Synchronize resources requested by a peer."""
    uris = payload.get("uris", [])
    since_str = payload.get("since")
    since = None
    if since_str:
        try:
            since = datetime.fromisoformat(since_str.replace("Z", "+00:00"))
        except ValueError:
            pass
            
    results = []
    
    if uris:
        for uri in uris:
            thing = db.query(Thing).filter(Thing.uri == uri).first()
            if thing:
                results.append({"type": "thing", "data": thing.to_dict()})
            # Also search by ID or custom logic if story/guide
            story = db.query(Story).filter(Story.id == uri).first()
            if story:
                results.append({"type": "story", "data": story.to_dict()})
            guide = db.query(Guide).filter(Guide.id == uri).first()
            if guide:
                results.append({"type": "guide", "data": guide.to_dict()})
    elif since:
        things = db.query(Thing).filter(Thing.updated_at >= since).all()
        for t in things:
            results.append({"type": "thing", "data": t.to_dict()})
        stories = db.query(Story).filter(Story.updated_at >= since).all()
        for s in stories:
            results.append({"type": "story", "data": s.to_dict()})
        guides = db.query(Guide).filter(Guide.updated_at >= since).all()
        for g in guides:
            results.append({"type": "guide", "data": g.to_dict()})
    else:
        things = db.query(Thing).all()
        for t in things:
            results.append({"type": "thing", "data": t.to_dict()})
        stories = db.query(Story).all()
        for s in stories:
            results.append({"type": "story", "data": s.to_dict()})
        guides = db.query(Guide).all()
        for g in guides:
            results.append({"type": "guide", "data": g.to_dict()})
            
    return {"results": results}

@app.get("/api/v1/federation/discover")
async def discover_peers(federation: FederationManager = Depends(get_federation)):
    """Discover connected federation peer instances."""
    peers = [inst.to_dict() for inst in federation.known_instances.values()]
    return {"peers": peers}

@app.get("/api/v1/federation/status")
async def federation_status(federation: FederationManager = Depends(get_federation)):
    """Retrieve federation system status and metrics."""
    health = await federation.check_health()
    return {
        "connected_count": len(federation.known_instances),
        "active_syncs_count": len(federation.active_syncs),
        "health": health,
        "queue_sizes": {uri: q.qsize() for uri, q in federation.sync_queues.items()}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
