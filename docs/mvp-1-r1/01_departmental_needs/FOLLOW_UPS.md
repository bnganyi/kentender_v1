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
2026-09-04 update note. **FU-16** and **FU-17** are new, discovered by Phase 6
and Phase 7 (NDS-713) respectively. **FU-18, FU-19 and FU-20** are new,
added by Phase 10's acceptance-criteria mapping: FU-18 is a spec-text
ambiguity needing Project Owner confirmation (not a defect); FU-19 is real,
missing automated-regression coverage inside this module (three specific
NDS-AC gaps, none currently believed broken); FU-20 is a Procurement
Planning-owned finding (that module's own test suite cannot currently execute
against this site) surfaced while trying to verify Planning-owned acceptance
criteria that are correctly out of this cycle's own scope.

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

**Update 2026-09-04, Phase 7:** the reference-reuse this item describes turned
out to have a sharper consequence than a fragile assertion — see FU-17.

---

## FU-17 — Reference reuse leaked old `Notification Log` rows onto new Needs; raw URA deletes left stale Frappe Roles (2026-09-04)

**What.** Two defects in Phase 6's own seed/fixture resets, found by the Phase
7 test rewrite and fixed in the same commit:

1. Neither `profiles.reset_kebs()` nor `playwright_ui_fixtures.reset_all()`
   deleted `Notification Log` rows for the Needs they removed. Because the
   `need_reference` counter only sees Needs that currently exist (FU-16),
   the next `create_need` re-issues the deleted reference — and every stale
   notification addressed to the old `document_name` silently attaches to
   the new, unrelated Need. Observed live as phantom recipients
   (`head.kebs@example.test`, `nds.pw.author@example.test`) in a fresh
   notification-recipient assertion; 11 orphaned rows were purged from the
   site.
2. `reset_kebs()` removed disposable actors' `User Responsibility Assignment`
   rows with a raw `frappe.db.delete`, which bypasses `_sync_projection` —
   the step that would normally strip the Frappe Role `grant()` synced onto
   the user. The actors therefore kept a stale `Head of User Department` /
   `Departmental Author` role with no assignment behind it, and kept
   surfacing as candidates in `notifications._reviewers()`'s `Has Role` scan
   (the resolver then correctly denied them, but only after they had been
   enumerated).

**Why it matters.** Both are invisible to every command test — a Need still
creates, submits and accepts with a phantom notification recipient or a stale
role in place. They only show up in the one place that asserts *exactly who
was told*. The first is also a standing hazard for any future reset that hard
deletes a Need: `Notification Log` is not a child of `Departmental Need` and
nothing cascades to it.

**Fix (done).** Both resets now delete `Notification Log` by
`document_type`/`document_name` before removing the Need rows;
`reset_kebs()` strips the two business roles from its disposable actors
unconditionally (not only when an assignment was found — an earlier reset
predating this fix could already have left the role stale with nothing to key
off). `reset_all()` deliberately does *not* touch its actors: the Playwright
actors are designed to persist across resets (`ensure_actors()` is
find-or-create), so their grants are real and current, not stale.

**Still open.** Any *new* fixture reset that hard-deletes a Need must repeat
the `Notification Log` cleanup — there is no shared helper for it yet, and
tracker rule 6 means the next author should not "delete later". A small
`departmental_needs.seeds._purge_need_graph(needs)` helper shared by both
resets would remove the duplication; not done here to keep the Phase 7 diff
to tests and the two defects.

**Update 2026-09-04, NDS-713 (Playwright half of Phase 7).** Two more real
defects in the same family — a Phase 6 rewrite regression and a permission
gap, both found only by actually driving the fixture actors through a real
browser rather than as Administrator — surfaced while getting
`npm run test:ui:smoke:nds` green, and were fixed in the same session:

3. `playwright_ui_fixtures.py::_ensure_user` never called `update_password`,
   so a newly-created NDS Playwright actor (`nds.pw.author@example.test`,
   `nds.pw.reviewer@example.test`, `nds.pw.planner@example.test`) had no
   password at all — every one of these actors was unable to log in
   ("Invalid Login") for the entire time this defect existed. Confirmed live
   2026-09-04 by attempting the actual browser login the specs use. This is a
   Phase 6 seed-rewrite regression: the pre-Phase-6 fixture used
   `kentender_mvp_r1`'s `base._user`, whose own docstring notes it "saves the
   User twice (add_roles, then update_password)" — the rewritten
   `_ensure_user` kept the role assignment half and silently dropped the
   password half. Fixed by calling `update_password(email, TEST_PASSWORD)`
   unconditionally (new user or existing), matching the same unconditional
   call in `kentender_core.seeds._common.upsert_seed_user`.
