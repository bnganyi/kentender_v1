# TPR-CHG-001 — Tenders: Preparation and Publication

| Control | Value |
|---|---|
| Document ID | TPR-CHG-001 |
| Version | **0.8** |
| Date | 17 September 2026 |
| Status | **Approved** |
| User-facing module | **Tenders** |
| Product | `IT-EQUIPMENT-OPEN-V1` — straightforward off-the-shelf IT equipment using the PPRA Goods Standard Tender Document |
| Starts from | One authorised, unconsumed `AuthorisedRequisitionHandoff v1.3` |
| Ends at | One immutable Tender package that is unpublished, published and open, cancelled, or closed for submission |
| Governing standard | KT-STD-001 v1.6 |
| Owner contracts | REQ v1.9, PLN v1.20, BUD v1.9, NDS v1.13, CFG v0.11, STR v1.8, AUTH v1.7, SEED v1.3, STD-STD-001 v1.1 and STD-TPL-001 v0.6 |
| Implementation authority | Approved for implementation; production release remains subject to the evidence in §§14–15 |

**Controlling decision:** KenTender presents Tender preparation, Head of Procurement Function approval, Accounting Officer publication authorisation, publication confirmation, the open-Tender period, addenda and pre-submission cancellation as stages of one Tender. Users work from one **Tenders** queue and one Tender record. Each statutory or professional decision remains separately attributed, immutable and role-bound. Approval never means publication; in the MVP, actual publication is established only by the named HOPF's accountable confirmation and required evidence for every required channel.

## 1. Governing decision

One Tender is one continuous procurement proceeding. The system shall not require users to move between Tender Preparation and Tender Publication modules, duplicate review of the same package, or interpret an internal handoff.

The routine journey is:

1. A Procurement Officer starts a Tender from one authorised Requisition.
2. The officer completes three visible tasks and submits the exact Tender Version.
3. The Head of Procurement Function returns or approves that Version.
4. The Accounting Officer authorises publication of the same immutable Version.
5. The Head of Procurement Function publishes the approved Invitation and issued Tender through the required channels and confirms each channel with accountable evidence.
6. The Tender becomes **Published — open** only after every required channel is confirmed.
7. While open, governed addenda, related inquiries and cancellation remain part of the same Tender record.
8. At the submission deadline, the Tender becomes **Submission period ended** and passes its immutable package and publication history to the Bid Submission boundary.

The user-facing module name is **Tenders**. **Preparation**, **Approval**, **Publication** and **Open Tender** are stages and statuses, not separate modules.

## 2. Purpose, outcomes and scope

### 2.1 Required outcomes

The module shall:

- consume one authorised Requisition without re-entry;
- bind one immutable code-owned Tender template release;
- preserve every inherited source, item, requirement, service, acceptance, reservation and funding-lineage identifier;
- collect only genuine Tender-specific values through three visible preparation tasks;
- generate the Invitation, issued Tender, supplier-pricing schedule, response schema, evaluation contract and contract-obligation projection;
- obtain one immutable approval from the Head of Procurement Function;
- obtain one separately attributed publication authorisation from the Accounting Officer;
- determine publication channels from governed configuration rather than user choice;
- let the Head of Procurement Function confirm actual publication through each required channel with accountable, channel-appropriate evidence;
- reserve automated channel acknowledgement for a future configured integration whose real interface and authoritative response have been approved and tested;
- record the actual invitation date only when every mandatory publication channel is confirmed;
- support governed addenda and addendum inquiries during the open period;
- support Accounting Officer cancellation and its compliance evidence before the submission boundary; and
- preserve complete audit, decision, document and external-publication evidence.

### 2.2 Included product boundary

- Goods;
- straightforward off-the-shelf IT equipment;
- Open Tender;
- one Procuring Entity implicit from the site;
- one inherited Financial Year;
- Single-year plan horizon;
- one authorised Requisition;
- one award package;
- Single lot;
- KES only;
- fixed-price contract treatment;
- pass/fail technical compliance followed by arithmetic and financial evaluation;
- reservation categories supported by the installed template;
- one Invitation and one complete issued Tender;
- configured publication channels for national Open Tender;
- publication, non-material addenda, addendum-related inquiries and pre-submission cancellation; and
- one actual invitation event written to Planning.

### 2.3 Excluded

- software development, systems implementation, integration, migration or hosting procurements;
- Works, consulting or non-consulting-services products;
- international, restricted, direct, two-stage or request-for-proposals methods;
- multiple lots, multiple award packages or multiple currencies;
- operational template, clause, schema, workflow, channel or evaluation configuration from the Tender UI;
- editing an authorised Requisition inside Tenders;
- Procurement Officer entry of supplier prices or supplier responses;
- weighted-scoring builders or evaluator-created criteria;
- substantive expansion or replacement of published requirements through an addendum;
- bid submission, electronic tender-box custody, tender opening, evaluation, award, contract formation or execution;
- a general-purpose candidate messaging system unrelated to a governed addendum;
- asserting any Planning milestone after the actual invitation date; and
- treating approval, an unsupported integration assumption, an unevidenced assertion or technical record acceptance as proof that publication succeeded.

## 3. Ownership and dependency boundary

| Information or action | Owner | Tenders treatment |
|---|---|---|
| Approved purchase, source allocations, method, schedule boundaries and Strategic objective | Planning / authorised Requisition | Inherit read-only; internal context only where stated. |
| Funding reservation and Budget lineage | Budget / authorised Requisition | Preserve exact reservation/source identities as internal evidence; never render as supplier price. |
| Requirement title, need, expected result, equipment, quantities, delivery, technical requirements, support, services, acceptance and supporting materials | Authorised Requisition | Inherit read-only and generate the Tender schedules and obligations. |
| Reservation category and lotting | Authorised Requisition | Inherit read-only; validate compatibility and render the template rule. |
| Standard wording, forms and render mappings | Installed template release | Bind one immutable release; operational users cannot edit or choose another release. |
| Tender title, dates, security, meeting, supplier evidence and finite contract parameters | Procurement Officer | Enter only through the controls in §5.2. |
| Tender package approval | Head of Procurement Function | Return or approve one immutable Version; cannot edit it. |
| Advertising rule and required channels | Configuration | Resolve from effective-dated configuration and snapshot at publication authorisation. |
| Publication authorisation | Accounting Officer | One explicit decision on the approved immutable Version. |
| Publication through every required channel | Head of Procurement Function | Carry out publication outside KenTender where necessary, then confirm the actual availability time with channel-appropriate evidence and explicit attestation. |
| Future automated acknowledgement | Approved publication adapter | Not an MVP capability. It may replace HOPF confirmation for a channel only after the real interface, authority, acknowledgement and recovery contract are approved, configured and tested. |
| Actual invitation date | Tenders | Set once when every required channel is confirmed; publish once to Planning. |
| Addendum drafting | Procurement Officer or Head of Procurement Function | Draft one structured non-material change against current published content. |
| Addendum issue | Head of Procurement Function | Decide and publish the immutable addendum through the original required channels. |
| Candidate inquiry about an addendum | Bidder-facing service | Supply authenticated inquiry and candidate identity; Tenders records and answers it. |
| Cancellation decision | Accounting Officer | Select a lawful ground, state the circumstances and close the proceeding. |
| Optional cancellation recommendation | Head of Procurement Function | Append recommendation; absence never blocks Accounting Officer decision. |
| Cancellation notices and PPRA-report evidence | Procurement function | Track accountable evidence and deadlines without fabricating external receipt. |
| Bid receipt and submission deadline closure | Bid Submission owner | Tenders publishes the immutable open-proceeding contract and closes its own preparation/publication work. |

All cross-module writes use owner commands or versioned events. Tenders shall not write Planning, Budget, Requisition, Configuration or bidder-service tables directly.

## 4. Canonical domain model

### 4.1 Tender

| Field | Rule |
|---|---|
| `tender_id` | Server-generated immutable identity. |
| `tender_reference` | Server-generated display reference; never editable. |
| `requisition_handoff_id` | Exact authorised handoff; one active Tender consumption at most. |
| `requisition_id`, `requisition_version_id` | Exact immutable source identities. |
| `plan_item_id`, `plan_item_version_id` | Stable item and exact approved content identities. |
| `fiscal_year` | Inherited display fact; never a permission dimension. |
| `product_key` | Fixed `IT-EQUIPMENT-OPEN-V1`. |
| `template_release_id`, `official_source_digest`, `bundle_digest` | Bound when the first Draft is created; immutable for each Version. |
| `current_version_id` | Server-maintained pointer to the current Draft/submitted/approved Version. |
| `overall_status` | Generated from §5.1; never directly set. |
| `published_at` | Null until all mandatory channel confirmations establish publication; immutable afterward. |
| `submission_deadline` | From the current approved/published Version or effective issued addendum. |
| `publication_id` | Null until Accounting Officer publication authorisation creates the publication record. |

One Tender consumes one Requisition handoff. It does not combine Requisitions or split one Requisition into user-configured packages.

### 4.2 TenderVersion

| Field | Rule |
|---|---|
| `tender_version_id` | Server-generated immutable identity. |
| `tender_id` | Owning Tender. |
| `version_number` | Positive integer, sequential per Tender. |
| `status` | `Draft`, `Submitted`, `Returned`, `Approved`, `Stopped for requisition correction`. |
| `predecessor_version_id` | Exact prior immutable Version when a copied successor exists. |
| `requisition_snapshot_digest` | Digest of the complete inherited package. |
| `template_release_id`, `official_source_digest`, `bundle_digest` | Exact bound render release. |
| `officer_payload` | Canonically serialized §5.2 values only. |
| `invitation_digest`, `issued_tender_digest` | Generated from the canonical projection. |
| `response_schema_digest`, `evaluation_contract_digest`, `contract_projection_digest` | Generated downstream contracts. |
| `review_result_digest` | Exact findings and render state reviewed at submission/approval. |
| `prepared_by`, `prepared_at`, `submitted_by`, `submitted_at` | Server-derived audit facts. |
| `approved_by`, `approved_at` | Set only by the Head of Procurement Function approval command. |
| `package_digest` | Digest covering every inherited/officer/generated value and document. |

Submitted, approved and stopped Versions are immutable. Return, reopen and corrected-Requisition continuation create a new Draft Version.

### 4.3 InheritedRequirementSnapshot

The snapshot contains, without re-entry:

- exact Plan Item, Requisition, source allocation and Requisition item identities;
- exact Quantity and Money decimal strings with currency/UOM identity;
- requirement title, business need and expected operational result;
- Strategic objective and Single-year plan horizon as internal-only context;
- method, category, product, reservation category, lotting and award-package facts;
- every equipment item with quantity, unit, intended use, delivery location and latest delivery date;
- every technical requirement with comparison, typed value, unit and applicability;
- every warranty/support value;
- every related service and acceptance check;
- every supporting material with treatment, digest and row links;
- every Budget reservation and source-line identity required for audit; and
- lead-HoD certification and Procurement authorisation evidence.

Inherited facts are rejected in write payloads. Strategic objective, plan horizon, authorised value and funding evidence are visible only to authorised internal readers and are absent from the Invitation, issued Tender and supplier response package.

### 4.4 TenderEvidenceRequirement

| Field | Rule |
|---|---|
| `evidence_requirement_id` | Server-generated. |
| `tender_version_id` | Draft Version only. |
| `label` | Plain text, 3–160 characters. |
| `evidence_type` | `Declaration`, `Certificate`, `Datasheet or brochure`, `Schedule or form`, `Other document`. |
| `linked_requirement_type` | `Item`, `Technical requirement`, `Service`, `Warranty/support`. |
| `linked_requirement_id` | Required exact visible inherited identity. |
| `mandatory` | Boolean. |

The evidence must prove a published inherited requirement. It cannot create a hidden qualification threshold or new technical obligation.

### 4.5 Generated schedules and mappings

For every Version, KenTender deterministically generates:

- goods and delivery schedule;
- related-services schedule;
- supplier pricing schedule;
- supplier response controls;
- fixed evaluation sequence and pass/fail mappings;
- contract-obligation projection;
- Invitation;
- complete issued Tender; and
- one canonical package digest.

Same-specification equipment items may render as one supplier-facing schedule line only when every grouping condition matches. Every contributing Requisition item, source allocation, quantity and reservation identity remains retrievable from that line.

#### 4.5.1 Supplier response schema

The generated supplier response is structured and identified; it is not an upload-only envelope.

| Published content | Required supplier response |
|---|---|
| Each goods line | Offered make/model; quantity; unit price; total price; delivery commitment; linked evidence. |
| Each mandatory technical requirement | `Comply` or `Do not comply`; typed offered value where measurable, otherwise text up to 300 characters; optional comment up to 500 characters; required evidence references when specified. |
| Each related service | Confirmation; offered completion date; price-schedule line; required evidence. |
| Each warranty/support obligation | Confirmation; offered term/value where applicable; service/escalation details; evidence. |
| Each acceptance requirement | Explicit acceptance linked to the resulting contract obligation. |
| Each evidence requirement | One or more permitted evidence references, with mandatory/optional treatment preserved. |

Every response row retains the published stable identifier. The response schema cannot add a criterion that is absent from the published Tender.

#### 4.5.2 Evaluation contract

The generated evaluation contract provides:

- the published eligibility and evidence checklist;
- one pass/fail check for every mandatory technical requirement identity;
- offered typed values and their evidence references;
- arithmetic and price totals from the response schema;
- the fixed governed stage order; and
- no evaluator-created or hidden criterion.

A failure must identify the exact published criterion and a reason. The evaluator cannot change the criterion, weight, comparison or mandatory status.

#### 4.5.3 Contract-obligation projection

The generated contract projection carries the awarded response into identified obligations for:

- each Requisition item, source allocation, quantity and delivery commitment;
- each mandatory technical requirement and accepted offered value;
- each related service and completion date;
- each warranty/support obligation;
- each acceptance requirement;
- each agreed price row; and
- the finite officer-authored contract parameters in §5.2.

No obligation is reconstructed by copying free text from a rendered Tender.

### 4.6 TenderPublication

| Field | Rule |
|---|---|
| `publication_id` | Server-generated immutable identity. |
| `tender_id`, `tender_version_id`, `package_digest` | Exact approved immutable package. One publication authorisation per approved Version. |
| `authorised_by`, `authorised_at` | Accounting Officer decision facts; server-derived. |
| `rule_snapshot_id` | Exact effective publication/advertising rule resolved at authorisation. |
| `threshold_snapshot` | Exact configured value and currency where applicable; internal evidence. |
| `required_channels` | Generated immutable set from the rule snapshot; never user-selected. |
| `publication_status` | `Evidence required`, `Published`, `Withdrawn before confirmation`, `Cancelled`. Authorisation creates the Evidence-required state atomically. |
| `published_at` | Actual Tender-availability instant established after all required channels are confirmed; mathematically the latest `available_at` among those confirmations. It is not the time the final confirmation record was entered. |
| `publication_digest` | Digest covering decision, package, rule snapshot, channels and final evidence. |
| `withdrawn_by`, `withdrawn_at`, `withdrawal_reason` | Set only when no channel has been confirmed and accountable evidence establishes that publication did not occur. |

