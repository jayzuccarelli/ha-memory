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

`Memory` registers itself as a native HA LLM API, so any conversation agent that uses HA's standard LLM helpers can pick it up without you editing prompts.

### Recommended: select the API in your conversation agent (zero prompt edits)

Settings → Devices & Services → *your conversation agent* → Configure → **Control Home Assistant API** → choose **Memory** (or "Assist + Memory").

That's it. The current memory index is automatically injected into the system prompt, and the three tools (`memory_save`, `memory_read`, `memory_delete`) are exposed to the LLM. Works the same for:

- Anthropic Claude
- OpenAI Conversation
- Google Generative AI / Gemini
- AI Tasks
- Any custom integration that consumes `homeassistant.helpers.llm`

### Alternative: use the services directly

If you want to drive memory from automations, scripts, or AI Task service calls, the integration also exposes `memory.save`, `memory.read`, and `memory.delete` as plain HA services with full schemas.

### Optional: inject the index into a custom prompt

If you don't select the API and instead want to template the index into your own instructions field manually:

```
{{ state_attr('sensor.memory_index', 'content') or '(no memories yet)' }}
```

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
