"""Sensor exposing the MEMORY.md index as an attribute."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .memory_store import MemoryStore, async_read_index

SCAN_INTERVAL = timedelta(seconds=60)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    store: MemoryStore = hass.data[DOMAIN][entry.entry_id]["store"]
    async_add_entities([MemoryIndexSensor(entry, store)], update_before_add=True)


class MemoryIndexSensor(SensorEntity):
    """Sensor whose state is the count of memories and whose attribute holds the full index."""

    _attr_has_entity_name = False
    _attr_should_poll = True
    _attr_icon = "mdi:notebook-outline"

    def __init__(self, entry: ConfigEntry, store: MemoryStore) -> None:
        self._store = store
        self._attr_unique_id = f"{entry.entry_id}_index"
        self._attr_name = "Memory Index"
        self.entity_id = f"sensor.{DOMAIN}_index"
        self._content = ""

    @property
    def native_value(self) -> int:
        return sum(1 for ln in self._content.splitlines() if ln.strip())

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        return {"content": self._content}

    async def async_update(self) -> None:
        self._content = await async_read_index(self.hass, self._store)
