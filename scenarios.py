"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Three scenarios are filled in to show the shape. Add or change whatever your
own criteria need — these are a starting point, not a fixed set.
"""

import re

# Five different queries that each match listings and carry a price ceiling.
# They serve criteria 3, 4 and 5, which all say "5 different queries/items".
# Mixed on purpose: some matches have a brand, some have brand = None.
FIVE_QUERIES = [
    "vintage graphic tee under $30",
    "silk slip dress in midi length under $40",
    "denim jacket under $50",
    "90s track jacket under $60",
    "black cargo pants under $35",
]


# ── pass rules ────────────────────────────────────────────────────────────────
# Each check takes one try's record and returns (passed, reason). They encode
# the criteria in criteria.md word for word.

def _session(record):
    return record["session"] or {}


def check_1(record):
    """Criterion 1: all three tools complete and a fit card comes back."""
    s = _session(record)
    if s.get("error"):
        return False, f"stopped early: {str(s['error'])[:80]}"
    card = s.get("fit_card") or ""
    if not s.get("selected_item") or not s.get("outfit_suggestion"):
        return False, "search or outfit step produced nothing"
    if not card.strip() or card.startswith("No fit card"):
        return False, f"no real fit card: {card[:60]!r}"
    return True, "search, outfit and fit card all produced output"


def check_2(record):
    """Criterion 2: an impossible query stops before suggest_outfit, with a message."""
    s = _session(record)
    if record["outfit_input_id"] is not None:
        return False, "suggest_outfit was called"
    if s.get("outfit_suggestion") or s.get("fit_card"):
        return False, "outfit or fit card was filled in"
    msg = s.get("error") or ""
    if not msg or "try" not in msg.lower():
        return False, f"no message naming what to change: {msg!r}"
    return True, f"stopped before suggest_outfit; message: {msg[:70]}"


def check_3(record):
    """Criterion 3: selected_item id == id suggest_outfit received."""
    s = _session(record)
    chosen = (s.get("selected_item") or {}).get("id")
    got = record["outfit_input_id"]
    if chosen is None or got is None:
        return False, f"selected_item id={chosen!r}, suggest_outfit received id={got!r}"
    if chosen != got:
        return False, f"selected_item id={chosen}, suggest_outfit received id={got}"
    return True, f"both ids are {chosen}"


def check_4(record):
    """Criterion 4: the fit card names the price (as a dollar figure) and platform."""
    s = _session(record)
    item = s.get("selected_item") or {}
    card = s.get("fit_card") or ""
    if not item or not card:
        return False, "no item or no fit card"
    price = f"{item['price']:g}"          # 18.0 -> "18"
    has_price = re.search(rf"\${re.escape(price)}(\.0+)?(?!\d)", card) is not None
    has_platform = item["platform"].lower() in card.lower()
    if has_price and has_platform:
        return True, f"found ${price} and {item['platform']}"
    missing = [n for n, ok in (("price", has_price), ("platform", has_platform)) if not ok]
    return False, f"card is missing {' and '.join(missing)} (item ${price} on {item['platform']})"


def check_5(record):
    """Criterion 5: every returned listing has price <= the query's ceiling."""
    s = _session(record)
    match = re.search(r"under\s*\$?\s*(\d+(?:\.\d+)?)", record["query"], re.I)
    ceiling = float(match.group(1))
    results = s.get("search_results") or []
    if not results:
        return False, "search returned nothing, so nothing was checked"
    over = [(r["title"], r["price"]) for r in results if r["price"] > ceiling]
    if over:
        return False, f"over the ${ceiling:g} ceiling: {over}"
    return True, f"all {len(results)} results are <= ${ceiling:g}"


SIZE_QUERIES = [
    "black cargo pants size W29 under $35",
    "vintage tee size M under $30",
    "jacket size M under $50",
    "denim jacket size L under $50",
    "graphic tee size L under $30",
]


def check_size(record):
    """Diagnostic: a size in the query is honoured — every result fits that size."""
    s = _session(record)
    wanted = re.search(r"size\s+(\S+)", record["query"], re.I).group(1).lower()
    results = s.get("search_results") or []
    if not results:
        return False, "search returned nothing"
    wrong = [(r["title"][:30], r["size"]) for r in results
             if wanted not in re.findall(r"[a-z0-9]+", r["size"].lower())]
    parsed = (s.get("parsed") or {}).get("size")
    if wrong:
        return False, (f"asked for size {wanted.upper()}, parsed size={parsed!r}; "
                       f"{len(wrong)} of {len(results)} results are other sizes, e.g. {wrong[:2]}")
    return True, f"parsed size={parsed!r}; all {len(results)} results fit {wanted.upper()}"


SCENARIOS = [
    {
        # A query the data can match. Criterion 1.
        "name": "matching query completes",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 1,
        "need": 4,
        "target": "a matching query completes all three tools",
        "rule": "no error, an outfit, and a real fit card",
        "check": check_1,
    },
    {
        # A query nothing can match. Criterion 2 — the branch.
        "name": "impossible query stops early",
        "query": "designer ballgown size XXS under $5",
        "wardrobe": "example",
        "criterion": 2,
        "need": 5,
        "target": "an impossible query stops before suggest_outfit",
        "rule": "suggest_outfit never called, no outfit/fit card, error names what to change",
        "check": check_2,
    },
    {
        # State. Five different queries, one per try.
        "name": "state: selected item reaches suggest_outfit",
        "query": FIVE_QUERIES[0],
        "queries": FIVE_QUERIES,
        "wardrobe": "example",
        "criterion": 3,
        "need": 5,
        "target": "selected_item id equals the id suggest_outfit receives",
        "rule": "session['selected_item']['id'] == id of new_item given to suggest_outfit",
        "check": check_3,
    },
    {
        # Fit card. Five different items, one per try.
        "name": "fit card names price and platform",
        "query": FIVE_QUERIES[0],
        "queries": FIVE_QUERIES,
        "wardrobe": "example",
        "criterion": 4,
        "need": 5,
        "target": "fit card mentions the item's $ price and platform",
        "rule": "card contains '$<price>' and the platform name (case-insensitive)",
        "check": check_4,
    },
    {
        # Price ceiling. Five different queries, one per try.
        "name": "price ceiling holds for every result",
        "query": FIVE_QUERIES[0],
        "queries": FIVE_QUERIES,
        "wardrobe": "example",
        "criterion": 5,
        "need": 5,
        "target": "every search result has price <= the ceiling",
        "rule": "every listing in session['search_results'] has price <= X",
        "check": check_5,
    },
    {
        # A user with nothing saved. One of unit 4's three failure modes.
        "name": "empty wardrobe",
        "query": "denim jacket under $50",
        "wardrobe": "empty",
        "criterion": None,
    },
    {
        # Diagnostic, not one of the five criteria: does a size survive parsing
        # when a price follows it? Found while reading the before-run traces.
        "name": "size is honoured (size before price)",
        "query": SIZE_QUERIES[0],
        "queries": SIZE_QUERIES,
        "wardrobe": "example",
        "criterion": None,
        "need": 5,
        "target": "every result fits the requested size",
        "rule": "requested size is a whole token of every listing's size",
        "check": check_size,
    },
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems
