# PLN-CHG-001 — Clean Procurement Planning

| Control | Value |
|---|---|
| Document ID | PLN-CHG-001 |
| Version | 1.9 |
| Date | 3 September 2026 |
| Status | **Approved** |
| Approved on | 3 September 2026 |
| Change type | Complete consolidated successor to v1.8. Implements LAW-REG-001 v1.0, which maps the Act and Regulations read in full — including the Second, Third and Thirteenth Schedules — to required changes. Earlier versions of this document. **Corrects v1.7's optional statutory approval, which was wrong in law.** Expands the plan to the contents required by regulation 41, adds asset disposal planning, admits the procurement methods the threshold matrix requires, and moves the DPP window to the Fiscal Year flag pattern. |
| Module | Procurement Planning |
| Standards | Governed by KT-STD-001 v1.1. Sections not restated here are inherited from it. |
| Implementation posture | Correct the existing module in place; reuse the proven Planning UI and Claude Design → Vue 3 → Frappe Desk pattern |

**Controlling decision:** Procurement Planning turns departmental requirements into one funded, governed Annual Procurement Plan with the fewest necessary user actions. A **Departmental Procurement Plan is a departmental submission into** the Annual Procurement Plan, not a plan that competes with it: PPADA 2015 vests one annual procurement plan in the accounting officer, while the user department originates requirements and the procurement function consolidates them. A Departmental Procurement Plan may contain accepted Departmental Needs, direct departmental requirements, or both. Departmental Needs supports consultation but is not a prerequisite for planning. When the first DPP is accepted, the system automatically creates the initial Draft Annual Procurement Plan and places the accepted entries in its unallocated-source queue. The Planner begins with the meaningful work of forming Plan Items; there is no separate **Begin consolidation** gate. Planning owns requirement classification, the Procurement Budget Line and indicative amount on each departmental-plan entry, formation of Plan Items, selection of one Strategic Objective per Plan Item, one plan-level funding confirmation, Accounting Officer adoption, statutory approval where a route is configured, system publication and the approved lineage exposed to Procurement Requisitions.

## 1. Governing decision

This complete document is the single implementation authority for Procurement Planning. It consolidates approved v1.4 with the one-site-one-PE, role-bound assignment, site-local Organisation Unit and ERPNext Fiscal Year rules in AUTH-ADR-001 v1.6, and replaces the Planning documents listed in section 18 wherever they conflict with it.

The existing application is corrected in place. Proven page structure, components, visual tokens and working Planning interactions are reused where they conform. Removed concepts are deleted rather than renamed, aliased, dual-read or retained behind feature flags.

Completion requires one coherent result across schema, services, permissions, screens, fixtures and tests. A field, action, object, service, queue or screen not defined here is outside the module.

### 1.1 Conflict and disposition register

| Earlier item | Disposition in v1.4 |
|---|---|
| Every DPP entry and Plan Item must originate from an accepted Need | Correct. A DPP entry originates from either an `Accepted Departmental Need` or a `Direct departmental requirement`. |
| Accepted Need carries Strategy, requirement type, Procurement Budget Line, funding source, currency and amount into Planning | Remove. The Need supplies title, description, expected operational result, quantity, unit and required-by date only. Planning adds the Procurement Budget Line and indicative amount; the Procurement Planner classifies the entry; the Planner selects the Strategic Objective on the Plan Item. |
| HoD must create a Need before planning a known requirement | Remove. The authorised departmental plan preparer may create a direct requirement inside the Draft DPP. No synthetic Need or bypass reason is created. |
| Need-origin quantity can be partially included or changed in Planning | Remove. A current accepted Need is represented exactly once and at its full accepted quantity in the DPP. |
| Direct and Need-origin entries use different approval routes | Remove. Both are certified in the same DPP and receive the same Procurement validation. |
| Budget specification belongs at Need creation | Remove. Procurement Budget Line and indicative amount are required on the DPP entry before HoD submission. |
| Strategic Objective belongs on the Need or DPP entry | Remove. Exactly one Active Strategic Objective is selected on each Plan Item. |
| `Value Commitment` on a Plan Item | Remove. Strategic Objectives and Outcomes already express the intended strategic contribution. |
| Separate recommended method and planned method | Replace with one governed `Procurement method` on the Plan Item. |
| Editable `Single year` and `No lots expected` fields when those are the only admitted values | Remove. Fixed MVP scope is not collected as user data. |
| Generic source reference, authority reference, evidence, note, contact or attachment fields | Remove unless a named decision in this document explicitly consumes the value. |
| AO recipient captured on a DPP submission | Remove. A DPP submission routes to the scoped DPP validation queue. The Accounting Officer acts later on the consolidated Annual Plan. |
| Separate **Begin consolidation** action and `Not started` Annual Plan state after a DPP is accepted | Remove. Acceptance of the first DPP creates/reuses Draft Version 1 automatically and projects its entries into the unallocated-source queue. |
| Mandatory wait for every department or a nil-plan declaration before Plan Item work | Remove. Accepted DPP entries may be formed incrementally. Later accepted entries flow into the same open Draft or, after activation, become pending inputs for a successor. |
| DPP readiness score or percentage | Remove. Readiness is an exact blocker list. |
| Custom System Administrator Planning workspace | Remove. Support and audit use authorised framework records and logs; they receive no Planning business action. |
| Planning-owned actual milestone entry and Monitoring Officer role | Remove from MVP-1. Tendering, Requisitions and Contract Management own actual operational events. Planning may display their read-only projections later. |
| 71 separately specified Stitch frames | Replace with the smaller Claude Design contract in section 11. State variants are functional requirements unless a visually distinct artboard is explicitly required. |
| Stitch/Tailwind markup imported into Frappe | Replace with Claude Design as visual evidence, then Vue 3 SFCs mounted in Frappe Desk. No design-runtime file is shipped. |
| Breadcrumb drawn inside the artboard | Remove. Breadcrumb is fixture data outside the artboard and is rendered by the existing Frappe header. |
| Plan approval page shows only a summary | Correct. Every review, certification and approval task shows the complete submitted Plan details before its decision controls. |
| Separate professional-review stage before the Accounting Officer | Remove. It creates no distinct statutory decision in this Planning chain. |
| Head of Procurement Function approves the Annual Plan | Remove. The Head of Procurement Function is not an Annual Plan approval stage. |
| Publication Operator as a business role | Remove. Publication is an idempotent system action after statutory approval. |
| Separate departmental preparer and validator roles | Replace with Departmental Author and Procurement Planner respectively. |
| Separate Frappe Role, User Permission, User Scope Assignment or capability records as authority | Remove. Use one role-bound User Responsibility Assignment and the AUTH-ADR-001 v1.6 resolver. |
| Publication acknowledges a Tender opportunity | Remove. Annual Plan publication does not create or advertise a Tender. |
| Legacy compatibility and migrated Demand records | Prohibited. This remains a clean Planning domain. |
| Draft Plan Item formation is irreversible | Correct. A Planner may dissolve an item while its Plan Version is mutable; sources return to the unallocated list. Submitted evidence is never dissolved. |
| Reservation release left to implementation inference | Remove. Planning must call the Budget-owned release contract on the exact lifecycle triggers defined in sections 5 and 7. |
| Generic maker-checker error without an action matrix | Remove. Section 6.1 defines the incompatible actions on one DPP submission or Plan Version. |
| Returned Annual Plan resumes at an inferred stage | Remove. A correction is a copied Draft with a new submitted snapshot; every resubmission restarts at Accounting Officer adoption. Finance repeats only under the objective rules in section 5.2. |
| Accepted DPP successor silently rewrites an allocated source | Prohibited. The affected Draft item is marked **Source correction required** and must be dissolved and re-formed. Submitted and Active evidence is never rewritten. |
| Withdrawn initial DPP permanently closes the root | Correct. It may be reopened as the next Draft Version only while the initial submission window remains Open. |
| Accepted Needs disappear when their department misses DPP submission | Remove. Planning shows **Not included — DPP submission window closed** while Departmental Needs retains the accepted records; this is visibility, not a late-submission bypass. |
| Combined sources need not share currency | Correct. Sources must resolve to the same Budget and currency. Cross-currency Planning is outside MVP-1. |
| One Plan Item can be consumed by only one Requisition | Remove. Requisitions may make sequential partial drawdowns while balances remain, subject to its one-open-Requisition rule. |
| Browser-stored PE/FY choice is the operating authority | Prohibited. Server-side role-bound User Responsibility Assignment defines organisational authority. The Planning Financial Year is a visible, changeable module filter and never a permanent browser lock. |
| Financial Year or PE/FY Context assigned to a user | Prohibited. Durable authority is the role-bound site-wide or Organisation Unit assignment; the applicable Fiscal Year derives from the ERPNext catalogue, operation windows and record state. |
| Separate sidebar links for Finance, validation or approval queues | Prohibited. Procurement Planning has one workspace entry. Actionable work arrives through that workspace, the shared **My Work** surface and notifications; task routes are deep links, not menu items. |

New in v1.5:

| Earlier item | Disposition in v1.5 |
|---|---|
| `pe_fy_context_id` on `DPPSubmissionWindow`, `DepartmentalProcurementPlan` and `AnnualProcurementPlan` | **Replace with `fiscal_year`**, referencing the ERPNext `Fiscal Year` governed by CFG-CHG-002 v0.6 §4.2. One site is one Procuring Entity, and `PEFiscalYearContext` no longer exists. |
| Uniqueness keyed on PE/FY | Rekey to Fiscal Year. One DPP root per Fiscal Year and Organisation Unit; one Annual Plan per Fiscal Year. |
| Business responsibilities scoped to a Procuring Entity | **Site-wide.** Procurement Planner, Accounting Officer, the statutory approver and the Planning Auditor are registered with `scope_type = Site-wide` under AUTH-ADR-001 v1.6 §4.4. Departmental Author and Head of User Department remain Organisation Unit scoped. |
| `Budget Officer` as the Finance confirmation actor | **Rename to `Finance Confirmation Officer`.** BUD-CHG-001 v1.3 §7 owns the role and distinguishes it from Budget Officer, which authors budget versions and holds no Planning task. |
| Procuring Entity selector in the Planning page header and the PLN-DES-01 context row | **Remove.** There is no PE to select. The Financial Year select survives as a local view filter that gates nothing. |
| `Procurement Budget Line` as the Budget & Funding record name | Rename to `Procurement Budget Line` per BUD-CHG-001 v1.3 §1.1. Identifiers are unchanged. |
| `ListEligibleBudgetLines` and `ListEligibleStrategicObjectives` taking a Procuring Entity argument | Remove the argument. Budget lines resolve by Fiscal Year and source Organisation Unit; Strategic Objectives resolve by date or Fiscal Year only, per STR-CHG-001 v1.6 §7. |
| KenTender-governed unit catalogue | Replace with ERPNext `UOM` per CFG-CHG-002 v0.6 §4.4. |
| Bespoke fixture actors | Replace with the KT-STD-001 §8.3 shared register, extended by §14.2 below. |
| Restated closed-input rules, verification protocol, release evidence and universal prohibitions | **Remove.** Cite KT-STD-001 v1.1. |
| Citations of AUTH-ADR-001 v1.6, CFG-CHG-002 v0.3, STR-CHG-001 v1.3, BUD-CHG-001 v1.1 and NDS-CHG-001 v1.3 | Update to AUTH-ADR-001 v1.6, CFG-CHG-002 v0.6, STR-CHG-001 v1.6, BUD-CHG-001 v1.3 and NDS-CHG-001 v1.6. |

New in v1.9 — conformance to the Schedules, from full primary text:

| Item | Disposition in v1.9 |
|---|---|
| Prohibition on showing actual milestones | **Reversed.** Column 8 of the Third Schedule requires planned dates, planned days, **actual days and variance**, filled after activities conclude. The plan is a living record, and this is the data regulation 40(6)'s quarterly implementation report is built from. |
| No Status column, no Project Name | **Added.** Column 17 and the Third Schedule header block. |
| Three admitted procurement methods | **Replaced by the eleven the Third Schedule permits in a plan.** Two-stage tendering and framework agreements are in section 92(1) but absent from the plan format's list. Open tender is the default under section 91(1). |
| No goods / works / services classification | **Added** as `procurement_category`. The Second Schedule threshold matrix sets different limits for each, so admissibility cannot be evaluated without it. **Works** was absent from the requirement-type seed and is added. |
| Illustrative threshold figures | **Replaced with the Second Schedule figures.** The low-value limit is **per item per financial year**, so its check is cumulative across the plan rather than per transaction. |
| Four reservation categories | **Expanded** to the section 157(4) classes, including micro, small and medium enterprises and the regional schemes in regulation 151. Regulation 149 is the correct current citation for the 30%; the earlier reference to regulation 31 was to the repealed 2005-Act regulations. |
| No highest-advantage rule | **Added.** Section 156 and regulation 153: one scheme at a time, the one with the highest advantage. |
| No exclusive-preference classification | **Added** per regulation 163 — KES 1bn works and construction materials made in Kenya, KES 500m goods and services. |
| Lotting unexplained | **Grounded.** Regulation 154 makes lotting the mechanism for unbundling into quantities affordable to target groups, and the express exception to section 54(1). |
| Statutory returns named loosely | **Enumerated** in §7.5A — seven obligations with their authorities, recipients and deadlines. |
| Publication described neutrally | **Corrected.** Section 53(12) makes it publication **as an invitation to treat**. |
| Disposal items inside the procurement plan (§4.4A) | **Removed.** Section 53(4) requires a separate annual asset disposal plan in the Thirteenth Schedule format, approved by the Accounting Officer. Owned by DSP-CHG-001. |
| Estimate basis | **Extended.** Note 7 to the Third Schedule requires the estimate to be established through market surveys; section 54(2A) assigns those to the head of the procurement function. |

New in v1.8 — statutory conformance:

| Gap or error | Disposition in v1.8 |
|---|---|
| v1.7 made statutory approval optional | **Reversed.** Regulation 40(4) makes approval above the accounting officer mandatory. See §4.12. |
| Plan contents did not match regulation 41 | **Expanded.** Regulation 41 lists what an annual consolidated procurement plan shall include. v1.7 was missing the single-year or multi-year indication and its justification, the lotting indication, and an explicit aggregation indication. All three are added to the Plan Item. |
| Lotting explicitly prohibited on every artboard and in §17 | **Reversed.** Regulation 41(e) requires the plan to indicate which items shall be packaged into lots. The prohibition was directly contrary to the Regulations. |
| Only Open Tender admitted | **Expanded** to Open Tender, Request for Quotations and Low Value Procurement, which the Second Schedule threshold matrix requires and without which the threshold check in invariant 25 has nothing to validate. Regulation 91(6) additionally requires that a procuring entity maximise the use of request for quotations when implementing preferences and reservations for women, youth and persons with disabilities. |
| No asset disposal planning | **Added.** Regulation 34(i) makes the user department responsible for preparing departmental procurement **and asset disposal** plans, and section 53 of the Act covers both. A minimal Disposal Item is added to the departmental plan and the consolidated plan. |
| `DPPSubmissionWindow` as a separate DocType with `opens_at`, `closes_at` and derived states | **Remove.** Replaced by `kentender_dpp_submission_open` and `kentender_dpp_submission_closes_at` on the ERPNext Fiscal Year, following the flag pattern CFG-CHG-002 v0.6 §4.2 requires of every module flag. The window is configuration and belongs in Configuration & Governance. |
| An accepted Departmental Need could not be excluded from the DPP | **Add** `not_proceeding_reason` on the DPP entry. The department records that it is not proceeding this financial year; the entry is retained for audit, excluded from the plan, and the outcome is published back to Departmental Needs. |
| No quarterly implementation reporting | **Added as a named non-goal with its data reserved.** Regulation 40(6) requires the accounting officer to prepare a quarterly report on implementation of the annual procurement plan for the approving authority. MVP 1 does not generate it; the plan retains the lineage from which it is derived. |
| County resident-tenderer reservation absent | **Added** as a second reservation dimension. Regulation 40(5) requires a county procuring entity to indicate a minimum 20% budgetary allocation for preferences and reservations for resident tenderers of the county. Applies only where the site entity type is a county entity. |
| Departmental Needs and direct requirements presented as two equivalent paths | **Clarified.** The Departmental Procurement Plan is the statutory instrument under regulations 34(i) and 40(3). Departmental Needs is internal departmental consultation that feeds it and has no statutory standing. See §7.1. |

New in v1.7 — lifecycle simplification:

| Earlier item | Disposition in v1.7 |
|---|---|
| Finance confirmation per Plan Item, with a reservation created for every source allocation before the Plan could be submitted | **Replace with one plan-level funding confirmation.** A ministry plan runs to hundreds of items; the earlier model generated hundreds of tasks and reservations per cycle. PPADA requires the plan to sit within the approved budget — an affordability test, not a per-item hold. |
| Reservations created at planning stage | **Remove entirely.** Planning creates no reservation. Reservation and commitment happen at Procurement Requisition, where money is actually drawn and where independent drawdown makes double-spend a real risk. At planning one Planner consolidates the whole plan and can see every line. |
| Reservation release on item dissolution, successor cancellation and successor activation; reservation revalidation on corrected submission | **Remove.** All of it existed only because reservations were created at planning time and could go stale during governance. |
| `finance_state` on the Plan Item | **Remove.** Funding status is a property of the Plan Version. |
| Unconditional statutory approval task | **Retained and confirmed mandatory.** v1.7 made it optional on the mistaken view that the accounting officer is the final authority. Regulation 40(4) requires approval by the Cabinet Secretary, the county executive committee member, or the board of directors. v1.8 reverses that change; configuration selects which route applies, never whether one applies. |
| `Pending addition` as a stored entry state | **Derive it.** The behaviour is "accepted and unallocated with no open Draft Version to join", computable from allocation status and plan state. |

New in v1.6 — statutory planning controls:

| Gap | Disposition in v1.6 |
|---|---|
| No preference and reservation data anywhere | **Add** `reservation_category` to the Plan Item and a derived entity-level reserved percentage against the statutory target. Access to Government Procurement Opportunities reserves a share of procurement value for enterprises owned by youth, women and persons with disabilities, and the Third Schedule plan format expects the plan to show it. |
| No control against contract splitting | **Add** a non-blocking splitting advisory on Plan readiness. The Regulations prohibit splitting or structuring contracts to avoid a procurement procedure under section 54(1), except where unbundling is allowed under the preference and reservation schemes and regulation 154. Planning is where splitting is visible. |
| Procurement method never validated against value | **Add** a blocking readiness check against the threshold matrix in force for the plan's Fiscal Year. A method inadmissible for the estimated value fails readiness. |
| Estimate basis undefined | **Define.** The indicative amount is the full estimated cost including insurance, clearing and forwarding, demurrage, warehousing, advertisement and other incidental costs where applicable, as the Regulations require of planning estimates. |
| No rule on when the Annual Plan must be in force | **Add** PLN-BR-025. The Annual Plan for a Fiscal Year shall be Active before that year begins; a later activation is permitted but recorded with a reason. |
| Asset disposal planning silently absent | **Name as an explicit non-goal.** The Act treats procurement and asset disposal planning together; a disposal plan is a separate change unit and shall not be forced into the procurement plan. |
| Periodic PPRA reporting silently absent | **Name as an explicit non-goal**, with the publication payload shaped so the returns are derivable later. |
| Publication payload had no defined schema | **Shape it along Open Contracting Data Standard planning-stage fields**, so PPRA publication and open-contracting reporting do not require a rebuild. |
| Regulator reference data had no owner | **Assign to CFG-CHG-002** as effective-dated records: the threshold matrix, reservation categories and targets, and the quarterly market price index. A plan approved in 2027 must be auditable against the thresholds in force in 2027, not today's. |

**Identifiers are deliberately unchanged.** `DPP-{PE code}-{OU code}-{FY start}-{n}` and `PLN-{PE code}-{FY start}-{n}` keep their embedded entity code. They are opaque stable strings referenced by approved downstream contracts and seed data; the code is not a permission dimension or a source of truth. Do not renumber them.

## 2. Purpose and outcomes

Procurement Planning shall provide:

- one Departmental Procurement Plan for each department and Fiscal Year;
- automatic intake of every current accepted Need in that department and context;
- direct capture of a known departmental requirement without a Need;
- HoD certification of the complete departmental plan;
- Procurement classification and acceptance of each departmental entry;
- automatic intake of accepted departmental entries into the Draft Annual Plan;
- controlled formation of those entries into Plan Items;
- exact source lineage for every Plan Item;
- one Strategic Objective on every Plan Item;
- Procurement Budget Line selection and indicative amounts before departmental submission;
- one plan-level funding confirmation before plan governance;
- Accounting Officer adoption and exactly one applicable statutory approval;
- publication of the exact approved Plan Version before activation;
- an Active Plan baseline that Procurement Requisitions can validate; and
- controlled successor versions that never rewrite the Active baseline.

