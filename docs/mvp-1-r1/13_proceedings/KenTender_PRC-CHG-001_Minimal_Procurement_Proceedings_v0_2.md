# PRC-CHG-001 — Minimal Procurement Proceedings

| Control | Value |
|---|---|
| Document ID | PRC-CHG-001 |
| Version | 0.2 |
| Status | **Proposed** — shared contract specified; Bid Opening journey and design binding pending |
| Date | 26 September 2026 |
| Supersedes | v0.1, accepted as the first scope baseline on 26 September 2026 |
| Governing standard | KT-STD-001 v1.9 |
| First owning module | Bid Opening (future change unit); BDS-CHG-001 v0.8 is the sealed upstream source |
| Product | Open Tender, single lot, KES, fixed price, off-the-shelf IT Goods, per G1-REG-001 v1.1 |

**Controlling decision.** KenTender will implement a small shared proceedings record, first used *inside* Bid Opening. The record captures actual attendance, session events, minutes, attestations and supplements. Bid Opening owns the statutory ceremony and every business decision. No standalone Proceedings workspace, general meeting workflow or generic approval authority is created.

## 1. Governing decision and disposition

The Project Owner accepted v0.1 as the first version and directed that it receive the same requirements rigor as other KenTender change units. This v0.2 is a proposed revision, not an approval of Bid Opening. The shared service can be specified independently; its full user journey, signed opening targets and lawful completion rules must be closed in the Bid Opening change unit before production.

| v0.1 / source-concept item | Disposition in v0.2 |
|---|---|
| One formal session, attendance, chronology, minutes, attestations and immutable evidence | Retained; defined as records and commands with clear ownership. |
| Bid Opening ceremony, opening register, bid disclosure and Evaluation handoff | Retained as **Bid Opening-owned**, not Proceedings commands. |
| Generic scheduled/reviewed/approved/locked meeting workflow, agenda, resolutions and actions from supplied Functional Design v1 | Excluded from first release. No generic “Approve” action. |
| Contract implementation, inspection, variation, claims, disputes and termination | Future consumers; no current fields or UI justified by them. |
| Standalone Proceedings screen anticipated by v0.1 | Corrected: embed the relevant record and actions in Bid Opening. Its design contract must be supplied there. |
| v0.1 fixed particulars for signing and ceremony | Qualified as owner bindings subject to LAW-V-001 and the electronic operating profile. |

## 2. Purpose, outcome and exclusions

**Outcome:** a committee and a later reviewer can reconstruct what happened at the actual opening, who attended, which owner events occurred, what minutes were attested, and any subsequent correction, without copying bid data into an editable meeting record.

**First release:** exactly one proceedings record for an actual Bid Opening session of a Tender; appointed members and actual attendees; chronological factual events; versioned minutes; member attestations against exact content; append-only supplements; contextual read access and export. The owner may record a planned session that was never held, with a reason, without manufacturing start/end times.

**Excluded:** generalized scheduling, quorum configuration, agenda/resolution/action tables, supplier portal meeting management, arbitrary evidence uploads, generic signature issuance, automatic business transitions, payment/contract decisions, and reporting dashboards. Supplier attendance is not supplier access to internal minutes.

## 3. Ownership and dependency boundary

| Concern | Authoritative owner | PRC seam |
|---|---|---|
| Published Tender and opening arrangement | Tenders | Reference only. |
| Effective deadline, current envelopes, withdrawals/replacements and custody | BDS | No pre-opening bidder identity, count, price or content returned to PE users. |
| Appointment, committee eligibility, clock and opening credentials | Bid Opening and accounting officer | Read authorized member snapshot and owner verdict; never appoint or unlock. |
| Opening of packages, readout, bid number/page count, register, exception classification and lawful disclosure | Bid Opening | Refer to owner events and artifacts; do not duplicate or recalculate facts. |
| Attendance, actual session chronology, minutes versions, attestations and supplements | PRC | Own immutable records and context-limited reads. |
| Evaluation access and decisions | Evaluation/Award after Bid Opening handoff | No evaluation command or authority. |

**Dependency rule:** PRC has no independent production activation. Its first production use is enabled only through a Bid Opening owner adapter after the BDS sealed handoff, BO requirements, legal operating profile, authorization and integrated tests are complete. PRC's service may be built and contract-tested against a simulated owner; that is not a compliant live opening. The owner cannot bypass PRC's evidence requirements by implementing a private duplicate.

