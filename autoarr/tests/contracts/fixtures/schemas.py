"""
Contract schemas for API request/response validation.

These schemas define the expected structure of data at service boundaries.
"""

from typing import Any

# SABnzbd API Contracts
SABNZBD_QUEUE_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["queue"],
    "properties": {
        "queue": {
            "type": "object",
            "required": ["slots", "status", "speed"],
            "properties": {
                "slots": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["nzo_id", "filename", "status"],
                        "properties": {
                            "nzo_id": {"type": "string"},
                            "filename": {"type": "string"},
                            "status": {"type": "string"},
                            "percentage": {"type": "string"},
                            "timeleft": {"type": "string"},
                            "mb": {"type": "string"},
                            "mbleft": {"type": "string"},
                        },
                    },
                },
                "status": {"type": "string"},
                "speed": {"type": "string"},
                "paused": {"type": "boolean"},
            },
        },
    },
}

SABNZBD_HISTORY_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["history"],
    "properties": {
        "history": {
            "type": "object",
            "required": ["slots"],
            "properties": {
                "slots": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["nzo_id", "name", "status"],
                        "properties": {
                            "nzo_id": {"type": "string"},
                            "name": {"type": "string"},
                            "status": {"type": "string"},
                            "fail_message": {"type": "string"},
                            "completed": {"type": "integer"},
                        },
                    },
                },
            },
        },
    },
}

SABNZBD_CONFIG_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["config"],
    "properties": {
        "config": {
            "type": "object",
            "properties": {
                "misc": {"type": "object"},
                "servers": {"type": "array"},
                "categories": {"type": "array"},
            },
        },
    },
}

# Sonarr API Contracts
SONARR_SERIES_RESPONSE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["id", "title", "tvdbId"],
        "properties": {
            "id": {"type": "integer"},
            "title": {"type": "string"},
            "tvdbId": {"type": "integer"},
            "path": {"type": "string"},
            "qualityProfileId": {"type": "integer"},
            "monitored": {"type": "boolean"},
            "seasonFolder": {"type": "boolean"},
        },
    },
}

SONARR_QUALITY_PROFILE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["id", "name"],
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "upgradeAllowed": {"type": "boolean"},
            "cutoff": {"type": "integer"},
        },
    },
}

SONARR_ROOT_FOLDER_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["id", "path"],
        "properties": {
            "id": {"type": "integer"},
            "path": {"type": "string"},
            "freeSpace": {"type": "integer"},
        },
    },
}

# Radarr API Contracts
RADARR_MOVIE_RESPONSE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["id", "title", "tmdbId"],
        "properties": {
            "id": {"type": "integer"},
            "title": {"type": "string"},
            "tmdbId": {"type": "integer"},
            "path": {"type": "string"},
            "qualityProfileId": {"type": "integer"},
            "monitored": {"type": "boolean"},
            "hasFile": {"type": "boolean"},
        },
    },
}

RADARR_QUALITY_PROFILE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["id", "name"],
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "upgradeAllowed": {"type": "boolean"},
            "cutoff": {"type": "integer"},
        },
    },
}

# Internal API Contracts
CONFIG_AUDIT_REQUEST_SCHEMA = {
    "type": "object",
    "required": ["service"],
    "properties": {
        "service": {
            "type": "string",
            "enum": ["sabnzbd", "sonarr", "radarr", "plex"],
        },
    },
}

CONFIG_AUDIT_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["service", "findings", "timestamp"],
    "properties": {
        "service": {"type": "string"},
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["setting", "current", "recommended", "severity"],
                "properties": {
                    "setting": {"type": "string"},
                    "current": {},
                    "recommended": {},
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                    },
                    "explanation": {"type": "string"},
                },
            },
        },
        "timestamp": {"type": "string"},
        "score": {"type": "integer", "minimum": 0, "maximum": 100},
    },
}

