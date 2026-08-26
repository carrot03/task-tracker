# Context-Strategy Comparison — Architecture Doc Generation

Three drafts of the same architecture-documentation task were produced under three
context strategies: **A** (minimal context), **B** (structured — `AGENTS.md` +
file summaries), **C** (targeted — a small set of anchor files read directly).
Findings below are cross-checked against the actual repo (`app/main.py`,
`app/store/__init__.py`, `app/business_rules.py`, `AGENTS.md`, `frontend/index.html`,
`tests/`), not just compared draft-to-draft.

## 1. Strategy comparison table

| Strategy | What it got right | What it got wrong / missed / invented | Best-suited task shape |
|---|---|---|---|
| **A — Minimal context** | Correct data model (incl. the comments sub-resource, tags, `is_overdue` computed at read time); correct request flow for `POST /tasks`; correct key-files list; correctly flags `app/routers/` as unused scaffold; cites `docs/midcourse/mini-adr.md`. | Never mentions `AGENTS.md` at all, even though it's the most detailed operational doc in the repo (exact status-transition graph, CI, Docker, lint status). Describes `business_rules.py` only as "a validation graph" instead of stating the actual `ToDo→InProgress→Done→InProgress` transitions. Omits field-length limits (title ≤200, description ≤2000, assignee ≤100, tag ≤50) that both B and C captured. Speculates that CORS origins imply a "Live Server / Vite dev workflow" without a citable source for that inference. | A fast first-pass orientation doc for someone opening the repo cold with no curated docs to lean on — good breadth, weak on precision and citations. |
| **B — Structured (AGENTS.md + summaries)** | The only draft to catch a real documentation-drift finding: the comments sub-resource is fully implemented and tested (`tests/test_comments.py` exists) but is mentioned in neither `AGENTS.md` nor `CLAUDE.md` — verified true, both docs are silent on comments. Correctly quotes `AGENTS.md` for "no lint/format tool configured" and "Docker workflow... not documented elsewhere as a supported workflow." Captures field-length limits and case-insensitive enum parsing. | Despite having `AGENTS.md`, which spells out the exact status-transition graph, B's `business_rules.py` entry only says "the status-transition state machine; raises 422 directly" — it had the detail available and still summarized it away. Never mentions `docs/midcourse/mini-adr.md`, so the in-memory-storage decision isn't linked to its documented rationale. | A doc meant to catch drift between code and its own documentation/governance files — an audit or handoff doc where "is this documented elsewhere, correctly" matters as much as "what does the code do." |
| **C — Targeted anchor files** | The only draft to catch `store.update_task`'s `model_dump(exclude_unset=True)` partial-update semantics — a real behavior, verified in `app/store/__init__.py:174`, visible only by reading the source directly. Most disciplined about scope: explicitly lists `business_rules.py` and `frontend/` as "not read" rather than guessing, and hedges status-transition rules as "per docstring" instead of asserting them. Captures field limits and enum behavior correctly. | Overgeneralizes one edge case: says `update_task` "re-stamps `updated_at`," but the actual code leaves `updated_at` untouched when no fields were set (a no-op update returns the task unchanged) — a minor slip in an otherwise precise read. Completely silent on `AGENTS.md`, `docs/midcourse/`, CI, and Docker — no operational/process context at all. | A precise, source-of-truth reference for a specific subsystem (e.g., "how does task create/update actually work") where line-level accuracy on the files you did read matters more than broad repo coverage. |

## 2. Verdict

I chose **Strategy C** as the base for the final architecture doc, with **Strategy
B's one confirmed finding** (the undocumented comments sub-resource) folded in as
an added note. C was the only draft that surfaced a real code-level behavior
(`exclude_unset` partial-update semantics) invisible from docs or summaries, and
the only one that consistently distinguished "read and verified" from "not read" —
which matters most for a doc that will be treated as a source of truth about how
the code behaves. B's documentation-drift catch is real and worth keeping, but it
came from having `AGENTS.md` in context, not from reading `app/`, so it's an
addendum rather than a reason to prefer B's version wholesale — B under-used the
transition-graph detail that was sitting right in the same doc it was given.

## 3. Context-engineering rule

For task shape "write an architecture doc that will be treated as a source of
truth for code behavior," I use Strategy C (targeted anchor files) because it was
the only strategy that surfaced a genuine code-level nuance and never stated
something as fact without having read the file behind it. When the task shape
shifts to auditing whether docs and governance files (`AGENTS.md`/`CLAUDE.md`)
still match the code, I switch to Strategy B instead, since giving it `AGENTS.md`
directly was what let it catch the one confirmed documentation gap that neither A
nor C found.