4. ERPNext's native `UOM` doctype (retargeted onto by D6) carries DocPerm
   rows only for ERPNext's own Item/Stock/Sales roles — none of Departmental
   Needs' three business roles (`Departmental Author`, `Head of User
   Department`, `Procurement Planner`) had read access. Every real
   Departmental Author's "Create need" flow hit Frappe's own "Insufficient
   Permission for UOM" dialog from `DepartmentalNeeds.vue::loadUnits()`'s
   client-side `frappe.db.get_list("UOM", ...)` call — and because that read
   sits inside the editor's one shared `load()` promise, the failure left
   `data-loading` stuck `"true"` forever (the form still rendered underneath
   the dialog, since `NeedEditorScreen` doesn't gate on `loading`, so this
   looked like a passing screen to anything short of a real click-through).
   Phase 5's own live verification (NDS-504/NDS-G05) never caught this
   because it was done as Administrator, who bypasses every DocPerm.

**Why it matters.** Both defects are invisible to every Python test and to
any browser verification done as Administrator — the exact blind spot this
module's own accumulated experience already warns about (see
`IMPLEMENTATION_TRACKER.md` headline finding 9 and NDS-509/510). A UI gate
that only ever logs in as an unrestricted user cannot catch either class of
bug.

**Fix (done).** (3) `_ensure_user` now calls `update_password` unconditionally.
(4) A new idempotent patch, `kentender_procurement.patches.
nds_chg_001_v16_grant_uom_read_permission`, grants a `Custom DocPerm` read
row on `UOM` for the three Departmental Needs business roles — the normal
Frappe mechanism for extending permissions on a doctype this app does not
own, rather than a new §8.1 endpoint or an edit to erpnext's own doctype
JSON. Both fixes are live-verified: fixture-actor login succeeds, and
`Custom DocPerm` for `UOM` shows `read: 1` for all three roles.

**Still open.** No other Departmental Needs screen was audited for a similar
DocPerm gap on a core/ERPNext doctype it reads client-side — `UOM` is the
only one currently read that way (Fiscal Year and Organisation Unit reads
all go through server-side `frappe.get_all`/`frappe.db.get_value`, which
bypass DocType permissions, per `services/context.py`'s existing pattern).
If a future screen adds another direct client-side `frappe.db.get_list()`
against a doctype this module doesn't own, check its DocPerm table against
these three roles before assuming it works — Administrator-only verification
will not catch a gap.

---

## FU-18 — Resubmit of a Returned correction is not re-gated on a closed intake flag; the spec text is internally tensioned on this point (2026-09-04)

**What.** `services/lifecycle.py::submit_need` calls `require_open_intake` only
when `prior == STATE_DRAFT` (the very first Draft → Submitted transition). A
*resubmit* of a Returned correction (`prior == STATE_RETURNED`) is never gated
on the flag at all, by explicit design — the inline comment reads "the initial
submission needs the flag Open; a correction of a version submitted before
close does not" — and is proven by a real, currently-passing test:
`test_a_returned_correction_may_be_resubmitted_after_the_window_closes`
(`test_departmental_needs_lifecycle.py`) closes the flag and then successfully
resubmits a returned correction in the same transaction.

**Why it matters.** NDS-CHG-001 v1.6's own text is not unambiguous on this
point. NDS-BR-002 and AC-003 both use the qualifier "initial" ("initial
creation and initial submission require the flag Open"), which supports the
implemented reading. But NDS-BR-003's own final sentence, unqualified, reads
"Submission stays blocked while the flag is closed" — and the v1.6 "New in
v1.6" disposition table's own rationale for the correction ("a draft that can
be neither finished nor cleanly abandoned is dead weight, and intake
extensions are routine") reads as an argument for allowing exactly this
resubmit path, but was written to justify Draft/Returned *editability*, not
explicitly *resubmission*. Both readings are defensible; the code picked one
and it is well-tested, but no Project Owner sign-off on this specific
resubmit-while-closed question is recorded anywhere.

**Why it was not treated as a defect.** The chosen reading is internally
consistent (matches AC-003's own "initial" wording), product-sensible (a
correction already in the review pipeline before close is not new intake
demand), and deliberately commented in the source rather than accidental. This
pass does not silently accept or reverse it — per this repo's own convention
of surfacing rather than guessing at an ambiguous business rule.

**Fix.** A Project Owner should confirm, in the next NDS specification
version, that "initial submission" in NDS-BR-002/AC-003 is the controlling,
narrower phrase and that NDS-BR-003's later "Submission stays blocked" applies
only to the *initial* path — or state the opposite and require `submit_need`
to gate the resubmit branch too. Either way, restate NDS-BR-003 so the two
sentences do not read as contradicting each other.

---

## FU-19 — Three NDS-owned acceptance criteria have no automated regression: multi-OU create dialog, multi-Fiscal-Year browsing, save-draft-while-closed (2026-09-04)

**What.** Phase 10's acceptance-criteria mapping (`IMPLEMENTATION_TRACKER.md`
Phase 10 work register) found three real, specific gaps in this module's own
automated test coverage — not functional defects (in two of the three, source
inspection or a one-time live check supports the implementation being
correct), but criteria this tracker cannot honestly call `Done` without an
observed, checked-in result:

1. **NDS-AC-048 — the NDS-DES-15 "Create need for" multi-OU dialog.**
   `list_need_create_targets` is checked only for being a whitelisted contract
   *name*, never for its actual zero/one/several-OU return shape. No
   Playwright spec exercises `CreateTargetDialog.vue` at all — confirmed by
   grep, zero hits for `CreateTargetDialog`/`create-target`/`Create need for`
   under `tests/ui/`. The Playwright `AUTHOR` fixture is single-OU only, so
   the suite cannot structurally reach this branch. The only evidence is
   Phase 5's one-time manual browser check (NDS-507), performed *before*
   Phase 6/7 rewrote the seed/actor world.
2. **NDS-AC-050 — multi-Fiscal-Year browsing / remembered-year trap
   (§16.4 step 9).** Already honestly recorded at the Phase 2 gate level
   (`NDS-G02`: "steps 9/10/13 still proven live only") but not previously
   mapped to its exact AC id. No test file in this module references a second
   Fiscal Year; `list_needs_financial_years`/`selectable_financial_years` is,
   like `list_need_create_targets`, only checked for whitelisting.
3. **NDS-AC-054 (half) — Save draft stays enabled on a Draft/Returned Need
   while intake is closed.** `close_window()` is called exactly 3 times in
   `test_departmental_needs_lifecycle.py`; none combines it with `update_need`
   (the save-draft command) — only with create, submit, and resubmit (see
   FU-18). Source inspection confirms `update_need` never calls
   `require_open_intake`, so the behaviour is almost certainly correct, but
   that is code-reading, not an observed test result.

Separately, and lower-severity: **NDS-AC-025** (design fidelity) currently
rests on visual-regression baselines (NDS-908) rather than the newer,
mechanized `design-fidelity` Playwright gate (structural landmarks + geometry
measured directly off the `.dc.html` artboard) that AGENTS.md §6.6 says every
UI phase should ship and that System Setup/Budget already have
(`tests/ui/smoke/design-fidelity/`). This module's `.dc.html` artboards were
themselves edited this cycle (the PE row removed), which is exactly the
"reused component, changed artboard" case AGENTS.md §6.6 says needs either the
fidelity gate or an explicit, owner-signed-off exception — neither exists for
Departmental Needs today.

**Why it matters.** All four are the kind of gap that is invisible right up
until the one specific scenario is exercised — exactly the failure mode this
module has already hit twice this cycle (NDS-509/510, NDS-713's two
Playwright-only defects). A future session should not assume these paths are
covered just because the surrounding suite is green.

**Fix.** Add, in a future session scoped for it (not required to reopen this
NDS-CHG-001 v1.6 cycle, since nothing here is a known defect): a Python test
for `list_need_create_targets`'s multi-OU return shape plus a Playwright spec
giving one fixture actor two Organisation Units to reach `CreateTargetDialog`;
a Python or Playwright test exercising a second Fiscal Year to prove browsing
and creation-eligibility survive a remembered/filtered year; a lifecycle test
combining `close_window()` with `update_need`; and, if this module's screens
are touched again, a `departmental-needs-fidelity.spec.ts` following the
System Setup/Budget pattern.

**CLOSED 2026-09-19 (NDS-CHG-001 v1.14).** All three items closed:
1. NDS-AC-048 — `CreateTargetDialog.vue` no longer exists (retired by
   NDS13-CHG-003's inline DES-15 selector, closed in v1.13). The Python half
   closed: `TestCreateTargets` in `test_departmental_needs_contracts.py`
   proves `list_need_create_targets`'s multi-OU shape using Grace's own real
   2-OU grant. The Playwright half — a spec reaching the inline `/new`
   multi-select flow — was **not** written; see the new FU-32.
2. NDS-AC-050 — `TestMultiFiscalYearBrowsing` in
   `test_departmental_needs_lifecycle.py`: a disposable second Fiscal Year,
   proves `selectable_financial_years()` offers both years and the workspace
   neither leaks one year's rows into a filtered read of the other nor hides
   either from an unfiltered one. Found a real bug while building this: the
   server-side remembered-FY default (`frappe.defaults`, CTX-CHG-001)
   persists for real between test runs on this bench (see FU-30) and was
   bleeding into unrelated later tests — fixed with an explicit reset.
3. NDS-AC-054 half — `test_save_draft_still_succeeds_once_intake_has_closed`
   proves `update_need` still succeeds on a Draft/Returned Need while intake
   is closed, confirming `require_open_intake` was never called there.
The design-fidelity gate itself was added in v1.13 (NDS13-401), separately.

---

## FU-20 — Procurement Planning's own test suite cannot currently execute against this site (2026-09-04)

**What.** While attempting to independently verify NDS-CHG-001 v1.6's
Planning-owned acceptance criteria (AC-031, AC-034–037, AC-045 — the
direct-departmental-requirement editor, mixed-origin DPP, and KEBS-equivalence
requirements) for Phase 10, running
`kentender_procurement.procurement_planning.tests.test_dpp_lifecycle` live
errored at `setUpClass` with `ValidationError: Exactly one root organisation
unit exists per site`. Planning's own fixture builder
(`procurement_planning/tests/fixtures.py::ensure_world`) still creates a
second `Procuring Entity`-scoped Organisation Unit tree, an `Organisation Unit
Type` record and the legacy custom `Financial Year` doctype — none compatible
with the one-PE/one-root-OU/ERPNext-`Fiscal Year` model this site now runs
under (the same model NDS-CHG-001 v1.6 cut Departmental Needs over to this
cycle).

**Why it matters.** This tracker's own Decision log already records that
"Procurement Planning is not yet cut over to AUTH-ADR-001... and is two spec
versions behind approved" as a known, out-of-scope-for-NDS fact. This finding
sharpens that: it is not only Planning's *authorization layer* that is behind
— Planning's entire test suite currently cannot execute at all against this
site's real state, meaning no one can currently get a fresh green confirmation
of *any* Planning behaviour, including functionality (direct requirements,
mixed-origin DPP) that predates and is unrelated to the AUTH-ADR-001 cutover
itself.

**Why this was not fixed here.** Out of scope for a Departmental Needs
rebuild cycle — Planning is a separate module with its own tracker and its
own Project Owner-approved scope. This session made no change to
`kentender_procurement/procurement_planning/`.

**Fix.** A future Planning rebuild session (or an interim, narrowly-scoped
fixture repair) needs to rewrite `tests/fixtures.py::ensure_world` onto the
current site model before any of Planning's own acceptance criteria — NDS's
AC-031/034–037/045 included — can be evidenced by a live, passing test again.

---

## FU-21 — Workspace `<h1>` relabelled from "My needs" to "Departmental Needs" (2026-09-07)

**What.** NDS-UI-01's own workspace masthead literally reads "My needs" (see
`WorkspaceScreen.vue`'s original header comment); the live screen now reads
"Departmental Needs" instead. This is a deliberate, cross-module product
decision — the Project Owner flagged that landing-page queue titles were
inconsistent across modules (NDS "My needs", Requisitions "Your
Requisitions", Planning "Your work", Strategy "My work" vs. neutral titles
elsewhere) and asked for a single neutral convention everywhere. NDS's own
`<h1>` now matches the module-name-as-page-title pattern already used by
Procurement Requisitions and Planning's own headers, rather than being
corrected against NDS-UI-01's literal copy.

**Why this was not fixed here [via a spec correction].** The artboard itself
is not wrong for what it was asked to show at the time; this is a later,
explicit cross-module tone decision, not a defect in NDS-UI-01. The same
session relabelled Procurement Requisitions ("Your Requisitions" →
"Requisitions"), Procurement Planning ("Your work" → "Actions") and
Strategy's My Work tab label ("My work" → "Actions", route slug and the
underlying `kt_my_work_providers`/`my_work` aggregator feature name
untouched) for the same reason — see each module's own FOLLOW_UPS.

**Fix.** None outstanding. No test in this repo hardcoded the old "My needs"
string (confirmed by repo-wide grep before the edit), so nothing else needed
updating; NDS-UI-01's next revision should simply record the corrected copy.

## FU-22 — `DepartmentalNeedsPageRolesTest` contradicts the Page's empty role list (2026-09-11)

`test_departmental_needs_navigation.DepartmentalNeedsPageRolesTest` asserts the
`departmental-needs` Page names every §6 business role and none of the §1.1
removed ones. Commit `b81f5ccc` (2026-09-05, graceful Forbidden panel, KT-STD-001
§3A) emptied that Page's role list — the convention every KenTender Vue-in-Desk
Page now follows: reaching Desk is the only gate, each module's contracts decide
what a role may read or do, and a refusal renders as the in-page Forbidden state
rather than the framework popup. Two of the three tests have failed since. The
test, not the Page, is stale: rewrite it to assert the §3A behaviour (a removed
role opening the Page gets the Forbidden state and no record data) or retire it.
Found on 2026-09-11 while verifying the returned-Need correction route; left as is
because the choice between the two is the module owner's.

## FU-23 — the workspace has no Financial Year filter (2026-09-11) — CLOSED 2026-09-15

NDS-CHG-001 v1.10 §11.2 specifies a filter row of Search / Status / Financial
Year (showing "All financial years") / Clear filters, and §12.1 names
department and FY as optional filters; `WorkspaceScreen.vue` renders Search,
Status and Clear filters only ("status is the only filter" in its own comment).
Found on 2026-09-11 while auditing v1.9 against the build for v1.10; left open
because a second-FY fixture does not exist on the canonical site yet, so the
filter would ship untested.

**Closed**: delivered in the v1.13 usability pass (NDS-CHG-001 tracker
NDS13-301) — the workspace's §11.1 filter row now includes a Financial Year
`<select>`, client-side against the already-loaded list. Live-verified as
Grace and again in the Phase 4 golden-path walkthrough (NDS13-404).

## FU-24 — technical read is now centralised in KT-STD-001 (2026-09-11)

Technical read is now stated once in KT-STD-001 v1.5 §3A.6 (11 Sep 2026). At
this module's next version: replace its own technical-read prose, roles-table
row wording, Forbidden carve-out and any masking clause's silence about
technical readers with a citation of §3A.6; update AUTH-ADR-001 citations to
v1.8.

## FU-25 — Two more AUTH-ADR-001 §16.3 steps have no checked-in regression (2026-09-15)

**What.** Auditing the NDS-CHG-001 v1.13 §16.3 AUTH-ADR-001 v1.7 correction
slice against the v1.10 cycle's own gate (`NDS-G02`) for the NDS13-CHG-001..005
usability pass found: step 8 (Cartesian-product isolation) was genuinely
missing a checked-in test and has now been added
(`test_departmental_needs_permissions.py::TestCartesianProductIsolation`).
Steps 10 (a parent-OU Head of User Department assignment covers its named
descendants but never a sibling outside that subtree) and 13 (reaching
`kentender_needs_submission_closes_at` has the same effect as a manual close,
including a command issued after close but before page reload) remain exactly
where the v1.10 tracker left them — implemented in `context.py`/the shared
resolver's `descendants_of`, live-verified once, never asserted by an
automated test. Step 9 (multi-Fiscal-Year browsing) is the same gap FU-19
already names as NDS-AC-050.

**Why it matters.** Same blind-spot class this module has hit twice before
(NDS-509/510, NDS-713's two Playwright-only defects): correct-by-inspection
code with no regression to catch a future change that breaks it silently.

**Why not fixed here.** Step 10 needs an Organisation Unit tree with a real
parent/two-descendants/sibling shape and step 13 needs a controlled
close-instant fixture; neither is required by NDS12-AC-*/NDS13-AC-* (this
cycle's own acceptance criteria) and building either is pre-existing
regression debt, not part of the §11/§12.10 screen rewrite this cycle exists
to deliver.

**Fix.** A future session scoped for it: a permission test using the site's
real OU tree (or a disposable one) to prove `descendants_of` includes the two
named descendants and excludes a sibling; a lifecycle test that sets
`kentender_needs_submission_closes_at` to a near-future instant, advances the
clock past it, and asserts create/submit are refused before the hourly
`close_due_needs_submissions` job has run.

**CLOSED 2026-09-19 (NDS-CHG-001 v1.14).** Both steps covered:
1. Step 10 — this site's real Organisation Unit tree is flat (confirmed by
   direct query: no `Organisation Unit` has a `parent_org_unit`), so a
   real-tree test would need to build disposable tree data, which is
   `kentender_core`'s tree-doctype territory, not this module's. Instead,
   `TestParentOrganisationUnitCoversDescendantsNotSiblings` in
   `test_departmental_needs_permissions.py` mocks
   `kentender_core.services.authorization.descendants_of` to prove NDS's own
   `require_review_command` actually consults the shared resolver's
   descendant set (covers two named units, excludes a third) rather than
   only ever comparing for an exact OU match.
2. Step 13 — `TestAutoCloseInstant` in `test_departmental_needs_lifecycle.py`
   opens a window with `closes_at` 1.5 seconds in the future, sleeps past it
   with real wall-clock time (no mocked clock), and confirms both create and
   submit are refused with `NDS_INTAKE_NOT_OPEN` — proving
   `needs_submission_state`'s direct instant-comparison (already correct
   code, per its own docstring) with a real regression, not just a read.

---

## FU-26 — Four pre-existing test failures found running the full NDS suite during the v1.13 screen rewrite (2026-09-15)

**What.** Running all 11 Departmental Needs Python test files individually
while verifying Phase 3A/3B of the v1.13 screen rewrite surfaced four
failures, none in a file this cycle touched and none caused by it:

1. `test_departmental_needs_architecture.py::test_planning_never_touches_a_needs_table`
   — `procurement_planning/services/plan_read.py` calls
   `frappe.get_value('Departmental Need Decision', ...)` directly, a real D1
   architecture-boundary violation in Planning's own code (reads a Needs
   table instead of the published contract).
2. `test_departmental_needs_my_work.py::test_an_author_notification_still_opens_the_record`
   — a Returned-need author notification link already pointed at
   `/app/departmental-needs/{ref}/edit` instead of the plain detail route
   before this session began.
3/4. `test_departmental_needs_static_scan.py::test_partially_included_is_gone_from_the_projection`
   and `::test_the_module_defines_exactly_the_section_4_doctypes` — both
   fail because `Need Planning Disposition Projection` (§4.8's disposition
   projection doctype, and its `Not proceeding` value) isn't in this test's
   `PERMITTED_DOCTYPES`/expected-values allowlists. That doctype predates
   this session (built for the PLN-CHG-001 v1.18 disposition work, see
   FU-07 below) — the static scan was simply never updated to match.

**Why not fixed here.** (1) is Planning-owned code; (2) is a notifications
routing decision unrelated to the screen rewrite; (3)/(4) are stale
allowlists for a doctype this cycle didn't introduce. Fixing any of them
would be scope creep into work this usability cycle doesn't own.

**Fix.** A future session scoped for it: Planning reads accepted Needs
through `get_current_accepted_need`, never the Decision table directly;
confirm the correct notification target for a Returned need with the
Project Owner; update the static scan's allowlists to include `Need
Planning Disposition Projection` and its `Not proceeding` value.

**Update 2026-09-15, Phase 3C.** A fifth pre-existing failure, same class:
`test_departmental_needs_domain_model.py::test_accepted_seed_need_points_at_its_accepted_version`
expects `NDS-MOH-2027-0001.current_accepted_revision == "...-V001"` but the
live site has it at `...-V002` — the canonical Need already has a real
accepted successor on it, from work that landed on this site before this
session began (this session only read the Need and added/removed disposition/
usage projection test rows, cleaned up after, never touched its lifecycle).
The site's canonical data has drifted from what the seed/tests assert; a
`make seed-canonical` reseed would fix it but was not run mid-cycle to avoid
disrupting in-progress verification — flagged for the Phase 4 release-gate
pass instead.

**Update 2026-09-19 (NDS-CHG-001 v1.14).** Of the five items: (3)/(4) closed
— `PERMITTED_DOCTYPES` gained `Need Planning Disposition Projection`, and a
second, previously-unnoticed static-scan gap in the same test file was found
and fixed alongside it: `test_partially_included_is_gone_from_the_projection`
still asserted the `usage` field's options were exactly `["Not included",
"Fully included"]`, stale since PLN-CHG-001 v1.12 §4.4 added `Not
proceeding` to that same field (confirmed against the live DocType JSON
before changing the assertion). The domain-model flake — item 5 above — is
**confirmed resolved**: `NDS-MOH-2027-0001.current_accepted_revision` reads
`...-V001` again (a live query 19 Sep 2026, and a clean `test_
departmental_needs_domain_model.py` run, 24/24), a side effect of `db1e7c6a`'s
canonical-seed fixes, not a change made this cycle. Items (1) Planning's
`plan_read.py` boundary violation and (2) the notification-link routing
question remain exactly as written — still reproduced this session, still
not this module's to fix.

---

## FU-27 — Four NDS-DES-07A Planning-status variants need a new async boundary or a revision lookback (2026-09-15)

**What.** NDS-CHG-001 v1.13 §11.8A specifies 9 Planning-status variants for
the accepted-Need detail screen. 5 are shipped (NONE, PROCEEDING, EXCLUDED,
STILL-ACTIVE, RESTORED — all pure combinations of the existing disposition +
usage projection reads, verified live). 4 are not:

1. **REFRESHING** / **UNAVAILABLE** / **UNAVAILABLE-NO-SNAPSHOT** — these are
   about the Planning-status *read itself* failing or being slow, independent
   of the rest of the page (which loads fine). Today, usage/disposition are
   bundled into the one atomic `get_need()` call the whole detail screen
   waits on — there is no separate loading/error boundary for just this
   section to be in. Building these needs a real architecture change: a
   second async fetch (with its own pending/retry state) for planning status,
   not a template port.
2. **OLDER** — shows an *earlier* accepted revision's Planning facts when a
   newer revision has been accepted but Planning hasn't caught up yet. The
   current reads (`planning_usage_detail`/`planning_disposition_detail`)
   only ever look at the Need's *current* `current_accepted_revision`; there
   is no lookback across a Need's prior accepted revisions' own projections.

**Why not fixed here.** Both are genuine new capabilities, not visual
fidelity work — the kind of change this usability cycle's own scope
(§20: "introduces no new business field, approval stage, role, module or
prototype stack") is meant to stay clear of. Building them properly means
touching the read contracts' shape, not just the Vue templates.

**Fix.** A future session: split the Planning-status read into its own
whitelisted call with independent loading/retry state (closes
REFRESHING/UNAVAILABLE/UNAVAILABLE-NO-SNAPSHOT); extend
`planning_usage_detail`/`planning_disposition_detail` (or add a sibling read)
to walk back through a Need's accepted-revision history when the current
revision has no projection yet (closes OLDER).

**Update 2026-09-15, Phase 3E.** The withdrawal review screen (NDS-DES-12)
has the identical gap: `check_accepted_need_withdrawal_dependency` returns
`included`/`active_plan`/`active_plan_item` only — there is no way for it to
say "the check itself failed" (NDS-DES-12-UNAVAILABLE) as opposed to "checked,
not included" (CLEAR). Same fix category: the read needs a distinguishable
failure/unavailable result (or the command needs to let a failure propagate
as a typed, catchable state) before that variant can be built.

**Update 2026-09-19 (NDS-CHG-001 v1.14) — backend and UI built, formal test
coverage split out as FU-31.** All 5 variants now have real logic and a real
UI:
- `services/usage.py::planning_status_for_need` — a new whitelisted read
  (`get_need_planning_status`), separate from `get_departmental_need`'s
  atomic payload, fetched by the client as an independent, retriable
  revalidation. `planning_usage_detail()` gained a `recorded` boolean
  (mirroring `planning_disposition_detail`'s existing one) so "never
  checked" is distinguishable from "checked, not included" — this is what
  makes UNAVAILABLE-NO-SNAPSHOT representable at all.
- `services/usage.py::older_revision_usage()` — walks a Need's
  `REVISION_SUPERSEDED` revisions newest-first for the first one Planning
  reported `Fully included`, returning that revision's own 6 content fields
  too, so "View earlier requirement" can render inline (a disclosure toggle
  reusing `RequirementCard`, not a new route/screen).
- The same failure-signal pattern (try/catch → `{unavailable: true}` →
  distinguishable UI state + Try again) was applied to
  `check_accepted_need_withdrawal_dependency` for DES-12-UNAVAILABLE.
- `NeedDetailScreen.vue`/`WithdrawalReviewScreen.vue` render all 5 states
  with the exact §11.8A/§11.13 copy; `DepartmentalNeeds.vue` orchestrates the
  revalidation calls.
- **Genuinely not done**: no fixture builder in `playwright_ui_fixtures.py`
  for any of these 5 states (none of the named `NDS-SC-DISPOSITION-*`
  profiles exist in seeds, confirmed again by grep), and no Playwright spec
  exercises any of them — REFRESHING needs a route-delay, the three
  UNAVAILABLE variants need a route-abort/500. Only live-verified manually
  for the 5 unaffected (already-shipped) variants plus a general smoke check
  that nothing broke. See the new **FU-31**.

---

## FU-28 — Two visual baselines carry a live "requested/submitted at" timestamp and drift on every re-run (2026-09-15)

**What.** `nds-des-06-review-task` and `nds-des-12a-withdrawal-blocked` each
show a "Submitted at"/"Requested at" fact sourced from `now_datetime()` at
fixture-build time — not a fixed date. Re-running the visual suite at a
different wall-clock moment than the baseline was shot produces a small
(≈0.01 ratio) pixel diff purely from that one line's changed text, with no
other change on the page. Hit twice this session (both baselines needed a
second re-shoot for exactly this reason, confirmed via the diff size and
unchanged image dimensions).

**Why not fixed here.** `ReadonlyRow.vue`'s existing `data-volatile` masking
convention (`departmental-needs-visual.spec.ts` already masks other volatile
instants) is the right fix, but neither screen's live timestamp fact is
currently rendered through `ReadonlyRow` after the v1.13 rewrite — both use a
plain `<span>`. Wiring the mask through touches the visual-regression
harness itself, out of scope for this screen-redesign cycle.

**Fix.** A future session: give the live "Submitted at"/"Requested at"
elements a `data-volatile="true"` attribute (matching `ReadonlyRow`'s own
convention) and confirm the visual spec's existing volatile-masking logic
picks them up.

**CLOSED 2026-09-19 (NDS-CHG-001 v1.14).** `data-volatile="true"` added
directly to `ReviewTaskScreen.vue`'s "Submitted at" value and
`WithdrawalReviewScreen.vue`'s "Requested at" value. Confirmed by re-shooting
both baselines: the regenerated images show the value masked (a solid
magenta box) exactly where the volatile-masking convention is expected to
apply it. Full visual spec re-run afterward: 6/6 green.

---

## FU-29 — CLOSED 2026-09-15 — UI-driven Playwright fixtures leaked ~1,000 untagged Needs into the site

**What.** A Phase 4 release-gate DB audit found only 4 genuinely canonical
`Departmental Need` rows (`NDS-MOH-2027-0001..0004`, tagged
`fixture_namespace=KENTENDER_MVP_1_R1_NDS`) against 925 untagged rows
matching the real `NDS-MOH-2027-####` reference pattern plus 75 more matching
`NDS-TEST-*` — all `fixture_namespace IS NULL`, invisible to
`clearFixtures()`/`reset_all()`. Visible live impact before the fix: the
workspace register showed "829 needs" instead of ~4, and a Head of
Department's decision queue showed the same fixture title duplicated 9 times.