### 2.1 Scope exclusions

The module shall not contain:

- Need consultation, Need justification or Need review;
- Strategy plan authoring, Strategy approval, outcomes, indicators, targets or Value Commitment;
- Budget authorisation, Procurement Budget Line maintenance, funding-source maintenance, currency maintenance, commitments, expenditure or payments;
- a purchase request, Procurement Requisition, Tender, evaluation, contract, invoice or payment action;
- specifications, bills of quantities, Terms of Reference or attachments;
- a synthetic Need for a direct departmental requirement;
- a reason for not using Departmental Needs;
- partial use of an accepted Need;
- unit price, tax, cost breakdown or market-estimate components;
- editable contract-period or lotting fields in MVP-1;
- a generic note, comment, source reference, authority reference, evidence field, priority, score or completion percentage;
- actual procurement milestone entry or a Planning Monitoring Officer;
- editable technical identifiers, digests, audit actors or timestamps;
- a custom Frappe shell, header, breadcrumb or navigation system;
- **asset disposal planning of any kind.** Section 53(4) requires a separate **annual asset disposal plan** in the format set out in the Regulations, and regulation 176(2) makes that the Thirteenth Schedule. It is a distinct statutory instrument with its own contents, its own milestone dates and a different approver — the Accounting Officer, not the statutory authority that approves the procurement plan. It is owned by DSP-CHG-001. No disposal item, field, column or screen belongs in this module;
- **generation and transmission of statutory returns.** Seven distinct obligations attach to the plan, listed in §7.6. MVP 1 generates none of them and transmits nothing to the Authority, the National Treasury or the State Portal. It holds every field each return requires, including the actual dates and variance under column 8 of the Third Schedule, so each is a later reporting change unit rather than a data problem. **The accounting officer must know that all seven are discharged outside the system in MVP 1** — several carry statutory deadlines and one is an offence-bearing duty;
- an authoritative browser-stored context or a Planning-only work-queue menu; or
- legacy routes, aliases, compatibility adapters, fallback records or migrated fixtures.

### 2.2 Data-purpose gate

No stored field is permitted unless all three conditions are documented before implementation:

1. a current operational decision or output uses the field;
2. the screen, rule or service consuming it is named; and
3. its validation and system effect are defined.

“Useful later”, “normally captured”, “helpful context” and “the design showed it” are not valid reasons. An undocumented field is omitted, not added as optional data.

The Planning values below pass this gate:

| Value | Current consumer and effect |
|---|---|
| Direct requirement title | Identifies the departmental entry, validation task, source selector and Plan lineage. |
| Direct requirement description | Tells the HoD, Procurement Planner and Planner what the department requires. |
| Expected operational result | Preserves what the department expects the requirement to achieve and passes it read-only into Requisition eligibility. |
| Quantity and unit | Establish the complete source quantity and the quantity available for one Plan Item allocation. |
| Required by | Constrains the Plan Item completion date. |
| Procurement Budget Line | Identifies the authoritative funding position checked by Finance. |
| Indicative amount | Establishes the entry value and Plan Item value, and is the figure the affordability check sums. |
| Requirement type classification | Determines compatible Plan Item formation and procurement reporting. |
| Plan Item title and description | Define the procurement package shown in the Annual Plan and downstream lineage. |
| Strategic Objective | Provides the approved strategic alignment for the Plan Item. |
| Procurement method | Provides the method recorded in the Annual Plan, required by regulation 41(g). The server proposes it from the resolved threshold band; the Planner may change it only within that band. |
| Aggregation reason | Explains why several departmental entries form one procurement package; required only for a combined item. |
| Seven planned dates | Produce the approved procurement schedule and enforce chronological readiness. |
| Return reason | Gives the correction owner one actionable reason while preserving the submitted snapshot. |

## 3. Fixed ownership and dependency boundary

- Configuration & Governance owns the site Procuring Entity, Organisation Unit, the ERPNext Fiscal Year, timezone, the ERPNext `UOM` catalogue, requirement-type catalogue, procurement-method catalogue, module windows and statutory approval route. `kentender_core` owns the business-role registry, User Responsibility Assignment, Organisation Unit scope resolution and administration surface.
- Departmental Needs owns accepted Need identity, accepted versions and the six requirement facts supplied to Planning.
- Strategy Alignment owns Strategic Plans and Active Strategic Objectives. Planning stores the selected Objective lineage on a Plan Item and never edits Strategy.
- Budget & Funding owns Budget identity, Procurement Budget Lines, funding source, currency, live positions, reservations, commitments and ledger events.
- Procurement Planning owns DPPs, direct requirements, DPP funding specification, classification, Annual Plans, Plan Items, source allocations, the plan-level Finance task, Planning decisions, publication evidence and Requisition-eligibility projection. It owns no reservation.
- Procurement Requisitions owns the Requisition and its drawdown. Tendering and Contract Management own later operational records and actual milestones.

| Information or decision | Owner | Planning relationship |
|---|---|---|
| ERPNext Fiscal Year, Organisation Unit and timezone | Configuration & Governance | Resolve exact governed identifiers and fail closed when absent or ambiguous. The site Procuring Entity is implicit and never resolved as a choice. |
| Regulator reference data: threshold matrix, reservation categories and targets, market price index | Configuration & Governance, effective-dated | Read the version **in force for the plan's Fiscal Year**, never today's. Planning stores the resolved values on the record so a historical plan remains auditable after a gazette change. |
| Business responsibility and organisational scope | `kentender_core` under AUTH-ADR-001 v1.6 | Resolve the exact active role-bound assignment and PE/OU scope; never infer one from a separate Role or permission row. |
| DPP submission window | Procurement Planning configuration | Gate the first submission of a DPP root, including a reopened root with no accepted predecessor. Returned corrections and accepted-plan successors follow section 5.1. Opening a page creates nothing. |
| Accepted Need facts | Departmental Needs | Project read-only title, description, quantity, unit and required-by date. |
| Direct departmental requirement | Procurement Planning | Create and edit only inside a Draft or Returned DPP Version. |
| Procurement Budget Line identity, funding source and currency | Budget & Funding | Select from eligible Active Procurement Budget Lines and read live funding through services. |
| DPP indicative amount | Procurement Planning | Capture on every DPP entry and pass to Plan Item formation. |
| Requirement type | Procurement Planning | Procurement Planner classifies the immutable submitted entry. |
| Strategic Objective | Strategy Alignment / Procurement Planning | Select exactly one Active Objective on the Plan Item and preserve its version lineage. |
| Plan funding confirmation | Planning task / Budget service | Planning owns one plan-level task and its decision UI; Budget computes the affordability statement. No reservation is created. |
| Annual Plan adoption, statutory approval and publication | Procurement Planning | Present the exact Plan Version to the Accounting Officer and one applicable statutory authority, then activate only the acknowledged approved payload. |
| Requisition drawdown | Procurement Requisitions | Planning exposes eligibility and consumes authoritative drawdown references; it does not create a Requisition. |

Permitted dependency paths are:

**Configuration & Governance → Departmental Needs → Procurement Planning**

**Configuration & Governance / Strategy Alignment / Budget & Funding → Procurement Planning → Procurement Requisitions**

Planning shall consume other modules through explicit service or event contracts. It shall not import another module's controller or write directly to another module's tables.

## 4. Canonical domain model

All identifiers are generated by the server. Frappe audit fields remain framework-managed and are not duplicated as user data.

### 4.1 Departmental plan submission control

There is **no `DPPSubmissionWindow` DocType**. Departmental plan intake is governed by two namespaced fields on the canonical ERPNext `Fiscal Year`, owned by Configuration & Governance and following the flag pattern that CFG-CHG-002 v0.6 §4.2 requires of every module flag:

| Field | Rule |
|---|---|
| `kentender_dpp_submission_open` | `1` permits an initial departmental plan submission for that Fiscal Year; `0` blocks it. At most one Fiscal Year may have it enabled. |
| `kentender_dpp_submission_closes_at` | Optional datetime. Reaching it closes intake automatically. |

Procurement Planning reads both and writes neither. There is no `opens_at`, no `Scheduled` state, no window lifecycle, no approval and no title, description or reason field. Administrator or System Manager maintains the flag in the Fiscal Years section of System setup.

Regulation 40(3) requires the head of a user department to submit an annual departmental procurement plan **before the commencement of the financial year**, so the close instant is normally set at or before 30 June preceding the plan year.

### 4.2 DepartmentalProcurementPlan

Stable identity for one department in one Fiscal Year.

| Field | Operational purpose and system effect |
|---|---|
| `dpp_id` | Immutable internal identity. |
| `dpp_reference` | Generated as `DPP-{PE code}-{OU code}-{FY start}-{3 digits}` and used in routes and queues. |
| `fiscal_year` | The ERPNext `Fiscal Year` this plan belongs to. Required and immutable. It is planning data, never a permission dimension. |
| `org_unit_id` | Fixes the department and HoD scope. Required and immutable. |
| `current_state` | Derived root display state: `Draft`, `Submitted`, `Returned`, `Accepted` or `Withdrawn`. |
| `current_version_id` | Points to the current Draft, Returned or Submitted Version. |
| `current_accepted_version_id` | Points to the latest accepted Version. Empty until acceptance. |
| `record_version` | Monotonic optimistic-concurrency token. |

There is exactly one DPP root per `fiscal_year + org_unit_id`.

### 4.3 DPPVersion

| Field | Operational purpose and system effect |
|---|---|
| `dpp_version_id` | Immutable version reference used by submission and Annual Plan lineage. |
| `dpp_id` | Links the Version to its stable root. |
| `version_number` | Generated sequence within the DPP. |
| `based_on_version_id` | Identifies the accepted Version copied for an update. Empty on Version 1. |
| `version_status` | `Draft`, `Submitted`, `Returned`, `Accepted`, `Superseded` or `Withdrawn`. |
| `submission_id` | Points to the immutable submitted snapshot. Empty before submission. |

A Draft Version is mutable. Submission locks its snapshot. A return creates a copied Draft correction and preserves the submitted Version. One accepted Version may coexist with at most one open successor.

### 4.4 DPPEntry

One departmental requirement in one DPP Version.

The stable `source_line_id` is the Need ID for a Need-origin entry and the `dpp_entry_id` for a direct entry. No duplicate source identifier is stored.

| Field | Operational purpose and system effect |
|---|---|
| `dpp_entry_id` | Immutable entry reference used by classification and source lineage. |
| `dpp_version_id` | Fixes the containing Version. |
| `source_origin` | `Accepted Departmental Need` or `Direct departmental requirement`. Required and immutable after creation. |
| `need_id` / `need_version_id` | Fix the accepted Need source. Required only for Need-origin entries; empty for direct entries. |
| `title` | Requirement label. Read-only projection for Need-origin; editable for direct origin. |
| `description` | Requirement statement. Read-only projection for Need-origin; editable for direct origin. |
| `expected_operational_result` | Intended operational effect. Read-only projection for Need-origin; editable for direct origin. Required for every entry. |
| `quantity` | Full source quantity, greater than zero. Read-only for Need-origin. |
| `unit_id` | Governed quantity unit. Read-only for Need-origin. |
| `required_by_date` | Required and inside the target FY. Read-only for Need-origin. |
| `budget_line_id` | Planning-selected Active eligible Procurement Budget Line. Required before submission. |
| `indicative_amount_minor_units` | Planning-owned entry value. Required before submission and greater than zero, unless the entry is marked not proceeding. Currency is read from the Procurement Budget Line; there is no editable currency field. |
| `not_proceeding_reason` | Set only on a Need-origin entry the department has decided not to pursue this financial year; 20–500 characters. The entry is retained in the submitted plan for audit, carries no funding specification, forms no Plan Item, and is excluded from every plan total. The outcome is published back to Departmental Needs as usage information. A direct requirement is removed rather than marked, because nothing upstream depends on it. |

Direct entries contain no Need reference, bypass reason, attachment or source evidence. Need-origin entries retain the accepted Need's expected operational result as a read-only projection.

### 4.5 DPPSubmission

The immutable HoD-certified snapshot of one DPP Version.

| Field | Operational purpose and system effect |
|---|---|
| `dpp_submission_id` | Immutable submission and queue reference. |
| `dpp_version_id` | Fixes the submitted Version. |
| `submission_number` | Generated sequence for the DPP root. |
| `submitted_entry_snapshots` | Immutable ordered rows containing each entry and its source lineage, funding specification and source version. |
| `attestation_text` | Exact fixed certification rendered with department and FY. |
| `submitted_by_user_id` | Records the HoD or acting HoD who certified the plan. |
| `authority_snapshot` | Records the exact User Responsibility Assignment ID and immutable role/PE/OU/effective-period snapshot used for the decision. |
| `submitted_at` | Server decision instant. |

The attestation is:

> I certify that this Departmental Procurement Plan contains the current procurement requirements of {department} for {financial_year}, including every current accepted Departmental Need either planned or recorded as not proceeding, and any direct departmental requirements shown. I confirm that the quantities, required-by dates, Procurement Budget Lines and indicative amounts are ready for Procurement validation and inclusion in the Annual Procurement Plan.

### 4.6 DPPValidationTask and DPPValidationDecision

`DPPValidationTask` identifies the exact submitted DPP Version, its Fiscal Year and Organisation Unit, Open/Completed status and decision token. It is visible only to a Procurement Planner with an active site-wide User Responsibility Assignment. The task routes work but grants no authority; its FY is record data, not a user grant.

`DPPValidationDecision` is immutable and records:

- `Accept departmental plan` with one governed requirement type for every submitted entry; or
- `Return to department` with at least one structured issue containing the affected entry, concise problem and exact correction required.

There is no claim, priority, score, generic note or AO recipient.

### 4.7 AnnualProcurementPlan

| Field | Operational purpose and system effect |
|---|---|
| `plan_id` | Stable Annual Plan identity. |
| `plan_reference` | Generated as `PLN-{PE code}-{FY start}-{3 digits}`. |
| `fiscal_year` | The ERPNext `Fiscal Year` this Annual Plan covers. Required and immutable. |
| `title` | System-generated as `{entity name} Annual Procurement Plan {FY period}`, with the entity name read from site configuration and not stored as a link. `FY period` is the display period without an `FY` prefix, for example `2027/28`. |
| `active_version_id` | Points to the sole Active Version. Empty before activation. |
| `open_successor_version_id` | Points to the sole Draft or in-governance successor. Empty when none. |
| `record_version` | Optimistic-concurrency token. |

There is at most one AnnualProcurementPlan per Fiscal Year and at most one open successor.

### 4.8 PlanVersion

| Field | Operational purpose and system effect |
|---|---|
| `plan_version_id` | Immutable version reference. |
| `plan_id` | Links to the stable Annual Plan. |
| `version_number` | Generated sequence within the Annual Plan. |
| `based_on_version_id` | Identifies the Active predecessor. Empty for Version 1. |
| `correction_of_plan_version_id` | Identifies the immutable submitted Plan Version returned by a governance actor. Empty unless this Draft is a correction. |
| `version_status` | `Draft`, `Awaiting Accounting Officer`, `Awaiting statutory approval`, `Returned`, `Approved — publication pending`, `Publication failed`, `Active`, `Superseded` or `Cancelled`. |
| `change_reason` | Required only for a successor Version; identifies the approved-plan change being proposed. |

The mutable Draft content is locked when submitted. A return preserves that immutable Plan Version and creates the next numbered Draft Plan Version linked through `correction_of_plan_version_id`; it does not reopen the submitted record. The correction retains the returned Version's `based_on_version_id`, if any. Pending DPP additions cannot enter it. The Active predecessor remains operational until the correction or successor is approved, published and acknowledged.

### 4.9 PlanItem

| Field | Operational purpose and system effect |
|---|---|
| `plan_item_id` | Stable item reference used in plan output and downstream lineage. |
| `plan_version_id` | Fixes the containing Version. |
| `title` | Procurement package title; required, 5–160 characters. |
| `description` | Procurement-facing description; required, 10–1,000 characters. |
| `strategic_objective_id` | Exactly one Active Strategic Objective valid for the PE and Plan period. Required before Finance request. |
| `procurement_category` | `Goods`, `Works` or `Services`. The Second Schedule threshold matrix sets different limits for each, so method admissibility cannot be evaluated without it. Required, derived from the accepted DPP classification, and identical across all combined sources. |
| `requirement_type_id` | The finer classification used for grouping and reporting, derived from the accepted DPP classification. All combined sources must have the same type. It does not substitute for `procurement_category`. |
| `procurement_method_id` | The method planned for this package, required by regulation 41(g) and column 5 of the Third Schedule. The catalogue is the **eleven methods the Third Schedule permits in a plan**: open tender, direct, restricted, request for quotation, low value, community participation, design competition, electronic reverse auction, force account, competitive negotiations and request for proposals. Two-stage tendering and framework agreements appear in section 92(1) of the Act but **not** in the plan format's list and are therefore not selectable here. Open tender is the default, because section 91(1) makes it the preferred method; an alternative may be chosen only where admissible for the item's category and value. |
| `plan_horizon` | `Single year` or `Multi-year`, required by regulation 41(c). |
| `multi_year_justification` | Required only when `plan_horizon` is `Multi-year`; 20–500 characters. Regulation 41(c) requires the indication to be justified, and regulation 40(2) requires multi-year plans to be integrated into the medium term expenditure framework. |
| `aggregation_indicator` | `Not aggregated`, `Aggregated into this package` or `Common-user item arrangement`, required by regulation 41(d). |
| `lotting_indicator` | `Single lot` or `Packaged into lots`, required by regulation 41(e). |
| `lot_count` | Required only when `lotting_indicator` is `Packaged into lots`; a positive integer. Lot specifications belong to Tender Management; the plan states only that lotting is intended and how many lots. |
| `county_resident_reservation` | Check. Available and required only where the site entity is a county entity. Regulation 40(5) requires a county procuring entity to indicate a minimum 20% budgetary allocation for preferences and reservations for resident tenderers of the county. |
| `reservation_category` | The preference and reservation scheme this item is planned under. Section 157(4) applies preferences and reservations to disadvantaged groups; micro, small and medium enterprises; works, services and goods; identified regions; and other prescribed categories. Governed values, sourced from the effective-dated reference for the plan's Fiscal Year, are therefore: `None`; `Youth`; `Women`; `Persons with disabilities`; `Other disadvantaged group`; `Micro, small and medium enterprise`; `Regional — county`; `Regional — sub-county`; `Regional — constituency`; `National reservation — citizen contractor`. Required before plan funding confirmation; `None` is an explicit choice, not an empty value. |
| `exclusive_preference` | Derived, not entered. Set where funding is wholly national or county and the planned value falls below the regulation 163 threshold — KES 1,000,000,000 for works, construction materials and other materials made in Kenya, or KES 500,000,000 for goods and services. Exclusive preference to citizen contractors then applies under section 157(8)(a). |
| `threshold_band_at_readiness` | The threshold band resolved when readiness last passed, retained so a historical plan stays auditable after the matrix changes. Server-set. |
| `aggregation_reason` | Required only when more than one DPP entry forms the item; 20–500 characters. Empty for a single-source item. |
| `invitation_date` | First planned procurement milestone. |
| `bid_opening_date` | Planned bid opening. |
| `evaluation_completion_date` | Planned evaluation completion. |
| `award_approval_date` | Planned award approval. |
| `award_notification_date` | Planned notification. |
| `contract_signing_date` | Planned contract signing. |
| `delivery_completion_date` | Planned delivery or implementation completion; not later than the earliest source required-by date. |
| `actual_*_date` | One actual date per planned milestone above, recorded as each activity concludes. Column 8 of the Third Schedule requires the plan to carry planned dates, planned days, **actual days and variance**. The plan is therefore a living record of execution against intention, not a frozen statement of intent. |
| `planned_days` / `actual_days` / `variance_days` | Derived per milestone. Variance is planned days minus actual days, computed only once the corresponding actual date exists. |
| `item_status` | Column 17 of the Third Schedule. A short governed status for the item's execution against plan. |
| `item_state` | `Draft`, `Dissolved`, `Active`, `Removed in successor` or `Superseded`. A Dissolved item is historical, read-only and excluded from Plan totals. |

