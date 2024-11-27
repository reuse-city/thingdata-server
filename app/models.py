from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base
import json

class Thing(Base):
    __tablename__ = "things"

    id = Column(String, primary_key=True)
    uri = Column(String, unique=True, nullable=False)
    type = Column(String, nullable=False)
    name = Column(JSONB, nullable=False)
    manufacturer = Column(JSONB)
    properties = Column(JSONB)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    stories = relationship("Story", back_populates="thing", cascade="all, delete-orphan")
    relationships = relationship("Relationship", back_populates="thing", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'uri': self.uri,
            'type': self.type,
            'name': self.name,
            'manufacturer': self.manufacturer,
            'properties': self.properties,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Story(Base):
    __tablename__ = "stories"

    id = Column(String, primary_key=True)
    thing_id = Column(String, ForeignKey("things.id"))
    version = Column(JSONB, nullable=False)
    type = Column(String, nullable=False)
    procedure = Column(JSONB, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    thing = relationship("Thing", back_populates="stories")

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'thing_id': self.thing_id,
            'version': self.version,
            'type': self.type,
            'procedure': self.procedure,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(String, primary_key=True)
    thing_id = Column(String, ForeignKey("things.id"))
    relationship_type = Column(String, nullable=False)
    target_uri = Column(String, nullable=False)
    relation_metadata = Column(JSONB)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    thing = relationship("Thing", back_populates="relationships")

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'thing_id': self.thing_id,
            'relationship_type': self.relationship_type,
            'target_uri': self.target_uri,
            'relation_metadata': self.relation_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