**Binding register required in Bid Opening:** actual owner record and identity, creation/start/end commands, eligible committee snapshot, event schema and ordering, statutory minutes content, opening register reference, member attestation targets and method, participant disclosure route, completion/handoff guard, recovery from every named interruption, actor-specific next steps, and exact embedded screens. Each binding has a producer, consumer, validation, failure and test. A blank binding disables the affected production command.

## 4. Canonical domain model

No field below is included solely for future types. The owner reference resolves Tender and site context; these are displayed, not independently editable copies.

| Record | Minimum fields / producer | Consumer, validation and effect |
|---|---|---|
| Proceeding | Server ID; owner type and owner ID; type `Bid Opening`; owner-supplied title; state; created at/by; actual start/end | Owner ID unique for first-release Bid Opening; owner read resolves Tender. Start/end are trusted recorded instants, never entered retrospectively. UI shows current truth. |
| Member snapshot | Owner-appointed member identity, designation, committee capacity and appointment reference | Owner validates actual eligibility; PRC displays designated members and checks attestations against the snapshot, not a self-added participant list. |
| Attendance | Session ID; identity and capacity; represented tenderer where attendance requires it; arrival/departure event; recorder | Owner attendance route supplies actual attendee. Absent appointees are shown as such; attendee record grants no role. Personal details disclosed only under owner policy. |
| Event | Server sequence and time; type; actor/source; factual note or owner event reference; unique owner event ID | Timeline/minutes consume; owner facts are linked, not rewritten. Replay of an event ID yields original result; another payload with same ID fails. |
| Minutes version | Server version; frozen rendered content; exact digest; owner register reference; authored/frozen at/by; finalization state | Committee reads and attests exact version; finalized version immutable. Regeneration makes a new version, not a silent edit. |
| Attestation | Member ID; action; target type, ID/version and digest; recorded time; approved signing method; proof/verification result | Owner defines required targets and validates lawful method. PRC binds evidence; failed verification cannot satisfy a required target. |
| Supplement | Original version; reason; content or owner evidence reference; actor/time; required supplementary attestations if owner demands | Read/export shows original and supplement together; original remains unchanged. |

Raw bid prices, supplier bid contents, custody material, evaluated amounts, quorum percentages, approval authority, action priorities and generic confidentiality flags are **not PRC fields**. The owner can expose a legally permitted readout as an owner event without placing sensitive content in a generally readable PRC note.

## 5. Lifecycle, invariants and next steps

| Transition | Caller and precondition | Result |
|---|---|---|
| Create pending session | Bid Opening owner only, once its record exists | `Pending`; no bid disclosure or start time. |
| Start | Bid Opening owner command after its exact-time, appointment and custody checks | `In session`; trusted actual start time and first event. |
| Append attendance/event | Owner or its authorized recorder during session | Ordered append; no removal or re-sequencing. Interrupt/resume are events, not status resets. |
| End actual session | Bid Opening owner after its ceremony outcome is recorded | `Session ended`; actual end time; unresolved owner exceptions remain visible. |
| Freeze minutes | Authorized owner-designated recorder, after session ended and required owner event references are reconciled | Fixed version; `Awaiting attestations` if targets remain, otherwise owner policy decides completion. |
| Record attestation | Actual appointed member, on exact frozen target and approved method | Verification recorded; no proxy signing or stale-target acceptance. |
| Finalize | Owner decision after all its required evidence and attestations pass | `Finalized`; read-only original; owner, not PRC, decides Evaluation handoff. |
| Mark not held | Owner where session never started | `Not held`, factual reason, no invented opening/minutes. |
| Supplement | Owner-authorized recorder after finalization | Additional immutable linked record; no reversal of original finalization. |

**Invariants:** one owner session identity; trustworthy chronology; no mutation of submitted packages; no Proceedings action unlocks a sealed bid; no disqualification; no automatic authority from attendance; no missing or forged member attestation; finalized content is immutable; replay is idempotent; conflicting or stale writes have no partial effect. A failed session cannot be converted into a successful ceremony by editing its minutes.

**Next-step ownership:** Bid Opening returns the KT-STD-001 §3B `next_step`, guards, hand-off register and My Work items for the full ceremony. PRC supplies state/evidence facts and reason codes to that owner. There is no independent PRC journey tracker, Home task, hand-off or parallel status narrative. The Bid Opening contract must state the exact actor, holder, fix and clearing event for waiting, blocked, interrupted, unsigned and completed states.

## 6. Responsibilities and permissions

