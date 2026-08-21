# KenTender MVP Cross-Module Operating Model

**Document ID:** KENTENDER-MVP-CMOM-1.1  
**Version:** 1.1  
**Date:** 11 August 2026  
**Status:** Approved by product owner — controlling baseline  
**Approval recorded:** 11 August 2026  
**Supersedes:** `KENTENDER-MVP-CMOM-1.0`  
**Applies to:** Strategy Alignment, Budget & Funding, Demands and Procurement Planning

**Revision 1.1:** Allows the planner to select one or more Approved Demands in the Plan Item formation dialog. One selection creates one Plan Item. Multiple selections require an explicit choice between separate Plan Items and one compatible combined Plan Item. This removes the unnecessary create-then-add aggregation sequence while retaining deliberate formation, compatibility and source-lineage controls.

## 1. Purpose

This document defines the minimum business operating model that all module requirements, Stitch prompts, Cursor packs, schema, services, permissions, seed data and tests must follow.

It deliberately excludes detailed screen layouts and implementation choices. Its purpose is to prevent a design or implementation artifact from inventing a field, role, approval or workflow that has not been accepted at the business level.

## 2. Governing principles

1. **Simple but complete.** Include every control needed to progress a lawful, auditable procurement; exclude fields and stages without a real operational consequence.
2. **One fact, one owner.** A fact is created and approved in its owning module, then inherited downstream.
3. **No duplicate approval.** A later module does not request the same actor to approve the same business fact again.
4. **Operational tasks drive screens.** A screen exists because an authorised actor has a recognisable task, not because a record contains many fields.
5. **The Plan Item is the execution unit.** The Plan Version controls approval and immutability; ordinary execution meaning remains on the Plan Item.
6. **Explicit scope.** PE/OU ownership is never guessed.
7. **Generated references.** Users work with titles and business context, not technical codes.
8. **Authority is task-specific.** Seeing a record does not grant access to an approval or edit form.
9. **Preserve upstream evidence.** Planning and Tender consume approved snapshots and references rather than rewriting upstream records.
10. **Prefer omission to speculation.** A deferred feature is safer than an unsupported field or workflow.

## 3. Lifecycle spine

| Stage | Business question answered | Authoritative output |
|---|---|---|
| Strategy | What public outcomes and commitments should procurement support? | Approved Strategy version, targets and Strategy Value Commitments |
| Budget & Funding | What approved procurement funding is available and controlled? | Active Budget Lines and auditable funding controls |
| Demands | What does the organisation need, who owns it and has the business approved it? | Approved Demand and Need Items |
| Procurement Planning | How will the Approved Demand be procured, funded and scheduled? | Approved Plan Version containing executable Plan Items |
| Tender | How will the market be approached for an eligible Plan Item? | Tender linked to an immutable planning handoff |
| Contract | What obligation resulted from the procurement? | Contract and commitment linked to the procurement lineage |

## 4. Normal actor journey

| Sequence | Actor | Task | Result |
|---|---|---|---|
| 1 | Requester | Describe and submit the business need | Demand awaiting HoD decision |
| 2 | Head of Department / Business Approver | Approve or return the need | Approved Demand or returned Demand |
| 3 | Procurement Planner | Select one or more Approved Demands, choose Plan Item formation where needed and complete the resulting item(s) | Draft Plan Item(s) in the applicable Plan Version |
| 4 | Budget Officer / authorised Finance role | Confirm funding assignment and availability | Recorded funding sign-off |
| 5 | Head of Procurement / configured professional authority | Review or approve planning completeness | Approved or review-complete Plan Version/Item according to configured authority |
| 6 | Authorised Procurement role | Create or prepare the Tender from an eligible Plan Item | Tender with immutable source lineage |

The exact title of an approval authority may vary by Procuring Entity. The accountable capability remains stable and is configured without changing the domain model.

## 5. Approval boundary

### 5.1 HoD approval

HoD approval of the Demand confirms:

- the need is legitimate;
- the OU owns it;
- its business scope and intended outcome are accepted;
- its priority and timing are suitable for planning; and
- the Requester may hand it to Procurement.

It does not approve the procurement method, aggregation, lotting or detailed procurement schedule. Those are Procurement Planning decisions.

### 5.2 No routine second HoD sign-off

