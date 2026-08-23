# PLN-STC-001 — Procurement Planning MVP-1 Stitch Contract

## 1. Document control and binding

| Item | Value |
| --- | --- |
| Document ID | PLN-STC-001 |
| Title | KenTender Procurement Planning MVP-1 Stitch Contract |
| Version | 0.1 |
| Date | 21 August 2026 |
| Status | Approved |
| Derivative type | Stitch Contract |
| Canonical source | PLN-CAN-001 — KenTender Procurement Planning MVP-1 Canonical Source Specification |
| Canonical version | 0.1, approved 21 August 2026 |
| Canonical content fingerprint | `sha256:2e8e8790309b4d738ab80934f609111753f94766aab8e4bf2d3313146289e879` |
| Functional dependency | PLN-FR-001 v0.1, approved 21 August 2026 |
| Functional content fingerprint | `sha256:46b01d1876a880ca1ef9a327722961b8f4c3b676c2cf5acd471b7afbe4d0dd96` |
| Approved Stitch output version | Not yet generated or approved |
| Visual baseline | Existing constructed KenTender Procurement Planning UI composition, corrected only as specified here |
| Production publication hold | LEG-AUTH-001 and ASMP-003 remain open; publication frames use sandbox evidence only |

> **Binding instruction.** If this derivative conflicts with or omits a required canonical rule, stop and return the issue to PLN-CAN-001. Do not infer a resolution.

PLN-CAN-001 is the sole product truth. PLN-FR-001 is the approved functional interpretation. Historical Planning documents and earlier Stitch prompts are visual-composition evidence only and may not supply a field, actor, record, command, state or outcome absent from those approved sources.

## 2. Purpose and controlled use

This contract defines the exact visible composition for every admitted Procurement Planning MVP-1 screen and materially different actor/state frame. It is written to prevent Stitch, a design agent or an implementation agent from inventing content.

It governs:

- the existing visual families to keep, correct or retire;
- the exact prompt assembly and generation order;
- one signed-in actor, PE/FY, point-in-time record state and authoritative projection per frame;
- visible page regions in order;
- exact labels, copy, values, controls, tables, rows, notices and buttons;
- overlay type and the business outcome each visible action represents;
- role/state-specific omission of inaccessible controls;
- responsive stacking and scrolling;
- explicit screen exclusions; and
- screenshot, frame-name and selector acceptance evidence.

It does not authorize Stitch to implement permissions, calculate values, call services, validate data, persist fields, route users, simulate transitions, create success/error behavior or generate alternate states. Those obligations remain in PLN-FR-001 and the later Implementation Pack.

## 3. Authority separation and fail-closed rules

### 3.1 Product truth versus visual evidence

| Source | Permitted use in this contract | Prohibited use |
| --- | --- | --- |
| PLN-CAN-001 v0.1 | Actors, records, states, screen registry, fixed copy, boundaries and canonical fixtures | None; it is controlling |
| Approved PLN-FR-001 v0.1 | Command meaning, guards, actor visibility and acceptance linkage | Altering canonical truth |
| Constructed Planning UI and approved screenshots/selectors | Geometry, density, component family, spacing, shell and interaction-pattern reuse | Supplying obsolete semantics or behavior |
| Procurement Planning Stitch Prompts v1.9 and Revision Ledger | Historical visual evidence for the existing workspace, workbench, editor, drawer, modal, review and active-detail families | Current Demand/DMD, generic approval, direct Tender, unsupported method, multi-year, lotting or lifecycle behavior |
| PLN-GF-003 UI section | Historical P3 page anatomy and exact composition evidence | Current product authority, a separate workspace or a missing canonical behavior |

### 3.2 Visual-reference gate STC-VIS-001

Before any frame is sent to Stitch, the operator shall attach or select the accepted existing frame screenshot and, where an implemented component exists, its selector/route inventory entry. The evidence must correspond to the layout family named in section 4.

If the reference is unavailable, ambiguous or materially inconsistent with this contract:

1. do not ask Stitch to approximate the existing UI;
2. do not substitute a generic dashboard, form or design system;
3. mark the frame **Blocked — visual reference missing**; and
4. return the missing screenshot/selector item for resolution.

This is a generation-evidence hold, not permission to consult historical documents for product behavior.

### 3.3 Static-design boundary

Every final Stitch request shall describe one static frame only. Separate frames are required for a different actor, record state, task owner, modal/drawer state, success, failure, returned, stale, shortfall, waiting or acknowledgement composition.

The phrases **if applicable**, **where present**, **show as needed**, **appropriate control**, **short description**, **sample rows**, **use realistic data**, **for example** and equivalent discretion are prohibited. An exact listed value may be omitted only when the same frame specification explicitly says **Do not render**.

## 4. UI reuse and disposition register

| Visual family / prior component | Disposition | Preserve exactly | Mandatory correction or retirement |
| --- | --- | --- | --- |
| KenTender Procurement navigation rail, breadcrumb bar, top bar, account controls, typography, colour and content-width rhythm | Keep | Existing shell and branding | Stitch designs main content only; no new global navigation |
| Procurement Planning workspace shell | Keep / Correct | Context row, compact Current Plan panel, action and waiting sections, compact tables | Accepted DPP/Need lineage; **Begin consolidation**; exact governance owner; ready for requisitioning; no role dashboards |
| No-context/support blocked composition | Keep / Correct | Restrained empty/support presentation | No PE/FY or Plan disclosure; persistent **Support view - read only** label; no impersonation |
| Old annual-plan registration panel | Correct | Compact confirmation-panel geometry | Rename to **Begin consolidation**; derived read-only identity; no editable PE/FY/title/currency/coordinating unit |
| Empty/populated wide Plan workbench | Keep / Correct | Header, summary strip, issue strip, compact filters/table and bottom action rhythm | DPP sources, predecessor separation, exact Finance/governance readiness; standalone PLN-UI-10 retired |
| Source-selection dialog | Keep / Correct | Large focused dialog, compact filters/table, selected-source summary | Accepted DPP entries/Needs, exact separate/combined result; no Approved Demand/DMD semantics |
| Single-page Plan Item editor | Keep / Correct | Focused page, read-only source block, procurement approach, schedule and sticky footer | Open Tender only; Single year only; No lots expected only; seven canonical milestones; no source edit or Tender configuration |
| Finance right drawer and return modal | Keep / Correct | Focused drawer over dimmed queue, funding rows, totals and bottom decisions | Protected assigned actor; full all-source confirmation; no partial amount, Plan approval or inline Budget edit |
| Wide review page with right decision rail | Keep / Extend | Summary, item/source/funding evidence, decision history and rail | Independently generate professional validation, AO certification and statutory approval; no generic **Review and approve** |
| Publication focused task | Extend existing focused-task family | Read-only task/evidence density | Exact approved payload, destination/configuration, attempt and acknowledgement; no payload edit or self-declared success |
| Approved Plan operational-detail page | Keep / Correct | Wide read-only detail, summary, compact item table and version history | State **Active** only after acknowledgement; publication evidence; Requisition eligibility/drawdown; no direct Tender action |
| DPP full-page detail, selected-source panel and decision modals | Keep / Correct | Existing P3 anatomy and table/panel relationship | It belongs to the one Procurement Planning workspace; no `PLN-GF-002 workspace`; amendment purpose added |
| Legacy Demand/DMD rows, contribution/release-package UI, direct Plan-to-Tender, generic approval, **Create annual plan**, **ready for tendering**, Multi-year and Lots expected controls | Retire | Nothing | Must not appear in any generated frame or hidden control |

### 4.1 Required visual evidence manifest

The Stitch project shall contain the following evidence aliases before generation. Each alias points to the accepted existing screenshot plus selector list; the aliases are not screen IDs and are never shown in the UI.

| Alias | Required reference family |
| --- | --- |
| VB-SHELL-01 | Authenticated Procurement shell and main-content width |
| VB-WS-01 | Procurement Planning workspace |
| VB-DPP-01 | DPP full-page table plus selected-source panel |
| VB-CONF-01 | Compact annual-plan confirmation panel |
| VB-SELECT-01 | Large source-selection dialog |
| VB-WB-01 | Wide Plan workbench |
| VB-ITEM-01 | Single-page Plan Item editor |
| VB-FIN-01 | Finance right drawer |
| VB-MODAL-01 | Compact return/removal confirmation modal |
| VB-REVIEW-01 | Wide review page with right decision rail |
| VB-ACTIVE-01 | Read-only operational Plan detail |
| VB-EVD-01 | Read-only evidence viewer, or the closest accepted audit/evidence pattern |

## 5. Prompt assembly contract

### 5.1 Mandatory assembled prompt

Each Stitch call is assembled in this exact order:

1. `STC-PREFIX-001` in section 5.2;
2. for a full-page P3 DPP frame only, `STC-FAMILY-DPP-001` in section 8.0; omit it for the modal frames P3-UI-DPP-02A, P3-UI-DPP-03C and P3-UI-DPP-03D;
3. the selected frame's complete **Contract item** table and **Frame block** from sections 7 to 12; and
4. `STC-SUFFIX-001` in section 5.3.

The operator must paste the assembled text as one prompt. A frame sent without the prefix, applicable DPP family block, complete contract table or suffix is non-conforming. Section 6.1 is a reconciliation catalogue for this contract and the later Seed Data Contract; it is not pasted into Stitch. Every value Stitch may render is repeated literally in the selected frame/family text. Stitch shall generate frames in section 6 order. Where a modal's Visual reference names an earlier accepted frame as its dimmed background, attach that exact accepted screenshot with VB-MODAL-01. An earlier accepted frame may supply visual geometry only; its actor, values, controls and state do not carry into the new prompt.

Every source frame block in this contract is already standalone. **Reuse 9.17**, **same as 11.7**, **as above**, **from section**, **standard table**, **standard panel** and equivalent maintenance shorthand are prohibited in a frame block. No prompt compiler or human expansion step may fill missing visible content. A missing exact value is **Blocked — incomplete Stitch contract** and returns to PLN-STC-001.

### 5.2 STC-PREFIX-001 — repeat verbatim in every Stitch prompt

> Design exactly one static authenticated KenTender Procurement Planning frame. Preserve the supplied existing KenTender Procurement shell, navigation, breadcrumb bar, top bar, account controls, branding, typography, colour, spacing scale and content-width rhythm. Design the main content area only. Use the attached accepted visual reference named in this frame; do not redraw or reinterpret the shell.
>
> Render the primary composition for a 1440 px desktop viewport. Use compact public-sector application density, sentence-case headings and buttons, readable read-only values, restrained status chips, modest borders and one obvious primary action only where this exact actor/state frame has one. Do not use decorative KPI cards, charts, progress rings, illustrations, tabs, steppers, wizards, activity feeds, generic approval matrices, administrator business controls or technical-schema presentation.
>
> Use only the exact actor, context, state, copy, values, controls, columns, rows and actions stated in this frame block. Do not create alternate data, extra rows, metrics, alerts, deadlines, filters, links, fields, buttons, statuses or workflow stages. If a value is not stated, omit it. Business titles are primary text; stable references are quiet secondary text. Authoritative source facts appear as readable text, never disabled inputs.
>
> This is static presentation work. Do not simulate a click, transition, validation, calculation, permission check, save, service call, loading state, success state or error state. Do not infer hidden variants. The visible actions represent the named business outcomes only; implementation remains outside Stitch.

### 5.3 STC-SUFFIX-001 — repeat verbatim in every Stitch prompt

> Responsive composition: at narrower widths, preserve business identity, status, amount and the primary action. Stack summary values without converting them into decorative cards. Stack a left table above its detail panel where specified. Wide tables may scroll horizontally; retain the first identifying column and row access. Drawers become full-width overlays and modals remain focused without losing title, message, required field or footer actions.
>
> Accessibility: use visible keyboard focus, programmatic-looking labels, sufficient contrast, text plus colour for status, a single visible H1, correct table headers and no icon-only action without an accessible label. The intended implementation must announce status/validation changes, but do not simulate those changes in this frame.
>
> Output exactly one desktop frame named with the supplied frame name. Add no annotation panel, screen identifier, developer note, alternate state, mobile mock-up or explanatory caption inside the UI. Return the generated frame for screenshot/selector comparison before another prompt is run.

## 6. Prompt inventory and generation order

| Order | Frame name | Product screen ID | Exact static state |
| --- | --- | --- | --- |
| 001 | PLN-UI-00__NO-CONTEXT | PLN-UI-00 | Authenticated actor with no authorised Planning context |
| 002 | PLN-UI-01A__NO-PLAN | PLN-UI-01A | Authorised MOH/FY context, accepted DPP source, no Annual Plan root |
| 003 | PLN-UI-01B__INITIAL-DRAFT | PLN-UI-01B | Initial Draft with zero Plan Items |
| 004 | PLN-UI-01C__ACTIVE-PLUS-DRAFT | PLN-UI-01C | Active V1 plus editable Draft V2 with planner work |
| 005 | PLN-UI-01D__FINANCE-ACTOR | PLN-UI-01D | Assigned Budget Officer actionable task |
| 006 | PLN-UI-01D__PLANNER-WAITING | PLN-UI-01D | Planner neutral waiting projection |
| 007 | PLN-UI-01E__PROFESSIONAL-ACTOR | PLN-UI-01E | Head of Procurement Function actionable validation task |
| 008 | PLN-UI-01E__AO-ACTOR | PLN-UI-01E | Accounting Officer actionable certification task |
| 009 | PLN-UI-01F__APPROVER-ACTOR | PLN-UI-01F | Configured authority actionable approval task |
| 010 | PLN-UI-01F__PUBLICATION-PENDING | PLN-UI-01F | Publication Operator actionable pending task |
| 011 | PLN-UI-01F__PUBLICATION-FAILED | PLN-UI-01F | Publication Operator retry task |
| 012 | PLN-UI-01G__ACTIVE-NO-WORK | PLN-UI-01G | Active Plan and empty action/waiting sections |
| 013 | PLN-UI-SUP-01__READ-ONLY | PLN-UI-SUP-01 | System Administrator support projection |
| 014 | P3-UI-DPP-01__DRAFT-PREPARER | P3-UI-DPP-01 | DPP Draft; Departmental Plan Preparer read-only review |
| 015 | P3-UI-DPP-02__DRAFT-HOD-READY | P3-UI-DPP-02 | Complete current Draft; HoD ready to submit |
| 016 | P3-UI-DPP-02A__SUBMIT-CONFIRMATION | P3-UI-DPP-02A | HoD immutable submission confirmation |
| 017 | P3-UI-DPP-03A__VALIDATION-CLASSIFICATION-MISSING | P3-UI-DPP-03A | Submitted DPP; Planning classification incomplete |
| 018 | P3-UI-DPP-03B__VALIDATION-READY | P3-UI-DPP-03B | Submitted DPP; Procurement validation ready |
| 019 | P3-UI-DPP-03C__RETURN-CONFIRMATION | P3-UI-DPP-03C | Procurement return confirmation with required reason |
| 020 | P3-UI-DPP-03D__ACCEPT-CONFIRMATION | P3-UI-DPP-03D | Procurement acceptance confirmation |
| 021 | P3-UI-DPP-04__SUBMITTED-DEPARTMENT-VIEW | P3-UI-DPP-04 | Neutral departmental view of immutable submitted DPP |
| 022 | P3-UI-DPP-05A__RETURNED-CORRECTION-OUTSTANDING | P3-UI-DPP-05A | Returned DPP; owning source correction outstanding |
| 023 | P3-UI-DPP-05B__RETURNED-CORRECTED | P3-UI-DPP-05B | Returned DPP; source corrected and ready to resubmit |
| 024 | P3-UI-DPP-06__ACCEPTED-CURRENT | P3-UI-DPP-06 | Accepted current DPP eligible for consolidation |
| 025 | P3-UI-DPP-06A__ACCEPTED-SOURCE-STALE-PRE-CONSUMPTION | P3-UI-DPP-06A | Accepted DPP source stale before Plan consumption |
| 026 | P3-UI-DPP-06B__SOURCE-CHANGED-POST-CONSUMPTION | P3-UI-DPP-06B | Source changed after consumption; existing Plan evidence preserved |
| 027 | P3-UI-DPP-07__WITHDRAWN | P3-UI-DPP-07 | Withdrawn DPP retained as read-only evidence |
| 028 | P3-UI-DPP-09D__AMENDMENT-DRAFT | P3-UI-DPP-09 | Departmental-plan amendment Draft |
| 029 | P3-UI-DPP-09S__AMENDMENT-SUBMITTED | P3-UI-DPP-09 | Immutable submitted departmental-plan amendment |
| 030 | P3-UI-DPP-09R__AMENDMENT-RETURNED | P3-UI-DPP-09 | Returned departmental-plan amendment |
| 031 | P3-UI-DPP-09A__AMENDMENT-ACCEPTED | P3-UI-DPP-09 | Accepted departmental-plan amendment eligible for successor Plan work |
| 032 | PLN-UI-02__BEGIN-CONSOLIDATION | PLN-UI-02 | Confirmation for creation/reuse of the one Annual Plan root and Draft |
| 033 | PLN-UI-03__INITIAL-DRAFT-ZERO-ITEM | PLN-UI-03 | Initial Draft Version 1 with zero Plan Items |
| 034 | PLN-UI-04__ONE-SOURCE | PLN-UI-04 | One accepted source selected for one Plan Item |
| 035 | PLN-UI-04__MULTI-COMBINED | PLN-UI-04 | Two accepted sources selected for one combined Plan Item |
| 036 | PLN-UI-04__MULTI-SEPARATE | PLN-UI-04 | Two accepted sources selected for two separate Plan Items |
| 037 | PLN-UI-05__INITIAL-DRAFT-INCOMPLETE | PLN-UI-05 | Initial Draft workbench with one incomplete item |
| 038 | PLN-UI-05__SUCCESSOR-INCOMPLETE | PLN-UI-05 | Active V1 plus incomplete Draft V2 addition |
| 039 | PLN-UI-05__SUCCESSOR-FINANCE-WAITING | PLN-UI-05 | Active V1 plus Draft V2 waiting for Finance |
| 040 | PLN-UI-05__SUCCESSOR-READY | PLN-UI-05 | Active V1 plus Draft V2 ready for professional submission |
| 041 | PLN-UI-05__SUCCESSOR-RETURNED | PLN-UI-05 | Active V1 plus returned Draft V2 correction work |
| 042 | PLN-UI-05__FINANCE-STALE | PLN-UI-05 | Draft Finance evidence stale after governed content change |
| 043 | PLN-UI-05__REMOVAL-ONLY-READY | PLN-UI-05 | Successor Draft containing one justified Active-item removal |
| 044 | PLN-UI-05A__DRAFT-ITEM-REMOVAL | PLN-UI-05A | Whole-item removal from an editable Draft |
| 045 | PLN-UI-05A__ACTIVE-ITEM-REMOVAL | PLN-UI-05A | Proposal to remove an Active item through a successor Draft |
| 046 | PLN-UI-05A__COMBINED-ITEM-REMOVAL | PLN-UI-05A | Whole combined-item removal; partial source detachment prohibited |
| 047 | PLN-UI-05B__CANCEL-NO-EFFECTIVE-CHANGE | PLN-UI-05B | Cancel successor with no effective change |
| 048 | PLN-UI-06__SINGLE-SOURCE-COMPLETE | PLN-UI-06 | Complete editable single-source Plan Item |
| 049 | PLN-UI-06__FINANCE-RETURNED | PLN-UI-06 | Complete Plan Item returned by Finance |
| 050 | PLN-UI-06__COMBINED-SOURCE-COMPLETE | PLN-UI-06 | Complete editable combined-source Plan Item |
| 051 | PLN-UI-07__SUFFICIENT-SINGLE-SOURCE | PLN-UI-07 | Assigned Finance task; sufficient single-source funding |
| 052 | PLN-UI-07__SUFFICIENT-COMBINED-SOURCE | PLN-UI-07 | Assigned Finance task; sufficient combined-source funding |
| 053 | PLN-UI-07A-1__INSUFFICIENT | PLN-UI-07A-1 | Assigned Finance task; exact KES 10,000,000 shortfall |
| 054 | PLN-UI-07A-2__RETURN-CONFIRMATION | PLN-UI-07A-2 | Finance return confirmation with required reason |
| 055 | PLN-UI-07B__PLANNER-NEUTRAL-WAITING | PLN-UI-07B | Planner read-only view while protected Finance task is pending |
| 056 | PLN-UI-08__PROFESSIONAL-VALIDATION | PLN-UI-08 | Head of Procurement Function professional validation |
| 057 | PLN-UI-08R__PROFESSIONAL-RETURN | PLN-UI-08R | Professional return confirmation with required reason |
| 058 | PLN-UI-08A__AO-CERTIFICATION | PLN-UI-08A | Accounting Officer certification |
| 059 | PLN-UI-08AR__AO-RETURN | PLN-UI-08AR | AO return confirmation with required reason |
| 060 | PLN-UI-08B__STATUTORY-APPROVAL | PLN-UI-08B | Configured authority statutory approval |
| 061 | PLN-UI-08BR__STATUTORY-RETURN | PLN-UI-08BR | Statutory return confirmation with required reason |
| 062 | PLN-UI-08C__PUBLICATION-PENDING | PLN-UI-08C | Approved exact payload pending sandbox publication |
| 063 | PLN-UI-08C__PUBLICATION-FAILED | PLN-UI-08C | Same approved payload after failed publication attempt |
| 064 | PLN-UI-08CA__PUBLICATION-ACKNOWLEDGED | PLN-UI-08CA | Authoritative acknowledgement received; Version 1 Active |
| 065 | PLN-UI-09__ACTIVE-PLAN | PLN-UI-09 | Active Annual Plan Version 1 operational detail |
| 066 | PLN-UI-09__ACTIVE-PLUS-DRAFT-NOTICE | PLN-UI-09 | Active Version 1 with separate successor Draft notice |
| 067 | PLN-UI-09A__REQUISITION-ELIGIBLE | PLN-UI-09A | Active item fully eligible for Procurement Requisition |
| 068 | PLN-UI-09A__PARTIAL-DRAWDOWN | PLN-UI-09A | Active item partially drawn by one Requisition |
| 069 | PLN-UI-09A__FULLY-DRAWN-BLOCKED | PLN-UI-09A | Active item fully drawn; no further Requisition eligibility |
| 070 | PLN-UI-09M__MONITORING-ENTRY-HISTORY | PLN-UI-09M | Planned-versus-actual milestone entry and correction history |
| 071 | PLN-UI-EVD-01__PLAN-EVIDENCE | PLN-UI-EVD-01 | Read-only immutable Annual Plan evidence timeline |

Every product screen ID in PLN-CAN-001 section 11 is represented. Frame suffixes identify static variants only; they do not create new product screens or routes.

## 6.1 Exact presentation fixture catalogue