| `record_version` | Optimistic-concurrency token. |

Quantity, unit, planned value, funding source and Procurement Budget Line breakdown are derived from source allocations. The item's **planned value** is the sum of its source indicative amounts, each of which is the full estimated cost of that requirement including insurance, clearing and forwarding, demurrage, warehousing, advertisement and other incidental costs where applicable. A planning estimate net of incidentals is invalid, because the affordability check and every downstream reservation are computed from this figure. Note 7 to the Third Schedule adds that the estimated cost **shall be established through market surveys**, and section 54(2A) makes the head of the procurement function responsible for carrying those surveys out. The plan records the estimate; the market price index and the entity's own survey are its evidence. **Source correction required** is derived when an allocation no longer points to the current accepted DPP entry/version for its stable departmental source. Contract period, lotting, Value Commitment, recommended method, generic basis and actual milestone fields do not exist.

### 4.10 PlanSourceAllocation

| Field | Operational purpose and system effect |
|---|---|
| `plan_source_allocation_id` | Immutable source-lineage reference passed to Requisition eligibility as `plan_item_line_id`. |
| `plan_item_id` | Identifies the Plan Item consuming the source. |
| `accepted_dpp_entry_id` | Fixes the exact accepted departmental entry. |
| `source_origin` | Preserves `Accepted Departmental Need` or `Direct departmental requirement`. |
| `need_id` / `need_version_id` | Preserves Need lineage only when the source has it. |
| `quantity` / `unit_id` | Full accepted source quantity. |
| `budget_line_id` / `indicative_amount_minor_units` | Full accepted source funding specification. |
| `allocation_state` | `Draft`, `Active`, `Released`, `Removed in successor` or `Superseded`. `Released` preserves a dissolved Draft item's lineage but makes the source available for new formation. |

One accepted DPP entry has at most one effective allocation and is allocated at full quantity in one open Plan Version. `Released` allocations are historical and do not block re-formation. No split allocation or partial amount is permitted in MVP-1.

### 4.11 FinanceTask and FinanceDecision

**One Finance task exists per Plan Version, not per Plan Item.** It fixes the exact submitted Plan Version, the per-Procurement-Budget-Line affordability statement computed by Budget, `Open`, `Completed` or `Cancelled` status, and a concurrency token.

The immutable Finance decision records `Confirm plan funding` or `Return to planner`, the actor, the exact User Responsibility Assignment ID and snapshot, the decision time, the affordability statement as it stood at the decision, and a required return reason where applicable.

**Planning creates no funding reservation.** Reservations and commitments are created at Procurement Requisition, where money is actually drawn. Confirmation here states that the consolidated plan sits within the approved budget — the evidence the accounting officer adopts on — and nothing more.

Finance evidence becomes `Stale` when the plan's Procurement Budget Line totals change after confirmation, or when a Procurement Budget Line's approved amount changes through a Budget successor. A title, description, Strategic Objective, aggregation reason, method or schedule correction does not invalidate an otherwise current confirmation.

### 4.12 PlanGovernanceTask and PlanDecision

One protected task is created for each of two controlled decisions:

- `Accounting Officer adoption` — the Accounting Officer adopts or returns the complete consolidated Plan; and
- `Statutory approval` — **always created. Approval above the accounting officer is mandatory.**

Regulation 40(4) of the PPAD Regulations 2020 provides that the consolidated annual procurement plan is prepared by the accounting officer **and approved by** the Cabinet Secretary, the county executive committee member for finance or responsible for the entity, or, where applicable, the board of directors or a similar body.

The route is therefore not optional. Site configuration selects **which** of the three applies to this entity; it cannot select none. Exactly one route applies, it is resolved from configuration, and users cannot add, remove or substitute a stage.

This is not an inferred approval stage under AUTH-ADR-001 v1.6 §5.8. That rule bars inventing an approver where an approved source names the accounting officer as final authority. Here a regulation names a different authority, so the stage is a legal requirement rather than an inference.

A misconfigured or absent route is a **configuration defect** that blocks adoption with `PLN_STATUTORY_ROUTE_UNCONFIGURED`. The plan cannot lawfully complete without it.

Each task fixes the exact immutable submitted Plan Version, current stage, role or legal capacity, scope and concurrency token. Each decision stores the action, actor, capacity exercised, decision time, submitted Version and required return reason. A Board decision also stores its collective resolution reference. There is no optional note field.

### 4.13 PlanPublication

| Field | Operational purpose and system effect |
|---|---|
| `publication_id` | Immutable attempt reference. |
| `plan_version_id` | Fixes the approved Version. |
| `destination_configuration_id` | Fixes the configured Annual Plan publication destination. |
| `attempt_number` | Supports idempotent retry of the same approved payload. |
| `result` | `Pending`, `Acknowledged`, `Failed` or `Indeterminate`. |
| `external_reference` | Authoritative acknowledgement or failure reference returned by the adapter. |
| `attempted_at` / `acknowledged_at` | Server instants used by task and audit views. |

The approved Plan payload is generated from the immutable Version. Users cannot edit the payload, destination or acknowledgement.

**Legal character.** Section 53(12) requires the accounting officer to publish and publicise the approved plan **as an invitation to treat** on the entity website, upon submission of the plan to the National Treasury under section 44(2)(c). Section 53(13) then requires the Treasury to publish it on the state tender portal. The publication record shall carry that characterisation.

**Scope of publication.** Regulation 50(2) contemplates a system that can prepare and publish **departmental or consolidated** procurement plans. MVP 1 publishes the consolidated Annual Procurement Plan and retains every accepted departmental plan version in a form publishable without rework. The annual asset disposal plan is published separately under DSP-CHG-001; the two are distinct statutory instruments and are never combined into one payload.

**Payload shape.** The payload uses **Open Contracting Data Standard planning-stage fields**: one release per Plan Item with an `ocid`, the `planning` block carrying budget reference, planned value and rationale, and the `tender` block carrying title, description, procurement method, value band, planned milestone dates, the plan horizon, the aggregation and lotting indicators, and the reservation category. Disposal items are carried in a separate section of the payload, since OCDS planning-stage fields do not model disposal. The entity is identified from site configuration, not from a stored key.

This is a schema decision made now rather than later. PPRA publication and periodic returns are named non-goals in §2.1, but both derive from this payload; shaping it to a standard now avoids rebuilding the publication path when either becomes real. The adapter may translate to a destination-specific format, but the canonical payload retained in the publication record is the OCDS-shaped one.

### 4.14 RequisitionEligibilityProjection

Read-only contract containing Plan, Version, Plan Item and allocation lineage; approved quantity/value; authoritative drawdown quantity/value; remaining quantity/value; current funding state; Active status; and evaluation time. It creates no Requisition and stores no duplicate operational status on the Plan Item.

## 5. Lifecycle and business rules

### 5.1 DPP lifecycle

| Current state | Command | Result | Actor |
|---|---|---|---|
| No DPP | Open departmental plan | DPP root and Draft Version 1 | Departmental Author or HoD |
| Draft | Save direct requirement / enrich Need / remove direct requirement | Draft updated | Departmental Author or HoD |
| Draft | Submit departmental plan | Immutable submission and Open validation task | HoD or acting HoD using the same role |
| Submitted | Return to department | Submitted snapshot preserved; copied correction Draft created | Procurement Planner |
| Submitted | Accept departmental plan | Submitted Version Accepted with classifications; accepted entries appear in the open Draft Annual Plan | Procurement Planner |
| Returned | Save / Resubmit | Corrected Draft saved or submitted as the next submission | Departmental Author; HoD submits |
| Accepted; change required | Create update | One Draft successor copied from Accepted Version | Departmental Author or HoD |
| Draft successor | Submit update | Same validation route; Active Plan unchanged | HoD or acting HoD using the same role |
| Draft / Returned with no downstream consumption | Withdraw DPP Version | Version Withdrawn; prior Accepted Version remains current when one exists | HoD or acting HoD using the same role |
| Withdrawn with no accepted predecessor; initial window Open | Reopen departmental plan | Same DPP root; next numbered Draft Version | Departmental Author or HoD |

The DPP may consist entirely of direct requirements. If current accepted Needs exist in the exact department, all must be **accounted for** exactly once before submission — either carried as a funded entry or marked with a `not_proceeding_reason`. A department is never forced to plan a requirement it has reconsidered, and never permitted to omit one silently. Direct entries may be added in any number. A DPP with no entries cannot be submitted. The window gates the first submission and any reopened root that still has no accepted predecessor. A correction returned from validation and a successor required by an authoritative source change may be resubmitted after window close; neither route admits a new unreviewed initial DPP.

### 5.2 Annual Plan lifecycle

| Current state | Command | Result | Actor |
|---|---|---|---|
| First DPP accepted; no Annual Plan | Project accepted entries | Annual Plan and Draft Version 1 created automatically; entries shown as unallocated | System, in the DPP-acceptance transaction |
| Active; no successor | Begin plan update | Draft successor; Active Version unchanged | Procurement Planner |
| Draft | Form Plan Items / save item | Draft updated | Procurement Planner |
| Mutable Draft item | Dissolve Plan Item | Allocations marked Released; sources return to unallocated | Procurement Planner |
| Draft; readiness passed | Request plan funding confirmation | One Finance task for the whole Version | Procurement Planner |
| Awaiting Finance | Confirm plan funding | Affordability statement recorded; Version Confirmed | Finance Confirmation Officer |
| Awaiting Finance | Return to planner | Version returns to Draft with a reason | Finance Confirmation Officer |
| Draft; funding confirmed | Submit consolidated Plan | Immutable submitted snapshot and Accounting Officer task | Procurement Planner |
| Awaiting Accounting Officer | Adopt and submit for statutory approval | Adoption decision and one statutory-approval task | Accounting Officer |
| Awaiting Accounting Officer | Return for correction | Submitted Version marked Returned; next numbered Draft correction created | Accounting Officer |
| Awaiting statutory approval | Approve Annual Procurement Plan | Approved — publication pending | The one configured statutory authority |
| Awaiting statutory approval | Return for correction | Submitted Version marked Returned; next numbered Draft correction created | The one configured statutory authority |
| Returned correction; ready | Submit corrected Plan | New immutable snapshot; affordability re-checked; funding confirmation repeated only if stale; route restarts at Accounting Officer | Procurement Planner |
| Approved / Publication failed | Publish / Retry | Active only on exact acknowledgement; otherwise failed/indeterminate | System; technical retry by System Manager if required |
| Draft successor | Cancel update | Successor Cancelled; the Active Version is unchanged | Procurement Planner |

A governance return never edits or reopens the submitted Version. It creates the next numbered Draft Plan Version containing exactly the sources present in the returned Version. DPP entries accepted while the Plan is submitted, returned or being corrected simply remain unallocated; they enter the next open Draft Version. **Pending addition** is a derived display label meaning "accepted and unallocated with no open Draft Version to join". It is computed from the entry's allocation status and the plan's state and is never stored as an entry state.

On corrected-Plan submission, affordability is re-checked. Funding confirmation is repeated only when the plan's per-line totals changed or a Procurement Budget Line's approved amount changed through a Budget successor; an unchanged plan carries its existing confirmation forward. Every corrected submission restarts at Accounting Officer adoption, including one returned at the statutory stage.

### 5.3 Invariants

1. Reads never create a DPP, Annual Plan, Version, task, allocation, reservation or publication attempt.
2. One DPP root exists per Fiscal Year and Organisation Unit, and one Annual Plan root per Fiscal Year. The initial Annual Plan is created only by the first successful DPP acceptance, never by a read.
3. A current accepted Need is represented once and at full quantity in its department's submitted DPP.
4. A direct requirement never creates or pretends to be a Need.
5. Every submitted DPP entry has one eligible Procurement Budget Line and one positive indicative amount.
6. Only the Procurement Planner classifies a submitted entry.
7. Every accepted DPP entry is allocated exactly once and at full quantity in the submitted Plan Version.
8. Sources may be combined only when Fiscal Year, Procurement Budget Line, currency, requirement type, unit and procurement treatment are compatible. Cross-currency combination is prohibited in MVP-1.
9. Every Plan Item has exactly one current Active Strategic Objective.
10. Plan Item value equals the sum of its source-allocation amounts.
11. Funding confirmation is one decision covering the whole Plan Version. There is no per-item confirmation and no partial confirmation.
12. Planned dates are chronological and delivery completion is no later than the earliest source required-by date.
13. Governance actors decide only an immutable submitted Version and cannot edit it.
14. The Accounting Officer adoption is followed by exactly one statutory approval route applicable to the PE; no professional-review, Head of Procurement Function, generic committee or publication approval is inserted.
15. Statutory approval does not itself publish or activate the Plan.
16. Only acknowledgement of the exact approved payload activates a Version.
17. At most one Plan Version is Active and at most one successor is open.
18. An Active item remains eligible until an acknowledged successor changes it, subject to funding and drawdown.
19. An Active item with a Requisition drawdown, Tender handoff, commitment or contract cannot be removed through Planning.
20. Submitted, decided, approved, Active and Superseded evidence is never edited or deleted.
21. Draft dissolution and successor cancellation change no Budget balance, because Planning holds no reservation.
22. An acknowledged successor that removes an Active item leaves Budget balances untouched. Any reservation or commitment created downstream at Requisition is released through the Requisition module's own controlled process, never by Planning.
23. A corrected Plan always returns to Accounting Officer adoption and never resumes directly at statutory approval.
24. Every Plan Item records an explicit `reservation_category` before plan funding confirmation may be requested. The Annual Plan derives the reserved share of planned value and compares it with the statutory target in force for its Fiscal Year. Falling short is an **advisory**, never a block: the target is an entity-level obligation discharged across the year, and the accounting officer adopts with the figure in view.
24aa. Where more than one preference or reservation scheme could apply to a Plan Item, the scheme with the **highest advantage** governs, under section 156, and a candidate is entitled to one scheme at a time under regulation 153. The server proposes the highest-advantage category from the effective-dated reference; the Planner may record a different category only with a reason, which is retained.
24ab. Lotting under `lotting_indicator` is the mechanism regulation 154 provides for unbundling a category into quantities affordable to specific target groups. Where an item is both lotted and reserved, the plan records that the lotting serves the reservation; this is the express exception to the anti-splitting rule in section 54(1).
24a. Where the site entity is a county entity, the Annual Plan additionally derives the share of planned value marked `county_resident_reservation` and compares it with the 20% minimum in regulation 40(5). Advisory on the same basis as invariant 24.
24b. Every Plan Item records `plan_horizon`, `aggregation_indicator` and `lotting_indicator` before plan funding confirmation may be requested. A `Multi-year` horizon requires its justification and a `Packaged into lots` indicator requires a lot count. These are contents the plan shall include under regulation 41.
25. A Plan Item's `procurement_method_id` shall be admissible for its planned value under the threshold matrix in force for the plan's Fiscal Year. An inadmissible method **blocks** readiness and names both the value band and the admissible methods. The resolved band is stored on the item so a later gazette change does not rewrite history.
26. Plan readiness raises a non-blocking **splitting advisory** when two or more Plan Items in one Version share the same Procurement Budget Line and requirement type and each falls below the open-tender threshold while their combined value would exceed it. The Planner records a short confirmation or aggregates the items. Legitimate unbundling under a preference and reservation scheme is a valid confirmation and is recorded as such.
27. The Annual Plan for a Fiscal Year shall be Active before that Fiscal Year begins. A later activation is permitted, blocks nothing, and requires a recorded reason retained in the plan's audit history.
28. A database uniqueness constraint enforces one Annual Plan root per Fiscal Year and one open Version per Plan; concurrent first-DPP acceptance returns or reloads the winner rather than creating a duplicate.

## 6. Roles, assignments and permissions

| Business responsibility or legal capacity | Central scope classification | Exact permitted work |
|---|---|---|
| Departmental Author | Organisation Unit | Open the relevant FY DPP in the assigned OU subtree, enrich Need-origin entries, create/edit direct entries and correct a returned Draft. Several people may hold this responsibility for one department, and one person may cover several assigned departments. Cannot submit unless also assigned HoD responsibility. |
| Head of User Department | Organisation Unit | All Author work plus certify, submit, resubmit and withdraw the departmental Version. Only an effective HoD assignment covering the DPP's OU may act at command time. |
| Procurement Planner | Site-wide | Accept or return submitted DPPs, classify entries, consolidate accepted sources, form and edit Plan Items, request Finance, submit the Annual Plan and prepare successors. |
| Finance Confirmation Officer | Site-wide | Open the one plan-level Finance task, confirm that the consolidated plan sits within the approved budget, or return it with a reason. Confirmation creates no reservation. This is the role defined by BUD-CHG-001 v1.4 §7; Budget Officer authors budget versions and holds no Planning task. |
| Accounting Officer | Site-wide | Adopt or return the complete consolidated Annual Procurement Plan. |
| Responsible Cabinet Secretary / County Executive Committee Member for finance or responsible for the entity / Board of Directors or similar governing body | Site-wide, in the exact approved legal capacity | Approve or return the Accounting-Officer-adopted Plan where that distinct statutory route is approved. Exactly one route applies to this entity. |
| Auditor | Site-wide or approved OU oversight scope | Neutral read of Plan and immutable evidence; no business mutation. |
| Administrator / System Manager | Technical read-all under AUTH-ADR-001 v1.6 | Inspect all Planning records, tasks, files and evidence; no Planning decision without the applicable business responsibility assignment. |

User Responsibility Assignment is the sole source of the relationship between a business responsibility and its site-wide or Organisation Unit scope. Frappe Roles are synchronized framework projections and Frappe User Permission, User Scope Assignment, Capability Profile and Operational Scope Assignment grant no Planning authority. Eligible Fiscal Years derive from the ERPNext Fiscal Year catalogue and the requested operation's window or state. Fiscal Year is never assigned to a user. Every list, count, detail, file, export, button and command uses the same shared AUTH resolver plus Planning's task, state and domain predicates.

Publication is an idempotent system service. A technical retry may be available to System Manager, but it retries the same approved payload and is not a procurement decision.

### 6.1 Maker-checker rules

Role combinations are permitted. The conflict is between actions on the same evidence chain, not between role labels held by a user.

| Earlier action by the same user | Later action prohibited on the same evidence chain |
|---|---|
| Submit one DPP submission as HoD | Accept or return that DPP submission as Procurement Planner |
| Create the Version, form/dissolve an item, save any Planner-owned field, request Finance or submit one Annual Plan Version as Procurement Planner | Confirm or return Finance for that Version; adopt or return it as Accounting Officer; approve or return it as statutory authority |
| Confirm or return funding for one Plan Version | Adopt or return that Version as Accounting Officer; approve or return it as statutory authority |
| Adopt or return one Plan Version as Accounting Officer | Approve or return that Version as statutory authority |

A Departmental Author may also be the effective HoD and submit the DPP: this is one departmental certification step, not an invented review level. For Annual Plans, the evidence chain includes the submitted Version and every correction derived through `correction_of_plan_version_id` until one Version activates or the open chain is cancelled. A correction does not reset segregation history. Administrator and System Manager receive no business-decision exception.

## 7. Cross-module integration contracts

### 7.1 Departmental Needs intake

**Standing of the two sources.** The Departmental Procurement Plan is the statutory instrument: regulation 34(i) makes the user department responsible for preparing departmental procurement and asset disposal plans and submitting them to the procurement function, and regulation 40(3) requires the head of a user department to submit an annual departmental procurement plan before the financial year begins.

**Departmental Needs has no statutory standing.** It is internal departmental consultation — a way for staff to raise anticipated requirements to their head of department during the year, and for the head to triage them early. An accepted Need is a candidate for the departmental plan, nothing more.

It follows that a direct departmental requirement is not a weaker path. It is the ordinary path, and the departmental plan is where a department's requirements legally live. Departmental Needs adds early visibility and an audit trail from the originating officer; it is never a precondition, and no document shall treat it as one.


`DepartmentalNeedAccepted.v2` supplies event identity, Need/version lineage, PE/OU/FY, title, description, expected operational result, quantity, unit and required-by date. Projection is idempotent.

