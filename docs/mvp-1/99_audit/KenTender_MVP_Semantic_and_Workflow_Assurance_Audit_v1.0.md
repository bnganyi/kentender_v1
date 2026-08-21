# KenTender MVP Semantic and Workflow Assurance Audit

**Document ID:** KENTENDER-MVP-SWA-1.0  
**Version:** 1.0  
**Date:** 11 August 2026  
**Status:** Draft for user validation — not approved for implementation  
**Scope:** Strategy Alignment, Budget & Funding, Demands, Procurement Planning, shared organisation scope, authorisation surfaces and canonical demo data  

## 1. Decision and immediate control

The current module documents are **provisional evidence**, not approved authority. New feature design and implementation should remain frozen until the corrections in this audit are accepted and the affected documents are reissued.

This audit does not silently rewrite the modules. It identifies what is sound, what is wrong, what must be removed, and what requires an explicit product decision.

The governing rule is:

> KenTender shall omit a feature, field, record or workflow stage unless its real-world task, accountable actor, source, state change and downstream use can all be stated plainly.

No document may mark itself `Approved`, `Locked` or an implementation baseline without an explicit recorded approval by the product owner.

## 2. Why the assurance audit is necessary

The documents contain several classes of semantic failure:

1. **Invented business objects.** Procurement Planning introduced `Departmental Submission` and “unit contributions” even though the agreed operating model is that the Procurement Planner prepares the Plan Items and the responsible Head of Department signs them off.
2. **Generic questionnaires without an operational consequence.** Strategy, Budget, Demand and Planning introduced overlapping “value treatment,” “funding treatment,” “statutory treatment,” rationale and planned-treatment fields.
3. **Workflow multiplication.** Legal evidence or sign-off was sometimes converted into a separate preparation workflow, record and status projection.
4. **Version and authority drift.** Stitch and Cursor packs cite superseded requirements or seed versions, while several documents self-declare approval.
5. **Uncontrolled vocabulary.** Similar concepts are named differently across modules and implementation packs.
6. **Screen sprawl.** A small number of required user tasks became many screens, tabs or specialised workbenches.

These are product-model failures. They cannot be corrected reliably by relabelling fields in isolated screens.

## 3. Evidence baseline

### 3.1 Kenyan legal baseline

The relevant legal requirements are retained without creating extra workflow objects:

- Section 53 of the Public Procurement and Asset Disposal Act requires a realistic annual procurement plan within the approved budget, sufficient funds before procurement begins, applicable preference and reservation allocations, approval and publication.
- Regulations 40–42 require annual planning, a departmental plan submitted by the Head of User Department, a consolidated annual plan, prescribed plan contents and use of the prescribed format.
- Regulation 41 requires the consolidated plan to cover the requirement, schedule, single- or multi-year treatment, aggregation, lots, value, funding source, method, applicable transfer timing and incidental costs.
- Regulation 71 treats the later requisition against the approved plan as the initiation of the procurement process.

Primary sources:

