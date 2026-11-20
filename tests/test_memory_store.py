"""Unit tests for the synchronous MemoryStore: pure file I/O, no HA needed."""
from __future__ import annotations

import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from custom_components.memory.const import INDEX_FILENAME
from custom_components.memory.memory_store import MemoryError, MemoryStore


@pytest.fixture
def store(tmp_path):
    return MemoryStore(str(tmp_path))


def test_empty_index(store):
    assert store.read_index() == ""


def test_save_creates_file_and_indexes(store, tmp_path):
    store.save("pet_bau", "user", "User has a dog named Bau", "Body content here.")

    assert (tmp_path / "pet_bau.md").exists()
    body = (tmp_path / "pet_bau.md").read_text()
    assert "name: pet_bau" in body
    assert "type: user" in body
    assert "description: User has a dog named Bau" in body
    assert "Body content here." in body

    index = store.read_index()
    assert "pet_bau" in index
    assert "User has a dog named Bau" in index


def test_save_dedupes_on_overwrite(store):
    store.save("a", "user", "first", "x")
    store.save("a", "user", "second", "y")
    lines = [ln for ln in store.read_index().splitlines() if ln.strip()]
    assert len(lines) == 1
    assert "second" in lines[0]
    assert "first" not in lines[0]


def test_index_is_sorted(store):
    for name in ("zebra", "apple", "mango"):
        store.save(name, "user", f"desc-{name}", f"body-{name}")
    lines = [ln for ln in store.read_index().splitlines() if ln.strip()]
    assert lines == sorted(lines)


def test_read_returns_full_body(store):
    store.save("k", "project", "d", "the body")
    out = store.read("k")
    assert "the body" in out
    assert "name: k" in out


def test_read_missing_raises(store):
    with pytest.raises(MemoryError):
        store.read("does_not_exist")


def test_delete_removes_file_and_index(store, tmp_path):
    store.save("k", "user", "d", "b")
    assert (tmp_path / "k.md").exists()
    store.delete("k")
    assert not (tmp_path / "k.md").exists()
    assert store.read_index().strip() == ""


def test_delete_missing_is_idempotent(store):
    store.delete("never_existed")
    assert store.read_index().strip() == ""


@pytest.mark.parametrize(
    "bad_name", ["Has-Dashes", "UPPER", "with space", "with.dot", "", "ñame"]
)
def test_invalid_name_rejected(store, bad_name):
    with pytest.raises(MemoryError):
        store.save(bad_name, "user", "d", "b")
    with pytest.raises(MemoryError):
        store.read(bad_name)
    with pytest.raises(MemoryError):
        store.delete(bad_name)


def test_invalid_type_rejected(store):
    with pytest.raises(MemoryError):
        store.save("k", "not_a_real_type", "d", "b")


def test_atomic_write_no_partial_files_on_error(store, tmp_path, monkeypatch):
    """If a write fails mid-stream, no partial .tmp_ file should remain."""
    real_replace = os.replace

    def boom(*args, **kwargs):
        raise OSError("simulated failure")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError):
        store.save("k", "user", "d", "b")
    monkeypatch.setattr(os, "replace", real_replace)

    leftovers = [p for p in os.listdir(tmp_path) if p.startswith(".tmp_")]
    assert leftovers == []


def test_index_follows_files_edited_by_hand(store, tmp_path):
    """The index is derived from the files, so manual edits show up on the next read."""
    store.save("a", "user", "first", "x")
    store.save("b", "user", "second", "y")

    (tmp_path / "b.md").unlink()
    (tmp_path / "a.md").write_text(
        "---\nname: a\ndescription: edited by hand\ntype: user\n---\n\nbody\n"
    )
    (tmp_path / "c.md").write_text("No frontmatter, just a note.\n")

    lines = store.read_index().splitlines()
    assert lines == [
        "- [a](a.md): edited by hand",
        "- [c](c.md): No frontmatter, just a note.",
    ]


def test_index_ignores_files_that_are_not_memories(store, tmp_path):
    store.save("a", "user", "d", "x")
    (tmp_path / "Not-A-Memory.md").write_text("x")
    (tmp_path / "notes.txt").write_text("x")
    assert store.read_index().splitlines() == ["- [a](a.md): d"]


def test_newline_in_description_stays_on_one_index_line(store, tmp_path):
    store.save("a", "user", "line one\nline two\r\n  line three", "x")
    assert store.read_index().splitlines() == ["- [a](a.md): line one line two line three"]
    assert "description: line one line two line three\n" in (tmp_path / "a.md").read_text()


def test_index_file_on_disk_matches_read_index(store, tmp_path):
    store.save("a", "user", "d", "x")
    store.save("b", "user", "e", "y")
    store.delete("a")
    assert (tmp_path / INDEX_FILENAME).read_text() == store.read_index()


def test_concurrent_save_and_delete_keep_index_in_sync(store, tmp_path):
    """Parallel tool calls land save() and delete() on executor threads at once."""
    stale = [f"stale_{i:02d}" for i in range(10)]
    fresh = [f"fresh_{i:02d}" for i in range(20)]
    for name in stale:
        store.save(name, "user", f"desc {name}", "old")

    ops = [("delete", n) for n in stale] + [("save", n) for n in fresh]
    barrier = threading.Barrier(len(ops))

    def run(op, name):
        barrier.wait()
        if op == "save":
            store.save(name, "user", f"desc {name}", "new")
        else:
            store.delete(name)

    with ThreadPoolExecutor(max_workers=len(ops)) as pool:
        for fut in [pool.submit(run, op, n) for op, n in ops]:
            fut.result()

    def names(text):
        return [
            re.match(r"- \[([a-z0-9_]+)\]\(", ln).group(1)
            for ln in text.splitlines()
            if ln.strip()
        ]

    assert names(store.read_index()) == sorted(fresh)
    assert names((tmp_path / INDEX_FILENAME).read_text()) == sorted(fresh)
