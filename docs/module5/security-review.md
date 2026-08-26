# Module 5 Security Review — Reconciliation

AI security audit findings (F1–F6) reconciled against a manual scan. The manual scan produced
zero recorded findings (empty table: Severity, Line:line, Finding, Suggested Fix, Reason), so
every finding below is AI-only by construction — there was nothing on the manual side to place
in Agreement or You-only.

## Agreement
Both reviews agree that the largest production concern is the intentional absence of authentication and authorization. Both also treat broad local-development CORS and dependency hygiene as real items to track without overstating them as immediate course-scope failures.

## AI-only
Tthe AI review added OSV-backed dependency findings for `python-dotenv` and `pytest`, plus CI/Docker supply-chain hardening around tag pins, image pins, and unhashed installs. I did not independently reproduce those advisories beyond checking the pinned versions and workflows.

## You-only
My manual review added lowe-severity usability and deployment-context notes: echoed task ids in 404 responses, verbose validation text shown in the frontend, and the need to document network boundaries for the Docker deployment.

## Top-3 Security Backlog (from Valid findings only — F5 and F6 excluded)

| Rank | Finding | Why it matters | Suggested owner | Next action |
|---|---|---|---|---|
| 1 | No auth (accepted risk) | Currently correct for course scope, but this is the one item that becomes a real IDOR/no-authz vulnerability the moment the app is deployed beyond localhost — highest blast radius of the three. | Course/project owner | Add an explicit "not authenticated — do not deploy beyond localhost" gate to `README.md`/mini-ADR deployment notes, not just a scope note. |
| 2 | CORS `"null"` + stale dev origins | Real anti-pattern, currently Low severity only because `allow_credentials=False`, but it's a one-line cleanup with no downside. | Backend | Remove `"null"` and unused dev-server origins from `allow_origins` in `app/main.py:28-39`. |
| 3 | No input bounds / unbounded store, no rate limiting | Legitimate resource-exhaustion vector; audit's own conclusion is "no action needed" for current course scope, so this is a watch-item, not urgent. | Backend/DevOps | Track as backlog only; revisit if the app is ever exposed beyond localhost (add `max_length` on `tag_ids`, consider basic rate limiting). |
