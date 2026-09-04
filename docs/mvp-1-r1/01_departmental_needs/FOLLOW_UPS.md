# Departmental Needs (NDS-CHG-001 v1.1) — open follow-ups

Items deliberately left open when the rebuild closed on **2026-08-29**. Each is
recorded because it is real, not because it is planned for a particular date.
Mirrors `docs/mvp-1-r1/03_budget/FOLLOW_UPS.md`.

Nothing here blocks the module: all ten phases are complete, all gates are Done,
and 246 Python tests, 23 Playwright specs and 16 vitest tests are green. These
are the things a future session would otherwise have to rediscover.

**2026-09-04 update.** The module is now mid a further rebuild cycle,
NDS-CHG-001 v1.1 → v1.6 (AUTH-ADR-001 v1.6 cutover; see
`02_NDS_Rebuild_Gap_Analysis.md` and `IMPLEMENTATION_TRACKER.md`). **FU-11**
below is addressed by that cycle rather than left open: the `Financial Year`
User Permission mechanism it describes is exactly what this cycle retires
(NDS-CHG-001 v1.6 §16.4 step 3 replaces it with a record-driven, non-authoritative
offer). The remaining items (FU-01..06, FU-07..10, FU-12..14) are independent
infrastructure debts, unaffected by the v1.6 cutover, and stay open as written
— FU-06 in particular (a missing Procurement Home pipeline-count contract) is
untouched: v1.6 adds no such contract to §8.1. **FU-15** (added by Phase 5's
browser verification) is resolved by Phase 6's seed rewrite, per its own
2026-09-04 update note. **FU-16** is new, discovered by Phase 6 itself, and
worth reading before Phase 7 touches any Playwright spec.

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

---

## FU-13 — frappe app-switcher phantom `/undefined` request poisons console-strict specs (2026-08-30)

**What.** Every Desk page load fires one `GET /undefined` (404, Image).
Traced via CDP: frappe's `sidebar_header.js` `populate_dropdown_menu()`
builds a **detached** jQuery fragment (`this.dropdown_menu` resolves empty
under the current sidebar markup) in which one icon-less dropdown item
renders `<img src="${item.icon_url}">` with `icon_url` undefined; the parser
fetches the image even though the fragment never enters the DOM. The console
error surfaces only intermittently in Playwright, so unrelated specs failed
their strict `collectConsoleErrors` assertion depending on run order —
verified pre-existing by a stash-control run.

**Interim.** `tests/ui/smoke/departmental_needs/helpers.ts` ignores exactly
this resource error (URL ending `/undefined`).

**Fix.** Frappe-core defect; on a frappe upgrade re-test and drop the
suppression. Alternatively give every KenTender app real desktop-icon/logo
data so no switcher item lacks both `icon` and `icon_url`.

---

## FU-14 — §10 "Review tasks" menu entry was a specification defect (2026-08-30)

**What.** NDS-CHG-001 v1.1 §10 specified a "Review tasks" sidebar entry and
defined `/app/departmental-needs/review` as a review-queue landing. The
requirement itself was wrong (author's correction, 2026-08-30): the KenTender
pattern sends decisions to the established **My Work** queue and notification
mechanism, keeps **Departmental Needs** as the only operational menu entry,
and places **Intake window** under Configuration and Governance. A work queue
is never exposed as a module sidebar entry.

**Implemented correction.**
- "Review tasks" removed from `workspace_sidebar/procurement.json`; the
  navigation and G0-012 contract tests now pin the two-entry menu.
- The queue landing screen (`ReviewScreen.vue`, bare `/review`) was removed;
  the URL redirects to the workspace. The protected review-task record,
  its permissions and the NDS-UI-05/NDS-UI-07 decision screens
  (`/review/{task}`, `/review/{task}/withdrawal`) are unchanged.
- Open departmental review tasks register with My Work through
  kentender_core's new `kt_my_work_providers` hook
  (`departmental_needs/services/my_work_provider.py`), mirroring §12.2
  eligibility (HoD role, exact scope, maker-checker exclusion).
- Reviewer notifications (submission, withdrawal request) now deep-link to
  the exact decision screen; author notifications keep the record link.
- The HoD's departmental register is the workspace itself (role-aware rows
  with "Requested by"), not a separate menu entry.

