# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2024-11-27

### Added
- Root endpoint (/) with API information
- Improved datetime handling in database operations

### Fixed
- Datetime serialization in database operations
- Health check status reporting

### Technical Details
- Using proper datetime serialization in models
- Improved error handling for database operations
- Health check now properly uses SQLAlchemy text()

## [0.1.0] - 2024-11-26

### Added
- Basic CRUD operations for Things
- Basic CRUD operations for Repair Stories
- Basic CRUD operations for Relationships
- Multi-language support in content
- Health check endpoint
- API documentation with Swagger/OpenAPI
- PostgreSQL database with JSONB storage
- Docker Compose development setup
- Basic logging system
- Favicon handling

### Technical Details
- FastAPI framework for API implementation
- SQLAlchemy with PostgreSQL for database
- Pydantic for data validation
- Docker and Docker Compose for containerization
- Integrated logging system
- Health monitoring basics

### API Endpoints
- GET /health - System health check
- POST /api/v1/things - Create a new thing
- GET /api/v1/things - List things
- GET /api/v1/things/{id} - Get specific thing
- POST /api/v1/stories - Create a repair story
- GET /api/v1/stories/{id} - Get specific story
- GET /api/v1/things/{id}/stories - Get stories for a thing
- GET /api/v1/things/{id}/relationships - Get relationships for a thing

### Known Issues
- No authentication/authorization system yet
- Limited error handling
- No data pagination
- No search functionality

### Removed
- Alembic migrations in favor of direct schema creation
- MinIO and file storage functionality (planned for future releases)
- Federation capabilities (planned for future releases)
