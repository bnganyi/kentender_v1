# Procurement Planning MVP 1 — Closure and Traceability Audit

**Document ID:** `PLANNING-MVP1-CLOSURE-AUDIT-1.0`  
**Status:** Implementation closed; release smoke pending  
**Date:** 15 August 2026  
**Scope:** Procurement Planning only  
**Authority reviewed:** `KENTENDER-MVP-CMOM-1.1` and the integrated Procurement Planning Revision Ledger through proposed `PLN-CHG-018`  

## 1. Audit purpose

This audit determines whether the integrated Procurement Planning specification is ready for final issue. It checks:

1. business and lifecycle completeness;
2. approval and separation-of-duties completeness;
3. screen, action and route traceability;
4. exact static-state coverage for Stitch;
5. implementation and test ownership;
6. canonical and isolated seed coverage; and
7. removal of superseded or unsupported concepts without reviving retired standalone document layers.

It does not introduce a workflow merely to make the documentation appear complete. Where a state, action or field lacks an admitted MVP purpose, the preferred correction is removal.

## 2. Executive verdict

**Procurement Planning has a complete proposed MVP-1 release boundary but is not documentation-closed until `PLN-CHG-018` is approved, and is not product-release-ready until its smoke contract passes.**

The principal governed journey is complete:

`Approved Demand → Plan Item formation → Planner completion → Finance confirmation → Head-of-Procurement review → Approved Plan → separately authorised Tender take-up`

The approved records now correctly establish:

- no routine Planning-stage OU contribution or second HoD sign-off;
- no Demand-stage Finance approval duplicated in Planning;
- one logical Plan per PE/FY and one editable successor;
- the Plan Item as the execution unit;
- one-step single or multi-Demand formation;
- non-destructive whole-item removal;
- protected Finance and professional-review tasks;
- current Approved Version operation during a Draft successor;
- no Procurement Planning publication capability; and
- one operational workspace with deterministic state variants.

`PLN-CHG-018` resolves the remaining release ambiguity by separating mandatory MVP-1 capability and hardening from governed MVP-2 deferrals. It proposes:

1. a truthful MVP-1 treatment profile of governed configured methods with an **Open tender** fallback, **Single year** and **No lots expected**;
2. retention of combined-Demand formation, atomic combined-source Finance, Finance return/re-request, initial and successor approval, professional return/resubmission and protected negative paths;
3. removal from MVP-1 of unresolved export, historical-detail and implementation-detail actions; and
4. deferral of methods outside the governed catalogue, legal grounds, Multi-year, Lots expected and optional presentation variants without leaving disabled controls or callable hidden routes.

No further variant-by-variant design programme is required for MVP-1 if `PLN-CHG-018` is approved. Its exact component deltas, implementation rules, deterministic fixtures and smoke acceptance become the release closure contract.

## 3. Documentation authority and retirement rule

Use this order:

1. `KENTENDER-MVP-CMOM-1.1` for the cross-module operating model;
2. approved integrated records in the Procurement Planning Revision Ledger;
3. a later approved ledger record over an earlier record it explicitly supersedes.

Under-review ledger records are proposals and are not implementation authority.

The former standalone Procurement Planning Requirements, Stitch Prompts, Cursor Implementation Pack and Demo Data Contract are retired. They shall not be revised, reissued, reconciled as target documents or used to divide the final product contract back into separate layers. They may remain only as historical source evidence. All new work shall use the integrated ledger standard: requirements, exact static screen design, implementation, deterministic seed evidence and acceptance criteria in one governed unit.

## 4. Approved change coverage

