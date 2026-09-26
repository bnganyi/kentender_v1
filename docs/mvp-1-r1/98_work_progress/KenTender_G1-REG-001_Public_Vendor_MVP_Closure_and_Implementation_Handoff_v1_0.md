# G1-REG-001 — Public/Vendor MVP Closure and Implementation Handoff

| Control | Value |
|---|---|
| Document ID | G1-REG-001 |
| Version | 1.0 |
| Date | 25 September 2026 |
| Status | **Prepared for Project Owner review** |
| Closed requirements slice | Public Tender discovery through sealed electronic Bid Submission handoff |
| Controlling documents | CFG-CHG-002 v0.16; TPR-CHG-001 v0.10; BDS-CHG-001 v0.7; STD-TPL-001 v0.9; REQ-CHG-001 v1.11 |
| Upstream governed context | PLN-CHG-001 v1.25; BUD-CHG-001 v1.10; LAW-REG-001 v1.2; AUTH-ADR-001 v1.9; KT-STD-001 v1.7; SEED-001 v1.3 |
| Future boundary | Bid Opening, Evaluation and Award, Supplier Management/prequalification, additional procurement methods and additional product families |

## 1. Closure decision

Gate 1 is closed at requirements level for the supported MVP slice: straightforward off-the-shelf IT Goods, Open Tender, single lot, KES, fixed price, public Tender discovery, Tender-bound candidate registration, STD-driven bid preparation and sealed electronic submission.

There is no separate **Declare interest** or **Follow Tender** step. **Start bid** atomically creates or returns the Tender-bound candidate registration, mandatory-notice address and Bid Workspace. General pre-bid questions are supported before the clarification deadline. Tenders owns the authoritative clarification, answer, candidate audience, notice and delivery evidence; Bid Submission owns the candidate relationship and verified notice contact. Configuration owns one allowlisted public support/legal-link projection. The template bundle owns only reusable Tender/document/response/mapping assets and addendum identity rules.

Gate 1 requirements closure is not production go-live approval. Production submission remains disabled by default until the exact signing, trusted-time, encryption, sealed-custody, backup/recovery and incident operating profile has approved implementation and verification evidence.

## 2. Authoritative interface matrix

| Interface fact | Authoritative owner | Consumer | Closed rule |
|---|---|---|---|
| Authorised requirement package | Requisitions v1.11 | Tenders | One immutable handoff; no Tender-side re-entry or expansion. |
| Installed template release | STD-TPL v0.9 | Tenders / Bid Submission | Exact Available release, manifest and digests; no runtime schema or clause builder. |
| Published Bid Definition | Tenders + released template runtime | Bid Submission | Frozen with publication; successor definition becomes effective only with final addendum-channel confirmation. |
| Public support/legal links | CFG v0.16 | Tenders / Bid Submission | One allowlisted read-only projection; no copied editable settings. |
| Candidate registration | Bid Submission v0.7 | Tenders | Created/returned atomically by **Start bid**; no passive follower or standalone arrangement command. |
| Mandatory notice contact | Bid Submission v0.7 | Tenders | Verified Account email, prospectively editable; no opt-out and no retroactive delivery rewrite. |
| Supplier question | Bid Submission → Tenders | Tenders | Authenticated Active candidate only, before deadline; no parallel BDS response store. |
| Clarification answer | Tenders v0.10 | Public portal / candidate workspace | Direct or anonymised general answer when published content is unchanged. |
| Published-content change | Tenders + STD addendum rules | Bid Submission | Answer waits for an issued/effective addendum; no informal change through clarification. |
| Candidate audience and notices | Tenders v0.10 / platform outbox | Bid Submission displays state | Audience frozen at authoritative event; Queued/Sent/Delivered/Failed are truthful evidence states. |
| Bid form and validation | STD-TPL v0.9 definition | Bid Submission | Five supplier tasks generated from exact released metadata; Works/Services are not inferred from the Goods profile. |
| Production submission availability | Deployment operating profile | Bid Submission | One server-side default-false flag checked centrally; no Desk, portal, user or Tender override. |
| Sealed submission handoff | Bid Submission v0.7 | Future Bid Opening | Immutable package, receipt and custody evidence only; no opening/decryption or post-close disclosure. |

## 3. Full functional and design change matrix

