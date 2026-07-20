# Memory

**Persistent memory for Home Assistant Assist, in plain markdown.**

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Validate](https://github.com/jayzuccarelli/ha-memory/actions/workflows/validate.yml/badge.svg)](https://github.com/jayzuccarelli/ha-memory/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A lightweight memory layer for HA Assist, OpenAI, Anthropic Claude, or any conversation agent that supports tool use. **No vector DB. No embeddings. Just markdown files** you can read, edit, and version-control.

Inspired by Claude Code's `MEMORY.md` pattern.

## Why this and not the others?

Other HA memory integrations retrieve semantically, backed by embeddings or a
dedicated memory engine. They work, and they scale further than this does. The
trade-off is that they're heavier, and you can't debug them with `cat`.

This integration takes the opposite trade-off:

| | This (`memory`) | Retrieval-based (Home Mind, hass-agent-llm, …) |
|---|---|---|
| Index always in prompt | ✅ | ❌ (top-k retrieval) |
| Inspect with `cat` / `git diff` | ✅ | ❌ |
| External dependencies | None | Varies (Shodh, ChromaDB, …) |
| Provider-agnostic | ✅ | Mostly |
| Scales to 10,000s of memories | ❌ | ✅ |
| Resource footprint | ~0 | Non-trivial |

If you have a few dozen memories and want them transparent and predictable, use this. If you have thousands and want semantic search, use a retrieval-based one.

## What you get

- **Services** (exposed as tools to your LLM):
  - `memory.save`: save or overwrite a memory
  - `memory.read`: read the full body of a memory
  - `memory.delete`: delete a memory
- **Sensor**: `sensor.memory_index`, whose `content` attribute holds the full `MEMORY.md` index, ready to inject into your conversation agent's system prompt template
- **A directory of markdown files** you control completely

## Quick start

Once your conversation agent (Claude / OpenAI / Gemini / etc.) is set up in HA:

1. Install Memory (instructions below) and restart HA.
2. **Settings → Devices & Services → Add Integration → "Memory"**, submit (default path is fine).
3. **Settings → Devices & Services → *your conversation agent* → Configure** → tick the **Memory** checkbox in the API list (next to the existing "Assist" one) → submit.
4. Talk to your assistant: *"Remember that my dog's name is Bau."*
5. New conversation, days later: *"What's my dog's name?"* → it remembers.

That's it. No prompt templates, no script wrappers, no exposure step.

## Install

### Via HACS (custom repository, until HACS default PR merges)

1. HACS → Integrations → top-right ⋮ → Custom repositories
2. Add `https://github.com/jayzuccarelli/ha-memory` as category **Integration**
3. Install **Memory**
4. Restart Home Assistant

### Manually

Copy `custom_components/memory/` into your HA `config/custom_components/`, restart.

### Add the integration

After install + restart: **Settings → Devices & Services → Add Integration → search "Memory" → submit**. The default storage path `/config/memory` is correct for most setups.

## Wire it into your conversation agent

Memory registers itself as a native HA LLM API. In your conversation agent's config, you'll see **Memory** appear in the API list (alongside the built-in **Assist**). Tick it.

That's all the wiring. The agent now sees:

- The three tools (`memory_save`, `memory_read`, `memory_delete`) as native LLM tools
- The current memory index, auto-injected into the system prompt, no template editing needed

Tested with **Anthropic Claude**, **OpenAI Conversation**, **Google Generative AI / Gemini**, and **AI Tasks**.

> **Tip:** if your agent's UI shows a single "Assist" checkbox and no API list, you may need to expand the section labeled something like *"Recommended model settings"* or *"Advanced options"*, since providers vary slightly in how they surface the API picker.

### Driving memory from automations / scripts

If you want a non-LLM caller (an automation, AI Task service call, or bespoke script) to read or write memories, the integration also exposes plain HA services:

- `memory.save`: `name`, `type`, `description`, `content`
- `memory.read`: `name` (returns content as response data)
- `memory.delete`: `name`

### Manual prompt injection (only if you skip the API)

If you'd rather not select the Memory API and want to inject the index into your agent's instructions field by hand:

```
{{ state_attr('sensor.memory_index', 'content') or '(no memories yet)' }}
```

You'd then also need to instruct the LLM to use the services. The native API path is much cleaner, and recommended unless you have a specific reason.

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

MIT, see [LICENSE](LICENSE).