CONTENT_REQUEST_SCHEMA = {
    "type": "object",
    "required": ["query"],
    "properties": {
        "query": {"type": "string", "minLength": 1},
        "content_type": {
            "type": "string",
            "enum": ["movie", "series", "auto"],
        },
    },
}

CONTENT_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["results", "content_type"],
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "title"],
                "properties": {
                    "id": {"type": "integer"},
                    "title": {"type": "string"},
                    "year": {"type": "integer"},
                    "overview": {"type": "string"},
                },
            },
        },
        "content_type": {"type": "string"},
        "total_results": {"type": "integer"},
    },
}

HEALTH_CHECK_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["status"],
    "properties": {
        "status": {"type": "string", "enum": ["healthy", "degraded", "unhealthy"]},
        "services": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "latency_ms": {"type": "number"},
                    "error": {"type": "string"},
                },
            },
        },
        "timestamp": {"type": "string"},
    },
}

ACTIVITY_LOG_ENTRY_SCHEMA = {
    "type": "object",
    "required": ["id", "action", "timestamp"],
    "properties": {
        "id": {"type": "string"},
        "action": {"type": "string"},
        "timestamp": {"type": "string"},
        "correlation_id": {"type": "string"},
        "details": {"type": "object"},
        "source": {"type": "string"},
    },
}

# MCP Tool Contracts
MCP_TOOL_CALL_SCHEMA = {
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {"type": "string"},
        "arguments": {"type": "object"},
    },
}

MCP_TOOL_RESULT_SCHEMA = {
    "type": "object",
    "required": ["content"],
    "properties": {
        "content": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["type"],
                "properties": {
                    "type": {"type": "string", "enum": ["text", "image", "resource"]},
                    "text": {"type": "string"},
                },
            },
        },
        "isError": {"type": "boolean"},
    },
}


def validate_schema(data: Any, schema: dict) -> tuple[bool, list[str]]:
    """
    Validate data against a JSON schema.

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    def _validate(data: Any, schema: dict, path: str = "") -> None:
        schema_type = schema.get("type")

        # Type validation
        if schema_type == "object":
            if not isinstance(data, dict):
                errors.append(f"{path}: Expected object, got {type(data).__name__}")
                return

            # Required fields
            for required in schema.get("required", []):
                if required not in data:
                    errors.append(f"{path}: Missing required field '{required}'")

            # Property validation
            properties = schema.get("properties", {})
            for key, value in data.items():
                if key in properties:
                    _validate(value, properties[key], f"{path}.{key}")

        elif schema_type == "array":
            if not isinstance(data, list):
                errors.append(f"{path}: Expected array, got {type(data).__name__}")
                return

            items_schema = schema.get("items", {})
            for i, item in enumerate(data):
                _validate(item, items_schema, f"{path}[{i}]")

        elif schema_type == "string":
            if not isinstance(data, str):
                errors.append(f"{path}: Expected string, got {type(data).__name__}")
            elif "enum" in schema and data not in schema["enum"]:
                errors.append(f"{path}: Value '{data}' not in allowed values {schema['enum']}")
            elif "minLength" in schema and len(data) < schema["minLength"]:
                errors.append(f"{path}: String too short (min {schema['minLength']})")

        elif schema_type == "integer":
            if not isinstance(data, int) or isinstance(data, bool):
                errors.append(f"{path}: Expected integer, got {type(data).__name__}")
            elif "minimum" in schema and data < schema["minimum"]:
                errors.append(f"{path}: Value {data} below minimum {schema['minimum']}")
            elif "maximum" in schema and data > schema["maximum"]:
                errors.append(f"{path}: Value {data} above maximum {schema['maximum']}")

        elif schema_type == "number":
            if not isinstance(data, (int, float)) or isinstance(data, bool):
                errors.append(f"{path}: Expected number, got {type(data).__name__}")

        elif schema_type == "boolean":
            if not isinstance(data, bool):
                errors.append(f"{path}: Expected boolean, got {type(data).__name__}")

    _validate(data, schema, "root")
    return len(errors) == 0, errors
