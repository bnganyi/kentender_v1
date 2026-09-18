# BDS-CHG-001 — Supplier Portal and Electronic Bid Submission

| Control | Value |
|---|---|
| Document ID | BDS-CHG-001 |
| Version | **0.4** |
| Date | 18 September 2026 |
| Status | **Proposed for Project Owner review** |
| Supersedes | On approval, v0.3 in full |
| User-facing areas | **Tenders**, **My bids**, **Account** |
| Product | `IT-EQUIPMENT-OPEN-V1` — straightforward off-the-shelf IT equipment using the PPRA Goods Standard Tender Document |
| Starts from | One Published — open Tender and one authenticated supplier arrangement |
| Ends at | One current bid that is Draft, Submitted into the electronic tender box, Withdrawn before deadline, or closed without submission |
| Governing standard | KT-STD-001 v1.6 |
| Owner contracts | TPR-CHG-001 v0.8, STD-TPL-001 v0.6, LAW-REG-001 v1.1, AUTH-ADR-001 v1.7 and SEED-001 v1.3 |
| Implementation authority | None until Project Owner approval and satisfaction of the production gates in §§5.10 and 15 |
| v0.4 change scope | Closed six residual artboard-contract gaps: review/read timestamps, recovery-action mappings and receipt route, submitted-time display precision, narrow-width inventory coverage, verification-action naming, and the Review-and-submit completion rule; 6 acceptance criteria and 6 reimplementation rows |

**Controlling decision:** KenTender provides one simple supplier portal and one structured electronic bid for each supplier arrangement and Tender. A separately curated, code-owned STD release defines the product-specific response content and mappings; the exact Published Tender materialises them into one immutable bid definition. Bidders complete ordinary business tasks; they do not upload a filled Tender PDF, choose a template, interpret a schema or re-enter published requirements. A bid becomes Submitted only after server-authoritative validation, a valid licensed digital signature, immutable receipt evidence and successful deposit into the approved electronic tender box before the deadline.

## 1. Governing decision

The supplier journey is continuous:

1. Anyone may find and read a Published Tender without an account.
2. An authenticated supplier representative registers or selects one supplier arrangement and starts one bid.
3. The system creates the bid from the exact current published response definition.
4. For the current `IT-EQUIPMENT-OPEN-V1` product, the bidder completes five visible tasks:
   1. Tender documents and addenda;
   2. Company, declarations and tender security;
   3. Requirements and supporting evidence;
   4. Price; and
   5. Review and submit.
5. An authorised signatory signs and submits the exact validated bid before the deadline.
6. The system deposits the signed bid into the closed electronic tender box and issues an electronic receipt.
7. Before the deadline, the supplier may submit a replacement or withdraw the current bid. Every action receives a separate acknowledgement.
8. At the deadline, submission closes automatically. The Bid Opening owner receives custody evidence and sealed envelopes—not bid content exposed by this module.

The five-task composition is the approved Goods/IT product profile, not a universal layout imposed on Works or Services. A future product family requires its own curated STD release, code-owned composition profile, fixtures and acceptance contract. Shared portal controls may be reused, but an unsupported family cannot fall back to the Goods screen or a generic form builder.

**Start bid**, **Submit bid**, **Prepare replacement** and **Withdraw bid** are distinct actions. Saving a Draft, completing a section, validating a bid, signing a package, uploading evidence or receiving a client-side success message never means the bid was submitted.

## 2. Purpose, outcomes and scope

### 2.1 Required outcomes

The module shall:

- publish a clear public list of currently available Tenders;
- provide supplier organisation registration as an identity and access facility, not prequalification or eligibility approval;
- support a single supplier, joint venture or disclosed association where the published Tender permits it;
- create at most one active bid workspace for one supplier arrangement and Tender;
- consume the exact published response definition, declaration texts, price rows, evidence requirements and addenda without bidder re-entry;
- capture all substantive responses as structured data linked to stable published identifiers;
- keep the issued Tender document available as reference without using it as the response surface;
- reuse known organisation and evidence facts without changing the immutable copy bound into a submitted bid;
- give the bidder one clear next action and exact links to incomplete work;
- accept only evidence that passes the configured technical checks;
- require and verify the applicable licensed digital signature at submission;
- accept a bid only before the authoritative submission deadline;
- deposit the exact signed package into the approved electronic tender box without exposing its contents to Procuring Entity users before opening;
- issue verifiable electronic acknowledgements for submission, replacement and withdrawal;
- support lawful pre-deadline replacement and withdrawal without editing an earlier submission;
- preserve all submitted Versions, receipts, signature evidence, custody evidence and changes immutably; and
- hand sealed submission envelopes and custody evidence to Bid Opening without opening, evaluating or scoring them.

### 2.2 Included product boundary

- one Procuring Entity implicit from the site;
- public Tender discovery;
- authenticated supplier organisation account;
- one single-entity or permitted joint-venture supplier arrangement;
- Open Tender;
- one Published `IT-EQUIPMENT-OPEN-V1` Tender;
- Single lot;
- KES only;
- fixed-price treatment;
- structured supplier identity, declarations, tender security, requirement responses, warranty/support commitments, evidence and price schedule;
- one current submitted bid per arrangement and Tender;
- pre-deadline replacement and withdrawal;
- electronic acknowledgement and bidder receipt;
- closed electronic-tender-box deposit; and
- immutable handoff to Bid Opening.

### 2.3 Excluded

- supplier prequalification, grading, performance scoring or approval as eligible to win;
- automatic verification against KRA, AGPO, company, professional or licensing registries without an approved real interface;
- operational template, response-schema or validation-rule editing;
- PDF, spreadsheet or ZIP upload as the primary bid;
- bidder entry of a requirement, price line, quantity, unit, criterion, weight or evaluation rule absent from the published Tender;
- multiple lots, multiple currencies, alternative bids or product families outside the stated product;
- Procurement Officer access to Draft or sealed bid content;
- bid opening, preliminary examination, evaluation, clarification during evaluation, award or contract formation;
- generic supplier messaging unrelated to a governed Tender clarification;
- manual **Mark as submitted**, **Mark as signed**, **Open bid** or deadline override;
- a homemade certificate authority, digital-signature scheme, encryption scheme or tender-box substitute; and
- any claim that KenTender is an authorised replacement for or integration with a government e-procurement service until the operating model in §5.10 is approved and evidenced.

## 3. Ownership and dependency boundary

| Information or action | Owner | BDS treatment |
|---|---|---|
| Published Invitation, issued Tender, deadline, addenda, clarification answers and cancellation | Tenders | Consume an immutable bidder-safe projection. Never edit or independently reconstruct it. |
| Published response, evaluation and contract mappings | Curated code-owned STD release / Tenders | Materialise one immutable response definition and exact supported product profile tied to the published package; BDS consumes but does not redefine them. |
| Supplier organisation identity and user assignments | Supplier Account | Create and maintain through Account; self-declared facts are not eligibility approval. |
| External registry or certificate status | Authoritative external owner | Record only an authenticated result from an approved interface; otherwise retain supplier evidence without claiming external verification. |
| Bid preparation responses | Supplier arrangement | Accept only against published identifiers and applicable controls. |
| Evidence file storage and malware result | Platform evidence service | Store, scan, digest and retain; BDS binds exact accepted evidence into a bid Version. |
| Digital-signature certificate and signature verification | Licensed certifying agency / approved trust service | Verify through the approved facility. No checkbox substitutes for the required signature. |
| Tender-security physical original | Procurement-function receipt owner | Record receipt reference and time without opening the bid. Supplier sees the truthful receipt status. |
| Submission deadline and trusted time | Tenders / platform time service | Use the effective published deadline and trusted server time; the browser clock is never authority. |
| Electronic tender box and sealed custody | Approved custody service | Deposit the signed package and return authoritative acceptance/custody evidence. BDS cannot decrypt it. |
| Government e-procurement / State Portal transaction | Approved external system, where applicable | Use only the approved operating profile and real receipt semantics in §5.10. |
| Bid opening | Bid Opening | Receive sealed envelopes and custody history after automatic close; obtain no BDS command to read content. |
| Evaluation | Evaluation | Receive structured opened bid data and the published criterion mappings only after governed opening. |

Cross-owner writes use commands or versioned events. Supplier-facing reads use explicit allowlists. Internal identifiers, digests, schemas, rule keys, storage locations and security metadata never appear in portal HTML, URLs, accessibility text, downloads or errors.

## 4. Canonical domain model

### 4.1 SupplierOrganisation

| Field | Rule |
|---|---|
| `supplier_organisation_id` | Server-generated immutable identity. |
| `legal_name` | Required registered name; 3–200 characters. |
| `country` | Required governed country value. |
| `registration_number` | Required for a registered entity; exact self-declared identifier. |
| `tax_identifier` | Required when applicable to the organisation and Tender. |
| `registered_address` | Required structured postal/physical address. |
| `official_email`, `official_phone` | Required verified communication channels. |
| `account_status` | `Pending verification`, `Active` or `Suspended`; status controls access, not procurement eligibility. |
| `record_version` | Optimistic-concurrency token. |

Creating an Account sets `Pending verification`. Activating it requires successful verification of the configured communication channel. Activation proves only control of that channel and permission to act within the Account; it does not prove ownership, tax compliance, reservation entitlement, capacity, responsiveness or qualification.

### 4.2 SupplierUserAssignment

| Field | Rule |
|---|---|
| `assignment_id` | Immutable identity. |
| `supplier_organisation_id`, `user_id` | Exact organisation and authenticated person. |
| `responsibility` | `Supplier Representative` or `Authorised Signatory`. |
| `authority_evidence_id` | Required for Authorised Signatory; exact retained evidence. |
| `effective_from`, `effective_to` | Server-enforced authority window. |
| `assigned_by`, `assigned_at` | Immutable organisation-side assignment evidence. |

An Authorised Signatory may also prepare a bid. A Supplier Representative cannot submit, replace or withdraw a bid. Displayed role names never override the active assignment and authority window.

### 4.3 BidderArrangement

| Field | Rule |
|---|---|
| `bidder_arrangement_id` | Immutable identity, unique by Tender and arrangement. |
| `arrangement_type` | `Single organisation` or `Joint venture` when permitted by the published Tender. |
| `lead_organisation_id` | Required. |
| `member_organisation_ids` | Empty for single organisation; complete ordered set for a joint venture. |
| `joint_venture_name`, `agreement_evidence_id` | Required only for a joint venture. |
| `authorised_signatory_assignment_id` | Exact active signatory for submission. |
| `status` | `Active` or `Closed`. |

Joint-venture membership is frozen for a submitted Version. Changing it requires a replacement bid before the deadline; it never mutates an earlier submission.

### 4.4 PublishedBidDefinition

This is the immutable server-side contract generated with the Published Tender. It is not a runtime form builder, user-facing manifest or configurable Tender screen.

| Field | Rule |
|---|---|
| `bid_definition_id`, `definition_version` | Stable identity and sequential immutable version. |
| `tender_id`, `tender_version_id`, `publication_id` | Exact published source. |
| `effective_addendum_ids` | Exact ordered set incorporated into this definition. |
| `submission_deadline` | Effective published deadline. |
| `template_family`, `template_release_id`, `product_profile_id`, `package_digest` | Exact code-owned STD family, released template, approved composition/renderer profile and published package binding. |
| `sections` | Finite ordered task/group definitions supplied by the selected product profile; five visible tasks for the current Goods/IT release. |
| `response_rows` | Stable published identifiers, response types, applicability and evidence requirements. |
| `price_rows` | Stable items, quantities, units, currency and tax treatment. |
| `declaration_texts` | Exact locked official statements/forms to be confirmed and signed. |
| `evaluation_mappings`, `contract_mappings` | Stable downstream links; never bidder-editable or bidder-visible as technical metadata. |
| `supported_renderer_version` | Code-owned compatibility marker; an unsupported value blocks bid start/submission. |

The definition can require only content published in the Tender. It cannot introduce a hidden qualification, criterion, price line, declaration or evidence item.

#### 4.4.1 STD-to-bid ownership boundary

The STD release, Tender publication and Bidder Workspace perform different work. None may silently take over another layer.

| Layer | Owns | Must not do |
|---|---|---|
| Curated STD release | Official fixed text treatment; product-family composition; response, evidence, declaration, price and calculation definitions; validation; evaluation and contract mappings; compatible renderer profile | Read a live PDF at runtime, expose a schema editor or make Procurement Officers design the form |
| Tender Preparation / publication | Bind the released template to the exact authorised Requisition, approved Tender values and addenda; validate completeness; materialise and freeze the `PublishedBidDefinition` | Invent a response field, criterion, price row, evidence requirement or evaluation rule outside the released template and Published Tender |
| Bidder Workspace | Render the exact published definition through the supported code-owned profile; save typed responses by stable published identity; validate server-side | Reconstruct the form from the PDF, interpret arbitrary executable metadata or substitute a Goods layout for another product family |
| Opening, Evaluation and Contract owners | Consume the exact submitted response identities and published mappings after the applicable lawful handoff | Re-key, reinterpret or independently recreate controlled submission content |

The issued PDF is a human-readable output and reference. It is never parsed to create the response UI. The runtime source is the immutable, versioned definition produced from the reviewed STD release and exact Tender.

#### 4.4.2 Definition units

The materialised definition is declarative but not an unrestricted form-builder schema. It contains only reviewed units supported by the selected product profile.

| Unit | Required meaning |
|---|---|
| Product profile | Stable template-family/profile identity and compatible code-owned renderer Version |
| Task | Stable identity, ordinary-language title, purpose, order and completion rule |
| Group | Stable identity, heading, short guidance, order and approved composition treatment |
| Response row | Stable published identity, label, full requirement or question, response type, required/optional rule, applicability and source lineage |
| Options | Exact code/value, bidder-facing label and order for a controlled choice; the client cannot add an option |
| Evidence rule | Exact row/declaration proved, allowed file treatment and any required issue/expiry facts |
| Schedule or price row | Stable identity, published description, quantity/unit where applicable, permitted bidder inputs, calculation and rounding rule |
| Declaration | Exact locked text identity and Version plus the permitted confirmation response |
| Validation | Code-owned named rule and parameters from an allowlist; no executable expression or client-authored rule |
| Downstream mappings | Exact evaluation criterion/response destination and contract carry-forward destination, where applicable |

Every bidder-editable value must have a visible purpose and at least one defined validation, evidence, evaluation, calculation or contract consumer. Metadata retained only for storage, possible future use or implementation convenience does not create a bidder field.

#### 4.4.3 Response and composition allowlists

The shared runtime may implement a small allowlist of response controls: confirmation, yes/no, controlled single choice, short text, long text, integer/decimal/money, date, evidence reference and reviewed table/schedule input. Calculated values and published facts are read-only. A product profile composes those controls into usable tasks, groups, schedules and review summaries.

Complex product structures are code-owned compositions, not arbitrary nested JSON. For example, a Goods price schedule and a future Works Bill of Quantities may reuse decimal/money controls, but they are different approved schedule components with different hierarchy, calculations, validation and review presentation.

The renderer registry resolves the exact combination of template family, template release and `supported_renderer_version`. If the combination, response type, composition or rule is unknown, publication or **Start bid** fails with `BDS_DEFINITION_UNSUPPORTED`. There is no generic fallback, raw-schema screen or best-effort partial workspace.

#### 4.4.4 Publication materialisation

Before publication, the definition builder shall:

1. load the exact released STD bundle and its supported renderer profile;
2. bind the exact Tender Version, authorised Requisition rows, governed Tender values and effective addenda;
3. resolve applicability using only code-owned named rules and published facts;
4. assign and check stable identities for every task, group, response, evidence requirement, declaration and price/schedule row;
5. prove that every bidder-visible obligation is present in the Published Tender and that no hidden obligation has been introduced;
6. prove that every required response has its validation and applicable evaluation/contract mapping;
7. reconcile quantities, units, currency, tax and calculation sources across the human-readable Tender and structured definition;
8. verify that every referenced renderer component and rule is supported by the deployed release; and
9. freeze the exact definition, ordered addendum set, mappings and package identity atomically with publication.

Failure of any check blocks publication. It does not create an officer override, editable schema or bidder-visible incomplete form.

#### 4.4.5 Runtime rendering and saving

`GetBidWorkspace` returns a bidder-safe projection of the exact definition and current Draft values. The client chooses no template and infers no rule. It renders only the server-supplied tasks/groups through the resolved product profile and shared approved controls.

Each save submits values against stable published response identities. The server re-resolves the current Draft definition and enforces type, allowed option, applicability, multiplicity, calculation, evidence and record Version. Unknown, hidden, inapplicable or removed values are rejected. Client-side validation may improve feedback but never supplies authority.

Conditional behavior uses named, reviewed rules. When a controlling response changes, the server recalculates applicability. A newly required value becomes incomplete; a value that is no longer applicable is excluded from readiness and final packaging while its Draft audit history is retained. The interface explains the resulting task in ordinary language and never displays the rule key.

#### 4.4.6 Addenda and definition migration

An addendum that changes bid content creates a new immutable definition Version. Its release mapping must classify every earlier identity as unchanged, changed, removed or newly added.

- Unchanged responses may copy forward by exact stable identity.
- Changed responses may copy only through an explicit reviewed conversion; otherwise they require fresh bidder input.
- Removed responses remain in prior Draft/Version history but are absent from the new final package.
- New responses begin incomplete when required.
- Every changed or newly applicable response is shown in the affected-task review before submission.

Text similarity, row position, label matching or client guesses never migrate a response.

#### 4.4.7 Product-family extension

This release implements only `IT-EQUIPMENT-OPEN-V1`. It deliberately does not claim that Goods, Works and Services have the same bid composition.

| Product family | Illustrative product-owned content | Treatment in this document |
|---|---|---|
| Simple Goods / IT equipment | Goods and delivery schedule, related services, technical compliance, warranty/support, experience, evidence and supplier price schedule | Fully specified current product |
| Works | Qualification for similar works, personnel and equipment; method statement; work programme; site/HSE/quality submissions; drawings/specification treatment; hierarchical Bill of Quantities, provisional sums/dayworks and Works contract carry-forward | Not implemented here; requires a separately curated Works release, renderer profile, fixtures, artboards and acceptance tests |
| Consulting or non-consulting Services | Methodology, work plan, staffing/CVs, deliverables, technical and financial proposal treatment, applicable scoring and service contract carry-forward | Not implemented here; requires its own separately approved product release and profile |

Shared infrastructure may include identity, evidence, Draft saving, signature, deadline and custody services. Product-specific composition, validation, pricing and mappings remain with the applicable released STD. A future product must prove that its bidder journey is simple and complete in its own artboards; it cannot be admitted merely because its metadata fits the primitive field allowlist.

### 4.5 BidWorkspace

| Field | Rule |
|---|---|
| `bid_workspace_id`, `bid_reference` | Server-generated immutable identities. |
| `tender_id`, `bidder_arrangement_id` | Exact Tender and supplier arrangement; one active workspace at most. |
| `bid_definition_id` | Exact effective definition used by the Draft. |
| `status` | `Draft`, `Needs attention`, `Ready to submit`, `Submitted`, `Withdrawn`, `Closed without submission`. |
| `current_draft_version` | Positive integer; changes only through saved Draft responses or a successor Draft. |
| `current_submission_version_id` | Null until accepted; points to the current Submitted Version. |
| `created_by`, `created_at`, `last_saved_by`, `last_saved_at` | Server-derived. |
| `record_version` | Optimistic-concurrency token. |

Status is derived. The bidder cannot set it directly. A workspace may retain earlier immutable submission history while a replacement Draft is being prepared.

### 4.6 BidSectionResponse

| Field | Rule |
|---|---|
| `bid_workspace_id`, `draft_version`, `section_key` | Exact Draft and published section. |
| `response_rows` | Canonical values keyed by stable published response-row identity. |
| `status` | `Not started`, `In progress`, `Needs attention`, `Complete`, `Not applicable`. |
| `blocker_count`, `warning_count` | Server-derived from the exact definition and values. |
| `last_saved_by`, `last_saved_at` | Server-derived. |

Unknown sections, rows, fields, values or hidden conditional inputs are rejected. Completing a section is a reversible Draft fact, not a submission or evaluation decision.

### 4.7 BidEvidence

| Field | Rule |
|---|---|
| `bid_evidence_id` | Immutable identity. |
| `bid_workspace_id`, `draft_version` | Exact Draft use. |
| `evidence_requirement_id` | Exact published requirement the file proves. |
| `file_id`, `file_digest`, `media_type`, `size_bytes` | Server evidence facts. |
| `original_filename` | Sanitised display name; never a storage path. |
| `issued_by`, `reference`, `issued_on`, `expires_on` | Captured only where the published evidence rule requires them. |
| `scan_status` | `Pending`, `Accepted`, `Rejected`. |
| `source_evidence_id` | Optional Account-library source; submitted use still freezes an exact copy/digest. |
| `uploaded_by`, `uploaded_at` | Server-derived. |

