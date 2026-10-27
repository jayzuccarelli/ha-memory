# Memory

**Home Assistant's Assist remembers things between conversations, by voice or chat.**

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![Validate](https://github.com/jayzuccarelli/ha-memory/actions/workflows/validate.yml/badge.svg)](https://github.com/jayzuccarelli/ha-memory/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

<!-- demo GIF goes here -->

> "Remember that my dog's name is Spot."
>
> *Next day, new conversation:* "What's my dog's name?" → **"Spot."**

Works with Claude, OpenAI, Gemini, and other AI agents that use Home Assistant's built-in AI tools. Memories are plain markdown files you can read and edit.

## Install (about 2 minutes)

You need an AI conversation agent already set up in Home Assistant.

Tip: Ctrl-click (Cmd-click on Mac) the buttons to keep these steps open.

1. **Download.** Click the button, or open HACS and search **Memory**. Then **Download** and restart Home Assistant.

   [![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jayzuccarelli&repository=ha-memory&category=integration)

2. **Add it.** Click the button, or go to Settings → Devices & Services → **Add Integration** and search **Memory**. Then **Submit**.

   [![Add integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=memory)

3. **Turn it on for your assistant.** Settings → Devices & Services → *your AI agent* → **Configure** → tick **Memory** next to **Assist** → Submit.

That's it. Say *"Remember that…"* and it saves. Ask later and it knows.

> **Don't see a Memory checkbox?** Some agents hide it under *"Recommended model settings"* or *"Advanced options"*. Expand that section.

## Why this one

Most memory add-ons use a vector database or a separate memory engine. This one keeps a short list of memories in the assistant's prompt and stores each memory as a markdown file.

| | Memory | Retrieval-based (Home Mind, hass-agent-llm, …) |
|---|---|---|
| Setup | Install, tick a box | Extra services or databases |
| Read and edit memories | Any text editor | Usually not plain files |
| Best for | A few dozen facts | Thousands of memories |

## Reference

<details>
<summary><b>Install manually (without HACS)</b></summary>

Copy `custom_components/memory/` into your Home Assistant `config/custom_components/` and restart. Then do steps 2 and 3 above. The default storage path, `/config/memory`, is correct for most setups.

</details>

<details>
<summary><b>How it works</b></summary>

Memory registers as a native Home Assistant LLM API. When ticked, your agent gets:

- Three tools: `memory_save`, `memory_read`, `memory_delete`
- The memory index, added to the system prompt on every request

Each memory is one markdown file under your storage path:

```markdown
---
name: pet_spot
description: User has a dog named Spot
type: user
---

The user has a dog named Spot. Spot is a household member.
```

An auto-maintained `MEMORY.md` index lists one line per memory. The index is always in the prompt; the agent reads a full file only when it needs the details.

Tested with Anthropic Claude, OpenAI Conversation, Google Generative AI / Gemini, and AI Tasks. Inspired by Claude Code's `MEMORY.md` pattern.

</details>

<details>
<summary><b>Memory types</b></summary>

| Type | What it's for |
|---|---|
| `user` | Facts about the user, household, family, pets |
| `feedback` | How the assistant should behave (style preferences, things to avoid) |
| `project` | State of ongoing things in the home |
| `reference` | Pointers to external systems, dashboards, docs |
| `vocabulary` | What specific words mean in this household ("all the lights" excludes the printer plug) |

</details>

<details>
<summary><b>Use from automations and scripts</b></summary>

Plain Home Assistant services, for callers that aren't an LLM:

- `memory.save`: `name`, `type`, `description`, `content`
- `memory.read`: `name` (returns content as response data)
- `memory.delete`: `name`

The sensor `sensor.memory_index` holds the full index in its `content` attribute.

</details>

<details>
<summary><b>Inject the index by hand (skip the API)</b></summary>

If you don't tick the Memory API, add this to your agent's instructions:

```
{{ state_attr('sensor.memory_index', 'content') or '(no memories yet)' }}
```

You then also need to tell the model to use the services. Ticking the API is simpler.

</details>

## Found a bug?

[Open an issue](https://github.com/jayzuccarelli/ha-memory/issues/new?template=bug_report.yml). It takes a minute.

## License

MIT. See [LICENSE](LICENSE).
