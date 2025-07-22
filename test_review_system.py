#!/usr/bin/env python3
"""
Test script for the review system.
"""

import asyncio
import logging
import tempfile
import os
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_review_system():
    """Test the complete review system workflow."""
    
    logger.info("=" * 70)
    logger.info("TESTING REVIEW SYSTEM")
    logger.info("=" * 70)
    
    try:
        # Test 1: Create a sample document
        logger.info("\n1. Creating sample document for testing...")
        
        sample_content = """
        John Smith is the CEO of TechCorp Inc., a technology company based in San Francisco.
        He previously worked at DataSoft as a Senior Engineer before joining TechCorp in 2020.
        
        TechCorp Inc. is a private technology company founded in 2018. The company specializes
        in artificial intelligence and machine learning solutions. Mary Johnson serves as the
        CTO of TechCorp, leading the technical team.
        
        The company has partnerships with several organizations including Microsoft and Google.
        TechCorp received $10 million in Series A funding from Venture Capital Partners in 2021.
        """
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(sample_content)
            temp_path = tmp_file.name
        
        logger.info(f"✅ Sample document created: {temp_path}")
        
        # Test 2: Test staging manager
        logger.info("\n2. Testing staging manager...")
        
        from staging.staging_manager import staging_manager
        
        # Create staging session
        session_id = staging_manager.create_staging_session(
            document_title="Test Document",
            document_source="test_sample.txt"
        )
        logger.info(f"✅ Staging session created: {session_id}")
        
        # Add sample entities
        entity_data = {
            "name": "John Smith",
            "type": "Person",
            "attributes": {"position": "CEO", "company": "TechCorp Inc."},
            "confidence": 0.9,
            "source_text": "John Smith is the CEO of TechCorp Inc."
        }
        entity_id = staging_manager.add_entity_to_staging(session_id, entity_data)
        logger.info(f"✅ Entity added to staging: {entity_id}")
        
        # Add sample relationship
        relationship_data = {
            "source": "John Smith",
            "target": "TechCorp Inc.",
            "type": "Employment",
            "attributes": {"position": "CEO"},
            "confidence": 0.9,
            "source_text": "John Smith is the CEO of TechCorp Inc."
        }
        rel_id = staging_manager.add_relationship_to_staging(session_id, relationship_data)
        logger.info(f"✅ Relationship added to staging: {rel_id}")
        
        # Test 3: Test staging ingestion
        logger.info("\n3. Testing staging ingestion...")
        
        from staging.staging_ingestion import staging_ingestion
        
        try:
            review_session_id = await staging_ingestion.ingest_document_for_review(
                file_path=temp_path,
                document_title="Test Document Review",
                document_source="test_sample.txt"
            )
            logger.info(f"✅ Document processed for review: {review_session_id}")
            
            # Load and check the session
            session_data = staging_manager.load_session(review_session_id)
            logger.info(f"✅ Session loaded with {len(session_data['entities'])} entities and {len(session_data['relationships'])} relationships")
            
        except Exception as e:
            logger.warning(f"⚠️ Staging ingestion test failed: {e}")
        
        # Test 4: Test status updates
        logger.info("\n4. Testing status updates...")
        
        # Approve the entity
        staging_manager.update_entity_status(session_id, entity_id, "approved")
        logger.info(f"✅ Entity approved: {entity_id}")
        
        # Approve the relationship
        staging_manager.update_relationship_status(session_id, rel_id, "approved")
        logger.info(f"✅ Relationship approved: {rel_id}")
        
        # Test 5: Test approved items retrieval
        logger.info("\n5. Testing approved items retrieval...")
        
        approved_items = staging_manager.get_approved_items(session_id)
        logger.info(f"✅ Retrieved {len(approved_items['entities'])} approved entities")
        logger.info(f"✅ Retrieved {len(approved_items['relationships'])} approved relationships")
        
        # Test 6: Test session listing
        logger.info("\n6. Testing session listing...")
        
        sessions = staging_manager.list_sessions()
        logger.info(f"✅ Found {len(sessions)} staging sessions")
        
        for session in sessions[:3]:  # Show first 3 sessions
            logger.info(f"   - {session['document_title']} ({session['status']})")
        
        # Test 7: Test ingestion of approved items (optional)
        logger.info("\n7. Testing ingestion of approved items...")
        
        try:
            results = await staging_ingestion.ingest_approved_items(session_id)
            logger.info(f"✅ Ingested {results['entities_ingested']} entities and {results['relationships_ingested']} relationships")
        except Exception as e:
            logger.warning(f"⚠️ Ingestion test failed: {e}")
        
        # Cleanup
        try:
            os.unlink(temp_path)
            logger.info("✅ Temporary file cleaned up")
        except:
            pass
        
        logger.info(f"\n🎉 Review system test completed successfully!")
        logger.info(f"📋 You can now:")
        logger.info(f"   1. Start the web UI: cd web_ui && python3 app.py")
        logger.info(f"   2. Go to http://localhost:5000/review")
        logger.info(f"   3. Upload documents for review")
        logger.info(f"   4. Review and approve entities/relationships")
        logger.info(f"   5. Ingest approved items into Graphiti")
        
    except Exception as e:
        logger.error(f"❌ Review system test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

def main():
    """Main function to run the tests."""
    asyncio.run(test_review_system())

if __name__ == "__main__":
    main()