A file is usable only when `scan_status = Accepted`. Technical acceptance does not prove legal validity, authenticity or criterion satisfaction; those remain evaluation questions against the published rule.

### 4.8 TenderSecurityResponse

| Field | Rule |
|---|---|
| `security_type` | One published permitted type. |
| `issuer`, `reference` | Required structured values. |
| `amount`, `currency` | Must match the published requirement. |
| `valid_until` | Required when the published form states a validity date. |
| `proof_evidence_id` | Required scanned/uploaded proof. |
| `physical_original_required` | Generated from the published Tender and applicable rule. |
| `physical_receipt_status` | `Not required`, `Not recorded`, `Recorded before deadline`, `Recorded after deadline`. |
| `physical_receipt_reference`, `physical_received_at` | Set only by the authorised procurement receipt owner. |

Absence of a recorded physical original does not prevent electronic submission. It remains a prominent warning and an opening/evaluation fact. The module never fabricates receipt or decides disqualification.

### 4.9 BidSubmissionVersion

| Field | Rule |
|---|---|
| `bid_submission_version_id`, `version_number` | Immutable identity and sequence per workspace. |
| `bid_workspace_id`, `bid_definition_id` | Exact workspace and effective definition. |
| `response_snapshot_digest`, `evidence_set_digest`, `package_digest` | Server-only immutable bindings. |
| `signed_by`, `signed_at` | Exact active Authorised Signatory and trusted instant. |
| `signature_certificate_ref`, `signature_verification_evidence` | Server-only evidence from the approved trust service. |
| `received_at`, `accepted_at` | Trusted instants; both must satisfy the effective deadline rule. |
| `status` | `Submitted`, `Superseded`, `Withdrawn`. |
| `predecessor_submission_version_id` | Required for a replacement. |
| `tender_box_envelope_id`, `receipt_id` | Exact custody and acknowledgement identities. |

No submitted Version is updated in place. A replacement creates a new Version and supersedes the former only when the replacement is successfully accepted into the tender box.

### 4.10 TenderBoxEnvelope and BidReceipt

| Record | Required facts |
|---|---|
| Tender-box envelope | Stable envelope identity; exact Tender and submission Version; signed-package binding; accepted custody instant; approved custody-service receipt; closed/open state. No response content or decrypt command is exposed to BDS. |
| Bid receipt | Human-readable receipt reference; Tender reference/title; supplier arrangement name; submission Version; received and accepted date/time with timezone; current acknowledgement status; submitter; replacement/withdrawal lineage where applicable. |

The bidder receipt omits internal digests, encryption details, schema identifiers, database IDs and storage locations. A receipt is generated only from authoritative accepted custody evidence.

### 4.11 SubmissionChange

| Field | Rule |
|---|---|
| `submission_change_id` | Immutable identity. |
| `bid_workspace_id`, `affected_submission_version_id` | Exact current submission. |
| `change_type` | `Replacement submitted` or `Withdrawal`. |
| `reason` | Optional for replacement; required 10–500 characters for withdrawal. |
| `requested_by`, `requested_at` | Active Authorised Signatory and trusted instant. |
| `acknowledgement_ref`, `acknowledged_at` | Authoritative electronic acknowledgement. |

## 5. Lifecycle and business rules

### 5.1 Lifecycle

| Current state | Action | Actor | Result |
|---|---|---|---|
| Published — open Tender | View Tender | Anyone | Read-only bidder-safe Tender; no record created. |
| No supplier Account | Register organisation | Authenticated person | Creates a Pending verification identity/access Account; no qualification claim and no Tender-bound arrangement. |
| Pending verification Account | Verify contact | Authenticated Account owner | Activates the Account after the configured communication challenge succeeds; proves channel control only. |
| Published — open; no workspace | Start bid | Supplier Representative / Authorised Signatory | Creates or returns one Draft from the current definition. |
| Draft / Needs attention | Save task | Supplier Representative / Authorised Signatory | Saves valid Draft values and refreshes derived task/readiness status. |
| Draft; new effective addendum | Refresh bid | Supplier Representative / Authorised Signatory | Creates a successor Draft definition, preserves unaffected values and marks affected work for review. |
| Ready to submit | Submit bid | Authorised Signatory | Revalidates, verifies licensed signature, freezes the Version, deposits it in the closed tender box and issues a receipt atomically. |
| Submitted; before deadline | Prepare replacement | Authorised Signatory | Creates an editable successor Draft; current submitted Version remains valid. |
| Replacement Draft ready; before deadline | Submit replacement | Authorised Signatory | Accepts a new Version and atomically marks the former Submitted Version Superseded. |
| Submitted; before deadline | Withdraw bid | Authorised Signatory | Records Withdrawal and authoritative acknowledgement; no current submitted bid remains. |
| Withdrawn; before deadline | Start replacement bid | Authorised Signatory | Creates a new Draft against the current definition. |
| Deadline reached | Close submission | System / tender-box owner | Rejects new submission/change commands; closes Drafts without submission; emits sealed-envelope inventory to Bid Opening. |

### 5.2 Registration and access rules

1. Tender discovery and the published Tender are public; starting or saving a bid requires authentication.
2. Registration captures identity and access facts only. The interface never says **Approved supplier**, **Qualified supplier** or **Verified eligible**.
3. The Account remains **Pending verification** until the configured email or phone challenge is completed. Verification proves control of that communication channel, not the underlying legal fact.
4. One user may belong to more than one supplier organisation only through separate explicit assignments; the active organisation is selected before entering My bids.
5. A suspended Account cannot start, edit, submit, replace or withdraw. Existing receipts remain available to the organisation through an authorised recovery route.
6. A supplier arrangement may be a joint venture only when permitted by the Published Tender. Every member and the lead/signatory are explicit.
7. An Authorised Signatory assignment requires organisation-side authority evidence and must be active at command time.

### 5.3 Current Goods/IT five-task response rules

These five tasks are generated by the released `IT-EQUIPMENT-OPEN-V1` product profile. They are fixed for this product and ordered by the published definition. They are not a universal task inventory for Works or Services.

| Visible task | Published content consumed | Bidder work |
|---|---|---|
| Tender documents and addenda | Invitation, issued Tender, issued addenda, answers affecting requirements | View and acknowledge the current set. |
| Company, declarations and tender security | Tenderer information forms, locked declarations, reservation/security rules | Confirm arrangement facts, complete structured forms, accept exact declarations and provide security response/evidence. |
| Requirements and supporting evidence | Goods, delivery, technical, warranty/support, experience and evidence rows | Give typed offers/responses and bind evidence to the exact published rows. |
| Price | Published goods/services price rows, currency and tax treatment | Enter permitted prices only; system calculates totals. |
| Review and submit | Complete response definition and current addenda | Resolve blockers, review the exact bid, sign and submit. |

The UI may group a large set of requirement rows for readability. Grouping never changes identity, applicability, requirement wording or completeness.

The **Review and submit** task is **Complete** when the server derives readiness against the exact current definition and finds no **Must fix** issue. A non-blocking **Review note** does not prevent Complete. Opening or viewing the review does not change this status, create a business fact or advance `last_saved_at`; a later Draft mutation recalculates it.

### 5.4 Addendum and clarification rules

1. The bidder sees all issued addenda and authoritative clarification answers tied to the Tender.
2. An addendum acknowledgement is required before submission.
3. A new addendum creates a new `PublishedBidDefinition`. It never overwrites the prior definition or a submitted Version.
4. A Draft moves to Needs attention until the bidder acknowledges the addendum and reviews every affected response.
5. Unaffected valid responses may be copied to the successor Draft through explicit stable mappings. No free-text or positional guess is permitted.
6. A current Submitted bid remains sealed. The bidder must submit a replacement before the revised deadline if the addendum requires changed responses.
7. A general Tender clarification uses the Tenders-owned inquiry contract. BDS authenticates the supplier arrangement and presents the response; it does not create an independent messaging store.
8. A response affecting a requirement is distributed without identifying the questioner and becomes part of the effective published information.

### 5.5 Evidence and tender-security rules

1. Every bid evidence item is requested by and linked to a visible published response or declaration.
2. Uploads are scanned before they can be bound into a submission. A rejected file is reported immediately and remains outside the tender-box package.
3. Allowed media types, size and any issue/expiry metadata come from the published definition and platform security policy.
4. Reusing Account evidence creates an exact bid-bound snapshot; replacing the Account copy never changes a submitted bid.
5. The signatory's final signature covers the structured responses, locked declaration texts and exact evidence set.
6. Where a physical original tender security is required, the portal displays the delivery instruction and deadline separately from electronic proof.
7. The procurement receipt owner records the exact physical receipt without seeing bid content. Absence or lateness remains truthful and passes to opening/evaluation; BDS does not pre-judge responsiveness.

### 5.6 Price rules

1. Quantity, unit, description, currency, schedule identity and applicable tax treatment are read-only published facts.
2. The bidder enters only permitted unit prices, tax values and other explicitly published financial response fields.
3. All arithmetic uses Decimal values and deterministic rounding from the published definition.
4. System-calculated subtotals and totals are read-only and are the only totals used by the Form of Tender projection.
5. No authorised estimate, Budget value, source allocation or internal reservation is visible.
6. The current product rejects another currency, alternative price, unrequested discount, additional line or spreadsheet import.

### 5.7 Validation, signature and submission rules

1. Readiness is derived from the exact current definition, responses, evidence, acknowledgements, arrangement, signatory authority and deadline.
2. **Must fix** prevents submission. **Review note** does not unless its underlying published rule says the value is mandatory.
3. The server reruns complete validation immediately before signing/deposit.
4. The final action and terminal confirmation control are both labelled **Submit bid**. The confirmation explains that the bid will be digitally signed, locked and placed in the electronic tender box; it will not be opened or evaluated.
5. Submission requires an active Authorised Signatory and a valid digital signature certificate from an approved licensed certifying agency.
6. The approved signature/trust service must bind the exact canonical package and return verifiable identity, certificate and signature evidence. A typed name, uploaded signature image, checkbox, password or staff override is not a substitute.
7. The complete signed request must reach the trusted server before the deadline. The browser clock and the time the user first opened the dialog are irrelevant.
8. Evidence is already accepted/scanned before final submission. The submission transaction performs no deferred large upload that could hide whether receipt occurred before the deadline.
9. `Submitted` and the receipt commit only after the approved tender-box service accepts the exact signed envelope. Partial success creates no Submitted state.
10. Replay with the same idempotency key returns the same receipt; a changed package under the same key is rejected.

### 5.8 Replacement and withdrawal rules

1. Electronic replacement and withdrawal are available up to, but not after, the effective submission deadline.
2. Preparing a replacement does not withdraw or alter the current submitted bid.
3. The replacement uses a bidder-authorised working copy without opening the tender-box envelope to the Procuring Entity. The custody design must keep the working copy inaccessible to PE users.
4. Only successful acceptance of the replacement marks the former Version Superseded.
5. Withdrawal is explicit, names the current submission Version, requires confirmation and produces an electronic acknowledgement with trusted date/time.
6. Withdrawal does not delete the envelope, receipt, signature or audit history; it changes consideration status under the governed custody contract.
7. A withdrawn bidder may submit a new replacement before deadline. The new accepted Version receives a new receipt and complete lineage.

### 5.9 Deadline, closing and custody rules

1. The effective deadline is the current published value, including an issued addendum, displayed with **EAT**.
2. Every submit, replace and withdraw command checks trusted server time inside the committing transaction.
3. The system accepts no bid received after the deadline and returns no misleading receipt.
4. At the deadline the electronic tender box closes automatically. An ordinary user, Administrator or System Manager cannot extend, reopen or backdate it.
5. Drafts that were never submitted are marked Closed without submission and never enter the opening inventory.
6. Before governed opening, Procuring Entity business users see no supplier identity, bid count, prices, responses, filenames or evidence from the box.
7. Technical operators may see service health and non-content envelope/custody identifiers only. They cannot decrypt, render, export or search bid content.
8. The Bid Opening handoff contains the closed-box identity, deadline evidence, sealed envelope identities, submission/withdrawal lineage and custody proofs. Opening credentials and ceremony are owned by Bid Opening.
9. Submitted bid content remains protected from unauthorised access throughout opening, evaluation and award. Downstream owners receive only the access their governed stage permits.

### 5.10 Production electronic-procurement operating profile

KenTender must not assume that a State Portal, government E-GPS, certifying agency or tender-box integration exists. Before production submission is enabled, the Project Owner must approve one exact operating profile that states:

- whether KenTender is the authorised e-procurement system, an integrated client, or a preparatory surface handing off to another authoritative service;
- the applicable current legal/directional basis and institutional approval;
- the authoritative system of receipt and which receipt is shown to the bidder;
- the real government/State Portal interface and acknowledgement semantics, where applicable;
- the licensed certifying agencies/trust chain and certificate-validation mechanism;
- the approved tender-box custody service, encryption/key custody and three-credential opening compatibility;
- how any currently applicable bidder-controlled encryption/password direction interoperates with structured responses, malware screening and the governed opening ceremony; the portal must not solicit or accept an unsupported password-protected package;
- trusted-time source, deadline and timezone treatment;
- idempotency, timeout, uncertain-result, reconciliation and disaster-recovery behavior;
- supplier support and incident ownership; and
- production contract, security, penetration, recovery and statutory acceptance evidence.

If another system is authoritative, KenTender may show **Submission being confirmed** only with truthful correlation evidence and may show **Submitted** only after the authoritative receipt is obtained. No blind retry, staff success flag, duplicate submission path or internal-only receipt is permitted. Without an approved profile, Draft preparation may operate in a labelled test environment, but production **Submit bid** remains unavailable.

### 5.11 Core invariants

1. One Tender and supplier arrangement have at most one active bid workspace and one current Submitted Version.
2. Public Tender reads and page opens create no supplier, workspace, response, evidence or audit business fact.
3. Every response and evidence item traces to a stable published identifier.
4. A Draft never changes published Tender content, evaluation criteria or contract mappings.
5. Registration, Account activation, section completion, validation, upload, signature preparation and tender-box deposit are different facts.
6. No Submitted state or bidder receipt exists without authoritative accepted custody evidence.
7. No late command can submit, supersede or withdraw a bid.
8. Submitted, superseded and withdrawn Versions are immutable and retained.
9. An addendum never rewrites a Draft or submitted Version silently.
10. No Procuring Entity user can read bid content before governed opening.
11. A technical operator cannot exercise supplier or opening authority.
12. Bid Opening and Evaluation receive the exact published mappings; they cannot introduce a criterion absent from the published Tender.

## 6. Responsibilities and permissions

| Responsibility | Scope | Exact work |
|---|---|---|
| Public visitor | Public published Tenders | Find and read published Tender information and documents; no bid or account action. |
| Supplier Representative | Assigned supplier organisation | Maintain permitted Account facts; start and prepare Drafts; upload evidence; view organisation receipts. Cannot submit, replace or withdraw. |
| Authorised Signatory | Assigned supplier organisation and active authority window | All Supplier Representative work plus digitally sign, submit, replace and withdraw the organisation's bid. |
| Procurement receipt owner | Site-wide procurement-function assignment | Record receipt of a required physical tender-security original; cannot read Draft or sealed bid content. |
| Auditor | Approved oversight scope | Read registration, command, receipt, signature and custody metadata under the legal access rule; no pre-opening bid content by default and no mutation. |
| Authorised technical operator | Explicit custody/support assignment | Monitor non-content service health and approved recovery evidence; cannot view responses, sign, submit, withdraw, open or evaluate. |
| Administrator / System Manager | Technical read under KT-STD-001 §3A.6 | Configuration/health metadata only for sealed bids; no business authority and no content access before governed opening. |
| System | Internal | Derive readiness, validate, bind evidence, enforce deadline, obtain approved signature/custody receipts, close the box and publish the opening handoff. |

Responsibility checks use active immutable assignments and supplier arrangement identity. A user cannot switch displayed organisation or responsibility to gain access to another organisation's Draft, evidence or receipt.

## 7. Service and command contracts

### 7.1 Public and supplier reads

| Service | Required result |
|---|---|
| `GetAvailableTenders` | Public bidder-safe list of open Tenders with server-derived availability and no internal package data. |
| `GetPublishedTenderForBidder` | Current Invitation/Tender, dates, documents, addenda, clarifications and permitted public actions. |
| `GetSupplierAccount` | Exact organisation, assignments and truthful self-declared/communication status. |
| `GetMyBids` | Role-safe organisation bid list with status, deadline and one next action. |
| `GetBidWorkspace` | Current product-profile task checklist—five tasks for `IT-EQUIPMENT-OPEN-V1`—with current definition, issues and permitted actions. |
| `GetBidTask` | Exact published content, saved Draft response, evidence and validation for one task. |
| `GetBidReview` | Complete result-first review of current Draft with exact blockers/notes and immutable source links. |
| `GetSubmissionReceipt` | Human-readable authoritative receipt and current submission lineage; no internal security metadata. |

Reads create no organisation, assignment, workspace, acknowledgement, evidence, signature, submission, receipt or audit business event.

### 7.2 Account and preparation commands

| Command | Minimum effect |
|---|---|
| `RegisterSupplierOrganisation` | Validate identity/access fields; create or return one Pending verification organisation Account; send no approval or qualification claim. |
| `SendAccountVerification` | Send or resend a bounded challenge to the configured email or phone without activating the Account. |
| `VerifyAccountCommunication` | Validate the current challenge and activate the Account once; record channel, actor and trusted time without claiming verification of legal facts. |
| `UpdateSupplierOrganisation` | Update only permitted self-declared Account fields with version check. |
| `AssignSupplierRepresentative` | Create an active representative assignment under organisation authority. |
| `AssignAuthorisedSignatory` | Require authority evidence and effective window; create immutable assignment. |
| `CreateBidderArrangement` | Create or return one permitted single/JV arrangement for the Tender. |
| `StartBid` | Recheck Tender open state, Active Account, Tender-bound arrangement, definition compatibility and uniqueness; create or return one Draft. |
| `SaveBidTask` | Accept only applicable published response values for one task; derive result and next action. |
| `UploadBidEvidence` | Scan and store evidence; bind only after Accepted result. |
| `LinkAccountEvidenceToBid` | Create an exact bid-bound evidence snapshot against one published requirement. |
| `AcknowledgeTenderDocument` | Record exact current Tender/addendum identity and actor/time. |
| `RefreshBidForAddendum` | Create successor Draft definition, map unaffected stable responses and mark affected work. |

### 7.3 Security, submission and change commands

| Command | Minimum effect |
|---|---|
| `RecordPhysicalTenderSecurityReceipt` | Procurement receipt owner records exact security, receipt reference and trusted time without bid-content access. |
| `ValidateBid` | Rebuild full current result without mutating lifecycle state. |
| `PrepareBidSignature` | Recheck readiness/authority/deadline and return an approved trust-service signing request for the exact canonical package. |
| `SubmitBid` | Verify returned signature, recheck all facts, deposit exact package into approved tender box and atomically commit Submitted Version and receipt. |
| `PrepareReplacementBid` | Create successor Draft while leaving the current submitted Version effective. |
| `SubmitReplacementBid` | Perform full sign/deposit; atomically accept new Version and supersede former only on success. |
| `WithdrawBid` | Before deadline, require active signatory and confirmation; record withdrawal and authoritative acknowledgement without deleting history. |
| `CloseBidSubmission` | At deadline, close box/workspaces once and emit immutable Bid Opening handoff. |

Every mutation accepts an expected record version and idempotency key. The server derives user, organisation, responsibility, definition, deadline, totals, status and permitted actions.

### 7.4 STD publication and runtime services

These are server-internal or owner-to-owner contracts. They are never bidder-facing actions.

| Service | Owner and required result |
|---|---|
| `BuildPublishedBidDefinition` | Tenders/template runtime takes the exact released template, Tender Version, authorised source rows and effective addenda; performs every §4.4.4 check; returns one deterministic immutable definition or blocks publication atomically |
| `ResolveBidProductProfile` | Code-owned registry resolves exact template family/release/renderer Version to one supported composition; unknown or mismatched input fails closed with no fallback |
| `ValidateBidResponses` | BDS validates one task or the whole Draft against the exact definition using the same named rules used by readiness and final submission |
| `MapBidDefinitionAddendum` | Tenders/template runtime produces the explicit unchanged/changed/removed/new identity map required by §4.4.6; heuristic matching is prohibited |
| `BuildCanonicalBidPackage` | BDS orders the exact definition, current typed responses, locked declarations and accepted evidence into the one package signed and deposited; no client-supplied schema or total is trusted |

The first two services are release/publication dependencies, not runtime template administration. Their inputs come only from installed code-owned releases and governed Tender data. They create no Desk configuration surface.

## 8. Error contract

