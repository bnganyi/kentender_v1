# TPR-CHG-001 v0.12 — Tenders delta build — tracker

**Authority:** `KenTender_TPR-CHG-001_Tenders_v0_12.md` (control table: Approved 26 September 2026).
**Companions:** `TPR-CHG-001_Implementation_Plan.md` (decisions D2′–D26, W1–W8; conflicts C17–C24), `TPR-CHG-001_FOLLOW_UPS.md`, `design/` (26 Sep 2026 board set), `evidence/v0_12/`.
**Predecessor tracking:** `retired/TPR-CHG-001_v0_8_IMPLEMENTATION_TRACKER.md` (v0.8, Phases 0–9 Done 19 Sep 2026). v0.8 evidence proves the kept mechanics only; every v0.12 row needs its own evidence.
**Status:** Phase 0 in progress.
**Started:** 26 September 2026.

## Tracker rules

1. Rows are permanent. Vocabulary: `Planned` / `In progress` / `Blocked` / `Partial` / `Done`. Reversed decisions are struck through in place.
2. `Done` requires the row's own evidence: a command with result counts, a named test, a diff, or a described browser observation with literal rendered strings. Never record a result that was not observed.
3. Prohibited after this cycle: `Tender Addendum Inquiry`, `TND_INQUIRY_LATE`, `receive_addendum_inquiry`, `respond_to_addendum_inquiry`, the three-part preparation progress row, a Tender-local response/evaluation/contract builder, **Mark as published**, an active `Integrated acknowledgement`, a channel selector for the AO, a Candidate release state, a status narrative that §10.17 says the guidance replaces.
4. Boards govern structure (class-for-class); §10.1 and §10.17 govern every literal the browser asserts (W1).
5. Every visible action maps to exactly one §7 command; guards and `next_step` come from the server only.
6. Site-safety protocol (plan §5) applies to every Python and Playwright run.

## Decision log

| Date | Decision | Rationale |
|---|---|---|
| 2026-09-26 | OD-1 update the shared guidance component; OD-2 build everything with a candidate stand-in; OD-3 implement to the end. | Owner answers this session (plan §2). |
| 2026-09-26 | Planning keeps its approved reduced wording and header placement as per-module settings. | PLN-CHG-001 v1.27 lines 1271, 1917 (plan §2 note). |

## Gate register

| Gate | Condition | Status | Evidence |
|---|---|---|---|
| TND12-G00 | Docs; design set committed; scoped fixture wipes proven | In progress | |
| TND12-G01 | Schema, errors, compatibility, STD digests, Published Bid Definition; schema + services gates | Planned | |
| TND12-G02 (CP1) | Shared guidance; Tenders guidance/guards/hand-offs; dead-end matrix; Planning re-verified; fidelity harness | Planned | |
| TND12-G03 | Slice A DES-03/04/05 | Planned | |
| TND12-G04 | Slice B DES-06/07 | Planned | |
| TND12-G05 (CP2) | Slice C DES-08 | Planned | |
| TND12-G06 | Slice D DES-09 + clarification intake + notice engine | Planned | |
| TND12-G07 | Slice E DES-10 | Planned | |
| TND12-G08 | Slice F DES-11 | Planned | |
| TND12-G09 (CP3) | Slice G DES-12 | Planned | |
| TND12-G10 | Slice H DES-13 | Planned | |
| TND12-G11 | Slice I DES-14 | Planned | |
| TND12-G12 | Slice J DES-01/02 | Planned | |
| TND12-G13 (CP4) | Seeds, persona pass, evidence, AC map | Planned | |

## Work register — Phase 0: docs, safety, housekeeping

| ID | Item | Status | Evidence |
|---|---|---|---|
| TND12-001 | Retire v0.8 spec/plan/tracker/follow-ups to `retired/` with banner; author v0.12 plan, tracker, follow-ups | In progress | |
| TND12-002 | Commit the 26 Sep design set (+ handoff note, TenderGuidance, DES-11 rename); delete `retired/design/*:Zone.Identifier` | Planned | |
| TND12-003 | Scope `tenders/tests/fixtures.py` and `procurement_requisitions/tests/fixtures.py` wipes; `test_fixture_scope.py` counts test | Planned | |
| TND12-004 | `make tenders-preflight` (process check) wired into the `tenders-*` gates | Planned | |

## Work register — Phase 1: schema, errors, contracts, definition

| ID | Item | Status | Evidence |
|---|---|---|---|
| TND12-101 | STD `binding_facts` returns the three rule digests; Tender/Version bind and verify them | Planned | |
| TND12-102 | New doctypes: Clarification, Candidate Notice (+attempt), Bid Definition, Candidate Registration (stand-in) | Planned | |
| TND12-103 | Changed doctypes: Publication, Addendum, Channel Confirmation, Cancellation, Task; drop Addendum Inquiry; patches; `_TND_FAMILY` hooks | Planned | |
| TND12-104 | `errors.py` → 35 codes; schema test re-pinned | Planned | |
| TND12-105 | Nine-check compatibility incl. County-residents and reservation-rule availability | Planned | |
| TND12-106 | `bid_definition.py`: TenderVersionProjection v1 + shared compiler; retire Tender-local builders | Planned | |
| TND12-107 | `candidate_gateway.py`, `notice_transport.py`, stand-in; contract pins | Planned | |
| TND12-108 | Canonical clear lists; migrate ×2; reseed; gates | Planned | |

