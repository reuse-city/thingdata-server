from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, Dict, List, Any, Union
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

# --- Thing Specification Schemas ---

class CertificationSpec(BaseModel):
    name: str
    issuer: str
    date: str  # ISO8601

class SustainabilitySpec(BaseModel):
    repairability_score: Optional[float] = None
    lifetime_expectancy: Optional[str] = None
    energy_rating: Optional[str] = None
    certifications: List[CertificationSpec] = Field(default_factory=list)

class VariationSpec(BaseModel):
    market: str
    identifier: str
    differences: List[str] = Field(default_factory=list)

class ModelSpec(BaseModel):
    name: str
    number: Optional[str] = None
    series: Optional[str] = None
    year: Optional[int] = None
    generation: Optional[str] = None
    variations: List[VariationSpec] = Field(default_factory=list)

class DimensionSpec(BaseModel):
    value: float
    unit: str

class PhysicalDimensions(BaseModel):
    length: Optional[DimensionSpec] = None
    width: Optional[DimensionSpec] = None
    height: Optional[DimensionSpec] = None

class WeightSpec(BaseModel):
    value: float
    unit: str

class MaterialSpec(BaseModel):
    name: str
    type: str
    recyclable: bool
    hazardous: bool

class PhysicalProperties(BaseModel):
    dimensions: Optional[PhysicalDimensions] = None
    weight: Optional[WeightSpec] = None
    materials: List[MaterialSpec] = Field(default_factory=list)

# --- Manufacturer Schemas ---

class ArchiveStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    PENDING = "PENDING"
    FAILED = "FAILED"

class WebsiteArchive(BaseModel):
    wayback: Optional[str] = None
    archived_date: Optional[str] = None
    status: ArchiveStatus = ArchiveStatus.AVAILABLE

class ManufacturerWebsite(BaseModel):
    primary: str
    archive: Optional[WebsiteArchive] = None

class Manufacturer(BaseModel):
    name: str
    website: Optional[Union[str, ManufacturerWebsite]] = None
    contact: Optional[str] = None

# Custom properties schema for backward compatibility / backend storage
class Properties(BaseModel):
    dimensions: Optional[Dict[str, float]] = None
    materials: List[str] = Field(default_factory=list)
    manufacturing_date: Optional[str] = None
    serial_number: Optional[str] = None

# --- Core Thing Payload Schemas ---

class ThingDataPayload(BaseModel):
    type: str
    name: MultilingualText
    manufacturer: Manufacturer
    properties: Optional[Union[Properties, PhysicalProperties]] = None

class ThingCreate(BaseModel):
    data: ThingDataPayload

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

class ThingUpdate(BaseModel):
    data: Optional[Dict[str, Any]] = None

class ThingResponse(BaseModel):
    id: str
    uri: str
    created_at: str
    updated_at: Optional[str] = None
    relationships: Optional[List["RelationshipResponse"]] = None
    data: ThingDataPayload

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

# --- Story Specification Schemas ---

class StoryVersionHistory(BaseModel):
    version: str
    date: str
    changes: List[str] = Field(default_factory=list)
    author_uri: str

class StoryVersion(BaseModel):
    number: str
    parent_uri: Optional[str] = None
    date: str
    history: List[StoryVersionHistory] = Field(default_factory=list)

class AuthorSpec(BaseModel):
    uri: str
    name: str
    instance_uri: str
    expertise: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)

class TimeEstimateSpec(BaseModel):
    duration: float
    unit: str
    skill_factor: Optional[str] = None

class CostEstimateSpec(BaseModel):
    amount: float
    currency: str
    region: Optional[str] = None
    date: str

class StoryMetadataSpec(BaseModel):
    title: MultilingualText
    description: MultilingualText
    difficulty: str  # Enum: EASY, MEDIUM, HARD, EXPERT
    time_estimate: TimeEstimateSpec
    cost_estimate: CostEstimateSpec

class SkillPrerequisite(BaseModel):
    name: str
    level: str  # Enum: BASIC, INTERMEDIATE, ADVANCED
    description: str

class ToolPrerequisite(BaseModel):
    thing_uri: str
    required: bool
    alternatives: List[str] = Field(default_factory=list)

class PartPrerequisite(BaseModel):
    thing_uri: str
    quantity: float
    required: bool
    alternatives: List[str] = Field(default_factory=list)

class SafetyPrerequisite(BaseModel):
    warnings: List[str] = Field(default_factory=list)
    equipment: List[str] = Field(default_factory=list)
    certifications_needed: List[str] = Field(default_factory=list)

class PrerequisitesSpec(BaseModel):
    skills: List[SkillPrerequisite] = Field(default_factory=list)
    tools: List[ToolPrerequisite] = Field(default_factory=list)
    parts: List[PartPrerequisite] = Field(default_factory=list)
    safety: Optional[SafetyPrerequisite] = None