Publication authorisation commits the Accounting Officer's decision and creates the required channel-confirmation records. It does not claim that publication occurred, call an assumed external interface or make documents public by itself.

### 4.7 PublicationChannelConfirmation

| Field | Rule |
|---|---|
| `channel_confirmation_id` | Server-generated; unique by publication and required channel. |
| `publication_id` | Owning publication. |
| `channel` | One generated required channel from the rule snapshot. |
| `confirmation_mode` | `Evidence based` in MVP. `Integrated acknowledgement` is reserved for the future facility in §5.5.1 and cannot be activated in MVP. |
| `status` | `Awaiting confirmation` or `Confirmed`. |
| `available_at` | Required actual instant the approved documents became available through this channel; supplied in the HOPF attestation. |
| `evidence_reference` | Required publication reference, register entry, placement reference or other channel-appropriate identifier, 1–160 characters. |
| `public_url` | Required for an online channel when a stable public URL exists; otherwise null with the reason captured in notes. |
| `evidence_file_id`, `evidence_digest` | Required for every MVP channel; the supporting file must pass technical validation. |
| `evidence_notes` | Optional plain text, maximum 500 characters. |
| `attestation_text`, `attested_by`, `attested_at` | Exact confirmation statement plus server-derived HOPF identity and time. The actor confirms that the exact approved package was publicly available through the named channel at `available_at`. |
| `package_digest` | Exact approved package being confirmed; must equal the publication package digest. |
| `record_version` | Optimistic-concurrency token. |

KenTender validates record completeness, field formats, actor authority, package/channel identity, file integrity, malware-scan result, duplicate/conflicting confirmation and applicable channel rules. It does **not** independently prove that a website, notice board or newspaper was publicly available. That factual confirmation is the named HOPF's accountable attestation supported by the recorded evidence.

### 4.8 Addendum

| Field | Rule |
|---|---|
| `addendum_id`, `addendum_number` | Server-generated; sequential per Tender. |
| `tender_id`, `publication_id` | Exact published Tender. |
| `status` | `Draft`, `Awaiting issue`, `Awaiting publication confirmation`, `Issued`. |
| `change_class` | `Administrative clarification`, `Non-material correction`, `Submission deadline extension`. |
| `affected_area` | `Invitation detail`, `Technical requirement`, `Goods/delivery schedule`, `Submission or opening detail`, `Evaluation or contract term`, `Other stated location`. |
| `affected_reference` | Exact current published row, section and paragraph, or generated schedule line. |
| `previous_value` | Exact current published value; server-verifiable. |
| `revised_value` | Exact proposed value. |
| `reason` | Required, 20–1,000 characters. |
| `materiality_statement` | Required explanation of why the change does not expand or substantially alter the procurement. |
| `deadline_extension_required` | Generated from issue timing and the applicable rule. |
| `revised_submission_deadline` | Required when the applicable rule requires extension; must be later than the current deadline and pass the rule check. |
| `drafted_by`, `drafted_at`, `issued_by`, `issued_at` | Server-derived; issue authority is Head of Procurement Function. |
| `addendum_digest` | Covers content, affected published baseline, decision and resulting deadline. |

An addendum is append-only. It never edits the approved Tender Version. A proposed change to quantity, authorised value, method, reservation, lotting, award package, substantive technical requirement or evaluation basis is rejected and follows cancellation/new-Tender governance.

Each issued addendum creates channel-confirmation records under the same required-channel set as the original publication. It becomes **Issued** only when the HOPF confirms every required channel with the applicable evidence and attestation.

### 4.9 AddendumInquiry

| Field | Rule |
|---|---|
| `inquiry_id` | Server-generated. |
| `addendum_id` | Required issued addendum. |
| `candidate_identity` | Authenticated owner-service identity; never free text. |
| `question`, `received_at` | Exact inbound question and authoritative receipt instant. |
| `response` | Required bounded text. |
| `affects_requirements` | Boolean decided by the responding procurement professional. |
| `responded_by`, `responded_at` | Server-derived. |
| `broadcast_status`, `broadcast_digest` | Required when the response affects requirements; uses the publication channel/candidate-notification contract without identifying the source. |

The module creates no inquiry on behalf of a candidate. It consumes an authenticated bidder-facing event and rejects inquiries received after the stated inquiry deadline.

### 4.10 TenderCancellation

| Field | Rule |
|---|---|
| `cancellation_id` | Server-generated. |
| `tender_id`, `publication_id` | Exact proceeding and publication. |
| `ground` | One configured, verified lawful ground from the applicable rule set. |
| `reason` | Specific circumstances, 20–2,000 characters. |
| `recommendation_id` | Optional immutable HOPF recommendation. |
| `decided_by`, `decided_at` | Accounting Officer; server-derived. |
| `ppra_report_due_by`, `candidate_notice_due_by` | Generated from the verified applicable rule. |
| `ppra_report_status`, `ppra_report_evidence_id` | `Not due`, `Due`, `Recorded`, `Overdue`; evidence append-only. |
| `candidate_notice_status` | Derived from the candidate registry and notice dispatch evidence. |
| `notice_publication_status` | Uses accountable channel-confirmation records against the original required-channel set. |
| `cancellation_digest` | Covers ground, reason, actor/time, recommendation and notice package. |

The cancellation decision closes the Tender immediately. Notice/report publication and evidence recording continue as compliance work and cannot reopen the procurement.

## 5. Lifecycle and business rules

### 5.1 Lifecycle

| Current state | Action | Actor | Result |
|---|---|---|---|
| Authorised requisition, unconsumed | Start Tender | Procurement Officer | Atomically creates/returns one Draft and records authoritative Requisition consumption. |
| Draft | Save | Procurement Officer | Saves valid incomplete/complete officer values; refreshes generated projection. |
| Draft | Submit for approval | Procurement Officer | Requires zero must-fix findings; locks Version and assigns HOPF decision. |
| Awaiting procurement approval | Return for correction | Head of Procurement Function | Preserves submitted Version; creates copied Draft at affected task. |
| Awaiting procurement approval | Approve Tender package | Head of Procurement Function | Freezes approved Version/package and creates Accounting Officer publication task. |
| Approved, publication not authorised | Reopen Tender | Head of Procurement Function | Preserves approved Version and creates copied Draft with reason. |
| Approved, publication not authorised | Authorise publication | Accounting Officer | Commits immutable publication decision, rule snapshot and required channel-confirmation records. |
| Publication authorised / evidence required | Confirm channel publication | Head of Procurement Function | Records actual availability, channel-appropriate evidence and explicit attestation against the exact package. |
| Publication authorised; no channel confirmed; confirmed unpublished | Withdraw publication authorisation | Accounting Officer | Preserves decision; records withdrawal; returns Tender to Approved for HOPF correction. |
| Every required channel confirmed | Confirm publication | System | Sets Published — open and `published_at`; writes actual invitation once to Planning. |
| Published — open | Draft addendum | Procurement Officer / HOPF | Creates one Draft addendum against current published content. |
| Draft addendum | Submit addendum for issue | Procurement Officer | Locks Draft and assigns HOPF issue task. |
| Awaiting-issue addendum | Issue addendum | HOPF | Commits immutable addendum and required channel-confirmation records; deadline changes only as governed. |
| Addendum awaiting publication confirmation | Confirm addendum channel publication | HOPF | Records evidence and attestation; the addendum becomes Issued only after every original required channel is confirmed. |
| Issued addendum inquiry | Respond | Procurement Officer / HOPF | Records response and broadcasts when required. |
| Published — open | Recommend cancellation | HOPF | Appends optional recommendation; does not cancel. |
| Published — open | Cancel Tender | Accounting Officer | Closes Tender immediately; creates notice/report compliance work. |
| Published — open; submission deadline reached | Close submission period | System / Bid Submission owner | Sets Submission period ended and emits immutable downstream contract. |
| Draft, Returned, Submitted or Approved before publication authorisation | Request requisition correction | Procurement Officer / HOPF | Stops Version; invokes governed corrected-Requisition route; no local override. |
| Corrected authorised Requisition available | Start corrected Tender Version | Procurement Officer | Consumes successor and creates linked Draft; stopped history remains immutable. |

### 5.2 Officer controls

#### Tender details

| Field | Control | Rule |
|---|---|---|
| Tender title | Single-line text, maximum 160 | Defaults from Requisition; required; no markup or generic title. |
| Issue date | Date | Required; cannot precede publication readiness. |
| Clarification deadline | Datetime | After issue date and before submission deadline. |
| Submission deadline | Datetime | After clarification; must allow the applicable minimum preparation period from actual publication. |
| Tender validity | Integer days, 1–365 | Default 120; helper explains supplier-offer validity. |
| Tender security treatment | Read-only | Fixed by template. |
| Tender security currency | Read-only KES | Fixed. |
| Tender security amount | Money, exact 2-decimal KES | Positive and within governed rule. |
| Pre-tender meeting | Yes/No | Default No. |
| Meeting date/time | Datetime | Required when Yes; before submission. |
| Meeting mode | `Physical`, `Online` | Required when meeting is Yes. |
| Meeting venue | Active Location | Required for Physical. |
| Online joining information | Text, maximum 240 | Required for Online. |

Opening date/time is generated equal to the submission deadline for this product.

#### Supplier requirements

| Field | Control | Rule |
|---|---|---|
| Manufacturer authorisation required | Yes/No | Default Yes; review note tests proportionality. |
| Product datasheets or brochures required | Yes/No | Default Yes. |
| Warranty confirmation required | Read-only Yes | Generated from inherited warranty. |
| Past supply experience required | Yes/No | Default No. |
| Minimum comparable contracts | Positive whole number | Required when experience is Yes; no fixed menu or policy default. |
| Experience period | Positive whole number of years | Required when experience is Yes; label **Within the last ___ years** and do not restrict the user to preset periods. |
| After-sales support evidence required | Yes/No | Default from inherited support. |
| After-sales evidence | `Kenya service-centre details and escalation contacts`, `Manufacturer or authorised service-partner commitment`, `Both` | Required when support evidence is Yes. |

#### Contract terms

| Field | Control | Rule |
|---|---|---|
| Inspection and acceptance location | Active Location | Required. |
| Payment timing | `30`, `45`, `60 days` | Default 30. |
| Performance security required | Yes/No | Default Yes. |
| Performance security percentage | Exact decimal percent, 1–10 | Required when Yes; default 10. |
| Delay damages per week | Exact decimal percent, 0.1–1.0 | Default 0.5. |
| Maximum delay damages | Integer percent, 5–10 | Default 10; not less than weekly rate. |
| Contract contact office | Active Office | Required; no person selector. |

The client and server enforce identical types, applicability, ranges and options. Hidden conditional fields are rejected in payloads.

### 5.3 Compatibility

A Requisition may start this product only when all eight checks pass:

| Check | Required value |
|---|---|
| Procurement category | Goods |
| Product | Straightforward off-the-shelf IT equipment |
| Method | Open Tender |
| Reservation | A category supported by the bound template release |
| Lotting | Single lot |
| Currency | KES |
| Award package | One |
| Plan horizon | Single year |

Compatibility is rechecked at Draft creation, submission, approval and publication authorisation against the exact immutable owner facts applicable to that action.

### 5.4 Review result

Review is a deterministic projection, not a workflow state or separate user task. A Draft may be incomplete; submission and approval may not.

Findings are:

- **Must fix** — prevents submission/approval/publication and links to the exact task, field or inherited owner route; or
- **Review note** — remains visible through HOPF and Accounting Officer decisions; cannot be dismissed.

The result verifies the source handoff, template release, eight compatibility checks, officer fields, dates, inherited completeness, grouping lineage, schedules, response schema, evaluation/contract mappings, file treatments, security/contract values, both renders and package digest.

### 5.5 Publication rules

1. The Accounting Officer sees the exact HOPF-approved package, review result, notes, documents and generated channels.
2. **Authorise publication** records the decision and creates the required confirmation work; it does not publish the Tender or call an assumed external interface.
3. Every MVP channel is **Evidence based**. The HOPF confirms the exact approved package through each channel using the fields and attestation in §4.7.
4. A checkbox, unevidenced assertion or technically valid upload without HOPF attestation is insufficient.
5. `published_at` is set only when every mandatory channel has a confirmed `available_at`.
6. The submission deadline is revalidated against `published_at`. If the applicable minimum period would be breached, the Tender cannot become Published until a lawful revised deadline is issued in the same immutable publication package.
7. Planning receives exactly one actual invitation event for `published_at`; idempotent replay or recovery emits none.
8. A new configuration rule never reclassifies an already-authorised publication; the snapshot controls it.

#### 5.5.1 Future integrated acknowledgement — not MVP

KenTender may later support `Integrated acknowledgement` for an individual publication channel. This facility is explicitly **to be implemented later** and shall remain unavailable in MVP.

It may be activated only after the Project Owner approves:

- the real external interface and responsible authority;
- authentication, package-identity and acknowledgement semantics;
- idempotency, timeout, uncertain-result, reconciliation and retry behaviour;
- operational ownership and audit evidence; and
- channel-specific acceptance and failure-recovery tests.

Until then, Configuration must reject `Integrated acknowledgement`, no adapter or transactional outbox is required, and no screen may describe a channel as automatically confirmed.

### 5.6 Addendum rules

- The affected reference must resolve to the current effective published package, including prior issued addenda.
- The prior value must match exactly; otherwise the Draft is stale.
- The system blocks changes that expand quantity/value/scope, change method/reservation/lotting/package, introduce a new requirement or alter the evaluation basis.
- Deadline-extension applicability is computed; professional judgement supplies the lawful new deadline where the governing rule does not provide a deterministic duration.
- Issue authority is HOPF. The addendum is not effective until every original required channel confirms the exact addendum digest.
- Supplier-facing documents show the current effective content and the complete addendum trail; the original package remains immutable.

### 5.7 Cancellation rules

- The Accounting Officer is the decision-maker.
- HOPF recommendation is optional and non-binding.
- A configured verified lawful ground and specific reason are mandatory.
- The decision closes the procurement even if cancellation notices or reports are still pending.
- Notices use the original channel set and immutable cancellation digest.
- Named candidate/tenderer notices use the authoritative bidder-service registry; absence is recorded, not assumed.
- Compliance deadlines and overdue status remain visible until evidence is recorded.
- Cancellation never reopens the Requisition, restores reserved funding or creates a replacement Tender automatically.

### 5.8 Core invariants

1. One authorised handoff has at most one active Tender consumption.
2. Draft creation and Requisition consumption commit together or neither commits.
3. Requisition revocation and Tender creation serialize on the same handoff identity.
4. Every Version binds one exact Requisition snapshot and template release.
5. Inherited identifiers/content never change in Tenders.
6. Every published technical requirement has exactly one supplier response, evaluation mapping and contract obligation mapping.
7. HOPF approval, AO publication authorisation and publication confirmation are three different facts.
8. Evidence upload, technical validation and record persistence are never publication confirmation by themselves.
9. Approved/published documents and decisions are never edited in place.
10. A repeated publication/addendum confirmation for the same channel and package is idempotent; a conflicting confirmation is rejected and preserved for audit.
11. Cancellation is terminal for the proceeding.
12. No publication, addendum or cancellation event expands the authorised procurement scope.

## 6. Roles and permissions

