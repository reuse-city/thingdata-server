from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum

class ComponentStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

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
    manufacturing_date: Optional[str] = None  # Changed from datetime to str
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
    created_at: str  # Changed from datetime to str
    updated_at: Optional[str] = None  # Changed from datetime to str

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

class GuideType(BaseModel):
    primary: str = Field(..., description="Primary type (manual, tutorial, specification, documentation)")
    secondary: Optional[str] = Field(None, description="Secondary classification (repair, maintenance, transformation, safety)")

class GuideContent(BaseModel):
    title: MultilingualText
    summary: Optional[MultilingualText] = None
    requirements: Optional[Dict[str, List[str]]] = Field(
        None,
        description="Required skills, tools, materials, certifications"
    )
    warnings: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Safety warnings with severity levels"
    )
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

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

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

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

class RelationshipCreate(BaseModel):
    thing_id: str
    relationship_type: str
    target_uri: str
    relation_metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

class RelationshipResponse(RelationshipCreate):
    id: str
    created_at: str  # Changed from datetime to str

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

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
