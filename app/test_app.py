"""
Unit tests for Flask API
"""
import pytest
import json
from app import app as flask_app


@pytest.fixture
def app():
    """Create and configure a test app instance"""
    flask_app.config['TESTING'] = True
    yield flask_app


@pytest.fixture
def client(app):
    """A test client for the app"""
    return app.test_client()


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert 'version' in data
    assert 'timestamp' in data


def test_ready_endpoint(client):
    """Test readiness check endpoint"""
    response = client.get('/ready')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data['status'] == 'ready'


def test_metrics_endpoint(client):
    """Test Prometheus metrics endpoint"""
    response = client.get('/metrics')
    assert response.status_code == 200
    assert b'app_requests_total' in response.data


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get('/')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data['name'] == 'GitOps Demo API'
    assert 'version' in data
    assert 'endpoints' in data


def test_get_items_empty(client):
    """Test getting items when list is empty"""
    response = client.get('/api/items')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data['count'] == 0
    assert data['items'] == []


def test_create_item(client):
    """Test creating a new item"""
    item_data = {
        'name': 'Test Item',
        'description': 'This is a test item'
    }

    response = client.post('/api/items',
                           data=json.dumps(item_data),
                           content_type='application/json')

    assert response.status_code == 201

    data = json.loads(response.data)
    assert data['name'] == 'Test Item'
    assert data['description'] == 'This is a test item'
    assert 'id' in data
    assert 'created_at' in data


def test_create_item_without_name(client):
    """Test creating item without required name field"""
    item_data = {
        'description': 'Missing name'
    }

    response = client.post('/api/items',
                           data=json.dumps(item_data),
                           content_type='application/json')

    assert response.status_code == 400

    data = json.loads(response.data)
    assert 'error' in data


def test_get_item(client):
    """Test getting a specific item"""
    # First create an item
    item_data = {'name': 'Test Item'}
    create_response = client.post('/api/items',
                                  data=json.dumps(item_data),
                                  content_type='application/json')

    created_item = json.loads(create_response.data)
    item_id = created_item['id']

    # Now get it
    response = client.get(f'/api/items/{item_id}')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data['id'] == item_id
    assert data['name'] == 'Test Item'


def test_get_nonexistent_item(client):
    """Test getting an item that doesn't exist"""
    response = client.get('/api/items/9999')
    assert response.status_code == 404

    data = json.loads(response.data)
    assert 'error' in data


def test_update_item(client):
    """Test updating an existing item"""
    # Create item
    item_data = {'name': 'Original Name'}
    create_response = client.post('/api/items',
                                  data=json.dumps(item_data),
                                  content_type='application/json')

    created_item = json.loads(create_response.data)
    item_id = created_item['id']

    # Update it
    update_data = {'name': 'Updated Name', 'description': 'New description'}
    response = client.put(f'/api/items/{item_id}',
                          data=json.dumps(update_data),
                          content_type='application/json')

    assert response.status_code == 200

    data = json.loads(response.data)
    assert data['name'] == 'Updated Name'
    assert data['description'] == 'New description'
    assert 'updated_at' in data


def test_update_nonexistent_item(client):
    """Test updating an item that doesn't exist"""
    update_data = {'name': 'Test'}
    response = client.put('/api/items/9999',
                          data=json.dumps(update_data),
                          content_type='application/json')

    assert response.status_code == 404


def test_delete_item(client):
    """Test deleting an item"""
    # Create item
    item_data = {'name': 'To Delete'}
    create_response = client.post('/api/items',
                                  data=json.dumps(item_data),
                                  content_type='application/json')

    created_item = json.loads(create_response.data)
    item_id = created_item['id']

    # Delete it
    response = client.delete(f'/api/items/{item_id}')
    assert response.status_code == 204

    # Verify it's gone
    get_response = client.get(f'/api/items/{item_id}')
    assert get_response.status_code == 404


def test_delete_nonexistent_item(client):
    """Test deleting an item that doesn't exist"""
    response = client.delete('/api/items/9999')
    assert response.status_code == 404


def test_full_crud_workflow(client):
    """Test complete CRUD workflow"""
    # Create
    create_data = {'name': 'Workflow Test', 'description': 'Testing CRUD'}
    create_response = client.post('/api/items',
                                  data=json.dumps(create_data),
                                  content_type='application/json')
    assert create_response.status_code == 201
    item = json.loads(create_response.data)

    # Read
    read_response = client.get(f'/api/items/{item["id"]}')
    assert read_response.status_code == 200

    # Update
    update_data = {'name': 'Updated Workflow Test'}
    update_response = client.put(f'/api/items/{item["id"]}',
                                 data=json.dumps(update_data),
                                 content_type='application/json')
    assert update_response.status_code == 200

    # Delete
    delete_response = client.delete(f'/api/items/{item["id"]}')
    assert delete_response.status_code == 204