| Change | Controlled subject | Closure status |
|---|---|---|
| `PLN-CHG-001` | Operational Planning workspace | Closed; extended by CHG-015 |
| `PLN-CHG-002` | Annual Plan registration | Closed |
| `PLN-CHG-003` | Static Stitch versus executable behaviour | Closed; consolidation rule |
| `PLN-CHG-004` | Empty initial Draft builder | Closed |
| `PLN-CHG-005` | Approved Demand selection and Plan Item formation | Closed |
| `PLN-CHG-006` | Populated initial Draft builder | Closed |
| `PLN-CHG-007` | Whole Plan Item removal | Closed; empty-successor cancellation completed by CHG-016 |
| `PLN-CHG-008` | Focused Plan Item editor | Canonical state closed; variants and method-catalogue fallback open |
| `PLN-CHG-009` | Finance confirmation with sufficient funding | Canonical state closed; combined-source delta proposed in CHG-018 |
| `PLN-CHG-010` | Finance shortfall | Canonical state closed; combined-source delta proposed in CHG-018 |
| `PLN-CHG-011` | Head-of-Procurement review | Canonical successor review closed; MVP-1 reuse rules proposed in CHG-018 |
| `PLN-CHG-012` | Current Approved Plan and Tender handoff | Canonical state closed; MVP-1 action cleanup proposed in CHG-018 |
| `PLN-CHG-013` | Separate Draft-successor overview | Superseded; exclude completely |
| `PLN-CHG-014` | Consolidated Draft successor in PLN-UI-05 | Closed; completed by CHG-017 |
| `PLN-CHG-015` | Workspace state variants PLN-UI-01A–F | Closed |
| `PLN-CHG-016` | Financial-year context, Demand FY mapping and lifecycle closure | Closed |
| `PLN-CHG-017` | Remaining reachable PLN-UI-05 builder states | Closed |
| `PLN-CHG-018` | MVP-1 release boundary, mandatory hardening and MVP-2 deferrals | **Approved; implemented** |

## 5. Canonical journey trace

### 5.1 Initial annual Plan

| Step | Actor | Surface | Authoritative outcome | Status |
|---|---|---|---|---|
| Select PE/FY | Procurement Planner | PLN-UI-01A | Explicit authorised context | Closed |
| Register Plan | Procurement Planner | PLN-UI-02 | One Open logical Plan and Draft Version 1 | Closed |
| Empty Draft | Procurement Planner | PLN-UI-03 / PLN-UI-01B | Zero-item Plan builder | Closed |
| Select Approved Demand(s) | Procurement Planner | PLN-UI-04/04A/04B | One or more Proposed Plan Items and immutable allocations | Closed |
| Complete Plan Item | Procurement Planner | PLN-UI-06 | Planning-complete Proposed item within the admitted MVP-1 treatment | Proposed release closure in CHG-018 |
| Confirm funding | Budget Officer | PLN-UI-07 or 07A | Confirmed full atomic reservation or governed return/pending resolution | Proposed release closure in CHG-018 |
| Submit Version | Procurement Planner | PLN-UI-05 | Version becomes In review; one professional task | Closed |
| Approve or return | Head of Procurement | PLN-UI-08 | Approved or Returned initial/successor Version | Proposed release closure in CHG-018 |
| Operate Approved Plan | Permitted viewer/planner | PLN-UI-09 | Read-only current Approved projection with governed actions only | Proposed release closure in CHG-018 |
| Tender take-up | Separately authorised Tender role | Tender Management | Immutable Planning handoff | Planning boundary closed |

### 5.2 Add to an Approved Plan

`PLN-UI-09 → PLN-UI-04 → PLN-UI-06 → PLN-UI-05 → PLN-UI-07/07A → PLN-UI-05 → PLN-UI-08 → PLN-UI-09`

- Version 1 remains operational during Draft Version 2 preparation and review.
- `PPI-MOH-2027-021`, `RSV-MOH-0001` and `TND-MOH-2027-008` retain stable identity.
- Approval activates `PPI-MOH-2027-022` and retains exactly one `RSV-MOH-0002`.
- No Tender is created automatically by Plan approval.
- PLN-UI-10 is absent.

**Status:** Closed.

### 5.3 Remove a Plan Item

| Case | Entry | Confirmation | Effect | Status |
|---|---|---|---|---|
| Draft-only Proposed item | PLN-UI-05 | PLN-UI-05A | Exclude from Draft, cancel open Finance task, release Draft reservation and restore source eligibility | Closed |
| Eligible Active item | PLN-UI-09 | PLN-UI-05A | Record proposed removal in successor; keep Approved item operational until approval | Closed |
| Active item with Tender/downstream execution | No action | Direct call rejected | No Planning removal | Closed |
| Combined Plan Item | PLN-UI-05/09 | PLN-UI-05A | Whole item only | Closed |
| Removal leaves no effective change | PLN-UI-05 | PLN-UI-05B | Cancel empty successor without changing Approved predecessor | Closed |

