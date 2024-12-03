# ThingData Server

ThingData is a data-powered solution to promote a longer lifetime for goods and materials. This repository contains the reference implementation of the ThingData Protocol server.

**Attention:** good part of the code and documentation in this repository were created with the assistance of chatbots and large language models. If something looks weird, let us know.

## Features

### Currently Implemented (v0.1.3)
- Guide entity with CRUD operations
- Category-based repair documentation
- Flexible relationship system between all entities
- Bidirectional relationships
- Enhanced relationship metadata support
- Cross-entity relationship querying
- Support for stories and guides without specific things
- Category-based knowledge organization

### Breaking Changes in v0.1.3
- New relationship model requires different API calls
- Stories and guides can now exist without specific things
- Relationship queries have changed significantly
- See [CHANGELOG.md](CHANGELOG.md) for detailed migration notes

### Core Features (v0.1.2)
- Persistent data storage
- Environment-based configuration
- Database backup capabilities
- Improved logging system
- Sample data generation
- Test infrastructure
- Basic CRUD operations for Things
- Basic CRUD operations for Stories
- Multi-language support in content
- Health check endpoint
- API-first design with OpenAPI/Swagger

### Planned Features
See our [Roadmap](ROADMAP.md) for details on:
- Federation capabilities
- Advanced search
- File storage
- Advanced relationship mapping
- Impact tracking

## Getting Started



### Prerequisites
- Docker
- Docker Compose
- Git

### Installation
1. Clone the repository:
```bash
git clone git@github.com:reuse-city/thingdata-server.git
cd thingdata-server
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Start the server:
```bash
docker-compose up --build
```

The server will be available at:
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Alternative documentation: http://localhost:8000/redoc

4. Verify installation:
```bash
curl http://localhost:8000/health
```

5. Add sample data:
```bash
# From project root
./scripts/init_sample_data.sh
```

This will create sample data including:
- A laptop and its components
- A general laptop repair guide
- Category-based repair stories
- Various relationships between entities

6. Testing

6.1. Install test dependencies:
```bash
pip install -r requirements.txt
```

6.2. Run tests:
```bash
pytest
```

For test coverage report:
```bash
pytest --cov=app tests/
```

## API Overview

### Core Endpoints
- `GET /` - HTML documentation
- `GET /health` - System health check
- `/docs` - OpenAPI documentation (Swagger UI)
- `/redoc` - Alternative API documentation

### Entity Management
- `/api/v1/things` - Thing operations
- `/api/v1/stories` - Story operations
- `/api/v1/guides` - Guide operations
- `/api/v1/relationships` - Relationship operations

### Quick Example: Creating Related Entities
```bash
# Create a thing
curl -X POST http://localhost:8000/api/v1/things \
-H "Content-Type: application/json" \
-d '{
  "type": "device",
  "name": {"default": "Example Device"},
  "manufacturer": {"name": "Example Corp"}
}'

# Create a guide
curl -X POST http://localhost:8000/api/v1/guides \
-H "Content-Type: application/json" \
-d '{
  "thing_category": {
    "category": "device",
    "subcategory": "electronic"
  },
  "type": {
    "primary": "repair",
    "secondary": "maintenance"
  },
  "content": {
    "title": {"default": "General Maintenance Guide"}
  }
}'

# Create a relationship between them
curl -X POST http://localhost:8000/api/v1/relationships \
-H "Content-Type: application/json" \
-d '{
  "source_type": "guide",
  "source_id": "guide_id",
  "target_type": "thing",
  "target_id": "thing_id",
  "relationship_type": "applies_to",
  "direction": "unidirectional"
}'
```

### Category-based Documentation
Support for stories and guides that apply to categories of things rather than specific items. See [API Documentation](docs/api/README.md) for detailed examples.

### Relationships
Flexible relationship system supporting all entity types:
- Thing-to-Thing relationships
- Guide-to-Thing relationships
- Story-to-Thing relationships
- Guide-to-Story relationships
- Guide-to-Guide relationships
- Story-to-Story relationships

## Documentation

See our detailed documentation for:
- [API Documentation](docs/api/README.md)
- [Advanced Operations](docs/advanced-operations.md)
- [Implementation Status](IMPLEMENTATION_STATUS.md)
- [Development Workflows](docs/workflows.md)

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See our [Contributing Guide](CONTRIBUTING.md) for detailed instructions.

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). This license requires that modifications to this software must also be made available under the AGPL-3.0, both when distributed and when run over a network. For more details, see the [LICENSE](LICENSE) file in the repository.

The choice of the AGPL-3.0 license reflects our commitment to keeping knowledge about repair and reuse open and accessible to all, ensuring that improvements to this platform benefit the entire community.

## Acknowledgments

ThingData is a spin-off of PhD research at Northumbria University / Mozilla Foundation investigating social and conceptual aspects of waste prevention through community-based practices of material reuse.
