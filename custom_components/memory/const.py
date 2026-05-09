"""Constants for the Memory integration."""
from __future__ import annotations

DOMAIN = "memory"
DEFAULT_PATH = "/config/memory"

CONF_PATH = "path"

VALID_TYPES = ("user", "feedback", "project", "reference", "vocabulary")

INDEX_FILENAME = "MEMORY.md"

SERVICE_SAVE = "save"
SERVICE_READ = "read"
SERVICE_DELETE = "delete"
