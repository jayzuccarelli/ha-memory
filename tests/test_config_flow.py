"""Tests for the config flow."""
from __future__ import annotations

from homeassistant.config_entries import SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType

from custom_components.memory.const import CONF_PATH, DEFAULT_PATH, DOMAIN


async def test_user_flow_creates_entry(hass, tmp_path):
    """Submitting the user form creates a config entry with the given path."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PATH: str(tmp_path)}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_PATH: str(tmp_path)}


async def test_single_instance_only(hass, tmp_path):
    """A second flow attempt aborts because only one instance is allowed."""
    first = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    await hass.config_entries.flow.async_configure(
        first["flow_id"], {CONF_PATH: str(tmp_path)}
    )

    second = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert second["type"] == FlowResultType.ABORT
    assert second["reason"] == "single_instance_allowed"


async def test_default_path_in_form(hass):
    """The form pre-fills the default path."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    schema = result["data_schema"].schema
    path_key = next(k for k in schema if str(k) == CONF_PATH)
    assert path_key.default() == DEFAULT_PATH