**Root cause.** The `need_reference` counter is site-wide (AUTH-ADR-001 v1.7
§1.1 — one implicit Procuring Entity, one open Fiscal Year), and
`departmental-needs-fidelity.spec.ts`'s DES-04/08/09 tests reach their target
states through genuine UI create/submit/propose-change clicks rather than a
namespaced fixture builder — each one mints a brand-new `Departmental Need`
nothing ever stamps for cleanup. This session's many live-actor browser
verification passes across Phase 3 did the same thing by hand.

**Fixed.** Added `purge_untagged_needs_since(since, commit=True)` to
`playwright_ui_fixtures.py` (mirrors the existing `purge_fixture_needs`/
`reset_all` pattern: direct `frappe.db.delete`, bypassing
`Departmental Need.on_trash()`'s retention guard the same way those helpers
already do; cascades across all 7 `_NAMESPACED` doctypes plus
`Need Planning Disposition Projection`, which links back to a Need but isn't
in that tuple, and `Notification Log`). Wired into the fidelity spec's own
`test.afterAll` via new `siteNow()`/`purgeUntaggedNeedsSince()` helpers in
`helpers.ts`, so every future run self-cleans whatever it created.

A second bug surfaced while wiring this in: the first version captured the
cutoff with JavaScript's `Date.toISOString()` (UTC-labelled), but `creation`
is stored as a naive **site-local (EAT)** timestamp — the UTC cutoff read
about 3 hours earlier than intended and over-deleted (harmlessly, since
canonical rows stay protected by the namespace filter regardless of the
timestamp). Fixed by adding `now_marker()` (wraps `frappe.utils.now()`) to
`playwright_ui_fixtures.py` and having the spec read the site's own clock
instead of a JS one.

