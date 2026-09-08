"""Shared base entity for Super Productivity."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import SuperProductivityCoordinator


class SuperProductivityEntity(CoordinatorEntity[SuperProductivityCoordinator]):
    """Base entity that ties everything to one service device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SuperProductivityCoordinator, key: str) -> None:
        """Set unique id and device info."""
        super().__init__(coordinator)
        entry_id = coordinator.config_entry.entry_id
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Super Productivity",
            manufacturer=MANUFACTURER,
            model="Local REST API",
        )
