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

## Working Examples

See [advanced-operations.md](../advanced-operations.md) for detailed examples and workflows.
