# Strategy Alignment — Cross-Module Lifecycle Tracker

**Document ID:** STRATEGY-MVP1-XMOD-TRACKER-1.0  
**Status:** Strategy Core Complete + Integration Ready (Budget/Demand/Planning) — handoff to TM/consumers  
**Date:** 6 August 2026  
**Authority:** `06_Strategy_Alignment_MVP1_Cursor_Implementation_Prompt.md` → `STRATEGY-MVP1-REQ-1.1` → Stitch  
**Companion audit canvas:** workspace canvases `strategy-mvp1-requirements-audit.canvas.tsx` (copy under this folder as `strategy-mvp1-requirements-audit.canvas.tsx`)

## Goal

Track Strategy Alignment capabilities that span modules so provider work, consumer wiring, and end-to-end proof are never collapsed into a single “Implemented” flag. Use this file for remaining **consumer/TM** work without re-opening Strategy Core.

## Canonical fixture (settled)

Use the **implementation / seed / Stitch** identity set as the working fixture:

| Role | Canonical code |
|---|---|
| Active Entity Strategic Plan | `MOH-SP-0001` |
| Programme / Sub / Outcome / Indicator / Target | `MOH-PROG-0001`, `MOH-SUB-0001`, `MOH-OUT-0001`, `MOH-IND-0001`, `MOH-TGT-0001` |
| Seed entry | `upsert_works_master_strategy_hierarchy()` (`kentender_strategy/.../seeds/works_master_strategy_hierarchy.py`) |

Secondary plan `MOH-SP-0002` (HR) may appear in portfolio seeds — do not invent a second primary MOH pack.

## Completion levels (report only these)

| Level | Meaning | Verdict (2026-08-06) |
|---|---|---|
| **Strategy Core Complete** | Strategy-owned screens, rules, and services work with provider tests | **Met** — Desk proven (STR-SUP-005 waves 1–2); residual AC/§12 polish is backlog only |
| **Integration Ready** | Stable, tested contracts exist for Budget / Demand / Planning callers | **Met** for Budget / Demand / Planning |
| **End-to-End Complete (B/D/P)** | Demand / Budget / Planning triggers wired and proven | **Met** — XMOD-STR-001–004, 006, 007 |
| **End-to-End Complete (+ Tender)** | Tender / Award (+ later Contract) carry Strategy Reference | **Not met** — XMOD-STR-005 (consumer-owned; do not block Strategy Core) |

**Current overall:** **Strategy Core Complete** + **Integration Ready (Budget/Demand/Planning)**. Safe to move on from Strategy-owned work. Remaining queue is consumer/TM (XMOD-STR-005 → Downstream Tender/Contract → XMOD-STR-008 UX).

### Move-on gate (Strategy → TM)

Leave Strategy when all of the following hold (they do as of this revision):

1. Strategy Core + STR-SUP-005 **Provider complete — Desk proven**
2. Budget / Demand / Planning Strategy Reference paths **End-to-end complete**
3. No Strategy-owned row still **Provider in progress** (hygiene Closed; notifications Provider complete; due/overdue parked under XMOD-STR-009)
4. Next priorities list is forward-only consumer work — STR-SUP-005 is **not** re-queued

Parked (do not reopen Strategy Core for these): full §12 role matrix, leftover AC polish, due/overdue cron.

## Delivery statuses (mandatory vocabulary)

Do **not** use a single “Implemented” flag.

- Not started
- Provider in progress
- Provider complete — Desk proven — Strategy Desk/API evidence green; residual AC polish may remain
- Provider complete — consumer pending
- Consumer wired — end-to-end proof pending
- End-to-end complete
- Future external integration
- Blocked
- Out of scope
- Closed (hygiene) — terminal status for STR-SUP documentation/registry rows only

## Condition classes (track separately)

Every gap must be classified as exactly one of:

1. **Strategy-owned capability missing** — provider service/rules/projection absent or broken in Strategy
2. **Provider present — consumer not invoked** — Strategy contract exists; trigger module has not wired/proven it
3. **Future external / out of scope** — intentionally unavailable in MVP 1 (REQ §4.2 / §24)

