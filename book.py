"""Load the book being pitched: book.yaml (private, git-ignored), or the example if it's missing."""

from __future__ import annotations

from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REQUIRED = ["title", "author", "ages", "pitch", "editions", "website", "author_email"]


def book_path() -> Path:
    real = HERE / "book.yaml"
    return real if real.exists() else HERE / "book.example.yaml"


def load(path: Path | None = None) -> dict:
    data = yaml.safe_load((path or book_path()).read_text()) or {}
    missing = [k for k in REQUIRED if not data.get(k)]
    if missing:
        raise ValueError(f"{(path or book_path()).name} is missing: {', '.join(missing)}")
    data.setdefault("extra_lines", [])
    data.setdefault("offers", [])
    data.setdefault("mailing_address", "")
    return data


def isbn_line(book: dict) -> str:
    parts = [f"{e['format']}: ISBN {e['isbn']}" for e in book["editions"] if e.get("isbn")]
    return " · ".join(parts)
