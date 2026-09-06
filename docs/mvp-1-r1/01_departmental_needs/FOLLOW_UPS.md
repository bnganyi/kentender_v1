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
