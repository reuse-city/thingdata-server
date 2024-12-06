# ThingData API Documentation

## Core Endpoints

### Root Endpoint
```http
GET /

Returns HTML page with API information and available endpoints.
```

### Health Check
```http
GET /health

Returns:
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "2024-12-01T00:00:00Z",
  "version": "0.1.3",
  "components": {
    "database": "healthy|degraded|unhealthy",
    "api": "healthy|degraded|unhealthy"
  },
  "metrics": {
    "memory_usage": 45.2,
    "cpu_usage": 12.5,
    "active_connections": 0,
    "storage_usage": 32.1,
    "federation_peers": 0
  }
}
```

## Entity Management

### Things
```http
GET /api/v1/things
POST /api/v1/things
GET /api/v1/things/{id}

Query Parameters:
- skip: int (default: 0)
- limit: int (default: 100)
- type: string (optional)
```

### Stories
```http
GET /api/v1/stories
POST /api/v1/stories
GET /api/v1/stories/{id}

Query Parameters:
- skip: int (default: 0)
- limit: int (default: 100)
- thing_id: string (optional)
- category: string (optional)
```

### Guides
```http
GET /api/v1/guides
POST /api/v1/guides
GET /api/v1/guides/{id}

Query Parameters:
- skip: int (default: 0)
- limit: int (default: 100)
- thing_id: string (optional)
- category: string (optional)
- type: string (optional)
```

### Relationships
```http
GET /api/v1/relationships
POST /api/v1/relationships
GET /api/v1/relationships/{id}

Query Parameters:
- skip: int (default: 0)
- limit: int (default: 100)
- source_type: 'thing'|'guide'|'story'
- source_id: string
- target_type: 'thing'|'guide'|'story'
- target_id: string
- relationship_type: string
```

## Data Models

### Thing Creation
```json
{
  "type": "string",
  "name": {
    "default": "string",
    "translations": {
      "lang_code": "string"
    }
  },
  "manufacturer": {
    "name": "string",
    "website": "string?",
    "contact": "email?"
  },
  "properties": {
    "dimensions": {
      "length": "float?",
      "width": "float?",
      "height": "float?"
    },
    "materials": ["string"],
    "manufacturing_date": "string?",
    "serial_number": "string?"
  }
}
```

### Story Creation
```json
{
  "thing_id": "string?",
  "thing_category": {
    "category": "string",
    "subcategory": "string?",
    "attributes": {
      "key": "value"
    }
  }?,
  "type": "string",
  "procedure": [
    {
      "order": "integer",
      "description": {
        "default": "string",
        "translations": {
          "lang_code": "string"
        }
      },
      "warnings": ["string"],
      "tools": ["string"],
      "media": ["string"]
    }
  ]
}
```

### Guide Creation
```json
{
  "thing_id": "string?",
  "thing_category": {
    "category": "string",
    "subcategory": "string?",
    "attributes": {
      "key": "value"
    }
  }?,
  "type": {
    "primary": "string",
    "secondary": "string?"
  },
  "content": {
    "title": {
      "default": "string",
      "translations": {
        "lang_code": "string"
      }
    },
    "summary": {
      "default": "string",
      "translations": {
        "lang_code": "string"
      }
    }?,
    "requirements": {
      "skills": ["string"],
      "tools": ["string"],
      "materials": ["string"],
      "certifications": ["string"]
    }?,
    "warnings": [
      {
        "severity": "string",
        "message": {
          "default": "string"
        }
      }
    ]?
  }
}
```

### Relationship Creation
```json
{
  "source_type": "'thing'|'guide'|'story'",
  "source_id": "string",
  "target_type": "'thing'|'guide'|'story'",
  "target_id": "string",
  "relationship_type": "string",
  "direction": "'unidirectional'|'bidirectional'",
  "metadata": {
    "key": "value"
  }?
}
```

## Security Constraints

### Request Limits
- Maximum request size: 10MB
- Content type: `application/json` required for all POST/PUT/PATCH requests
- Maximum JSON nesting depth: 20 levels

### Allowed Types
#### Things
- Allowed types: `device`, `component`, `material`, `tool`

#### Stories
- Allowed types: `repair`, `maintenance`, `modification`, `diagnosis`

#### Guides
- Primary types: `manual`, `tutorial`, `specification`, `documentation`
- Secondary types: `repair`, `maintenance`

### Relationships
- Direction must be either `unidirectional` or `bidirectional`
- Source and target types must be valid entity types (`thing`, `guide`, `story`)

### Examples with Security Requirements

```bash
# Create a thing (with valid type)
curl -X POST http://localhost:8000/api/v1/things \
-H "Content-Type: application/json" \
-d '{
  "type": "device",  # Must be one of: device, component, material, tool
  "name": {"default": "Example Device"},
  "manufacturer": {"name": "Example Corp"}
}'

# Create a guide (with valid primary/secondary types)
curl -X POST http://localhost:8000/api/v1/guides \
-H "Content-Type: application/json" \
-d '{
  "type": {
    "primary": "manual",     # Must be one of: manual, tutorial, specification, documentation
    "secondary": "repair"    # Must be one of: repair, maintenance
  },
  "content": {
    "title": {"default": "Example Guide"}
  }
}'
```

### Error Responses
The API will return appropriate error status codes and messages for security violations:
- `413 Request Entity Too Large` - Request exceeds 10MB
- `400 Bad Request` - Invalid content type or invalid entity type
- `400 Bad Request` - JSON structure too deep

## Working Examples

See [advanced-operations.md](../advanced-operations.md) for detailed examples and workflows.