Historical leaked data (the full ~1,000 rows) was cleaned up as part of
closing this out; a DB check immediately after confirmed the site holds
exactly the 4 canonical Needs. See NDS-CHG-001 tracker NDS13-406.

---

## FU-07 — PLN-CHG-001 v1.18 disposition event (opened 2026-09-12)

Planning emits `NeedPlanningDispositionChanged.v1` (event_id, schema_version, producer_sequence, need_id, need_revision_id, dpp_submission_id, disposition, reason when excluded, actor, decision_at) after a departmental submission is **accepted** with a Need marked not proceeding. Departmental Needs consumes it into a `Need Planning Disposition Projection` and shows it as Planning information on the Need; it is separate from `NeedPlanningUsageChanged.v1`, whose `Fully included` / `Not included` / `Not proceeding` semantics are unchanged (a DPP exclusion never clears an existing Active dependency). Code lands under Planning tracker row PLN18-108; NDS-CHG-001 v1.11 (§4.7, §7.2) is owed. See `docs/mvp-1-r1/04_planning/PLN-CHG-001_FOLLOW_UPS.md` FU-24.

---

## FU-30 — `bench run-tests` does not roll back on this bench (found 2026-09-19)

**What.** Discovered mid-NDS-CHG-001 v1.14: `bench --site kentender.midas.com
run-tests --app kentender_procurement --module <file>` does **not** wrap the
run in a transaction that gets rolled back afterward, contrary to the
default/expected behaviour of Frappe's `IntegrationTestCase`. Every write a
test makes — a created `Departmental Need`, a `frappe.defaults.set_user_default`
call, a disposable `User`/`Fiscal Year` doc — persists for real on the site,
across the whole run and across separate invocations. Confirmed directly: a
single full run of `test_departmental_needs_lifecycle.py` (73 tests) alone
left ~200 real `Departmental Need` rows; running the full 11-file suite
across one session left 643.

