# ThingData Server

ThingData is a data-powered solution to promote a longer lifetime for goods and materials. This repository contains the reference implementation of the ThingData Protocol server.

**Attention:** good part of the code and documentation in this repository were created with the assistance of chatbots and large language models. If something looks weird, let us know.

## Features

### Currently Implemented (v0.1.2)
- Persistent data storage
- Environment-based configuration
- Database backup capabilities
- Improved logging system
- Sample data generation
- Test infrastructure

### Currently Implemented (v0.1.1)
- Basic CRUD operations for Things (products, objects, materials)
- Basic CRUD operations for Repair Stories
- Basic CRUD operations for Relationships between Things
- Multi-language support in content
- Health check endpoint
- API-first design and documentation with OpenAPI/Swagger

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

```markdown
### Sample Data
To populate the server with sample data for testing and development:

```bash
# From project root
./scripts/init_sample_data.sh
```

This will create sample things (a laptop and its components), relationships between them, and repair stories. Perfect for exploring the API capabilities.
```

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

## Next Steps Recommended

1. Implement automatic backups:
   - Set up cron jobs for regular backups
   - Implement backup rotation
   - Add backup verification

2. Add monitoring:
   - Track storage usage
   - Monitor database performance
   - Set up alerts for storage issues

3. Implement data migration tools:
   - Create database schema migrations
   - Add data export/import tools
   - Implement version tracking

4. Enhance backup strategy:
   - Add compression
   - Implement point-in-time recovery
   - Add remote backup storage

## Migration Path

1. For existing installations:
```bash
# Stop services
docker-compose down

# Backup current data
docker exec -t thingdata-db pg_dumpall -c -U thingdata > dump.sql

# Remove old volumes
docker volume rm thingdata_postgres_data

# Start with new configuration
docker-compose up -d

# Restore data if needed
cat dump.sql | docker exec -i thingdata-db psql -U thingdata
```

2. For new installations:
```bash
# Clone repository
git clone https://github.com/reuse-city/thingdata-server.git

# Configure environment
cp .env.example .env

# Start services
docker-compose up -d
```

## API Documentation

See our [API Documentation](docs/api/README.md) for:
- Currently implemented endpoints
- Data models
- Usage examples
- Error handling

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