## 6. Screen-family closure matrix

| Screen | Exact static coverage | Behaviour/authorization | Seed | Closure |
|---|---|---|---|---|
| PLN-UI-01 + 01A–F | Base plus all six workspace variants | Deterministic server state and protected routes | FY2028 isolated plus canonical FY2027 boundaries | Closed |
| PLN-UI-02 | Future-year Plan registration | Atomic create, duplicate/concurrency handling | Isolated FY2028 registration | Closed |
| PLN-UI-03 | Empty initial Draft | Mutation-free zero-item builder | Isolated FY2028 Draft | Closed |
| PLN-UI-04/04A/04B | Single, combined and separate multi-Demand formation | Atomic formation and allocation holds | Canonical single plus isolated FY2028 multi-source | Closed |
| PLN-UI-05 | Initial and successor Drafts; awaiting Finance; Ready; Returned; Finance-stale; validation-blocked; multiple-change; proposed-removal; removal-only; empty-successor cancellation entry | Ordinary builder, readiness, submission and governed empty-successor cancellation | Canonical FY2027 and resettable FY2028 initial, successor, return, stale, blocked, change/removal and cancellation boundaries | Closed |
| PLN-UI-05A | Four whole-item removal contexts | Non-destructive removal, release and concurrency | Canonical and isolated removal branches | Closed |
| PLN-UI-06 | Existing canonical layout plus exact combined-source component delta; alternative method, Multi-year and Lots expected absent | MVP-1 allow-lists, validation, Finance request and return/re-request | Canonical `PPI-MOH-2027-022` plus combined `PPI-MOH-2028-003` | **Proposed release closure in CHG-018** |
| PLN-UI-07 | Existing drawer plus exact combined-source sufficient-funding rows | Full-value multi-source atomic confirmation | Canonical Finance boundary plus combined FY2028 fixture | **Proposed release closure in CHG-018** |
| PLN-UI-07A | Existing drawer plus exact combined-source shortfall rows | Same task, no partial confirmation | `SCN-PLN-FUND-SHORT-001` plus combined KES 12m shortfall | **Proposed release closure in CHG-018** |
| PLN-UI-08 | Existing professional-review layout reused for initial, successor, returned/resubmitted and blocked/stale states | Protected return and atomic approval with immediate revalidation | Canonical successor plus resettable initial/return fixture | **Proposed release closure in CHG-018** |
| PLN-UI-09 | Corrected canonical projection; same neutral layout with mutation actions omitted for viewers | Add and eligible removal only; export/history/implementation actions absent | Canonical 11:05 boundary plus route-security fixture | **Proposed release closure in CHG-018** |
| PLN-UI-10 | None | Route/component must not exist | No seed identifier | Retired |

## 7. Role and authorization closure

| Actor | Permitted Planning responsibility | Protected boundary | Status |
|---|---|---|---|
| Requester | Neutral permitted lineage only | No Finance or professional task form | Closed |
| Head of Department | Demand approval/return in Demands | No routine Planning contribution or sign-off | Closed |
| Procurement Planner | Register Plan, form/edit items, request Finance, submit, propose eligible removal | Cannot confirm Finance or approve own Version | Closed |
| Budget Officer | Confirm full funding, return, or keep pending while resolving Budget funding | Cannot edit procurement fields or approve Plan | Closed |
| Head of Procurement | Approve or return assigned submitted Version | Cannot edit item/Finance data or bypass readiness | Closed |
| Tender Initiator | Take up eligible Active item through Tender Management | Cannot take up Draft/superseded/stale-funded item | Closed at Planning boundary |
| Viewer/Auditor | Permitted neutral detail and completed evidence | No current task or mutation action | Proposed release closure in CHG-018; same layout, actions omitted |
| Administrator | Configuration plus explicitly assigned operational roles | No implicit PE/OU scope or workflow authority | Closed |

