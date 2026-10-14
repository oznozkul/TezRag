"""Small I/O helpers: JSONL, atomic + write-once writes, hashing, logging."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable, Iterator


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def read_jsonl(path: str | os.PathLike) -> Iterator[dict]:
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def _write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def _jsonl_text(rows: Iterable[dict]) -> str:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)


def write_jsonl(path: str | os.PathLike, rows: Iterable[dict]) -> None:
    _write_atomic(Path(path), _jsonl_text(rows))


def write_json(path: str | os.PathLike, obj: Any) -> None:
    _write_atomic(Path(path), json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def write_text(path: str | os.PathLike, text: str) -> None:
    _write_atomic(Path(path), text)


class WriteOnceError(FileExistsError):
    pass


def write_once_jsonl(path: str | os.PathLike, rows: Iterable[dict]) -> None:
    """Create a file exactly once. Refuses to overwrite (the split must never change silently)."""
    p = Path(path)
    if p.exists():
        raise WriteOnceError(
            f"{p} already exists and is write-once. Delete it by hand if you really mean to regenerate."
        )
    _write_atomic(p, _jsonl_text(rows))


def write_once_json(path: str | os.PathLike, obj: Any) -> None:
    p = Path(path)
    if p.exists():
        raise WriteOnceError(f"{p} already exists and is write-once.")
    _write_atomic(p, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def append_jsonl(f, row: dict) -> None:
    """Append one record to an open file and flush, so a crash loses at most the in-flight record."""
    f.write(json.dumps(row, ensure_ascii=False) + "\n")
    f.flush()
    os.fsync(f.fileno())


def sha256_file(path: str | os.PathLike, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while b := f.read(chunk):
            h.update(b)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()
