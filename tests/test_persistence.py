from __future__ import annotations

import hashlib

from cosmos import persistence


def test_atomic_write_bytes_integrity_and_hash(tmp_path):
    target = tmp_path / "sub" / "file.bin"
    data = b"cosmos-savant-\x00\x01\x02"
    digest = persistence.atomic_write_bytes(target, data)
    assert target.read_bytes() == data
    assert digest == hashlib.sha256(data).hexdigest()


def test_no_temp_file_left_behind(tmp_path):
    # dedicated write dir so the assertion isn't confused by the isolate_data
    # fixture's tmp data/ tree
    wdir = tmp_path / "writedir"
    target = wdir / "file.txt"
    persistence.atomic_write_text(target, "hello")
    leftovers = [p.name for p in wdir.iterdir() if p.name != "file.txt"]
    assert leftovers == []  # no stray .tmp remnant from the atomic rename


def test_atomic_overwrite_replaces_content(tmp_path):
    target = tmp_path / "f.json"
    persistence.atomic_write_json(target, {"v": 1})
    persistence.atomic_write_json(target, {"v": 2})
    import json
    assert json.loads(target.read_text())["v"] == 2


def test_jsonl_roundtrip(tmp_path):
    target = tmp_path / "rows.jsonl"
    rows = [{"a": 1}, {"b": 2}, {"c": [3, 4]}]
    persistence.atomic_write_jsonl(target, rows)
    assert persistence.read_jsonl(target) == rows