| Code | User-visible message and treatment |
|---|---|
| `BDS_TENDER_NOT_FOUND` | **Tender not found.** Return to Tenders. |
| `BDS_TENDER_NOT_OPEN` | **This Tender is not accepting bids.** Show the truthful published/cancelled/closed status. |
| `BDS_SIGN_IN_REQUIRED` | **Sign in to start or continue a bid.** Preserve the safe return destination. |
| `BDS_ACCOUNT_REQUIRED` | **Set up your supplier account before starting a bid.** Link Account. |
| `BDS_ACCOUNT_SUSPENDED` | **This supplier account cannot submit bids.** Show the configured support route. |
| `BDS_ARRANGEMENT_INVALID` | **Check the supplier or joint-venture information.** Link exact field/member. |
| `BDS_RESPONSIBILITY_REQUIRED` | **An Authorised Signatory must complete this action.** |
| `BDS_DEFINITION_UNSUPPORTED` | **This bid format is not available.** Do not create a partial workspace; contact support. |
| `BDS_ADDENDUM_REVIEW_REQUIRED` | **Review the latest addendum and the affected bid responses.** Link each affected task. |
| `BDS_FIELD_INVALID` | **Check the highlighted value.** Bind each exact field error. |
| `BDS_UNKNOWN_RESPONSE` | **This response is not part of the published Tender.** Reject without saving. |
| `BDS_EVIDENCE_REQUIRED` | **Add the required supporting evidence.** Link the published requirement. |
| `BDS_EVIDENCE_REJECTED` | **This file could not be accepted.** Show type/size/scan reason without internal details. |
| `BDS_SECURITY_PROOF_REQUIRED` | **Add the required tender-security proof.** |
| `BDS_SECURITY_ORIGINAL_OUTSTANDING` | **The physical tender-security original has not been recorded as received.** This warns but does not falsely block electronic receipt. |
| `BDS_MUST_FIX` | **Fix the listed items before submitting.** Link every issue. |
| `BDS_STALE_VERSION` | **Another person changed this bid. Reload before continuing.** |
| `BDS_SIGNATORY_REQUIRED` | **Only an active Authorised Signatory can submit this bid.** |
| `BDS_SIGNATURE_UNAVAILABLE` | **Digital signing is not available.** Keep the bid Draft and show the approved support route. |
| `BDS_SIGNATURE_INVALID` | **The digital signature could not be verified for this bid.** Nothing is submitted. |
| `BDS_SUBMISSION_SERVICE_UNAVAILABLE` | **Electronic submission is temporarily unavailable. Your bid remains saved.** Never imply receipt. |
| `BDS_SUBMISSION_UNCERTAIN` | **Submission confirmation is still pending. Do not submit again.** Show correlation/support route; no receipt or success claim. |
| `BDS_DEADLINE_PASSED` | **The submission deadline has passed. This bid was not submitted.** Show authoritative deadline/time. |
| `BDS_ALREADY_SUBMITTED` | **This bid Version has already been submitted.** Show its receipt. |
| `BDS_REPLACEMENT_CONFLICT` | **A newer submitted bid already exists.** Show current receipt; do not change either Version. |
| `BDS_WITHDRAWAL_BLOCKED` | **This bid can no longer be withdrawn because the deadline has passed.** |
| `BDS_IDEMPOTENCY_CONFLICT` | **This request was already used with different information. Stop and refresh.** |

Record-existence masking prevents cross-organisation disclosure. A public not-found response never confirms whether another supplier has a Draft or submission.

## 9. UI architecture, navigation and routes

The supplier experience is a Website portal, not Frappe Desk. It uses the KenTender visual tokens and accessibility rules but does not render officer modules, Desk navigation or internal metadata.

| Area | Route | Purpose |
|---|---|---|
| Tenders | `/tenders` | Public list of Tenders currently available to suppliers. |
| Tender overview | `/tenders/{tender_reference}` | Published Tender, dates, notices, documents and Start/Continue action. |
| My bids | `/my-bids` | Signed-in organisation's Draft, Submitted and Withdrawn bids. |
| Account | `/account` | Supplier organisation, user assignments and reusable evidence. |
| Receipt history | `/account/receipts` | Authorised recovery view of the organisation's existing submission and withdrawal receipts, including when the Account is Suspended; no preparation or change action. |
| Bid workspace | `/tenders/{tender_reference}/bid` | Five-task checklist and next action. |
| Bid task | `/tenders/{tender_reference}/bid/{task_key}` | One of documents, company, requirements or price. |
| Review | `/tenders/{tender_reference}/bid/review` | Complete current Draft and issues. |
| Submit | `/tenders/{tender_reference}/bid/submit` | Exact final confirmation and digital-signature step. |
| Receipt | `/tenders/{tender_reference}/bid/receipt/{receipt_reference}` | Authoritative supplier receipt. |
| Security receipts | `/desk/tender-security-receipts` | Procurement receipt-owner queue; no bid-content access. |

Public header links are **Tenders**, **My bids** and **Account**. Signed-out selection of My bids or Account goes to sign-in with a safe return route. Inside a bid, use the page's five-task checklist and Back links; do not add a second permanent sidebar.

## 10. Static design contract

Supply **KT-STD-001 v1.6 §2 plus this section only** to the design tool. Apply KT-STD-001 §2.2, §2.6–2.8. Supplier artboards use the Website portal shell below; BDS-DES-15 alone uses the internal Desk shell below. Fixture metadata remains outside the artboard. Every variant is an isolated reset unless the primary lifecycle explicitly links it.

This design contract renders only the `IT-EQUIPMENT-OPEN-V1` Goods profile. It is not the universal appearance of every future STD family. A Works or Services release must provide its own complete self-contained artboards using the same plain-language and usability rules; a designer must not extrapolate such screens from these Goods fixtures.

### 10.1 Shared shells and fixture pack

#### Supplier Website shell

- 1440 × 1024 px desktop artboard; 1200 px maximum-width centred content column; warm-white background.
- Provide a 390 × 844 px narrow-width derivative for every supplier artboard and dialog. At narrow width, grids stack, table rows become labelled cards, actions remain adjacent to their subject and no value or action is omitted or hidden by horizontal scrolling.
- Compact white public header above the content: **KenTender** at left; **Tenders**, **My bids**, **Account** at right in that order. Show the selected item with text and underline, not a large tab card.
- Below the header use 32 px vertical page padding, 24 px after each page header and 16 px between sections.
- Dialogs are 520 px over a dimmed parent artboard.
- No Frappe Desk header, breadcrumb, officer module navigation, custom permanent sidebar, charts, hero illustration or promotional content.
- On bid pages, place **Back to bid** above the page title. The bid workspace itself contains the five-task table; task pages do not repeat a large progress stepper.

#### Internal Desk shell — BDS-DES-15 only

- Use the established compact KenTender Desk content area for `/desk/tender-security-receipts`, with the authenticated officer header and breadcrumb **Tender-security receipts**.
- Do not show the supplier Website header, **Tenders**, **My bids**, **Account**, supplier organisation switcher or any supplier bid-content navigation.
- Apply the same spacing, keyboard, focus, table-to-card and narrow-width rules. BDS-DES-15 is the only artboard in this section that uses this shell.

#### Tender

| Fact | Exact visible value |
|---|---|
| Procuring Entity | Ministry of Health |
| Tender | TND-MOH-2027-033 |
| Title | Supply and delivery of business laptops |
| Method | Open Tender |
| Reservation | Youth |
| Quantity | 250 Each |
| Currency | KES |
| Published | 15 May 2027, 08:00 EAT |
| Clarification deadline | 27 May 2027, 17:00 EAT |
| Original submission deadline | 5 Jun 2027, 11:00 EAT |
| Current submission deadline | 12 Jun 2027, 11:00 EAT |
| Latest delivery | 30 Sep 2027 |
| Tender validity | 120 days |
| Tender security | KES 500,000.00; proof uploaded and physical original required before deadline |
| Addendum | ADD-MOH-2027-033-001 · Delivery point clarified · Issued 31 May 2027, 09:00 EAT |
| Current delivery location | Ministry of Health Headquarters, Afya House, 3rd Floor Procurement Stores, Nairobi |

Published documents: **Invitation to Tender.pdf** and **Complete Tender.pdf**. The addendum document is **ADD-MOH-2027-033-001.pdf**.

Published clarification: question **Do suppliers who downloaded the original Tender need to change the offered delivery price?** Answer **No. The addendum clarifies the internal delivery point within Afya House and does not change the delivery city, quantity or pricing basis.** Answered 1 Jun 2027, 11:00 EAT.

#### Supplier organisation and users

| Fact | Exact value |
|---|---|
| Legal name | Afya Digital Supplies Limited |
| Country | Kenya |
| Registration number | PVT-9X7K2M |
| KRA PIN | P051234567X |
| Registered address | Westlands Business Park, Waiyaki Way, Nairobi |
| Official email | tenders@afyadigital.example |
| Official phone | +254 709 555 014 |
| Reservation evidence | AGPO Youth Certificate AGPO-Y-2026-04172; expires 30 Jun 2027 |
| Supplier Representative | David Ouma · Bid Coordinator |
| Authorised Signatory | Mary Wanjiku · Managing Director |
| Signatory authority | Board authority dated 5 May 2027; evidence `mary-wanjiku-signing-authority.pdf` |

The Account is Active. Values are self-declared or supplier-provided unless a named external verification result is explicitly stated. Do not display **Verified supplier** or **Approved supplier**.

#### Bid

| Fact | Exact value |
|---|---|
| Bid | BID-MOH-2027-033-001 |
| Arrangement | Single organisation |
| Draft started | David Ouma · 19 May 2027, 09:20 EAT |
| Addendum acknowledged | David Ouma · 1 Jun 2027, 12:10 EAT |
| Current Draft | Version 7 |
| Final Draft saved | David Ouma · 10 Jun 2027, 13:50 EAT |
| Signatory certificate | Ready; Mary Wanjiku; fixture certificate valid to 31 Dec 2027 |
| Submitted by | Mary Wanjiku |
| Received by tender-box service | 10 Jun 2027, 14:31:58 EAT |
| Accepted into tender box | 10 Jun 2027, 14:32:01 EAT |
| Receipt | RCPT-MOH-2027-033-001 |

The fixture certificate and tender-box acknowledgements are labelled synthetic test evidence in the seed. The visible artboards show ordinary **Digital certificate ready** and **Submitted** states; they never imply that test evidence is production accreditation.

#### Company forms and declarations

| Item | Exact displayed result |
|---|---|
| Tenderer information | Complete |
| Form of Tender | Confirmed |
| Independent tender determination | Confirmed |
| Self-declaration — not debarred | Confirmed |
| Self-declaration — no corrupt or fraudulent practice | Confirmed |
| Code of ethics commitment | Confirmed |
| Youth reservation declaration | Complete |

Each declaration's **View declaration** disclosure contains the locked published text. The table never exposes template keys, form IDs or schema names.

#### Tender security

| Fact | Exact value |
|---|---|
| Type | Bank guarantee |
| Issuer | Kenya Commercial Bank PLC |
| Reference | KCB/TG/2027/8841 |
| Amount | KES 500,000.00 |
| Valid until | 15 Nov 2027 |
| Uploaded proof | `tender-security-kcb-8841.pdf` |
| Physical original | Recorded as received |
| Receipt | MOH-SEC-2027-033-017 · 10 Jun 2027, 10:00 EAT |

#### Offered goods and technical responses

| Published requirement | Required value | Offered response | Evidence |
|---|---|---|---|
| Electrical compatibility | Suitable for Kenyan mains supply | Yes — 240 V, 50 Hz adaptor supplied | Product datasheet |
| New and unused equipment | Yes | Yes — all units new and unused | Manufacturer authorisation |
| Memory | Minimum 16 GB | 16 GB | Product datasheet |
| Storage capacity | Minimum 512 GB | 512 GB | Product datasheet |
| Storage type | NVMe SSD | NVMe SSD | Product datasheet |
| Display size | Minimum 14.0 inches | 14.0 inches | Product datasheet |
| Battery runtime | Minimum 8 hours | 10 hours | Product datasheet |
| Processor requirement | 64-bit business-class; minimum 10 cores or equivalent | 64-bit business-class; 12 cores | Product datasheet |
| Operating-system compatibility | Approved organisational Windows environment | Windows 11 Pro compatible | Product datasheet |
| Network connectivity | Wi-Fi 6 and Bluetooth 5 or later | Wi-Fi 6E and Bluetooth 5.3 | Product datasheet |
| Required ports | USB-C ×2; USB-A ×2; HDMI ×1 | USB-C ×2; USB-A ×2; HDMI ×1 | Product datasheet |

Offered model: **ApexBook Pro 14**. Delivery commitment: **15 Sep 2027** to the current published delivery location.

#### Warranty, support and experience

| Published requirement | Offered response | Evidence |
|---|---|---|
| Minimum warranty 36 months | 36 months | Warranty and support commitment |
| On-site support required | Yes | Warranty and support commitment |
| Maximum support response 8 hours | 4 hours | Warranty and support commitment |
| Manufacturer support required | Yes | Manufacturer authorisation |
| Service location within Kenya | Nairobi service centre | Kenya service-centre details |
| Escalation and warranty contacts | Supplied | Kenya service-centre details |

Comparable contracts:

| Customer | Supply | Completion date | Evidence |
|---|---|---|---|
| Kenyatta National Hospital | 180 business laptops | 30 Nov 2026 | `knh-laptop-supply-2026.pdf` |
| Kenya Medical Training College | 220 business laptops | 15 Mar 2027 | `kmtc-laptop-supply-2027.pdf` |

#### Evidence set

| Evidence item | File | Status |
|---|---|---|
| Certificate of incorporation | `certificate-of-incorporation.pdf` | Accepted |
| Tax compliance certificate | `kra-tax-compliance-2027.pdf` | Accepted |
| Youth reservation evidence | `agpo-youth-2026-04172.pdf` | Accepted |
| Manufacturer authorisation | `manufacturer-authorisation-apexbook.pdf` | Accepted |
| Product datasheet | `apexbook-pro-14-datasheet.pdf` | Accepted |
| Warranty and support commitment | `warranty-support-commitment.pdf` | Accepted |
| Kenya service-centre details | `kenya-service-centre-details.pdf` | Accepted |
| Comparable contract 1 | `knh-laptop-supply-2026.pdf` | Accepted |
| Comparable contract 2 | `kmtc-laptop-supply-2027.pdf` | Accepted |
| Tender-security proof | `tender-security-kcb-8841.pdf` | Accepted |

#### Price

| Item | Quantity | Unit | Unit price excluding tax | Line amount before tax |
|---|---:|---|---:|---:|
| Business laptops | 250 | Each | KES 160,000.00 | KES 40,000,000.00 |

Subtotal excluding tax is **KES 40,000,000.00**. Tax is **KES 6,400,000.00**. Bid total is **KES 46,400,000.00**. These fixture values test arithmetic; they are not a tax-rate rule or a disclosed internal estimate.

#### Isolated variants

| Variant | Exact facts |
|---|---|
| Signed out | Public visitor opens Tender; no supplier or bid identity exists. |
| New Account | Mary has no supplier organisation; registration form is empty. |
| Organisation incomplete | Official phone is empty; Account task shows one Must fix. |
| Account pending verification | Organisation details are saved; verification challenge sent to `tenders@afyadigital.example`; Account cannot start a bid until the challenge succeeds. |
| Account suspended | Afya Digital Supplies Limited is Suspended; preparation and change commands are unavailable; existing receipts remain reachable through the authorised recovery route. |
| Cross-organisation denial | Peter Mwangi, with no assignment to Afya Digital Supplies Limited, requests `BID-MOH-2027-033-001` at 10 Jun 2027, 14:20 EAT; the response masks record existence and exposes no Tender-specific bid fact. |
| Needs attention | Product datasheet is Rejected after malware scan; Requirements task has one Must fix. |
| Addendum review | Addendum is issued; old delivery response remains saved but acknowledgement/review is outstanding. |
| Security outstanding | Electronic proof Accepted; physical original status Not recorded; submission remains allowed with a prominent warning. |
| Signature unavailable | Bid is otherwise Ready; no approved certificate is available for Mary. |
| Submission service unavailable | Draft is Ready; approved tender-box service cannot return acceptance. |
| Custody definitely failed | Mary submits at 10 Jun 2027, 14:30 EAT; test tender box returns definitive rejection `TBX-REJECT-033-01`; Draft remains Ready to submit and no receipt or envelope is created. |
| Custody uncertain | Mary submits at 10 Jun 2027, 14:30 EAT; correlation `COR-BDS-2027-033-01` remains pending; support reference `SUP-BDS-2027-033-01`; no retry, receipt or Submitted state is available. |
| Late submission | Complete signed request reaches the trusted server at 12 Jun 2027, 11:00:01 EAT; it is rejected and creates no envelope or receipt. |
| Submitted receipt after deadline | Version 1 was accepted on 10 Jun 2027, 14:32:01 EAT; trusted current time is 12 Jun 2027, 11:00:01 EAT; the receipt remains available but replacement and withdrawal are closed. |
| Idempotency conflict | Correlation `COR-BDS-2027-033-02` reuses the Version-7 idempotency key with different price information; original attempt is unchanged and refresh is required. |
| Replacement conflict | Replacement Version 3 is attempted after Version 2 is already current with receipt `RCPT-MOH-2027-033-002`; neither Version changes. |
| Replacement | Primary Submitted Version 1 remains current while replacement Draft Version 2 is prepared; Version 2 is accepted on 11 Jun 2027, 09:15 EAT with receipt `RCPT-MOH-2027-033-002`. |
| Withdrawal | Separate Tender `TND-MOH-2027-041`; bid `BID-MOH-2027-041-001`; withdrawn by Mary on 10 Jun 2027, 15:00 EAT; acknowledgement `WD-MOH-2027-041-001`. |
| Cancelled Tender | `TND-MOH-2027-034`; public page shows Cancelled and no Start/Continue action. |

### 10.2 BDS-DES-01 — Available Tenders

**Purpose.** Help a supplier find a current Tender and open its complete public information.

**Fixture context — outside the artboard.** Signed-out public visitor; 20 May 2027, 10:00 EAT; public list.

**Page header.** Title **Available Tenders**. Description **Find current opportunities and review the full Tender before deciding to bid.** No header action.

**Composition, top to bottom.**

1. Place a compact filter row below the header: Search title or reference; Method **All methods**; Reservation **All categories**; Closing **Open Tenders**; **Clear filters**.
2. Place one result table beneath the filters with columns Tender; Procuring Entity; Method; Reservation; Submission deadline; Action.
3. Render the fixture row: title on the first line and Tender reference beneath in muted text; Ministry of Health; Open Tender; Youth; 12 Jun 2027, 11:00 EAT; **View Tender**.
4. Beneath the table show **1 available Tender**. Do not show Start bid, account status, internal value, schema family or document counts.

**Variant BDS-DES-01-EMPTY.** Keep header/filters; table area says **No Tenders match these filters.** Show **Clear filters** only.

**Visual check.** The public list is calm, searchable and directs every supplier to the complete Tender before any bid action.

### 10.3 BDS-DES-02 — Published Tender overview

**Purpose.** Let the supplier understand the opportunity, current notices and deadline before starting or continuing a bid.

**Fixture context — outside the artboard.** David Ouma; Supplier Representative; Afya Digital Supplies Limited; no workspace; 20 May 2027, 10:05 EAT.

**Page header.** Title **Supply and delivery of business laptops**. Place `TND-MOH-2027-033` beneath it. Description **Ministry of Health · Open Tender · Youth reservation.** Place primary **Start bid** at the right of the title.

**Composition, top to bottom.**

1. Deadline strip: **Submissions close 12 Jun 2027, 11:00 EAT**; Clarifications closed 27 May 2027, 17:00 EAT; Published 15 May 2027, 08:00 EAT.
2. Summary card with separately labelled Quantity **250 Each**; Delivery location; Latest delivery; Currency **KES**; Tender security **KES 500,000.00**; Bid validity **120 days**.
3. Section **Tender documents** with rows Invitation to Tender and Complete Tender; each has Published 15 May 2027 and **View** / **Download**.
4. Section **Addenda and clarification answers**. Show ADD-MOH-2027-033-001 with issued date, summary **Delivery point clarified**, current deadline and **View**. Beneath it show the shared clarification question/answer with answered date.
5. Section **Before you start** with three short bullets: sign in; use one supplier organisation or permitted joint venture; an Authorised Signatory and valid digital certificate are needed only when submitting.

**Variants.**

