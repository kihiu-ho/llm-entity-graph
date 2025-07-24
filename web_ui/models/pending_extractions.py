"""
SQLAlchemy models for pending entity extractions.
"""
from datetime import datetime
from typing import Dict, Any, Optional
import json
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()


class PendingDocument(Base):
    """Model for documents pending entity extraction review."""
    __tablename__ = 'pending_documents'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=True)
    extraction_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default='pending')  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    entities = relationship("PendingEntity", back_populates="document", cascade="all, delete-orphan")
    relationships = relationship("PendingRelationship", back_populates="document", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'filename': self.filename,
            'content': self.content,
            'metadata': self.metadata,
            'extraction_date': self.extraction_date.isoformat() if self.extraction_date else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'entity_count': len(self.entities),
            'relationship_count': len(self.relationships)
        }


class PendingEntity(Base):
    """Model for entities pending review."""
    __tablename__ = 'pending_entities'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('pending_documents.id'), nullable=False)
    entity_type = Column(String(100), nullable=False)  # Person, Company, etc.
    name = Column(String(255), nullable=False)
    properties = Column(JSON, nullable=True)  # Additional properties like role, description, etc.
    approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    document = relationship("PendingDocument", back_populates="entities")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'entity_type': self.entity_type,
            'name': self.name,
            'properties': self.properties or {},
            'approved': self.approved,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PendingRelationship(Base):
    """Model for relationships pending review."""
    __tablename__ = 'pending_relationships'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('pending_documents.id'), nullable=False)
    source_entity = Column(String(255), nullable=False)
    target_entity = Column(String(255), nullable=False)
    relationship_type = Column(String(100), nullable=False)
    properties = Column(JSON, nullable=True)  # Additional properties like description, confidence, etc.
    approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    document = relationship("PendingDocument", back_populates="relationships")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'source_entity': self.source_entity,
            'target_entity': self.target_entity,
            'relationship_type': self.relationship_type,
            'properties': self.properties or {},
            'approved': self.approved,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Database session management
class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self, database_url: str = "sqlite:///pending_extractions.db"):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """Create all tables."""
        Base.metadata.create_all(bind=self.engine)
        
    def get_session(self):
        """Get a database session."""
        return self.SessionLocal()
        
    def close_session(self, session):
        """Close a database session."""
        session.close()


# Global database manager instance
db_manager = DatabaseManager()