The values below are presentation fixtures for cross-frame reconciliation and the later Seed Data Contract. They are not prompt shorthand and are not pasted into Stitch. Every renderable value is repeated literally in its frame block. The later Seed Data Contract must instantiate or reconcile them without changing product behavior. A mismatch is returned to PLN-CAN-001/PLN-STC-001; Stitch must not repair it.

### STC-FIX-BASE — integrated MOH plan

| Visible item | Exact value |
| --- | --- |
| Context | Ministry of Health · FY 2027/28 · 1 July 2027 to 30 June 2028 · Africa/Nairobi |
| Context ID | CTX-MOH-2027-2028 |
| Plan | Ministry of Health Annual Procurement Plan 2027/28 · PLN-MOH-2027-001 |
| Version | PLN-MOH-2027-001-V1 |
| Plan Item | National digital health infrastructure upgrade · PPI-MOH-2027-021 |
| DPP source | Digital Health Departmental Procurement Plan · DPPS-MOH-DIGITAL-2027-001-V1 |
| Need source | National digital health infrastructure upgrade · NDS-MOH-2027-0001 |
| Type / quantity / required by | Non-consulting services · 1 programme · 31 August 2027 |
| Funding / value | Government of Kenya · KES 80,000,000 |
| Treatment | Open Tender · Single year · No lots expected |
| Finance evidence | RSV-MOH-2027-021-001 · KES 80,000,000 · confirmed 4 December 2026 at 10:00 EAT |
| Professional decision | Samuel Otieno · 7 December 2026 at 10:00 EAT |
| AO certification | Amina Hassan · 8 December 2026 at 10:00 EAT |
| Statutory approval | National-government approving authority · 9 December 2026 at 11:00 EAT |
| Publication | PUB-MOH-2027-001-A1; sandbox transmission 10 December 2026 at 14:55 EAT |
| Acknowledgement | ACK-MOH-2027-001-A1; 10 December 2026 at 15:00 EAT; V1 Active |

### STC-FIX-DPP — departmental source

| Visible item | Exact value |
| --- | --- |
| Department | Digital Health |
| DPP | DPP-MOH-DIGITAL-2027-001 |
| Entry | DPPE-MOH-DIGITAL-2027-001 |
| Submission | DPPS-MOH-DIGITAL-2027-001-V1 · 25 November 2026 at 10:00 EAT |
| Validation | DPPV-MOH-DIGITAL-2027-001-V1 · 27 November 2026 at 14:00 EAT |
| Source-set display | 1 accepted Need · snapshot 9b41c28d…e2c7 |
| Submission window | Open; closes 30 November 2026 at 23:59 EAT |
| Preparer | Grace Wanjiku |
| HoD | Peter Kimani |
| Delegate | Julia Njeri |
| Validator | Mercy Kilonzo |
| AO recipient | Amina Hassan |

### STC-FIX-COMBINE — isolated two-source formation

| Source | Exact visible values |
| --- | --- |
| Source 1 | NDS-MOH-2027-0003 · Clinical training laptops for digital health rollout · Human Resources Management and Development · Goods · 200 each · KES 48,000,000 · required 31 December 2027 · DPPS-MOH-HR-2027-002-V1 |
| Source 2 | NDS-MOH-2027-0004 · Clinical deployment laptops for digital health rollout · Digital Health · Goods · 300 each · KES 72,000,000 · required 31 December 2027 · DPPS-MOH-DIGITAL-2027-002-V1 |
| Separate result | 2 Plan Items · 2 allocations · 500 each · KES 120,000,000 |
| Combined result | PPI-MOH-2027-033 · Clinical training and deployment laptops for digital health rollout · PE-level Procurement Function ownership · 2 allocations · 500 each · KES 120,000,000 |
| Combined reason | Procure one standard laptop specification and deployment service for the same national digital-health rollout. |

### STC-FIX-SUCCESSOR — isolated Active V1 plus Draft V2

| Visible item | Exact value |
| --- | --- |
| Active predecessor | PLN-MOH-2027-001-V1 · 1 Active item · KES 80,000,000 |
| Draft successor | PLN-MOH-2027-001-V2 · created 15 December 2026 at 09:00 EAT |
| Added source | NDS-MOH-2027-0002 · Digital health workforce certification programme · Human Resources Management and Development · 1 programme · KES 40,000,000 · required 31 December 2027 |
| Added item | PPI-MOH-2027-022 · Digital health workforce certification programme · KES 40,000,000 |
| Draft total / net change | KES 120,000,000 · KES 40,000,000 added |
| Update reason | Add the accepted digital-health workforce certification programme to the FY 2027/28 Plan. |

### STC-FIX-FINANCE — sufficient and shortfall profiles

| Profile | Exact visible values |
| --- | --- |
| Base Budget Line | MOH-BL-DHI-2027 · Digital health infrastructure programme · Government of Kenya |
| Sufficient | Approved KES 100,000,000; reserved KES 0; committed KES 0; available KES 100,000,000; required KES 80,000,000; after confirmation KES 20,000,000; As at 4 December 2026, 09:55 EAT |
| Shortfall | Approved KES 100,000,000; reserved KES 30,000,000; committed KES 0; available KES 70,000,000; required KES 80,000,000; shortfall KES 10,000,000; As at 4 December 2026, 09:55 EAT |
| Return reason | Funding availability is KES 10,000,000 below the amount required. Resolve the Budget Line or authoritative source before requesting Finance again. |

### STC-FIX-PUBLICATION — sandbox publication evidence

| Visible item | Exact value |
| --- | --- |
| Destination | KenTender Annual Plan Publication Sandbox |
| Configuration version | MOH-APP-SANDBOX-v1 |
| Payload | PLN-MOH-2027-001-V1 · KES 80,000,000 · 1 Plan Item |
| Payload hash display | SHA-256 7f2a9c1e4b76…91c4 |
| Failed result | No authoritative acknowledgement was returned. The approved payload is unchanged and may be retried. |
| Acknowledged result | ACK-MOH-2027-001-A1 · 10 December 2026 at 15:00 EAT · Version 1 activated |
| Hold note | Sandbox evidence only. Production publication remains unavailable while LEG-AUTH-001 and ASMP-003 are open. |

## 7. Exact workspace and support frame blocks

### 7.1 PLN-UI-00__NO-CONTEXT

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-WS-01 and VB-SHELL-01 |
| Purpose | Tell an authenticated user that no Procurement Planning context is available without disclosing any PE/FY or Plan data. |
| Primary actor | Peter Ouma, Internal Auditor, with no active Planning visibility assignment in this frame. |
| Origin / logical route | Procurement navigation → Procurement Planning. |
| Point-in-time state | Zero authorised Planning contexts. |
| Authoritative reads | Authentication identity and zero-context result only. |
| Visible action outcome | None. |

Frame block:

- Frame name: **PLN-UI-00__NO-CONTEXT**.
- Breadcrumb: **Procurement Planning**.
- H1: **Procurement Planning**.
- In the ordinary main-content position, show one restrained empty-state panel.
- Panel heading: **No Procurement Planning access**.
- Exact body copy: **Your account has no active Procurement Planning assignment. Contact your organisation's access administrator if you expect access.**
- Quiet signed-in account line: **Peter Ouma · Internal Auditor**.
- Render no context selector, PE, FY, cycle timing, counts, Plan title/reference, action/waiting sections, support diagnostics or business button.
- Evidence: compare shell and empty-panel geometry with VB-WS-01; screenshot must show no tenant fact.

### 7.2 PLN-UI-01A__NO-PLAN

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-WS-01 |
| Purpose | Show an authorised planner the eligible accepted DPP source before the Annual Plan root exists. |
| Primary actor | Mercy Kilonzo, Procurement Planner / Consolidator. |
| Origin / logical route | Procurement Planning workspace for CTX-MOH-2027-2028. |
| Point-in-time state | 1 December 2026 at 08:55 EAT; no Annual Plan root; one current accepted DPP submission is eligible. |
| Authoritative reads | Context, DPP window/cycle projection and DPPS-MOH-DIGITAL-2027-001-V1 eligibility. |
| Visible action outcome | **Begin consolidation** represents guarded creation/reuse of the one Annual Plan root and Draft Version. |

Frame block:

- Frame name: **PLN-UI-01A__NO-PLAN**.
- Breadcrumb: **Procurement Planning**.
- H1: **Procurement Planning**.
- Description: **Turn accepted departmental plans into funded, approved Plan Items ready for requisitioning.**
- Context row: read-only **Ministry of Health** and FY select **2027/28**.
- Context helper: **These controls define the workspace view; they do not change record ownership or grant operational authority.**
- Header primary button: **Begin consolidation**.
- Current Plan panel heading: **Current Plan**.
- Empty heading: **No Annual Procurement Plan**.
- Exact copy: **No Annual Procurement Plan exists for Ministry of Health for FY 2027/28.**
- Supporting copy: **One accepted departmental submission is ready for consolidation.**
- Summary values in order: **Eligible departmental submissions — 1**; **Accepted requirements — 1**; **Indicative value — KES 80,000,000**; **Submission window — Closed 30 November 2026 at 23:59 EAT**.
- Section **Work requiring action**: one compact row with columns **Work item**, **Type**, **Department**, **Amount**, **Why it needs action**, **Status**, **Action**. Row: **Digital Health Departmental Procurement Plan** with quiet **DPPS-MOH-DIGITAL-2027-001-V1**; **Accepted departmental plan**; **Digital Health**; **KES 80,000,000**; **Accepted source is ready for Annual Plan consolidation.**; **Ready for consolidation**; **Begin consolidation**.
- Section **Waiting on others**: exact empty copy **Nothing is currently waiting on another reviewer.**
- Do not render editable Plan metadata, **Create annual plan**, blank Plan registration, Need row, Finance/governance task or disabled action.

### 7.3 PLN-UI-01B__INITIAL-DRAFT

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-WS-01 |
| Purpose | Show the initial Draft Version before any Plan Item has been formed. |
| Primary actor | Mercy Kilonzo, Procurement Planner / Consolidator. |
| Origin / logical route | Return to workspace after Begin consolidation. |
| Point-in-time state | 1 December 2026 at 09:01 EAT; PLN-MOH-2027-001-V1 Draft; zero Plan Items; one accepted source available. |
| Authoritative reads | Plan/Draft identity, source availability and zero-item workbench projection. |
| Visible action outcome | **View plan update** represents opening the same initial Draft workbench. |

Frame block:

- Frame name: **PLN-UI-01B__INITIAL-DRAFT**.
- Breadcrumb and H1 **Procurement Planning**; description **Turn accepted departmental plans into funded, approved Plan Items ready for requisitioning.**
- Context row: read-only **Ministry of Health** and FY select **2027/28**; helper **These controls define the workspace view; they do not change record ownership or grant operational authority.**; header action **View plan update**.
- Current Plan panel: title **Ministry of Health Annual Procurement Plan 2027/28**; quiet **PLN-MOH-2027-001**; state line **Draft Version 1**; supporting copy **The initial Draft is ready for accepted departmental requirements.**
- Summary values in order: **Plan Items — 0**; **Draft planned value — KES 0**; **Accepted requirements available — 1**; **Finance confirmed — 0 of 0**; **Validation — Not run**.
- Work requiring action: one row **Add accepted departmental requirements**; type **Draft Plan**; department **Digital Health**; amount **KES 80,000,000 available**; reason **Form the first Plan Item from the accepted departmental source.**; status **Source available**; action **View plan update**.
- Waiting on others: **Nothing is currently waiting on another reviewer.**
- Do not render an Active version, publication evidence, Finance task, professional task, Plan approval, DPP validation controls or a second Draft action.

### 7.4 PLN-UI-01C__ACTIVE-PLUS-DRAFT

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-WS-01 |
| Purpose | Keep the Active baseline distinct from a Draft successor that needs planner work. |
| Primary actor | Mercy Kilonzo, Procurement Planner / Consolidator. |
| Origin / logical route | Procurement Planning workspace after an accepted addition creates Draft V2. |
| Point-in-time state | 15 December 2026 at 09:05 EAT; Active V1 KES 80,000,000; Draft V2 KES 120,000,000; added item incomplete. |
| Authoritative reads | Active V1 KES 80,000,000; Draft V2 KES 120,000,000; PPI-MOH-2027-022 incomplete; Draft readiness projection. |
| Visible action outcome | **View approved plan**, **View plan update** and **Complete item** represent distinct neutral/detail/editor destinations. |

Frame block:

- Frame name: **PLN-UI-01C__ACTIVE-PLUS-DRAFT**.
- Breadcrumb and H1 **Procurement Planning**; description **Turn accepted departmental plans into funded, approved Plan Items ready for requisitioning.**
- Context row: read-only **Ministry of Health** and FY select **2027/28**; helper **These controls define the workspace view; they do not change record ownership or grant operational authority.**; header buttons: quieter **View approved plan**, primary **View plan update**.
- Current Plan panel: **Ministry of Health Annual Procurement Plan 2027/28**; quiet **PLN-MOH-2027-001**; state line **Active Version 1 · Draft Version 2**; copy **Active Version 1 remains operational while Draft Version 2 is prepared.**
- Summary in order: **Active value — KES 80,000,000**; **Draft value — KES 120,000,000**; **Net change — KES 40,000,000 added**; **Planning complete — 1 of 2**; **Finance confirmed — 1 of 2**; **Validation — Needs attention**.
- Work requiring action table: one row **Digital health workforce certification programme** with quiet **PPI-MOH-2027-022**; type **Plan Item**; department **Human Resources Management and Development**; amount **KES 40,000,000**; reason **Complete procurement treatment and schedule before Finance confirmation.**; status **Planning incomplete**; action **Complete item**.
- Waiting on others: **Nothing is currently waiting on another reviewer.**
- Do not render full Active item rows, raw version diff, Finance decision form, professional decision rail, submission button or direct Tender/Requisition action.

### 7.5 PLN-UI-01D__FINANCE-ACTOR

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-WS-01 |
| Purpose | Give the assigned Budget Officer one actionable Finance task without Planning approval meaning. |
| Primary actor | MOH Budget Officer, `moh.budget.officer@example.test`. |
| Origin / logical route | Finance-capable user opens Procurement Planning for CTX-MOH-2027-2028. |
| Point-in-time state | Draft V2; PPI-MOH-2027-022 Planning complete and Awaiting confirmation. |
| Authoritative reads | Protected Finance task summary only after task authorization. |
| Visible action outcome | **Review financial reconciliation** represents opening PLN-UI-07. |

Frame block:

- Frame name: **PLN-UI-01D__FINANCE-ACTOR**.
- Breadcrumb and H1 **Procurement Planning**; description **Turn accepted departmental plans into funded, approved Plan Items ready for requisitioning.**
- Context row: read-only **Ministry of Health** and FY select **2027/28**; helper **These controls define the workspace view; they do not change record ownership or grant operational authority.**; no header creation/edit action.
- Current Plan panel state line: **Active Version 1 · Draft Version 2 · Finance reconciliation**.
- Summary: **Draft Plan Items — 2**; **Draft value — KES 120,000,000**; **Finance confirmed — 1 of 2**; **Waiting on Finance — 1**; **Validation — Needs attention**.
- Work requiring action table columns **Work item**, **Stage**, **Amount**, **Status**, **Action**. Exact row: **Digital health workforce certification programme** with quiet **PPI-MOH-2027-022**; **Finance reconciliation**; **KES 40,000,000**; **Awaiting confirmation**; **Review financial reconciliation**.
- Waiting on others: **Nothing is currently waiting on another reviewer.**
- Do not render Plan Item editing, professional validation, AO certification, approval, publication or disabled planner controls.

### 7.6 PLN-UI-01D__PLANNER-WAITING

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-WS-01 |
| Purpose | Show the planner that Finance owns the current task without exposing protected Finance content. |
| Primary actor | Mercy Kilonzo, Procurement Planner / Consolidator. |
| Origin / logical route | Procurement Planning workspace while the Finance task is current. |
| Point-in-time state | Draft V2; PPI-MOH-2027-022 Planning complete and Awaiting Finance confirmation; no planner-action work. |
| Authoritative reads | Neutral task owner/status only. |
| Visible action outcome | **View plan update** represents neutral Draft detail. |

Frame block:

- Frame name: **PLN-UI-01D__PLANNER-WAITING**.
- Breadcrumb and H1 **Procurement Planning**; description **Turn accepted departmental plans into funded, approved Plan Items ready for requisitioning.**
- Context row: read-only **Ministry of Health** and FY select **2027/28**; helper **These controls define the workspace view; they do not change record ownership or grant operational authority.**; header primary action **View plan update**.
- Current Plan panel state line **Active Version 1 · Draft Version 2 · Finance reconciliation**.
- Summary: **Draft Plan Items — 2**; **Draft value — KES 120,000,000**; **Finance confirmed — 1 of 2**; **Waiting on Finance — 1**; **Validation — Needs attention**.
- Work requiring action: do not render filters/table; exact copy **No planning work currently needs your action.**
- Waiting on others table columns **Work item**, **Stage**, **Status**, **With**. Exact row: **Digital health workforce certification programme** with quiet **PPI-MOH-2027-022**; **Finance reconciliation**; **Awaiting confirmation**; **Budget Officer**.
- Render no row action, drawer link, funding amounts, Budget Line, Confirm/Return controls or disabled Finance form.

### 7.7 PLN-UI-01E__PROFESSIONAL-ACTOR

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-WS-01 |
| Purpose | Give the Head of Procurement Function the exact professionally submitted Plan Version task. |
| Primary actor | Samuel Otieno, Head of Procurement Function. |
| Origin / logical route | Procurement Planning workspace after Plan Version submission. |
| Point-in-time state | 7 December 2026 at 09:55 EAT; PLN-MOH-2027-001-V1 awaiting professional validation; KES 80,000,000. |
| Authoritative reads | Protected professional task summary. |
| Visible action outcome | **Review plan version** represents opening PLN-UI-08. |

Frame block:

- Frame name: **PLN-UI-01E__PROFESSIONAL-ACTOR**.
- Breadcrumb and H1 **Procurement Planning**; description **Turn accepted departmental plans into funded, approved Plan Items ready for requisitioning.**
- Context row: read-only **Ministry of Health** and FY select **2027/28**; helper **These controls define the workspace view; they do not change record ownership or grant operational authority.**; no header action.
- Current Plan state line: **Version 1 · Awaiting professional validation**.
- Summary: **Plan Items — 1**; **Submitted value — KES 80,000,000**; **Finance confirmed — 1 of 1**; **Validation — Ready**; **Current owner — Head of Procurement Function**.
- Work requiring action: one row **Ministry of Health Annual Procurement Plan 2027/28 — Version 1** with quiet **PLN-MOH-2027-001-V1**; stage **Professional validation**; status **Ready for validation**; action **Review plan version**.
- Waiting on others: **Nothing is currently waiting on another reviewer.**
- Do not label the task final approval; do not render AO, authority or publication actions.

### 7.8 PLN-UI-01E__AO-ACTOR

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-WS-01 |
| Purpose | Give the Accounting Officer the exact certification task after professional validation. |
| Primary actor | Amina Hassan, Accounting Officer. |
| Origin / logical route | Procurement Planning workspace after the professional decision. |
| Point-in-time state | 8 December 2026 at 09:55 EAT; PLN-MOH-2027-001-V1 awaiting AO certification. |
| Authoritative reads | Protected AO task summary and professional-decision status. |
| Visible action outcome | **Review certification** represents opening PLN-UI-08A. |

Frame block:

- Frame name: **PLN-UI-01E__AO-ACTOR**.
- Breadcrumb and H1 **Procurement Planning**; description **Turn accepted departmental plans into funded, approved Plan Items ready for requisitioning.**
- Context row: read-only **Ministry of Health** and FY select **2027/28**; helper **These controls define the workspace view; they do not change record ownership or grant operational authority.**; no header action.
- Current Plan state line: **Version 1 · Awaiting AO certification**.
- Summary: **Plan Items — 1**; **Submitted value — KES 80,000,000**; **Finance confirmed — 1 of 1**; **Professional validation — Complete**; **Current owner — Accounting Officer**.
- Work requiring action: one row **Ministry of Health Annual Procurement Plan 2027/28 — Version 1**; quiet **PLN-MOH-2027-001-V1**; stage **AO certification**; status **Awaiting certification**; action **Review certification**.
- Waiting on others: **Nothing is currently waiting on another reviewer.**
- Do not render professional edit/redecision, statutory approval or publication controls.

### 7.9 PLN-UI-01F__APPROVER-ACTOR

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-WS-01 |
| Purpose | Give the configured statutory authority the exact AO-certified Plan Version task. |
| Primary actor | National-government Plan Approver, `moh.statutory.approver@example.test`. |
| Origin / logical route | Procurement Planning workspace after AO certification. |
| Point-in-time state | 9 December 2026 at 10:55 EAT; PLN-MOH-2027-001-V1 awaiting statutory approval. |
| Authoritative reads | Protected configured-authority task summary and AO certification status. |
| Visible action outcome | **Review for approval** represents opening PLN-UI-08B. |

Frame block:

- Frame name: **PLN-UI-01F__APPROVER-ACTOR**.
- Breadcrumb and H1 **Procurement Planning**; description **Turn accepted departmental plans into funded, approved Plan Items ready for requisitioning.**
- Context row: read-only **Ministry of Health** and FY select **2027/28**; helper **These controls define the workspace view; they do not change record ownership or grant operational authority.**; no header action.
- Current Plan state line: **Version 1 · Awaiting statutory approval**.
- Summary: **Plan Items — 1**; **Certified value — KES 80,000,000**; **Finance confirmed — 1 of 1**; **AO certification — Complete**; **Current owner — National-government approving authority**.
- Work requiring action: one row **Ministry of Health Annual Procurement Plan 2027/28 — Version 1**; stage **Statutory approval**; status **Awaiting approval**; action **Review for approval**.
- Waiting on others: **Nothing is currently waiting on another reviewer.**
- Do not render AO redecision, publication, activation or generic **Review and approve** copy.

### 7.10 PLN-UI-01F__PUBLICATION-PENDING

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-WS-01 |
| Purpose | Give the Publication Operator the approved exact-payload task without implying activation. |
| Primary actor | MOH Plan Publisher, `moh.plan.publisher@example.test`. |
| Origin / logical route | Procurement Planning workspace after statutory approval. |
| Point-in-time state | 10 December 2026 at 14:50 EAT; Approved - publication pending. |
| Authoritative reads | Approved V1, destination/configuration and no acknowledgement. |
| Visible action outcome | **Publish Annual Procurement Plan** represents opening PLN-UI-08C. |

Frame block:

- Frame name: **PLN-UI-01F__PUBLICATION-PENDING**.
- Breadcrumb and H1 **Procurement Planning**; description **Turn accepted departmental plans into funded, approved Plan Items ready for requisitioning.**
- Context row: read-only **Ministry of Health** and FY select **2027/28**; helper **These controls define the workspace view; they do not change record ownership or grant operational authority.**; no header action.
- Current Plan state line: **Version 1 · Approved - publication pending**.
- Summary: **Plan Items — 1**; **Approved value — KES 80,000,000**; **Statutory approval — Complete**; **Publication — Pending**; **Current owner — Publication Operator**.
- Work requiring action: one row **Ministry of Health Annual Procurement Plan 2027/28 — Version 1**; stage **Annual Plan publication**; status **Ready to publish**; action **Publish Annual Procurement Plan**.
- Quiet hold note below the row: **Sandbox evidence only. Production publication remains unavailable while LEG-AUTH-001 and ASMP-003 are open.**
- Do not show **Active**, Requisition eligibility, payload editor, Tender publication or disabled approval actions.

### 7.11 PLN-UI-01F__PUBLICATION-FAILED

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-WS-01 |
| Purpose | Give the Publication Operator the retry task for the same approved payload. |
| Primary actor | MOH Plan Publisher. |
| Origin / logical route | Procurement Planning workspace after a failed sandbox attempt. |
| Point-in-time state | 10 December 2026 at 14:58 EAT; Publication failed; approval remains valid. |
| Authoritative reads | Approved PLN-MOH-2027-001-V1 and failed attempt PUB-MOH-2027-001-A1 evidence. |
| Visible action outcome | **Retry publication** represents reopening the exact publication task. |

Frame block:

- Frame name: **PLN-UI-01F__PUBLICATION-FAILED**.
- Breadcrumb and H1 **Procurement Planning**; description **Turn accepted departmental plans into funded, approved Plan Items ready for requisitioning.**
- Context row: read-only **Ministry of Health** and FY select **2027/28**; helper **These controls define the workspace view; they do not change record ownership or grant operational authority.**; no header action.
- Current Plan state line: **Version 1 · Publication failed**.
- Summary: **Plan Items — 1**; **Approved value — KES 80,000,000**; **Statutory approval — Complete**; **Publication — Failed**; **Current owner — Publication Operator**.
- Work requiring action: one row **Ministry of Health Annual Procurement Plan 2027/28 — Version 1**; stage **Annual Plan publication**; status **Retry required**; action **Retry publication**.
- Add restrained warning below Current Plan: **The latest sandbox attempt did not return an authoritative acknowledgement. The approved payload is unchanged.**
- Quiet hold note below the row: **Sandbox evidence only. Production publication remains unavailable while LEG-AUTH-001 and ASMP-003 are open.**
- Do not show a second approval, Active state, edit control, manual success toggle or new payload.

### 7.12 PLN-UI-01G__ACTIVE-NO-WORK

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-WS-01 |
| Purpose | Show the acknowledged Active Plan when no work is actionable or waiting. |
| Primary actor | Mercy Kilonzo, Procurement Planner / Consolidator. |
| Origin / logical route | Procurement Planning workspace after sandbox acknowledgement. |
| Point-in-time state | 10 December 2026 at 15:05 EAT; V1 Active; no Draft successor. |
| Authoritative reads | Active Plan summary, acknowledgement and zero queue projection. |
| Visible action outcome | **View approved plan** represents opening PLN-UI-09. |

Frame block:

- Frame name: **PLN-UI-01G__ACTIVE-NO-WORK**.
- Breadcrumb and H1 **Procurement Planning**; description **Turn accepted departmental plans into funded, approved Plan Items ready for requisitioning.**
- Context row: read-only **Ministry of Health** and FY select **2027/28**; helper **These controls define the workspace view; they do not change record ownership or grant operational authority.**; header primary button **View approved plan**.
- Current Plan: **Ministry of Health Annual Procurement Plan 2027/28**; quiet **PLN-MOH-2027-001**; state line **Active Version 1**; copy **No plan update is currently in progress.**
- Summary: **Plan Items — 1 active**; **Active value — KES 80,000,000**; **Finance confirmed — 1 of 1**; **Publication — Acknowledged**; **Requisition eligibility — 1 item ready**.
- Work requiring action: **No planning work currently needs your action.**
- Waiting on others: **Nothing is currently waiting on another reviewer.**
- Do not render a Draft version, add-source row, approval/publication task, direct Requisition/Tender command or decorative implementation dashboard.

### 7.13 PLN-UI-SUP-01__READ-ONLY

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-WS-01 and VB-EVD-01 |
| Purpose | Provide labelled technical support visibility without a business command or impersonation. |
| Primary actor | KenTender System Administrator, `kentender.system.admin@example.test`. |
| Origin / logical route | Audited support navigation → Procurement Planning support projection. |
| Point-in-time state | Selected support context CTX-MOH-2027-2028; diagnostic reference PLN-SUPPORT-2026-0001. |
| Authoritative reads | Scope-limited workspace projection and non-sensitive configuration diagnostics. |
| Visible action outcome | **View evidence** represents read-only authorised evidence access. |

Frame block:

- Frame name: **PLN-UI-SUP-01__READ-ONLY**.
- Persistent banner at the top of main content: **Support view - read only**.
- Breadcrumb: **Support / Procurement Planning**.
- H1: **Procurement Planning support view**.
- Description: **Inspect the authorised Planning projection and diagnostic reference without performing a business action.**
- Context: **Ministry of Health · FY 2027/28**; quiet **CTX-MOH-2027-2028**.
- Diagnostic panel rows: **Planning configuration — Available**; **Current Plan — PLN-MOH-2027-001**; **Current version — Active Version 1**; **Diagnostic reference — PLN-SUPPORT-2026-0001**.
- One secondary action: **View evidence**.
- Render no actor selector, impersonation, command button, task form, edit field, hidden business menu or role assignment control.

## 8. Exact Departmental Procurement Plan frame blocks

### 8.0 STC-FAMILY-DPP-001 — repeat verbatim in every DPP prompt

All full-page DPP frames use VB-DPP-01. The desktop order is: breadcrumb/title/context; state/ownership notice and current action; compact summary strip; one-row accepted-Needs table on the left and selected-Need panel on the right; submission/validation/evidence region. At narrower widths the table stacks above the detail panel. Read-only source values are text, never disabled inputs.

The DPP table has exactly these columns in this order: **Requirement**, **Quantity**, **Required by**, **Source status**, **Planning type**. It has exactly one selected row: **National digital health infrastructure upgrade**, with quiet **NDS-MOH-2027-0001** below; **1 programme**; **31 August 2027**; **Current**; **Not classified** until a frame explicitly replaces that value. Do not add a selection checkbox, inclusion toggle, action-menu column, editable quantity/date, method, lot, package, Requisition or Tender column.

The adjacent panel is titled **Selected accepted Need** and shows these read-only labelled values in order: **Requirement — National digital health infrastructure upgrade**; **Need reference — NDS-MOH-2027-0001**; **Department — Digital Health**; **Quantity — 1 programme**; **Required by — 31 August 2027**; **Funding source — Government of Kenya**; **Indicative amount — KES 80,000,000**; **Source status — Current**; **Planning type — Not classified**. A frame may replace only the exact values it names.

### 8.1 P3-UI-DPP-01__DRAFT-PREPARER

| Contract item | Exact value |
| --- | --- |
| Purpose / actor | Review projected accepted Needs; Grace Wanjiku, Departmental Plan Preparer. |
| Origin / route | Workspace row **Review departmental plan** → DPP detail. |
| State / reads | DPP-MOH-DIGITAL-2027-001 Draft and current NDS-MOH-2027-0001 projection. |
| Visible outcome | Read-only review; quiet **View accepted Need** only. |

Frame block:

- Frame name: **P3-UI-DPP-01__DRAFT-PREPARER**.
- Breadcrumb: **Procurement Planning / 2027/28 / Departmental plan**.
- H1: **Departmental Procurement Plan**; description **Review accepted departmental needs before the Head of User Department submits the complete plan.**; quiet **DPP-MOH-DIGITAL-2027-001**; context **Ministry of Health · FY 2027/28 · Digital Health**; chip **Draft**.
- Notice: **Awaiting Head of User Department submission. Review every accepted Need. Source facts are changed in Departmental Needs, not here.**
- Summary: **Accepted Needs — 1**; **Source coverage — 1 of 1**; **Indicative amount — KES 80,000,000**; **Blocking issues — None**.
- Render the exact one-row DPP table and **Selected accepted Need** panel; add quiet link **View accepted Need**.
- Submission section: **Submission status — Not submitted**; **Head of User Department — Peter Kimani**; **Accounting Officer recipient — Amina Hassan**; **Submission window — Open; closes 30 November 2026 at 23:59 EAT**.
- Do not render Submit, classification, validation, inclusion checkbox, editable source, Annual Plan or downstream controls.

### 8.2 P3-UI-DPP-02__DRAFT-HOD-READY

| Contract item | Exact value |
| --- | --- |
| Purpose / actor | Certify the complete current DPP; Peter Kimani, effective HoD. |
| Origin / route | Workspace **Submit departmental plan** or HoD DPP detail. |
| State / reads | Draft, complete and current; exact recipient/window. |
| Visible outcome | **Submit departmental plan** represents opening 02A. |

Frame block:

- Frame name: **P3-UI-DPP-02__DRAFT-HOD-READY**.
- Breadcrumb: **Procurement Planning / 2027/28 / Departmental plan**.
- H1: **Departmental Procurement Plan**; description **Certify and submit the complete departmental plan to the Accounting Officer.**; quiet **DPP-MOH-DIGITAL-2027-001**; context **Ministry of Health · FY 2027/28 · Digital Health**; chip **Draft**.
- Notice: **Ready for submission. This plan contains every current accepted Need for Digital Health and is ready for certification.**
- Header primary button **Submit departmental plan**; quieter **Back to planning workspace**.
- Summary: **Accepted Needs — 1**; **Source coverage — 1 of 1**; **Indicative amount — KES 80,000,000**; **Blocking issues — None**.
- Render the exact one-row DPP table and **Selected accepted Need** panel.
- Section **Certification summary**: **Accepted Needs included — 1 of 1**; **Source status — Current**; **Blocking issues — None**; **Head of User Department — Peter Kimani**; **Recipient — Amina Hassan, Accounting Officer**; **Submission deadline — 30 November 2026 at 23:59 EAT**.
- Do not render a checkbox, typed name, signature upload, comment, editable recipient or Procurement decision.

### 8.3 P3-UI-DPP-02A__SUBMIT-CONFIRMATION

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-MODAL-01; accepted P3-UI-DPP-02__DRAFT-HOD-READY frame as the dimmed background |
| Purpose / actor | Confirm the exact immutable HoD submission; Peter Kimani. |
| State / reads | Current Draft, 1 source, exact recipient and source-set display. |
| Visible outcome | **Submit departmental plan** represents creation of the immutable submission. |

Frame block:

- Frame name: **P3-UI-DPP-02A__SUBMIT-CONFIRMATION**.
- Focused modal title **Submit departmental plan**.
- Read-only summary in order: **Departmental Plan — DPP-MOH-DIGITAL-2027-001**; **Department — Digital Health**; **Financial year — 2027/28**; **Accepted Needs — 1**; **Indicative amount — KES 80,000,000**; **Recipient — Amina Hassan, Accounting Officer**; **Source set — 1 accepted Need · snapshot 9b41c28d…e2c7**.
- Certification panel, exact: **I certify that this Departmental Procurement Plan contains the current accepted procurement needs of Digital Health for FY 2027/28, and that the descriptions, units, quantities and required-by dates shown are the authoritative departmental records submitted for consolidation. I understand that source corrections must be made in the owning module and resubmitted.**
- Permanence notice: **Submitting creates an immutable record of this exact source set. Later corrections require a new submission.**
- Footer: **Cancel**; primary **Submit departmental plan**.
- Do not render checkbox, typed name, free comment, source edit or Procurement decision.

### 8.4 P3-UI-DPP-03A__VALIDATION-CLASSIFICATION-MISSING

| Contract item | Exact value |
| --- | --- |
| Purpose / actor | Classify the immutable submitted requirement; Mercy Kilonzo, assigned DPP Validator. |
| Origin / route | Workspace **Validate departmental plan** → protected DPP validation. |
| State / reads | Submitted V1; current source; classification missing. |
| Visible outcome | **Return to department** is available; acceptance is visibly unavailable in this static frame. |

Frame block:

- Frame name: **P3-UI-DPP-03A__VALIDATION-CLASSIFICATION-MISSING**.
- Breadcrumb **Procurement Planning / Validation / DPP-MOH-DIGITAL-2027-001**; H1 **Validate Departmental Procurement Plan**; description **Review the exact submitted source set. Submitted values cannot be edited.**; context line; chip **Submitted**.
- Notice: **Procurement Function validation. Classify each submitted requirement and either accept the complete submission for consolidation or return it with an actionable source issue.**
- Summary: **Submission — V1**; **Submitted Needs — 1**; **Indicative amount — KES 80,000,000**; **Planning types complete — 0 of 1**; **Blocking issues — 1**.
- Render the exact one-row DPP table and **Selected accepted Need** panel with **Planning type — Not classified**.
- Selected panel adds one required single-select **Requirement type**, placeholder **Select requirement type**, options only **Goods; Works; Non-consulting services; Consulting services**; inline issue **Select a requirement type before accepting this submission.**
- Submission evidence: **DPPS-MOH-DIGITAL-2027-001-V1**; **Peter Kimani**; **25 November 2026 at 10:00 EAT**; **Amina Hassan, Accounting Officer**; **1 accepted Need**; quiet **View evidence**.
- Bottom bar: quieter **Return to department** only.
- Do not render **Accept for consolidation**, generic Approve or source edit in this classification-missing frame.

### 8.5 P3-UI-DPP-03B__VALIDATION-READY

| Contract item | Exact value |
| --- | --- |
| Purpose / actor | Review the fully classified, issue-free immutable submission; Mercy Kilonzo. |
| Origin / route | Same validation page after the illustrated classification value is present. |
| State / reads | Submitted V1, 1 of 1 classified, no blocker. |
| Visible outcome | **Accept for consolidation** represents opening 03D; **Return to department** opens 03C. |

Frame block:

- Frame name: **P3-UI-DPP-03B__VALIDATION-READY**.
- Breadcrumb **Procurement Planning / Validation / DPP-MOH-DIGITAL-2027-001**; H1 **Validate Departmental Procurement Plan**; description **Review the exact submitted source set. Submitted values cannot be edited.**; context **Ministry of Health · FY 2027/28 · Digital Health**; chip **Submitted**.
- Notice: **Procurement Function validation. Classify each submitted requirement and either accept the complete submission for consolidation or return it with an actionable source issue.**
- Summary: **Submission — V1**; **Submitted Needs — 1**; **Indicative amount — KES 80,000,000**; **Planning types complete — 1 of 1**; **Blocking issues — None**.
- Render the exact one-row DPP table and **Selected accepted Need** panel with Planning type **Non-consulting services**. In the selected panel, show required single-select **Requirement type**, selected value **Non-consulting services**, options only **Goods; Works; Non-consulting services; Consulting services**.
- Submission evidence: **DPPS-MOH-DIGITAL-2027-001-V1**; **Peter Kimani**; **25 November 2026 at 10:00 EAT**; **Amina Hassan, Accounting Officer**; **1 accepted Need**; quiet **View evidence**.
- Success notice: **All DPP validation checks are ready for decision.**
- Bottom bar: quieter **Return to department**; primary **Accept for consolidation**.
- Do not add score, checklist, comment requirement, approval label or another review stage.

### 8.6 P3-UI-DPP-03C__RETURN-CONFIRMATION

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-MODAL-01; accepted P3-UI-DPP-03B__VALIDATION-READY frame as the dimmed background |
| Purpose / actor | Record one structured return issue; Mercy Kilonzo. |
| State / reads | Submitted V1 and affected accepted Need. |
| Visible outcome | **Return to department** represents an immutable return and issue set. |

Frame block:

- Frame name: **P3-UI-DPP-03C__RETURN-CONFIRMATION**.
- Modal title **Return to department**.
- Read-only context: **Departmental Plan — DPP-MOH-DIGITAL-2027-001**; **Submission — V1**; **Affected requirement — National digital health infrastructure upgrade**; **Need reference — NDS-MOH-2027-0001**.
- Controls in order: required single-select **Correction type**, selected **Required-by date**, options only **Requirement details; Required-by date; Budget or funding reference; Strategy reference; Context mismatch; Source no longer accepted**; read-only **Owning module — Departmental Needs**; required multiline **Explanation** value **The required-by date must be confirmed against the delivery requirement.**; required multiline **Required action** value **Correct and re-approve the accepted Need in Departmental Needs, then resubmit the departmental plan.**
- Warning: **This submission will remain unchanged. Corrections must be completed in the owning record before the department resubmits.**
- Footer **Cancel**; **Return to department**.
- Do not render Reject, Correct here, editable submission or ungoverned Other.

### 8.7 P3-UI-DPP-03D__ACCEPT-CONFIRMATION

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-MODAL-01; accepted P3-UI-DPP-03B__VALIDATION-READY frame as the dimmed background |
| Purpose / actor | Confirm acceptance only as a consolidation source; Mercy Kilonzo. |
| State / reads | Current fully classified Submitted V1. |
| Visible outcome | **Accept for consolidation** represents the terminal professional intake decision. |

Frame block:

- Frame name: **P3-UI-DPP-03D__ACCEPT-CONFIRMATION**.
- Modal title **Accept for consolidation**.
- Read-only summary: **Departmental Plan — DPP-MOH-DIGITAL-2027-001**; **Submission — DPPS-MOH-DIGITAL-2027-001-V1**; **Submitted Needs — 1**; **Requirement types complete — 1 of 1**; **Indicative amount — KES 80,000,000**; **Current-source check — Current**.
- Information panel exact: **This action accepts the departmental submission as a source for Annual Plan consolidation. It does not approve the Annual Procurement Plan.**
- Footer **Cancel**; primary **Accept for consolidation**.
- Do not render Approve, Create Annual Plan, Begin consolidation, Requisition or Tender wording.

### 8.8 P3-UI-DPP-04__SUBMITTED-DEPARTMENT-VIEW

| Contract item | Exact value |
| --- | --- |
| Purpose / actor | Show the immutable submitted DPP and current owner; Grace Wanjiku, department viewer. |
| Origin / route | Waiting row after submission. |
| State / reads | Submitted V1; Procurement validation awaiting. |
| Visible outcome | Read-only **View evidence** only. |

Frame block:

- Frame name: **P3-UI-DPP-04__SUBMITTED-DEPARTMENT-VIEW**.
- Breadcrumb: **Procurement Planning / 2027/28 / Departmental plan**; H1 **Departmental Procurement Plan**; description **View the submitted departmental plan and its current validation status.**; quiet **DPP-MOH-DIGITAL-2027-001**; context **Ministry of Health · FY 2027/28 · Digital Health**; chip **Submitted**.
- Notice: **Submitted to the Accounting Officer. Waiting on Procurement Function.**
- Summary: **Accepted Needs — 1**; **Source coverage — 1 of 1**; **Indicative amount — KES 80,000,000**; **Blocking issues — None**.
- Render the exact one-row DPP table and **Selected accepted Need** panel read-only with **Planning type — Not classified**.
- Submission section: **DPPS-MOH-DIGITAL-2027-001-V1**; **Peter Kimani**; **25 November 2026 at 10:00 EAT**; **Amina Hassan, Accounting Officer**; **Procurement validation — Awaiting validation**; quiet **View evidence**.
- Do not render disabled Validate/Return/Accept/Withdraw/Submit again or any local edit.

### 8.9 P3-UI-DPP-05A__RETURNED-CORRECTION-OUTSTANDING

| Contract item | Exact value |
| --- | --- |
| Purpose / actor | Explain the exact upstream correction; Grace Wanjiku, department preparer. |
| Origin / route | Workspace returned-work row. |
| State / reads | Returned DPP; V1 preserved; one unresolved structured issue. |
| Visible outcome | **Open Departmental Need** represents navigation to the owner; **View submission V1** is evidence. |

Frame block:

- Frame name: **P3-UI-DPP-05A__RETURNED-CORRECTION-OUTSTANDING**.
- Breadcrumb **Procurement Planning / 2027/28 / Departmental plan**; H1 **Departmental Procurement Plan**; description **Resolve the returned source issue in its authoritative owning record.**; quiet **DPP-MOH-DIGITAL-2027-001**; context **Ministry of Health · FY 2027/28 · Digital Health**; chip **Returned**.
- Notice: **Correction required. This plan was returned. Complete the correction in its owning record, then return here to resubmit.**
- Summary: **Accepted Needs — 1**; **Source coverage — 1 of 1**; **Indicative amount — KES 80,000,000**; **Open issues — 1**.
- Render the exact one-row DPP table and **Selected accepted Need** panel with source status **Correction required** and Planning type **Non-consulting services**.
- Selected panel issue heading **Required-by date correction**; **Owning module — Departmental Needs**; **Explanation — The required-by date must be confirmed against the delivery requirement.**; **Required action — Correct and re-approve the accepted Need in Departmental Needs, then resubmit the departmental plan.**; primary **Open Departmental Need**.
- Quiet line **Submission V1 remains unchanged.**; secondary **View submission V1**.
- Do not render resubmit, local issue closure, source input or Procurement classification control.

### 8.10 P3-UI-DPP-05B__RETURNED-CORRECTED

| Contract item | Exact value |
| --- | --- |
| Purpose / actor | Review corrected current sources before resubmission; Peter Kimani, HoD. |
| Origin / route | Returned DPP after authoritative corrected Need projection. |
| State / reads | Returned; source current; issue resolved; V1 preserved. |
| Visible outcome | **Resubmit departmental plan** represents opening the predecessor-aware confirmation. |

Frame block:

- Frame name: **P3-UI-DPP-05B__RETURNED-CORRECTED**.
- Breadcrumb **Procurement Planning / 2027/28 / Departmental plan**; H1 **Departmental Procurement Plan**; description **Review the corrected current source set before resubmitting the departmental plan.**; quiet **DPP-MOH-DIGITAL-2027-001**; context **Ministry of Health · FY 2027/28 · Digital Health**; chip **Returned**.
- Success notice: **The corrected accepted Need is current. Review the complete source set and resubmit the departmental plan.**
- Summary: **Accepted Needs — 1**; **Source coverage — 1 of 1**; **Indicative amount — KES 80,000,000**; **Open issues — None**.
- Render the exact one-row DPP table and **Selected accepted Need** panel with source status **Current** and Planning type **Non-consulting services**; do not render an issue block.
- Header primary **Resubmit departmental plan**; quiet **View submission V1**.
- Add compact permanence line **Resubmitting creates immutable Submission V2 and does not change Submission V1.**
- Do not render version input, issue checkbox or editable predecessor.

