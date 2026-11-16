"""LLM API exposing Memory tools to any conversation agent on HA.

Registering this API with `llm.async_register_api` makes the three tools
(save/read/delete) available to every conversation agent that uses HA's
standard LLM helpers: Anthropic, OpenAI, Google Generative AI, AI Tasks,
and any other integration that consumes `llm.API`. Selection happens in
the agent's config flow under "Control Home Assistant" → API.
"""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import llm
from homeassistant.util.json import JsonObjectType

from .const import DOMAIN, MAX_INDEX_CHARS, VALID_TYPES
from .memory_store import (
    MemoryError as _MemoryError,
    MemoryStore,
    async_delete,
    async_read,
    async_read_index,
    async_save,
)

_LOGGER = logging.getLogger(__name__)

_DEFAULT_TYPE = "user"


_API_PROMPT_TEMPLATE = (
    "You have access to a persistent memory of stable facts that survives across "
    "conversations. The full memory index is below. When the index entry isn't "
    "enough to answer, call memory_read with the matching name. When the user asks "
    "to remember something, call memory_save with a snake_case name and a type "
    "(user, feedback, project, reference, or vocabulary). When a fact changes, "
    "save it under the same name as the existing memory so it replaces the old "
    "one, and delete only other memories the new fact makes obsolete. When the "
    "user asks to forget something, call memory_delete.\n\n"
    "Current memory index:\n{index}"
)


def _capped_index(index: str) -> str:
    """Index trimmed to MAX_INDEX_CHARS, with a note saying how much was left out."""
    lines = [ln for ln in index.splitlines() if ln.strip()]
    kept: list[str] = []
    size = 0
    for ln in lines:
        if size + len(ln) + 1 > MAX_INDEX_CHARS:
            break
        kept.append(ln)
        size += len(ln) + 1
    omitted = len(lines) - len(kept)
    if omitted:
        _LOGGER.warning(
            "Memory index is over %d characters; %d of %d memories are not in "
            "the prompt. Delete or merge memories to bring it back under the limit",
            MAX_INDEX_CHARS, omitted, len(lines),
        )
        kept.append(f"({omitted} more memories not listed)")
    return "\n".join(kept)


class _SaveTool(llm.Tool):
    name = "memory_save"
    description = (
        "Save a fact to long-term memory. Survives across conversations. Use when "
        "the user asks to remember something, or when they share a stable fact "
        "about themselves, their household, vocabulary, or preferences."
    )
    parameters = vol.Schema(
        {
            vol.Required("name"): str,
            vol.Optional("type", default=_DEFAULT_TYPE): str,
            vol.Required("description"): str,
            vol.Required("content"): str,
        }
    )

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: llm.ToolInput,
        llm_context: llm.LLMContext,
    ) -> JsonObjectType:
        args = tool_input.tool_args
        mtype = args.get("type")
        if mtype not in VALID_TYPES:
            mtype = _DEFAULT_TYPE
        try:
            await async_save(
                hass, self._store, args["name"], mtype,
                args["description"], args["content"],
            )
        except _MemoryError as err:
            raise HomeAssistantError(str(err)) from err
        return {"saved": args["name"]}


class _ReadTool(llm.Tool):
    name = "memory_read"
    description = (
        "Read the full body of a memory by its snake_case name. Use when the "
        "one-line index entry isn't enough to answer."
    )
    parameters = vol.Schema({vol.Required("name"): str})

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: llm.ToolInput,
        llm_context: llm.LLMContext,
    ) -> JsonObjectType:
        name = tool_input.tool_args["name"]
        try:
            content = await async_read(hass, self._store, name)
        except _MemoryError as err:
            raise HomeAssistantError(str(err)) from err
        return {"name": name, "content": content}


class _DeleteTool(llm.Tool):
    name = "memory_delete"
    description = (
        "Delete a memory by its snake_case name. Use when the user asks to "
        "forget something or when a memory is no longer accurate."
    )
    parameters = vol.Schema({vol.Required("name"): str})

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: llm.ToolInput,
        llm_context: llm.LLMContext,
    ) -> JsonObjectType:
        name = tool_input.tool_args["name"]
        try:
            await async_delete(hass, self._store, name)
        except _MemoryError as err:
            raise HomeAssistantError(str(err)) from err
        return {"deleted": name}


class MemoryAPI(llm.API):
    """LLM API exposing the three memory tools and the index as prompt context."""

    def __init__(self, hass: HomeAssistant, store: MemoryStore) -> None:
        super().__init__(hass=hass, id=DOMAIN, name="Memory")
        self._store = store
        self._tools: list[llm.Tool] = [
            _SaveTool(store),
            _ReadTool(store),
            _DeleteTool(store),
        ]

    async def async_get_api_instance(
        self, llm_context: llm.LLMContext
    ) -> llm.APIInstance:
        index = _capped_index(await async_read_index(self.hass, self._store))
        return llm.APIInstance(
            api=self,
            api_prompt=_API_PROMPT_TEMPLATE.format(
                index=index or "(no memories yet)"
            ),
            llm_context=llm_context,
            tools=self._tools,
        )