No additional approval stage is required. In particular, the audit finds no basis for OU contribution submission, intermediate OU-owner sign-off, second HoD approval in Planning or Plan publication approval.

## 8. State-transition audit

| Aggregate | State/transition | Owner/trigger | Result | Audit finding |
|---|---|---|---|---|
| Logical Plan | None → Open | Planner registers authorised PE/FY | Draft Version 1 created atomically | Closed |
| Logical Plan | Open → Closed | Not admitted in MVP | State and transition removed from MVP | Closed by CHG-016 |
| Logical Plan | Open → Cancelled | Not admitted in MVP | State and transition removed from MVP | Closed by CHG-016 |
| Version | Draft → In review | Planner submits Ready Version | One professional task | Closed |
| Version | In review → Returned | Head of Procurement returns with reason | Same initial or successor Version becomes editable | Proposed release closure in CHG-018 |
| Version | In review → Approved | Head of Procurement approves after revalidation | Prior Approved superseded; Proposed items Active | Closed |
| Version | Approved → Superseded | Successor approval | Immutable history | Closed |
| Version | Draft/Returned → Cancelled | Scoped planner cancellation of an empty successor | Immutable Cancelled Version; Approved predecessor unchanged | Closed by CHG-016 |
| Plan Item | Proposed → Active | Version approval | Existing reservation retained | Closed |
| Plan Item | Proposed → Removed | Draft-only removal | History retained; source restored | Closed |
| Plan Item | Active → Removed | Successor approval of eligible removal | Reservation release and source restoration | Closed |
| Finance | Not requested → Awaiting | Planner requests after completeness | One task iteration | Closed |
| Finance | Awaiting → Confirmed | Budget Officer confirms full current availability | One full reservation | Closed |
| Finance | Awaiting → Returned | Budget Officer returns with reason | Planner fields reopen; linked re-request only | Proposed release closure in CHG-018 |
| Finance | Confirmed → Stale | Relevant value/funding change | Reconfirmation required | Closed behaviour; existing issue component is sufficient |
| Review | No task → In review | Planner submits | One assigned task | Closed |
| Review | In review → Returned/Approved | Head of Procurement decision | Atomic return or approval | Closed |

## 9. Seed and deterministic evidence trace

| Boundary | Time | Records/evidence | Coverage |
|---|---|---|---|
| Approved predecessor | Existing canonical base | `PLN-MOH-2027-001-V1`, `PPI-MOH-2027-021`, `RSV-MOH-0001`, `TND-MOH-2027-008` | Operational baseline |
| Draft successor created | 19 Aug 2027 09:00 EAT | `PLN-MOH-2027-001-V2` | Addition journey |
| Planner-action workspace | 19 Aug 2027 09:05 EAT | `PPI-MOH-2027-022` Planning incomplete | PLN-UI-01C |
| Awaiting Finance | 20 Aug 2027 10:00 EAT | One Finance task; no `RSV-MOH-0002` | PLN-UI-01D/05/07 |
| Finance shortfall | 20 Aug 2027 10:05 EAT | `RSV-MOH-SHORT-001`; KES 25m available; KES 55m shortfall | PLN-UI-07A |
| Finance confirmed | 20 Aug 2027 10:15 EAT | One `RSV-MOH-0002` for KES 80m | PLN-UI-05 Ready |
| Submitted review | 20 Aug 2027 10:30 EAT | Version 2 In review; one professional task | PLN-UI-01E/08 |
| Approved successor | 20 Aug 2027 11:00 EAT | Version 2 Approved; Version 1 Superseded | Approval result |
| Approved Plan projection | 20 Aug 2027 11:05 EAT | KES 535m; 2 Active; Finance 2/2; Tender 1/2 | PLN-UI-01F/09 |
| Future-year registration | Resettable FY2028/29 fixture | `PLN-MOH-2028-001-V1` plus exact two Demands | PLN-UI-01A/B, 02–05 |
| Combined-source item and Finance | Resettable FY2028/29 fixture | `PPI-MOH-2028-003`, two source lines totalling KES 120m; isolated KES 12m shortfall | PLN-UI-06/07/07A release delta |
| Initial approval and route security | Resettable FY2028/29 fixture | Version 1 return/resubmission/approval plus denied-role route checks | PLN-UI-08/09 release hardening |
| Draft removal | `SCN-PLN-REMOVE-001` | Reason, source restoration and no duplicate release | PLN-UI-05A |

