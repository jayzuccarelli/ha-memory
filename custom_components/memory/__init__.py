"""The Memory integration — file-backed persistent memory for HA Assist."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, llm

from .const import (
    CONF_PATH,
    DEFAULT_PATH,
    DOMAIN,
    SERVICE_DELETE,
    SERVICE_READ,
    SERVICE_SAVE,
    VALID_TYPES,
)
from .assist_api import MemoryAPI
from .memory_store import (
    MemoryError as _MemoryError,
    MemoryStore,
    async_delete,
    async_read,
    async_save,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

SAVE_SCHEMA = vol.Schema(
    {
        vol.Required("name"): cv.string,
        vol.Required("type"): vol.In(VALID_TYPES),
        vol.Required("description"): cv.string,
        vol.Required("content"): cv.string,
    }
)

READ_SCHEMA = vol.Schema({vol.Required("name"): cv.string})
DELETE_SCHEMA = vol.Schema({vol.Required("name"): cv.string})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Memory from a config entry."""
    path = entry.data.get(CONF_PATH, DEFAULT_PATH)
    store = await hass.async_add_executor_job(MemoryStore, path)

    api = MemoryAPI(hass, store)
    unregister_api = llm.async_register_api(hass, api)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "store": store,
        "unregister_api": unregister_api,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_save(call: ServiceCall) -> None:
        try:
            await async_save(
                hass,
                store,
                call.data["name"],
                call.data["type"],
                call.data["description"],
                call.data["content"],
            )
        except _MemoryError as err:
            raise HomeAssistantError(str(err)) from err
        sensor_eid = f"sensor.{DOMAIN}_index"
        if hass.services.has_service("homeassistant", "update_entity"):
            await hass.services.async_call(
                "homeassistant",
                "update_entity",
                {"entity_id": sensor_eid},
                blocking=False,
            )

    async def handle_read(call: ServiceCall) -> ServiceResponse:
        try:
            content = await async_read(hass, store, call.data["name"])
        except _MemoryError as err:
            raise HomeAssistantError(str(err)) from err
        return {"name": call.data["name"], "content": content}

    async def handle_delete(call: ServiceCall) -> None:
        try:
            await async_delete(hass, store, call.data["name"])
        except _MemoryError as err:
            raise HomeAssistantError(str(err)) from err
        sensor_eid = f"sensor.{DOMAIN}_index"
        if hass.services.has_service("homeassistant", "update_entity"):
            await hass.services.async_call(
                "homeassistant",
                "update_entity",
                {"entity_id": sensor_eid},
                blocking=False,
            )

    hass.services.async_register(DOMAIN, SERVICE_SAVE, handle_save, schema=SAVE_SCHEMA)
    hass.services.async_register(
        DOMAIN,
        SERVICE_READ,
        handle_read,
        schema=READ_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_DELETE, handle_delete, schema=DELETE_SCHEMA
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        slot = hass.data[DOMAIN].pop(entry.entry_id, None)
        if slot is not None:
            slot["unregister_api"]()
        for svc in (SERVICE_SAVE, SERVICE_READ, SERVICE_DELETE):
            hass.services.async_remove(DOMAIN, svc)
    return unload_ok
