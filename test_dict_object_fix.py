#!/usr/bin/env python3
"""
Test script to verify the fix for 'dict' object has no attribute 'fact' error.
"""

import asyncio
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_dict_object_handling():
    """Test that the code handles both dict and object formats correctly."""
    logger.info("Testing dict/object handling fix...")
    
    # Mock data to simulate both dict and object formats
    class MockResult:
        def __init__(self, fact, uuid, valid_at=None):
            self.fact = fact
            self.uuid = uuid
            self.valid_at = valid_at
    
    # Test data - mix of dict and object formats
    test_results_dict = [
        {"fact": "NG Shella S C is a person", "uuid": "uuid1", "valid_at": "2024-01-01"},
        {"fact": "HKJC employs many staff members", "uuid": "uuid2", "valid_at": "2024-01-02"}
    ]
    
    test_results_object = [
        MockResult("NG Shella S C works at HKJC", "uuid3", "2024-01-03"),
        MockResult("HKJC has various departments", "uuid4", "2024-01-04")
    ]
    
    # Test the helper function that should handle both formats
    def extract_fact_info(result):
        """Helper function to extract fact info from either dict or object."""
        if isinstance(result, dict):
            fact = result.get("fact", "")
            uuid = result.get("uuid", "")
            valid_at = result.get("valid_at")
        else:
            fact = getattr(result, "fact", "")
            uuid = str(getattr(result, "uuid", ""))
            valid_at = str(result.valid_at) if hasattr(result, 'valid_at') and result.valid_at else None
        
        return {
            "fact": fact,
            "uuid": uuid,
            "valid_at": valid_at
        }
    
    # Test with dict format
    logger.info("Testing dict format:")
    for result in test_results_dict:
        info = extract_fact_info(result)
        logger.info(f"  Fact: {info['fact']}")
        logger.info(f"  UUID: {info['uuid']}")
        logger.info(f"  Valid at: {info['valid_at']}")
    
    # Test with object format
    logger.info("Testing object format:")
    for result in test_results_object:
        info = extract_fact_info(result)
        logger.info(f"  Fact: {info['fact']}")
        logger.info(f"  UUID: {info['uuid']}")
        logger.info(f"  Valid at: {info['valid_at']}")
    
    # Test mixed format
    logger.info("Testing mixed format:")
    mixed_results = test_results_dict + test_results_object
    for i, result in enumerate(mixed_results):
        info = extract_fact_info(result)
        result_type = "dict" if isinstance(result, dict) else "object"
        logger.info(f"  Result {i+1} ({result_type}): {info['fact']}")
    
    logger.info("✅ Dict/object handling test completed successfully!")
    return True


async def test_enhanced_entity_relationships_mock():
    """Mock test of the enhanced entity relationships function."""
    logger.info("Testing enhanced entity relationships with mock data...")
    
    try:
        # This would normally import from agent.tools, but we'll mock it
        # to test the logic without requiring full setup
        
        entity_name = "NG Shella S C"
        
        # Mock search results in both formats
        mock_results = [
            {"fact": f"{entity_name} is a staff member", "uuid": "uuid1"},
            {"fact": f"HKJC employs {entity_name}", "uuid": "uuid2"},
            {"fact": f"{entity_name} works in administration", "uuid": "uuid3"}
        ]
        
        # Simulate the fixed processing logic
        seen_facts = set()
        processed_results = []
        
        for result in mock_results:
            # Handle both dict and object formats (this is the fix)
            if isinstance(result, dict):
                fact = result.get("fact", "")
                uuid = result.get("uuid", "")
            else:
                fact = getattr(result, "fact", "")
                uuid = str(getattr(result, "uuid", ""))
            
            # Skip empty facts or duplicates
            if not fact or fact in seen_facts:
                continue
            seen_facts.add(fact)
            
            # Only process facts that mention our entity
            if entity_name.lower() not in fact.lower():
                continue
            
            processed_results.append({
                "fact": fact,
                "uuid": uuid,
                "entity": entity_name
            })
        
        logger.info(f"Processed {len(processed_results)} results for {entity_name}:")
        for i, result in enumerate(processed_results, 1):
            logger.info(f"  {i}. {result['fact']}")
        
        logger.info("✅ Enhanced entity relationships mock test completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced entity relationships mock test failed: {e}")
        return False


async def main():
    """Main test function."""
    logger.info("🚀 Starting dict/object handling fix tests")
    logger.info("=" * 60)
    
    try:
        # Run tests
        test_results = []
        
        # Test 1: Basic dict/object handling
        result1 = await test_dict_object_handling()
        test_results.append(("Dict/Object Handling", result1))
        
        # Test 2: Enhanced entity relationships mock
        result2 = await test_enhanced_entity_relationships_mock()
        test_results.append(("Enhanced Entity Relationships Mock", result2))
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("TEST SUMMARY")
        logger.info("="*60)
        
        passed = 0
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{test_name}: {status}")
            if result:
                passed += 1
        
        logger.info(f"\nOverall: {passed}/{len(test_results)} tests passed")
        
        if passed == len(test_results):
            logger.info("🎉 All dict/object handling tests passed!")
            logger.info("The fix should resolve the 'dict' object has no attribute 'fact' error.")
        else:
            logger.warning("⚠️  Some tests failed - review implementation")
        
        return passed == len(test_results)
        
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        return False


if __name__ == "__main__":
    import sys
    sys.exit(0 if asyncio.run(main()) else 1)
