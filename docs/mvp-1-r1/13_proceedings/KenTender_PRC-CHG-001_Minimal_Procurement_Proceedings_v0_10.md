# PRC-CHG-001 — Minimal Procurement Proceedings

**Current approval record — 1 October 2026.** The Project Owner instructed: “Mark all the proposed documents as approved”. This approves PRC-CHG-001 v0.10 in full, including its incorporated amendments. This record supersedes earlier pending/proposed approval wording and conditional predecessor-authority statements retained below as drafting history. Earlier versions remain historical. Approval does not establish implementation completion, test success, legal verification or production release; existing operating gates and substantive follow-ups remain in force.

| Control | Value |
|---|---|
| Document ID | PRC-CHG-001 |
| Version | 0.10 |
| Status | **Approved requirement — Project Owner approved 1 October 2026** |
| Date | 30 September 2026 |
| Approved on | 1 October 2026; prior approvals retained in history |
| Supersedes | On approval, v0.9; historical approvals retained below |
| Revision record | v0.9 aligns the active-arrival snapshot, single-action zero-bid end, attributed readout time and page-target flow with BOP v0.9. PRC still has no standalone artboards. |
| Governing standard | KT-STD-001 v1.10 |
| First owning module | BOP-CHG-001 v0.9 approved owner; approved BDS-CHG-001 v0.8 is the sealed upstream source, with a receipt-visibility correction proposed in v0.9 |
| Product | Open Tender, single lot, KES, fixed price, off-the-shelf IT Goods, per G1-REG-001 v1.1 |

**Controlling decision.** KenTender will implement a small shared proceedings record, first used *inside* Bid Opening. The record captures actual attendance, session events, minutes, attestations and supplements. Bid Opening owns the statutory ceremony and every business decision. No standalone Proceedings workspace, general meeting workflow or generic approval authority is created.

**v0.10 scope and precedence.** PRC now specifies two explicit owner profiles: **Bid Opening**, whose existing one-session/minutes contract below is unchanged, and **Bid Evaluation**, defined in §20. References below to the first release, one owner session, opening-only commands, minutes, opening messages, BOP completion and sealed custody apply to the Bid Opening profile. Shared identity, immutable evidence, audit, personal proof and replay rules apply to both. Evaluation business decisions remain in EVL; PRC records their attributed evidence. Neither profile can call the other profile’s lifecycle commands. BOP v0.10 remains the approved Opening owner; EVL v0.4 supplies Evaluation rules and screens. KT-STD v1.13 is the coordinated fixture amendment; approved v1.12 remains the governing standard pending its approval.

## 1. Governing decision and disposition

The Project Owner accepted v0.1 as the first version and directed that it receive the same requirements rigor as other KenTender change units. The previous v0.2 was a proposed revision, not approval of all Bid Opening details. The Project Owner accepted the live opening interaction on 27 September 2026. The shared service can be specified independently; statutory signed targets and lawful completion still require the Bid Opening owner and deferred TRUST-ADR-001 v0.1 support-module integration before production.

**Accepted human interaction binding.** In the Bid Opening screen, the owner supplies verified one-by-one package reveals and readout facts. PRC records actual committee and supplier/representative arrivals/departures, the speaking member and actual readout event, and material interventions: the attendee/member who spoke, the bid/step concerned, factual request or observation, the chair's procedural response, repetition, dissent, pause and resumption. The recorder need not transcribe every utterance. These append-only notes never amend a submitted price, make an Evaluation finding or authorize bid access. The chair ends the live session; the recorder prepares minutes from ordered owner facts plus reviewed human notes; the appointed members individually attest their exact targets.

**Interim test binding.** TRUST-ADR-001 v0.1 permits a clearly marked, individually attributable target-digest **test attestation** and synthetic owner/tender-box events to exercise PRC services. They are neither advanced electronic signatures nor legally effective page initials; `FinalizeProceeding` in a test profile is a simulated result only. There is no production PRC activation through a proxy. The approved BDS production gate and BOP legal/custody guards remain in force until a separate Trust, Signing and Custody support module and operating profile are approved and integrated.

| v0.1 / source-concept item | Retained disposition from v0.2 |
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
| Published Tender definition and effective opening time | Tenders | Reference only; PRC cannot change published Tender data. |
| Public Opening attendance projection on the Tender page | Bid Opening | Reference BOP versioned method, place/link, time and publication evidence; no PRC owner mutation or box facts. |
| Effective deadline, current envelopes, withdrawals/replacements and custody | BDS | No general PE opening-user access to pre-opening **sealed-box-derived** bidder identity, count, price or content. The separately scoped BDS physical-security receipt owner and voluntary attendee may disclose supplier/representation facts independent of submission; neither fact proves a bid exists or grants box access; BDS v0.9 must reconcile this exception before production. |
| Appointment, committee eligibility, clock and opening credentials | Bid Opening and accounting officer | Read authorized member snapshot and owner verdict; never appoint or unlock. |
| Opening of packages, readout, bid number/page count, register, exception classification and lawful disclosure | Bid Opening | Refer to owner events and artifacts; do not duplicate or recalculate facts. |
| Attendance, actual session chronology, minutes versions, attestations and supplements | PRC | Own immutable records and context-limited reads. |
| Evaluation access and decisions | Evaluation after governed opening | EVL owns access and decisions; PRC records its events, sessions and proof targets through §20, without evaluation authority. |