class MediaArchive(BaseModel):
    wayback: Optional[str] = None
    archived_date: Optional[str] = None
    status: str
    local_cache: Optional[str] = None

class MediaSpec(BaseModel):
    uri: str
    type: str
    caption: str
    timestamp: Optional[str] = None
    archive: Optional[MediaArchive] = None

class StepDuration(BaseModel):
    estimate: float
    unit: str

class VerificationSpec(BaseModel):
    checks: List[str] = Field(default_factory=list)
    success_indicators: List[str] = Field(default_factory=list)

class StoryStep(BaseModel):
    order: int
    title: Optional[MultilingualText] = None
    description: MultilingualText
    warnings: List[str] = Field(default_factory=list)
    media: List[Union[str, MediaSpec]] = Field(default_factory=list)
    duration: Optional[StepDuration] = None
    tools_used: List[str] = Field(default_factory=list)
    parts_used: List[str] = Field(default_factory=list)
    verification: Optional[VerificationSpec] = None

class ThingCategory(BaseModel):
    category: str
    subcategory: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None

class StoryProcedureSpec(BaseModel):
    steps: List[StoryStep]

# --- Core Story Payload Schemas ---

class StoryDataPayload(BaseModel):
    type: str
    version: Optional[StoryVersion] = None
    author: Optional[AuthorSpec] = None
    metadata: Optional[StoryMetadataSpec] = None
    prerequisites: Optional[PrerequisitesSpec] = None
    procedure: StoryProcedureSpec

class StoryCreate(BaseModel):
    thing_id: Optional[str] = None
    thing_category: Optional[ThingCategory] = None
    data: StoryDataPayload

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

class StoryUpdate(BaseModel):
    data: Optional[Dict[str, Any]] = None

class StoryResponse(BaseModel):
    id: str
    thing_id: Optional[str] = None
    thing_category: Optional[ThingCategory] = None
    created_at: str
    updated_at: Optional[str] = None
    relationships: Optional[List["RelationshipResponse"]] = None
    data: StoryDataPayload

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

# --- Guide Specification Schemas ---

class GuideSourceSpec(BaseModel):
    type: str  # Enum: manufacturer, community, professional, regulatory
    url: Optional[Union[str, ManufacturerWebsite]] = None
    platform: Optional[str] = None
    author: Optional[str] = None
    publication_date: Optional[str] = None
    license: Optional[str] = None

class AccessRequirementsSpec(BaseModel):
    requires_registration: bool = False
    requires_payment: bool = False
    region_restricted: bool = False

class ExternalContentVerificationSpec(BaseModel):
    last_checked: str
    checksum: str
    verified: bool

class ExternalContentSpec(BaseModel):
    type: str
    url: ManufacturerWebsite
    format: str
    language: str
    access_requirements: Optional[AccessRequirementsSpec] = None
    verification: Optional[ExternalContentVerificationSpec] = None

class GuideContentWarning(BaseModel):
    default: str
    translations: Dict[str, str] = Field(default_factory=dict)
    severity: str  # Enum: INFO, CAUTION, WARNING, DANGER

class GuideContent(BaseModel):
    title: MultilingualText
    summary: Optional[MultilingualText] = None
    requirements: Optional[Dict[str, List[str]]] = None
    warnings: Optional[List[GuideContentWarning]] = None
    procedure: Optional[List[Dict[str, Any]]] = None

# --- Core Guide Payload Schemas ---

class GuideType(BaseModel):
    primary: str = Field(..., description="Primary type of guide")
    secondary: Optional[str] = Field(None, description="Secondary classification")

class GuideDataPayload(BaseModel):
    type: GuideType
    content: GuideContent
    source: Optional[GuideSourceSpec] = None
    external_content: Optional[Union[ExternalContentSpec, List[ExternalContentSpec]]] = None

class GuideCreate(BaseModel):
    thing_id: Optional[str] = None
    thing_category: Optional[ThingCategory] = None
    data: GuideDataPayload

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

class GuideUpdate(BaseModel):
    data: Optional[Dict[str, Any]] = None

class GuideResponse(BaseModel):
    id: str
    thing_id: Optional[str] = None
    thing_category: Optional[ThingCategory] = None
    created_at: str
    updated_at: Optional[str] = None
    relationships: Optional[List["RelationshipResponse"]] = None
    data: GuideDataPayload

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

# --- Relationship Schemas ---

class RelationshipCreate(BaseModel):
    source_type: EntityType
    source_id: str
    target_type: EntityType
    target_id: str
    relationship_type: str
    direction: RelationshipDirection
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

class RelationshipUpdate(BaseModel):
    source_type: Optional[EntityType] = None
    source_id: Optional[str] = None
    target_type: Optional[EntityType] = None
    target_id: Optional[str] = None
    relationship_type: Optional[str] = None
    direction: Optional[RelationshipDirection] = None
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

class RelationshipResponse(RelationshipCreate):
    id: str
    created_at: str
    updated_at: Optional[str] = None

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

# --- System Schemas ---

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
