"""Test the LLM AssistAPI tools (memory_save / memory_read / memory_delete)."""
from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.helpers import llm

from custom_components.memory.const import CONF_PATH, DOMAIN


@pytest.fixture
async def setup_integration(hass, tmp_path):
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_PATH: str(tmp_path)}, title="Memory"
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _ctx(hass) -> llm.LLMContext:
    return llm.LLMContext(
        platform="test",
        context=None,
        language="en",
        assistant=None,
        device_id=None,
    )


async def test_api_registered(hass, setup_integration):
    api = await llm.async_get_api(hass, DOMAIN, _ctx(hass))
    assert api is not None
    assert api.api.name == "Memory"


async def test_api_prompt_contains_index(hass, setup_integration):
    # Save through the service; then the API prompt should reflect it.
    await hass.services.async_call(
        DOMAIN, "save",
        {"name": "k", "type": "user", "description": "an entry", "content": "body"},
        blocking=True,
    )
    api = await llm.async_get_api(hass, DOMAIN, _ctx(hass))
    assert "an entry" in api.api_prompt


async def test_save_tool_persists_memory(hass, setup_integration):
    api = await llm.async_get_api(hass, DOMAIN, _ctx(hass))
    save_tool = next(t for t in api.tools if t.name == "memory_save")

    result = await api.async_call_tool(
        llm.ToolInput(
            tool_name="memory_save",
            tool_args={
                "name": "pet_bau",
                "type": "user",
                "description": "User has a dog named Bau",
                "content": "The user has a dog named Bau.",
            },
        )
    )
    assert result == {"saved": "pet_bau"}

    # Confirm via service that it's actually saved.
    response = await hass.services.async_call(
        DOMAIN, "read", {"name": "pet_bau"}, blocking=True, return_response=True,
    )
    assert "Bau" in response["content"]


async def test_read_tool_returns_content(hass, setup_integration):
    await hass.services.async_call(
        DOMAIN, "save",
        {"name": "k", "type": "user", "description": "d", "content": "the body"},
        blocking=True,
    )
    api = await llm.async_get_api(hass, DOMAIN, _ctx(hass))
    result = await api.async_call_tool(
        llm.ToolInput(tool_name="memory_read", tool_args={"name": "k"})
    )
    assert result["name"] == "k"
    assert "the body" in result["content"]


async def test_delete_tool_removes_memory(hass, setup_integration):
    await hass.services.async_call(
        DOMAIN, "save",
        {"name": "k", "type": "user", "description": "d", "content": "b"},
        blocking=True,
    )
    api = await llm.async_get_api(hass, DOMAIN, _ctx(hass))
    result = await api.async_call_tool(
        llm.ToolInput(tool_name="memory_delete", tool_args={"name": "k"})
    )
    assert result == {"deleted": "k"}
