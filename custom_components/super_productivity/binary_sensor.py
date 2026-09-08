"""Binary sensors for Super Productivity."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import SuperProductivityConfigEntry, SuperProductivityCoordinator
from .entity import SuperProductivityEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class SuperProductivityBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a Super Productivity binary sensor."""

    value_fn: Callable[[dict[str, Any]], bool | None]


def _timer_status(data: dict[str, Any]) -> str | None:
    timer = data.get("focus", {}).get("timer")
    if isinstance(timer, dict):
        return timer.get("status")
    return None


BINARY_SENSORS: tuple[SuperProductivityBinarySensorDescription, ...] = (
    SuperProductivityBinarySensorDescription(
        key="tracking",
        translation_key="tracking",
        icon="mdi:play-circle-outline",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda d: d.get("status", {}).get("currentTaskId") is not None,
    ),
    SuperProductivityBinarySensorDescription(
        key="focus_running",
        translation_key="focus_running",
        icon="mdi:timer-play-outline",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda d: _timer_status(d) == "running",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SuperProductivityConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        SuperProductivityBinarySensor(coordinator, description)
        for description in BINARY_SENSORS
    )


class SuperProductivityBinarySensor(SuperProductivityEntity, BinarySensorEntity):
    """A single Super Productivity binary sensor."""

    entity_description: SuperProductivityBinarySensorDescription

    def __init__(
        self,
        coordinator: SuperProductivityCoordinator,
        description: SuperProductivityBinarySensorDescription,
    ) -> None:
        """Initialise the binary sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return the binary state."""
        return self.entity_description.value_fn(self.coordinator.data)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Write state on every coordinator refresh."""
        self.async_write_ha_state()
