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

---

## FU-06 — No published count contract for Needs under review

**What.** Procurement Home's pipeline previously carried a **Demands under
review** stage. It was replaced rather than relabelled, because §8.1 publishes
no contract that answers "how many Needs are awaiting departmental decision in
this Procuring Entity". The stage was dropped instead of being wired, leaving a
five-stage pipeline in which every number is real.

**Why it matters.** The funnel now jumps from nothing to *Accepted needs
awaiting planning*, so the review backlog is invisible on the landing page even
though it is the stage a Head of User Department most needs to see. The
information exists; only a published way to ask for it does not.

**Why it was not just added.** §8.1 is a closed contract set, asserted by
`test_departmental_needs_contracts.py` to equal its documented names exactly.
Adding an endpoint is a specification change (an NDS-CHG-001 v1.2), not an
implementation decision. Reading `tabDepartmental Need` from `procurement_home`
would have been the alternative, and the architecture guard now explicitly
forbids it — that module was outside the D1 boundary check until this change,
which is why nothing caught the original defect.

**Fix.** Add a scoped count read to §8.1 in the next NDS specification version
(`get_needs_pipeline_counts`, PE-scoped, returning per-state counts), then
restore the stage sourced from it.

---

## FU-07 — Procurement Home and Departmental Needs disagree about "financial year"

**Superseded (2026-08-30):** carried forward as CTX-FU-02 in
`docs/mvp-1-r1/00_common/KenTender_CTX-CHG-001_Working_Context_v1.0.md` —
Home's context is now permission-scoped with its own per-module FY memory,
but its int-year vocabulary remains until the unification lands.

**What.** Procurement Home derives an **integer start year** from Budget's
`fiscal_period` column (`2026/27` → `2026`) and shows it as "FINANCIAL YEAR
2026". Departmental Needs, Planning and Strategy key on **`Financial Year`
records** (`FY-2027-2028`, label `2027/28`). The site currently has no Financial
Year record starting before 2027, so the year the landing page displays
corresponds to no record at all.

**Why it matters.** Any Home counter that filters Needs by the selected year
silently returns zero forever — exactly the failure FU-06's stage was replacing.
`_count_needs_awaiting_planning` therefore sums across every Financial Year
rather than the selected one, which is correct for a funnel count but means the
page's year selector does not filter it.

**Fix.** Decide which vocabulary is authoritative for cross-module context (the
`Financial Year` doctype is the stronger candidate — three modules already use
it) and migrate Procurement Home's selector onto it. Until then, do not add
Home counters keyed on the integer year.

---

## FU-08 — §10 menu placement now differs from the rail (2026-08-30)

**What.** NDS-CHG-001 v1.1 §10 lists the module menu as three consecutive
entries: **Departmental Needs**, **Review tasks**, **Intake window**. At the
user's request the rail now groups every configuration surface under the
**Configuration and Governance** section, so **Intake window** (NDS-UI-08) is a
child of that section rather than a flat spine row beside its module. The other
two entries are unchanged, as are all routes, roles and `display_depends_on`.

**Why it matters.** Frappe nests one level only (`Sidebar.find_nested_items`),
so a Departmental Needs sub-group *inside* Configuration and Governance is not
expressible — the choice was flat-beside-module or child-of-configuration, and
the second was taken. The tests that encoded §10's contiguity
(`test_departmental_needs_navigation.py`,
`test_procurement_sidebar_g0_012_contract.py`) were updated to match, so the
specification is now the only place carrying the old arrangement.

**Fix.** Restate §10 in the next NDS specification version: the module menu is
two business-flow entries plus one configuration entry that lives in the
Procurement configuration group.

---

## FU-09 — Frappe forces `target="_blank"` on every `URL` sidebar row (2026-08-30)

