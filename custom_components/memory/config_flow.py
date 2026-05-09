"""Config flow for the Memory integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import config_validation as cv

from .const import CONF_PATH, DEFAULT_PATH, DOMAIN


class MemoryConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Memory."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Single-instance integration; pick the on-disk path."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title="Memory", data=user_input)

        schema = vol.Schema(
            {vol.Required(CONF_PATH, default=DEFAULT_PATH): cv.string}
        )
        return self.async_show_form(step_id="user", data_schema=schema)