| ID | Area | Functional requirement | Design/UI requirement | Implementation and proof |
|---|---|---|---|---|
| G1-001 | Candidate entry | `StartBid` creates or returns arrangement, Active Tender candidate registration, notice contact and workspace atomically. | Public Tender action remains **Start bid**; dialog explains mandatory notices and captures/selects the verified email. | Transaction, idempotency, concurrent-start and no-partial-record tests. |
| G1-002 | Removed workflow | No standalone `CreateBidderArrangement`, Declare interest or Follow Tender in MVP. | Remove buttons, routes, empty states and helper copy that imply those workflows. | Repository/API/route negative scan and migration test. |
| G1-003 | Notice contact | Notice email must be a verified Account email; changes affect future notices only. | Account shows **Tender notice contacts**; Bid company section shows the selected Tender notice email. | Verification, scope, prospective-effect and history tests. |
| G1-004 | General clarification | Active registered candidate may send one 10–2,000-character question before the clarification deadline without an addendum. | **Ask a question** is available after Start bid; show deadline, sent state and immutable receipt time. | Boundary-time, identity, idempotency and input tests. |
| G1-005 | Clarification ownership | BDS sends the authenticated question to TPR and stores no answer/message duplicate. | Candidate workspace renders the TPR-owned question/answer projection. | Cross-module identity and no-parallel-store tests. |
| G1-006 | Answer audience | Procurement may answer the asker or publish an anonymised general response when content is unchanged. | Response form requires **Only this supplier** or **All registered suppliers** and previews protected/public copy. | Audience, privacy, immutability and audit tests. |
| G1-007 | Addendum gate | An answer changing wording, criteria, dates, schedules or obligations cannot be sent until linked addendum is Issued/effective. | Show **Prepare addendum** and an **Awaiting addendum** state; never offer an informal send action. | Change-classification, addendum-state and rollback tests. |
| G1-008 | Mandatory notice events | General broadcasts, issued addenda/deadline changes and cancellation freeze the authoritative candidate audience. | Candidate workspace groups clarification/addendum notices in **Tender documents, clarifications and addenda**. | Audience freeze, concurrent registration and replay tests. |
| G1-009 | Delivery evidence | One dispatch per candidate records destination snapshot and Queued/Sent/Delivered/Failed attempts. Failure does not undo the governing event. | Procurement sees **Delivery problem** with retry/recovery; suppliers never see fabricated delivery. | Atomic outbox, retry, provider-response and no-false-receipt tests. |
| G1-010 | Public Tender history | Public readers see issued addenda, general answers, changed deadlines and cancellation without protected candidate identity/destination. | Public detail keeps documents and authoritative updates together; support/legal footer is visible. | Anonymous-access, redaction and historical-order tests. |
| G1-011 | Supplier portal settings | CFG stores support email, optional phone/hours, and HTTPS Privacy, Terms and Accessibility destinations atomically. | Add **Supplier portal** after Reminders inside Procurement settings; complete, incomplete, invalid-link and saved variants. | Schema, service, role, validation, replay and desktop/narrow artboard tests. |
| G1-012 | Public projection | TPR/BDS consume only current allowlisted values, completeness and Version. | Render **Supplier support**, **Privacy and data use**, **Terms**, **Accessibility** consistently. | Projection allowlist and absence-of-audit/mutation tests. |
| G1-013 | Incomplete portal settings | Public Tender reading and existing Draft/receipt access remain; new Start and production Submit fail closed. | Use one plain supplier-information-unavailable state; do not hide the Tender or existing work. | Complete/incomplete transition and no-retroactive-mutation tests. |
| G1-014 | Portal-setting boundary | CFG does not own Tender content, notices, consent or submission enablement. | No Publish, Approve, Activate, content editor or production-submission switch in System Setup. | UI/API negative scan. |
| G1-015 | Template ownership | STD-TPL bundle excludes candidate/question/notice/portal operational records. | **STD Templates** remains a separate read-only admin module, not a System Setup section. | Bundle-schema and route-ownership scans. |
| G1-016 | Clarification versus bundle | Non-changing answer leaves bundle/definition digests unchanged; published change uses issued addendum identity rules. | STD detail need not show operational questions or deliveries. | Digest invariance and addendum-successor tests. |
| G1-017 | Generated bid UI | Bid tasks, controls, evidence, declarations, prices and mappings come from exact `PublishedBidDefinition v1`. | Five tasks: Tender documents/clarifications/addenda; company/declarations/security; requirements/evidence; price; review/submit. | Definition-to-control, accessibility, completeness and no-hidden-obligation tests. |
| G1-018 | Product boundary | Current release supports only straightforward IT Goods/Open Tender/single lot/KES/fixed price. | Unsupported method/product shows a controlled unavailable state, not a generic form. | Method/product allowlist and fail-closed tests. |
| G1-019 | Production switch | `production_bid_submission_enabled` is one server-side default-false deployment flag checked by the central availability service. | No visible switch; unavailable message confirms the Draft is safely saved. | False/true/health transition, client-forgery and no-local-override tests. |
| G1-020 | Operating profile | Submit/replacement require approved signing, trusted time, encryption, custody, backup/recovery and incident dependencies. | Readiness failure is direct and preserves all work. | Independent security, deadline, recovery and custody evidence before enablement. |
| G1-021 | Submit/receipt | Initial and replacement submission remain atomic and return a trusted immutable receipt; withdrawal preserves history. | Review page shows exact signed package; receipt clearly identifies submission and supersession state. | Transaction, retry, receipt, replacement and withdrawal tests. |
| G1-022 | Close/handoff | Deadline closes receipt and emits sealed package/custody evidence to future Bid Opening. | No Open bids, View prices or opening-register action in this release. | Exact-time, late-request, confidentiality and no-post-close-disclosure tests. |
| G1-023 | Accessibility/UX | Public and supplier tasks remain direct, role-appropriate and recoverable. | Desktop, 200% zoom and 390 px variants; keyboard, focus, error and saved-work evidence. | KT-STD v1.7 browser suite and representative supplier walkthrough. |
| G1-024 | Integrated fixture | One closed scenario covers published Tender → Start bid → question/answer → addendum notice → bid preparation → sealed submission. | All named states are reproducible without invented values. | Deterministic cross-module seed and signed end-to-end report. |