**Dependency rule:** PRC has no independent production activation. Its first production use is enabled only through a Bid Opening owner adapter after the BDS sealed handoff, BO requirements, legal operating profile, authorization and integrated tests are complete. PRC's service may be built and contract-tested against a simulated owner; that is not a compliant live opening. The owner cannot bypass PRC's evidence requirements by implementing a private duplicate.

**Binding register required in Bid Opening:** actual owner record and identity, creation/start/end commands, eligible committee snapshot, event schema and ordering, statutory minutes content, opening register reference, member attestation targets and method, participant disclosure route, completion/handoff guard, recovery from every named interruption, actor-specific next steps, and exact embedded screens. Each binding has a producer, consumer, validation, failure and test. A blank binding disables the affected production command.

## 4. Canonical domain model

No field below is included solely for future types. The owner reference resolves Tender and site context; these are displayed, not independently editable copies.

| Record | Minimum fields / producer | Consumer, validation and effect |
|---|---|---|
| Proceeding | Server ID; owner type and owner ID; type `Bid Opening`; owner-supplied title; state; created at/by; actual start/end | Owner ID unique for first-release Bid Opening; owner read resolves Tender. Start/end are trusted recorded instants, never entered retrospectively. UI shows current truth. |
| Member snapshot | Owner-appointed member identity, designation, committee capacity and appointment reference | Owner validates actual eligibility; PRC displays designated members and checks attestations against the snapshot, not a self-added participant list. |
| Attendance | Session ID; identity and capacity; represented tenderer where attendance requires it; arrival/departure event; recorder | Owner attendance route supplies actual attendee. At Start, an active pre-session arrival appears in the in-session view by reference, without a duplicate arrival event or click. Absent appointees are shown as such; attendee record grants no role. Personal details disclosed only under owner policy. |
| Event | Server sequence and time; type; actor/source; factual note or owner event reference; unique owner event ID | Timeline/minutes consume; owner facts are linked, not rewritten. Replay of an event ID yields original result; another payload with same ID fails. |
| Minutes version | Server version; frozen rendered content; exact digest; owner register reference; authored/frozen at/by; finalization state | Committee reads and attests exact version; finalized version immutable. Regeneration makes a new version, not a silent edit. |
| Attestation | Member ID; action; target type, ID/version and digest; recorded time; approved signing method; proof/verification result | Owner defines required targets and validates lawful method. PRC binds evidence; failed verification cannot satisfy a required target. |
| Supplement | Original version; reason; content or owner evidence reference; actor/time; required supplementary attestations if owner demands | Read/export shows original and supplement together; original remains unchanged. |

Raw bid prices, supplier bid contents, custody material, evaluated amounts, quorum percentages, approval authority, action priorities and generic confidentiality flags are **not PRC fields**. The owner can expose a legally permitted readout as an owner event without placing sensitive content in a generally readable PRC note.

## 5. Lifecycle, invariants and next steps

| Transition | Caller and precondition | Result |
|---|---|---|
| Create pending session | Bid Opening owner only, once its record exists | `Pending`; no bid disclosure or start time. |
| Start | Bid Opening owner command after its exact-time, appointment and custody checks | `In session`; trusted actual start time and first event; active pre-session arrivals become the initial attendance view without manufacturing arrivals at Start. |
| Record pre-session presence/custody event | Owner-authorized member/recorder while `Pending`, after appointment and before Start | Ordered and attributed `pre-session` arrival/departure or approved custody participation; no bid facts, no actual ceremony start, no member authority from attendance. |
| Append in-session attendance/event | Owner or its authorized recorder after actual Start | Ordered append; no removal or re-sequencing. Interrupt/resume are events, not status resets. |
| End actual session | Bid Opening owner after its ceremony outcome is recorded | `Session ended`; actual end time; unresolved owner exceptions remain visible. |
| Freeze minutes | Authorized owner-designated recorder, after session ended and required owner event references are reconciled | Fixed version; `Awaiting attestations` if targets remain, otherwise owner policy decides completion. |
| Supersede frozen minutes | Authorized recorder before finalization, with reason, corrected factual note and owner revalidation | New frozen version/digest and fresh member targets; prior proofs remain auditable but do not satisfy the current version. |
| Record attestation | Actual appointed member, on exact frozen target and approved method | Verification recorded; no proxy signing or stale-target acceptance. |
| Finalize | Owner decision after all its required evidence and attestations pass | `Finalized`; read-only original; owner, not PRC, decides Evaluation handoff. |
| Mark not held | Owner where session never started; AO fact after scheduled instant or authoritative pre-start TPR cancellation | Terminal `Not held`, factual AO reason or TPR cancellation reference and existing BDS/Trust custody reference (closed manifest only if one exists); no opening/minutes/handoff. Start, release, resume and finalization on this identity are denied. BOP creates an AO Tender-decision item only when no prior cancellation exists. If ceremony started, interruption remains In session and cannot be relabelled. A convened zero-bid session instead starts and follows ordinary minutes/proof/finalization. |
| Close aborted proceeding | BOP owner after actual Start and authoritative TPR cancellation | Terminal `Aborted after start`, actual cessation time, partial events and custody reference preserved; no normal End/Freeze/Finalize, fabricated minutes, proof or Evaluation handoff. TPR owns statutory cancellation notices; legal profile defines any supplementary partial record obligations before production. |
| Supplement | Owner-authorized recorder after finalization | Additional immutable linked record; no reversal of original finalization. |

