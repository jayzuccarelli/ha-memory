"""Tests for the save/delete audit trail: frontmatter provenance, events, logbook."""
from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
)

from homeassistant.components.logbook import LOGBOOK_ENTRY_MESSAGE, LOGBOOK_ENTRY_NAME
from homeassistant.core import Context
from homeassistant.helpers import device_registry as dr, llm

from custom_components.memory.const import (
    CONF_PATH,
    DOMAIN,
    EVENT_MEMORY_DELETED,
    EVENT_MEMORY_SAVED,
)
from custom_components.memory.logbook import async_describe_events
from custom_components.memory.memory_store import MemoryStore

SAVE_ARGS = {
    "name": "pet_spot",
    "type": "user",
    "description": "User has a dog named Spot",
    "content": "The user has a dog named Spot.",
}


@pytest.fixture
async def entry(hass, tmp_path):
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_PATH: str(tmp_path)}, title="Memory"
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _llm_context(context: Context | None, device_id: str | None) -> llm.LLMContext:
    return llm.LLMContext(
        platform="test",
        context=context,
        language="en",
        assistant=None,
        device_id=device_id,
    )


async def _call_tool(hass, tool_name, tool_args, llm_context):
    api = await llm.async_get_api(hass, DOMAIN, llm_context)
    tool = next(t for t in api.tools if t.name == tool_name)
    return await tool.async_call(
        hass, llm.ToolInput(tool_name=tool_name, tool_args=tool_args), llm_context
    )


def _frontmatter(text: str) -> dict[str, str]:
    lines = text.split("---\n")[1].splitlines()
    return dict(ln.split(": ", 1) for ln in lines)


async def test_tool_save_records_provenance(hass, entry, tmp_path):
    await _call_tool(
        hass, "memory_save", SAVE_ARGS, _llm_context(Context(user_id="user1"), "dev1")
    )

    text = (tmp_path / "pet_spot.md").read_text()
    front = _frontmatter(text)
    assert list(front) == [
        "name", "description", "type", "saved_by_user", "saved_by_device", "saved_at",
    ]
    assert front["saved_by_user"] == "user1"
    assert front["saved_by_device"] == "dev1"
    saved_at = datetime.fromisoformat(front["saved_at"])
    assert saved_at.utcoffset().total_seconds() == 0
    assert abs((datetime.now(UTC) - saved_at).total_seconds()) < 60
    assert text.endswith("---\n\nThe user has a dog named Spot.\n")


@pytest.mark.parametrize("context", [None, Context()])
async def test_tool_save_omits_unknown_provenance(hass, entry, tmp_path, context):
    await _call_tool(hass, "memory_save", SAVE_ARGS, _llm_context(context, None))

    front = _frontmatter((tmp_path / "pet_spot.md").read_text())
    assert list(front) == ["name", "description", "type", "saved_at"]


async def test_service_save_records_user(hass, entry, tmp_path):
    await hass.services.async_call(
        DOMAIN, "save", SAVE_ARGS, blocking=True, context=Context(user_id="user1")
    )

    front = _frontmatter((tmp_path / "pet_spot.md").read_text())
    assert front["saved_by_user"] == "user1"
    assert "saved_by_device" not in front
    assert "saved_at" in front


async def test_tool_fires_events_without_memory_text(hass, entry):
    saved = async_capture_events(hass, EVENT_MEMORY_SAVED)
    deleted = async_capture_events(hass, EVENT_MEMORY_DELETED)
    context = Context(user_id="user1")
    llm_context = _llm_context(context, "dev1")

    await _call_tool(hass, "memory_save", SAVE_ARGS, llm_context)
    await _call_tool(hass, "memory_delete", {"name": "pet_spot"}, llm_context)
    await hass.async_block_till_done()

    for events in (saved, deleted):
        assert len(events) == 1
        assert events[0].data == {
            "name": "pet_spot", "user_id": "user1", "device_id": "dev1",
        }
        assert events[0].context is context


async def test_service_fires_events_without_memory_text(hass, entry):
    saved = async_capture_events(hass, EVENT_MEMORY_SAVED)
    deleted = async_capture_events(hass, EVENT_MEMORY_DELETED)
    context = Context(user_id="user1")

    await hass.services.async_call(
        DOMAIN, "save", SAVE_ARGS, blocking=True, context=context
    )
    await hass.services.async_call(
        DOMAIN, "delete", {"name": "pet_spot"}, blocking=True, context=context
    )
    await hass.async_block_till_done()

    for events in (saved, deleted):
        assert len(events) == 1
        assert events[0].data == {
            "name": "pet_spot", "user_id": "user1", "device_id": None,
        }
        assert events[0].context.id == context.id


async def test_failed_save_fires_no_event(hass, entry):
    saved = async_capture_events(hass, EVENT_MEMORY_SAVED)
    with pytest.raises(Exception):
        await _call_tool(
            hass, "memory_save", {**SAVE_ARGS, "name": "Bad-Name"},
            _llm_context(None, None),
        )
    await hass.async_block_till_done()
    assert saved == []


async def test_logbook_describes_events(hass, entry):
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "satellite")},
        name="Kitchen Satellite",
    )
    described = {}
    async_describe_events(
        hass, lambda domain, event_type, fn: described.update({event_type: (domain, fn)})
    )
    assert set(described) == {EVENT_MEMORY_SAVED, EVENT_MEMORY_DELETED}

    def describe(event_type, device_id):
        domain, fn = described[event_type]
        assert domain == DOMAIN
        return fn(
            SimpleNamespace(
                event_type=event_type,
                data={"name": "pet_spot", "user_id": None, "device_id": device_id},
            )
        )

    assert describe(EVENT_MEMORY_SAVED, None) == {
        LOGBOOK_ENTRY_NAME: "Memory",
        LOGBOOK_ENTRY_MESSAGE: "saved: pet_spot",
    }
    assert describe(EVENT_MEMORY_DELETED, device.id) == {
        LOGBOOK_ENTRY_NAME: "Memory",
        LOGBOOK_ENTRY_MESSAGE: "deleted: pet_spot (from Kitchen Satellite)",
    }
    assert describe(EVENT_MEMORY_SAVED, "gone")[LOGBOOK_ENTRY_MESSAGE] == (
        "saved: pet_spot (from gone)"
    )


def test_index_unchanged_by_provenance(tmp_path):
    store = MemoryStore(str(tmp_path))
    store.save("a", "user", "first", "x", "user1", "dev1")
    store.save("b", "user", "second", "y")
    assert store.read_index() == "- [a](a.md): first\n- [b](b.md): second\n"