The planner's addition of procurement-owned decisions does not trigger another HoD approval. There is no normal `OU contribution`, `Departmental Submission` or per-Plan-Item `OU_SIGNOFF` stage.

### 5.3 Material-change reapproval

The system routes a targeted change back to the HoD only when Planning changes a HoD-owned fact materially.

| Change | Reapproval required? | Reason |
|---|---|---|
| Procurement method | No | Procurement-owned decision |
| Procurement schedule within the approved need | No | Procurement-owned decision |
| Indicative lots | No, unless business scope/accountability changes | Normally procurement-owned structure |
| Combine compatible Demands | Only if scope, ownership or accountability changes materially | May alter the HoD-approved business requirement |
| Owning OU | Yes | Changes accountability |
| Scope or intended outcome | Yes | Changes the approved need |
| Quantity or delivery requirement | Yes when material | Changes the approved need |
| Estimated value | Yes when materially increased | Changes the business/funding basis |
| Funding source | Finance approval; HoD only if the business requirement changes | Funding is not itself an HoD planning decision |

The reapproval request contains only the changed facts, the previous values, the proposed values and the reason. It does not reopen unrelated planning decisions.

### 5.4 Departmental-plan evidence

The system can generate an OU-scoped annual departmental plan projection from HoD-approved Demands and their resulting Plan Items. If a Procuring Entity requires formal annual certification, it may configure one batch certification over that annual projection.

This optional certification is not:

- a second item-authoring process;
- a contribution editor;
- a prerequisite repeated for every ordinary item change; or
- authority for the OU to edit procurement-owned decisions.

Its admission to MVP requires explicit product-owner and legal acceptance.

## 6. Module ownership boundaries

### 6.1 Strategy Alignment owns

- Strategic Plan versions;
- outcomes, objectives, targets and measurements;
- Strategy Value Commitments;
- Strategy approval and performance evidence.

It does not own procurement funding, Demand approval, procurement method, Plan Item schedule or Tender configuration.

### 6.2 Budget & Funding owns

- procurement Budget registration;
- Budget Lines;
- availability calculations;
- Reservation and Commitment controls;
- Finance/Budget Officer decisions; and
- integration references to the authoritative financial system.

It does not reproduce the financial system's complete budgeting, accounting or expenditure function.

### 6.3 Demands owns

- the Requester's description of need;
- Need Items;
- PE and owning OU;
- business justification and requested delivery context;
- HoD approval/return; and
- an immutable approved business snapshot.

The Requester does not select Strategy targets, Budget Lines, procurement method, aggregation, lots or procurement schedule.

### 6.4 Procurement Planning owns

- Plan and Plan Version;
- Plan Item and Plan Item Version;
- Demand Allocation;
- procurement description;
- method and method basis where required;
- arrangement;
- procurement schedule;
- aggregation decision when multiple Demands are intentionally combined;
- indicative lotting; and
- planning review/approval evidence.

Planning does not rewrite the Approved Demand, create a duplicate departmental contribution or demand routine HoD reapproval.

## 7. Procurement Plan and Plan Item rules

1. Selecting one Approved Demand creates one Draft Plan Item.
2. The Plan Item formation dialog may select one or more Approved Demands.
3. When multiple Demands are selected, the planner must explicitly choose **Create separate Plan Items** or **Combine into one Plan Item**.
4. Separate formation creates one actual Plan Item per selected Demand; it is not stored as a cosmetic `Keep separate` value.
5. Combined formation is available only when all selected Demands are compatible under the accepted MVP rules and requires a reason for combining.
6. Each Demand and Need Item retains its own allocation, funding and approval lineage regardless of formation choice.
7. Source selection and editing the resulting Plan Item(s) are parts of one journey; the Plan Item editor does not select the source again.
8. Indicative lots divide the expected Tender structure within a Plan Item. They do not create Plan Items.
9. An Approved Plan is not edited in place.
10. Adding Demand(s) to an Approved Plan quietly creates or reuses one Draft successor.
11. The current Approved Plan Version and its existing Tender handoffs remain operational during revision.
12. Only the Draft successor is editable.
13. Approval of the successor replaces the current Plan Version according to an auditable state transition.

## 8. Funding rules