- **BDS-DES-02-SIGNED-OUT:** replace Start bid with **Sign in to start bid**.
- **BDS-DES-02-JV-START:** after an active Account user selects Start bid and the Tender permits joint ventures, open a short step titled **Who is bidding?** Choices are **My organisation** and **A joint venture**. For a joint venture show Joint-venture name; Lead organisation; member organisations; agreement evidence; Authorised Signatory. Primary **Create arrangement and start bid**. The arrangement is bound to this Tender and no workspace is created until validation succeeds.
- **BDS-DES-02-DRAFT:** primary **Continue bid**; secondary status **Draft · 3 of 5 tasks complete**.
- **BDS-DES-02-SUBMITTED:** primary **View receipt**; status **Submitted 10 Jun 2027, 14:32 EAT**.
- **BDS-DES-02-CANCELLED:** use Cancelled Tender fixture; red status **Cancelled**; no bid action; show cancellation notice action **View notice**.

**Visual check.** The decision to bid is based on current Tender facts and notices; account or system internals do not compete with the opportunity.

### 10.4 BDS-DES-03 — Register supplier organisation

**Purpose.** Create the minimum organisation Account needed to prepare a bid without implying qualification.

**Fixture context — outside the artboard.** Mary Wanjiku; authenticated user with verified email; New Account variant; 18 May 2027, 09:00 EAT.

**Page header.** Title **Set up your supplier account**. Description **Enter the organisation that will prepare and submit bids.** No header action.

**Composition, top to bottom.**

1. Visible information panel: **Account setup gives your organisation access to bid preparation. It does not prequalify or approve the organisation for a Tender.**
2. Form section **Organisation details**: Legal name full width; Country and Registration number; KRA PIN; Registered address full width.
3. Section **Official contact**: Official email and Official phone. Show the authenticated user's email as secondary helper, not as the organisation email value.
4. Section **Your responsibility**: read-only **Authorised Signatory**; Job title **Managing Director**; Authority evidence upload using the shared filename.
5. Footer: secondary **Cancel**; primary **Create account**.

**Verification state BDS-DES-03-VERIFY.** After Create account, show heading **Verify your contact** and text **We sent a verification link to tenders@afyadigital.example. Verify it before starting a bid.** Actions **Resend verification link** and **Back to Account**. Status is Pending verification; do not show Active or create a bidder arrangement.

**Visual check.** Registration is short, factual and explicitly separated from Tender eligibility.

### 10.5 BDS-DES-04 — Supplier Account

**Purpose.** Maintain organisation facts, authorised people and reusable evidence in one place.

**Fixture context — outside the artboard.** Mary Wanjiku; Authorised Signatory; Afya Digital Supplies Limited; 18 May 2027, 10:00 EAT.

**Page header.** Title **Account**. Description **Manage the organisation information and people used for bids.** Badge **Active** beside the legal name. Primary **Edit organisation** at right.

**Composition, top to bottom.**

1. Section **Organisation** with labelled values Legal name; Country; Registration number; KRA PIN; Registered address; Official email; Official phone.
2. Section **People** with table columns Person; Responsibility; Effective period; Action. Rows David Ouma / Supplier Representative / From 18 May 2027 / View; Mary Wanjiku / Authorised Signatory / From 18 May 2027 / View. Secondary **Add person** beneath table.
3. Section **Reusable evidence** with columns Evidence; Reference; Valid until; Status; Action. Rows Certificate of incorporation / PVT-9X7K2M / — / Available / View; Tax compliance certificate / P051234567X / 31 Dec 2027 / Available / View; Youth reservation evidence / AGPO-Y-2026-04172 / 30 Jun 2027 / Available / View.
4. Text below evidence: **A bid uses an exact copy of linked evidence. Updating this list does not change a submitted bid.** Secondary **Add evidence**.

**Incomplete variant BDS-DES-04-ATTENTION.** Amber result **Complete 1 item before starting a bid**; list **Enter the official phone number** with **Edit organisation**. Do not call the Account unverified.

**Pending-verification variant BDS-DES-04-VERIFY.** Badge **Pending verification**. Information result **Verify tenders@afyadigital.example before starting a bid.** Action **Resend verification link**. Organisation facts remain editable; bid start/edit/submit actions are absent.

**Visual check.** Account management contains only reusable identity/access facts and never resembles supplier approval or evaluation.

### 10.6 BDS-DES-05 — My bids

**Purpose.** Let the active supplier organisation find every Draft, submitted or withdrawn bid and its next action.

**Fixture context — outside the artboard.** David Ouma; Supplier Representative; Afya Digital Supplies Limited; 10 Jun 2027, 14:20 EAT; primary bid Draft Version 7, reviewed and Ready to submit.

**Page header.** Title **My bids**. Description **Continue your organisation's bids and view submission receipts.** No header action.

**Composition, top to bottom.**

1. Compact filter row: Search Tender or bid; Status **All statuses**; **Clear filters**.
2. Table columns Tender; Bid; Status; Submission deadline; Last updated; Action.
3. Fixture row: Tender title first line and TND reference beneath; BID-MOH-2027-033-001 with secondary **Draft Version 7**; status **Ready to submit**; 12 Jun 2027, 11:00 EAT; Last updated 10 Jun 2027, 13:50 EAT; primary **Review bid**.

**Variants.**

- **BDS-DES-05-SUBMITTED:** status Submitted; Last updated 10 Jun 2027, 14:32 EAT; action **View receipt**.
- **BDS-DES-05-WITHDRAWN:** use Withdrawal fixture; status Withdrawn; action **View acknowledgement**; secondary **Start replacement** before deadline.
- **BDS-DES-05-EMPTY:** **No bids yet. Find a Tender to start your first bid.** Action **View Tenders**.

**Visual check.** Each bid appears once with one plain-language next action; no workflow stage, schema or package terminology appears.

### 10.7 BDS-DES-06 — Bid workspace

**Purpose.** Show exactly what remains before the bid can be submitted.

**Fixture context — outside the artboard.** David Ouma; Supplier Representative; BID-MOH-2027-033-001 Draft Version 7; 10 Jun 2027, 14:20 EAT; all preparation tasks complete and Mary reviewed at 14:15 EAT.

**Page header.** Title **Your bid**. Place Tender title and references beneath on separate muted lines. Description **Complete the five tasks below before an Authorised Signatory submits the bid.** Badge **Ready to submit**. Primary **Review bid** at right.

**Composition, top to bottom.**

1. Deadline strip **Submissions close 12 Jun 2027, 11:00 EAT** with text **2 days remaining**.
2. Current notice panel: ADD-MOH-2027-033-001 **Acknowledged**; **View addendum**.
3. Five-row task table with columns Task; Status; Updated; Action. Rows:
   - Tender documents and addenda / Complete / 1 Jun 2027, 12:10 / View;
   - Company, declarations and tender security / Complete / 10 Jun 2027, 10:05 / View;
   - Requirements and supporting evidence / Complete / 10 Jun 2027, 11:30 / View;
   - Price / Complete / 10 Jun 2027, 12:15 / View;
   - Review and submit / Complete / 10 Jun 2027, 13:50 / **Review bid**.
4. Beneath table show **Saved 10 Jun 2027, 13:50 EAT by David Ouma.** The Review-and-submit row uses this underlying Draft mutation time; merely opening the review never changes an Updated value. Do not show a percentage, system counts, manifest version or technical validation keys.

**Variants.**

- **BDS-DES-06-IN-PROGRESS:** Requirements status Needs attention; Price status In progress; header badge **Needs attention**; supporting summary **2 tasks need attention**; primary **Continue bid** opens Requirements.
- **BDS-DES-06-ADDENDUM:** use Addendum review facts; amber panel **Review the latest addendum before submitting**; Documents Needs attention; Requirements Needs attention; primary **Review addendum**.
- **BDS-DES-06-REPRESENTATIVE:** same Ready fixture for David; primary **Review bid**, and beneath it text **Mary Wanjiku must submit this bid.** No Submit action.

**Visual check.** The bidder sees five ordinary tasks, current notices, deadline and one next action without a dense dashboard.

### 10.8 BDS-DES-07 — Tender documents and addenda

**Purpose.** Review and acknowledge the exact documents and notices controlling the bid.

**Fixture context — outside the artboard.** David Ouma; Supplier Representative; BID-MOH-2027-033-001 Draft Version 7; 1 Jun 2027, 12:05 EAT; addendum not yet acknowledged.

**Page header.** Back to bid. Title **Tender documents and addenda**. Description **Review the current Tender and acknowledge the issued addendum.** Badge **Needs attention**. No header action.

**Composition, top to bottom.**

1. Section **Official Tender documents** with table columns Document; Published; Action. Rows Invitation to Tender / 15 May 2027 / View, Download; Complete Tender / 15 May 2027 / View, Download.
2. Section **Issued addendum** with one bordered row: ADD-MOH-2027-033-001; Delivery point clarified; Issued 31 May 2027, 09:00 EAT; revised deadline 12 Jun 2027, 11:00 EAT; actions **View** and **Download**.
3. Below the row show required checkbox **I have reviewed ADD-MOH-2027-033-001 and understand that the delivery point and submission deadline changed.** It starts unchecked.
4. Section **Clarification answer** with the exact shared question, answer and answered time. No reply field.
5. Footer: secondary **Back to bid**; primary **Save and continue**, disabled until acknowledgement; explanation beside it **Acknowledge the addendum to continue.**

**Complete variant BDS-DES-07-COMPLETE.** Checkbox checked; badge Complete; primary Save and continue enabled. Display **Acknowledged by David Ouma on 1 Jun 2027, 12:10 EAT** beneath checkbox.

**No-addendum variant BDS-DES-07-NONE.** Omit addendum and clarification sections; show **No addenda have been issued.** Task is Complete after the bidder opens the current Tender documents; no empty acknowledgement control.

**Visual check.** Current documents, changed facts and acknowledgement are obvious; internal package inventory and hashes are absent.

### 10.9 BDS-DES-08 — Company, declarations and tender security

**Purpose.** Confirm the bidding organisation, complete official declarations and provide the required security details.

**Fixture context — outside the artboard.** David Ouma; Supplier Representative; primary Draft; 10 Jun 2027, 10:05 EAT; complete state.

**Page header.** Back to bid. Title **Company, declarations and tender security**. Description **Confirm who is bidding and complete the required legal forms.** Badge **Complete**. No header action.

**Composition, top to bottom.**

1. Section **Bidding organisation** with labelled values Legal name; Registration number; KRA PIN; Address; Arrangement **Single organisation**. Link **Update Account**. Text **Changes apply to this Draft only after you return and confirm them.**
2. Section **Declarations** with table columns Declaration; Status; Action. Render all seven fixture rows in the stated order. Each action **View declaration**; confirmed rows show **Confirmed by David Ouma** as secondary text beneath status.
3. Section **Tender security** with fields in two-column rows: Type and Issuer; Reference and Valid until; Amount and Currency as read-only published values; uploaded proof full width with View/Replace.
4. Directly below show green result **Physical original recorded as received** with Receipt and Received at as separate labelled facts.
5. Section **Authorised Signatory** with Mary Wanjiku; Managing Director; authority evidence View; digital certificate **Ready**.
6. Footer: secondary **Back to bid**; primary **Save and continue**.

**Security-outstanding variant BDS-DES-08-SECURITY.** Amber panel **Physical original not yet recorded**. Text **Deliver the original bank guarantee to the Ministry of Health Procurement Office before 12 Jun 2027, 11:00 EAT. You may submit electronically, but failure to deliver the original before closing may disqualify the bid.** Keep Submit readiness as Review note, not Must fix.

**Joint-venture variant BDS-DES-08-JV.** Replace Bidding organisation values with JV name; lead organisation; member table; agreement evidence; signatory. Declarations remain arrangement-specific. No free-text member list.

**Visual check.** Organisation, official declarations, electronic proof, physical-original status and signatory are distinct and readable; none implies eligibility approval.

### 10.10 BDS-DES-09 — Requirements and supporting evidence

**Purpose.** Respond to every published goods, delivery, technical, warranty, support and experience requirement.

**Fixture context — outside the artboard.** David Ouma; Supplier Representative; primary Draft; 10 Jun 2027, 11:30 EAT; complete state.

**Page header.** Back to bid. Title **Requirements and supporting evidence**. Description **State what you are offering and attach the evidence requested by the Tender.** Badge **Complete**. No header action.

**Composition, top to bottom.**

1. Place a compact group row below header: Offered goods selected; Technical requirements; Warranty and support; Experience; Evidence. Each is an in-page anchor with status text, not a navigation sidebar.
2. Section **Offered goods**: Offered model ApexBook Pro 14; Quantity 250 Each read-only; Delivery date 15 Sep 2027; Delivery location current published value read-only.
3. Section **Technical requirements** with table columns Requirement; Tender requirement; Your response; Evidence; Status. Render all eleven fixture rows. Requirement names are primary; no requirement IDs.
4. Section **Warranty and support** with the six complete fixture rows and columns Requirement; Your response; Evidence; Status.
5. Section **Comparable experience** with published helper **Provide at least 2 comparable contracts completed within the last 5 years.** Render the two fixture contracts with columns Customer; Supply; Completion date; Evidence; Action. Secondary **Add contract**.
6. Section **Supporting evidence** with the ten evidence-set rows and columns Evidence; File; Status; Action. Accepted rows offer View/Replace. No digest or file-storage metadata.
7. Footer: secondary **Back to bid**; primary **Save and continue**.

**Response drawer.** Opens from a technical row. Heading is the requirement name. Show Tender requirement; response control appropriate to the published type; evidence selector/upload; optional comment only if published. Footer Cancel / **Save response**.

**Needs-attention variant BDS-DES-09-ATTENTION.** Use Rejected product datasheet fixture. Red summary **Fix 1 item**; issue **Replace the rejected product datasheet** links Evidence. Technical rows using that file show Needs evidence; task badge Needs attention.

**Addendum variant BDS-DES-09-ADDENDUM.** Amber summary **Review 1 changed response**; Offered goods delivery location shows old value struck through, current published value beneath and action **Confirm current delivery location**. Unaffected technical responses remain Complete.

**Visual check.** Large response content is grouped and scannable, but every published row and exact evidence relationship remains visible and editable without a PDF.

### 10.11 BDS-DES-10 — Price

**Purpose.** Enter the financial offer against the exact published price line.

**Fixture context — outside the artboard.** David Ouma; Supplier Representative; primary Draft; 10 Jun 2027, 12:15 EAT; complete state.

**Page header.** Back to bid. Title **Price**. Description **Enter your price for the published quantity. Totals are calculated automatically.** Badge **Complete**. No header action.

**Composition, top to bottom.**

1. Information line **Currency KES · Fixed prices · Taxes shown separately.** This is one price-treatment lineage; do not show the authorised estimate.
2. Table columns Item; Quantity; Unit; Unit price excluding tax; Line amount before tax. Render the single fixture row. Quantity and Unit are read-only; Unit price is editable; Line amount before tax is calculated and read-only. Any bidder-entered tax control required by the published price treatment sits in the totals panel. Tax and Bid total appear once there, not ambiguously in every row.
3. Totals panel aligned beneath numeric columns: Subtotal excluding tax; Tax; **Bid total**, with the exact fixture values separately labelled.
4. Text **The Form of Tender uses this Bid total. You do not enter the total again.**
5. Footer: secondary **Back to bid**; primary **Save and continue**.

**Incomplete variant BDS-DES-10-INCOMPLETE.** Unit price empty; row Needs attention; totals show em dash, not zero; primary disabled with **Enter the unit price before continuing.**

**Visual check.** Published quantity and bidder price are unmistakable; arithmetic and total reuse prevent duplicate entry.

### 10.12 BDS-DES-11 — Review bid

**Purpose.** Show whether the complete Draft is ready and lead directly to any unresolved work.

**Fixture context — outside the artboard.** Mary Wanjiku; Authorised Signatory; primary Draft Version 7; 10 Jun 2027, 14:15 EAT.

**Page header.** Back to bid. Title **Review bid**. Description **Check the complete bid before submitting it to the electronic tender box.** Badge **Ready to submit**. Primary **Submit bid** at right.

**Composition, top to bottom.**

1. Green result **Ready to submit** with text **All required bid information is complete.**
2. Green supporting fact **Physical tender-security original recorded as received on 10 Jun 2027, 10:00 EAT.** This satisfied fact is not a Review note. Only the Security-outstanding variant uses the amber warning copy from BDS-DES-08.
3. Summary grid with separately labelled Tender; Bidder; Bid; Current deadline; Signatory; Bid total.
4. Section **Bid tasks** with all five rows using the exact §4.6 section statuses; the complete fixture shows **Complete** for every row. Each preparation task offers **Review**.
5. Section **What you are offering**: ApexBook Pro 14; 250 Each; delivery 15 Sep 2027; warranty 36 months; support response 4 hours.
6. Section **Declarations and evidence**: seven declarations confirmed; ten evidence items accepted; tender security reference and physical receipt separately labelled.
7. Section **Price summary** with subtotal, tax and total separately labelled.
8. Footer: secondary **Back to bid**; primary **Submit bid**.

**Evidence-attention variant BDS-DES-11-EVIDENCE-ATTENTION.** Use only the Evidence rejected fixture. Red result **Fix 1 item before submitting** with exact issue link **Replace the rejected product datasheet**. Submit absent; primary **Fix item**.

**Addendum-attention variant BDS-DES-11-ADDENDUM-ATTENTION.** Use only the Addendum review fixture. Red result **Fix 1 item before submitting** with exact issue link **Confirm the current delivery location**. Submit absent; primary **Fix item**.

**Representative variant BDS-DES-11-REPRESENTATIVE.** David sees the same complete review; no Submit action. Visible text at header right **Mary Wanjiku must submit this bid.**

**Visual check.** Readiness, full business offer, evidence and exact submitter are understandable without internal validation or package terminology.

### 10.13 BDS-DES-12 — Submit bid

**Purpose.** Let the Authorised Signatory deliberately sign and submit the exact reviewed bid.

**Fixture context — outside the artboard.** Mary Wanjiku; active Authorised Signatory; primary Draft Version 7; 10 Jun 2027, 14:30 EAT; approved digital certificate available.

**Page header.** Back to review. Title **Submit bid**. Description **Digitally sign and place this bid in the electronic tender box.** Badge **Ready to submit**. No header action.

**Composition, top to bottom.**

1. Visible consequence panel: **After submission, this Version cannot be edited. You may prepare a replacement or withdraw it before 12 Jun 2027, 11:00 EAT. The bid will not be opened or evaluated now.**
2. Directly below it show labelled fact **Current server time 10 Jun 2027, 14:30 EAT**. This value comes from the trusted server-time source and refreshes on a fresh read; it is not the browser clock.
3. Section **Submission summary** with Tender; Bidder; Bid; Bid total; Current deadline; Addendum acknowledged; tender-security physical receipt.
4. Section **Authorised Signatory** with Mary Wanjiku; Managing Director; authority evidence Available; digital certificate **Ready**.
5. Required final confirmation: **I confirm that the information, declarations and evidence in this bid are correct and that I am authorised to submit it for Afya Digital Supplies Limited.** Starts unchecked.
6. Footer: secondary **Cancel**; primary **Submit bid**, disabled until confirmation.

**Confirmation dialog.** Heading **Submit this bid?** Show Tender; Bidder; Bid total; Deadline as four labelled rows. Text **KenTender will apply your digital signature and submit this exact Version to the electronic tender box. Wait for the submission receipt before leaving.** Footer Cancel / primary **Submit bid**.

**Pending state BDS-DES-12-PENDING.** Replace footer with disabled **Submitting bid…** and text **Do not close this page or submit again.** Do not show success until receipt.

**Signature-unavailable variant BDS-DES-12-SIGNATURE.** Red result **Digital signing is not available** with text **Your bid remains saved and has not been submitted. Contact the configured support service before the deadline.** No Submit action.

**Service-unavailable variant BDS-DES-12-SERVICE.** Red result **Electronic submission is temporarily unavailable**; show current time/deadline and **Try confirmation again** only when the server says the earlier attempt definitely failed. An uncertain result uses the common state in §10.17 and offers no retry.

**Visual check.** The final act is explicit and calm; signature, deadline, custody and receipt are clear without exposing cryptographic internals.

### 10.14 BDS-DES-13 — Submission receipt

**Purpose.** Give the supplier authoritative proof that the exact bid Version was accepted.

**Fixture context — outside the artboard.** Mary Wanjiku; Authorised Signatory; primary Submitted Version 1; 10 Jun 2027, 14:33 EAT.

**Page header.** Title **Bid submitted**. Description **Your bid was accepted into the electronic tender box.** Green badge **Submitted**. Primary **Print receipt** at right.

**Composition, top to bottom.**

1. Receipt card with separately labelled Receipt reference `RCPT-MOH-2027-033-001`; Tender; Bidder; Bid; Submission Version 1; Submitted by Mary Wanjiku; Received by tender-box service 10 Jun 2027, 14:31:58 EAT; Accepted into tender box 10 Jun 2027, 14:32:01 EAT; Status Submitted.
2. Section **Submission summary** with Bid total; Offered item; Quantity; Delivery date; Current deadline.
3. Information panel **This receipt confirms submission only. It is not an opening, evaluation or award result.**
4. Section **Before the deadline** with secondary actions **Prepare replacement** and destructive **Withdraw bid**; show text **The current submitted bid remains valid until a replacement is accepted or a withdrawal is acknowledged.**
5. Footer: secondary **Back to My bids**; secondary **Download receipt**.

