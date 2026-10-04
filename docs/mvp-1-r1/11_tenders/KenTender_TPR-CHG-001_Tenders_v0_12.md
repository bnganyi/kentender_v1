# TPR-CHG-001 — Tenders: Preparation and Publication

| Control | Value |
|---|---|
| Document ID | TPR-CHG-001 |
| Version | **0.12** |
| Date | 26 September 2026 |
| Revision record | Same-day v0.12 correction, 26 September 2026: replaces the obsolete Draft progress row and supplies KT-STD-001 v1.8 journey, next-step, guard and hand-off detail. The Project Owner approved the reviewed v0.12 on 26 September 2026 without a version increment. |
| Status | **Approved** — Project Owner, 26 September 2026; supersedes unapproved v0.11 |
| User-facing module | **Tenders** |
| Product | `IT-EQUIPMENT-OPEN-V1` — straightforward off-the-shelf IT equipment using the PPRA Goods Standard Tender Document |
| Starts from | One authorised, unconsumed `AuthorisedRequisitionHandoff v1.3` |
| Ends at | One immutable Tender package that is unpublished, published and open, cancelled, or closed for submission |
| Governing standard | KT-STD-001 v1.8 |
| Owner contracts | REQ v1.12, PLN v1.27, BUD v1.11, NDS v1.14, CFG v0.16, STR v1.8, AUTH v1.10, SEED v1.3, STD-STD-001 v1.1, STD-TPL-001 v0.10, STD-TPL-IMP-001 v1.1 and BDS v0.7 |
| Implementation authority | This approved v0.12 is the Tender implementation baseline. Production release remains subject to §§14–15. Under OD5, the template release needs no separate approval or commissioning step; a new Tender can start only on an intact release that is installed, Available and switched On on the site (§5.3). |
| v0.11 closure scope (retained) | Retains the v0.10 public/vendor closure and adds exact behaviour for Tenders bound to Superseded or Withdrawn STD releases. New binding remains Available-only; no lifecycle event silently rebinds a Tender. v0.12 adds that a new binding also requires the release to be switched On on the site. |
| v0.12 closure scope | Owner decision OD5 and KT-STD-001 v1.8 workflow guidance. A template release is an On/Off switch on the site. A new Tender binds only a release that is Available and switched On on the site. A Tender already bound to a release continues as in v0.11: Available (switched On or Off) or Superseded while integrity and renderer checks pass; Withdrawn blocks. Switching a release Off never strands a started Tender and never rebinds one. No other Tender business rule changes; §§5.9–5.11 and 10.17 specify the existing lifecycle guidance and hand-offs. |
| v0.12 owner decision | OD5, Project Owner, 26 September 2026: “I don't want this complicated admin overhead regarding approvals and commissioning of templates. It is unnecessary, adds no value and is vexing. Allow development work to contine without this friction. Template release is purely an on and off switch on an affected site. Update this decision as a follow up to reflect in affected documents if necessary” |
| v0.12 update instruction | Project Owner, 26 September 2026: “Close the open issues” |

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
7. While open, governed supplier clarifications, addenda, candidate notices and cancellation remain part of the same Tender record.
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
- support governed supplier clarifications before the clarification deadline, whether or not an addendum already exists;
- require an issued addendum before any clarification answer can change the published Tender;
- notify the authoritative Tender-bound candidate set of addenda, general clarification broadcasts, deadline changes and cancellation without fabricating delivery;
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
- unreserved procurement and reserved procurement for Youth, Women and Persons with disabilities;
- the independently applicable County-residents restriction for a county Procuring Entity when its verified rule and overlap treatment are available;
- one Invitation and one complete issued Tender;
- configured publication channels for national Open Tender;
- publication, pre-bid clarifications, non-material addenda, mandatory candidate notices and pre-submission cancellation; and
- one actual invitation event written to Planning.

### 2.3 Excluded

- software development, systems implementation, integration, migration or hosting procurements;
- Works, consulting or non-consulting-services products;
- international, restricted, direct, two-stage or request-for-proposals methods;
- multiple lots, multiple award packages or multiple currencies;
- a reservation category or County-residents treatment not supported by the exact installed template release or lacking an applicable verified rule;
- operational template, clause, schema, workflow, channel or evaluation configuration from the Tender UI;
- editing an authorised Requisition inside Tenders;
- Procurement Officer entry of supplier prices or supplier responses;
- weighted-scoring builders or evaluator-created criteria;
- substantive expansion or replacement of published requirements through an addendum;
- bid submission, electronic tender-box custody, tender opening, evaluation, award, contract formation or execution;
- generic chat, private officer messaging or supplier-to-supplier communication;
- passive Tender following or a separate declaration-of-interest step in this MVP—candidate registration occurs only through **Start bid**;
- asserting any Planning milestone after the actual invitation date; and
- treating approval, an unsupported integration assumption, an unevidenced assertion or technical record acceptance as proof that publication succeeded.

## 3. Ownership and dependency boundary

| Information or action | Owner | Tenders treatment |
|---|---|---|
| Approved purchase, source allocations, method, schedule boundaries and Strategic objective | Planning / authorised Requisition | Inherit read-only; internal context only where stated. |
| Funding reservation and Budget lineage | Budget / authorised Requisition | Preserve exact reservation/source identities as internal evidence; never render as supplier price. |
| Requirement title, need, expected result, equipment, quantities, delivery, technical requirements, support, services, acceptance and supporting materials | Authorised Requisition | Inherit read-only and generate the Tender schedules and obligations. |
| Reservation category, County-residents restriction and lotting | Authorised Requisition | Inherit read-only with exact effective rule snapshots. Require a template-supported category, applicable County-residents treatment and `Single lot`. Planning designation is not bidder entitlement. |
| Standard wording, forms, response rules and downstream mappings | Installed template release | Bind one immutable Available release and exact digests; operational users cannot edit, activate or choose another release. v0.12 (OD5): the release bound to a new Tender must also be switched On on the site; whether a release is switched On is set outside Tenders. Administrator, System Manager, Procurement Officer and HOPF may inspect it through **STD Templates** under the bounded read/concern contract. |
| Tender title, dates, security, meeting, supplier evidence and finite contract parameters | Procurement Officer | Enter only through the controls in §5.2. |
| Tender package approval | Head of Procurement Function | Return or approve one immutable Version; cannot edit it. |
| Advertising rule and required channels | Configuration | Resolve from effective-dated configuration and snapshot at publication authorisation. |
| Publication authorisation | Accounting Officer | One explicit decision on the approved immutable Version. |
| Publication through every required channel | Head of Procurement Function | Carry out publication outside KenTender where necessary, then confirm the actual availability time with channel-appropriate evidence and explicit attestation. |
| Future automated acknowledgement | Approved publication adapter | Not an MVP capability. It may replace HOPF confirmation for a channel only after the real interface, authority, acknowledgement and recovery contract are approved, configured and tested. |
| Actual invitation date | Tenders | Set once when every required channel is confirmed; publish once to Planning. |
| Addendum drafting | Procurement Officer or Head of Procurement Function | Draft one structured non-material change against current published content. |
| Addendum issue | Head of Procurement Function | Decide and publish the immutable addendum through the original required channels. |
| Tender-bound candidate registration and notice address | Bid Submission | **Start bid** atomically creates or confirms the supplier arrangement/candidate registration and its verified mandatory-notice address. Tenders consumes the owner projection; it does not create or edit supplier contacts. |
| Supplier clarification | Bid Submission | Supply one authenticated question from a registered Tender candidate. Tenders records, classifies and answers it; Bid Submission holds no parallel message store. |
| Candidate notices | Tenders / platform notification outbox | Tenders freezes the exact candidate audience for each notice and records delivery attempts. Bid Submission supplies current verified addresses; delivery failure never becomes false receipt or changes Tender effectiveness. |
| Public Tender support and legal/accessibility links | Configuration | Consume the read-only bidder-safe CFG projection. Tenders neither hard-codes nor edits these values and exposes no setup audit data. |
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
| `template_release_id`, `template_key`, `template_release`, `product_profile_id`, `renderer_profile_id`, `supported_renderer_version` | Exact Available installed release, display release and supported runtime profiles bound when the first Draft is created. v0.12 (OD5): at that moment the release must also be switched On on the site. `template_release_id` is the opaque STD `release_id`; `template_release` is the display value. |
| `official_source_digest`, `bundle_digest`, `response_rules_digest`, `downstream_rules_digest`, `addendum_identity_rules_digest` | Exact immutable release evidence. A missing or mismatched digest blocks creation and publication. |
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
| `template_release_id`, `template_key`, `template_release`, `product_profile_id`, `renderer_profile_id`, `supported_renderer_version` | Exact bound installed release and runtime profiles. |
| `official_source_digest`, `bundle_digest`, `response_rules_digest`, `downstream_rules_digest`, `addendum_identity_rules_digest` | Exact bound source, document, response, mapping and addendum-identity assets. |
| `officer_payload` | Canonically serialized §5.2 values only. |
| `invitation_digest`, `issued_tender_digest` | Generated from the canonical projection. |
| `response_schema_digest`, `evaluation_contract_digest`, `contract_projection_digest` | Component digests retained for diagnostic and downstream reconciliation; each must equal the corresponding content inside the Published Bid Definition. |
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
- method, category, product, reservation category, independently applicable County-residents restriction, lotting and award-package facts;
- the exact effective reservation-rule snapshot identities, including any verified overlap treatment;
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

Same-specification equipment items may render as one supplier-facing schedule line only when category, approved specification-set identity, unit, delivery location, latest delivery date, warranty/support treatment, reservation/County treatment, lot and currency all match. The line identity uses STD-TPL-001 v0.10 §13.6's exact canonical grouping algorithm. Every contributing Requisition item, source allocation, quantity and reservation identity remains retrievable from that line; changing an input produces a new identity rather than silently repurposing the old one.

#### 4.5.1 Supplier response schema

The generated supplier response is structured and identified; it is not an upload-only envelope.

| Published content | Required supplier response |
|---|---|
| Each goods line | Read-only published quantity/unit; offered make/model; delivery commitment; linked evidence; permitted unit price and tax inputs; calculated total. |
| Each mandatory technical requirement | `Comply` or `Do not comply`; typed offered value where measurable, otherwise text up to 300 characters; optional comment up to 500 characters; required evidence references when specified. |
| Each related service | Confirmation; offered completion date; price-schedule line; required evidence. |
| Each warranty/support obligation | Confirmation; offered term/value where applicable; service/escalation details; evidence. |
| Each acceptance requirement | Explicit acceptance linked to the resulting contract obligation. |
| Each evidence requirement | One or more permitted evidence references, with mandatory/optional treatment preserved. |
| Published reservation treatment | The category-specific declaration and required certificate, reference, validity and evidence; where applicable, separate County-residents evidence. Address, Account state and file upload never prove entitlement by themselves. |

Every response row retains the published stable identifier. The response schema cannot add a criterion that is absent from the published Tender.

#### 4.5.2 Evaluation contract

The generated evaluation contract provides the published eligibility checklist, including the applicable reservation declaration/evidence under `EVG-ELIGIBILITY`; one shared `EVG-TECHNICAL-COMPLIANCE` group; the individual mandatory checks, offered values and evidence feeding that group; the arithmetic and price results; the fixed governed stage order; and no evaluator-created or hidden criterion.

The exact group set is `EVG-ELIGIBILITY`, `EVG-TECHNICAL-COMPLIANCE`, `EVG-FINANCIAL` and `EVG-AWARD`. No runtime group can be added, renamed or omitted.

Every technical row retains its pass/fail result and reason, but the rows are not independently weighted criteria. The Technical compliance group passes only when every applicable mandatory check passes. The evaluator cannot change a check, group, weight, comparison or mandatory status.

#### 4.5.3 Contract-obligation projection

The generated contract projection carries the awarded response into identified obligations for:

- each Requisition item, source allocation, quantity and delivery commitment;
- each mandatory technical requirement and accepted offered value;
- each related service and completion date;
- each warranty/support obligation;
- each acceptance requirement;
- each agreed price row; and
- the finite officer-authored contract parameters in §5.2.

Supplier reservation evidence is an eligibility fact, not a contract obligation. The applicable reservation category, County-residents restriction and evaluated result are nevertheless preserved in the governed award and statutory-reporting handoff.

No obligation is reconstructed by copying free text from a rendered Tender.

#### 4.5.4 Published Bid Definition

Publication authorisation materialises one immutable `PublishedBidDefinition v1`; Tenders owns that transaction and the exact STD release owns the product rules. The definition uses these top-level fields and no aliases:

```text
bid_definition_id,definition_version,tender_id,tender_version_id,publication_id,
effective_addendum_ids,submission_deadline,template_family,template_release_id,
product_profile_id,renderer_profile_id,supported_renderer_version,package_digest,
official_source_digest,bundle_digest,response_rules_digest,downstream_rules_digest,
addendum_identity_rules_digest,sections,response_rows,price_rows,declaration_texts,
reservation_treatment,evaluation_mappings,contract_mappings,definition_digest
```

`template_family` equals the installed release `template_key`; `template_release_id` is its opaque `release_id`. `sections` contains the finite ordered supplier tasks/groups. `response_rows`, `price_rows` and `declaration_texts` contain only obligations present in the issued Tender. `reservation_treatment` contains only the Tender-specific category, independent County-residents treatment, exact rule/overlap snapshots and bidder declaration/evidence rules; it contains no APP target, denominator, shortfall, Budget ceiling or claim of bidder entitlement.

`BuildPublishedBidDefinition` calls the shared `CompilePublishedBidDefinition` implementation in STD-TPL-IMP-001 v1.1. At Draft creation the bound release must be Available. v0.12 (OD5): it must also be switched On on the site. At later submission, approval, reopening and publication actions it may be Available or Superseded, but its exact manifest, assets and renderer adapter must still verify. v0.12 (OD5): at those later actions an Available release may be switched On or Off; the switch is not rechecked. Withdrawn always blocks an unpublished Tender. The service validates every control, composition, identity, obligation, price/calculation, evaluation mapping and contract disposition; proves human/structured reconciliation; and returns the canonical definition plus `definition_digest`. Failure rolls back the invoking publication-authorisation or addendum-issue transaction. It never calls a separate curation algorithm and never parses the rendered PDF.

The publication-authorisation transaction freezes the definition, Invitation, issued Tender, package digest, required channel records and `publication_id` together. The definition identity and digest belong to `TenderPublication`, not the already-approved immutable `TenderVersion`. BDS receives the exact frozen definition only after every required publication channel is confirmed and cannot add, remove or repair content.

### 4.6 TenderPublication

| Field | Rule |
|---|---|
| `publication_id` | Server-generated immutable identity. |
| `tender_id`, `tender_version_id`, `package_digest` | Exact approved immutable package. One publication authorisation per approved Version. |
| `bid_definition_id`, `definition_version`, `definition_digest` | Exact immutable Published Bid Definition created in the publication-authorisation transaction. These fields are never written back into the approved Tender Version. |
| `response_schema_digest`, `evaluation_contract_digest`, `contract_projection_digest` | Exact definition-component digests; each must reconcile with the approved Version's generated component digest and the frozen definition content. |
| `authorised_by`, `authorised_at` | Accounting Officer decision facts; server-derived. |
| `rule_snapshot_id` | Exact effective publication/advertising rule resolved at authorisation. |
| `threshold_snapshot` | Exact configured value and currency where applicable; internal evidence. |
| `required_channels` | Generated immutable set from the rule snapshot; never user-selected. |
| `publication_status` | `Evidence required`, `Published`, `Withdrawn before confirmation`, `Cancelled`. Authorisation creates the Evidence-required state atomically. |
| `published_at` | Actual Tender-availability instant established after all required `Tender package` subject/channels are confirmed; mathematically the latest `available_at` among those original-package confirmations. Addendum/cancellation confirmations are excluded. It is not the time the final confirmation record was entered. |
| `publication_digest` | Digest covering decision, package, rule snapshot, channels and final evidence. |
| `withdrawn_by`, `withdrawn_at`, `withdrawal_reason` | Set only when no channel has been confirmed and accountable evidence establishes that publication did not occur. |

Publication authorisation commits the Accounting Officer's decision and creates the required channel-confirmation records. It does not claim that publication occurred, call an assumed external interface or make documents public by itself.

### 4.7 PublicationChannelConfirmation

| Field | Rule |
|---|---|
| `channel_confirmation_id` | Server-generated immutable identity. |
| `publication_id` | Original publication whose rule snapshot and required-channel set govern this confirmation. |
| `subject_type` | `Tender package`, `Addendum` or `Cancellation notice`. |
| `subject_id`, `subject_digest` | Exact immutable item being confirmed. Uniqueness is `(subject_type, subject_id, channel)`; a later addendum or cancellation notice never reuses the original package confirmation. |
| `channel` | One generated required channel from the rule snapshot. |
| `confirmation_mode` | `Evidence based` in MVP. `Integrated acknowledgement` is reserved for the future facility in §5.5.1 and cannot be activated in MVP. |
| `status` | `Awaiting confirmation` or `Confirmed`. |
| `available_at` | Required actual instant the approved documents became available through this channel; supplied in the HOPF attestation. |
| `evidence_reference` | Required publication reference, register entry, placement reference or other channel-appropriate identifier, 1–160 characters. |
| `public_url` | Required for an online channel when a stable public URL exists; otherwise null with the reason captured in notes. |
| `evidence_file_id`, `evidence_digest` | Required for every MVP channel; the supporting file must pass technical validation. |
| `evidence_notes` | Optional plain text, maximum 500 characters. |
| `attestation_text`, `attested_by`, `attested_at` | Exact subject-specific confirmation statement plus server-derived HOPF identity and time. The actor confirms that the exact approved Tender package, addendum or cancellation notice identified by the record was publicly available through the named channel at `available_at`. |
| `record_version` | Optimistic-concurrency token. |

