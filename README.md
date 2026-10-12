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

Produced by `python run_eval.py --label before` (full log: `results/run_2026-10-12_0216_before.md`). Caching off, 5 tries per row. Criteria 3, 4 and 5 use five different queries, one per try; criteria 1 and 2 repeat one query five times. PASS/FAIL is decided by the check function for each criterion in `scenarios.py` (`check_1` … `check_5`), which restates the wording in `criteria.md`.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
| --------- | ------ | ----- | ----- | ----- | ----- | ----- | ------- |
| 1. matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. selected_item id equals the id suggest_outfit receives | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. fit card names the price and the platform | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. every search result is at or under the price ceiling | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| _extra, not one of the five:_ a requested size is honoured when a price follows it | 5 of 5 | FAIL | FAIL | FAIL | FAIL | FAIL | MISSED (0/5) |

The extra row is a sixth diagnostic scenario I added after reading the traces of the first run, where I noticed `size` coming out as `None`. It is not one of my five criteria and I did not edit `criteria.md`.

**Real output from one try** — `run_eval.py::main` calling `agent.py::run_agent`, which calls `tools.py::create_fit_card` (query `black cargo pants size W29 under $35`, try 1 of the size row). The user asked for size W29 and the trace shows `size: None`:

```
[1] parse_query
      in:  black cargo pants size W29 under $35
      out: {'description': 'black cargo pants', 'size': None, 'max_price': 35.0}
      →    regex, no model call
[2] search_listings (via MCP)
      in:  {'description': 'black cargo pants', 'size': None, 'max_price': 35.0}
      out: 7 items: Low-Rise Cargo Pants — Khaki, Oversized Flannel Shirt — Plaid Red/Black, Corduroy Wide-Leg Pants — Rust … +4 more
[3] select first result
      out: Low-Rise Cargo Pants — Khaki ($27.0, poshmark)

Fit card (tools.py::create_fit_card):
Scored these vintage khaki cargos on Poshmark for just $27, and they are officially the backbone of my new off-duty uniform. Throwing them on with a crisp ribbed tank and chunky sneakers gives off the ultimate effortless Y2K vibe. Adding a cropped zip hoodie and my go-to black crossbody finishes the fit with just the right amount of edge.

Check result: FAIL: asked for size W29, parsed size=None; 6 of 7 results are other sizes, e.g. [('Oversized Flannel Shirt — Plai', 'XL (oversized)'), ('Corduroy Wide-Leg Pants — Rust', 'W28')]
```

---

## Verdicts and Diagnoses

| #   | Criterion | Target | Verdict | How I decided |
| --- | --------- | ------ | ------- | ------------- |
| 1   | A matching query completes all three tools | 4 of 5 | MET | 5 of 5 tries ended with no error, an outfit, and a real fit card. 5 ≥ 4. |
| 2   | An impossible query stops before the second tool | 5 of 5 | MET | 5 of 5 tries: `suggest_outfit` was never called (a spy on it recorded nothing), outfit and fit card stayed `None`, and the error said what to change. |
| 3   | `selected_item` id equals the id `suggest_outfit` receives | 5 of 5 | MET | A spy around `suggest_outfit` recorded the id it received; it matched `session["selected_item"]["id"]` on all 5 different queries. |
| 4   | Fit card names its price and platform | 5 of 5 | MET | Each of the 5 cards contained `$<price>` and the platform name. |
| 5   | Every search result is at or under the ceiling | 5 of 5 | MET | Across all 5 queries, every listing in `session["search_results"]` (not just the first) had `price <= X`. |
| —   | _Extra:_ requested size is honoured | 5 of 5 | MISSED | 0 of 5. Every result list contained sizes other than the one asked for. |

**Diagnoses**

*The extra size row (0 of 5) — place: the loop's parse step, `agent.py::parse_query`, which feeds the tool.* `_SIZE_RE` was `\bsize\s+([a-z0-9/.\s]+?)(?:,|$)`: the size has to be followed by a comma or the end of the string. In all five queries a price follows the size (`size W29 under $35`), and the character class has no `$`, so the lazy match can never reach a comma or the end and the regex finds nothing. `size` comes out `None`, and `search_listings` — which worked correctly — is told to skip size filtering. The tool did what it was asked; the parser never asked it. This is one problem, not five: it appears every time a size is followed by "under $X". `90s track jacket in size M` (size at the end of the query) worked, which is why the five criteria never caught it — none of them has a size in it.

*Criteria 1–5 had no misses, so a target was set too low.* Criterion 1's target of 4 of 5 was too low: it was 5 of 5 here and 5 of 5 again in the after-run, and the two things I gave as the reason (a zero-score search and a model hiccup) did not happen in 10 tries. A tighter target would be **5 of 5, with the search covering at least one query containing a size**. The reason I wrote for 4 of 5 also missed the failure that did exist: the size filter silently dropping out.

---

## Loop Trace

Added one `trace.step()` per step to `agent.py::run_agent`, including the MCP call, named `search_listings (via MCP)`. Printed with `python app.py ask '...' --trace`.

**Happy path** — `python app.py ask 'vintage graphic tee under $30' --trace`

```
[1] parse_query
      in:  vintage graphic tee under $30
      out: {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      →    regex, no model call
[2] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
[3] select first result
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
[4] suggest_outfit
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
      out: Pair the Y2K butterfly baby tee with your baggy straight-leg dark wash jeans and chunky white sneakers for a c…
      →    wardrobe items: 10
[5] create_fit_card
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
      out: Scored this little butterfly tee on Depop for just $18 and I am officially ready to re-enter my 2000s pop prin…
```