Do not show a hash, encryption key, certificate serial, package digest, schema identity, database ID or storage location.

**Deadline-passed variant BDS-DES-13-CLOSED.** Use only the Submitted receipt after deadline fixture. Omit replacement/withdraw actions; show **Submission changes closed on 12 Jun 2027, 11:00 EAT.** Receipt remains downloadable. Do not use the never-submitted Late submission fixture for this receipt state.

**Visual check.** The bidder can prove when and what Version was accepted while the receipt reveals no confidential technical internals.

### 10.15 BDS-DES-14 — Replacement and withdrawal

**Purpose.** Change the current bid safely before the deadline without editing or losing the submitted Version.

**Fixture context — outside the artboard.** Mary Wanjiku; Authorised Signatory; Replacement variant; 11 Jun 2027, 08:30 EAT.

**Replacement page.**

1. Page header title **Prepare replacement bid**. Description **Create a new Draft while the submitted bid remains valid.** Badge **Version 1 submitted**. No header action.
2. Visible panel **Receipt RCPT-MOH-2027-033-001 remains current until the replacement is accepted.**
3. Summary labelled Current submitted Version 1; Submitted 10 Jun 2027, 14:32 EAT; Deadline 12 Jun 2027, 11:00 EAT; Current definition includes ADD-MOH-2027-033-001.
4. Text **The new Draft copies your organisation's working responses and current published requirements. Review every changed value before submitting.**
5. Footer Cancel / primary **Create replacement Draft**.

**Replacement receipt variant BDS-DES-14-REPLACED.** Reuse receipt composition with heading **Replacement bid submitted**. Receipt `RCPT-MOH-2027-033-002`; Version 2; submitted 11 Jun 2027, 09:15 EAT. Show lineage **Version 1 superseded** and its receipt as a view action.

**Withdrawal dialog.** Heading **Withdraw this bid?** Show Tender; Bid; current receipt; deadline. Required textarea label **Reason for withdrawal** with helper **Enter 10–500 characters.** Consequence **The bid will no longer be considered. You may submit a new replacement before the deadline. The submitted history will not be deleted.** Footer Keep bid / destructive **Withdraw bid**.

**Withdrawal acknowledgement variant BDS-DES-14-WITHDRAWN.** Use isolated Withdrawal facts. Heading **Bid withdrawn**; acknowledgement reference; Tender; Bidder; Withdrawn by; Withdrawn at; status Withdrawn. Actions Download acknowledgement / Start replacement / Back to My bids.

**Visual check.** Replacement preserves the current bid until success; withdrawal is deliberate, acknowledged and never presented as deletion.

### 10.16 BDS-DES-15 — Record physical tender-security receipt

**Purpose.** Let the procurement receipt owner record the physical original without seeing bid content.

**Shell.** Use the Internal Desk shell in §10.1, not the supplier Website shell.

**Fixture context — outside the artboard.** Charles Mutiso; Procurement receipt owner; 10 Jun 2027, 10:00 EAT; supplier presents original bank guarantee.

**Page header.** Title **Tender-security receipts**. Description **Record physical originals received before the Tender deadline.** Primary **Record receipt** at right.

**Composition, top to bottom.**

1. Filter row Tender reference; Security reference; Receipt status **All statuses**; Clear filters.
2. Table columns Tender; Supplier arrangement; Security reference; Required amount; Deadline; Receipt status; Action.
3. Fixture row TND-MOH-2027-033; Afya Digital Supplies Limited; KCB/TG/2027/8841; KES 500,000.00; 12 Jun 2027, 11:00 EAT; Not recorded; **Record receipt**.
4. Do not show Bid total, responses, evidence filenames, Draft status or bid content.

**Record dialog.** Heading **Record tender-security receipt**. Read-only Tender; Supplier; Security reference; Required amount. Fields Received date/time **10 Jun 2027, 10:00 EAT**; Receipt reference **MOH-SEC-2027-033-017**; Notes optional maximum 500. Required confirmation **I confirm that the physical original identified above was received at the date and time recorded.** Footer Cancel / **Record receipt**.

**Recorded variant BDS-DES-15-RECORDED.** Row status Recorded before deadline; action View receipt. Immutable detail names Charles/time/reference.

**Visual check.** Receipt recording is operationally complete but discloses no bid content and makes no responsiveness decision.

### 10.17 BDS-DES-16 — Common states

| Variant | Heading | Message | Action |
|---|---|---|---|
| Sign-in required | Sign in to start or continue a bid. | Return to this Tender after authentication. | Sign in |
| Forbidden Account | You do not have access to this supplier account | Ask an Authorised Signatory for Afya Digital Supplies Limited to add you as a Supplier Representative. | Back to Tenders |
| Account suspended | This supplier account cannot submit bids. | Preparation and change actions are unavailable. Existing receipts remain available through the authorised recovery route. | View receipts |
| Tender not found | Tender not found. | Return to Tenders. | Back to Tenders |
| Format unsupported | This bid format is not available. | Do not create a partial workspace; contact support. | Contact support |
| Load failure | Bid could not be loaded | Your saved bid has not changed. | Try again |
| Stale Draft | Another person changed this bid. Reload before continuing. | Compare the refreshed Draft before saving. | Reload |
| Evidence rejected | This file could not be accepted. | Show the safe type, size or scan reason without internal details. | Choose another file |
| Submission unavailable | Electronic submission is temporarily unavailable. Your bid remains saved. | Nothing was submitted. | Contact support |
| Definitive custody failure | Electronic submission is temporarily unavailable. Your bid remains saved. | Reference `TBX-REJECT-033-01`. Nothing was submitted; contact support or retry only when the server permits it. | Contact support |
| Confirmation pending | Submission confirmation is still pending. Do not submit again. | Correlation `COR-BDS-2027-033-01`; support reference `SUP-BDS-2027-033-01`. KenTender is checking this same attempt. | View status |
| Deadline passed | The submission deadline has passed. This bid was not submitted. | Deadline 12 Jun 2027, 11:00 EAT; trusted server time 12 Jun 2027, 11:00:01 EAT. | Back to My bids |
| Idempotency conflict | This request was already used with different information. Stop and refresh. | The original attempt is unchanged. | Refresh |
| Replacement conflict | A newer submitted bid already exists. | Show receipt `RCPT-MOH-2027-033-002`; do not change either Version. | View current receipt |
| Tender cancelled | This Tender is not accepting bids. | Status Cancelled; view the cancellation notice for details. | View notice |

Each state replaces the affected content surface. No state renders a successful receipt, Submitted badge or retry mutation until the server has a definitive authoritative result.

### 10.18 Artboard inventory

| Artboard | Primary actor | Purpose | Required variants | Required render sizes |
|---|---|---|---|---|
| BDS-DES-01 | Public visitor | Find Tenders | Filtered empty. | 1440 × 1024 and 390 × 844 |
| BDS-DES-02 | Public / supplier | Review current Tender | Signed out; Joint-venture start; Draft; Submitted; Cancelled. | 1440 × 1024 and 390 × 844 |
| BDS-DES-03 | Authenticated person | Register supplier organisation | Verification. | 1440 × 1024 and 390 × 844 |
| BDS-DES-04 | Authorised Signatory | Manage Account | Incomplete Account; Pending verification. | 1440 × 1024 and 390 × 844 |
| BDS-DES-05 | Supplier user | Find organisation bids | Submitted; Withdrawn; Empty. | 1440 × 1024 and 390 × 844 |
| BDS-DES-06 | Supplier user | Understand remaining bid work | In progress; Addendum review; Representative-ready. | 1440 × 1024 and 390 × 844 |
| BDS-DES-07 | Supplier Representative | Review documents/addenda | Complete; No addendum. | 1440 × 1024 and 390 × 844 |
| BDS-DES-08 | Supplier Representative | Complete company/declarations/security | Security outstanding; Joint venture. | 1440 × 1024 and 390 × 844 |
| BDS-DES-09 | Supplier Representative | Respond to requirements/evidence | Response drawer; Needs attention; Addendum changed. | 1440 × 1024 and 390 × 844 |
| BDS-DES-10 | Supplier Representative | Enter price | Incomplete. | 1440 × 1024 and 390 × 844 |
| BDS-DES-11 | Supplier / Signatory | Review complete bid | Evidence attention; Addendum attention; Representative. | 1440 × 1024 and 390 × 844 |
| BDS-DES-12 | Authorised Signatory | Submit the reviewed bid | Confirmation; Pending; Signature unavailable; Service unavailable. | 1440 × 1024 and 390 × 844 |
| BDS-DES-13 | Authorised Signatory | Prove submission | Deadline closed. | 1440 × 1024 and 390 × 844 |
| BDS-DES-14 | Authorised Signatory | Replace or withdraw | Replacement receipt; Withdrawal dialog/acknowledgement. | 1440 × 1024 and 390 × 844 |
| BDS-DES-15 | Procurement receipt owner | Record physical security receipt | Recorded. | 1440 × 1024 Desk and 390 × 844 Desk |
| BDS-DES-16 | All | Recover from common states | All table variants. | 1440 × 1024 and 390 × 844 |

The design set is complete only when every base artboard, named variant and dialog has been rendered at both listed sizes and checked against its Visual check. A desktop-only render does not complete an inventory row.

## 11. Functional interaction contract

Section 10 defines appearance and content. This section maps every visible control to its exact read or command. It is not supplied to the design tool.

### 11.1 General interaction rules

1. The first page read returns data, access verdict and permitted actions together; no protected content flashes before a denial.
2. Opening a route, document, disclosure, filter, dialog or receipt creates no business fact.
3. A mutation occurs only after the named user action; no page view or preview auto-creates a workspace.
4. Browser code never derives authority, readiness, deadline, totals, submission status, signature validity or custody result.
5. While a mutation is pending, its initiating control is disabled and a second submission is impossible.
6. Successful mutations return the authoritative record version, derived statuses and permitted actions.
7. Failed saves preserve safe entered values and focus the exact error summary/control.
8. A stale result never overwrites another organisation member's change.
9. Back and Cancel close or navigate without saving unless the user has already selected a named save action.
10. Leaving a page with unsaved changes asks **Leave without saving?** with Stay / Leave.
11. Dates and deadlines display EAT; the final Submit page also displays the trusted current server time. List and summary surfaces label the submission time **Submitted** and show `accepted_at` to the minute by omitting seconds without rounding. The authoritative receipt separately labels `received_at` and `accepted_at` to the second.
12. Currency is KES with two decimals; quantities retain the published unit.
13. Bidder-facing responses omit all internal identifiers, digests, schema/renderer names, storage paths, encryption data and audit metadata.
14. A successful upload, save, validation or signature preparation never displays Submitted.

### 11.2 Public Tender and navigation actions

| Visible control | Behaviour |
|---|---|
| Tenders | Opens `/tenders`; public and read-only. |
| My bids | Opens the active organisation's `GetMyBids`; signed-out users authenticate first. |
| Account | Opens `GetSupplierAccount`; signed-out users authenticate first. |
| Search / Method / Reservation / Closing | Requests a server-filtered public list; never expands bidder access. |
| Clear filters | Restores the default open-Tender list. |
| View Tender | Opens the current `GetPublishedTenderForBidder` projection. |
| View / Download document | Opens or streams the exact published document from Tenders by bidder-safe reference. |
| View addendum / notice | Opens the exact current public record; no acknowledgement is implied. |
| Sign in to start bid | Authenticates and returns to the same Tender overview. |
| Start bid | Requires an Active Account. If no Tender-bound arrangement exists, opens **Who is bidding?**; after `CreateBidderArrangement` succeeds, calls `StartBid`. Registration alone never creates an arrangement. |
| Create arrangement and start bid | Calls `CreateBidderArrangement` for the current Tender, then `StartBid`; if either fails, no partial workspace is created. |
| Continue bid | Opens the existing workspace returned by `GetBidWorkspace`; never creates another. |
| View receipt | Opens the current organisation-owned receipt. |

### 11.3 Account actions

| Visible control | Behaviour |
|---|---|
| Create account | Calls `RegisterSupplierOrganisation`; opens BDS-DES-03-VERIFY with status Pending verification. |
| Resend verification link | Calls `SendAccountVerification`; retains Pending verification and rate-limits without disclosing whether another Account exists. |
| Open verification link | Calls `VerifyAccountCommunication`; on success opens Account with status Active. |
| Edit organisation | Opens the bounded editor and calls `UpdateSupplierOrganisation` on Save. |
| Add person | Creates one Supplier Representative or Authorised Signatory assignment; signatory requires authority evidence. |
| View person | Shows immutable assignment, responsibility, evidence and effective dates. |
| Add evidence | Uploads through the Account evidence service; it creates no bid evidence until explicitly linked. |
| View evidence | Opens the authorised Account evidence and its self-declared metadata. |

Changing the active organisation reloads My bids and Account under that organisation. It does not copy, expose or move another organisation's records.

### 11.4 Bid workspace and preparation actions

| Visible control | Behaviour |
|---|---|
| Task View / Continue / Fix | Opens the exact current Draft task and first relevant issue when present. |
| Review addendum | Opens BDS-DES-07 against the effective addendum set. |
| Acknowledge addendum | `AcknowledgeTenderDocument` commits only after the user selects Save and continue. |
| Save and continue | Calls `SaveBidTask`; on success opens the next incomplete task or workspace. |
| Back to bid | Warns on unsaved changes, then returns to workspace without mutation. |
| Update Account | Opens Account in a new safe route; returning refreshes, but does not automatically overwrite, the Draft. |
| View declaration | Opens the complete locked published text read-only. |
| Confirm declaration | Saves explicit confirmation for the exact text/version; never preselected. |
| View / Replace evidence | Opens or replaces the exact Draft evidence item; replacement re-runs scan and invalidates affected task completeness until Accepted. |
| Add contract | Adds one structured comparable-contract row and its evidence. |
| Technical requirement row | Opens the response drawer for the exact published row. |
| Save response | Validates and saves only that published response/evidence relationship. |
| Save price | Calls `SaveBidTask` for Price; server returns deterministic totals. |
| Review bid | Calls no mutation; opens a fresh `GetBidReview`. |

### 11.5 Review, signature and submission actions

| Visible control | Behaviour |
|---|---|
| Issue link / Review | Opens the exact task, row or evidence item. |
| Submit bid | Available only to an active Authorised Signatory with server readiness; opens BDS-DES-12. |
| Final confirmation | Local required control for this submission attempt; it does not sign or submit by itself. |
| Submit bid in confirmation dialog | Calls `PrepareBidSignature`, completes the approved signature flow and then calls `SubmitBid` with the signed exact package and one idempotency key. |
| View status | Reads the existing uncertain correlation; it never dispatches another submission. |
| Try confirmation again | Available only after a definitive failed attempt with no accepted custody result; reuses the safe server correlation rule. |
| Contact support | Opens the configured support instructions and correlation reference; grants no authority and changes nothing. |

The browser waits for the authoritative `SubmitBid` result. Only a returned accepted receipt routes to BDS-DES-13. Timeout or lost response uses Confirmation pending until the server resolves the existing correlation.

### 11.6 Receipt, replacement and withdrawal actions

| Visible control | Behaviour |
|---|---|
| Print receipt | Opens the accessible print view of the exact receipt. |
| Download receipt / acknowledgement | Downloads a human-readable immutable artifact from the recorded receipt. |
| Prepare replacement | Opens BDS-DES-14; `PrepareReplacementBid` runs only after confirmation. |
| Create replacement Draft | Calls `PrepareReplacementBid`; current Submitted Version remains effective. |
| Withdraw bid | Opens the named destructive dialog; after reason/confirmation calls `WithdrawBid`. |
| Keep bid | Closes the dialog without mutation. |
| Start replacement | Starts a new Draft from a Withdrawn workspace before deadline. |
| View earlier receipt | Opens the immutable predecessor receipt and its Superseded status. |

### 11.7 Tender-security receipt actions

| Visible control | Behaviour |
|---|---|
| Record receipt | Opens the exact security item without bid responses or price. |
| Confirm receipt | Calls `RecordPhysicalTenderSecurityReceipt`; server derives actor/time and classifies before/after deadline. |
| View receipt | Opens immutable reference, received time and recorder. |

The receipt owner cannot edit or reverse a committed receipt. A correction is an append-only linked record requiring the configured accountable route.

### 11.8 Common recovery and accessibility

| Visible control | Behaviour |
|---|---|
| View receipts | Opens `/account/receipts` and reads only the authorised organisation's existing receipts. A Suspended Account gains no preparation or change action. |
| Refresh | Repeats the current authoritative read and changes no business fact. |
| View current receipt | Calls `GetSubmissionReceipt` for the organisation-owned current receipt and changes nothing. |
| Choose another file | Reopens the file chooser for the exact evidence requirement. Selection alone changes nothing; the existing upload command runs only after the user confirms the replacement. |
| Back to Account | Opens `GetSupplierAccount` at `/account` and changes nothing. |

- Back, Reload, Try again and Clear filters repeat reads only.
- No recovery action bypasses Account, authority, definition, evidence, deadline, signature or custody checks.
- All pages have one `h1`, logical heading order, landmarks and keyboard-operable controls.
- Status uses text, not colour alone. Dynamic issue/submit status is announced once without repeated interruption.
- Tables expose headers and a meaningful row label; at narrow widths each row becomes a labelled card without losing values or actions.
- Dialog focus is trapped and returns to the initiating control. Error focus goes to the summary or exact invalid field.
- Files show accessible filename, format, size and View/Download action; no filename is the only statement of purpose.
- Destructive withdrawal uses both a destructive label and explicit consequence.
- Portal pages meet the applicable KT-STD-001 v1.6 accessibility and responsive release gates.

## 12. Audit, confidentiality and custody

### 12.1 Event minimum

Every successful mutation records:

- event identity and schema version;
- organisation, arrangement, Tender, workspace and resulting record version identities;
- command name and idempotency-key hash;
- authenticated user and active supplier/procurement responsibility assignment;
- server occurrence time in UTC and displayed EAT value;
- previous and resulting lifecycle states;
- affected published definition, task/row or submission Version identities;
- reason, acknowledgement or declaration identity where applicable;
- evidence/signature/custody references and server-only digests where applicable; and
- permitted security/session metadata under the security and retention policy.

Rejected commands create a security/operational audit fact where policy requires it, but never create a supplier declaration, acknowledgement, submission, receipt or withdrawal.

### 12.2 Required business evidence

| Business fact | Immutable evidence |
|---|---|
| Organisation registered | Exact self-declared fields, communication verification, creator and time; no eligibility claim. |
| User assigned | Organisation, person, responsibility, authority evidence, effective window, assigner/time. |
| Bid started | Tender, supplier arrangement, exact definition, creator/time and uniqueness result. |
| Document/addendum acknowledged | Exact document/addendum Version, supplier user and time. |
| Draft response saved | Draft version, published row identity, canonical prior/new values and actor/time. |
| Evidence accepted | Exact requirement, file identity/digest, technical scan result and uploader/time. |
| Physical security received | Tender, supplier arrangement, security reference, receipt reference, received time and procurement recorder. |
| Bid validated | Exact Draft definition/response/evidence set and complete findings; no submission claim. |
| Bid signed | Exact canonical package, signatory assignment, certificate/trust evidence and verification time. |
| Bid submitted | Signed package, received/accepted times, approved tender-box receipt, immutable submission Version and bidder receipt. |
| Replacement submitted | New Version/receipt and predecessor marked Superseded in the same authoritative result. |
| Bid withdrawn | Exact current Version, signatory, reason, trusted time and electronic acknowledgement. |
| Submission closed | Effective deadline/timezone, automatic close evidence, sealed envelope inventory and Bid Opening handoff. |

### 12.3 Confidentiality and custody rules

1. Draft responses and evidence are visible only to assigned users of the supplier arrangement and narrowly authorised support under a separately approved process.
2. Submitted content is encrypted/sealed under the approved tender-box design and is unavailable to BDS, Procuring Entity business users, database users, report builders, search indexes, logs, analytics and backups in plaintext.
3. Secrets, private keys and opening credentials are never stored in application configuration, fixtures, logs or ordinary database fields.
4. The application logs package/correlation identities, not response values, prices, filenames, personal document contents or signature secrets.
5. Download links are short-lived, authorised and bound to the requesting supplier/record.
6. A supplier can read its own Draft and receipt; this does not authorise Procuring Entity access.
7. Support tooling exposes service health and correlation status only. No routine **decrypt**, **preview submitted bid**, **download envelope** or **open now** control exists.
8. Retention, legal hold and disposal follow the approved procurement records schedule. Business users cannot delete a Draft history, submission, receipt, signature, withdrawal or custody event.
9. Personal data is limited to what is necessary for identity, authority, communication and the bid; portal/API projections exclude unrelated internal data.
10. A security incident never changes the legal status of a bid silently; containment, evidence and any decision follow the approved incident and procurement route.

