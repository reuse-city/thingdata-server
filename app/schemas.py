from pydantic import BaseModel, Field, EmailStr
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
    manufacturing_date: Optional[datetime] = None
    serial_number: Optional[str] = None

class ThingCreate(BaseModel):
    type: str
    name: MultilingualText
    manufacturer: Manufacturer
    properties: Optional[Properties] = None

class ThingResponse(ThingCreate):
    id: str
    uri: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class StoryStep(BaseModel):
    order: int
    description: MultilingualText
    warnings: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    media: List[str] = Field(default_factory=list)

class StoryCreate(BaseModel):
    thing_id: str
    type: str
    procedure: List[StoryStep]

class StoryResponse(StoryCreate):
    id: str
    version: Dict[str, Any]
    created_at: datetime

class RelationshipCreate(BaseModel):
    thing_id: str
    relationship_type: str
    target_uri: str
    relation_metadata: Optional[Dict[str, Any]] = None

class RelationshipResponse(RelationshipCreate):
    id: str
    created_at: datetime

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