**Invariants:** one owner session identity; trustworthy chronology; no mutation of submitted packages; no Proceedings action unlocks a sealed bid; no disqualification; no automatic authority from attendance; no missing or forged member attestation; finalized content is immutable; replay is idempotent; conflicting or stale writes have no partial effect. Not held and Aborted after start are terminal; no Start, resumed reveal, normal proof or finalization follows them. A failed session cannot be converted into a successful ceremony by editing its minutes.

**Next-step ownership:** Bid Opening returns the KT-STD-001 §3B `next_step`, guards, hand-off register and My Work items for the full ceremony. PRC supplies state/evidence facts and reason codes to that owner. There is no independent PRC journey tracker, Home task, hand-off or parallel status narrative. The Bid Opening contract must state the exact actor, holder, fix and clearing event for waiting, blocked, interrupted, unsigned and completed states.

## 6. Responsibilities and permissions

| Responsibility | Permitted PRC action | Constraint |
|---|---|---|
| Bid Opening owner service | Create/start/end, append authoritative events and request finalization | Owns statutory guards; cannot bypass member proof. |
| Owner-designated recorder/secretary | Record actual attendance and factual notes, prepare minutes, propose supplement | Bound to this Tender/session; cannot alter owner bid events or attest for others. |
| Appointed committee member | Read authorized session, attest exact assigned target | Identity must match owner's appointment; attendance alone does not confer member authority. |
| Tenderer/representative | Attend under owner procedure; receive the legally permitted readout/register route | No automatic general PRC read, bid-content or internal minutes permission. |
| Auditor | Read lawful historical record and proofs | Oversight scope; no mutation or pre-opening content by default. |
| Administrator/System Manager | Technical status/health and assigned infrastructure incident outside PRC | No PRC business action, member proxy, opening/attestation, or PRC actionable My Work. The synthetic TRUST proxy makes no confidentiality guarantee against infrastructure administrators; production separation belongs to the approved Trust operating profile. |

Resolve user, site and record access before returning any record. Outside lawful scope, protected existence is not disclosed. The owner applies the stricter disclosure rule at each read; a generic `Internal` or `Public` toggle cannot override it.

## 7. Service and command contract

These are **logical commands**; Frappe method names and persistence layout may differ. All mutating commands take `owner_id`, `expected_version` and `idempotency_key`, authenticate the actor, and return committed record version, event ID and a current owner-readable state. Retry returns the original committed result. A stale or conflicting payload returns a named error without partial write.

| Command/read | Input and result | Critical enforcement |
|---|---|---|
| `CreateProceeding` | Owner type/ID and authenticated owner call → one pending ID | Unique owner; owner exists; no public create. |
| `StartProceeding`, `EndProceeding`, `MarkNotHeld` | Owner verdict/evidence and custody reference → recorded actual time/state | Start is allowed only from Pending with active Tender and snapshots active arrivals. End follows an actual session; the empty-outcome owner action records fact and End atomically. MarkNotHeld only from Pending/no Start and becomes terminal. AO action after scheduled time creates a BOP AO decision item; prior TPR cancellation does not. Never invent a manifest or release the box. |
| `CloseAbortedProceeding` | BOP cites authoritative TPR cancellation after actual Start, last event and custody → terminal partial session | Actual cessation time, append-only prior events; no normal minutes, attestations, finalization or Evaluation handoff. Replay safe. |
| `RecordAttendance` | Person/capacity/represented party, event and pre-session flag → attendance fact | Pending accepts restricted join/leave/arrival only; in-session accepts new arrival/departure. At Start the still-active Pending arrival is referenced in the in-session attendance view, not re-recorded. Does not grant authority. |
| `AppendProceedingEvent` | Owner event ID/type/reference or factual recorder note → one ordered event | Pending accepts attributed pre-session presence/custody and an opaque once-only closed-manifest reference after deadline, never sealed-box-derived bidder identity/count/price/content; separately recorded attendee representation does not prove submission. Owner-generated opening facts need actual Start. A readout confirmation has trusted commit time; any earlier reported speech instant is attributed as a human observation, not forged as server event time. |
| `FreezeMinutes` | Owner-provided canonical event/register references, selected tender page/price/change targets and rendered content → version/digest | Reconcile with owner event set; prohibit fabricated owner facts and edits to a frozen target. |
| `SupersedeFrozenMinutes` | Recorder reason, corrected factual note, owner revalidation and latest target set → new version/digest | Before finalization only; supersedes satisfaction of prior proofs without deleting their evidence, then requires every applicable fresh proof. |
| `AttestTarget` | Member, frozen target, proof and verified method → proof outcome | Member appointment and target digest match; approved method; no proxy. |
| `FinalizeProceeding` | Owner completion verdict referencing specific required targets → finalized record | All required verified attestations and owner evidence; no generic approval. |
| `AppendSupplement` | Reason, content/evidence and actor → linked supplement | Original remains readable; owner policy governs supplemental proof. |
| `ReadProceeding`, `ExportProceeding` | Owner-scoped reader → permitted facts/proof bundle | Contextual field-level disclosure; public readout/register is a Bid Opening read, not these endpoints. |

