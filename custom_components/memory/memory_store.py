"""File-backed memory store. All disk I/O is offloaded to the executor."""
from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass

from homeassistant.core import HomeAssistant

from .const import INDEX_FILENAME, VALID_TYPES

_NAME_RE = re.compile(r"^[a-z0-9_]+$")


class MemoryError(Exception):
    """Raised for invalid memory operations."""


@dataclass
class MemoryStore:
    """Synchronous file ops; wrap in async via hass.async_add_executor_job."""

    path: str

    def __post_init__(self) -> None:
        os.makedirs(self.path, exist_ok=True)

    @property
    def index_path(self) -> str:
        return os.path.join(self.path, INDEX_FILENAME)

    def _validate_name(self, name: str) -> None:
        if not _NAME_RE.match(name):
            raise MemoryError(f"invalid name {name!r}: a-z, 0-9, _ only")

    def _atomic_write(self, target: str, content: str) -> None:
        fd, tmp = tempfile.mkstemp(dir=self.path, prefix=".tmp_", suffix=".md")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(content)
            os.replace(tmp, target)
        except Exception:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

    def _read_index_lines(self) -> list[str]:
        if not os.path.exists(self.index_path):
            return []
        with open(self.index_path) as f:
            return [ln.rstrip("\n") for ln in f if ln.strip()]

    def _write_index_lines(self, lines: list[str]) -> None:
        body = "\n".join(lines) + ("\n" if lines else "")
        self._atomic_write(self.index_path, body)

    @staticmethod
    def _index_line(name: str, description: str) -> str:
        return f"- [{name}]({name}.md) — {description}"

    def read_index(self) -> str:
        if not os.path.exists(self.index_path):
            return ""
        with open(self.index_path) as f:
            return f.read()

    def read(self, name: str) -> str:
        self._validate_name(name)
        target = os.path.join(self.path, f"{name}.md")
        if not os.path.exists(target):
            raise MemoryError(f"not found: {name}")
        with open(target) as f:
            return f.read()

    def save(self, name: str, mtype: str, description: str, content: str) -> None:
        self._validate_name(name)
        if mtype not in VALID_TYPES:
            raise MemoryError(f"invalid type {mtype!r}; valid: {VALID_TYPES}")
        body = (
            f"---\nname: {name}\ndescription: {description}\ntype: {mtype}\n---\n\n"
            f"{content}\n"
        )
        self._atomic_write(os.path.join(self.path, f"{name}.md"), body)
        lines = [ln for ln in self._read_index_lines() if not ln.startswith(f"- [{name}](")]
        lines.append(self._index_line(name, description))
        lines.sort()
        self._write_index_lines(lines)

    def delete(self, name: str) -> None:
        self._validate_name(name)
        target = os.path.join(self.path, f"{name}.md")
        if os.path.exists(target):
            os.unlink(target)
        lines = [ln for ln in self._read_index_lines() if not ln.startswith(f"- [{name}](")]
        self._write_index_lines(lines)


async def async_read_index(hass: HomeAssistant, store: MemoryStore) -> str:
    return await hass.async_add_executor_job(store.read_index)


async def async_read(hass: HomeAssistant, store: MemoryStore, name: str) -> str:
    return await hass.async_add_executor_job(store.read, name)


async def async_save(
    hass: HomeAssistant,
    store: MemoryStore,
    name: str,
    mtype: str,
    description: str,
    content: str,
) -> None:
    await hass.async_add_executor_job(store.save, name, mtype, description, content)


async def async_delete(hass: HomeAssistant, store: MemoryStore, name: str) -> None:
    await hass.async_add_executor_job(store.delete, name)
