"""Common test fixtures for the Memory integration."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading of the local custom_components in every test."""
    yield
