"""
Database initialization and utilities for the web UI.
"""
import os
import logging
from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session
from web_ui.models.pending_extractions import db_manager, Base

logger = logging.getLogger(__name__)


def initialize_database():
    """Initialize the database and create tables."""
    try:
        # Create tables
        db_manager.create_tables()
        logger.info("✅ Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        return False


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    Ensures proper cleanup of database connections.
    """
    session = db_manager.get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def get_database_stats() -> dict:
    """Get database statistics."""
    try:
        with get_db_session() as session:
            from web_ui.models.pending_extractions import PendingDocument, PendingEntity, PendingRelationship
            
            total_documents = session.query(PendingDocument).count()
            pending_documents = session.query(PendingDocument).filter(PendingDocument.status == 'pending').count()
            approved_documents = session.query(PendingDocument).filter(PendingDocument.status == 'approved').count()
            total_entities = session.query(PendingEntity).count()
            approved_entities = session.query(PendingEntity).filter(PendingEntity.approved == True).count()
            total_relationships = session.query(PendingRelationship).count()
            approved_relationships = session.query(PendingRelationship).filter(PendingRelationship.approved == True).count()
            
            return {
                'total_documents': total_documents,
                'pending_documents': pending_documents,
                'approved_documents': approved_documents,
                'total_entities': total_entities,
                'approved_entities': approved_entities,
                'total_relationships': total_relationships,
                'approved_relationships': approved_relationships
            }
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {
            'total_documents': 0,
            'pending_documents': 0,
            'approved_documents': 0,
            'total_entities': 0,
            'approved_entities': 0,
            'total_relationships': 0,
            'approved_relationships': 0
        }


def cleanup_database():
    """Clean up old or rejected extractions."""
    try:
        with get_db_session() as session:
            from web_ui.models.pending_extractions import PendingDocument
            
            # Delete rejected documents older than 7 days
            from datetime import datetime, timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            
            deleted_count = session.query(PendingDocument).filter(
                PendingDocument.status == 'rejected',
                PendingDocument.updated_at < cutoff_date
            ).delete()
            
            logger.info(f"Cleaned up {deleted_count} old rejected documents")
            return deleted_count
            
    except Exception as e:
        logger.error(f"Failed to cleanup database: {e}")
        return 0