All access uses AUTH-ADR-001 v1.7 role-bound `User Responsibility Assignment` through registered permission hooks. No native Frappe User Permission participates in authorisation.

| Business responsibility | Scope | Exact work |
|---|---|---|
| Procurement Officer | Site-wide | Start and prepare Tender; submit; correct returned work; request Requisition correction; draft addendum; respond to addendum inquiry. |
| Head of Procurement Function | Site-wide | Return/approve Tender package; reopen before publication authorisation; confirm channel publication with evidence and attestation; draft/issue addendum; respond to inquiry; optionally recommend cancellation. |
| Accounting Officer | Site-wide | Authorise publication; withdraw authorisation only when confirmed unpublished and no channel was confirmed; cancel Tender. Cannot edit package/addendum content. |
| Departmental Author / Head of User Department | Organisation Unit | Read inherited requirements and neutral Tender/publication status already authorised by source scope; no Tender action. |
| Auditor | Site-wide or approved oversight scope | Read Versions, decisions, publication confirmations/evidence, addenda, inquiries and cancellation; no business action. |
| Authorised technical operator | Explicit future integration assignment | No MVP publication action. When §5.5.1 is implemented, may perform only approved reconciliation/recovery; cannot attest publication, edit content, authorise, issue or cancel. |
| Administrator / System Manager | Technical read | Read all records under KT-STD-001 v1.6 §3A.6; no business action unless separately assigned an explicit business/recovery responsibility. |
| System | Internal | Generate schedules/renders; validate and derive publication state from accountable confirmations; close submission period; publish Planning invitation actual and downstream event. |

The person who prepared or submitted a Version cannot approve it as HOPF. The person who prepared, submitted or HOPF-approved a Version cannot authorise its publication as Accounting Officer. Checks use the immutable Version audit, not role labels alone.

## 7. Service and command contracts

### 7.1 Reads

| Service | Required result |
|---|---|
| `GetTendersWorkspace` | One role-aware queue with exact status, next action and permitted filters. |
| `GetTenderStart` | Authorised Requisition summary, eight compatibility results and fixed template evidence; no mutation. |
| `GetTender` | One projection containing current Version, inherited snapshot, officer values, generated content, review result, decisions, publication status and permitted actions. |
| `GetTenderReview` | Complete result-first review with exact rows, renders and mappings. |
| `GetTenderPublication` | Approved package, AO task, rule snapshot, required channels, confirmation/evidence status and permitted actions. |
| `GetTenderHistory` | Versions, decisions, correction lineage, channel confirmations, addenda, inquiries, cancellation and downstream events. |
| `GetTenderDocument` | Exact immutable Invitation, issued Tender, addendum or cancellation notice by digest and authorised audience. |

Reads create no record, task, decision, render, confirmation or event.

### 7.2 Preparation and approval commands

| Command | Minimum effect |
|---|---|
| `StartTender` | Recheck handoff/template/compatibility; create or return one Draft; bind digests and record authoritative Requisition consumption atomically. |
| `SaveTenderDraft` | Accept only applicable §5.2 officer fields; reject inherited/generated/hidden/unknown fields. |
| `AddTenderEvidenceRequirement` / `UpdateTenderEvidenceRequirement` / `RemoveTenderEvidenceRequirement` | Mutate one valid Draft evidence row linked to an inherited published requirement. |
| `SubmitTenderForApproval` | Rebuild/review exact projection; require zero Must fix; lock Version and assign HOPF. |
| `ReturnTenderForCorrection` | Require reason and governed affected task; preserve submitted Version and create copied Draft. |
| `ApproveTenderPackage` | Recheck authority, segregation, package and review; commit immutable HOPF decision and AO task. |
| `ReopenApprovedTender` | Require reason and publication not authorised; preserve approved Version and create copied Draft. |
| `RequestRequisitionCorrection` | Stop current pre-publication Version and invoke the governed Requisition correction route; never edit inherited content. |
| `StartCorrectedTenderVersion` | Consume exact newly authorised successor; create linked Draft with regenerated snapshot/schedules. |

### 7.3 Publication commands

| Command | Minimum effect |
|---|---|
| `AuthoriseTenderPublication` | Recheck AO authority, segregation, approved package, current rule and minimum-period feasibility; commit decision, snapshot and one Evidence-based confirmation record for every required channel. |
| `ConfirmPublicationChannel` | HOPF records actual availability, required reference/URL/evidence and explicit attestation for one required channel against the exact package; server performs only the technical and authority checks in §4.7. |
| `WithdrawPublicationAuthorisation` | AO only; require no channel confirmed and accountable evidence that publication did not occur; preserve decision and record withdrawal. |
| `ConfirmTenderPublished` | Internal; require all channels confirmed, deadline valid and matching digests; set `published_at`, emit Planning actual and Bidder-facing open-Tender event once. |

The future integrated-acknowledgement commands are not part of MVP. They shall be specified and added only through the approval gate in §5.5.1.

### 7.4 Open-period and cancellation commands

| Command | Minimum effect |
|---|---|
| `CreateAddendumDraft` / `UpdateAddendumDraft` | Create/update structured Draft against current effective published content. |
| `SubmitAddendumForIssue` | Lock exact Draft and assign HOPF. |
| `ReturnAddendumForCorrection` | Preserve submitted Draft and create copied Draft with reason. |
| `IssueAddendum` | Recheck materiality/reference/deadline; commit the immutable issue decision and required channel-confirmation records. |
| `ConfirmAddendumPublicationChannel` | HOPF records channel-appropriate evidence and attestation against the exact addendum digest; confirm Issued only after all original required channels are confirmed. |
| `ReceiveAddendumInquiry` | Authenticate bidder-service producer and exact candidate/addendum; deduplicate inbound event. |
| `RespondToAddendumInquiry` | Record professional response; create anonymous broadcast when requirements are affected. |
| `RecommendTenderCancellation` | Append optional HOPF recommendation; no status change. |
| `CancelTender` | AO decision; require lawful ground/reason; close Tender and create immutable notice/report obligations. |
| `RecordCancellationComplianceEvidence` | Append verified PPRA-report or candidate/channel notice evidence; never change cancellation decision. |
| `CloseTenderSubmissionPeriod` | Internal/owner-authenticated; set boundary and emit immutable downstream contract once. |

Every command accepts expected record version and idempotency key. The server derives actor, responsibility assignment, state, totals, digests, rule applicability and permitted actions.

## 8. Error contract

| Code | User-visible message and treatment |
|---|---|
| `TND_NOT_FOUND` | **Tender not found.** Return to Tenders. |
| `TND_RESPONSIBILITY_REQUIRED` | **This action requires {named responsibility}.** |
| `TND_HANDOFF_INVALID` | **The authorised requisition is no longer available to start this Tender.** |
| `TND_HANDOFF_CONFLICT` | **A Tender has already been started for this requisition.** Open it when permitted. |
| `TND_PRODUCT_UNSUPPORTED` | **This requisition is not supported by the current IT-equipment Tender format.** No bypass. |
| `TND_TEMPLATE_UNAVAILABLE` | **The standard IT-equipment Tender format is not available.** Create nothing. |
| `TND_CONTROL_INVALID` | **Check the highlighted value.** Bind exact field error. |
| `TND_INHERITED_EDIT` | **Authorised requisition information cannot be changed here.** |
| `TND_MAPPING_INCOMPLETE` | **A published requirement is not fully connected to supplier response, evaluation and contract records.** Link exact row. |
| `TND_FILE_INVALID` | **A supporting file could not be verified.** Link exact file. |
| `TND_MUST_FIX` | **Fix the listed items before continuing.** Link every issue. |
| `TND_STALE_VERSION` | **Another user changed this Tender. Reload before continuing.** |
| `TND_SOD_BLOCKED` | **Another authorised officer must complete this decision.** Explain the conflicting prior action. |
| `TND_PUBLICATION_STARTED` | **Publication has started. This Tender can no longer be reopened.** |
| `TND_PUBLICATION_RULE_UNAVAILABLE` | **The publication rule is not configured for this Tender.** Contact administrator. |
| `TND_PUBLICATION_PERIOD_INVALID` | **The submission deadline does not allow the required preparation period after publication.** Link Tender details. |
| `TND_PUBLICATION_CONFIRMATION_INCOMPLETE` | **Complete the publication confirmation for this channel.** Link every missing or invalid field. |
| `TND_PUBLICATION_EVIDENCE_INVALID` | **The publication evidence could not be accepted.** Show the technical reason without claiming that publication did or did not occur. |
| `TND_PUBLICATION_DIGEST_MISMATCH` | **This confirmation does not match the approved Tender package.** Reject and preserve the conflict for audit. |
| `TND_PUBLICATION_ALREADY_CONFIRMED` | **Publication through this channel is already confirmed.** Show the immutable confirmation. |
| `TND_PUBLICATION_WITHDRAWAL_BLOCKED` | **Publication authorisation cannot be withdrawn because at least one channel is already confirmed.** |
| `TND_ADDENDUM_STALE` | **The published wording has changed. Reload before preparing this addendum.** |
| `TND_ADDENDUM_MATERIAL` | **This change is too significant for an addendum. Cancel and start a newly governed Tender if procurement must continue.** |
| `TND_ADDENDUM_DEADLINE_REQUIRED` | **Set a lawful revised submission deadline for this addendum.** |
| `TND_INQUIRY_LATE` | **The inquiry deadline has passed.** Preserve receipt evidence; no response command. |
| `TND_CANCELLATION_GROUND_INVALID` | **Select an applicable cancellation ground.** |
| `TND_CANCELLED` | **This Tender has been cancelled and cannot accept further work.** |
| `TND_IDEMPOTENCY_CONFLICT` | **This request was already used with different information. Stop and refresh.** |

Record-existence masking follows AUTH-ADR-001. Administrator/System Manager technical read follows KT-STD-001 v1.6 §3A.6 and is not masked.

## 9. UI architecture, menu and routes

The navigation contains one module entry: **Tenders**.

| Surface | Route | Purpose |
|---|---|---|
| Tenders workspace | `/app/tenders` | One queue for authorised Requisitions, Drafts, decisions, publication work and open Tenders. |
| Start Tender | `/app/tenders/new/{handoff_id}` | Read-only confirmation; explicit Start creates/reuses Draft. |
| Tender record | `/app/tenders/{tender_id}` | Role- and state-aware preparation, review, approval, publication and open-period detail. |
| Tender history | `/app/tenders/{tender_id}/history` | Immutable Versions, decisions, channel confirmations, addenda, inquiries, cancellation and downstream events. |

Tasks link to the Tender record with the exact record/task identity; they do not create separate module workspaces. Opening a route creates nothing. Dialogs handle Start, Return, approval, publication authorisation, evidence, addendum issue, inquiry response, reopen, correction and cancellation.

The Tender record uses one header and one state-specific primary content area. It does not expose every future stage as a stepper. Preparation alone uses the three-part progress row in §10.

## 10. Static design contract

Supply **KT-STD-001 v1.6 §2 plus this section only** to the design tool. Fixture metadata remains outside the artboard. Every variant below is an isolated reset unless the primary lifecycle explicitly links it.

### 10.1 Shared fixture pack

#### Tender and actors

| Fact | Exact value |
|---|---|
| Financial year | FY 2027/28 |
| Approved purchase | Clinical training and deployment laptops for digital health rollout |
| Plan Item | PPI-MOH-2027-033 |
| Strategic objective | Strengthen interoperable national digital health services |
| Plan horizon | Single year |
| Requisition | REQ-MOH-2027-033-001 · Authorised · Version 1 |
| Requisition value | KES 50,000,000.00 — internal only |
| Procurement method | Open Tender |
| Reservation category | Youth |
| Lotting | Single lot |
| Award package | One |
| Latest delivery | 30 September 2027 |
| Tender | TND-MOH-2027-033 |
| Template | IT Equipment — Open Tender · Version 1.1 |
| Procurement Officer | Brian Wafula |
| Head of Procurement Function | Charles Mutiso |
| Accounting Officer | Amina Hassan |

#### Equipment

| Item | Approved requirement | Requisition item ID | Quantity | Intended use | Delivery |
|---|---|---|---:|---|---|
| Business laptops | Human Resources Management and Development | SRC-MOH-033-001 | 100 Each | Clinical training | Afya House, Nairobi · 30 Sep 2027 |
| Business laptops | Digital Health | SRC-MOH-033-002 | 150 Each | Field digital-health deployment | Afya House, Nairobi · 30 Sep 2027 |

The two inherited items render as one supplier-facing **Business laptops · 250 Each** schedule line. Both item/source identities remain available in Source details.

#### Technical requirements

| Requirement | Comparison | Exact value | Unit |
|---|---|---|---|
| Electrical compatibility | Required | Yes — suitable for Kenyan mains supply | — |
| New and unused equipment | Required | Yes | — |
| Memory | Minimum | 16 | GB |
| Storage capacity | Minimum | 512 | GB |
| Storage type | One of | NVMe SSD | — |
| Display size | Minimum | 14.0 | inches |
| Battery runtime | Minimum | 8 | hours |
| Processor requirement | Minimum | 64-bit business-class processor, minimum 10 cores or equivalent benchmark | — |
| Operating-system compatibility | Required | Approved organisational Windows environment | — |
| Network connectivity | Required | Wi-Fi 6 and Bluetooth 5 or later | — |
| Required ports | Required | USB-C ×2; USB-A ×2; HDMI ×1 | — |

#### Warranty and support

| Label | Exact value |
|---|---|
| Minimum warranty | 36 months |
| On-site support required | Yes |
| Maximum support response | 8 hours |
| Manufacturer support required | Yes |
| Service location constraint | Within Kenya |
| Support description | Supplier to provide escalation and warranty-contact details. |

#### Acceptance checks

| Check | Applies to | Pass condition | Evidence |
|---|---|---|---|
| Quantity | All items | Delivered quantities equal the authorised schedule | Inspection record |
| Physical condition | All items | No visible damage and all listed accessories are present | Inspection record |
| Required specification | All items | Every delivered unit complies with all mandatory technical rows | Inspection record |
| Functional test | All items | Each device powers on and completes the agreed basic functional test | Test result |
| Documents received | All items | Warranty and delivery documents are received and verified | Certificate |

The fixture has no related services and no supporting materials.

#### Officer values

| Group | Field | Exact value |
|---|---|---|
| Tender details | Tender title | Supply and delivery of business laptops |
| Tender details | Issue date | 15 May 2027 |
| Tender details | Clarification deadline | 27 May 2027, 17:00 EAT |
| Tender details | Submission deadline | 5 Jun 2027, 11:00 EAT |
| Tender details | Tender validity | 120 days |
| Tender details | Tender security | KES 500,000.00 |
| Tender details | Pre-tender meeting | No |
| Supplier requirements | Manufacturer authorisation | Yes |
| Supplier requirements | Product datasheets or brochures | Yes |
| Supplier requirements | Warranty confirmation | Yes — required by authorised requisition |
| Supplier requirements | Past supply experience | Yes; 2 comparable contracts in 5 years |
| Supplier requirements | After-sales support evidence | Kenya service-centre details and escalation contacts |
| Contract terms | Inspection and acceptance location | Ministry of Health Headquarters, Afya House, Nairobi |
| Contract terms | Payment timing | 30 days |
| Contract terms | Performance security | Yes; 10% |
| Contract terms | Delay damages | 0.5% per week; maximum 10% |
| Contract terms | Contract contact office | Ministry of Health Procurement Office |