**Why it matters.** Every existing test file in this module already assumes
this (namespaced grants get `revoke()`d in `addCleanup`, and the module's own
Playwright fixture layer has an elaborate `purge_fixture_needs`/`reset_all`/
`purge_untagged_needs_since` apparatus) — but nothing said so in one place for
the *Python* suite specifically, and the assumption is easy to miss when
writing a new test that reads or asserts on real counts (`frappe.db.count`,
`get_needs_workspace`'s row count, a `selectable_financial_years()` list)
against what should be a clean canonical baseline.

**Fix applied this session, not a general fix.** After every Python test run
that could have created `Departmental Need` rows, called
`kentender_procurement.departmental_needs.seeds.playwright_ui_fixtures.purge_untagged_needs_since`
with an early cutoff (`'2020-01-01 00:00:00'`) via `bench execute`, confirmed
back to exactly the 4 canonical rows each time. Also found and fixed a
related persistence surprise: `frappe.defaults.set_user_default` (the
CTX-CHG-001 remembered-Financial-Year mechanism) also does not roll back,
and a stale value from an earlier failed test attempt broke an unrelated
later test in the same file until reset directly.

**Not fixed.** The runner's own transaction behaviour is out of this
module's control (and possibly intentional — `IntegrationTestCase` may be
deliberately commit-based on this bench, as distinct from a lighter-weight
unit-test base class). A future session should: (a) treat every Python
`bench run-tests` invocation on this bench as commit-for-real, exactly like a
Playwright run, and purge afterward; (b) consider whether a `tearDown`/
`addClassCleanup` hook belongs on `DepartmentalNeedsCommandCase` and its
siblings to make this automatic rather than relying on a human to remember.