| Responsibility | Permitted PRC action | Constraint |
|---|---|---|
| Bid Opening owner service | Create/start/end, append authoritative events and request finalization | Owns statutory guards; cannot bypass member proof. |
| Owner-designated recorder/secretary | Record actual attendance and factual notes, prepare minutes, propose supplement | Bound to this Tender/session; cannot alter owner bid events or attest for others. |
| Appointed committee member | Read authorized session, attest exact assigned target | Identity must match owner's appointment; attendance alone does not confer member authority. |
| Tenderer/representative | Attend under owner procedure; receive the legally permitted readout/register route | No automatic general PRC read, bid-content or internal minutes permission. |
| Auditor | Read lawful historical record and proofs | Oversight scope; no mutation or pre-opening content by default. |
| Administrator/System Manager | Technical status/health only | No business action, member proxy, sealed content or actionable My Work. |

Resolve user, site and record access before returning any record. Outside lawful scope, protected existence is not disclosed. The owner applies the stricter disclosure rule at each read; a generic `Internal` or `Public` toggle cannot override it.

## 7. Service and command contract

These are **logical commands**; Frappe method names and persistence layout may differ. All mutating commands take `owner_id`, `expected_version` and `idempotency_key`, authenticate the actor, and return committed record version, event ID and a current owner-readable state. Retry returns the original committed result. A stale or conflicting payload returns a named error without partial write.

| Command/read | Input and result | Critical enforcement |
|---|---|---|
| `CreateProceeding` | Owner type/ID and authenticated owner call → one pending ID | Unique owner; owner exists; no public create. |
| `StartProceeding`, `EndProceeding`, `MarkNotHeld` | Owner verdict and evidence reference → recorded actual time/state | A client-supplied verdict or clock is insufficient; owner performs guards atomically. |
| `RecordAttendance` | Person/capacity/represented party and event → attendance fact | Actual attendance, capacity and authorized recorder; no implicit permission. |
| `AppendProceedingEvent` | Owner event ID/type/reference or factual recorder note → one ordered event | Owner-generated bid facts accepted only from owner; no unrestricted tender text in note. |
| `FreezeMinutes` | Owner-provided canonical event/register references and rendered content → version/digest | Reconcile with owner event set; prohibit fabricated owner facts and edits to a frozen target. |
| `AttestTarget` | Member, frozen target, proof and verified method → proof outcome | Member appointment and target digest match; approved method; no proxy. |
| `FinalizeProceeding` | Owner completion verdict referencing specific required targets → finalized record | All required verified attestations and owner evidence; no generic approval. |
| `AppendSupplement` | Reason, content/evidence and actor → linked supplement | Original remains readable; owner policy governs supplemental proof. |
| `ReadProceeding`, `ExportProceeding` | Owner-scoped reader → permitted facts/proof bundle | Contextual field-level disclosure; public readout/register is a Bid Opening read, not these endpoints. |

## 8. Error contract

| Code | User-visible message | Result and recovery owner |
|---|---|---|
| `PRC_OWNER_UNAVAILABLE` | **This opening record is not available.** | No disclosure; Bid Opening repairs/authorizes reference. |
| `PRC_START_BLOCKED` | **The opening session cannot start yet. Review the opening requirement shown here.** | Owner supplies specific blocker and in-product fix in its next-step contract. |
| `PRC_MEMBER_REQUIRED` | **You are not an appointed member for this opening.** | No attestation; accounting officer/Bid Opening manages appointment. |
| `PRC_TARGET_CHANGED` | **These minutes changed. Review the latest version before signing.** | No stale proof; member reviews new frozen version. |
| `PRC_PROOF_UNVERIFIED` | **Your signature could not be verified. Try again or follow the recovery shown here.** | No completion; owner operating profile supplies concrete recovery. |
| `PRC_EVIDENCE_INCOMPLETE` | **The opening record is incomplete. Review the missing items shown here.** | No finalization; owner supplies all missing facts and holders. |
| `PRC_VERSION_CONFLICT` | **This record changed while you were working. Refresh it and try again.** | No partial effect. |
| `PRC_ALREADY_FINALIZED` | **These minutes are final. Add a correction if a factual change is needed.** | Original immutable; owner-authorized supplement route. |

Cross-scope reads use the KT-STD-001 `Not found` treatment. Every blocked owner action must return its concrete guard reason and fixes under KT-STD-001 §3B, rather than exposing only the generic PRC error sentence.

## 9. UI architecture and routes