#### Publication configuration and evidence

| Fact | Exact value |
|---|---|
| Publication rule | PUB-RULE-MOH-OT-2027-01 · effective FY 2027/28 |
| Required channels | State Portal; Ministry website; Notice board; Two national newspapers |
| State Portal mode | Evidence based |
| Ministry website mode | Evidence based |
| Notice board mode | Evidence based |
| Newspapers mode | Evidence based |
| Publication authorised | Amina Hassan · 15 May 2027, 07:55 EAT |
| State Portal confirmation | PPIP-MOH-2027-033; public fixture URL `https://portal.example.test/tenders/PPIP-MOH-2027-033`; evidence `PPIP-MOH-2027-033.pdf`; available 15 May 2027, 08:00 EAT; attested by Charles Mutiso at 08:03 EAT |
| Ministry website confirmation | WEB-MOH-2027-033; public fixture URL `https://health.example.test/tenders/TND-MOH-2027-033`; evidence `WEB-MOH-2027-033.pdf`; available 15 May 2027, 08:00 EAT; attested by Charles Mutiso at 08:04 EAT |
| Notice-board confirmation | NB-MOH-2027-033; evidence `NB-MOH-2027-033.jpg`; available 15 May 2027, 08:00 EAT; attested by Charles Mutiso at 08:06 EAT |
| Newspaper confirmation | NP-MOH-2027-033; evidence `NP-MOH-2027-033.pdf` showing both editions; available 15 May 2027, 08:00 EAT; attested by Charles Mutiso at 08:07 EAT |
| Published at | 15 May 2027, 08:00 EAT |
| Publication fully confirmed | 15 May 2027, 08:07 EAT |
| Tendering period | 21 days |

The configured fixture output tests the UI and rules engine; it is not a hardcoded national threshold.

#### Primary lifecycle

| Event | Actor | Exact time and result |
|---|---|---|
| Draft started | Brian Wafula | 20 Mar 2027, 09:00 EAT |
| Submitted Version 1 | Brian Wafula | 20 Mar 2027, 11:40 EAT |
| Returned | Charles Mutiso | 25 Mar 2027, 14:00 EAT |
| Corrected Version 2 submitted | Brian Wafula | 15 Apr 2027, 09:15 EAT |
| Tender package approved | Charles Mutiso | 20 Apr 2027, 10:00 EAT |
| Publication authorised | Amina Hassan | 15 May 2027, 07:55 EAT |
| Published — open | System | Fully confirmed 15 May 2027, 08:07 EAT; actual `published_at` 15 May 2027, 08:00 EAT |
| Addendum issued and fully published | Charles Mutiso | 31 May 2027, 09:00 EAT; revised deadline 12 Jun 2027, 11:00 EAT |
| Addendum inquiry answered | Brian Wafula | 1 Jun 2027, 11:00 EAT |

Review note: **Confirm that manufacturer authorisation is proportionate for this purchase.** Return comment: **Confirm whether manufacturer authorisation is necessary and update the supplier evidence requirement.**

Addendum: `ADD-MOH-2027-033-001`; affected reference **Goods and delivery — delivery location**; previous **Ministry of Health Headquarters, Afya House, Nairobi**; revised **Ministry of Health Headquarters, Afya House, 3rd Floor Procurement Stores, Nairobi**; reason **The published address omitted the internal delivery point**; class **Administrative clarification**; late-issue rule requires extension; revised submission deadline **12 Jun 2027, 11:00 EAT**.

Inquiry: **Do suppliers who downloaded the original Tender need to change the offered delivery price?** Response: **No. The addendum clarifies the internal delivery point within Afya House and does not change the delivery city, quantity or pricing basis.** `affects_requirements = No`.

#### Isolated variant facts

| Variant | Exact facts |
|---|---|
| Unsupported start | Purchase **Implementation of a national health-data exchange platform**; Requisition `REQ-MOH-2027-038-001`; Product **Software integration**; Quantity **1 Project**; Approved value **KES 120,000,000.00**; Method **Open Tender**; Latest delivery **31 Dec 2027**. |
| Needs-attention review | Contract term **Inspection and acceptance location** is empty. Must-fix text **Enter the inspection and acceptance location.** Link **Review contract terms**. The manufacturer-authorisation review note remains separate. |
| Publication evidence rejected | Tender `TND-MOH-2027-035`; State Portal confirmation remains Awaiting confirmation because uploaded file `PPIP-MOH-2027-035.exe` is not an allowed evidence type. Entered values remain available for correction; no channel is confirmed. |
| Conflicting confirmation | Tender `TND-MOH-2027-036`; State Portal already confirmed against the approved package; a second request supplies a different availability time and is rejected without changing the immutable confirmation. |
| Material addendum | Separate open Tender `TND-MOH-2027-039`; Purchase **Supply and delivery of field laptops**; affected reference **Business laptops — Quantity**; current **250 Each**; proposed **300 Each**; reason **Additional deployment sites require 50 more laptops**. |
| Cancellation | Tender `TND-MOH-2027-034`; Purchase **Supply and delivery of district clinic printers**; Published **20 May 2027, 08:00 EAT**; Submission deadline **10 Jun 2027, 11:00 EAT**; original channels are the four shared channels. Decision is **4 Jun 2027, 14:00 EAT**; compliance deadlines are **18 Jun 2027**. |
| Cancellation recommendation | Charles Mutiso; **4 Jun 2027, 13:30 EAT**; **I recommend cancellation because the confirmed budget is insufficient to complete this procurement.** |
| Requisition correction | Purchase **Clinical training laptops for county facilities**; Charles Mutiso requests correction on `TND-MOH-2027-037` Version 2 on **21 Apr 2027, 09:00 EAT**; reason **The authorised battery-runtime requirement must be corrected before this Tender can continue.** Current owner **Grace Wanjiku, Departmental Author**. Corrected successor is Requisition `REQ-MOH-2027-037-001` Version 2, authorised **23 Apr 2027, 10:00 EAT**. |

### 10.2 TPR-DES-01 — Tenders workspace

**Purpose.** Find the next Tender task or inspect an existing Tender.

**Fixture outside the artboard.** Brian Wafula; Procurement Officer; 20 Mar 2027, 08:50 EAT; authorised Requisition ready and no Tender exists.

**Header.** Title **Tenders**. Description **Prepare approved requisitions, complete approvals and follow publication.** No header primary action.

**Composition, top to bottom.**

1. Compact work-summary row: **Ready to start 1**, **Drafts 0**, **Returned to me 0**. Each is a local filter.
2. Filter row: Search by Tender, requisition or purchase; Status **All statuses**; Financial year **All financial years**; Clear filters.
3. One table with columns Purchase; Tender; Status; Required by; Action.
4. Fixture row: purchase title with `PPI-MOH-2027-033` beneath; Tender value **Not started** with `REQ-MOH-2027-033-001` beneath; Status **Ready to start**; Required by **30 Sep 2027**; primary row action **Start Tender**.

**Variants.**

- **TPR-DES-01-DRAFT:** Tender `TND-MOH-2027-033`; Status **Draft — Tender details need attention**; action **Continue**.
- **TPR-DES-01-RETURNED:** Status **Returned to you — Supplier requirements need attention**; action **Correct**.
- **TPR-DES-01-HOPF:** Charles Mutiso sees count **Awaiting procurement approval 1**; Status **Awaiting your approval**; action **Review**.
- **TPR-DES-01-AO:** Amina Hassan sees count **Awaiting publication authorisation 1**; Status **Awaiting your publication decision**; action **Review publication**.
- **TPR-DES-01-PUBLISHING:** Charles Mutiso sees Status **Publication confirmation required**; secondary line **Notice board and newspaper confirmations**; action **Complete confirmations**.
- **TPR-DES-01-PUBLISHED:** Status **Published — open until 12 Jun 2027, 11:00 EAT**; action **View**.
- **TPR-DES-01-READER:** departmental reader or Auditor sees permitted records and neutral statuses; no counts or business actions; action **View**.
- **TPR-DES-01-TECHNICAL:** Administrator/System Manager sees all records with Status and Financial year filters; no counts or business actions; action **View**.
- **TPR-DES-01-EMPTY:** table text **No Tenders match these filters.** Action **Clear filters** only.

**Visual check.** One queue shows each Tender once and gives the current actor one unambiguous next action.

### 10.3 TPR-DES-02 — Start Tender dialog

**Purpose.** Confirm the authorised requisition before creating the Draft.

**Fixture outside the artboard.** Same reset as TPR-DES-01.

**Dialog.** A 520 px dialog over the workspace. Heading **Start this Tender?** Text **A Draft Tender will be created from the authorised requisition below.**

Place labelled rows vertically: Purchase; Requisition; Quantity; Approved value; Method; Latest delivery. Values are the shared fixture title, reference, **250 Each**, **KES 50,000,000.00**, **Open Tender**, **30 Sep 2027**.

Show green result **Supported — IT equipment using the standard Open Tender format.** Closed disclosure **Why this requisition is supported** contains Category Goods; Product straightforward off-the-shelf IT equipment; Method Open Tender; Reservation Youth; Lotting Single lot; Currency KES; Award package One; Plan horizon Single year. Closed disclosure **Template and source details** contains the exact template and official source.

Footer left **Cancel**; right primary **Start Tender**. Both enabled. No package, template, schema, manifest or configuration selector.

**Unsupported variant.** Use the isolated Unsupported start facts; show **This requisition is not supported by the current IT-equipment Tender format.** Disable Start Tender; retain Cancel.

**Visual check.** The user knows what will be created and makes no false template or configuration decision.

### 10.4 TPR-DES-03 — Draft: Tender details

**Purpose.** Set the dates, security and optional meeting.

**Fixture outside the artboard.** Brian Wafula; Draft Version 1; 20 Mar 2027, 09:10 EAT.

**Header.** Title **Supply and delivery of business laptops**. Description **Set the dates and security suppliers must follow.** Badge **Draft**. Tender and Requisition references appear on separate muted lines beneath. No header action.

**Composition, top to bottom.**

1. Three-part progress row: Tender details selected and **Needs attention**; Supplier and contract requirements **Not started**; Review and submit **Not started**.
2. Context strip with Purchase; Method; Quantity; Latest delivery. Link **View authorised requisition** opens an in-page drawer.
3. **Tender dates**: Tender title full width; Issue date and Clarification deadline; Submission deadline and Tender validity. Helper beneath validity: **How long suppliers' offers must remain valid.**
4. **Tender security**: Treatment and Currency as plain read-only values; editable Amount.
5. **Pre-tender meeting**: Yes/No; conditional group absent for No.
6. Footer: secondary **Back to Tenders**, secondary **Save draft**, primary **Continue**.

**Authorised-requisition drawer.** Section **Approved purchase and policy context** contains Plan Item; Requisition; authorised value; reservation; lotting; Strategic objective; Plan horizon; Template; generated Opening date/time. Show **For internal review only — not included in supplier documents.** Section **Authorised requirements** contains every equipment, technical, support and acceptance row from §10.1.

**Meeting variants.**

- **TPR-DES-03-PHYSICAL:** Pre-tender meeting Yes; date/time **22 May 2027, 10:00 EAT**; mode Physical; venue **Ministry of Health Headquarters, Afya House, Nairobi**; no online field.
- **TPR-DES-03-ONLINE:** Pre-tender meeting Yes; date/time **22 May 2027, 10:00 EAT**; mode Online; joining information **Microsoft Teams — https://meet.example.test/tnd-moh-2027-033**; no venue field.

**Visual check.** The screen is one manageable form; fixed and inherited facts cannot be mistaken for inputs.

### 10.5 TPR-DES-04 — Draft: Supplier and contract requirements

**Purpose.** Set permitted supplier evidence and contract terms without rewriting authorised requirements.

**Fixture outside the artboard.** Brian Wafula; Draft Version 1; 20 Mar 2027, 10:30 EAT; Tender details complete.

**Header.** Reuse TPR-DES-03. Progress: Tender details Complete; this task selected and Needs attention; Review and submit Not started.

**Composition, top to bottom.**

1. Text **The authorised requirements are already included. Choose only the additional evidence suppliers must provide and complete the contract terms below.**
2. Section **Supplier evidence**: Manufacturer authorisation; Product datasheets or brochures; read-only Warranty confirmation with source; Past supply experience with dependent positive-whole-number fields **Minimum comparable contracts** and **Within the last ___ years**; After-sales support evidence with dependent option. Arrange dependent controls directly beneath the parent. Do not use preset number/year menus. Helper: **Use only experience requirements that are necessary and proportionate for this purchase.**
3. Table **Additional evidence** with columns Evidence; Type; Proves; Required; Action. Routine empty text **No additional evidence has been added.** Secondary **Add evidence**.
4. Section **Contract terms**: Inspection and acceptance location full width; Payment timing and Performance security; dependent Security percentage and Delay damages; Maximum delay damages and Contract contact office.
5. Closed disclosure **How suppliers will be evaluated** with the fixed four stages.
6. Closed disclosure **Requirements carried into the contract** with summaries and **Show full requirements**, revealing complete §10.1 tables in place.
7. Footer: secondary **Back**, secondary **Save draft**, primary **Review Tender**.

**Add-evidence dialog.** Heading **Add supplier evidence**. Fields: Evidence label **Electrical compatibility certificate**; Evidence type Certificate; Requirement type Technical requirement; Proves **Electrical compatibility — suitable for Kenyan mains supply**; Required Yes. Helper **Additional evidence must prove a published requirement. It cannot add a new qualification or technical condition.** Footer Cancel / **Add evidence**. Edit uses **Save changes**. Remove confirmation names evidence and linked requirement; Cancel / destructive **Remove evidence**.

**Visual check.** The editable Procurement decisions are grouped into two readable sections; no authorised requirement or supplier price is re-entered.

### 10.6 TPR-DES-05 — Review and submit

**Purpose.** Understand whether the Tender is ready, inspect exceptions and submit the exact package.

**Fixture outside the artboard.** Brian Wafula; Draft Version 1; 20 Mar 2027, 11:35 EAT.

**Header.** Title **Review Tender**. Description **Check the complete Tender and submit it to the Head of Procurement Function.** Badge Draft; references beneath. Progress shows all tasks Complete; Review and submit selected.

**Composition, top to bottom.**

1. Green result **Ready to submit** and text **All required information is complete. Review the note below before submitting.**
2. Amber panel **1 review note** with the manufacturer-authorisation note and link **Review supplier requirements**.
3. Key facts: Requisition; Quantity; Approved value; Method; Submission deadline; Tender security; Reservation Youth; Latest delivery.
4. Actions **Preview Invitation** and **Preview complete Tender**, secondary and enabled.
5. Review sections: Tender details; Requirements from the authorised requisition; Supplier pricing schedule; Supplier and evaluation requirements; Contract terms; Technical evidence. Each has a plain summary and Show details. Only a section containing a must-fix item or review note starts open.
6. Supplier pricing detail: one 250-Each row; Unit price/Tax **Completed by supplier**; totals **Calculated from supplier response**. The authorised value is absent from price cells.
7. Requirements detail contains all §10.1 rows. Technical evidence contains exact template/source/package identities, both item/source lineages, mappings and digests.
8. Footer: secondary **Back**, primary **Submit for approval**.

