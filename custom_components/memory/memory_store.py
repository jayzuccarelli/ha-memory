"""File-backed memory store. All disk I/O is offloaded to the executor."""
from __future__ import annotations

import os
import re
import tempfile
import threading
from dataclasses import dataclass, field

from homeassistant.core import HomeAssistant

from .const import INDEX_FILENAME, VALID_TYPES

_NAME_RE = re.compile(r"^[a-z0-9_]+$")
_DESCRIPTION_PREFIX = "description:"


class MemoryError(Exception):
    """Raised for invalid memory operations."""


@dataclass
class MemoryStore:
    """Synchronous file ops; wrap in async via hass.async_add_executor_job."""

    path: str
    # save()/delete() run on executor threads; this keeps MEMORY.md on disk
    # consistent when parallel tool calls land at once.
    _lock: threading.Lock = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        os.makedirs(self.path, exist_ok=True)
        self._lock = threading.Lock()

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

    @staticmethod
    def _index_line(name: str, description: str) -> str:
        return f"- [{name}]({name}.md): {description}"

    @staticmethod
    def _file_description(path: str) -> str:
        """Description from a memory file's frontmatter, or its first body line."""
        try:
            with open(path) as f:
                lines = f.read().splitlines()
        except OSError:
            return ""
        body_start = 0
        if lines and lines[0].strip() == "---":
            for i, ln in enumerate(lines[1:], start=1):
                if ln.strip() == "---":
                    body_start = i + 1
                    break
                if ln.startswith(_DESCRIPTION_PREFIX):
                    return ln[len(_DESCRIPTION_PREFIX):].strip()
        for ln in lines[body_start:]:
            if ln.strip():
                return ln.strip()[:120]
        return ""

    def _build_index(self) -> str:
        """Index derived from the memory files on disk, one sorted line each."""
        lines = []
        for filename in os.listdir(self.path):
            name, ext = os.path.splitext(filename)
            if ext != ".md" or filename == INDEX_FILENAME or not _NAME_RE.match(name):
                continue
            description = self._file_description(os.path.join(self.path, filename))
            lines.append(self._index_line(name, description))
        lines.sort()
        return "\n".join(lines) + ("\n" if lines else "")

    def read_index(self) -> str:
        return self._build_index()

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
        description = " ".join(description.split())
        body = (
            f"---\nname: {name}\ndescription: {description}\ntype: {mtype}\n---\n\n"
            f"{content}\n"
        )
        with self._lock:
            self._atomic_write(os.path.join(self.path, f"{name}.md"), body)
            self._atomic_write(self.index_path, self._build_index())

    def delete(self, name: str) -> None:
        self._validate_name(name)
        target = os.path.join(self.path, f"{name}.md")
        with self._lock:
            if os.path.exists(target):
                os.unlink(target)
            self._atomic_write(self.index_path, self._build_index())


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