## 4. Streamlined implementation order

1. Implement CFG v0.16 `PublicPortalSettings`, owner commands, public projection and C05 UI.
2. Reconcile and rebuild the STD-TPL v0.9 release 1.1 bundle; rerun validator, issue a new manifest and obtain exact-manifest approval.
3. Implement TPR v0.10 clarification, candidate-audience, outbox and delivery-evidence records/services before changing portal screens.
4. Implement BDS v0.7 atomic Start bid, notice-contact selection and TPR clarification/notice consumers.
5. Generate the five-task Bid Workspace only from the exact effective Published Bid Definition; remove superseded hard-coded or addendum-only paths.
6. Implement central submission availability, signature/package/deposit/receipt paths and keep the production flag false.
7. Run changed-contract tests, then the deterministic integrated fixture through sealed handoff.
8. Enable production submission only after the separate operating-profile, security, custody and recovery evidence is approved.

Design and code may proceed in parallel only after the owner contracts in steps 1–3 are fixed. Design must use KT-STD-001 v1.7 §2 plus the complete static-design section of the owning module; it must not infer missing fields from another module or from raw JSON.

## 5. Release evidence checklist

| Evidence | Required result |
|---|---|
| Dependency scan | No active reference to TPR v0.9, BDS v0.6, CFG v0.15 or STD-TPL v0.8 remains outside historical change records. |
| API/route scan | No standalone arrangement, Declare interest, Follow Tender, BDS response store, per-Tender submission switch or System Setup template route. |
| Template release | Revised candidate passes all STD-TPL v0.9 gates; exact manifest and bundle digest are owner-approved. |
| Functional tests | Owner-boundary, deadline, idempotency, privacy, audience, outbox, projection and submission/custody tests pass. |
| Design evidence | All new/changed variants exist at desktop and 390 px and pass KT-STD keyboard, focus, error and 200% checks. |
| Seed evidence | Exact identities/times reproduce the public/vendor journey without reusing one event to prove opposite outcomes. |
| Operating profile | Signing, time, encryption, custody, recovery and incident controls are approved and independently verified before the production flag becomes true. |
| Future-boundary scan | No Bid Opening, evaluation, award, prequalification or unsupported method/product behavior is exposed as implemented. |

## 6. Planned future work — not part of this implementation

| Future body of work | Boundary preserved now |
|---|---|
| Bid Opening | Receives sealed packages and custody evidence only; owns opening/decryption, ceremony, register/minutes and lawful disclosure. |
| Evaluation and Award | Receives published evaluation mappings after lawful opening; owns evaluator conflicts, decisions, professional opinion, AO award, notices, standstill and debrief. |
| Supplier Management and prequalification | Separate lawful-purpose, data-minimised organisation evidence and method-specific list management; portal registration is not qualification. |
| Additional methods | RFQ, Restricted, Direct and RFP require separate method contracts and template releases. |
| Additional products | Works and other Services require separate curated schedules, response controls, pricing/BOQ treatment, mappings and artboards. |
| Contract Management and external integrations | Begin only after award/contract handoff and real external owner/interface contracts are defined. |

## 7. Approval effect

Approval of this register confirms the reconciled implementation sequence and boundary. It does not supersede the four controlling module documents, approve a template manifest, turn on production submission or approve any future module. Where this register and an owner document differ, the newer approved owner document controls and this register must be revised before implementation continues.