For `Tender package`, `subject_id` is the publication identity and `subject_digest` must equal its approved package digest. For `Addendum`, they equal the addendum identity/digest. For `Cancellation notice`, they equal the immutable notice-package identity/digest. KenTender validates record completeness, field formats, actor authority, subject/channel identity, file integrity, malware-scan result, duplicate/conflicting confirmation and applicable channel rules. It does **not** independently prove that a website, notice board or newspaper was publicly available. That factual confirmation is the named HOPF's accountable attestation supported by the recorded evidence.

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
| `drafted_by`, `drafted_at` | Server-derived authoring facts. |
| `issue_decided_by`, `issue_decided_at` | HOPF issue decision; set when the successor definition and channel work are frozen. This is not publication/effectiveness. |
| `issued_at` | Null until every required channel is confirmed; then set once to the latest subject `available_at` across those confirmations. This is the effective addendum instant, not the time the final confirmation was entered. |
| `addendum_digest` | Covers content, affected published baseline, decision and resulting deadline. |
| `successor_bid_definition_id`, `successor_definition_version`, `successor_definition_digest` | Null in Draft/Awaiting issue. Frozen atomically by `IssueAddendum` from the current effective definition plus this exact addendum; activated only when the addendum becomes Issued. |

An addendum is append-only. It never edits the approved Tender Version. A proposed change to quantity, authorised value, method, reservation, lotting, award package, substantive technical requirement or evaluation basis is rejected and follows cancellation/new-Tender governance.

`IssueAddendum` first builds and freezes the complete successor Published Bid Definition and then creates channel-confirmation records under the same required-channel set as the original publication in one transaction. The candidate successor is not bidder-effective while confirmation is outstanding. The addendum becomes **Issued**, its deadline becomes effective and its already-frozen successor definition becomes the current bidder definition atomically only when the HOPF confirms every required channel with the applicable evidence and attestation.

### 4.9 TenderClarification

| Field | Rule |
|---|---|
| `clarification_id` | Server-generated immutable identity. |
| `tender_id`, `publication_id`, `bid_definition_id` | Exact open Tender and effective bidder definition at receipt. |
| `related_addendum_id` | Optional issued addendum when the question concerns it; null for a general Tender question. |
| `candidate_registration_id` | Authenticated Bid Submission owner identity created through **Start bid**; never free text. |
| `question`, `received_at` | Exact inbound question and authoritative receipt instant. Question is 10–2,000 characters. |
| `status` | `Awaiting response`, `Awaiting addendum`, `Answered` or `Closed with reason`. |
| `response` | Required bounded text before Answered. |
| `response_audience` | `Asker only` or `All registered candidates`; selected deliberately by the responding procurement professional. |
| `affects_published_tender` | Boolean decided by the responding procurement professional. |
| `required_addendum_id` | Required before Answered when `affects_published_tender = Yes`; the addendum must be Issued and its successor definition effective. |
| `responded_by`, `responded_at` | Server-derived from the committing authorised actor. |
| `notice_id`, `response_digest` | Immutable response and delivery evidence. A broadcast never identifies the source candidate. |

The module creates no clarification on behalf of a candidate. It consumes an authenticated Bid Submission event, verifies the exact registered-candidate/Tender relationship and rejects receipt at or after the stated clarification deadline. A question does not change the Tender. When the proposed answer would change, qualify or add to published wording, criteria, schedules or bidder obligations, the clarification remains **Awaiting addendum**: an authorised addendum must be issued first. Only then may the linked answer be sent to all registered candidates and shown publicly with the effective addendum. A response that changes nothing may be sent to the asker only or broadcast when it is generally useful.

### 4.9A CandidateNoticeDispatch

| Field | Rule |
|---|---|
| `notice_id`, `notice_type` | Immutable identity; type is `Clarification response`, `Addendum issued`, `Deadline changed` or `Tender cancelled`. |
| `subject_id`, `subject_digest` | Exact immutable clarification, addendum, deadline-changing addendum or cancellation notice. |
| `audience_frozen_at` | Trusted instant at which the authoritative candidate set is resolved. |
| `candidate_registration_id` | Exact Tender-bound candidate identity supplied by Bid Submission. |
| `destination_snapshot` | Protected verified mandatory-notice address used for this dispatch; earlier dispatches never follow later contact edits. |
| `status` | `Queued`, `Sent`, `Delivered` or `Failed`. `Sent` is never displayed as Delivered. |
| `attempt_count`, `last_attempt_at`, `provider_reference`, `failure_reason` | Append-only delivery/retry evidence; protected to authorised procurement/support/audit roles. |

The candidate audience is every Active Tender-bound registration existing at `audience_frozen_at`. A candidate registered later sees the complete current public Tender history but is not retroactively described as a recipient. Mandatory procurement notices cannot be opted out of. Tenders records an outbox event in the same transaction as the authoritative notice; dispatch and retry are asynchronous. Failure is visible to authorised staff and may require lawful alternative contact, but it does not retract an issued addendum, change the effective deadline, reopen a cancellation or fabricate receipt.

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
| Published — open; before clarification deadline | Receive supplier clarification | Bid Submission owner event | Records one authenticated question against the exact candidate registration and effective definition. |
| Clarification awaiting response; no published change | Respond | Procurement Officer / HOPF | Records a direct or general answer and creates the required notice evidence. |
| Clarification would affect published Tender | Require addendum | Procurement Officer / HOPF | Sets Awaiting addendum; no answer is issued until the linked addendum is Issued. |
| Published — open | Recommend cancellation | HOPF | Appends optional recommendation; does not cancel. |
| Published — open | Cancel Tender | Accounting Officer | Closes Tender immediately; creates notice/report compliance work. |
| Published — open; submission deadline reached | Close submission period | System / Bid Submission owner | Sets Submission period ended and emits immutable downstream contract. |
| Draft, Returned, Submitted or Approved before publication authorisation | Request requisition correction | Procurement Officer / HOPF | Stops Version; invokes governed corrected-Requisition route; no local override. |
| Corrected authorised Requisition available | Start corrected Tender Version | Procurement Officer | Consumes successor and creates linked Draft; stopped history remains immutable. |
| Bound release becomes Superseded before publication | Continue existing Tender action | Existing authorised actor | Permitted only when the exact bound assets, digests and renderer adapter still verify; displays successor notice and never rebinds. |
| Bound release is switched Off on the site (v0.12, OD5) | Continue existing Tender action, before or after publication | Existing authorised actor | Permitted while the exact bound assets, digests and renderer adapter still verify. The switch governs only new Tenders; it never blocks, strands or rebinds a started Tender. |
| Bound release becomes Withdrawn before publication | Attempt submit, approve, authorise, confirm publication or start Bid | Any actor | Blocks the action and directs the governed cancellation/new-Tender or expressly authorised correction route; preserves every Version and decision. |
| Bound release becomes Superseded or Withdrawn after publication | View historical Tender | Authorised/public viewer as applicable | Keeps the exact documents and Published Bid Definition immutable and readable; displays the release lifecycle notice. |

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

A Requisition may start this product only when all nine checks pass:

| Check | Required value |
|---|---|
| Procurement category | Goods |
| Product | Straightforward off-the-shelf IT equipment |
| Method | Open Tender |
| Reservation | `None`, `Youth`, `Women` or `Persons with disabilities`, supported by the exact Available template release and an applicable verified rule snapshot. At Draft creation this is the Available release that is switched On on the site (v0.12, OD5). |
| County-residents restriction | `Not applicable`; or, for a county Procuring Entity, an applicable verified County-residents rule and supported overlap treatment. |
| Lotting | Single lot |
| Currency | KES |
| Award package | One |
| Plan horizon | Single year |

Compatibility is rechecked at Draft creation, submission, approval, reopening and publication authorisation against the exact immutable owner facts applicable to that action. Draft creation requires `Available`. An existing bound release may be `Available` or `Superseded` at later actions; `Superseded` never causes rebinding and requires all exact integrity/adapter checks to pass. `Withdrawn` blocks every unpublished continuation. v0.12 (OD5): Draft creation also requires the `Available` release to be switched On on the site. At later actions an `Available` bound release may be switched On or Off; the site switch is not rechecked after Draft creation, so switching a release Off never strands a started Tender and never rebinds it.

### 5.4 Review result

Review is a deterministic projection, not a workflow state or separate user task. A Draft may be incomplete; submission and approval may not.

Findings are:

- **Must fix** — prevents submission/approval/publication and links to the exact task, field or inherited owner route; or
- **Review note** — remains visible through HOPF and Accounting Officer decisions; cannot be dismissed.

The result verifies the source handoff; the bound release's permitted lifecycle state for the current action; exact source, bundle, profile, response, downstream and addendum-rule digests; renderer-adapter health; nine compatibility checks, including the bound reservation-rule and overlap snapshots; officer fields; dates; inherited completeness; grouping lineage; schedules; response schema; evaluation/contract mappings; file treatments; security/contract values; both renders; and package digest. v0.12 (OD5): the site switch is not part of the review result; a started Tender's result never fails because its bound release was later switched Off.

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
- Issue authority is HOPF. Issue freezes a complete successor Published Bid Definition against the current effective definition plus the exact addendum; any unsupported control, missing mapping, migration ambiguity or reconciliation failure blocks issue and creates neither a partial definition nor channel work.
- The addendum, revised deadline and successor definition are not effective until every original required channel confirms the exact addendum digest. Final confirmation activates all three atomically; BDS cannot see an awaiting-confirmation definition as current.
- Supplier-facing documents show the current effective content and the complete addendum trail; the original package remains immutable.
- For the successor Published Bid Definition, every prior identity is classified exactly as `unchanged`, `converted`, `fresh_response_required`, `removed` or `new`; labels, order and text similarity never migrate a bidder response.

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
13. New Tenders bind only an Available release; an existing Tender never rebinds automatically. v0.12 (OD5): the release must also be switched On on the site.
14. Superseded may continue only for an already-bound unpublished Tender whose exact release integrity and renderer adapter still pass.
15. Withdrawn blocks every unpublished continuation and Bid start; published evidence remains immutable and readable.
16. Switching a release Off on the site stops only new Tenders binding it. An already-bound Tender continues on its release, whether Available (switched On or Off) or Superseded, while integrity and renderer-adapter checks pass, and is never stranded or rebound because of the switch (v0.12, OD5).

### 5.9 Next-step ownership and Tender stages (KT-STD-001 v1.8 §3B)

`GetTender`, `GetTenderReview` and `GetTenderPublication` return the server-derived `next_step` contract in KT-STD-001 §3B.2 for the signed-in actor. Guards in §5.10 supply its blockers and fixes; the browser never infers it from a badge or disabled control. The five formal Tender stages are `PREPARE` (Procurement Officer prepares and submits), `HOPF_APPROVAL` (HOPF returns or approves), `AO_AUTHORISATION` (Accounting Officer authorises publication), `PUBLICATION` (HOPF confirms required channels), and `OPEN_MANAGEMENT` (authorised people handle open-period clarification, addenda and cancellation). The three preparation tasks are sections of `PREPARE`, not stages. Channel confirmations are work inside `PUBLICATION`, not four tracker stages. Addenda and clarifications are work in `OPEN_MANAGEMENT`, not new whole-Tender stages. The system deadline closes the final stage without inventing a human closure decision.

| Tender state / signed-in responsibility | Current stage | Server next step and holder | Completion or hand-off |
|---|---|---|---|
| Draft/Returned; Procurement Officer | `PREPARE` | Your turn to complete the form; Submit is blocked only if must-fix findings remain. Holder: assigned Procurement Officer (Brian Wafula in fixture). | Submit gives HOPF Charles Mutiso the exact locked Version. |
| Draft/Returned; HOPF or AO | `PREPARE` | Waiting on Procurement Officer Brian Wafula since Draft/return event. | No approval/publication control until submission. |
| Submitted; eligible HOPF | `HOPF_APPROVAL` | Your turn to Return or Approve. Holder: Charles Mutiso. | Return gives Procurement Officer correction work; approval gives AO authorisation work. |
| Submitted; Procurement Officer/AO | `HOPF_APPROVAL` | Waiting on HOPF Charles Mutiso since submission. | Submitted Version is immutable. |
| Approved, not authorised; eligible AO | `AO_AUTHORISATION` | Your turn to Authorise publication. Holder: Amina Hassan. | Authorisation gives HOPF the publication confirmations. |
| Approved, not authorised; Procurement Officer/HOPF | `AO_AUTHORISATION` | Waiting on AO Amina Hassan since approval, except HOPF's explicit Reopen action when still lawful. | Reopen creates a copied Draft and returns to `PREPARE`. |
| Publication authorised; eligible HOPF | `PUBLICATION` | Your turn to confirm outstanding channels; block only a specific confirmation whose evidence fails. Holder Charles Mutiso. | Final channel confirmation makes the Tender Published — open. |
| Publication authorised; other business readers | `PUBLICATION` | Waiting on HOPF Charles Mutiso since authorisation. | No reader attestation action. |
| Published — open; Procurement Officer/HOPF with pending clarification or addendum | `OPEN_MANAGEMENT` | Your turn on that exact item, or blocked with its reason. Holder is the assigned Procurement Officer or HOPF. | Answer, addendum issue/publication, and notices remain on the same Tender. |
| Published — open; no required action for viewer | `OPEN_MANAGEMENT` | Not involved for neutral readers; HOPF, Procurement Officer and AO see the exact optional actions available in their role views without a My Work item, due marker or assigned cancellation review. An available option can produce Your turn under KT-STD-001 §3B.2, but its headline must state the option without implying obligation. | Submission deadline closes the period. |
| Material addendum cancellation review requested; Procurement Officer | `OPEN_MANAGEMENT` blocked | Waiting on AO Amina Hassan to consider cancellation; the material addendum remains unissuable. | AO cancels the Tender or closes the review with a reason. |
| Material addendum cancellation review requested; AO | `OPEN_MANAGEMENT` | Your turn to decide whether to cancel or close the review. Holder: Amina Hassan. | Cancellation closes the Tender; closure returns the Procurement Officer to the blocked draft with a discard route. |
| Material addendum review closed without cancellation; Procurement Officer | `OPEN_MANAGEMENT` blocked | Your turn, blocked: the 250-to-300 Each change cannot be issued. Holder: Brian Wafula. | **Discard addendum draft** archives the unissued draft and returns to the Published Tender; a new material proposal follows a new governed decision, not the closed request. |
| Cancellation pending; AO | `OPEN_MANAGEMENT` | Your turn to decide cancellation on an applicable ground. Holder: Amina Hassan. | Cancellation creates separate notice/report compliance work. |
| Cancelled or submission ended; reader | Final stage done | Done with named decision actor/time for cancellation, or actual deadline for submission end. | Outstanding cancellation compliance stays current in `OPEN_MANAGEMENT` only for its assigned holder. |
| Requisition correction requested; Procurement Officer | `PREPARE` blocked | Waiting on Departmental Author Grace Wanjiku since correction request; current Version is stopped. | An authorised successor makes Start corrected Tender Version available. |

For any state, a person with no Tender business responsibility receives `Not involved` or a truthful waiting/done answer. Administrator/System Manager technical readers never receive Your turn, blocked Your turn, fixes or business actions under KT-STD-001 §3B.6. `since` uses the recorded state-entry event; omit it from a design fixture that supplies no instant. A returned Version's current stage resets to `PREPARE`; old decisions remain in History. Guard precedence and full blocker aggregation follow KT-STD-001 §3B.2.

### 5.10 Guard reasons and fixes

Every guarded action returns `allowed`, stable `reason_code`, concrete `figures`, and every permitted fix with responsible holder and route. These codes extend the §8 error contract; the server also returns them to record reads before the actor attempts the action. No action is silently disabled. Values such as remaining channels or missing fields are current computed results, not formal tracker stages.

