# Best Practices Database Schema

## Overview

The best_practices table stores configuration best practices for SABnzbd, Sonarr, Radarr, and Plex.

## Schema Design

### Table: best_practices

| Column             | Type        | Description                                     | Constraints                         |
| ------------------ | ----------- | ----------------------------------------------- | ----------------------------------- |
| id                 | Integer     | Primary key                                     | AUTO_INCREMENT, NOT NULL            |
| application        | String(50)  | Application name                                | NOT NULL, INDEX                     |
| category           | String(100) | Configuration category                          | NOT NULL, INDEX                     |
| setting_name       | String(200) | Name of the setting                             | NOT NULL                            |
| setting_path       | String(500) | JSON path or config location                    | NOT NULL                            |
| recommended_value  | Text        | Recommended value (JSON)                        | NOT NULL                            |
| current_check_type | String(50)  | How to validate (equals, contains, range, etc.) | NOT NULL                            |
| explanation        | Text        | Why this is recommended                         | NOT NULL                            |
| priority           | String(20)  | Priority level (critical, high, medium, low)    | NOT NULL, DEFAULT 'medium'          |
| impact             | Text        | Impact of not following this practice           | NULL                                |
| documentation_url  | String(500) | Link to official docs                           | NULL                                |
| version_added      | String(50)  | Version when practice was added                 | NOT NULL                            |
| version_updated    | String(50)  | Last version updated                            | NULL                                |
| enabled            | Boolean     | Whether this practice is active                 | NOT NULL, DEFAULT TRUE              |
| created_at         | DateTime    | When record was created                         | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at         | DateTime    | When record was last updated                    | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

### Indexes

- `idx_application` on (application)
- `idx_category` on (category)
- `idx_priority` on (priority)
- `idx_application_category` on (application, category)
- `idx_enabled` on (enabled)

### Applications

- `sabnzbd` - SABnzbd download client
- `sonarr` - TV show manager
- `radarr` - Movie manager
- `plex` - Media server

### Categories

**SABnzbd:**

- downloads - Download settings
- performance - Performance optimization
- indexers - Indexer configuration
- post_processing - Post-processing settings
- security - Security settings

**Sonarr:**

- quality - Quality profiles and settings
- indexers - Indexer configuration
- media_management - File organization
- download_clients - Download client settings
- metadata - Metadata settings

**Radarr:**

- quality - Quality profiles and settings
- indexers - Indexer configuration
- media_management - File organization
- download_clients - Download client settings
- metadata - Metadata settings

**Plex:**

- library - Library settings
- transcoding - Transcoding settings
- network - Network settings
- agents - Metadata agents
- performance - Performance settings

### Priority Levels

- `critical` - Must be fixed immediately (security, data loss)
- `high` - Should be fixed soon (significant performance/functionality)
- `medium` - Should be fixed eventually (minor issues)
- `low` - Nice to have (cosmetic, minor optimizations)

### Check Types

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

## Example Records

### SABnzbd - Incomplete Download Directory

```json
{
  "application": "sabnzbd",
  "category": "downloads",
  "setting_name": "incomplete_dir",
  "setting_path": "misc.incomplete_dir",
  "recommended_value": "{\"type\": \"not_empty\", \"description\": \"Separate directory for incomplete downloads\"}",
  "current_check_type": "not_empty",
  "explanation": "Using a separate incomplete directory prevents partially downloaded files from being processed by post-processing scripts and keeps your completed downloads directory clean.",
  "priority": "high",
  "impact": "Incomplete downloads may be processed by automation tools, causing errors and wasted bandwidth.",
  "documentation_url": "https://sabnzbd.org/wiki/configuration/",
  "version_added": "1.0.0",
  "enabled": true
}
```

### Sonarr - Episode Monitoring

```json
{
  "application": "sonarr",
  "category": "media_management",
  "setting_name": "auto_unmonitor_previously_downloaded_episodes",
  "setting_path": "settings.mediaManagement.autoUnmonitorPreviouslyDownloadedEpisodes",
  "recommended_value": "{\"type\": \"boolean\", \"value\": true}",
  "current_check_type": "equals",
  "explanation": "Automatically unmonitoring previously downloaded episodes prevents Sonarr from re-downloading episodes when switching quality profiles or re-syncing.",
  "priority": "medium",
  "impact": "May result in duplicate downloads and wasted bandwidth when upgrading quality profiles.",
  "documentation_url": "https://wiki.servarr.com/sonarr/settings#media-management",
  "version_added": "1.0.0",
  "enabled": true
}
```

## Querying Patterns

### Get all practices for an application

```python
practices = await repository.get_by_application("sabnzbd")
```

### Get practices by category

```python
practices = await repository.get_by_category("sabnzbd", "downloads")
```

### Get critical/high priority practices

```python
practices = await repository.get_by_priority(["critical", "high"])
```

### Search practices

```python
practices = await repository.search("incomplete", "sabnzbd")
```

## Data Validation

### Recommended Value JSON Schema

The `recommended_value` field stores JSON with the following structure:

```json
{
  "type": "string|number|boolean|array|object",
  "value": "actual_recommended_value",
  "description": "Human readable description",
  "alternatives": ["optional", "alternative", "values"],
  "min": 0, // for numeric ranges
  "max": 100 // for numeric ranges
}
```

## Migration Strategy

### Initial Migration (v1)

1. Create best_practices table
2. Add indexes
3. Seed initial 20+ best practices

### Future Migrations

- Add fields for user customization
- Add versioning/history tracking
- Add tags/labels for filtering
- Add dependencies between practices