### 7.1 First-owner binding and profile presentation

BOP-CHG-001 v0.9 §7.1 is the controlling binding register. PRC rejects an owner transition whose producer event ID, consumer operation, validation, failure result or integrated test is absent; the owner supplies actor-specific next steps and maps generic PRC errors to profile-specific BOP copy. Owner interruption is an append-only event while PRC remains `In session`; BOP's completion transition first finalizes PRC and then emits its once-only handoff in a guarded transaction/recoverable outbox. Failed PRC finalization cannot yield a BOP handoff. `MarkNotHeld` is terminal for a never-started session. `CloseAbortedProceeding` is terminal after Start and TPR cancellation; neither can finalize or hand off. A convened zero-bid session has the same approved count-neutral pre-Begin custody guard as a nonempty one, then real start/end, factual empty register and actual minutes/targets without any decrypt, subject to the approved legal profile. A never-started Not held case preserves BDS custody and AO work until a lawful Tender decision; if TPR already cancelled, its committed decision needs no duplicate AO item. TPR does not imply an automatic restart.

Before freeze, BOP supplies the committee's recorded designated page(s) selected in the bid work area, renderer-identified price and applicable change locations, every minutes page and final-page targets with immutable render/version/digests. The generated draft is reviewed before the recorder invokes Finish; PRC does not create a separate approval. An empty opening has only opening-record targets in its design scenario. A roster successor attests only their own required scope and never signs for a former member's participation. The owner leaves unresolved proof blocked pending a lawful operating-profile disposition; PRC invents no substitute signer. `SupersedeFrozenMinutes` records a new version before finalization and invalidates satisfaction of earlier digests; after finalization the only correction route is an immutable supplement.

## 8. Error contract

| Code | User-visible message | Result and recovery owner |
|---|---|---|
| `PRC_OWNER_UNAVAILABLE` | **This opening record is not available.** | No disclosure; Bid Opening repairs/authorizes reference. |
| `PRC_START_BLOCKED` | **The opening session cannot start yet. Review the opening requirement shown here.** | Owner supplies specific blocker and in-product fix in its next-step contract. |
| `PRC_MEMBER_REQUIRED` | **You are not an appointed member for this opening.** | No attestation; accounting officer/Bid Opening manages appointment. |
| `PRC_TARGET_CHANGED` | **The opening record changed. Review the latest version before signing.** | No stale proof; member reviews new frozen version. |
| `PRC_PROOF_UNVERIFIED` | **We could not verify your signature. Follow the steps shown here.** | No completion; the shared support method supplies the precise recovery interaction. This integration requirement is not user-facing copy. |
| `PRC_EVIDENCE_INCOMPLETE` | **Some opening details are still missing. Review the items shown here.** | No finalization; owner supplies all missing facts and holders. |
| `PRC_VERSION_CONFLICT` | **This record changed while you were working. Refresh it and try again.** | No partial effect. |
| `PRC_ALREADY_FINALIZED` | **This record is final. Add a correction if a fact needs to change.** | Original immutable; owner-authorized supplement route. In BOP use **This opening record is final. Add a correction if a fact needs to change.** and BOP §10.6 **Correct opening record**. |

Cross-scope reads use the KT-STD-001 `Not found` treatment. Every blocked owner action must return its concrete guard reason and fixes under KT-STD-001 §3B, rather than exposing only the generic PRC error sentence.

## 9. UI architecture and routes

PRC defines **no menu entry, Home tile, independent register, generic form or supplier portal route**. The Bid Opening change unit owns the canonical internal opening route and the authorized attendance/readout and bidder-register-copy routes. It composes PRC's attendance, event timeline, minutes and member-action regions into its screens. A read-only auditor view may reuse the same owner route under its own verdict.

No route may infer authority from possession of a PRC record ID. A verified pre-session arrival still active at Start is retained as in-session attendance automatically; departure is separately recorded. A pending proceeding viewed before opening cannot expose BDS box-derived bidder identities, bid counts or contents; independently observed attendee/receipt identities are separately restricted.

## 10. Static design contract — owner binding required

This document intentionally supplies **no incomplete Claude Design prompt**. PRC has no standalone page to draw. Bid Opening v0.9 §10 supplies labelled design scenarios and complete owner artboard briefs under KT-STD-001 v1.10 §2.6.8 for: before opening; live session; interruption/blocked recovery; session ended/minutes preparation; member review/signing; finalized history; supplier attendance/readout; and requested register copy if a supplier-facing screen is used. The owner brief identifies actor, pictured instant, Tender/version, illustrative attendance and event facts, Level 1/2/3 hierarchy, action and next holder for each variant; §20 traces the owner/PRC result and disclosure.

