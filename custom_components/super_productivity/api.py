"""Client for the Super Productivity Local REST API."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import LOOPBACK_HOST_HEADER

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)


class SuperProductivityError(Exception):
    """Base error for the Super Productivity API."""


class SuperProductivityConnectionError(SuperProductivityError):
    """Raised when the API cannot be reached."""


class SuperProductivityAuthError(SuperProductivityError):
    """Raised when the access token is missing or wrong."""


class SuperProductivityApiClient:
    """Minimal async client for the desktop Local REST API."""

    def __init__(
        self,
        host: str,
        port: int,
        token: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Store connection details."""
        self._base_url = f"http://{host}:{port}"
        self._token = token
        self._session = session
        # Always claim to be talking to loopback so the server's Host-header
        # guard accepts the request regardless of how HA routes to it.
        self._host_header = f"{LOOPBACK_HOST_HEADER}:{port}"

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        auth: bool = True,
    ) -> Any:
        """Perform one request and unwrap the `{ok, data}` envelope."""
        headers = {"Host": self._host_header}
        if auth:
            headers["Authorization"] = f"Bearer {self._token}"

        try:
            async with self._session.request(
                method,
                f"{self._base_url}{path}",
                params=params,
                json=json,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            ) as resp:
                try:
                    payload = await resp.json(content_type=None)
                except (aiohttp.ContentTypeError, ValueError):
                    payload = None

                if resp.status in (401, 403):
                    raise SuperProductivityAuthError(
                        _error_message(payload, "Access token rejected")
                    )
                if resp.status >= 400 or not _is_ok(payload):
                    raise SuperProductivityError(
                        _error_message(payload, f"HTTP {resp.status} for {path}")
                    )
                return payload.get("data") if isinstance(payload, dict) else None
        except SuperProductivityError:
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as err:
            raise SuperProductivityConnectionError(str(err)) from err

    async def async_health(self) -> dict[str, Any]:
        """Hit the unauthenticated health endpoint."""
        return await self._request("GET", "/health", auth=False)

    async def async_get_status(self) -> dict[str, Any]:
        """Return current task and task count."""
        return await self._request("GET", "/status")

    async def async_get_focus(self) -> dict[str, Any]:
        """Return the read-only Focus Mode timer state."""
        return await self._request("GET", "/focus")

    async def async_get_today_tasks(self) -> list[dict[str, Any]]:
        """Return today's tasks, done ones included."""
        return await self._request(
            "GET",
            "/tasks",
            params={"tagId": "TODAY", "includeDone": "true"},
        )

    async def async_start_task(self, task_id: str) -> Any:
        """Set a task as the current (tracked) task."""
        return await self._request("POST", f"/tasks/{task_id}/start")

    async def async_stop_task(self) -> Any:
        """Clear the current task, stopping time tracking."""
        return await self._request("POST", "/task-control/stop")

    async def async_create_task(self, payload: dict[str, Any]) -> Any:
        """Create a task."""
        return await self._request("POST", "/tasks", json=payload)

    async def async_complete_task(self, task_id: str) -> Any:
        """Mark a task as done."""
        return await self._request("PATCH", f"/tasks/{task_id}", json={"isDone": True})

    async def async_archive_task(self, task_id: str) -> Any:
        """Archive a task."""
        return await self._request("POST", f"/tasks/{task_id}/archive")


def _is_ok(payload: Any) -> bool:
    """True when the envelope reports success."""
    return isinstance(payload, dict) and payload.get("ok") is True


def _error_message(payload: Any, fallback: str) -> str:
    """Pull a human message out of an error envelope."""
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict) and error.get("message"):
            return str(error["message"])
    return fallback