| Guard/action | Reason code and figures | Fix label and responsible holder |
|---|---|---|
| Submit for approval with missing fields | `TND_MUST_FIX`; list every field, including Inspection and acceptance location | **Review contract terms** or the exact task/field; Procurement Officer. |
| Approve/authorise with same-person conflict | `TND_SOD_BLOCKED`; conflicting earlier act and Version | No self-fix; System Manager assigns another eligible HOPF/AO through existing System setup. The conflicted viewer sees the System Manager as holder and **Back to Tenders** outside the waiting line; no approval override. |
| Authorise publication with no effective rule | `TND_PUBLICATION_RULE_UNAVAILABLE`; missing rule/channel facts | **Open System setup** for an authorised System Manager to correct the governed rule; routine actors see the named responsible role and **Back to Tenders**, with no local rule editor. |
| Authorise with unlawful period | `TND_PUBLICATION_PERIOD_INVALID`; deadline and required period | **Reopen Tender** while permitted, then **Review Tender dates**; HOPF and Procurement Officer respectively. |
| Confirm publication, incomplete channel | `TND_PUBLICATION_CONFIRMATION_INCOMPLETE`; remaining channel names/count and missing fields | **Confirm publication** on each outstanding channel; HOPF. |
| Confirm publication, bad evidence/conflict | `TND_PUBLICATION_EVIDENCE_INVALID`, `TND_PUBLICATION_DIGEST_MISMATCH` or `TND_PUBLICATION_ALREADY_CONFIRMED`; channel and file/package fact | **Choose evidence file** in the current confirmation before saving, or **View confirmation** for an immutable existing record; HOPF. No mutation of confirmed evidence. |
| Issue addendum that changes the procurement materially | `TND_ADDENDUM_MATERIAL`; affected reference, current 250 Each and proposed 300 Each | **Ask Amina Hassan (Accounting Officer) to consider cancellation** calls `RequestTenderCancellationReview`; AO Amina Hassan owns the decision. **Discard addendum draft** clears the unissuable proposal; after AO closes that exact review, discard is the remaining fix. **View cancellation requirements** is navigation, not a fix. |
| Send answer that changes published content | `TND_CLARIFICATION_ADDENDUM_REQUIRED`; clarification and changed published anchor | **Prepare addendum**; Procurement Officer/HOPF. Send response after linked issue. |
| Notice delivery fails | `TND_NOTICE_DELIVERY_FAILED`; protected recipient and attempts | **Retry notice** or authorised follow-up; HOPF/Procurement function. Tender effectiveness does not change. |
| Correct Requisition while current Tender is stopped | `TND_HANDOFF_INVALID`; current/successor Requisition identities | **View requisition status**; Departmental Author owns correction, Procurement Officer starts the authorised successor. |
| Bound release withdrawn or integrity fails | `TND_TEMPLATE_RELEASE_WITHDRAWN` or `TND_TEMPLATE_RELEASE_INTEGRITY_FAILED`; release and reason | **View STD Template** for authorised inspection; AO uses governed cancellation/new-Tender route if withdrawn. A site switch Off alone is never this guard for an already-bound Tender. |

For a conflicted HOPF/AO viewer, `TND_SOD_BLOCKED` means Waiting on an eligible alternate holder, not Not involved. The System Manager resolves an eligible decision holder without giving the conflicted viewer an override; if the isolated fixture lacks a System Manager name/time, the design omits those facts.

The existing §8 messages remain the user-facing error text. Where a named holder's corrective route is outside Tenders, the record offers the existing authorised route and creates no new approval or arbitrary repair action. The dead-end test in KT-STD-001 §3B.7 covers every §5.1 state, visible responsibility, guard, fix route and tracker agreement; browser checks verify only faithful rendering of the returned answer.

### 5.11 Tender hand-off register

These rows feed My Work and waiting-on summaries. Each item clears on the stated business transition, never on reading a notification. Internal notifications are in-product work alerts; they do not claim publication or supplier notice delivery. The exact person is resolved from responsibility assignments at the event; the cancellation fixture assigns Procurement Officer Brian Wafula to compliance evidence.

| Event | Next holder | Their My Work item | Sender's waiting-on item | Notification | Clears when |
|---|---|---|---|---|---|
| Submit Tender Version | HOPF, Charles Mutiso | **Review Tender TND-MOH-2027-033** | Procurement Officer: **Waiting for Charles Mutiso to review Tender TND-MOH-2027-033** | Yes, HOPF | Return or Approve package. |
| Return for correction | Procurement Officer, Brian Wafula | **Correct Tender TND-MOH-2027-033 — Supplier and contract requirements** with return comment | HOPF: None | Yes, Procurement Officer | Corrected Version submitted or stopped for Requisition correction. |
| Approve Tender package | AO, Amina Hassan | **Authorise publication of Tender TND-MOH-2027-033** | HOPF: **Waiting for Amina Hassan to decide publication of Tender TND-MOH-2027-033** | Yes, AO | Publication authorised or approved Version reopened. |
| Reopen approved Tender before authorisation | Procurement Officer, Brian Wafula | **Correct reopened Tender TND-MOH-2027-033** with HOPF reason | HOPF: None | Yes, Procurement Officer | Copied Draft submitted or stopped for Requisition correction. |
| Authorise publication | HOPF, Charles Mutiso | **Confirm publication of Tender TND-MOH-2027-033** | AO: **Waiting for Charles Mutiso to confirm publication of Tender TND-MOH-2027-033** | Yes, HOPF | All channels confirmed or lawful authorisation withdrawal. |
| Withdraw publication authorisation before any confirmation | HOPF, Charles Mutiso | **Review withdrawn publication authorisation for TND-MOH-2027-033** with AO reason | AO: None | Yes, HOPF | Tender reopened for correction or a new authorisation decision. |
| Submit addendum for issue | HOPF, Charles Mutiso | **Decide addendum ADD-MOH-2027-033-001** | Procurement Officer: **Waiting for Charles Mutiso to decide addendum ADD-MOH-2027-033-001** | Yes, HOPF | Addendum returned or issue decided. |
| Return addendum for correction | Procurement Officer, Brian Wafula | **Correct addendum ADD-MOH-2027-033-001** with HOPF comment | HOPF: None | Yes, Procurement Officer | Corrected addendum submitted. |
| Issue addendum | HOPF, Charles Mutiso | **Confirm publication of addendum ADD-MOH-2027-033-001** | Procurement Officer: **Waiting for addendum ADD-MOH-2027-033-001 to be published** | Yes, HOPF | All original channels confirmed. |
| Supplier clarification received | Procurement Officer, Brian Wafula | **Respond to clarification for TND-MOH-2027-033** | HOPF: None | Yes, Procurement Officer | Answer recorded or linked addendum issue required. |
| Request Requisition correction | Departmental Author, Grace Wanjiku | **Correct Requisition REQ-MOH-2027-037-001** with reason | Procurement Officer: **Waiting for Grace Wanjiku to correct the requisition** | Yes, Departmental Author | Corrected successor authorised or request closed under Requisition governance. |
| Corrected Requisition successor authorised | Procurement Officer, Brian Wafula | **Start corrected Tender Version for TND-MOH-2027-037** | Departmental Author: None | Yes, Procurement Officer | Start corrected Tender Version. |
| Request cancellation review for material addendum | AO, Amina Hassan | **Consider cancellation of TND-MOH-2027-039** with 250-to-300 Each comparison and reason | Procurement Officer: **Waiting for Amina Hassan to consider cancellation of TND-MOH-2027-039** | Yes, AO | AO cancels Tender or closes the request with a reason. |
| Cancel Tender | Procurement Officer, Brian Wafula | **Record cancellation notices and PPRA report for TND-MOH-2027-034** | AO: **Waiting for cancellation compliance evidence for TND-MOH-2027-034** | Yes, Procurement function | Every required notice/report evidence recorded. |

## 6. Roles and permissions

All access uses AUTH-ADR-001 v1.10 role-bound `User Responsibility Assignment` through registered permission hooks. No native Frappe User Permission participates in authorisation.

| Business responsibility | Scope | Exact work |
|---|---|---|
| Procurement Officer | Site-wide | Start and prepare Tender; submit; correct returned work; request Requisition correction; draft addendum; respond to supplier clarification. |
| Head of Procurement Function | Site-wide | Return/approve Tender package; reopen before publication authorisation; confirm channel publication with evidence and attestation; draft/issue addendum; respond to clarification; optionally recommend cancellation. |
| Accounting Officer | Site-wide | Authorise publication; withdraw authorisation only when confirmed unpublished and no channel was confirmed; cancel Tender. Cannot edit package/addendum content. |
| Departmental Author / Head of User Department | Organisation Unit | Read inherited requirements and neutral Tender/publication status already authorised by source scope; no Tender action. |
| Auditor | Site-wide or approved oversight scope | Read Versions, decisions, publication confirmations/evidence, addenda, clarifications, candidate-notice evidence and cancellation; no business action. |
| Authorised technical operator | Explicit future integration assignment | No MVP publication action. When §5.5.1 is implemented, may perform only approved reconciliation/recovery; cannot attest publication, edit content, authorise, issue or cancel. |
| Administrator / System Manager | Technical read | Read all records under KT-STD-001 v1.8 §3A.6; no business action unless separately assigned an explicit business/recovery responsibility. |
| System | Internal | Generate schedules/renders; validate and derive publication state from accountable confirmations; close submission period; publish Planning invitation actual and downstream event. |

The person who prepared or submitted a Version cannot approve it as HOPF. The person who prepared, submitted or HOPF-approved a Version cannot authorise its publication as Accounting Officer. Checks use the immutable Version audit, not role labels alone.

## 7. Service and command contracts

### 7.1 Reads

| Service | Required result |
|---|---|
| `GetTendersWorkspace` | One role-aware queue with exact status, next action and permitted filters. |
| `GetTenderStart` | Authorised Requisition summary, nine compatibility results and fixed template/rule evidence; no mutation. |
| `GetTender` | One projection containing current Version, inherited snapshot, officer values, generated content, review result, decisions, publication status, permitted actions and the signed-in actor's server-derived §5.9 `next_step`. |
| `GetTenderReview` | Complete result-first review with exact rows, renders, mappings and the same signed-in-actor `next_step`. |
| `GetTenderPublication` | Approved package, frozen Published Bid Definition identity/digest, AO task, rule snapshot, required channels, subject-scoped confirmation/evidence status, permitted actions and the same signed-in-actor `next_step`. |
| `GetTenderHistory` | Versions, decisions, correction lineage, subject-scoped channel confirmations, addenda and successor-definition activation, inquiries, cancellation and downstream events. |
| `GetTenderDocument` | Exact immutable Invitation, issued Tender, addendum or cancellation notice by digest and authorised audience. |

Reads create no record, task, decision, render, confirmation or event.

### 7.2 Preparation and approval commands

| Command | Minimum effect |
|---|---|
| `StartTender` | Recheck handoff/template/compatibility; require an Available release that is switched On on the site (v0.12, OD5); create or return one Draft; bind digests and record authoritative Requisition consumption atomically. |
| `SaveTenderDraft` | Accept only applicable §5.2 officer fields; reject inherited/generated/hidden/unknown fields. |
| `AddTenderEvidenceRequirement` / `UpdateTenderEvidenceRequirement` / `RemoveTenderEvidenceRequirement` | Mutate one valid Draft evidence row linked to an inherited published requirement. |
| `SubmitTenderForApproval` | Rebuild/review exact projection; require zero Must fix; lock Version and assign HOPF. |
| `ReturnTenderForCorrection` | Require reason and governed affected task; preserve submitted Version and create copied Draft. |
| `ApproveTenderPackage` | Recheck authority, segregation, package and review; commit immutable HOPF decision and AO task. |
| `ReopenApprovedTender` | Require reason and publication not authorised; preserve approved Version and create copied Draft. |
| `RequestRequisitionCorrection` | Stop current pre-publication Version and invoke the governed Requisition correction route; never edit inherited content. |
| `StartCorrectedTenderVersion` | Consume exact newly authorised successor; create linked Draft with regenerated snapshot/schedules. |
| `BuildPublishedBidDefinition` | Internal adapter to the shared compiler; consume the exact approved Version, the bound Available-or-Superseded `InstalledSTDRelease v1` (an Available release may be switched On or Off; v0.12, OD5), current effective addenda and, for addendum issue, one proposed immutable addendum; reject Withdrawn or failed integrity/adapter checks; return the exact §4.5.4 definition and digest or one Blocking result. It creates no partial definition. |

### 7.3 Publication commands

| Command | Minimum effect |
|---|---|
| `AuthoriseTenderPublication` | Recheck AO authority, segregation, approved package, current rule and minimum-period feasibility; invoke `BuildPublishedBidDefinition`; atomically commit decision, definition, snapshot and one Evidence-based confirmation record for every required channel. |
| `ConfirmPublicationChannel` | HOPF records actual availability, required reference/URL/evidence and explicit attestation for one `Tender package` channel against the exact package; server performs only the technical and authority checks in §4.7. |
| `WithdrawPublicationAuthorisation` | AO only; require no channel confirmed and accountable evidence that publication did not occur; preserve decision and record withdrawal. |
| `ConfirmTenderPublished` | Internal; require every required `Tender package` subject/channel confirmed, deadline valid and matching digests; set `published_at`, emit Planning actual and Bidder-facing open-Tender event once. Addendum/cancellation confirmations cannot satisfy this condition. |

The future integrated-acknowledgement commands are not part of MVP. They shall be specified and added only through the approval gate in §5.5.1.

### 7.4 Open-period and cancellation commands

| Command | Minimum effect |
|---|---|
| `CreateAddendumDraft` / `UpdateAddendumDraft` | Create/update structured Draft against current effective published content. |
| `SubmitAddendumForIssue` | Lock exact Draft and assign HOPF. |
| `ReturnAddendumForCorrection` | Preserve submitted Draft and create copied Draft with reason. |
| `IssueAddendum` | Recheck materiality/reference/deadline; build and freeze the complete successor Published Bid Definition; atomically commit the immutable issue decision, successor definition identity/digest and required channel-confirmation records. Any definition failure leaves the addendum Awaiting issue. |
| `ConfirmAddendumPublicationChannel` | HOPF records channel-appropriate evidence and attestation against the exact addendum digest; the final required confirmation atomically marks the addendum Issued and activates its already-frozen successor definition and revised deadline. |
| `ReceiveTenderClarification` | Authenticate Bid Submission producer, exact Tender-bound candidate registration and effective definition; reject late receipt and deduplicate the inbound event. The related addendum is optional. |
| `RespondToTenderClarification` | Record professional classification and response. If published content is affected, require an already Issued linked addendum; otherwise create direct or anonymous general notice as selected. |
| `DispatchCandidateNotice` | Internal outbox worker; dispatch one frozen subject to one frozen candidate/destination, append attempt evidence and never convert Sent to Delivered without provider evidence. |
| `RetryFailedCandidateNotice` | Authorised support/procurement recovery against the same notice/recipient; no new business notice, audience or content. |
| `RequestTenderCancellationReview` | For a blocked material-addendum proposal, the Procurement Officer or HOPF sends the reason and affected comparison to the assigned AO. Creates one idempotent AO work item and a sender waiting item; changes neither the published Tender nor the addendum. AO may use the existing `CancelTender` decision or close the request with a recorded reason and no cancellation. |
| `CloseTenderCancellationReview` | AO records that the requested cancellation will not be pursued and a reason; clears the request/work item, leaves the Tender open and the material addendum blocked. The same proposal cannot create another cancellation review; Procurement Officer can discard it. It is not an approval, publication or cancellation event. |
| `DiscardAddendumDraft` | Assigned Procurement Officer archives an unissued addendum draft, including a material proposal; it cannot affect an issued or publishing addendum. Clears its draft work and returns to the unchanged Published Tender. |
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
| `TND_HANDOFF_CONFLICT` | For Brian Wafula, who may read the linked Tender: **A Tender has already been started for this requisition.** Show the Tender reference and **Open Tender**. For a viewer without linked-Tender read access: **This requisition cannot be used to start a Tender.** Show no Tender reference or identity and only **Back to Tenders**. |
| `TND_PRODUCT_UNSUPPORTED` | **This requisition is not supported by the current IT-equipment Tender format.** No bypass. |
| `TND_RESERVATION_UNSUPPORTED` | **This reservation treatment is not supported by the installed Tender format.** Create nothing; return to the governed Requisition/Planning route. No free-text bypass. |
| `TND_RESERVATION_RULE_UNAVAILABLE` | **The applicable reservation rule is not ready for this Tender.** Create nothing. An authorised System Manager may inspect the rule in System setup; routine users receive **Return to Tenders**. |
| `TND_TEMPLATE_UNAVAILABLE` | **The IT-equipment Tender format is not available.** Create nothing. An authorised Administrator, System Manager, Procurement Officer or HOPF receives **View STD Template** linking to `/app/std-templates/{template_release_id}`; other users receive **Return to Tenders**. v0.12 (OD5): this includes a site where no `Available` release of the format is switched On. |
| `TND_TEMPLATE_RELEASE_WITHDRAWN` | **This Tender cannot continue because its Tender format was withdrawn.** Preserve all work and show the reason. Offer **View STD Template** to a reader with STD inspection access or **Back to Tenders** otherwise. Do not offer a continuation control or an unnamed route on this state. |
| `TND_TEMPLATE_RELEASE_INTEGRITY_FAILED` | **The Tender format bound to this Tender could not be verified.** Block the action and preserve the Tender. Show **View STD Template** to a reader with STD inspection access or **Back to Tenders** otherwise. |
| `TND_CONTROL_INVALID` | **Check the highlighted value.** Bind exact field error. |
| `TND_INHERITED_EDIT` | **Authorised requisition information cannot be changed here.** |
| `TND_MAPPING_INCOMPLETE` | **A published requirement is not fully connected to its supplier response and downstream treatment.** Link the exact row. An authorised System Manager may inspect the bound Tender format; no user may repair mappings inside Tenders. |
| `TND_FILE_INVALID` | **A supporting file could not be verified.** Link exact file. |
| `TND_MUST_FIX` | **Fix the listed items before continuing.** Link every issue. |
| `TND_STALE_VERSION` | **Another user changed this Tender. Reload before continuing.** |
| `TND_SOD_BLOCKED` | **Another authorised officer must complete this decision.** Explain the conflicting prior action. |
| `TND_PUBLICATION_STARTED` | **Publication has started. This Tender can no longer be reopened.** |
| `TND_PUBLICATION_RULE_UNAVAILABLE` | **The publication rule is not configured for this Tender.** A System Manager must configure it. An authorised System Manager sees **Open System setup**; a routine Tender reader sees **Back to Tenders**. |
| `TND_PUBLICATION_PERIOD_INVALID` | **The submission deadline does not allow the required preparation period after publication.** Link Tender details. |
| `TND_PUBLICATION_CONFIRMATION_INCOMPLETE` | **Complete the publication confirmation for this channel.** Link every missing or invalid field. |
| `TND_PUBLICATION_EVIDENCE_INVALID` | **The publication evidence could not be accepted.** Show the technical reason without claiming that publication did or did not occur. |
| `TND_PUBLICATION_DIGEST_MISMATCH` | **This confirmation does not match the approved Tender package.** Reject and preserve the conflict for audit. |
| `TND_PUBLICATION_ALREADY_CONFIRMED` | **Publication through this channel is already confirmed.** Show the immutable confirmation. |
| `TND_PUBLICATION_WITHDRAWAL_BLOCKED` | **Publication authorisation cannot be withdrawn because at least one channel is already confirmed.** |
| `TND_ADDENDUM_STALE` | **The published wording has changed. Reload before preparing this addendum.** |
| `TND_ADDENDUM_MATERIAL` | **This change is too significant for an addendum. Cancel and start a newly governed Tender if procurement must continue.** |
| `TND_ADDENDUM_DEADLINE_REQUIRED` | **Set a lawful revised submission deadline for this addendum.** |
| `TND_CLARIFICATION_LATE` | **The clarification deadline has passed.** Preserve receipt evidence; create no clarification. |
| `TND_CLARIFICATION_CANDIDATE_REQUIRED` | **Start a bid before asking a question about this Tender.** Return to the public Tender with **Start bid**. |
| `TND_CLARIFICATION_ADDENDUM_REQUIRED` | **This answer would change the published Tender. Issue an addendum before sending it.** Preserve the Draft response and link Prepare addendum. |
| `TND_NOTICE_DELIVERY_FAILED` | **A candidate notice could not be delivered.** Show the protected recipient and permitted retry/follow-up action only to authorised staff; do not change the Tender state. |
| `TND_CANCELLATION_GROUND_INVALID` | **Select an applicable cancellation ground.** |
| `TND_CANCELLED` | **This Tender has been cancelled and cannot accept further work.** |
| `TND_IDEMPOTENCY_CONFLICT` | **This request was already used with different information. Stop and refresh.** |

