"""Services for Super Productivity."""

from __future__ import annotations

from typing import Any, cast

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .api import SuperProductivityError
from .const import (
    ATTR_CONFIG_ENTRY_ID,
    ATTR_NOTES,
    ATTR_PARENT_ID,
    ATTR_PROJECT_ID,
    ATTR_TAG_IDS,
    ATTR_TASK_ID,
    ATTR_TIME_ESTIMATE,
    ATTR_TITLE,
    DOMAIN,
    SERVICE_ARCHIVE_TASK,
    SERVICE_CREATE_TASK,
    SERVICE_START_TASK,
    SERVICE_STOP_TASK,
)
from .coordinator import SuperProductivityConfigEntry, SuperProductivityCoordinator

_ENTRY_SCHEMA = {vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string}

_START_TASK_SCHEMA = vol.Schema(
    {**_ENTRY_SCHEMA, vol.Required(ATTR_TASK_ID): cv.string}
)
_STOP_TASK_SCHEMA = vol.Schema(_ENTRY_SCHEMA)
_ARCHIVE_TASK_SCHEMA = vol.Schema(
    {**_ENTRY_SCHEMA, vol.Required(ATTR_TASK_ID): cv.string}
)
_CREATE_TASK_SCHEMA = vol.Schema(
    {
        **_ENTRY_SCHEMA,
        vol.Required(ATTR_TITLE): cv.string,
        vol.Optional(ATTR_PROJECT_ID): cv.string,
        vol.Optional(ATTR_PARENT_ID): cv.string,
        vol.Optional(ATTR_TAG_IDS): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(ATTR_NOTES): cv.string,
        vol.Optional(ATTR_TIME_ESTIMATE): vol.All(
            vol.Coerce(int), vol.Range(min=0)
        ),
    }
)


def _get_coordinator(
    hass: HomeAssistant, call: ServiceCall
) -> SuperProductivityCoordinator:
    """Resolve the coordinator a service call targets."""
    entries: list[SuperProductivityConfigEntry] = [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.state is ConfigEntryState.LOADED
    ]
    if not entries:
        raise ServiceValidationError("Super Productivity is not set up")

    entry_id = call.data.get(ATTR_CONFIG_ENTRY_ID)
    if entry_id is None:
        if len(entries) > 1:
            raise ServiceValidationError(
                "Multiple Super Productivity entries configured — "
                f"pass {ATTR_CONFIG_ENTRY_ID}"
            )
        return entries[0].runtime_data

    for entry in entries:
        if entry.entry_id == entry_id:
            return entry.runtime_data
    raise ServiceValidationError(f"Unknown {ATTR_CONFIG_ENTRY_ID}: {entry_id}")


def async_setup_services(hass: HomeAssistant) -> None:
    """Register services once."""
    if hass.services.has_service(DOMAIN, SERVICE_START_TASK):
        return

    async def _start_task(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        await _run(coordinator.client.async_start_task(call.data[ATTR_TASK_ID]))
        await coordinator.async_request_refresh()

    async def _stop_task(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        await _run(coordinator.client.async_stop_task())
        await coordinator.async_request_refresh()

    async def _archive_task(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        await _run(coordinator.client.async_archive_task(call.data[ATTR_TASK_ID]))
        await coordinator.async_request_refresh()

    async def _create_task(call: ServiceCall) -> ServiceResponse:
        coordinator = _get_coordinator(hass, call)
        payload: dict[str, Any] = {"title": call.data[ATTR_TITLE]}
        if ATTR_PROJECT_ID in call.data:
            payload["projectId"] = call.data[ATTR_PROJECT_ID]
        if ATTR_PARENT_ID in call.data:
            payload["parentId"] = call.data[ATTR_PARENT_ID]
        if ATTR_TAG_IDS in call.data:
            payload["tagIds"] = call.data[ATTR_TAG_IDS]
        if ATTR_NOTES in call.data:
            payload["notes"] = call.data[ATTR_NOTES]
        if ATTR_TIME_ESTIMATE in call.data:
            payload["timeEstimate"] = call.data[ATTR_TIME_ESTIMATE]

        created = await _run(coordinator.client.async_create_task(payload))
        await coordinator.async_request_refresh()
        task = cast(dict[str, Any], created or {})
        return {"id": task.get("id"), "task": task}

    hass.services.async_register(
        DOMAIN, SERVICE_START_TASK, _start_task, schema=_START_TASK_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_STOP_TASK, _stop_task, schema=_STOP_TASK_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_ARCHIVE_TASK, _archive_task, schema=_ARCHIVE_TASK_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_TASK,
        _create_task,
        schema=_CREATE_TASK_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )


async def _run(coro: Any) -> Any:
    """Await an API call, turning API errors into HA errors."""
    try:
        return await coro
    except SuperProductivityError as err:
        raise HomeAssistantError(f"Super Productivity request failed: {err}") from err