**Needs-attention variant.** Use the isolated Needs-attention review facts. Red result **Needs attention**; the must-fix item links to the exact task/field. Submit disabled with **Fix the item above before submitting.** The review note remains separate and does not disable submission.

**Confirmation.** Heading **Submit this Tender for approval?** Text **The submitted Version will be locked. Charles Mutiso can return it or approve the package for publication review.** Footer Cancel / **Submit for approval**.

**Visual check.** Result and exceptions lead; complete content remains available without revisiting preparation tasks.

### 10.7 TPR-DES-06 — HOPF approval

**Purpose.** Decide whether the immutable package may proceed to publication authorisation.

**Fixture outside the artboard.** Charles Mutiso; HOPF; submitted Version 2; 20 Apr 2027, 10:00 EAT; Charles did not prepare/submit it.

**Header.** Title **Review Tender package**. Description **Decide whether this Tender may proceed to Accounting Officer publication review.** Badge **Awaiting your approval**; references beneath.

**Composition, top to bottom.**

1. Green **Ready to approve** and text **Approval locks this package for the Accounting Officer's publication decision. It does not publish the Tender.**
2. Visible one review note.
3. Submitted by Brian Wafula; Submitted at 15 Apr 2027, 09:15 EAT; Version 2, separately labelled.
4. Same key facts, document actions and six review sections as TPR-DES-05; all read-only.
5. Sticky footer: secondary **Return for correction**; primary **Approve Tender package**.

**Return dialog.** Heading **Return this Tender for correction?** Required Correction required; affected task Select: Tender details / Supplier and contract requirements / Review and generated documents. Fixture selects Supplier and contract requirements with the shared return comment. Text **The submitted Version will remain in history and a copied Draft will be created.** Footer Cancel / **Return for correction**.

**Approval dialog.** Heading **Approve this Tender package?** Values: Tender; Version; Submission deadline; Documents **Invitation and complete Tender**. Text **The Accounting Officer must separately authorise publication. Suppliers cannot see this Tender yet.** Footer Cancel / **Approve Tender package**.

**Segregation variant.** Omit decisions; show **You cannot approve a Tender Version you prepared or submitted. Another Head of Procurement Function must decide it.**

**Visual check.** HOPF sees the decision and full evidence without any implication that approval advertises the Tender.

### 10.8 TPR-DES-07 — Accounting Officer publication authorisation

**Purpose.** Authorise publication of the exact approved Tender package through the generated channels.

**Fixture outside the artboard.** Amina Hassan; Accounting Officer; 15 May 2027, 07:55 EAT; approved Version 2; no publication confirmation exists.

**Header.** Title **Authorise Tender publication**. Description **Review the approved package and the channels through which it must be published.** Badge **Awaiting publication authorisation**; references beneath.

**Composition, top to bottom.**

1. Green **Ready to authorise publication**. Text **Authorisation allows publication work to begin. The Tender is shown as Published only after every required channel is confirmed.**
2. Approval trail: Prepared by Brian Wafula; Approved by Charles Mutiso; Approved at 20 Apr 2027, 10:00 EAT; Version 2; package digest, each labelled separately.
3. Visible one review note.
4. Key facts: Purchase; Requisition; Quantity; Approved value; Method; Submission deadline; Tendering period; Reservation Youth.
5. Documents: **View Invitation**, **View complete Tender**.
6. Section **Required publication channels** with columns Channel; How confirmation is obtained; Current result. Every row says **HOPF confirmation with evidence** / **Not started**. No channel is described as integrated or automatic.
7. Closed **Complete Tender details** containing the same six review sections as HOPF.
8. Footer primary **Authorise publication**. No channel selection or edit control.

**Confirmation.** Heading **Authorise publication of this Tender?** Text **This allows the Head of Procurement Function to publish the exact approved Invitation and Tender through every required channel and confirm the evidence. It does not itself publish the Tender or edit the package.** Values: Package Version 2; Submission deadline 5 Jun 2027, 11:00 EAT; Required channels 4. Footer Cancel / **Authorise publication**.

**Segregation variant.** Omit primary action; show **You cannot authorise publication of a Tender Version you prepared, submitted or approved as Head of Procurement Function. Another Accounting Officer must decide it.**

**Visual check.** AO sees one business decision, generated channels and the exact package; no operational publication machinery is presented as an editable choice.

### 10.9 TPR-DES-08 — Publication confirmation

**Purpose.** Let the HOPF confirm actual publication through each required channel with evidence and explicit accountability.

**Fixture outside the artboard.** Charles Mutiso; HOPF; 15 May 2027, 08:05 EAT; digital channels confirmed; physical evidence not yet recorded.

**Header.** Tender title. Description **Confirm where and when the approved Tender was published.** Badge **Publication confirmation required**; references beneath.

**Composition, top to bottom.**

1. Amber result **2 of 4 required channels confirmed** and text **The Tender is not yet shown as Published. Confirm the remaining channels below.**
2. Channel table columns Channel; Result; Available at; Confirmation/action. State Portal Confirmed / 15 May 08:00 / View confirmation. Ministry website Confirmed / 15 May 08:00 / View confirmation. Notice board Awaiting confirmation / — / **Confirm publication**. Two national newspapers Awaiting confirmation / — / **Confirm publication**.
3. Section **Approved documents** with View Invitation and View complete Tender.
4. Closed **Publication decision and rule** with AO/time, rule snapshot and package digest.
5. No automatic-acknowledgement, Retry, manual overall Published or package-edit action.

**Confirmation dialog.** Heading **Confirm notice-board publication**. Intro **Confirm only after the exact approved Invitation and complete Tender were publicly available through this channel.** Fields: Available date/time **15 May 2027, 08:00 EAT**; Publication reference **NB-MOH-2027-033**; Public URL absent and not applicable; Evidence file `NB-MOH-2027-033.jpg`, required; Notes optional, maximum 500. Required attestation checkbox: **I confirm that the exact approved Tender package was publicly available through the Notice board at the date and time stated above.** Footer Cancel / **Confirm publication**. Newspaper variant names both national newspapers, uses reference `NP-MOH-2027-033`, evidence `NP-MOH-2027-033.pdf` and the same channel-specific attestation.

**Online-channel variant.** State Portal and Ministry website use the same dialog. Public URL is required when a stable URL exists; the exact fixture URLs and evidence files come from §10.1. The system does not claim to test public availability.

**Invalid-evidence variant.** Use the isolated Publication evidence rejected facts. Inline error **The selected file cannot be used as publication evidence. Choose an allowed document or image file.** The channel remains Awaiting confirmation; entered non-file values are preserved.

**Conflicting-confirmation variant.** Use the isolated Conflicting confirmation facts. Full inline state **This channel is already confirmed** with View confirmation. The later conflicting request changes nothing.

**Visual check.** HOPF sees one accountable confirmation action per channel, the exact package and evidence requirements; the screen makes no unsupported claim of automatic integration or independent factual verification.

### 10.10 TPR-DES-09 — Published Tender

**Purpose.** Show the effective public Tender, open-period work and immutable evidence.

**Fixture outside the artboard.** Charles Mutiso; HOPF; 1 Jun 2027, 12:00 EAT; addendum issued; inquiry answered.

**Header.** Title **Supply and delivery of business laptops**. Description **Published and open for supplier submissions.** Badge **Published — open**. Tender reference beneath. Upper-right **View public Tender**.

**Composition, top to bottom.**

1. Status panel: Published at **15 May 2027, 08:00 EAT**; Current submission deadline **12 Jun 2027, 11:00 EAT**; Publication authorised by **Amina Hassan**; Effective addenda **1**.
2. Documents row: View Invitation; View complete Tender; View current addendum.
3. Channel table with all four Confirmed results, available times and evidence links.
4. Section **Changes and notices**. Addenda table columns Addendum; Change; Issued; Deadline; Action. Row ADD-MOH-2027-033-001; Delivery point clarified; 31 May 2027, 09:00 EAT; 12 Jun 2027, 11:00 EAT; View.
5. Inquiries table columns Addendum; Question; Received; Response status; Action. One row with the shared inquiry; 1 Jun 2027, 09:00 EAT; Answered; View.
6. Section **Tender content** with six closed summaries and complete in-page detail.
7. Section **History and evidence** collapsed with decisions, digests and publication confirmations.
8. HOPF actions at foot: primary **Prepare addendum**; secondary **Recommend cancellation**. Accounting Officer variant replaces both with destructive **Cancel Tender**. Procurement Officer sees **Prepare addendum** only. Departmental reader/Auditor sees no business action.

**No-addendum variant.** Addenda text **No addenda have been issued.** Inquiries text **No addendum inquiries have been received.** Current deadline remains 5 Jun 2027, 11:00 EAT.

**Submission-ended variant.** Badge **Submission period ended**; no addendum or cancellation action; text **Supplier submission is closed. The proceeding has moved to the next procurement stage.**

**Visual check.** One record shows current effective documents, deadline, channels, changes and actor-appropriate work without a second module.

### 10.11 TPR-DES-10 — Prepare and issue addendum

**Purpose.** Record one non-material change against exact current published content and issue it through every original channel.

**Fixture outside the artboard.** Brian Wafula; Procurement Officer; 31 May 2027, 08:30 EAT; Draft addendum.

**Header.** Title **Prepare addendum**. Description **Identify the published wording that needs a non-material correction.** Badge **Draft addendum**; Tender and current deadline beneath.

**Composition, top to bottom.**

1. Visible warning **An addendum cannot expand the purchase, add a requirement or change the evaluation basis. A material change requires cancellation and a newly governed Tender.**
2. Fields in order: Change class Administrative clarification; Affected area Goods/delivery schedule; Affected reference Delivery location; Current published value plain read-only; Revised value textarea; Reason textarea; Why this is not material textarea.
3. Result panel **Submission deadline must be extended**. Current deadline 5 Jun 2027, 11:00 EAT; editable Revised submission deadline 12 Jun 2027, 11:00 EAT; explanation **This addendum is being issued within the governed late-amendment period.**
4. Section **Publication** lists the four original channels as read-only.
5. Footer: secondary Back; secondary Save draft; primary **Submit for issue**.

**HOPF issue variant.** Charles Mutiso sees all content read-only, result **Ready to issue**, exact changed-fields comparison, revised deadline and four channels. Footer Return for correction / **Issue addendum**. Confirmation states that issue is immutable and accountable publication confirmation for every channel follows separately.

**Material-change variant.** Use the isolated Material addendum facts. Result **This change cannot be made by addendum.** Primary absent; show **Cancel the Tender and start a newly governed Tender if procurement must continue.** Link View cancellation requirements.

**Visual check.** The affected content, before/after difference, materiality and deadline consequence are immediately understandable.

### 10.12 TPR-DES-11 — Respond to addendum inquiry

**Purpose.** Answer an authenticated candidate question about an issued addendum.

**Fixture outside the artboard.** Brian Wafula; Procurement Officer; 1 Jun 2027, 10:30 EAT; shared inquiry unanswered.

**Header.** Title **Respond to addendum inquiry**. Description **Answer the question and state whether the response changes any Tender requirement.** Addendum and Tender references beneath.

**Composition, top to bottom.**

1. Read-only Candidate **Verified supplier account**; Received **1 Jun 2027, 09:00 EAT**; Addendum `ADD-MOH-2027-033-001`.
2. Read-only Question with exact fixture text.
3. Response textarea with exact fixture response.
4. Yes/No **Does this response affect a Tender requirement?** Fixture No.
5. With No, visible text **The response will be sent to the candidate and recorded.** With Yes variant, text **The response will be sent to every registered candidate without identifying who asked.**
6. Footer Cancel / primary **Send response**.

**Visual check.** The source remains confidential in any broadcast and the officer deliberately classifies the response effect.

### 10.13 TPR-DES-12 — Cancel Tender

**Purpose.** Record the Accounting Officer's cancellation decision and resulting compliance work.

**Fixture outside the artboard.** Amina Hassan; Accounting Officer; isolated Cancellation facts; Published — open; no HOPF recommendation.

**Header.** Title **Cancel Tender**. Description **Cancel this procurement proceeding using an applicable statutory ground.** Badge **Published — open**; reference beneath.

**Composition, top to bottom.**

1. Red warning **Cancellation is final for this Tender. It does not restore the Requisition or create a replacement Tender.**
2. Summary: Purchase; Tender; Published at; Submission deadline; Required channels.
3. Ground Select **Inadequate budgetary provision**; Reason required textarea with fixture **The confirmed budget available for this procurement is insufficient to proceed.**
4. Recommendation panel absent in the base fixture. Recommendation variant uses the exact isolated Cancellation recommendation facts.
5. Consequences: Tender closes immediately; cancellation notice published through all original channels; PPRA report due **18 Jun 2027**; candidate notices due **18 Jun 2027**; replacement procurement requires new governance.
6. Footer secondary Back / destructive **Cancel Tender**.

**Confirmation.** Heading **Cancel this Tender?** Values Ground; Tender; Decision date; Channels. Text **The decision is final and the cancellation notices and reports will remain due until evidence is recorded.** Footer Keep Tender / destructive **Cancel Tender**.

**Cancelled-detail variant.** Badge Cancelled; show decision actor/time, ground, reason, notice status, PPRA report status and deadlines. No Tender/addendum/inquiry action. Evidence actions appear only to the authorised procurement function for the exact outstanding obligation.

**Visual check.** Authority, ground, finality and unfinished compliance obligations remain distinct.

### 10.14 TPR-DES-13 — Returned and requisition-correction states

**Returned fixture.** Brian Wafula; copied Draft Version 2; 25 Mar 2027, 14:05 EAT. Reuse TPR-DES-04 with amber **Returned for correction** panel containing returned by/time/comment. Select Supplier and contract requirements and show Needs attention. Save/Review available.

**Request-requisition-correction dialog.** Heading **Request a requisition correction?** Reason **The authorised battery-runtime requirement must be corrected before this Tender can continue.** Text **This Tender Version will stop and remain in history. Work can continue only from a newly authorised corrected Requisition.** Footer Cancel / destructive **Request requisition correction**.

**Correction-requested variant.** Use the isolated Requisition correction facts. Brian sees badge **Requisition correction requested**, result **This Tender cannot continue**, Requested by/time/reason/Requisition/current owner. No Save, Submit, Approve or Resume. Actions View requisition status / View history.

**Corrected-successor variant.** Use the isolated Requisition correction facts. Result **A corrected requisition is ready** with Requisition Version 1 and Version 2 separately. Primary **Start corrected Tender Version**. State that it creates a new Draft Version 3 and leaves Version 2 stopped and unchanged.

**Visual check.** Returned work is editable and targeted; Requisition-owned correction is terminal for the current Version.

### 10.15 TPR-DES-14 — Common states

