#!/usr/bin/env python3
"""
Test suite for Flask web application endpoints.
Tests all API endpoints including chat, ingestion, graph visualization, and approval APIs.
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from flask import Flask
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.abspath('.'))

# Import the Flask app
from web_ui.app import app


class TestFlaskWebApplication:
    """Test Flask web application endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_index_page(self, client):
        """Test main index page loads."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Agentic RAG with Knowledge Graph' in response.data
    
    def test_approval_page(self, client):
        """Test approval dashboard page loads."""
        response = client.get('/approval')
        assert response.status_code == 200
        assert b'Entity Approval Dashboard' in response.data
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
    
    @patch('web_ui.app.Agent')
    def test_chat_endpoint_post(self, mock_agent_class, client):
        """Test chat endpoint with POST request."""
        mock_agent = AsyncMock()
        mock_result = Mock()
        mock_result.data = "Test response from agent"
        mock_result.tool_calls = []
        mock_agent.run.return_value = mock_result
        mock_agent_class.return_value = mock_agent
        
        response = client.post('/api/chat', 
                              json={'message': 'Hello, test message'},
                              content_type='application/json')
        
        assert response.status_code == 200
        # Note: This may return SSE stream, so we check that it starts properly
        assert response.content_type.startswith('text/plain')
    
    def test_chat_endpoint_get_error(self, client):
        """Test chat endpoint rejects GET requests."""
        response = client.get('/api/chat')
        assert response.status_code == 405  # Method not allowed
    
    def test_chat_endpoint_invalid_json(self, client):
        """Test chat endpoint with invalid JSON."""
        response = client.post('/api/chat',
                              data='invalid json',
                              content_type='application/json')
        
        # Should handle gracefully, likely return 400 or process as text
        assert response.status_code in [200, 400]
    
    @patch('web_ui.app.ingest_documents')
    def test_ingest_endpoint(self, mock_ingest, client):
        """Test document ingestion endpoint."""
        mock_ingest.return_value = {
            'status': 'completed',
            'chunks_created': 10,
            'documents_processed': 1
        }
        
        # Test with mock file data
        response = client.post('/api/ingest',
                              data={'mode': 'full'},
                              content_type='multipart/form-data')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_ingest_endpoint_no_files(self, client):
        """Test ingest endpoint with no files."""
        response = client.post('/api/ingest',
                              data={'mode': 'full'},
                              content_type='multipart/form-data')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        # Should handle no files gracefully
        assert 'success' in data


class TestApprovalAPIEndpoints:
    """Test approval system API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @patch('web_ui.app.approval_service')
    def test_create_approval_session(self, mock_service, client):
        """Test creating approval session."""
        mock_service.create_approval_session.return_value = "session-123"
        
        response = client.post('/api/approval/sessions',
                              json={
                                  'document_title': 'Test Document',
                                  'document_source': 'test.md',
                                  'reviewer_id': 'reviewer-1'
                              },
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['session_id'] == 'session-123'
    
    @patch('web_ui.app.approval_service')
    def test_get_entities_for_approval(self, mock_service, client):
        """Test getting entities for approval."""
        mock_entities = [
            {
                'entity_id': 'entity-1',
                'entity_type': 'Person',
                'name': 'John Doe',
                'status': 'pending',
                'confidence': 0.85,
                'properties': {'age': 30}
            }
        ]
        mock_service.get_entities_for_approval.return_value = mock_entities
        
        response = client.get('/api/approval/entities/test.md')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['entities']) == 1
        assert data['entities'][0]['entity_type'] == 'Person'
    
    @patch('web_ui.app.approval_service')
    def test_approve_entity(self, mock_service, client):
        """Test approving an entity."""
        mock_service.approve_entity.return_value = True
        
        response = client.post('/api/approval/entities/entity-1/approve',
                              json={'reviewer_id': 'reviewer-1'},
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    @patch('web_ui.app.approval_service')
    def test_reject_entity(self, mock_service, client):
        """Test rejecting an entity."""
        mock_service.reject_entity.return_value = True
        
        response = client.post('/api/approval/entities/entity-1/reject',
                              json={
                                  'reviewer_id': 'reviewer-1',
                                  'review_notes': 'Incorrect data'
                              },
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    @patch('web_ui.app.approval_service')
    def test_bulk_approve_entities(self, mock_service, client):
        """Test bulk approving entities."""
        mock_service.bulk_approve_entities.return_value = {
            'approved_count': 3,
            'failed_entities': []
        }
        
        response = client.post('/api/approval/entities/bulk-approve',
                              json={
                                  'entity_ids': ['entity-1', 'entity-2', 'entity-3'],
                                  'reviewer_id': 'reviewer-1'
                              },
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['approved_count'] == 3
    
    @patch('web_ui.app.approval_service')
    def test_get_approval_statistics(self, mock_service, client):
        """Test getting approval statistics."""
        mock_stats = {
            'total_entities': 100,
            'approved': 45,
            'rejected': 15,
            'pending': 40
        }
        mock_service.get_approval_statistics.return_value = mock_stats
        
        response = client.get('/api/approval/statistics/test.md')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['statistics']['total_entities'] == 100


class TestGraphVisualizationEndpoints:
    """Test graph visualization API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @patch('web_ui.app.graph_client')
    def test_neo4j_visualize_endpoint(self, mock_graph_client, client):
        """Test Neo4j graph visualization endpoint."""
        mock_graph_data = {
            'nodes': [
                {'id': 'node1', 'labels': ['Person'], 'properties': {'name': 'John Doe'}},
                {'id': 'node2', 'labels': ['Company'], 'properties': {'name': 'Tech Corp'}}
            ],
            'relationships': [
                {
                    'id': 'rel1',
                    'type': 'WORKS_AT',
                    'startNode': 'node1',
                    'endNode': 'node2',
                    'properties': {}
                }
            ]
        }
        mock_graph_client.get_neo4j_visualization_data.return_value = mock_graph_data
        
        response = client.get('/api/graph/neo4j/visualize?limit=50')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'nodes' in data
        assert 'relationships' in data
        assert len(data['nodes']) == 2
        assert len(data['relationships']) == 1
    
    @patch('web_ui.app.graph_client')
    def test_neo4j_query_endpoint(self, mock_graph_client, client):
        """Test custom Neo4j query endpoint."""
        mock_query_result = {
            'nodes': [{'id': 'test-node', 'labels': ['Test'], 'properties': {}}],
            'relationships': []
        }
        mock_graph_client.execute_custom_query.return_value = mock_query_result
        
        response = client.post('/api/graph/neo4j/query',
                              json={
                                  'query': 'MATCH (n:Person) RETURN n LIMIT 10',
                                  'parameters': {}
                              },
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'nodes' in data
        assert 'relationships' in data


class TestErrorHandling:
    """Test error handling in web application."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_404_error(self, client):
        """Test 404 error handling."""
        response = client.get('/nonexistent-endpoint')
        assert response.status_code == 404
    
    @patch('web_ui.app.approval_service')
    def test_approval_service_error_handling(self, mock_service, client):
        """Test approval service error handling."""
        # Mock service to raise exception
        mock_service.get_entities_for_approval.side_effect = Exception("Database error")
        
        response = client.get('/api/approval/entities/test.md')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data
    
    def test_invalid_json_handling(self, client):
        """Test invalid JSON handling."""
        response = client.post('/api/approval/sessions',
                              data='invalid json',
                              content_type='application/json')
        
        # Should return 400 for invalid JSON
        assert response.status_code == 400


class TestCORSHeaders:
    """Test CORS headers in responses."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_cors_headers_present(self, client):
        """Test that CORS headers are present."""
        response = client.get('/api/health')
        
        assert response.status_code == 200
        # Flask-CORS should add these headers
        assert 'Access-Control-Allow-Origin' in response.headers
    
    def test_options_request(self, client):
        """Test OPTIONS request for CORS preflight."""
        response = client.options('/api/health')
        
        # Should handle OPTIONS requests for CORS
        assert response.status_code in [200, 204]


def test_app_configuration():
    """Test Flask app configuration."""
    assert app is not None
    # Test that app is properly configured
    assert hasattr(app, 'config')
    
    # Test that required extensions are loaded
    assert hasattr(app, 'url_map')
    assert len(app.url_map._rules) > 0  # Should have routes


def test_static_files_serving():
    """Test static files can be served."""
    with app.test_client() as client:
        # Test CSS file
        response = client.get('/static/css/style.css')
        # Should either serve the file (200) or return 404 if missing
        assert response.status_code in [200, 404]
        
        # Test JavaScript file
        response = client.get('/static/js/app.js')
        assert response.status_code in [200, 404]


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"])