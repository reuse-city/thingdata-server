from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum

# First define the enums
class ComponentStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class EntityType(str, Enum):
    THING = "thing"
    GUIDE = "guide"
    STORY = "story"

class RelationshipDirection(str, Enum):
    UNIDIRECTIONAL = "unidirectional"
    BIDIRECTIONAL = "bidirectional"

class MultilingualText(BaseModel):
    default: str
    translations: Dict[str, str] = Field(default_factory=dict)

class Manufacturer(BaseModel):
    name: str
    website: Optional[str] = None
    contact: Optional[EmailStr] = None

class Properties(BaseModel):
    dimensions: Optional[Dict[str, float]] = None
    materials: List[str] = Field(default_factory=list)
    manufacturing_date: Optional[str] = None
    serial_number: Optional[str] = None

class ThingCreate(BaseModel):
    type: str
    name: MultilingualText
    manufacturer: Manufacturer
    properties: Optional[Properties] = None
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

class ThingResponse(ThingCreate):
    id: str
    uri: str
    created_at: str
    updated_at: Optional[str] = None
    relationships: Optional[List["RelationshipResponse"]] = None

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

class StoryStep(BaseModel):
    order: int
    description: MultilingualText
    warnings: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    media: List[str] = Field(default_factory=list)

class ThingCategory(BaseModel):
    category: str
    subcategory: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None

class StoryCreate(BaseModel):
    thing_id: Optional[str] = None
    thing_category: Optional[ThingCategory] = None
    type: str
    procedure: List[StoryStep]

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

class StoryResponse(StoryCreate):
    id: str
    version: Dict[str, Any]
    created_at: str
    updated_at: Optional[str] = None
    relationships: Optional[List["RelationshipResponse"]] = None

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

class GuideType(BaseModel):
    primary: str = Field(..., description="Primary type of guide")
    secondary: Optional[str] = Field(None, description="Secondary classification")

class GuideContent(BaseModel):
    title: MultilingualText
    summary: Optional[MultilingualText] = None
    requirements: Optional[Dict[str, List[str]]] = None
    warnings: Optional[List[Dict[str, Any]]] = None
    procedure: Optional[List[Dict[str, Any]]] = None

class GuideCreate(BaseModel):
    thing_id: Optional[str] = None
    thing_category: Optional[ThingCategory] = None
    type: GuideType
    content: GuideContent

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

class GuideResponse(GuideCreate):
    id: str
    created_at: str
    updated_at: Optional[str] = None
    relationships: Optional[List["RelationshipResponse"]] = None

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

class RelationshipCreate(BaseModel):
    source_type: EntityType
    source_id: str
    target_type: EntityType
    target_id: str
    relationship_type: str
    direction: RelationshipDirection
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

class RelationshipResponse(RelationshipCreate):
    id: str
    created_at: str
    updated_at: Optional[str] = None

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

# Add this to schemas.py after the other schemas

class HealthMetrics(BaseModel):
    memory_usage: float
    cpu_usage: float
    active_connections: int
    storage_usage: Optional[float] = None
    federation_peers: Optional[int] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    components: Dict[str, ComponentStatus]
    metrics: HealthMetrics

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


# Update forward references
ThingResponse.model_rebuild()
StoryResponse.model_rebuild()
GuideResponse.model_rebuild()
