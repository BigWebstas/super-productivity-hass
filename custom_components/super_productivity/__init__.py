"""The Super Productivity integration."""

from __future__ import annotations

from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SuperProductivityApiClient
from .const import CONF_TOKEN
from .coordinator import SuperProductivityConfigEntry, SuperProductivityCoordinator
from .services import async_setup_services

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.SENSOR,
]


async def async_setup_entry(
    hass: HomeAssistant, entry: SuperProductivityConfigEntry
) -> bool:
    """Set up Super Productivity from a config entry."""
    client = SuperProductivityApiClient(
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_TOKEN],
        async_get_clientsession(hass),
    )
    coordinator = SuperProductivityCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    async_setup_services(hass)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: SuperProductivityConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