## Work register — Phase 2: guidance, guards, hand-offs, harness (CP1)

| ID | Item | Status | Evidence |
|---|---|---|---|
| TND12-201 | Core `next_step.py`: per-module reduced wording; "Waiting on someone" label | Planned | |
| TND12-202 | Core JourneyTracker/NextStep/`.kt-guidance` restyle to the handoff; `.kt-choice-row`/`.kt-dependent`; guidance.spec | Planned | |
| TND12-203 | Planning re-verification (vitest, dead-end gate, one browser look) | Planned | |
| TND12-204 | `tenders/services/guidance.py` + reads return `next_step`/`journey` | Planned | |
| TND12-205 | `tenders/services/guards.py`; `allowed_actions` derived from guards | Planned | |
| TND12-206 | `tenders/services/handoffs.py` + My Work assigned/waiting rows + notifications | Planned | |
| TND12-207 | `test_dead_end_matrix.py` + `make tenders-dead-end-gate` | Planned | |
| TND12-208 | UI plumbing: guidance bundle, `useGuidance`, vitest setup | Planned | |
| TND12-209 | Fidelity harness: label-keyed boards, departures registry, §10.17 guidance table, provenance fix | Planned | |

## Work register — Phases 3–12: vertical slices

| ID | Slice | Boards | Status | Evidence |
|---|---|---|---|---|
| TND12-300 | A — Preparation | DES-03, DES-04 (+Returned), DES-05 | Planned | |
| TND12-400 | B — Decisions + definition freeze | DES-06, DES-07 | Planned | |
| TND12-500 | C — Publication confirmation | DES-08 | Planned | |
| TND12-600 | D — Published, clarification intake, notices | DES-09 | Planned | |
| TND12-700 | E — Addendum (seven variants), cancellation review | DES-10 | Planned | |
| TND12-800 | F — Supplier clarification | DES-11 | Planned | |
| TND12-900 | G — Cancel (five variants) | DES-12 | Planned | |
| TND12-1000 | H — Correction states | DES-13 | Planned | |
| TND12-1100 | I — Common states | DES-14 | Planned | |
| TND12-1200 | J — Workspace, Start | DES-01, DES-02 | Planned | |

## Work register — Phase 13: seeds and release evidence (CP4)

| ID | Item | Status | Evidence |
|---|---|---|---|
| TND12-1301 | Canonical §13.3 seed idempotent ×2; every §13.4 profile | Planned | |
| TND12-1302 | Persona pass (Brian, Charles, Amina, Naomi, Grace) at 1440 / 390 / 200% | Planned | |
| TND12-1303 | Evidence pack, bundle hash, gates, prohibited-token scan, runbooks, AC map | Planned | |
| TND12-1304 | Representative-user sessions (TPR-IMP-052, TPR09-AC-080) | Planned — owner | |

## Board map

| Board (label) | File | Vue | Spec | Status |
|---|---|---|---|---|
| TPR-DES-01 Tenders workspace | Tenders Workspace.dc.html | WorkspaceScreen | tnd-workspace | Planned |
| TPR-DES-02 Start Tender dialog | Start Tender Dialog.dc.html | StartTenderDialog | tnd-start | Planned |
| TPR-DES-03 Draft: Tender details | Draft - Tender Details.dc.html | EditorScreen, TaskDetails, RequisitionDrawer | tnd-editor-details | Planned |
| TPR-DES-04 Draft: Supplier and contract requirements | Draft - Supplier and Contract Requirements.dc.html | TaskRequirements, EvidenceDialog | tnd-editor-requirements | Planned |
| TPR-DES-05 Review and submit | Review and Submit.dc.html | ReviewScreen, ContentSections | tnd-review | Planned |
| TPR-DES-06 HOPF approval | HOPF Approval.dc.html | ApprovalScreen | tnd-approval | Planned |
| TPR-DES-07 AO publication authorisation | AO Publication Authorisation.dc.html | AuthorisationScreen | tnd-authorisation | Planned |
| TPR-DES-08 Publication confirmation | Publication Progress and Evidence.dc.html | PublicationScreen, ChannelConfirmationDialog | tnd-publication | Planned |
| TPR-DES-09 Published Tender | Published Tender.dc.html | PublishedScreen | tnd-published | Planned |
| TPR-DES-10 Prepare and issue addendum | Prepare and Issue Addendum.dc.html | AddendumScreen | tnd-addendum | Planned |
| TPR-DES-11 Respond to supplier clarification | Respond to Supplier Clarification.dc.html | ClarificationScreen | tnd-clarification | Planned |
| TPR-DES-12 Cancel Tender | Cancel Tender.dc.html | CancelScreen | tnd-cancel | Planned |
| TPR-DES-13 Returned and requisition-correction states | Requisition Correction.dc.html | CorrectionRequestedScreen | tnd-correction | Planned |
| TPR-DES-14 Common states | Common States.dc.html | CommonState | tnd-common-states | Planned |
| (guidance component) | TenderGuidance.dc.html | core JourneyTracker/NextStep | guidance-10-17 table | Planned |

