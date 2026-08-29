# Departmental Needs (NDS-CHG-001 v1.1) — open follow-ups

Items deliberately left open when the rebuild closed on **2026-08-29**. Each is
recorded because it is real, not because it is planned for a particular date.
Mirrors `docs/mvp-1-r1/03_budget/FOLLOW_UPS.md`.

Nothing here blocks the module: all ten phases are complete, all gates are Done,
and 246 Python tests, 23 Playwright specs and 16 vitest tests are green. These
are the things a future session would otherwise have to rediscover.

---

## FU-01 — One Playwright fixture entity per spec file

**What.** The five NDS browser spec files share a single fixture Need under
`PE-CGKIS`, so the suite must run with `--workers=1` (`npm run test:ui:smoke:nds`
sets this). `playwright.config.ts` allows 2 workers and `fullyParallel: false`
only serialises *within* a file, so two spec files running concurrently reset
each other's fixture mid-test.

**Why it matters.** The failure mode is not a clean error. It was observed as a
review-task screen resolving to the withdrawal route — a plausible-looking wrong
page, not a crash. Anyone who runs `npx playwright test` directly, without the
npm script, gets that behaviour with no warning.

**Fix.** Give each spec file its own fixture entity, as `kentender_budget` does.
The fixture module already parameterises PE/OU/FY; the work is mostly in
`seeds/playwright_ui_fixtures.py` and the per-file `resetFixture` calls.

**Cost of leaving it.** The suite takes ~4.7 minutes single-worker. Acceptable
now; it will not stay acceptable as spec files are added.

---

## FU-02 — Production-mode asset build not exercised (tracker NDS-1005)

**What.** Every browser verification in Phases 9 and 10 ran against the
development bundle. A production-mode build (`./scripts/bench-with-node.sh build
--app kentender_procurement`) has not been run against the rebuilt module.

**Why it matters.** This repo has a documented history of build-only defects that
render clean in dev: a bundled CSS import that esbuild compiles but nothing links,
and a `*/` inside a CSS comment that silently truncates a stylesheet. Both were
invisible to console-error checks and to accessibility-tree snapshots.

**Fix.** Run the targeted build, clear the site cache, hard-refresh, confirm the
bundle content hash changed, and re-run the 7 visual baselines. If the baselines
pass against the production bundle they are genuinely portable; if they do not,
the difference is the finding.

---

## FU-03 — `_TRANSPORT_FIELDS` is a deny-list, not a derivation

**What.** NDS-914's fix drops `cmd`, `csrf_token` and `_` before forwarding
`**kwargs` into a service. That list is written down, not derived from Frappe.

**Why it matters.** If a future Frappe version injects another transport field
into `form_dict`, the same class of 500 returns. The AST guard added alongside the
fix catches an endpoint that forwards `**kwargs` *raw*, but it cannot catch a new
framework field passing through `_command_args` untouched.

**Fix (if it recurs).** Filter positively against the target service's signature
via `inspect.signature` instead of negatively against a list of framework names.
Not done now because a positive filter silently swallows a genuinely misspelled
argument, turning a loud `TypeError` into a quiet no-op — the worse failure of the
two for a command layer. Revisit only if a second transport field appears.

---

## FU-04 — Two `_validate_submission` branches are unreachable in practice

**What.** Writing the submission-rejection tests surfaced that content rules live
in two layers: the version controller checks the *shape* of a supplied value at
save, and `_validate_submission` checks *completeness* at submit. Because of that,
some service-layer branches cannot be reached through a normal save-then-submit —
an out-of-bounds description or a non-positive quantity is refused at save, so the
matching submit-time check never fires.

**Why it matters.** It is defence in depth, not dead code — the service is also
called by seeds and fixtures, which bypass nothing but do construct versions
directly. It is recorded here so a future reader does not "simplify" by deleting
the apparently-unreachable service checks, which would leave those paths guarded
only by a controller that a direct `frappe.get_doc(...).db_set()` can skip.

**Fix.** None needed. Do not remove either layer.

---

## FU-05 — Stale pre-approval draft still in `design/uploads/`

**What.** `design/uploads/KenTender_NDS-CHG-001_Clean_Departmental_Needs_v1.1.md`
is a pre-approval copy carrying `Status: Proposed for approval`, sitting beside the
approved document at the folder root. Flagged in the Phase 0 gap analysis (NDS-005)
and never reconciled.

**Why it matters.** Two files with the same name and different approval status is
exactly the ambiguity `full-replacement-change-docs` warns about. A future session
reading the upload copy would build against unapproved text.

**Fix.** Delete the upload copy, or move it under a clearly-dated `superseded/`
directory. Left alone here because deleting a document is the Project Owner's call,
not an implementation decision.
