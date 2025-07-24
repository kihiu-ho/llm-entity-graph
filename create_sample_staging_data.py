#!/usr/bin/env python3
"""
Create sample staging data for testing the entity review interface.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path


def create_sample_staging_data():
    """Create sample staging data with entities and relationships."""
    
    # Create staging directory
    staging_dir = Path('staging/data')
    staging_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Sample entities
    entities = [
        {
            "id": str(uuid.uuid4()),
            "name": "John Smith",
            "type": "Person",
            "attributes": {
                "entity_type": "person",
                "role_type": "executive",
                "position": "CEO",
                "company": "TechCorp Inc.",
                "source_chunk": 0
            },
            "confidence": 0.95,
            "status": "pending",
            "edited": False,
            "created_at": datetime.now().isoformat(),
            "source_text": "John Smith is the CEO of TechCorp Inc., a technology company founded in 2020."
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Mary Johnson",
            "type": "Person",
            "attributes": {
                "entity_type": "person",
                "role_type": "executive",
                "position": "CTO",
                "company": "TechCorp Inc.",
                "source_chunk": 0
            },
            "confidence": 0.92,
            "status": "pending",
            "edited": False,
            "created_at": datetime.now().isoformat(),
            "source_text": "Mary Johnson is the CTO of TechCorp Inc. and holds a PhD in Computer Science."
        },
        {
            "id": str(uuid.uuid4()),
            "name": "TechCorp Inc.",
            "type": "Company",
            "attributes": {
                "entity_type": "company",
                "industry": "Technology",
                "founded": "2020",
                "location": "San Francisco",
                "source_chunk": 0
            },
            "confidence": 0.98,
            "status": "pending",
            "edited": False,
            "created_at": datetime.now().isoformat(),
            "source_text": "TechCorp Inc., a technology company founded in 2020 and based in San Francisco."
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Microsoft",
            "type": "Company",
            "attributes": {
                "entity_type": "company",
                "industry": "Technology",
                "source_chunk": 1
            },
            "confidence": 0.99,
            "status": "pending",
            "edited": False,
            "created_at": datetime.now().isoformat(),
            "source_text": "TechCorp Inc. has partnerships with Microsoft and Google."
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Google",
            "type": "Company",
            "attributes": {
                "entity_type": "company",
                "industry": "Technology",
                "source_chunk": 1
            },
            "confidence": 0.99,
            "status": "pending",
            "edited": False,
            "created_at": datetime.now().isoformat(),
            "source_text": "TechCorp Inc. has partnerships with Microsoft and Google."
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Sequoia Capital",
            "type": "Company",
            "attributes": {
                "entity_type": "company",
                "industry": "Venture Capital",
                "source_chunk": 2
            },
            "confidence": 0.94,
            "status": "pending",
            "edited": False,
            "created_at": datetime.now().isoformat(),
            "source_text": "The company recently raised $50 million in Series A funding led by Sequoia Capital."
        }
    ]
    
    # Sample relationships
    relationships = [
        {
            "id": str(uuid.uuid4()),
            "source_entity": "John Smith",
            "target_entity": "TechCorp Inc.",
            "type": "CEO_OF",
            "attributes": {
                "relationship_type": "employment",
                "role": "Chief Executive Officer",
                "source_chunk": 0
            },
            "confidence": 0.95,
            "status": "pending",
            "edited": False,
            "created_at": datetime.now().isoformat(),
            "source_text": "John Smith is the CEO of TechCorp Inc."
        },
        {
            "id": str(uuid.uuid4()),
            "source_entity": "Mary Johnson",
            "target_entity": "TechCorp Inc.",
            "type": "CTO_OF",
            "attributes": {
                "relationship_type": "employment",
                "role": "Chief Technology Officer",
                "source_chunk": 0
            },
            "confidence": 0.92,
            "status": "pending",
            "edited": False,
            "created_at": datetime.now().isoformat(),
            "source_text": "Mary Johnson is the CTO of TechCorp Inc."
        },
        {
            "id": str(uuid.uuid4()),
            "source_entity": "TechCorp Inc.",
            "target_entity": "Microsoft",
            "type": "PARTNERSHIP_WITH",
            "attributes": {
                "relationship_type": "business",
                "nature": "partnership",
                "source_chunk": 1
            },
            "confidence": 0.88,
            "status": "pending",
            "edited": False,
            "created_at": datetime.now().isoformat(),
            "source_text": "TechCorp Inc. has partnerships with Microsoft and Google."
        },
        {
            "id": str(uuid.uuid4()),
            "source_entity": "TechCorp Inc.",
            "target_entity": "Google",
            "type": "PARTNERSHIP_WITH",
            "attributes": {
                "relationship_type": "business",
                "nature": "partnership",
                "source_chunk": 1
            },
            "confidence": 0.88,
            "status": "pending",
            "edited": False,
            "created_at": datetime.now().isoformat(),
            "source_text": "TechCorp Inc. has partnerships with Microsoft and Google."
        },
        {
            "id": str(uuid.uuid4()),
            "source_entity": "Sequoia Capital",
            "target_entity": "TechCorp Inc.",
            "type": "INVESTED_IN",
            "attributes": {
                "relationship_type": "financial",
                "investment_type": "Series A",
                "amount": "$50 million",
                "source_chunk": 2
            },
            "confidence": 0.94,
            "status": "pending",
            "edited": False,
            "created_at": datetime.now().isoformat(),
            "source_text": "The company recently raised $50 million in Series A funding led by Sequoia Capital."
        }
    ]
    
    # Calculate statistics
    total_entities = len(entities)
    total_relationships = len(relationships)
    
    # Create session data
    session_data = {
        "session_id": session_id,
        "document_title": "TechCorp Inc. Company Profile",
        "document_source": "techcorp_profile.md",
        "created_at": datetime.now().isoformat(),
        "status": "pending_review",
        "entities": entities,
        "relationships": relationships,
        "statistics": {
            "total_entities": total_entities,
            "total_relationships": total_relationships,
            "approved_entities": 0,
            "approved_relationships": 0,
            "rejected_entities": 0,
            "rejected_relationships": 0,
            "pending_entities": total_entities,
            "pending_relationships": total_relationships
        },
        "metadata": {
            "extraction_method": "sample_data",
            "created_for": "demo_purposes"
        }
    }
    
    # Save to staging file
    staging_file = staging_dir / f'{session_id}.json'
    with open(staging_file, 'w', encoding='utf-8') as f:
        json.dump(session_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Created sample staging session: {session_id}")
    print(f"📄 Document: {session_data['document_title']}")
    print(f"👥 Entities: {total_entities}")
    print(f"🔗 Relationships: {total_relationships}")
    print(f"📁 File: {staging_file}")
    print(f"🌐 Review at: http://localhost:5001/entity-review")
    
    return session_id


if __name__ == "__main__":
    create_sample_staging_data()
