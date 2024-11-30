import pytest
from fastapi.testclient import TestClient
import uuid
from datetime import datetime

from app.main import app, get_db
from app.database import Base, engine, SessionLocal

@pytest.fixture(scope="module")
def test_client():
    """Create test client."""
    # Set up test database
    Base.metadata.create_all(bind=engine)
    
    client = TestClient(app)
    yield client
    
    # Clean up
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_db():
    """Create fresh database session for each test."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def test_thing_data():
    return {
        "type": "appliance",
        "name": {
            "default": "Coffee Machine",
            "translations": {
                "es": "Máquina de Café",
                "de": "Kaffeemaschine"
            }
        },
        "manufacturer": {
            "name": "BaristaPlus",
            "website": "https://example.com",
            "contact": "info@example.com"
        },
        "properties": {
            "dimensions": {
                "length": 30.0,
                "width": 20.0,
                "height": 40.0
            },
            "materials": ["steel", "plastic", "glass"],
            "serial_number": "BPC123456"
        }
    }

def test_read_main(test_client):
    """Test root endpoint."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert "ThingData Server" in response.text  # Updated to match HTML response

def test_health_check(test_client):
    """Test health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "components" in data
    assert "metrics" in data

def test_create_thing(test_client, test_thing_data):
    """Test creating a new thing."""
    response = test_client.post("/api/v1/things", json=test_thing_data)
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == test_thing_data["type"]
    assert data["name"] == test_thing_data["name"]
    assert "id" in data
    assert "uri" in data

def test_get_thing(test_client, test_thing_data):
    """Test retrieving a thing."""
    # First create a thing
    create_response = test_client.post("/api/v1/things", json=test_thing_data)
    thing_id = create_response.json()["id"]

    # Then retrieve it
    response = test_client.get(f"/api/v1/things/{thing_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == thing_id
    assert data["type"] == test_thing_data["type"]

def test_create_story(test_client, test_thing_data):
    """Test creating a repair story."""
    # First create a thing
    thing_response = test_client.post("/api/v1/things", json=test_thing_data)
    thing_id = thing_response.json()["id"]

    story_data = {
        "thing_id": thing_id,
        "type": "repair",
        "procedure": [
            {
                "order": 1,
                "description": {
                    "default": "Remove top cover",
                    "translations": {
                        "es": "Quitar la tapa superior"
                    }
                },
                "warnings": ["Disconnect power first"],
                "tools": ["screwdriver"],
                "media": []
            }
        ]
    }

    response = test_client.post("/api/v1/stories", json=story_data)
    assert response.status_code == 200
    data = response.json()
    assert data["thing_id"] == thing_id
    assert "id" in data
    assert "version" in data

def test_create_relationship(test_client, test_thing_data):
    """Test creating a relationship between things."""
    # Create two things
    thing1 = test_client.post("/api/v1/things", json=test_thing_data).json()
    thing2 = test_client.post("/api/v1/things", json=test_thing_data).json()

    relationship_data = {
        "thing_id": thing1["id"],
        "relationship_type": "has_component",
        "target_uri": thing2["id"],
        "relation_metadata": {
            "position": "top",
            "removable": True
        }
    }

    response = test_client.post("/api/v1/relationships", json=relationship_data)
    assert response.status_code == 200
    data = response.json()
    assert data["thing_id"] == thing1["id"]
    assert data["target_uri"] == thing2["id"]