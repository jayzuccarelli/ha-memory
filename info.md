# Memory

**Persistent memory for Home Assistant Assist, in plain markdown.** No vector DB, no embeddings, just files you can read, edit, and version-control.

Inspired by Claude Code's `MEMORY.md` pattern. Provider-agnostic: works with any conversation agent that supports tools (Anthropic Claude, OpenAI, local LLMs).

## Why

LLM-backed Home Assistant assistants forget everything between conversations. Existing solutions retrieve semantically, backed by embeddings or a dedicated memory engine: heavier, and hard to debug by hand.

This integration takes the opposite approach: a small index file is *always* injected into the system prompt, and individual memories are markdown files the LLM can read on demand via a tool call. Predictable, transparent, debuggable with `cat`.

## What you get

- Three services: `memory.save`, `memory.read`, `memory.delete`, exposed to your conversation agent as tools
- One sensor: `sensor.memory_index`, whose `content` attribute holds your full memory index, ready to inject into a prompt template
- A directory of plain markdown files you can read, edit, and back up

See the [README](https://github.com/jayzuccarelli/ha-memory) for full setup instructions.