- The current accepted Need appears as one read-only Need-origin DPP entry.
- Planning adds only Procurement Budget Line and indicative amount.
- A successor accepted event marks the earlier unsubmitted source stale and refreshes the Draft; if already submitted or consumed, it creates a correction requirement without rewriting evidence.
- A withdrawn event removes only an unsubmitted/unconsumed source. Departmental Needs cannot publish withdrawal while an Active Plan dependency exists.
- `NeedPlanningUsageChanged.v1` is published only when an Active Plan begins or ceases to represent the accepted Need version.
- When a DPP successor is accepted and its predecessor entry is allocated to a mutable Draft item, Planning marks the item **Source correction required**, leaves the historical allocation unchanged but ineligible, and lists the successor entry as unallocated. It never moves the allocation automatically. The Planner dissolves and re-forms the item.
- When the affected Plan Version is submitted or in governance, Planning blocks the decision and requires a governance return before correction. When the predecessor is Active, it remains authoritative and the successor entry waits for the next Plan successor.
- Accepted Needs belonging to a department with no submitted DPP after window close remain visible in the Planning workspace as **Not included — DPP submission window closed**. Departmental Needs retains the accepted records. This creates no DPP and does not permit a late first submission.

### 7.2 Strategy selection

`ListEligibleStrategicObjectives` wraps the Strategy contract `list_strategy_objectives` from STR-CHG-001 v1.6 §8. Planning first resolves the applicable Active plan version through `resolve_strategy_context`, supplying a date or Fiscal Year only — there is no Procuring Entity or organisation-unit argument. It returns Active Strategic Objectives from that resolved version. The selector displays the Objective title and its hierarchy path. Saving stores Objective ID, Strategy Plan ID and Strategy Version ID. Planning does not store Outcome, Indicator, Target or Value Commitment.

If the selected Objective ceases to be eligible before Plan submission, the item is blocked and the Planner must select a current Objective. An already Active Plan preserves its approved lineage.

### 7.3 Budget and Finance

`ListEligibleBudgetLines` wraps the Budget contract `list_eligible_budget_lines` from BUD-CHG-001 v1.4 §9.1, supplying the Fiscal Year and the source Organisation Unit. A line is eligible when its owner scope is Entity-wide or matches that unit; owner scope is a Budget record-eligibility rule and never a user-permission check. The DPP entry stores the selected line ID and amount; funding source and currency display from Budget read services.

**Affordability, not reservation.** `CheckPlanAffordability` wraps the Budget contract `check_plan_affordability`. Planning supplies the Fiscal Year and the plan's per-Procurement-Budget-Line planned totals; Budget returns, for each line, its approved amount, the plan's planned total, the current reserved and committed positions, and two verdicts:

| Verdict | Basis | Effect |
|---|---|---|
| Within approved amount | Planned total ≤ approved amount | **Blocking.** Failure prevents Plan submission and names every failing line with its exact excess. |
| Within currently available | Planned total ≤ approved − reserved − committed | **Advisory.** A plan may legitimately exceed today's availability, because planning and drawdown run on different horizons. Shown to the Planner, the Finance Confirmation Officer and the Accounting Officer; blocks nothing. |

The call is non-mutating. It creates no reservation, no ledger event and no Budget record.

**Planning creates no reservation at any point.** Need acceptance, DPP save, DPP submission, DPP validation, Plan Item formation, Finance confirmation, adoption, approval and publication all leave Budget balances untouched. Reservation and commitment happen at Procurement Requisition through the Budget contracts in BUD-CHG-001 v1.4 §9.1, against the Plan Item lineage exposed in §7.4.

This removes from Planning: per-item Finance tasks, reservation references on Plan Items, reservation release on item dissolution or successor cancellation, and reservation revalidation on corrected submission. None of those had a statutory basis at planning stage, and each created work proportional to the number of Plan Items rather than to the number of decisions.

### 7.4 Requisition eligibility

`GetRequisitionEligiblePlanItem.v2` exposes an item only when its Plan Version is Active, Finance evidence remains current, remaining quantity and value are positive, and no blocking successor or withdrawal effect applies.

It returns the Plan, Version and Plan Item IDs; Fiscal Year; requirement type; procurement method; Strategic Objective and path; planned dates; funding-confirmation references; total and remaining quantity/value; and, for every `plan_source_allocation_id`:

- source origin and stable `source_line_id`;
- DPP entry ID and Need/version lineage where applicable;
- department, title, description and expected operational result;
- approved and remaining quantity, unit and required-by date; and
- Procurement Budget Line, allocated amount and remaining amount.

Each authorised Requisition draws a positive quantity and value from one eligible Plan Item and preserves every selected `plan_source_allocation_id`. Several sequential Requisitions may draw the same Plan Item while quantity/value remain. Procurement Requisitions enforces at most one open Requisition per `plan_item_id + requesting_org_unit_id`. Drawdown and reversal are atomic and cannot exceed either the source row or Plan Item balance. Planning never creates the Requisition or technical specification, and a later Plan successor never silently changes an authorised Requisition.

### 7.5A Statutory returns and publication

Seven obligations attach to the annual procurement plan. MVP 1 implements the website publication in §4.13 and none of the returns; all are listed so that the data they need is retained rather than rediscovered.

| Authority | Obligation | Recipient | When |
|---|---|---|---|
| s.44(2)(c) | The procurement plan, in conformity with the medium term fiscal framework | National Treasury | On preparation. National security organs exempt under s.44(3) |
| **s.53(12)** | **Publish the approved plan as an invitation to treat on the entity website** | Public | On submission to Treasury |
| s.53(13) | Treasury publishes plans as invitation to treat on the state tender portal | Public | On receipt — not this entity's action |
| s.158(2), s.44(2)(i) | The part of the plan demonstrating application of preference and reservation schemes | The Authority | **Within 60 days after the financial year commences** |
| s.157(12)–(13) | Compliance certification with data disaggregated by youth, women and persons with disability | The Authority | **Every six months** |
| s.158(3) | All awards where a preference or reservation applied, disaggregated | The Authority | **Quarterly** |
| reg 40(6) | Report on **implementation** of the plan | Cabinet Secretary, CECM or governing body | **Quarterly** |

Regulation 161(2): the section 157(12) and 158(3) reports go to the Authority **within fourteen days after the end of the reporting period**, copied to the National Treasury, in formats the Authority provides.

Publication under section 53(12) is characterised in the Act as an **invitation to treat**. It is a legal act with consequences for bidders, not a transparency gesture, and the published artefact is the approved plan in the Third Schedule format.

### 7.5 Regulator reference data

Three PPRA-published references change independently of this codebase and are consumed, never authored, here:

| Reference | Use in Planning |
|---|---|
| Threshold matrix | Determines which procurement methods are admissible for a Plan Item's planned value. Blocking, per invariant 25. |
| Reservation categories and target | Supplies the governed `reservation_category` values and the entity-level target percentage. Advisory, per invariant 24. |
| Market price index | Displayed beside a planning estimate for standard goods, works and services as a benchmark. Advisory and display-only in MVP 1; it never blocks, adjusts or overwrites an estimate. |

All three are **effective-dated**. Planning resolves the version in force for the plan's Fiscal Year, never the current one, and stores the resolved band or target on the record. A plan approved under a 2027 gazette remains auditable against that gazette after it is superseded.

Where a reference is absent for the plan's Fiscal Year, method admissibility fails closed with `PLN_REFERENCE_UNAVAILABLE`; the reservation target and price index degrade to "not published" and block nothing.

## 8. Service and command contracts

### 8.1 Read contracts

| Contract | Required result |
|---|---|
| `ResolvePlanningContexts` | Authorised PEs/OUs and matching assignment IDs from the shared AUTH resolver plus configured Financial Years available to the module; no implicit first record and no per-user FY assignment. |
| `GetPlanningWorkspace` | Reconciled action queue, waiting work and current Plan state using one scope predicate. |
| `GetDepartmentalPlan` | Current DPP Version, accepted Need coverage, direct entries, blockers and authorised commands. |
| `GetDPPValidationTask` | Exact immutable submission, all entry details, funding specification, source origin and current decision controls. |
| `GetRegulatoryReference` | The threshold matrix, reservation categories and target, and market price index in force for a supplied Fiscal Year, with their effective dates. Read-only; Planning never writes regulator reference data. |
| `ListAcceptedDPPSources` | Current accepted, unallocated entries for the exact Fiscal Year. The read model joins each accepted DPP entry through the immutable `DPPValidationDecision` for that submission/version to obtain its classification; it does not invent a classification field on `DPPEntry` or `PlanSourceAllocation`. |
| `GetPlanVersion` | Complete Version, all Plan Items, source allocations, Finance state, governance history and current commands. |
| `GetPlanItem` | Exact item, all source rows, Objective, method, schedule and Finance state. |
| `GetFinanceTask` | Protected current Budget positions and required/after-confirmation amounts for every source. |
| `GetPlanGovernanceTask` | Complete immutable Plan details and exact stage decision controls. |
| `GetPublicationTask` | Exact approved Version, destination, attempt result and permitted publish/retry action. |
| `GetRequisitionEligibility` | Current eligible or blocked result with lineage, balances and evaluation time. |

### 8.2 Commands

| Command | Core effect |
|---|---|
| `OpenDepartmentalPlan` | Idempotently create/reuse the one DPP root and current Draft after exact authority checks; after withdrawal with no accepted predecessor, create the next Draft Version only while the initial window is Open. |
| `SaveNeedFunding` | Add or change only Procurement Budget Line and amount on a current Need-origin Draft entry. |
| `SaveDirectRequirement` | Create/update the eight permitted direct-entry values, including expected operational result. |
| `RemoveDirectRequirement` | Remove an unsubmitted direct entry from the current Draft. |
| `SubmitDepartmentalPlan` | Revalidate complete accepted-Need coverage, direct entries, funding, window and HoD authority; create immutable submission and validation task. |
| `ReturnDepartmentalPlan` | Preserve submission, record structured issues and create the correction Draft. |
| `AcceptDepartmentalPlan` | Record classifications, create/reuse the initial Draft Annual Plan when necessary and project accepted entries into its unallocated-source queue in the same transaction. |
| `FormPlanItems` | Create one item per selected source or one combined item for compatible selected sources; allocate each source atomically. |
| `DissolvePlanItem` | On a mutable Draft only, mark allocations Released and return the sources to the unallocated list atomically. Budget balances are untouched. |
| `SavePlanItem` | Save only the Plan Item allow-list and recalculate exact blockers. |
| `RequestPlanFundingConfirmation` | Validate Plan readiness, compute the affordability statement and create or reuse the one current Finance task for the Version. |
| `ConfirmPlanFunding` | Re-check affordability under lock and record the Finance decision with the affordability statement. It creates no reservation. |
| `ReturnFromFinance` | Record the required reason and return the Version to Draft. |
| `SubmitConsolidatedPlan` | Require all accepted sources allocated, all items complete and Finance current; create the immutable submission and Accounting Officer task. |
| `AdoptAndSubmitPlan` | Record Accounting Officer adoption and create exactly one statutory-approval task resolved for the PE. |
| `ApproveAnnualPlan` | Record approval and move the exact Version to publication pending. |
| `ReturnPlanVersion` | Mark the submitted Plan Version Returned, record the actionable reason and create the next numbered Draft correction linked to it. |
| `SubmitCorrectedPlan` | Lock a new corrected snapshot, re-check affordability, repeat funding confirmation only when the plan's per-line totals or a Procurement Budget Line's approved amount changed, then restart governance at Accounting Officer adoption. |
| `PublishAnnualPlan` | Transmit the exact approved payload and activate only on acknowledged response. |
| `BeginPlanUpdate` | Create the sole Draft successor from the Active Version. |
| `RemovePlanItemInSuccessor` | Propose whole-item removal only when downstream checks permit it. |
| `CancelPlanUpdate` | Cancel the successor and leave the Active Version unchanged. No Budget balance changes. |

All mutating commands require an expected record version and idempotency key. Server-side role-bound assignment, record scope, state, task, segregation and live-data checks are repeated inside the transaction.

## 9. Error contract

| Code | Plain-language result |
|---|---|
| `PLN_NO_CONTEXT` | You do not have an assigned Procurement Planning scope, or no configured Financial Year is available. |
| `PLN_WINDOW_CLOSED` | The initial departmental-plan submission window is closed. |
| `PLN_NEED_COVERAGE_INCOMPLETE` | Add every current accepted Need to this departmental plan before submitting. |
| `PLN_ENTRY_INCOMPLETE` | Complete the highlighted requirement fields before submitting. |
| `PLN_BUDGET_LINE_INELIGIBLE` | Select an Active Procurement Budget Line available to this department and Financial Year. |
| `PLN_DPP_STALE` | This departmental plan changed. Reload and review the current Version. |
| `PLN_CLASSIFICATION_INCOMPLETE` | Classify every submitted requirement before accepting the plan. |
| `PLN_SOURCE_UNAVAILABLE` | One or more selected departmental entries are no longer available for Plan Item formation. |
| `PLN_SOURCE_INCOMPATIBLE` | The selected entries cannot form one Plan Item. Create separate items. |
| `PLN_SOURCE_CORRECTION_REQUIRED` | A departmental source changed. Dissolve and re-form the affected Draft item before continuing. |
| `PLN_DISSOLUTION_BLOCKED` | This Plan Item is no longer in a mutable Draft and cannot be dissolved. |
| `PLN_OBJECTIVE_INELIGIBLE` | Select an Active Strategic Objective valid for this Plan. |
| `PLN_SCHEDULE_INVALID` | Correct the highlighted dates so the schedule is chronological and meets the required-by date. |
| `PLN_PLAN_NOT_AFFORDABLE` | The planned total exceeds the approved amount on one or more Procurement Budget Lines. Every failing line and its exact excess are returned. No plan state changes. |
| `PLN_FINANCE_STALE` | Funding confirmation is no longer current. Request confirmation again. |
| `PLN_RESERVATION_RELEASE_FAILED` | Funding could not be released. The Planning change was not completed. Try again or quote the support reference. |
| `PLN_REVIEW_STALE` | This task has already changed. Reload to see the current decision. |
| `PLN_SEGREGATION_CONFLICT` | You cannot make this decision because you performed an incompatible earlier action. |
| `PLN_PUBLICATION_FAILED` | Publication was not acknowledged. The approved Plan remains unchanged and may be retried. |
| `PLN_REMOVAL_BLOCKED` | This Active Plan Item has downstream use and cannot be removed through Planning. |
| `PLN_STATUTORY_ROUTE_UNCONFIGURED` | The statutory approval route for this entity is not configured. Adoption cannot proceed; a plan cannot lawfully complete without statutory approval. |
| `PLN_PLAN_CONTENTS_INCOMPLETE` | One or more Plan Items are missing a plan horizon, aggregation indicator, lotting indicator, multi-year justification or lot count required by the plan contents rules. |
| `PLN_METHOD_NOT_ADMISSIBLE` | The selected procurement method is not admissible for this planned value. The applicable value band and admissible methods are returned. |
| `PLN_RESERVATION_REQUIRED` | Record a preference and reservation category before requesting Finance confirmation. `None` is a valid choice. |
| `PLN_REFERENCE_UNAVAILABLE` | The threshold matrix for this financial year has not been configured. Method admissibility cannot be checked and readiness fails closed. |
| `PLN_STALE_WRITE` | Another user changed this record. Reload before continuing. |

Unauthorised detail and task reads return the same not-found response as a nonexistent record. Internal diagnostics are logged with a support correlation and are not shown as user fields.

## 10. UI architecture, menu and routes

Procurement Planning has one KenTender navigation entry named **Procurement Planning**. It does not add sidebar entries for DPP review, Finance, Accounting Officer, statutory approval, publication or any other work queue.

| Surface | Canonical Frappe Desk route | Primary user |
|---|---|---|
| Planning workspace | `/app/procurement-planning` | All authorised Planning users |
| Departmental Plan | `/app/departmental-procurement-plan/{dpp_reference}` | Departmental preparer, HoD, Procurement Planner read |
| DPP validation task | `/app/procurement-planning/dpp-review/{task_id}` | Procurement Planner |
| Annual Plan | `/app/annual-procurement-plan/{plan_reference}` | Planner and authorised readers |
| Plan Item | `/app/procurement-plan-item/{plan_item_id}` | Planner and authorised readers |
| Finance task | `/app/procurement-planning/finance/{task_id}` | Assigned Budget Officer |
| Governance task | `/app/procurement-planning/review/{task_id}` | Accounting Officer or the one statutory authority applicable to the PE |
| Publication result | `/app/procurement-planning/publication/{publication_id}` | Neutral read; technical retry only for System Manager when required |

The workspace shows only work the actor can perform or is waiting for. The same tasks may appear in the shared KenTender **My Work** surface and notifications. Task routes above are authorised deep links reached from a task row or notification; they are not menu definitions. The workspace does not duplicate Budget, Strategy, Needs or Configuration dashboards. Frappe supplies the Desk header, breadcrumb, global search, user menu and common navigation.

Access is resolved server-side from the active User Responsibility Assignment for the required role and, where the role is Organisation Unit scoped, the record's unit. Fiscal Year is never assigned to a user; it derives from the ERPNext Fiscal Year catalogue and is filtered by the operation's window and record state.

There is no Procuring Entity selector anywhere in Procurement Planning. A selected Fiscal Year is only a visible filter and never grants access. The page loads the sole eligible year directly; when several are eligible it shows one changeable Financial Year select in the Planning page header. The last valid selection may be stored as a server-side user preference for convenience, always with a visible reset. A browser value may cache presentation only and must be ignored when unauthorised, invalid or absent. Direct record and task routes derive the Fiscal Year from the record and reauthorise it; they never depend on a prior selection.

### 10.1 Existing UI reuse and correction

| Existing Planning asset | Disposition |
|---|---|
| Page shell, context strip, headers, cards, tables, status badges, dialogs and sticky action footer | Reuse. |
| Planning workspace, DPP workspace, Plan workbench, Plan Item editor, Finance drawer/task and wide governance review layout | Reuse and correct against this document. |
| Need-origin DPP row | Retain; remove Need-owned funding/Strategy/classification assumptions and add Planning funding completion. |
| Direct requirement editor | Add using PLN-DES-04. |
| Accepted-Need funding editor | Add or correct using PLN-DES-03. |
| Plan Item Strategy control | Add exactly one Strategic Objective selector. |
| Governance task detail | Retain layout; show the complete Plan Item table and Plan output before decisions. |
| Separate actor dashboards or sidebar work-queue entries | Remove. Use one role-aware Planning workspace, shared My Work/notifications and authorised task deep links. |
| Monitoring entry/history and custom support workspace | Retire. |
| Stitch runtime, Tailwind utilities and vendor design markup | Keep only as historical visual evidence; never import into production. |

## 11. Static Claude Design contract

This section is the complete visual input to Claude Design. It defines appearance and exact fixture content only. Behaviour, validation, permissions, service calls, routing and state transitions are defined in section 12 and shall not be added to a design prompt.

### 11.1 Closed-input rules

Supply **KT-STD-001 §2 plus this section** to Claude Design. Nothing else. The closed-input rules, product-wide prohibitions, approved desktop shell, page-header pattern, fixture-context block and division of supply are in KT-STD-001 §2.2–2.5 and are not repeated here.

**Additional prohibitions for this document:** do not show a Procuring Entity selector, row or column; do not show technical digests, record versions, idempotency keys, event IDs, audit field names or editable identifiers; and do not show Value Commitment, contract period, recommended method, generic method basis, unit price, tax, cost breakdown, Requisition creation or Tender controls. **Actual dates, planned and actual days and variance are required by column 8 of the Third Schedule and are shown where an artboard states them** — they are plan content, not operational monitoring. **Lot specifications** belong to Tender Management and are not drawn here; the plan shows only the lotting indicator and lot count.

Fixture actors, organisation units, fiscal years and units of measure come from KT-STD-001 §8, extended by §14.2 below.

### 11.2 PLN-DES-01 — Procurement Planning workspace

**Fixture context — outside the artboard:** Mercy Kilonzo · `mercy.kilonzo@moh.example.test` · Procurement Planner · FY 2027/28 · 1 Dec 2026, 09:00 EAT · Frappe header breadcrumb: **Home > Procurement Planning**

**Page content header**

- Eyebrow: **PROCUREMENT PLANNING**
- Title: **Annual procurement planning**
- Description: **Turn accepted departmental plans into a funded and approved Annual Procurement Plan.**
- No header action button

**Planning context row**

- Label **Financial Year** above a select showing **FY 2027/28**.
- Quiet value **Annual Plan · Draft Version 1** to the right.

The select uses normal editable-select styling. Do not depict it as permanently fixed, and do not add a Procuring Entity control.

**Your work card**

Heading: **Your work**

| Work item | Scope | Status | Action |
|---|---|---|---|
| Form Plan Items | 1 accepted departmental entry · KES 80,000,000 | Ready | Open Annual Plan |

