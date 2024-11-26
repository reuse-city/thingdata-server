from sqlalchemy import Column, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Thing(Base):
    __tablename__ = "things"

    id = Column(String, primary_key=True)
    uri = Column(String, unique=True, nullable=False)
    type = Column(String, nullable=False)
    name = Column(JSON, nullable=False)  # Multilingual support
    manufacturer = Column(JSON)
    properties = Column(JSON)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    stories = relationship("Story", back_populates="thing", cascade="all, delete-orphan")
    relationships = relationship("Relationship", back_populates="thing", cascade="all, delete-orphan")

class Story(Base):
    __tablename__ = "stories"

    id = Column(String, primary_key=True)
    thing_id = Column(String, ForeignKey("things.id"))
    version = Column(JSON, nullable=False)
    type = Column(String, nullable=False)
    procedure = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    thing = relationship("Thing", back_populates="stories")

class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(String, primary_key=True)
    thing_id = Column(String, ForeignKey("things.id"))
    relationship_type = Column(String, nullable=False)
    target_uri = Column(String, nullable=False)
    relation_metadata = Column(JSON)  # Changed from metadata to relation_metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    thing = relationship("Thing", back_populates="relationships")