**Region contract for owner artboards:** top task/next-step and lawful opening action; committee and attendance facts; chronological opened-bid/readout facts from Bid Opening; minutes/attestation action in the relevant later state; register and custody evidence as subordinate links. No second PRC status narrative or generic approval bar. The supplier view contains only its lawful attendance/readout data, never internal member actions or full competing bids. Use KT-STD-001 §2, §2.9 and the approved desktop shell; the BOP v0.9 owner artboards are drawable from the labelled scenarios; the support module owns provider-specific signing and secure-access screens.

## 11. Functional interaction requirements — excluded from design prompts

The owning Bid Opening interaction map must bind every visible control to its command/read, navigation/mutation result, permission, successful outcome and error. At minimum: publish arrangements, join/leave, guarded custody participation, Start opening, record attendee, open next bid/read out, factual observation/exception, interruption/resume, end session, prepare/freeze/supersede minutes, personally review and sign the required record, view register, request/copy, AO record-not-held only where no session began, export permitted record and append correction. `FinalizeProceeding` is a guarded internal owner transition after the last verified proof, not a visible chair/recorder control. PRC does not define the bid-opening controls' behavior; it supplies the corresponding evidence operations in §7. No artboard may display a control whose owner command is absent.

## 12. Audit and historical integrity

Every material command records actor, owner, trusted time, prior/current version, outcome, idempotency key and evidence references; denied, stale and failed attestation attempts are auditable without disclosing bid contents. Owner events retain their owner IDs and order. Final minutes, digest, each member's proof and each supplement are independently reproducible on export. Audit/technical reads cannot become a path around the sealed box. Retention follows the authorized procurement record schedule in the governing owner; PRC invents no separate retention period.

## 13. Deterministic seed and negative fixtures

In a synthetic test profile, every relevant PRC owner view has **Test opening — synthetic bids only** and each proof has **Test attestation — not an electronic signature**. The action is **Record test attestation**. These labels apply solely to verification scripts; BOP v0.9 §10 owns product wording; verification labels are not product copy.

Use KT-STD-001 v1.10 §8's `PE-MOH`, `Africa/Nairobi`, Amina Hassan (Accounting Officer), Charles Mutiso (Head of Procurement), Brian Wafula (Procurement Officer), Naomi Chebet (Auditor) and Administrator. BOP v0.9 §10 uses the BDS Tender/receipt facts and separately labelled illustrative BOP/PRC events for the design scenario. BOP §13 keeps invented proxy records in an isolated verification deployment/database using the same site-wide `PE-MOH`, with separate data, routes and credentials. No second PE is modelled. Amina's accounting-officer responsibility **does not itself make her an opening committee member**. The Bid Opening owner must commit at least three eligible appointments and designate the recorder before any product screen asserts an actual committee; proposed design names alone are not an appointment.

| Fixture ID | Setup / expected PRC result | Use |
|---|---|---|
| PRC-S01 | Owner simulator creates a pending record and replays same key; one ID and one create event | Independent shared-service contract only. |
| PRC-S02 | Simulator starts, appends two ordered events, records attendance, ends, freezes minutes, records verified target proofs and finalizes | Independent state/immutability test with **test-only** actors and targets; not legal compliance evidence. |
| PRC-N01 | Different payload reuses same event ID; rejected, original unchanged | Replay/conflict. |
| PRC-N02 | Member proof binds obsolete minutes digest; rejected, prior proof retained | Attestation integrity. |
| PRC-N03 | Administrator attempts start, sign and content read; denied | Separation of authority. |
| PRC-N04 | Unfinished session, missing owner event or unverified proof; finalization blocked with all missing items | Owner binding and dead-end. |
| PRC-N05 | Finalized minutes correction adds supplement; original export unchanged | History. |
| PRC-N06 | One member attests Version 1; authorized recorder supersedes with reason; old proof retained, each current target on Version 2 requires fresh proof and finalization blocks until complete | Pre-finalization correction. |
| PRC-N07 | Convened session with zero bids reaches factual empty-register minutes/proofs, after the same count-neutral custody guard but without decrypt; never-started session is Not held with no successful handoff | State distinction. |
| PRC-N08 | Member and visitor join/leave while Pending: attributed pre-session events, no bidder facts or false start; Start snapshots active members and carries still-active visitors into session attendance without a second arrival event | Pre-session chronology. |
| PRC-N09 | Authoritative TPR cancellation after actual Start calls CloseAbortedProceeding once; actual start/cessation and partial events remain, while Start/End/Freeze/Attest/Finalize and BOP handoff are denied. | Terminal partial ceremony. |
| PRC-N10 | MarkNotHeld from Pending is terminal; late Start/release/finalization on same identity fails. | Terminal never-started case. |
| PRC-N11 | Recorder confirms readout after reveal; trusted confirmation time is retained while a reported earlier speech time stays attributed, never replaces the event time. A pre-reveal confirmation fails. | Time and human evidence. |
| PRC-N12 | Owner's one empty-outcome command commits factual zero and End exactly once; replay adds no second event, and pre-Start use is denied. | One-action empty ceremony. |
| PRC-INT-01 | BDS closes the canonical Tender; Bid Opening opens with appointed members, supplier attendance, custody exception and final minutes | Design scenario supplied in BOP v0.9. Integrated implementation test remains pending; a synthetic owner test does not establish a real ceremony. |

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
| PRC-A07 | For a nonempty completed opening, Bid Opening handoff to Evaluation cites exact opened packages, register and PRC record without PRC evaluating a bid. A zero-bid completion has no Evaluation handoff. | Bid Opening integration test. |
| PRC-A08 | Every owner artboard/control has a source-grounded scenario, permission and interaction mapping; all BOP variants use labelled design scenarios; runtime fields map to actual owner/support events, and verification proxy data stays outside product UI. | Bid Opening design/release evidence. |
| PRC-A09 | Superseding a frozen pre-final version requires reason and latest targets; prior proofs remain visible but cannot complete; finalized correction uses supplement. | PRC-N06 and BOP-N11. |
| PRC-A10 | A convened zero-current-bid session has real attendance/empty register/minutes/targets, while never-started is Not held; the same approved count-neutral pre-Begin custody guard are required, but no package is decrypted. | PRC-N07 and BOP-N12. |
| PRC-A11 | Pending accepts only attributed pre-session presence/custody/opaque close-reference events, has no actual start time or sealed-box-derived bidder facts; attendee representation never proves submission. At Start, active arrivals appear in the session view without duplicated arrivals. | PRC-N08 and BOP-N14. |
| PRC-A12 | Terminal Not held and Aborted after start cannot Start, resume, freeze, attest, finalize or hand off; the latter retains actual partial chronology and cessation time. | PRC-N09, PRC-N10 and BOP-N17–N18. |
| PRC-A13 | Readout time does not backdate trusted events; empty outcome/end is atomic and idempotent. | PRC-N11–N12 and BOP-A19–A20. |