### 8.11 P3-UI-DPP-06__ACCEPTED-CURRENT

| Contract item | Exact value |
| --- | --- |
| Purpose / actor | Show current accepted evidence and limited consolidation meaning; Grace Wanjiku, Departmental Plan Preparer. |
| Origin / route | Accepted history/waiting row or acceptance result. |
| State / reads | Accepted for consolidation, current and unconsumed. |
| Visible outcome | Read-only **View evidence** only. |

Frame block:

- Frame name: **P3-UI-DPP-06__ACCEPTED-CURRENT**.
- Breadcrumb **Procurement Planning / 2027/28 / Departmental plan**; H1 **Departmental Procurement Plan**; description **View the accepted departmental submission and its Annual Plan source eligibility.**; quiet **DPP-MOH-DIGITAL-2027-001**; context **Ministry of Health · FY 2027/28 · Digital Health**; chip **Accepted for consolidation**.
- Notice: **Accepted for consolidation. This departmental submission may be used as a source for Annual Plan consolidation. This is not Annual Plan approval.**
- Summary: **Accepted Needs — 1**; **Source coverage — 1 of 1**; **Indicative amount — KES 80,000,000**; **Eligibility — Eligible for consolidation**.
- Render the exact one-row DPP table and **Selected accepted Need** panel with source status **Current** and Planning type **Non-consulting services**.
- Validation outcome: **Submission — DPPS-MOH-DIGITAL-2027-001-V1**; **Outcome — Accepted for consolidation**; **Validated by — Mercy Kilonzo**; **Accepted — 27 November 2026 at 14:00 EAT**; **Requirement type — Non-consulting services**; **Current-source eligibility — Eligible**; quiet **View evidence**.
- Do not render Begin consolidation, Approve, Create Annual Plan, Requisition/Tender or overflow menu.

### 8.12 P3-UI-DPP-06A__ACCEPTED-SOURCE-STALE-PRE-CONSUMPTION

| Contract item | Exact value |
| --- | --- |
| Purpose / actor | Show stale accepted source before consumption; Mercy Kilonzo, assigned validator. |
| Origin / route | Accepted detail after newer authoritative source version. |
| State / reads | Accepted V1 preserved; source changed; P4 consumption not started; ineligible. |
| Visible outcome | **Reopen for source correction** represents the governed reopen confirmation. |

Frame block:

- Frame name: **P3-UI-DPP-06A__ACCEPTED-SOURCE-STALE-PRE-CONSUMPTION**.
- Breadcrumb **Procurement Planning / 2027/28 / Departmental plan**; H1 **Departmental Procurement Plan**; description **Review the accepted submission after a source change before Annual Plan consumption.**; quiet **DPP-MOH-DIGITAL-2027-001**; context **Ministry of Health · FY 2027/28 · Digital Health**; chips **Accepted for consolidation**, **Correction required**.
- Notice: **Accepted source changed. A newer accepted version of NDS-MOH-2027-0001 exists. This submission cannot be used for consolidation until it is reopened, corrected and resubmitted.**
- Summary: **Accepted Needs — 1**; **Source coverage — 1 of 1**; **Indicative amount — KES 80,000,000**; **Eligibility — Not eligible for consolidation**.
- Render the exact one-row DPP table and **Selected accepted Need** panel with source status **Correction required** and Planning type **Non-consulting services**.
- Issue panel: **Changed source — NDS-MOH-2027-0001**; **Accepted submission — V1 preserved**; **P4 consumption — Not started**; **Eligibility — Not eligible for consolidation**; quiet **View changed source**.
- Primary **Reopen for source correction**; secondary **View evidence**.
- Do not render source fields, automatic reopen or consolidation action.

### 8.13 P3-UI-DPP-06B__SOURCE-CHANGED-POST-CONSUMPTION

| Contract item | Exact value |
| --- | --- |
| Purpose / actor | Preserve P3 evidence after the accepted source was consumed; Grace Wanjiku, Departmental Plan Preparer. |
| Origin / route | Accepted detail after post-consumption source change. |
| State / reads | Accepted V1 consumed by PLN-MOH-2027-001-V1; source changed. |
| Visible outcome | Read-only evidence only; later Annual Plan control owns the impact. |

Frame block:

- Frame name: **P3-UI-DPP-06B__SOURCE-CHANGED-POST-CONSUMPTION**.
- Breadcrumb **Procurement Planning / 2027/28 / Departmental plan**; H1 **Departmental Procurement Plan**; description **View preserved departmental evidence after Annual Plan consumption.**; quiet **DPP-MOH-DIGITAL-2027-001**; context **Ministry of Health · FY 2027/28 · Digital Health**; chips **Accepted for consolidation**, **Source changed after consumption**.
- Notice: **Source changed after consolidation began. DPP evidence is preserved and this submission cannot be reopened here. Resolve the impact through the governed Annual Plan change-control process.**
- Summary: **Accepted Needs — 1**; **Source coverage — 1 of 1**; **Indicative amount — KES 80,000,000**; **Eligibility — Consumed; no P3 action**.
- Render the exact one-row DPP table and **Selected accepted Need** panel read-only with source status **Changed after consumption** and Planning type **Non-consulting services**.
- Read-only values: **Accepted submission — V1 preserved**; **Consumed by — PLN-MOH-2027-001-V1**; **P4 consumption — Recorded**; **DPP action — None available**; quiet **View evidence**.
- Do not invent a change-control route/button, delete allocation or substitute source.

### 8.14 P3-UI-DPP-07__WITHDRAWN

| Contract item | Exact value |
| --- | --- |
| Purpose / actor | Show preserved withdrawn history without reactivation; Grace Wanjiku, Departmental Plan Preparer. |
| Origin / route | DPP history after governed withdrawal. |
| State / reads | Withdrawn reset profile; no accepted downstream consumption. |
| Visible outcome | Read-only **View evidence**. |

Frame block:

- Frame name: **P3-UI-DPP-07__WITHDRAWN**.
- Breadcrumb **Procurement Planning / 2027/28 / Departmental plan**; H1 **Departmental Procurement Plan**; description **View the preserved withdrawn departmental plan evidence.**; quiet **DPP-MOH-DIGITAL-2027-001**; context **Ministry of Health · FY 2027/28 · Digital Health**; chip **Withdrawn**.
- Notice: **This departmental plan was withdrawn and is read-only. A new cycle or separately governed amendment path is required before departmental planning can continue.**
- Summary: **Accepted Needs — 1**; **Source coverage — 1 of 1 historical**; **Indicative amount — KES 80,000,000**; **Current eligibility — None**.
- Render the exact one-row DPP table and **Selected accepted Need** panel as historical read-only evidence with source status **Withdrawn** and Planning type **Not classified**.
- Withdrawal section: **Withdrawn by — Peter Kimani**; **Withdrawn — 20 November 2026 at 15:00 EAT**; **Reason — The department confirmed that the requirement will not be procured in FY 2027/28.**; quiet **View evidence**.
- Do not render Reactivate, Reopen, Submit, Validate, Accept or Delete.

### 8.15 P3-UI-DPP-09D__AMENDMENT-DRAFT

| Contract item | Exact value |
| --- | --- |
| Purpose / actor | Review a post-consumption departmental update before HoD submission; Grace Wanjiku. |
| Origin / route | Workspace **Review departmental plan update** after a new accepted Need version. |
| State / reads | Amendment Draft under the stable DPP root; predecessor DPPS V1 consumed; Active Plan unchanged. |
| Visible outcome | Read-only preparer review; HoD submission occurs in the separate HoD frame. |

Frame block:

- Frame name: **P3-UI-DPP-09D__AMENDMENT-DRAFT**.
- Breadcrumb **Procurement Planning / 2027/28 / Departmental plan update**; H1 **Departmental plan update**; description **Review the changed accepted Need before the Head of User Department submits this update.**; quiet **DPP-MOH-DIGITAL-2027-001**; context **Ministry of Health · FY 2027/28 · Digital Health**; chip **Draft**.
- Purpose strip: **Departmental plan update · Predecessor submission V1**.
- Notice: **A newer accepted Need version requires a new departmental submission. Active Annual Plan Version 1 remains unchanged.**
- Summary: **Updated Needs — 1**; **Source coverage — 1 of 1**; **Updated indicative amount — KES 84,000,000**; **Change — KES 4,000,000 increase**.
- Render the DPP table columns **Requirement**, **Quantity**, **Required by**, **Source status**, **Planning type** with one selected row: **National digital health infrastructure upgrade** with quiet **NDS-MOH-2027-0001**; **1 programme**; **15 September 2027**; **Current**; **Not classified**.
- Panel **Selected accepted Need** shows **Requirement — National digital health infrastructure upgrade**; **Need reference — NDS-MOH-2027-0001**; **Department — Digital Health**; **Quantity — 1 programme**; **Required by — 15 September 2027**; **Funding source — Government of Kenya**; **Indicative amount — KES 84,000,000**; **Previous amount — KES 80,000,000**; **Current amount — KES 84,000,000**; **Predecessor — DPPS-MOH-DIGITAL-2027-001-V1**; **Source status — Current**; **Planning type — Not classified**.
- Submission section: **Purpose — Departmental plan update**; **Submission status — Not submitted**; **HoD — Peter Kimani**; **Recipient — Amina Hassan**.
- Do not render Active Plan edit, Begin consolidation, local source edit or approval control.

### 8.16 P3-UI-DPP-09S__AMENDMENT-SUBMITTED

| Contract item | Exact value |
| --- | --- |
| Purpose / actor | Show the immutable submitted departmental update; Grace Wanjiku, neutral department viewer. |
| Origin / route | Workspace waiting row after update submission. |
| State / reads | DPPS-MOH-DIGITAL-2027-001-V2 Submitted; predecessor V1 preserved. |
| Visible outcome | Read-only evidence only. |

Frame block:

- Frame name: **P3-UI-DPP-09S__AMENDMENT-SUBMITTED**.
- Breadcrumb **Procurement Planning / 2027/28 / Departmental plan update**; H1 **Departmental plan update**; description **View the submitted departmental-plan update and its current validation owner.**; quiet **DPP-MOH-DIGITAL-2027-001**; context **Ministry of Health · FY 2027/28 · Digital Health**; chip **Submitted**.
- Purpose strip **Departmental plan update · Predecessor submission V1**.
- Notice: **Departmental plan update submitted. Waiting on Procurement Function validation.**
- Summary: **Updated Needs — 1**; **Source coverage — 1 of 1**; **Updated indicative amount — KES 84,000,000**; **Change — KES 4,000,000 increase**.
- Render table columns **Requirement**, **Quantity**, **Required by**, **Source status**, **Planning type** with one selected row: **National digital health infrastructure upgrade** with quiet **NDS-MOH-2027-0001**; **1 programme**; **15 September 2027**; **Current**; **Not classified**. Panel **Selected accepted Need** shows **Requirement — National digital health infrastructure upgrade**; **Need reference — NDS-MOH-2027-0001**; **Department — Digital Health**; **Quantity — 1 programme**; **Required by — 15 September 2027**; **Funding source — Government of Kenya**; **Current amount — KES 84,000,000**; **Previous amount — KES 80,000,000**; **Predecessor — DPPS-MOH-DIGITAL-2027-001-V1**; **Source status — Current**; **Planning type — Not classified**.
- Submission section: **Submission — DPPS-MOH-DIGITAL-2027-001-V2**; **Purpose — Departmental plan update**; **Previous submission — V1**; **Submitted by — Peter Kimani**; **Submitted — 15 December 2026 at 10:00 EAT**; **Recipient — Amina Hassan**; quiet **View evidence**.
- Do not render validation controls, Active Plan mutation or duplicate submission.

### 8.17 P3-UI-DPP-09R__AMENDMENT-RETURNED

| Contract item | Exact value |
| --- | --- |
| Purpose / actor | Explain an actionable source issue on the immutable update; Grace Wanjiku. |
| Origin / route | Workspace returned update row. |
| State / reads | V2 Returned; predecessor V1 and Active Plan preserved. |
| Visible outcome | **Open Departmental Need** represents upstream correction. |

Frame block:

- Frame name: **P3-UI-DPP-09R__AMENDMENT-RETURNED**.
- Breadcrumb **Procurement Planning / 2027/28 / Departmental plan update**; H1 **Departmental plan update**; description **Resolve the returned source issue before resubmitting this departmental-plan update.**; quiet **DPP-MOH-DIGITAL-2027-001**; context **Ministry of Health · FY 2027/28 · Digital Health**; chip **Returned**.
- Purpose strip **Departmental plan update · Predecessor submission V1**.
- Notice: **Departmental plan update returned. Correct the Budget or funding reference in the authoritative source and resubmit the update.**
- Summary: **Updated Needs — 1**; **Updated indicative amount — KES 84,000,000**; **Change — KES 4,000,000 increase**; **Open issues — 1**.
- Render table columns **Requirement**, **Quantity**, **Required by**, **Source status**, **Planning type** with one selected row: **National digital health infrastructure upgrade** with quiet **NDS-MOH-2027-0001**; **1 programme**; **15 September 2027**; **Correction required**; **Non-consulting services**. Panel **Selected accepted Need** shows **Requirement — National digital health infrastructure upgrade**; **Need reference — NDS-MOH-2027-0001**; **Department — Digital Health**; **Quantity — 1 programme**; **Required by — 15 September 2027**; **Funding source — Government of Kenya**; **Current amount — KES 84,000,000**; **Previous amount — KES 80,000,000**; **Predecessor — DPPS-MOH-DIGITAL-2027-001-V1**; **Source status — Correction required**; **Planning type — Non-consulting services**.
- Issue panel: **Correction type — Budget or funding reference**; **Owning module — Departmental Needs / Budget & Funding**; **Explanation — The updated amount does not have a current FY 2027/28 Budget Line reference.**; **Required action — Attach an active governed Budget Line to the accepted Need, complete its owning approval, then resubmit this departmental plan update.**; primary **Open Departmental Need**.
- Quiet **V2 remains unchanged** and **View submission V2**.
- Do not render local Budget selector, Finance confirmation or Active Plan edit.

### 8.18 P3-UI-DPP-09A__AMENDMENT-ACCEPTED

| Contract item | Exact value |
| --- | --- |
| Purpose / actor | Show the accepted departmental update and successor-only eligibility; Grace Wanjiku, Departmental Plan Preparer. |
| Origin / route | Validation result/history row. |
| State / reads | V2 accepted; predecessor V1 consumed; eligible for one Annual Plan Draft successor. |
| Visible outcome | Read-only evidence; Annual Plan workspace owns the next action. |

Frame block:

- Frame name: **P3-UI-DPP-09A__AMENDMENT-ACCEPTED**.
- Breadcrumb **Procurement Planning / 2027/28 / Departmental plan update**; H1 **Departmental plan update**; description **View the accepted departmental-plan update and its successor-only eligibility.**; quiet **DPP-MOH-DIGITAL-2027-001**; context **Ministry of Health · FY 2027/28 · Digital Health**; chip **Accepted for consolidation**.
- Purpose strip **Departmental plan update · Predecessor submission V1**.
- Notice: **Departmental plan update accepted. This submission is eligible only for an Annual Plan Draft successor. Active Version 1 remains operational until a successor is approved, published and acknowledged.**
- Summary: **Submission — V2**; **Updated Needs — 1**; **Updated amount — KES 84,000,000**; **Change — KES 4,000,000 increase**; **Eligibility — Annual Plan successor**.
- Render table columns **Requirement**, **Quantity**, **Required by**, **Source status**, **Planning type** with one selected row: **National digital health infrastructure upgrade** with quiet **NDS-MOH-2027-0001**; **1 programme**; **15 September 2027**; **Current**; **Non-consulting services**. Panel **Selected accepted Need** shows **Requirement — National digital health infrastructure upgrade**; **Need reference — NDS-MOH-2027-0001**; **Department — Digital Health**; **Quantity — 1 programme**; **Required by — 15 September 2027**; **Funding source — Government of Kenya**; **Current amount — KES 84,000,000**; **Previous amount — KES 80,000,000**; **Predecessor — DPPS-MOH-DIGITAL-2027-001-V1**; **Source status — Current**; **Planning type — Non-consulting services**.
- Validation outcome: **Accepted by — Mercy Kilonzo**; **Accepted — 17 December 2026 at 14:00 EAT**; **Requirement type — Non-consulting services**; **Predecessor submission — V1**; quiet **View evidence**.
- Do not render Begin consolidation on DPP detail, Activate, Publish, Requisition or source edit.

## 9. Exact consolidation, workbench, removal and Plan Item frame blocks

### 9.1 PLN-UI-02__BEGIN-CONSOLIDATION

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-CONF-01 |
| Purpose / actor | Confirm creation/reuse of the one Annual Plan Draft; Mercy Kilonzo. |
| Origin / route | Workspace **Begin consolidation**. |
| State / reads | CTX-MOH-2027-2028; no Plan root; one eligible accepted DPP source. |
| Visible outcome | **Begin consolidation** represents atomic root/Draft creation and source hold. |

Frame block:

- Frame name: **PLN-UI-02__BEGIN-CONSOLIDATION**.
- Breadcrumb **Procurement Planning / Begin consolidation**; H1 **Begin Annual Plan consolidation**; description **Confirm the Annual Procurement Plan and accepted departmental source that will open Draft Version 1.**
- One compact panel **Plan identity** with read-only rows in order: **Procuring Entity — Ministry of Health**; **Financial year — 2027/28**; **Plan period — 1 July 2027 to 30 June 2028**; **Plan title — Ministry of Health Annual Procurement Plan 2027/28**; **Reporting currency — KES**.
- Section **Accepted departmental sources**: **Departmental submissions — 1**; **Accepted requirements — 1**; **Indicative value — KES 80,000,000**; source line **Digital Health · DPPS-MOH-DIGITAL-2027-001-V1**.
- Exact effect copy: **Beginning consolidation creates or reuses the one Annual Plan root and Draft Version 1 for this PE/FY. It does not approve the Plan.**
- Footer **Cancel**; primary **Begin consolidation**.
- Do not render editable PE/FY/title/currency/unit, **Create plan**, blank metadata, Budget approval, method or source checkbox.

### 9.2 PLN-UI-03__INITIAL-DRAFT-ZERO-ITEM

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-WB-01 |
| Purpose / actor | Show the zero-item initial Draft and the accepted source available for formation; Mercy Kilonzo. |
| Origin / route | Successful Begin consolidation or workspace **View plan update**. |
| State / reads | PLN-MOH-2027-001-V1 Draft; zero items; one available accepted entry. |
| Visible outcome | **Add accepted departmental requirements** represents opening PLN-UI-04. |

Frame block:

- Frame name: **PLN-UI-03__INITIAL-DRAFT-ZERO-ITEM**.
- Breadcrumb **Procurement Planning / Ministry of Health Annual Procurement Plan 2027/28**; H1 **Ministry of Health Annual Procurement Plan 2027/28**; quiet **PLN-MOH-2027-001**; state **Draft Version 1**; period **1 July 2027 to 30 June 2028**; primary **Add accepted departmental requirements**.
- Summary: **Plan Items — 0**; **Draft planned value — KES 0**; **Accepted requirements available — 1**; **Finance confirmed — 0 of 0**; **Validation — Not run**.
- Issue strip: **One accepted departmental requirement is available to form into a Plan Item.**
- Main panel heading **Plan Items**; empty heading **No Plan Items yet**; copy **Add the accepted Digital Health requirement to begin completing the Annual Plan.**
- Quiet **Back to Procurement Planning**.
- Do not render filters over the empty table, manual blank item, disabled submit, editable header, contribution/package concept or source row inside the empty item table.

### 9.3 PLN-UI-04__ONE-SOURCE

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-SELECT-01 |
| Purpose / actor | Form one item from one accepted current departmental entry; Mercy Kilonzo. |
| Origin / route | PLN-UI-03 or 05 **Add accepted departmental requirements**. |
| State / reads | Draft V1; exactly one current accepted, unconsumed source selected. |
| Visible outcome | **Create Plan Item and continue** represents one item and one allocation. |

Frame block:

- Frame name: **PLN-UI-04__ONE-SOURCE**.
- Large focused dialog title **Add accepted departmental requirements** over dimmed Draft workbench.
- Header context: **Ministry of Health Annual Procurement Plan 2027/28**; **Draft Version 1**.
- Controls in one row: search **Search accepted requirements** empty; select **Department — All permitted departments**; checkbox **Available to plan only** checked.
- Table columns: checkbox; **Requirement**; **Departmental submission**; **Department**; **Type**; **Quantity**; **Value**; **Required by**; **Funding**; **Status**.
- One checked row: **National digital health infrastructure upgrade** with quiet **NDS-MOH-2027-0001**; **DPPS-MOH-DIGITAL-2027-001-V1**; **Digital Health**; **Non-consulting services**; **1 programme**; **KES 80,000,000**; **31 August 2027**; **Government of Kenya**; **Available**.
- Selected-source panel: **1 accepted requirement · 1 departmental source · KES 80,000,000**; **Need — NDS-MOH-2027-0001**; **DPP submission — DPPS-MOH-DIGITAL-2027-001-V1**; **Result — 1 Plan Item and 1 source allocation will be created.**
- Footer **Cancel**; primary **Create Plan Item and continue**.
- Do not render a second formation question, Need edit, amount input, package, lot, method or Tender control.

### 9.4 PLN-UI-04__MULTI-COMBINED

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-SELECT-01 |
| Purpose / actor | Show the exact combined result for two compatible sources; Mercy Kilonzo. |
| Origin / route | Source selection with NDS-MOH-2027-0003 and NDS-MOH-2027-0004 selected. |
| State / reads | Initial Draft isolated combine profile; 2 current accepted unconsumed sources. |
| Visible outcome | **Create combined Plan Item and continue** represents one item and two allocations. |

Frame block:

- Frame name: **PLN-UI-04__MULTI-COMBINED**.
- Large focused dialog title **Add accepted departmental requirements** over the dimmed Draft Version 1 workbench.
- Header context: **Ministry of Health Annual Procurement Plan 2027/28**; **Draft Version 1**.
- Controls in one row: search **Search accepted requirements** empty; select **Department — All permitted departments**; checkbox **Available to plan only** checked.
- Table columns: checkbox; **Requirement**; **Departmental submission**; **Department**; **Type**; **Quantity**; **Value**; **Required by**; **Funding**; **Status**.
- Show exactly two checked rows and no others: **Clinical training laptops for digital health rollout** with quiet **NDS-MOH-2027-0003**; **DPPS-MOH-HR-2027-002-V1**; **Human Resources Management and Development**; **Goods**; **200 each**; **KES 48,000,000**; **31 December 2027**; **Government of Kenya**; **Available**. **Clinical deployment laptops for digital health rollout** with quiet **NDS-MOH-2027-0004**; **DPPS-MOH-DIGITAL-2027-002-V1**; **Digital Health**; **Goods**; **300 each**; **KES 72,000,000**; **31 December 2027**; **Government of Kenya**; **Available**.
- Section **Create Plan Items**; summary **2 accepted requirements · 2 departments · 500 each · KES 120,000,000**.
- Question **How should these requirements be added?**
- Unselected radio **One Plan Item for each selected requirement**; helper **Creates 2 separate Plan Items.**
- Selected radio **One combined Plan Item for all selected requirements**; helper **Creates 1 Plan Item while retaining both departmental and funding sources.**
- Required multiline **Why should these requirements be procured together?** with value **Procure one standard laptop specification and deployment service for the same national digital-health rollout.**
- Result panel **1 combined Plan Item · 2 source allocations · 500 each · KES 120,000,000**.
- Footer **Cancel**; primary **Create combined Plan Item and continue**.
- Do not render an automated recommendation, department incompatibility warning, per-source procurement treatment or hidden source loss.