Record-existence masking follows AUTH-ADR-001. Administrator/System Manager technical read follows KT-STD-001 v1.8 §3A.6 and is not masked. Procurement Officer/HOPF release inspection is the narrower module-specific access in AUTH-ADR-001 v1.10 and does not confer general technical read.

## 9. UI architecture, menu and routes

The navigation contains one module entry: **Tenders**.

| Surface | Route | Purpose |
|---|---|---|
| Tenders workspace | `/app/tenders` | One queue for authorised Requisitions, Drafts, decisions, publication work and open Tenders. |
| Start Tender | `/app/tenders/new/{handoff_id}` | Read-only confirmation; explicit Start creates/reuses Draft. |
| Tender record | `/app/tenders/{tender_id}` | Role- and state-aware preparation, review, approval, publication and open-period detail. |
| Tender history | `/app/tenders/{tender_id}/history` | Immutable Versions, decisions, channel confirmations, addenda, inquiries, cancellation and downstream events. |

Tasks link to the Tender record with the exact record/task identity; they do not create separate module workspaces. Opening a route creates nothing. Dialogs handle Start, Return, approval, publication authorisation, evidence, addendum issue, clarification response, notice recovery, reopen, correction and cancellation.

`/app/std-templates/{template_release_id}` is the read-only STD-template owner route used only for authorised inspection and error recovery. It is not a Tenders configuration screen and exposes no edit, activation, upload, repair or override action.

The Tender record uses one header and one state-specific primary content area. The §10.17 journey tracker shows formal Tender lifecycle stages without dividing preparation into steps. The §10.17 next-step block replaces repeated status/ready/awaiting narratives. The Tenders workspace, focused dialogs and full-page load/denial states have no tracker.

## 10. Static design contract

Supply **KT-STD-001 v1.8 §2 plus this section only** to the design tool. Fixture metadata remains outside the artboard. Every variant below is an isolated reset unless the primary lifecycle explicitly links it.

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
| County-residents restriction | Not applicable |
| Reservation rule | Applicable verified Youth reservation rule · Version 1 |
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
| Addendum issue decided | Charles Mutiso | 31 May 2027, 08:30 EAT; successor definition frozen; awaiting channel confirmation |
| Addendum issued and fully published | Charles Mutiso | Effective `issued_at` 31 May 2027, 09:00 EAT; fully confirmed 09:07 EAT; revised deadline 12 Jun 2027, 11:00 EAT |
| Supplier clarification answered | Brian Wafula | 26 May 2027, 11:00 EAT |

Review note: **Confirm that manufacturer authorisation is proportionate for this purchase.** Return comment: **Confirm whether manufacturer authorisation is necessary and update the supplier evidence requirement.**

Addendum: `ADD-MOH-2027-033-001`; affected reference **Goods and delivery — delivery location**; previous **Ministry of Health Headquarters, Afya House, Nairobi**; revised **Ministry of Health Headquarters, Afya House, 3rd Floor Procurement Stores, Nairobi**; reason **The published address omitted the internal delivery point**; class **Administrative clarification**; late-issue rule requires extension; revised submission deadline **12 Jun 2027, 11:00 EAT**.

Addendum channel fixture: State Portal reference `PPIP-MOH-2027-033-A1`, URL `https://portal.example.test/tenders/PPIP-MOH-2027-033/addenda/1`, evidence `PPIP-MOH-2027-033-A1.pdf`, available 08:50 EAT, attested 09:03 EAT; Ministry website reference `WEB-MOH-2027-033-A1`, URL `https://health.example.test/tenders/TND-MOH-2027-033/addenda/1`, evidence `WEB-MOH-2027-033-A1.pdf`, available 08:50 EAT, attested 09:04 EAT; notice-board reference `NB-MOH-2027-033-A1`, evidence `NB-MOH-2027-033-A1.jpg`, available 08:55 EAT, attested 09:06 EAT; newspaper reference `NP-MOH-2027-033-A1`, evidence `NP-MOH-2027-033-A1.pdf`, available 09:00 EAT, attested 09:07 EAT. The latest availability makes the addendum effective at 09:00 EAT; the final attestation completes confirmation at 09:07 EAT.

Candidate registration: Afya Digital Supplies Limited; arrangement `ARR-MOH-2027-033-001`; mandatory-notice address `tenders@afyadigital.example`; registered through **Start bid** on 19 May 2027, 09:20 EAT.

Clarification: received 26 May 2027, 09:00 EAT, before the 27 May 2027, 17:00 EAT clarification deadline. Question: **May the two comparable contracts be from different customers?** Response: **Yes. The Tender requires two comparable contracts and does not require both contracts to be from the same customer.** `response_audience = All registered candidates`; `affects_published_tender = No`. The broadcast hides the questioner.

Candidate-notice fixture: the clarification response is Delivered to `tenders@afyadigital.example` at 26 May 2027, 11:01 EAT; addendum `ADD-MOH-2027-033-001` is Delivered at 31 May 2027, 09:02 EAT; the revised-deadline fact is part of the same addendum notice, not a duplicate message. An isolated failed-delivery fixture uses candidate `ARR-MOH-2027-033-009`, destination `procurement@failed-delivery.example`, three attempts and status Failed; the addendum remains Issued.

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

Show green result **Supported — IT equipment using the standard Open Tender format.** Closed disclosure **Why this requisition is supported** contains Category Goods; Product straightforward off-the-shelf IT equipment; Method Open Tender; Reservation Youth; County-residents restriction Not applicable; Lotting Single lot; Currency KES; Award package One; Plan horizon Single year. Closed disclosure **Template and source details** contains the exact template, official source and applicable verified reservation-rule snapshot.

Footer left **Cancel**; right primary **Start Tender**. Both enabled. No package, template, schema, manifest or configuration selector.

**Unsupported variant.** Use the isolated Unsupported start facts; show **This requisition is not supported by the current IT-equipment Tender format.** Disable Start Tender; retain Cancel.

**Visual check.** The user knows what will be created and makes no false template or configuration decision.

### 10.4 TPR-DES-03 — Draft: Tender details

**Purpose.** Set the dates, security and optional meeting.

**Fixture outside the artboard.** Brian Wafula; Draft Version 1; 20 Mar 2027, 09:10 EAT.

**Header.** Title **Supply and delivery of business laptops**. Description **Set the dates and security suppliers must follow.** Badge **Draft**. Tender and Requisition references appear on separate muted lines beneath. No header action.

**Composition, top to bottom.**

1. The §10.17 next-step and Tender journey guidance sits below the header; there is no preparation stepper.
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

**Header.** Reuse TPR-DES-03. The §10.17 Tender journey remains at Preparation; it does not split the two editor tasks into lifecycle stages.

**Composition, top to bottom.**

1. Text **The authorised requirements are already included. Choose only the additional evidence suppliers must provide and complete the contract terms below.**
2. Section **Supplier evidence**: read-only **Youth reservation declaration and evidence** generated from the applicable verified rule, with plain summary **Suppliers must declare Youth eligibility and provide the published certificate reference, validity and evidence**; Manufacturer authorisation; Product datasheets or brochures; read-only Warranty confirmation with source; Past supply experience with dependent positive-whole-number fields **Minimum comparable contracts** and **Within the last ___ years**; After-sales support evidence with dependent option. Arrange dependent controls directly beneath the parent. Do not expose rule identifiers in this routine view and do not allow the officer to edit the inherited reservation treatment. Do not use preset number/year menus. Helper: **Use only experience requirements that are necessary and proportionate for this purchase.**
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

**Header.** Title **Review Tender**. Description **Check the complete Tender and submit it to the Head of Procurement Function.** Badge Draft; references beneath. The §10.17 Tender journey remains at Preparation until submission.

**Composition, top to bottom.**

1. The §10.17 **Your turn** guidance and existing Submit action replace the green Ready to submit narrative; the review note remains distinct.
2. Amber panel **1 review note** with the manufacturer-authorisation note and link **Review supplier requirements**.
3. Key facts: Requisition; Quantity; Approved value; Method; Submission deadline; Tender security; Reservation Youth; Latest delivery.
4. Actions **Preview Invitation** and **Preview complete Tender**, secondary and enabled.
5. Review sections: Tender details; Requirements from the authorised requisition; Supplier pricing schedule; Supplier and evaluation requirements; Contract terms; Technical evidence. Each has a plain summary and Show details. Only a section containing a must-fix item or review note starts open.
6. Supplier pricing detail: one 250-Each row; Unit price/Tax **Completed by supplier**; totals **Calculated from supplier response**. The authorised value is absent from price cells.
7. Requirements detail contains all §10.1 rows. Technical evidence contains exact template/source/package identities, both item/source lineages, mappings and digests.
8. Footer: secondary **Back**, primary **Submit for approval**.

**Needs-attention variant.** Use the isolated Needs-attention review facts. The §10.17 **Your turn, blocked** guidance names the inspection-location blocker and links **Review contract terms** to the exact task/field. Submit is unavailable until fixed; the review note remains separate and does not block submission.

**Confirmation.** Heading **Submit this Tender for approval?** Text **The submitted Version will be locked. Charles Mutiso can return it or approve the package for publication review.** Footer Cancel / **Submit for approval**.

**Visual check.** Result and exceptions lead; complete content remains available without revisiting preparation tasks.

### 10.7 TPR-DES-06 — HOPF approval

**Purpose.** Decide whether the immutable package may proceed to publication authorisation.

**Fixture outside the artboard.** Charles Mutiso; HOPF; submitted Version 2; 20 Apr 2027, 10:00 EAT; Charles did not prepare/submit it.

**Header.** Title **Review Tender package**. Description **Decide whether this Tender may proceed to Accounting Officer publication review.** Version and references beneath; no awaiting-action badge.

**Composition, top to bottom.**

1. The §10.17 **Your turn** guidance joins the existing decision actions. State once, in the confirmation, that approval locks the package for the Accounting Officer and does not publish it.
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

**Header.** Title **Authorise Tender publication**. Description **Review the approved package and the channels through which it must be published.** Approved Version and references beneath; no awaiting-action badge.

**Composition, top to bottom.**

1. The §10.17 **Your turn** guidance joins the existing Authorise publication action. The confirmation explains that authorisation starts publication work and does not itself publish the Tender.
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

**Header.** Tender title. Description **Confirm where and when the approved Tender was published.** Publication identity and references beneath; no duplicate confirmation-required badge.

**Composition, top to bottom.**

1. The §10.17 blocked next step states **2 of 4 required channels confirmed** once. The channel table below identifies the two outstanding channels and their evidence controls; the Tender is not yet Published.
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

**Fixture outside the artboard.** Charles Mutiso; HOPF; 1 Jun 2027, 12:00 EAT; addendum issued; supplier clarification answered.

**Header.** Title **Supply and delivery of business laptops**. Description **Published and open for supplier submissions.** Badge **Published — open**. Tender reference beneath. Upper-right **View public Tender**.

**Composition, top to bottom.**

1. Current facts (without a second status narrative): Published at **15 May 2027, 08:00 EAT**; Current submission deadline **12 Jun 2027, 11:00 EAT**; Publication authorised by **Amina Hassan**; Effective addenda **1**.
2. Documents row: View Invitation; View complete Tender; View current addendum.
3. Channel table with all four Confirmed results, available times and evidence links.
4. Section **Changes and notices**. Addenda table columns Addendum; Change; Issued; Deadline; Action. Row ADD-MOH-2027-033-001; Delivery point clarified; 31 May 2027, 09:00 EAT; 12 Jun 2027, 11:00 EAT; View.
5. Clarifications table columns Question; Related notice; Received; Response status; Candidate notice; Action. One row with the shared clarification; Related notice **None**; 26 May 2027, 09:00 EAT; Answered; **1 of 1 delivered**; View.
6. Section **Tender content** with six closed summaries and complete in-page detail.
7. Section **History and evidence** collapsed with decisions, digests and publication confirmations.
8. HOPF actions at foot: primary **Prepare addendum**; secondary **Recommend cancellation**. Accounting Officer variant replaces both with destructive **Cancel Tender**. Procurement Officer sees **Prepare addendum** only. Departmental reader/Auditor sees no business action.

**No-addendum variant.** Addenda text **No addenda have been issued.** Clarifications retain the general question/answer because they do not depend on an addendum. Current deadline remains 5 Jun 2027, 11:00 EAT.

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

**Awaiting-publication variant.** After the 08:30 issue decision, show the immutable issue decision as a fact; the §10.17 next step states that channel confirmation remains before effectiveness. Show the frozen changed-fields comparison and successor deadline read-only. Channel table columns Channel; Result; Available at; Confirmation/action. Use the four addendum channel facts in §10.1; before confirmation each row is **Awaiting confirmation** with **Confirm publication**. Confirmed rows show their actual Available at value and **View confirmation**. Do not expose definition identity or digest.

**Addendum confirmation dialog.** Heading **Confirm addendum publication — {channel}**. Intro **Confirm only after ADD-MOH-2027-033-001 was publicly available through this channel.** Fields use the channel-specific Available date/time, reference, applicable public URL, evidence file and optional Notes maximum 500 from §10.1. Required attestation **I confirm that ADD-MOH-2027-033-001 was publicly available through {channel} at the date and time stated above.** Footer Cancel / **Confirm publication**.

**Issued variant.** After the fourth confirmation, show green result **Addendum issued**; effective **31 May 2027, 09:00 EAT**; confirmation completed **09:07 EAT**; revised deadline **12 Jun 2027, 11:00 EAT**. All rows offer **View confirmation** and no mutation action. The bidder-facing successor definition and deadline are now effective together.

**Material-change variant.** Use the isolated Material addendum facts. Result **This change cannot be made by addendum.** Omit **Submit for issue**; show **Cancel the Tender and start a newly governed Tender if procurement must continue.** Show primary **Ask Amina Hassan (Accounting Officer) to consider cancellation** as the hand-off action, secondary **Discard addendum draft**, and **View cancellation requirements** as a page link. The request does not cancel the Tender or issue the addendum. While the request is open, show the waiting variant in §10.17 and suppress the duplicate request action. If AO closes the review, show the recorded reason and only **Discard addendum draft** as the fix for this proposal.

**Visual check.** The affected content, before/after difference, materiality and deadline consequence are immediately understandable.

### 10.12 TPR-DES-11 — Respond to supplier clarification

**Purpose.** Answer an authenticated question from a Tender-bound candidate without changing the published Tender informally.

**Fixture outside the artboard.** Brian Wafula; Procurement Officer; 26 May 2027, 10:30 EAT; shared clarification unanswered.

**Header.** Title **Respond to supplier clarification**. Description **Answer the question and state whether the response changes the published Tender.** Tender reference and clarification deadline beneath.