## 13. Deterministic seed contract

### 13.1 Seed rules

The seed uses the complete fixture in §10.1. Re-running it is idempotent and creates no duplicate organisation, assignment, arrangement, workspace, response, evidence, acknowledgement, submission, receipt, withdrawal or tender-box envelope. All displayed times are EAT with exact UTC equivalents.

Synthetic evidence files contain real deterministic test bytes and recorded digests. The test certificate, trust response and tender-box receipt are explicitly labelled simulation in seed/audit evidence and never presented as production accreditation.

### 13.2 Actors and assignments

| Actor | Responsibility |
|---|---|
| David Ouma | Supplier Representative for Afya Digital Supplies Limited. |
| Mary Wanjiku | Authorised Signatory for Afya Digital Supplies Limited from 18 May 2027; authority evidence present. |
| Charles Mutiso | Procurement receipt owner for the physical tender-security fixture; no bid-content access. |
| Alice Njeri | Auditor; metadata/evidence access only under approved test scope. |
| Daniel Otieno | Administrator/System Manager; non-content technical read. |
| Test Trust Service | Simulated licensed-certificate verification for isolated testing only. |
| Test Tender Box | Simulated approved custody receipt and closed-box behavior for isolated testing only. |

### 13.3 Primary lifecycle fixture

| Date and time | Event | Result |
|---|---|---|
| 18 May 2027 09:00 | Register Afya Digital Supplies Limited | Pending verification Account; challenge sent; no qualification claim. |
| 18 May 2027 09:10 | Verify configured email | Account becomes Active; proves channel control only. |
| 18 May 2027 09:20 | Assign David | Supplier Representative active. |
| 18 May 2027 09:30 | Assign Mary | Authorised Signatory active with authority evidence. |
| 19 May 2027 09:20 | Start bid | `BID-MOH-2027-033-001` Draft against published definition Version 1. |
| 19–30 May 2027 | Complete initial tasks | Structured Draft responses/evidence only. |
| 31 May 2027 09:00 | Tender owner issues addendum | Definition Version 2 and revised deadline 12 Jun 2027, 11:00 EAT. |
| 1 Jun 2027 12:10 | David acknowledges addendum | Affected delivery response reviewed; unrelated responses preserved. |
| 10 Jun 2027 10:00 | Charles records physical security | `MOH-SEC-2027-033-017`, Recorded before deadline; no bid content exposed. |
| 10 Jun 2027 13:50 | David saves complete Draft Version 7 | All preparation tasks Complete; David cannot submit. |
| 10 Jun 2027 14:15 | Mary opens review | Readiness is returned as Ready to submit; this read creates no business fact and does not change the 13:50 `last_saved_at`. |
| 10 Jun 2027 14:31:58–14:32:01 | Mary submits | Test signature verifies; Test Tender Box receives at 14:31:58 and accepts Version 1 at 14:32:01; receipt `RCPT-MOH-2027-033-001`. |
| 12 Jun 2027 11:00 | Submission closes | Version 1 remains current; sealed envelope handed to Bid Opening owner. |

### 13.4 Isolated and continuation fixtures

| Fixture | Required state |
|---|---|
| Public signed out | Tender is readable; sign-in required only on Start bid. |
| Account incomplete | Organisation has no official phone; no bid workspace created. |
| Account pending verification | Afya Digital Supplies Limited is Pending verification at 18 May 2027, 09:05 EAT; start is blocked until the configured email challenge succeeds. |
| Account suspended | Afya Digital Supplies Limited is Suspended at 10 Jun 2027, 14:20 EAT; all preparation/change commands are blocked while its existing receipt remains recoverable. |
| Cross-organisation denial | Peter Mwangi, unassigned to Afya Digital Supplies Limited, requests the primary workspace at 10 Jun 2027, 14:20 EAT; response masks record existence and returns no bid fact. |
| Addendum review | Definition Version 2 exists; acknowledgement and delivery-location review outstanding. |
| Evidence rejected | Product datasheet fails test malware scan; no Accepted evidence binding. |
| Security outstanding | Proof accepted; no physical receipt; Review note only at electronic submission. |
| Supplier Representative ready | David sees complete review but no Submit action. |
| Signature unavailable | Mary has authority but no valid approved test certificate; nothing submitted. |
| Custody definitely failed | Mary submits at 10 Jun 2027, 14:30 EAT; rejection `TBX-REJECT-033-01`; Draft preserved; no envelope or receipt. |
| Custody uncertain | Mary submits at 10 Jun 2027, 14:30 EAT; correlation `COR-BDS-2027-033-01` and support reference `SUP-BDS-2027-033-01` remain pending; no retry, receipt or Submitted state until reconciled. |
| Late submission | Mary's complete request reaches the trusted server at 12 Jun 2027, 11:00:01 EAT; rejected; no envelope or receipt. |
| Submitted receipt after deadline | Version 1 received 10 Jun 2027, 14:31:58 EAT and accepted 14:32:01 EAT; current trusted time 12 Jun 2027, 11:00:01 EAT; receipt remains readable and change actions are closed. |
| Replacement | Continue primary after Version 1; Version 2 accepted 11 Jun 2027 09:15 with `RCPT-MOH-2027-033-002`; Version 1 Superseded atomically. |
| Replacement Draft abandoned | Version 1 remains current when the deadline passes; unsent successor closes without submission. |
| Withdrawal | Separate Tender/Bid from §10.1; `WD-MOH-2027-041-001` acknowledged; envelope/history retained; no current bid. |
| Concurrent submission | Two Version-7 requests share one idempotency key; one Version/receipt results. |
| Conflicting replay | Same idempotency key with changed price; rejected; original receipt unchanged. |
| Replacement conflict | Version 2 is already current with receipt `RCPT-MOH-2027-033-002`; a stale Version-3 replacement attempt changes neither Version. |
| Cancelled Tender | Public notice remains; no Start/Continue/Submit command. |

An isolated fixture never reuses one receipt, signature, envelope, evidence result or event time to prove opposite outcomes.

## 14. Acceptance contract

Each criterion is independently testable. A visually correct page without its authority, deadline, signature, custody and audit controls does not pass.

### 14.1 Public access, Account and organisation scope

| ID | Acceptance criterion |
|---|---|
| BDS01-AC-001 | Anyone can view the available-Tenders list, current public Tender, documents, addenda, clarification answers and cancellation notice without creating an Account or business record. |
| BDS01-AC-002 | Public and portal DTOs expose only bidder-task information and omit internal package, schema, digest, configuration, database, security and audit metadata. |
| BDS01-AC-003 | Start bid requires authentication and returns safely to the same Tender after sign-in. |
| BDS01-AC-004 | Organisation registration captures only the fields in §4.1 and explicitly states that Account activation is not qualification or eligibility approval. |
| BDS01-AC-005 | Communication verification is displayed only as channel control, never as proof of company, tax or reservation status. |
| BDS01-AC-006 | Cross-organisation reads and commands are denied and mask whether another organisation has a Draft or submission. |
| BDS01-AC-007 | A Supplier Representative can prepare but cannot submit, replace or withdraw. |
| BDS01-AC-008 | An Authorised Signatory command requires an active assignment, authority evidence and effective window at command time. |
| BDS01-AC-009 | One person can act for several organisations only through separate assignments and an explicit active-organisation context. |
| BDS01-AC-010 | A suspended Account cannot start, edit or submit, but its authorised recovery route preserves receipts and records. |
| BDS01-AC-011 | A joint venture is available only when permitted by the published Tender and records lead, members, agreement evidence and exact signatory. |
| BDS01-AC-012 | One Tender and supplier arrangement can create at most one active workspace under concurrent/repeated Start bid requests. |

### 14.2 Published definition and bid preparation

| ID | Acceptance criterion |
|---|---|
| BDS01-AC-013 | Start bid binds the exact Published Tender, template release, addendum set and supported definition Version atomically. |
| BDS01-AC-014 | An unsupported response definition creates no partial workspace and shows the exact unavailable state. |
| BDS01-AC-015 | For `IT-EQUIPMENT-OPEN-V1`, the bidder workspace presents exactly five visible tasks in the order defined in §5.3. |
| BDS01-AC-016 | Every response row originates from the Published Tender and retains stable response, evaluation and contract mappings server-side. |
| BDS01-AC-017 | Unknown, hidden, inapplicable or client-invented response fields are rejected and never stored. |
| BDS01-AC-018 | Tender quantities, units, requirements, declaration texts, price rows, currency and tax treatment are read-only to the bidder. |
| BDS01-AC-019 | Draft saves accept incomplete valid work and derive task/readiness status without implying submission. |
| BDS01-AC-020 | Concurrent Draft edits use record versions; a stale save cannot overwrite another organisation member's change. |
| BDS01-AC-021 | All eleven technical rows, six warranty/support rows and five acceptance obligations from the published fixture remain accounted for in the response/evaluation/contract chain. |
| BDS01-AC-022 | Large requirement sets are grouped for navigation without changing identity, order, wording, applicability or completeness. |
| BDS01-AC-023 | Known organisation values are reused once and changes require explicit Draft refresh; silent Account-to-Draft mutation is impossible. |
| BDS01-AC-024 | Locked declaration text is fully viewable, never preselected and explicitly confirmed against its exact published Version. |
| BDS01-AC-025 | Completing a declaration or task remains reversible in Draft and is not an evaluation or legal-success decision. |
| BDS01-AC-026 | PDF documents are view/download references only; no filled PDF, ZIP or spreadsheet can replace required structured responses. |
| BDS01-AC-027 | The bidder sees one plain next action derived by the server and never sees a schema, renderer, manifest or internal status key. |
| BDS01-AC-028 | The primary fixture can be completed through the five tasks without duplicate entry of company identity, Tender facts, requirements or total price. |

### 14.3 Evidence, tender security and price

| ID | Acceptance criterion |
|---|---|
| BDS01-AC-029 | Every evidence item links to one visible published requirement, declaration or permitted form; miscellaneous unrequested evidence cannot become a criterion. |
| BDS01-AC-030 | An uploaded file is unusable until media/size/integrity/malware checks return Accepted. |
| BDS01-AC-031 | Rejected evidence immediately identifies the safe technical reason and prevents affected task completion without claiming criterion failure. |
| BDS01-AC-032 | Reusing Account evidence freezes an exact bid-bound copy; later Account replacement cannot alter a submitted bid. |
| BDS01-AC-033 | Evidence metadata is captured only when required by the published definition and no storage path/digest is bidder-visible. |
| BDS01-AC-034 | Tender-security type, issuer, reference, amount, currency, validity and proof follow the published rule and cannot be replaced by a generic upload. |
| BDS01-AC-035 | The procurement receipt owner can record physical tender-security receipt without access to responses, price or Draft status. |
| BDS01-AC-036 | Physical receipt records server actor/time and classifies before/after deadline immutably. |
| BDS01-AC-037 | An outstanding physical original produces the exact warning but does not falsely prevent electronic submission or fabricate disqualification. |
| BDS01-AC-038 | Quantity, unit, line identity and currency are read-only in Price; only published bidder price/tax fields are editable. |
| BDS01-AC-039 | Decimal arithmetic and rounding deterministically produce the §10.1 subtotal, tax and bid total. |
| BDS01-AC-040 | The Form of Tender projection consumes the one current Price total without re-entry or independent edit. |
| BDS01-AC-041 | The bidder never sees the authorised estimate, Budget, source allocation or internal reservation value. |
| BDS01-AC-042 | Another currency, alternative price, new line, unrequested discount and spreadsheet import are rejected for this product. |

### 14.4 Addenda, clarifications and readiness

| ID | Acceptance criterion |
|---|---|
| BDS01-AC-043 | The portal displays every issued addendum and authoritative clarification answer applicable to the Tender. |
| BDS01-AC-044 | A new addendum creates a new immutable definition and never edits an earlier definition, Draft Version or submitted Version. |
| BDS01-AC-045 | Submission is blocked until every current required addendum is acknowledged. |
| BDS01-AC-046 | Stable unaffected responses may copy forward; every affected response becomes Needs attention with an exact issue link. |
| BDS01-AC-047 | A submitted bid remains sealed after an addendum; changing it requires a replacement before the revised deadline. |
| BDS01-AC-048 | The effective deadline shown and enforced is the latest lawfully issued Tender/addendum deadline. |
| BDS01-AC-049 | BDS submits authenticated questions through the Tenders owner contract and does not create a parallel clarification store. |
| BDS01-AC-050 | A clarification affecting requirements is displayed to all candidates without identifying the questioner and participates in the effective definition. |
| BDS01-AC-051 | Validation recomputes the exact current definition, arrangement, responses, evidence, acknowledgements, security and price. |
| BDS01-AC-052 | Every Must fix issue blocks submission and links to the exact task/row; a Review note does not block unless the published rule requires it. |
| BDS01-AC-053 | A Supplier Representative sees the same complete review but no Submit control and the page names the Authorised Signatory. |

### 14.5 Digital signature, submission and receipt

| ID | Acceptance criterion |
|---|---|
| BDS01-AC-054 | Production Submit bid is unavailable until the exact operating profile in §5.10 is approved, configured and healthy. |
| BDS01-AC-055 | The final action is plain-language Submit bid; its consequence states signature, locking, tender-box deposit and no opening/evaluation. |
| BDS01-AC-056 | The server rechecks readiness, authority, definition, deadline, totals and evidence immediately before signing and immediately before deposit. |
| BDS01-AC-057 | Submission requires a valid digital signature certificate from the approved licensed trust chain and binds the exact canonical package. |
| BDS01-AC-058 | Typed name, checkbox, uploaded signature image, login password, staff override or client flag cannot satisfy the signature requirement. |
| BDS01-AC-059 | A signature for another person, organisation, package or expired/revoked certificate is rejected and nothing is submitted. |
| BDS01-AC-060 | The complete signed request must reach the trusted server before the effective deadline; client time and dialog-open time are ignored. |
| BDS01-AC-061 | All evidence is Accepted before final submission; no hidden post-deadline evidence upload can complete the bid. |
| BDS01-AC-062 | Submitted state and receipt commit only after the approved tender box accepts the exact signed envelope. |
| BDS01-AC-063 | A definite tender-box rejection leaves the Draft unchanged and creates no receipt. |
| BDS01-AC-064 | An uncertain result shows Confirmation pending, prevents duplicate dispatch and reconciles the same correlation to one outcome. |
| BDS01-AC-065 | Identical replay returns the original receipt; changed content under the same idempotency key is rejected. |
| BDS01-AC-066 | The receipt contains all §4.10 human-readable facts and omits hashes, keys, certificate internals, schemas and storage data. |
| BDS01-AC-067 | The receipt explicitly says that submission is not opening, evaluation or award. |
| BDS01-AC-068 | Supplier-facing Submitted appears only from authoritative accepted custody evidence, never from a save, upload, validation, signature start, queue or internal record insert. |

### 14.6 Replacement, withdrawal, closing and handoff

| ID | Acceptance criterion |
|---|---|
| BDS01-AC-069 | Prepare replacement leaves the current submitted Version and receipt effective. |
| BDS01-AC-070 | A replacement becomes current only when its new signed envelope is accepted; predecessor Superseded and new receipt commit atomically. |
| BDS01-AC-071 | If a replacement Draft is abandoned or the deadline passes, the prior submitted Version remains current. |
| BDS01-AC-072 | Withdrawal requires the active Authorised Signatory, exact current Version, reason, confirmation and trusted pre-deadline time. |
| BDS01-AC-073 | Withdrawal produces an electronic acknowledgement and retains the envelope, signature, receipt and complete history. |
| BDS01-AC-074 | A withdrawn arrangement may submit a new replacement before deadline with a new Version and receipt. |
| BDS01-AC-075 | Submit, replacement and withdrawal arriving after the deadline are rejected without status change or misleading acknowledgement. |
| BDS01-AC-076 | The tender box closes automatically at the effective deadline and no business/technical user can reopen, extend or backdate it. |
| BDS01-AC-077 | Unsubmitted Drafts become Closed without submission and never appear in the opening inventory. |
| BDS01-AC-078 | The Bid Opening handoff contains only closed-box, sealed-envelope, receipt/change lineage and custody evidence; BDS provides no open/decrypt command. |

### 14.7 Confidentiality, usability, accessibility and audit

| ID | Acceptance criterion |
|---|---|
| BDS01-AC-079 | Before governed opening, Procuring Entity business users cannot see bidder identities, bid count, responses, evidence filenames, prices or content from the tender box. |
| BDS01-AC-080 | Technical and administrator views expose only authorised service/custody metadata and cannot decrypt, preview, download or search submitted content. |
| BDS01-AC-081 | Draft and submitted-content values never appear in logs, search indexes, analytics, traces or error messages. |
| BDS01-AC-082 | Submitted content is protected under the approved custody design and secrets/private keys are absent from application data/configuration/fixtures. |
| BDS01-AC-083 | Every artboard can be produced from §10 plus KT-STD-001 v1.6 §2 without invented content or behavior. |
| BDS01-AC-084 | Every visible action has exactly one mapping in §11 and is absent when the server does not permit it. |
| BDS01-AC-085 | Public and supplier tasks use ordinary language and expose no internal workflow, schema, rendering, package or cryptographic terminology. |
| BDS01-AC-086 | For the current Goods/IT product, a representative user can find a Tender, set up an Account, prepare the five tasks and understand who must submit without moderator explanation. |
| BDS01-AC-087 | An Authorised Signatory can review, submit and identify the authoritative receipt without mistaking submission for opening or award. |
| BDS01-AC-088 | All portal and Desk receipt surfaces meet the keyboard, focus, status-text, error-linking and responsive rules in §§10–11 and KT-STD-001. |
| BDS01-AC-089 | Every successful Account, response, evidence, acknowledgement, security-receipt, signature, submission, replacement, withdrawal and close fact records the minimum evidence in §12. |
| BDS01-AC-090 | The §13 seed reruns without duplication, isolates opposing outcomes and never presents simulated trust/custody evidence as production compliance. |

### 14.8 STD-derived definition and rendering acceptance

| ID | Acceptance criterion |
|---|---|
| BDS02-AC-001 | The exact released STD bundle, Tender Version, authorised source rows and effective addenda deterministically produce one ordered immutable `PublishedBidDefinition`; repeated generation produces no semantic drift. |
| BDS02-AC-002 | Every task, group, response, evidence requirement, declaration and price/schedule row has one stable published identity, visible published source and supported product-profile treatment. |
| BDS02-AC-003 | Publication fails if a required response lacks validation or applicable downstream mapping, if human-readable and structured schedules disagree, or if the definition introduces an unpublished obligation. |
| BDS02-AC-004 | The runtime resolves an exact code-owned product profile and renderer Version. An unknown template family, component, response type or named rule creates no partial workspace and has no generic fallback. |
| BDS02-AC-005 | The bidder client selects no template, executes no arbitrary metadata logic and saves only typed values against stable published identities; the server independently revalidates every save. |
| BDS02-AC-006 | Every bidder-editable field has a current visible purpose and a validation, evidence, evaluation, calculation or contract consumer; storage-only and speculative metadata create no field. |
| BDS02-AC-007 | Conditional applicability is resolved by reviewed named rules; newly required work becomes incomplete and newly inapplicable values are excluded from readiness/final packaging without erasing Draft audit history. |
| BDS02-AC-008 | Addendum migration uses an explicit unchanged/changed/removed/new identity map. No response copies through label, row position, text similarity or client inference. |
| BDS02-AC-009 | The issued Tender PDF is reference/output only and is never parsed at runtime to generate bidder controls, validation or downstream mappings. |
| BDS02-AC-010 | `IT-EQUIPMENT-OPEN-V1` retains its approved five-task Goods composition. Works or Services cannot use it merely because their data fits shared primitive controls; each requires a separately approved release, renderer profile, fixtures, artboards and acceptance tests. |

### 14.9 Artboard consistency and recovery acceptance

