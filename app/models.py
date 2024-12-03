from sqlalchemy import Column, String, DateTime, ForeignKey, and_, select, union
from sqlalchemy.orm import relationship, Session
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base

class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(String, primary_key=True)
    source_type = Column(String, nullable=False)
    source_id = Column(String, nullable=False)
    target_type = Column(String, nullable=False)
    target_id = Column(String, nullable=False)
    relationship_type = Column(String, nullable=False)
    direction = Column(String, nullable=False)
    relation_metadata = Column(JSONB)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'relationship_type': self.relationship_type,
            'direction': self.direction,
            'metadata': self.relation_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

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

    stories = relationship("Story", back_populates="thing")
    guides = relationship("Guide", back_populates="thing")

    def get_relationships(self, db: Session, direction: str = 'both'):
        """Get all relationships for this thing."""
        queries = []
        
        if direction == 'outgoing' or direction == 'both':
            outgoing = db.query(Relationship).filter(
                and_(
                    Relationship.source_type == 'thing',
                    Relationship.source_id == self.id
                )
            )
            queries.append(outgoing)
        
        if direction == 'incoming' or direction == 'both':
            incoming = db.query(Relationship).filter(
                and_(
                    Relationship.target_type == 'thing',
                    Relationship.target_id == self.id
                )
            )
            queries.append(incoming)

        if len(queries) > 1:
            return queries[0].union(queries[1]).all()
        elif queries:
            return queries[0].all()
        return []

    def to_dict(self):
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
    thing_id = Column(String, ForeignKey("things.id"), nullable=True)
    thing_category = Column(JSONB, nullable=True)
    version = Column(JSONB, nullable=False)
    type = Column(String, nullable=False)
    procedure = Column(JSONB, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    thing = relationship("Thing", back_populates="stories")

    def get_relationships(self, db: Session, direction: str = 'both'):
        """Get all relationships for this story."""
        queries = []
        
        if direction == 'outgoing' or direction == 'both':
            outgoing = db.query(Relationship).filter(
                and_(
                    Relationship.source_type == 'story',
                    Relationship.source_id == self.id
                )
            )
            queries.append(outgoing)
        
        if direction == 'incoming' or direction == 'both':
            incoming = db.query(Relationship).filter(
                and_(
                    Relationship.target_type == 'story',
                    Relationship.target_id == self.id
                )
            )
            queries.append(incoming)

        if len(queries) > 1:
            return queries[0].union(queries[1]).all()
        elif queries:
            return queries[0].all()
        return []

    def to_dict(self):
        return {
            'id': self.id,
            'thing_id': self.thing_id,
            'thing_category': self.thing_category,
            'version': self.version,
            'type': self.type,
            'procedure': self.procedure,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Guide(Base):
    __tablename__ = "guides"

    id = Column(String, primary_key=True)
    thing_id = Column(String, ForeignKey("things.id"), nullable=True)
    thing_category = Column(JSONB, nullable=True)
    type = Column(JSONB, nullable=False)
    content = Column(JSONB, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    thing = relationship("Thing", back_populates="guides")

    def get_relationships(self, db: Session, direction: str = 'both'):
        """Get all relationships for this guide."""
        queries = []
        
        if direction == 'outgoing' or direction == 'both':
            outgoing = db.query(Relationship).filter(
                and_(
                    Relationship.source_type == 'guide',
                    Relationship.source_id == self.id
                )
            )
            queries.append(outgoing)
        
        if direction == 'incoming' or direction == 'both':
            incoming = db.query(Relationship).filter(
                and_(
                    Relationship.target_type == 'guide',
                    Relationship.target_id == self.id
                )
            )
            queries.append(incoming)

        if len(queries) > 1:
            return queries[0].union(queries[1]).all()
        elif queries:
            return queries[0].all()
        return []

    def to_dict(self):
        return {
            'id': self.id,
            'thing_id': self.thing_id,
            'thing_category': self.thing_category,
            'type': self.type,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