---

## FU-31 — DES-07A's 4 new Planning-status variants and DES-12-UNAVAILABLE have real logic but no Playwright regression (2026-09-19)

**What.** NDS-CHG-001 v1.14 built the genuine missing capability FU-27 named
— a dedicated, independently-retriable Planning-status read
(`get_need_planning_status`), a revision-lookback helper
(`older_revision_usage`), and the equivalent failure-signal treatment for the
withdrawal-dependency check — and wired all 5 resulting UI states
(REFRESHING, UNAVAILABLE, UNAVAILABLE-NO-SNAPSHOT, OLDER,
DES-12-UNAVAILABLE) into `NeedDetailScreen.vue`/`WithdrawalReviewScreen.vue`
with the exact §11.8A/§11.13 copy. What it did **not** build:

1. Fixture builders in `playwright_ui_fixtures.py` for any of the 5 states —
   none of the named `NDS-SC-DISPOSITION-*` §14.6A profiles exist in seeds
   (reconfirmed by grep, same finding as NDS13-201).
2. A Playwright spec exercising any of them. REFRESHING needs a
   `page.route()` delay on `get_need_planning_status`; UNAVAILABLE and
   UNAVAILABLE-NO-SNAPSHOT need a `page.route()` abort/500 on the same
   endpoint (with/without a prior successful projection, respectively);
   DES-12-UNAVAILABLE needs the same treatment on
   `check_accepted_need_withdrawal_dependency`; OLDER needs a real
   successor-accept-then-project-on-the-superseded-revision fixture (the
   exact sequence `test_older_revision_usage_walks_back_when_current_
   revision_is_unprojected` in `test_departmental_needs_lifecycle.py`
   already proves works at the service layer — a Playwright fixture would
   reuse the same command sequence).