Also never confuse:

- **Seeded display state** (Verified measurement, Verified-complete CA) with consumer alignment enforcement
- **Screen live** with cross-module lifecycle complete
- **§16 whitelist present** with Demand/Budget/Planning actually calling it on the critical path

## Cross-module ownership model

A requirement must have both a **trigger owner** and a **Strategy (provider) responsibility**.

| Business event | Trigger owner | Strategy responsibility |
|---|---|---|
| Select Active Performance Target on Budget Line | Budget | Expose Active targets; validate Strategy Reference |
| Require primary alignment on Demand Value Case | Demand | Validate reference; Active-only for new selection |
| Apply Required / Recommended Plan Value Commitments | Demand | Expose applicable PVCs by category / type / asset condition |
| Inherit Strategy Reference into Planning package | Planning | Re-validate / carry the same reference snapshot |
| Carry Strategy Reference through Tender / Award | Tender / Award | Historical resolvable; Active-only for new picks |
| Show downstream usage on a plan | Strategy (read) | Project authoritative consumer references by module |
| Strategy Performance contribution stages | Strategy (read) + consumers | Aggregate from measurements, CAs, and authorised refs |
| Correct invalid / superseded downstream refs | Strategy admin + owning module | `correct_strategy_reference` + portfolio remediation flags |
| Notify measurement / readiness / CA work items | Strategy workflows | Notification Log adapters (§17) |

## Required fields per cross-module requirement

| Field | Purpose |
|---|---|
| Requirement ID | Canonical traceability |
| Business event | What causes the operation |
| Trigger module | Module responsible for initiating it |
| Provider module | Module enforcing the business rules (usually Strategy) |
| Service contract | API or domain service invoked |
| Preconditions | Required state and authority |
| Idempotency key | Prevent duplicate processing where mutating |
| Expected mutation | Reference write, treatment record, notification, etc. |
| Failure result | Block, invalid reference, missing treatment exception |
| Audit event | Evidence recorded at runtime |
| Provider test | Strategy service works independently |
| Consumer test | Calling module invokes it correctly |
| End-to-end test | Complete business transition works |
| Delivery status | Current completion classification |

## Runtime tracking target

Maintain a **Strategy Reference + Audit + Usage read model** over authoritative DocTypes — **not** a new journal store / DocType. Authority remains:

- Strategic Plan hierarchy (Programme → Sub-programme → Outcome → Indicator → Target)
- Plan Value Commitment (+ applicability triggers on Public Value Objective)
- Performance Measurement / Strategy Corrective Action
- Strategy Audit Event
- Downstream Strategy Reference fields owned by consumer DocTypes (Demand, Budget Line, …)

Canonical provider APIs (REQ §16): `list_active_targets`, `validate_strategy_reference`, `list_applicable_value_commitments`, `get_strategy_usage`, `get_strategy_performance`.

Downstream Usage and Strategy Performance screens should be **projections** of those contracts and consumer-stored references — not separately authored truth stores. Align Budget Line field names (`primary_plan_version_id` / `primary_target_*`) with Strategy usage queries (`strategy_plan_version`) before claiming Integration Ready.

---

## Tracker rows

Update **Delivery status** and evidence columns as work lands. Add rows if new cross-module events are discovered; do not delete historical rows — mark Out of scope / Blocked instead.

### XMOD-STR-001 — Budget Line Active target selection

