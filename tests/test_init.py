"""Integration setup/unload tests using HA fixtures."""
from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.memory.const import CONF_PATH, DOMAIN


@pytest.fixture
def config_entry(hass, tmp_path):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_PATH: str(tmp_path)},
        title="Memory",
    )
    entry.add_to_hass(hass)
    return entry


async def test_setup_and_unload(hass, config_entry):
    """Setting up the integration registers services and a sensor."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.services.has_service(DOMAIN, "save")
    assert hass.services.has_service(DOMAIN, "read")
    assert hass.services.has_service(DOMAIN, "delete")
    assert hass.states.get("sensor.memory_index") is not None

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert not hass.services.has_service(DOMAIN, "save")


async def test_save_and_read_via_service(hass, config_entry):
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        "save",
        {
            "name": "pet_bau",
            "type": "user",
            "description": "User has a dog named Bau",
            "content": "The user has a dog named Bau.",
        },
        blocking=True,
    )

    response = await hass.services.async_call(
        DOMAIN,
        "read",
        {"name": "pet_bau"},
        blocking=True,
        return_response=True,
    )
    assert "Bau" in response["content"]


async def test_delete_via_service(hass, config_entry):
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN, "save",
        {"name": "k", "type": "user", "description": "d", "content": "b"},
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN, "delete", {"name": "k"}, blocking=True,
    )
    state = hass.states.get("sensor.memory_index")
    assert state is not None
