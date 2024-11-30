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
  "timestamp": "2024-11-27T00:00:00Z",
  "version": "0.1.2",
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

## Working Example

Here's a complete working example of creating a coffee machine, its water tank component, a repair story, and establishing their relationship:

```bash
# 1. Create a coffee machine
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
    "name": "BaristaPlus",
    "website": "https://baristaplus.example.com",
    "contact": "support@baristaplus.example.com"
  },
  "properties": {
    "dimensions": {
      "length": 30.0,
      "width": 20.0,
      "height": 40.0
    },
    "materials": ["stainless steel", "plastic", "glass"],
    "manufacturing_date": "2024-01-01",
    "serial_number": "XK42-001"
  }
}'

# 2. Create its water tank component
curl -X POST http://localhost:8000/api/v1/things \
-H "Content-Type: application/json" \
-d '{
  "type": "component",
  "name": {
    "default": "Water Tank XK-42",
    "translations": {
      "es": "Tanque de Agua XK-42"
    }
  },
  "manufacturer": {
    "name": "BaristaPlus"
  },
  "properties": {
    "dimensions": {
      "length": 15.0,
      "width": 10.0,
      "height": 20.0
    },
    "materials": ["plastic", "rubber"],
    "serial_number": "WT-XK42-001"
  }
}'

# 3. Create a repair story
curl -X POST http://localhost:8000/api/v1/stories \
-H "Content-Type: application/json" \
-d '{
  "thing_id": "your_coffee_machine_id",
  "type": "repair",
  "procedure": [
    {
      "order": 1,
      "description": {
        "default": "Remove water tank and filter",
        "translations": {
          "es": "Retirar el tanque de agua y el filtro"
        }
      },
      "warnings": ["Ensure machine is cool and unplugged"],
      "tools": ["none"],
      "media": []
    },
    {
      "order": 2,
      "description": {
        "default": "Clean the water tank with mild soap",
        "translations": {
          "es": "Limpiar el tanque con jabón suave"
        }
      },
      "warnings": ["Use only mild soap", "Rinse thoroughly"],
      "tools": ["soft cloth", "mild soap"],
      "media": []
    }
  ]
}'

# 4. Create relationship between coffee machine and water tank
curl -X POST http://localhost:8000/api/v1/relationships \
-H "Content-Type: application/json" \
-d '{
  "thing_id": "your_coffee_machine_id",
  "relationship_type": "has_component",
  "target_uri": "your_water_tank_id",
  "relation_metadata": {
    "position": "top",
    "removable": true,
    "capacity": "1.5L"
  }
}'
```

All these examples have been tested and are working in the current implementation.

## Important Notes

### DateTime Handling
- All dates must be provided in ISO 8601 format
- The API returns dates in ISO 8601 format with UTC timezone
- The `created_at` and `updated_at` fields are automatically managed by the server

### Health Check Details
- The health check endpoint performs database connectivity tests
- System metrics include memory and CPU usage
- Component statuses can be: healthy, degraded, or unhealthy
- The overall status reflects the worst component status
