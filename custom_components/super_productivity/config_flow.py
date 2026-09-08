"""Config flow for Super Productivity."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    SuperProductivityApiClient,
    SuperProductivityAuthError,
    SuperProductivityConnectionError,
    SuperProductivityError,
)
from .const import CONF_TOKEN, DEFAULT_HOST, DEFAULT_PORT, DOMAIN


class SuperProductivityConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the UI configuration flow."""

    VERSION = 1

    async def _validate(self, data: Mapping[str, Any]) -> dict[str, str]:
        """Probe the API. Return a dict of errors (empty on success)."""
        client = SuperProductivityApiClient(
            data[CONF_HOST],
            data[CONF_PORT],
            data[CONF_TOKEN],
            async_get_clientsession(self.hass),
        )
        try:
            await client.async_health()
            await client.async_get_status()
        except SuperProductivityAuthError:
            return {"base": "invalid_auth"}
        except SuperProductivityConnectionError:
            return {"base": "cannot_connect"}
        except SuperProductivityError:
            return {"base": "unknown"}
        return {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect host, port and token."""
        errors: dict[str, str] = {}
        if user_input is not None:
            unique_id = f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            errors = await self._validate(user_input)
            if not errors:
                return self.async_create_entry(
                    title="Super Productivity", data=user_input
                )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_HOST,
                    default=(user_input or {}).get(CONF_HOST, DEFAULT_HOST),
                ): str,
                vol.Required(
                    CONF_PORT,
                    default=(user_input or {}).get(CONF_PORT, DEFAULT_PORT),
                ): int,
                vol.Required(CONF_TOKEN): str,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle re-authentication after a token change."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for a fresh token."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            data = {**entry.data, CONF_TOKEN: user_input[CONF_TOKEN]}
            errors = await self._validate(data)
            if not errors:
                return self.async_update_reload_and_abort(entry, data=data)

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}),
            errors=errors,
            description_placeholders={"host": entry.data[CONF_HOST]},
        )
