# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - 2024-12-01

### Added
- New Guide entity with CRUD operations
- Support for category-based stories and guides
- Flexible relationship system between all entities (things, stories, guides)
- Bidirectional relationships support
- Enhanced relationship metadata
- Cross-entity relationship querying capabilities
- Updated API documentation with new endpoints

### Changed
- Modified relationship model to support multiple entity types
- Made thing_id optional in stories for category-based documentation
- Updated database schema for new relationship model
- Enhanced API response format to include relationships
- Improved relationship querying capabilities

### Breaking Changes
- Relationship API endpoints structure has changed completely
  - Old: `/api/v1/relationships` expected thing_id and target_uri
  - New: `/api/v1/relationships` expects source_type, source_id, target_type, target_id
- Relationship model now requires direction field ('unidirectional' or 'bidirectional')
- thing_id in stories and guides is now optional
- GET /api/v1/things/{id}/relationships endpoint removed in favor of relationship field in response

### Migration Notes
- Existing relationships need to be updated to include source_type='thing' and target_type='thing'
- Custom scripts using the relationship endpoints need to be updated
- Applications should be updated to handle optional thing_id in stories/guides
- Update any code that relied on /things/{id}/relationships to use new relationship queries

### Fixed
- Fixed relationship query handling
- Improved error handling for relationship operations
- Fixed relationship metadata handling
- Corrected issues with entity relationship retrieval

## [0.1.2] - 2024-11-30

### Added
- Centralized version management
- Version update script
- Version environment variable
- Testing configuration with pytest
- Test coverage reporting
- Testing documentation
- Sample data initialization script in scripts/ directory
- Environment configuration example file (.env.example)
- Persistent database storage using named volumes
- Centralized configuration management with config.py
- Database initialization scripts
- Environment-based configuration
- Backup script for database
- Logs persistence

### Changed
- Improved logging configuration
- Version number now sourced from single location
- Simplified test infrastructure
- Updated tests to match current implementation
- Removed async test configuration
- Moved from development to production environment settings
- Updated database connection pooling settings and persistence configuration
- Updated development documentation
- Improved logging configuration
- Simplified Docker configuration
- Consolidated environment configuration

### Removed
- conftest.py (replaced with simplified test setup)
- Async database test configuration
- Obsolete development and test Docker compose files
- Unused development tools
- Legacy storage implementation
- Development-specific configuration files
- Redundant initialization files

### Fixed
- Logger initialization issues
- Database connection handling in health checks
- Version consistency across components
- Python path configuration for tests
- Data persistence across container rebuilds
- Database connection management
- Environment configuration handling
- Logging persistence

## [0.1.1] - 2024-11-27

### Added
- Root endpoint (/) with API information and links
- Working Story creation with proper procedure handling
- Working Relationship creation between Things
- Improved datetime handling in database operations

### Fixed
- Datetime serialization in database operations
- Story creation procedure handling
- JSON data handling in relationships
- Health check status reporting

### Technical Details
- Using model_dump() for Pydantic models
- Proper JSONB handling in PostgreSQL
- Improved error handling and logging
- Health check using proper SQLAlchemy text()
- Using proper datetime serialization in models

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