**What.** `frappe/public/js/frappe/ui/sidebar/sidebar_item.html` renders
`target="{%= item.link_type === "URL" ? "_blank" : "" %}"`, so both NDS sub-route
rows opened a second browser tab. A sub-route cannot be a `Page` link — `link_to`
is a Dynamic Link validated against a real `Page` record, and a dangling value
fails the whole-site migrate — so the rows stay `URL` and
`procurement_sidebar_header.js` (`patchInternalUrlTarget`) strips the target for
same-origin paths, letting Frappe's own body click handler push-state them.

**Why it matters.** It is a monkey patch over a framework template. A Frappe
upgrade that changes `TypeLink.prototype.make`, or renames `item-anchor`, makes
the patch a silent no-op — the rows would start opening new tabs again with no
test failure, because the JSON contract tests only read the export.

**Fix.** Either carry a Playwright assertion that the rail's `URL` rows have no
`target` attribute, or upstream a `Frappe`-side option for internal URL rows.

---

## FU-10 — kentender_budget's `frappeCall.js` still double-renders refusals (2026-08-30)

**What.** NDS's `frappeCall.js` now passes `silent: true` so a server refusal
renders once, in the screen's own inline error summary, instead of also raising
Frappe's native "Message" modal from `_server_messages`. The adapter is a
declared verbatim copy of `kentender_budget/public/js/budget_shared/data/
frappeCall.js` (AGENTS.md §6.6 — each app keeps its own copy), and the Budget
copy still lacks the flag, so every Budget screen shows each refusal twice.

**Why it matters.** Same defect, different app: fixing it here without running
Budget's own Playwright suite would have been an unverified cross-app change,
so it was left. The two copies have now deliberately diverged by one line.

**Fix.** Add `silent: true` to the Budget copy and re-run Budget's UI gate;
consider asserting `.msgprint` absence in one Budget refusal spec, as
`departmental-needs-intake-window.spec.ts` now does.

---

## FU-11 — §8.1's Financial Year offer is now scope-filtered (2026-08-30)

**What.** `selectable_financial_years` now intersects the Available, unexpired
years with the caller's `Financial Year` User Permissions (native semantics: no
rows = unrestricted; administrative users unrestricted), and `get_workspace`
resolves a remembered year outside that offer to the single offered year
instead of carrying it. NDS-CHG-001 v1.1 §8.1 described the plain Available
list. Observed live: the KEBS foundation seed's `FY-2026-2027` was offered to
the §14 MoH Planner, whose only year is `FY-2027-2028`; every command in that
context — her intake-window save included — was a guaranteed
`NDS_SCOPE_DENIED` at the very end of the flow.

**Why it matters.** The offer and the §17 controls must not drift: offering a
context every command refuses is the NDS-807 defect class. The commands
themselves are unchanged and still re-check their own scope.

**Fix.** Restate §8.1's context resolution in the next NDS specification
version: contexts *and* years are offered only where the caller could act, and
`can_maintain` on the intake read is scoped to the exact PE/FY (shared
predicate with `save_needs_intake_window`). The same restatement should cover
the remembered PE/OU pair: the client stores its last selection per browser
origin, not per user, so after an account switch `get_needs_workspace` now
resolves a pair outside the caller's contexts to "unselected" (auto-resolving
a single context) instead of the previous hard `NDS_SCOPE_DENIED`, which
dead-ended the next user's first load behind a Try-again loop.

---

## FU-12 — "Requested by" added beyond the §11 static compositions (2026-08-30)

**What.** At the user's request the NDS-UI-01 workspace table gained a
"Requested by" column and the NDS-UI-04 detail context card a "Requested by"
row (both from the read contracts' existing `author_label`). §11's static
compositions (NDS-DES-01/05/07) do not show them: the workspace was drawn as
the author's own list, but §6 also routes the Head of User Department through
it, where rows are the whole department's and authorship must be visible
without opening each record.

**Fix.** Fold the column and card row into the §11 compositions in the next
NDS specification version. The NDS-908 baselines already carry them.
