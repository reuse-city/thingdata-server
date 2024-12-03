# Advanced Operations Guide

## Entity Management

### Category-based Documentation
Create documentation for categories of items rather than specific things:

```http
POST /api/v1/guides
Content-Type: application/json

{
  "thing_category": {
    "category": "laptop",
    "subcategory": "notebook",
    "attributes": {
      "form_factor": "clamshell",
      "size_range": "13-15 inch"
    }
  },
  "type": {
    "primary": "guide",
    "secondary": "repair"
  },
  "content": {
    "title": {
      "default": "Generic Laptop Hinge Repair Guide"
    },
    "summary": {
      "default": "How to fix common laptop hinge issues"
    },
    "requirements": {
      "skills": ["Basic electronics"],
      "tools": ["Screwdriver set"],
      "materials": ["Replacement hinges"]
    }
  }
}
```

### Cross-Entity Relationships

#### Create Guide-to-Story Relationship
```http
POST /api/v1/relationships
Content-Type: application/json

{
  "source_type": "guide",
  "source_id": "guide_uuid",
  "target_type": "story",
  "target_id": "story_uuid",
  "relationship_type": "implementation",
  "direction": "unidirectional",
  "metadata": {
    "success_rate": 0.95,
    "adaptations": ["modified_tools"]
  }
}
```

#### Create Story Reference
```http
POST /api/v1/relationships
Content-Type: application/json

{
  "source_type": "story",
  "source_id": "story_uuid1",
  "target_type": "story",
  "target_id": "story_uuid2",
  "relationship_type": "references",
  "direction": "unidirectional",
  "metadata": {
    "context": "alternative_method",
    "success_rate": 0.9
  }
}
```

## Deletion Operations

### Delete a Thing
```http
DELETE /api/v1/things/{thing_id}
X-Confirm-Delete: true

Returns: 204 No Content
```

### Delete a Story
```http
DELETE /api/v1/stories/{story_id}
X-Confirm-Delete: true

Returns: 204 No Content
```

### Delete a Guide
```http
DELETE /api/v1/guides/{guide_id}
X-Confirm-Delete: true

Returns: 204 No Content
```

### Delete a Relationship
```http
DELETE /api/v1/relationships/{relationship_id}
X-Confirm-Delete: true

Returns: 204 No Content
```

## Query Operations

### Search by Category
```http
GET /api/v1/guides?category=laptop&subcategory=notebook
GET /api/v1/stories?category=laptop&subcategory=notebook
```

### Complex Relationship Queries
```http
# Get all guides referencing a story
GET /api/v1/relationships?target_type=story&target_id={story_id}&source_type=guide

# Get all stories implementing a guide
GET /api/v1/relationships?source_type=story&target_type=guide&target_id={guide_id}&relationship_type=implements
```

### Find Related Content
```http
# Get all content related to a thing
GET /api/v1/relationships?target_type=thing&target_id={thing_id}

# Get all relationships for a guide
GET /api/v1/guides/{guide_id}/relationships
```

## Complete Working Examples

### Create a Complex Documentation Structure

1. Create a general guide:
```bash
curl -X POST http://localhost:8000/api/v1/guides \
-H "Content-Type: application/json" \
-d '{
  "thing_category": {
    "category": "laptop",
    "subcategory": "notebook"
  },
  "type": {
    "primary": "guide",
    "secondary": "repair"
  },
  "content": {
    "title": {
      "default": "Laptop Screen Replacement Guide"
    }
  }
}'
```

2. Create an implementation story:
```bash
curl -X POST http://localhost:8000/api/v1/stories \
-H "Content-Type: application/json" \
-d '{
  "thing_category": {
    "category": "laptop",
    "subcategory": "notebook"
  },
  "type": "repair",
  "procedure": [
    {
      "order": 1,
      "description": {
        "default": "Detailed implementation steps"
      }
    }
  ]
}'
```

3. Link them together:
```bash
curl -X POST http://localhost:8000/api/v1/relationships \
-H "Content-Type: application/json" \
-d '{
  "source_type": "story",
  "source_id": "story_uuid",
  "target_type": "guide",
  "target_id": "guide_uuid",
  "relationship_type": "implements",
  "direction": "unidirectional",
  "metadata": {
    "success_rate": 1.0,
    "modifications": []
  }
}'
```

### Find Related Documentation

1. Find all guides for a category:
```bash
curl "http://localhost:8000/api/v1/guides?category=laptop"
```

2. Find all stories implementing a guide:
```bash
curl "http://localhost:8000/api/v1/relationships?target_type=guide&target_id={guide_id}&relationship_type=implements"
```

3. Get complete documentation tree:
```bash
curl "http://localhost:8000/api/v1/guides/{guide_id}/relationships?include=stories,guides"
```

## Best Practices

1. Category Management
   - Use consistent category names
   - Include relevant attributes
   - Keep subcategories focused

2. Relationship Types
   - 'implements' for story->guide
   - 'references' for guide->guide
   - 'alternative' for story->story
   - 'has_component' for thing->thing

3. Documentation Structure
   - Create general guides first
   - Link implementation stories
   - Reference related guides
   - Document adaptations in metadata

4. Metadata Usage
   - Include success rates
   - Document modifications
   - Note regional variations
   - Track tool alternatives
