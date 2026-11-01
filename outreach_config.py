"""Who to reach out to, and what to offer each kind of organization. Edit to change the campaign."""

CAMPAIGN = "New York picture-book outreach"

# Start small and local; widen once replies show what works.
REGIONS = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]

# Organization types, in the order the skill should work through them.
# ask:      what we're asking for (shapes the template)
# who:      the role to look for on their website
# template: file in templates/
ORG_TYPES = {
    "Black-owned bookstore": {
        "ask": "Stock the book or host a story time",
        "who": "owner, buyer or events coordinator",
        "template": "bookstore.md",
    },
    "Independent bookstore": {
        "ask": "Stock the book (children's section) or host a story time",
        "who": "children's book buyer or events coordinator",
        "template": "bookstore.md",
    },
    "Children's library": {
        "ask": "Add the book to the children's collection, or book a story-time reading",
        "who": "children's librarian or youth services coordinator (children's rooms, children's centers)",
        "template": "library.md",
    },
    "Public library": {
        "ask": "Add the book to the collection, or book a story-time reading",
        "who": "children's librarian, branch manager, or the system's purchase-suggestion form",
        "template": "library.md",
    },
    "School": {
        "ask": "An author read-aloud for pre-K to 2nd grade, or adding the book to the school library",
        "who": "school librarian, PTA/PTO, or early-grades coordinator",
        "template": "school.md",
    },
    "Children's hospital": {
        "ask": "A donated-copy program or a reading for patients",
        "who": "child life department or volunteer services",
        "template": "childrens_hospital.md",
    },
}

STATUSES = [
    "To Review",       # found and checked, not yet approved
    "Approved",        # you want to contact them; draft gets written
    "Drafted",         # draft ready for your edits
    "Sent",            # you sent it (from your own email)
    "Interested",      # positive reply
    "Not Now",         # polite no for now; follow up later
    "Declined",        # no
    "No Reply",        # nothing after the follow-up
    "Carrying the Book",  # outcome: stocked, added to collection, or booked an event
    "Skipped",         # decided not to contact
]

FOLLOW_UP_DAYS = 10  # suggested gap before one polite follow-up
