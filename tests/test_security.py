import os
os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient
import uuid
from datetime import datetime, timedelta
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from sqlalchemy.orm import Session

from app.main import app, get_db
from app.database import Base, engine, SessionLocal, init_db
from app.models import User, Instance, Thing
from app.security import get_password_hash, rate_limit, limiters

@pytest.fixture(scope="function")
def test_setup():
    """Create test setup containing client and database cleanup."""
    init_db()
    
    # Reset rate limiters state
    for limiter in limiters.values():
        limiter.history.clear()
    
    # Disable get_federation dependency mock override if any
    app.dependency_overrides.clear()
    
    with TestClient(app) as client:
        yield client
        
    Base.metadata.drop_all(bind=engine)

def test_first_user_register_success(test_setup):
    """Test that the first user can register without authentication (bootstrapping)."""
    client = test_setup
    payload = {
        "username": "admin1",
        "password": "secretpassword",
        "role": "admin"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin1"
    assert data["role"] == "admin"
    assert "id" in data

def test_second_user_register_requires_auth(test_setup):
    """Test that registering subsequent users requires an existing authenticated admin."""
    client = test_setup
    
    # Register first user (bootstrap)
    first_payload = {
        "username": "first_admin",
        "password": "firstpassword"
    }
    response = client.post("/api/v1/auth/register", json=first_payload)
    assert response.status_code == 200
    
    # Try to register second user without auth headers
    second_payload = {
        "username": "second_admin",
        "password": "secondpassword"
    }
    response = client.post("/api/v1/auth/register", json=second_payload)
    assert response.status_code == 401
    assert "Authentication required" in response.json()["detail"]
    
    # Login as first user to get token
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "first_admin", "password": "firstpassword"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Register second user using first user's token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/auth/register", json=second_payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == "second_admin"

def test_login_and_me_endpoints(test_setup):
    """Test user login for token and profile retrieval endpoints."""
    client = test_setup
    
    # Create user
    payload = {
        "username": "test_user",
        "password": "my_password"
    }
    client.post("/api/v1/auth/register", json=payload)
    
    # Login with wrong credentials
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "test_user", "password": "wrong_password"}
    )
    assert response.status_code == 401
    
    # Login with correct credentials
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "test_user", "password": "my_password"}
    )
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    
    # Request profile
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    profile_response = client.get("/api/v1/auth/me", headers=headers)
    assert profile_response.status_code == 200
    assert profile_response.json()["username"] == "test_user"

def test_local_mutations_secured(test_setup):
    """Test that mutation (write/delete) endpoints are blocked without a valid token."""
    client = test_setup
    
    # Try to create a thing without authentication
    thing_payload = {
        "data": {
            "type": "device",
            "name": {"default": "Toaster"},
            "manufacturer": {"name": "ToastMaster"}
        }
    }
    response = client.post("/api/v1/things", json=thing_payload)
    assert response.status_code == 401
    
    # Register and login to get token
    payload = {"username": "admin", "password": "password123"}
    client.post("/api/v1/auth/register", json=payload)
    login_resp = client.post("/api/v1/auth/token", data=payload)
    token = login_resp.json()["access_token"]
    
    # Try creating with valid token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/things", json=thing_payload, headers=headers)
    assert response.status_code == 200
    thing_id = response.json()["id"]
    
    # Try deleting it without token
    delete_resp = client.delete(f"/api/v1/things/{thing_id}", headers={"X-Confirm-Delete": "True"})
    assert delete_resp.status_code == 401
    
    # Try deleting it with token
    delete_resp = client.delete(
        f"/api/v1/things/{thing_id}",
        headers={"X-Confirm-Delete": "True", "Authorization": f"Bearer {token}"}
    )
    assert delete_resp.status_code == 204

def test_federation_signature_verification(test_setup):
    """Test federation request signature verification logic."""
    client = test_setup
    
    # Generate RSA keypair for mock peer
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    
    pem_public_key = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode("utf-8")
    
    pem_private_key = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ).decode("utf-8")
    
    # Insert peer Instance into the test database
    db = SessionLocal()
    peer_uri = "https://repairhub-berlin.example.com"
    peer = Instance(
        id=str(uuid.uuid4()),
        uri=peer_uri,
        name="RepairHub Berlin",
        type="peer",
        endpoints={"api": f"{peer_uri}/api/v1"},
        capabilities=["sync"],
        languages=["en"],
        trust_status="verified",
        public_key=pem_public_key,
        sync_status={}
    )
    db.add(peer)
    db.commit()
    db.close()
    
    # Create valid JWT signed with peer's private key
    import time
    now_ts = time.time()
    payload = {
        "iss": peer_uri,
        "sub": "http://localhost:8000",  # Local instance URI
        "iat": now_ts,
        "exp": now_ts + 300
    }
    token = jwt.encode(payload, pem_private_key, algorithm="RS256")
    
    # Test sync request with valid signature
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Federation-Instance": peer_uri
    }
    response = client.post("/api/v1/federation/sync", json={}, headers=headers)
    assert response.status_code == 200
    
    # Test sync request with invalid signature
    bad_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    bad_pem_private_key = bad_private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ).decode("utf-8")
    
    bad_token = jwt.encode(payload, bad_pem_private_key, algorithm="RS256")
    bad_headers = {
        "Authorization": f"Bearer {bad_token}",
        "X-Federation-Instance": peer_uri
    }
    response = client.post("/api/v1/federation/sync", json={}, headers=bad_headers)
    assert response.status_code == 401
    assert "Invalid token signature" in response.json()["error"]

def test_rate_limiter(test_setup):
    """Test in-memory rate limiting triggers 429 after limit is reached."""
    client = test_setup
    
    # Limit is 5 requests per 60 seconds
    for i in range(5):
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "user", "password": "pwd"}
        )
        # We expect 401 Unauthorized for these since user doesn't exist, but NOT 429
        assert response.status_code == 401
        
    # The 6th request should hit the rate limiter and return 429
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "user", "password": "pwd"}
    )
    assert response.status_code == 429
    assert "Too many requests" in response.json()["error"]