**Composition, top to bottom.**

1. Read-only Candidate **Registered Tender candidate**; Received **26 May 2027, 09:00 EAT**; Related addendum **None**. This proves only the Bid Submission registration and Tender relationship, not supplier qualification or eligibility.
2. Read-only Question with exact fixture text.
3. Response textarea with exact fixture response.
4. Yes/No **Would this response change the published Tender?** Fixture No.
5. With No, show **Who should receive this answer?** choices **Only the supplier who asked** and **All registered candidates**; fixture All registered candidates. Supporting text **A general answer will not identify who asked.**
6. Footer Cancel / primary **Send response**.

**Published-change variant.** With Yes, remove the recipient choice and show blocking result **Issue an addendum before sending this answer.** Supporting text **A clarification cannot change requirements, criteria, dates or supplier obligations on its own.** Primary **Prepare addendum**; no Send response. After the linked addendum is Issued, show its reference read-only and permit **Send response to all registered candidates**.

**Delivery-failure variant.** The Answered detail shows **1 candidate notice failed** and the exact protected recipient only to authorised procurement/support roles. Action **Retry notice** reuses the same notice and content. The clarification remains Answered and the Tender remains open.

**Visual check.** The officer can answer an ordinary pre-bid question without an addendum, cannot change published content through an answer, and sees notice failure without mistaking it for a failed Tender action.

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

**Cancellation-review request variant (TPR-DES-12-REQUEST).** Amina Hassan sees the exact `TND-MOH-2027-039` request from Brian Wafula: proposed quantity 250 Each → 300 Each, reason **Additional deployment sites require 50 more laptops**, and the finding that an addendum cannot expand the purchase. This is a request to consider cancellation, not a cancellation decision. The fixture supplies no request time or lawful cancellation ground, so show neither. Next-step and tracker are in §10.17. Available actions: primary **Cancel Tender** opens the existing ground/reason decision flow; secondary **Close cancellation review** requires Amina to give a reason and leaves the Tender open, the addendum blocked and all published content unchanged. No new approval stage or automatic cancellation.

**Cancelled-detail variant.** Badge Cancelled; show decision actor/time, ground, reason, notice status, PPRA report status and deadlines. No Tender/addendum/clarification action. Evidence actions appear only to the authorised procurement function for the exact outstanding obligation.

**Visual check.** Authority, ground, finality and unfinished compliance obligations remain distinct.

### 10.14 TPR-DES-13 — Returned and requisition-correction states

**Returned fixture.** Brian Wafula; copied Draft Version 2; 25 Mar 2027, 14:05 EAT. Reuse TPR-DES-04 with amber **Returned for correction** panel containing returned by/time/comment. Open Supplier and contract requirements with the return comment and §10.17 Your turn next step. Save/Review available; no task stepper.

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
| Already started — Brian with linked-Tender read access | Tender already started | This requisition is linked to TND-MOH-2027-033. | **Open Tender** |
| Already started — viewer without linked-Tender read access | Requisition unavailable | This requisition cannot be used to start a Tender. Do not show the Tender reference, title, owner or other identifying facts. | **Back to Tenders** |
| Template unavailable — STD inspection reader | Tender format unavailable | The standard IT-equipment Tender format is not available. | **View STD Template** |
| Template unavailable — reader without STD inspection access | Tender format unavailable | The standard IT-equipment Tender format is not available. | **Back to Tenders** |
| Bound release Superseded — Brian, integrity passed | Tender format has a newer release | This Tender remains on release 1.1. Its integrity and renderer checks passed; KenTender will not change the format automatically. | **View STD Template**; **Continue** |
| Bound release Superseded — reader with STD inspection access | Tender format has a newer release | This Tender remains on release 1.1. Existing work retains the bound format. | **View STD Template** |
| Bound release Superseded — reader without STD inspection access | Tender format has a newer release | This Tender remains on release 1.1. Existing work retains the bound format. | **Back to Tenders** |
| Bound release Withdrawn — STD inspection reader | Tender format withdrawn | This Tender cannot continue to publication because release 1.1 was withdrawn. Your work is preserved. | **View STD Template** |
| Bound release Withdrawn — reader without STD inspection access | Tender format withdrawn | This Tender cannot continue to publication because release 1.1 was withdrawn. Your work is preserved. | **Back to Tenders** |
| Bound release integrity failed — STD inspection reader | Tender format could not be verified | This Tender is preserved, but no further approval or publication action is permitted until the release owner resolves the verification failure. | **View STD Template** |
| Bound release integrity failed — reader without STD inspection access | Tender format could not be verified | This Tender is preserved, but no further approval or publication action is permitted until the release owner resolves the verification failure. | **Back to Tenders** |
| Publication not configured — System Manager | Publication rule unavailable | The publication rule is not configured for this Tender. Configure the governed rule in System setup. | **Open System setup** |
| Publication not configured — routine Tender reader | Publication rule unavailable | The publication rule is not configured for this Tender. A System Manager must configure it. | **Back to Tenders** |
| Stale write | Tender changed | Another user changed this Tender. | Reload |
| Load failure | Tenders could not be loaded | Try again. | Try again |

Each is a full inline state under KT-STD-001 v1.8 §3A. Successful content never renders behind it. Administrator/System Manager follows technical read and never receives Forbidden.

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
| TPR-DES-09 | HOPF / readers | Read effective Published Tender | HOPF open; Procurement Officer open; AO open; reader/Auditor; No addendum; Submission period ended. |
| TPR-DES-10 | Procurement Officer / HOPF | Prepare, publish and issue addendum | Draft addendum; HOPF issue; Awaiting publication; channel confirmation dialog; Issued; Material change blocked; After cancellation-review request; After AO closes cancellation review. |
| TPR-DES-11 | Procurement Officer / HOPF | Respond to supplier clarification | Ordinary/general broadcast; published-change blocked; delivery failure. |
| TPR-DES-12 | Accounting Officer | Cancel Tender | AO cancellation; HOPF recommendation; cancellation-review request; confirmation; Cancelled detail for procurement holder; Cancelled detail for AO/reader. |
| TPR-DES-13 | Procurement Officer / HOPF | Correct returned work or stop for Requisition correction | Returned Draft; correction dialog; correction requested/stopped; corrected successor available. |
| TPR-DES-14 | All permitted roles | Recover from common read/state errors | Forbidden; Not found; source unavailable; already started for Brian with linked-Tender read access; already started for viewer without linked-Tender read access; template unavailable for STD inspection reader; template unavailable for reader without STD inspection access; Superseded for Brian; Superseded for reader with STD inspection access; Superseded for reader without STD inspection access; Withdrawn for STD inspection reader; Withdrawn for reader without STD inspection access; integrity failed for STD inspection reader; integrity failed for reader without STD inspection access; publication not configured for System Manager; publication not configured for routine Tender reader; stale write; load failure. |

The design set is complete only when every base artboard and named variant has been rendered and checked against its visual check.

### 10.17 Next-step and journey content for record variants

Use KT-STD-001 v1.8 §§2.9.1–2.9.3. This section is the complete design input for the shared components. One row describes the viewer stated in the artboard fixture; alternate role views use §5.9's holder rule and do not gain an action by reading the record. Focused dialogs, TPR-DES-01 workspace, TPR-DES-02 start dialog, and TPR-DES-14 full-page denial/load/error states carry neither component. They keep their existing plain message and recovery action. The content below sits beneath the record header, within the existing action area, before the first working section. At 1440 × 1024, if the full tracker would displace that section, use its single-line reduced form **{current stage} · {position} of 5**; at 390 px use that reduced form without horizontal scrolling; the next-step text remains with its action. No separate card, timeline or task-navigation stepper is drawn.

Tracker stage labels, in this exact order: **Prepare Tender** (`P`), **HOPF approval** (`H`), **AO publication authorisation** (`A`), **Confirm publication** (`C`), **Manage open Tender** (`O`). Each tuple below gives the five exact markers in P/H/A/C/O order: `D` done, `C` current, `B` blocked, `N` not started. Only the current/blocked stage shows the holder. Runtime resolves the named person; isolated segregation fixtures with no eligible alternate person show the responsibility without inventing a name. A returned Draft resets P to current/blocked and H to not started. An addendum is work within O; it does not restart C for the whole Tender. The tracker is orientation only and does not navigate between editor sections. No upstream/downstream link is supplied for these artboards; draw none. History holds actor/time for completed stages. For a stopped Tender, keep P blocked until a successor Draft starts; a corrected authorised handoff makes P current for the officer who can start it. For cancellation or submission end, all applicable completed stages show D; cancellation is named once by the next-step line.

| Record artboard / variant | P/H/A/C/O markers | Next-step kind; exact headline and optional sentence | Holder and fix/action labels | Existing element replaced |
|---|---|---|---|---|
| DES-03 Draft details; PHYSICAL; ONLINE | C/N/N/N/N | **Your turn:** Set the Tender dates, security and meeting details. | Procurement Officer Brian Wafula; **Save draft**, **Continue**. | Three-part progress row and generic Needs attention chip. |
| DES-04 Supplier/contract; add/edit/remove evidence; full disclosure parent | C/N/N/N/N | **Your turn:** Set supplier evidence and contract terms. | Brian Wafula; **Save draft**, **Review Tender**. | Three-part task progress and duplicate task status. Focused evidence dialogs have neither component. |
| DES-05 Review ready | C/N/N/N/N | **Your turn:** Submit this Tender for approval. | Brian Wafula; **Submit for approval**. | Three-part progress and Ready to submit result. The separate review note stays. |
| DES-05 Needs attention | B/N/N/N/N | **Your turn, blocked:** Enter the inspection and acceptance location. | Brian Wafula; **Review contract terms**. | Needs attention panel and duplicate disabled-submit explanation. Review note stays separate. |
| DES-06 HOPF review; return/approve dialog parent | D/C/N/N/N | **Your turn:** Decide whether to approve this Tender package. | HOPF Charles Mutiso; **Return for correction**, **Approve Tender package**. | Awaiting your approval badge narrative and Ready to approve result. Dialogs have neither component. |
| DES-06 segregation blocked | D/B/N/N/N | **Waiting on someone:** A System Manager must assign an eligible Head of Procurement Function to decide this Version. This negative fixture supplies no System Manager name or assignment time, so neither is invented. | Holder: System Manager until an eligible HOPF is assigned; then that HOPF holds the decision. The existing **Back to Tenders** page link sits outside the block; no approval action or fix is shown to the conflicted viewer. | Segregation warning as a second status narrative. |
| DES-07 AO authorisation; confirmation dialog parent | D/D/C/N/N | **Your turn:** Authorise publication of the approved Tender package. | AO Amina Hassan; **Authorise publication**. | Awaiting publication authorisation narrative and Ready to authorise result. Dialog has neither component. |
| DES-07 segregation blocked | D/D/B/N/N | **Waiting on someone:** A System Manager must assign an eligible Accounting Officer to decide this Version. This negative fixture supplies no System Manager name or assignment time, so neither is invented. | Holder: System Manager until an eligible AO is assigned; then that AO holds the decision. The existing **Back to Tenders** page link sits outside the block; no authorisation action or fix is shown to the conflicted viewer. | Segregation warning as a second status narrative. |
| DES-08 Publication confirmation; online-channel parent | D/D/D/C/N | **Your turn:** Confirm publication through Notice board and Two national newspapers; 2 of 4 channels are confirmed. | HOPF Charles Mutiso; **Confirm publication** on each outstanding row. | Amber result and separate Publication confirmation required narrative. Channel table retains its factual results. |
| DES-08 invalid evidence | D/D/D/B/N | **Your turn, blocked:** State Portal evidence could not be accepted. | Charles Mutiso; **Choose evidence file**, **Confirm publication**. | Generic incomplete-channel warning; preserve entered non-file values. |
| DES-08 conflicting confirmation | D/D/D/C/N | **Your turn:** Continue with the channels still awaiting confirmation. | Charles Mutiso; **View confirmation** for State Portal, then **Confirm publication** on outstanding channels. | Duplicate conflicting-confirmation status panel; the conflict remains a specific immutable-row error. |
| DES-09 Published; no-addendum; HOPF | D/D/D/D/C | **Your turn:** Prepare an addendum or recommend cancellation if the open Tender needs it. These are available options, not overdue work. | Charles Mutiso; **Prepare addendum**, **Recommend cancellation**. Both are visible and enabled in this HOPF fixture. | Published-and-open explanatory status panel narrative; factual publication/deadline values remain. |
| DES-09 Procurement Officer view | D/D/D/D/C | **Your turn:** Prepare an addendum if the published Tender needs a non-material correction. This is an available option, not assigned work. | Brian Wafula; **Prepare addendum**. | Duplicate open status explanation. |
| DES-09 AO view | D/D/D/D/C | **Your turn:** You can cancel this open Tender on an applicable ground. This is an available option, not an assigned cancellation review. | Amina Hassan; **Cancel Tender**. It is visible and enabled in this AO open-Tender fixture. | Duplicate open status explanation. |
| DES-09 reader/Auditor | D/D/D/D/C | **Not involved:** no next-step line. | No business action. | No new block; existing factual status stays. |
| DES-09 submission ended | D/D/D/D/D | **Done:** The system closed supplier submission at 12 Jun 2027, 11:00 EAT. | No Tender action; exact deadline is the completion fact. | Submission period ended status sentence; badge may remain as compact identity, not a second narrative. |
| DES-10 Draft addendum | D/D/D/D/C | **Your turn:** Submit the non-material addendum for issue. | Brian Wafula; **Save draft**, **Submit for issue**. | Draft addendum status sentence; materiality/deadline facts stay in the working region. |
| DES-10 HOPF issue | D/D/D/D/C | **Your turn:** Decide whether to issue this addendum. | Charles Mutiso; **Return for correction**, **Issue addendum**. | Ready to issue result. |
| DES-10 awaiting channel confirmation | D/D/D/D/C | **Your turn:** Confirm publication of ADD-MOH-2027-033-001 through the remaining original channels. | Charles Mutiso; **Confirm publication** on each outstanding channel. | Publication confirmation required and duplicate not-yet-effective banner. |
| DES-10 Issued | D/D/D/D/C | **Done:** Charles Mutiso completed addendum publication on 31 May 2027, 09:07 EAT. | No addendum mutation; **View confirmation** remains read-only. | Addendum issued result narrative; effective time/deadline stay factual. |
| DES-10 material change | D/D/D/D/B | **Your turn, blocked:** Increasing the laptop quantity from 250 to 300 cannot be issued as an addendum. | Procurement Officer Brian Wafula; fixes **Ask Amina Hassan (Accounting Officer) to consider cancellation**, **Discard addendum draft**. **View cancellation requirements** remains an ordinary page link outside the block. | Material-change warning narrative; retain changed-value comparison. |
| DES-10 after cancellation-review request | D/D/D/D/B | **Waiting on someone:** Accounting Officer Amina Hassan is considering cancellation of TND-MOH-2027-039. The isolated fixture supplies no request time; omit it. | Amina Hassan; no action in the waiting line. **View cancellation requirements** remains a page link outside it. | Material-change blocker action after it creates the hand-off; keep the proposed comparison as evidence. |
| DES-10 after AO closes cancellation review | D/D/D/D/B | **Your turn, blocked:** The 250-to-300 Each addendum remains unissuable; Amina Hassan closed the cancellation review with a recorded reason. | Brian Wafula; **Discard addendum draft** is the sole fix for this proposal. Keep **View cancellation requirements** outside the block. | Retain the changed-value comparison and AO's exact recorded reason; no repeat request for this proposal. |
| DES-11 ordinary/general clarification | D/D/D/D/C | **Your turn:** Send the answer to all registered candidates. | Brian Wafula; **Send response**. | Duplicate answer-status narrative. Question and audience facts stay. |
| DES-11 published-change | D/D/D/D/B | **Your turn, blocked:** Issue an addendum before sending this answer. | Brian Wafula or Charles Mutiso; **Prepare addendum**. | Separate blocking result paragraph. |
| DES-11 delivery failure | D/D/D/D/B | **Your turn, blocked:** 1 candidate notice failed delivery; the Tender remains open. | HOPF Charles Mutiso in this fixture; **Retry notice**. | Failed-notice status panel; protected recipient and attempts stay in detail. |
| DES-12 AO cancellation; recommendation variant | D/D/D/D/C | **Your turn:** Decide whether to cancel this Tender for inadequate budgetary provision. | Amina Hassan; **Cancel Tender**. | Separate cancellation decision narrative. Warning about finality remains. |
| DES-12 cancellation-review request | D/D/D/D/C | **Your turn:** Consider the request to cancel TND-MOH-2027-039 because the proposed quantity increase cannot be issued by addendum. | Amina Hassan; **Cancel Tender**, **Close cancellation review**. | Request work item becomes the single next-step line. The 250-to-300 Each comparison stays in the working region. |
| DES-12 Cancelled detail, procurement holder | D/D/D/D/C | **Your turn:** Record the outstanding cancellation notices and PPRA report by 18 Jun 2027. | Procurement Officer Brian Wafula in this fixture; **Record cancellation notice evidence**, **Record PPRA report evidence**. | Generic cancelled status narrative; decision actor/time and deadlines remain factual. |
| DES-12 Cancelled detail, AO/reader | D/D/D/D/D | **Done:** Amina Hassan cancelled this Tender on 4 Jun 2027, 14:00 EAT. | No Tender mutation; procurement compliance remains a separate holder's work. | Generic cancelled status narrative. |
| DES-13 Returned Draft | C/N/N/N/N | **Your turn:** Address Charles Mutiso's return comment about manufacturer authorisation. | Brian Wafula; **Save draft**, **Review Tender**. Both are visible and enabled; a later Submit attempt uses the current server validation result. | Returned for correction panel's duplicated next-action sentence and task progress. Keep exact return comment. |
| DES-13 Correction requested | B/N/N/N/N | **Waiting on someone:** Grace Wanjiku, Departmental Author, is correcting the requisition since 21 Apr 2027, 09:00 EAT. | Grace Wanjiku; **View requisition status** and **View history** remain existing page links outside the waiting line; they are not next-step actions or fixes. | This Tender cannot continue status panel. |
| DES-13 Corrected successor available | C/N/N/N/N | **Your turn:** Start a corrected Tender Version from authorised Requisition Version 2. | Brian Wafula; **Start corrected Tender Version**. | A corrected requisition is ready result panel. |

