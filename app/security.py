from fastapi import FastAPI, Request, HTTPException, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
import time
from typing import Optional, Dict, Any, List

from app.schemas import EntityType, RelationshipDirection
from app.database import get_db
from app.models import User, Instance
from app.config import get_settings

# Initialize password hashing context
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# OAuth2 Password Bearer scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token", auto_error=False)

class SecurityConfig:
    MAX_REQUEST_SIZE: int = 10_000_000  # 10MB
    MAX_CONTENT_TYPE_LENGTH: int = 256
    MAX_JSON_DEPTH: int = 20
    ALLOWED_THING_TYPES = ["device", "component", "material", "tool"]
    ALLOWED_STORY_TYPES = ["repair", "maintenance", "modification", "diagnosis"]
    ALLOWED_GUIDE_PRIMARY_TYPES = ["manual", "tutorial", "specification", "documentation"]
    ALLOWED_GUIDE_SECONDARY_TYPES = ["repair", "maintenance"]

class SecurityException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            if request.method in ("POST", "PUT", "PATCH"):
                await self._validate_request_size(request)
                await self._validate_content_type(request)
            return await call_next(request)
        except SecurityException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"error": e.detail}
            )

    async def _validate_request_size(self, request: Request):
        content_length = request.headers.get("content-length", 0)
        try:
            if int(content_length) > SecurityConfig.MAX_REQUEST_SIZE:
                raise SecurityException(413, "Request too large")
        except ValueError:
            pass

    async def _validate_content_type(self, request: Request):
        content_type = request.headers.get("content-type", "")
        if request.url.path == "/api/v1/auth/token" and content_type.startswith("application/x-www-form-urlencoded"):
            return
        if not content_type.startswith("application/json"):
            raise SecurityException(400, "Only application/json content type is allowed")

class SecurityValidator:
    @staticmethod
    def validate_json_depth(data: Dict[str, Any], current_depth: int = 0) -> None:
        if current_depth > SecurityConfig.MAX_JSON_DEPTH:
            raise SecurityException(400, "JSON structure too deep")
        
        if isinstance(data, dict):
            for value in data.values():
                SecurityValidator.validate_json_depth(value, current_depth + 1)
        elif isinstance(data, list):
            for item in data:
                SecurityValidator.validate_json_depth(item, current_depth + 1)

    @staticmethod
    def validate_thing_data(data: Dict[str, Any]) -> None:
        if data.get("type") not in SecurityConfig.ALLOWED_THING_TYPES:
            raise SecurityException(
                400, 
                f"Invalid thing type. Allowed types: {SecurityConfig.ALLOWED_THING_TYPES}"
            )

    @staticmethod
    def validate_story_data(data: Dict[str, Any]) -> None:
        if data.get("type") not in SecurityConfig.ALLOWED_STORY_TYPES:
            raise SecurityException(
                400, 
                f"Invalid story type. Allowed types: {SecurityConfig.ALLOWED_STORY_TYPES}"
            )

    @staticmethod
    def validate_guide_data(data: Dict[str, Any]) -> None:
        if "type" in data:
            guide_type = data["type"]
            if isinstance(guide_type, dict):
                if guide_type.get("primary") not in SecurityConfig.ALLOWED_GUIDE_PRIMARY_TYPES:
                    raise SecurityException(
                        400,
                        f"Invalid guide primary type. Allowed types: {SecurityConfig.ALLOWED_GUIDE_PRIMARY_TYPES}"
                    )
                if guide_type.get("secondary") and guide_type.get("secondary") not in SecurityConfig.ALLOWED_GUIDE_SECONDARY_TYPES:
                    raise SecurityException(
                        400,
                        f"Invalid guide secondary type. Allowed types: {SecurityConfig.ALLOWED_GUIDE_SECONDARY_TYPES}"
                    )

    @staticmethod
    def validate_relationship_data(data: Dict[str, Any]) -> None:
        try:
            EntityType(data.get("source_type"))
            EntityType(data.get("target_type"))
            RelationshipDirection(data.get("direction", "unidirectional"))
        except ValueError as e:
            raise SecurityException(400, str(e))

# --- Cryptography & Password Hashing Helpers ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# --- JWT Utility Functions ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    settings = get_settings()
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str) -> Optional[dict]:
    try:
        settings = get_settings()
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except Exception:
        return None

# --- OAuth2 Current User Dependency ---

async def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = SecurityException(
        status_code=401,
        detail="Could not validate credentials"
    )
    if not token:
        raise credentials_exception
    payload = verify_access_token(token)
    if payload is None:
        raise credentials_exception
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# --- Federation Signature Verification Dependency ---

async def verify_federation_request(
    request: Request,
    db: Session = Depends(get_db)
) -> str:
    """Verify incoming federation requests from peers."""
    auth_header = request.headers.get("Authorization")
    peer_uri_header = request.headers.get("X-Federation-Instance")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise SecurityException(401, "Missing or invalid Authorization header")
    if not peer_uri_header:
        raise SecurityException(401, "Missing X-Federation-Instance header")
        
    token = auth_header.split(" ")[1]
    
    # Look up peer instance
    peer = db.query(Instance).filter(Instance.uri == peer_uri_header).first()
    if not peer:
        raise SecurityException(401, f"Unknown federation peer: {peer_uri_header}")
        
    # Verify signature of the token using the peer's public key
    try:
        settings = get_settings()
        payload = jwt.decode(
            token,
            peer.public_key,
            algorithms=["RS256"]
        )
        
        # Verify issuer and subject
        if payload.get("iss") != peer.uri:
            raise SecurityException(401, "Token issuer does not match peer URI")
        if payload.get("sub") != settings.INSTANCE_URI:
            raise SecurityException(401, "Token subject is not this instance")
            
        return peer.uri
    except Exception as e:
        raise SecurityException(401, f"Invalid token signature or payload: {str(e)}")

# --- In-Memory Rate Limiter ---

class SimpleRateLimiter:
    def __init__(self, requests_limit: int = 100, window_seconds: int = 60):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.history: Dict[str, List[float]] = {}

    def is_rate_limited(self, client_id: str) -> bool:
        now = time.time()
        if client_id not in self.history:
            self.history[client_id] = []
        
        # Clean up old timestamps
        self.history[client_id] = [t for t in self.history[client_id] if now - t < self.window_seconds]
        
        if len(self.history[client_id]) >= self.requests_limit:
            return True
            
        self.history[client_id].append(now)
        return False

# Global rate limiters cache
limiters: Dict[str, SimpleRateLimiter] = {}

def rate_limit(requests_limit: int = 100, window_seconds: int = 60):
    key = f"{requests_limit}_{window_seconds}"
    if key not in limiters:
        limiters[key] = SimpleRateLimiter(requests_limit, window_seconds)
    limiter = limiters[key]
    
    def dependency(request: Request):
        # Identify client by IP
        client_ip = request.client.host if request.client else "unknown"
        if limiter.is_rate_limited(client_ip):
            raise SecurityException(429, "Too many requests. Please try again later.")
    return dependency

def configure_security(app: FastAPI) -> None:
    """Configure security middleware."""
    app.add_middleware(SecurityMiddleware)

    @app.exception_handler(SecurityException)
    async def security_exception_handler(request: Request, exc: SecurityException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail}
        )
