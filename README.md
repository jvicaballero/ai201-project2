# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

A user types a plain-language query describing what they're thrifting for —
e.g. `vintage graphic tee under $30` or `90s track jacket in size M` — and
optionally runs with `--empty-wardrobe` to simulate a new user. FitFindr
searches the mock listings data for a match, picks the best one, and returns
three things: the matched listing (title, price, platform), an outfit
suggestion that pairs it with the user's existing wardrobe (or general styling
advice if they have none saved), and a short social-style caption ("fit card")
for the find. If nothing in the data matches the query, it returns a message
naming what to change instead of guessing.

---

<!--
My own notes:
New Terms:
Agent: a program that chooses its next action based on what just happened, rather than following a fixed script. This example is an agent because it looks at the result of each step which influences the next decision/thing to run.
Tool: one single-purpose function the agent can call (search_listing, suggest_outfit, create_fit_card).
Planning loop / branch rule: the "if this, do that; otherwise do this other thing" logic that decides which tool runs next.
Session / state: the data being passed from one tool to the next during one run (e.g., which item was picked, so the outfit tool knows what you're asking about).
Stub: placeholder code that runs but does nothing yet
Token (in "size tokens"): here, just a fragment of text splitting "S/M" into "S" and "M" so a search for size "M" matches it without accidentally matching unrelated sizes like "US 9".

-->

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Filters the listings data by price and size, then scores
  what's left by keyword overlap between `description` and each listing's
  title, description, category, and style tags, and returns the best matches.
- **Inputs:** `description` (str), `size` (str or None), `max_price` (float or
  None). Size is matched by token, not substring — `"M"` matches `"S/M"` but
  not `"US 9"` — so a listing is included if any token of its size string
  matches any token of the requested size.
- **Returns:** A list of listing dicts (each with `id`, `title`, `description`,
  `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`,
  `platform`), sorted best-match first, capped at
  `config.SEARCH_RESULT_LIMIT` (10).
- **When it has nothing:** Returns `[]` — an empty list, never `None` and never
  an exception. This is what `run_agent`'s branch checks.

### `suggest_outfit`

- **What it does:** Calls the model to suggest one or two outfits pairing a
  candidate listing with the user's wardrobe.
- **Inputs:** `new_item` (dict — a listing dict), `wardrobe` (dict with an
  `items` key holding a list of wardrobe item dicts; may be empty).
- **Returns:** A non-empty string, two to three sentences, naming specific
  wardrobe pieces by name when the wardrobe has items.
- **When it has nothing:** If `wardrobe["items"]` is empty, it still returns a
  non-empty string — general styling advice for the item on its own, instead
  of raising or returning `""`.

### `create_fit_card`

- **What it does:** Calls the model to write a short, social-style caption
  about the find, based on the outfit suggestion and the listing.
- **Inputs:** `outfit` (str — the string returned by `suggest_outfit`),
  `new_item` (dict — a listing dict).
- **Returns:** A two-to-four sentence string that mentions the item, its
  price, and its platform once each.
- **When it has nothing:** If `outfit` is empty or whitespace-only, returns the
  fixed string `"No fit card: there was no outfit suggestion to write one
from."` instead of raising or calling the model.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a message in
`session["error"]` naming what to change (broaden the description, raise the
price ceiling, or try a different size) and return the session immediately —
`suggest_outfit` and `create_fit_card` are never called. Otherwise, take the
first result as `session["selected_item"]` and continue to `suggest_outfit`
and then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex (`agent.py::parse_query`). `under\s*\$?\s*(\d+)`
pulls out `max_price`, `\bsize\s+([a-z0-9/.\s]+?)(?:,|$)` pulls out `size`, and
both matches are stripped out of the query to leave the keyword `description`.
A regex was enough because the example queries all use the same two phrasings
("under $X", "size Y"); asking the model to parse two numbers out of a short
string would cost a call for no real gain.

**What moves through the session:** `query` → `parsed` (description, size,
max_price) → `search_results` → `selected_item` (first of `search_results`) →
`outfit_suggestion` (built from `selected_item` + `wardrobe`) → `fit_card`
(built from `outfit_suggestion` + `selected_item`). `error` is set only on the
empty-search branch or a `ModelUnavailable` from the model calls, and when it's
set every field after it stays `None`.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Pair the Y2K butterfly baby tee with your baggy straight-leg dark wash jeans and chunky white sneakers for a classic, nostalgic 2000s streetwear look. Layer the black cropped zip hoodie over top on cooler days and accessorize with your black crossbody bag.

  Fit card: Scored this little butterfly tee on Depop for just $18 and I am officially ready to re-enter my 2000s pop princess era. Can't wait to pair it with some baggy dark denim and chunky sneakers for the ultimate nostalgic streetwear fit. Early 2000s mall goth energy is undefeated!

0 model calls this session, 2 served from cache
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
Pair the vintage Levi's 501 jeans with the white ribbed tank top, layered under the black cropped zip hoodie for a casual, textured look. Complete the outfit with the chunky white sneakers and the black crossbody bag for an effortless, everyday street-style vibe.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Scored these vintage Levi's 501s on Depop for just $38 and I am never taking them off. The medium wash is *so* perfectly broken in, giving off that effortless 90s off-duty model vibe. Just threw them on with my favorite white sneakers and the fit is genuinely unmatched.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- I did the same thing here as I did with the project before. I went through the repo and had AI give me a small summary of the files, doing this, Claude helped me narrow down which files I should be focusing on. I then filled out the stubbed functions in tools.py, but Claude was very helpful with filling in the parse_query where a majority of the work required REGEX work. I filled in the requirements as to how to parse through the data and Claude implemented on the idea.

**Moment 2**

- For some reason, the first time I was trying to run the project the command python app.py ask "vintage graphic tee under $30" wasn't working for me. After maybe like 10 mins of trying to figure out what was wrong, I had Claude debug the issue, only to find out that the command needed to be in single quotes ('). I definitely missed the disclaimer on the project instructions since after looking at it again under the command it stated that the prompt had to be in single quotes. Consulting Claude saved me so much time since I would've tunneled on this issue for a while!

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
| --------- | ------ | ----- | ----- | ----- | ----- | ----- | ------- |
| 1.        |        |       |       |       |       |       |         |
| 2.        |        |       |       |       |       |       |         |
| 3.        |        |       |       |       |       |       |         |
| 4.        |        |       |       |       |       |       |         |
| 5.        |        |       |       |       |       |       |         |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| #   | Criterion | Target | Verdict | How I decided |
| --- | --------- | ------ | ------- | ------------- |
| 1   |           |        |         |               |
| 2   |           |        |         |               |
| 3   |           |        |         |               |
| 4   |           |        |         |               |
| 5   |           |        |         |               |

**Diagnoses**

---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->

---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
| --------- | ------ | ----- | ----- | ----- | ----- | ----- | ------- |
| 1.        |        |       |       |       |       |       |         |
| 2.        |        |       |       |       |       |       |         |
| 3.        |        |       |       |       |       |       |         |
| 4.        |        |       |       |       |       |       |         |
| 5.        |        |       |       |       |       |       |         |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->

---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
