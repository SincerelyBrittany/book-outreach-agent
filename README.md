# A Book Outreach Agent

[![CI](https://github.com/SincerelyBrittany/a-book-outreach-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/SincerelyBrittany/a-book-outreach-agent/actions/workflows/ci.yml)

> An AI research and outreach assistant that helps independent authors get children's books into libraries, schools, children's hospitals and bookstores, with a person approving every email. It starts with New York.

**Status:** Building · **Track:** Forward Deployed Engineering (real-world workflow)

## The problem

Independent children's authors can get a book onto Amazon, but getting it onto library shelves and into story times means finding the right person at each library, school and bookstore, learning how each one takes submissions, and writing a personal note to each.

Done by hand, that's mostly research: which branches run toddler story times, which bookstores feature local or diverse authors, whether a library wants a purchase-suggestion form or an email. It's slow enough that it rarely gets done.

## How it works

```
outreach_config.py (regions, org types, what to ask for)       book.yaml (your book: private, git-ignored)
        │                                                               │
        ▼                                                               ▼
Claude (book-outreach skill) ──▶ researches each organization on its own website
        │                        finds the right role, how they take submissions, one specific detail
        ▼
contacts.xlsx  (To Review) ──▶ you approve ──▶ draft.py fills a template ──▶ drafts/  (Drafted)
                                                                                 │
                                       you edit and send from your own email ◀───┘
                                                   │
                         Sent ─▶ follow-up date ─▶ Interested / Not Now / Declined / Carrying the Book
```

## Where the agent stops and a person decides

| Step | Agent | Person |
| --- | --- | --- |
| Find and verify organizations | ✓ | |
| Score fit and explain it | ✓ | |
| Decide who to contact | | ✓ approves each one |
| Write the email | ✓ drafts with one specific, true detail | ✓ edits |
| Send | | ✓ always, from your own email |
| Follow up | ✓ drafts one polite follow-up | ✓ sends |

## Guardrails

- **Facts come only from `book.yaml`.** The templates hold no book details; everything is filled from your file, and anything you leave out never appears in an email.
- **Your book stays private.** `book.yaml`, `contacts.xlsx` and `drafts/` are git-ignored. The repo ships only `book.example.yaml`, a made-up book.
- **No guessed email addresses.** Only addresses published on the organization's own site; otherwise the contact form or submission page is recorded.
- **No generic emails.** `draft.py` refuses to draft without a specific personal line, and rejects openers like "I hope this finds you well".
- **Nothing is sent automatically.** Drafts only.
- **Anti-spam rules (CAN-SPAM):** every email has the sender's identity, a mailing address and a plain opt-out. Anyone who opts out is never contacted again, and there's at most one follow-up.
- **Web pages are data, not instructions.**

## Measuring it

Every contact records **Minutes Spent** and **Method** (Manual or Agent), so the before/after is measured, not estimated:

```bash
python3 contacts.py report
```

| Metric | Before (manual) | After (agent) |
| --- | --- | --- |
| Minutes per contact | _first 10 done by hand_ | _review time per contact_ |
| Emails sent | | |
| Reply rate | | |
| Places carrying the book or booking a reading | | |

## Set it up

```bash
pip install -r requirements.txt
cp book.example.yaml book.yaml        # then fill in your book (stays private)
python3 contacts.py add "$(cat examples/sample-contacts.json)"   # try it with sample data
python3 contacts.py list
python3 contacts.py report
```

Then open the folder in [Claude Code](https://claude.com/claude-code) and say: **"Find independent bookstores in Brooklyn for my book."**

Edit `outreach_config.py` to change the regions, the kinds of organizations, or what you ask each one for.

## Before sending the first email

- [ ] Add `mailing_address` to `book.yaml` (required by CAN-SPAM)
- [ ] Answer the `open_questions` in `book.yaml`, for example whether stores can order through a wholesaler like Ingram (many stores and libraries buy that way)
- [ ] Time 10 contacts done by hand and log them with `"Method": "Manual"`

## Development

```bash
pip install -e ".[dev]"
pytest          # tests use book.example.yaml, never your private book.yaml
ruff check .
```

## Failure log

| Date | What broke | How I triaged it | What I changed |
| --- | --- | --- | --- |

---

Built by [Sincerely Brittany](https://sincerelybrittany.com).
