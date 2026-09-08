"""Diagnostics support for Super Productivity."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .const import CONF_TOKEN
from .coordinator import SuperProductivityConfigEntry

TO_REDACT = {CONF_TOKEN, CONF_HOST, "notes"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: SuperProductivityConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return {
        "entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "data": async_redact_data(coordinator.data, TO_REDACT),
    }