**Fix.** Restate §10 (two menu entries), §12.2 (My Work + notification as the
reviewer's entry points) and the route table in the next complete NDS
successor. This is a spec correction, not an implementation deviation.

---

## FU-15 — `upsert_departmental_needs()` is currently broken; Phase 6 is a hard test-suite prerequisite (2026-09-04)

**What.** The module's own MVP seed builder,
`seeds/kentender_mvp_r1.py::upsert_departmental_needs()`, throws
`ModuleNotFoundError`/`ImportError` trying to insert a `Needs Intake Window`
document — a doctype NDS-CHG-001 v1.6 Phase 1 deleted outright. Confirmed live
via `bench execute`. Because nearly every Phase 2/3/4-era Python test class's
`setUp`/`setUpClass` calls this function (`test_departmental_needs_permissions.py`,
`test_departmental_needs_lifecycle.py`, `test_departmental_needs_seed.py`,
`test_departmental_needs_contracts.py`), those classes now error at fixture
setup regardless of any fix to the test file's own body. Several of these
files also still open-code writes to `Needs Intake Window` in their own
`setUp` (e.g. `DepartmentalNeedsCommandCase.open_window()`/`close_window()`
in `test_departmental_needs_lifecycle.py`), so fixing the seed builder alone
would not be sufficient either — those helpers need the same v1.6 rewrite.

**Why it matters.** This is not an independent, deferrable phase the way it
reads in the Implementation Plan's phase list — it is a **blocking
prerequisite** for almost the entire NDS Python test suite. A future session
should not attempt a file-by-file Phase 7 test rewrite before Phase 6 (seeds
onto `User Responsibility Assignment` grants, ERPNext `Fiscal Year`/`UOM`, no
`Needs Intake Window`) lands — the fixtures underneath would still be broken
regardless of how correct the test file's own assertions are.

**Separately, but discovered the same way:** a single broken import in *any*
one of those test files was enough to abort Frappe's entire app-wide test
discovery (`frappe/testing/discovery.py::discover_all_tests` wraps its whole
directory walk in one `try/except`), so `bench run-tests --app
kentender_procurement` with no `--module` filter could not run at all — for
any module in the app, not just Departmental Needs — until this session fixed
the import-time breaks (see `IMPLEMENTATION_TRACKER.md` headline finding 11 /
row NDS-511). That specific abort is now fixed; the underlying seed breakage
above is not.

**Fix.** Phase 6 (seed rewrite) first, then Phase 7 (test-suite rewrite) —
in that order, not in parallel per-file. `test_departmental_needs_navigation.py`
is the one file whose classes are seed-independent and is already fully green
(NDS-512); its two remaining failures are pre-existing Procurement Planning
naming drift (`"Procurement Plans"` → `"Procurement Planning"`, and a
`"departmental"` substring collision with Planning's own `departmental-
procurement-plan` page), out of this module's scope.

**Update 2026-09-04, Phase 6 landed:** the seed rewrite this item called for
is done (`IMPLEMENTATION_TRACKER.md` Phase 6, NDS-601–613) — confirmed live,
`upsert_departmental_needs()` now builds all 4 default Needs correctly and
the 4 previously setUpClass-erroring test files now execute their bodies
(31/61/42/30 tests ran, not 0). Phase 7 (rewriting those bodies' own stale
`PE`/`OU_DIGITAL_HEALTH`/`ISOLATION_REQUESTER`/etc. assertions) remains open
exactly as this item describes.

---

## FU-16 — Playwright fixtures no longer draw a separate `need_reference` sequence (2026-09-04)

**What.** `seeds/playwright_ui_fixtures.py` used to build its Needs under a
dedicated `PE-CGKIS` Procuring Entity specifically so its `need_reference`
sequence (`NDS-{PE code}-{FY start}-####`) never collided with the §14.3
default profile's `NDS-MOH-2027-0001..0004`. AUTH-ADR-001 v1.6 §1.1 makes the
site exactly one implicit Procuring Entity, so that isolation mechanism no
longer exists — and CFG-BR-010 keeps at most one Fiscal Year Open at a time,
which forces every seed/fixture that creates a Need (the default profile, the
§14.6 KEBS profile, and the Playwright fixtures) onto the *same* open Fiscal
Year, and therefore the *same* reference-number counter. Live-verified: with
the default profile's 4 Needs already seeded, the KEBS profile's three Needs
came back as `NDS-MOH-2027-0005..0007`, and a Playwright fixture applied
afterward took `NDS-MOH-2027-0008`.

**Why it matters.** No test in this repo currently asserts an exact
`need_reference` for anything the KEBS or Playwright fixtures create — every
consumer reads the reference off the command's own return value, never a
hardcoded string — so nothing is broken today. But this is a standing
constraint a future session must not design past: a Playwright spec (or a
Phase 7 automated test) that hardcodes an expected reference number for a
fixture-created Need will be fragile against run order, and reseeding the
default profile *after* Playwright/KEBS fixtures have already consumed
numbers in the same sequence will not reset that counter back to 0001.

**Fix.** None needed unless a future spec starts asserting exact reference
numbers for non-default-profile Needs — if that happens, assert on content
(title, state, scope) instead, the way every current fixture consumer
already does. Isolation between fixture families is now provided by
Organisation Unit + `fixture_namespace` only (see `playwright_ui_fixtures.py`'s
dedicated "Playwright — Departmental Needs" OU and `_kebs_unit()`'s "Coast
Region — Administration and ICT" OU), not by a separate reference sequence.
