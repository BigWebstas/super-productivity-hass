"""Sensors for Super Productivity."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import SuperProductivityConfigEntry, SuperProductivityCoordinator
from .entity import SuperProductivityEntity

PARALLEL_UPDATES = 0


def _today_key() -> str:
    """SP stores per-day time under a local YYYY-MM-DD key."""
    return date.today().isoformat()


def _current_task(data: dict[str, Any]) -> dict[str, Any] | None:
    task = data.get("status", {}).get("currentTask")
    return task if isinstance(task, dict) else None


def _today_tasks(data: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = data.get("today_tasks", [])
    return [t for t in tasks if isinstance(t, dict)]


def _timer(data: dict[str, Any]) -> dict[str, Any] | None:
    timer = data.get("focus", {}).get("timer")
    return timer if isinstance(timer, dict) else None


def _ms_to_min(value: Any) -> float | None:
    if not isinstance(value, (int, float)):
        return None
    return round(value / 60000, 1)


@dataclass(frozen=True, kw_only=True)
class SuperProductivitySensorDescription(SensorEntityDescription):
    """Describes a Super Productivity sensor."""

    value_fn: Callable[[dict[str, Any]], Any]
    attributes_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


SENSORS: tuple[SuperProductivitySensorDescription, ...] = (
    SuperProductivitySensorDescription(
        key="current_task",
        translation_key="current_task",
        icon="mdi:checkbox-marked-circle-outline",
        value_fn=lambda d: (t := _current_task(d)) and t.get("title") or None,
        attributes_fn=lambda d: _current_task_attrs(_current_task(d)),
    ),
    SuperProductivitySensorDescription(
        key="task_count",
        translation_key="task_count",
        icon="mdi:format-list-checks",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="tasks",
        value_fn=lambda d: d.get("status", {}).get("taskCount"),
    ),
    SuperProductivitySensorDescription(
        key="tasks_today_open",
        translation_key="tasks_today_open",
        icon="mdi:calendar-today",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="tasks",
        value_fn=lambda d: sum(
            1 for t in _today_tasks(d) if not t.get("isDone")
        ),
        attributes_fn=lambda d: {
            "titles": [
                t.get("title") for t in _today_tasks(d) if not t.get("isDone")
            ]
        },
    ),
    SuperProductivitySensorDescription(
        key="tasks_today_done",
        translation_key="tasks_today_done",
        icon="mdi:calendar-check",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="tasks",
        value_fn=lambda d: sum(1 for t in _today_tasks(d) if t.get("isDone")),
    ),
    SuperProductivitySensorDescription(
        key="tasks_today_total",
        translation_key="tasks_today_total",
        icon="mdi:calendar-multiple",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="tasks",
        value_fn=lambda d: len(_today_tasks(d)),
    ),
    SuperProductivitySensorDescription(
        key="time_spent_today",
        translation_key="time_spent_today",
        icon="mdi:timer-outline",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _ms_to_min(
            sum(
                t.get("timeSpentOnDay", {}).get(_today_key(), 0)
                for t in _today_tasks(d)
                if isinstance(t.get("timeSpentOnDay"), dict)
            )
        ),
    ),
    SuperProductivitySensorDescription(
        key="time_estimated_today",
        translation_key="time_estimated_today",
        icon="mdi:timer-sand",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _ms_to_min(
            sum(
                t.get("timeEstimate", 0)
                for t in _today_tasks(d)
                if isinstance(t.get("timeEstimate"), (int, float))
            )
        ),
    ),
    SuperProductivitySensorDescription(
        key="focus_mode",
        translation_key="focus_mode",
        icon="mdi:timer-play-outline",
        device_class=SensorDeviceClass.ENUM,
        options=["Flowtime", "Pomodoro", "Countdown"],
        value_fn=lambda d: d.get("focus", {}).get("mode"),
        attributes_fn=lambda d: {
            "cycle": d.get("focus", {}).get("cycle"),
            "session_done": d.get("focus", {}).get("isSessionDone"),
            "purpose": (_timer(d) or {}).get("purpose"),
            "status": (_timer(d) or {}).get("status"),
            "is_overtime": (_timer(d) or {}).get("isOvertime"),
        },
    ),
    SuperProductivitySensorDescription(
        key="focus_time_remaining",
        translation_key="focus_time_remaining",
        icon="mdi:timer-outline",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=lambda d: (
            round((_timer(d) or {}).get("remainingMs", 0) / 1000)
            if _timer(d)
            else None
        ),
    ),
)


def _current_task_attrs(task: dict[str, Any] | None) -> dict[str, Any]:
    """Expose useful fields of the current task."""
    if not task:
        return {}
    return {
        "task_id": task.get("id"),
        "project_id": task.get("projectId"),
        "tag_ids": task.get("tagIds"),
        "is_done": task.get("isDone"),
        "time_spent_minutes": _ms_to_min(task.get("timeSpent")),
        "time_estimate_minutes": _ms_to_min(task.get("timeEstimate")),
        "notes": task.get("notes"),
    }


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SuperProductivityConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        SuperProductivitySensor(coordinator, description) for description in SENSORS
    )


class SuperProductivitySensor(SuperProductivityEntity, SensorEntity):
    """A single Super Productivity sensor."""

    entity_description: SuperProductivitySensorDescription

    def __init__(
        self,
        coordinator: SuperProductivityCoordinator,
        description: SuperProductivitySensorDescription,
    ) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return the sensor state."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra attributes when the description provides them."""
        if self.entity_description.attributes_fn is None:
            return None
        return self.entity_description.attributes_fn(self.coordinator.data)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Write state on every coordinator refresh."""
        self.async_write_ha_state()