**Departmental plans card**

Heading: **Departmental plans**

| Department | Version | Requirements | Value | Status | Action |
|---|---:|---:|---:|---|---|
| Digital Health | 1 | 1 | KES 80,000,000 | Accepted | View |
| Human Resources Management and Development | 1 | 2 | KES 88,000,000 | Not submitted — window closed | View |

Below the table: **2 departmental plans**. Under it show the neutral message **2 accepted Needs are not included because the departmental-plan submission window closed.** Do not show a late-submit action, summary cards, charts, waiting queues or system support links.

### 11.3 PLN-DES-02 — Draft Departmental Procurement Plan

**Fixture context — outside the artboard:** Grace Wanjiku · `grace.wanjiku@moh.example.test` · Departmental Author · OU-MOH-DHI — Digital Health · FY 2027/28 · 24 Nov 2026, 15:00 EAT · Frappe header breadcrumb: **Home > Procurement Planning > DPP-MOH-DHI-2027-001**

**Page content header**

- Eyebrow: **DEPARTMENTAL PROCUREMENT PLAN**
- Title: **Digital Health departmental plan**
- Quiet reference: **DPP-MOH-DHI-2027-001 · Version 1**
- Status badge: **Draft**
- Right-aligned secondary button: **View accepted needs**
- Right-aligned primary button: **Add direct requirement**

**Context strip**

| Label | Value |
|---|---|
| Department | OU-MOH-DHI — Digital Health |
| Financial Year | FY 2027/28 |
| Submission window | Open until 30 Nov 2026, 23:59 EAT |

**Readiness notice**

Amber notice title: **1 requirement needs funding details**

Text: **Select a Procurement Budget Line and enter the indicative amount for every requirement before the plan can be submitted.**

**Requirements table**

| Requirement | Source | Quantity | Required by | Procurement Budget Line | Indicative amount | Status | Action |
|---|---|---:|---|---|---:|---|---|
| National digital health infrastructure upgrade | Accepted Need · NDS-MOH-2027-0001 | 1 programme | 31 Aug 2027 | Not selected | — | Funding incomplete | Complete |
| Digital health platform security assessment | Direct requirement | 1 service | 31 Oct 2027 | MOH-BL-DHI-2027 | KES 20,000,000 | Ready | Edit |

Below the table: **2 requirements · KES 20,000,000 specified**.

**Sticky page footer**

- Left-aligned secondary text button: **Back to workspace**
- Right-aligned secondary button: **Save draft**
- Right-aligned disabled primary button: **Submit departmental plan**

Do not show Strategy, requirement type, funding source column, currency selector, attachment, source reference or Plan Item controls.

### 11.4 PLN-DES-03 — Accepted Need funding details

**Fixture context — outside the artboard:** Grace Wanjiku · `grace.wanjiku@moh.example.test` · Departmental Author · OU-MOH-DHI — Digital Health · FY 2027/28 · 24 Nov 2026, 15:05 EAT · Frappe header breadcrumb: **Home > Procurement Planning > DPP-MOH-DHI-2027-001 > NDS-MOH-2027-0001**

**Page content header**

- Title: **Complete funding details**
- Description: **Add the Planning-owned funding details for this accepted departmental requirement.**
- Status badge: **Accepted Need**
- No header action button

**Accepted requirement card**

Use the six Need-owned facts as read-only fields, followed by the accepted-source reference:

| Field label | Displayed value |
|---|---|
| Title | National digital health infrastructure upgrade |
| Description | Procure and implement national digital health infrastructure across priority health facilities. |
| Expected operational result | Priority health facilities can use secure and interoperable digital health services. |
| Quantity | 1 programme |
| Unit | Programme |
| Required by | 31 Aug 2027 |
| Accepted Need | NDS-MOH-2027-0001 · Version 1 |

**Planning funding card**

| Field label | Displayed value |
|---|---|
| Procurement Budget Line | MOH-BL-DHI-2027 — Digital health infrastructure programme |
| Indicative amount | 80,000,000 |
| Currency | KES |

Procurement Budget Line is a select field. Indicative amount is a money input. Currency uses the approved read-only field component.

**Sticky page footer**

- Left-aligned secondary button: **Cancel**
- Right-aligned primary button: **Save funding details**

Do not edit any Need-owned fact. Do not show Strategy, requirement type, procurement method or reservation.

### 11.5 PLN-DES-04 — Direct departmental requirement

**Fixture context — outside the artboard:** Grace Wanjiku · `grace.wanjiku@moh.example.test` · Departmental Author · OU-MOH-DHI — Digital Health · FY 2027/28 · 24 Nov 2026, 15:10 EAT · Frappe header breadcrumb: **Home > Procurement Planning > DPP-MOH-DHI-2027-001 > Add direct requirement**

**Page content header**

- Title: **Add direct requirement**
- Description: **Add a requirement the department already knows it needs to procure.**
- Status badge: **New**
- No header action button

**Context card**

| Field label | Displayed value |
|---|---|
| Department | OU-MOH-DHI — Digital Health |
| Financial Year | FY 2027/28 |

All three rows use the approved read-only field component.

**Requirement card**

| Field label | Displayed value |
|---|---|
| Title | Digital health platform security assessment |
| Description | Assess the security of the national digital health platform and provide a prioritised remediation report. |
| Expected operational result | The Ministry receives a prioritised and actionable security remediation plan. |
| Quantity | 1 |
| Unit | Service |
| Required by | 31 Oct 2027 |

Title is a single-line input. Description and Expected operational result are multiline inputs. Quantity and Unit appear side by side; Required by appears below them.

**Funding card**

| Field label | Displayed value |
|---|---|
| Procurement Budget Line | MOH-BL-DHI-2027 — Digital health infrastructure programme |
| Indicative amount | 20,000,000 |
| Currency | KES |

Procurement Budget Line is a select field. Indicative amount is a money input. Currency is read-only.

**Sticky page footer**

- Left-aligned secondary button: **Cancel**
- Right-aligned primary button: **Add requirement**

Do not show Need, bypass reason, Strategy, requirement type, procurement method, attachment, source reference, funding source selector or reservation.

### 11.6 PLN-DES-05 — HoD departmental-plan submission

**Fixture context — outside the artboard:** Dr Peter Kimani · `peter.kimani@moh.example.test` · Head of User Department · OU-MOH-DHI — Digital Health · FY 2027/28 · 25 Nov 2026, 09:55 EAT · Frappe header breadcrumb: **Home > Procurement Planning > DPP-MOH-DHI-2027-001**

Use PLN-DES-02 page geometry with these exact differences:

- Status badge: **Ready to submit**
- No readiness notice
- Both table rows show status **Ready**
- First row Procurement Budget Line: **MOH-BL-DHI-2027**
- First row Indicative amount: **KES 80,000,000**
- Below the table: **2 requirements · KES 100,000,000**
- Right-aligned primary button: **Submit departmental plan**

Below the table, show a bordered certification card:

Heading: **Departmental certification**

Text: **I certify that this Departmental Procurement Plan contains the current procurement requirements of Digital Health for FY 2027/28, including every current accepted Departmental Need and any direct departmental requirements shown. I confirm that the quantities, required-by dates, Procurement Budget Lines and indicative amounts are ready for Procurement validation and inclusion in the Annual Procurement Plan.**

Checkbox label: **I confirm this certification**

Do not show an Accounting Officer recipient, classification, Strategy, approval route or generic comments field.

### 11.7 PLN-DES-06 — DPP validation task

**Fixture context — outside the artboard:** Mercy Kilonzo · `mercy.kilonzo@moh.example.test` · Procurement Planner · FY 2027/28 · 27 Nov 2026, 13:45 EAT · Frappe header breadcrumb: **Home > Procurement Planning > DPP review > DPP-MOH-DHI-2027-001**

**Page content header**

- Eyebrow: **DEPARTMENTAL PLAN REVIEW**
- Title: **Validate Digital Health departmental plan**
- Quiet reference: **DPP-MOH-DHI-2027-001 · Submitted Version 1**
- Status badge: **Awaiting validation**
- No header action button

**Submission context card**

| Label | Value |
|---|---|
| Department | Digital Health |
| Financial Year | FY 2027/28 |
| Submitted by | Dr Peter Kimani |
| Submitted | 25 Nov 2026, 10:00 EAT |
| Requirements | 2 |
| Total indicative value | KES 100,000,000 |

**Submitted requirements table**

| Requirement | Source | Quantity | Required by | Procurement Budget Line | Amount | Requirement type | Action |
|---|---|---:|---|---|---:|---|---|
| National digital health infrastructure upgrade | Accepted Need · NDS-MOH-2027-0001 | 1 programme | 31 Aug 2027 | MOH-BL-DHI-2027 | KES 80,000,000 | Non-consulting services | View |
| Digital health platform security assessment | Direct requirement | 1 service | 31 Oct 2027 | MOH-BL-DHI-2027 | KES 20,000,000 | Consulting services | View |

Requirement type uses an inline select in each row. All other cells are read-only.

**Departmental certification card**

Show the exact certification text from PLN-DES-05, followed by **Certified by Dr Peter Kimani · 25 Nov 2026, 10:00 EAT**.

**Decision footer**

- Left-aligned secondary button: **Return to department**
- Right-aligned primary button: **Accept departmental plan**

Do not show editable requirement facts, editable Budget data, Strategy, Finance confirmation, AO decision, score, checklist or generic note.

### 11.8 PLN-DES-07 — Draft Annual Procurement Plan

**Fixture context — outside the artboard:** Mercy Kilonzo · `mercy.kilonzo@moh.example.test` · Procurement Planner · FY 2027/28 · 1 Dec 2026, 09:10 EAT · Frappe header breadcrumb: **Home > Procurement Planning > PLN-MOH-2027-001**

**Page content header**

- Eyebrow: **ANNUAL PROCUREMENT PLAN**
- Title: **Ministry of Health Annual Procurement Plan 2027/28**
- Quiet reference: **PLN-MOH-2027-001 · Version 1**
- Status badge: **Draft**
- Right-aligned primary button: **Form Plan Items**

**Plan summary strip**

| Label | Value |
|---|---|
| Accepted departmental entries | 1 |
| Allocated | 0 |
| Plan Items | 0 |
| Plan value | KES 0 |
| Reserved share | 0% of plan value · target 30% |

**Unallocated sources card**

Heading: **Accepted departmental entries**

| Requirement | Department | Source origin | Classification | Quantity | Procurement Budget Line | Amount | Status |
|---|---|---|---|---:|---|---:|---|
| National digital health infrastructure upgrade | Digital Health | Accepted Departmental Need | Non-consulting services | 1 programme | MOH-BL-DHI-2027 | KES 80,000,000 | Unallocated |

Below the table: **1 entry available**.

**Plan Items card**

Heading: **Plan Items**

Empty-state title: **No Plan Items yet**

Empty-state text: **Form Plan Items from the accepted departmental entries above.**

**Plan readiness card**

Heading: **Plan readiness**

| Check | Result |
|---|---|
| Every Plan Item has a Strategic Objective | Not started |
| Every Plan Item has a reservation category | Not started |
| Procurement method admissible for value | Not started |
| Plan within approved budget | Not started |
| Plan funding confirmed | Not started |
| Preference and reservation target | 0% of plan value reserved · target 30% |
| Contract splitting review | No advisory |

The first five rows use the approved neutral state badge. The sixth row uses the approved advisory state treatment. The seventh uses the approved neutral badge.

**Sticky page footer**

- Left-aligned secondary button: **Back to workspace**
- Right-aligned disabled secondary button: **Request plan funding confirmation**
- Right-aligned disabled primary button: **Submit consolidated Plan**

Do not show charts, creation of a blank Plan Item, per-item Finance controls or approval controls.

### 11.9 PLN-DES-08 — Form Plan Items dialog

**Fixture context — outside the artboard:** Mercy Kilonzo · `mercy.kilonzo@moh.example.test` · Procurement Planner · FY 2027/28 · 1 Dec 2026, 09:12 EAT · Frappe header breadcrumb: **Home > Procurement Planning > PLN-MOH-2027-001**

Use PLN-DES-07 as a dimmed background.

**Dialog**

- Title: **Form Plan Items**
- Intro: **Select accepted departmental entries and choose how they should form procurement packages.**

**Source table**

| Select | Requirement | Department | Classification | Quantity | Amount |
|---|---|---|---|---:|---:|
| Checked | National digital health infrastructure upgrade | Digital Health | Non-consulting services | 1 programme | KES 80,000,000 |

**Formation choice**

Selected radio: **Create one Plan Item for each selected requirement**

Unselected radio: **Create one combined Plan Item from all selected requirements**

**Result preview**

| Label | Value |
|---|---|
| Selected entries | 1 |
| Plan Items to create | 1 |
| Total value | KES 80,000,000 |

**Dialog footer**

- Secondary button: **Cancel**
- Primary button: **Create 1 Plan Item**

Do not show a source search, partial quantity, amount override, lot split, Strategy, method, Finance or generic note.

### 11.10 PLN-DES-09 — Plan Item editor

**Fixture context — outside the artboard:** Mercy Kilonzo · `mercy.kilonzo@moh.example.test` · Procurement Planner · FY 2027/28 · 3 Dec 2026, 14:00 EAT · Frappe header breadcrumb: **Home > Procurement Planning > PLN-MOH-2027-001 > PPI-MOH-2027-021**

**Page content header**

- Eyebrow: **PLAN ITEM**
- Title: **National digital health infrastructure upgrade**
- Quiet reference: **PPI-MOH-2027-021 · Draft Version 1**
- Status badge: **Proposed**
- No header action button

**Source card**

Heading: **Departmental source**

| Label | Value |
|---|---|
| Department | Digital Health |
| Source origin | Accepted Departmental Need |
| Departmental plan | DPP-MOH-DHI-2027-001 · Version 1 |
| Accepted Need | NDS-MOH-2027-0001 · Version 1 |
| Quantity | 1 programme |
| Required by | 31 Aug 2027 |
| Procurement Budget Line | MOH-BL-DHI-2027 — Digital health infrastructure programme |
| Planned value | KES 80,000,000 |

All source rows are read-only.

**Procurement package card**

| Field label | Displayed value |
|---|---|
| Plan Item title | National digital health infrastructure upgrade |
| Procurement description | Procure and implement the national digital health infrastructure upgrade as one integrated FY 2027/28 programme. |
| Requirement type | Non-consulting services |
| Strategic Objective | OBJ-MOH-2023-001 — Strengthen interoperable national digital health services |
| Objective path | Digital health systems › Health policy, standards and regulation › Digital health governance |
| Procurement method | Open Tender |
| Value band | Above KES 5,000,000 · Open Tender admissible |
| Preference and reservation | None |

Title and Procurement description are editable. Strategic Objective and Preference and reservation are select fields. Requirement type, Objective path, Procurement method and Value band are read-only.

Quiet helper text beneath **Preference and reservation**: **Recorded for the entity's 30% target. Choose None only where no reservation applies.**

Quiet helper text beneath the **Planned value** row of the Source card: **Market price index: not published for this category.**

**Planned schedule card**

Use a two-column field grid with these exact dates:

| Field label | Displayed value |
|---|---|
| Invitation or advertisement | 1 May 2027 |
| Bid opening | 23 May 2027 |
| Evaluation completion | 23 Jun 2027 |
| Tender award approval | 10 Jul 2027 |
| Notification of award | 14 Jul 2027 |
| Contract signing | 1 Aug 2027 |
| Delivery or implementation completion | 31 Aug 2027 |

**Sticky page footer**

- Left-aligned secondary text button: **Back to Annual Plan**
- Left-aligned secondary button: **Dissolve Plan Item**
- Right-aligned primary button: **Save draft**

Do not show a Finance action, a funding-confirmation button, a reservation, Value Commitment, contract period, lotting, recommended method, method basis, actual dates, attachment or source edit. Funding confirmation is requested once for the whole Plan Version from PLN-DES-07, never from a Plan Item.

### 11.11 PLN-DES-09A — Combined Plan Item editor

**Fixture context — outside the artboard:** Mercy Kilonzo · `mercy.kilonzo@moh.example.test` · Procurement Planner · FY 2027/28 · 3 Dec 2026, 15:00 EAT · Frappe header breadcrumb: **Home > Procurement Planning > PLN-MOH-2027-001 > PPI-MOH-2027-033**

Use PLN-DES-09 page geometry with these exact replacements:

- Title: **Clinical training and deployment laptops for digital health rollout**
- Quiet reference: **PPI-MOH-2027-033 · Draft Version 1**

Replace the single source card with **Departmental sources**:

| Requirement | Department | Source origin | Quantity | Required by | Procurement Budget Line | Amount |
|---|---|---|---:|---|---|---:|
| Clinical training laptops for digital health rollout | Human Resources Management and Development | Accepted Departmental Need | 200 each | 31 Dec 2027 | MOH-BL-HWD-2027 | KES 48,000,000 |
| Clinical deployment laptops for digital health rollout | Digital Health | Accepted Departmental Need | 300 each | 31 Dec 2027 | MOH-BL-DHI-2027 | KES 72,000,000 |

Below the table: **2 sources · 500 each · KES 120,000,000**.

**Procurement package card**

| Field label | Displayed value |
|---|---|
| Plan Item title | Clinical training and deployment laptops for digital health rollout |
| Procurement description | Procure one standard laptop specification and deployment service for the national digital-health rollout across both source departments. |
| Requirement type | Goods |
| Strategic Objective | OBJ-MOH-2023-001 — Strengthen interoperable national digital health services |
| Objective path | Digital health systems › Health policy, standards and regulation › Digital health governance |
| Procurement method | Open Tender |
| Aggregation reason | Procure one standard laptop specification and deployment service for the same national digital-health rollout. |

Use the same schedule card and footer layout as PLN-DES-09, with delivery completion **31 Dec 2027**. Do not show source detachment, partial allocation, different treatment per source or a generic reason field.

### 11.12 PLN-DES-10 — Plan funding confirmation task

**Fixture context — outside the artboard:** Josphat Mwangi · `josphat.mwangi@moh.example.test` · Finance Confirmation Officer · FY 2027/28 · 4 Dec 2026, 09:58 EAT · Frappe header breadcrumb: **Home > Procurement Planning > Finance > FNT-MOH-2027-001**

**Page content header**

- Eyebrow: **PLAN FUNDING CONFIRMATION**
- Title: **Ministry of Health Annual Procurement Plan 2027/28**
- Quiet reference: **FNT-MOH-2027-001 · PLN-MOH-2027-001 · Version 1**
- Status badge: **Awaiting Finance**
- No header action button

**Plan summary card**

| Label | Value |
|---|---|
| Plan Items | 1 |
| Plan value | KES 80,000,000 |
| Procurement Budget Lines used | 1 |
| Reserved share | 0% of plan value · target 30% |

**Affordability table**

As-at line: **Position as at 4 Dec 2026, 09:58 EAT**

| Procurement Budget Line | Funding source | Approved | Planned in this Plan | Within approved | Reserved | Committed | Currently available |
|---|---|---:|---:|---|---:|---:|---:|
| MOH-BL-DHI-2027 — Digital health infrastructure programme | Government of Kenya | KES 100,000,000 | KES 80,000,000 | Yes | KES 0 | KES 0 | KES 100,000,000 |
| MOH-BL-HWD-2027 — Digital health workforce development | Government of Kenya | KES 60,000,000 | KES 0 | Yes | KES 0 | KES 0 | KES 60,000,000 |

Green notice: **The consolidated plan is within the approved budget on every Procurement Budget Line.**

Quiet line beneath the notice: **Confirmation records that this plan fits the approved budget. It reserves no funds; reservation happens at requisition.**

**Decision footer**

- Left-aligned secondary button: **Return to planner**
- Right-aligned primary button: **Confirm plan funding**

Do not show a per-item confirmation, a Plan Item list, editable amounts, Procurement Budget Line changes, an optional note, a reservation, an "available after confirmation" column, Plan approval or Budget-maintenance controls.

### 11.13 PLN-DES-11 — Accounting Officer adoption

**Fixture context — outside the artboard:** Amina Hassan · `amina.hassan@moh.example.test` · Accounting Officer · FY 2027/28 · 8 Dec 2026, 09:55 EAT · Frappe header breadcrumb: **Home > Procurement Planning > Accounting Officer adoption > PLN-MOH-2027-001-V1**

**Page content header**

- Eyebrow: **ACCOUNTING OFFICER ADOPTION · PLN-MOH-2027-001 · VERSION 1**
- Title: **Ministry of Health Annual Procurement Plan 2027/28**
- Status badge: **Awaiting Accounting Officer**