PRC defines **no menu entry, Home tile, independent register, generic form or supplier portal route**. The Bid Opening change unit owns the canonical internal opening route and the authorized attendance/readout and bidder-register-copy routes. It composes PRC's attendance, event timeline, minutes and member-action regions into its screens. A read-only auditor view may reuse the same owner route under its own verdict.

No route may infer authority from possession of a PRC record ID. A pending proceeding viewed before opening cannot expose BDS bidder identities, bid counts or contents.

## 10. Static design contract — owner binding required

This document intentionally supplies **no incomplete Claude Design prompt**. PRC has no standalone page to draw. The Bid Opening change unit must supply closed inputs and complete artboard briefs under KT-STD-001 v1.9 §2.6.8 for: before opening; live session; interruption/blocked recovery; session ended/minutes preparation; member attestation; finalized history; supplier attendance/readout; and requested register copy if a supplier-facing screen is used. It must give actor, instant, exact Tender/version, attendance and event facts, Level 1/2/3 hierarchy, exact labels/actions, next-step headline/holder/fixes, and stable variants.

**Region contract for owner artboards:** top task/next-step and lawful opening action; committee and attendance facts; chronological opened-bid/readout facts from Bid Opening; minutes/attestation action in the relevant later state; register and custody evidence as subordinate links. No second PRC status narrative or generic approval bar. The supplier view contains only its lawful attendance/readout data, never internal member actions or full competing bids. Use KT-STD-001 §2, §2.9 and the approved desktop shell; full exact content awaits owner fixtures.

## 11. Functional interaction requirements — excluded from design prompts

The owning Bid Opening interaction map must bind every visible control to its command/read, navigation/mutation result, permission, successful outcome and error. At minimum: Start opening, record attendee, open next bid/read out (owner actions), record interruption/resume, end session, prepare/freeze minutes, attest exact target, finalize, view register, export permitted record and append correction. PRC does not define the bid-opening controls' behavior; it supplies the corresponding evidence operations in §7. No artboard may display a control whose owner command is absent.

## 12. Audit and historical integrity

Every material command records actor, owner, trusted time, prior/current version, outcome, idempotency key and evidence references; denied, stale and failed attestation attempts are auditable without disclosing bid contents. Owner events retain their owner IDs and order. Final minutes, digest, each member's proof and each supplement are independently reproducible on export. Audit/technical reads cannot become a path around the sealed box. Retention follows the authorized procurement record schedule in the governing owner; PRC invents no separate retention period.

## 13. Deterministic seed and negative fixtures

Use KT-STD-001 v1.9 §8's `PE-MOH`, `Africa/Nairobi`, Amina Hassan (Accounting Officer), Charles Mutiso (Head of Procurement), Brian Wafula (Procurement Officer), Naomi Chebet (Auditor) and Administrator. Use BDS's approved Tender/receipt chronology and supplier identities where that source explicitly supplies them. Amina's accounting-officer responsibility **does not itself make her an opening committee member**. The Bid Opening document must appoint at least three named members and designate the recorder before an integrated fixture can assert the committee. Do not invent the identities here.

| Fixture ID | Setup / expected PRC result | Use |
|---|---|---|
| PRC-S01 | Owner simulator creates a pending record and replays same key; one ID and one create event | Independent shared-service contract only. |
| PRC-S02 | Simulator starts, appends two ordered events, records attendance, ends, freezes minutes, records verified target proofs and finalizes | Independent state/immutability test with **test-only** actors and targets; not legal compliance evidence. |
| PRC-N01 | Different payload reuses same event ID; rejected, original unchanged | Replay/conflict. |
| PRC-N02 | Member proof binds obsolete minutes digest; rejected, prior proof retained | Attestation integrity. |
| PRC-N03 | Administrator attempts start, sign and content read; denied | Separation of authority. |
| PRC-N04 | Unfinished session, missing owner event or unverified proof; finalization blocked with all missing items | Owner binding and dead-end. |
| PRC-N05 | Finalized minutes correction adds supplement; original export unchanged | History. |
| PRC-INT-01 | BDS closes the canonical Tender; Bid Opening opens with appointed members, supplier attendance, custody exception and final minutes | **Pending** Bid Opening's approved fixture, method, actual values and legal gate. Cannot be counted as passed now. |

Seeds use the same commands as UI, are idempotent, fail on conflicting authoritative data, and never grant Administrator a business role. Owner simulation cannot turn a failed integrated case into a pass.

## 14. Acceptance and readiness