1. Automatic matching or recommendation does not replace Budget Officer sign-off.
2. Finance confirms the proposed Budget Line, amount and availability after the planned requirement is available for review.
3. A Reservation follows the same requirement through Planning and Tender; downstream modules do not create duplicate holds.
4. A funding change is audited and revalidated before approval.
5. Expenditure remains read-only unless supplied by an authoritative integration.
6. “Budget context” is not a free-text Plan header field. Relevant funding is shown through actual Budget Line assignments and balances.

## 9. Strategy lineage rules

1. Strategy links are resolved by an authorised role or inherited from an approved upstream assignment; the Requester is not expected to maintain them.
2. Downstream records retain stable version references and readable snapshots.
3. A Strategy Value Commitment is read-only context downstream until a module owns a concrete decision implementing it.
4. Generic `treatment`, `planned treatment value` and rationale fields are prohibited unless a named operational decision and consumer are accepted.
5. Strategy technical codes are generated. An external reference may be stored only when present in an authoritative source.

## 10. PE/OU scope rules

| Eligible creation scopes | Required behaviour |
|---|---|
| Zero | Block creation and explain that operational scope is required |
| One | Show the selected PE/OU explicitly; do not hide it as an arbitrary default |
| Multiple | Require deliberate PE selection followed by eligible OU selection |

Additional rules:

- an authorised user may create for another PE/OU only when an explicit scope assignment grants that capability;
- Administrator status does not invent an operational PE/OU;
- an Administrator may be assigned operational scope like any other user;
- record queries, counts, queues, exports and notifications use the same scope rules; and
- PE/OU values stored on the record are validated server-side against the actor's capability.

## 11. Record visibility and task authority

For every workflow record, the system distinguishes:

1. **Record visibility** — may the user see the neutral business record?
2. **Task visibility** — does the user currently have an actionable task?
3. **Mutation authority** — may the user execute this state-changing action?

An unauthorised user shall not see a `Review`, `Approve`, `Return`, `Activate` or similar task action that opens a restricted task form. Direct navigation to the task route is rejected server-side. A permitted viewer may instead see a neutral read-only detail page and completed decision history appropriate to their visibility rights.

## 12. Prohibited MVP concepts

Unless separately admitted through the concept gate, the following are prohibited:

- user-maintained plan, target, Budget, Demand or Plan Item codes;
- generic value-treatment questionnaires;
- generic statutory-treatment controls;
- unsupported planned-treatment amounts;
- Organisation Unit contribution workbenches;
- routine planning-stage HoD sign-off;
- silent PE/OU fallbacks;
- Administrator operational bypasses;
- disabled approval forms exposed to unauthorised roles;
- duplicate source selection between Add Plan Item and the Plan Item editor; and
- fields added only for hypothetical future reporting.

## 13. Canonical seed story invariants

The repeatable seed must preserve:

- stable identities and idempotent loading;
- Ministry of Health as the principal end-to-end story;
- County Government of Kisumu as a minimal second-entity isolation story;
- realistic role assignments and explicit PE/OU scope;
- the KES 480,000,000 Budget Line;
- the KES 455,000,000 Approved Demand and Active Plan Item;
- the KES 310,000,000 commitment and KES 145,000,000 remaining reservation;
- the returned Demand corrected from KES 95,000,000 to KES 80,000,000;
- Draft Revision 2 at KES 535,000,000 while Approved Version 1 remains operational; and
- the normal Requester → HoD → Planner → Finance → Head of Procurement story.

The seed shall not create generic treatment, contribution or routine planning-stage HoD-sign-off records.

## 14. Screen and implementation contract

Every Stitch prompt must declare:

- screen purpose;
- primary actor;
- entry point;
- authoritative records read;
- exact visible fields;
- fields written, if any;
- primary actions and outcomes;
- exit/result; and
- adjacent tasks explicitly excluded.

Every Cursor pack must trace each screen and action to:

- requirement ID;
- domain record;
- service/action;
- capability and scope rule;
- state transition;
- audit event;
- seed fixture; and
- positive and negative tests.

Neither Stitch nor Cursor may create a new business requirement from design copy.

## 15. Acceptance status

The product owner approved this operating model on 11 August 2026. It is the controlling semantic and workflow baseline for correcting Strategy Alignment, Budget & Funding, Demands and Procurement Planning.

Approval of this document does not automatically approve any existing module requirements, Stitch pack, Cursor pack or implementation. Each must still be reconciled and reissued against this baseline.