The marker tuple and next-step stage must always agree. Done for a completed addendum refers to that addendum item while the Tender remains at O. Outstanding cancellation compliance keeps O current only for its assigned holder; other viewers see the completed Tender journey. For waiting variants on a record that another person holds, use the same tuple and replace the next-step line with **Waiting on {responsibility} {name} since {recorded instant}** from §5.9; do not offer the viewer the holder's controls. For technical readers use §5.9's Not involved/waiting/done rule. A full-page error in DES-14, a focused confirmation/dialog or the DES-01 workspace never inherits the parent tracker inside itself. Keep the parent record guidance visible behind a modal only as background, not as a second component.

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

### 11.6 Published Tender, clarifications, addenda and candidate notices

| Visible control | Behaviour |
|---|---|
| Prepare addendum | Calls `CreateAddendumDraft` and opens TPR-DES-10. |
| Save draft | Calls `UpdateAddendumDraft` and retains Draft status. |
| Submit for issue | Calls `SubmitAddendumForIssue`; the server rechecks materiality, deadline and scope. |
| Return for correction | Requires comment and calls `ReturnAddendumForCorrection`. |
| Issue addendum | Opens confirmation and calls `IssueAddendum`; success means the successor bidder definition is frozen and required channel-confirmation records exist, but neither is effective yet. |
| Confirm addendum publication | Opens the channel-specific confirmation dialog and calls `ConfirmAddendumPublicationChannel`; final confirmation activates the issued addendum, revised deadline and successor definition together. |
| Respond | Opens TPR-DES-11 for the authenticated clarification. |
| Send response | Calls `RespondToTenderClarification`; sends directly or anonymously to the frozen candidate audience only when no published change is introduced. |
| Prepare addendum | From a published-change clarification, opens TPR-DES-10 with the Tender/clarification context; it does not mark the clarification Answered. |
| Retry notice | Calls `RetryFailedCandidateNotice` for the same immutable subject, recipient and content; it cannot change the candidate audience or Tender state. |
| Ask Amina Hassan (Accounting Officer) to consider cancellation | Calls `RequestTenderCancellationReview` for the exact blocked material-addendum proposal; creates one AO work item and one sender waiting item, without changing the Tender or publishing the addendum. |
| Discard addendum draft | Calls `DiscardAddendumDraft` after confirmation; archives only the unissued draft and returns to the unchanged Published Tender. |
| View cancellation requirements | Opens the read-only cancellation requirements summary on the Tender record for the Procurement Officer or HOPF; it does not open the AO-only cancellation decision or change status. |
| View or download Invitation / complete Tender / Addendum | Opens or streams the immutable generated document represented by its recorded digest. |
| View public Tender | Opens the supplier-visible published package without internal values, decisions or evidence. |
| View addendum / clarification | Opens the exact immutable issued addendum or recorded question/response with source identity protected from public/general audiences. |
| History and evidence | Expands the permitted read projection; it creates no event and exposes protected facts only to authorised roles. |

An issued addendum appears in the Tender record only after every required channel is confirmed. While channel confirmation is incomplete, the record shows its truthful publishing state.

### 11.7 Cancellation

| Visible control | Behaviour |
|---|---|
| Recommend cancellation | Requires a ground/reason recommendation and calls `RecommendTenderCancellation`; it does not cancel. |
| Cancel Tender | Opens the §10.13 confirmation and then calls `CancelTender`. |
| Close cancellation review | AO records a reason and calls `CloseTenderCancellationReview`; removes the AO work item, leaves the Tender open and the material addendum blocked. |
| Record cancellation notice evidence | Records evidence against one required original channel. |
| Record PPRA report evidence | Records the report acknowledgement/reference and date. |
| Record candidate notice evidence | Records dispatch evidence against the governed candidate set. |

After `CancelTender` commits, preparation, publication, addendum and clarification mutations are absent. Only outstanding compliance-evidence and candidate-notice recovery actions remain. Failure or uncertainty in a notice channel does not reopen the Tender.

### 11.8 Common recovery actions

| Visible control | Behaviour |
|---|---|
| Back / Back to Tenders | Returns to the named safe route without mutation. |
| Open Tender | Opens the already-created authorised Tender returned by the conflict result. |
| View STD Template | Opens the exact bound release for a reader with STD inspection access; on an unavailable new binding, opens the permitted STD Templates view without creating a Tender. |
| Open System setup | Opens the governed publication-rule configuration for an authorised System Manager; it does not change the rule by navigation alone. |
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
- All controls and content meet KT-STD-001 v1.8 accessibility and responsive-release gates.

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
| Publication authorised | AO, time, approved Version, package digest, Published Bid Definition identity/digest, rule snapshot and required channel records. |
| Channel confirmed | Subject type/identity/digest, channel, actual availability time, reference/URL, evidence digest, exact attestation and HOPF identity/time. |
| Published | Every mandatory channel confirmation, computed actual invitation time and final publication digest. |
| Addendum issued | Original publication, change comparison, materiality result, revised deadline, HOPF/time, document digest, frozen successor-definition identity/digest and subject-scoped channel confirmations. |
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
7. Audit access is read-only and scoped. Protected clarification-source identity and notice destination are restricted to authorised procurement, support, oversight and investigation use.
8. Retention, legal hold and disposal follow the platform records-management policy; application deletion is not a business-user action.

## 13. Deterministic seed contract

### 13.1 Seed rules

Seed identities and timestamps are stable. Re-running the seed is idempotent: it creates no duplicate Tender, Version, publication, channel confirmation, addendum, clarification, candidate notice, cancellation or task. All timestamps below are EAT and are stored with their UTC equivalents.

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
| 19 May 2027 09:20 | Receive candidate-registration event from Start bid | Afya Digital Supplies Limited becomes an Active Tender candidate with one verified mandatory-notice address. |
| 26 May 2027 09:00 | Receive authenticated clarification | Clarification awaiting response. |
| 26 May 2027 11:00 | Answer general clarification | Answer frozen for all registered candidates without identifying the asker. |
| 26 May 2027 11:01 | Deliver clarification notice | One of one candidate notices Delivered. |
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
| TPR09-AC-001 | The authenticated application exposes one user-facing menu item named **Tenders**, not separate Preparation and Publication modules. |
| TPR09-AC-002 | The Tenders workspace combines authorised Requisition starts, Draft work, decisions, publication work and open Tenders in one role-safe queue. |
| TPR09-AC-003 | A user without a permitted responsibility receives the §10.15 Forbidden state and no Tender data. |
| TPR09-AC-004 | A user with permitted cross-entity scope sees only records in that scope; changing a filter cannot expand it. |
| TPR09-AC-005 | Opening a route, drawer, preview or dialog creates no Tender, Version, publication, task or audit business event. |
| TPR09-AC-006 | A Tender can start only from an available authorised Requisition handoff whose compatibility result permits start. |
| TPR09-AC-007 | Concurrent or repeated `StartTender` requests for one handoff produce one Tender and return its identity. |
| TPR09-AC-008 | Start snapshots the exact authorised Requisition, requirements, Planning references, method, reservation, lotting, funding and applicable governed templates/rules. |
| TPR09-AC-009 | Inherited content is visibly read-only and has a route to its source; the Tender service cannot update owner data directly. |
| TPR09-AC-010 | Requisition-owned correction stops the current Tender Version and can continue only from a newly authorised successor handoff. |

### 14.2 Preparation and generated content

| ID | Acceptance criterion |
|---|---|
| TPR09-AC-011 | Preparation is presented as three understandable tasks: Tender details; Supplier and contract requirements; Review and submit. |
| TPR09-AC-012 | Tender details show the purchase, quantities, funding and source facts before officer-authored fields. |
| TPR09-AC-013 | Closing date/time, clarification deadline and meeting choices validate as dates and as an ordered business sequence. |
| TPR09-AC-014 | A physical meeting requires date/time, venue and access instructions; an online meeting requires date/time and join instructions. |
| TPR09-AC-015 | Supplier and contract requirements separate inherited requirements, officer evidence requirements, contract values and generated content; comparable-contract count and experience period are positive whole-number inputs with no preset value menu. |
| TPR09-AC-016 | An officer can add, edit and remove only Draft evidence requirements; each change is versioned and audited. |
| TPR09-AC-017 | Qualification or evidence wording cannot silently alter an inherited mandatory technical, warranty or acceptance requirement. |
| TPR09-AC-018 | The generated price schedule contains the exact authorised line items, quantities, units, lots and funding split. |
| TPR09-AC-019 | The generated technical schedule contains all eleven §10.1 technical requirements without truncation or substitution. |
| TPR09-AC-020 | The generated warranty/support schedule contains all six §10.1 values and the acceptance schedule all five checks. |
| TPR09-AC-021 | Optional service/material schedules are absent when their inherited source sets are empty and present only when governed data exists. |
| TPR09-AC-022 | Generated evaluation mappings trace every mandatory check to its governed source and shared evaluation group and cannot be edited as free text. |
| TPR09-AC-023 | Invitation and complete-Tender previews use saved Version data and do not submit, approve, authorise or publish. |
| TPR09-AC-024 | Document generation is deterministic: identical recorded inputs produce the recorded document digest. |
| TPR09-AC-025 | Save returns the authoritative record version; a stale save never overwrites another user's change. |

### 14.3 Review, approval and segregation

| ID | Acceptance criterion |
|---|---|
| TPR09-AC-026 | Review displays one readiness result, issue counts and direct issue links; it does not require users to interpret internal rule identifiers. |
| TPR09-AC-027 | A Must fix issue prevents submission and identifies the exact task, field or owner route. |
| TPR09-AC-028 | A Review note is visible but does not prevent submission unless another governed rule fails. |
| TPR09-AC-029 | Compatibility is evaluated from authoritative owner projections at start, submit, approve and publication authorisation. |
| TPR09-AC-030 | Submission freezes one exact Version, package digest and generated-document set. |
| TPR09-AC-031 | After submission, the submitted Version is read-only to every business actor. |
| TPR09-AC-032 | HOPF return requires a comment, preserves the submitted Version and creates one copied Draft. |
| TPR09-AC-033 | HOPF approval records the exact submitted Version and package digest and creates an AO publication task. |
| TPR09-AC-034 | HOPF approval does not create channel confirmations, set `published_at` or expose documents to suppliers. |
| TPR09-AC-035 | A person who prepared or submitted a Version cannot approve that Version as HOPF, regardless of concurrent role labels. |
| TPR09-AC-036 | Reopening an approved Tender is possible only before publication authorisation, requires a reason and creates a copied Draft. |
| TPR09-AC-037 | HOPF, AO and reader artboards use the exact fixture actors, values and statuses in §10.1. |
| TPR09-AC-038 | The AO sees the approved package, decision facts and generated required channels, with no package-edit control. |
| TPR09-AC-039 | A person who prepared, submitted or HOPF-approved a Version cannot authorise its publication as AO. |
| TPR09-AC-040 | Every decision command rechecks state, assignment, segregation and package integrity on the server. |

### 14.4 Publication

| ID | Acceptance criterion |
|---|---|
| TPR09-AC-041 | Publication authorisation records AO, time, approved Version, package digest, complete Published Bid Definition identity/digest, effective rule snapshot and complete required-channel set atomically without mutating the approved Version. |
| TPR09-AC-042 | The AO cannot choose, remove, replace or edit a required publication channel. |
| TPR09-AC-043 | Committing publication authorisation creates one Evidence-based confirmation record for every required channel and makes no external publication call or success claim. |
| TPR09-AC-044 | The MVP contains no active State Portal, Ministry website or other publication adapter; Configuration rejects `Integrated acknowledgement`. |
| TPR09-AC-045 | Each required channel confirmation has one stable identity bound to the original publication's channel set and the exact immutable subject type, identity and digest. |
| TPR09-AC-046 | Only a currently assigned HOPF can confirm channel publication; the AO, technical operator and Procurement Officer cannot attest it. |
| TPR09-AC-047 | Confirmation records the exact required attestation, server-derived HOPF identity/time and actual channel availability time atomically. |
| TPR09-AC-048 | System checks are limited to record completeness, format, authority, identity, file integrity/scan and conflicts; no result claims independent proof of real-world publication. |
| TPR09-AC-049 | Confirmation requires availability time, evidence reference, applicable public URL, required evidence file/digest and HOPF attestation; optional notes are stored only when present and limited to 500 characters. |
| TPR09-AC-050 | Uploaded evidence is scanned, digested and retained; failed or rejected uploads cannot confirm a channel. |
| TPR09-AC-051 | A Tender is not Published while any mandatory channel is Awaiting confirmation or has missing, invalid or rejected confirmation evidence. |
| TPR09-AC-052 | `published_at` is written once as the latest actual availability time among all mandatory channel confirmations. |
| TPR09-AC-053 | On publication confirmation, the minimum preparation period is revalidated from actual `published_at`; an invalid deadline cannot become Published. |
| TPR09-AC-054 | The exact actual invitation date is written once to Planning through its owner contract and replay is idempotent. |
| TPR09-AC-055 | Publication authorisation can be withdrawn only while confirmed unpublished and before any channel confirmation; reason and decision remain auditable. |

### 14.5 Open period, clarifications, addenda, candidate notices and cancellation

| ID | Acceptance criterion |
|---|---|
| TPR09-AC-056 | A Published Tender shows actual publication time, submission deadline, documents, channel evidence, addenda and clarifications in one record. |
| TPR09-AC-057 | `CreateAddendumDraft` is unavailable before publication, after submission close or after cancellation. |
| TPR09-AC-058 | An addendum records an explicit before/after comparison, affected reference, reason and materiality explanation. |
| TPR09-AC-059 | An addendum that expands quantity, value, scope, method, reservation, lotting, package structure, technical requirement or evaluation basis cannot be issued. |
| TPR09-AC-060 | A late non-material addendum calculates and requires the lawful revised submission deadline before submission for issue. |
| TPR09-AC-061 | HOPF issue freezes the addendum and creates Evidence-based confirmation records for every original required channel. |
| TPR09-AC-062 | The addendum becomes Issued only after HOPF confirms all required channels with the same evidence and attestation semantics as the original publication. |
| TPR09-AC-063 | A clarification can originate only from an authenticated Bid Submission event tied to an Active Tender-bound candidate registration; an issued addendum is optional. |
| TPR09-AC-064 | A response that would change published Tender content cannot be sent until an authorised linked addendum is Issued and its successor bidder definition is effective. |
| TPR09-AC-065 | A response that changes no published content may be sent to the asker or all registered candidates as deliberately selected; every broadcast hides the asker and remains fully auditable. |
| TPR09-AC-066 | Only the AO can cancel; cancellation requires an applicable ground and reason and becomes final immediately on commit. |
| TPR09-AC-067 | Cancellation never restores the Requisition, reopens the Tender or creates a replacement procurement automatically. |
| TPR09-AC-068 | Cancellation creates independently tracked notice-publication, candidate-notice and PPRA-report obligations with truthful due/recorded/overdue states. |

### 14.6 Usability, accessibility, audit and boundaries

