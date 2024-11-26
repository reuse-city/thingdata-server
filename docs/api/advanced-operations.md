# Advanced Operations: Conflict Resolution & Data Management

## Deletion Operations

### Delete a Thing
```http
DELETE /api/v1/things/{thing_id}
```
- Deleting a thing will cascade delete all its stories and relationships
- Returns 204 No Content on success
- Requires confirmation header: `X-Confirm-Delete: true`

### Delete a Story
```http
DELETE /api/v1/stories/{story_id}
```
- Returns 204 No Content on success
- Does not affect related things or relationships

### Delete a Relationship
```http
DELETE /api/v1/relationships/{relationship_id}
```
- Returns 204 No Content on success
- Does not affect the connected things

### Batch Delete
```http
POST /api/v1/batch-delete
Content-Type: application/json

{
  "things": ["thing_id1", "thing_id2"],
  "stories": ["story_id1", "story_id2"],
  "relationships": ["relationship_id1", "relationship_id2"]
}
```

## Conflict Resolution

### Version Conflicts

#### Story Version Conflicts
When multiple users update the same story, the system handles conflicts through versioning:

1. **Version Check**
```http
GET /api/v1/stories/{story_id}/version
```
Returns:
```json
{
  "version": "1.0.0",
  "last_modified": "2024-11-26T12:00:00Z",
  "locked_by": null
}
```

2. **Update with Version Check**
```http
PUT /api/v1/stories/{story_id}
If-Match: "1.0.0"

{
  "type": "repair",
  "procedure": [...],
  "version": {
    "number": "1.0.0",
    "parent": null
  }
}
```

3. **Handling Version Conflicts**
If a conflict occurs (412 Precondition Failed), you can:

a. Get the conflicting versions:
```http
GET /api/v1/stories/{story_id}/versions
```

b. Create a merge resolution:
```http
POST /api/v1/stories/{story_id}/resolve
{
  "base_version": "1.0.0",
  "conflicting_version": "1.0.1",
  "resolution": {
    "procedure": [...],
    "resolution_notes": "Combined steps from both versions"
  }
}
```

### Relationship Conflicts

#### Conflicting Relationships
When conflicting relationships are detected (e.g., incompatible components):

1. **Check for Conflicts**
```http
GET /api/v1/things/{thing_id}/relationships/conflicts
```

2. **Resolve Conflicts**
```http
POST /api/v1/relationships/resolve
{
  "primary_relationship": "relationship_id1",
  "conflicting_relationship": "relationship_id2",
  "resolution": "replace|keep|merge",
  "resolution_metadata": {
    "reason": "Newer component supersedes old one",
    "documentation": "URL to documentation"
  }
}
```

### Federation Conflicts

When data conflicts occur between federated instances:

1. **Check Federation Status**
```http
GET /api/v1/federation/status
```

2. **List Conflicts**
```http
GET /api/v1/federation/conflicts
```

3. **Resolve Federation Conflict**
```http
POST /api/v1/federation/resolve
{
  "conflict_id": "conflict_uuid",
  "resolution": {
    "action": "accept_local|accept_remote|merge",
    "merge_strategy": "newest|manual|consensus",
    "resolution_metadata": {
      "reason": "Local instance has more recent data",
      "consensus_reached": true,
      "participating_instances": ["instance1", "instance2"]
    }
  }
}
```

## Data Management Policies

### Soft Delete
By default, deletions are "soft" - data is marked as deleted but not removed:

- Add `?permanent=true` to DELETE requests for permanent deletion
- Soft-deleted items can be restored within 30 days
- Permanently deleted items cannot be restored

### Restore Deleted Data
```http
POST /api/v1/restore
{
  "type": "thing|story|relationship",
  "id": "item_id"
}
```

### Audit Trail
Track changes and deletions:
```http
GET /api/v1/audit-trail?item_id=xxx&type=thing
```
Returns:
```json
{
  "audit_trail": [
    {
      "timestamp": "2024-11-26T12:00:00Z",
      "action": "delete",
      "user": "system",
      "metadata": {
        "reason": "User request",
        "permanent": false
      }
    }
  ]
}
```

## Example: Handling a Complex Conflict

Here's an example of resolving a conflict when two instances have different versions of a repair story:

1. Detect the conflict:
```bash
curl -X GET http://localhost:8000/api/v1/stories/story_id/conflicts
```

2. Get both versions:
```bash
curl -X GET http://localhost:8000/api/v1/stories/story_id/versions
```

3. Create a merged resolution:
```bash
curl -X POST http://localhost:8000/api/v1/stories/story_id/resolve \
-H "Content-Type: application/json" \
-d '{
  "base_version": "1.0.0",
  "conflicting_version": "1.0.1",
  "resolution": {
    "procedure": [
      {
        "order": 1,
        "description": {
          "default": "Updated step combining both versions",
          "translations": {
            "es": "Paso actualizado combinando ambas versiones"
          }
        },
        "warnings": [
          "Warning from version 1",
          "Additional warning from version 2"
        ],
        "tools": ["tool1", "tool2"]
      }
    ],
    "resolution_notes": "Combined safety warnings and tools from both versions",
    "resolution_metadata": {
      "consensus": true,
      "reviewed_by": ["expert1", "expert2"],
      "resolution_date": "2024-11-26T12:00:00Z"
    }
  }
}'
```

4. Verify the resolution:
```bash
curl -X GET http://localhost:8000/api/v1/stories/story_id/resolution-status
```

Would you like me to:
1. Add more conflict resolution scenarios?
2. Add documentation about automated conflict resolution?
3. Add cleanup and maintenance procedures?
4. Add federation-specific conflict handling?