"""Buttons for Super Productivity."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import SuperProductivityError
from .coordinator import SuperProductivityConfigEntry, SuperProductivityCoordinator
from .entity import SuperProductivityEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SuperProductivityConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up buttons from a config entry."""
    async_add_entities([StopTrackingButton(entry.runtime_data)])


class StopTrackingButton(SuperProductivityEntity, ButtonEntity):
    """Clears the current task, stopping time tracking."""

    _attr_translation_key = "stop_tracking"
    _attr_icon = "mdi:stop-circle-outline"

    def __init__(self, coordinator: SuperProductivityCoordinator) -> None:
        """Initialise the button."""
        super().__init__(coordinator, "stop_tracking")

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            await self.coordinator.client.async_stop_task()
        except SuperProductivityError as err:
            raise HomeAssistantError(f"Could not stop tracking: {err}") from err
        await self.coordinator.async_request_refresh()
