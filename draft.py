#!/usr/bin/env python3
"""Fill an outreach template for one contact and save the draft for review.

Usage:
  draft.py <row> '{"contact_name": "Ms. Lee", "personal_line": "...", "offer_line": "..."}'

- personal_line is required: one specific, true sentence about this organization
  (an event they ran, a booklist they published, their mission). No generic openers.
- offer_line is optional: what the author can offer this organization.
The draft is saved to drafts/<type>/<organization>.md and the contact's Status becomes "Drafted".
Nothing is ever sent from here.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import book as book_info
import contacts
from outreach_config import ORG_TYPES

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE / "templates"
DRAFTS = HERE / "drafts"
GENERIC = re.compile(r"^(i hope (this|you)|hope you|i came across|i wanted to reach out|my name is)", re.I)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "contact"


def render(org_type: str, fields: dict, book: dict | None = None) -> str:
    personal = (fields.get("personal_line") or "").strip()
    if not personal:
        raise ValueError("personal_line is required: one specific, true sentence about this organization.")
    if GENERIC.match(personal):
        raise ValueError("personal_line reads as a generic opener; say something specific to them.")
    book = book or book_info.load()
    details = {
        "title": book["title"],
        "author": book["author"],
        "ages": book["ages"],
        "pitch": " ".join(str(book["pitch"]).split()),
        "extra": " ".join(book.get("extra_lines") or []),
        "isbn_line": book_info.isbn_line(book),
        "website": book["website"],
        "author_email": book["author_email"],
        "mailing_address": book.get("mailing_address") or "[MAILING ADDRESS]",
    }
    footer = (TEMPLATES / "_footer.md").read_text().strip().format(**details)
    template = (TEMPLATES / ORG_TYPES[org_type]["template"]).read_text()
    text = template.format(
        contact_name=(fields.get("contact_name") or "there").strip(),
        personal_line=personal,
        offer_line=(fields.get("offer_line") or "").strip(),
        footer=footer,
        **details,
    )
    return re.sub(r"[ \t]+\n", "\n", text).replace("\n\n\n", "\n\n")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    row, fields = int(argv[0]), json.loads(argv[1])
    ws = contacts.init()[contacts.SHEET]
    record = {c: ws.cell(row, i + 1).value for i, c in enumerate(contacts.COLUMNS)}
    if not record.get("Organization"):
        sys.exit(f"Row {row} has no contact.")
    if record.get("Status") not in ("Approved", "Drafted"):
        sys.exit(f"Row {row} is '{record.get('Status')}'. Only Approved contacts get drafts.")
    text = render(record["Type"], fields)
    path = DRAFTS / slug(record["Type"]) / f"{slug(record['Organization'])}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    contacts.update(row, {"Status": "Drafted", "Draft": str(path.relative_to(HERE))})
    if "[MAILING ADDRESS]" in text:
        print("Note: add mailing_address to book.yaml before sending (CAN-SPAM).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
