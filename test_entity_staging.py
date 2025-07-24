#!/usr/bin/env python3
"""
Test script for entity staging functionality.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ingestion.graph_builder import GraphBuilder
from ingestion.chunker import DocumentChunk


async def test_entity_staging():
    """Test the entity staging functionality."""
    print("🧪 Testing Entity Staging System")
    print("=" * 50)
    
    # Create test document content
    test_content = """
    John Smith is the CEO of TechCorp Inc., a technology company.
    Mary Johnson is the CTO of TechCorp Inc.
    The company was founded in 2020 and is based in San Francisco.
    
    TechCorp Inc. has partnerships with Microsoft and Google.
    John Smith previously worked at Apple Inc. as a Senior Engineer.
    Mary Johnson holds a PhD in Computer Science from Stanford University.
    
    The company recently raised $50 million in Series A funding led by Sequoia Capital.
    """
    
    # Create test chunks
    chunks = [
        DocumentChunk(
            content=test_content,
            index=0,
            start_char=0,
            end_char=len(test_content),
            metadata={"test": True}
        )
    ]
    
    try:
        # Initialize graph builder
        print("📊 Initializing graph builder...")
        graph_builder = GraphBuilder()
        await graph_builder.initialize()
        
        # Test staging
        print("🔄 Testing entity staging...")
        result = await graph_builder.stage_document_entities(
            chunks=chunks,
            document_title="Test Document",
            document_source="test.txt",
            document_metadata={"test": True},
            use_staging=True
        )
        
        print("✅ Staging completed!")
        print(f"📋 Session ID: {result.get('session_id')}")
        print(f"👥 Entities extracted: {result.get('entities_extracted')}")
        print(f"🔗 Relationships extracted: {result.get('relationships_extracted')}")
        print(f"📊 Status: {result.get('status')}")
        
        # Check if staging file was created
        session_id = result.get('session_id')
        if session_id:
            staging_file = Path(f'staging/data/{session_id}.json')
            if staging_file.exists():
                print(f"✅ Staging file created: {staging_file}")
                
                # Read and display staging data
                import json
                with open(staging_file, 'r', encoding='utf-8') as f:
                    staging_data = json.load(f)
                
                print(f"📄 Document: {staging_data.get('document_title')}")
                print(f"📊 Statistics: {staging_data.get('statistics')}")
                print(f"👥 Entities found:")
                
                for i, entity in enumerate(staging_data.get('entities', [])[:5]):  # Show first 5
                    print(f"  {i+1}. {entity.get('name')} ({entity.get('type')}) - {entity.get('status')}")
                
                if len(staging_data.get('entities', [])) > 5:
                    print(f"  ... and {len(staging_data.get('entities', [])) - 5} more")
                
            else:
                print(f"❌ Staging file not found: {staging_file}")
        
        # Clean up
        await graph_builder.close()
        
        print("\n🎉 Entity staging test completed successfully!")
        print("🌐 You can now review entities at: http://localhost:5001/entity-review")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


async def test_web_ui_endpoints():
    """Test the web UI endpoints."""
    print("\n🌐 Testing Web UI Endpoints")
    print("=" * 50)
    
    try:
        import aiohttp
        
        # Test staging sessions endpoint
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get('http://localhost:5001/api/staging/sessions') as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Staging sessions endpoint working: {len(data.get('sessions', []))} sessions found")
                    else:
                        print(f"⚠️ Staging sessions endpoint returned {response.status}")
            except aiohttp.ClientConnectorError:
                print("⚠️ Web UI not running on localhost:5001")
                print("   Start it with: cd web_ui && python start.py")
                
    except ImportError:
        print("⚠️ aiohttp not available for endpoint testing")
    
    return True


def main():
    """Main test function."""
    print("🚀 Entity Review & Approval System Test")
    print("=" * 60)
    
    # Run staging test
    success = asyncio.run(test_entity_staging())
    
    if success:
        # Run web UI test
        asyncio.run(test_web_ui_endpoints())
        
        print("\n📋 Next Steps:")
        print("1. Start the web UI: cd web_ui && python start.py")
        print("2. Open http://localhost:5001/entity-review")
        print("3. Review and approve the extracted entities")
        print("4. Ingest approved entities to Graphiti")
    
    return success


if __name__ == "__main__":
    main()
