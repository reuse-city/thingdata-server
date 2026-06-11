import pytest
from fastapi.testclient import TestClient
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app, get_db
from app.database import Base

# Set up isolated in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Override the database dependency in FastAPI
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def test_client():
    """Create test client."""
    # Set up test database tables
    Base.metadata.create_all(bind=test_engine)
    
    client = TestClient(app)
    yield client
    
    # Clean up test database tables
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def test_db():
    """Create fresh test database session for each test."""
    db = TestingSessionLocal()
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
    # First create a thing with a unique name/URI
    data = test_thing_data.copy()
    data["name"] = {"default": f"Coffee Machine {uuid.uuid4()}"}
    create_response = test_client.post("/api/v1/things", json=data)
    thing_id = create_response.json()["id"]

    # Then retrieve it
    response = test_client.get(f"/api/v1/things/{thing_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == thing_id
    assert data["type"] == test_thing_data["type"]

def test_create_story(test_client, test_thing_data):
    """Test creating a repair story."""
    # First create a thing with a unique name/URI
    data = test_thing_data.copy()
    data["name"] = {"default": f"Coffee Machine {uuid.uuid4()}"}
    thing_response = test_client.post("/api/v1/things", json=data)
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
    # Create two things with unique names/URIs
    data1 = test_thing_data.copy()
    data1["name"] = {"default": f"Coffee Machine {uuid.uuid4()}"}
    data2 = test_thing_data.copy()
    data2["name"] = {"default": f"Coffee Component {uuid.uuid4()}"}

    thing1 = test_client.post("/api/v1/things", json=data1).json()
    thing2 = test_client.post("/api/v1/things", json=data2).json()

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
    data = response.json()
    assert data["source_id"] == thing1["id"]
    assert data["target_id"] == thing2["id"]
    assert data["relationship_type"] == "has_component"

def test_get_relationships_subresource(test_client, test_thing_data):
    """Test retrieving relationships sub-resource endpoint."""
    # Create two things
    data1 = test_thing_data.copy()
    data1["name"] = {"default": f"Thing A {uuid.uuid4()}"}
    data2 = test_thing_data.copy()
    data2["name"] = {"default": f"Thing B {uuid.uuid4()}"}

    thing1 = test_client.post("/api/v1/things", json=data1).json()
    thing2 = test_client.post("/api/v1/things", json=data2).json()

    # Create relationship
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

    # Fetch sub-resource relationships
    response = test_client.get(f"/api/v1/things/{thing1['id']}/relationships")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["source_id"] == thing1["id"]

def test_delete_endpoints(test_client, test_thing_data):
    """Test DELETE endpoints with X-Confirm-Delete header."""
    # Create a thing
    data = test_thing_data.copy()
    data["name"] = {"default": f"Thing to delete {uuid.uuid4()}"}
    thing = test_client.post("/api/v1/things", json=data).json()
    thing_id = thing["id"]

    # Delete without header should fail (FastAPI raises validation error since header is required)
    response = test_client.delete(f"/api/v1/things/{thing_id}")
    assert response.status_code == 422

    # Delete with header should succeed
    response = test_client.delete(
        f"/api/v1/things/{thing_id}",
        headers={"X-Confirm-Delete": "true"}
    )
    assert response.status_code == 204

    # Get should fail
    response = test_client.get(f"/api/v1/things/{thing_id}")
    assert response.status_code == 404