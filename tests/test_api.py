import pytest
from fastapi.testclient import TestClient
import uuid
from datetime import datetime

from app.main import app
from app.schemas import MultilingualText, Properties, Manufacturer

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

def test_read_main(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "ThingData API"

def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in ["healthy", "unhealthy"]

def test_create_thing(client, test_thing_data):
    """Test creating a new thing."""
    response = client.post("/api/v1/things", json=test_thing_data)
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == test_thing_data["type"]
    assert data["name"] == test_thing_data["name"]
    assert "id" in data

def test_get_thing(client, test_thing_data):
    """Test retrieving a thing."""
    # First create a thing
    create_response = client.post("/api/v1/things", json=test_thing_data)
    thing_id = create_response.json()["id"]

    # Then retrieve it
    response = client.get(f"/api/v1/things/{thing_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == thing_id
    assert data["type"] == test_thing_data["type"]

def test_list_things(client, test_thing_data):
    """Test listing things."""
    # Create a few things
    client.post("/api/v1/things", json=test_thing_data)
    client.post("/api/v1/things", json=test_thing_data)

    response = client.get("/api/v1/things")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    assert all(isinstance(thing["id"], str) for thing in data)

def test_create_story(client, test_thing_data):
    """Test creating a repair story."""
    # First create a thing
    thing_response = client.post("/api/v1/things", json=test_thing_data)
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
                "tools": ["screwdriver"]
            }
        ]
    }

    response = client.post("/api/v1/stories", json=story_data)
    assert response.status_code == 200
    data = response.json()
    assert data["thing_id"] == thing_id
    assert "id" in data
    assert "version" in data

def test_nonexistent_thing(client):
    """Test getting a nonexistent thing."""
    response = client.get(f"/api/v1/things/{uuid.uuid4()}")
    assert response.status_code == 404