| Field | Value |
|---|---|
| Requirement ID | XMOD-STR-001 / STR-FR-095 / STR-AC-009 |
| Business event | Select Active Performance Target on Budget Line |
| Trigger module | Budget |
| Provider module | Strategy |
| Service contract | `list_active_targets` + `validate_strategy_reference` |
| Preconditions | Active Entity Strategic Plan; entity scope; selectable_for_new |
| Idempotency key | N/A (selection on save) |
| Expected mutation | Budget Line stores Strategy Reference fields |
| Failure result | Block invalid / non-Active selection |
| Audit event | Optional Budget + Strategy audit as designed |
| Provider test | `test_strategy_mvp1_ac_matrix` / `test_strategy_reference` |
| Consumer test | `test_budget_line_strategy_validate` + `test_budget_lines` — `save_budget_line` / `BudgetLine.validate` via `apply_budget_primary_strategy_reference` (Active for new/changed; historical unchanged OK) |
| End-to-end test | `budget-funding-line-strategy-xmod-str-001.spec.ts` — empty primary field error + Active select save on Draft `MOH-BUD-0004` / `MOH-BL-0006` |
| Delivery status | **End-to-end complete** |
| Condition class | Provider + consumer + Desk E2E proven |

### XMOD-STR-002 — Demand primary alignment (Value Case)

| Field | Value |
|---|---|
| Requirement ID | XMOD-STR-002 / STR-FR-099 / STR-AC-009 |
| Business event | Require primary alignment on Demand Value Case |
| Trigger module | Demand |
| Provider module | Strategy |
| Service contract | `validate_strategy_reference` / `strategy_consumer.apply_strategy_reference_to_doc` |
| Preconditions | Active target; Demand strategy fields present |
| Idempotency key | N/A |
| Expected mutation | Demand stores `strategy_plan_version` / `strategy_target` / snapshot |
| Failure result | Readiness incomplete / submit blocked |
| Audit event | Demand/Strategy as designed |
| Provider test | Strategy consumer helper + validate tests |
| Consumer test | `test_demand_strategy_readiness` + submission/planning readiness; create-demand Active target picker + draft persist |
| End-to-end test | `create-demand-strategy-xmod-str-002.spec.ts` — empty Next field error + Active `Name (CODE)` select → Step 2 |
| Delivery status | **End-to-end complete** |
| Condition class | Provider + consumer + Desk E2E proven |

### XMOD-STR-003 — Applicable Plan Value Commitments on Demand

| Field | Value |
|---|---|
| Requirement ID | XMOD-STR-003 / STR-FR-110–113 / STR-FR-063 / STR-AC-028 |
| Business event | Apply Required / Recommended PVCs to Value Case |
| Trigger module | Demand |
| Provider module | Strategy |
| Service contract | `list_applicable_value_commitments` |
| Preconditions | Active plan PVCs; category / type / asset triggers |
| Idempotency key | N/A |
| Expected mutation | Demand child `Demand Value Treatment` (Included / Not applicable + rationale) |
| Failure result | Missing Required treatment → readiness `value_commitments` fails |
| Audit event | Treatment decision evidence (Demand-owned) |
| Provider test | `test_strategy_mvp1_ac_matrix` applicability filter |
| Consumer test | `test_demand_strategy_readiness` PVC cases + create-demand Review treatments |
| End-to-end test | `create-demand-pvc-xmod-str-003.spec.ts` — Required untreated blocks Submit; Included / N/A+rationale refreshes readiness |
| Delivery status | **End-to-end complete** |
| Condition class | Provider + consumer + Desk E2E proven |

### XMOD-STR-004 — Planning inherit Strategy Reference

| Field | Value |
|---|---|
| Requirement ID | XMOD-STR-004 / STR-FR-095–099 |
| Business event | Inherit Strategy Reference into Planning package |
| Trigger module | Planning |
| Provider module | Strategy |
| Service contract | Planning `strategy_reference` adapter → `validate_strategy_reference` / `active_target_options` |
| Preconditions | Demand already carries Strategy Reference |
| Idempotency key | Package identity |
| Expected mutation | Package stores / displays same reference snapshot |
| Failure result | Block invalid inherit / force re-select Active target |
| Audit event | Planning/Strategy as designed |
| Provider test | Strategy validate + list_active_targets |
| Consumer test | `test_planning_strategy_inherit` + drawer/wizard display — `create_package_with_lines` inherits Demand `strategy_*` (`require_active=False`); package validate Active on re-select; wizard/drawer `Name (CODE)` |
| End-to-end test | `procurement-planning-strategy-display-xmod-str-004.spec.ts` (+ pw12 Step 1) — wizard demand card `kt-pw-demand-strategy` shows `Name (CODE)` / `MOH-TGT-0001` |
| Delivery status | **End-to-end complete** |
| Condition class | Provider + consumer + Desk E2E proven |

