"""Data update coordinator for Super Productivity."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    SuperProductivityApiClient,
    SuperProductivityAuthError,
    SuperProductivityError,
)
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_SECONDS, DOMAIN

_LOGGER = logging.getLogger(__name__)

type SuperProductivityConfigEntry = ConfigEntry[SuperProductivityCoordinator]


class SuperProductivityCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls the Local REST API and shares the result with all entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: SuperProductivityConfigEntry,
        client: SuperProductivityApiClient,
    ) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=entry.options.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_SECONDS
                )
            ),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch status, focus state and today's tasks in parallel."""
        try:
            status, focus, today_tasks = await asyncio.gather(
                self.client.async_get_status(),
                self.client.async_get_focus(),
                self.client.async_get_today_tasks(),
            )
        except SuperProductivityAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except SuperProductivityError as err:
            raise UpdateFailed(str(err)) from err

        return {
            "status": status or {},
            "focus": focus or {},
            "today_tasks": today_tasks or [],
        }
