# Departmental Needs — NDS-CHG-002 implementation plan

**Authority:** `KenTender_NDS-CHG-002_Departmental_Need_Capture_Items_and_Submission_v0.1.md` (referred to below as "the spec"), read in full 2026-08-21.
**Depends on:** NDS-CHG-001 v0.2, already substantially delivered via `06_Departmental_Needs_Greenfield_Rebuild_Tracker.md` (RBD-401..414, all Done as of 2026-08-20).
**Companion tracker:** `08_Departmental_Needs_NDS-CHG-002_Implementation_Tracker.md`.
**Build posture:** the spec mandates greenfield, no-migration, no-compatibility-shim delivery (§9) — same discipline already applied to STR-CHG-001 and BUD-CHG-001 in this repo.

## 1. Current-state findings (in place of a separate audit report)

A full read-only investigation of `kentender_procurement/kentender_procurement/departmental_needs/` (doctypes, services, api.py, UI assets, seeds, tests) found that NDS-CHG-001's rebuild delivered far more than its own tracker rows advertise:

**Already built and working:**
- Three real doctypes: `Departmental Need` (header, 6-state lifecycle matching the spec exactly: Draft/Submitted/Returned/Accepted for planning/Not taken forward/Withdrawn), `Departmental Need Item` (a genuine item/line doctype — not a stub), `Departmental Need Review` (an immutable audit-event doctype, `before_save`/`on_trash` both hard-throw except on insert).
- A full command layer in `services/lifecycle.py`, whitelisted through `api.py`: `create_need`, `update_need`, `submit_need`, `review_need` (accept/return/decline folded into one function via a `decision` parameter), `withdraw_need`, `request_withdrawal`, `approve_withdrawal`. All ten `api.py` functions are genuinely whitelisted (a real bug here was found and fixed under RBD-401).
- Working idempotency-key replay (`_existing()` looks up a `Departmental Need Review` row by a globally-unique `idempotency_key` field and replays the prior result) and a working optimistic-concurrency check (`concurrency_token`, regenerated on every state-changing write, checked via `_check_token()`).
- A reference-number generator (`_next_reference()`) using a MySQL named lock per PE+FY to serialize sequence allocation — concurrency-safe.
- Full PE/OU/FY-scoped capability wiring through `kentender_core.services.authorization_policy` (the same system `kentender_budget`/`kentender_strategy` use) — six capability strings, an audited support-read path (`get_support_need()` via `authorization_diagnostics.authorize_support_record_view`) already matching the spec's §8.4 support-read rule.
- The NDS-UI-01 workspace page: pixel-fidelity verified against its mockup, 5/5 Playwright specs passing, 11/11 Python tests passing across 3 test files.

**Not built at all:**
- All three of NDS-CHG-002's own screens (§7.1–7.3: Create, Returned-correction, Review). Every workspace row action ("Create need", "View", "Edit", "Review") is wired to a single handler that shows a placeholder toast — *"This Departmental Needs interaction is awaiting its approved detailed screen contract"* (`departmental_needs_page.js:364,368`). No `/departmental-needs/new`, `/{ref}`, `/{ref}/edit`, `/{ref}/review` routes exist anywhere.
- Supporting documents / attachments (spec §3.3): zero doctype, zero malware-scan/quarantine model, zero SHA-256 digest, zero 10-file/20MB enforcement. A from-scratch build.

