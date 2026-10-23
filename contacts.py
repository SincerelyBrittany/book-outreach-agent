#!/usr/bin/env python3
"""The outreach tracker: reads and writes contacts.xlsx, and reports results.

Usage:
  contacts.py init
  contacts.py add '<json object or array>'    # keys = column names; skips duplicates
  contacts.py list [--status Approved] [--type "Public library"] [--json]
  contacts.py update <row> '<json object>'    # row = spreadsheet row number
  contacts.py due                             # sent, no reply, follow-up date reached
  contacts.py report                          # before/after time and outcomes
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from outreach_config import FOLLOW_UP_DAYS, ORG_TYPES, STATUSES

PATH = Path(__file__).resolve().parent / "contacts.xlsx"
SHEET = "Contacts"
COLUMNS = [
    "Date Found", "Organization", "Type", "Borough/City", "Contact Name", "Role", "Email",
    "Contact Form", "Website", "How They Take Submissions", "Fit (1-5)", "Fit Note", "Source",
    "Status", "Draft", "Date Sent", "Follow-Up Date", "Reply Notes", "Minutes Spent", "Method",
    "Notes",
]
WIDTHS = [12, 30, 20, 14, 20, 22, 28, 30, 30, 34, 8, 44, 30, 14, 34, 12, 13, 34, 9, 10, 34]
METHODS = ["Manual", "Agent"]
REPLIED = {"Interested", "Not Now", "Declined", "Carrying the Book"}
CONTACTED = REPLIED | {"Sent", "No Reply"}


def init():
    if PATH.exists():
        return load_workbook(PATH)
    wb = Workbook()
    ws = wb.active
    ws.title = SHEET
    ws.append(COLUMNS)
    for i, cell in enumerate(ws[1]):
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="27313F")
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        ws.column_dimensions[cell.column_letter].width = WIDTHS[i]
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:{ws.cell(1, len(COLUMNS)).column_letter}1"
    for name, options in (("Status", STATUSES), ("Type", list(ORG_TYPES)), ("Method", METHODS)):
        col = ws.cell(1, COLUMNS.index(name) + 1).column_letter
        dv = DataValidation(type="list", formula1='"' + ",".join(options) + '"', allow_blank=True)
        dv.add(f"{col}2:{col}5000")
        ws.add_data_validation(dv)
    wb.save(PATH)
    return wb


def rows(ws):
    for r in range(2, ws.max_row + 1):
        vals = [ws.cell(r, c + 1).value for c in range(len(COLUMNS))]
        if any(v not in (None, "") for v in vals):
            yield r, dict(zip(COLUMNS, vals))


def norm(s) -> str:
    return " ".join(str(s or "").lower().split())


def find(ws, organization=None, city=None, email=None):
    for r, row in rows(ws):
        if email and norm(row["Email"]) == norm(email):
            return r
        if organization and norm(row["Organization"]) == norm(organization) and norm(row["Borough/City"]) == norm(city):
            return r
    return None


def _check(item: dict) -> None:
    bad = set(item) - set(COLUMNS)
    if bad:
        sys.exit(f"Unknown columns: {sorted(bad)}")
    checks = (("Status", STATUSES), ("Type", list(ORG_TYPES)), ("Method", METHODS))
    for key, allowed in checks:
        if item.get(key) not in (None, "") and item[key] not in allowed:
            sys.exit(f"{key} must be one of {allowed}")


def add(payload):
    wb = init()
    ws = wb[SHEET]
    items = payload if isinstance(payload, list) else [payload]
    added, skipped = [], []
    for item in items:
        _check(item)
        dup = find(ws, item.get("Organization"), item.get("Borough/City"), item.get("Email"))
        if dup:
            skipped.append({"row": dup, "Organization": item.get("Organization")})
            continue
        item.setdefault("Date Found", date.today().isoformat())
        item.setdefault("Status", "To Review")
        item.setdefault("Method", "Agent")
        ws.append([item.get(c) for c in COLUMNS])
        r = ws.max_row
        for c in range(1, len(COLUMNS) + 1):
            ws.cell(r, c).alignment = Alignment(wrap_text=True, vertical="top")
        added.append({"row": r, "Organization": item.get("Organization")})
    wb.save(PATH)
    print(json.dumps({"added": added, "skipped_duplicates": skipped}, indent=2))


def update(row: int, changes: dict, today: date | None = None):
    today = today or date.today()
    wb = init()
    ws = wb[SHEET]
    _check(changes)
    for k, v in changes.items():
        ws.cell(row, COLUMNS.index(k) + 1).value = v
    cell = lambda name: ws.cell(row, COLUMNS.index(name) + 1)  # noqa: E731
    if changes.get("Status") == "Sent":
        if not cell("Date Sent").value:
            cell("Date Sent").value = today.isoformat()
        if not cell("Follow-Up Date").value:
            cell("Follow-Up Date").value = (today + timedelta(days=FOLLOW_UP_DAYS)).isoformat()
    wb.save(PATH)
    print(json.dumps({"row": row, **{c: ws.cell(row, i + 1).value for i, c in enumerate(COLUMNS)}}, indent=2, default=str))


def due(today: date | None = None) -> list[dict]:
    today = (today or date.today()).isoformat()
    ws = init()[SHEET]
    return [
        {"row": r, **row}
        for r, row in rows(ws)
        if row["Status"] == "Sent" and row["Follow-Up Date"] and str(row["Follow-Up Date"]) <= today
    ]


def report() -> dict:
    """The numbers for the business case: time per contact before vs after, and outcomes."""
    ws = init()[SHEET]
    all_rows = [row for _, row in rows(ws)]

    def avg_minutes(method):
        mins = [float(r["Minutes Spent"]) for r in all_rows if r["Method"] == method and r["Minutes Spent"] not in (None, "")]
        return round(sum(mins) / len(mins), 1) if mins else None

    manual, agent = avg_minutes("Manual"), avg_minutes("Agent")
    contacted = [r for r in all_rows if r["Status"] in CONTACTED]
    replied = [r for r in contacted if r["Status"] in REPLIED]
    by_status = {s: sum(1 for r in all_rows if r["Status"] == s) for s in STATUSES}
    by_type = {t: sum(1 for r in all_rows if r["Type"] == t) for t in ORG_TYPES}
    return {
        "contacts": len(all_rows),
        "minutes_per_contact": {"manual": manual, "agent": agent},
        "time_saved_pct": round(100 * (manual - agent) / manual) if manual and agent is not None else None,
        "emails_sent": len(contacted),
        "reply_rate_pct": round(100 * len(replied) / len(contacted)) if contacted else None,
        "interested": by_status["Interested"],
        "carrying_the_book": by_status["Carrying the Book"],
        "by_status": by_status,
        "by_type": by_type,
    }


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    cmd = args[0]
    if cmd == "init":
        init()
        print(f"Tracker ready: {PATH}")
    elif cmd == "add":
        add(json.loads(args[1]))
    elif cmd == "update":
        update(int(args[1]), json.loads(args[2]))
    elif cmd == "list":
        ws = init()[SHEET]
        status = args[args.index("--status") + 1] if "--status" in args else None
        kind = args[args.index("--type") + 1] if "--type" in args else None
        out = [{"row": r, **row} for r, row in rows(ws) if (not status or row["Status"] == status) and (not kind or row["Type"] == kind)]
        if "--json" in args:
            print(json.dumps(out, indent=2, default=str))
        else:
            for o in out:
                where = o["Borough/City"] or "?"
                print(f'{o["row"]:>4}  {o["Status"] or "":<17} {o["Fit (1-5)"] or "-"}  [{o["Type"]}] {o["Organization"]} ({where})')
            print(f"{len(out)} contact(s)")
    elif cmd == "due":
        print(json.dumps(due(), indent=2, default=str))
    elif cmd == "report":
        print(json.dumps(report(), indent=2))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