### XMOD-STR-005 — Tender / Award carry Strategy Reference

| Field | Value |
|---|---|
| Requirement ID | XMOD-STR-005 / STR-AC-008/009 |
| Business event | Carry Strategy Reference through Tender / Award |
| Trigger module | Tender / Award |
| Provider module | Strategy |
| Service contract | Historical resolve + Active-only for new |
| Preconditions | Upstream reference present |
| Idempotency key | Tender/Award identity |
| Expected mutation | Persist snapshot; do not invent new Strategy truth |
| Failure result | Block new picks against superseded Active-only rules |
| Audit event | As designed |
| Provider test | Historical resolve covered in Strategy AC sample |
| Consumer test | Pending TM consumers |
| End-to-end test | Pending |
| Delivery status | **Provider complete — consumer pending** |
| Condition class | Provider present — consumer not invoked (does not block Strategy Core move-on) |

### XMOD-STR-006 — Downstream usage projection

| Field | Value |
|---|---|
| Requirement ID | XMOD-STR-006 / STR-FR-120–123 / STR-UI-12 |
| Business event | Show Budget / Demand / Planning usage on a plan |
| Trigger module | Strategy (read) |
| Provider module | Strategy |
| Service contract | `get_strategy_usage` |
| Preconditions | Consumer DocTypes store Strategy Reference fields Strategy can query |
| Idempotency key | N/A (read) |
| Expected mutation | None |
| Failure result | Empty module groups when no data (not an error) |
| Audit event | N/A (read) |
| Provider test | `test_strategy_downstream_usage` — Demand + Budget (`MOH-BL-0001`) + Planning (`PKG-MOH-2026-001`) |
| Consumer test | Demand `strategy_*` + Budget `primary_*` + Procurement Package `strategy_*` projected; Tender/Contract/Asset/Disposal still empty stubs |
| End-to-end test | `strategy-alignment-nav.spec.ts` — Downstream Usage Budget/Demand/Planning counts + `PKG-MOH-2026-001` row |
| Delivery status | **End-to-end complete** |
| Condition class | Provider + Budget/Demand/Planning Desk E2E proven (other modules empty until consumers store refs) |

### XMOD-STR-007 — Strategy Performance contribution

| Field | Value |
|---|---|
| Requirement ID | XMOD-STR-007 / STR-FR-130–147 / STR-UI-15 / STR-AC-028 |
| Business event | Management performance projection across stages |
| Trigger module | Strategy (read) + consumers |
| Provider module | Strategy |
| Service contract | `get_strategy_performance` / `export_strategy_performance_report` |
| Preconditions | Measurements / CAs / authorised downstream refs |
| Idempotency key | N/A (read) |
| Expected mutation | None |
| Failure result | No causal savings claims without authoritative verified values |
| Audit event | N/A (read) |
| Provider test | `test_strategy_performance` — Budget `primary_*` + Demand Value Treatment adoption + Planning `estimated_value` |
| Consumer test | Demand treatments (XMOD-STR-003) + Package estimates (XMOD-STR-006) feed Performance; Tender/Contract stubs remain |
| End-to-end test | `strategy-alignment-nav.spec.ts` — Strategy Performance Planning stage + PVO-EFT-01 adoption depth |
| Delivery status | **End-to-end complete** |
| Condition class | Provider + Desk proven for Budget/Demand/Planning contribution (Tender/Contract stubs until XMOD-STR-005) |

### XMOD-STR-008 — Correct invalid / superseded references