### 9.5 PLN-UI-04__MULTI-SEPARATE

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-SELECT-01 |
| Purpose / actor | Show the exact separate result for NDS-MOH-2027-0003 and NDS-MOH-2027-0004; Mercy Kilonzo. |
| Origin / route | Source selection with both named Needs selected and separate formation chosen. |
| State / reads | Two current accepted, unconsumed laptop Needs from Human Resources Management and Development and Digital Health; separate formation selected. |
| Visible outcome | **Create 2 Plan Items** represents two items and two allocations. |

Frame block:

- Frame name: **PLN-UI-04__MULTI-SEPARATE**.
- Large focused dialog title **Add accepted departmental requirements** over the dimmed Draft Version 1 workbench.
- Header context: **Ministry of Health Annual Procurement Plan 2027/28**; **Draft Version 1**.
- Controls in one row: search **Search accepted requirements** empty; select **Department — All permitted departments**; checkbox **Available to plan only** checked.
- Table columns: checkbox; **Requirement**; **Departmental submission**; **Department**; **Type**; **Quantity**; **Value**; **Required by**; **Funding**; **Status**.
- Show two checked rows and no other row: **Clinical training laptops for digital health rollout** / **NDS-MOH-2027-0003** / **DPPS-MOH-HR-2027-002-V1** / **Human Resources Management and Development** / **Goods** / **200 each** / **KES 48,000,000** / **31 December 2027** / **Government of Kenya** / **Available**; and **Clinical deployment laptops for digital health rollout** / **NDS-MOH-2027-0004** / **DPPS-MOH-DIGITAL-2027-002-V1** / **Digital Health** / **Goods** / **300 each** / **KES 72,000,000** / **31 December 2027** / **Government of Kenya** / **Available**.
- Section **Create Plan Items**; summary **2 accepted requirements · 2 departments · 500 each · KES 120,000,000**.
- Question **How should these requirements be added?**
- Selected radio **One Plan Item for each selected requirement**; helper **Creates 2 separate Plan Items.**
- Unselected radio **One combined Plan Item for all selected requirements**; helper **Creates 1 Plan Item while retaining both departmental and funding sources.**
- Do not render aggregation reason.
- Result panel **2 Plan Items · 2 source allocations · 500 each · KES 120,000,000**.
- Footer **Cancel**; primary **Create 2 Plan Items**.

### 9.6 PLN-UI-05__INITIAL-DRAFT-INCOMPLETE

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-WB-01 |
| Purpose / actor | Direct the planner to complete a newly formed item in initial Draft V1; Mercy Kilonzo. |
| Origin / route | Return from one-source formation. |
| State / reads | Draft V1; PPI-MOH-2027-021 Proposed; Planning not started. |
| Visible outcome | **Complete item** opens the focused editor. |

Frame block:

- Frame name: **PLN-UI-05__INITIAL-DRAFT-INCOMPLETE**.
- Breadcrumb **Procurement Planning / Ministry of Health Annual Procurement Plan 2027/28**; H1 **Ministry of Health Annual Procurement Plan 2027/28**; quiet **PLN-MOH-2027-001**; state **Draft Version 1**; period **1 July 2027 to 30 June 2028**; primary **Add accepted departmental requirements**.
- Summary: **Plan Items — 1**; **Draft planned value — KES 80,000,000**; **Planning complete — 0 of 1**; **Finance confirmed — 0 of 1**; **Validation — Not run**.
- Issue: **One Plan Item needs procurement treatment and schedule before Finance confirmation.**
- Toolbar **Department — All permitted departments**; **Status — All statuses**; **Search Plan Items**.
- Table columns **Change**, **Plan Item**, **Owner**, **Planned value**, **Planning**, **Finance**, **Validation**, **Action**.
- One row: **Added**; **National digital health infrastructure upgrade** with quiet **PPI-MOH-2027-021**; **Digital Health**; **KES 80,000,000**; **Not started**; **Not requested**; **Not run**; primary **Complete item**; restrained overflow.
- Bottom **Back to Procurement Planning**.
- Do not render Active predecessor, raw diff, method/schedule columns, Finance task action or submission.

### 9.7 PLN-UI-05__SUCCESSOR-INCOMPLETE

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-WB-01 |
| Purpose / actor | Show Active V1 separately from Draft V2 while the added item needs planner work; Mercy Kilonzo. |
| Origin / route | Workspace **View plan update** after forming PPI-MOH-2027-022. |
| State / reads | Active V1 KES 80,000,000; Draft V2 KES 120,000,000; added PPI-MOH-2027-022 incomplete. |
| Visible outcome | **Complete item**, **View approved plan**, Save and add-source labels only. |

Frame block:

- Frame name: **PLN-UI-05__SUCCESSOR-INCOMPLETE**.
- Breadcrumb **Procurement Planning / Ministry of Health Annual Procurement Plan 2027/28**; H1 **Ministry of Health Annual Procurement Plan 2027/28**; quiet **PLN-MOH-2027-001**; state **Draft Version 2**; copy **Active Version 1 remains operational while this update is prepared.**; primary **Add accepted departmental requirements**.
- Summary: **Draft Plan Items — 2**; **Draft planned value — KES 120,000,000**; **Net change — KES 40,000,000 added**; **Planning complete — 1 of 2**; **Finance confirmed — 1 of 2**; **Validation — Needs attention**.
- Update reason multiline value **Add the accepted digital-health workforce certification programme to the FY 2027/28 Plan.**; helper **Explain why the Active Plan needs to change.**
- Issue **Complete PPI-MOH-2027-022 before Finance confirmation can be requested.**
- Changed-items table columns **Change**, **Plan Item**, **Owner**, **Planned value**, **Planning**, **Finance**, **Validation**, **Action**. One row: **Added**; **Digital health workforce certification programme** with quiet **PPI-MOH-2027-022**; **Human Resources Management and Development**; **KES 40,000,000**; **Not started**; **Not requested**; **Needs attention**; **Complete item**; overflow **Remove from draft**.
- Read-only line **1 unchanged Active Plan Item remains operational in Version 1.**; quiet **View approved plan**.
- Bottom **Back to Procurement Planning**; primary **Save draft**.
- Do not render submission, Finance controls, full Active rows or direct removal mutation.

### 9.8 PLN-UI-05__SUCCESSOR-FINANCE-WAITING

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-WB-01 |
| Purpose / actor | Show the completed added item while Finance owns the protected task; Mercy Kilonzo. |
| Origin / route | Return to workbench after Finance request. |
| State / reads | Draft V2; Planning 2 of 2; Finance 1 of 2; PPI-MOH-2027-022 Awaiting confirmation. |
| Visible outcome | Neutral **View Plan Item**, Save and approved-detail labels; no Finance action. |

Frame block:

- Frame name: **PLN-UI-05__SUCCESSOR-FINANCE-WAITING**.
- Breadcrumb **Procurement Planning / Ministry of Health Annual Procurement Plan 2027/28**; H1 **Ministry of Health Annual Procurement Plan 2027/28**; quiet **PLN-MOH-2027-001**; state **Draft Version 2**; copy **Active Version 1 remains operational while this update is prepared.**; primary **Add accepted departmental requirements**.
- Summary: **Draft Plan Items — 2**; **Draft planned value — KES 120,000,000**; **Net change — KES 40,000,000 added**; **Planning complete — 2 of 2**; **Finance confirmed — 1 of 2**; **Validation — Needs attention**.
- Update reason multiline value **Add the accepted digital-health workforce certification programme to the FY 2027/28 Plan.**; helper **Explain why the Active Plan needs to change.**
- Issue **Funding confirmation is still required for PPI-MOH-2027-022 before this Plan can be submitted for professional validation.**
- Table columns **Change**, **Plan Item**, **Owner**, **Planned value**, **Planning**, **Finance**, **Validation**, **Action**. One row: **Added**; **Digital health workforce certification programme** with quiet **PPI-MOH-2027-022**; **Human Resources Management and Development**; **KES 40,000,000**; Planning **Complete**; Finance **Awaiting confirmation**; Validation **Needs attention**; action **View Plan Item**; overflow **Remove from draft**.
- Read-only line **1 unchanged Active Plan Item remains operational in Version 1.**; quiet **View approved plan**.
- Bottom **Back to Procurement Planning**; primary **Save draft**.
- Do not render Submit, Budget arithmetic, Finance drawer/action or disabled confirmation.

### 9.9 PLN-UI-05__SUCCESSOR-READY

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-WB-01 |
| Purpose / actor | Show a complete, funded Draft successor ready for professional submission; Mercy Kilonzo. |
| Origin / route | Return after current Finance confirmation. |
| State / reads | Draft V2; Planning 2/2; Finance 2/2; no blocker. |
| Visible outcome | **Submit for professional validation** represents immutable submission/task creation. |

Frame block:

- Frame name: **PLN-UI-05__SUCCESSOR-READY**.
- Breadcrumb **Procurement Planning / Ministry of Health Annual Procurement Plan 2027/28**; H1 **Ministry of Health Annual Procurement Plan 2027/28**; quiet **PLN-MOH-2027-001**; state **Draft Version 2**; copy **Active Version 1 remains operational while this update is prepared.**; primary **Add accepted departmental requirements**.
- Summary: **Draft Plan Items — 2**; **Draft planned value — KES 120,000,000**; **Net change — KES 40,000,000 added**; **Planning complete — 2 of 2**; **Finance confirmed — 2 of 2**; **Validation — Ready**.
- Update reason multiline value **Add the accepted digital-health workforce certification programme to the FY 2027/28 Plan.**; helper **Explain why the Active Plan needs to change.**
- Success strip **All required Planning validation and Finance confirmations are ready.**
- Table columns **Change**, **Plan Item**, **Owner**, **Planned value**, **Planning**, **Finance**, **Validation**, **Action**. One row: **Added**; **Digital health workforce certification programme** with quiet **PPI-MOH-2027-022**; **Human Resources Management and Development**; **KES 40,000,000**; Planning **Complete**; Finance **Confirmed**; Validation **Ready**; action **View Plan Item**; overflow **Remove from draft**.
- Read-only line **1 unchanged Active Plan Item remains operational in Version 1.**; quiet **View approved plan**.
- Bottom actions **Back to Procurement Planning**; **Save draft**; primary **Submit for professional validation**.
- Do not render submission result, task owner controls, generic **Submit for review**, approval/publication or Tender action.

### 9.10 PLN-UI-05__SUCCESSOR-RETURNED

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-WB-01 |
| Purpose / actor | Show a professionally returned immutable version and governed correction path; Mercy Kilonzo. |
| Origin / route | Workspace returned-work row. |
| State / reads | Returned V2; Active V1 preserved; professional return evidence. |
| Visible outcome | **Edit Plan Item** and Save labels only. |

Frame block:

- Frame name: **PLN-UI-05__SUCCESSOR-RETURNED**.
- Breadcrumb **Procurement Planning / Ministry of Health Annual Procurement Plan 2027/28**; H1 **Ministry of Health Annual Procurement Plan 2027/28**; quiet **PLN-MOH-2027-001**; header state **Returned Version 2**; copy **Active Version 1 remains operational while the returned update is corrected.**
- Summary keeps Draft KES 120,000,000 and net +40m; **Validation — Needs attention**.
- Update reason multiline value **Add the accepted digital-health workforce certification programme to the FY 2027/28 Plan.**
- Return notice: heading **Returned for correction**; metadata **Samuel Otieno · 18 December 2026 at 10:00 EAT**; reason **Clarify the delivery sequence for the added workforce certification programme before resubmission.**
- One changed row: **Digital health workforce certification programme** with quiet **PPI-MOH-2027-022**; **Human Resources Management and Development**; **KES 40,000,000**; Planning **Complete**; Finance **Confirmed**; Validation **Needs attention**; action **Edit Plan Item**.
- Bottom **Back to Procurement Planning**; primary **Save draft**.
- Do not render response field, Finance/professional controls, submit before a correction or cancellation.

### 9.11 PLN-UI-05__FINANCE-STALE

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-WB-01 |
| Purpose / actor | Show that historical Finance evidence is stale and must be renewed; Mercy Kilonzo. |
| Origin / route | Workbench after a material funding/source/value change. |
| State / reads | Draft V2; PPI-MOH-2027-022 Finance Stale; Active V1 preserved. |
| Visible outcome | **View Plan Item** represents correction/re-request path. |

Frame block:

- Frame name: **PLN-UI-05__FINANCE-STALE**.
- Breadcrumb **Procurement Planning / Ministry of Health Annual Procurement Plan 2027/28**; H1 **Ministry of Health Annual Procurement Plan 2027/28**; quiet **PLN-MOH-2027-001**; state **Draft Version 2**; copy **Active Version 1 remains operational while this update is prepared.**; primary **Add accepted departmental requirements**.
- Summary: **Draft Plan Items — 2**; **Draft planned value — KES 120,000,000**; **Net change — KES 40,000,000 added**; **Planning complete — 2 of 2**; **Finance confirmed — 1 of 2 current**; **Validation — Stale**.
- Update reason multiline value **Add the accepted digital-health workforce certification programme to the FY 2027/28 Plan.**; helper **Explain why the Active Plan needs to change.**
- Issue: **Funding evidence for PPI-MOH-2027-022 is stale. Review the item and request a new Finance confirmation.**
- Table columns **Change**, **Plan Item**, **Owner**, **Planned value**, **Planning**, **Finance**, **Validation**, **Action**. One row: **Added**; **Digital health workforce certification programme** with quiet **PPI-MOH-2027-022**; **Human Resources Management and Development**; **KES 40,000,000**; Planning **Complete**; Finance **Stale**; Validation **Stale**; action **View Plan Item**.
- Read-only line **1 unchanged Active Plan Item remains operational in Version 1.**; quiet **View approved plan**.
- Bottom **Back to Procurement Planning**; primary **Save draft**.
- Do not render historical confirmation as current, Submit, Budget Line editor or Finance decision control.

### 9.12 PLN-UI-05__REMOVAL-ONLY-READY

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-WB-01 |
| Purpose / actor | Show a removal-only successor ready without a new Finance confirmation; Mercy Kilonzo. |
| Origin / route | Workbench after eligible Active whole-item removal is proposed. |
| State / reads | Isolated profile; Active V1 contains PPI-MOH-2027-021 with no downstream use; Draft V2 proposes whole-item removal. |
| Visible outcome | **Submit for professional validation** represents governed successor submission. |

Frame block:

- Frame name: **PLN-UI-05__REMOVAL-ONLY-READY**.
- Breadcrumb **Procurement Planning / Ministry of Health Annual Procurement Plan 2027/28**; H1 **Ministry of Health Annual Procurement Plan 2027/28**; quiet **PLN-MOH-2027-001**; header state **Active Version 1 · Draft Version 2**; copy **The Active item remains operational until this update is approved, published and acknowledged.**
- Summary: **Active value — KES 80,000,000**; **Draft value — KES 0**; **Proposed removals — KES 80,000,000**; **Net change — KES 80,000,000 reduction**; **Validation — Ready**.
- Update reason value **Remove the digital health infrastructure item because the department withdrew the requirement before any downstream execution.**
- Success strip **The eligible whole-item removal is ready. No new Finance confirmation is required for this removal-only update.**
- One row: **Proposed removal**; **National digital health infrastructure upgrade** with quiet **PPI-MOH-2027-021**; owner **Digital Health**; **KES 80,000,000**; Planning **Not applicable**; Finance **Confirmed**; Validation **Ready**; action **View Plan Item**.
- Bottom **Back to Procurement Planning**; **Save draft**; primary **Submit for professional validation**.
- Do not show item as Removed, immediate reservation release, source checkbox, second reason or partial removal.

### 9.13 PLN-UI-05A__DRAFT-ITEM-REMOVAL

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-MODAL-01; accepted PLN-UI-05__SUCCESSOR-INCOMPLETE frame as the dimmed background |
| Purpose / actor | Confirm whole-item removal from Draft V2 before Finance; Mercy Kilonzo. |
| State / reads | PPI-MOH-2027-022 Proposed; KES 40,000,000; Finance Not requested; one source allocation. |
| Visible outcome | **Remove from draft** represents governed removal and Draft-hold release. |

Frame block:

- Frame name: **PLN-UI-05A__DRAFT-ITEM-REMOVAL**.
- Modal title **Remove Plan Item from draft?**
- Intro **This removes the item from Draft Version 2 and releases its Draft source hold.**
- Read-only summary: **Digital health workforce certification programme**; **PPI-MOH-2027-022**; owner **Human Resources Management and Development**; value **KES 40,000,000**; source **NDS-MOH-2027-0002**; **1 source allocation**.
- Finance effect **No Finance task, decision or reservation will be reversed.**
- Required multiline **Reason for removal**; placeholder **Briefly explain why this item should be removed from the draft.**
- Footer **Keep item**; restrained destructive **Remove from draft**.
- Do not render source checkbox, funding edit, hard delete, another update reason or post-success message.

### 9.14 PLN-UI-05A__ACTIVE-ITEM-REMOVAL

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-MODAL-01 over dimmed PLN-UI-09 |
| Purpose / actor | Propose whole-item removal from an Active Plan with no downstream use; Mercy Kilonzo. |
| State / reads | Isolated Active PPI-MOH-2027-021; KES 80,000,000 reservation; no Requisition drawdown, Tender handoff, commitment or execution. |
| Visible outcome | **Add removal to plan update** represents one Draft successor proposal; Active item remains. |

Frame block:

- Frame name: **PLN-UI-05A__ACTIVE-ITEM-REMOVAL**.
- Modal title **Remove Plan Item from active plan?**
- Intro **The item remains active until the plan update is approved, published and acknowledged.**
- Summary: **National digital health infrastructure upgrade**; **PPI-MOH-2027-021**; **Digital Health**; **KES 80,000,000**; source **NDS-MOH-2027-0001**; **1 source allocation**.
- Downstream status: **Requisition drawdown — None**; **Tender handoff — None**; **Commitment/execution — None**.
- Effect: **If the successor activates, the whole item will be removed and reservation RSV-MOH-2027-021-001 will be released through the governed service.**
- Required multiline **Reason for removal**; placeholder **Briefly explain why this item should be removed from the draft.**
- Footer **Keep item**; restrained **Add removal to plan update**.
- Do not render immediate removal, Finance approval, Tender cancellation, source checkbox or second reason.

### 9.15 PLN-UI-05A__COMBINED-ITEM-REMOVAL

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-MODAL-01 over dimmed initial Draft workbench |
| Purpose / actor | Confirm that a combined item is removed only as a whole; Mercy Kilonzo. |
| State / reads | PPI-MOH-2027-033 Proposed; 2 sources; KES 120,000,000; Finance Not requested. |
| Visible outcome | **Remove from draft** represents whole combined-item removal. |

Frame block:

- Frame name: **PLN-UI-05A__COMBINED-ITEM-REMOVAL**.
- Modal title **Remove Plan Item from draft?**; intro **This removes the complete combined Plan Item and all of its source allocations.**
- Summary: **Clinical training and deployment laptops for digital health rollout**; **PPI-MOH-2027-033**; owner **Ministry of Health Procurement Function**; value **KES 120,000,000**.
- Section **Included departmental sources** with exactly two rows: **Clinical training laptops for digital health rollout** / **NDS-MOH-2027-0003** / **Human Resources Management and Development** / **200 each** / **KES 48,000,000** / **DPPS-MOH-HR-2027-002-V1**; and **Clinical deployment laptops for digital health rollout** / **NDS-MOH-2027-0004** / **Digital Health** / **300 each** / **KES 72,000,000** / **DPPS-MOH-DIGITAL-2027-002-V1**.
- Effect **The whole Plan Item and both source allocations will be removed together. Both accepted requirements will become available for planning again.**
- Required **Reason for removal**; footer **Keep item**; **Remove from draft**.
- Do not render source-level checkboxes, partial detachment or per-source removal buttons.

### 9.16 PLN-UI-05B__CANCEL-NO-EFFECTIVE-CHANGE

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-MODAL-01 over dimmed Draft successor workbench |
| Purpose / actor | Confirm cancellation of a successor with no effective change; Mercy Kilonzo. |
| State / reads | Draft V2; Active V1; zero additions/removals/changed sources; KES 80,000,000 unchanged. |
| Visible outcome | **Cancel plan update** represents successor cancellation and Draft-effect release. |

Frame block:

- Frame name: **PLN-UI-05B__CANCEL-NO-EFFECTIVE-CHANGE**.
- Modal title **Cancel plan update?**
- Read-only rows: **Draft successor — PLN-MOH-2027-001-V2**; **Active predecessor — PLN-MOH-2027-001-V1**; **Effective changes — None**; **Active value — KES 80,000,000**.
- Exact statement: **Cancelling Draft Version 2 releases its Draft holds and leaves Active Version 1 unchanged.**
- Required multiline **Reason for cancellation**; placeholder **Briefly explain why this no-change update should be cancelled.**
- Footer **Keep update**; restrained **Cancel plan update**.
- Do not render delete Plan, cancel Active version, change version number or success state.

### 9.17 PLN-UI-06__SINGLE-SOURCE-COMPLETE

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-ITEM-01 |
| Purpose / actor | Complete one existing Proposed item before Finance request; Mercy Kilonzo. |
| Origin / route | Workbench **Complete item** after one-source formation. |
| State / reads | Initial Draft V1; PPI-MOH-2027-021 Proposed; source immutable; Finance Not requested. |
| Visible outcome | **Save draft** and **Request Finance confirmation** represent the two named commands. |

Frame block:

- Frame name: **PLN-UI-06__SINGLE-SOURCE-COMPLETE**.
- Single page, no tabs/stepper. Breadcrumb **Ministry of Health Annual Procurement Plan 2027/28 / PPI-MOH-2027-021**; H1 **National digital health infrastructure upgrade**; quiet **PPI-MOH-2027-021**; context **Draft Version 1 · Added Plan Item**; chips **Proposed**, **Planning complete**; value **KES 80,000,000**.
- Section **Accepted departmental source**: DPP submission and Need refs; **Digital Health**; **Non-consulting services**; **1 programme**; **31 August 2027**; **Government of Kenya**; **KES 80,000,000**; quiet **View accepted Need** and **View DPP submission**.
- Quiet note **The accepted source controls the business scope, unit, quantity, required-by date, funding and planned value. Correct those facts in the owning module.**
- Section **Procurement approach**: required multiline **Plan Item description** value **Procure and implement the accepted national digital health infrastructure upgrade as one integrated FY 2027/28 programme.**; read-only **Requirement type — Non-consulting services**; read-only **Planned value — KES 80,000,000**.
- Recommendation strip **Recommended method — Open Tender**; helper **Configured competitive method for this requirement type and planned value.**
- Required single-select **Planned procurement method — Open Tender** with no other visible option; required fixed select **Contract period — Single year**; section **Indicative lotting** with selected fixed choice **No lots expected** only.
- Planned schedule table with canonical seven milestone labels/dates from PLN-CAN-001: 1 May; 23 May; 23 June; 10 July; 14 July; 1 August; 31 August 2027. Derived **Planned time to contract signature — 92 days**.
- Sticky footer **Back to plan update**; **Save draft**; primary **Request Finance confirmation**.
- Do not render source selection, aggregation, editable value/unit/quantity/funding, Multi-year, Lots expected, alternative method, technical specification, Requisition/Tender creation or approval controls.

### 9.18 PLN-UI-06__FINANCE-RETURNED

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-ITEM-01 |
| Purpose / actor | Correct planner-owned fields after Finance return while preserving source facts; Mercy Kilonzo. |
| Origin / route | Workbench returned row. |
| State / reads | PPI-MOH-2027-021 single-source item; Finance Returned; no reservation; immutable return evidence. |
| Visible outcome | Save or later re-request Finance after correction. |

Frame block:

- Frame name: **PLN-UI-06__FINANCE-RETURNED**.
- Single page, no tabs/stepper. Breadcrumb **Ministry of Health Annual Procurement Plan 2027/28 / PPI-MOH-2027-021**; H1 **National digital health infrastructure upgrade**; quiet **PPI-MOH-2027-021**; context **Draft Version 1 · Added Plan Item**; chips **Proposed**, **Planning complete**, **Returned by Finance**; value **KES 80,000,000**.
- Section **Accepted departmental source**: DPP submission **DPPS-MOH-DIGITAL-2027-001-V1** and Need **NDS-MOH-2027-0001**; **Digital Health**; **Non-consulting services**; **1 programme**; **31 August 2027**; **Government of Kenya**; **KES 80,000,000**; quiet **View accepted Need** and **View DPP submission**.
- Quiet note **The accepted source controls the business scope, unit, quantity, required-by date, funding and planned value. Correct those facts in the owning module.**
- Section **Procurement approach**: required multiline **Plan Item description** value **Procure and implement the accepted national digital health infrastructure upgrade as one integrated FY 2027/28 programme.**; read-only **Requirement type — Non-consulting services**; read-only **Planned value — KES 80,000,000**.
- Recommendation strip **Recommended method — Open Tender**; required single-select **Planned procurement method — Open Tender** with no other visible option; required fixed select **Contract period — Single year**; **Indicative lotting — No lots expected** only.
- Planned schedule table: **Invitation or advertisement — 1 May 2027**; **Bid opening — 23 May 2027**; **Evaluation completion — 23 June 2027**; **Tender award approval — 10 July 2027**; **Notification of award — 14 July 2027**; **Contract signing — 1 August 2027**; **Delivery or implementation completion — 31 August 2027**; derived **Planned time to contract signature — 92 days**.
- Return notice heading **Returned by Finance**; metadata **MOH Budget Officer · 4 December 2026 at 09:58 EAT**; reason **Funding availability is KES 10,000,000 below the amount required. Resolve the Budget Line or authoritative source before requesting Finance again.**
- Keep source block read-only and planner-owned fields editable. Footer **Back to plan update**; **Save draft**; primary **Request Finance confirmation**.
- Do not render Budget Line edit, requested amount override, Finance decision form, historical reservation as current or source correction input.

### 9.19 PLN-UI-06__COMBINED-SOURCE-COMPLETE

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-ITEM-01 |
| Purpose / actor | Complete one combined Proposed item while retaining all source departments/allocations; Mercy Kilonzo. |
| Origin / route | Successful combined formation. |
| State / reads | PPI-MOH-2027-033; 2 current source allocations; KES 120,000,000; Finance Not requested. |
| Visible outcome | Save / Request Finance for the one combined item. |

Frame block:

- Frame name: **PLN-UI-06__COMBINED-SOURCE-COMPLETE**.
- Single page, no tabs/stepper. Breadcrumb **Ministry of Health Annual Procurement Plan 2027/28 / PPI-MOH-2027-033**; H1 **Clinical training and deployment laptops for digital health rollout**; quiet **PPI-MOH-2027-033**; context **Draft Version 1 · Added Plan Item**; owner **Ministry of Health Procurement Function**; chips **Proposed**, **Planning complete**; value **KES 120,000,000**.
- Accepted departmental sources table columns **Requirement**, **DPP submission**, **Department**, **Quantity**, **Value**, **Funding**; row 1 **Clinical training laptops for digital health rollout** / **NDS-MOH-2027-0003** / **DPPS-MOH-HR-2027-002-V1** / **Human Resources Management and Development** / **200 each** / **KES 48,000,000** / **Government of Kenya**; row 2 **Clinical deployment laptops for digital health rollout** / **NDS-MOH-2027-0004** / **DPPS-MOH-DIGITAL-2027-002-V1** / **Digital Health** / **300 each** / **KES 72,000,000** / **Government of Kenya**.
- Summary **2 sources · 500 each · KES 120,000,000**.
- Procurement approach: description **Procure one standard laptop specification and deployment service for the national digital-health rollout across both source departments.**; requirement type **Goods**; planned value **KES 120,000,000**; read-only **Aggregation reason — Procure one standard laptop specification and deployment service for the same national digital-health rollout.**
- Method **Open Tender**; period **Single year**; **No lots expected**.
- Schedule: **Invitation — 1 September 2027**; **Bid opening — 22 September**; **Evaluation completion — 20 October**; **Tender award approval — 3 November**; **Notification of award — 6 November**; **Contract signing — 15 November**; **Delivery/implementation completion — 31 December 2027**; derived **75 days**.
- Sticky footer **Back to plan update**; **Save draft**; primary **Request Finance confirmation**.
- Do not render per-source procurement treatment, source edit/detachment, second editor, lot splitting or partial Finance request.

## 10. Exact Finance frame blocks

### 10.1 PLN-UI-07__SUFFICIENT-SINGLE-SOURCE

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-FIN-01 |
| Purpose / actor | Decide full funding for one protected single-source task; MOH Budget Officer, `moh.budget.officer@example.test`. |
| Origin / route | Finance work queue **Review financial reconciliation**. |
| State / reads | Draft V1, PPI-MOH-2027-021 Planning complete, Awaiting confirmation, sufficient live funding. |
| Visible outcome | **Confirm funding** represents all-source reservation/decision; **Return to planner** opens 07A-2. |

Frame block:

- Frame name: **PLN-UI-07__SUFFICIENT-SINGLE-SOURCE**.
- Focused right drawer over dimmed **Finance work queue**; same existing dimensions as VB-FIN-01.
- Drawer header: H1 **Confirm Plan Item funding**; quiet **PPI-MOH-2027-021**; context **Ministry of Health Annual Procurement Plan 2027/28 · Draft Version 1**; chips **Awaiting confirmation**, **Sufficient funding**; close icon label **Close**.
- Section **Plan Item**: title; owner **Digital Health**; DPP source **DPPS-MOH-DIGITAL-2027-001-V1**; Need **NDS-MOH-2027-0001**; **1 programme**; **31 August 2027**; **Amount requiring confirmation — KES 80,000,000**; quiet **View Plan Item**.
- Section **Funding position** with rows in exact order: **Budget Line — MOH-BL-DHI-2027 · Digital health infrastructure programme · Government of Kenya**; **Approved — KES 100,000,000**; **Reserved — KES 0**; **Committed — KES 0**; **Available now — KES 100,000,000**; **Amount to reserve — KES 80,000,000**; **Available after confirmation — KES 20,000,000**; **As at — 4 December 2026 at 09:55 EAT**; quiet **Open Budget & Funding**.
- Notice: **Confirming funding will reserve KES 80,000,000 for this Plan Item. It does not approve the Annual Procurement Plan.**
- Empty multiline **Finance note**; helper **Optional when confirming.**
- Footer **Cancel**; **Return to planner**; primary **Confirm funding**.
- Do not render editable funding, Budget selector, partial amount, override, Approve/Reject, Plan editor, reservation reference before confirmation or generic approval matrix.

### 10.2 PLN-UI-07__SUFFICIENT-COMBINED-SOURCE

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-FIN-01 |
| Purpose / actor | Show all funding sources and an atomic full-confirmation decision for PPI-MOH-2027-033; MOH Budget Officer, `moh.budget.officer@example.test`. |
| Origin / route | Finance queue combined-source task. |
| State / reads | PPI-MOH-2027-033; two allocations; both fully available; KES 120,000,000. |
| Visible outcome | One **Confirm funding** represents both reservations and one decision. |

Frame block:

- Frame name: **PLN-UI-07__SUFFICIENT-COMBINED-SOURCE**.
- Focused right drawer over dimmed **Finance work queue**, matching VB-FIN-01 dimensions.
- Drawer header: H1 **Confirm Plan Item funding**; quiet **PPI-MOH-2027-033**; context **Ministry of Health Annual Procurement Plan 2027/28 · Draft Version 1**; chips **Awaiting confirmation**, **Sufficient funding**; close icon label **Close**.
- Section **Plan Item**: title **Clinical training and deployment laptops for digital health rollout**; owner **Ministry of Health Procurement Function**; **2 departmental sources · 500 each**; **Amount requiring confirmation — KES 120,000,000**; quiet **View Plan Item**.
- Section **Source allocations** table columns **Source**, **Department**, **Budget Line**, **Required amount**, **Available now**, **After confirmation**.
- Row 1: **Clinical training laptops for digital health rollout** with quiet **NDS-MOH-2027-0003**; **Human Resources Management and Development**; **MOH-BL-HWD-2027 — Digital health workforce development**; **KES 48,000,000**; **KES 60,000,000**; **KES 12,000,000**.
- Row 2: **Clinical deployment laptops for digital health rollout** with quiet **NDS-MOH-2027-0004**; **Digital Health**; **MOH-BL-DHI-2027 — Digital health infrastructure programme**; **KES 72,000,000**; **KES 100,000,000**; **KES 28,000,000**.
- Totals row **Required — KES 120,000,000**; **Available — KES 160,000,000**; **After confirmation — KES 40,000,000**; As at **4 December 2026 at 09:55 EAT**.
- Notice: **Confirming funding will reserve every source allocation in one decision. It does not approve the Annual Procurement Plan.**
- Empty multiline **Finance note**; helper **Optional when confirming.**
- Footer **Cancel**; **Return to planner**; primary **Confirm funding**.
- Do not render per-source Confirm buttons, partial source selection, substitution or split decision.

### 10.3 PLN-UI-07A-1__INSUFFICIENT

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-FIN-01 |
| Purpose / actor | Show the exact shortfall in the current Finance task; MOH Budget Officer, `moh.budget.officer@example.test`. |
| Origin / route | Finance work queue or refresh of the protected task. |
| State / reads | PPI-MOH-2027-021 Awaiting confirmation; KES 10,000,000 shortfall profile. |
| Visible outcome | **Open Budget & Funding** represents navigation only; **Return to planner** opens 07A-2. |

Frame block:

- Frame name: **PLN-UI-07A-1__INSUFFICIENT**.
- Focused right drawer over dimmed **Finance work queue**, matching VB-FIN-01 dimensions. H1 **Funding shortfall**; quiet **PPI-MOH-2027-021**; context **Ministry of Health Annual Procurement Plan 2027/28 · Draft Version 1**; chips **Awaiting confirmation**, **Insufficient funding**; close icon label **Close**.
- Section **Plan Item**: title **National digital health infrastructure upgrade**; owner **Digital Health**; DPP source **DPPS-MOH-DIGITAL-2027-001-V1**; Need **NDS-MOH-2027-0001**; **1 programme**; **31 August 2027**; **Amount requiring confirmation — KES 80,000,000**; quiet **View Plan Item**.
- Section **Funding position** rows: **Budget Line — MOH-BL-DHI-2027 · Digital health infrastructure programme · Government of Kenya**; **Approved — KES 100,000,000**; **Reserved — KES 30,000,000**; **Committed — KES 0**; **Available now — KES 70,000,000**; **Amount required — KES 80,000,000**; **Shortfall — KES 10,000,000**; **As at — 4 December 2026 at 09:55 EAT**.
- Warning: **KES 70,000,000 is currently available. A further KES 10,000,000 is required before funding can be confirmed.**
- Supporting line **Review the Budget Line in Budget & Funding, or return the Plan Item to the planner.**
- Footer **Close**; **Return to planner**; primary route button **Open Budget & Funding**.
- Do not render Finance note, reason field, Confirm/disabled Confirm, editable funding, partial amount, override, Approve/Reject or mutation explanation.

### 10.4 PLN-UI-07A-2__RETURN-CONFIRMATION

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-MODAL-01; accepted PLN-UI-07A-1__INSUFFICIENT drawer frame as the dimmed background |
| Purpose / actor | Capture the exact reason for returning the item; MOH Budget Officer, `moh.budget.officer@example.test`. |
| State / reads | PPI-MOH-2027-021 shortfall task; KES 10,000,000 shortfall. |
| Visible outcome | **Return to planner** represents a no-reservation Finance return. |

Frame block:

- Frame name: **PLN-UI-07A-2__RETURN-CONFIRMATION**.
- Modal title **Return Plan Item to planner?**
- Intro **The Plan Item will return to the planner for correction. No funding will be reserved.**
- Read-only **PPI-MOH-2027-021 — National digital health infrastructure upgrade**; **Funding shortfall — KES 10,000,000**.
- Required multiline **Reason for return** with value **Funding availability is KES 10,000,000 below the amount required. Resolve the Budget Line or authoritative source before requesting Finance again.**
- Footer **Cancel**; restrained **Return to planner**.
- Do not render Budget edit, Confirm, Reject, Plan approval, source amendment control or post-return message.

### 10.5 PLN-UI-07B__PLANNER-NEUTRAL-WAITING

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-ITEM-01 |
| Purpose / actor | Show neutral item detail while the protected Finance task belongs to another actor; Mercy Kilonzo. |
| Origin / route | Workbench **View Plan Item** while Finance is pending. |
| State / reads | PPI-MOH-2027-021 read-only; Finance Awaiting confirmation; funding-request context only. |
| Visible outcome | Read-only **Back to plan update** and **View evidence**. |

Frame block:

- Frame name: **PLN-UI-07B__PLANNER-NEUTRAL-WAITING**.
- Single read-only page, no tabs/stepper. Breadcrumb **Ministry of Health Annual Procurement Plan 2027/28 / PPI-MOH-2027-021**; H1 **National digital health infrastructure upgrade**; quiet **PPI-MOH-2027-021**; context **Draft Version 1 · Added Plan Item**; chips **Proposed**, **Awaiting Finance confirmation**; value **KES 80,000,000**.
- Notice: **Waiting on Budget Officer. The Plan Item is read-only while Finance reconciliation is pending.**
- Section **Accepted departmental source**: DPP submission **DPPS-MOH-DIGITAL-2027-001-V1** and Need **NDS-MOH-2027-0001**; **Digital Health**; **Non-consulting services**; **1 programme**; **31 August 2027**; **Government of Kenya**; **KES 80,000,000**; quiet **View accepted Need** and **View DPP submission**.
- Section **Procurement approach** as read-only values: **Plan Item description — Procure and implement the accepted national digital health infrastructure upgrade as one integrated FY 2027/28 programme.**; **Requirement type — Non-consulting services**; **Planned value — KES 80,000,000**; **Planned procurement method — Open Tender**; **Contract period — Single year**; **Indicative lotting — No lots expected**.
- Section **Planned schedule** as read-only values: **Invitation or advertisement — 1 May 2027**; **Bid opening — 23 May 2027**; **Evaluation completion — 23 June 2027**; **Tender award approval — 10 July 2027**; **Notification of award — 14 July 2027**; **Contract signing — 1 August 2027**; **Delivery or implementation completion — 31 August 2027**; **Planned time to contract signature — 92 days**.
- Funding-request summary: **Requested amount — KES 80,000,000**; **Requested by — Mercy Kilonzo**; **Requested — 4 December 2026 at 09:45 EAT**; **Current owner — Budget Officer**; quiet **View evidence**.
- Footer **Back to plan update** only.
- Do not render Budget Line amounts, Finance note, Confirm/Return, Save, Request again or disabled task controls.

## 11. Exact professional validation, AO certification, approval and publication frame blocks

The three governance review pages reuse VB-REVIEW-01 but are generated independently. They may share geometry; they must not share generic **Review and approve** copy, actor labels or decision buttons.

### 11.1 PLN-UI-08__PROFESSIONAL-VALIDATION

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-REVIEW-01 |
| Purpose / actor | Professionally validate the exact Finance-confirmed Plan Version; Samuel Otieno, Head of Procurement Function. |
| Origin / route | Workspace **Review plan version**. |
| State / reads | PLN-MOH-2027-001-V1 submitted for professional validation; one item; KES 80,000,000; no predecessor. |
| Visible outcome | **Validate and submit to Accounting Officer** or **Return to planner**. |

Frame block:

- Frame name: **PLN-UI-08__PROFESSIONAL-VALIDATION**.
- Wide read-only page with right decision rail; no tabs/stepper.
- Breadcrumb **Procurement Planning / Professional validation / PLN-MOH-2027-001-V1**; H1 **Validate procurement plan**; context **Ministry of Health Annual Procurement Plan 2027/28 · Version 1**; chips **Professional validation**, **Ready**.
- Quiet notice **This is a professional validation decision. It does not approve, activate or publish the Annual Procurement Plan.**
- Summary in order: **Plan Items — 1**; **Submitted value — KES 80,000,000**; **Departmental sources — 1 of 1 current**; **Finance confirmed — 1 of 1**; **Validation — Ready**.
- Section **Submission context**: **Purpose — Initial Annual Procurement Plan**; **Predecessor — None**; **Submitted by — Mercy Kilonzo**; **Submitted — 7 December 2026 at 09:30 EAT**.
- Section **Plan Items in Version 1** table columns **Plan Item**, **Departmental source**, **Owner**, **Planned value**, **Method**, **Completion**, **Finance**, **Validation**, **Action**. One row: **National digital health infrastructure upgrade** with quiet **PPI-MOH-2027-021**; **DPPS-MOH-DIGITAL-2027-001-V1 · NDS-MOH-2027-0001**; **Digital Health**; **KES 80,000,000**; **Open Tender**; **31 August 2027**; **Confirmed**; **Ready**; quiet **View Plan Item**.
- Review notice **All required Planning validation and Finance confirmation are ready for professional decision.**
- Decision history: **Plan root and Draft Version 1 created — Mercy Kilonzo — 1 December 2026 at 09:00 EAT**; **Funding confirmed — MOH Budget Officer — 4 December 2026 at 10:00 EAT**; **Submitted for professional validation — Mercy Kilonzo — 7 December 2026 at 09:30 EAT**.
- Right rail: heading **Professional validation**; **Submitted Version — Version 1**; **Finance confirmation — Complete**; **Validation — Ready**; empty multiline **Professional note**, helper **Optional**; secondary **Return to planner**; primary **Validate and submit to Accounting Officer**.
- Do not render final approval language, AO/authority decision, editable item/funding, generic approval matrix or publication control.

### 11.2 PLN-UI-08R__PROFESSIONAL-RETURN

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-MODAL-01; accepted PLN-UI-08__PROFESSIONAL-VALIDATION frame as the dimmed background |
| Purpose / actor | Capture an actionable professional return reason; Samuel Otieno. |
| State / reads | Immutable PLN-MOH-2027-001-V1 professional-validation task. |
| Visible outcome | **Return to planner** represents a named return decision. |

Frame block:

- Frame name: **PLN-UI-08R__PROFESSIONAL-RETURN**.
- Modal title **Return Plan Version to planner?**
- Intro **The exact submitted Version 1 will remain unchanged. The planner must use the governed correction path before resubmission.**
- Read-only **Plan Version — PLN-MOH-2027-001-V1**; **Submitted value — KES 80,000,000**; **Stage — Professional validation**.
- Required multiline **Reason for return**; exact value **Clarify the delivery sequencing evidence for the digital health infrastructure programme before resubmission.**
- Footer **Cancel**; restrained **Return to planner**.
- Do not render item edit, Finance/Budget, AO/approval, publication or success state.

### 11.3 PLN-UI-08A__AO-CERTIFICATION

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-REVIEW-01 |
| Purpose / actor | Certify the exact professionally validated Plan Version and submit it onward; Amina Hassan. |
| Origin / route | Workspace **Review certification**. |
| State / reads | V1 Awaiting AO certification; professional decision complete. |
| Visible outcome | **Certify and submit** or **Return for correction**. |

Frame block:

- Frame name: **PLN-UI-08A__AO-CERTIFICATION**.
- Wide read-only page with right decision rail, matching VB-REVIEW-01; no tabs/stepper. Breadcrumb **Procurement Planning / AO certification / PLN-MOH-2027-001-V1**; H1 **Certify annual procurement plan**; context **Ministry of Health Annual Procurement Plan 2027/28 · Version 1**; chip **Awaiting AO certification**.
- Quiet notice **You are certifying the exact professionally validated Version 1 and submitting it to the configured statutory approving authority. Certification is not final approval.**
- Summary: **Plan Items — 1**; **Certified value under review — KES 80,000,000**; **Departmental sources — 1 of 1 current**; **Finance confirmed — 1 of 1**; **Professional validation — Complete**.
- Section **Professional validation**: **Validated by — Samuel Otieno**; **Validated — 7 December 2026 at 10:00 EAT**; **Outcome — Professionally validated**.
- Section **Plan Items in Version 1** table columns **Plan Item**, **Departmental source**, **Owner**, **Planned value**, **Method**, **Completion**, **Finance**, **Validation**, **Action**. One row: **National digital health infrastructure upgrade** with quiet **PPI-MOH-2027-021**; **DPPS-MOH-DIGITAL-2027-001-V1 · NDS-MOH-2027-0001**; **Digital Health**; **KES 80,000,000**; **Open Tender**; **31 August 2027**; **Confirmed**; **Ready**; quiet **View Plan Item**.
- Section **Annual Plan output preview**: **Procuring Entity — Ministry of Health**; **Financial year — 2027/28**; **Plan reference — PLN-MOH-2027-001**; **Version — 1**; **Total — KES 80,000,000**; **Plan Items — 1**.
- Decision history in order: **Plan root and Draft Version 1 created — Mercy Kilonzo — 1 December 2026 at 09:00 EAT**; **Funding confirmed — MOH Budget Officer — 4 December 2026 at 10:00 EAT**; **Submitted for professional validation — Mercy Kilonzo — 7 December 2026 at 09:30 EAT**; **Professionally validated and submitted to AO — Samuel Otieno — 7 December 2026 at 10:00 EAT**.
- Right rail heading **Accounting Officer certification**; **Version — 1**; **Professional validation — Complete**; **Finance evidence — Complete**; empty multiline **Certification note**, helper **Optional**; secondary **Return for correction**; primary **Certify and submit**.
- Do not render authority approval, publication, editable output, final-approval copy or generic review label.