**Immutable Plan table**

| Plan Item | Department | Source origin | Quantity | Strategic Objective | Method | Value | Completion | Finance |
|---|---|---|---:|---|---|---:|---|---|
| PPI-MOH-2027-021 · National digital health infrastructure upgrade | Digital Health | Accepted Departmental Need | 1 programme | OBJ-MOH-2023-001 — Strengthen interoperable national digital health services | Open Tender | None | KES 80,000,000 | 31 Aug 2027 | Within budget |

Insert a **Reservation** column between **Method** and **Value** in the header row, so the header reads: Plan Item · Department · Source origin · Quantity · Strategic Objective · Method · Reservation · Value · Completion · Funding.

Below the table: **1 Plan Item · KES 80,000,000**. Beneath that line, one advisory row: **Reserved share 0% of plan value · target 30%. No contract splitting advisory.** Do not collapse the Plan into summary cards.

**Decision statement:** **I adopt the complete consolidated Annual Procurement Plan Version 1 shown above and submit it for the statutory approval applicable to this Procuring Entity.**

**Sticky page footer**

- Left-aligned secondary button: **Return for correction**
- Right-aligned primary button: **Adopt and submit**

Do not show professional review, Head of Procurement Function approval, editable Plan content, optional comments or publication controls.

### 11.14 PLN-DES-12 — Statutory approval

**Fixture context — outside the artboard:** MOH statutory approver · `moh.plan.approver@example.test` · Responsible Cabinet Secretary · FY 2027/28 · 9 Dec 2026, 10:55 EAT · Frappe header breadcrumb: **Home > Procurement Planning > Statutory approval > PLN-MOH-2027-001-V1**

**Page content header**

- Eyebrow: **STATUTORY APPROVAL · PLN-MOH-2027-001 · VERSION 1**
- Title: **Ministry of Health Annual Procurement Plan 2027/28**
- Status badge: **Awaiting statutory approval**

**Authority card**

- Capacity: **Responsible Cabinet Secretary**
- Accounting Officer adoption: **Amina Hassan · 8 Dec 2026, 10:00 EAT**

Show the exact immutable Plan table and total defined in PLN-DES-11. For a Board or similar body, replace the individual capacity row with **Governing body** and require **Resolution reference** before approval.

**Sticky page footer**

- Left-aligned secondary button: **Return for correction**
- Right-aligned primary button: **Approve Annual Procurement Plan**

This is the only approval after Accounting Officer adoption. Do not show another approver, committee, professional recommendation or publication approval.

### 11.15 PLN-DES-13 — Publication result

Show the exact approved Version, destination, last attempt, result and acknowledgement reference read-only. Publication starts as a system action after approval. No business-role Publish button exists. When a retry is technically required, only System Manager sees **Retry exact approved payload**; the control cannot edit the destination or payload and creates no new approval.

### 11.16 PLN-DES-14 — Active Annual Procurement Plan

**Fixture context — outside the artboard:** Mercy Kilonzo · `mercy.kilonzo@moh.example.test` · Procurement Planner · FY 2027/28 · 10 Dec 2026, 15:05 EAT · Frappe header breadcrumb: **Home > Procurement Planning > PLN-MOH-2027-001**

**Page content header**

- Eyebrow: **ANNUAL PROCUREMENT PLAN**
- Title: **Ministry of Health Annual Procurement Plan 2027/28**
- Quiet reference: **PLN-MOH-2027-001 · Version 1**
- Status badge: **Active**
- Right-aligned primary button: **Prepare plan update**

**Plan summary strip**

| Label | Value |
|---|---|
| Plan Items | 1 |
| Approved value | KES 80,000,000 |
| Departments | 1 |
| Activated | 10 Dec 2026, 15:00 EAT |

**Plan Items table**

| Plan Item | Department | Source origin | Strategic Objective | Method | Completion | Value | Requisition availability | Action |
|---|---|---|---|---|---|---:|---|---|
| PPI-MOH-2027-021 · National digital health infrastructure upgrade | Digital Health | Accepted Departmental Need | Strengthen interoperable national digital health services | Open Tender | 31 Aug 2027 | KES 80,000,000 | 1 programme · KES 80,000,000 | View |

**Adoption, approval and publication card**

| Label | Value |
|---|---|
| Accounting Officer adoption | Amina Hassan · 8 Dec 2026, 10:00 EAT |
| Statutory approval | Responsible Cabinet Secretary · 9 Dec 2026, 11:00 EAT |
| Publication | Acknowledged · 10 Dec 2026, 15:00 EAT |

Do not show monitoring entry, create Requisition, create Tender, editable Plan fields other than the actual-date fields stated, chart or generic evidence table.

### 11.17 PLN-DES-15 — Return dialogs

Produce two separate dialog artboards over their corresponding dimmed task pages.

**Accounting Officer return**

- Title: **Return Plan Version for correction?**
- Intro: **The submitted Version 1 remains unchanged. State the correction required.**
- Required multiline label: **Correction required**
- Exact value: **Confirm the planned contract-signing date against the delivery completion date.**
- Footer buttons: **Cancel** and **Return for correction**

**Statutory-approval return**

- Title: **Return adopted Plan Version for correction?**
- Intro: **The Accounting-Officer-adopted Version 1 remains unchanged. State the correction required.**
- Required multiline label: **Correction required**
- Exact value: **Correct the procurement package description before the Plan is resubmitted.**
- Footer buttons: **Cancel** and **Return for correction**

Do not add a reason category, attachment, assignee, due date, optional note or editing controls.

### 11.18 PLN-DES-16 — Common page states

Use the approved KenTender empty, error and unavailable components with these exact variants:

| State | Heading | Text | Control |
|---|---|---|---|
| No authorised context | Procurement Planning is not available | You do not have an assigned Procuring Entity scope, or no configured Financial Year is available for Planning. | None |
| No departmental plan | No departmental plan yet | Open the departmental plan to review accepted Needs or add a direct requirement. | Open departmental plan |
| No validation tasks | No departmental plans awaiting validation | New submissions will appear here. | None |
| No accepted sources | No accepted departmental entries | Accepted departmental entries will appear here automatically. | None |
| Finance shortfall | Funding is insufficient | The required amount exceeds the current available amount on at least one Procurement Budget Line. No reservation has been created. | Return to planner |
| Publication failed | Publication was not acknowledged | The approved Plan is unchanged. Retry the same publication when the destination is available. | Retry publication |
| Load error | Procurement Planning could not be loaded | Try again. If the problem continues, quote the support reference shown below. | Try again |

Only the load-error component may display a generated support reference. Do not add diagnostic text, illustrations or alternative actions.

## 12. Functional interaction requirements — excluded from design prompts

### 12.1 PLN-UI-01 — Procurement Planning workspace

- Resolve authorised PE/OU scope and matching responsibility assignment from the shared AUTH resolver. Derive Financial Year options from configured records and operation windows; do not assign FY to the user. No client value grants access.
- One eligible PE or FY loads directly. Several are shown in visible, changeable Planning selectors. A user may change Financial Year at any time; choosing a future year does not permanently bind later visits.
- Store the last valid Planning selection as a server-side user preference only. Treat local storage as an optional cache, never as authority. Invalid or inaccessible cached values are discarded and the user can select again.
- A direct task or record route resolves context from the record, reauthorises it and displays it. It never requires a prior selector choice.
- The action queue contains only tasks the actor may decide now. Waiting work is neutral read-only information and never exposes disabled protected controls.
- Workspace counts and rows use the same database scope and snapshot.
- Opening the workspace or switching context creates no Planning record.
- A departmental user sees their DPP work, a Procurement Planner sees submitted DPP tasks, a Planner sees accepted sources and Plan work, a Budget Officer sees Finance tasks, and each governance actor sees only their exact task.
- No role receives a separate sidebar work-queue menu. The sole **Procurement Planning** entry, shared **My Work** and notifications link to the same authorised tasks.
- Search and counts never disclose another PE, FY, OU, task or Plan.

### 12.2 PLN-UI-02 — Departmental Plan

- **Open departmental plan** calls the explicit guarded command; subsequent reads reuse the one root and Draft Version.
- Project every current accepted Need in the exact Fiscal Year and Organisation Unit once. Its six facts remain read-only.
- **Complete** opens PLN-UI-03 for a Need-origin entry. **Add direct requirement** opens PLN-UI-04. **Edit** opens the current direct entry only.
- Draft save permits incomplete funding. Submission requires all entries complete, every current accepted Need covered once, every direct entry valid and at least one entry in total.
- Only direct entries can be removed from a Draft. A current accepted Need cannot be omitted or locally deleted.
- Source successor, withdrawal and Procurement Budget Line changes are rechecked on every save and submission.
- If the initial Version was withdrawn without an accepted predecessor, **Open departmental plan** creates the next numbered Draft only while the original submission window is Open. It never revives or edits the withdrawn Version.
- Initial HoD submission requires the exact certification checkbox, an active Head of User Department assignment covering the DPP's OU and an Open window. An acting HoD uses the same responsibility through a dated Acting assignment. A returned correction or source-change successor requires the same certification and authority but may be resubmitted after the initial window closes. The certification text is server supplied, not client composed.
- A successful submission routes to immutable submitted detail. The submitter sees neutral status while the Procurement Planner acts.
- A returned submission loads the copied correction Draft and displays each structured issue next to its affected entry.

### 12.3 PLN-UI-03 — Accepted Need funding details

- Load the exact accepted Need version fixed by the DPP entry and display all six source facts read-only.
- Procurement Budget Line options come only from `ListEligibleBudgetLines` for the exact Fiscal Year and Organisation Unit.
- Selecting a line refreshes its currency and approved line amount for context; it does not display or promise live availability.
- Save accepts only Procurement Budget Line and positive indicative amount. Direct URL or payload attempts to alter Need facts are rejected.
- Save creates no reservation, commitment or Budget mutation.
- If the Need version is no longer current, save is blocked and the DPP refresh path is shown.

### 12.4 PLN-UI-04 — Direct requirement editor

- A new direct entry exists only after a successful save command; opening or cancelling the blank editor creates nothing.
- Save accepts exactly title, description, expected operational result, quantity, unit, required-by, Procurement Budget Line and indicative amount.
- Unit options come only from enabled ERPNext `UOM` records; Procurement Budget Lines come from the eligible Budget contract.
- Required-by must fall inside the selected FY. Amount and quantity must be positive.
- Save creates no Need, bypass reason, reservation or Strategy link.
- A submitted, accepted or another department's entry is never editable through a direct URL.

### 12.5 PLN-UI-05 — HoD submission

- Recalculate readiness from current authoritative sources when the page loads and again inside the submit transaction.
- Certification is available only to a substantive or acting HoD with an active role-bound assignment whose OU subtree contains the DPP. The DPP's Financial Year must be eligible under the current Planning window and record state; it is not an assignment dimension.
- Submission locks one immutable snapshot and creates one validation task atomically.
- A repeated command with the same idempotency key returns the original submission and task.
- A concurrent source, Procurement Budget Line or DPP change returns `PLN_DPP_STALE` and creates no partial submission.

### 12.6 PLN-UI-06 — DPP validation task

- Load the exact immutable DPP submission and all submitted entry details before any decision controls.
- Requirement-type options come from the governed active catalogue. Classification does not edit the submitted source row.
- **Accept departmental plan** requires one classification for every entry, current source versions, no unresolved issue and maker-checker compliance.
- **Return to department** opens a structured issue dialog. At least one issue with affected entry, concise problem and correction required is mandatory.
- Decision commands recheck task token, assignment, state, sources and segregation under one transaction.
- Acceptance completes the task and places every accepted entry in the open Draft Annual Plan as an unallocated source. If this is the first accepted DPP for the Fiscal Year, the same transaction inserts the uniquely constrained Annual Plan root and Draft Version 1. If a concurrent acceptance won that insert, the command reloads and reuses the winner inside the transaction. It does not form a Plan Item, reserve funds or approve expenditure.
- Return completes the task, preserves the submission and creates the correction Draft atomically.

### 12.7 PLN-UI-07 and PLN-UI-08 — Annual Plan workbench and formation

- There is no **Begin consolidation** command, page or permission gate. The initial Draft Annual Plan already exists after the first DPP acceptance.
- Each later DPP accepted before the initial Plan is submitted adds its entries automatically to the same Draft Version's unallocated-source queue.
- The Planner may form Plan Items incrementally and does not wait for the submission window to close, every department to submit or a department to declare a nil plan.
- A DPP accepted after the current Plan Version has been submitted cannot alter that immutable Version and does not interrupt its governance. Its entries appear as **Pending addition** in the workspace and become available in the next Draft successor after the current Version is activated.
- A DPP successor that replaces a source already allocated to a mutable Draft item marks that item **Source correction required**. It does not rewrite or move the allocation. The Planner must dissolve and re-form the item from the current source.
- Source selection lists only current accepted entries in the exact Fiscal Year that are not already allocated in the open Version.
- One selected source creates one Plan Item without asking for an unnecessary second choice.
- Several selected sources require **one each** or **one combined**. Combined formation requires the same Fiscal Year, Procurement Budget Line, currency, requirement type, unit and treatment plus a complete aggregation reason before the item is ready.
- Formation is atomic and idempotent. A unique active allocation prevents concurrent duplicate use.
- A single created item opens its editor. Several separately created items return to the workbench.
- The Planner never creates a blank source-less Plan Item.
- Draft summary counts, value and blockers are derived from source allocations and current item states.
- **Dissolve Plan Item** appears only for an item in a mutable Draft Version. Confirmation states that its sources will return to the unallocated list and any effective funding hold will be released. The server completes cancellation, release and allocation updates atomically or changes nothing.

### 12.8 PLN-UI-09 — Plan Item editor

- Load an existing formed item and every allocation read-only. Source selection, regrouping and partial allocation are absent; regrouping is done by dissolving the Draft item and forming again.
- For a single source, default title from the source. For combined sources, require a Planner-entered package title and aggregation reason.
- Strategic Objective options are only current eligible Active Objectives and show title plus hierarchy path.
- The server assigns Open Tender as the sole admitted MVP method. It is displayed read-only and the UI does not present a one-option selector.
- Save accepts only title, description, Strategic Objective, aggregation reason when combined and seven planned dates.
- Requirement type, quantity, unit, source details, Procurement Budget Lines and planned value are derived and read-only.
- Schedule validation binds each failure to the exact date control and explains the chronological or required-by conflict.
- **Save draft** creates no Finance task. **Request Finance confirmation** saves and fully validates in one transaction, then creates/reuses one current task.
- A change to the source set, Procurement Budget Line, amount or currency after Finance confirmation releases the affected Draft reservation remainder, marks Finance Stale and requires new confirmation. A title, description, Objective, aggregation reason, method or schedule edit retains the reservation but it is revalidated before Plan submission. No reservation is silently adjusted.

### 12.9 PLN-UI-10 — Plan funding confirmation task

- One task exists per Plan Version. There is no per-item Finance task, queue or route.
- Authorise the task and the actor's Finance Confirmation Officer assignment before returning any protected position.
- Recompute the affordability statement at command time; the displayed As-at time must match the snapshot.
- **Confirm plan funding** is available only when every Procurement Budget Line is within its approved amount. The command re-checks under lock and records the decision with the statement as it stood.
- A line over its approved amount omits Confirm and returns `PLN_PLAN_NOT_AFFORDABLE` with every failing line and its exact excess.
- Falling below currently available is displayed and blocks nothing.
- **Return to planner** requires one actionable correction reason.
- Confirmation creates no reservation, no ledger event and no Budget record. The screen shows no "available after confirmation" figure, because nothing is held.
- The task contains no editable amount, Procurement Budget Line, Plan field or optional note.
- Navigation to Budget & Funding preserves the Planning task and creates no mutation in either module.

### 12.10 PLN-UI-11 and PLN-UI-12 — Annual Plan decisions

- Each task loads the exact immutable submitted Plan Version and displays every Plan Item, source summary, Strategic Objective, method, completion date, value and Finance result before decision controls.
- The Accounting Officer may adopt and submit the complete Plan or return it for correction.
- Adoption creates exactly one statutory-approval task resolved from governed PE type and jurisdiction.
- The statutory authority may approve the Accounting-Officer-adopted Plan or return it for correction.
- For a Board or similar body, approval records the collective decision and mandatory resolution reference; the data-entry user is not represented as the sole authority.
- Every return requires one actionable correction. No reason category or optional note exists.
- Every decision rechecks the exact role-bound responsibility or legal capacity, matching assignment, task token, source currency, Objective eligibility and Finance freshness.
- No Head of Procurement Function, professional reviewer, generic committee or publication approval is inserted.
- A return preserves the submitted snapshot and creates a copied correction Draft containing only that snapshot's sources. Pending DPP additions remain outside it.
- Corrected submission revalidates every reservation. It repeats Finance only for an item whose source set, Procurement Budget Line, amount or currency changed, whose reservation is absent, released or `Needs Attention`, or whose Budget revalidation fails.
- Every corrected submission creates a new immutable snapshot and restarts at Accounting Officer adoption, including a correction returned from statutory approval.

### 12.11 PLN-UI-13 — Publication

- After statutory approval, the system serialises and transmits the exact approved Plan through the configured adapter.
- Acknowledgement activates the Version and supersedes the predecessor where applicable.
- Failed or indeterminate transmission preserves approval and permits an idempotent technical retry of the same payload by System Manager.
- There is no manual acknowledgement, payload edit, successful-result override or business publication decision.

### 12.12 PLN-UI-14 — Active Plan and successor

- Display the Active Version and its complete item baseline read-only.
- Requisition availability is a live neutral projection, not a Planning edit control.
- **Prepare plan update** creates/reuses the sole Draft successor after authority and state checks.
- The Active predecessor remains operational while the successor is Draft, returned or under governance.
- An item may be proposed for whole-item removal only after fresh downstream checks show no drawdown, Tender handoff, commitment or contract.
- Cancelling a Draft successor releases only successor-created reservations and leaves the Active predecessor unchanged.
- An acknowledged successor atomically becomes the sole Active Version; unchanged lineage is preserved, removed items cease future eligibility and their unconverted reservation remainder is released only after the downstream-use checks pass.
- Planning displays later downstream status only from authoritative projections. It does not collect actual milestone dates.

### 12.13 Common page behaviour and accessibility

- Use semantic headings, labels, tables, status text and keyboard-operable controls. Colour is never the only state carrier.
- Dialog focus is trapped and restored. Validation focus moves to the first invalid control or error summary.
- Buttons are disabled while their command is pending and reuse one idempotency key on retry.
- All dates display in `Africa/Nairobi`; service and audit instants remain UTC.
- Do not wait for `networkidle` on Frappe Desk pages. Browser tests wait for DOM content plus an exact page-ready selector.
- Route changes unmount the Vue app and cancel stale requests. Returning to a cached Desk page re-resolves context and authority.
- Direct links enforce the same scope as list reads and return Not found when existence disclosure is unauthorised.

## 13. Audit and historical integrity

The audit record shall preserve:

- DPP Draft creation, direct-entry changes and accepted-Need projection changes;
- each DPP submission, certification actor/assignment, submitted rows, validation classification and return/accept decision;
- Annual Plan and Version creation, each source allocation, dissolution, source-correction flag and every Planner field change;
- Finance task iterations, Budget snapshots used for decisions, reservation references, revalidation and release results;
- each Accounting Officer and statutory-approval task and immutable decision;
- publication attempts, adapter results, acknowledgement and activation;
- successor creation, whole-item removal proposal, cancellation and supersession; and
- Requisition drawdown references received from the owning module.

Audit uses framework timestamps and actor fields plus immutable decision records. It does not add editable `created by`, `approved by`, `evidence`, `history note` or `source reference` fields to business forms.

No submitted DPP, accepted classification, submitted Plan snapshot, Finance decision, reservation reference, governance decision, publication attempt, Active Version or Superseded Version may be edited or deleted through product commands.

## 14. Deterministic seed contract

### 14.1 Configuration prerequisites