| Variant | Heading | Message | Action |
|---|---|---|---|
| Forbidden | You do not have access to Tenders | This area needs one of these responsibilities: Procurement Officer, Head of Procurement Function, Accounting Officer, Departmental Author, Head of User Department, Auditor or Authorised technical operator. Ask your KenTender administrator to assign one in System setup. | None |
| Not found | Tender not found | This Tender is unavailable or you do not have permission to view it. | Back to Tenders |
| Source unavailable | Authorised requisition unavailable | The requisition is no longer available to start this Tender. | Back to Tenders |
| Already started | Tender already started | This requisition is linked to TND-MOH-2027-033. | For Brian, Open Tender |
| Template unavailable | Tender format unavailable | The standard IT-equipment Tender format is not available. | Back to Tenders |
| Publication not configured | Publication rule unavailable | The publication rule is not configured for this Tender. | Contact administrator |
| Stale write | Tender changed | Another user changed this Tender. | Reload |
| Load failure | Tenders could not be loaded | Try again. | Try again |

Each is a full inline state under KT-STD-001 v1.6 §3A. Successful content never renders behind it. Administrator/System Manager follows technical read and never receives Forbidden.

### 10.16 Artboard inventory

| Artboard | Primary actor | Base purpose | Required variants |
|---|---|---|---|
| TPR-DES-01 | Procurement Officer | Find/start/continue Tender work | Draft; Returned; HOPF; AO; Publishing; Published; Reader; Technical; Empty. |
| TPR-DES-02 | Procurement Officer | Confirm an authorised Requisition start | Unsupported product. |
| TPR-DES-03 | Procurement Officer | Complete Tender details | Physical meeting; Online meeting. |
| TPR-DES-04 | Procurement Officer | Complete supplier and contract requirements | Add/Edit/Remove evidence; full requirement disclosure. |
| TPR-DES-05 | Procurement Officer | Review and submit | Needs attention; submission confirmation. |
| TPR-DES-06 | HOPF | Return or approve package | Return dialog; approval dialog; segregation blocked. |
| TPR-DES-07 | Accounting Officer | Authorise publication | Confirmation; segregation blocked. |
| TPR-DES-08 | HOPF | Confirm channel publication | Online channel; Invalid evidence; Conflicting confirmation; confirmation dialogs. |
| TPR-DES-09 | HOPF / readers | Read effective Published Tender | No addendum; Submission period ended. |
| TPR-DES-10 | Procurement Officer / HOPF | Prepare and issue addendum | HOPF issue; Material change blocked. |
| TPR-DES-11 | Procurement Officer / HOPF | Respond to addendum inquiry | Affects requirements Yes/No. |
| TPR-DES-12 | Accounting Officer | Cancel Tender | HOPF recommendation; confirmation; Cancelled detail. |
| TPR-DES-13 | Procurement Officer / HOPF | Correct returned work or stop for Requisition correction | Correction dialog; stopped; authorised successor. |
| TPR-DES-14 | All permitted roles | Recover from common read/state errors | Forbidden; Not found; unavailable; already started; configuration missing; stale; load failure. |

The design set is complete only when every base artboard and named variant has been rendered and checked against its visual check.

## 11. Functional interaction contract

Section 10 defines appearance and content. This section defines what every visible control does. It is not supplied to the design tool.

### 11.1 General interaction rules

1. A control is shown only when the corresponding server-provided permitted action is present.
2. Opening a page, drawer, dialog, preview or history view never creates or changes a record.
3. A mutation is performed only after the user selects its named action and, where specified, confirms it.
4. The browser never calculates authority, compatibility, readiness, status, publication success, statutory dates or permitted actions.
5. Save actions validate the fields being saved. Decision actions revalidate the entire applicable package on the server.
6. While a mutation is pending, its initiating control is disabled, its label communicates progress, and a second submission is impossible.
7. A successful mutation returns the authoritative record version and permitted actions. The interface replaces stale local state with that result.
8. A failed mutation preserves entered values where safe, focuses the error summary and links field errors to their controls.
9. A stale-write response discards no data silently. The user is told to reload and compare the authoritative record.
10. Cancel and Back close the current transient surface without saving.
11. Browser Back returns to the previous safe route and never repeats a mutation.
12. Dates are displayed in EAT with the timezone shown where a decision, deadline or publication fact could otherwise be ambiguous.
13. Currency uses `KES` and two decimal places. Quantities retain the governed unit of measure.
14. The only optional disclosure patterns are View details, View source, View history and Preview document. Essential decisions, issues and consequences are never hidden.
15. The interface uses the plain labels in §10. Internal enum names, digests, confirmation identities and event identifiers remain technical detail.

### 11.2 Workspace and navigation

| Visible control | Behaviour |
|---|---|
| Work-summary count | Applies the corresponding server-defined queue filter and moves focus to the result heading. |
| Search | Filters by Tender reference, Requisition reference or purchase title after a short input debounce; Enter applies immediately. |
| Status / Financial year | Requests a server-filtered result and resets to page 1. |
| Clear filters | Restores the default permitted queue without changing data. |
| Start Tender | Opens TPR-DES-02 for that exact authorised Requisition handoff. |
| Continue | Opens the current editable Draft at its first incomplete task. |
| Correct | Opens the copied Draft at the task named by the return decision. |
| Review | Opens TPR-DES-06 for the exact submitted Version. |
| Review publication | Opens TPR-DES-07 for the exact approved Version. |
| Complete confirmations | Opens TPR-DES-08 for the exact publication and outstanding channel confirmations. |
| View | Opens the role-safe Tender record. |
| Contact administrator | Opens the configured support instruction; it grants no permission and changes nothing. |

Changing a filter or page never changes the user's authority. An empty filtered result uses §10.15 and retains the active filters until Clear filters is selected.

### 11.3 Starting and editing a Tender

| Visible control | Behaviour |
|---|---|
| View authorised requisition | Opens a read-only drawer from the owner projection. |
| Start Tender | Calls `StartTender`; on success opens TPR-DES-03. |
| Tender details / Supplier and contract requirements | Switches between the two preparation tasks without changing data. |
| Save draft | Calls `SaveTenderDraft` and stays on the current task. |
| Continue | Calls `SaveTenderDraft` and, on success, opens the next task. |
| Review Tender | Calls no mutation; opens TPR-DES-05 using a fresh `GetTenderReview`. |
| View source | Opens the exact inherited source record or snapshot named by the row. |
| Add / Edit evidence requirement | Opens an editor for an officer-authored evidence row. It cannot edit the inherited requirement. |
| Remove evidence requirement | Requires confirmation and removes only an officer-authored Draft row. |
| Preview Invitation / Preview complete Tender | Generates a read-only preview from the current saved Version. Previewing does not freeze or submit it. |
| Show details / Show full requirements | Expands the named read-only section in place and preserves heading/focus context. |

Closing a page with unsaved valid or invalid changes gives **Leave without saving?** with Stay / Leave. No autosave is implied.

### 11.4 Review, submission and correction

| Visible control | Behaviour |
|---|---|
| Issue link | Opens the exact task and focuses the affected field or inherited source route. |
| Submit for approval | Opens the §10.6 confirmation and then calls `SubmitTenderForApproval`. |
| Return for correction | Requires a plain-language comment, then calls `ReturnTenderForCorrection`. A copied Draft is created server-side. |
| Approve Tender package | Opens the §10.7 confirmation and then calls `ApproveTenderPackage`. |
| Reopen Tender | Requires a reason and calls `ReopenApprovedTender`; available only before publication authorisation. |
| Request requisition correction | Opens the §10.14 confirmation and then calls `RequestRequisitionCorrection`. |
| View requisition status | Opens the owner-safe Requisition route. |
| Start corrected Tender Version | Calls `StartCorrectedTenderVersion` for the authorised successor handoff. |

Return comments identify the work to correct but do not replace validation. Reopening never mutates the approved Version; it creates a new copied Draft.

### 11.5 Publication

| Visible control | Behaviour |
|---|---|
| Authorise publication | Opens the §10.8 confirmation and then calls `AuthoriseTenderPublication`. |
| Withdraw publication authorisation | Requires a reason and server confirmation that no channel was confirmed and publication did not occur, then calls `WithdrawPublicationAuthorisation`. |
| Confirm publication | Opens the channel-specific confirmation dialog and calls `ConfirmPublicationChannel`; the HOPF attestation and evidence commit atomically. |
| View confirmation | Opens the immutable channel, availability time, reference/URL, evidence, attestation and actor/time. |

The system derives overall publication after every required channel is confirmed. Reloading, closing the page or repeating an idempotent request changes no confirmed fact. The interface never offers **Mark as published**. No integrated-channel or technical-recovery control appears in MVP; §5.5.1 governs any later facility.

### 11.6 Published Tender, addenda and inquiries

| Visible control | Behaviour |
|---|---|
| Prepare addendum | Calls `CreateAddendumDraft` and opens TPR-DES-10. |
| Save draft | Calls `UpdateAddendumDraft` and retains Draft status. |
| Submit for issue | Calls `SubmitAddendumForIssue`; the server rechecks materiality, deadline and scope. |
| Return for correction | Requires comment and calls `ReturnAddendumForCorrection`. |
| Issue addendum | Opens confirmation and calls `IssueAddendum`; required channel-confirmation records follow. |
| Confirm addendum publication | Opens the channel-specific confirmation dialog and calls `ConfirmAddendumPublicationChannel`. |
| Respond | Opens TPR-DES-11 for the authenticated inquiry. |
| Send response | Calls `RespondToAddendumInquiry`; affected-requirement responses are broadcast without disclosing the asker. |
| View cancellation requirements | Opens TPR-DES-12 without changing status. |
| View or download Invitation / complete Tender / Addendum | Opens or streams the immutable generated document represented by its recorded digest. |
| View public Tender | Opens the supplier-visible published package without internal values, decisions or evidence. |
| View addendum / inquiry | Opens the exact immutable issued addendum or recorded inquiry/response. |
| History and evidence | Expands the permitted read projection; it creates no event and exposes protected facts only to authorised roles. |

An issued addendum appears in the Tender record only after every required channel is confirmed. While channel confirmation is incomplete, the record shows its truthful publishing state.

### 11.7 Cancellation

| Visible control | Behaviour |
|---|---|
| Recommend cancellation | Requires a ground/reason recommendation and calls `RecommendTenderCancellation`; it does not cancel. |
| Cancel Tender | Opens the §10.13 confirmation and then calls `CancelTender`. |
| Record cancellation notice evidence | Records evidence against one required original channel. |
| Record PPRA report evidence | Records the report acknowledgement/reference and date. |
| Record candidate notice evidence | Records dispatch evidence against the governed candidate set. |

After `CancelTender` commits, preparation, publication, addendum and inquiry mutations are absent. Only outstanding compliance-evidence actions remain. Failure or uncertainty in a notice channel does not reopen the Tender.

### 11.8 Common recovery actions

| Visible control | Behaviour |
|---|---|
| Back / Back to Tenders | Returns to the named safe route without mutation. |
| Open Tender | Opens the already-created authorised Tender returned by the conflict result. |
| Reload | Discards stale displayed state only after warning about unsaved local changes, then loads the authoritative record. |
| Try again | Repeats the failed read, not a mutation. |
| Clear filters | Clears the active read filters and reloads the first page. |

No error-state recovery action bypasses permission, readiness, configuration or compatibility.

### 11.9 Accessibility and responsive behaviour

- All functions are keyboard-operable in logical visual order.
- The page has one `h1`; task panels use descending headings and landmarks.
- Issue summaries receive focus after failed validation and link to affected controls.
- Status is expressed in text, not colour alone.
- Tables expose column headers and a meaningful row label. At narrow widths each row becomes a labelled summary card without losing actions or values.
- Dialog focus is trapped while open and returns to the initiating control on close.
- Destructive actions use both a destructive label and a stated consequence; colour alone is insufficient.
- Dynamic publication updates are announced without repeatedly interrupting the user. The page offers manual refresh where live updates are unavailable.
- Generated-document previews have an accessible file name, format, size and Download action.
- All controls and content meet KT-STD-001 v1.6 accessibility and responsive-release gates.

## 12. Audit and historical integrity

### 12.1 Event minimum

Every successful command writes an append-only audit event containing:

- event identity and schema version;
- aggregate identity and resulting record version;
- command name and idempotency key hash;
- actor identity, active responsibility assignment and organisation scope;
- authenticated session or service identity;
- decision or occurrence time in UTC plus the displayed EAT value;
- previous and resulting lifecycle status;
- affected record/version identities;
- reason, comment or statutory ground where required;
- input digest, resulting package digest and rule/template snapshots where applicable;
- channel confirmation, evidence and attestation identities where applicable; and
- source IP/device metadata only to the extent permitted by the security and retention policy.

Rejected commands record a security or operational audit fact where policy requires it, but never create a business event.

### 12.2 Required business evidence

| Business fact | Immutable evidence |
|---|---|
| Tender started | Requisition handoff, requirement snapshot, template/rule snapshots, creating actor/time. |
| Draft saved | Version, changed officer-owned fields, previous/new values and actor/time. |
| Submitted | Exact Version and package/document digests, compatibility result and submitter/time. |
| Returned | Submitted Version, HOPF, time, comment and copied Draft identity. |
| Approved | Exact submitted Version, HOPF, time and package/document digests. |
| Publication authorised | AO, time, approved Version, package digest, rule snapshot and required channel records. |
| Channel confirmed | Channel, actual availability time, reference/URL, evidence digest, exact attestation, HOPF identity/time and package digest. |
| Published | Every mandatory channel confirmation, computed actual invitation time and final publication digest. |
| Addendum issued | Original publication, change comparison, materiality result, revised deadline, HOPF/time, document digest and channel confirmations. |
| Inquiry answered | Authenticated receipt identity, protected source identity, answer, effect classification, responder/time and broadcast digest when required. |
| Tender cancelled | AO, time, applicable ground, reason, optional HOPF recommendation and compliance deadlines. |
| Cancellation obligation completed | Obligation, recipient/channel, evidence digest/reference, occurrence time and recorder/service identity. |

### 12.3 Preservation rules

1. Submitted, approved, publication-authorised, published, issued-addendum and cancelled facts are append-only.
2. A correction creates a new Version or new owner record. It never overwrites the fact that was acted upon.
3. Generated documents are addressed by digest and remain reproducible from their exact recorded inputs.
4. Uploaded publication evidence is retained with content digest, media type, scan result and controlled-access locator. A technically accepted file is not recorded as independent proof that publication occurred.
5. Role reassignment does not rewrite actor history.
6. Display-name changes do not replace the immutable actor identity.
7. Audit access is read-only and scoped. Protected inquiry-source identity is restricted to authorised oversight and investigation use.
8. Retention, legal hold and disposal follow the platform records-management policy; application deletion is not a business-user action.

## 13. Deterministic seed contract

### 13.1 Seed rules

Seed identities and timestamps are stable. Re-running the seed is idempotent: it creates no duplicate Tender, Version, publication, channel confirmation, addendum, inquiry, cancellation or task. All timestamps below are EAT and are stored with their UTC equivalents.

The complete UI fixture values are in §10.1. Seed implementation must use those values rather than substitute lorem ipsum, shortened requirement lists or invented totals.

### 13.2 Actors