**Readiness:** PRC-A01, A02's shared portions and A05 can be implemented against the test owner. PRC-A03, A04, A06–A08 and the owner-specific part of A02 **cannot pass in isolation**. This does not block PRC design or development. Complete the owner integration suite before marking integrated behavior complete. The owner's state/actor dead-end matrix and hand-off tests satisfy KT-STD-001 §3B/§6 for the combined journey; there is no duplicate independent PRC workflow matrix.

## 15. Implementation and test constraints

Implement in the existing KenTender procurement architecture as shared services and records; exact Frappe app/DocType placement follows repository ownership. Reuse canonical identity, authorization, audit, time, cryptographic signature and evidence custody services. Tests call public commands rather than writing governed records directly. KT-STD-001 v1.10 §4–6 governs build, contract, browser, visual and first-view checks. The binding seam shall be exercised by a deterministic simulated owner before integration, then by a real Bid Opening owner fixture. A simulated passing contract is labeled only as shared-service evidence.

## 16. Prohibited shortcuts

No generic “Approve minutes” action; no attendee-is-member assumption; no admin override; no arbitrary quorum field; no client clock; no editing event history or signed minutes; no copied bid data as free-text minutes; no bulk disclosure to supplier attendees; no silent completion on credential or signature failure; no PDF attachment standing in for structured owner events; no mock opening in production; no three-password rule hard-coded from an unverified operative regulation. KT-STD-001 §2.3 and §10 also apply.

## 17. Traceability and precedence

| Source | Effect here | Follow-up owner |
|---|---|---|
| Approved BDS-CHG-001 v0.8; G1-REG-001 v1.1 | Sealed handoff only, no BDS opening command; approved first product boundary | Bid Opening consumes, cannot revise BDS by implication. |
| KT-STD-001 v1.10 | Document skeleton, closed design input, next-step/guard/hand-off, seed, verification | PRC core and BOP v0.9 owner journey are specified; implementation follows their bindings. |
| PPADA 2015, §78 and §67 | Committee/opening/minutes and confidentiality constraints inform first consumer | LAW-V-001 and Bid Opening map statutory obligations to electronic controls. |
| LAW-REG-001 v1.2 LAW-V-001 | Current legal instrument and signing interpretation unresolved | Legal/operating profile before production. |
| Supplied Procurement Proceedings Functional Design v1 | Conceptual input, not a current KenTender authority | Future contract phases only where separately approved. |

