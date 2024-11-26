# ThingData Server API Documentation

## Core Concepts

### Things
A "Thing" represents any physical object that can be repaired, maintained, or modified. Things can be appliances, electronics, furniture, tools, or any other physical items. Each thing has:

- Unique identifier and URI
- Type classification
- Multilingual name and descriptions
- Manufacturer information
- Physical properties (dimensions, materials, etc.)
- Relationships with other things
- Associated repair stories

### Stories
Stories document repair, maintenance, or modification procedures for things. They capture:

- Step-by-step procedures
- Tools and parts required
- Safety warnings
- Supporting media (images, diagrams)
- Versions and history
- Multiple language support

### Relationships
Relationships define connections between things, such as:

- Component relationships (part-of)
- Tool requirements (requires-tool)
- Compatibility (works-with)
- Consumable relationships (uses-consumable)
- Alternative parts (can-replace)

## API Endpoints

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
      "tools": ["Phillips screwdriver"],
      "media": ["image1.jpg"]
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

### Relationship Management

#### Create Relationship
```http
POST /api/v1/relationships

{
  "thing_id": "uuid",
  "relationship_type": "component",
  "target_uri": "thing:appliance/coffeemachine/pump",
  "relation_metadata": {
    "required": true,
    "quantity": 1,
    "position": "internal"
  }
}
```

#### Get Thing Relationships
```http
GET /api/v1/things/{thing_id}/relationships
```

### System Information

#### Health Check
```http
GET /health
```

## Data Models

### Thing Schema
```typescript
interface Thing {
  id: string;
  uri: string;
  type: string;
  name: {
    default: string;
    translations: Record<string, string>;
  };
  manufacturer: {
    name: string;
    website?: string;
    contact?: string;
  };
  properties: {
    dimensions?: {
      length: number;
      width: number;
      height: number;
    };
    materials: string[];
    manufacturing_date?: string;
    serial_number?: string;
  };
  created_at: string;
  updated_at?: string;
}
```

### Story Schema
```typescript
interface Story {
  id: string;
  thing_id: string;
  type: string;
  version: {
    number: string;
    date: string;
    history: Array<{
      version: string;
      date: string;
      changes: string[];
    }>;
  };
  procedure: Array<{
    order: number;
    description: {
      default: string;
      translations: Record<string, string>;
    };
    warnings: string[];
    tools: string[];
    media: string[];
  }>;
  created_at: string;
}
```

### Relationship Schema
```typescript
interface Relationship {
  id: string;
  thing_id: string;
  relationship_type: string;
  target_uri: string;
  relation_metadata?: {
    required?: boolean;
    quantity?: number;
    position?: string;
  };
  created_at: string;
}
```

## Usage Examples

### Creating a Complete Repair Guide
1. Create the main thing:
```bash
curl -X POST http://localhost:8000/api/v1/things \
-H "Content-Type: application/json" \
-d '{
  "type": "appliance",
  "name": {
    "default": "Coffee Machine Model X",
    "translations": {
      "es": "Máquina de Café Modelo X"
    }
  },
  "manufacturer": {
    "name": "BaristaPlus",
    "website": "https://example.com"
  },
  "properties": {
    "dimensions": {
      "length": 30.0,
      "width": 20.0,
      "height": 40.0
    },
    "materials": ["steel", "plastic", "glass"]
  }
}'
```

2. Create relationships for components:
```bash
curl -X POST http://localhost:8000/api/v1/relationships \
-H "Content-Type: application/json" \
-d '{
  "thing_id": "THING_ID_HERE",
  "relationship_type": "component",
  "target_uri": "thing:appliance/coffeemachine/pump",
  "relation_metadata": {
    "required": true,
    "quantity": 1
  }
}'
```

3. Create a repair story:
```bash
curl -X POST http://localhost:8000/api/v1/stories \
-H "Content-Type: application/json" \
-d '{
  "thing_id": "THING_ID_HERE",
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
    },
    {
      "order": 2,
      "description": {
        "default": "Replace the pump",
        "translations": {
          "es": "Reemplace la bomba"
        }
      },
      "tools": ["wrench", "pliers"]
    }
  ]
}'
```

## Best Practices

1. **Multilingual Support**
   - Always provide a default language version
   - Use ISO language codes for translations
   - Keep translations consistent across related items

2. **Relationships**
   - Use clear, descriptive relationship types
   - Include relevant metadata for maintenance
   - Document both directions of relationships when applicable

3. **Stories**
   - Break procedures into clear, manageable steps
   - Include all necessary safety warnings
   - Document required tools and skills
   - Use clear, unambiguous language

4. **Media and Documentation**
   - Use high-quality images
   - Include multiple angles when relevant
   - Label diagrams clearly
   - Reference official documentation when available

## Error Handling

The API uses standard HTTP status codes:
- 200: Success
- 400: Bad Request (invalid input)
- 404: Not Found
- 500: Server Error

Error responses include detail messages:
```json
{
  "detail": "Error description"
}
```