**Why not fixed here.** This was already the single largest, most
architecturally novel item in the v1.14 cycle (its own tracker risk R1);
building 5 new fixture profiles plus 5 new route-mocked Playwright tests
was judged to be starting a second cycle's worth of work rather than
finishing this one, and the session was explicitly told not to loop
indefinitely. The backend is real, unit-tested where it can be
(`older_revision_usage`, 2 tests, green) and live-verified manually for the
unaffected 5 variants plus a general regression sweep (no console errors, no
existing-spec breakage) — but NDS13-AC-006/AC-008 stay `Partial`, not `Done`,
until this lands.

**Fix.** A future session: build the 5 fixtures, write the 5 (or more,
per-variant) Playwright tests using route interception for the failure
cases, then flip NDS13-AC-006/AC-008 to `Done` in the tracker.

---

## FU-32 — AC-048's inline multi-department flow has a Python contract test but no Playwright spec (2026-09-19)

**What.** `TestCreateTargets` in `test_departmental_needs_contracts.py`
(added this session) proves `list_need_create_targets`'s multi-OU return
shape using Grace's real two-OU grant. No Playwright spec drives the actual
`/new` inline DES-15 selector through a two-OU actor — the Playwright
`AUTHOR` fixture persona is single-OU only (same structural gap FU-19
originally named for the now-retired `CreateTargetDialog`), so the existing
Playwright suite cannot structurally reach the MULTIPLE-department branch of
`NeedEditorScreen.vue` at all. NDS13-302's own evidence records a one-time
manual browser verification of this exact flow as Grace (both departments
offered, Save draft/Submit for review disabled until one is chosen), but
that was never captured as a checked-in spec.

