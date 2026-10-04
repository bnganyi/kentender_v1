# REQ-CHG-001 v1.11 — Procurement Requisitions implementation plan

| Control | Value |
|---|---|
| Authority | `KenTender_REQ-CHG-001_Structured_Procurement_Requisitions_v1_11.md` (approved 24 September 2026; supersedes v1.9 and all earlier versions in full) |
| Design authority | `design/Requisitions - Design Board v2.dc.html` (owner-updated 24 September 2026) |
| Sibling authorities consumed | KT-STD-001 v1.7, AUTH-ADR-001 v1.9, CFG-CHG-002 v0.14, PLN-CHG-001 v1.25, BUD-CHG-001 v1.10, NDS-CHG-001 v1.14, STR-CHG-001 v1.8, LAW v1.2, SEED-001 v1.3. TPR-CHG-001 v0.9 and STD-TPL-001 v0.7 are proposed, not approved. |
| Companions | `02_REQ_Gap_Analysis.md`, `IMPLEMENTATION_TRACKER.md`, `FOLLOW_UPS.md` |
| Predecessor cycle | REQ-CHG-001 v1.6 build (6–7 September 2026), since patched to about v1.8 |
| Prepared | 24 September 2026 |
| Status | Approved by the Project Owner, 24 September 2026. D1–D4 were answered explicitly. |

## 1. Governing approach

**Correct the backend in place; re-port the UI in full.**
- v1.11 §1.1 removes nothing the code still carries: the manifest, attachment-primary specification and PE/FY scope went in v1.6. So the domain is corrected rather than rebuilt.
- The proven mechanics stay: the idempotency envelope, the authorisation predicate, the catalogue and the digest.
- The screens change shape entirely: five steps become three tasks, every board is redrawn, and new stopped, common-state and narrow families appear. AGENTS.md §6.6 forbids reusing a component for a changed artboard, so every component is re-ported from the v2 board.

**Phase order.** Phases 0–2 are horizontal: docs, owner contracts, domain. From the API layer up the work is vertical: one route goes API → screen → real browser → fidelity → Playwright before the next route starts. This follows the measured cost of batching verification last in earlier rebuilds.

**Done** means:
- every v1.11 functional requirement is proven by the named tests and a browser pass as the real actors;
- every screen matches the v2 board, structurally (`expectStructure`/`compareSkeletons`) and by text landmarks.

Non-negotiables (AGENTS.md):
- business rules live in Python services;
- every command re-checks responsibility, state, record version and idempotency on the server;
- no `frappe.db.commit()` in request services;
- Industry design system only;
- TDD for each behaviour;
- the Python suite and Playwright never run at the same time on the site.

## 2. Decision register