### 11.4 PLN-UI-08AR__AO-RETURN

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-MODAL-01; accepted PLN-UI-08A__AO-CERTIFICATION frame as the dimmed background |
| Purpose / actor | Capture an actionable AO return reason; Amina Hassan. |
| State / reads | Immutable PLN-MOH-2027-001-V1 AO-certification task. |
| Visible outcome | **Return for correction** represents the AO return. |

Frame block:

- Frame name: **PLN-UI-08AR__AO-RETURN**.
- Modal title **Return Plan Version for correction?**
- Intro **The exact certified-stage snapshot will remain unchanged. No approval or publication will occur.**
- Read-only **Plan Version — PLN-MOH-2027-001-V1**; **Value — KES 80,000,000**; **Stage — Accounting Officer certification**.
- Required multiline **Reason for return**; value **Confirm the accountability evidence for the Budget Line before the Plan is resubmitted for certification.**
- Footer **Cancel**; restrained **Return for correction**.
- Do not render item edit, approval, publication or silent correction.

### 11.5 PLN-UI-08B__STATUTORY-APPROVAL

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-REVIEW-01 |
| Purpose / actor | Approve or return the exact AO-certified version; National-government Plan Approver, `moh.statutory.approver@example.test`. |
| Origin / route | Workspace **Review for approval**. |
| State / reads | V1 Awaiting statutory approval; AO certification complete. |
| Visible outcome | **Approve Annual Procurement Plan** or **Return for correction**. |

Frame block:

- Frame name: **PLN-UI-08B__STATUTORY-APPROVAL**.
- Wide read-only page with right decision rail, matching VB-REVIEW-01; no tabs/stepper. Breadcrumb **Procurement Planning / Statutory approval / PLN-MOH-2027-001-V1**; H1 **Approve annual procurement plan**; context **Ministry of Health Annual Procurement Plan 2027/28 · Version 1**; chip **Awaiting statutory approval**.
- Authority panel at top: **Approval authority — National-government approving authority**; **Assigned account — moh.statutory.approver@example.test**; **Route — National government PE approval route**.
- Notice **Approval records an immutable statutory decision and moves the version to Approved - publication pending. It does not publish or activate the Plan.**
- Summary: **Plan Items — 1**; **Certified value — KES 80,000,000**; **Finance confirmed — 1 of 1**; **Professional validation — Complete**; **AO certification — Complete**.
- Section **Accounting Officer certification**: **Amina Hassan**; **8 December 2026 at 10:00 EAT**; **Outcome — Certified and submitted**.
- Section **Plan Items in Version 1** table columns **Plan Item**, **Departmental source**, **Owner**, **Planned value**, **Method**, **Completion**, **Finance**, **Validation**, **Action**. One row: **National digital health infrastructure upgrade** with quiet **PPI-MOH-2027-021**; **DPPS-MOH-DIGITAL-2027-001-V1 · NDS-MOH-2027-0001**; **Digital Health**; **KES 80,000,000**; **Open Tender**; **31 August 2027**; **Confirmed**; **Ready**; quiet **View Plan Item**.
- Section **Annual Plan output preview**: **Procuring Entity — Ministry of Health**; **Financial year — 2027/28**; **Plan reference — PLN-MOH-2027-001**; **Version — 1**; **Total — KES 80,000,000**; **Plan Items — 1**.
- Decision history in order: **Plan root and Draft Version 1 created — Mercy Kilonzo — 1 December 2026 at 09:00 EAT**; **Funding confirmed — MOH Budget Officer — 4 December 2026 at 10:00 EAT**; **Professionally validated and submitted to AO — Samuel Otieno — 7 December 2026 at 10:00 EAT**; **Certified and submitted for statutory approval — Amina Hassan — 8 December 2026 at 10:00 EAT**.
- Right rail heading **Statutory approval**; **Configured authority — National-government approving authority**; **Version — 1**; **AO certification — Complete**; empty multiline **Approval note**, helper **Optional**; secondary **Return for correction**; primary **Approve Annual Procurement Plan**.
- Do not render content edit, AO redecision, Publish, Active/Requisition status or generic **Review and approve**.

### 11.6 PLN-UI-08BR__STATUTORY-RETURN

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-MODAL-01; accepted PLN-UI-08B__STATUTORY-APPROVAL frame as the dimmed background |
| Purpose / actor | Capture the configured authority's actionable return reason; National-government Plan Approver, `moh.statutory.approver@example.test`. |
| State / reads | Exact AO-certified PLN-MOH-2027-001-V1; KES 80,000,000. |
| Visible outcome | **Return for correction** represents the statutory return. |

Frame block:

- Frame name: **PLN-UI-08BR__STATUTORY-RETURN**.
- Modal title **Return certified Plan Version for correction?**
- Intro **The exact certified Version 1 will remain unchanged. No publication or activation will occur.**
- Read-only **Plan Version — PLN-MOH-2027-001-V1**; **Certified value — KES 80,000,000**; **Authority — National-government approving authority**.
- Required multiline **Reason for return**; value **Clarify the publication-ready Annual Plan output description before resubmission through the same approval route.**
- Footer **Cancel**; restrained **Return for correction**.
- Do not render editable content, approval, publication or routing choice.

### 11.7 PLN-UI-08C__PUBLICATION-PENDING

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-REVIEW-01 focused-task density |
| Purpose / actor | Review and transmit the exact approved sandbox payload; MOH Plan Publisher, `moh.plan.publisher@example.test`. |
| Origin / route | Workspace **Publish Annual Procurement Plan**. |
| State / reads | V1 Approved - publication pending; no attempt yet. |
| Visible outcome | **Publish Annual Procurement Plan** represents one exact-payload attempt. |

Frame block:

- Frame name: **PLN-UI-08C__PUBLICATION-PENDING**.
- Focused main-content task, not a generic review page. Breadcrumb **Procurement Planning / Publication / PLN-MOH-2027-001-V1**; H1 **Publish Annual Procurement Plan**; chips **Approved - publication pending**, **Sandbox**.
- Notice **Publish only the exact approved payload. An authoritative acknowledgement is required before Version 1 becomes Active.**
- Section **Approved Plan Version**: **Ministry of Health Annual Procurement Plan 2027/28** with quiet **PLN-MOH-2027-001**; **Version — 1**; **Approved value — KES 80,000,000**; **Plan Items — 1**; **Approved by — National-government approving authority**; **Approved — 9 December 2026 at 11:00 EAT**.
- Section **Publication destination**: **Destination — KenTender Annual Plan Publication Sandbox**; **Configuration version — MOH-APP-SANDBOX-v1**; **Payload — PLN-MOH-2027-001-V1 · KES 80,000,000 · 1 Plan Item**; **Payload hash — SHA-256 7f2a9c1e4b76…91c4**; **Latest attempt — None**; **Acknowledgement — Not received**.
- Restrained warning **Sandbox evidence only. Production publication remains unavailable while LEG-AUTH-001 and ASMP-003 are open.**
- Secondary **View evidence**; primary **Publish Annual Procurement Plan**.
- Do not render payload editor, destination selector, manual acknowledgement, Active/Requisition status, Tender publication or approval control.

### 11.8 PLN-UI-08C__PUBLICATION-FAILED

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-REVIEW-01 focused-task density |
| Purpose / actor | Retry the exact approved payload after failure; MOH Plan Publisher, `moh.plan.publisher@example.test`. |
| Origin / route | Workspace **Retry publication** or failed task detail. |
| State / reads | V1 Publication failed; same approval/payload; attempt A1 failed. |
| Visible outcome | **Retry publication** represents idempotent retry without new approval. |

Frame block:

- Frame name: **PLN-UI-08C__PUBLICATION-FAILED**.
- Focused main-content task, not a generic review page. Breadcrumb **Procurement Planning / Publication / PLN-MOH-2027-001-V1**; H1 **Publish Annual Procurement Plan**; chips **Publication failed**, **Sandbox**.
- Notice **Retry only the exact approved payload. An authoritative acknowledgement is required before Version 1 becomes Active.**
- Section **Approved Plan Version**: **Ministry of Health Annual Procurement Plan 2027/28 · PLN-MOH-2027-001**; **Version — 1**; **Approved value — KES 80,000,000**; **Plan Items — 1**; **Approved by — National-government approving authority**; **Approved — 9 December 2026 at 11:00 EAT**.
- Publication destination rows: **Latest attempt — PUB-MOH-2027-001-A1**; **Attempted — 10 December 2026 at 14:55 EAT**; **Result — Failed**; **Acknowledgement — Not received**.
- In the same **Publication destination** section, also show **Destination — KenTender Annual Plan Publication Sandbox**; **Configuration version — MOH-APP-SANDBOX-v1**; **Payload — PLN-MOH-2027-001-V1 · KES 80,000,000 · 1 Plan Item**; **Payload hash — SHA-256 7f2a9c1e4b76…91c4**.
- Warning **No authoritative acknowledgement was returned. The approved payload is unchanged and may be retried.**
- Hold note **Sandbox evidence only. Production publication remains unavailable while LEG-AUTH-001 and ASMP-003 are open.**
- Secondary **View evidence**; primary **Retry publication**.
- Do not render a new approval, changed payload, manual success, Active state or second destination.

### 11.9 PLN-UI-08CA__PUBLICATION-ACKNOWLEDGED

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-REVIEW-01 focused-task density |
| Purpose / actor | Show exact authoritative acknowledgement and activation result; MOH Plan Publisher, `moh.plan.publisher@example.test`. |
| Origin / route | Publication result after acknowledged sandbox response. |
| State / reads | ACK-MOH-2027-001-A1 verified; V1 Active. |
| Visible outcome | **View active plan** represents opening PLN-UI-09. |

Frame block:

- Frame name: **PLN-UI-08CA__PUBLICATION-ACKNOWLEDGED**.
- Focused read-only main-content result. Breadcrumb **Procurement Planning / Publication / PLN-MOH-2027-001-V1**; H1 **Publish Annual Procurement Plan**; chips **Acknowledged**, **Version 1 Active**.
- Success notice **The exact approved payload was acknowledged. Version 1 is now the Active Annual Procurement Plan.**
- Read-only result rows: **Publication attempt — PUB-MOH-2027-001-A1**; **Acknowledgement — ACK-MOH-2027-001-A1**; **Destination — KenTender Annual Plan Publication Sandbox**; **Payload hash — SHA-256 7f2a9c1e4b76…91c4**; **Acknowledged — 10 December 2026 at 15:00 EAT**; **Activation — Version 1 Active**.
- Hold note **Sandbox evidence only. Production publication remains unavailable while LEG-AUTH-001 and ASMP-003 are open.**
- Secondary **View evidence**; primary **View active plan**.
- Do not render Retry, Publish again, payload/destination edit, approval control or Tender action.

## 12. Exact Active Plan, downstream, monitoring and evidence frame blocks

### 12.1 PLN-UI-09__ACTIVE-PLAN

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-ACTIVE-01 |
| Purpose / actor | Show the sole Active acknowledged Plan baseline and operational Requisition eligibility; Mercy Kilonzo. |
| Origin / route | Workspace **View approved plan** or publication acknowledgement result. |
| State / reads | Integrated base V1 Active; one item; no Draft successor; no Requisition drawdown. |
| Visible outcome | **View Plan Item**, eligible overflow **Propose removal** and evidence links only. |

Frame block:

- Frame name: **PLN-UI-09__ACTIVE-PLAN**.
- Wide read-only operational detail, not a dashboard/editor.
- Breadcrumb **Procurement Planning / Ministry of Health / 2027/28**; H1 **Ministry of Health Annual Procurement Plan 2027/28**; quiet **PLN-MOH-2027-001**; context **Active Version 1**; supporting line **Approved 9 December 2026 at 11:00 EAT · Published and acknowledged 10 December 2026 at 15:00 EAT**.
- No header primary creation action in this frame because no eligible accepted change source is present.
- Summary: **Active plan value — KES 80,000,000**; **Active Plan Items — 1**; **Finance confirmed — 1 of 1**; **Ready for requisitioning — 1**; **Requisition drawdown — KES 0 of KES 80,000,000**.
- Compact filter row: **Department — All permitted departments**; **Eligibility — All eligibility states**; **Downstream status — All statuses**; read-only **As at — 10 December 2026 at 15:05 EAT**.
- Section **Active Plan Items** table columns **Plan Item**, **Departmental source**, **Owner**, **Active value**, **Finance**, **Requisition eligibility**, **Drawdown**, **Downstream status**, **Action**.
- One row: **National digital health infrastructure upgrade** with quiet **PPI-MOH-2027-021**; **DPPS-MOH-DIGITAL-2027-001-V1 · NDS-MOH-2027-0001**; **Digital Health**; **KES 80,000,000**; **Confirmed**; **Ready for requisitioning**; **KES 0 of KES 80,000,000**; **No Procurement Requisition**; **View Plan Item** plus restrained overflow **Propose removal**.
- Section **Approval and publication evidence**: **Approved by — National-government approving authority**; **Approved — 9 December 2026 at 11:00 EAT**; **Publication attempt — PUB-MOH-2027-001-A1**; **Acknowledgement — ACK-MOH-2027-001-A1**; **Acknowledged — 10 December 2026 at 15:00 EAT**; **Payload hash — SHA-256 7f2a9c1e4b76…91c4**; quiet **View evidence**.
- Version history: **Version 1 — Active — KES 80,000,000 — acknowledged 10 December 2026**.
- Do not render editable baseline, Export, Add when no eligible source, Create Requisition/Tender, Tender take-up, approval or publication decision.

### 12.2 PLN-UI-09__ACTIVE-PLUS-DRAFT-NOTICE

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-ACTIVE-01 |
| Purpose / actor | Keep Active V1 operational while making the open Draft successor visible; Mercy Kilonzo. |
| Origin / route | Active Plan detail while Draft Version 2 adds PPI-MOH-2027-022 to Active Version 1. |
| State / reads | Active V1 KES 80,000,000; Draft V2 KES 120,000,000; added PPI-MOH-2027-022 incomplete. |
| Visible outcome | **View plan update** represents opening the Draft workbench; Active item remains read-only. |

Frame block:

- Frame name: **PLN-UI-09__ACTIVE-PLUS-DRAFT-NOTICE**.
- Breadcrumb **Procurement Planning / Ministry of Health / 2027/28**; H1 **Ministry of Health Annual Procurement Plan 2027/28**; quiet **PLN-MOH-2027-001**; context **Active Version 1**; supporting line **Approved 9 December 2026 at 11:00 EAT · Published and acknowledged 10 December 2026 at 15:00 EAT**; primary header button **View plan update**.
- Active-only summary: **Active plan value — KES 80,000,000**; **Active Plan Items — 1**; **Finance confirmed — 1 of 1**; **Ready for requisitioning — 1**; **Requisition drawdown — KES 0 of KES 80,000,000**.
- Add a distinct but restrained successor notice below header: heading **Draft plan update in progress**; **Draft Version — Version 2**; **Draft value — KES 120,000,000**; **Net change — KES 40,000,000 added**; **Validation — Needs attention**; exact copy **Active Version 1 remains the operational baseline until the successor is approved, published and acknowledged.**
- Compact filter row: **Department — All permitted departments**; **Eligibility — All eligibility states**; **Downstream status — All statuses**; read-only **As at — 10 December 2026 at 15:05 EAT**.
- Section **Active Plan Items** table columns **Plan Item**, **Departmental source**, **Owner**, **Active value**, **Finance**, **Requisition eligibility**, **Drawdown**, **Downstream status**, **Action**. One row: **National digital health infrastructure upgrade** with quiet **PPI-MOH-2027-021**; **DPPS-MOH-DIGITAL-2027-001-V1 · NDS-MOH-2027-0001**; **Digital Health**; **KES 80,000,000**; **Confirmed**; **Ready for requisitioning**; **KES 0 of KES 80,000,000**; **No Procurement Requisition**; **View Plan Item** plus restrained overflow **Propose removal**.
- Section **Approval and publication evidence**: **Approved by — National-government approving authority**; **Approved — 9 December 2026 at 11:00 EAT**; **Publication attempt — PUB-MOH-2027-001-A1**; **Acknowledgement — ACK-MOH-2027-001-A1**; **Acknowledged — 10 December 2026 at 15:00 EAT**; **Payload hash — SHA-256 7f2a9c1e4b76…91c4**; quiet **View evidence**.
- Version history: **Version 1 — Active — KES 80,000,000 — acknowledged 10 December 2026**; keep Draft Version 2 out of the immutable history list while it remains Draft.
- Do not add the Draft item into the Active-items table, blend values, show raw diff or expose Draft editor fields on this page.

### 12.3 PLN-UI-09A__REQUISITION-ELIGIBLE

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-ACTIVE-01 item-detail family |
| Purpose / actor | Show exact active-item lineage and remaining Requisition eligibility; Mercy Kilonzo. |
| Origin / route | Active Plan row **View Plan Item**. |
| State / reads | PPI-MOH-2027-021 Active, funded, unblocked, remaining quantity/value full. |
| Visible outcome | Read-only back/evidence actions; no Requisition creation. |

Frame block:

- Frame name: **PLN-UI-09A__REQUISITION-ELIGIBLE**.
- Breadcrumb **Ministry of Health Annual Procurement Plan 2027/28 / PPI-MOH-2027-021**; H1 **National digital health infrastructure upgrade**; quiet **PPI-MOH-2027-021**; chips **Active**, **Ready for requisitioning**; value **KES 80,000,000**.
- Section **Approved source lineage**: **DPP submission — DPPS-MOH-DIGITAL-2027-001-V1**; **DPP entry — DPPE-MOH-DIGITAL-2027-001**; **Need — NDS-MOH-2027-0001**; **Department — Digital Health**; **Requirement type — Non-consulting services**; **Quantity — 1 programme**; **Required by — 31 August 2027**; **Allocation — PSA-MOH-2027-021-001**; **Allocated value — KES 80,000,000**.
- Section **Funding evidence**: **RSV-MOH-2027-021-001**; **Confirmed — 4 December 2026 at 10:00 EAT**; **Covered amount — KES 80,000,000**.
- Section **Approved planned schedule** with read-only rows: **Invitation or advertisement — 1 May 2027**; **Bid opening — 23 May 2027**; **Evaluation completion — 23 June 2027**; **Tender award approval — 10 July 2027**; **Notification of award — 14 July 2027**; **Contract signing — 1 August 2027**; **Delivery or implementation completion — 31 August 2027**.
- Section **Procurement Requisition eligibility**: **Status — Ready for requisitioning**; **Approved quantity — 1 programme**; **Remaining quantity — 1 programme**; **Approved value — KES 80,000,000**; **Remaining value — KES 80,000,000**; **Blockers — None**; **As at — 10 December 2026 at 15:05 EAT**.
- Section **Procurement Requisitions**: exact empty copy **No Procurement Requisition has drawn down this Plan Item.**
- Quiet **Back to active plan**; **View evidence**.
- Do not render Create/Authorise Requisition, Create Tender, editable planned dates, source/funding edit or removal action in this detail frame.

### 12.4 PLN-UI-09A__PARTIAL-DRAWDOWN

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-ACTIVE-01 item-detail family |
| Purpose / actor | Show authoritative partial Requisition drawdown and remaining eligibility; Mercy Kilonzo, Procurement Planner / Consolidator. |
| Origin / route | Active Plan row for isolated PPI-MOH-2027-032. |
| State / reads | Active laptop item; 300 each / KES 72,000,000; PRQ-MOH-2027-001 consumes 120 each / KES 28,800,000. |
| Visible outcome | **View Procurement Requisition** represents authorised downstream detail. |

Frame block:

- Frame name: **PLN-UI-09A__PARTIAL-DRAWDOWN**.
- Breadcrumb **Ministry of Health Annual Procurement Plan 2027/28 / PPI-MOH-2027-032**; H1 **Clinical deployment laptops for digital health rollout**; quiet **PPI-MOH-2027-032**; chips **Active**, **Partially drawn**, **Ready for requisitioning**; value **KES 72,000,000**.
- Section **Approved source lineage**: **Need — NDS-MOH-2027-0004**; **Department — Digital Health**; **Requirement type — Goods**; **Approved quantity — 300 each**; **Required by — 31 December 2027**; **Allocation — PSA-MOH-2027-032-001**; **Funding — Digital health infrastructure programme**.
- Eligibility: **Approved quantity — 300 each**; **Drawn quantity — 120 each**; **Remaining quantity — 180 each**; **Approved value — KES 72,000,000**; **Drawn value — KES 28,800,000**; **Remaining value — KES 43,200,000**; **Blockers — None**; As-at **15 January 2027 at 12:00 EAT**.
- Requisition row: **PRQ-MOH-2027-001**; **Authorised**; **120 each**; **KES 28,800,000**; **15 January 2027 at 11:30 EAT**; action **View Procurement Requisition**.
- Do not render overdraw, a new Requisition button, Tender creation, editable drawdown or source reallocation.

### 12.5 PLN-UI-09A__FULLY-DRAWN-BLOCKED

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-ACTIVE-01 item-detail family |
| Purpose / actor | Show that a fully drawn Active item has no remaining Requisition eligibility; Mercy Kilonzo, Procurement Planner / Consolidator. |
| Origin / route | Active Plan row after full authoritative drawdown. |
| State / reads | PPI-MOH-2027-032; PRQ-MOH-2027-001 consumes 300 each / KES 72,000,000. |
| Visible outcome | Existing Requisition detail only. |

Frame block:

- Frame name: **PLN-UI-09A__FULLY-DRAWN-BLOCKED**.
- Breadcrumb **Ministry of Health Annual Procurement Plan 2027/28 / PPI-MOH-2027-032**; H1 **Clinical deployment laptops for digital health rollout**; quiet **PPI-MOH-2027-032**; chips **Active**, **Fully drawn**, **Not eligible for another Requisition**; value **KES 72,000,000**.
- Section **Approved source lineage**: **Need — NDS-MOH-2027-0004**; **Department — Digital Health**; **Requirement type — Goods**; **Approved quantity — 300 each**; **Required by — 31 December 2027**; **Allocation — PSA-MOH-2027-032-001**; **Funding — Digital health infrastructure programme**.
- Section **Procurement Requisition eligibility** as at **15 January 2027 at 12:00 EAT**.
- Eligibility values: **Approved quantity — 300 each**; **Drawn quantity — 300 each**; **Remaining quantity — 0 each**; **Approved value — KES 72,000,000**; **Drawn value — KES 72,000,000**; **Remaining value — KES 0**; **Blocker — Fully drawn**.
- Section **Procurement Requisitions** has one row: **PRQ-MOH-2027-001**; **Authorised**; **300 each**; **KES 72,000,000**; **15 January 2027 at 11:30 EAT**; action **View Procurement Requisition**.
- Warning **This Plan Item has no remaining quantity or value available for another Procurement Requisition.**
- Do not render disabled Create Requisition, override, negative remaining amount or direct Tender action.

### 12.6 PLN-UI-09M__MONITORING-ENTRY-HISTORY

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-ACTIVE-01 |
| Purpose / actor | Append actual milestone evidence and show correction history without changing the approved baseline; signed-in actor fixture **MOH Monitoring Officer**. |
| Origin / route | Active item **Monitoring** detail. |
| State / reads | PPI-MOH-2027-021 Active; one corrected actual exists; next actual is being recorded. |
| Visible outcome | **Record actual milestone** represents append-only monitoring evidence. |

Frame block:

- Frame name: **PLN-UI-09M__MONITORING-ENTRY-HISTORY**.
- Breadcrumb **Ministry of Health Annual Procurement Plan 2027/28 / PPI-MOH-2027-021 / Monitoring**; H1 **Plan Item monitoring**; **National digital health infrastructure upgrade** with quiet **PPI-MOH-2027-021**; chips **Active**, **Monitoring**.
- Summary: **Approved value — KES 80,000,000**; **Current planned milestone — Bid opening**; **Planned date — 23 May 2027**; **Latest actual status — Invitation completed**.
- Two-column main region. Left panel **Record actual milestone**: required select **Milestone — Bid opening** with options only **Invitation or advertisement; Bid opening; Evaluation completion; Tender award approval; Notification of award; Contract signing; Delivery or implementation completion**; read-only **Planned date — 23 May 2027**; required date **Actual date — 24 May 2027**; required multiline **Evidence note** value **Bid opening completed and confirmed by the downstream procurement record.**; read-only **Evidence source — Tender Preparation projection**; primary **Record actual milestone**.
- Right/lower section **Monitoring history** table columns **Milestone**, **Planned**, **Actual**, **Variance**, **Status**, **Evidence**, **Recorded**.
- Exact current row: **Invitation or advertisement**; **1 May 2027**; **3 May 2027**; **2 days late**; **Corrected**; **TND-MOH-2027-008 downstream event**; **6 May 2027**.
- Quiet correction chain below row: **Original entry: 4 May 2027 · Replaced by corrected actual date 3 May 2027 · Original evidence retained.**
- Do not render planned-date edit, delete history, overwrite, downstream-record edit, performance score or financial expenditure entry.

### 12.7 PLN-UI-EVD-01__PLAN-EVIDENCE

| Contract item | Exact value |
| --- | --- |
| Visual reference | VB-EVD-01 |
| Purpose / actor | Present lawful immutable lifecycle evidence for Active V1; Peter Ouma, Internal Auditor. |
| Origin / route | Any lawful **View evidence** action for PLN-MOH-2027-001-V1. |
| State / reads | Scope-authorised immutable DPP, Finance, professional, AO, approval, publication and audit references. |
| Visible outcome | Read-only evidence navigation only. |

Frame block:

- Frame name: **PLN-UI-EVD-01__PLAN-EVIDENCE**.
- Breadcrumb **Procurement Planning / Evidence / PLN-MOH-2027-001-V1**; H1 **Annual Plan evidence**; description **Review immutable evidence for the exact Active Plan Version.**; chips **Active Version 1**, **Read only**.
- Identity summary: **Plan — Ministry of Health Annual Procurement Plan 2027/28** with quiet **PLN-MOH-2027-001**; **Version — 1**; **Procuring Entity — Ministry of Health**; **Financial year — 2027/28**; **Active value — KES 80,000,000**; **Plan Items — 1**; **Payload hash — SHA-256 7f2a9c1e4b76…91c4**.
- Use an ordered vertical evidence timeline, not a dashboard.
- Exact entries: **Departmental submission — DPPS-MOH-DIGITAL-2027-001-V1 — Peter Kimani — 25 November 2026 at 10:00 EAT — Submitted**; **Procurement validation — DPPV-MOH-DIGITAL-2027-001-V1 — Mercy Kilonzo — 27 November 2026 at 14:00 EAT — Accepted for consolidation**; **Plan formation — PPI-MOH-2027-021 · PSA-MOH-2027-021-001 — Mercy Kilonzo — 1 December 2026 at 09:00 EAT — Formed in Draft Version 1**; **Finance confirmation — RSV-MOH-2027-021-001 — MOH Budget Officer — 4 December 2026 at 10:00 EAT — KES 80,000,000 confirmed**; **Professional validation — PLN-MOH-2027-001-V1 — Samuel Otieno — 7 December 2026 at 10:00 EAT — Professionally validated**; **AO certification — PLN-MOH-2027-001-V1 — Amina Hassan — 8 December 2026 at 10:00 EAT — Certified and submitted**; **Statutory approval — PLN-MOH-2027-001-V1 — National-government approving authority — 9 December 2026 at 11:00 EAT — Approved - publication pending**; **Publication attempt — PUB-MOH-2027-001-A1 — MOH Plan Publisher — 10 December 2026 at 14:55 EAT — Sent to sandbox**; **Acknowledgement and activation — ACK-MOH-2027-001-A1 — System — 10 December 2026 at 15:00 EAT — Version 1 Active**.
- Each of the nine entries shows decision type, exact canonical record/reference where one exists, actor, timestamp, outcome and a quiet secure **View record** link for this illustrated authorised auditor.
- Footer quiet **Back to active plan**.
- Do not render edit, repeat decision, raw authorization payload, sensitive cross-tenant fact, impersonation, export or administrator business action.

## 13. Visible action and cross-frame outcome map

This map states the business outcome represented by each visible label. Stitch displays the label only; the Implementation Pack owns routing, authorization, validation, persistence and state change.

| Visible label | Origin frame(s) | Business outcome represented | Required next static frame after a successful implementation command |
| --- | --- | --- | --- |
| Begin consolidation | PLN-UI-01A, PLN-UI-02 | Create/reuse one Plan root and Draft V1 from eligible accepted sources | PLN-UI-03 or populated PLN-UI-05 |
| Submit / Resubmit departmental plan | P3-UI-DPP-02/02A/05B | Immutable HoD-certified submission with predecessor when resubmitting | P3-UI-DPP-04 |
| Return to department | P3-UI-DPP-03A/B/C | Immutable structured return; submitted evidence unchanged | P3-UI-DPP-05A |
| Accept for consolidation | P3-UI-DPP-03B/D | Terminal DPP validation and current eligible projection | P3-UI-DPP-06 |
| Reopen for source correction | P3-UI-DPP-06A | Preserve accepted evidence and return unconsumed stale source for correction | P3-UI-DPP-05A |
| Requirement type selection | P3-UI-DPP-03A | Persist only the governed DPP-entry classification; do not change the Need or submission snapshot | P3-UI-DPP-03B when the one classification completes all checks; otherwise refreshed 03A |
| Open Departmental Need | P3-UI-DPP-05A/09R | Open the authorised Need record in Departmental Needs; no DPP mutation | Departmental Needs-owned detail, outside this contract |
| View accepted Need / View changed source | P3 DPP and Plan Item frames | Open the exact authorised Need/version read-only; no Planning mutation | Departmental Needs-owned neutral detail, outside this contract |
| View DPP submission / View submission V1/V2 | DPP and Plan Item frames | Open the named immutable DPP submission evidence | Applicable P3 read-only submission frame |
| Add accepted departmental requirements | PLN-UI-03/05 | Open source-selection task without mutation | PLN-UI-04 variant |
| Create Plan Item(s) | PLN-UI-04 variants | Atomically form exact item/allocation/hold result | One item → PLN-UI-06; multiple separate → PLN-UI-05 |
| Complete item / Edit Plan Item | PLN-UI-05 variants | Open the exact editable Draft Plan Item; no mutation on open | PLN-UI-06 applicable item variant |
| View Plan Item | Workspace/workbench/governance/Active frames | Open exact authorised item detail without mutation | Draft editable → PLN-UI-06; Finance pending for planner → PLN-UI-07B; Active → PLN-UI-09A |
| Save draft | PLN-UI-05/06 | Persist only allow-listed Draft fields and recalculate readiness | Same workbench/editor state as returned by implementation |
| Request Finance confirmation | PLN-UI-06 | Atomic save/revalidation and one protected Finance task | Planner sees PLN-UI-07B/05 waiting; Budget Officer sees PLN-UI-07/07A |
| Confirm funding | PLN-UI-07 | Full all-source reservations and one immutable Finance decision | Ready PLN-UI-05 for planner; task leaves Finance queue |
| Return to planner | PLN-UI-07/07A-2/08/08R | Named Finance or professional return with required reason | PLN-UI-06 returned or PLN-UI-05 returned |
| Return for correction | PLN-UI-08A/08AR/08B/08BR | Named AO or statutory return; immutable submitted version preserved | Governed returned Draft work in PLN-UI-05; no inline correction |
| Open Budget & Funding | PLN-UI-07/07A-1 | Navigate to the authorised Budget Line context without changing the Finance task | Budget & Funding-owned detail, outside this contract |
| Submit for professional validation | Ready PLN-UI-05 | Immutable Plan Version and protected professional task | Planner workspace waiting; Head of Procurement Function PLN-UI-08 |
| Validate and submit to Accounting Officer | PLN-UI-08 | Immutable professional decision and AO task | PLN-UI-08A for AO; exact waiting workspace for others |
| Certify and submit | PLN-UI-08A | Immutable AO certification and configured authority task | PLN-UI-08B for authority |
| Approve Annual Procurement Plan | PLN-UI-08B | Immutable statutory approval; publication pending | PLN-UI-08C / workspace publication task |
| Publish / Retry Annual Procurement Plan | PLN-UI-08C | Exact approved-payload attempt; acknowledgement activates | Failed frame or PLN-UI-08CA |
| Add removal to plan update | PLN-UI-05A Active variant | One successor proposal; Active item unchanged | PLN-UI-05 successor |
| Propose removal | PLN-UI-09 Active row | Open the whole-item Active removal confirmation without mutation | PLN-UI-05A__ACTIVE-ITEM-REMOVAL |
| Remove from draft | PLN-UI-05A Draft variants | Whole-item Draft exclusion and governed Draft-effect release | PLN-UI-03 or PLN-UI-05 |
| Cancel plan update | PLN-UI-05B | Cancel no-effective-change successor; Active predecessor unchanged | PLN-UI-09 / workspace Active state |
| View approved plan / View active plan | Workspace, workbench and publication-result frames | Open the exact Active acknowledged version; no mutation | PLN-UI-09 applicable Active frame |
| View plan update | Workspace and Active-detail frames | Open the exact current Draft successor; no mutation | PLN-UI-03 or applicable PLN-UI-05 variant |
| View evidence / View record | Any admitted evidence label | Open scope-authorised immutable evidence only; never elevate authorization | PLN-UI-EVD-01 or the named read-only evidence record |
| View Procurement Requisition | PLN-UI-09A drawn variants | Read authorised downstream Requisition detail | Requisitions-owned neutral detail, not specified by this contract |
| Record actual milestone | PLN-UI-09M | Append monitoring evidence/correction link | Refreshed PLN-UI-09M history |

**Cancel**, **Close**, **Back to planning workspace**, **Back to Procurement Planning**, **Back to plan update**, **Back to active plan**, **Keep item** and **Keep update** close or return to the exact origin state without mutation. Search, filter, FY/context view selection, row selection and opening any surface, drawer or overlay are mutation-free and shall not silently persist a business decision.

## 14. Explicitly outside Stitch

Do not ask Stitch to implement or simulate:

- PE/FY/department/funding scope or assignment/delegation resolution;
- task authorization, route protection or non-disclosure;
- Need/DPP event projection, source-current checks or reconciliation;
- readiness, blocker, method, schedule, funding, shortfall or remaining-value calculations;
- immutable snapshots, hashes, state transitions, idempotency, concurrency or transactions;
- Budget reservations, reversals, ledger changes or task iterations;
- professional, AO, authority or publication commands;
- publication serialization, transmission, retry, acknowledgement or activation;
- Requisition eligibility, Requisition creation or drawdown recording;
- monitoring persistence, audit, notifications, loading, service errors or automated tests; or
- fallback behavior for a missing screenshot, selector, fixture or product rule.

Application-wide loading, non-disclosing unauthorized access and unexpected-service-failure patterns are not redesigned here. Stitch must not create a Planning-specific spinner, permission error, technical error page or retry flow unless a later approved canonical version admits an exact frame.

## 15. Generation, review and acceptance procedure

### 15.1 One-frame generation sequence

For each frame in order:

1. verify the canonical and functional fingerprints/versions;
2. attach the named VB reference and its selector inventory;
3. assemble the prompt in the exact section 5.1 order;
4. generate exactly one frame;
5. compare the output against the reference and frame specification;
6. record Keep/Correct/Retire evidence for every reused component;
7. reject and regenerate the same frame if any unlisted visible element, missing value or wrong semantic appears; and
8. accept the frame before generating the next frame in that visual family.

Do not batch several materially different states into one prompt or ask Stitch to produce a flow, storyboard or inferred variants.

Before generation, save the final assembled prompt in the frame evidence record and run a literal-text check. It must contain no maintenance directive matching **Reuse [section/frame]**, **same as [section/frame]**, **as above**, **from section**, **standard table**, **standard panel** or an unresolved numbered-section/frame reference. Required business copy such as **creates or reuses the one Annual Plan root** is not a maintenance directive. A failure blocks the Stitch call.

### 15.2 Per-frame evidence record

| Evidence field | Required value |
| --- | --- |
| Frame name | Exact frame name from this contract |
| Product screen ID | Exact canonical screen ID |
| Prompt source | PLN-STC-001 v0.1 plus exact frame subsection |
| Assembled prompt | Immutable copy of the exact standalone text sent to Stitch; applicable DPP family block included; no unresolved maintenance directive |
| Canonical fingerprint | Exact fingerprint from section 1 |
| Visual reference | VB alias plus attached screenshot identifier |
| Implemented reference | Route/component selectors where they already exist |
| Stitch output | Project/frame identifier and immutable exported screenshot |
| Desktop comparison | 1440 px screenshot comparison and reviewer result |
| Visible contract result | Every required region/value/control/row present; no extra element |
| Reuse result | Keep/Correct/Retire result for each prior component |
| Accessibility review | H1, labels, table headers, focus affordance, status text/contrast |
| Reviewer decision | Accepted or Rejected with exact defect list |

### 15.3 Frame acceptance checklist

Accept a frame only when all answers are **Yes**:

1. Does it show exactly one actor, context and point-in-time state?
2. Is the existing shell preserved and the correct VB family used?
3. Are all regions in the stated order with exact labels, values and controls?
4. Are business titles primary and references visually secondary?
5. Are source-owned values readable text rather than disabled inputs?
6. Is the one primary action correct for this actor/state, or absent where none exists?
7. Are inaccessible actor controls omitted rather than disabled?
8. Are professional validation, AO certification, statutory approval and publication visibly distinct?
9. Is **Approved - publication pending** distinct from **Active**?
10. Is Requisition eligibility the immediate downstream Planning concept, with no direct Tender command?
11. Are unsupported Multi-year, Lots expected and non-admitted method choices absent?
12. Are all rows, amounts, counts, dates, statuses and arithmetic exact?
13. Are returned, stale, shortfall, waiting, failed and acknowledged states generated only in their named frames?
14. Is there no decorative KPI grid, generic questionnaire, score, activity feed or technical schema content?
15. Does the frame contain no unlisted text, control, icon, row, metric, state or workflow stage?

### 15.4 Cross-frame reconciliation checks

- DPP V1 source, amount, submission, classification and dates reconcile across every P3 frame.
- Begin consolidation, empty Draft, source selection, Plan Item, Finance and governance frames all reconcile to the exact selected reset boundary.
- The Active V1 value is KES 80,000,000 and remains operational throughout every Draft successor frame.
- STC-FIX-SUCCESSOR always reconciles KES 80,000,000 Active + KES 40,000,000 addition = KES 120,000,000 Draft.
- STC-FIX-COMBINE always reconciles 200 + 300 = 500 each and KES 48,000,000 + KES 72,000,000 = KES 120,000,000.
- Finance sufficient/shortfall arithmetic reconciles exactly and no shortfall frame exposes Confirm funding.
- Professional validation, AO certification, statutory approval, publication pending/failure and acknowledgement preserve the same immutable Plan Version and payload.
- Active Plan and item detail show the exact same publication acknowledgement, item, allocation, reservation and remaining eligibility.
- Partial/full drawdown frames reconcile quantity and value and never show a negative or overdrawn remainder.

## 16. Screen and frame coverage matrix

| Canonical screen ID | Required frame(s) in this contract | Coverage status |
| --- | --- | --- |
| PLN-UI-00 | PLN-UI-00__NO-CONTEXT | Complete |
| PLN-UI-01A | PLN-UI-01A__NO-PLAN | Complete |
| PLN-UI-01B | PLN-UI-01B__INITIAL-DRAFT | Complete |
| PLN-UI-01C | PLN-UI-01C__ACTIVE-PLUS-DRAFT | Complete |
| PLN-UI-01D | PLN-UI-01D__FINANCE-ACTOR; PLN-UI-01D__PLANNER-WAITING | Complete |
| PLN-UI-01E | PLN-UI-01E__PROFESSIONAL-ACTOR; PLN-UI-01E__AO-ACTOR | Complete |
| PLN-UI-01F | PLN-UI-01F__APPROVER-ACTOR; PUBLICATION-PENDING; PUBLICATION-FAILED | Complete |
| PLN-UI-01G | PLN-UI-01G__ACTIVE-NO-WORK | Complete |
| PLN-UI-SUP-01 | PLN-UI-SUP-01__READ-ONLY | Complete |
| P3-UI-DPP-01 | DRAFT-PREPARER | Complete |
| P3-UI-DPP-02 / 02A | DRAFT-HOD-READY; SUBMIT-CONFIRMATION | Complete |
| P3-UI-DPP-03A / 03B / 03C / 03D | CLASSIFICATION-MISSING; VALIDATION-READY; RETURN; ACCEPT | Complete |
| P3-UI-DPP-04 | SUBMITTED-DEPARTMENT-VIEW | Complete |
| P3-UI-DPP-05A / 05B | RETURNED-CORRECTION-OUTSTANDING; RETURNED-CORRECTED | Complete |
| P3-UI-DPP-06 / 06A / 06B | ACCEPTED-CURRENT; STALE-PRE-CONSUMPTION; CHANGED-POST-CONSUMPTION | Complete |
| P3-UI-DPP-07 | WITHDRAWN | Complete |
| P3-UI-DPP-09 family | AMENDMENT-DRAFT; SUBMITTED; RETURNED; ACCEPTED | Complete |
| PLN-UI-02 | BEGIN-CONSOLIDATION | Complete |
| PLN-UI-03 | INITIAL-DRAFT-ZERO-ITEM | Complete |
| PLN-UI-04 | ONE-SOURCE; MULTI-COMBINED; MULTI-SEPARATE | Complete |
| PLN-UI-05 | INITIAL-DRAFT-INCOMPLETE; SUCCESSOR-INCOMPLETE; FINANCE-WAITING; READY; RETURNED; FINANCE-STALE; REMOVAL-ONLY-READY | Complete |
| PLN-UI-05A | DRAFT-ITEM; ACTIVE-ITEM; COMBINED-ITEM removal | Complete |
| PLN-UI-05B | CANCEL-NO-EFFECTIVE-CHANGE | Complete |
| PLN-UI-06 | SINGLE-SOURCE-COMPLETE; FINANCE-RETURNED; COMBINED-SOURCE-COMPLETE | Complete |
| PLN-UI-07 | SUFFICIENT-SINGLE-SOURCE; SUFFICIENT-COMBINED-SOURCE | Complete |
| PLN-UI-07A-1 / 07A-2 | INSUFFICIENT; RETURN-CONFIRMATION | Complete |
| PLN-UI-07B | PLANNER-NEUTRAL-WAITING | Complete |
| PLN-UI-08 / 08R | PROFESSIONAL-VALIDATION; PROFESSIONAL-RETURN | Complete |
| PLN-UI-08A / 08AR | AO-CERTIFICATION; AO-RETURN | Complete |
| PLN-UI-08B / 08BR | STATUTORY-APPROVAL; STATUTORY-RETURN | Complete |
| PLN-UI-08C / 08CA | PUBLICATION-PENDING; PUBLICATION-FAILED; PUBLICATION-ACKNOWLEDGED | Complete |
| PLN-UI-09 | ACTIVE-PLAN; ACTIVE-PLUS-DRAFT-NOTICE | Complete |
| PLN-UI-09A | REQUISITION-ELIGIBLE; PARTIAL-DRAWDOWN; FULLY-DRAWN-BLOCKED | Complete |
| PLN-UI-09M | MONITORING-ENTRY-HISTORY | Complete |
| PLN-UI-EVD-01 | PLAN-EVIDENCE | Complete |

PLN-UI-10 is deliberately absent and retired. It must not be generated, routed, aliased or retained as a hidden screen.

## 17. Approval gate and next derivative

| Decision item | Value |
| --- | --- |
| Product-owner decision | Approved |
| Decision date | 21 August 2026 |
| Approved contract version | 0.1 |
| Canonical fingerprint verified | Yes — `sha256:2e8e8790309b4d738ab80934f609111753f94766aab8e4bf2d3313146289e879` |
| Visual-reference manifest STC-VIS-001 | Required before Stitch generation; not product approval |
| Approved Stitch output version | Pending generation and frame-by-frame acceptance |
| Conditions or exceptions | None |

PLN-STC-001 v0.1 is approved as the exact prompt contract and UI reuse decision record. This approval does not approve any generated Stitch frame until the frame-level evidence in section 15 passes. After reference-manifest completion, frames are generated in order. The next documentation derivative is the Seed Data Contract, which must instantiate the exact presentation fixtures and canonical scenario boundaries without repairing them.
