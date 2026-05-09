# Memory

**Persistent memory for Home Assistant Assist, in plain markdown.**

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Validate](https://github.com/jayzuccarelli/ha-memory/actions/workflows/validate.yml/badge.svg)](https://github.com/jayzuccarelli/ha-memory/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A lightweight memory layer for HA Assist, OpenAI, Anthropic Claude, or any conversation agent that supports tool use. **No vector DB. No embeddings. Just markdown files** you can read, edit, and version-control.

Inspired by Claude Code's `MEMORY.md` pattern.

## Why this and not the others?

Other HA memory integrations use vector embeddings, ChromaDB, or LangChain. They work — but they're heavy, opaque, and you can't debug them with `cat`.

This integration takes the opposite trade-off:

| | This (`memory`) | Vector-based (Home Mind, hass-agent-llm, …) |
|---|---|---|
| Index always in prompt | ✅ | ❌ (top-k retrieval) |
| Inspect with `cat` / `git diff` | ✅ | ❌ |
| External dependencies | None | ChromaDB / FAISS / LangChain |
| Provider-agnostic | ✅ | Mostly |
| Scales to 10,000s of memories | ❌ | ✅ |
| Resource footprint | ~0 | Non-trivial |

If you have a few dozen memories and want them transparent and predictable, use this. If you have thousands and want semantic search, use a vector-based one.

## What you get

- **Services** (exposed as tools to your LLM):
  - `memory.save` — save or overwrite a memory
  - `memory.read` — read the full body of a memory
  - `memory.delete` — delete a memory
- **Sensor**: `sensor.memory_index` — its `content` attribute holds the full `MEMORY.md` index, ready to inject into your conversation agent's system prompt template
- **A directory of markdown files** you control completely

## Install

### Via HACS (custom repository)

1. HACS → Integrations → top-right ⋮ → Custom repositories
2. Add `https://github.com/jayzuccarelli/ha-memory` as category **Integration**
3. Install **Memory**
4. Restart Home Assistant
5. Settings → Devices & Services → Add Integration → **Memory** → submit (default path is `/config/memory`)

### Manually

Copy `custom_components/memory/` into your HA `config/custom_components/`, restart, then add the integration via Settings.

## Wire it into your conversation agent

The integration's job is to expose the services + sensor. Telling the LLM *when* to call them is up to you, via the conversation agent's system-prompt / instructions field.

### For the official Anthropic integration

Settings → Devices & Services → Anthropic → Configure → Instructions:

````
You have a persistent memory of stable facts. Current memory index:

{{ state_attr('sensor.memory_index', 'content') or '(no memories yet)' }}

When the user asks to remember something, call memory.save. Use snake_case names. Pick a type: user, feedback, project, reference, or vocabulary.

When the user asks to forget something, call memory.delete with the matching name.

When an index entry isn't enough to answer, call memory.read to load the full body.
````

### For other agents (OpenAI, local LLMs)

Same pattern — inject the sensor's `content` attribute into your system prompt and instruct the model when to call the three services.

### Exposing services to Assist

Some conversation agents only see entities/scripts that you explicitly expose. If yours requires this, wrap each service in a `script:` and expose those scripts via Settings → Voice assistants → Expose.

## Memory file format

Each memory is one markdown file under your storage path:

```markdown
---
name: pet_bau
description: User has a dog named Bau
type: user
---

The user has a dog named Bau. Bau is a household member.
```

Plus an auto-maintained index (`MEMORY.md`) of one-liners pointing at each file.

## Memory types

| Type | What it's for |
|---|---|
| `user` | Facts about the user, household, family, pets |
| `feedback` | How the assistant should behave (style preferences, things to avoid) |
| `project` | State of ongoing things in the home |
| `reference` | Pointers to external systems / dashboards / docs |
| `vocabulary` | What specific words mean in this household ("all the lights" excludes the printer plug) |

## License

MIT — see [LICENSE](LICENSE).