| # | Decision | Why |
|---|---|---|
| D1 | **Owner-side changes in Planning, Budget and Tenders happen this cycle**, each TDD'd in its owner's own suite and pinned from `procurement_requisitions/tests/test_gateway_contracts.py`. | Owner answer, 24 Sep 2026. Shared-line shortfall, one atomic authorisation and correction outcomes cannot be met on the REQ side alone. |
| D2 | **Board read-only extras are built as drawn**: Decision chain on DES-07/08/10, Correction chain on DES-11, the funding bar on DES-08, the contributor Access column on DES-03. | Owner answer. They add no action or stored field; they project decisions already recorded. |
| D3 | **Only the v2 board is authoritative.** The reappeared v1.9 board is never referenced. Board slips are recorded in `tests/ui/fidelity/departures/procurement-requisitions.js` with the spec clause that wins. | Owner updated and approved the v2 board the same day. |
| D4 | **Handoff v1.4.** The payload gains County treatment, rule-snapshot identities, `plan_item_version_id`, `strategic_objective_id` and exact-string Money/Quantity. Event name `ProcurementRequisitionAuthorised.v1.4`. The Tenders reader is updated in the same change. Stored v1.3 handoffs are never rewritten or rehashed. | Owner answer. v1.11 §5.14 forbids two undocumented shapes under one name. |
| D5 | **Exact precision storage**: Money is stored as `Data` holding a canonical decimal string at KES scale 2; Quantity as `Data` holding a whole-number string for Each. The new `services/precision.py` parses to `decimal.Decimal`, rejects floats, exponents, NaN, excess scale and overflow (18 integral digits), and never rounds. Every comparison and total uses `Decimal`. | §5.14. Frappe `Currency`/`Float` fields round-trip through Python floats (`flt`), which v1.11 forbids. |
| D6 | **One transaction for authorisation.** Owner services (`check_funding`, `reserve_funding`, `authorise_requisition_drawdown`) are called in-process and never commit. REQ wraps the whole command in `envelope.atomic()`; any exception rolls back every effect. Planning takes all allocations in one call. | §7.2, §9.1A step 4. One database, one process: removing inner commits is enough; no distributed protocol is needed. |
| D7 | **Budget reservation identity** = one Funding Reservation per REQ drawdown line, keyed by `(calling_module, caller_reference, drawdown_line_id)`. The line check totals every row that shares a Budget Line before comparing with availability. | §9.1A steps 1–3; fixture 20m + 30m against 40m → 10m shortfall. |
| D8 | **Planning outcome delivery.** Planning's terminal dispositions build a `PlanItemCorrectionOutcome.v1` payload (§9.1B fields, monotonic `producer_sequence` per request) and hand it to REQ's `record_plan_item_correction_outcome` in the same disposition transaction. REQ authenticates the producer as the Planning service caller, deduplicates on event_id + payload digest, and quarantines conflicts as `REQ_CORRECTION_EVENT_INVALID`. | §9.1B. The two apps share one bench, so an in-transaction handoff is the outbox for this release, with the exact schema as the contract. |
| D9 | **Standard package** `LAPTOP-REQUIREMENTS-V1` is a code constant in `catalogue.py` with the exact §13.1 rows. Proposals are stored as `row_state = Proposed` rows; `ApplySelectedRequirementPackage` validates the posted proposal key/version and Draft record_version, then atomically replaces Proposed rows with Confirmed ones and marks the package `Reviewed`. | §6.4, §10.2. No Desk configuration surface. |
| D10 | **Lead change** is a return: `ChangeRequisitionLeadDepartment` records a Decision (`Changed lead and returned`), marks the submitted Version `Returned`, and copies a Draft whose `lead_org_unit_id` is the directive. `certified_lead_org_unit_id` is frozen on the submitted Version. | §7.3A. |
| D11 | **Tenders consumption.** Tenders calls `record_handoff_consumption` inside `StartTender`. REQ locks the handoff row, rechecks Authorised and unconsumed, binds the Tender. Same Tender replays; a different Tender raises `REQ_HANDOFF_CONFLICT`. `release_handoff_consumption` is deleted; the Tenders correction path is re-routed so it never un-consumes a handoff. If re-routing needs a TPR behaviour decision, the owner is asked. | §9.2, §7.4. |
| D12 | **Fidelity harness.** `tests/ui/fidelity/board.js` gains `requisitionsScope(doc, id, variant)` (frames are `div#desNN` → `.kt-panel-lg` / `.dialog`; variants are the `.sub`-headed frames; `.cap`/`.sub` annotations stripped). A departures registry and COVERED list are added; `--project procurement-requisitions` joins `make ui-structure-gate`. The browser spec is rewritten against the v2 board. | AGENTS.md §6.6; `design-fidelity-structural-gate`. |
| D13 | **Class porting.** `btn/dialog/field/table/input` → `kt-btn/kt-dialog/kt-field/kt-table/kt-input` (the existing alias convention). `seg`/`seg-opt`/`date-field` are promoted from `kt_admin_configuration.css` into `kt_industry_tokens.css`. `card-meta` → `kt-field-hint`. `kt-panel-lg` is the page frame. | One design system; no per-module copies. |
| D15 | **Tenders may break (owner, 24 Sep 2026).** "The Tender module will be revamped as a follow up to this. Make Requisitions complete even if it breaks Tender." REQ v1.11 is built literally: `release_handoff_consumption` is deleted, consumption is guarded, revocation after consumption is refused. Tenders gets only the minimum to stay importable and migratable; its correction route (release → revoke → re-authorise) and any Tenders test depending on it are expected to fail until the Tenders revamp. Supersedes the Tenders half of D1 and D11. | Owner answer. |
| D14 | **Dev data.** Existing dev Requisition rows are wiped and reseeded through commands (standing dev-site teardown permission); no migration of dev rows. Production cutover rules in §20 are recorded but not exercised. | §20; dev site policy. |
| D16 | **Stand-in consumption for demo profiles (owner, 24 Sep 2026).** The §16.4A profiles that need a consumed handoff (SCOPE-LOCK, SEQUENTIAL, REVOKE-CONSUME-RACE) consume it through REQ's own guarded `record_handoff_consumption` with labelled seed ids `TND-SEED-REQ-SC-*`; no Tender record is created. Replace with a real Tender after the Tenders revamp (FU-35). | Owner answer; D15. |
| D17 | **Profiles live on the canonical MOH item (owner, 24 Sep 2026).** The thirteen §16.4A profiles are named, mutually exclusive states of the canonical combined laptop item as the canonical actors — not a separate year. Loading one cleans the item first (REQ rows, profile holds, Planning namespace rebuilt when locked/held/changed); `restore_base()` and `make seed-canonical` put the §16.4 base back. | Owner answer; §16.4 "restore it after each profile". |
| D18 | **COMPATIBILITY builds real failing items and reports the rest (owner, 24 Sep 2026).** Every check a real published Plan Item can fail is shown failing on its own; checks Planning publishes as fixed values (Currency, Award package, Plan horizon) are reported as not producible and left to `test_compatibility`. Live finding at build: only category/requirement type, method and lotting are producible on this site — County residents, Women and Persons with disabilities are supported, and Planning refuses to publish "Other disadvantaged group" (FU-36). | Owner answer; live evidence. |