| Field | Value |
|---|---|
| Requirement ID | XMOD-STR-008 / STR-FR-123 |
| Business event | Remediate invalid or superseded downstream refs where required |
| Trigger module | Strategy admin + owning module |
| Provider module | Strategy |
| Service contract | `correct_strategy_reference` + portfolio flags |
| Preconditions | Pre-activation / admin authority rules |
| Idempotency key | Correction event |
| Expected mutation | Updated reference codes / snapshot where allowed |
| Failure result | Block illegal post-activation edits |
| Audit event | Strategy Audit Event |
| Provider test | `test_strategy_reference` / related |
| Consumer test | Pending formal consumer remediation UX |
| End-to-end test | Pending |
| Delivery status | **Provider complete — consumer pending** |
| Condition class | Provider present — consumer incomplete |

### XMOD-STR-009 — Notifications / work queue

| Field | Value |
|---|---|
| Requirement ID | XMOD-STR-009 / REQ §17 |
| Business event | Notify measurement / readiness / CA work items |
| Trigger module | Strategy workflows |
| Provider module | Strategy (+ kentender_core notification helper) |
| Service contract | Notification Log adapters (pattern: Budget `emit_notification_log`) |
| Preconditions | Role recipients; entity scope |
| Idempotency key | Event + record + recipient |
| Expected mutation | Notification Log rows |
| Failure result | Best-effort; must not break mutation |
| Audit event | Optional |
| Provider test | `test_strategy_notifications` — plan/measurement/CA Notification Log + idempotency |
| Consumer test | N/A (in-app Desk Notification Log) |
| End-to-end test | Domain provider bar (Budget 001A pattern); due/overdue scheduler deferred |
| Delivery status | **Provider complete** |
| Condition class | Transition-driven §17 events wired; due/overdue cron deferred |

---

## Strategy-owned support gaps (not always cross-module)

| ID | Item | Delivery status | Notes |
|---|---|---|---|
| STR-SUP-001 | Budget Line ↔ Strategy usage field alignment | Provider complete | Dual-read `primary_*` in `get_strategy_usage` + `get_strategy_performance`; no Budget rename; evidence `test_strategy_downstream_usage` + `test_budget_contribution_via_primary_plan_version` |
| STR-SUP-002 | Notifications §17 | Closed | Closed with XMOD-STR-009 — `strategy_notification_service` + transition wiring; evidence `test_strategy_notifications` |
| STR-SUP-003 | `module_registry.py` Strategy `route_prefixes` sync with JS + `page_js` | Closed (hygiene) | All 15 `page_js` slugs in Python + JS (incl. `strategy-plan-create`); evidence `test_strategy_route_prefixes_cover_all_page_js` / `test_strategy_js_registry_route_prefixes_match_page_js` |
| STR-SUP-004 | Teardown inventory §6 status refresh | Closed (hygiene) | `05_Strategy_Teardown_Dependency_Inventory.md` §6 + header/§2/§3.3–3.4 reflect Alignment shipped |
| STR-SUP-005 | Full STR-AC-001–030 + role Playwright evidence | Provider complete — Desk proven | Waves 1+2 Desk evidence green (`make ui-strategy-role-gate`). **Not on the active priority queue.** Backlog only (do not re-queue as “next”): full §12 role matrix, leftover AC polish, due/overdue job (owned under XMOD-STR-009). 002/023 already mapped to stitch/nav gates. |
| STR-SUP-006 | Cursor ticket-doc-read-gate → MVP-1 Strategy pack | Closed (hygiene) | Gate lists `docs/mvp-1/01_strategy/` + this tracker; evidence `test_strategy_ticket_doc_read_gate_targets_mvp1_pack` |
| STR-SUP-007 | Downstream usage seed Budget Line linking | Provider complete | `moh_downstream_usage` links `MOH-BL-0001` via `primary_*` (+ Demand `strategy_*` + `PKG-MOH-2026-001`); closed with STR-SUP-001 / XMOD-STR-006 |

## Recommended next priorities

Forward-only consumer/TM work (each item ends when its tracker row reaches End-to-end complete or explicit Blocked). Do **not** re-list STR-SUP-005 here.

