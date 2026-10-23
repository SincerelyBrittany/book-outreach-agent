import json
from datetime import date
from pathlib import Path

import pytest

import book as book_info
import contacts
import draft

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = book_info.load(ROOT / "book.example.yaml")
SAMPLES = json.loads((Path(__file__).resolve().parents[1] / "examples" / "sample-contacts.json").read_text())


@pytest.fixture(autouse=True)
def temp_files(tmp_path, monkeypatch):
    monkeypatch.setattr(contacts, "PATH", tmp_path / "contacts.xlsx")
    monkeypatch.setattr(draft, "DRAFTS", tmp_path / "drafts")
    monkeypatch.setattr(draft, "HERE", tmp_path)
    monkeypatch.setattr(book_info, "load", lambda path=None: EXAMPLE)  # never read the private book.yaml in tests


def add(items, capsys):
    contacts.add([dict(i) for i in items])
    return json.loads(capsys.readouterr().out)


def test_add_and_dedupe(capsys):
    assert len(add(SAMPLES, capsys)["added"]) == 3
    again = add(SAMPLES, capsys)
    assert not again["added"] and len(again["skipped_duplicates"]) == 3


def test_same_name_different_borough_is_not_a_duplicate(capsys):
    add([{"Organization": "Story Shop", "Type": "Independent bookstore", "Borough/City": "Bronx"}], capsys)
    out = add([{"Organization": "Story Shop", "Type": "Independent bookstore", "Borough/City": "Queens"}], capsys)
    assert len(out["added"]) == 1


@pytest.mark.parametrize("bad", [{"Status": "Maybe"}, {"Type": "Zoo"}, {"Method": "Magic"}, {"Shoe": 1}])
def test_bad_values_rejected(bad, capsys):
    with pytest.raises(SystemExit):
        contacts.add({"Organization": "X", "Type": "School", **bad})


def test_sent_sets_dates(capsys):
    add([{"Organization": "X", "Type": "School", "Borough/City": "Bronx"}], capsys)
    contacts.update(2, {"Status": "Sent"}, today=date(2026, 10, 23))
    capsys.readouterr()
    row = dict(next(contacts.rows(contacts.init()[contacts.SHEET]))[1])
    assert row["Date Sent"] == "2026-10-23" and row["Follow-Up Date"] == "2026-11-02"
    assert [d["Organization"] for d in contacts.due(today=date(2026, 11, 2))] == ["X"]
    assert contacts.due(today=date(2026, 11, 1)) == []


def test_report_compares_manual_and_agent_time(capsys):
    add(SAMPLES, capsys)
    r = contacts.report()
    assert r["minutes_per_contact"] == {"manual": 15.0, "agent": 3.5}
    assert r["time_saved_pct"] == 77
    assert r["emails_sent"] == 2 and r["reply_rate_pct"] == 50 and r["interested"] == 1


@pytest.mark.parametrize("kind", list(draft.ORG_TYPES))
def test_every_template_renders_from_the_book_file(kind):
    text = draft.render(kind, {"contact_name": "Ms. Lee", "personal_line": "Your Saturday story time is lovely."})
    assert "Ms. Lee" in text and "Saturday story time" in text
    assert EXAMPLE["title"] in text and EXAMPLE["author"] in text and EXAMPLE["ages"] in text
    assert "{" not in text and "}" not in text  # no unfilled placeholders
    assert "no thanks" in text  # opt-out line
    assert "[MAILING ADDRESS]" in text  # example has no address yet, so it's flagged


def test_mailing_address_used_when_set():
    text = draft.render("School", {"personal_line": "Your spring reading week looks wonderful."},
                        book={**EXAMPLE, "mailing_address": "PO Box 1, Example, NY 10001"})
    assert "PO Box 1" in text and "[MAILING ADDRESS]" not in text


@pytest.mark.parametrize("line", ["", "   ", "I hope this finds you well!", "I came across your website."])
def test_generic_or_missing_personal_line_rejected(line):
    with pytest.raises(ValueError):
        draft.render("School", {"personal_line": line})


def test_draft_only_for_approved_contacts(capsys):
    add([{"Organization": "Demo Library", "Type": "Public library", "Borough/City": "Bronx"}], capsys)
    with pytest.raises(SystemExit):
        draft.main(["2", json.dumps({"personal_line": "Your teen book club is great."})])
    contacts.update(2, {"Status": "Approved"})
    assert draft.main(["2", json.dumps({"personal_line": "Your bilingual story time is great."})]) == 0
    row = dict(next(contacts.rows(contacts.init()[contacts.SHEET]))[1])
    assert row["Status"] == "Drafted" and row["Draft"].endswith("demo-library.md")
    assert "bilingual story time" in (draft.HERE / row["Draft"]).read_text()


def test_templates_contain_no_book_details():
    # Book facts live only in book.yaml (private) or book.example.yaml.
    for t in (ROOT / "templates").glob("*.md"):
        text = t.read_text()
        assert not __import__("re").search(r"97[89]\d{10}", text), f"{t.name} hard-codes an ISBN"
        assert EXAMPLE["title"] not in text


def test_private_book_file_is_git_ignored():
    assert "book.yaml" in (ROOT / ".gitignore").read_text().splitlines()


def test_example_book_has_required_fields():
    for key in book_info.REQUIRED:
        assert EXAMPLE[key]
