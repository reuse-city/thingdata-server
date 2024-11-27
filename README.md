# ThingData Server

ThingData is a data-powered solution to promote a longer lifetime for goods and materials. This repository contains the reference implementation of the ThingData Protocol server.

## Features

### Currently Implemented (v0.1.0)
- Basic CRUD operations for Things (products, objects, materials)
- Basic CRUD operations for Repair Stories
- Basic CRUD operations for Relationships between Things
- Multi-language support in content
- Health check endpoint
- API-first design with OpenAPI/Swagger documentation

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

2. Start the server:
```bash
docker-compose up --build
```

The server will be available at:
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Alternative documentation: http://localhost:8000/redoc

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
