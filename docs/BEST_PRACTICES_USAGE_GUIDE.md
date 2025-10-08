# Best Practices Database - Usage Guide

## Quick Start

### Initialize Database

```python
from autoarr.api.database import Database, init_database
from autoarr.api.seed_data import seed_best_practices

# Initialize database
db = init_database("sqlite+aiosqlite:///./autoarr.db")
await db.init_db()

# Seed with best practices
count = await seed_best_practices(db)
print(f"Seeded {count} best practices")
```

### Create Repository

```python
from autoarr.api.database import BestPracticesRepository, get_database

db = get_database()
repository = BestPracticesRepository(db)
```

## Common Queries

### Get All Practices for an Application

```python
# Get all SABnzbd practices
sabnzbd_practices = await repository.get_by_application("sabnzbd")

# Get only enabled practices
enabled_practices = await repository.get_by_application("sabnzbd", enabled_only=True)
```

### Get Practices by Category

```python
# Get Sonarr media management practices
practices = await repository.get_by_category("sonarr", "media_management")
```

### Get High Priority Practices

```python
# Get critical and high priority practices
important = await repository.get_by_priority(["critical", "high"])
```

### Search Practices

```python
# Search for practices containing "rename"
results = await repository.search("rename")

# Search in enabled practices only
results = await repository.search("https", enabled_only=True)
```

### Complex Filtering

```python
# Get SABnzbd high priority practices in downloads category
practices = await repository.filter(
    application="sabnzbd",
    category="downloads",
    priority="high"
)
```

## CRUD Operations

### Create a New Practice

```python
from autoarr.api.models import BestPracticeCreate

practice_data = BestPracticeCreate(
    application="sabnzbd",
    category="security",
    setting_name="api_key_required",
    setting_path="misc.api_key",
    recommended_value='{"type": "not_empty", "description": "API key should be set"}',
    current_check_type="not_empty",
    explanation="API key protects access to SABnzbd",
    priority="critical",
    version_added="1.0.0"
)

new_practice = await repository.create(practice_data.model_dump())
```

### Update a Practice

```python
# Update priority and explanation
updated = await repository.update(
    practice_id=1,
    data={
        "priority": "critical",
        "explanation": "Updated explanation"
    }
)
```

### Soft Delete (Disable)

```python
# Disable a practice without deleting it
await repository.soft_delete(practice_id=1)
```

### Permanent Delete

```python
# Permanently delete a practice
success = await repository.delete(practice_id=1)
```

## Bulk Operations

### Bulk Create

```python
practices_data = [
    {"application": "sabnzbd", "category": "performance", ...},
    {"application": "sonarr", "category": "quality", ...},
    {"application": "radarr", "category": "indexers", ...},
]

created = await repository.bulk_create(practices_data)
print(f"Created {len(created)} practices")
```

### Bulk Delete

```python
ids_to_delete = [1, 2, 3, 4, 5]
deleted_count = await repository.bulk_delete(ids_to_delete)
```

## Pagination

```python
# Get first page (5 items per page)
page1 = await repository.get_paginated(page=1, page_size=5)

# Get second page
page2 = await repository.get_paginated(page=2, page_size=5)
```

## Count Operations

```python
# Count all practices
total = await repository.count()

# Count SABnzbd practices
sabnzbd_count = await repository.count(application="sabnzbd")

# Count enabled practices
enabled_count = await repository.count(enabled_only=True)
```

## Converting to API Response Models

```python
from autoarr.api.models import BestPracticeResponse, BestPracticeListResponse

# Convert single practice
practices = await repository.get_by_application("sabnzbd")
first_practice = practices[0]

response = BestPracticeResponse.model_validate(first_practice)

# Convert list of practices
response_list = [BestPracticeResponse.model_validate(p) for p in practices]

# Create list response
list_response = BestPracticeListResponse(
    practices=response_list,
    total=len(response_list)
)
```

## Validation Examples

### Validate JSON Recommended Value

```python
from autoarr.api.models import BestPracticeCreate
import json

# This will raise ValidationError if JSON is invalid
try:
    practice = BestPracticeCreate(
        application="sabnzbd",
        recommended_value='{"type": "not_empty"}',  # Valid JSON
        ...
    )
except ValidationError as e:
    print(f"Invalid: {e}")
```

### Validate Application Type

```python
# Valid applications: sabnzbd, sonarr, radarr, plex
practice = BestPracticeCreate(
    application="sabnzbd",  # Valid
    ...
)

# This will raise ValidationError
practice = BestPracticeCreate(
    application="invalid_app",  # Invalid
    ...
)
```

### Validate Priority Level

```python
# Valid priorities: critical, high, medium, low
practice = BestPracticeCreate(
    priority="high",  # Valid
    ...
)

# This will raise ValidationError
practice = BestPracticeCreate(
    priority="urgent",  # Invalid
    ...
)
```