### 2.1 Board findings (recorded as departures)

| # | Finding | Disposition |
|---|---|---|
| B1 | DES-10 Revoked shows "Owner fixture required" for reason, reversal and releases | Fixture data only; values come from the revoked record. No departure for structure. |
| B2 | DES-12 "Uncertain decision result" shows the retry-safe sentence under a "Committed reset" label | §13.13 wins: committed → "Requisition submitted to Procurement", retry-safe → "The result could not be confirmed…". Departure recorded. |
| B3 | The board's `.cap`/`.sub` captions and `kt-panel-lg` framing are design-tool annotation | Stripped by `requisitionsScope`. |

## 3. Phase sequence and gates

| Phase | Gate | Exit condition |
|---|---|---|
| 0 | REQ-G00 | Gap analysis, plan, tracker (135-row AC map) and follow-ups rewritten; no product code changed. |
| 1 | REQ-G01 | Budget shared-line aggregation and per-drawdown reservation; Planning projection facts, one-call drawdown, published reversal, outcome v1 payload; Tenders on handoff v1.4 via guarded consumption. Owners' suites green; REQ gateway contracts pin every signature. |
| 2 | REQ-G02 | Schema, precision, nine checks, all §10 commands and reads, exact §11 errors; module suite green; forced-failure rollback proves one-transaction authorisation; clean `bench migrate`. |
| 3 | REQ-G03 | Fidelity harness + registry + structure gate wired; shared module components; old step components deleted with their replacements. |
| 4 | REQ-G04a–i | One gate per slice (4a workspace … 4i stopped work). Each gate needs: component tests, structural + text fidelity for every drawn variant, a Playwright spec on its own reset fixture with per-role logins and absence assertions, first paint plus one live re-render, direct/reload/back-forward, a forced 500, zero console errors, a bundle hash change, and the 390px layout where drawn. |
| 5 | REQ-G05 | §16 canonical world + lifecycle and isolated profiles through real commands; Playwright world updated; `make seed-canonical THROUGH=tenders` validates green twice. |
| 6 | REQ-G06 | Persona pass (SMK-01..15), evidence pack `evidence/v1_11/`, handoff v1.4 + digest, prohibited-token search, AC map closed truthfully, follow-ups updated. REQ19-AC-107 (representative users) is left for the owner. |

## 4. Slice map (Phase 4)

| Slice | Boards | Route |
|---|---|---|
| 4a | DES-01 + DES-12 workspace states | `/app/procurement-requisitions` |
| 4b | DES-02 + DES-12 purchase states | `/new/{plan_item_id}` |
| 4c | DES-03, DES-04 | `/{requisition_id}` Request details |
| 4d | DES-05 + row dialogs | `/{requisition_id}` Requirements |
| 4e | DES-06 | `/{requisition_id}` Review and submit |
| 4f | DES-07 | `/department-task/{task_id}` |
| 4g | DES-08, DES-09 | `/procurement-task/{task_id}` |
| 4h | DES-10 | `/{requisition_id}/authorised` |
| 4i | DES-11 | `/{requisition_id}` stopped/returned rendering |

## 5. Risks

1. Removing inner commits from Budget and Planning must not break their existing callers. Prove this with rollback tests in each owner suite before REQ depends on it.
2. The precision storage change invalidates dev rows and old fixtures. Wipe and reseed; never rehash historical digests.
3. The Tenders correction path depends on release; see D11.
4. UI phases have historically hidden the most defects. The vertical slices plus the structural gate are the mitigation; no slice closes without a live browser pass.
