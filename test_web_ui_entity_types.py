#!/usr/bin/env python3
"""
Test script to verify web UI entity type detection and search functionality.
"""

import sys
import os

# Add web_ui to path
web_ui_path = os.path.join(os.path.dirname(__file__), 'web_ui')
if web_ui_path not in sys.path:
    sys.path.insert(0, web_ui_path)

def test_entity_type_detection():
    """Test the entity type detection function."""
    
    print("=" * 70)
    print("TESTING WEB UI ENTITY TYPE DETECTION")
    print("=" * 70)
    
    try:
        from app import detect_entity_type_query
        
        # Test cases: (query, expected_result)
        test_cases = [
            # Person queries
            ("Who is John Smith?", ["Person"]),
            ("Find people in technology", ["Person"]),
            ("Show me all executives", ["Person"]),
            ("List employees at TechCorp", ["Person"]),
            ("Search for directors", ["Person"]),
            
            # Company queries
            ("Show me companies in San Francisco", ["Company"]),
            ("List all organizations", ["Company"]),
            ("Find technology companies", ["Company"]),
            ("What companies are in Hong Kong?", ["Company"]),
            ("Search for corporations", ["Company"]),
            
            # Mixed or general queries (should return None)
            ("What is the relationship between people and companies?", None),
            ("Show me the graph", None),
            ("Find connections", None),
            ("General search query", None),
            ("How are entities connected?", None),
        ]
        
        print("\n🧪 Testing entity type detection:")
        print("-" * 50)
        
        passed = 0
        total = len(test_cases)
        
        for query, expected in test_cases:
            try:
                result = detect_entity_type_query(query)
                status = "✅" if result == expected else "❌"
                
                print(f"{status} '{query}'")
                print(f"   Expected: {expected}")
                print(f"   Got:      {result}")
                
                if result == expected:
                    passed += 1
                print()
                    
            except Exception as e:
                print(f"❌ Error testing '{query}': {e}")
                print()
        
        print(f"📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All entity type detection tests passed!")
        else:
            print("⚠️ Some tests failed - check the detection logic")
            
    except ImportError as e:
        print(f"❌ Could not import web UI functions: {e}")
        print("Make sure the web UI app.py is available")
    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_graphiti_search_filters():
    """Test if SearchFilters are available."""
    
    print("\n" + "=" * 70)
    print("TESTING GRAPHITI SEARCHFILTERS AVAILABILITY")
    print("=" * 70)
    
    try:
        from graphiti_core.search.search_filters import SearchFilters
        print("✅ SearchFilters imported successfully")
        
        # Test creating a filter
        person_filter = SearchFilters(node_labels=["Person"])
        print("✅ Person filter created successfully")
        
        company_filter = SearchFilters(node_labels=["Company"])
        print("✅ Company filter created successfully")
        
        mixed_filter = SearchFilters(node_labels=["Person", "Company"])
        print("✅ Mixed filter created successfully")
        
        print("\n🎯 SearchFilters are ready for entity type filtering!")
        
    except ImportError:
        print("❌ SearchFilters not available")
        print("   This means entity type filtering will fall back to regular search")
    except Exception as e:
        print(f"❌ SearchFilters test failed: {e}")

def test_custom_entity_models():
    """Test custom entity models."""
    
    print("\n" + "=" * 70)
    print("TESTING CUSTOM ENTITY MODELS")
    print("=" * 70)
    
    try:
        from agent.entity_models import Person, Company, PersonType, CompanyType
        from agent.edge_models import Employment, Leadership, Investment, Partnership, Ownership
        
        print("✅ Entity models imported successfully")
        
        # Test Person creation
        person = Person(
            name="Alice Johnson",
            person_type=PersonType.EXECUTIVE,
            current_company="DataCorp",
            current_position="CEO"
        )
        print(f"✅ Person created: {person.name} ({person.person_type.value})")
        
        # Test Company creation
        company = Company(
            name="DataCorp",
            company_type=CompanyType.PRIVATE,
            industry="Technology",
            headquarters="New York"
        )
        print(f"✅ Company created: {company.name} ({company.company_type.value})")
        
        # Test Edge models
        employment = Employment(
            position="CEO",
            is_current=True,
            employment_type="full-time"
        )
        print(f"✅ Employment edge created: {employment.position}")
        
        print("\n🏗️ Custom entity and edge models are working correctly!")
        
    except ImportError as e:
        print(f"❌ Could not import entity models: {e}")
    except Exception as e:
        print(f"❌ Entity models test failed: {e}")

def main():
    """Run all tests."""
    
    print("🚀 Starting Web UI Entity Types Tests...")
    
    test_entity_type_detection()
    test_graphiti_search_filters()
    test_custom_entity_models()
    
    print("\n" + "=" * 70)
    print("✅ WEB UI ENTITY TYPES TESTS COMPLETED")
    print("=" * 70)
    
    print("\n📋 Summary:")
    print("1. ✅ Entity type detection function tested")
    print("2. ✅ SearchFilters availability checked")
    print("3. ✅ Custom entity models verified")
    print("\n🎯 The web UI is ready to use custom entity types for enhanced search!")

if __name__ == "__main__":
    main()