| ID | Acceptance criterion |
|---|---|
| TPR09-AC-069 | Every artboard in §10 can be implemented using §10.1 plus KT-STD-001 v1.8 §2 without invented fixture data. |
| TPR09-AC-070 | Every visible action in §10 has exactly one behaviour in §11 and is absent when the server does not permit it. |
| TPR09-AC-071 | The default interface exposes no event keys, hashes, enum values, payloads, transport retries or infrastructure configuration. |
| TPR09-AC-072 | A Procurement Officer can start, complete and submit the primary fixture by following the three task labels without separate training on system states. |
| TPR09-AC-073 | HOPF and AO each see one plain-language decision, its consequence and the exact content being decided. |
| TPR09-AC-074 | Status, stage and next action remain distinct; the interface never labels approval, evidence upload or technical validation as confirmed publication. |
| TPR09-AC-075 | All tables and dialogs meet the keyboard, focus, heading, error-linking, text-status and responsive rules in §11.9. |
| TPR09-AC-076 | Every successful decision, publication, addendum, clarification, candidate-notice and cancellation command writes the minimum audit evidence in §12. |
| TPR09-AC-077 | Generated and external evidence remains retrievable by immutable digest under authorised audit access. |
| TPR09-AC-078 | The §13 seed can be rerun without duplication and proves the primary and isolated state fixtures independently. |
| TPR09-AC-079 | Owner-contract failure leaves source data unchanged, records a truthful pending/failure state where applicable and supports safe idempotent recovery. |
| TPR09-AC-080 | Representative Procurement Officer, HOPF and AO usability tests complete their assigned routine tasks without moderator explanation, material error or recourse to internal terminology. |
| TPR09-AC-081 | `StartTender` creates nothing unless the exact bound template release is Available and all release/profile/mapping digests verify. v0.12 (OD5): the release must also be switched On on the site. |
| TPR09-AC-082 | `None`, `Youth`, `Women` and `Persons with disabilities` may pass compatibility only when the exact Available template release supports the category and an applicable verified rule snapshot is bound; every unsupported category or missing rule fails before Tender creation with no bypass. At Draft creation the exact Available template release is the one switched On on the site (v0.12, OD5). |
| TPR09-AC-083 | The published supplier definition is generated from the released response rules and never reconstructed from the PDF. |
| TPR09-AC-084 | Every mandatory technical response retains its individual result and reason while feeding one shared Technical compliance group with no weight. |
| TPR09-AC-085 | Every response has an evaluation and contract destination or an explicit N/A disposition. |
| TPR09-AC-086 | Publication freezes the response, downstream and addendum-identity rule digests with the documents and package digest. |
| TPR09-AC-087 | A mapping or renderer incompatibility blocks publication and cannot be repaired from the Tenders UI. |
| TPR09-AC-088 | An authorised Administrator, System Manager, Procurement Officer or HOPF can follow a failure link to the read-only **STD Templates** detail, while other users see no internal schema or digest surface. |
| TPR09-AC-089 | A County-residents restriction is evaluated independently from the base reservation category and passes only for an applicable county Procuring Entity with a verified rule and supported overlap treatment; supplier address never establishes entitlement. |
| TPR09-AC-090 | A reserved Tender publishes its exact declaration and evidence requirements, evaluates them under `EVG-ELIGIBILITY`, and preserves the category and result for award and statutory reporting without turning eligibility evidence into a contract obligation. |
| TPR09-AC-091 | Publication freezes exactly one `PublishedBidDefinition v1` using every field in §4.5.4; its `template_family`, opaque release identity, renderer compatibility and constituent digests reconcile with the installed STD release. |
| TPR09-AC-092 | `BuildPublishedBidDefinition` and publication are atomic: any unsupported control, missing mapping, hidden obligation, reconciliation error or digest mismatch creates no publication and no partial definition. |
| TPR09-AC-093 | Controlled multi-select and structured ports requirements from `AuthorisedRequisitionHandoff v1.3` appear in both human and structured projections without flattening or re-entry. |
| TPR09-AC-094 | The four exact evaluation groups are Eligibility, Technical compliance, Financial and Award; no fifth group, hidden criterion or weighted technical screen is created. |
| TPR09-AC-095 | One closed fixture round-trip preserves every source and response identity from Requisition through Tender documents, Published Bid Definition, the five BDS tasks and the evaluation/contract mappings. |
| TPR09-AC-096 | Publication-definition identity and digests are recorded on `TenderPublication`; publication never writes a late field into an Approved immutable `TenderVersion`. |
| TPR09-AC-097 | `IssueAddendum` creates no awaiting-confirmation addendum unless the complete successor Published Bid Definition has been deterministically built, reconciled and frozen in the same transaction. |
| TPR09-AC-098 | While any required addendum channel is unconfirmed, BDS continues to receive the prior effective definition and deadline; the frozen successor is not bidder-current. |
| TPR09-AC-099 | The final addendum channel confirmation atomically marks the addendum Issued and activates its exact successor definition and revised deadline; replay cannot activate a second Version. |
| TPR09-AC-100 | Original Tender, addendum and cancellation-notice confirmations have distinct subject identities/digests and uniqueness scopes while reusing the original publication's governed channel set; evidence for one subject can never satisfy another. |

### 14.7 v0.10 public/vendor closure acceptance

| ID | Acceptance criterion |
|---|---|
| TPR10-AC-001 | A registered candidate can submit a general pre-bid question before the clarification deadline without an addendum already existing. |
| TPR10-AC-002 | No Account-only, public or free-text identity can submit a clarification; the exact Active Tender-bound candidate registration is required. |
| TPR10-AC-003 | Receipt at or after the clarification deadline creates no clarification and returns the canonical late message. |
| TPR10-AC-004 | A clarification answer that changes no published content may be direct or general; the selected audience and exact response are immutable and auditable. |
| TPR10-AC-005 | A clarification answer that would change wording, criteria, schedules, dates or supplier obligations remains Awaiting addendum and cannot be sent independently. |
| TPR10-AC-006 | The linked addendum must be Issued and its successor definition effective before the published-change response is sent to all registered candidates. |
| TPR10-AC-007 | Every general clarification broadcast, issued addendum, effective deadline change and cancellation freezes the authoritative Active candidate audience and creates one notice dispatch per candidate. |
| TPR10-AC-008 | Candidate destinations come only from the Bid Submission owner projection; Tenders cannot create or edit supplier contact data. |
| TPR10-AC-009 | Mandatory notices cannot be opted out of; later contact changes affect only future audience snapshots and never rewrite earlier dispatch evidence. |
| TPR10-AC-010 | Queued, Sent, Delivered and Failed remain distinct; a provider acceptance is not displayed as recipient delivery without supporting evidence. |
| TPR10-AC-011 | A failed notice has a safe same-subject retry/follow-up route and never retracts an issued addendum, changes a deadline, reopens cancellation or fabricates receipt. |
| TPR10-AC-012 | Public Tender readers see authoritative clarification answers and notices without the source candidate identity or protected delivery data. |
| TPR10-AC-013 | TPR-DES-09 and TPR-DES-11 render the general-question, published-change and failed-delivery fixtures at desktop and narrow widths with one clear next action. |
| TPR10-AC-014 | The current MVP ends at the Bid Submission boundary. Bid Opening, Evaluation/Award, Supplier Management/prequalification and additional method/product releases are not implied by approval of this document. |

### 14.8 v0.11 installed-release lifecycle acceptance

| ID | Acceptance criterion |
|---|---|
| TPR11-AC-001 | `StartTender` binds only an Available release after compatibility, digest and adapter checks pass. v0.12 (OD5): the release must also be switched On on the site. |
| TPR11-AC-002 | An already-bound unpublished Tender may continue on a Superseded release only while every exact asset, digest and renderer-adapter check passes. |
| TPR11-AC-003 | Supersession never changes `template_release_id`, regenerates content from a successor or silently offers a selector. |
| TPR11-AC-004 | A Withdrawn bound release blocks submit, approve, reopen, publication authorisation, publication confirmation, addendum issue and Bid start for an unpublished Tender. |
| TPR11-AC-005 | The Withdrawn state preserves all work, explains that the current unpublished Tender cannot continue, and offers only the exact role-permitted §10.15 read/navigation control. Any separately governed cancellation, corrected source or new Tender is handled through its own authorised workflow; this state never deletes or automatically rebinds. |
| TPR11-AC-006 | A published Tender retains its exact release, documents, Published Bid Definition and public readability after supersession or withdrawal, with a truthful lifecycle notice. |
| TPR11-AC-007 | `BuildPublishedBidDefinition` invokes the STD-TPL-IMP-001 v1.1 shared compiler and cannot use a separate Tender-specific implementation. |
| TPR11-AC-008 | Procurement Officer and HOPF can inspect the exact bound release and report a concern without gaining template-edit or general technical-read authority. |

### 14.9 v0.12 site-switch acceptance (owner decision OD5)

| ID | Acceptance criterion |
|---|---|
| TPR12-AC-001 | `StartTender` binds a release only when it is `Available` and switched On on the site and its compatibility, digest and renderer-adapter checks pass; when no `Available` release of `IT-EQUIPMENT-OPEN-V1` is switched On, it creates nothing and returns `TND_TEMPLATE_UNAVAILABLE`. |
| TPR12-AC-002 | After the bound release is switched Off on the site, every later action on an already-bound Tender (submit, approve, reopen, publication authorisation, publication confirmation, addendum issue and Bid start) proceeds while every exact asset, digest and renderer-adapter check passes; none fails because of the switch alone. |
| TPR12-AC-003 | Switching the bound release Off, or back On, never changes the Tender's `template_release_id`, digests, documents or Published Bid Definition and never rebinds the Tender to another release. |
| TPR12-AC-004 | An already-bound `Superseded` release continues and a `Withdrawn` release blocks exactly as TPR11-AC-002 and TPR11-AC-004 state; the site switch neither relaxes nor adds to those rules. |
| TPR12-AC-005 | No Tenders test, fixture, seed or message relies on a `Candidate` release state; start tests cover a release that is `Available` and switched On, `Available` and switched Off, `Superseded` and `Withdrawn`. |

### 14.10 v0.12 workflow-guidance acceptance (KT-STD-001 v1.8)

| ID | Acceptance criterion |
|---|---|
| TPR12-AC-006 | Every Tender record read supplies one server-derived `next_step` with kind, headline, stage, holder, recorded since fact where known, all blockers, fixes and permitted primary action. A technical reader never receives a business action. |
| TPR12-AC-007 | Every §5.1 state and visible responsibility passes KT-STD-001 §3B.7 dead-end conformance; a blocked action yields a stable §5.10 reason, concrete figures and a fix route the named holder can use. |
| TPR12-AC-008 | The five formal Tender stages and their markers match §10.17, while Tender details, Supplier/contract requirements and Review/submit remain one Preparation stage with no three-part stepper. |
| TPR12-AC-009 | Every record-screen variant renders the exact §10.17 next step and permitted tracker, replacing the identified duplicate narrative; workspace, focused dialogs and full-page error states render neither tracker nor an invented block. Every §10.15 full-page variant is checked for its exact role-permitted action; `TND_HANDOFF_CONFLICT` never exposes the linked Tender's identity to a viewer without read access. |
| TPR12-AC-010 | §5.11 hand-off items appear and clear on underlying state changes, preserve return comments and distinguish cancellation compliance from a cancelled Tender. |
| TPR12-AC-011 | At 1440 × 1024 the first working region remains in the first view, using the stated one-line reduced tracker if needed; keyboard, 200% zoom and 390 px checks preserve the same facts without a horizontal stepper. |
| TPR12-AC-012 | A material addendum cannot be issued. Its exact hand-off creates one AO cancellation-review item and a waiting item; AO cancellation uses `CancelTender`, while closing the review records a reason and changes no Tender content or status. The same proposal cannot request another review after closure; `DiscardAddendumDraft` archives only the unissued proposal and returns to the unchanged Published Tender. |

## 15. Implementation and verification constraints

### 15.1 Required implementation order

1. Install and verify the exact Available template release, product profile, renderer profile, response rules and downstream mappings. v0.12 (OD5): switch the release On on the site before any new Tender can bind it; neither installation nor the switch waits for a separate release approval.
2. Implement schemas, invariants, authority checks and owner-contract fakes.
3. Implement commands and audit events using test-driven state transitions.
4. Implement deterministic document and Published Bid Definition generation and digest verification.
5. Implement evidence storage, publication-confirmation commands and truthful status derivation.
6. Implement role-safe read projections and task generation.
7. Implement the §10 artboards against the real service contracts.
8. Run representative-user, accessibility, security, resilience and release-gate verification.

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
- security tests for horizontal access, role elevation, protected clarification identity/destination and direct-command forgery.

### 15.3 Publication-confirmation integrity tests

The test harness must prove at least these integrity and concurrency boundaries:

1. authorisation is committed before the HOPF opens the confirmation screen;
2. an identical duplicate confirmation is idempotent;
3. a replay with a different availability time, reference, URL or evidence digest is rejected as a conflict;
4. an evidence upload succeeds but the confirmation transaction fails, leaving no Confirmed state and allowing safe cleanup or reuse of the upload;
5. invalid media or a failed malware scan cannot confirm a channel;
6. evidence or a confirmation record bound to a different subject identity or digest is rejected, including cross-use between the original Tender package, an addendum and a cancellation notice;
7. two concurrent confirmations of the final outstanding channel produce one authoritative result; and
8. replay of internal Tender-published or Planning-owner events is idempotent.

In every case, one authoritative business outcome and a complete immutable confirmation history result.

If the future facility in §5.5.1 is activated, its approved integration contract must add separate adapter, acknowledgement, uncertain-result, recovery and operational tests before release. Those tests are not part of the MVP.

### 15.4 Release gates

Release requires:

- all TPR09 acceptance criteria passing;
- the exact `IT-EQUIPMENT-OPEN-V1` release is Available for new binding; an already-bound release is Available or Superseded as permitted by §5.3; every bound release digest and renderer adapter matches; v0.12 (OD5): for new binding the release is also switched On on the site, and an already-bound Available release may be switched On or Off;
- the response-definition, shared evaluation-group, contract-projection and addendum-identity reconciliation tests pass;
- no unresolved Must fix compatibility or security issue;
- validated owner contracts and migration/seed idempotency;
- exact rendered artboard review under KT-STD-001 v1.8;
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
16. accept a manually invented clarification that bypasses the authenticated Tender-bound candidate boundary;
17. disclose the identity of a clarification source in any general response or candidate notice;
18. send an answer that changes published Tender content without first issuing the linked addendum;
19. treat Sent as Delivered without provider evidence or let notice failure reverse the authoritative Tender action;
20. let failed cancellation notices reopen the Tender or reverse the AO decision;
21. restore a Requisition or create a replacement Tender automatically after cancellation;
22. hide required action or legal consequence inside an unlabeled disclosure;
23. display internal statuses, hashes, event names or technical integration controls to routine business users;
24. restrict comparable-contract count or experience period to an arbitrary preset menu; or
25. claim conformance from screenshots alone without service, audit, integrity and representative-user evidence.
26. automatically rebind a Tender when an STD release is superseded or withdrawn;
27. let an unpublished Tender proceed on a Withdrawn release; or
28. maintain a Tender-specific copy of the Published Bid Definition compiler.
29. bind a new Tender to a release that is not switched On on the site, or block, strand or rebind an already-bound Tender because its release was switched Off (v0.12, OD5).

## 17. Normative references and precedence

| Reference | Governs |
|---|---|
| Public Procurement and Asset Disposal Act, 2015, including §§63, 74, 75, 78, 89 and 96–98 as applicable | Cancellation, tender documents, addenda, submission periods, publication and access obligations. |
| Public Procurement and Asset Disposal Regulations, 2020, including Regulations 33, 48, 49, 56, 57, 85 and 86 as applicable | Procurement-function duties, cancellation, e-procurement publication, addendum inquiries and advertising-channel rules. |
| KenTender LAW-REG-001 | Accepted statutory correction decisions and controls. |
| KT-STD-001 v1.8 | Document structure, static design contract, accessibility and verification. |
| PLN-CHG-001 v1.27 | Approved Plan Item, funding, method, reservation, actual invitation date and owner commands. |
| BUD-CHG-001 v1.11 | Approved funding-control and authorised-value boundary. |
| REQ-CHG-001 v1.12 | Approved `AuthorisedRequisitionHandoff v1.3`, inherited structured requirements and correction route. |
| STD-TPL-001 v0.10 | Exact IT-equipment template boundary, bundle construction, documents, response rules, mappings, profiles, inspection and release lifecycle. |
| STD-TPL-IMP-001 v1.1 | Installed-release registry, shared compiler, renderer adapters, concern capture and lifecycle enforcement. |
| BDS-CHG-001 v0.7 | Supplier runtime, Tender-bound candidate registration, question submission, mandatory-notice contact, supported renderer, response persistence and submission boundary. |
| CFG-CHG-002 v0.16 | Effective rules, schedules and public portal support/legal-link configuration; it does not own installed-template inspection. |
| Project Owner decision OD5, 26 September 2026 (v0.12) | A template release is an On/Off switch on the site, with no release approval or commissioning step. STD-TPL-IMP-001 v1.1 implements the simplified installed-release runtime; OD5 governs Tender binding as specified in §5.3. |
| Platform identity, task, document, records and security contracts | Authentication, assignment, tasks, evidence storage, retention and access control. |

If a lower-level implementation note conflicts with this contract, this contract controls the Tenders behaviour. If this contract conflicts with applicable law, the law controls and the affected rule must be escalated before implementation; the system must not silently improvise a legal interpretation.

## 18. Approval effect

### 18.1 v0.12 approval effect

The Project Owner **approved v0.12 on 26 September 2026**, including the same-day correction recorded in the control table. This version is the Tender implementation baseline. It applies owner decision OD5 and supplies KT-STD-001 v1.8 next-step, journey, guard-reason and hand-off detail for the same Tender lifecycle. A new Tender binds only a release that is Available and switched On on the site; an already-bound release continues as in v0.11 (Available, switched On or Off, or Superseded, while integrity and renderer checks pass; Withdrawn blocks). Switching a release Off never strands or rebinds a started Tender. This approval does not approve an STD bundle; under OD5 there is no release approval or commissioning step for Tenders to wait on. It does not prove that software has been implemented, deployed or accepted in production; the §19.5 observations are evidence, not acceptance. The programme-boundary and implementation-completion statements in §18.2 continue to apply.

