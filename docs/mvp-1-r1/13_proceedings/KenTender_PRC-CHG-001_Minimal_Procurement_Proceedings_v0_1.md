# PRC-CHG-001 — Minimal Procurement Proceedings

| Control | Value |
|---|---|
| Document | PRC-CHG-001 v0.1 |
| Status | **Accepted as the first scope baseline** — Project Owner, 26 September 2026; detailed requirements revision requested |
| Date | 26 September 2026 |
| First consumer | Bid Opening |
| Source concept | *Procurement Proceedings Module — Functional Design v1* (supplied for review); narrowed by the Project Owner's instruction to proceed with a minimal capability |
| Related boundaries | Approved G1-REG-001 v1.1; approved BDS-CHG-001 v0.8; future Bid Opening and Evaluation/Award contracts |

## 1. Decision and purpose

KenTender shall provide a small, reusable **Procurement Proceedings** capability for formal sessions whose attendance, actions and minutes must be preserved. The first use is the electronic Bid Opening ceremony. Later procurement and contract workflows may use the same record pattern when their own approved requirements call for it.

A proceeding is **the record of one actual session**, attached to exactly one business process and its source record. It is not a replacement for that process's workflow, decision authority, statutory register or transactional data. The owning module defines when a session is required, who may act, what must be recorded, which attestations are necessary, and when its own business process advances.

For Bid Opening, the owner remains Bid Opening. It controls the opening time, committee appointment and eligibility, sealed-box access, reconciliation, readout, opening register, lawful disclosure, exceptions and Evaluation handoff. Proceedings records participants, attendance, the chronology of the ceremony, minutes, attestations and links to owner-owned evidence. It never opens a bid or releases content on its own.

## 2. First-release scope

The first release supports:

1. A proceeding linked to a Bid Opening for one Tender, with a readable title, actual start and end times, mode or location, and status.
2. The appointed committee and actual attendee records, including supplier representatives who choose to attend. Appointment and composition rules remain in Bid Opening; Proceedings reads their authoritative snapshot.
3. A time-ordered account of the procedure, interruptions, resumed activity and exceptions. The Bid Opening owner supplies opening events and their evidence references rather than requiring re-entry.
4. Human-readable minutes compiled from recorded facts, with additional factual notes where needed, and a link to the owner-generated opening register. The register is a separate Bid Opening artifact.
5. Member attestations against a fixed version of the minutes and, where legally required, identified parts of the opened tenders. An attestation captures the member, target, target digest/version, method, time and verification outcome. The acceptable method remains a legal/operating-profile decision; a click alone is not deemed a statutory signature.
6. A retained, immutable final record, with an append-only correction or supplementary note that preserves the original and identifies its author, time and reason.
7. Contextual access: committee members and authorized procurement staff can work on the relevant session; tenderers or representatives can attend and receive only the opening information that law and the Bid Opening contract permit. Being recorded as an attendee gives no general access to the minutes, other bids or deliberations.

The first release does **not** introduce generic agendas, resolutions, action tracking, configurable quorum, committee decision approval, calendar scheduling, a document-signing platform, generic evidence duplication, public/internal/restricted flags, or automatic triggers for contract and payment workflows. These may be specified by future owning modules on evidence of need. The originating v1 concept's contract implementation, inspection, variation, claim, dispute and termination examples are future consumers, not delivered features.

## 3. Ownership and handoffs

| Record or rule | Owner | Proceedings responsibility |
|---|---|---|
| Tender and published opening arrangement | Tenders | Link and display the authoritative reference; do not edit it. |
| Deadline, receipts, sealed envelopes and custody history | BDS | No direct content access or mutation. |
| Committee appointment and composition | Bid Opening / accounting officer | Show the appointed members and their actual participation; surface an unmet owner rule. |
| Open/decrypt, number and page count, readout and register | Bid Opening | Link the recorded events and register to the session; do not recalculate or approve them. |
| Attendance and session chronology | Proceedings | Record actual attendees and session events with attribution and time. |
| Minutes and member attestations | Proceedings, under Bid Opening rules | Freeze versions, record signatures/initials against exact targets and preserve audit evidence. |
| Evaluation decision and access to opened packages | Evaluation/Award, after Bid Opening handoff | No authority to evaluate, disqualify, score, award or grant bid-content access. |

The BDS close event may create or identify a pending Bid Opening record. Proceedings must not create an opening ceremony from BDS metadata alone. Bid Opening starts the session using its own legally permitted command after close and at the effective opening time. Ending the live session and finalizing minutes are distinct facts; a minutes drafting delay never rewrites when opening occurred.

## 4. Minimum data contract

| Object | Required data | Source / constraint |
|---|---|---|
| Proceeding | ID; proceeding type `Bid Opening`; owning record reference; Tender reference; title; actual start/end; mode/location; status; creation/actor audit | Exactly one parent Bid Opening record. Tender/site context is resolved from parent, not manually duplicated. |
| Participant | Person or external representative identity; capacity (committee, secretary, bidder/representative, observer); represented tenderer if applicable; actual attendance and arrival/departure when relevant | Appointment comes from owner; attendance is factual. No automatic portal role from attendance. |
| Event | Event type, time, actor or system source, brief factual description, owner event/evidence reference | Append-only; the owner is authoritative for bid and custody events. |
| Minutes version | Rendered content, version, generation/finalization time, content digest, register reference, author and status | Each attestation binds to this fixed content; signed content cannot be overwritten. |
| Attestation | Member, target (minutes/version or owner-designated tender section), action, method, timestamp, verification result and proof reference | Required targets and lawful signing method are set by Bid Opening and legal operating profile. |
| Supplementary record | Original reference, reason, added text/evidence, author, time and any new required attestations | Never erases the original record. |