| ID | Required result | Evidence owner |
|---|---|---|
| PRC-A01 | One owner produces exactly one proceeding; replay and stale write are safe. | PRC contract test. |
| PRC-A02 | Owner events and attendance are ordered, attributed and immutable; a supplier attendee gains no general read. | PRC/owner access test. |
| PRC-A03 | Minutes freeze to a digest; only appointed members can attest assigned fixed targets by the approved method. | PRC and Bid Opening integrated test. |
| PRC-A04 | Missing owner events, unverified proof or changed target blocks completion with named reasons and fixes; no false minutes. | Bid Opening next-step/dead-end matrix. |
| PRC-A05 | Correction preserves and exposes original finalized record and all proofs. | PRC contract/export test. |
| PRC-A06 | PE and technical users cannot see sealed identities/count/content via PRC before opening; post-opening access obeys owner disclosure. | BDS–Bid Opening–PRC integration test. |
| PRC-A07 | Bid Opening handoff to Evaluation cites the exact opened packages, register and PRC record without PRC evaluating a bid. | Bid Opening integration test. |
| PRC-A08 | Every owner artboard/control has a closed fixture, permission and interaction mapping; comprehension, responsive, browser and release evidence pass. | Bid Opening design/release evidence. |

**Readiness:** PRC-A01, A02's shared portions and A05 can be implemented against the test owner. PRC-A03, A04, A06–A08 and the owner-specific part of A02 **cannot pass in isolation**. Do not mark PRC production-ready or its first release complete until the owning Bid Opening contract and integrated suite pass. The owner's state/actor dead-end matrix and hand-off tests satisfy KT-STD-001 §3B/§6 for the combined journey; there is no duplicate independent PRC workflow matrix.

## 15. Implementation and test constraints

Implement in the existing KenTender procurement architecture as shared services and records; exact Frappe app/DocType placement follows repository ownership. Reuse canonical identity, authorization, audit, time, cryptographic signature and evidence custody services. Tests call public commands rather than writing governed records directly. KT-STD-001 v1.9 §4–6 governs build, contract, browser, visual and first-view checks. The binding seam shall be exercised by a deterministic simulated owner before integration, then by a real Bid Opening owner fixture. A simulated passing contract is labeled only as shared-service evidence.

## 16. Prohibited shortcuts

No generic “Approve minutes” action; no attendee-is-member assumption; no admin override; no arbitrary quorum field; no client clock; no editing event history or signed minutes; no copied bid data as free-text minutes; no bulk disclosure to supplier attendees; no silent completion on credential or signature failure; no PDF attachment standing in for structured owner events; no mock opening in production; no three-password rule hard-coded from an unverified operative regulation. KT-STD-001 §2.3 and §10 also apply.

## 17. Traceability and precedence

| Source | Effect here | Follow-up owner |
|---|---|---|
| Approved BDS-CHG-001 v0.8; G1-REG-001 v1.1 | Sealed handoff only, no BDS opening command; approved first product boundary | Bid Opening consumes, cannot revise BDS by implication. |
| KT-STD-001 v1.9 | Document skeleton, closed design input, next-step/guard/hand-off, seed, verification | PRC core now; Bid Opening journey and artboards next. |
| PPADA 2015, §78 and §67 | Committee/opening/minutes and confidentiality constraints inform first consumer | LAW-V-001 and Bid Opening map statutory obligations to electronic controls. |
| LAW-REG-001 v1.2 LAW-V-001 | Current legal instrument and signing interpretation unresolved | Legal/operating profile before production. |
| Supplied Procurement Proceedings Functional Design v1 | Conceptual input, not a current KenTender authority | Future contract phases only where separately approved. |

Source check: [PPRA review record reproducing Act §78](https://ppra.go.ke/?mdocs-file=10256); [2025 High Court judgment on the 2020 Regulations](https://new.kenyalaw.org/akn/ke/judgment/kehc/2025/19224/eng%402025-12-04/source.pdf). The operative effect of that judgment, any stay/appeal and any replacement instrument require legal verification; this document does not assert that an electronic click meets §78 signing.

## 18. Approval effect

Approval of v0.2 would replace v0.1's shared-service detail while retaining its accepted minimal scope. It would authorize implementation and contract testing of PRC's owner-independent core. It would **not** authorize standalone deployment, final Bid Opening UI, a production opening ceremony, a particular electronic signature method or Evaluation access. Those become concrete and reviewable in the Bid Opening change unit and operating profile. Until then, dependent acceptance items remain visibly pending, not inferred as satisfied.
