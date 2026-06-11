import os
os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app, get_db, get_federation
from app.database import Base, engine, SessionLocal, init_db
from app.models import Instance, Thing
from app.federation import FederationManager

@pytest.fixture(scope="function")
def test_setup():
    """Create test setup containing client and federation manager."""
    init_db()
    
    # Create a fresh FederationManager for this test and inject it
    fed_manager = FederationManager()
    
    # We override get_federation to return this specific manager
    def override_get_federation():
        return fed_manager
        
    app.dependency_overrides[get_federation] = override_get_federation
    
    from app.security import get_current_user, verify_federation_request
    from app.models import User
    app.dependency_overrides[get_current_user] = lambda: User(id="dummy", username="dummy_admin", role="admin")
    app.dependency_overrides[verify_federation_request] = lambda: "https://repairhub-berlin.example.com"
    
    with TestClient(app) as client:
        # Also set it on the app state directly
        client.app.state.federation = fed_manager
        yield client, fed_manager
        
    # Clean up overrides
    app.dependency_overrides.pop(get_federation, None)
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(verify_federation_request, None)
    Base.metadata.drop_all(bind=engine)

def test_webfinger_discovery_default(test_setup):
    """Test webfinger discovery with default/no resource parameter."""
    client, fed_manager = test_setup
    response = client.get("/.well-known/webfinger")
    assert response.status_code == 200
    data = response.json()
    assert data["subject"] == fed_manager.instance_uri
    assert any(link["rel"] == "self" for link in data["links"])

def test_webfinger_discovery_resource_found(test_setup):
    """Test webfinger discovery when resource exists locally."""
    client, fed_manager = test_setup
    
    # Create a Thing in the test database
    db = SessionLocal()
    thing_uri = "thing:device/BaristaPlus/Coffee-Machine"
    db_thing = Thing(
        id=str(uuid.uuid4()),
        uri=thing_uri,
        type="device",
        name={"default": "Coffee Machine"},
        manufacturer={"name": "BaristaPlus"},
        properties={}
    )
    db.add(db_thing)
    db.commit()
    db.close()

    response = client.get(f"/.well-known/webfinger?resource={thing_uri}")
    assert response.status_code == 200
    data = response.json()
    assert data["subject"] == thing_uri
    assert len(data["links"]) == 1
    assert data["links"][0]["rel"] == "self"
    assert "api/v1/things" in data["links"][0]["href"]

def test_webfinger_discovery_resource_not_found(test_setup):
    """Test webfinger discovery fallback when resource doesn't exist locally."""
    client, fed_manager = test_setup
    response = client.get("/.well-known/webfinger?resource=thing:nonexistent")
    assert response.status_code == 200
    data = response.json()
    assert data["subject"] == fed_manager.instance_uri

def test_connect_instance_success(test_setup):
    """Test registering/connecting a new federation peer instance."""
    client, fed_manager = test_setup
    peer_uri = "https://repairhub-berlin.example.com"
    payload = {
        "instance_uri": peer_uri,
        "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...\n-----END PUBLIC KEY-----",
        "capabilities": ["sync", "search"],
        "languages": ["en", "de"],
        "instance_name": "RepairHub Berlin",
        "instance_type": "peer"
    }
    
    response = client.post("/api/v1/federation/connect", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "connected"
    assert data["instance"]["uri"] == peer_uri
    assert data["instance"]["name"] == "RepairHub Berlin"
    
    # Verify memory store
    assert peer_uri in fed_manager.known_instances

def test_connect_instance_missing_fields(test_setup):
    """Test connection validation failures."""
    client, fed_manager = test_setup
    payload = {
        "instance_uri": "https://repairhub-berlin.example.com"
        # missing public_key
    }
    response = client.post("/api/v1/federation/connect", json=payload)
    assert response.status_code == 400

def test_announce_event(test_setup):
    """Test receiving a content announcement from a peer."""
    client, fed_manager = test_setup
    payload = {
        "type": "thing",
        "uri": "thing:device/BaristaPlus/Coffee-Machine",
        "timestamp": datetime.utcnow().isoformat()
    }
    response = client.post("/api/v1/federation/announce", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "announced"

def test_sync_resources_all(test_setup):
    """Test federation sync endpoint returns all when no filter is supplied."""
    client, fed_manager = test_setup
    
    # Populate a Thing in database
    db = SessionLocal()
    thing_uri = "thing:device/BaristaPlus/Coffee-Machine"
    db_thing = Thing(
        id=str(uuid.uuid4()),
        uri=thing_uri,
        type="device",
        name={"default": "Coffee Machine"},
        manufacturer={"name": "BaristaPlus"},
        properties={}
    )
    db.add(db_thing)
    db.commit()
    db.close()

    response = client.post("/api/v1/federation/sync", json={})
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert any(item["type"] == "thing" and item["data"]["uri"] == thing_uri for item in data["results"])

def test_sync_resources_filtered(test_setup):
    """Test federation sync endpoint returns only requested URIs."""
    client, fed_manager = test_setup
    
    db = SessionLocal()
    thing_uri = "thing:device/BaristaPlus/Coffee-Machine"
    db_thing = Thing(
        id=str(uuid.uuid4()),
        uri=thing_uri,
        type="device",
        name={"default": "Coffee Machine"},
        manufacturer={"name": "BaristaPlus"},
        properties={}
    )
    db.add(db_thing)
    db.commit()
    db.close()

    payload = {
        "uris": [thing_uri]
    }
    response = client.post("/api/v1/federation/sync", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["data"]["uri"] == thing_uri

def test_discover_peers(test_setup):
    """Test retrieving connected peer list."""
    client, fed_manager = test_setup
    
    # Connect a peer
    peer_uri = "https://repairhub-berlin.example.com"
    payload = {
        "instance_uri": peer_uri,
        "public_key": "some-pubkey"
    }
    client.post("/api/v1/federation/connect", json=payload)

    response = client.get("/api/v1/federation/discover")
    assert response.status_code == 200
    data = response.json()
    assert "peers" in data
    assert len(data["peers"]) == 1
    assert data["peers"][0]["uri"] == peer_uri

def test_federation_status(test_setup):
    """Test retrieving federation health and metrics status."""
    client, fed_manager = test_setup
    
    response = client.get("/api/v1/federation/status")
    assert response.status_code == 200
    data = response.json()
    assert "connected_count" in data
    assert "active_syncs_count" in data
    assert "health" in data