| Fixture | Exact value |
|---|---|
| ERPNext Fiscal Year | `2027-2028` — displayed FY 2027/28 · 1 Jul 2027 to 30 Jun 2028 |
| OU 1 | `OU-MOH-DHI` — Digital Health |
| OU 2 | `OU-MOH-HRMD` — Human Resources Management and Development |
| Unit 1 | ERPNext `UOM` **Programme**, enabled |
| Unit 2 | ERPNext `UOM` **Each**, enabled |
| Unit 3 | ERPNext `UOM` **Service Month**, enabled |
| Procurement categories | Goods; Works; Services |
| Requirement types | Non-consulting services; Consulting services; Goods; Works |
| Procurement methods | Open Tender; Request for Quotations; Low Value Procurement |
| Threshold matrix | Effective for FY 2027/28, taken from the Second Schedule. Low value procurement: max KES 50,000 goods, KES 100,000 works, KES 50,000 services, **per item per financial year**. Request for quotations: max KES 3,000,000 goods, KES 5,000,000 works, KES 3,000,000 services, per request. Restricted tender under section 102(1)(b): max KES 30,000,000 goods, KES 30,000,000 works, KES 20,000,000 services. Open tender, request for proposals and the remaining restricted-tender limbs: no minimum, maximum determined by the funds allocated in the budget for the particular procurement. Direct procurement: no minimum or maximum, subject to the section 103 conditions. |
| Exclusive preference thresholds | Regulation 163: KES 1,000,000,000 for works, construction materials and other materials made in Kenya; KES 500,000,000 for goods and services. |
| Reservation categories | None; Youth; Women; Persons with disabilities; Micro and small enterprise |
| Reservation target | 30% of planned value, effective for FY 2027/28 |
| Market price index | Not published for the seeded categories |
| DPP submission window | 1 Oct 2026, 00:00 EAT to 30 Nov 2026, 23:59:59 EAT inclusive |
| Publication destination | KenTender Annual Plan Publication Sandbox · `MOH-APP-SANDBOX-v1` |
| Design clock | Exact time stated on each artboard |

The site Procuring Entity is configured once by CFG-CHG-002 v0.6 and is never a seed input here. Seeds fail when an authoritative prerequisite is absent or differs. They do not invent a Fiscal Year, Organisation Unit, unit of measure, Procurement Budget Line, Objective or assignment.

### 14.2 Actors and assignments

| Actor | Exact assignment |
|---|---|
| `grace.wanjiku@moh.example.test` · Grace Wanjiku | Two Departmental Author assignments: OU-MOH-DHI and OU-MOH-HRMD |
| `peter.kimani@moh.example.test` · Dr Peter Kimani | Permanent Head of User Department assignment for OU-MOH-HRMD; DHI assignment ending 25 Nov 2026 and a successor DHI assignment starting 1 Dec 2026 |
| `julia.njeri@moh.example.test` · Julia Njeri | Acting Head of User Department assignment for OU-MOH-DHI from 26 to 30 Nov 2026 with authority reference |
| `mercy.kilonzo@moh.example.test` · Mercy Kilonzo | Site-wide Procurement Planner; DPP classification and Annual Plan preparation |
| `josphat.mwangi@moh.example.test` · Josphat Mwangi | Site-wide Finance Confirmation Officer; the exact task and Budget service eligibility narrow the named lines |
| `amina.hassan@moh.example.test` · Amina Hassan | Site-wide Accounting Officer |
| `daniel.rotich@moh.example.test` · Daniel Rotich | The one approved statutory-capacity assignment for this entity; exactly one statutory route |
| `naomi.chebet@moh.example.test` · Naomi Chebet | Site-wide Auditor |
| `samuel.otieno@moh.example.test` · Samuel Otieno | Expired assignment only; used for the forbidden and no-authority fixtures |

Grace, Peter Kimani, Julia Njeri, Mercy Kilonzo, Josphat Mwangi, Naomi Chebet and Samuel Otieno come from the KT-STD-001 §8.3 shared register. Two actors are added by this document and shall be added to that register: **Amina Hassan** (`amina.hassan@moh.example.test`, Accounting Officer, site-wide) and **Daniel Rotich** (`daniel.rotich@moh.example.test`, statutory approver, site-wide). KT-STD-001 §8.5 shall also gain: **Procurement Planning journeys — 24 Nov 2026 through 20 Dec 2026, EAT.**

No seed business decision uses Administrator.

### 14.3 Authoritative Strategy and Budget fixtures

| Fixture | Exact value |
|---|---|
| Active Strategic Plan | `STR-MOH-2023-001-V1` — Ministry of Health Strategic Plan (Demo) |
| Active Strategic Objective | `OBJ-MOH-2023-001` — Strengthen interoperable national digital health services |
| Objective path | Digital health systems › Health policy, standards and regulation › Digital health governance |
| Procurement Budget Line 1 | `MOH-BL-DHI-2027` — Digital health infrastructure programme · Government of Kenya · KES 100,000,000 |
| Procurement Budget Line 2 | `MOH-BL-HWD-2027` — Digital health workforce development · Government of Kenya · KES 60,000,000 |

Planning seed data references these exact owned records, which are created by STR-CHG-001 v1.6 §14.3 and BUD-CHG-001 v1.3 §15.3. It does not create a substitute Objective, Procurement Budget, Procurement Budget Line, funding source or currency.

### 14.4 Integrated accepted Need and DPP baseline

The default integrated lifecycle uses one accepted Need and no direct requirement.

| Field | Exact value |
|---|---|
| Need | `NDS-MOH-2027-0001` · Version `NDS-MOH-2027-0001-V1` |
| Title | National digital health infrastructure upgrade |
| Description | Procure and implement national digital health infrastructure across priority health facilities. |
| Expected operational result | Priority health facilities can use secure and interoperable digital health services. |
| Quantity | 1 programme |
| Required by | 31 Aug 2027 |
| DPP | `DPP-MOH-DHI-2027-001` · Digital Health · Version 1 |
| DPP entry | `DPPE-MOH-DHI-2027-001` · Accepted Departmental Need |
| Planning Procurement Budget Line | `MOH-BL-DHI-2027` |
| Planning indicative amount | KES 80,000,000 |
| DPP classification | Non-consulting services |
| DPP submission | `DPPS-MOH-DHI-2027-001-V1` · Dr Peter Kimani · 25 Nov 2026, 10:00 EAT |
| DPP validation | `DPPV-MOH-DHI-2027-001-V1` · Mercy Kilonzo · Accepted · 27 Nov 2026, 14:00 EAT |

The Need fixture contains no Procurement Budget Line, amount, funding source, currency, Strategy or classification. Those values first exist in their owning Planning records.

### 14.5 Integrated Annual Plan baseline

| Field | Exact value |
|---|---|
| Annual Plan | `PLN-MOH-2027-001` — Ministry of Health Annual Procurement Plan 2027/28 |
| Plan Version | `PLN-MOH-2027-001-V1` · Version 1 · created automatically from the first accepted DPP at 27 Nov 2026, 14:00 EAT · Active after publication acknowledgement |
| Plan Item | `PPI-MOH-2027-021` — National digital health infrastructure upgrade |
| Description | Procure and implement the national digital health infrastructure upgrade as one integrated FY 2027/28 programme. |
| Source allocation | `PSA-MOH-2027-021-001` · full DPPE-MOH-DHI-2027-001 allocation |
| Requirement type | Non-consulting services |
| Strategic Objective | `OBJ-MOH-2023-001` |
| Procurement method | Open Tender |
| Quantity and value | 1 programme · KES 80,000,000 |

Exact planned dates are:

| Milestone | Date |
|---|---|
| Invitation or advertisement | 1 May 2027 |
| Bid opening | 23 May 2027 |
| Evaluation completion | 23 Jun 2027 |
| Tender award approval | 10 Jul 2027 |
| Notification of award | 14 Jul 2027 |
| Contract signing | 1 Aug 2027 |
| Delivery or implementation completion | 31 Aug 2027 |

### 14.6 Integrated Finance, governance and publication baseline

| Evidence | Exact value |
|---|---|
| Finance task | `FNT-MOH-2027-001` — one task for Plan Version 1 |
| Finance decision | `FND-MOH-2027-001-V1` · Confirm plan funding · Josphat Mwangi · 4 Dec 2026, 10:00 EAT |
| Affordability statement at decision | MOH-BL-DHI-2027 approved KES 100,000,000 · planned KES 80,000,000 · within approved. MOH-BL-HWD-2027 approved KES 60,000,000 · planned KES 0 · within approved. |
| Reservations created | **None.** Planning creates no reservation; Budget balances are unchanged by the whole plan cycle. |
| Statutory route configured | `Responsible Cabinet Secretary` — the seed exercises the configured-route path |
| Accounting Officer adoption | `AOD-MOH-2027-001-V1` · Amina Hassan · 8 Dec 2026, 10:00 EAT |
| Statutory approval | `APP-MOH-2027-001-V1` · Daniel Rotich · 9 Dec 2026, 11:00 EAT |
| Publication attempt | `PUB-MOH-2027-001-A1` · System · 10 Dec 2026, 14:55 EAT |
| Acknowledgement | `ACK-MOH-2027-001-A1` · 10 Dec 2026, 15:00 EAT |
| Activation | `PLN-MOH-2027-001-V1` Active at the acknowledgement time |
| Budget position after the plan cycle | MOH-BL-DHI-2027 · approved KES 100,000,000 · reserved KES 0 · available KES 100,000,000, unchanged |

At the observation time of 10 Dec 2026, 15:05 EAT, PPI-MOH-2027-021 has remaining eligibility of 1 programme and KES 80,000,000 and no Requisition drawdown.

### 14.7 Isolated direct-requirement fixture

This profile exists for DPP and direct-source tests only. It is not loaded into the default integrated Active Plan.

| Field | Exact value |
|---|---|
| Direct entry | `DPPE-MOH-DHI-2027-DIR-001` |
| Title | Digital health platform security assessment |
| Description | Assess the security of the national digital health platform and provide a prioritised remediation report. |
| Expected operational result | The Ministry receives a prioritised and actionable security remediation plan. |
| Quantity | 1 service |
| Required by | 31 Oct 2027 |
| Procurement Budget Line | `MOH-BL-DHI-2027` |
| Indicative amount | KES 20,000,000 |
| Classification | Consulting services |
| Source origin | Direct departmental requirement |
| Need lineage | None |

Profiles shall prove a direct-only DPP, a Need-only DPP and a mixed DPP. No profile creates a synthetic Need or bypass reason.

### 14.8 Isolated combined-source fixture

| Source | Department | Quantity | Required by | Procurement Budget Line | Currency | Amount | Classification |
|---|---|---:|---|---|---|---:|---|
| Clinical training laptops for digital health rollout | Human Resources Management and Development | 200 each | 31 Dec 2027 | MOH-BL-HWD-2027 | KES | KES 48,000,000 | Goods |
| Clinical deployment laptops for digital health rollout | Digital Health | 300 each | 31 Dec 2027 | MOH-BL-DHI-2027 | KES | KES 72,000,000 | Goods |

Both sources resolve to the one FY 2027/28 Procurement Budget. The combined item is `PPI-MOH-2027-033`, totals 500 each and KES 120,000,000, completes on 31 Dec 2027, and uses the exact title, description and aggregation reason in PLN-DES-09A. It is isolated because its funding requirements exceed the default live baseline.

### 14.9 KEBS first-slice profile

The KEBS profile uses these exact departmental source lines:

| Source line | Requirement | Quantity | Expected operational result |
|---|---|---:|---|
| `SRC-KEBS-ICT-001` | Business laptops | 25 Each | Mobile officers can run approved office and standards applications securely. |
| `SRC-KEBS-ICT-002` | Desktop computers with monitors | 15 Each | Fixed workstations replace unsupported equipment at the Coast Region office. |
| `SRC-KEBS-ICT-003` | Business tablets | 10 Each | Field officers can capture and review inspection information away from the office. |

The profile runs once from three Accepted Departmental Needs and once from three direct DPP entries. Both produce the same source facts and form `PPI-KEBS-2026-ICT-001`. The Plan Item preserves all three source allocations and contains no specification, attachment, supplier evidence or Tender security.

### 14.10 Seed execution rules

- Upsert by exact stable seed identifiers and produce no duplicate root, Version, entry, allocation, task, decision, reservation or publication attempt.
- Run configuration, Strategy, Budget and Departmental Needs prerequisites before Planning.
- Validate fixtures through the same domain services used by commands.
- Use the named role actor for each lifecycle event, never Administrator.
- Freeze the service clock per profile.
- Keep isolated direct, combined, return, shortfall, stale, successor and publication-failure profiles out of the default integrated baseline.
- Fail loudly on missing prerequisite, ineligible Objective/Procurement Budget Line, invalid amount/date, duplicate allocation, authority conflict or inconsistent expected state.
- Seed no removed field, UI-only display value, optional note, source reference, monitoring event or legacy alias.

## 15. Acceptance contract

The module is accepted only when all statements below are demonstrably true.

| ID | Required result |
|---|---|
| PLN-AC-001 | Zero, one and multiple authorised PE plus configured-FY option cases fail closed and disclose no unauthorised data. |
| PLN-AC-002 | Workspace reads and direct routes create no record. |
| PLN-AC-003 | One DPP root is created idempotently per Fiscal Year and Organisation Unit. |
| PLN-AC-004 | Every current accepted Need appears once with six read-only facts, including expected operational result, and no Budget, Strategy or classification from Needs. |
| PLN-AC-005 | A direct-only DPP can be created and submitted without any Need. |
| PLN-AC-006 | A mixed DPP retains distinct source origins and creates no synthetic Need. |
| PLN-AC-007 | Direct requirement input is limited to the eight defined values. |
| PLN-AC-008 | Need-origin input is limited to Procurement Budget Line and indicative amount. |
| PLN-AC-009 | DPP submission blocks missing accepted Needs, partial quantities, incomplete funding, invalid dates and zero entries. |
| PLN-AC-010 | HoD submission records the exact certification and routes to DPP validation, not the AO. |
| PLN-AC-011 | A DPP return preserves the submitted Version and provides actionable entry-level correction. |
| PLN-AC-012 | DPP acceptance requires one governed classification per entry, creates/reuses the initial Draft Annual Plan and projects every accepted entry without creating a Plan Item. |
| PLN-AC-013 | The Draft Annual Plan has no separate start gate, window-close wait, all-department gate or nil-plan declaration; it lists only current accepted unallocated sources. |
| PLN-AC-014 | Single and separate formation allocate every source once and at full quantity. |
| PLN-AC-015 | Combined formation rejects incompatible sources and requires the defined aggregation reason. |
| PLN-AC-016 | No blank or source-less Plan Item can be created. |
| PLN-AC-017 | Each Plan Item has exactly one eligible Active Strategic Objective and no Value Commitment. |
| PLN-AC-018 | Plan Item input contains no contract period, lotting, recommended method, generic basis or actual milestone field. |
| PLN-AC-019 | Seven planned dates are required, chronological and bounded by source required-by date. |
| PLN-AC-020 | Plan Item value and funding breakdown equal the exact source allocations. |
| PLN-AC-021 | Finance task data is protected before serialization and displays a current As-at position. |
| PLN-AC-022 | Funding confirmation creates all source reservations and one decision atomically, or none on shortfall. |
| PLN-AC-023 | Need acceptance, DPP actions and Plan formation create no reservation. |
| PLN-AC-024 | A changed source set, Procurement Budget Line, amount or currency, or a failed Budget revalidation, makes prior Finance evidence Stale; narrative, Objective and schedule changes alone do not. |
| PLN-AC-025 | Accounting Officer and statutory-approval tasks each show the complete immutable Plan before decisions. |
| PLN-AC-026 | The Accounting Officer adopts or returns the complete consolidated Plan. |
| PLN-AC-027 | Exactly one statutory authority approves or returns the same Accounting-Officer-adopted Version. |
| PLN-AC-028 | Every return requires one actionable correction and preserves the submitted snapshot. |
| PLN-AC-029 | This approval authorises only the exact system publication payload and does not itself activate the Plan. |
| PLN-AC-030 | Publication transmits the exact approved payload and activates only on acknowledgement. |
| PLN-AC-031 | Failed/indeterminate publication can retry the same payload without a new approval. |
| PLN-AC-032 | Exactly one Plan Version is Active and one successor may be open. |
| PLN-AC-033 | Active predecessor eligibility remains unchanged until successor acknowledgement. |
| PLN-AC-034 | Requisition eligibility exposes exact remaining quantity/value and creates no Requisition. |
| PLN-AC-035 | Active item removal is blocked by drawdown, Tender handoff, commitment or contract. |
| PLN-AC-036 | Planning has no actual-milestone entry, Monitoring Officer action or custom support workspace. |
| PLN-AC-037 | All counts, queues, details and actions use the same Fiscal Year, Organisation Unit and task predicates, and a record hidden from a list is unreachable by direct route. |
| PLN-AC-038 | Same idempotency key returns the original result; concurrent different commands yield one winner and one stale result. |
| PLN-AC-039 | Cross-PE, cross-OU and otherwise out-of-scope direct URLs disclose no record existence. FY-specific mutations are allowed or denied by the owning operation's configured window and record-state rules, not by a user FY grant. |
| PLN-AC-040 | Seed reset and rerun produce the exact baseline without duplicates or semantic drift. |
| PLN-AC-041 | No Head of Procurement Function, professional reviewer, generic approval committee or publication approver exists in the Annual Plan chain. |
| PLN-AC-042 | A Board or similar-body approval records the collective decision and resolution reference. |
| PLN-AC-043 | Publication is an idempotent system action; any technical retry reuses the exact approved payload. |
| PLN-AC-044 | One role-bound User Responsibility Assignment and the shared AUTH resolver enforce PE/OU authority; Frappe User Permission, User Scope Assignment and Financial Year grants do not authorize Planning. |
| PLN-AC-045 | Requisition eligibility exposes every source allocation, expected operational result and exact remaining quantity and value. |
| PLN-AC-046 | The KEBS Needs-origin and direct-entry profiles produce equivalent approved source lineage. |
| PLN-AC-047 | A mutable Draft Plan Item can be dissolved; open Finance work is cancelled, effective reservations are released and its sources become available for re-formation without deleting history. |
| PLN-AC-048 | Dissolution is blocked after Plan submission and fails atomically when reservation release fails. |
| PLN-AC-049 | Reservation revalidation and every Planning-triggered release use the Budget-owned service and preserve exact correlation evidence. |
| PLN-AC-050 | Governance correction preserves the returned snapshot, excludes pending additions and restarts at Accounting Officer adoption. |
| PLN-AC-051 | Finance repeats on correction only for the defined stale conditions; narrative, Objective and schedule changes alone do not create replacement reservations. |
| PLN-AC-052 | Acceptance of a DPP successor never rewrites an allocated source; mutable Draft items require dissolve and re-form, submitted Plans require return, and Active Plans wait for a successor. |
| PLN-AC-053 | A withdrawn initial DPP can reopen only as the next Version while the initial window is Open. |
| PLN-AC-054 | Accepted Needs stranded by a closed DPP window remain visible with the exact not-included status and gain no late-submission bypass. |
| PLN-AC-055 | Combined Plan Items reject different Budgets or currencies. |
| PLN-AC-056 | Sequential Requisitions may draw one Plan Item while balances remain, subject to the Requisition module's one-open rule. |
| PLN-AC-057 | The maker-checker matrix blocks every prohibited same-user action pair and no unlisted approval level is introduced. |
| PLN-AC-058 | Concurrent first-DPP acceptance creates exactly one Annual Plan root and one open Version. |
| PLN-AC-059 | Planning has one navigation entry and no role-specific work-queue menu. |
| PLN-AC-060 | The Financial Year select is server-authorised, visible and changeable; local storage never grants access or permanently binds a year. No Procuring Entity selector exists on any Planning screen. |
| PLN-AC-061 | Draft, Accounting Officer, statutory approval and Active surfaces render the same generated Annual Plan title and the governance surfaces use the exact immutable fixture row and total. |
| PLN-AC-062 | The combined-source fixture has deterministic required-by dates and its completion date satisfies both sources. |
| PLN-AC-063 | A user with different responsibilities in different OUs cannot exercise either responsibility outside its own assignment. |
| PLN-AC-064 | A site-wide Planner responsibility and an OU-scoped departmental responsibility coexist without narrowing or broadening each other. |
| PLN-AC-065 | One parent-OU assignment covers its descendants and never a sibling outside that subtree. |
| PLN-AC-066 | Tasks route eligible work but cannot authorize a user who lacks the matching role-bound assignment. |
| PLN-AC-067 | Decision evidence stores the exact User Responsibility Assignment exercised. |
| PLN-AC-068 | A Plan Item cannot reach Finance request without an explicit `reservation_category`; `None` is accepted and recorded as a choice. |
| PLN-AC-069 | The Annual Plan derives the reserved share of planned value, compares it with the target in force for its Fiscal Year, and shows a shortfall as an advisory that blocks neither submission nor adoption. |
| PLN-AC-070 | A procurement method inadmissible for a Plan Item's planned value blocks readiness and returns the value band and the admissible methods. |
| PLN-AC-071 | Method admissibility resolves against the threshold matrix in force for the plan's Fiscal Year, not the current one, and the resolved band is stored on the item. |
| PLN-AC-072 | A missing threshold matrix for the plan's Fiscal Year fails readiness closed with `PLN_REFERENCE_UNAVAILABLE`; a missing reservation target or price index blocks nothing. |
| PLN-AC-073 | Two or more Plan Items sharing a Procurement Budget Line and requirement type, each below the open-tender threshold but jointly above it, raise a splitting advisory that the Planner must confirm or resolve by aggregation. |
| PLN-AC-074 | A confirmed splitting advisory records the confirmation, and a confirmation citing legitimate unbundling under a preference and reservation scheme is retained as such. |
| PLN-AC-075 | The indicative amount is treated as the full estimated cost including incidentals; Finance confirmation reserves against that figure and no net-of-incidentals estimate is accepted. |
| PLN-AC-076 | An Annual Plan activated after its Fiscal Year has begun is permitted, blocks nothing, and retains a recorded reason in its audit history. |
| PLN-AC-077 | The publication payload carries OCDS planning-stage fields for every Plan Item, and the canonical payload retained in the publication record is the OCDS-shaped one. |
| PLN-AC-078 | No asset disposal record, field, screen or plan item exists in this module. |
| PLN-AC-079 | No PPRA return, submission schedule or regulator transmission is produced by this module. |
| PLN-AC-080 | Exactly one Finance task exists per Plan Version regardless of the number of Plan Items, and no per-item Finance task, route or queue exists. |
| PLN-AC-081 | No Planning command creates, holds, releases or revalidates a funding reservation, and Budget balances are identical before and after a complete plan cycle from formation through publication. |
| PLN-AC-082 | Plan submission is blocked when planned value exceeds a Procurement Budget Line's approved amount, and the failing lines and exact excesses are returned. |
| PLN-AC-083 | Plan submission is not blocked when planned value exceeds currently available funds; the shortfall is displayed as an advisory to the Planner, Finance Confirmation Officer and Accounting Officer. |
| PLN-AC-084 | Adoption always creates exactly one statutory-approval task; no configuration permits a plan to reach publication without statutory approval. |
| PLN-AC-085 | Configuration selects which of the three statutory routes applies; an absent or ambiguous route blocks adoption with `PLN_STATUTORY_ROUTE_UNCONFIGURED` and is treated as a configuration defect. |
| PLN-AC-086 | Dissolving a Draft Plan Item and cancelling a Draft successor change no Budget balance. |
| PLN-AC-087 | A corrected submission repeats funding confirmation only when the plan's per-line totals or a Procurement Budget Line's approved amount changed; an unchanged plan carries its confirmation forward. |
| PLN-AC-088 | `Pending addition` is derived at read time and appears in no stored field, schema column or fixture. |
| PLN-AC-089 | Every Plan Item records a plan horizon, aggregation indicator and lotting indicator before funding confirmation may be requested; a multi-year horizon requires its justification and a lotted item requires a lot count. |
| PLN-AC-090 | The published plan carries, for every item, the breakdown, planned dates, horizon, aggregation indicator, lotting indicator, estimated value with budget and funding source, and procurement method required by the plan contents rules. |
| PLN-AC-091 | Open Tender, Request for Quotations and Low Value Procurement are all selectable; the server proposes the method from the resolved threshold band and rejects a change outside that band. |
| PLN-AC-092 | A departmental plan may record an accepted Departmental Need as not proceeding with a reason; the entry is retained in the submission, forms no Plan Item, is excluded from every total, and the outcome reaches Departmental Needs. |
| PLN-AC-093 | An accepted Need that is neither planned nor marked not proceeding blocks departmental plan submission. |
| PLN-AC-094 | Departmental plan intake is governed solely by the Fiscal Year flag and its close instant; no `DPPSubmissionWindow` DocType, route, command, seed or test exists. |
| PLN-AC-095 | No disposal item, field, column or screen exists in this module, and the accounting officer adopts the procurement plan alone. |
| PLN-AC-096 | No valuation, disposal committee, bidder, proceeds-accounting or asset write-off record exists in this module. |
| PLN-AC-097 | Where the site entity is a county entity, the plan derives the county resident-tenderer reserved share and compares it with the 20% minimum as an advisory; the control is absent for a non-county entity. |
| PLN-AC-098 | Adoption is blocked with `PLN_STATUTORY_ROUTE_UNCONFIGURED` when no statutory route is configured, and no path exists from adoption to publication that skips statutory approval. |
| PLN-AC-100 | Each Plan Item records an actual date per milestone as activities conclude, and planned days, actual days and variance are derived; a plan with no actuals recorded is still valid before execution begins. |
| PLN-AC-101 | The plan carries a Status per item and an optional Project Name in its header. |
| PLN-AC-102 | All eleven Third Schedule methods are selectable; two-stage tendering and framework agreements are not; open tender is the default. |
| PLN-AC-103 | Every Plan Item carries a goods, works or services category, and method admissibility resolves against the Second Schedule limits for that category. |
| PLN-AC-104 | The low-value limit is enforced cumulatively per item per financial year across the whole plan, not per line. |
| PLN-AC-105 | Where several preference schemes could apply, the server proposes the highest-advantage one; a different choice requires a retained reason. |
| PLN-AC-106 | Exclusive preference is derived, not entered, and applies below KES 1bn for works and construction materials made in Kenya and KES 500m for goods and services where funding is wholly national or county. |
| PLN-AC-107 | A lotted and reserved item records that the lotting serves the reservation, and the splitting advisory treats that as a valid confirmation. |
| PLN-AC-108 | The publication record characterises the published plan as an invitation to treat and carries the Third Schedule fields. |
| PLN-AC-109 | No disposal record, field, column, screen or plan item exists in this module. |
| PLN-AC-110 | Every field required by the seven statutory returns in §7.5A is retained by the plan, verified field by field against that table. |
| PLN-AC-099 | Departmental Needs is never a precondition for a departmental plan entry, and no command, screen or validation requires a Need reference on a direct requirement. |

