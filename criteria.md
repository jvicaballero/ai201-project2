# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
<!-- Why 4 of 5 and not 5 of 5? Something about your search, probably —
     "my search is a plain keyword match and some phrasings will miss" is a
     real answer. -->

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
<!-- Why is 5 of 5 reasonable here when criterion 1 isn't? What's different
     about this path? -->

---

## 3. Something about state

For 5 different queries that each match at least one listing, the `id` field
of `session["selected_item"]` equals the `id` field of the `new_item` dict
`suggest_outfit` actually receives — 5 of 5 tries.

**Why this target:** `run_agent` passes `session["selected_item"]` by
reference into `suggest_outfit` and `create_fit_card` — there's no copy, no
serialization step, and nothing deterministic that could change the `id`
between the two calls. If this criterion ever fails it means a later edit
introduced a second lookup, a re-filter, or a reassignment of
`session["selected_item"]` between the search branch and the outfit call —
not a tool bug. There's no randomness in this path, so 5 of 5 is the only
target that makes sense; anything less would mean the loop sometimes hands
one tool a different item than the one search found, and that's not an
acceptable rate for anything.

---

## 4. Something about the fit card

For 5 different matching items run through the full loop once each, every one
of the 5 fit cards mentions its item's price (as a dollar figure) and its
platform name at least once — 5 of 5 tries.

**Why this target:** `create_fit_card`'s prompt explicitly instructs the model
to mention the item and its price and platform once each, but nothing in the
tool *enforces* that — it's a request to the model, not a template with
required slots, so a dropped price or platform is a realistic failure, not a
theoretical one. Unlike the wording or tone of the caption, price and platform
are facts that came from the listing dict itself, not generated text, so
there's no reason variation between runs should ever cost a card its only two
required facts. That's why this one is 5 of 5 and not a softer target like
criterion 1 — the content being checked isn't the part of the output that's
supposed to vary.

---

## 5. Your choice

For 5 queries that each include a price ceiling (`"under $X"`), every listing
dict in `search_listings`'s returned list has `price <= X` — across all
results returned, not just the first one — 5 of 5 tries.

**Why this target:** The data has 40 listings ranging from $12 to $75, so a
ceiling that's off by one comparison operator (`<` vs `<=`, or filtering
before scoring instead of after) would still return *something* most of the
time — it just might include a $38 item for a $35 ceiling, and that's the
kind of bug a spot-check of the top result would never catch, since the first
result is usually the cheapest well-matched one anyway. Checking every item in
the returned list, not just `selected_item`, is what actually exercises the
filter. This step involves no model call and no randomness, so 5 of 5 is the
right bar — there's no reason a deterministic filter over a fixed price field
should ever let one through.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
