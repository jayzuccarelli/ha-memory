"""Describe Memory events in the logbook."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.components.logbook import (
    LOGBOOK_ENTRY_MESSAGE,
    LOGBOOK_ENTRY_NAME,
    LazyEventPartialState,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, EVENT_MEMORY_DELETED, EVENT_MEMORY_SAVED

_ACTIONS = {EVENT_MEMORY_SAVED: "saved", EVENT_MEMORY_DELETED: "deleted"}


@callback
def async_describe_events(
    hass: HomeAssistant,
    async_describe_event: Callable[
        [str, str, Callable[[LazyEventPartialState], dict[str, Any]]], None
    ],
) -> None:
    """Describe logbook events."""

    @callback
    def async_describe_memory_event(event: LazyEventPartialState) -> dict[str, Any]:
        data = event.data
        message = f"{_ACTIONS[event.event_type]}: {data['name']}"
        if device_id := data.get("device_id"):
            device = dr.async_get(hass).async_get(device_id)
            label = (device.name_by_user or device.name) if device else None
            message = f"{message} (from {label or device_id})"
        return {LOGBOOK_ENTRY_NAME: "Memory", LOGBOOK_ENTRY_MESSAGE: message}

    for event_type in _ACTIONS:
        async_describe_event(DOMAIN, event_type, async_describe_memory_event)
