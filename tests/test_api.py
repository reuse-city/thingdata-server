import os
os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app, get_db
from app.database import Base, engine, SessionLocal, init_db

@pytest.fixture(scope="module")
def test_client():
    """Create test client."""
    init_db()
    
    from app.models import User
    from app.security import get_current_user
    app.dependency_overrides[get_current_user] = lambda: User(id="dummy", username="dummy_admin", role="admin")
    
    with TestClient(app) as client:
        yield client
        
    app.dependency_overrides.pop(get_current_user, None)
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_db():
    """Create fresh test database session for each test."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def test_thing_data():
    return {
        "type": "device",
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
    assert "ThingData Server" in response.text

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
    payload = {"data": test_thing_data}
    response = test_client.post("/api/v1/things", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["type"] == test_thing_data["type"]
    assert data["data"]["name"] == test_thing_data["name"]
    assert "id" in data
    assert "uri" in data

def test_get_thing(test_client, test_thing_data):
    """Test retrieving a thing."""
    data = test_thing_data.copy()
    data["name"] = {"default": f"Coffee Machine {uuid.uuid4()}"}
    create_response = test_client.post("/api/v1/things", json={"data": data})
    thing_id = create_response.json()["id"]

    response = test_client.get(f"/api/v1/things/{thing_id}")
    assert response.status_code == 200
    res = response.json()
    assert res["id"] == thing_id
    assert res["data"]["type"] == test_thing_data["type"]

def test_create_story(test_client, test_thing_data):
    """Test creating a repair story."""
    data = test_thing_data.copy()
    data["name"] = {"default": f"Coffee Machine {uuid.uuid4()}"}
    thing_response = test_client.post("/api/v1/things", json={"data": data})
    thing_id = thing_response.json()["id"]

    story_data = {
        "thing_id": thing_id,
        "data": {
            "type": "repair",
            "procedure": {
                "steps": [
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
        }
    }

    response = test_client.post("/api/v1/stories", json=story_data)
    assert response.status_code == 200
    res = response.json()
    assert res["thing_id"] == thing_id
    assert "id" in res
    assert "version" in res["data"]

def test_create_relationship(test_client, test_thing_data):
    """Test creating a relationship between things."""
    data1 = test_thing_data.copy()
    data1["name"] = {"default": f"Coffee Machine {uuid.uuid4()}"}
    data2 = test_thing_data.copy()
    data2["name"] = {"default": f"Coffee Component {uuid.uuid4()}"}

    thing1 = test_client.post("/api/v1/things", json={"data": data1}).json()
    thing2 = test_client.post("/api/v1/things", json={"data": data2}).json()

    relationship_data = {
        "source_type": "thing",
        "source_id": thing1["id"],
        "target_type": "thing",
        "target_id": thing2["id"],
        "relationship_type": "has_component",
        "direction": "unidirectional",
        "metadata": {
            "position": "top",
            "removable": True
        }
    }

    response = test_client.post("/api/v1/relationships", json=relationship_data)
    assert response.status_code == 200
    res = response.json()
    assert res["source_id"] == thing1["id"]
    assert res["target_id"] == thing2["id"]
    assert res["relationship_type"] == "has_component"

def test_get_relationships_subresource(test_client, test_thing_data):
    """Test retrieving relationships sub-resource endpoint."""
    data1 = test_thing_data.copy()
    data1["name"] = {"default": f"Thing A {uuid.uuid4()}"}
    data2 = test_thing_data.copy()
    data2["name"] = {"default": f"Thing B {uuid.uuid4()}"}

    thing1 = test_client.post("/api/v1/things", json={"data": data1}).json()
    thing2 = test_client.post("/api/v1/things", json={"data": data2}).json()

    relationship_data = {
        "source_type": "thing",
        "source_id": thing1["id"],
        "target_type": "thing",
        "target_id": thing2["id"],
        "relationship_type": "has_component",
        "direction": "unidirectional",
        "metadata": {}
    }
    test_client.post("/api/v1/relationships", json=relationship_data)

    response = test_client.get(f"/api/v1/things/{thing1['id']}/relationships")
    assert response.status_code == 200
    res = response.json()
    assert len(res) >= 1
    assert res[0]["source_id"] == thing1["id"]

def test_delete_endpoints(test_client, test_thing_data):
    """Test DELETE endpoints with X-Confirm-Delete header."""
    data = test_thing_data.copy()
    data["name"] = {"default": f"Thing to delete {uuid.uuid4()}"}
    thing = test_client.post("/api/v1/things", json={"data": data}).json()
    thing_id = thing["id"]

    response = test_client.delete(f"/api/v1/things/{thing_id}")
    assert response.status_code == 422

    response = test_client.delete(
        f"/api/v1/things/{thing_id}",
        headers={"X-Confirm-Delete": "true"}
    )
    assert response.status_code == 204

    response = test_client.get(f"/api/v1/things/{thing_id}")
    assert response.status_code == 404

# --- New Tests for Spec Alignment & PUT Endpoints ---

def test_put_thing(test_client, test_thing_data):
    """Test updating a thing with PUT."""
    data = test_thing_data.copy()
    data["name"] = {"default": f"Thing to update {uuid.uuid4()}"}
    thing = test_client.post("/api/v1/things", json={"data": data}).json()
    thing_id = thing["id"]

    update_payload = {
        "data": {
            "type": "appliance",
            "name": {"default": "Updated Coffee Maker"},
            "manufacturer": {"name": "NewBrand"}
        }
    }
    response = test_client.put(f"/api/v1/things/{thing_id}", json=update_payload)
    assert response.status_code == 200
    res = response.json()
    assert res["data"]["type"] == "appliance"
    assert res["data"]["name"]["default"] == "Updated Coffee Maker"
    assert "Updated Coffee Maker" in res["uri"]

def test_put_story(test_client, test_thing_data):
    """Test updating a story with PUT."""
    data = test_thing_data.copy()
    data["name"] = {"default": f"Coffee Machine {uuid.uuid4()}"}
    thing = test_client.post("/api/v1/things", json={"data": data}).json()
    thing_id = thing["id"]

    story_data = {
        "thing_id": thing_id,
        "data": {
            "type": "repair",
            "procedure": {"steps": [{"order": 1, "description": {"default": "Step 1"}}]}
        }
    }
    story = test_client.post("/api/v1/stories", json=story_data).json()
    story_id = story["id"]

    update_payload = {
        "data": {
            "type": "maintenance",
            "author": {
                "uri": "author:123",
                "name": "Jane Doe",
                "instance_uri": "https://instance.example.com"
            }
        }
    }
    response = test_client.put(f"/api/v1/stories/{story_id}", json=update_payload)
    assert response.status_code == 200
    res = response.json()
    assert res["data"]["type"] == "maintenance"
    assert res["data"]["author"]["name"] == "Jane Doe"

def test_guide_endpoints_and_put(test_client, test_thing_data):
    """Test Guide creation, fetching, PUT updates, and archival endpoints."""
    # Create guide
    guide_data = {
        "data": {
            "type": {
                "primary": "tutorial",
                "secondary": "repair"
            },
            "content": {
                "title": {"default": "Repair Hinge Tutorial"}
            },
            "external_content": {
                "type": "video",
                "url": {
                    "primary": "https://example.com/video",
                    "archive": {
                        "wayback": "https://web.archive.org/video",
                        "status": "AVAILABLE"
                    }
                },
                "format": "mp4",
                "language": "en"
            }
        }
    }
    response = test_client.post("/api/v1/guides", json=guide_data)
    assert response.status_code == 200
    guide = response.json()
    guide_id = guide["id"]

    # Verify Guide sub-resource: external-content
    response = test_client.get(f"/api/v1/guides/{guide_id}/external-content")
    assert response.status_code == 200
    assert response.json()["type"] == "video"

    # Verify Guide sub-resource: archive
    response = test_client.get(f"/api/v1/guides/{guide_id}/archive")
    assert response.status_code == 200
    assert response.json()["status"] == "AVAILABLE"

    # PUT update guide
    update_payload = {
        "data": {
            "type": {"primary": "manual"},
            "content": {
                "title": {"default": "Updated Guide Title"}
            }
        }
    }
    response = test_client.put(f"/api/v1/guides/{guide_id}", json=update_payload)
    assert response.status_code == 200
    res = response.json()
    assert res["data"]["type"]["primary"] == "manual"
    assert res["data"]["content"]["title"]["default"] == "Updated Guide Title"