### 18.2 v0.11 approval effect (retained)

The v0.11 text was proposed and was not approved; it is superseded by the approved v0.12. The retained scope covers the user-facing Tenders module through its Bid Submission boundary, including general clarifications, candidate notices and the exact bound-release lifecycle. The v0.12 approval does not approve an STD bundle or prove that software has been implemented, deployed, legally re-verified or accepted in production.

Bid Opening, Evaluation and Award, Supplier Management/prequalification, RFQ, Restricted Tendering, Direct Procurement, RFP, Works and other Services are recorded programme work after this MVP slice. Their absence does not leave a hidden action inside Tenders and their future documents must consume the immutable published/closed handoffs defined here rather than revise this Tender retrospectively.

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
| TPR-IMP-012 | Implement compatibility checks at start, submit, approve and publication authorisation, including the supported reservation categories and independent County-residents restriction. | §5.3 | Nine-gate tests at all four boundaries, including missing-rule, unsupported-category and unsupported-overlap rejection. |
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
| TPR-IMP-025 | Implement stable `PublicationChannelConfirmation` identities bound to the exact original-publication channel set and immutable subject identity/digest. | §4.7 | Original/addendum/cancellation binding, idempotent replay and cross-subject conflict tests. |
| TPR-IMP-026 | Implement HOPF confirmation for State Portal and Ministry website using channel-specific reference, public URL, evidence and attestation. | §§4.7, 5.5, 7.3, 10.9 | Authority, URL, evidence, attestation and browser tests. |
| TPR-IMP-027 | Implement HOPF confirmation for notice-board and newspaper channels using channel-specific reference, evidence, attestation and optional 500-character notes. | §§4.7, 5.5, 7.3, 10.9, 11.5 | Upload, scan, digest, reference/notes, attestation and authority tests. |
| TPR-IMP-028 | Implement truthful Awaiting confirmation and Confirmed states, with rejected input remaining unconfirmed. | §§4.7, 5.5 | State-machine, derivation and display tests. |
| TPR-IMP-029 | Implement technical validation for confirmation completeness, authority, identity, evidence integrity/scan and package binding without claiming factual publication. | §§4.7, 5.5, 7.3 | Validation-boundary and false-success tests. |
| TPR-IMP-030 | Implement idempotent identical replay and reject any conflicting second confirmation. | §§5.5, 7.3, 11.5 | Replay, conflict and immutable-history tests. |
| TPR-IMP-031 | Compute one immutable actual publication time from all mandatory channel evidence. | §5.5 | Concurrent-final-confirmation tests. |
| TPR-IMP-032 | Revalidate the minimum preparation period against actual publication time. | §5.5 | Boundary-date tests. |
| TPR-IMP-033 | Write actual invitation date once through the Planning owner contract. | §§3, 5.5 | Owner-contract and replay tests. |
| TPR-IMP-034 | Implement withdrawal of publication authorisation with reason only before any channel is confirmed. | §§5.1, 7.3 | Positive and prohibited-state tests. |
| TPR-IMP-035 | Implement the published-Tender view with documents, evidence, addenda and clarifications. | §10.10 | Role and artboard tests. |
| TPR-IMP-036 | Implement Addendum schema, Draft save, materiality and deadline rules. | §§4.8, 5.6 | Material/non-material/date tests. |
| TPR-IMP-037 | Implement HOPF addendum issue and evidence-based confirmation through every original required channel. | §§5.6, 7.4 | Authority, digest, evidence, attestation and channel tests. |
| TPR-IMP-038 | Implement authenticated general Tender clarification ingestion from an exact Active candidate registration, with optional related addendum and protected source identity. | §§3, 4.9 | General/linked, deadline, access and forgery tests. |
| TPR-IMP-039 | Implement direct/general response classification and enforce the issued-addendum prerequisite whenever an answer would change published content. | §§4.9, 7.4, 11.6 | Direct/broadcast, addendum-required and privacy tests. |
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
| TPR-IMP-050 | Implement the idempotent primary and isolated fixture seeds without outcome conflation; the primary `IT-EQUIPMENT-OPEN-V1` fixture uses Youth, with isolated `None`, Women, Persons-with-disabilities and applicable County-residents paths. | §13 | Two-run seed comparison plus supported, missing-rule, unsupported-category and county-overlap fixture tests. |
| TPR-IMP-051 | Complete every acceptance criterion and automated test minimum. | §§14–15 | Signed test report with zero failed mandatory criteria. |
| TPR-IMP-052 | Complete representative-user tests for Procurement Officer, HOPF and AO routine journeys. | §§14.6, 15.4 | Observed completion evidence and resolved findings. |
| TPR-IMP-053 | Complete publication-confirmation integrity/concurrency exercises and operational runbooks. | §§15.3–15.4 | Integrity report and approved runbooks. |
| TPR-IMP-054 | Verify that every prohibited shortcut is absent from code, configuration and UI. | §16 | Architecture/code review checklist. |
| TPR-IMP-055 | Produce the immutable Bid Submission handoff at submission close. | §§1, 3, 5.1 | Consumer contract and end-to-end handoff test. |
| TPR-IMP-056 | Install and verify the exact Available template release and all document/response/mapping/profile digests. v0.12 (OD5): switch it On on the site before a new Tender can bind it. | §§4.1–4.2, 5.3, 15.4 | Release-registry and digest tests. |
| TPR-IMP-057 | Generate the exact `PublishedBidDefinition v1` from the released response rules rather than the rendered PDF and freeze it atomically with publication authorisation. | §§4.5.1–4.5.4, 7.2–7.3 | Exact-schema, deterministic fixture, atomicity and no-PDF-parser tests. |
| TPR-IMP-058 | Aggregate individual mandatory checks into one shared Technical compliance group while retaining row results and reasons. | §4.5.2 | Mapping and evaluator-projection tests. |
| TPR-IMP-059 | Require an explicit evaluation/contract destination or N/A for every response family. | §§4.5.2–4.5.3 | Completeness and hidden-criterion tests. |
| TPR-IMP-060 | Freeze response, downstream and addendum-identity rule digests at publication. | §§4.1–4.2, 5.4 | Immutable-Version and addendum tests. |
| TPR-IMP-061 | Link template failures to the read-only **STD Templates** owner route for Administrator, System Manager, Procurement Officer and HOPF only. | §§8–9 | Role-safe recovery-link tests. |
| TPR-IMP-062 | Generate category-specific reservation declarations/evidence and map each to `EVG-ELIGIBILITY` from the exact released response rules. | §§4.5, 5.3 | Published-definition, declaration, evidence and no-inferred-entitlement tests. |

### 19.1 v0.10 public/vendor closure implementation

| ID | Required implementation | Contract | Completion evidence |
|---|---|---|---|
| TPR10-IMP-001 | Consume the exact Tender-bound candidate projection created by BDS **Start bid**; do not create a local supplier/candidate registry. | §§3, 4.9–4.9A | Owner-contract, missing/closed candidate and duplicate-event tests. |
| TPR10-IMP-002 | Replace addendum-only inquiry endpoints and storage with `TenderClarification`, retaining an optional issued-addendum link. | §§4.9, 7.4 | Schema migration, general-question and linked-addendum tests. |
| TPR10-IMP-003 | Block receipt at the clarification deadline and block any published-changing response until its linked addendum is Issued and effective. | §§4.9, 5.1, 8, 14.7 | Boundary-time, addendum-state and no-informal-change tests. |
| TPR10-IMP-004 | Freeze one candidate audience and create outbox dispatches for general clarification broadcasts, issued addenda/deadline changes and cancellation. | §§4.9A, 5.6–5.7 | Audience, atomic-outbox, concurrent-registration and replay tests. |
| TPR10-IMP-005 | Record Queued/Sent/Delivered/Failed and append retry evidence without changing the authoritative Tender action or fabricating receipt. | §§4.9A, 7.4, 11.6 | Provider-result, retry, failure and state-independence tests. |
| TPR10-IMP-006 | Revise TPR-DES-09 and TPR-DES-11 for general questions, mandatory addendum escalation and failed-delivery recovery at desktop and narrow sizes. | §§10.10, 10.12 | Complete paired artboards and action-map tests. |
| TPR10-IMP-007 | Consume CFG v0.16 public portal support/legal-link projection for bidder-safe Tenders surfaces; expose no editable portal setting in Tenders. | §§3, 10–11 | Projection, missing-setting gate and public-output tests. |
| TPR10-IMP-008 | Run the closed Requisition→Tender→STD→BDS journey through general clarification, addendum notice, bid preparation and sealed submission handoff; stop before Bid Opening. | §§13–15 | Signed end-to-end report with exact identities and no future-module dependency. |
| TPR-IMP-063 | Preserve the reservation category, County-residents treatment and evaluated result in the governed award/statutory-reporting handoff. | §4.5.3 | Downstream mapping and no-contract-obligation tests. |
| TPR-IMP-064 | Adopt the exact release/renderer identity names and `PublishedBidDefinition v1` field contract shared with STD-TPL v0.10, STD-TPL-IMP v1.0 and BDS v0.7. | §§4.1–4.2, 4.5.4 | Schema and cross-document contract tests. |
| TPR-IMP-065 | Materialise the definition atomically with publication authorisation and reject partial output on any reconciliation or compatibility failure. | §§4.5.4, 7.2–7.3 | Transaction rollback and fault-injection tests. |
| TPR-IMP-066 | Preserve controlled multi-select and structured ports requirement values in documents, bidder rows and downstream lineage. | §§4.3, 4.5.1, 14.6 | Closed-fixture round-trip tests. |
| TPR-IMP-067 | Use exactly four evaluation groups including `EVG-AWARD`; do not create a weighted criterion or duplicate award stage. | §§4.5.2, 14.6 | Group vocabulary and mapping tests. |
| TPR-IMP-068 | Use `/app/std-templates/{release_id}` for authorised release inspection and remove the System setup Tender-format dependency. | §§3, 8–9 | Route, permission and absent-old-route tests. |
| TPR-IMP-069 | Complete the cross-module round-trip from `AuthorisedRequisitionHandoff v1.3` through BDS response/mapping consumption with exact identities and digests. | §§3–5, 14.6 | Coordinated end-to-end fixture test. |
| TPR-IMP-070 | Move publication-definition identity and component digests to `TenderPublication`; prohibit any publication-time mutation of an Approved `TenderVersion`. | §§4.2, 4.5.4, 4.6, 14.6 | Immutable-Version and publication-schema tests. |
| TPR-IMP-071 | Build and freeze the complete successor Published Bid Definition in the `IssueAddendum` transaction before creating channel-confirmation work. | §§4.8, 5.6, 7.4 | Rollback, reconciliation and no-partial-definition tests. |
| TPR-IMP-072 | Keep an awaiting-confirmation addendum's successor definition and revised deadline non-effective for BDS. | §§4.8, 5.6 | Prior-definition continuity and bidder-projection tests. |
| TPR-IMP-073 | Activate the issued addendum, revised deadline and exact successor definition atomically on final required-channel confirmation. | §§5.6, 7.4, 14.6 | Concurrent-final-confirmation and idempotent-activation tests. |
| TPR-IMP-074 | Scope every channel confirmation by subject type, identity, digest and channel so original package, addenda and cancellation notices cannot reuse or overwrite one another's evidence. | §§4.7–4.10, 14.6 | Uniqueness, subject-binding and evidence-isolation tests. |

### 19.2 v0.11 installed-release lifecycle implementation

| ID | Required implementation | Contract | Completion evidence |
|---|---|---|---|
| TPR11-IMP-001 | Require Available only at new Tender binding and persist the exact release/adapter/digest set. v0.12 (OD5): the release must also be switched On on the site. | §§4.1–4.2, 5.3 | Available/Candidate/Superseded/Withdrawn start tests. v0.12 (OD5): `Candidate` no longer exists; the start tests are those in TPR12-IMP-001. |
| TPR11-IMP-002 | Recheck bound lifecycle, integrity and renderer adapter at submit, approve, reopen, publication authorisation, confirmation, addendum issue and Bid start. | §§5.1, 5.3–5.6 | Boundary matrix with typed failures. |
| TPR11-IMP-003 | Permit Superseded continuation only for an already-bound Tender and never rewrite its release identity or content. | §§5.1, 5.8 | Continuation, no-rebind and successor-notice tests. |
| TPR11-IMP-004 | Block every unpublished continuation on Withdrawn while preserving Versions and governed next steps. | §§5.1, 8, 10.15 | State/action/error and preservation tests. |
| TPR11-IMP-005 | Preserve published documents and Published Bid Definition after lifecycle change and display the truthful release notice. | §§5.1, 12 | Historical-read and immutability tests. |
| TPR11-IMP-006 | Replace any Tender-local builder logic with the shared STD-TPL-IMP v1.0 compiler adapter and canonical parity tests. | §§4.5.4, 7.2 | CLI/production golden-vector evidence. |
| TPR11-IMP-007 | Grant Procurement Officer/HOPF the bounded release-inspection and concern path without template mutation or general technical read. | §§6, 8–10 | Permission and negative-capability tests. |

### 19.3 v0.12 site-switch implementation (owner decision OD5)

| ID | Required implementation | Contract | Completion evidence |
|---|---|---|---|
| TPR12-IMP-001 | Bind a new Tender only to the `Available` release of `IT-EQUIPMENT-OPEN-V1` that is switched On on the site, through the STD Templates owner's published binding service; create nothing otherwise. | §§4.1, 5.3, 7.2, 14.9 | Start tests for `Available` switched On, `Available` switched Off, `Superseded` and `Withdrawn`. |
| TPR12-IMP-002 | Leave the site switch out of every later-action recheck on an already-bound Tender; recheck only lifecycle, integrity and renderer adapter as TPR11-IMP-002 requires. | §§4.5.4, 5.1, 5.3–5.4, 5.8 | Switch-Off-after-start boundary matrix across the TPR11-IMP-002 actions. |
| TPR12-IMP-003 | Retire every `Candidate` release case from Tenders tests, fixtures, seeds and messages. | §14.9 | Test and fixture inventory showing no `Candidate` case. |

### 19.4 v0.12 workflow-guidance implementation

| ID | Required implementation | Contract | Completion evidence |
|---|---|---|---|
| TPR12-IMP-004 | Return server-derived next steps, guard reasons and all fixes on record reads; no browser recomputation. | §§5.9–5.10; KT-STD-001 §3B | State/actor/guard matrix and dead-end test. |
| TPR12-IMP-005 | Emit §5.11 hand-off My Work and waiting items and clear them only on the underlying state change. | §§5.1, 5.11 | Submission, return, approval, publication, addendum, correction and cancellation transition tests. |
| TPR12-IMP-006 | Replace the three-part Draft progress row and duplicate status narratives with shared §10.17 components on permitted record archetypes. | §§9–10.17; KT-STD-001 §2.9 | Variant screenshots and keyboard, 200% zoom, 390 px and first-view checks. |
| TPR12-IMP-007 | Implement the bounded material-addendum cancellation-review hand-off, AO close-with-reason outcome and unissued-draft discard route. | §§5.9–5.11, 7.4, 10.11–10.17, 11.6–11.7 | Idempotent request, waiting/clearing, no repeat after closure, AO decision, draft discard and unchanged-Tender negative tests. |

### 19.5 v0.12 as-built observations (evidence, not requirements)

These rows record what the Tenders and STD Templates code on branch `mvp1/dev` does, read from source on 26 September 2026 (commit 8e5ca5c9 plus uncommitted working-tree changes). They are observations, not rules. Where the build differs from or goes beyond this document, this document controls until the Project Owner decides otherwise.

| Observation | Section that already describes it | Observed build behaviour | Treatment |
|---|---|---|---|
| **View STD Template** on the Start screen | §8 `TND_TEMPLATE_UNAVAILABLE`; §10.15 Template unavailable variants | When no release can be bound, the Start screen shows **Tender format unavailable** and offers **View STD Template** only to a user whom STD Templates lets read (Administrator, System Manager, Procurement Officer or HOPF); other users get no link. | The inspection-link eligibility matches §§8 and 10.15. The §10.15 **Back to Tenders** navigation for a non-inspection reader is a design requirement, not an assertion that the observed build already shows it. |
| Release notice on an unpublished Tender record | §5.1 bound-release rows; §10.15 bound-release rows | A Tender whose bound release is `Superseded`, `Withdrawn` or failed verification shows the §10.15 heading and message, with **View STD Template** for STD Templates readers. | Matches §10.15. |
| Release notice on a published Tender record | §5.1 row for a release that becomes Superseded or Withdrawn after publication | A published Tender whose release is `Superseded` or `Withdrawn` shows an information notice whose wording this document does not state. | Build wording, not adopted here. |
| Release notice for a switched-Off bound release | §5.1 switched-Off row (v0.12) | A Tender whose bound release is switched Off shows no notice. | Build choice, not adopted here. |
| `TND_TEMPLATE_*` errors | §8 | `TND_TEMPLATE_UNAVAILABLE`, `TND_TEMPLATE_RELEASE_WITHDRAWN` and `TND_TEMPLATE_RELEASE_INTEGRITY_FAILED` return the **View STD Template** route only for STD Templates readers. A missing or unhealthy renderer adapter is reported as `TND_TEMPLATE_RELEASE_INTEGRITY_FAILED`. | Matches §8. |