**Fix.** A future session: add a two-OU Playwright fixture actor (or grant a
second OU to the existing `AUTHOR` fixture persona) and a spec asserting the
inline multi-select disable/enable behaviour and successful create.

---

## FU-33 — `test_departmental_needs_navigation.py` is stale against the live sidebar/role configuration (found 2026-09-19)

**What.** Running the full Python suite for NDS-CHG-001 v1.14 surfaced 6
failures/errors in `test_departmental_needs_navigation.py`, none touched by
this cycle and none present in any file this cycle edited:

1. `test_module_sits_after_budget_and_before_planning` — looks for a sidebar
   entry labelled exactly "Procurement Plans"; the committed
   `workspace_sidebar/procurement.json` (confirmed via `git diff`, clean —
   not a local uncommitted change) has renamed it to "Procurement Planning"
   at some point before this session.
2. `test_page_is_registered_once_with_its_own_controller` — expects
   `hooks.py`'s `nds_page_js` dict to have exactly one entry
   (`departmental-needs`); it has had a second, unrelated entry
   (`departmental-procurement-plan`) committed since at least 5 Sep 2026
   (confirmed via `git log` on that file — also not caused by this session).
3. Four `test_every_section_6_business_role_may_open_the_page` subtests
   (`Departmental Author`, `Head of User Department`, `Procurement Planner`,
   `Auditor`) — the sidebar row's own role-visibility set reads empty,
   presumably the same sidebar-file drift as (1).

**Why it matters.** Same class as `procurement-sidebar-g0012-preexisting-drift`
(memory) — a sidebar/label rename in Procurement Planning's own scope left
this module's navigation test uninformed. Not a Departmental Needs defect.

**Why not fixed here.** Fixing it means deciding the *correct* current label
and role set for Procurement Planning's own sidebar entry, which is that
module's call, not this cycle's (§11/§12.10 design-fidelity and Planning-
status scope named at the top of this tracker's own plan).

**Fix.** A future session, scoped to Procurement Planning or navigation
hygiene generally: update `test_departmental_needs_navigation.py`'s
expectations to match the current sidebar file, or fix the sidebar/role
configuration if the rename was itself unintentional — whichever the module
owner confirms is correct.
