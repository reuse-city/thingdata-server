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
  "version": "0.1.0",
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
    "materials": ["steel", "plastic"],
    "manufacturing_date": "2024-01-01"  # Note: dates must be in ISO format
  }
}'

# The response will include ISO formatted dates:
{
  "id": "uuid",
  "uri": "thing:appliance/BaristaPlus/Coffee Machine XK-42",
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
    "materials": ["steel", "plastic"],
    "manufacturing_date": "2024-01-01"
  },
  "created_at": "2024-11-27T01:23:45Z",
  "updated_at": null
}
```

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