## Quarantine register (Playwright specs disabled until their slice lands)

| Spec | Reason | Re-enabled by |
|---|---|---|

## Acceptance map

Criterion text is abbreviated; the spec §14 row controls. `Planned` until the named evidence is observed.

| ID | Criterion (short) | Phase | Status | Evidence |
|---|---|---|---|---|
| TPR09-AC-001 | The authenticated application exposes one user-facing menu item named **Tenders**, not separate Preparation and… | | Planned | |
| TPR09-AC-002 | The Tenders workspace combines authorised Requisition starts, Draft work, decisions, publication work and open Tenders… | | Planned | |
| TPR09-AC-003 | A user without a permitted responsibility receives the §10.15 Forbidden state and no Tender data. | | Planned | |
| TPR09-AC-004 | A user with permitted cross-entity scope sees only records in that scope; changing a filter cannot expand it. | | Planned | |
| TPR09-AC-005 | Opening a route, drawer, preview or dialog creates no Tender, Version, publication, task or audit business event. | | Planned | |
| TPR09-AC-006 | A Tender can start only from an available authorised Requisition handoff whose compatibility result permits start. | | Planned | |
| TPR09-AC-007 | Concurrent or repeated `StartTender` requests for one handoff produce one Tender and return its identity. | | Planned | |
| TPR09-AC-008 | Start snapshots the exact authorised Requisition, requirements, Planning references, method, reservation, lotting,… | | Planned | |
| TPR09-AC-009 | Inherited content is visibly read-only and has a route to its source; the Tender service cannot update owner data… | | Planned | |
| TPR09-AC-010 | Requisition-owned correction stops the current Tender Version and can continue only from a newly authorised successor… | | Planned | |
| TPR09-AC-011 | Preparation is presented as three understandable tasks: Tender details; Supplier and contract requirements; Review and… | | Planned | |
| TPR09-AC-012 | Tender details show the purchase, quantities, funding and source facts before officer-authored fields. | | Planned | |
| TPR09-AC-013 | Closing date/time, clarification deadline and meeting choices validate as dates and as an ordered business sequence. | | Planned | |
| TPR09-AC-014 | A physical meeting requires date/time, venue and access instructions; an online meeting requires date/time and join… | | Planned | |
| TPR09-AC-015 | Supplier and contract requirements separate inherited requirements, officer evidence requirements, contract values and… | | Planned | |
| TPR09-AC-016 | An officer can add, edit and remove only Draft evidence requirements; each change is versioned and audited. | | Planned | |
| TPR09-AC-017 | Qualification or evidence wording cannot silently alter an inherited mandatory technical, warranty or acceptance… | | Planned | |
| TPR09-AC-018 | The generated price schedule contains the exact authorised line items, quantities, units, lots and funding split. | | Planned | |
| TPR09-AC-019 | The generated technical schedule contains all eleven §10.1 technical requirements without truncation or substitution. | | Planned | |
| TPR09-AC-020 | The generated warranty/support schedule contains all six §10.1 values and the acceptance schedule all five checks. | | Planned | |
| TPR09-AC-021 | Optional service/material schedules are absent when their inherited source sets are empty and present only when… | | Planned | |
| TPR09-AC-022 | Generated evaluation mappings trace every mandatory check to its governed source and shared evaluation group and… | | Planned | |
| TPR09-AC-023 | Invitation and complete-Tender previews use saved Version data and do not submit, approve, authorise or publish. | | Planned | |
| TPR09-AC-024 | Document generation is deterministic: identical recorded inputs produce the recorded document digest. | | Planned | |
| TPR09-AC-025 | Save returns the authoritative record version; a stale save never overwrites another user's change. | | Planned | |
| TPR09-AC-026 | Review displays one readiness result, issue counts and direct issue links; it does not require users to interpret… | | Planned | |
| TPR09-AC-027 | A Must fix issue prevents submission and identifies the exact task, field or owner route. | | Planned | |
| TPR09-AC-028 | A Review note is visible but does not prevent submission unless another governed rule fails. | | Planned | |
| TPR09-AC-029 | Compatibility is evaluated from authoritative owner projections at start, submit, approve and publication authorisation. | | Planned | |
| TPR09-AC-030 | Submission freezes one exact Version, package digest and generated-document set. | | Planned | |
| TPR09-AC-031 | After submission, the submitted Version is read-only to every business actor. | | Planned | |
| TPR09-AC-032 | HOPF return requires a comment, preserves the submitted Version and creates one copied Draft. | | Planned | |
| TPR09-AC-033 | HOPF approval records the exact submitted Version and package digest and creates an AO publication task. | | Planned | |
| TPR09-AC-034 | HOPF approval does not create channel confirmations, set `published_at` or expose documents to suppliers. | | Planned | |
| TPR09-AC-035 | A person who prepared or submitted a Version cannot approve that Version as HOPF, regardless of concurrent role labels. | | Planned | |
| TPR09-AC-036 | Reopening an approved Tender is possible only before publication authorisation, requires a reason and creates a copied… | | Planned | |
| TPR09-AC-037 | HOPF, AO and reader artboards use the exact fixture actors, values and statuses in §10.1. | | Planned | |
| TPR09-AC-038 | The AO sees the approved package, decision facts and generated required channels, with no package-edit control. | | Planned | |
| TPR09-AC-039 | A person who prepared, submitted or HOPF-approved a Version cannot authorise its publication as AO. | | Planned | |
| TPR09-AC-040 | Every decision command rechecks state, assignment, segregation and package integrity on the server. | | Planned | |
| TPR09-AC-041 | Publication authorisation records AO, time, approved Version, package digest, complete Published Bid Definition… | | Planned | |
| TPR09-AC-042 | The AO cannot choose, remove, replace or edit a required publication channel. | | Planned | |
| TPR09-AC-043 | Committing publication authorisation creates one Evidence-based confirmation record for every required channel and… | | Planned | |
| TPR09-AC-044 | The MVP contains no active State Portal, Ministry website or other publication adapter; Configuration rejects… | | Planned | |
| TPR09-AC-045 | Each required channel confirmation has one stable identity bound to the original publication's channel set and the… | | Planned | |
| TPR09-AC-046 | Only a currently assigned HOPF can confirm channel publication; the AO, technical operator and Procurement Officer… | | Planned | |
| TPR09-AC-047 | Confirmation records the exact required attestation, server-derived HOPF identity/time and actual channel availability… | | Planned | |
| TPR09-AC-048 | System checks are limited to record completeness, format, authority, identity, file integrity/scan and conflicts; no… | | Planned | |
| TPR09-AC-049 | Confirmation requires availability time, evidence reference, applicable public URL, required evidence file/digest and… | | Planned | |
| TPR09-AC-050 | Uploaded evidence is scanned, digested and retained; failed or rejected uploads cannot confirm a channel. | | Planned | |
| TPR09-AC-051 | A Tender is not Published while any mandatory channel is Awaiting confirmation or has missing, invalid or rejected… | | Planned | |
| TPR09-AC-052 | `published_at` is written once as the latest actual availability time among all mandatory channel confirmations. | | Planned | |
| TPR09-AC-053 | On publication confirmation, the minimum preparation period is revalidated from actual `published_at`; an invalid… | | Planned | |
| TPR09-AC-054 | The exact actual invitation date is written once to Planning through its owner contract and replay is idempotent. | | Planned | |
| TPR09-AC-055 | Publication authorisation can be withdrawn only while confirmed unpublished and before any channel confirmation;… | | Planned | |
| TPR09-AC-056 | A Published Tender shows actual publication time, submission deadline, documents, channel evidence, addenda and… | | Planned | |
| TPR09-AC-057 | `CreateAddendumDraft` is unavailable before publication, after submission close or after cancellation. | | Planned | |
| TPR09-AC-058 | An addendum records an explicit before/after comparison, affected reference, reason and materiality explanation. | | Planned | |
| TPR09-AC-059 | An addendum that expands quantity, value, scope, method, reservation, lotting, package structure, technical… | | Planned | |
| TPR09-AC-060 | A late non-material addendum calculates and requires the lawful revised submission deadline before submission for issue. | | Planned | |
| TPR09-AC-061 | HOPF issue freezes the addendum and creates Evidence-based confirmation records for every original required channel. | | Planned | |
| TPR09-AC-062 | The addendum becomes Issued only after HOPF confirms all required channels with the same evidence and attestation… | | Planned | |
| TPR09-AC-063 | A clarification can originate only from an authenticated Bid Submission event tied to an Active Tender-bound candidate… | | Planned | |
| TPR09-AC-064 | A response that would change published Tender content cannot be sent until an authorised linked addendum is Issued and… | | Planned | |
| TPR09-AC-065 | A response that changes no published content may be sent to the asker or all registered candidates as deliberately… | | Planned | |
| TPR09-AC-066 | Only the AO can cancel; cancellation requires an applicable ground and reason and becomes final immediately on commit. | | Planned | |
| TPR09-AC-067 | Cancellation never restores the Requisition, reopens the Tender or creates a replacement procurement automatically. | | Planned | |
| TPR09-AC-068 | Cancellation creates independently tracked notice-publication, candidate-notice and PPRA-report obligations with… | | Planned | |
| TPR09-AC-069 | Every artboard in §10 can be implemented using §10.1 plus KT-STD-001 v1.8 §2 without invented fixture data. | | Planned | |
| TPR09-AC-070 | Every visible action in §10 has exactly one behaviour in §11 and is absent when the server does not permit it. | | Planned | |
| TPR09-AC-071 | The default interface exposes no event keys, hashes, enum values, payloads, transport retries or infrastructure… | | Planned | |
| TPR09-AC-072 | A Procurement Officer can start, complete and submit the primary fixture by following the three task labels without… | | Planned | |
| TPR09-AC-073 | HOPF and AO each see one plain-language decision, its consequence and the exact content being decided. | | Planned | |
| TPR09-AC-074 | Status, stage and next action remain distinct; the interface never labels approval, evidence upload or technical… | | Planned | |
| TPR09-AC-075 | All tables and dialogs meet the keyboard, focus, heading, error-linking, text-status and responsive rules in §11.9. | | Planned | |
| TPR09-AC-076 | Every successful decision, publication, addendum, clarification, candidate-notice and cancellation command writes the… | | Planned | |
| TPR09-AC-077 | Generated and external evidence remains retrievable by immutable digest under authorised audit access. | | Planned | |
| TPR09-AC-078 | The §13 seed can be rerun without duplication and proves the primary and isolated state fixtures independently. | | Planned | |
| TPR09-AC-079 | Owner-contract failure leaves source data unchanged, records a truthful pending/failure state where applicable and… | | Planned | |
| TPR09-AC-080 | Representative Procurement Officer, HOPF and AO usability tests complete their assigned routine tasks without… | | Planned | |
| TPR09-AC-081 | `StartTender` creates nothing unless the exact bound template release is Available and all release/profile/mapping… | | Planned | |
| TPR09-AC-082 | `None`, `Youth`, `Women` and `Persons with disabilities` may pass compatibility only when the exact Available template… | | Planned | |
| TPR09-AC-083 | The published supplier definition is generated from the released response rules and never reconstructed from the PDF. | | Planned | |
| TPR09-AC-084 | Every mandatory technical response retains its individual result and reason while feeding one shared Technical… | | Planned | |
| TPR09-AC-085 | Every response has an evaluation and contract destination or an explicit N/A disposition. | | Planned | |
| TPR09-AC-086 | Publication freezes the response, downstream and addendum-identity rule digests with the documents and package digest. | | Planned | |
| TPR09-AC-087 | A mapping or renderer incompatibility blocks publication and cannot be repaired from the Tenders UI. | | Planned | |
| TPR09-AC-088 | An authorised Administrator, System Manager, Procurement Officer or HOPF can follow a failure link to the read-only… | | Planned | |
| TPR09-AC-089 | A County-residents restriction is evaluated independently from the base reservation category and passes only for an… | | Planned | |
| TPR09-AC-090 | A reserved Tender publishes its exact declaration and evidence requirements, evaluates them under `EVG-ELIGIBILITY`,… | | Planned | |
| TPR09-AC-091 | Publication freezes exactly one `PublishedBidDefinition v1` using every field in §4.5.4; its `template_family`, opaque… | | Planned | |
| TPR09-AC-092 | `BuildPublishedBidDefinition` and publication are atomic: any unsupported control, missing mapping, hidden obligation,… | | Planned | |
| TPR09-AC-093 | Controlled multi-select and structured ports requirements from `AuthorisedRequisitionHandoff v1.3` appear in both… | | Planned | |
| TPR09-AC-094 | The four exact evaluation groups are Eligibility, Technical compliance, Financial and Award; no fifth group, hidden… | | Planned | |
| TPR09-AC-095 | One closed fixture round-trip preserves every source and response identity from Requisition through Tender documents,… | | Planned | |
| TPR09-AC-096 | Publication-definition identity and digests are recorded on `TenderPublication`; publication never writes a late field… | | Planned | |
| TPR09-AC-097 | `IssueAddendum` creates no awaiting-confirmation addendum unless the complete successor Published Bid Definition has… | | Planned | |
| TPR09-AC-098 | While any required addendum channel is unconfirmed, BDS continues to receive the prior effective definition and… | | Planned | |
| TPR09-AC-099 | The final addendum channel confirmation atomically marks the addendum Issued and activates its exact successor… | | Planned | |
| TPR09-AC-100 | Original Tender, addendum and cancellation-notice confirmations have distinct subject identities/digests and… | | Planned | |
| TPR10-AC-001 | A registered candidate can submit a general pre-bid question before the clarification deadline without an addendum… | | Planned | |
| TPR10-AC-002 | No Account-only, public or free-text identity can submit a clarification; the exact Active Tender-bound candidate… | | Planned | |
| TPR10-AC-003 | Receipt at or after the clarification deadline creates no clarification and returns the canonical late message. | | Planned | |
| TPR10-AC-004 | A clarification answer that changes no published content may be direct or general; the selected audience and exact… | | Planned | |
| TPR10-AC-005 | A clarification answer that would change wording, criteria, schedules, dates or supplier obligations remains Awaiting… | | Planned | |
| TPR10-AC-006 | The linked addendum must be Issued and its successor definition effective before the published-change response is sent… | | Planned | |
| TPR10-AC-007 | Every general clarification broadcast, issued addendum, effective deadline change and cancellation freezes the… | | Planned | |
| TPR10-AC-008 | Candidate destinations come only from the Bid Submission owner projection; Tenders cannot create or edit supplier… | | Planned | |
| TPR10-AC-009 | Mandatory notices cannot be opted out of; later contact changes affect only future audience snapshots and never… | | Planned | |
| TPR10-AC-010 | Queued, Sent, Delivered and Failed remain distinct; a provider acceptance is not displayed as recipient delivery… | | Planned | |
| TPR10-AC-011 | A failed notice has a safe same-subject retry/follow-up route and never retracts an issued addendum, changes a… | | Planned | |
| TPR10-AC-012 | Public Tender readers see authoritative clarification answers and notices without the source candidate identity or… | | Planned | |
| TPR10-AC-013 | TPR-DES-09 and TPR-DES-11 render the general-question, published-change and failed-delivery fixtures at desktop and… | | Planned | |
| TPR10-AC-014 | The current MVP ends at the Bid Submission boundary. Bid Opening, Evaluation/Award, Supplier… | | Planned | |
| TPR11-AC-001 | `StartTender` binds only an Available release after compatibility, digest and adapter checks pass. v0.12 (OD5): the… | | Planned | |
| TPR11-AC-002 | An already-bound unpublished Tender may continue on a Superseded release only while every exact asset, digest and… | | Planned | |
| TPR11-AC-003 | Supersession never changes `template_release_id`, regenerates content from a successor or silently offers a selector. | | Planned | |
| TPR11-AC-004 | A Withdrawn bound release blocks submit, approve, reopen, publication authorisation, publication confirmation,… | | Planned | |
| TPR11-AC-005 | The Withdrawn state preserves all work, explains that the current unpublished Tender cannot continue, and offers only… | | Planned | |
| TPR11-AC-006 | A published Tender retains its exact release, documents, Published Bid Definition and public readability after… | | Planned | |
| TPR11-AC-007 | `BuildPublishedBidDefinition` invokes the STD-TPL-IMP-001 v1.1 shared compiler and cannot use a separate… | | Planned | |
| TPR11-AC-008 | Procurement Officer and HOPF can inspect the exact bound release and report a concern without gaining template-edit or… | | Planned | |
| TPR12-AC-001 | `StartTender` binds a release only when it is `Available` and switched On on the site and its compatibility, digest… | | Planned | |
| TPR12-AC-002 | After the bound release is switched Off on the site, every later action on an already-bound Tender (submit, approve,… | | Planned | |
| TPR12-AC-003 | Switching the bound release Off, or back On, never changes the Tender's `template_release_id`, digests, documents or… | | Planned | |
| TPR12-AC-004 | An already-bound `Superseded` release continues and a `Withdrawn` release blocks exactly as TPR11-AC-002 and… | | Planned | |
| TPR12-AC-005 | No Tenders test, fixture, seed or message relies on a `Candidate` release state; start tests cover a release that is… | | Planned | |
| TPR12-AC-006 | Every Tender record read supplies one server-derived `next_step` with kind, headline, stage, holder, recorded since… | | Planned | |
| TPR12-AC-007 | Every §5.1 state and visible responsibility passes KT-STD-001 §3B.7 dead-end conformance; a blocked action yields a… | | Planned | |
| TPR12-AC-008 | The five formal Tender stages and their markers match §10.17, while Tender details, Supplier/contract requirements and… | | Planned | |
| TPR12-AC-009 | Every record-screen variant renders the exact §10.17 next step and permitted tracker, replacing the identified… | | Planned | |
| TPR12-AC-010 | §5.11 hand-off items appear and clear on underlying state changes, preserve return comments and distinguish… | | Planned | |
| TPR12-AC-011 | At 1440 × 1024 the first working region remains in the first view, using the stated one-line reduced tracker if… | | Planned | |
| TPR12-AC-012 | A material addendum cannot be issued. Its exact hand-off creates one AO cancellation-review item and a waiting item;… | | Planned | |

## Re-implementation register map (§19)

| ID | Required implementation (short) | Phase | Status | Evidence |
|---|---|---|---|---|
| TPR-IMP-001 | Create one **Tenders** menu entry and the three routes in §9. | | Planned | |
| TPR-IMP-002 | Build one role-safe workspace covering starts, preparation, decisions, publication and open Tenders. | | Planned | |
| TPR-IMP-003 | Implement server-derived work-summary counts, filters and next actions. | | Planned | |
| TPR-IMP-004 | Implement the exact `Tender` and `TenderVersion` schemas, identities, statuses and concurrency versions. | | Planned | |
| TPR-IMP-005 | Implement immutable inherited requirement snapshots and owner-source links. | | Planned | |
| TPR-IMP-006 | Implement officer-authored evidence requirements separately from inherited requirements. | | Planned | |
| TPR-IMP-007 | Generate price, technical, warranty, acceptance, delivery and evaluation content deterministically. | | Planned | |
| TPR-IMP-008 | Integrate the authorised Requisition handoff and idempotent start command. | | Planned | |
| TPR-IMP-009 | Implement the three-task preparation journey and unsaved-change protection. | | Planned | |
| TPR-IMP-010 | Implement meeting-type conditional fields, ordered date validation and positive-whole-number supplier-experience… | | Planned | |
| TPR-IMP-011 | Implement money/quantity/unit precision and funding/line-item reconciliation. | | Planned | |
| TPR-IMP-012 | Implement compatibility checks at start, submit, approve and publication authorisation, including the supported… | | Planned | |
| TPR-IMP-013 | Implement deterministic Must fix and Review note results with exact issue routes. | | Planned | |
| TPR-IMP-014 | Implement Draft save commands with optimistic concurrency and idempotency. | | Planned | |
| TPR-IMP-015 | Implement deterministic Invitation and complete-Tender generation and preview. | | Planned | |
| TPR-IMP-016 | Implement submission as an immutable Version/package freeze. | | Planned | |
| TPR-IMP-017 | Implement HOPF return with required comment and one copied Draft. | | Planned | |
| TPR-IMP-018 | Implement HOPF approval without publication-confirmation side effects. | | Planned | |
| TPR-IMP-019 | Implement approved-Tender reopening before authorisation only. | | Planned | |
| TPR-IMP-020 | Implement Requisition-correction stop and authorised-successor route. | | Planned | |
| TPR-IMP-021 | Enforce immutable-actor maker-checker rules for HOPF and AO decisions. | | Planned | |
| TPR-IMP-022 | Implement `TenderPublication` with approved package, rule snapshot and AO decision. | | Planned | |
| TPR-IMP-023 | Resolve and snapshot required publication channels from governed configuration; enforce Evidence based mode for every… | | Planned | |
| TPR-IMP-024 | Implement AO publication authorisation as one decision that atomically creates the required evidence-based… | | Planned | |
| TPR-IMP-025 | Implement stable `PublicationChannelConfirmation` identities bound to the exact original-publication channel set and… | | Planned | |
| TPR-IMP-026 | Implement HOPF confirmation for State Portal and Ministry website using channel-specific reference, public URL,… | | Planned | |
| TPR-IMP-027 | Implement HOPF confirmation for notice-board and newspaper channels using channel-specific reference, evidence,… | | Planned | |
| TPR-IMP-028 | Implement truthful Awaiting confirmation and Confirmed states, with rejected input remaining unconfirmed. | | Planned | |
| TPR-IMP-029 | Implement technical validation for confirmation completeness, authority, identity, evidence integrity/scan and package… | | Planned | |
| TPR-IMP-030 | Implement idempotent identical replay and reject any conflicting second confirmation. | | Planned | |
| TPR-IMP-031 | Compute one immutable actual publication time from all mandatory channel evidence. | | Planned | |
| TPR-IMP-032 | Revalidate the minimum preparation period against actual publication time. | | Planned | |
| TPR-IMP-033 | Write actual invitation date once through the Planning owner contract. | | Planned | |
| TPR-IMP-034 | Implement withdrawal of publication authorisation with reason only before any channel is confirmed. | | Planned | |
| TPR-IMP-035 | Implement the published-Tender view with documents, evidence, addenda and clarifications. | | Planned | |
| TPR-IMP-036 | Implement Addendum schema, Draft save, materiality and deadline rules. | | Planned | |
| TPR-IMP-037 | Implement HOPF addendum issue and evidence-based confirmation through every original required channel. | | Planned | |
| TPR-IMP-038 | Implement authenticated general Tender clarification ingestion from an exact Active candidate registration, with… | | Planned | |
| TPR-IMP-039 | Implement direct/general response classification and enforce the issued-addendum prerequisite whenever an answer would… | | Planned | |
| TPR-IMP-040 | Implement AO cancellation with applicable ground, reason and immediate final state. | | Planned | |
| TPR-IMP-041 | Implement optional HOPF cancellation recommendation without decision effect. | | Planned | |
| TPR-IMP-042 | Create and track cancellation channel, candidate-notice and PPRA-report obligations. | | Planned | |
| TPR-IMP-043 | Preserve cancellation finality while required cancellation evidence remains due, is rejected or becomes overdue. | | Planned | |
| TPR-IMP-044 | Implement role-safe reads for Department, Auditor, technical operator and Administrator/System Manager. | | Planned | |
| TPR-IMP-045 | Implement every plain-language error and recovery route in §8. | | Planned | |
| TPR-IMP-046 | Implement all fourteen artboards and stated variants from the self-contained fixture pack. | | Planned | |
| TPR-IMP-047 | Implement every visible control exactly as defined in §11, including pending and error behaviour. | | Planned | |
| TPR-IMP-048 | Implement keyboard, focus, status-text, responsive-table and document-accessibility rules. | | Planned | |
| TPR-IMP-049 | Implement append-only audit and evidence preservation for every fact in §12. | | Planned | |
| TPR-IMP-050 | Implement the idempotent primary and isolated fixture seeds without outcome conflation; the primary… | | Planned | |
| TPR-IMP-051 | Complete every acceptance criterion and automated test minimum. | | Planned | |
| TPR-IMP-052 | Complete representative-user tests for Procurement Officer, HOPF and AO routine journeys. | | Planned | |
| TPR-IMP-053 | Complete publication-confirmation integrity/concurrency exercises and operational runbooks. | | Planned | |
| TPR-IMP-054 | Verify that every prohibited shortcut is absent from code, configuration and UI. | | Planned | |
| TPR-IMP-055 | Produce the immutable Bid Submission handoff at submission close. | | Planned | |
| TPR-IMP-056 | Install and verify the exact Available template release and all document/response/mapping/profile digests. v0.12… | | Planned | |
| TPR-IMP-057 | Generate the exact `PublishedBidDefinition v1` from the released response rules rather than the rendered PDF and… | | Planned | |
| TPR-IMP-058 | Aggregate individual mandatory checks into one shared Technical compliance group while retaining row results and… | | Planned | |
| TPR-IMP-059 | Require an explicit evaluation/contract destination or N/A for every response family. | | Planned | |
| TPR-IMP-060 | Freeze response, downstream and addendum-identity rule digests at publication. | | Planned | |
| TPR-IMP-061 | Link template failures to the read-only **STD Templates** owner route for Administrator, System Manager, Procurement… | | Planned | |
| TPR-IMP-062 | Generate category-specific reservation declarations/evidence and map each to `EVG-ELIGIBILITY` from the exact released… | | Planned | |
| TPR10-IMP-001 | Consume the exact Tender-bound candidate projection created by BDS **Start bid**; do not create a local… | | Planned | |
| TPR10-IMP-002 | Replace addendum-only inquiry endpoints and storage with `TenderClarification`, retaining an optional issued-addendum… | | Planned | |
| TPR10-IMP-003 | Block receipt at the clarification deadline and block any published-changing response until its linked addendum is… | | Planned | |
| TPR10-IMP-004 | Freeze one candidate audience and create outbox dispatches for general clarification broadcasts, issued… | | Planned | |
| TPR10-IMP-005 | Record Queued/Sent/Delivered/Failed and append retry evidence without changing the authoritative Tender action or… | | Planned | |
| TPR10-IMP-006 | Revise TPR-DES-09 and TPR-DES-11 for general questions, mandatory addendum escalation and failed-delivery recovery at… | | Planned | |
| TPR10-IMP-007 | Consume CFG v0.16 public portal support/legal-link projection for bidder-safe Tenders surfaces; expose no editable… | | Planned | |
| TPR10-IMP-008 | Run the closed Requisition→Tender→STD→BDS journey through general clarification, addendum notice, bid preparation and… | | Planned | |
| TPR-IMP-063 | Preserve the reservation category, County-residents treatment and evaluated result in the governed… | | Planned | |
| TPR-IMP-064 | Adopt the exact release/renderer identity names and `PublishedBidDefinition v1` field contract shared with STD-TPL… | | Planned | |
| TPR-IMP-065 | Materialise the definition atomically with publication authorisation and reject partial output on any reconciliation… | | Planned | |
| TPR-IMP-066 | Preserve controlled multi-select and structured ports requirement values in documents, bidder rows and downstream… | | Planned | |
| TPR-IMP-067 | Use exactly four evaluation groups including `EVG-AWARD`; do not create a weighted criterion or duplicate award stage. | | Planned | |
| TPR-IMP-068 | Use `/app/std-templates/{release_id}` for authorised release inspection and remove the System setup Tender-format… | | Planned | |
| TPR-IMP-069 | Complete the cross-module round-trip from `AuthorisedRequisitionHandoff v1.3` through BDS response/mapping consumption… | | Planned | |
| TPR-IMP-070 | Move publication-definition identity and component digests to `TenderPublication`; prohibit any publication-time… | | Planned | |
| TPR-IMP-071 | Build and freeze the complete successor Published Bid Definition in the `IssueAddendum` transaction before creating… | | Planned | |
| TPR-IMP-072 | Keep an awaiting-confirmation addendum's successor definition and revised deadline non-effective for BDS. | | Planned | |
| TPR-IMP-073 | Activate the issued addendum, revised deadline and exact successor definition atomically on final required-channel… | | Planned | |
| TPR-IMP-074 | Scope every channel confirmation by subject type, identity, digest and channel so original package, addenda and… | | Planned | |
| TPR11-IMP-001 | Require Available only at new Tender binding and persist the exact release/adapter/digest set. v0.12 (OD5): the… | | Planned | |
| TPR11-IMP-002 | Recheck bound lifecycle, integrity and renderer adapter at submit, approve, reopen, publication authorisation,… | | Planned | |
| TPR11-IMP-003 | Permit Superseded continuation only for an already-bound Tender and never rewrite its release identity or content. | | Planned | |
| TPR11-IMP-004 | Block every unpublished continuation on Withdrawn while preserving Versions and governed next steps. | | Planned | |
| TPR11-IMP-005 | Preserve published documents and Published Bid Definition after lifecycle change and display the truthful release… | | Planned | |
| TPR11-IMP-006 | Replace any Tender-local builder logic with the shared STD-TPL-IMP v1.0 compiler adapter and canonical parity tests. | | Planned | |
| TPR11-IMP-007 | Grant Procurement Officer/HOPF the bounded release-inspection and concern path without template mutation or general… | | Planned | |
| TPR12-IMP-001 | Bind a new Tender only to the `Available` release of `IT-EQUIPMENT-OPEN-V1` that is switched On on the site, through… | | Planned | |
| TPR12-IMP-002 | Leave the site switch out of every later-action recheck on an already-bound Tender; recheck only lifecycle, integrity… | | Planned | |
| TPR12-IMP-003 | Retire every `Candidate` release case from Tenders tests, fixtures, seeds and messages. | | Planned | |
| TPR12-IMP-004 | Return server-derived next steps, guard reasons and all fixes on record reads; no browser recomputation. | | Planned | |
| TPR12-IMP-005 | Emit §5.11 hand-off My Work and waiting items and clear them only on the underlying state change. | | Planned | |
| TPR12-IMP-006 | Replace the three-part Draft progress row and duplicate status narratives with shared §10.17 components on permitted… | | Planned | |
| TPR12-IMP-007 | Implement the bounded material-addendum cancellation-review hand-off, AO close-with-reason outcome and unissued-draft… | | Planned | |