| ID | Acceptance criterion |
|---|---|
| BDS03-AC-001 | Every artboard fixture time is at or after every fact rendered as already completed; the primary My bids/workspace fixture is 10 Jun 2027, 14:20 EAT and is consistent with the 13:50 save and 14:15 read-only review. |
| BDS03-AC-002 | Workspace and task badges use only the exact §4.5 and §4.6 status values; issue counts are supporting text, never replacement statuses. |
| BDS03-AC-003 | A recorded physical tender-security original is displayed as a satisfied supporting fact; only an outstanding original is an amber Review note. |
| BDS03-AC-004 | Every common state that maps to a §8 error reproduces that error text exactly before any fixture-specific context or recovery action. |
| BDS03-AC-005 | Supplier artboards use the Website shell and BDS-DES-15 alone uses the internal Desk shell; neither shell exposes the other's navigation or authority. |
| BDS03-AC-006 | Registration creates an organisation Account only. A single-organisation or joint-venture arrangement is created for the exact Tender during Start bid and never as a Tender-free registration fact. |
| BDS03-AC-007 | The Submit page visibly shows the trusted current server time with EAT and never presents the browser clock as authority. |
| BDS03-AC-008 | BDS-DES-13-CLOSED uses a dedicated already-submitted, post-deadline fixture; it never uses a never-submitted late-attempt fixture to prove a valid receipt. |
| BDS03-AC-009 | A new Account remains Pending verification until the configured communication challenge succeeds; the complete registration and Account artboards cover that transition explicitly. |
| BDS03-AC-010 | A Suspended Account cannot start, edit, submit, replace or withdraw, while existing receipts remain reachable through an authorised recovery route. |
| BDS03-AC-011 | `BDS_IDEMPOTENCY_CONFLICT` and `BDS_REPLACEMENT_CONFLICT` each have a deterministic common state, exact message, safe action and isolated fixture. |
| BDS03-AC-012 | Cross-organisation denial, definitive custody failure, uncertain custody and late submission each have exact actors, times and safe correlation/support facts sufficient for deterministic rendering and testing. |
| BDS03-AC-013 | Every supplier artboard and dialog has a 390 × 844 px derivative in which grids stack and table rows become labelled cards without losing values or actions; BDS-DES-15 obeys the equivalent Desk rule. |
| BDS03-AC-014 | A receipt shows `received_at` and `accepted_at` as separately labelled EAT instants and never collapses them into one ambiguous Received value. |
| BDS03-AC-015 | Every price row labels its pre-tax line amount unambiguously; tax and Bid total are separately labelled once in the totals panel. |
| BDS03-AC-016 | The withdrawal dialog labels the required reason and visibly states the 10–500 character rule before submission. |
| BDS03-AC-017 | **Submit bid** is the single visible terminal action label on the page and confirmation dialog; the consequence explains that digital signing occurs. |
| BDS03-AC-018 | Rejected-evidence and addendum-change review failures use separate isolated BDS-DES-11 variants and never combine independent reset fixtures into one state. |

### 14.10 Residual artboard-boundary acceptance

| ID | Acceptance criterion |
|---|---|
| BDS04-AC-001 | Opening or viewing Review creates no business fact and never changes an Updated or Last updated timestamp; the primary Draft continues to show David's 13:50 save. |
| BDS04-AC-002 | **View receipts**, **Refresh**, **View current receipt**, **Choose another file** and **Back to Account** each have exactly one §11 mapping; `/account/receipts` is the explicit read-only recovery route for authorised access to existing receipts. |
| BDS04-AC-003 | List and summary surfaces derive **Submitted** from `accepted_at` and omit seconds without rounding; the authoritative receipt shows `received_at` and `accepted_at` separately to the second. |
| BDS04-AC-004 | Every §10.18 inventory row is incomplete until its base artboard, variants and dialogs are rendered at both the listed desktop and 390 × 844 sizes. |
| BDS04-AC-005 | Both pending-verification surfaces use the exact control label **Resend verification link**, and **Back to Account** is a mapped read-only navigation action. |
| BDS04-AC-006 | **Review and submit** is Complete only when server-derived readiness for the exact current definition has no Must fix issue; opening Review alone never changes status or time. |

## 15. Implementation and verification constraints

### 15.1 Required implementation order

Implementation shall proceed in this order:

1. approve the current-law and production operating profile in §5.10;
2. encode and verify the released `IT-EQUIPMENT-OPEN-V1` definition units, mappings and exact supported renderer profile under §4.4;
3. implement the publication-time definition builder and block every incomplete, hidden or unsupported definition;
4. publish the immutable Tender-to-bid definition and bidder-safe read projections;
5. implement organisation isolation, responsibilities and Account controls;
6. implement the five-task Goods/IT Draft workspace and deterministic server validation;
7. implement evidence scanning, tender-security treatment and addendum acknowledgement/migration;
8. integrate the approved trust service, trusted time and tender-box custody service;
9. implement receipt, uncertain-result reconciliation, replacement, withdrawal and automatic close;
10. implement the sealed Bid Opening handoff; and
11. release only after the tests and gates below pass.

A prototype may stop after step 7 only if every surface is labelled **Test environment — bids are not submitted** and the production **Submit bid** action is absent.

### 15.2 Mandatory automated verification

The test suite shall prove at least:

- the exact released STD/Tender inputs deterministically materialise the same ordered definition, human-readable Tender content and downstream mappings;
- every response, evidence, declaration and price/schedule row has one stable published identity, valid supported type and visible source obligation;
- an unknown template family, renderer Version, composition, response type or named rule blocks publication/start without a generic fallback or partial workspace;
- bidder saves are rejected for unknown, hidden, inapplicable, removed or client-invented response identities and options;
- addendum migration uses explicit unchanged/changed/removed/new mappings and never label, position or text-similarity matching;
- cross-organisation and cross-Tender reads, writes, evidence access and identifier guessing are denied;
- page opens, retries and repeated seed runs create no duplicate business facts;
- every response is checked against the exact published definition and stale versions are rejected;
- issued addenda update the effective deadline, require acknowledgement where configured and never silently rewrite a Draft;
- evidence type, size, malware and availability outcomes are enforced without leaking filenames or content;
- tender-security upload and physical-original receipt are distinct facts, and an absent physical receipt does not falsify electronic receipt;
- all server-calculated totals, rounding and currency rules reproduce the published schedule exactly;
- valid, expired, revoked, wrong-person, wrong-organisation, wrong-package and unavailable digital-signature outcomes behave as specified;
- arrival immediately before, at and after the deadline uses trusted server time and one defined boundary rule;
- tender-box acceptance, definite rejection, timeout/uncertain result and later reconciliation each produce exactly one lawful outcome;
- identical idempotent replay returns one receipt while changed content under the same key is rejected;
- two concurrent final submissions cannot create two current Versions;
- replacement is atomic and cannot invalidate the current submission before successor acceptance;
- withdrawal is pre-deadline, acknowledged and preserves all evidence;
- automatic close excludes unsubmitted Drafts and cannot be overridden by business or technical users;
- pre-opening business and technical surfaces, logs, search, analytics, backups and exports reveal no prohibited bid content;
- the Bid Opening handoff contains the exact closed-box lineage but no BDS open/decrypt capability; and
- every §13 fixture produces the stated screen, state, receipt or rejection.

### 15.3 Security, custody and recovery verification

Before production use, an independent competent reviewer shall approve the threat model, organisation isolation, signature binding, certificate validation, key custody, encryption at rest and in transit, tender-box design, three-credential opening compatibility, trusted-time dependency, secrets handling, immutable evidence, logging redaction, backup confidentiality, incident response, reconciliation and disaster recovery. Penetration tests shall include cross-tenant access, object-reference guessing, upload abuse, race conditions, deadline manipulation, replay, forged callbacks, privilege escalation and pre-opening disclosure.

Recovery exercises must show that an uncertain submission is reconciled from the same correlation and never blindly sent as a second bid. Restoring from backup must preserve receipt uniqueness, Version lineage, withdrawal status, automatic-close evidence and the prohibition on pre-opening access.

### 15.4 Legal and operating-model gates

Before production **Submit bid** is enabled, the Project Owner shall hold recorded approval of:

- the current consolidated legal and regulatory position, including any operative e-procurement directions;
- the exact role of KenTender relative to the authorised government system and State Portal;
- the approved signature/trust chain and certificate-validation service;
- the approved electronic tender-box, custody, opening-credential and bidder-encryption treatment;
- the authoritative receipt, deadline/time source and uncertain-result reconciliation contract;
- the handling of original physical tender security and any lawful disqualification decision owner;
- the applicable data-protection, retention, incident and support controls; and
- end-to-end evidence from a production-equivalent certification environment.

An unresolved gate disables production submission; it is not a warning that staff may override.

### 15.5 Usability and accessibility verification

Representative suppliers—including a first-time public-sector bidder, a user on a small screen and a keyboard-only user—shall complete the primary fixture without being taught internal KenTender concepts. The moderated test must establish that users can:

1. distinguish registration from qualification;
2. find the effective deadline and current addendum;
3. understand the five tasks and the next incomplete item;
4. distinguish saving from submitting;
5. identify who may sign and submit;
6. understand the physical tender-security status without mistaking it for bid receipt;
7. recognise the authoritative submission receipt; and
8. replace or withdraw a bid without believing the existing bid has already disappeared.

No required task may depend on a tooltip, colour alone, institutional jargon or knowledge of schemas, packages, custody internals or cryptography. Findings that cause a user to miss the deadline, submit the wrong bid, misunderstand receipt or expose content are release blockers.

### 15.6 Release evidence

The release record shall link the approved operating profile, current-law confirmation, traceability from every acceptance criterion to tests, seed verification, accessibility report, representative-user findings, security review, penetration report, recovery exercise, production-equivalent integration evidence and approval of all unresolved exceptions. A screen mock-up, happy-path demonstration or locally generated receipt is not sufficient release evidence.

## 16. Prohibited shortcuts

The implementation shall not:

- make a completed Tender PDF, spreadsheet, ZIP or free-form upload the primary bid;
- parse the issued Tender PDF or office document at runtime to discover bidder fields or validation;
- expose a generic schema, form, clause, insertion-point or validation-rule editor to Procurement Officers or bidders;
- execute arbitrary metadata expressions, client scripts or unreviewed conditions from a template;
- fall back to a raw-schema screen, partial workspace or Goods renderer when a definition/profile is unsupported;
- treat fitting the primitive control allowlist as sufficient approval for a new Goods, Works or Services product;
- expose a schema, manifest, renderer, field key, digest, storage path or cryptographic identifier to the bidder;
- treat Account creation, certificate upload or registry evidence as prequalification or eligibility approval;
- collect a criterion, weight, requirement, price row or declaration absent from the published Tender;
- let the bidder or staff edit server-derived totals or published content;
- provide **Mark as submitted**, **Mark as signed**, **Open bid**, staff deadline override or client-clock authority;
- equate save, validation, upload, signature initiation, queueing or an internal database row with accepted submission;
- implement a homemade certificate authority, signature, encryption or electronic tender box;
- store submitted content in plaintext logs, search indexes, analytics, traces, notifications or support exports;
- reveal pre-opening supplier identity, bid count, price, filenames or content to Procuring Entity users;
- invalidate the current submitted Version while a replacement is only being prepared or confirmed;
- delete a submitted envelope, receipt, signature or history on withdrawal;
- infer a government-portal, certifying-agency or custody integration that has not been approved and tested;
- accept an unsupported password-protected bidder package; or
- enable production submission while any §15.4 gate remains unresolved.

## 17. Normative and source references

This contract shall be interpreted with:

- the Public Procurement and Asset Disposal Act, 2015, especially the tendering and electronic-submission provisions applicable to the procurement;
- the Public Procurement and Asset Disposal Regulations, 2020, including Regulations 49, 51, 53, 55 and 57–59 as applicable;
- the Kenya Information and Communications Act and applicable rules for advanced electronic signatures and licensed electronic certification services;
- the Data Protection Act, 2019;
- LAW-REG-001 v1.1 for identified legal corrections, currency limitations and release gates;
- TPR-CHG-001 v0.8 for the Published Tender and addendum boundary;
- STD-TPL-001 v0.6 for the approved `IT-EQUIPMENT-OPEN-V1` supplier response content;
- AUTH-ADR-001 v1.7 for authentication, responsibility and segregation-of-duty foundations; and
- KT-STD-001 v1.6 for document, artboard, interaction and verification rules.

The locally available 2020 Regulations text is a historical official source, not proof of the consolidated law or current government operating directions on 18 September 2026. The responsible legal and institutional owners must verify the current position before production approval. This document does not assert that KenTender is an authorised government e-procurement system or that any named integration presently exists.

## 18. Approval effect

This document is **Proposed for Project Owner review**. Approval will:

1. establish it as the canonical Supplier Portal and Electronic Bid Submission contract for the stated product;
2. authorise implementation against §§1–16 and the register in §19;
3. establish the §4.4 STD-derived definition/renderer boundary and the rule that every future product family requires its own approved release/profile;
4. retire v0.3 and all earlier bidder-workspace versions as implementation authority while retaining them only as reference history; and
5. leave production submission disabled until every §15.4 gate is independently satisfied and recorded.

Approval of this document is not approval of a production electronic-procurement operating profile, legal compliance, an integration, a trust service or an electronic tender box.

## 19. Full reimplementation register

The following 124-row register is the minimum reimplementation scope: 90 retained v0.1 rows, 10 retained v0.2 STD-generation/product-profile rows, 18 retained v0.3 consistency/recovery rows and 6 v0.4 residual-boundary rows. **Completion evidence** means tested, reviewable evidence; a mock-up or assertion is insufficient.

### 19.1 Public access, Account and scope

| ID | Required implementation | Contract | Completion evidence |
|---|---|---|---|
| BDS01-IMP-001 | Provide one public **Tenders** list with search, closing filter, deadline, method, category and **View Tender**; a public read creates no supplier or bid fact. | §§2, 5.1, 10.2 | Public-route and no-side-effect tests; BDS-DES-01. |
| BDS01-IMP-002 | Provide one public Tender overview with authoritative deadline in EAT, current addenda, documents, eligibility summary and **Start bid**. | §§3, 5.1, 10.3 | Projection/version tests; BDS-DES-02. |
| BDS01-IMP-003 | Route unauthenticated **Start bid** through sign-in/registration and return to the same Tender without creating a workspace prematurely. | §§5.1, 11.2 | Redirect and duplicate-prevention tests. |
| BDS01-IMP-004 | Implement supplier-organisation registration with legal name, registration number, KRA PIN, contact and address; label all data self-declared until separately verified. | §§4.1, 10.4 | Validation, duplicate and copy review; BDS-DES-03. |
| BDS01-IMP-005 | State plainly that registration creates portal access and is not prequalification, eligibility approval or assurance of award. | §§2.3, 5.2, 10.4 | Content assertion and representative-user test. |
| BDS01-IMP-006 | Implement a supplier **Account** area for organisation facts, users, responsibilities and signature readiness without exposing technical certificate internals. | §§4.1–4.2, 10.5 | Permission and artboard tests; BDS-DES-04. |
| BDS01-IMP-007 | Limit supplier-side responsibilities to Supplier Representative and Authorised Signatory; enforce active, time-bounded assignments. | §§4.2, 6 | Authorisation matrix and boundary-time tests. |
| BDS01-IMP-008 | Require separate users for preparation and final signature where the approved segregation policy requires it; never permit technical staff to assume supplier authority. | §§6, 12.3 | Segregation and impersonation tests. |
| BDS01-IMP-009 | Support one single-entity or permitted joint-venture/association arrangement with disclosed members and one authorised signatory authority. | §§2.2, 4.3, 5.2 | Arrangement validation and fixture tests. |
| BDS01-IMP-010 | Enforce supplier-organisation, arrangement and Tender isolation on every read, write, file and command. | §§5.11, 12.3 | Cross-tenant penetration tests. |
| BDS01-IMP-011 | Make external registry/certificate verification truthful: use only approved interfaces and otherwise show supplier-provided evidence without a verified claim. | §§3, 5.2 | Adapter-contract and no-integration variant tests. |
| BDS01-IMP-012 | Provide one **My bids** queue showing Tender, deadline, status, task progress and one next action, with no large dashboard cards or internal lifecycle labels. | §§9, 10.6 | BDS-DES-05 and usability test. |

### 19.2 Published definition and workspace

| ID | Required implementation | Contract | Completion evidence |
|---|---|---|---|
| BDS01-IMP-013 | Generate one immutable `PublishedBidDefinition` from the exact published Tender/template release, including product profile, response, evaluation and contract mappings. | §§3, 4.4.1–4.4.4 | Release-generation, immutability and mapping tests. |
| BDS01-IMP-014 | Keep the published definition internal; do not expose a manifest, schema, renderer, field key or rule identity to bidders. | §§3, 10.1, 16 | HTML/API/accessibility-output scan. |
| BDS01-IMP-015 | Create at most one active workspace for one Tender and supplier arrangement using an idempotent **Start bid** command. | §§4.5, 5.1, 5.11 | Concurrent-start and replay tests. |
| BDS01-IMP-016 | Store the exact published-definition version and addendum state used by the Draft and each submitted Version. | §§4.5, 4.9 | Persistence and lineage tests. |
| BDS01-IMP-017 | For `IT-EQUIPMENT-OPEN-V1`, present exactly five visible tasks: documents/addenda; company/declarations/security; requirements/evidence; price; review/submit. | §§1, 5.3, 9, 10.7 | BDS-DES-06 and navigation assertions. |
| BDS01-IMP-018 | Show one clear next action plus section status; link every readiness issue to the exact field or task that resolves it. | §§5.5, 10.7, 10.12 | Error-link and first-time-user tests. |
| BDS01-IMP-019 | Save section Drafts independently without calling them submitted, accepted, signed or received. | §§1, 5.5, 11.4 | State-transition and terminology tests. |
| BDS01-IMP-020 | Retain stable response identifiers through preparation, opening, evaluation and contract handoff; prevent bidders from adding unpublished criteria or price rows. | §§4.4, 4.6, 5.3 | Referential-integrity and malicious-request tests. |
| BDS01-IMP-021 | Render the issued Tender PDF and schedules as reference downloads, never as the primary response surface. | §§2.1, 5.3, 10.8 | UI and endpoint tests. |
| BDS01-IMP-022 | Provide short, structured supporting detail with progressive disclosure; keep task names, labels and help in ordinary bidder language. | §§10.1, 15.5 | Content review and representative-user test. |
| BDS01-IMP-023 | Reuse eligible Account facts and evidence only by copying an explicit immutable snapshot into the bid; later Account changes do not alter a submitted Version. | §§4.6–4.7, 5.3 | Snapshot and mutation tests. |
| BDS01-IMP-024 | Reject a Draft command against a withdrawn, cancelled, closed, wrong-Tender or superseded definition. | §§5.1, 5.11, 8 | State/definition mismatch tests. |
| BDS02-IMP-001 | Encode `IT-EQUIPMENT-OPEN-V1` as one code-owned released product profile containing the reviewed tasks, groups, response rows, evidence rules, declarations, schedules, validation and downstream mappings. | §§4.4.1–4.4.3 | Released-bundle inventory, source coverage and mapping review. |
| BDS02-IMP-002 | Implement one deterministic publication-time definition builder from exact template/Tender/Requisition/addendum inputs; freeze the definition atomically with publication. | §§4.4.4, 7.4 | Repeat-build, ordering, identity, package-binding and transaction tests. |
| BDS02-IMP-003 | Validate before publication that every obligation is visible in the Tender, every editable field has a consumer, every mapping target exists and every schedule/price fact reconciles. | §§4.4.2, 4.4.4 | Missing-source, hidden-obligation, orphan-field, broken-mapping and mismatch tests. |
| BDS02-IMP-004 | Maintain a code-owned registry resolving exact template family/release/renderer Version to an approved product profile; block unknown combinations with no fallback. | §§4.4.3, 7.4, 8 | Registry, unsupported-Version and no-partial-workspace tests. |
| BDS02-IMP-005 | Render only supported definition units through shared approved controls and the Goods/IT composition profile; expose no generic schema or runtime form editor. | §§4.4.2–4.4.5, 10 | Component allowlist, UI snapshot and schema-leakage tests. |
| BDS02-IMP-006 | Revalidate every save server-side against the exact Draft definition, including type, option, applicability, calculation, evidence and record Version. | §§4.4.5, 7.4 | Tampering, stale, hidden, inapplicable and invented-value tests. |
| BDS02-IMP-007 | Implement conditional applicability through reviewed named rules only; update completeness/final packaging correctly while retaining Draft audit history. | §§4.4.2, 4.4.5 | Controlling-response and audit-history tests. |
| BDS02-IMP-008 | Require explicit addendum identity maps and migrate only unchanged or expressly converted responses; surface every affected item for review. | §§4.4.6, 5.4, 7.4 | Unchanged/changed/removed/new and no-heuristic-migration tests. |
| BDS02-IMP-009 | Keep the issued PDF outside the runtime generation path; prove the bidder UI and server validation can be reproduced from the released definition without parsing the document. | §§4.4.1, 4.4.7, 16 | Dependency scan and definition-only reconstruction test. |
| BDS02-IMP-010 | Gate every future Goods, Works or Services product on its own curated STD release, renderer profile, deterministic fixtures, complete artboards and product acceptance evidence. | §4.4.7 | New-product admission checklist and negative attempt to use the Goods profile for Works. |

### 19.3 Bid content, evidence, security and price