1. **XMOD-STR-005** — Tender / Award Strategy Reference carry (when TM consumers ready)  
2. **Downstream Usage / Performance** — Tender/Contract/Asset/Disposal when those modules store Strategy Reference (same consumer gate as #1)  
3. **XMOD-STR-008** — consumer remediation UX for invalid / superseded refs  

**Parked (not “next”; already deferred with an owner):** due/overdue notification job under XMOD-STR-009; STR-SUP-005 backlog notes on that row only. |

## Change log

| Date | Change |
|---|---|
| 2026-08-06 | Initial tracker from Strategy MVP-1 requirements audit (provider/consumer/external separation); companion canvas `strategy-mvp1-requirements-audit.canvas.tsx` |
| 2026-08-06 | STR-SUP-001 Provider complete + XMOD-STR-006 Provider complete — consumer pending — dual-read Budget Line `primary_*` in usage/performance; `moh_downstream_usage` links `MOH-BL-0001` |
| 2026-08-06 | XMOD-STR-002 / XMOD-STR-003 → Consumer wired — E2E proof pending — Demand readiness requires `strategy_target`; `Demand Value Treatment` + create-demand picker/Review PVC UI; evidence `test_demand_strategy_readiness` |
| 2026-08-06 | XMOD-STR-001 / XMOD-STR-004 → Consumer wired — E2E proof pending — Budget `save_budget_line` + DocType validate via `apply_budget_primary_strategy_reference`; Procurement Package `strategy_*` inherit from Demand in `create_package_with_lines`; wizard/drawer Name (CODE); evidence `test_budget_line_strategy_validate`, `test_planning_strategy_inherit`, drawer P4-002 |
| 2026-08-06 | XMOD-STR-001 / XMOD-STR-004 → **End-to-end complete** — Budget drawer `ktFormErrors` + Playwright Active save/empty error; Planning wizard `kt-pw-demand-strategy` Name (CODE); evidence `budget-funding-line-strategy-xmod-str-001.spec.ts`, `procurement-planning-strategy-display-xmod-str-004.spec.ts` |
| 2026-08-06 | XMOD-STR-002 / XMOD-STR-003 → **End-to-end complete** — create-demand Active target empty-Next error + PVC treatment readiness refresh; evidence `create-demand-strategy-xmod-str-002.spec.ts`, `create-demand-pvc-xmod-str-003.spec.ts`, `make ui-create-demand-strategy-gate` |
| 2026-08-06 | XMOD-STR-006 → **End-to-end complete** — `get_strategy_usage` Planning packages + seed `PKG-MOH-2026-001`; Downstream Usage Desk Budget/Demand/Planning; evidence `test_strategy_downstream_usage`, `strategy-alignment-nav` downstream test |
| 2026-08-06 | XMOD-STR-007 → **End-to-end complete** — Performance PVC adoption from Demand Value Treatment + Planning `estimated_value` stage; evidence `test_strategy_performance`, Strategy Performance Desk depth test |
| 2026-08-06 | STR-SUP-003 / 004 / 006 → **Closed (hygiene)** — Strategy `route_prefixes` synced to all `page_js`; teardown inventory §6 refreshed; ticket-doc-read-gate lists MVP-1 Strategy pack; evidence `kentender_core.tests.test_module_registry` |
| 2026-08-06 | XMOD-STR-009 / STR-SUP-002 → **Provider complete** — `strategy_notification_service` + transition emits; due/overdue deferred; evidence `test_strategy_notifications` |
| 2026-08-06 | STR-SUP-005 wave 1 — AC 005/011/013/015/019 + coverage map; thin Viewer/Manager Playwright (`make ui-strategy-role-gate`); status remains Provider in progress |
| 2026-08-06 | STR-SUP-005 wave 2 → **Provider complete — Desk proven** — AC 001/012/022/025/026/018/030 + role PW create/export/wrong-PE; `assert_entity_in_scope` on `list_measurements`; evidence `make ui-strategy-role-gate` |
| 2026-08-06 | **Handoff** — overall → Strategy Core Complete + Integration Ready (B/D/P); move-on gate recorded; next work is XMOD-STR-005 / consumer modules (not Strategy Core waves) |
