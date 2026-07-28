"""
Atomic persistence (Section: Persistence & Pipeline Integrity).

Every staging write follows: write to a temp file in the SAME directory ->
fsync -> compute SHA-256 -> atomic os.replace() rename. A reader never sees a
torn write; a crash mid-write leaves the previous file intact and only a
stray .tmp (which we clean up).
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import tempfile
from typing import Any, Iterable, Union

PathLike = Union[str, "os.PathLike[str]", pathlib.Path]


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write_bytes(path: PathLike, data: bytes) -> str:
    """Atomically write `data` to `path`. Returns the SHA-256 of the content."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    digest = sha256_hex(data)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent),
                               prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)          # atomic on POSIX and Windows
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return digest


def atomic_write_text(path: PathLike, text: str, encoding: str = "utf-8") -> str:
    return atomic_write_bytes(path, text.encode(encoding))


def atomic_write_json(path: PathLike, obj: Any, *, indent: int = 2) -> str:
    return atomic_write_text(path, json.dumps(obj, indent=indent, default=str))


def atomic_write_jsonl(path: PathLike, records: Iterable[Any]) -> str:
    body = "".join(json.dumps(r, default=str) + "\n" for r in records)
    return atomic_write_text(path, body)


def read_jsonl(path: PathLike) -> list:
    text = pathlib.Path(path).read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]