Source check: [PPRA review record reproducing Act §78](https://ppra.go.ke/?mdocs-file=10256); [2025 High Court judgment on the 2020 Regulations](https://new.kenyalaw.org/akn/ke/judgment/kehc/2025/19224/eng%402025-12-04/source.pdf). The operative effect of that judgment, any stay/appeal and any replacement instrument require legal verification; this document does not assert that an electronic click meets §78 signing.

## 18. Approval effect

**v0.10:** proposed coordinated amendment; v0.9 approval below is historical and does not imply v0.10 approval. The new Evaluation profile follows the already approved EVL v0.4 contract. Shared Trust production gates and integration verification remain unchanged.

Project Owner approval on 29 September 2026 replaces v0.8's shared-service detail with v0.9 while retaining its accepted minimal scope. It authorizes implementation and contract testing of PRC's owner-independent core. Bid Opening v0.9 specifies the contextual UI for design and development. This approval does not choose a provider-specific electronic signature method or authorize a real opening ceremony. Dependent integration tests remain pending until implemented.


## 19. Controlled change account

**v0.9 over v0.8.** Active pre-session arrivals are referenced at Start without fabricated second arrival events; empty-outcome recording and End are one owner action; human readout confirmation has trusted commit time separately from any reported speech instant; page selection is recorded during readout and consumed by Freeze. The owner is BOP v0.9. PRC has no standalone design boards.

**Historical v0.8 over v0.7.** The owner design was supplied in BOP v0.8 §10. PRC had no standalone page; its service could be implemented against the owner interface and labelled scenarios. Source evidence was required at runtime, not before an artboard could be drawn. The v0.7 file contains the earlier change account.

**Historical v0.7 account.** The retained v0.6 contains the prior change account. v0.7 aligned the PRC binding and design references with BOP v0.6, while incorrectly blocking artboards on real method/renderer/proof inputs. PRC still had no standalone page. `Not held` and `Aborted after start` remained terminal, and zero-bid completion emitted no Evaluation handoff.

| v0.6 exact excerpt | v0.7 exact replacement excerpt | Reason |
|---|---|---|
| “BOP-CHG-001 v0.5 proposed owner” | “BOP-CHG-001 v0.6 proposed owner” | Current owner. |
| “The Bid Opening v0.5 change unit” | “The Bid Opening v0.6 change unit” | Historical v0.7 design reference. |
| “test custody confirmation, Start opening” | “guarded custody participation, Start opening” | Product control no longer names the proxy. |

**29 September 2026 focused clarification (v0.9 retained).** In BOP, map PRC_VERSION_CONFLICT to BOP_VERSION_CONFLICT copy. RecordMemberAccount retains the member as author; a recorder’s response is a separate linked event. The BOP §10.6 attendance-note supplement uses authenticated recorder authorship under that narrow owner policy; it cannot replace signatures, original records or handoff evidence.

## 20. Bid Evaluation owner profile — coordinated EVL v0.4 binding

### 20.1 Ownership, records and access

One Evaluation proceeding is unique by owner type **Bid Evaluation** and Evaluation case ID. It references the completed BOP proceeding; it never reuses or alters that record. It can exist during preparation with no session or bid content. Zero or more real discussion sessions are children; at most one is active. Ending a session does not end the evaluation. Individual evidence review and report signing do not require an active session.

| Record | Required owner binding and purpose |
|---|---|
| Evaluation proceeding | Evaluation ID, tender reference, creation event, owner lifecycle/version and optional completed BOP reference. Projection of EVL state, not a second competing workflow. |
| Roster history | EVL appointment/replacement/declaration references, member identity/designation/capacity and eligibility version. No PRC appointment, automatic eligibility or removal for absence. |
| Discussion session | Child identity, start/end event and trusted time, chair, personal joins/leaves, secretary presence, subjects, attributed notes and owner conclusion references. No retrospective attendance entry. |
| Ordered material event | Owner event ID/version, actor, trusted time, affected bid/requirement references, session where applicable, immutable evidence/reason references and participating roster for collective decisions. Replays return the original; conflicting payloads fail. |
| Report target set | Kind Evaluation report or Due-diligence report; owner report ID/version, immutable rendered content/annex references and digests, required personal signer set and page/final targets. Evaluation report targets cover the same report version and annex set for all required members. Due-diligence targets cover every rendered page for initials and final report signature by each actual participant. |
| Personal proof | Exact target identity/version/digest, appointed signer, approved method, result and trusted time; uncertain, failed, stale or wrong-person proof satisfies no target. |
| Completion/correction | Owner durable delivery event/report version or later correction/supplement reference. No PRC-generated recommendation or downstream review decision. |

Every read/export rechecks EVL’s current actor/record verdict. Committee appointment plus personal eligibility governs internal bid access; the secretary has only their EVL-appointed scope. Supplier correspondence is an EVL allowlisted projection through BDS, never general PRC access. The AO/Head’s preparation tasks disclose no sealed-bid facts. Technical support sees only safe incident details. EVL owns My Work, next steps, all screens and all task clearing; PRC adds no workspace, approval or parallel task.

### 20.2 Logical operations and committed effects

All operations use authenticated EVL owner identity, expected owner/record version, an idempotency key and exact source references. Human actions preserve the actual acting person. An owner conclusion and its PRC evidence must commit atomically or via a durable recoverable outbox; an incomplete required write cannot appear as a completed business action.

| Operation | Guard and effect |
|---|---|
| `CreateEvaluationProceeding` | One case per Evaluation ID; duplicate publication/intake paths reuse it. Preparation contains no opening success or bid data. |
| `StartEvaluationDiscussion` | Current eligible chair; no active session; EVL’s suspension/cancellation guards pass. Creates child and chair’s personal join atomically. No second Join for the chair. |
| `JoinEvaluationDiscussion`, `LeaveEvaluationDiscussion` | Actual current member personally joins/leaves an active child; secretary presence is distinct and cannot satisfy member participation. No bulk attendance action or invented timer. |
| `RecordEvaluationConclusion` | EVL supplies its committed decision reference and evidence, complete current eligible roster and current personal participation. Applies to resolved/qualified findings, clarification authorisation, verification plans/outcomes and final reply disposition. These specialised EVL commands record this evidence directly; no preceding generic conclusion click. Notes and own-authored dissent remain distinct from the collective decision. |
| `EndEvaluationDiscussion` | Chair ends actual child; preserve attendance and events. Absence may end a paused session without inventing a conclusion. No active child may remain when EVL freezes its report. |
| `FreezeEvaluationReport` | EVL validates source impact, roster, correspondence dispositions, due diligence and outcome; supplies complete immutable target set and required signers. Also used with kind Due-diligence report after all named participants record observations, under the named lead’s EVL action. Creates no extra PRC approval. |
| `RecordEvaluationProof` | Personally authenticated required signer and verified exact current target. EVL may sign an explicitly qualified expired-validity report; PRC adds no unconditional expiry rejection. Test attestation remains test-only under TRUST. |
| `SupersedeEvaluationReport` | EVL reason and new owner version/target set; preserve earlier content/proofs but none satisfies the successor. Roster or material target changes require fresh proof. A delivered report is retained and corrected through the owner’s versioned return/correction route. |
| `CompleteEvaluationRecord` | EVL supplies all required valid report proofs AND the committed recipient record/task delivery identity. Failed delivery retains Signing and all valid proofs; retry uses the same delivery identity. No Complete/Release button and no second receipt approval. |
| `AppendEvaluationCorrection` | Immutable owner correction or source-supplement reference; retain delivered report and original proofs. EVL supplies source-specific review/impact tasks; PRC cannot reopen an award basis. |
| Scoped read/export | Return authorised sessions, ordered owner evidence, exact reports/proofs and linked later corrections; no reusable unscoped evidence URL. |

Appointment, replacement, declaration, individual finding, own disagreement, note, suspension, cancellation, no-bids closure and delivery failure are append-only owner events using the shared event envelope. They do not create an additional user command. PRC must not manufacture a session merely to store one of these events.

### 20.3 State, recovery and design bindings

EVL lifecycle **Preparing / Reviewing / Signing / Report sent / No evaluation required / Cancelled** is authoritative. PRC stores the owner state/version and evidence status; it does not run the Bid Opening Pending→In session→minutes→Finalized lifecycle for Evaluation. A verified empty outcome preserves any preparation/roster history and closes it without sessions, assessment/report/signing tasks; without an existing case, no PRC case is created. Cancellation retains partial sessions/proofs, stops further decisions/signing, and records terminal closure; an already delivered report remains delivered. Suspension retains current work/proofs while EVL enforces allowed administrative scope and resumption. A source issue is not an empty outcome.

| Failure | Evaluation-facing recovery |
|---|---|
| Absent/ineligible member at collective commit | EVL_MEMBERS_ABSENT / EVL eligibility guard; current named member joins or AO resolves appointment. Reading and individual notes continue. |
| Target changed or proof uncertain | EVL stale-target/proof recovery; refresh or reconcile the same proof attempt, never count uncertainty as signed. |
| PRC evidence write unavailable | Keep owner operation pending/failed with its correlation identity; retry/reconcile once, no duplicate conclusion/task or false completion. Technical support cannot supply the missing decision. |
| Delivery unavailable after valid proofs | EVL_REPORT_DELIVERY_FAILED; secretary Retry delivery; preserve Signing and signatures until durable recipient delivery. |
| Cross-scope read | Not found; no record existence or bid facts. |

EVL v0.4 §9 owns the complete design input (discussion D05, report D07, verification D08); §10 maps visible actions to EVL commands. This service supplies no standalone artboard. Use owner-specific plain language rather than the opening-specific messages in §8. Preserve the approved Opening messages and tests.

### 20.4 Acceptance and regression evidence

| ID | Required implementation evidence |
|---|---|
| PRC-E01 | Replayed publication/intake creates one Evaluation case; two successive discussions create two children, never two Evaluation cases; concurrent Start admits one active child. |
| PRC-E02 | Start joins chair once; other members join personally; a leave/recusal before decision prevents collective commit; secretary presence and historical attendance never substitute. |
| PRC-E03 | Specialised clarification/verification commands commit one conclusion reference and PRC event; failed evidence writes cannot appear complete; own dissent remains attributed. |
| PRC-E04 | Freeze exact report/annex targets; exercise ordinary and due-diligence target sets, stale/failed/uncertain/wrong-signer proofs and roster/target supersession. All current required targets must pass. |
| PRC-E05 | Final proof plus failed recipient delivery retains Signing and proofs; retry creates one recipient task, then completion. No extra human completion action. |
| PRC-E06 | Empty closure, cancellation at preparation/review/signing/after delivery, suspension and pre-/post-decision correction preserve the EVL histories and guards. |
| PRC-E07 | Supplier and technical readers cannot use PRC IDs to reach internal findings; export reproduces exact reports, proofs and later corrections. |
| PRC-E08 | Existing PRC-A01–A13 and BOP v0.10 owner outcomes retain their Opening meaning; no Evaluation command opens a bid or changes completed opening evidence. |

These are required tests, not executed results. v0.10 adds the Evaluation profile only; production signing/custody remains deferred as stated in TRUST-ADR-001.
