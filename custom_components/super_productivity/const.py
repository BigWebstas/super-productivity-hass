"""Constants for the Super Productivity integration."""

from __future__ import annotations

DOMAIN = "super_productivity"

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 3876

DEFAULT_SCAN_INTERVAL_SECONDS = 30
MIN_SCAN_INTERVAL_SECONDS = 5
MAX_SCAN_INTERVAL_SECONDS = 3600

CONF_TOKEN = "token"
CONF_SCAN_INTERVAL = "scan_interval"

# The Local REST API rejects requests whose Host header is not loopback
# (DNS-rebinding guard). aiohttp derives Host from the URL, so when Home
# Assistant runs on a different machine than Super Productivity we must send a
# loopback Host header explicitly.
LOOPBACK_HOST_HEADER = "127.0.0.1"

MANUFACTURER = "Super Productivity"

# Service names.
SERVICE_START_TASK = "start_task"
SERVICE_STOP_TASK = "stop_task"
SERVICE_CREATE_TASK = "create_task"
SERVICE_ARCHIVE_TASK = "archive_task"

ATTR_CONFIG_ENTRY_ID = "config_entry_id"
ATTR_TASK_ID = "task_id"
ATTR_TITLE = "title"
ATTR_PROJECT_ID = "project_id"
ATTR_TAG_IDS = "tag_ids"
ATTR_NOTES = "notes"
ATTR_TIME_ESTIMATE = "time_estimate"
ATTR_PARENT_ID = "parent_id"