| Actor | Responsibility |
|---|---|
| Brian Wafula | Procurement Officer; prepares and submits. |
| Charles Mutiso | Head of Procurement Function; returns, approves, records physical-channel evidence and issues addenda. |
| Amina Hassan | Accounting Officer; authorises publication and owns the isolated cancellation decision. |
| Technical Publisher Service | Reserved future actor for §5.5.1; has no MVP fixture action. |
| Alice Njeri | Auditor; read-only full evidence fixture. |
| Daniel Otieno | Administrator/System Manager; technical read-only fixture. |

Each business actor has a distinct immutable identity and active responsibility assignment. No seed grants an actor a decision merely by changing the displayed role.

### 13.3 Primary lifecycle fixture

| Date and time | Event | Result |
|---|---|---|
| 20 Mar 2027 09:00 | Start from authorised Requisition | `TND-MOH-2027-033`, Draft Version 1. |
| 20 Mar 2027 11:40 | Submit Version 1 | Awaiting procurement approval. |
| 25 Mar 2027 14:00 | Return with the §10.1 comment | Version 1 immutable; Draft Version 2 created. |
| 15 Apr 2027 09:15 | Resubmit Version 2 | Awaiting procurement approval. |
| 20 Apr 2027 10:00 | Approve Version 2 | Approved, publication not authorised. |
| 15 May 2027 07:55 | Authorise publication | Publication and four required Evidence-based channel-confirmation records created. |
| 15 May 2027 08:03 | Confirm State Portal publication | Charles attests availability at 08:00 with the §10.1 reference, URL and evidence. |
| 15 May 2027 08:04 | Confirm Ministry website publication | Charles attests availability at 08:00 with the §10.1 reference, URL and evidence. |
| 15 May 2027 08:06 | Confirm notice-board publication | Charles attests availability at 08:00 with the §10.1 reference and evidence. |
| 15 May 2027 08:07 | Confirm two-newspaper publication | Charles attests both editions were available at 08:00; final channel confirms and `published_at` = 15 May 2027 08:00. |
| 31 May 2027 09:00 | Issue and fully publish `ADD-MOH-2027-033-001` | Issued through all four channels; deadline revised to 12 Jun 2027 11:00. |
| 1 Jun 2027 09:00 | Receive authenticated inquiry | Inquiry awaiting response. |
| 1 Jun 2027 11:00 | Send no-effect response | Inquiry Answered; no broadcast. |
| 12 Jun 2027 11:00 | Submission deadline reached | Submission period ended; immutable handoff available. |

The seed includes snapshots, digests, generated documents, tasks, audit events and authorised read projections needed to prove every row.

### 13.4 Isolated state fixtures

| Fixture | Required isolated state |
|---|---|
| Unsupported start | `REQ-MOH-2027-038-001` with Product Software integration; TPR-DES-02 shows the unsupported result and creates no Tender. |
| Needs-attention review | Draft with Inspection and acceptance location empty; TPR-DES-05 shows the exact Must fix item and disables submission. |
| Draft complete | Primary Tender immediately before 15 Apr resubmission. |
| Awaiting HOPF | Primary Tender immediately after 15 Apr resubmission. |
| Awaiting AO | Primary Tender immediately after 20 Apr approval. |
| Publication evidence rejected | `TND-MOH-2027-035` with the invalid State Portal file in §10.1; channel remains Awaiting confirmation. |
| Conflicting confirmation | `TND-MOH-2027-036` with an immutable State Portal confirmation and rejected conflicting replay. |
| Evidence required | Separate authorised publication with two channels confirmed and two channel confirmations outstanding. |
| Segregation blocked | Actor responsible for an earlier Version decision views the prohibited later decision. |
| Correction requested | Separate Tender Version stopped for owner correction, plus an authorised successor variant. |
| Material addendum | Separate open Tender `TND-MOH-2027-039` whose quantity change from 250 Each to 300 Each expands scope; issue action absent. |
| Cancellation | `TND-MOH-2027-034`, Published — open, cancelled by Amina Hassan on 4 Jun 2027 14:00 for inadequate budgetary provision. |
| Cancelled obligations | Same cancellation with notice and report states separately Due, Recorded and Overdue. |

An isolated fixture must never reuse an event identity, confirmation identity, document digest or decision timestamp to prove an opposite outcome.

## 14. Acceptance contract

Each criterion is independently testable. Passing a visual example without passing the underlying command, authority, audit and owner-boundary checks is insufficient.

### 14.1 Entry, scope and inheritance

| ID | Acceptance criterion |
|---|---|
| TPR08-AC-001 | The authenticated application exposes one user-facing menu item named **Tenders**, not separate Preparation and Publication modules. |
| TPR08-AC-002 | The Tenders workspace combines authorised Requisition starts, Draft work, decisions, publication work and open Tenders in one role-safe queue. |
| TPR08-AC-003 | A user without a permitted responsibility receives the §10.15 Forbidden state and no Tender data. |
| TPR08-AC-004 | A user with permitted cross-entity scope sees only records in that scope; changing a filter cannot expand it. |
| TPR08-AC-005 | Opening a route, drawer, preview or dialog creates no Tender, Version, publication, task or audit business event. |
| TPR08-AC-006 | A Tender can start only from an available authorised Requisition handoff whose compatibility result permits start. |
| TPR08-AC-007 | Concurrent or repeated `StartTender` requests for one handoff produce one Tender and return its identity. |
| TPR08-AC-008 | Start snapshots the exact authorised Requisition, requirements, Planning references, method, reservation, lotting, funding and applicable governed templates/rules. |
| TPR08-AC-009 | Inherited content is visibly read-only and has a route to its source; the Tender service cannot update owner data directly. |
| TPR08-AC-010 | Requisition-owned correction stops the current Tender Version and can continue only from a newly authorised successor handoff. |

### 14.2 Preparation and generated content

| ID | Acceptance criterion |
|---|---|
| TPR08-AC-011 | Preparation is presented as three understandable tasks: Tender details; Supplier and contract requirements; Review and submit. |
| TPR08-AC-012 | Tender details show the purchase, quantities, funding and source facts before officer-authored fields. |
| TPR08-AC-013 | Closing date/time, clarification deadline and meeting choices validate as dates and as an ordered business sequence. |
| TPR08-AC-014 | A physical meeting requires date/time, venue and access instructions; an online meeting requires date/time and join instructions. |
| TPR08-AC-015 | Supplier and contract requirements separate inherited requirements, officer evidence requirements, contract values and generated content; comparable-contract count and experience period are positive whole-number inputs with no preset value menu. |
| TPR08-AC-016 | An officer can add, edit and remove only Draft evidence requirements; each change is versioned and audited. |
| TPR08-AC-017 | Qualification or evidence wording cannot silently alter an inherited mandatory technical, warranty or acceptance requirement. |
| TPR08-AC-018 | The generated price schedule contains the exact authorised line items, quantities, units, lots and funding split. |
| TPR08-AC-019 | The generated technical schedule contains all eleven §10.1 technical requirements without truncation or substitution. |
| TPR08-AC-020 | The generated warranty/support schedule contains all six §10.1 values and the acceptance schedule all five checks. |
| TPR08-AC-021 | Optional service/material schedules are absent when their inherited source sets are empty and present only when governed data exists. |
| TPR08-AC-022 | Generated evaluation mappings trace every scored or mandatory criterion to its governed source and cannot be edited as free text. |
| TPR08-AC-023 | Invitation and complete-Tender previews use saved Version data and do not submit, approve, authorise or publish. |
| TPR08-AC-024 | Document generation is deterministic: identical recorded inputs produce the recorded document digest. |
| TPR08-AC-025 | Save returns the authoritative record version; a stale save never overwrites another user's change. |

### 14.3 Review, approval and segregation

| ID | Acceptance criterion |
|---|---|
| TPR08-AC-026 | Review displays one readiness result, issue counts and direct issue links; it does not require users to interpret internal rule identifiers. |
| TPR08-AC-027 | A Must fix issue prevents submission and identifies the exact task, field or owner route. |
| TPR08-AC-028 | A Review note is visible but does not prevent submission unless another governed rule fails. |
| TPR08-AC-029 | Compatibility is evaluated from authoritative owner projections at start, submit, approve and publication authorisation. |
| TPR08-AC-030 | Submission freezes one exact Version, package digest and generated-document set. |
| TPR08-AC-031 | After submission, the submitted Version is read-only to every business actor. |
| TPR08-AC-032 | HOPF return requires a comment, preserves the submitted Version and creates one copied Draft. |
| TPR08-AC-033 | HOPF approval records the exact submitted Version and package digest and creates an AO publication task. |
| TPR08-AC-034 | HOPF approval does not create channel confirmations, set `published_at` or expose documents to suppliers. |
| TPR08-AC-035 | A person who prepared or submitted a Version cannot approve that Version as HOPF, regardless of concurrent role labels. |
| TPR08-AC-036 | Reopening an approved Tender is possible only before publication authorisation, requires a reason and creates a copied Draft. |
| TPR08-AC-037 | HOPF, AO and reader artboards use the exact fixture actors, values and statuses in §10.1. |
| TPR08-AC-038 | The AO sees the approved package, decision facts and generated required channels, with no package-edit control. |
| TPR08-AC-039 | A person who prepared, submitted or HOPF-approved a Version cannot authorise its publication as AO. |
| TPR08-AC-040 | Every decision command rechecks state, assignment, segregation and package integrity on the server. |

### 14.4 Publication

| ID | Acceptance criterion |
|---|---|
| TPR08-AC-041 | Publication authorisation records AO, time, approved Version, package digest, effective rule snapshot and complete required-channel set atomically. |
| TPR08-AC-042 | The AO cannot choose, remove, replace or edit a required publication channel. |
| TPR08-AC-043 | Committing publication authorisation creates one Evidence-based confirmation record for every required channel and makes no external publication call or success claim. |
| TPR08-AC-044 | The MVP contains no active State Portal, Ministry website or other publication adapter; Configuration rejects `Integrated acknowledgement`. |
| TPR08-AC-045 | Each required channel has one stable confirmation identity bound to the exact publication and package digest. |
| TPR08-AC-046 | Only a currently assigned HOPF can confirm channel publication; the AO, technical operator and Procurement Officer cannot attest it. |
| TPR08-AC-047 | Confirmation records the exact required attestation, server-derived HOPF identity/time and actual channel availability time atomically. |
| TPR08-AC-048 | System checks are limited to record completeness, format, authority, identity, file integrity/scan and conflicts; no result claims independent proof of real-world publication. |
| TPR08-AC-049 | Confirmation requires availability time, evidence reference, applicable public URL, required evidence file/digest and HOPF attestation; optional notes are stored only when present and limited to 500 characters. |
| TPR08-AC-050 | Uploaded evidence is scanned, digested and retained; failed or rejected uploads cannot confirm a channel. |
| TPR08-AC-051 | A Tender is not Published while any mandatory channel is Awaiting confirmation or has missing, invalid or rejected confirmation evidence. |
| TPR08-AC-052 | `published_at` is written once as the latest actual availability time among all mandatory channel confirmations. |
| TPR08-AC-053 | On publication confirmation, the minimum preparation period is revalidated from actual `published_at`; an invalid deadline cannot become Published. |
| TPR08-AC-054 | The exact actual invitation date is written once to Planning through its owner contract and replay is idempotent. |
| TPR08-AC-055 | Publication authorisation can be withdrawn only while confirmed unpublished and before any channel confirmation; reason and decision remain auditable. |

### 14.5 Open period, addenda, inquiries and cancellation

| ID | Acceptance criterion |
|---|---|
| TPR08-AC-056 | A Published Tender shows actual publication time, submission deadline, documents, channel evidence, addenda and inquiries in one record. |
| TPR08-AC-057 | `CreateAddendumDraft` is unavailable before publication, after submission close or after cancellation. |
| TPR08-AC-058 | An addendum records an explicit before/after comparison, affected reference, reason and materiality explanation. |
| TPR08-AC-059 | An addendum that expands quantity, value, scope, method, reservation, lotting, package structure, technical requirement or evaluation basis cannot be issued. |
| TPR08-AC-060 | A late non-material addendum calculates and requires the lawful revised submission deadline before submission for issue. |
| TPR08-AC-061 | HOPF issue freezes the addendum and creates Evidence-based confirmation records for every original required channel. |
| TPR08-AC-062 | The addendum becomes Issued only after HOPF confirms all required channels with the same evidence and attestation semantics as the original publication. |
| TPR08-AC-063 | An inquiry can originate only from an authenticated candidate-service event tied to an issued addendum. |
| TPR08-AC-064 | A response classified as affecting a Tender requirement is sent to all registered candidates without identifying the asker and records a broadcast digest. |
| TPR08-AC-065 | A response classified as not affecting a requirement is sent to the asker and remains fully auditable. |
| TPR08-AC-066 | Only the AO can cancel; cancellation requires an applicable ground and reason and becomes final immediately on commit. |
| TPR08-AC-067 | Cancellation never restores the Requisition, reopens the Tender or creates a replacement procurement automatically. |
| TPR08-AC-068 | Cancellation creates independently tracked notice-publication, candidate-notice and PPRA-report obligations with truthful due/recorded/overdue states. |

### 14.6 Usability, accessibility, audit and boundaries

| ID | Acceptance criterion |
|---|---|
| TPR08-AC-069 | Every artboard in §10 can be implemented using §10.1 plus KT-STD-001 v1.6 §2 without invented fixture data. |
| TPR08-AC-070 | Every visible action in §10 has exactly one behaviour in §11 and is absent when the server does not permit it. |
| TPR08-AC-071 | The default interface exposes no event keys, hashes, enum values, payloads, transport retries or infrastructure configuration. |
| TPR08-AC-072 | A Procurement Officer can start, complete and submit the primary fixture by following the three task labels without separate training on system states. |
| TPR08-AC-073 | HOPF and AO each see one plain-language decision, its consequence and the exact content being decided. |
| TPR08-AC-074 | Status, stage and next action remain distinct; the interface never labels approval, evidence upload or technical validation as confirmed publication. |
| TPR08-AC-075 | All tables and dialogs meet the keyboard, focus, heading, error-linking, text-status and responsive rules in §11.9. |
| TPR08-AC-076 | Every successful decision, publication, addendum, inquiry and cancellation command writes the minimum audit evidence in §12. |
| TPR08-AC-077 | Generated and external evidence remains retrievable by immutable digest under authorised audit access. |
| TPR08-AC-078 | The §13 seed can be rerun without duplication and proves the primary and isolated state fixtures independently. |
| TPR08-AC-079 | Owner-contract failure leaves source data unchanged, records a truthful pending/failure state where applicable and supports safe idempotent recovery. |
| TPR08-AC-080 | Representative Procurement Officer, HOPF and AO usability tests complete their assigned routine tasks without moderator explanation, material error or recourse to internal terminology. |

## 15. Implementation and verification constraints

### 15.1 Required implementation order

1. Implement schemas, invariants, authority checks and owner-contract fakes.
2. Implement commands and audit events using test-driven state transitions.
3. Implement deterministic document generation and digest verification.
4. Implement evidence storage, publication-confirmation commands and truthful status derivation.
5. Implement role-safe read projections and task generation.
6. Implement the §10 artboards against the real service contracts.
7. Run representative-user, accessibility, security, resilience and release-gate verification.

No UI prototype is evidence that its backing authority or lifecycle rule exists.