| ID | Required implementation | Contract | Completion evidence |
|---|---|---|---|
| BDS01-IMP-025 | Capture the baseline company forms, bidder information, declarations, code-of-ethics commitments and permitted joint-venture facts as structured responses. | §§4.6, 5.3, 10.9 | Published-definition coverage and fixture tests. |
| BDS01-IMP-026 | Capture all 11 published technical requirements as direct structured responses with applicable supporting evidence. | §§5.3, 10.10, 13.3 | Row-count, stable-ID and response tests. |
| BDS01-IMP-027 | Capture the six published warranty/support commitments and the required comparable-contract evidence without imposing invented three- or five-year options. | §§4.4, 5.3, 10.10 | Definition-driven option and fixture tests. |
| BDS01-IMP-028 | Render choice, number, date, text, table and evidence controls only from approved typed definitions through the exact product profile; reject unrecognised types, components or options safely. | §§4.4.2–4.4.5, 4.6 | Renderer allowlist and invalid-definition tests. |
| BDS01-IMP-029 | Implement evidence upload with published type/size rules, server-side malware scan, safe storage and immutable accepted-file identity. | §§4.7, 5.3, 7, 8 | Clean/infected/timeout/oversize/type tests. |
| BDS01-IMP-030 | Keep an evidence item unavailable to the bid until scan acceptance; a rejected or unavailable file cannot satisfy readiness. | §§4.7, 5.3 | Asynchronous-state and readiness tests. |
| BDS01-IMP-031 | Show bidder-friendly filename, document purpose, scan status and replacement action; hide digest, bucket, path and scanner internals. | §§4.7, 10.10, 16 | Render/API redaction tests. |
| BDS01-IMP-032 | Implement exact-evidence replacement before submission while retaining audit lineage and preventing mutation of evidence already bound to a Version. | §§4.7, 12 | Replacement and immutability tests. |
| BDS01-IMP-033 | Capture tender-security instrument facts and electronic proof separately from receipt of the physical original. | §§4.8, 5.4, 10.9 | Domain and UI separation tests. |
| BDS01-IMP-034 | Provide the authorised PE receipt owner a minimal Desk surface to record the original instrument reference, receipt time and receiving officer without bid-content access. | §§6, 7, 10.16 | Permission tests; BDS-DES-15. |
| BDS01-IMP-035 | Show the supplier the truthful physical-security receipt status and reference; absence warns but does not block or falsify electronic bid receipt. | §§5.4, 10.9 | Receipt-present/absent variants. |
| BDS01-IMP-036 | Leave any disqualification consequence of missing/invalid tender security to the lawful downstream decision owner; BDS records facts only. | §§3, 5.4 | No-auto-decision and handoff tests. |
| BDS01-IMP-037 | Render the exact published price lines, quantity, unit and KES currency; make published quantities and line identities read-only. | §§4.6, 5.3, 10.11 | Schedule-fidelity tests. |
| BDS01-IMP-038 | Calculate subtotals, tax and total on the server under one rounding rule and reproduce 250 × KES 160,000 plus KES 6,400,000 tax = KES 46,400,000 in the seed. | §§5.3, 10.11, 13.3 | Independent total/rounding tests. |
| BDS01-IMP-039 | Prevent a client, import or API caller from writing derived totals, currency or unpublished price rows. | §§5.3, 16 | Tampering and mass-assignment tests. |
| BDS01-IMP-040 | Store declaration text/version, response value, confirmer and time so the final signatory can review the exact statements being signed. | §§4.6, 12.2 | Versioning and audit tests. |
| BDS01-IMP-041 | Implement deterministic section validation from the same published rules used for readiness; UI and server may not disagree. | §§5.5, 7 | Contract and parity tests. |
| BDS01-IMP-042 | Ensure validation messages identify what the bidder must do and where, without revealing evaluation scoring or internal rule keys. | §§5.5, 8, 10.17 | Copy review, field-link and leakage tests. |

### 19.4 Addenda, clarifications and readiness

| ID | Required implementation | Contract | Completion evidence |
|---|---|---|---|
| BDS01-IMP-043 | Consume issued addenda and clarification answers from Tenders through an immutable bidder-safe projection; BDS cannot author them. | §§3, 5.4, 10.8 | Owner-boundary and projection tests. |
| BDS01-IMP-044 | Display current deadline and addendum effect everywhere from one authoritative value; never retain a stale date in the workspace or receipt flow. | §§5.4, 5.9 | Addendum propagation tests. |
| BDS01-IMP-045 | Require acknowledgement of every issued addendum configured as acknowledgement-required, with actor and trusted time. | §§5.4, 12.2 | Acknowledgement and readiness tests. |
| BDS01-IMP-046 | Detect an addendum that changes the response definition; preserve prior values where valid and require explicit review of every affected response. | §§4.5, 5.4 | Compatibility and affected-response tests. |
| BDS01-IMP-047 | Never rewrite a Draft, price or submitted Version silently when an addendum is issued. | §§5.4, 5.11 | Mutation and immutable-Version tests. |
| BDS01-IMP-048 | Coordinate bidder clarification submission with the Tenders owner so the supplier uses one governed Tender thread and receives published answers without bid-content leakage. | §§3, 5.4 | Cross-module contract and access tests. |
| BDS01-IMP-049 | Calculate readiness on the server from current definition, required responses, evidence, declarations, price, addenda, arrangement and signatory authority. | §§5.5, 7 | Complete/incomplete/stale fixtures. |
| BDS01-IMP-050 | Present one review page with the five task summaries, total, signatory, physical-security fact and exact issue links. | §§10.12, 11.5 | BDS-DES-11 and accessibility tests. |
| BDS01-IMP-051 | Keep **Submit bid** absent or disabled until readiness and production operating-profile conditions are satisfied; explain the bidder-resolvable reason. | §§5.5, 5.10, 10.12 | Permission/profile/readiness variants. |
| BDS01-IMP-052 | Recheck every readiness fact in the final server transaction; never trust a previously rendered green status. | §§5.7, 14.5 | Race and stale-client tests. |

### 19.5 Signature, deposit and receipt

| ID | Required implementation | Contract | Completion evidence |
|---|---|---|---|
| BDS01-IMP-053 | Approve and configure one real production electronic-procurement operating profile covering authority, portal role, receipt, trust, custody, time and recovery. | §§5.10, 15.4 | Signed profile and production-equivalent evidence. |
| BDS01-IMP-054 | Integrate an approved licensed digital-signature/trust service; bind the signatory, supplier arrangement, Tender, Version and exact canonical package. | §§5.7, 7, 12 | Valid-signature and package-binding tests. |
| BDS01-IMP-055 | Validate certificate chain, purpose, person, organisation, validity and revocation under the approved profile immediately before deposit. | §§5.7, 15.2 | Expired/revoked/wrong-identity tests. |
| BDS01-IMP-056 | Reject typed names, signature images, checkboxes, passwords, staff overrides and client flags as substitutes for the required digital signature. | §§5.7, 16 | Negative signature tests. |
| BDS01-IMP-057 | Present a plain-language **Submit bid** confirmation stating the Tender, supplier, total, deadline and that the bid will be signed, locked and placed in the tender box—not opened or evaluated. | §§5.7, 10.13 | BDS-DES-12 and comprehension test. |
| BDS01-IMP-058 | Assemble the canonical package only from current server-held responses and accepted evidence; perform no hidden large upload in the final transaction. | §§4.9, 5.7 | Package determinism and timing tests. |
| BDS01-IMP-059 | Check the complete signed request against trusted server time and the effective deadline in the committing flow; browser time and dialog-open time have no authority. | §§5.7, 5.9 | Boundary and clock-manipulation tests. |
| BDS01-IMP-060 | Deposit through the approved tender-box custody service and create Submitted state only from authoritative acceptance of that exact signed envelope. | §§4.9–4.10, 5.7 | Accepted/rejected/correlation tests. |
| BDS01-IMP-061 | Use one idempotency key and correlation per submission attempt; identical replay returns the original outcome and changed payload replay is rejected. | §§5.7, 7 | Retry and collision tests. |
| BDS01-IMP-062 | Treat a timeout or indeterminate callback as **Submission being confirmed**, block duplicate dispatch and reconcile the same correlation to one final outcome. | §§5.10, 8, 10.17 | Uncertain-result and recovery exercise. |
| BDS01-IMP-063 | Generate the bidder receipt only from authoritative accepted custody evidence and show reference, Tender, supplier, Version, accepted time in EAT, deadline, status and replacement lineage. | §§4.10, 10.14 | Receipt contract and BDS-DES-13. |
| BDS01-IMP-064 | Omit hashes, keys, certificate internals, schemas, database IDs, paths and encryption details from the receipt; state that receipt is not opening, evaluation or award. | §§4.10, 10.14 | Receipt snapshot and leakage tests. |

### 19.6 Replacement, withdrawal, close and handoff

| ID | Required implementation | Contract | Completion evidence |
|---|---|---|---|
| BDS01-IMP-065 | Provide **Prepare replacement** before deadline by copying an authorised working snapshot while the current submitted Version remains effective and sealed. | §§5.8, 10.15 | BDS-DES-14 and current-Version tests. |
| BDS01-IMP-066 | Require the replacement to pass the same readiness, signature, deadline and custody rules as an initial submission. | §§5.7–5.8 | Replacement negative-path tests. |
| BDS01-IMP-067 | Mark the old Version Superseded and the new one current only in the same atomic outcome that records tender-box acceptance and the new receipt. | §§4.9, 5.8 | Transaction/failure-injection tests. |
| BDS01-IMP-068 | If replacement fails, is abandoned or misses the deadline, preserve the prior current Version and receipt unchanged. | §§5.8, 14.6 | Failure and deadline tests. |
| BDS01-IMP-069 | Provide **Withdraw bid** only to the active Authorised Signatory before deadline, with current Version, reason and explicit confirmation. | §§4.11, 5.8, 10.15 | Permission, concurrency and boundary tests. |
| BDS01-IMP-070 | Produce an electronic withdrawal acknowledgement and preserve envelope, signature, receipt and full lineage; withdrawal never deletes evidence. | §§4.11, 5.8, 12 | Acknowledgement and retention tests. |
| BDS01-IMP-071 | Permit a withdrawn arrangement to submit a new Version before deadline under the same full controls and new receipt. | §§5.8, 14.6 | Withdraw-then-resubmit fixture. |
| BDS01-IMP-072 | Close the electronic tender box automatically at the effective deadline; no business, administrator or technical role can reopen, extend or backdate it. | §§5.9, 16 | Scheduled-close and privilege tests. |
| BDS01-IMP-073 | Mark never-submitted Drafts **Closed without submission** and exclude them from the opening inventory. | §§4.5, 5.9 | Close and inventory tests. |
| BDS01-IMP-074 | Build a sealed Bid Opening handoff containing closed-box identity, deadline evidence, envelope identities, receipts, replacement/withdrawal lineage and custody proofs only. | §§3, 5.9, 12.3 | Handoff schema and access tests. |
| BDS01-IMP-075 | Keep every open/decrypt/inspect operation outside BDS and subject to the separately governed opening ceremony and credentials. | §§2.3, 5.9 | Capability and permission review. |
| BDS01-IMP-076 | Resolve the current lawful bidder-controlled encryption/password treatment in the operating profile; do not accept unsupported encrypted uploads. | §§5.10, 15.4, 16 | Approved decision and interoperability tests. |

### 19.7 Confidentiality, audit, UX and release

| ID | Required implementation | Contract | Completion evidence |
|---|---|---|---|
| BDS01-IMP-077 | Prevent Procuring Entity business users from seeing pre-opening bidder identity, bid count, prices, responses, filenames or evidence content. | §§5.9, 12.3 | Role/API/UI/side-channel tests. |
| BDS01-IMP-078 | Restrict technical operators to authorised service and custody metadata; prohibit decrypt, render, download, export and content search. | §§6, 12.3 | Technical-role penetration tests. |
| BDS01-IMP-079 | Exclude Draft and submitted values from logs, traces, analytics, search indexes, alerts, emails and support exports. | §§12.3, 16 | Observability and data-flow inspection. |
| BDS01-IMP-080 | Protect submitted content and backups using the independently approved custody design; keep private keys and production secrets out of application data, code, configuration and fixtures. | §§12.3, 15.3 | Architecture review, secret scan and recovery test. |
| BDS01-IMP-081 | Record the minimum event and business evidence for Account changes, responses, files, addenda, validation, security receipt, signature, deposit, replacement, withdrawal and close. | §§12.1–12.2 | Audit completeness and immutability tests. |
| BDS01-IMP-082 | Implement all 16 artboards and every isolated state from the self-contained §10 design contract at both §10.18 render sizes, using KT-STD-001 v1.6 §2. | §§10–11 | Desktop/narrow artboard inventory and visual acceptance. |
| BDS01-IMP-083 | Provide keyboard operation, visible focus, programmatic labels, status text independent of colour, error summary links and usable small-screen reflow. | §§10.1, 11.8 | Accessibility audit and device tests. |
| BDS01-IMP-084 | Map every visible action to exactly one service/command and omit it when not server-permitted; page refresh must reproduce authoritative state. | §11 | Action-map and stale-client tests. |
| BDS01-IMP-085 | Use the §13 deterministic seed for primary, opposing and recovery states; keep simulated signature/custody data unmistakably non-production. | §13 | Repeatable seed and isolation tests. |
| BDS01-IMP-086 | Complete representative-supplier usability tests for registration, task completion, signature, receipt, replacement and withdrawal; treat material misunderstandings as blockers. | §15.5 | Moderated findings and resolved defect log. |
| BDS01-IMP-087 | Complete independent threat modelling, security architecture review, penetration testing and uncertain-result/disaster-recovery exercises. | §§15.2–15.3 | Approved reports and retest evidence. |
| BDS01-IMP-088 | Trace every acceptance criterion in §14 and every register row to an automated, manual, legal, security or usability verification result. | §§14–15 | Complete bidirectional traceability matrix. |
| BDS01-IMP-089 | Keep production **Submit bid** unavailable until current-law, operating-model, portal, trust, custody, time, security and recovery gates are all approved. | §§5.10, 15.4 | Deployment guard and signed approvals. |
| BDS01-IMP-090 | Remove or quarantine earlier bidder-workspace implementation artifacts as non-authoritative so runtime and design tools consume this contract only. | §§18–19 | Repository/content inventory and owner sign-off. |

### 19.8 v0.3 artboard consistency and recovery corrections

| ID | Required implementation | Contract | Completion evidence |
|---|---|---|---|
| BDS03-IMP-001 | Render the primary My bids/workspace only at 10 Jun 2027, 14:20 EAT or later so the 13:50 save and 14:15 read-only review are already true; reject visual fixtures containing future-completed facts. | §§10.6–10.7, 13.3, 14.9 | Chronology assertion across every displayed event and artboard snapshot. |
| BDS03-IMP-002 | Bind every workspace badge and task result to the exact §4.5/§4.6 enum; render counts such as **2 tasks need attention** as supporting text only. | §§4.5–4.6, 10.6–10.7 | Enum-to-copy test and visual review of complete/in-progress variants. |
| BDS03-IMP-003 | Render a received physical tender-security original as a green satisfied fact and reserve the amber Review note for the outstanding-original variant. | §§10.9, 10.12 | Recorded/outstanding paired snapshots and semantic-colour accessibility test. |
| BDS03-IMP-004 | Source common-state messages from the §8 error catalogue or assert exact equality; append fixture context separately without rewriting the canonical message. | §§8, 10.17 | Automated copy equality test for every common-state error. |
| BDS03-IMP-005 | Implement separate supplier Website and internal Desk shells; bind BDS-DES-15 exclusively to `/desk/tender-security-receipts` with no supplier navigation or bid content. | §§9, 10.1, 10.16 | Route-shell snapshots, permission tests and navigation leakage scan. |
| BDS03-IMP-006 | Remove Tender-free JV creation from registration; capture the exact single/JV arrangement only after Start bid identifies the Tender and before workspace creation. | §§4.3, 10.3–10.4, 11.2–11.3 | Registration negative test and permitted/prohibited Tender JV start tests. |
| BDS03-IMP-007 | Return and display trusted current server time on BDS-DES-12 in EAT and recheck it in the committing flow without trusting browser time. | §§5.7, 10.13, 11.1 | Clock-manipulation, refresh and deadline-boundary tests. |
| BDS03-IMP-008 | Seed a submitted Version accepted before deadline and render its receipt after deadline with change actions closed; keep it isolated from the late rejected attempt. | §§10.1, 10.14, 13.4 | BDS-DES-13-CLOSED snapshot and receipt/late-attempt isolation test. |
| BDS03-IMP-009 | Implement Pending verification creation, challenge/resend, successful activation and explicit registration/Account states; activation proves channel control only. | §§4.1, 5.1–5.2, 7.2, 10.4–10.5 | Challenge lifecycle, replay/rate-limit and copy tests. |
| BDS03-IMP-010 | Block every preparation/change command for a Suspended Account while retaining authorised read access to existing receipts. | §§5.2, 8, 10.17 | Command-matrix denial tests and receipt-recovery test. |
| BDS03-IMP-011 | Render deterministic idempotency-conflict and replacement-conflict states with exact §8 messages and non-mutating recovery actions. | §§8, 10.1, 10.17, 13.4 | Conflicting-replay and stale-replacement tests with unchanged original evidence. |
| BDS03-IMP-012 | Seed exact cross-organisation, definitive custody failure, uncertain custody and late submission fixtures with actors, EAT times, correlation/support references and stated no-receipt outcomes. | §§10.1, 13.4 | Seed inventory, cross-tenant redaction, correlation and late-boundary tests. |
| BDS03-IMP-013 | Produce 390 × 844 px derivatives for all supplier artboards/dialogs and equivalent responsive BDS-DES-15 output; reflow tables to labelled cards without dropping data/actions. | §§10.1, 11.8 | Desktop/narrow visual suite, keyboard run and horizontal-overflow assertion. |
| BDS03-IMP-014 | Persist and display tender-box `received_at` and `accepted_at` independently on receipts using the exact fixture instants and EAT labels. | §§4.9–4.10, 10.1, 10.14 | Receipt schema/API/snapshot tests and ordering assertion. |
| BDS03-IMP-015 | Rename the calculated row value to **Line amount before tax** and present subtotal, tax and Bid total once as separately labelled totals. | §§5.6, 10.1, 10.11 | Arithmetic test and one-row/multi-row semantic UI review. |
| BDS03-IMP-016 | Add **Reason for withdrawal** and visible **Enter 10–500 characters** helper; enforce the same rule server-side before `WithdrawBid`. | §§4.11, 10.15, 11.6 | 9/10/500/501-character boundary and accessibility tests. |
| BDS03-IMP-017 | Use **Submit bid** for both terminal controls while retaining the plain-language digital-signature consequence and exact command sequence. | §§5.7, 10.13, 11.5 | Copy/action-map snapshot and representative-signatory comprehension test. |
| BDS03-IMP-018 | Implement separate evidence-attention and addendum-attention BDS-DES-11 variants, each backed by one isolated fixture and one exact issue link. | §§10.12, 10.18, 13.4 | Paired isolated snapshots and fixture-identity assertion. |

### 19.9 v0.4 residual artboard-boundary corrections

| ID | Required implementation | Contract | Completion evidence |
|---|---|---|---|
| BDS04-IMP-001 | Keep `GetBidReview` read-only: show 13:50 as Last updated/Updated for the primary Draft and never stamp Mary's 14:15 view as a mutation. | §§7.1, 10.6–10.7, 11.1, 13.3 | Read-side-effect assertion and paired My bids/workspace snapshots. |
| BDS04-IMP-002 | Map **View receipts**, **Refresh**, **View current receipt**, **Choose another file** and **Back to Account** exactly once; implement `/account/receipts` as an authorised read-only recovery route that grants no bid-change capability. | §§5.2, 9, 10.17, 11.8 | Action-map coverage, Suspended Account receipt read and mutation-denial tests. |
| BDS04-IMP-003 | Derive every list/summary **Submitted** time from `accepted_at`, displayed in EAT to the minute without rounding; retain second precision for both receipt instants. | §§4.9–4.10, 10.3, 10.6, 10.14–10.15, 11.1 | Cross-surface timestamp assertion using 14:32:01 accepted and 14:31:58 received. |
| BDS04-IMP-004 | Track both desktop and 390 × 844 completion for every §10.18 base artboard, named variant and dialog; reject desktop-only inventory completion. | §§10.1, 10.18 | Two-size inventory matrix and visual regression suite. |
| BDS04-IMP-005 | Standardise the control label **Resend verification link** on BDS-DES-03 and BDS-DES-04; map **Back to Account** to a non-mutating Account read. | §§10.4–10.5, 11.3, 11.8 | Copy equality and navigation/no-side-effect tests. |
| BDS04-IMP-006 | Derive the **Review and submit** task as Complete only when the exact current readiness result has no Must fix issue; opening the review changes neither status nor `last_saved_at`. | §§4.5–4.6, 5.3, 10.7, 11.4 | Complete/blocking/Review-note fixtures and repeated-read immutability test. |