## Recommended Value Structure

The `recommended_value` field should contain JSON with this structure:

```json
{
  "type": "not_empty",
  "value": "actual_recommended_value",
  "description": "Human readable description",
  "alternatives": ["optional", "alternative", "values"],
  "min": 0,
  "max": 100,
  "example": "/path/to/recommended/location"
}
```

### Common Check Types

- `equals` - Value must equal recommended value
- `not_equals` - Value must not equal a certain value
- `contains` - Value must contain substring
- `not_contains` - Value must not contain substring
- `greater_than` - Numeric value must be greater
- `less_than` - Numeric value must be less
- `in_range` - Numeric value must be in range
- `regex` - Value must match regex pattern
- `exists` - Setting must exist
- `not_empty` - Setting must not be empty
- `boolean` - Boolean check
- `custom` - Custom validation logic required

## Error Handling

```python
from sqlalchemy.exc import IntegrityError

try:
    practice = await repository.create(data)
except IntegrityError as e:
    print(f"Database constraint violation: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Best Practices for Usage

1. **Use Enabled Filter**: When querying for active practices, use `enabled_only=True`
2. **Bulk Operations**: Use bulk operations when creating/deleting multiple practices
3. **Pagination**: Use pagination for large result sets to avoid memory issues
4. **Soft Delete**: Prefer soft delete over permanent delete to maintain history
5. **Validation**: Always validate inputs using Pydantic models before database operations
6. **Transactions**: Repository handles transactions automatically - don't nest session contexts
7. **Search**: Use search for user-facing queries, filter for programmatic queries
8. **Count**: Use count operations before pagination to calculate total pages

## Integration with Configuration Auditing

```python
from autoarr.api.database import BestPracticesRepository

async def audit_application_config(app_name: str, current_config: dict):
    """Audit application configuration against best practices."""
    repository = BestPracticesRepository(get_database())

    # Get all enabled practices for the application
    practices = await repository.get_by_application(app_name, enabled_only=True)

    issues = []
    for practice in practices:
        # Extract recommended value
        recommended = json.loads(practice.recommended_value)

        # Get current value from config
        current_value = get_config_value(current_config, practice.setting_path)

        # Check against practice
        if not validate_practice(current_value, practice.current_check_type, recommended):
            issues.append({
                "practice": practice,
                "current_value": current_value,
                "recommended_value": recommended
            })

    return issues
```

## Command-Line Usage (Future)

```bash
# Seed database
python -m autoarr.api.seed_data

# List practices
python -m autoarr.api.best_practices list --app=sabnzbd

# Search practices
python -m autoarr.api.best_practices search --query="https"

# Disable practice
python -m autoarr.api.best_practices disable --id=5
```

## API Endpoints (Future)

```
GET    /api/v1/best-practices                    # List all practices
GET    /api/v1/best-practices/{id}               # Get single practice
GET    /api/v1/best-practices?app=sabnzbd        # Filter by application
GET    /api/v1/best-practices?priority=critical  # Filter by priority
POST   /api/v1/best-practices                    # Create new practice
PUT    /api/v1/best-practices/{id}               # Update practice
DELETE /api/v1/best-practices/{id}               # Delete practice
POST   /api/v1/best-practices/bulk               # Bulk create
POST   /api/v1/best-practices/seed               # Seed database
```

## Performance Tips

1. **Index Usage**: Queries using application, category, priority, or enabled will use indexes
2. **Bulk Operations**: Creating 100+ practices? Use `bulk_create()` instead of loop
3. **Pagination**: For web UIs, use page_size=20 or page_size=50
4. **Caching**: Consider caching frequently accessed practices (all practices change rarely)
5. **Connection Pooling**: Configure SQLAlchemy pool size based on concurrent requests

## Troubleshooting

### Database Not Initialized

```python
# Error: RuntimeError: Database not initialized
# Solution: Call init_database() first
db = init_database("sqlite+aiosqlite:///./autoarr.db")
await db.init_db()
```

### Practice Not Found

```python
practice = await repository.get_by_id(999)
if practice is None:
    print("Practice not found")
```

### Validation Errors

```python
from pydantic import ValidationError

try:
    practice = BestPracticeCreate(**data)
except ValidationError as e:
    print(e.errors())  # Detailed error information
```

## Additional Resources

- Schema Documentation: `/app/docs/BEST_PRACTICES_SCHEMA.md`
- Implementation Summary: `/app/docs/BEST_PRACTICES_DB_IMPLEMENTATION_SUMMARY.md`
- API Models: `/app/autoarr/api/models.py`
- Repository Implementation: `/app/autoarr/api/database.py`
- Seed Data: `/app/autoarr/api/seed_data.py`
- Tests: `/app/autoarr/tests/unit/api/test_best_practices*.py`
