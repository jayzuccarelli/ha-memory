"""Common test fixtures for the Memory integration."""
from __future__ import annotations

import pytest

from homeassistant.setup import async_setup_component


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading of the local custom_components in every test."""
    yield


@pytest.fixture(autouse=True)
async def setup_homeassistant_core(hass):
    """Make sure the `homeassistant.update_entity` service is available."""
    await async_setup_component(hass, "homeassistant", {})