### 15.1 Minimum automated coverage

1. Domain tests for DPP coverage, direct-entry fields, source immutability, classification, formation/dissolution compatibility, correction restart, schedule, Objective eligibility and lifecycle transitions.
2. Permission tests for every role, Organisation Unit boundary, task assignment, acting-HoD period and maker-checker rule.
3. Contract tests for Needs events, Strategy Objective selection, Procurement Budget Line eligibility, all-source reservation, revalidation/release, publication adapter and Requisition eligibility.
4. Transaction tests for submission, concurrent first-DPP acceptance, formation, dissolution, Finance, governance correction, successor cancellation, publication acknowledgement and concurrent retries.
5. Vue component tests for exact fields, absent fields, task detail, errors, dialog copy and action visibility.
6. Focused Playwright journeys for direct-only DPP, accepted-Need DPP, mixed DPP, integrated Active Plan, Finance shortfall, governance return and publication retry.

## 16. Implementation and test constraints

### 16.1 Frappe and Vue implementation

- Retain one Frappe app/module boundary for Procurement Planning and conventional DocType ownership.
- Use standard naming, permissions, link fields, child tables, background jobs, transactions and framework audit fields.
- Enforce every important rule in Python domain services; Vue state and client controls are never the authority.
- Mount Vue 3 SFCs into real `frappe.ui.make_app_page()` Desk pages through the bench build pipeline already proven by the Strategy pilot.
- Port Claude Design tokens into the existing KenTender token chain. Do not ship `.dc.html`, design runtime, vendor state logic, CDN assets or utility-class output.
- Use scoped component styles and existing shared KenTender components before adding a new component.
- Unmount Vue and detach listeners on Desk route change.
- Self-host any approved fonts through the application asset pipeline; no CDN dependency.
- Keep the Frappe header, breadcrumb and navigation outside the Vue artboard. Render the Planning Financial Year select inside the Planning workspace page content exactly as defined in PLN-DES-01.
- Prefer server-computed projections tailored to each screen over client joins across DocTypes.

### 16.2 Verification and release evidence

The verification protocol is KT-STD-001 §5; release evidence is KT-STD-001 §6.

Additional evidence for this document:

- repository scan proving `pe_fy_context_id`, `PEFiscalYearContext`, every Frappe User Permission read, every Fiscal Year user grant and every Procuring Entity selector are absent from Planning code, seeds, fixtures and screens;
- Strategy and Budget contract consumer tests proving `list_strategy_objectives`, `create_strategy_snapshot`, `list_eligible_budget_lines`, `check_funding` and `reserve_funding` are called without a Procuring Entity argument;
- effective-dating tests proving method admissibility, the reservation target and the price index resolve against the plan's Fiscal Year rather than the current date, and that a superseded gazette does not rewrite a historical plan;
- a readiness test proving an inadmissible method blocks while a reservation shortfall and a splitting advisory do not;
- a publication test asserting the canonical payload carries OCDS planning-stage fields for every Plan Item;
- a concurrency test proving one Annual Plan root per Fiscal Year survives simultaneous first-DPP acceptance; and
- browser journeys for the Planner, Head of User Department, Finance Confirmation Officer, Accounting Officer and statutory approver, plus a no-authority actor confirming no data disclosure.

### 16.4 Required AUTH-ADR-001 v1.6 correction slice

Implement the authorization correction as one controlled cross-module slice:

1. Replace every Planning use of Frappe User Permission, User Scope Assignment or module-local scope logic with the shared AUTH-ADR-001 v1.6 resolver registered through both Frappe permission hooks, plus the exact role-bound assignment ID.
2. Resolve DPP departmental work from OU-scoped Author and HoD assignments, and Annual Plan, Finance and governance work from the applicable site-wide responsibility.
3. Remove Financial Year from every user grant, required dimension and seed. Continue to gate operations through the record FY, configured context, DPP window and Plan state.
4. Use one resolver predicate for workspaces, counts, DPP/Plan details, tasks, files, exports and every command. Do not keep a read-path fallback to User Scope Assignment.
5. Make the Planning Financial Year select optional, visible and changeable, and remove the Procuring Entity selector entirely. Direct record and task routes derive the year from the record and reauthorise it.
6. Store the exact User Responsibility Assignment ID and snapshot on every DPP certification, validation, Finance and Plan-governance decision.
7. Replace seeds with exact role-bound assignments, including the non-overlapping Peter/Julia acting-HoD periods. Do not seed business roles to Administrator.
8. Add Cartesian-product, mixed PE/OU scope, OU-tree descendant, cross-PE, acting-period and task-without-assignment regression tests.
9. Cut over all Planning authorization callers atomically with the shared resolver; remove obsolete rows only after the cross-module gate passes.

## 17. Prohibited shortcuts

The universal list is KT-STD-001 §2.3 and §10. Additionally, for this document:

- make Departmental Needs a prerequisite for a DPP entry;
- create a synthetic Need or collect a bypass reason for a direct requirement;
- source Strategy, requirement type, Procurement Budget Line or amount from Departmental Needs;
- let Planning edit accepted Need facts;
- add a field because it appeared in an old document or visual;
- add Value Commitment, source reference, generic evidence, optional note, attachment, contract period, lotting or actual milestone fields;
- create an Annual Plan or task from a page read;
- create a source-less Plan Item or partially allocate a DPP entry;
- accept a client-computed value, permission, state, balance or approval route as authoritative;
- reserve only part of a combined item;
- release or mark a Budget reservation through a local Planning-table update;
- rewrite an allocated source automatically when a DPP successor is accepted;
- hide full Plan details from the Accounting Officer or statutory approver;
- insert professional review, Head of Procurement Function approval, a generic committee or publication approval into the Accounting Officer plus one-statutory-approval chain;
- activate on approval or on an unacknowledged publication attempt;
- expose create-Requisition or create-Tender actions from Planning;
- import Claude Design runtime, `.dc.html`, Tailwind utilities or copied vendor markup into production;
- create a role-specific sidebar work-queue entry;
- add Financial Year, module or capability strings to a User Responsibility Assignment;
- draw or replace the Frappe breadcrumb or header inside the page;
- maintain old routes, aliases, duplicate fields or compatibility reads; or
- Do not reintroduce `pe_fy_context_id`, a Procuring Entity selector, a PE-scoped role or a Fiscal Year user grant.
- Do not call a Strategy or Budget contract with a Procuring Entity or organisation-unit scope argument.
- Do not treat Procurement Budget Line owner scope as a user-permission check.
- Do not create a `Budget Officer` Planning task; the Finance confirmation role is Finance Confirmation Officer.
- Do not author, edit or hard-code regulator reference data. The threshold matrix, reservation categories and target, and market price index are read from Configuration & Governance, effective-dated.
- Do not resolve a threshold, reservation target or price index using today's date when the plan belongs to another Fiscal Year.
- Do not make the reservation target blocking, and do not let a shortfall prevent submission, adoption, approval or publication.
- Do not make the splitting advisory blocking, and do not auto-aggregate items to clear it.
- Do not accept a planning estimate stated net of insurance, clearing and forwarding, demurrage, warehousing, advertisement or other incidental costs.
- Do not add an asset disposal record, field, screen or plan item to this module.
- Do not produce a PPRA return, submission schedule or regulator transmission from this module.
- Do not publish a payload whose canonical form is not OCDS-shaped.
- Do not create a Finance task, decision or queue per Plan Item. One task covers one Plan Version.
- Do not create, hold, release or revalidate a funding reservation anywhere in Procurement Planning. Reservation belongs to Procurement Requisition.
- Do not make the statutory approval stage unconditional, and do not treat an unconfigured statutory route as a defect or a blocker.
- Do not store `Pending addition` as an entry or allocation state.
- Do not recreate `DPPSubmissionWindow` or any window record with opening and closing instants. Departmental plan intake is a Fiscal Year flag owned by Configuration & Governance.
- Do not make statutory approval optional, skippable or configurable to `None`.
- Do not prohibit or omit the lotting indicator; regulation 41(e) requires it. Equally, do not model lot specifications here — those belong to Tender Management.
- Do not restrict the plan to a single procurement method, and do not allow a method outside the resolved threshold band.
- Do not force a department to plan an accepted Need it has recorded as not proceeding, and do not permit an accepted Need to be silently omitted.
- Do not add any disposal record, field, column or screen to this module; the annual asset disposal plan is a separate statutory instrument owned by DSP-CHG-001.
- Do not restrict the method catalogue below the eleven the Third Schedule permits, and do not add two-stage tendering or framework agreements to a plan.
- Do not evaluate method admissibility without the goods, works or services category.
- Do not treat the low-value limit as per transaction; it is per item per financial year.
- Do not let the Planner choose a reservation category freely where a higher-advantage scheme applies without recording a reason.
- Do not describe published plans as anything other than an invitation to treat.
- Do not treat actual dates and variance as operational monitoring to be excluded from the plan.
- Do not treat Departmental Needs as a precondition for a departmental plan entry.
- Do not block Plan submission because planned value exceeds currently available funds; only the approved amount blocks.

## 18. Traceability and precedence

This document incorporates the approved boundary decisions from:

**Required correction in another document.** CFG-CHG-002 v0.6 has no owner for regulator reference data. It shall gain an **effective-dated** register covering the PPRA threshold matrix, reservation categories and their target percentage, and the quarterly market price index, surfaced in System setup and read-only to every module. This is a different kind of record from the fiscal years and units CFG governs today — it is regulator-sourced, changes on gazette, and must retain superseded versions so historical plans stay auditable. CFG-CHG-002 also still owes an owner for the funding-source catalogue required by BUD-CHG-001 v1.3.

- KT-STD-001 v1.1 — document structure, design closed-input rules, artboard shell, shared fixture register, common page behaviour, verification protocol, release evidence, seed conventions, universal prohibitions and error conventions;
- AUTH-ADR-001 v1.6 — sole role-bound authority, the site-local Organisation Unit tree, registered permission hooks, no per-user Fiscal Year and non-authoritative UI filters;
- CFG-CHG-002 v0.6 — the one site Procuring Entity, the ERPNext Fiscal Year surface, Organisation Unit records and the ERPNext `UOM` catalogue;
- STR-CHG-001 v1.6 — exactly one Active Strategic Objective on each Plan Item, site-wide Strategy scope and no Value Commitment;
- BUD-CHG-001 v1.3 — Planning-owned Finance task, the Finance Confirmation Officer role, Budget-owned live position and reservations, and the `Procurement Budget Line` record name; and
- NDS-CHG-001 v1.6 — optional consultation, direct departmental planning path, six Need values, role-bound departmental scope and Planning-owned DPP funding specification; and
- REQ-CHG-001 v1.2 — partial Plan Item drawdown, one-open-Requisition control, reversal and remaining balances.

This document supersedes conflicting Planning requirements in:

- PLN-CAN-001 v0.1;
- PLN-CDR-001 v0.1;
- PLN-FR-001 v0.1;
- PLN-STC-001 v0.1;
- PLN-SDC-001 v0.1;
- PLN-GF-001 v0.1/v0.2;
- PLN-GF-002 v0.2;
- PLN-GF-003 v0.1/v0.2; and
- the Procurement Planning Revision Ledger.

Earlier UI assets remain evidence for reuse only. Where their fields, states, labels, source ownership or actions differ from this document, this document controls.

## 19. E2E-REQ-001 conformance

| End-to-end control | Procurement Planning implementation |
|---|---|
| Structured information is primary | DPP entries and Plan Items are governed records; attachments do not replace requirement data. |
| Enter once, carry forward | Accepted Need facts and direct-requirement facts flow into the Plan and Requisition-eligibility projection without re-entry. |
| Ownership remains clear | Planning may classify and fund a requirement, but it cannot rewrite accepted departmental facts. |
| Stable lineage | Every Plan Item preserves its exact DPP entry and Need-version source where applicable. |
| Minimal approval chain | The Accounting Officer adopts the complete Plan and exactly one statutory authority approves it. Publication is a system action. |
| No STD configuration dependency | Planning exposes governed requirement lineage; it does not create, select or configure a tender template. |

## 20. Approval effect

Approved 3 September 2026. PLN-CHG-001 v1.9 supersedes v1.8 and all earlier versions in full and becomes the only Procurement Planning requirements document to consult.

Approval authorises implementation of the complete clean Procurement Planning module and conversion of section 11 into Claude Design artboards. It further authorises: replacement of `pe_fy_context_id` with the ERPNext `fiscal_year` on the submission window, departmental plan and Annual Plan; rekeying uniqueness to Fiscal Year; registration of Procurement Planner, Accounting Officer, the statutory approver and Auditor as site-wide business roles resolved through the AUTH-ADR-001 v1.6 permission hooks; renaming the Finance confirmation actor to Finance Confirmation Officer per BUD-CHG-001 v1.4; removal of every Procuring Entity selector, PE-scoped role and Fiscal Year user grant; adoption of the `Procurement Budget Line` record name and ERPNext `UOM` units; and adoption of the KT-STD-001 v1.1 standards and shared fixture register.

It further authorises the statutory planning controls in §1.1: the `reservation_category` field and derived entity target; blocking method admissibility against the effective-dated threshold matrix; the non-blocking splitting advisory; the defined estimate basis; the plan-timing rule; the OCDS-shaped publication payload; and the explicit non-goals for asset disposal planning and periodic PPRA reporting.

It further authorises the statutory conformance changes in §1.1: mandatory statutory approval with configuration selecting only which route applies; the regulation 41 plan contents added to the Plan Item; reinstatement of the lotting indicator; Open Tender, Request for Quotations and Low Value Procurement as admitted methods; the departmental plan intake flag replacing `DPPSubmissionWindow`; the not-proceeding outcome on a Need-origin entry; the county resident-tenderer reservation; and the clarified standing of Departmental Needs as internal consultation with no statutory role.

It also authorises the lifecycle simplification in §5.2: one plan-level funding confirmation replacing per-item confirmation, no reservation created anywhere in Planning, a statutory route configured per site with `None` valid, and **Pending addition** as a derived label rather than a stored state.

Implementers shall not retain v1.4's PE/FY context field, its Procuring Entity selector, its PE-scoped role assignments or its `Budget Officer` Planning task; shall not ship a Plan Item without a recorded reservation category or an unvalidated procurement method; and shall not create a per-item Finance task, a Planning-held reservation or an unconditional statutory approval stage. It does not approve generated visual deviations, production publication configuration, a Procurement Requisition, a Tender or any field not defined here.