Use existing KenTender identity, permissions, file custody and audit services. A link to evidence stays with its owning record; Proceedings stores a reference and digest where necessary, not a second editable copy. Exact DocType names and storage schema are implementation choices, provided these invariants hold.

## 5. Journey and UI contract

| Moment | User sees / does | System behavior |
|---|---|---|
| Before opening | Authorized committee sees Tender, published opening time/place or mode, committee appointment, readiness and a clear **Waiting for opening time** state. | No supplier identity, count, price or bid content is revealed from the sealed box. Attendance arrangements may be communicated without opening it. |
| Start ceremony | Authorized member starts under Bid Opening's time, composition and credential rules. Supplier representatives may attend by the published route. | Creates the actual session start and event trail. Proceedings does not decide that the box may open. |
| During opening | Committee sees the next bid, its owner-provided opening facts and the readout/registration actions. Attendees receive only the lawful readout. Secretary records attendance and factual interruptions. | Each owner event is referenced once. A failed or resumed action remains visible; no silent replacement of events or bids. |
| Close live session | Committee sees the complete event sequence, attendees and owner-generated opening register. | Records actual end time independently of later drafting. Unresolved discrepancies stay visible. |
| Finalize minutes | Secretary reviews a readable draft; members review the frozen version and perform required attestations. | Produces a fixed version; checks the specific Bid Opening targets and lawful method. Missing or failed attestations are explicit. |
| After finalization | Authorized users read the register and minutes according to their access. Bidder requests for register copies follow Bid Opening's disclosure route. | Original record is retained; correction adds a linked supplement. No edit of signed content. |

The screen should present a plain **Opening session** view: Tender and time, committee and attendees, event timeline, opening register link, minutes, and required member actions. Put technical digests and custody proofs in an evidence detail, with clear human-readable failure messages. No generic proceedings dashboard or extra agenda/resolution tabs are needed for the first release.

## 6. State and failure rules

`Pending → In session → Session ended → Minutes finalized` describes the proceeding record. `Interrupted` is a visible condition and event while a session is in progress; it is not a way to erase or reset the session. A session planned but never started retains a factual `Not held` outcome and reason if the owner requires that record.

- Only Bid Opening's authorized command may start or resume opening. Proceedings never unlocks a sealed package merely because its status changed.
- The owner's legal and appointment rules determine required member participation. No user-configurable quorum percentage or generic override is introduced.
- If attendance, custody, readout, register or attestation evidence is incomplete, show the specific missing item; do not fabricate a normal completion. Bid Opening determines whether and how its own handoff may proceed.
- Interrupted connectivity, missing credentials, absent members and unreadable packages are recorded with times and actors. Restoration continues from the immutable owner state; no backdating or re-opening a previously opened tender.
- Final minutes and their attestations cannot be changed in place. A correction is distinguishable from the original in every view/export.
- A system administrator may maintain technical health but receives no business authority, sealed bid content or ability to attest for a committee member solely through administrator status.

## 7. Acceptance checks for the first consumer

1. BDS closes a Tender with one current submission, one replaced version and one written withdrawal. Before lawful opening, Proceedings reveals none of their bid contents or bidder identities to a PE user. After start, the owner supplies only the current eligible opening set; lineage remains evidential.
2. A three-member appointed committee, including the independent member required by Bid Opening, conducts an opening with one supplier representative attending. The session preserves actual participants, sequence, register link and separate minutes; the representative sees the readout but cannot browse bids or internal minutes.
3. An interruption and a failed opening/verification are visible in the session and minutes. No event, timestamp or package is silently corrected.
4. A member attests to a specific minutes version and designated tender price target. Changing minutes creates a new version and requires the applicable attestations again; the old proof remains verifiable.
5. An administrator cannot use Proceeding status to open bids, approve a register, evaluate a tender or acquire bidder-content access.
6. A later correction preserves the original finalized minutes and its signatures and is linked in every relevant view/export.
7. The Bid Opening owner can consume the completed proceeding references for its Evaluation handoff without Proceedings making an evaluation decision.

## 8. Explicit gates and later extension

**Legal operating-profile gate.** Before production electronic opening, LAW-V-001 and the Bid Opening contract must settle the operative legal instruments, electronic equivalents for tender page counts and member initials/signatures, acceptable signature proof, committee credential control and disclosure/attendance procedure. Proceedings provides the evidence structure but does not claim that a specific electronic action already satisfies section 78. The 2020 Regulations' status is under legal review following the December 2025 judgment; no three-password rule is hard-coded here.

**Later extension rule.** Evaluation, inspection and contract workflows may add type-specific agenda items, recommendations, action follow-up or additional attestations in their own change units. They must name their business owner, legal rule, visibility and handoff. The common proceeding record and immutable evidence semantics may be reused without creating a universal approval engine.

## 9. Traceability and status

This first version records the Project Owner's accepted minimal scope. It does **not** approve or alter BDS-CHG-001, G1-REG-001, Bid Opening or future Evaluation/Award scope. The detailed requirements are proposed in PRC-CHG-001 v0.2; the Bid Opening contract will specify its statutory ceremony, register, access and completion rules.

Legal references for the next change unit: Public Procurement and Asset Disposal Act, 2015, sections 67 and 78 (section 78 reproduced in the [PPRA review record](https://ppra.go.ke/?mdocs-file=10256)); [*Roads and Civil Engineering Contractors Association & another v Attorney General & another* [2025] KEHC 19224 (KLR)](https://new.kenyalaw.org/akn/ke/judgment/kehc/2025/19224/eng%402025-12-04/source.pdf). The latter is a reason to verify the operative regulatory position, not a substitute for a formal legal determination.
