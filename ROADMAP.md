# ThingData Development Roadmap

> For current implementation status, see [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)

## Current Phase - Core Functionality Enhancement 🚧

### Completed (v0.1.4) ✅
- Security validation system
- Request size limits
- Entity type validation
- Content type enforcement
- Input validation improvements

### Completed (v0.1.3) ✅
- Guide entity implementation
- Category-based documentation
- Flexible relationship system
- Cross-entity relationships
- Bidirectional relationships
- Enhanced metadata support

### In Progress
- Authentication system
- Authorization framework
- Rate limiting
- Audit logging
- Search functionality
  - Basic text search
  - Category-based search
  - Relationship-based search
  - Multilingual support
- Data validation
  - Conflict detection
  - Version control
  - Format validation
  - Schema compliance
- Batch operations
  - Multi-entity creation
  - Bulk updates
  - Mass relationship management

### Next Steps
- Core CRUD Completion
  - Implement entity update endpoints (`PUT` for things, stories, guides, and relationships)
  - Align models/schemas with protocol (nest under `"data"` object or resolve nesting standard; implement missing fields for `Thing.sustainability`, `Story.author`, `Story.prerequisites`, and `Guide.source`)
- Advanced filtering system
  - Category filtering
  - Relationship filtering
  - Metadata queries
  - Combined filters
- API optimizations
  - Response pagination
  - Query optimization
  - Error handling improvements

## Planned Features

### Phase 2: Search & Discovery
- Full-text search across all entities (PostgreSQL FTS)
- Advanced filtering capabilities
- Multi-language search support
- Category-based discovery
- Related content suggestions
- Tag-based organization

### Phase 3: Content Management
- Media handling & file attachments
- Version control & content moderation
- External content archive integration
  - Implement `GET /api/v1/guides/{id}/external-content`
  - Implement `GET /api/v1/guides/{id}/archive`
- Batch operations & import/export capabilities

### Phase 4: Federation System
> Design documents available in docs/design/
- Mount federation router in `app/main.py`
- Expose discovery endpoints (`GET /.well-known/webfinger` & `GET /api/v1/federation/discover`)
- Expose interaction routes (`POST /api/v1/federation/connect` & `POST /api/v1/federation/announce`)
- Expose synchronization endpoints (`POST /api/v1/federation/sync` & `GET /api/v1/federation/status`)
- Instance discovery, trust system, and conflict resolution

### Phase 5: Impact & Analytics
- Environmental metrics
- Social impact measures
- Resource conservation tracking
- Community engagement metrics
- Success rate tracking
- Usage analytics

### Phase 6: Scale & Performance
- Load balancing
- Caching system
- Connection pooling
- Query optimization
- Resource management
- Monitoring system

## Contributing
See our [Contributing Guide](CONTRIBUTING.md) for information on how to help with these developments.

## Documentation
- [API Documentation](docs/api/README.md)
- [Implementation Status](IMPLEMENTATION_STATUS.md)
- [Development Guide](docs/workflows.md)
- [Design Documents](docs/design/) - Future feature designs