**Empty search** — `python app.py ask 'designer ballgown size XXS under $5' --trace` (three steps, then it stops)

```
[1] parse_query
      in:  designer ballgown size XXS under $5
      out: {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
      →    regex, no model call
[2] search_listings (via MCP)
      in:  {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
      out: [] (empty)
[3] branch: search returned nothing
      →    set session['error'] and stop; suggest_outfit and create_fit_card are not called

  No listings matched that. Try a broader description, a higher price ceiling, or a different size.
```

(The size shows as `XXS` here because this trace was taken after the improvement below; before it, it was `None`.)

**The three failure modes**

- *Empty search:* above. Stops at step 3, no model call.
- *Empty wardrobe:* `python app.py ask 'denim jacket under $50' --empty-wardrobe --trace`. Step 4 shows `wardrobe items: 0`, `suggest_outfit` returned general styling advice instead of raising, and a fit card was still produced.
- *Model unreachable:* ran with a bad key (`GEMINI_API_KEY=badkey123 AI201_CACHE=0`). Steps 1–3 ran normally, then `[4] branch: model unavailable → The model rejected your API key. Check GEMINI_API_KEY in your .env file…` and the program printed that message with no stack trace (`agent.py::run_agent` catches `generate.ModelUnavailable`).

**On the MCP move:** I uncommented and filled in the `search_listings` registration in `mcp_server.py` — name `search_listings`, typed inputs `description: str`, `size: str | None`, `max_price: float | None`, and a description written for a reader who cannot see the code (units, result fields, and that it returns `[]` rather than an error when nothing matches). The registered function only calls the original `tools.py::search_listings` under an alias. In `agent.py::run_agent` I replaced the direct call with `call_tool("search_listings", {...})` and removed the now-unused import. I compared the two on `graphic tee`, `max_price=30`: the lists were identical (6 and 6 items), and an impossible query returned `[]` over MCP, so the empty-search branch still works. Nothing behaved differently. The only visible cost is that each call starts a server process, so runs are slower.

---

## The Improvement

**What I changed:** One line in `agent.py`: `_SIZE_RE` went from `\bsize\s+([a-z0-9/.\s]+?)(?:,|$)` to `\bsize\s+([a-z0-9/.\s]+?)(?=\s+under\b|,|$)`. The size now also ends where "under" begins.

**Which failure it was meant to fix:** The size row's 0 of 5 above — `parse_query` returning `size: None` whenever a price follows the size, so `search_listings` was never asked to filter by size.

### Run Log — After

Produced by `python run_eval.py --label after` (full log: `results/run_2026-10-12_0223_after.md`). Same scenarios, same queries.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
| --------- | ------ | ----- | ----- | ----- | ----- | ----- | ------- |
| 1. matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. selected_item id equals the id suggest_outfit receives | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. fit card names the price and the platform | 5 of 5 | PASS | FAIL | PASS | PASS | PASS | MISSED (4/5) |
| 5. every search result is at or under the price ceiling | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| _extra:_ a requested size is honoured when a price follows it | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Did it help, and how do I know:** Yes for the thing I targeted. The size row went from 0 of 5 to 5 of 5, and the trace shows why: `size` is now `'W29'`, `'M'`, `'M'`, `'L'`, `'L'` instead of `None`, and every returned listing fits the requested size (for `black cargo pants size W29 under $35`, 1 result, size W29, instead of 7 results in mixed sizes). I also checked `parse_query` directly on `size W30 L30 under $40` (→ `W30 L30`), `size S, under $30`, and `90s track jacket in size M`, which still work.

The after-run also had one miss I did not expect: **criterion 4 went from 5 of 5 to 4 of 5**. I don't think the change caused it, because the change is in `parse_query` and the fit card is written by `create_fit_card` from the selected item; the failing item (`silk slip dress in midi length under $40`, $30 on Depop) was selected the same way in both runs. The card it produced said *"…on Depop for just thirty bucks…"*. Place: the model's output. Mechanism: the prompt in `tools.py::create_fit_card` says to "mention the item and its price and platform once each" and never says to write the price as a dollar figure, and the temperature is 0.9 (`config.py`), so the model sometimes writes the price in words. My check (`$30`) reads that as missing. I'm reporting it rather than rerunning until it passes: one sample either way is thin, but it shows the 5 of 5 in the before-run was partly luck, not a guarantee.

---

## What's Still Broken

- **Criterion 4 (fit card price) is flaky.** Fix I would try: change the `create_fit_card` prompt to say "write the price as a dollar figure, e.g. $30" and lower the temperature. I did not do it because the unit asks for one change measured properly, and this one only showed up in the after-run, so I have no before/after for it.
- **Criterion 1's target is too loose** (4 of 5 against 10 of 10 observed) and none of my five criteria cover size. I'd tighten criterion 1 to 5 of 5 and add a size criterion. I left `criteria.md` untouched: the unit says a target that was missed or too easy is not grounds for editing the original.
- **Query parsing is still fragile in other ways.** `90s track jacket in size M` leaves the stray word `in` in the description (`'90s track jacket in'`), and the size rule only knows the phrasing "size X" followed by "under", a comma, or the end of the query.
- **Search ranks by keyword overlap only.** `black cargo pants` ranked khaki cargo pants first. I didn't measure this and haven't tried a fix.

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
