# ThingData Server API Documentation

> Note: This documentation covers currently implemented features only. For planned features and future development, see our [Roadmap](../../ROADMAP.md) and [Implementation Status](../../IMPLEMENTATION_STATUS.md).

## Core Concepts

### Things
A "Thing" represents any physical object that can be repaired, maintained, or modified. Currently implemented features:

- Unique identifier and URI
- Type classification
- Multilingual name and descriptions
- Manufacturer information
- Basic physical properties (dimensions, materials)

### Stories
Stories document repair, maintenance, or modification procedures. Currently implemented features:

- Basic step-by-step procedures
- Tool requirements
- Safety warnings
- Multi-language support for descriptions

### Relationships
Basic relationships between things are supported, including:

- Component relationships (part-of)
- Basic compatibility information

## Working API Endpoints

### Thing Management

#### Create Thing
```http
POST /api/v1/things

{
  "type": "appliance",
  "name": {
    "default": "Coffee Machine",
    "translations": {
      "es": "Máquina de Café",
      "de": "Kaffeemaschine"
    }
  },
  "manufacturer": {
    "name": "BaristaPlus",
    "website": "https://example.com",
    "contact": "support@example.com"
  },
  "properties": {
    "dimensions": {
      "length": 30.0,
      "width": 20.0,
      "height": 40.0
    },
    "materials": ["steel", "plastic", "glass"],
    "serial_number": "BPC123456"
  }
}
```

#### Get Thing
```http
GET /api/v1/things/{thing_id}
```

#### List Things
```http
GET /api/v1/things?type=appliance&skip=0&limit=100
```

### Story Management

#### Create Story
```http
POST /api/v1/stories

{
  "thing_id": "uuid",
  "type": "repair",
  "procedure": [
    {
      "order": 1,
      "description": {
        "default": "Remove the top cover",
        "translations": {
          "es": "Quite la cubierta superior"
        }
      },
      "warnings": ["Disconnect power first"],
      "tools": ["Phillips screwdriver"]
    }
  ]
}
```

#### Get Story
```http
GET /api/v1/stories/{story_id}
```

#### Get Thing Stories
```http
GET /api/v1/things/{thing_id}/stories
```

### Basic Health Check
```http
GET /health
```

## Working Example

Here's a complete working example of creating a thing and its repair story:

```bash
# 1. Create a thing
curl -X POST http://localhost:8000/api/v1/things \
-H "Content-Type: application/json" \
-d '{
  "type": "appliance",
  "name": {
    "default": "Coffee Machine XK-42",
    "translations": {
      "es": "Máquina de Café XK-42"
    }
  },
  "manufacturer": {
    "name": "BaristaPlus"
  },
  "properties": {
    "dimensions": {
      "length": 30.0,
      "width": 20.0,
      "height": 40.0
    },
    "materials": ["steel", "plastic"]
  }
}'

# Save the returned ID
THING_ID="returned_id_here"

# 2. Create a repair story
curl -X POST http://localhost:8000/api/v1/stories \
-H "Content-Type: application/json" \
-d '{
  "thing_id": "'$THING_ID'",
  "type": "repair",
  "procedure": [
    {
      "order": 1,
      "description": {
        "default": "Remove the top cover",
        "translations": {
          "es": "Quite la cubierta superior"
        }
      },
      "warnings": ["Disconnect power first"],
      "tools": ["Phillips screwdriver"]
    }
  ]
}'
```

## Error Handling

The API currently implements standard HTTP status codes:
- 200: Success
- 400: Bad Request (invalid input)
- 404: Not Found
- 500: Server Error

Error responses include basic detail messages:
```json
{
  "detail": "Error description"
}
```

## Related Documentation
- See [Implementation Status](../../IMPLEMENTATION_STATUS.md) for current feature status
- See [Roadmap](../../ROADMAP.md) for planned features
- See the [Contributing Guide](../../CONTRIBUTING.md) for development setup

## Known Limitations
- Media file handling is not yet implemented
- Advanced search features are not available
- Federation features are not yet implemented
- Conflict resolution is not yet implemented