- [Public Procurement and Asset Disposal Act, section 53](https://new.kenyalaw.org/akn/ke/act/2015/33/eng%402022-12-31)
- [Public Procurement and Asset Disposal Regulations, regulations 40–43 and 71](https://new.kenyalaw.org/akn/ke/act/ln/2020/69/eng%402020-12-24)

The legal requirement for a departmental plan does **not** prescribe a separate KenTender contribution authoring workbench. A recorded Head-of-Department sign-off over the completed, OU-scoped Plan Items can provide the submission evidence without duplicating the planner's work.

### 3.2 Product decisions already established

The following decisions are treated as the current product truth:

1. KenTender supports any public Procuring Entity; it does not assume a Ministry hierarchy.
2. Every owned record has one `procuring_entity` and, where applicable, one `owner_org_unit`.
3. Users with one authorised creation scope see it explicitly; users with several scopes choose; users with none are blocked. No first-row, workspace-filter or Administrator fallback is allowed.
4. Technical and business references are system-generated. Users do not maintain codes.
5. The canonical lifecycle spine is:

   **Strategy → Budget & Funding → Demand → Procurement Plan Item → Tender → Contract**

6. Upstream facts are inherited downstream and are not re-entered or silently changed.
7. The Requester describes the need. Procurement confirms procurement and Strategy context. The Budget Officer confirms every funding assignment. The Procurement Planner prepares Plan Items.
8. The Head of Department or OU owner signs off the completed OU-owned planning entries; the OU does not author a separate “contribution.”
9. The Plan Item is the operational unit. The Plan Version is the approval and immutability boundary.
10. Adding an Approved Demand to an Approved Plan quietly opens or reuses one Draft successor. The current Approved version remains operational until the revision is approved.
11. Strategy Value Commitments flow downstream as governed context. A consuming module may add a concrete decision only when that module owns a real operational decision.
12. Unauthorised workflow tasks and forms are absent, not merely disabled.

## 4. Mandatory concept-admission gate

Every proposed entity, field, status, action, screen, tab, service or notification must pass all of the following questions before it enters requirements:

| Gate | Required answer |
|---|---|
| Real-world task | What recognisable business task is being completed? |
| Accountable actor | Who owns the decision or fact? |
| Preparation actor | Who supplies the content, if different? |
| Source | Is the value entered, selected, inherited, calculated or received by integration? |
| State consequence | What record or state changes when the user completes the task? |
| Downstream consumer | Which later task or control uses the value? |
| Legal or business basis | Why must KenTender retain it? |
| Omission consequence | What fails if it is absent? |
| UI necessity | Why must a user see or edit it on this screen? |
| Testability | What observable test proves the requirement? |

If any answer is missing or circular, the concept is excluded from MVP 1. “For completeness,” “for reporting,” “for audit” and “future use” are not sufficient answers without a named consumer and consequence.

Rationale fields are conditional exception evidence. They shall not appear by default simply because a design has room for them.

## 5. Authoritative cross-module operating model

| Module | Primary user task | Authoritative records | Required decision actors | Output to next module |
|---|---|---|---|---|
| Strategy Alignment | Define approved outcomes, targets and Strategy Value Commitments; record verified performance | Strategic Plan Version, Strategy node/target, Strategy Value Commitment, Measurement | Strategy preparer, reviewer/approver, performance verifier | Valid versioned Strategy references and commitments |
| Budget & Funding | Register the approved procurement funding baseline and control its availability | Budget, Budget Line, Reservation, Commitment; external expenditure snapshot only when integrated | Budget Officer, Budget Reviewer, Budget Authority | Confirmed Budget Line allocation and reservation |
| Demands | Capture, enrich, fund and approve a business need | Demand, Need Item, stage decisions, funding allocation, approved snapshot | Requester, Business Approver, Procurement, Budget Officer, final Demand approver | Approved, funded Demand with inherited Strategy context |
| Procurement Planning | Convert Approved Demands into executable Plan Items and approve the consolidated Plan Version | Procurement Plan, Plan Version, Plan Item, Plan Item Version, Demand Allocation, Plan Decision, Handoff Snapshot | Procurement Planner, Head of Department/OU signatory, professional reviewer, configured Plan approver | Active Plan Item and immutable Tender handoff |

The table is a boundary. A downstream module may consume an upstream record but may not recreate it under a new name.

## 6. Cross-module concept verdicts

### 6.1 Keep

| Concept | Reason |
|---|---|
| Generic Procuring Entity and Organisation Unit scope | Required for national applicability and data ownership |
| Explicit zero/single/multiple creation-scope behaviour | Prevents silent cross-entity attribution |
| Versioned approved records | Preserves immutable legal and operational baselines |
| System-generated references | Removes user-maintained codes while retaining traceability |
| Versioned Strategy target reference and readable snapshot | Gives stable downstream lineage |
| Strategy Value Commitment | User-required downstream Strategy linkage, provided it is simplified as described below |
| Budget header and Budget Lines | Minimum funding-control baseline |
| Mandatory Budget Officer confirmation on each Demand | Established control even when matching is automatic |
| Reservation following Demand through Planning and Tender | Prevents duplicate holds |
| Plan, Plan Version, Plan Item, Plan Item Version and Demand Allocation | Clean separation of approval baseline and operational execution unit |
| Neutral record surface versus authorised task surface | Corrects role-based form exposure |
| Canonical, deterministic cross-module seed story | Provides repeatable development and demonstration evidence |

### 6.2 Correct

| Current concept | Correction |
|---|---|
| User-visible Strategy and hierarchy codes | Generate stable references; show meaningful titles and paths. Retain an optional external source reference only when one exists in an authoritative source document. |
| Unlimited overlapping Active strategic plans | Permit one Active primary entity/corporate plan for the same scope, type and effective period. Explicitly scoped supporting plans may overlap only when their purpose and scope are distinct. |
| `Plan Value Commitment` and varying public-value labels | Standardise the business term as **Strategy Value Commitment**. It is defined and approved in Strategy, then inherited downstream. |
| Budget Line must have exactly one primary target | Allow zero or more approved Strategy references according to actual budget structure. Do not force an artificial one-to-one relationship or block activation solely to populate it. |
| Demand duplicate/aggregation “treatment” | Demand may flag a possible duplicate or aggregation candidate. Planning owns the actual combine/separate decision. |
| Planning “Organisation Unit contribution” | Planner-prepared, OU-owned Plan Items followed by Head-of-Department/OU-owner sign-off. |
| Planning `Departmental Submission` record | Record the scoped sign-off as a `Plan Decision` with type `OU_SIGNOFF`, the signed item/version set, actor, date and declaration. Do not create a second authored submission aggregate. |
| Plan review readiness based on submitted contributions | Base readiness on all required OU sign-offs for the applicable changed items, plus plan validation. |
| Re-signing unchanged items in a revision | Require a new sign-off only for added or materially changed OU-owned items. Carry forward unchanged approved evidence. |
| Strategy/Budget/Demand/Planning approval-form visibility | Show a task form only to a user authorised for the current task. Other authorised viewers use a neutral read-only detail surface. |
| Document status vocabulary | Use Draft, Draft for validation, Approved by product owner, Superseded or Withdrawn. Approval must be externally recorded. |

### 6.3 Remove

The following concepts currently lack a defensible independent business purpose in MVP 1:

| Remove | Reason |
|---|---|
| Generic `Budget Value Treatment` / funding-treatment questionnaire | Duplicates Strategy commitments without controlling a real funding transaction |
| Generic `Demand Value Treatment` and “approved treatment” table | Repeats the same commitment as a narrative instead of carrying it forward |
| Generic Planning statutory/Strategy treatment fields | Already identified as indefensible; no operational consumer |
| Separate `Departmental Submission` / “contribution” authoring object | Duplicates the planner-authored Plan Items and misstates who prepares them |
| `Organisation Unit Planning Contributor` role for authoring Plan Items | Conflicts with the agreed planner-authored model |
| Default aggregation decision for one selected Demand | Ordinary source selection already creates one Plan Item; there is no decision to record |
| Blank or zero-filled inapplicable controls and rationale fields | Create false compliance data and unnecessary work |
| Administrator operational fallbacks | Violates explicit role and scope ownership |

Removal of generic value-treatment records does not remove Strategy Value Commitments. The commitment remains a read-only inherited reference until a downstream module owns a concrete, named decision such as a Tender specification, disclosed evaluation treatment or contract obligation.

### 6.4 Defer pending a separate approved case

| Concept | Why deferred |
|---|---|
| Reusable Public Value Objective Catalogue with applicability engine and enforcement-guidance routes | Substantial rules product with no yet-approved minimum operating case; it is the source of several generic downstream questionnaires |
| Strategy corrective-action workflow | Valuable but not necessary to establish Strategy-to-procurement traceability; retain only after the measurement workflow is validated |
| Funding Performance management dashboard | Can be derived later; operational balances and exceptions must work first |
| Manual or simulated Actual Expenditure operations | The financial system is authoritative and future integration is API-based |
| Demand Performance management dashboard | Not required to complete a Demand or hand it to Planning |
| Automated aggregation recommendations and benefit reporting | Candidate detection may be retained; decision automation and benefit claims need evidence and policy |
| Advanced publication/open-contracting portal behaviour | Preserve a clean handoff contract; implement the portal when its consumer is in scope |

Deferred does not mean prohibited. It means the concept must return through the admission gate with a focused user journey and evidence.

## 7. Module audit

### 7.1 Strategy Alignment

#### Preserve

- A versioned Strategic Plan with approved outcomes/targets.
- Versioned downstream Strategy references and readable snapshots.
- Strategy Value Commitments as approved business commitments.
- Separate target definitions and verified measurements.
- A read-only Strategy Performance entry point for authorised managers.

#### Correct before further implementation

1. Remove the expectation that users maintain plan, programme, outcome, indicator or target codes. Generate references and display titles/paths.
2. Replace `Plan Value Commitment` with the standard term `Strategy Value Commitment` across requirements, design, implementation and seeds.
3. A Strategy Value Commitment shall contain only fields that Strategy owns: commitment statement, linked Strategy scope, accountable owner, applicability description and approval/version evidence. It shall not prescribe a generic downstream “treatment.”
4. Define plan-overlap rules by plan type and ownership scope. “One Active version per code” is not sufficient when codes are generated and business users need protection from competing primary plans.
5. Reassess the Public Value Objective Catalogue and enforcement-guidance engine as deferred scope.
6. Align Stitch and Cursor to Requirements 1.1 or the next audited requirements version. They currently cite Requirements 1.0.
7. Rebuild the screen inventory. The current Strategy Stitch document does not provide the complete set of screens cited by the Cursor pack.

#### Status

Strategy Requirements 1.1, Stitch 1.0 and Cursor 1.0 are **provisional**. Stitch and Cursor are not safe implementation baselines.

### 7.2 Budget & Funding

#### Preserve

- Direct registration of a small approved Budget header and its Budget Lines.
- One Active procurement Budget per Procuring Entity and fiscal year.
- Budget Officer preparation, independent review and activation for procurement use.
- Available, reserved and committed calculations with no double-counting.
- Transactional, idempotent reservation and conversion contracts.
- Future API ownership for authoritative budget/expenditure facts.

#### Correct before further implementation

1. Remove `Budget Value Treatment` and all activation blockers that require generic funding-treatment records.
2. Strategy references on a Budget Line are optional, multiple and selected only where the approved budget structure supports them. They are not a forced one-primary-target classification.
3. Strategy Value Commitments are shown as inherited context only. No Dedicated/Embedded/No direct allocation/Not applicable questionnaire is required in MVP 1.
4. Funding-check and reservation controls remain operational services. Planning and Tender revalidate the existing reservation and never create a duplicate.
5. Actual expenditure is read-only and unavailable until an authoritative integration supplies it. The UI shall not invite manual entry or seed it as if it were a live fact outside a clearly labelled demo fixture.
6. Defer the Funding Performance dashboard until registration, activation, balance arithmetic, confirmation, reservation and revision are stable.

#### Status

Budget Requirements 1.1, Stitch prompts and Cursor pack are **provisional** and require a coherent new version.

### 7.3 Demands

#### Preserve

- Module name **Demands**.
- Progressive enrichment: Requester → Business Review → Procurement Enrichment → Budget Confirmation → Final Approval.
- Explicit PE/OU selection when the user has several eligible creation scopes.
- Requester does not select Strategy, Budget, method or planning data.
- Mandatory Budget Officer confirmation even for an automatically recommended Budget Line.
- Final approval and reservation are atomic.
- Approved means Planning Ready; planning usage is a separate projection.

#### Correct before further implementation

1. Remove `Demand Value Treatment`. Procurement confirms the primary Strategy alignment and receives applicable Strategy Value Commitments as read-only carry-forward context.
2. A possible duplicate or aggregation candidate is a flag and supporting evidence only. The Demand module does not decide the final Plan Item formation.
3. Replace references to “link Plan Items/packages” with Plan Items and Demand Allocations only.
4. Reduce Approved Demand detail to clearly separated business sections. Every tab must have a unique purpose; no Overview may duplicate all other tabs.
5. Defer the Demand Performance dashboard until the operational journey is stable.
6. Update all requirements and implementation references from Canonical Demo Data 2.4 to the next audited canonical version.
7. Remove duplicate requirement identifier `DIA-FR-001`.

#### Status

Demand Requirements 1.4, Stitch 1.5 and Cursor 1.5 are **provisional**. Their PE/OU selection and Budget Officer controls are retained; their value-treatment and baseline references are not.

### 7.4 Procurement Planning

#### Correct operating journey

1. The authorised planner opens or creates the annual Plan.
2. The planner selects **Add Plan Item**.
3. `PLN-UI-04` selects one eligible Approved Demand. Confirmation creates one Proposed Plan Item by default and, for an already Approved Plan, quietly creates or reuses the single Draft successor.
4. `PLN-UI-06` completes that already-created Plan Item: description, method, arrangement, schedule and indicative lots. It does not select the Demand again and does not ask a default aggregation question.
5. The responsible Head of Department/OU owner reviews the completed OU-owned item and records **Sign off** or **Return to planner**.
6. The professional reviewer reviews the consolidated Plan Version.
7. The configured authority approves the Plan Version.
8. Active Plan Items in the current Approved Plan Version can be taken up by Tender Management.

For a revision, only added or materially changed items require a new OU sign-off. Existing unchanged items and their downstream handoffs remain operational.

#### Aggregation and lotting boundary

- One Approved Demand selected through `PLN-UI-04` creates one Plan Item by default.
- Aggregation appears only when the planner explicitly adds another compatible Approved Demand to the same Draft Plan Item.
- Planning Need Items separately is an exceptional action that creates actual separate Plan Items and runs the anti-splitting control.
- Indicative lots describe the intended structure of the eventual Tender within one Plan Item. Lots do not create Plan Items and are not source aggregation.

#### Required document and screen corrections

1. Replace “One annual plan, many accountable contributors” with “One annual plan, planner-prepared Plan Items, accountable OU sign-off.”
2. Remove `Organisation Unit Planning Contributor` from the actor model.
3. Replace “Submit departmental contributions” with “Obtain OU sign-off on completed Plan Items.”
4. Rename `PLN-UI-07 Departmental contribution sign-off` to `PLN-UI-07 Organisation Unit Plan Item sign-off`.
5. PLN-UI-07 shows the completed OU-owned items, inherited Demand/funding context, planning decisions, and actions **Sign off** and **Return to planner**. It contains no contribution editor.
6. Keep `PLN-UI-08` as the consolidated Plan Version review/approval screen. It shows sign-off coverage, not contribution status.
7. Remove `Departmental Submission` from the domain model.
8. Store sign-off as `Plan Decision` type `OU_SIGNOFF` with `plan_version`, `owner_org_unit`, signed item-version set/hash, actor, time, declaration and decision.
9. Replace service `submit_departmental_contribution` with `record_ou_plan_signoff`.
10. Replace projection `Departmental contribution: Preparing / Submitted / Returned` with item-scoped sign-off state: `Pending sign-off`, `Signed off`, or `Returned to planner`.
11. Consolidated review readiness requires the applicable sign-offs, not a separate submitted contribution aggregate.
12. Update the canonical seed story: Mercy Kilonzo prepares the added Plan Item; the responsible Head of Department signs off `PPI-MOH-2027-022`; no contribution record is created.

#### Legal reconciliation

Regulation 40(3) requires the Head of User Department to submit an annual departmental procurement plan. In KenTender MVP 1, the OU-scoped item set in the consolidated Draft Plan Version is the electronic departmental plan content. The Head's recorded sign-off/submission decision is the evidence required by the regulation. The system does not need a duplicate Departmental Plan header, contribution editor or parallel item set.

#### Status

Planning Requirements 1.5, Stitch 1.6 and Cursor 1.4 are **withdrawn as implementation baselines** pending correction. Their Plan/Version/Item model, post-approval-addition path, field-admission rule and simplified `PLN-UI-06` are retained.

### 7.5 Organisation scope and authorisation

#### Preserve

- Generic PE/OU model and configurable hierarchy.
- Explicit User Scope Assignments.
- Server-side record, task, route and field projections.
- Neutral read-only record surfaces for viewers.
- Task forms absent for unauthorised users.
- No operational power from Administrator status alone.

#### Correct

1. Remove self-declared `Approved`/`Implementation baseline` status until user validation.
2. Test every role in every module against list actions, queues, counts, direct URLs, API reads, API mutations, exports and notifications.
3. Separate record visibility from task visibility and from mutation authority.

## 8. Screen-contract standard

Every Stitch screen prompt shall begin with this compact contract:

| Item | Required content |
|---|---|
| Screen purpose | One sentence describing the task |
| Primary actor | The role completing the task |
| Entry point | Exact prior action and screen |
| Reads | Authoritative records shown |
| Writes | Exact records or decisions changed |
| Primary actions | Buttons and outcomes |
| Exit/result | Destination and new state |
| Not this screen | Explicit adjacent tasks excluded |

Stitch may design only the stated visible content. It may not invent data, validation, workflow, roles, records, statuses or services.

Cursor implementation packs shall map each screen contract to requirements, domain records, services, permissions and tests. Cursor may not treat design copy as a new requirement.

## 9. Canonical demo-data audit

### 9.1 Story consistency retained

The following story is coherent and should be preserved:

- Ministry of Health principal Budget Line: KES 480,000,000.
- Principal Approved Demand and Active Plan Item: KES 455,000,000.
- Contract commitment: KES 310,000,000.
- Remaining reservation: KES 145,000,000.
- Returned certification Demand corrected from KES 95,000,000 to KES 80,000,000.
- Draft Revision 2 consolidated Plan value: KES 535,000,000.
- Approved Version 1 remains operational while Draft Revision 2 is prepared.
- County Government of Kisumu supplies a minimal, isolated second-entity story.

### 9.2 Required semantic corrections

The next canonical version shall:

1. remove Budget funding-treatment records;
2. remove Demand value-treatment records;
3. remove Planning contribution/Departmental Submission records;
4. retain Strategy Value Commitment identities as inherited references only;
5. retain explicit preference/reservation designation only where a real scheme is deliberately assigned;
6. record the Head-of-Department sign-off as a scoped Plan Decision;
7. update all module documents to cite the same canonical version; and
8. retain deterministic identities, dates and arithmetic unless a correction is explicitly approved.

The current Canonical Demo Data Contract 2.5 is therefore **provisional**, despite its internally consistent amounts.

## 10. Document register and disposition

| Document | Current disposition | Required next action |
|---|---|---|
| Strategy Requirements 1.1 | Provisional | Reissue after simplification and code/plan-overlap decisions |
| Strategy Stitch 1.0 | Withdrawn as design baseline | Regenerate against audited requirements; complete the full screen set |
| Strategy Cursor 1.0 | Withdrawn as implementation baseline | Regenerate after Stitch approval |
| Budget Requirements 1.1 | Provisional | Remove treatment model and defer unsupported management scope |
| Budget Stitch prompts | Provisional | Regenerate from corrected requirements |
| Budget Cursor pack | Provisional | Regenerate after corrected designs |
| Demand Requirements 1.4 | Provisional | Remove treatment model, align canonical version and terminology |
| Demand Stitch 1.5 | Provisional | Simplify and remap screens after requirements correction |
| Demand Cursor 1.5 | Withdrawn as implementation baseline | Regenerate against audited requirements and seed |
| Planning Requirements 1.5 | Withdrawn as implementation baseline | Reissue with planner-author/sign-off model |
| Planning Stitch 1.6 | Withdrawn as design baseline | Reissue PLN-UI-07/08 and all affected wording |
| Planning Cursor 1.4 | Withdrawn as implementation baseline | Reissue domain, service, role, seed and test corrections |
| Canonical Demo Data 2.5 | Provisional | Reissue after semantic corrections without changing the coherent story |
| PE/OU Scope Model 1.0 | Substantively retained; approval status provisional | Add concept-admission and task-scope rules |
| Authorisation Surface 1.0 | Substantively retained; approval status provisional | Validate capabilities against corrected actor model |

## 11. Required reissue sequence

No module should be corrected in isolation. Reissue in this order:

1. **Cross-module semantic contract** — canonical vocabulary, roles, ownership, record boundaries and lifecycle spine.
2. **Strategy requirements** — simplified Strategy Value Commitment model and plan-overlap rule.
3. **Budget requirements** — direct baseline, lines, confirmation and funding control without generic treatment.
4. **Demand requirements** — progressive enrichment with inherited commitments and mandatory Budget Officer confirmation.
5. **Planning requirements** — planner-authored items, scoped OU sign-off, consolidated approval and direct Tender handoff.
6. **Canonical demo data** — same coherent story, corrected semantics.
7. **Stitch prompts** — screen contracts only.
8. **Cursor packs** — domain/services/permissions/tests mapped to approved requirements and screens.
9. **Implementation reconciliation** — inventory existing code as Keep, Correct, Remove or Defer before changes.

Each reissued document must include a change matrix showing the exact concepts removed, renamed and retained.

## 12. Acceptance gates before design resumes

Design may resume only when the product owner has explicitly accepted:

- the cross-module operating model in section 5;
- the verdicts in section 6;
- the planner-author/OU-sign-off model in section 7.4;
- the simplified Strategy Value Commitment boundary;
- the removal of generic treatment records;
- the document disposition in section 10; and
- the reissue sequence in section 11.

No acceptance shall be inferred from silence or from use of a document in Stitch or Cursor.

## 13. Audit conclusion

The platform does not need to be discarded. Its strongest foundations are the generic PE/OU scope model, explicit role scoping, immutable versions, transactional funding reservation, progressive Demand enrichment, the Plan/Version/Item separation and the coherent canonical story.

The unreliable layer is the semantic expansion around those foundations: generic treatment records, contribution/submission indirection, self-approved documents and unsupported management scope. Removing that layer produces a smaller and more defensible MVP without breaking the end-to-end procurement journey.

