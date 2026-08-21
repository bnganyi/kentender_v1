# Procurement Planning — MVP 1 Requirements

**Document ID:** PLANNING-MVP1-REQ-1.9  
**Version:** 1.9  
**Status:** Approved functional baseline for direct MVP correction  
**Date:** 12 August 2026  
**Supersedes:** `PLANNING-MVP1-REQ-1.8`  
**Controlling authority:** `KENTENDER-MVP-CMOM-1.1`  
**Design baseline:** `PLANNING-MVP1-STITCH-2.0`  
**Module:** Procurement Planning  
**Primary fixture:** Ministry of Health  
**Secondary fixture:** County Government of Kisumu

**Revision 1.9:** Defines removal of a Plan Item as a controlled, audited Plan-Version change. A planner may remove a draft-only Proposed item or propose removal of an eligible Active item through a Draft successor. Removal never hard-deletes lineage, never edits an Approved Version in place, restores source-Demand eligibility only when the removal is effective, and reverses Finance tasks/reservations at the correct lifecycle boundary. All v1.8 Finance-shortfall and earlier workflow corrections remain in force.

## Source baseline

### Kenyan legal sources

- [Constitution of Kenya, Article 227](https://new.kenyalaw.org/akn/ke/act/2010/constitution/eng%402010-09-03)
- [Public Procurement and Asset Disposal Act, 2015](https://new.kenyalaw.org/akn/ke/act/2015/33/eng%402022-12-31), including procurement-planning, method and funding controls
- [Public Procurement and Asset Disposal Regulations, 2020](https://new.kenyalaw.org/akn/ke/act/ln/2020/69/eng%402020-12-24), including annual-plan content, consolidation and implementation controls

### International reference standards

- [OECD Recommendation of the Council on Public Procurement](https://legalinstruments.oecd.org/en/instruments/OECD-LEGAL-0411)
- [World Bank Procurement Regulations for IPF Borrowers, Seventh Edition](https://thedocs.worldbank.org/en/doc/c84273d1b230aeb2b0b8134de5dc8cd7-0290012025/original/Procurement-Regulations-7th-Edition-Sep-2025.pdf)
- [Open Contracting Data Standard](https://standard.open-contracting.org/latest/en/primer/how/)

### KenTender baselines

- `KENTENDER-MVP-CMOM-1.1`
- Demands Requirements v1.4 or its approved successor
- Budget & Funding Requirements v1.1 or its approved successor
- Strategy Alignment Requirements v1.1 or its approved successor
- KenTender Procuring Entity and Organisation Scope Model
- KenTender MVP Canonical Demo Data Contract v2.7
- KenTender Statutory and Public-Value Obligations Matrix v1.1

Applicable Kenyan law and binding financing agreements prevail. International references inform value for money, competition, integration, proportionality, transparency and lifecycle evidence; they do not create extra screens or approvals. Approval routes and legal rules must be configurable and verified before production use.

---

## 1. Purpose

Procurement Planning converts an Approved Demand into an executable Plan Item within an approved annual Procurement Plan.

The ordinary journey is:

> **Approved Demand → Planner completes Plan Item → Finance confirms funding → Head of Procurement approves Plan Version → Tender take-up**

The module answers:

1. Which Approved Demands will the Procuring Entity procure in the planning period?
2. What procurement method, arrangement, indicative lotting and schedule apply?
3. Has Finance confirmed the proposed Budget Line, amount and availability?
4. Has the authorised professional authority approved the Plan Version?
5. Which Active Plan Items have been taken into Tender preparation?

The module is not a package, contribution or compliance-questionnaire workbench.

## 2. Governing product decisions

1. **The Plan Item is the execution unit.** Plan Version controls approval and immutability.
2. **Plan Item formation is decided during source selection.** One selected Demand creates one Plan Item; multiple selected Demands require an explicit separate-or-combined choice.
3. **Source selection happens once.** The resulting Plan Item editor does not select the Demand(s) again.
4. **HoD approves the business need once in Demands.** Planning does not request routine second HoD approval.
5. **Finance confirms funding once after planning.** Auto-matching does not replace the Budget Officer decision.
6. **Head of Procurement performs the professional Plan decision.** The accountable title is configurable by PE.
7. **Approved Plans are not edited in place.** An addition quietly creates or reuses one Draft successor.
8. **The Approved Version remains operational during revision.** Existing Tender handoffs remain effective.
9. **Planning cannot change HoD-owned facts.** Material changes require a Demand amendment and HoD reapproval upstream.
10. **Prefer omission to speculation.** Unsupported fields and workflows are removed, not relabelled.
11. **Plan Item removal is a versioned business change, not deletion.** Draft-only additions can be removed from the Draft; an Active item can only be proposed for removal in a Draft successor and remains operational until that successor is approved.

## 3. Legal and standards treatment

| Planning obligation | MVP system treatment |
|---|---|
| Annual procurement planning | One logical Plan per PE and financial year, with controlled versions |
| Consolidation of user-unit requirements | OU ownership inherited from HoD-approved Demands and visible on Plan Items; no duplicate contribution submission |
| Approved-budget discipline | Proposed Budget Line shown to Planning; Budget Officer confirms and reserves after the Plan Item is complete |
| Procurement description and category | Planner records a concise procurement description and governed category |
| Procurement method | System recommends; planner confirms; non-recommended method requires applicable grounds and reason |
| Timing | Governed milestone dates with chronological validation |
| Aggregation and anti-splitting | One Demand/one Plan Item default; explicit compatible-source combination; actual separate items when kept separate |
| Indicative lots | Planner indicates likely Tender lots without creating extra Plan Items |
| Preference and reservation monitoring | Derived Plan-level coverage only when supported by governed source data; no generic item treatment questionnaire |
| Approval and accountability | Finance confirmation followed by configured professional approval, with actor, time, reason and immutable version |
| Reporting and implementation | Approved Plan export and downstream implementation projections |
| Tender eligibility | Only an Active item in the current Approved Version may create a Planning handoff |

MVP shall not use opaque scoring or autonomous procurement decisions.

## 4. Lifecycle boundary

### 4.1 Authoritative inputs

Planning reads but does not own:

- Approved Demand and immutable approved snapshot;
- Need Items and remaining planning availability;
- PE and owning OU;
- approved business scope, quantity, delivery requirement and estimated value;
- proposed Budget Line and funding allocation context;
- Strategy targets and Strategy Value Commitments; and
- upstream approval evidence.

### 4.2 Planning-owned outputs

Planning owns:

- Procurement Plan and Plan Versions;
- stable Plan Item and Plan Item Versions;
- Plan Demand Allocations;
- procurement description, category, method, arrangement, schedule and indicative lotting;
- multi-Demand Plan Item formation decision and reason evidence;
- planning validation and professional decisions;
- immutable Planning Handoff Snapshot; and
- implementation projections and Planning audit events.

### 4.3 Boundary rules

- Planning shall not mutate Approved Demand facts, Strategy baselines or Budget balances directly.
- Finance confirmation uses the Budget & Funding control service and records Plan Item/version context.
- An Active Plan Item is permission to begin the next governed procurement stage; it is not a Tender, award, contract, commitment, expenditure or proof of realised public value.

## 5. Scope

### 5.1 Included

- PE/FY-scoped Planning workspace
- Annual Plan registration
- Approved Demand eligibility and selection
- One Demand → one Proposed Plan Item default formation
- Plan Demand Allocation lineage
- Focused Plan Item editor
- Controlled method, arrangement, indicative lotting and planned schedule
- Explicit same-PE/same-OU aggregation of compatible Approved Demands
- Actual separate Plan Items when sources are planned separately
- Anti-splitting validation
- Finance confirmation and return after Plan Item completion
- Plan validation, professional return and approval
- Immutable Approved Versions and one Draft successor
- Add Plan Item to an Approved Plan
- Publication/export evidence
- Tender handoff and implementation projection
- Audit, notification and entity-isolated reporting

### 5.2 Excluded from MVP 1

- Departmental Contribution or Departmental Submission
- Routine planning-stage HoD sign-off
- Departmental planning workbench
- Cross-OU aggregation
- Planning edits to HoD-owned Demand facts
- Targeted HoD reapproval workbench
- Generic statutory, Strategy or public-value treatment questionnaire
- Item-level planned-treatment or generic reserved-value field
- User-maintained statutory percentages
- Planning Inclusion, Procurement Package, Package Line, Release Package or Consumption workbench
- Detailed Tender lot configuration
- Tender evaluation, award, contract, commitment or expenditure entry
- Live financial-system replacement
- Manual actual-milestone entry where downstream evidence exists
- Advanced analytics or claimed realised benefits without downstream evidence

## 6. Actors and responsibilities

| Actor | Planning responsibility | Explicitly cannot |
|---|---|---|
| Requester | View permitted neutral lineage | Open Finance or professional approval task forms |
| Head of Department / Business Approver | Approve or return the Demand in Demands | Reapprove ordinary procurement-owned Planning decisions |
| Procurement Planner | Create Plan; select Approved Demand; complete Plan Item; validate and submit | Approve own professional decision; change Approved Demand facts; confirm Finance |
| Budget Officer / Finance authority | Confirm proposed Budget Line, amount and availability; reserve or return | Edit procurement method or approve the Plan Version |
| Head of Procurement / professional authority | Review completeness and approve or return the Plan Version | Bypass current Finance confirmation or edit Plan Items in the task form |
| Tender Initiator | Create Tender from eligible Active Plan Item | Take up Draft, superseded, stale-funded or unauthorised item |
| Viewer / Auditor | View permitted neutral records, decisions and evidence | Open or call mutation task routes |
| Administrator | Configure system and receive explicit operational scope when needed | Gain implicit PE/OU scope or workflow authority merely through Administrator status |

## 7. State model

### 7.1 Logical Plan

- Open
- Closed
- Cancelled

### 7.2 Plan Version

- Draft
- In review
- Returned
- Approved
- Superseded
- Cancelled

Rules:

- One logical Plan exists per PE and financial year.
- At most one current Approved Version exists.
- At most one editable Draft successor exists.
- Approved, Superseded and Cancelled Versions are immutable.

### 7.3 Plan Item

- Proposed — exists only in a Draft/Returned Version
- Active — included in the current Approved Version
- Removed — excluded from an editable Draft when it existed only in that Draft, or intentionally omitted by an Approved successor; identity, sources, decisions and audit history remain

### 7.4 Separate projections

These are not Plan statuses:

- Validation: Not run, Ready, Needs attention, Blocked, Stale
- Finance confirmation: Not requested, Awaiting confirmation, Confirmed, Returned, Stale
- Publication: Not submitted, Queued, Published, Failed, Not applicable
- Tender take-up: Not taken up, Tender in preparation, Tender active, Contracted, Closed downstream

## 8. User journeys

### 8.1 Initial Plan

1. Planner selects authorised PE and financial year and creates Draft Version 1.
2. Planner selects one or more Planning Ready Approved Demands.
3. With one selected Demand, the system creates one Proposed Plan Item. With multiple selected Demands, the planner explicitly chooses separate Plan Items or one compatible combined Plan Item.
4. The system creates the resulting Proposed Plan Item(s) and Draft Need Item allocations transactionally; the planner then completes procurement-owned fields.
5. Planner requests Finance confirmation.
6. Budget Officer confirms/reserves or returns to planner.
7. Planner submits the Ready Plan Version for professional review.
8. Head of Procurement approves or returns it.
9. Approval locks the Version and activates its Plan Items.
10. Authorised Tender role creates a Tender from an eligible Active Plan Item.

### 8.2 Add Approved Demand(s) to an Approved Plan

1. Planner selects **Add Plan Item** on the Approved Plan.
2. System shows PLN-UI-04; the user does not create a revision manually.
3. The planner selects one or more Demands and, where multiple are selected, chooses separate or compatible combined formation.
4. On confirmation, the server creates or reuses one Draft successor and creates the resulting Proposed Plan Item(s) atomically.
5. Planner completes the new Plan Item(s) in PLN-UI-06.
6. Existing Active items and Tender handoffs in the current Approved Version remain operational.
7. Finance confirms the new item(s).
8. Planner submits the Draft successor for professional review.
9. Approval supersedes the old Version, activates the addition and preserves unchanged item identity and handoffs.

### 8.3 Material upstream change

If the owner OU, business scope, quantity, delivery requirement or approved estimate must change materially:

1. Planning does not edit the fact.
2. The user is directed to amend the Demand.
3. HoD reapproves the amended Demand in Demands.
4. Planning refreshes or replaces the Draft source allocation as permitted.

No targeted Planning-stage HoD workbench is created in MVP.

### 8.4 Multi-Demand Plan Item formation

- PLN-UI-04 allows selection of one or more Approved Demands.
- With one selected Demand, formation controls remain hidden and one Plan Item is created.
- With multiple selected Demands, **Plan Item formation** becomes required: **Create separate Plan Items** or **Combine into one Plan Item**.
- Separate formation creates one actual Plan Item per selected Demand.
- Combined formation is enabled only when all selected Demands share PE and owning OU and pass compatibility checks.
- Combined formation requires a reason.
- Every Demand and Need Item retains Budget, funding, approval and allocation lineage.
- `Keep separate` is not stored as a cosmetic value on one combined item.

### 8.5 Remove a Plan Item

Removal is initiated from the Plan builder/update view, not from the Plan Item editor.

1. The authorised planner opens the row action and selects **Remove from draft** for a draft-only Proposed item, or **Propose removal** for an eligible Active item carried into a Draft successor.
2. The system shows one compact confirmation dialog with the item, value, source Demand(s), funding effect and one required business reason.
3. Removing a draft-only Proposed item takes effect immediately in the editable Draft, preserves an audit tombstone, cancels any open Finance task and releases any draft-stage reservation atomically. Its source Demand allocation(s) return to the eligible queue.
4. Proposing removal of an Active item records a removal change only in the Draft successor. The current Approved Version, reservation and item remain operational until successor approval; its source Demand(s) do not become eligible yet.
5. On successor approval, the Active item becomes Removed, its unconsumed reservation is released atomically and its source Demand allocation(s) return to the eligible queue.
6. An item with a Tender handoff or other downstream execution cannot be removed in MVP. The action is absent and the server rejects direct calls. Cancellation or amendment of downstream procurement is a separate lifecycle.
7. A combined Plan Item is removed as one whole item. MVP does not remove an individual source from an already formed combined item; the planner removes the item and reforms it from the intended source Demands.
8. If removal leaves a Draft successor with no effective changes, the system shows **No changes remain** and requires the planner to cancel the empty update; it does not submit a no-op Version.

## 9. Functional requirements

### 9.1 Workspace and scope

| ID | Requirement |
|---|---|
| PLN-FR-001 | The module shall provide one PE/FY-scoped Planning workspace with the current Plan and actionable work. |
| PLN-FR-002 | Zero eligible PE scopes shall block operational use with a clear explanation. |
| PLN-FR-003 | One eligible PE shall remain visibly selected; multiple eligible PEs shall require deliberate selection. |
| PLN-FR-004 | The system shall never select the first PE/OU silently or use an Administrator fixture fallback. |
| PLN-FR-005 | Queues, counts, totals, exports and notifications shall enforce the same server-side scope. |

### 9.2 Plan registration

| ID | Requirement |
|---|---|
| PLN-FR-010 | Plan registration shall capture PE, financial year, title, currency and coordinating procurement unit. |
| PLN-FR-011 | Planning period dates shall be derived from the financial year and read-only. |
| PLN-FR-012 | Currency and coordinating procurement unit shall be governed selections; a single eligible value may be shown read-only. |
| PLN-FR-013 | Internal Plan references shall be generated. |
| PLN-FR-014 | Plan registration shall not capture free-text Budget context. |
| PLN-FR-015 | One logical Plan per PE/FY and one open Draft-successor invariant shall be enforced transactionally. |

### 9.3 Demand eligibility and Plan Item formation

| ID | Requirement |
|---|---|
| PLN-FR-020 | Only authorised, Approved, Planning Ready and not-fully-planned Demands shall be selectable. |
| PLN-FR-021 | PLN-UI-04 shall allow the planner to select one or more eligible Approved Demands using row checkboxes. |
| PLN-FR-022 | One selected Demand shall create one Proposed Plan Item without showing a formation choice. |
| PLN-FR-023 | Each available Need Item shall be represented by a distinct Draft Plan Demand Allocation. |
| PLN-FR-024 | Selection shall not mutate the Demand or create a Finance decision. |
| PLN-FR-025 | With multiple selected Demands, PLN-UI-04 shall require **Create separate Plan Items** or **Combine into one Plan Item** before confirmation. |
| PLN-FR-026 | Separate formation shall create one Proposed Plan Item per selected Demand; combined formation shall create one Proposed Plan Item with allocations from every selected Demand. |
| PLN-FR-027 | On an Approved Plan, Draft-successor creation/reuse and all resulting Plan Item/allocation creation shall be one atomic server action. |
| PLN-FR-028 | PLN-UI-06 shall edit the created Plan Item and shall not reselect or reallocate its source Demand(s). |

### 9.4 Plan Item field register

| Field | Type and owner | Source/condition | Operational effect |
|---|---|---|---|
| Demand title, Need Items, owner OU, approved value and requested delivery | Read-only | Approved Demand snapshot; always | Preserves HoD-approved facts |
| Proposed Budget Line and Finance state | Read-only | Funding allocation context; always | Identifies the funding decision Finance must make |
| Strategy targets / Strategy Value Commitments | Read-only | Approved upstream lineage; when present | Preserved into Planning handoff |
| Plan Item description | Multiline; Planner | Always | Defines procurement-facing summary without changing business scope |
| Category | Searchable governed select; Planner | Always | Drives method/STD recommendations and reporting |
| Governing regime | Derived read-only | Applicable legal/funding context | Drives permitted methods |
| Recommended method and basis | Derived read-only | Regime, category, value and configuration | Supports explainable method decision |
| Confirmed method | Governed select; Planner | Always | Defines planned market approach |
| Alternative-method grounds and reason | Conditional governed input and multiline reason | Only when confirmed method differs from recommendation | Supports lawful exception and review |
| Arrangement | Governed select; Planner | Always | Single-year or multi-year planning treatment |
| Indicative lotting decision | Radio; Planner | Always | Signals likely Tender structure |
| Expected lot count and basis | Conditional number and multiline inputs | Only when indicative lots are expected | Informs Tender preparation; does not create Plan Items |
| Planned milestone dates | Date inputs; Planner | Always | Defines implementation schedule and validation basis |

The ordinary editor shall not contain aggregation controls, Departmental Contribution, HoD sign-off, generic statutory/Strategy treatment, preference/reservation scheme inputs, planned-treatment/reserved-value inputs, Plan-level coverage placeholders or editable upstream facts.

### 9.5 Aggregation, separation and lotting

| ID | Requirement |
|---|---|
| PLN-FR-030 | Multi-Demand formation shall be decided in PLN-UI-04 during the same source-selection task. |
| PLN-FR-031 | **Combine into one Plan Item** shall be enabled only when all selected Demands share the same PE and owning OU and pass compatibility checks. |
| PLN-FR-032 | Combined formation shall require a reason and preserve source allocation lineage. |
| PLN-FR-033 | Cross-OU aggregation shall be blocked in MVP. |
| PLN-FR-034 | Planning Need Items separately shall create actual separate Plan Items and require an anti-splitting reason/check. |
| PLN-FR-035 | Indicative lots shall remain within one Plan Item and shall not create or split Plan Items. |

### 9.6 Finance confirmation

| ID | Requirement |
|---|---|
| PLN-FR-040 | A completed Plan Item shall create one actionable Finance task for the authorised Budget Officer. |
| PLN-FR-041 | The task shall show Plan Item/version, source Demand allocation, proposed Budget Line, amount and current availability. |
| PLN-FR-042 | Finance may Confirm funding or Return to planner; a return reason is required. |
| PLN-FR-043 | Confirm funding shall atomically validate availability, create or confirm the reservation, and record actor, time and Plan Item/version context. |
| PLN-FR-044 | Finance confirmation shall become Stale when relevant funding allocation or Plan Item value changes. |
| PLN-FR-045 | No earlier Demand-stage Finance approval shall remain as a duplicate sign-off. |
| PLN-FR-046 | Requesters and other unauthorised roles shall not see or open the Finance task form. |
| PLN-FR-047 | When current availability is less than the amount required, PLN-UI-07A shall show the available amount, exact shortfall and **Insufficient funding** status. |
| PLN-FR-048 | A shortfall shall remove the Confirm funding action and shall not permit partial confirmation, negative availability, manual override or silent reduction of the Plan Item value. |
| PLN-FR-049 | The Budget Officer may keep the task Awaiting confirmation and open the governed Budget & Funding resolution route, or Return to planner with a required reason; Return is not final rejection. Budget changes occur only in Budget & Funding, and the same Finance task shall revalidate without duplication after resolution. |

### 9.7 Validation and professional approval

| ID | Requirement |
|---|---|
| PLN-FR-050 | Validation shall show business-readable issues using Not run, Ready, Needs attention, Blocked and Stale. |
| PLN-FR-051 | Submission for review shall require complete Plan Items, current Finance confirmation and no blocking issue. |
| PLN-FR-052 | Submission shall not require Departmental Submission, contribution or routine HoD planning sign-off. |
| PLN-FR-053 | PLN-UI-08 shall show Plan/version summary, Plan Items, issues, Finance state, derived supported preference/reservation coverage and decision history. |
| PLN-FR-054 | The authorised professional authority may Approve or Return to planner; a return reason is required. |
| PLN-FR-055 | Approval shall lock the Version and item snapshots, activate Proposed items, make allocations effective once and supersede the prior Approved Version when applicable. |
| PLN-FR-056 | Preference/reservation coverage shall appear only when it can be derived from governed supported data; otherwise the section shall be omitted and shall not block approval. |

### 9.8 Revision and Approved Plan operation

| ID | Requirement |
|---|---|
| PLN-FR-060 | Approved Versions shall be immutable. |
| PLN-FR-061 | Add Plan Item shall create or reuse one Draft successor without a manual revision step. |
| PLN-FR-062 | The current Approved Version and existing Tender handoffs shall remain operational while the successor is Draft/In review/Returned. |
| PLN-FR-063 | PLN-UI-05 shall focus on changed items and show unchanged operational items as read-only context. |
| PLN-FR-064 | An addition after approval shall capture one concise update reason. |
| PLN-FR-065 | Approval of the successor shall atomically replace the current Version without duplicating unchanged item identity or handoffs. |
| PLN-FR-066 | A scoped Procurement Planner shall be able to remove a draft-only Proposed Plan Item from the editable Draft or propose removal of an eligible Active Plan Item through the Draft successor. |
| PLN-FR-067 | Removal shall require one business reason, preserve the Plan Item, source allocations, decisions and audit history, and shall never hard-delete or edit an Approved Version in place. |
| PLN-FR-068 | Draft-only removal shall atomically exclude the item, cancel its open Finance task, release any draft-stage reservation and restore its source Demand allocation(s) to Planning eligibility. |
| PLN-FR-069 | Active-item removal shall become effective only on successor approval. Until then the current Approved item and reservation remain operational; approval shall recheck that no Tender/downstream handoff exists, then mark the item Removed, release unconsumed reservation and restore source eligibility atomically. |
| PLN-FR-069A | Items with a Tender handoff or downstream execution shall not expose removal and shall be rejected by the server. Combined Plan Items shall be removable only as a whole in MVP. |

### 9.9 Publication, Tender handoff and monitoring

| ID | Requirement |
|---|---|
| PLN-FR-070 | Publication shall use the current Approved Version and retain destination, status, time and evidence. |
| PLN-FR-071 | Publication failure shall create an operational issue without reversing Plan approval. |
| PLN-FR-072 | Tender take-up shall require an Active Plan Item in the current Approved Version with current funding and remaining take-up. |
| PLN-FR-073 | Tender take-up shall atomically create an immutable Planning Handoff Snapshot. |
| PLN-FR-074 | The handoff shall preserve Plan, Plan Item/version, Demand allocations, Finance/reservation and Strategy lineage. |
| PLN-FR-075 | Implementation and actual milestones shall be derived from downstream records. |
| PLN-FR-076 | Reporting shall show scope, reporting period, As at, planned value, take-up and schedule variance without claiming realised value unsupported by downstream evidence. |

### 9.10 Visibility, tasks and mutations

| ID | Requirement |
|---|---|
| PLN-FR-080 | Record visibility, task visibility and mutation authority shall be evaluated separately. |
| PLN-FR-081 | An unauthorised user shall not see Review, Approve, Return, Confirm funding or similar task actions. |
| PLN-FR-082 | Direct navigation and API calls to unauthorised task forms/actions shall be rejected server-side. |
| PLN-FR-083 | A permitted viewer may see a neutral read-only detail and permitted completed decision history. |
| PLN-FR-084 | Administrator status alone shall confer neither PE/OU scope nor operational task authority. |

## 10. Readiness rules

### 10.1 Request Finance confirmation

A Plan Item is ready to request Finance confirmation when:

- source Demand and allocations remain eligible;
- procurement description and category are complete;
- method and any conditional grounds are complete;
- arrangement and indicative lotting are complete;
- milestone dates are complete and chronologically valid; and
- no blocking source or scope issue exists.

### 10.2 Submit Plan for review

A Draft Plan Version is ready when:

- every included Plan Item is complete and valid;
- every applicable Plan Item has current Confirmed Finance state;
- all source allocations reconcile to approved available amounts;
- no blocking validation issue remains; and
- the update reason is complete for a post-approval change; and
- at least one effective change remains in a Draft successor.

### 10.3 Approve Plan Version

Approval requires:

- authorised professional task and PE scope;
- current Draft/In review Version;
- current validation run marked Ready;
- current Finance confirmation for every applicable item; and
- no concurrent version conflict.

### 10.4 Tender take-up

Take-up requires:

- Active Plan Item in the current Approved Version;
- current funding/reservation lineage;
- approved method and valid scope;
- remaining take-up availability; and
- authorised Tender Initiator scope.

## 11. Clean domain model

| Record | Responsibility |
|---|---|
| Procurement Plan | Stable PE/FY container and logical lifecycle |
| Procurement Plan Version | Draft/review/Approved immutable consolidated baseline |
| Procurement Plan Item | Stable execution identity across Versions |
| Procurement Plan Item Version | Version-specific planning decisions and snapshots |
| Plan Demand Allocation | Need Item quantity/value lineage to one Plan Item |
| Plan Decision | Professional review/return/approval evidence |
| Plan Validation Result | Validation run and business-readable issues |
| Planning Handoff Snapshot | Immutable source for Tender take-up |

Finance confirmation shall reuse the existing Demand Funding Allocation, Budget availability/reservation service and existing decision/audit foundation, extended with Plan Item/version context where required. It shall not introduce a generic approval engine or separate Finance workbench.

`Departmental Submission` is removed from the clean MVP domain.

## 12. Service and integration contract

### 12.1 Required capabilities

The implementation shall provide these capabilities without requiring a second public alias solely to satisfy document wording:

- create/register annual Plan;
- return scoped Planning workspace projection;
- list eligible Approved Demands;
- add one or more selected Demands to a Plan atomically using an explicit formation mode when multiple are selected;
- save one existing Draft Plan Item Version;
- validate Plan/Version;
- request and record Finance confirmation/return;
- submit Plan Version for professional review;
- record return/approval decision;
- approve Plan Version atomically;
- open/reuse/cancel Draft successor;
- remove a draft-only Proposed Plan Item or record an eligible Active-item removal in the Draft successor;
- publish/export current Approved Version;
- create Tender handoff from eligible Plan Item;
- return implementation and audit projections.

Repository public service names are authoritative when already used and semantically correct. Requirements define behaviour, not duplicate aliases. The Cursor traceability table shall map each capability to the actual service name and tests.

### 12.2 Integration boundaries

| Module | Planning interaction |
|---|---|
| PE/OU Scope | Authorised entity/unit options and server-side enforcement |
| Strategy | Read immutable targets and Strategy Value Commitment snapshots |
| Budget & Funding | Read proposed allocation; validate and reserve through Finance confirmation |
| Demands | Read Approved Demand/Need Items; never rewrite approved facts |
| Tender | Create immutable handoff; read take-up and actual milestones |
| Publication | Send Approved Plan projection and retain evidence |
| Audit/Notifications | Record material events and notify task owners |

## 13. Minimum screen families

| Screen | Purpose |
|---|---|
| PLN-UI-01 | Scoped Planning workspace |
| PLN-UI-02 | Create annual Plan |
| PLN-UI-03 | Empty Draft Plan builder |
| PLN-UI-04 | Select one or more Approved Demands and choose separate or compatible combined formation when needed |
| PLN-UI-05 | Unified populated Draft builder for initial and successor Versions |
| PLN-UI-05A | Remove Plan Item confirmation dialog, reused for draft removal and proposed removal |
| PLN-UI-06 | Focused Plan Item editor |
| PLN-UI-07 | Finance funding confirmation task — sufficient-funding state |
| PLN-UI-07A | Finance funding confirmation task — shortfall state |
| PLN-UI-08 | Head-of-Procurement review and approval task |
| PLN-UI-09 | Approved Plan and implementation |

Screen composition is controlled by Stitch v2.0. Requirements control behaviour, ownership, state and authority.

## 14. Canonical seed contract

### 14.1 Principal Ministry story

- PE: Ministry of Health
- Secondary PE: County Government of Kisumu with minimal isolated data
- FY: 2027/28
- Budget Line allocation: KES 480,000,000
- Approved Demand / principal Plan Item: KES 455,000,000
- Owner OU: Directorate of Digital Health and Policy
- Plan Item: PPI-MOH-2027-021
- Finance confirmation follows Plan Item completion and reserves KES 455,000,000
- Later commitment fixture: KES 310,000,000
- Remaining reservation fixture: KES 145,000,000
- Tender: TND-MOH-2027-008

### 14.2 Post-approval addition

- Returned Demand history: KES 95,000,000
- Corrected and HoD-approved Demand: KES 80,000,000
- New Proposed Plan Item: PPI-MOH-2027-022
- Approved Version 1 remains operational at KES 455,000,000
- Draft Version 2 totals KES 535,000,000
- Finance confirmation occurs after the new Plan Item is complete
- Approval activates the new item and supersedes Version 1 without disrupting unchanged handoffs

### 14.3 Seed invariants

- Stable identities and idempotent loading
- Explicit roles and PE/OU scopes for Requester, HoD, Planner, Budget Officer, Head of Procurement and Viewer
- No generic treatment rows
- No Departmental Submission/contribution rows
- No routine planning-stage HoD-sign-off records
- No cosmetic `Keep separate` value
- Running the canonical seed twice produces no duplicates and reconciles all amounts

### 14.4 Optional removal scenario

- `SCN-PLN-REMOVE-001` starts after Proposed `PPI-MOH-2027-022` has been added to Draft Version 2 and before Finance confirmation.
- Removing the item records the required reason **Added for demonstration; remove from this draft**, returns `DMD-MOH-2027-019` to Planning eligibility, restores the Draft total from KES 535,000,000 to KES 455,000,000 and leaves Approved Version 1 and `TND-MOH-2027-008` unchanged.
- Reset restores the pre-removal Draft Version 2 state without duplicating items, allocations or audit events.

## 15. Non-functional requirements

- **Security:** server-side role, task and PE/OU scope enforcement on every read and mutation.
- **Audit:** actor, role, time, record/version, before/after state and reason for every material decision.
- **Atomicity:** Plan formation, Finance confirmation, approval and Tender handoff must not leave partial state.
- **Idempotency:** retries and scenario reruns must not duplicate records or events.
- **Concurrency:** stale Version and double-submit protection.
- **Performance:** compact list projections; avoid loading complete histories into workspace tables.
- **Accessibility:** labelled controls, keyboard operation, visible focus, error association and meaningful status text.
- **Explainability:** method, validation and decision messages use business-readable language.
- **Maintainability:** one public capability per behaviour; no compatibility aliases or dual-write for disposable MVP structures.

## 16. Acceptance criteria

| ID | Acceptance criterion |
|---|---|
| PLN-AC-001 | A multi-PE planner deliberately selects PE; zero scope blocks; one scope remains visible. |
| PLN-AC-002 | One selected Approved Demand creates exactly one Proposed Plan Item; formation controls remain hidden. |
| PLN-AC-003 | PLN-UI-06 completes the item without selecting or allocating the Demand again. |
| PLN-AC-004 | The item editor contains only the approved field register and no generic treatment/contribution controls. |
| PLN-AC-005 | Material HoD-owned facts cannot be changed in Planning and direct the user to Demand amendment. |
| PLN-AC-006 | Planning Ready does not imply Finance approval or reservation. |
| PLN-AC-007 | Budget Officer can Confirm fully available funding, keep a shortfall task pending while resolving it through Budget & Funding, or Return to planner; unauthorised users cannot open the task. |
| PLN-AC-008 | Finance confirmation atomically reserves the approved amount and becomes stale after relevant change. |
| PLN-AC-009 | Submit for review requires current Finance confirmation and never requires Departmental Submission or second HoD sign-off. |
| PLN-AC-010 | Head of Procurement can Approve or Return; Requester/Planner/Administrator-without-task cannot open the task form. |
| PLN-AC-011 | Approved Version and item snapshots are immutable. |
| PLN-AC-012 | Add Plan Item to an Approved Plan quietly creates/reuses one Draft successor. |
| PLN-AC-013 | Approved Version 1 and its Tender remain operational throughout Draft Version 2 preparation. |
| PLN-AC-014 | Selecting multiple compatible same-PE/same-OU Demands and choosing Combine creates one Plan Item while preserving every source allocation and the reason. |
| PLN-AC-015 | Selecting multiple Demands and choosing Separate creates one actual Plan Item per Demand; no cosmetic `Keep separate` state remains. |
| PLN-AC-016 | Cross-OU aggregation is unavailable and rejected server-side. |
| PLN-AC-017 | Preference/reservation coverage is read-only, derived only from governed supported data and omitted otherwise. |
| PLN-AC-018 | Strategy targets and Strategy Value Commitments pass through unchanged with no Planning-authored treatment note. |
| PLN-AC-019 | Tender take-up is allowed only from an eligible Active item and creates one immutable handoff. |
| PLN-AC-020 | Canonical seed and post-approval scenario run twice without duplication and with correct arithmetic. |
| PLN-AC-021 | Neutral record visibility does not expose Finance or approval task forms/actions. |
| PLN-AC-022 | A shortfall state shows the exact deficit, prevents confirmation and overrides, and returns to Confirmable on the same task only after governed funding resolution. |
| PLN-AC-023 | A planner can remove a draft-only Proposed item from PLN-UI-05 through one confirmation; the item disappears from the Draft projection, history remains and its source Demand becomes eligible again. |
| PLN-AC-024 | Removing a Finance-confirmed draft-only item cancels the open task and releases its reservation once; a retry creates no duplicate release or audit event. |
| PLN-AC-025 | Proposing removal of an Active item creates/reuses a Draft successor while the current Approved item remains operational and its Demand remains unavailable for replanning. |
| PLN-AC-026 | Successor approval makes an eligible proposed removal effective atomically; a concurrent/new Tender handoff blocks removal approval. |
| PLN-AC-027 | An item with Tender/downstream execution has no removal action and direct service calls are rejected. A combined item can be removed only as a whole. |

## 17. Explicit removals from v1.5

Remove from requirements, schema, services, UI, seeds and tests where present:

- Departmental Submission record
- Departmental Contribution status and workflow
- superseded contribution drawer formerly labelled PLN-UI-07
- `submit_departmental_contribution` capability
- routine planning-stage HoD sign-off
- contribution readiness and approval gates
- generic statutory allocation treatment/rationale
- generic Strategy/value-treatment note
- item-level preference/reservation scheme, target-group and planned-value controls
- zero-filled planned-treatment records
- Finance approval before Plan Item completion
- Administrator operational fallback
- disabled restricted task forms shown to unauthorised users

## 18. Approval decision

Version 1.9 is the complete controlling Procurement Planning Requirements baseline. Version 1.8 and earlier are superseded for implementation. Any new field, approval, record or workflow requires a new approved Requirements version and must pass the field/concept admission rule in `KENTENDER-MVP-CMOM-1.1`.