**Built, but with concrete gaps against the spec's exact rules:**
- **NDS-FR-023 (partial draft save) is not honored.** `create_need`/`update_need` currently require the *full* header field set (title, business_justification, required_by_date, delivery_or_use_location) plus at least one valid item on first save. The spec requires only "context and title" to be valid for a Draft save — everything else may be incomplete until submission.
- **Reference format is 3-digit, not 4-digit.** Generator produces `NDS-MOH-2027-001`; spec (§3.1, §10.2 fixtures) requires `NDS-MOH-2027-0001`.
- **`unit_code` is an open Link to the generic `UOM` doctype, not the closed 10-value enum** (Each/Set/Lot/Person/Staff/Month/Day/Service/Programme/Other) **+ `other_unit` free-text field** the spec requires.
- **No `revision_no` field.** The spec requires it to start at 1 on first submission and increment on each resubmission; nothing in the current schema or lifecycle tracks this.
- **`record_version` is implemented as `concurrency_token`** — an opaque, regenerated-per-write string, not a monotonic integer. Functionally equivalent for stale-write detection (which is all NDS-FR-041/§5 actually require) — **confirmed, not renamed**, matching this repo's established "don't force a disruptive rename onto a working, differently-shaped mechanism" precedent (BUD-CHG-001 Phase 8/9). Flagged in the tracker for visibility, not treated as a gap to close.
- **`currency_code` is a free Link to `Currency`,** not fixed/uneditable to KES as the spec requires for MVP-1.
- **No `need_id` UUID primary key** — the doctype uses `need_reference` as its Frappe `name`/PK directly. This is an internal identity-modeling choice with no observable behavioral consequence (Frappe's `name` already serves as an immutable PK); **confirmed, not rebuilt**, same reasoning as `record_version` above.
- **Capability strings partially diverge**: `submit_own`→spec's `submit`, `planning_read`→spec's `read_accepted_for_planning`, `support_read` is implemented as a generic support-record-view capability on a dedicated profile rather than the literal string `departmental_needs.support_read`. Functionally these already gate the right actions; this is a naming reconciliation, not new authorization logic.
- **Audit events don't capture §8.4's full field set.** `Departmental Need Review` records actor/prior-state/result-state/reason/timestamp/idempotency-key — real and working — but not "effective assignment, request identifier, source IP/session, or before/after state hashes" as §8.4 explicitly lists. Unlike the `record_version`/`need_id` items above, this is called out in the spec's *Implementation controls* section as a mandatory build rule for a still-in-progress module, not a legacy shape to tolerate — scoped as real work below, not confirmed-and-left.
- **Seed data is 3 of 6 required Need states** (Accepted/Submitted/Returned exist; Draft/Not taken forward/Withdrawn don't have durable seed fixtures — those transitions are only exercised ad hoc inside test code). **The Departmental Review Delegate persona (`julia.njeri@moh.example.test`) has no durable seed fixture at all** — it's created inline inside one test (`test_departmental_needs_completeness_gaps.py`), not the shared seed file.
- **No test explicitly proves** "the submitting user cannot decide their own Need" (NDS-FR-031/AC-028) as a direct assertion — it's currently true only as an emergent property of task routing (a task is assigned to someone other than the submitter, so the submitter never has a task to act on). No test explicitly walks Draft→Submit→Return→Edit→Resubmit checking `revision_no` incrementing and the prior snapshot staying unchanged (NDS-FR-033/AC-030) — partly because `revision_no` doesn't exist yet.

## 2. Scope boundary

In scope: everything inside `kentender_procurement/kentender_procurement/departmental_needs/` needed to satisfy the spec's data model (§3), functional requirements (§4), validation contract (§5), the three static screens (§7), implementation controls (§8), seed data (§10), and acceptance criteria (§11).

Out of scope, explicitly, matching NDS-CHG-001's own locked boundary (`06_...Tracker.md`'s "Effort boundary" decision, which this plan inherits unless a specific NDS-CHG-002 requirement forces a narrow exception):
- Procurement Planning, Budget, Strategy, Procurement Home — none of their Demand-era dangling references are touched here.
- `Plan Need Allocation` / planning-usage projection — already correctly out of NDS-CHG-002's own stated boundary (§1: "It does not define Procurement Planning allocation...").
- NDS-CHG-003 (workspace queues/filtering/landing) — the next change unit per the spec's own §13, not this one.

## 3. Sequencing rationale

Data-model fixes (Phase 1–2) come first because the three new screens (Phase 6) and the attachment model (Phase 4) both need the corrected fields (`revision_no`, closed `unit_code` enum, 4-digit reference) to exist before UI work reads/writes them — building the screens against the current shape first would mean rebuilding them again. Validation-contract enforcement (Phase 3) comes before the screens for the same reason: NDS-FR-023's partial-draft-save fix changes what `create_need`/`update_need` accept, which the Create/Returned-correction screens (02A/02B) both depend on directly. Attachments (Phase 4) precede the screens because all three screens display supporting-document state. Capability reconciliation (Phase 5) is cheap and independent, sequenced just before the UI phase so the screens are built against final capability names, not ones about to be renamed. Seed completion (Phase 7) follows the screens because the missing seed states are most easily verified by opening the corresponding new screen. Audit/security hardening and the explicit maker-checker/resubmission tests (Phase 8) close out the remaining functional-requirement gaps once the surface they're testing is complete. Phase 9 (final verification) is last by definition, mirroring BUD-CHG-001/STR-CHG-001's own closing phase.

## 4. Phases

### Phase 0 — Baseline
Run the Departmental Needs module's full Python + Playwright test suite; record exact pass/fail/error counts as the reference point every later phase diffs against, matching this repo's established discipline for every prior change unit.

### Phase 1 — Header field reconciliation
Add `revision_no` (Int, defaults 1, incremented on resubmission per NDS-FR-033); fix the reference generator to zero-pad to 4 digits; fix `currency_code` to be fixed/read-only to KES for MVP-1 (per §3.1 — confirm no other currency is ever seeded or accepted). Explicitly confirm (not rebuild) `concurrency_token` as record_version's functional equivalent and `need_reference`-as-`name` as need_id's functional equivalent, documenting both decisions in the tracker.

### Phase 2 — Item line closed-enum
Replace `Departmental Need Item.unit` (open `Link` to `UOM`) with a closed `unit_code` Select (Each/Set/Lot/Person/Staff/Month/Day/Service/Programme/Other) plus a conditionally-required `other_unit` field (2–50 chars, required only when unit_code is Other), matching §3.2 exactly. Migrate any existing seeded/test data off the old field.

### Phase 3 — Submission validation contract
Fix NDS-FR-023: `create_need`/`update_need` must accept a Draft save once only context (PE/OU/FY) and title are valid — every other header field and all items may be incomplete. Build the full §5 validation matrix precisely for submit/resubmit: business_justification 50–2,000 chars, required_by_date required and inside target FY, delivery_or_use_location required, at least one complete item line and no incomplete item rows, indicative estimate positive with ≤2 decimals if present, all active attachments clean (depends on Phase 4). Validation failures must return stable field/business-rule error codes and must not change state, increment revision_no, dispatch work, or send a notification (matching the existing idempotency/audit discipline already in `lifecycle.py`).

### Phase 4 — Supporting documents / attachments
New doctype (or File-based model) for supporting documents: immutable identifier, original filename, size, MIME type, SHA-256 digest, uploader, timestamps; extension/MIME/file-signature agreement check; PDF/DOCX/XLSX/PNG/JPG only; max 10 active files per Need, max 20 MB per file; quarantine state that blocks submission but not draft save; logical (audit-trailed) deletion of draft attachments; submitted snapshots retain their attachment references even if a file is later logically deleted. Attachments served via short-lived authorized access only (§8.4), never public object URLs.

### Phase 5 — Capability reconciliation
Confirm each of the spec's 6 named capability strings against the current 9. Rename where the divergence is purely cosmetic and low-risk (`submit_own`→`submit`, `planning_read`→`read_accepted_for_planning`); confirm-not-rename where the current implementation's extra granularity (`view_own`/`view_department` split, a dedicated `support_read`-equivalent profile) serves the same effective access rules the spec describes — document the reasoning either way in the tracker, same "confirm substance" discipline as Phase 1.

### Phase 6 — Build NDS-UI-02A / 02B / 02C and wire the workspace
Build all three screens as Frappe Desk pages (or a shared page with mode-driven rendering, whichever fits this app's existing Stitch-page conventions — `budget_ui_fixtures`/`planning_ui_fixtures` precedent applies), hand-porting each exact fixture from spec §7 and cross-checked against the corresponding `NDS-UI-02[A|B|C].html` mockup (noting the mockups themselves have gaps against the spec — 02B's own HTML is missing its footer entirely; the MD spec's field/action tables are authoritative per this repo's established precedent, not the raw HTML). Wire routes per §8.1 (`/departmental-needs/new`, `/{need_reference}`, `/{need_reference}/edit`, `/{need_reference}/review`) and replace the workspace's placeholder-toast row actions with real navigation. Confirm every explicit-exclusion list in §7.1/§7.2/§7.3 (no procurement classification, no Plan/Requisition/Tender references, no approval stepper, no reason field on the base review screen) is genuinely absent, not just unstyled.

### Phase 7 — Seed data completion
Add the 3 missing Need states as durable seed fixtures (Draft `NDS-MOH-2027-0004`, Not taken forward `-0005`, Withdrawn `-0006`, matching §10.2's exact titles/owners/reasons) and promote the Departmental Review Delegate persona (`julia.njeri@moh.example.test`) from test-local setup into the shared seed file. Update all seed-created references to the corrected 4-digit format from Phase 1.

### Phase 8 — Audit/security hardening and explicit gap tests
Extend the audit-event capture to include request identifier, source IP/session, and before/after state hashes per §8.4 (a genuine build item, not a confirm-and-defer, since the spec lists it under mandatory implementation controls for a module still being actively built, not as an aspirational future-state note). Add an explicit test asserting a submitting user cannot decide their own Need (NDS-FR-031/AC-028) as a direct assertion, not only an emergent property of task routing. Add an explicit Draft→Submit→Return→Edit→Resubmit test asserting `revision_no` increments and the prior snapshot is unchanged (NDS-FR-033/AC-030).

### Phase 9 — Final verification
Build the full NDS-AC-020..042 coverage map (mirroring BUD-CHG-001 Phase 9's BCL-902 methodology); walk every row of §12's role-based smoke-scenario table and confirm each live; add Playwright specs for the 3 new screens; run the complete module test suite (Python + Playwright) and confirm zero regression against the Phase 0 baseline; confirm no `/demands` route or legacy Demand schema object exists anywhere (§9, NDS-AC-041 — already true per NDS-CHG-001's Phase 1 deletion, re-confirm here as a closing gate).