### 15.2 Automated test minimum

- unit tests for every §5 transition and invariant;
- property tests for totals, dates, period calculations and status derivation;
- schema tests for money precision, quantity/unit preservation, timestamps and immutable digests;
- contract tests for Requisition, Planning, Configuration, identity/task, candidate, document and Bid Submission boundaries;
- command tests for assignment, scope, segregation, optimistic concurrency and idempotency;
- document snapshot tests for all §10.1 requirement and schedule values;
- publication-confirmation tests for missing reference, missing applicable URL, missing evidence, missing attestation, replay, conflicting confirmation and concurrent final-channel confirmation;
- evidence tests for media-type rejection, malware scan failure, digest mismatch, retention and access control;
- browser tests for every §10 artboard and §11 action;
- accessibility tests plus manual keyboard and screen-reader checks;
- end-to-end tests for the §13 primary lifecycle and every isolated state fixture; and
- security tests for horizontal access, role elevation, protected inquiry identity and direct-command forgery.

### 15.3 Publication-confirmation integrity tests

The test harness must prove at least these integrity and concurrency boundaries:

1. authorisation is committed before the HOPF opens the confirmation screen;
2. an identical duplicate confirmation is idempotent;
3. a replay with a different availability time, reference, URL or evidence digest is rejected as a conflict;
4. an evidence upload succeeds but the confirmation transaction fails, leaving no Confirmed state and allowing safe cleanup or reuse of the upload;
5. invalid media or a failed malware scan cannot confirm a channel;
6. evidence or a confirmation package bound to a different package digest is rejected;
7. two concurrent confirmations of the final outstanding channel produce one authoritative result; and
8. replay of internal Tender-published or Planning-owner events is idempotent.

In every case, one authoritative business outcome and a complete immutable confirmation history result.

If the future facility in §5.5.1 is activated, its approved integration contract must add separate adapter, acknowledgement, uncertain-result, recovery and operational tests before release. Those tests are not part of the MVP.

### 15.4 Release gates

Release requires:

- all TPR08 acceptance criteria passing;
- no unresolved Must fix compatibility or security issue;
- validated owner contracts and migration/seed idempotency;
- exact rendered artboard review under KT-STD-001 v1.6;
- representative-user evidence for Procurement Officer, HOPF and AO routine journeys;
- publication-confirmation integrity evidence from §15.3;
- accessible PDF/downloaded document verification; and
- production support runbooks for evidence rejection, conflicting confirmation, failed confirmation transactions and overdue cancellation obligations.

## 16. Prohibited shortcuts

The implementation shall not:

1. create separate Tender Preparation and Tender Publication workspaces for the same proceeding;
2. expose document-template authoring or publication-rule configuration inside Tenders;
3. let a Tender user edit inherited Requisition, Planning, Budget or Configuration facts;
4. treat a PDF upload as a substitute for structured inherited requirements;
5. let the officer type generated quantities, totals, schedules or evaluation mappings that owner data can produce;
6. use approval, evidence upload, technical validation or local persistence as evidence of publication;
7. provide **Mark as published** or any confirmation path that bypasses the HOPF's explicit attestation and required evidence;
8. activate or configure integrated acknowledgement in MVP, or later activate it without satisfying the gate in §5.5.1;
9. allow the AO to edit the package or choose publication channels;
10. allow HOPF approval to publish or AO publication authorisation to confirm publication;
11. collapse HOPF and AO decisions into one generic approval;
12. evaluate segregation from a current role label without checking immutable Version actors;
13. overwrite a submitted, approved, published, issued or cancelled record to make a correction;
14. infer a missing configuration rule or statutory threshold from hard-coded UI logic;
15. issue a material scope, quantity, value, method, reservation, lotting, technical or evaluation change as an addendum;
16. accept a manually invented inquiry that bypasses the authenticated candidate boundary;
17. disclose the identity of an inquiry source in a requirement-affecting broadcast;
18. let failed cancellation notices reopen the Tender or reverse the AO decision;
19. restore a Requisition or create a replacement Tender automatically after cancellation;
20. hide required action or legal consequence inside an unlabeled disclosure;
21. display internal statuses, hashes, event names or technical integration controls to routine business users;
22. restrict comparable-contract count or experience period to an arbitrary preset menu; or
23. claim conformance from screenshots alone without service, audit, integrity and representative-user evidence.

## 17. Normative references and precedence

| Reference | Governs |
|---|---|
| Public Procurement and Asset Disposal Act, 2015, including §§63, 74, 75, 78, 89 and 96–98 as applicable | Cancellation, tender documents, addenda, submission periods, publication and access obligations. |
| Public Procurement and Asset Disposal Regulations, 2020, including Regulations 33, 48, 49, 56, 57, 85 and 86 as applicable | Procurement-function duties, cancellation, e-procurement publication, addendum inquiries and advertising-channel rules. |
| KenTender LAW-REG-001 | Accepted statutory correction decisions and controls. |
| KT-STD-001 v1.6 | Document structure, static design contract, accessibility and verification. |
| PLN-CHG-001 v1.20 | Approved Plan Item, funding, method, reservation, actual invitation date and owner commands. |
| REQ-CHG-001 v1.9 | Authorised Requisition handoff, inherited structured requirements and correction route. |
| CFG-CHG-002 v0.11 | Effective templates, rule snapshots, channel rules and support configuration. |
| Platform identity, task, document, records and security contracts | Authentication, assignment, tasks, evidence storage, retention and access control. |

If a lower-level implementation note conflicts with this contract, this contract controls the Tenders behaviour. If this contract conflicts with applicable law, the law controls and the affected rule must be escalated before implementation; the system must not silently improvise a legal interpretation.

## 18. Approval effect

This document is **Approved** as the complete implementation contract for the user-facing Tenders module described here. Approval confirms the product and control design; it is not evidence that the software has been implemented, deployed, legally re-verified or accepted in production.

Implementation completion requires the acceptance and release evidence in §§14–15.

## 19. Re-implementation register

This register is the build checklist. Each row states a required target capability, its controlling contract and the evidence needed to close it.

| ID | Required implementation | Contract | Completion evidence |
|---|---|---|---|
| TPR-IMP-001 | Create one **Tenders** menu entry and the three routes in §9. | §§1, 9 | Route/menu test and TPR-DES-01 screenshot. |
| TPR-IMP-002 | Build one role-safe workspace covering starts, preparation, decisions, publication and open Tenders. | §§6, 10.2, 11.2 | AC-002–004 browser and scope tests. |
| TPR-IMP-003 | Implement server-derived work-summary counts, filters and next actions. | §§7.1, 10.2, 11.2 | Projection and browser tests. |
| TPR-IMP-004 | Implement the exact `Tender` and `TenderVersion` schemas, identities, statuses and concurrency versions. | §§4.1–4.2 | Migration/schema and transition tests. |
| TPR-IMP-005 | Implement immutable inherited requirement snapshots and owner-source links. | §4.3 | Snapshot/digest and owner-boundary tests. |
| TPR-IMP-006 | Implement officer-authored evidence requirements separately from inherited requirements. | §4.4 | CRUD, authority and audit tests. |
| TPR-IMP-007 | Generate price, technical, warranty, acceptance, delivery and evaluation content deterministically. | §4.5, §10.1 | Document snapshot and digest tests. |
| TPR-IMP-008 | Integrate the authorised Requisition handoff and idempotent start command. | §§3, 7.2 | Contract, duplicate-start and failure tests. |
| TPR-IMP-009 | Implement the three-task preparation journey and unsaved-change protection. | §§10.4–10.6, 11.3 | Representative-user and browser tests. |
| TPR-IMP-010 | Implement meeting-type conditional fields, ordered date validation and positive-whole-number supplier-experience controls without preset menus. | §§5.2, 10.4–10.5 | Field, business-date and input-boundary tests. |
| TPR-IMP-011 | Implement money/quantity/unit precision and funding/line-item reconciliation. | §§4–5 | Property and schema tests. |
| TPR-IMP-012 | Implement compatibility checks at start, submit, approve and publication authorisation. | §5.3 | Eight-gate tests at all four boundaries. |
| TPR-IMP-013 | Implement deterministic Must fix and Review note results with exact issue routes. | §5.4, §10.6 | Review projection and focus-link tests. |
| TPR-IMP-014 | Implement Draft save commands with optimistic concurrency and idempotency. | §§7.2, 11.1 | Stale-write and replay tests. |
| TPR-IMP-015 | Implement deterministic Invitation and complete-Tender generation and preview. | §§4.5, 7.1, 11.3 | Digest and accessible-document tests. |
| TPR-IMP-016 | Implement submission as an immutable Version/package freeze. | §§5.1, 7.2, 12 | AC-030–031 and audit tests. |
| TPR-IMP-017 | Implement HOPF return with required comment and one copied Draft. | §§5.1, 7.2, 10.7 | Transition/idempotency tests. |
| TPR-IMP-018 | Implement HOPF approval without publication-confirmation side effects. | §§5.1, 7.2 | Authority and no-confirmation tests. |
| TPR-IMP-019 | Implement approved-Tender reopening before authorisation only. | §§5.1, 7.2, 11.4 | State, reason and version tests. |
| TPR-IMP-020 | Implement Requisition-correction stop and authorised-successor route. | §§3, 5.1, 10.14 | Owner-contract and terminal-Version tests. |
| TPR-IMP-021 | Enforce immutable-actor maker-checker rules for HOPF and AO decisions. | §6 | Multi-role and reassignment tests. |
| TPR-IMP-022 | Implement `TenderPublication` with approved package, rule snapshot and AO decision. | §4.6 | Schema, digest and decision tests. |
| TPR-IMP-023 | Resolve and snapshot required publication channels from governed configuration; enforce Evidence based mode for every MVP channel and reject Integrated acknowledgement. | §§3, 5.5–5.5.1 | Configuration contract, mode-rejection and no-user-choice tests. |
| TPR-IMP-024 | Implement AO publication authorisation as one decision that atomically creates the required evidence-based confirmation records without an external publication call. | §§5.5, 7.3 | Atomicity, authority and no-external-call tests. |
| TPR-IMP-025 | Implement stable `PublicationChannelConfirmation` identities bound to the exact publication and package digest. | §4.7 | Schema, binding, idempotent replay and conflict tests. |
| TPR-IMP-026 | Implement HOPF confirmation for State Portal and Ministry website using channel-specific reference, public URL, evidence and attestation. | §§4.7, 5.5, 7.3, 10.9 | Authority, URL, evidence, attestation and browser tests. |
| TPR-IMP-027 | Implement HOPF confirmation for notice-board and newspaper channels using channel-specific reference, evidence, attestation and optional 500-character notes. | §§4.7, 5.5, 7.3, 10.9, 11.5 | Upload, scan, digest, reference/notes, attestation and authority tests. |
| TPR-IMP-028 | Implement truthful Awaiting confirmation and Confirmed states, with rejected input remaining unconfirmed. | §§4.7, 5.5 | State-machine, derivation and display tests. |
| TPR-IMP-029 | Implement technical validation for confirmation completeness, authority, identity, evidence integrity/scan and package binding without claiming factual publication. | §§4.7, 5.5, 7.3 | Validation-boundary and false-success tests. |
| TPR-IMP-030 | Implement idempotent identical replay and reject any conflicting second confirmation. | §§5.5, 7.3, 11.5 | Replay, conflict and immutable-history tests. |
| TPR-IMP-031 | Compute one immutable actual publication time from all mandatory channel evidence. | §5.5 | Concurrent-final-confirmation tests. |
| TPR-IMP-032 | Revalidate the minimum preparation period against actual publication time. | §5.5 | Boundary-date tests. |
| TPR-IMP-033 | Write actual invitation date once through the Planning owner contract. | §§3, 5.5 | Owner-contract and replay tests. |
| TPR-IMP-034 | Implement withdrawal of publication authorisation with reason only before any channel is confirmed. | §§5.1, 7.3 | Positive and prohibited-state tests. |
| TPR-IMP-035 | Implement the published-Tender view with documents, evidence, addenda and inquiries. | §10.10 | Role and artboard tests. |
| TPR-IMP-036 | Implement Addendum schema, Draft save, materiality and deadline rules. | §§4.8, 5.6 | Material/non-material/date tests. |
| TPR-IMP-037 | Implement HOPF addendum issue and evidence-based confirmation through every original required channel. | §§5.6, 7.4 | Authority, digest, evidence, attestation and channel tests. |
| TPR-IMP-038 | Implement authenticated candidate inquiry ingestion and protected source identity. | §§3, 4.9 | Contract, access and forgery tests. |
| TPR-IMP-039 | Implement inquiry response classification and anonymised broadcast when required. | §§4.9, 7.4, 11.6 | Direct/broadcast and privacy tests. |
| TPR-IMP-040 | Implement AO cancellation with applicable ground, reason and immediate final state. | §§4.10, 5.7 | Authority, ground and finality tests. |
| TPR-IMP-041 | Implement optional HOPF cancellation recommendation without decision effect. | §§5.7, 7.4 | Independence and audit tests. |
| TPR-IMP-042 | Create and track cancellation channel, candidate-notice and PPRA-report obligations. | §§4.10, 5.7 | Due/recorded/overdue state tests. |
| TPR-IMP-043 | Preserve cancellation finality while required cancellation evidence remains due, is rejected or becomes overdue. | §§5.7, 11.7 | Due/rejected/overdue and finality tests. |
| TPR-IMP-044 | Implement role-safe reads for Department, Auditor, technical operator and Administrator/System Manager. | §§6–7 | Field-level access and action-absence tests. |
| TPR-IMP-045 | Implement every plain-language error and recovery route in §8. | §8 | Error-contract and browser tests. |
| TPR-IMP-046 | Implement all fourteen artboards and stated variants from the self-contained fixture pack. | §10 | Rendered design verification. |
| TPR-IMP-047 | Implement every visible control exactly as defined in §11, including pending and error behaviour. | §11 | Action-coverage and duplicate-submit tests. |
| TPR-IMP-048 | Implement keyboard, focus, status-text, responsive-table and document-accessibility rules. | §11.9 | Automated and manual accessibility evidence. |
| TPR-IMP-049 | Implement append-only audit and evidence preservation for every fact in §12. | §12 | Audit completeness and tamper tests. |
| TPR-IMP-050 | Implement the idempotent primary and isolated fixture seeds without outcome conflation. | §13 | Two-run seed comparison and fixture tests. |
| TPR-IMP-051 | Complete every acceptance criterion and automated test minimum. | §§14–15 | Signed test report with zero failed mandatory criteria. |
| TPR-IMP-052 | Complete representative-user tests for Procurement Officer, HOPF and AO routine journeys. | §§14.6, 15.4 | Observed completion evidence and resolved findings. |
| TPR-IMP-053 | Complete publication-confirmation integrity/concurrency exercises and operational runbooks. | §§15.3–15.4 | Integrity report and approved runbooks. |
| TPR-IMP-054 | Verify that every prohibited shortcut is absent from code, configuration and UI. | §16 | Architecture/code review checklist. |
| TPR-IMP-055 | Produce the immutable Bid Submission handoff at submission close. | §§1, 3, 5.1 | Consumer contract and end-to-end handoff test. |
