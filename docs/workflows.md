# ThingData Workflows and Examples

## Related Documentation
- [Core API Documentation](api/README.md)
- [Advanced Operations](api/advanced-operations.md)
- [Federation Protocol](api/federation.md)

## System Architecture

```mermaid
graph TB
    Client[Client Applications] --> API[ThingData API]
    API --> DB[(Database)]
    API --> Storage[Storage Service]
    API --> Federation[Federation Service]
    
    Federation --> |Sync| Instance1[Remote Instance 1]
    Federation --> |Sync| Instance2[Remote Instance 2]
    
    subgraph Services
        API
        DB
        Storage
        Federation
    end
```

## Data Relationships

```mermaid
erDiagram
    Thing ||--o{ Story : "has"
    Thing ||--o{ Relationship : "has"
    Thing ||--o{ Relationship : "target_of"
    
    Thing {
        string id
        string uri
        string type
        json name
        json manufacturer
        json properties
    }
    
    Story {
        string id
        string thing_id
        string type
        json version
        json procedure
    }
    
    Relationship {
        string id
        string thing_id
        string relationship_type
        string target_uri
        json relation_metadata
    }
```

## Example Workflows

### 1. Documenting a Coffee Machine Repair

```mermaid
sequenceDiagram
    participant User
    participant API
    participant DB
    
    User->>API: Create Thing (Coffee Machine)
    API->>DB: Store Thing
    DB-->>API: Return Thing ID
    
    User->>API: Create Components
    API->>DB: Store Components
    
    User->>API: Create Relationships
    API->>DB: Store Relationships
    
    User->>API: Create Repair Story
    API->>DB: Store Story
    
    User->>API: Add Media to Story
    API->>Storage: Store Media
```

Example API calls for this workflow:

```bash
# 1. Create the coffee machine
curl -X POST http://localhost:8000/api/v1/things \
-H "Content-Type: application/json" \
-d '{
  "type": "appliance",
  "name": {
    "default": "Professional Coffee Machine XK-42",
    "translations": {
      "es": "Máquina de Café Profesional XK-42",
      "de": "Professionelle Kaffeemaschine XK-42"
    }
  },
  "manufacturer": {
    "name": "BaristaPlus",
    "website": "https://example.com",
    "contact": "support@example.com"
  },
  "properties": {
    "dimensions": {
      "length": 45.0,
      "width": 30.0,
      "height": 40.0
    },
    "materials": ["stainless steel", "plastic", "glass"],
    "serial_number": "XK42-2024-001"
  }
}'

# Store the returned ID
COFFEE_MACHINE_ID="returned_id_here"

# 2. Create pump component
curl -X POST http://localhost:8000/api/v1/things \
-H "Content-Type: application/json" \
-d '{
  "type": "component",
  "name": {
    "default": "Water Pump 15 Bar",
    "translations": {
      "es": "Bomba de Agua 15 Bar",
      "de": "Wasserpumpe 15 Bar"
    }
  },
  "manufacturer": {
    "name": "PumpTech",
    "website": "https://example.com"
  },
  "properties": {
    "materials": ["brass", "steel"],
    "serial_number": "PT-15B-001"
  }
}'

# Store the returned ID
PUMP_ID="returned_id_here"

# 3. Create relationship between machine and pump
curl -X POST http://localhost:8000/api/v1/relationships \
-H "Content-Type: application/json" \
-d '{
  "thing_id": "'$COFFEE_MACHINE_ID'",
  "relationship_type": "component",
  "target_uri": "thing:component/pumptech/waterpump-15bar",
  "relation_metadata": {
    "required": true,
    "quantity": 1,
    "position": "internal",
    "maintenance_interval": "12 months"
  }
}'

# 4. Create repair story
curl -X POST http://localhost:8000/api/v1/stories \
-H "Content-Type: application/json" \
-d '{
  "thing_id": "'$COFFEE_MACHINE_ID'",
  "type": "repair",
  "procedure": [
    {
      "order": 1,
      "description": {
        "default": "Disconnect power and water supply",
        "translations": {
          "es": "Desconecte la alimentación y el suministro de agua",
          "de": "Trennen Sie Strom- und Wasserversorgung"
        }
      },
      "warnings": ["Ensure machine is completely powered off",
                  "Wait 30 minutes for machine to cool down"],
      "tools": []
    },
    {
      "order": 2,
      "description": {
        "default": "Remove the side panel (6 screws)",
        "translations": {
          "es": "Quite el panel lateral (6 tornillos)",
          "de": "Entfernen Sie die Seitenverkleidung (6 Schrauben)"
        }
      },
      "tools": ["Phillips screwdriver PH2"]
    },
    {
      "order": 3,
      "description": {
        "default": "Replace the pump",
        "translations": {
          "es": "Reemplace la bomba",
          "de": "Ersetzen Sie die Pumpe"
        }
      },
      "tools": ["Adjustable wrench", "Pliers"],
      "warnings": ["Mark water line connections before disconnecting"]
    }
  ]
}'
```

### 2. Alternative Parts Workflow

```mermaid
sequenceDiagram
    participant User
    participant API
    participant DB
    
    User->>API: Get Thing Details
    API->>DB: Fetch Thing
    DB-->>API: Return Thing
    
    User->>API: Get Relationships
    API->>DB: Fetch Relationships
    DB-->>API: Return Relationships
    
    User->>API: Create Alternative Part
    API->>DB: Store Alternative Part
    
    User->>API: Create Compatibility Relationship
    API->>DB: Store Relationship
    
    Note over User,DB: Optional: Add compatibility notes
```

Example for documenting alternative parts:

```bash
# 1. Create alternative pump
curl -X POST http://localhost:8000/api/v1/things \
-H "Content-Type: application/json" \
-d '{
  "type": "component",
  "name": {
    "default": "Universal Pump 16 Bar",
    "translations": {
      "es": "Bomba Universal 16 Bar",
      "de": "Universal-Pumpe 16 Bar"
    }
  },
  "manufacturer": {
    "name": "GenericPumps",
    "website": "https://example.com"
  },
  "properties": {
    "materials": ["brass", "steel"],
    "serial_number": "GP-16B-002"
  }
}'

# Store the returned ID
ALT_PUMP_ID="returned_id_here"

# 2. Create compatibility relationship
curl -X POST http://localhost:8000/api/v1/relationships \
-H "Content-Type: application/json" \
-d '{
  "thing_id": "'$PUMP_ID'",
  "relationship_type": "alternative",
  "target_uri": "thing:component/genericpumps/universal-16bar",
  "relation_metadata": {
    "compatibility": {
      "fully_compatible": true,
      "notes": "Slightly higher pressure (16 bar vs 15 bar)",
      "verified_by": "RepairCafe Berlin",
      "verification_date": "2024-01-15"
    }
  }
}'
```

## Federation Workflows
For detailed federation examples and workflows, see the [Federation Protocol Documentation](api/federation.md).