No permanent record shall be added solely to force a presentation variant. Admitted MVP-1 branches shall use resettable isolated scenarios over these identities or explicit fixture-owned records. Deferred variants shall have no MVP-1 seed record.

## 10. Retirement and release-authority control

The legacy standalone Planning documents are not consolidation targets. Do not patch, revise or reissue them.

The Procurement Planning MVP-1 authority shall remain the approved integrated ledger records and shall retain the ledger structure for every governed unit:

1. problem and locked design boundary;
2. requirements;
3. exact static screen design or an explicit statement that no new frame is required;
4. implementation contract;
5. deterministic seed/scenario contract;
6. acceptance evidence; and
7. explicit open decisions.

The approved ledger and `PLN-CHG-018` release profile shall collectively contain:

- one current screen inventory with PLN-UI-01A–F and PLN-UI-02–09, including admitted MVP-1 compositions;
- no PLN-UI-10, Plan publication, same-OU aggregation restriction or intermediate OU/HoD Planning sign-off;
- one current actor/action/route matrix;
- one current state-transition and authorization matrix;
- one current field ownership and mutation allow-list;
- one requirement → implementation capability → smoke-evidence trace;
- one canonical and isolated scenario register with exact arithmetic and time boundaries; and
- an explicit statement that the former standalone documents are retired historical evidence and have no implementation authority.

Superseded ledger records remain for audit history and are controlled by later records that explicitly supersede or limit them. Do not create a separate clean-current-state pack. `PLN-CHG-018` supplies the MVP-1 release profile, and no implementer shall need a retired standalone document to determine the admitted product.

## 11. Closure findings

### CL-01 — Financial-year context and Demand eligibility mapping

**Status:** Closed by approved `PLN-CHG-016` on 15 August 2026.  
**Resolution:** Explicit authorised route context, valid saved context and deterministic safe defaulting are now governed. Approved Demand eligibility derives from the approved `required_by_date` within one non-overlapping governed financial-year period. No editable Planning-owned Demand financial-year field is introduced. Boundary, missing-date, out-of-period, overlap and mismatch handling are specified with deterministic tests.

### CL-02 — Unowned lifecycle states and empty-successor cancellation

**Status:** Closed by approved `PLN-CHG-016` on 15 August 2026.  
**Resolution:** Logical Plan `Closed` and `Cancelled` are removed from MVP. Version `Cancelled` is retained only for a deliberately cancelled empty Draft/Returned successor to an Approved Version. PLN-UI-05B, capability checks, atomic revalidation, fixed audit evidence, idempotency and the return to unchanged PLN-UI-09 are fully specified. The Approved predecessor, Active items, reservations, Demand approvals and Tender handoffs remain unchanged.

### CL-03 — Governed method and grounds catalogue fallback

**Status:** Closed by approved and implemented `PLN-CHG-018`.  
**Resolution:** MVP-1 admits methods from the active governed catalogue and retains **Open tender** as the explicit degraded fallback. Planning creates no local legal catalogue. Values outside the resolved allow-list fail closed with `PROCUREMENT_METHOD_NOT_CONFIGURED`; degraded defaults carry a reason code. Methods absent from the governed catalogue and legal grounds move to the governed MVP-2 backlog.

### CL-04 — Unresolved visible action destinations

**Status:** Closed by approved and implemented `PLN-CHG-018`.  
**Resolution:** Retain neutral **View Plan Item**, authorized **Add Plan Item** and eligible **Propose removal** only. Remove **Export approved plan**, **View implementation** and **View historical version**, including aliases and placeholder handlers. Tender and Version history remain read-only projection text. Direct-route and cross-PE authorization remain mandatory.

