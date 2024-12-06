from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from app.schemas import EntityType, RelationshipDirection, GuideType
import re
from typing import Optional, Dict, Any

class SecurityConfig:
    MAX_REQUEST_SIZE: int = 10_000_000  # 10MB
    MAX_CONTENT_TYPE_LENGTH: int = 256
    MAX_JSON_DEPTH: int = 20
    # Use the allowed types from your domain model
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
        if int(content_length) > SecurityConfig.MAX_REQUEST_SIZE:
            raise SecurityException(413, "Request too large")

    async def _validate_content_type(self, request: Request):
        content_type = request.headers.get("content-type", "")
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
        # EntityType validation is handled by Pydantic
        try:
            EntityType(data.get("source_type"))
            EntityType(data.get("target_type"))
            RelationshipDirection(data.get("direction", "unidirectional"))
        except ValueError as e:
            raise SecurityException(400, str(e))

def configure_security(app: FastAPI) -> None:
    """Configure security middleware and any other security settings."""
    app.add_middleware(SecurityMiddleware)
