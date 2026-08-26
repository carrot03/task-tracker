# Final AI Review and Ownership Evidence
## AGENTS.md guardrails
- Repo-specific stack and commands included: yes — `AGENTS.md` §2 lists the exact stack (FastAPI 0.115.12, Pydantic 2.11.3, uvicorn 0.34.0, pytest 9.1.1) and setup/run/test/Docker commands.
- Docs-first/read-first guardrail included: yes — `AGENTS.md` §4 "Docs-first" requires checking `docs/midcourse/` and `docs/module4/` for prior decisions before proposing changes.
- Unexpected app/frontend edits rule included: yes — §4 "No `app/` or `frontend/` changes without explicit approval" now explicitly covers both `app/` (routes, models, store, business rules) and `frontend/` (the static frontend served via `StaticFiles`). Originally only named `app/`; updated during this final review pass to close that gap.

## AI code review mini-log
| AI comment | Grade: Useful / Noise / Wrong | Reason | Verification or decision |
|---|---|---|---|
| Initial tags prompt returned a full tag-management plan (rename/delete, management screens) before scope was decided | Wrong | Assumed a bigger feature than requested and produced implementation detail ahead of a scoping decision | Rejected outright; rewrote the prompt to request only three user stories and constraints with no code (`docs/midcourse/prompt-log.md`, Feature 1 Prompt 1) |
| Tag endpoint implementation returned tasks with bare `tag_ids` rather than expanded tag objects | Noise | Technically matched the request but was less useful for the frontend, which needed tag name/id together on each card | Edited the response shape to return expanded `TagResponse` objects; verified duplicate tag names are rejected case-insensitively (`docs/midcourse/prompt-log.md`, Feature 1 Prompt 3) |
| Suggested a derived `is_overdue` computed field instead of a stored overdue boolean | Useful | Keeps overdue status correct as `due_date`/`status` change, instead of going stale like a stored flag would | Confirmed by break-test: changing the comparison from `<` to `<=` failed the due-today test, proving the boundary is actually exercised (`docs/midcourse/verification.md`, `docs/midcourse/reflection.md`) |

## AI security mini-review
| Finding | File evidence | Grade: Valid / False Positive / Noise | Reason | Next action |
|---|---|---|---|---|
| No authentication/authorization anywhere in the API | `README.md` (no-auth stated), `app/main.py` (no auth dependency on any route), `docs/midcourse/mini-adr.md` | Valid (accepted risk for course scope) | Correct and intentional for an in-memory course project, but becomes a real IDOR/no-authz vulnerability the moment it's deployed beyond localhost | Add an explicit "not authenticated — do not deploy beyond localhost" statement to `README.md`/mini-ADR deployment notes, not just an implicit scope note |
| CORS allows the `"null"` origin plus stale/unused dev-server origins | `app/main.py:28-39` | Valid | Real anti-pattern; currently low severity only because `allow_credentials=False`, and it's a one-line cleanup with no downside | Remove `"null"` and unused dev-server entries from `allow_origins` |
| OSV-backed dependency advisories for `python-dotenv`/`pytest`, plus CI/Docker supply-chain gaps (unpinned base image tag, unhashed installs) | `requirements.txt`, `Dockerfile`, `.github/workflows/ci.yml` | Valid, not independently reproduced | I checked pinned versions and workflow steps but did not independently verify the underlying advisories beyond that | Pin the `python:3.11-slim` tag to a digest and re-check `python-dotenv`/`pytest` versions against current advisories before next dependency bump |

## Manual security check
I manually reviewed the parts the AI security audit didn't flag as findings: error response bodies, frontend validation display, and deployment framing. I found that 404 responses echo the requested task/tag id back in the message body (e.g. `f"Task with id {task_id} not found"`, `app/main.py`) it is a low-risk here since ids are random UUIDs since there is no authentication rules in this project delivery. I also found the frontend surfaces raw Pydantic validation text to the user rather than a friendlier message, and that nothing in the repo documents the expected network boundary for the Docker image (it binds `0.0.0.0:8000` with no reverse proxy or TLS assumption stated). 
These matter because they are the kind of gaps that are ok for now but if ever the project gets bigger or deployed then we must address them.

## One AI output I rejected or corrected
For the tags feature, my first prompt was too open-ended ("I want to add tags and labels. Tell me how to do it."). The AI returned a broad implementation plan that included tag rename/delete and management functionality I hadn't asked for and that wasn't in any user story yet. I rejected the response and the code it proposed, and rewrote the prompt to explicitly separate design from implementation: "Act as a senior developer. List three user stories and constraints for tags and labels. Do not mention code." Only after reviewing and accepting the narrowed scope did I ask for the endpoint list and then the implementation, which kept rename/delete out of the final feature (`docs/midcourse/prompt-log.md`, Feature 1).

## Three AI usage rules
1. Never paste secret variables or tokens into any AI prompt.
2. Always verify architectural decisions before accepting them 
3. Record AI contributions by always asking before AI makes changes, and using `git diff` to track exactly what AI-authored code ended up in the repo.

## Ownership statement
I'm comfortable submitting this repo as my own work because every AI-proposed feature went through an explicit review-and-narrow step before I accepted it. The test suite passes, including boundary tests I verified actually catch regressions via break-testing, and I independently confirmed the Docker image builds and serves `/health` with a 200 after fixing a local Docker credential-helper misconfiguration unrelated to the app itself. The AI security findings were reconciled against my own manual pass rather than accepted as-is, producing a backlog with findings I added myself that the AI audit didn't surface. CI runs the full suite on every push and PR into `main`, giving an automated, repeatable check independent of my local environment. Where I couldn't verify an AI claim myself (the OSV dependency advisories), I said so explicitly rather than presenting it as confirmed.