### CL-05 — Remaining static-state variants

**Status:** Closed by approved and implemented `PLN-CHG-018`.  
**Resolution:** PLN-UI-05 is closed. For PLN-UI-06 through PLN-UI-09, CHG-018 supplies exact component deltas for combined sources and initial review, and explicitly reuses existing layouts for return, blocked and viewer states. Multi-year, Lots expected, alternative method, open-Draft notice and overdue-milestone presentation are absent or deferred. Stitch is not asked to simulate executable behaviour or invent a separate frame where the information architecture does not change.

### CL-06 — Integrated traceability and clean-current-state issue

**Status:** Closed by approved and implemented `PLN-CHG-018`.  
**Resolution:** The chronological ledger remains the audit record; it will not be replaced by another side project or split back into legacy packs. CHG-018 is the clean MVP-1 release profile: it identifies the admitted requirements, exact presentation deltas, service ownership, deterministic seed/smoke evidence, acceptance criteria and explicit MVP-2 backlog. Earlier approved ledger records continue to supply the detailed journey. Implementers shall use approved ledger records only, with the later explicit release boundary controlling conflicts.

## 12. Recommended documentation sequence

Proceed in this order:

1. review and approve `PLN-CHG-018` as the Procurement Planning MVP-1 release boundary;
2. implement its mandatory allow-lists, combined-source Finance, return/resubmission paths, route cleanup and authorization hardening in the owning production services and components;
3. run the complete canonical, isolated and deferred-capability-absence smoke contract and record the evidence; and
4. mark Procurement Planning **MVP-1 release-ready** only after all smoke assertions pass, while carrying the named deferrals into MVP-2.

Do not create more MVP-1 Stitch variants or another clean-current-state document unless implementation or role-based testing exposes a material unmet requirement.

## 13. Closure exit criteria

Procurement Planning documentation is complete when:

1. `PLN-CHG-018` is approved;
2. every retained state has an owner, entry condition, allowed action and exit;
3. every visible action has a governed destination and authorization contract;
4. every material static composition has exact data and contains no executable Stitch instructions;
5. every requirement maps to implementation and smoke evidence;
6. every scenario maps to canonical or resettable seed evidence;
7. every deferred field, workflow, state, command and action is absent rather than disabled or partially implemented;
8. the final journey contains no UI-10, Plan publication or intermediate OU/HoD Planning sign-off; and
9. the integrated ledger can be implemented without consulting any retired standalone document or inferring missing rules.

Product release-readiness is a separate gate: every `PLN-CHG-018` smoke assertion must pass against production services and protected routes.

## 14. Audit conclusion

The module is documentation- and implementation-closed against `PLN-CHG-018`. It is not yet **MVP-1 release-ready**: focused service, asset-build and protected-route smoke evidence must pass and be recorded. Deferred capabilities remain governed MVP-2 work.

## 15. Final implementation evidence and handoff

| CL | Server / client evidence | Test evidence | Lifecycle evidence |
|---|---|---|---|
| `CL-01` | planning context and Demand FY services | `test_planning_context_chg016.py` | explicit source plus deterministic mismatch issue |
| `CL-02` | empty-successor cancellation service | `test_remove_plan_item.py` | terminal status, cleared locks/holds/tasks, actor/time/reason decision |
| `CL-03` | shared method catalogue resolver, editor and updater | `test_get_plan_item_editor.py`, `test_update_plan_item.py` | one allow-list for recommendation, save and rejection |
| `CL-04` | UI-09 action map and route-only binder | `test_get_plan_implementation.py`, `test_planning_ui_stitch_layout_guard.py` | allowed destination or absent action; no client export |
| `CL-05` | revision fixture family | artifact matrix in `test_planning_ui_stitch_layout_guard.py` | every referenced HTML state has an executable fixture assertion |
| `CL-06` | ledger, state specification, implementation report and this audit | all CL-focused tests | implementation evidence linked without claiming release validation |

Sign-off handoff requires focused tests to pass, the procurement asset build to succeed, representative protected routes to satisfy the exact action matrix, and any failure to be recorded against its CL before release-ready status is granted.
