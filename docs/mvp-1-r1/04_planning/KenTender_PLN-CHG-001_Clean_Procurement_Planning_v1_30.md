# PLN-CHG-001 — Clean Procurement Planning

**Status of this version — approved by the Project Owner on 9 October 2026.** The Project Owner stated: “1, Approved” (control table). Version 1.30 supersedes PLN-CHG-001 v1.29, approved on 3 October 2026, which is retained unchanged as historical evidence; PLN-CHG-001 v1.31, also approved on 9 October 2026, supersedes this version. (Proposed wording read: “Version 1.30 is **Proposed**. PLN-CHG-001 v1.29, approved on 3 October 2026, remains the approved document until the Project Owner approves this version.”) The controlling-approval paragraphs below record the approval of v1.29 and are retained as history. This version adds the receiving side of NDS-CHG-001 v1.17 (proposed): a Need-origin departmental plan entry starts from the accepted Need's estimated total cost, and Planning shows any change from it. Every other rule of v1.29 is retained.

**Controlling approval — 3 October 2026.** The Project Owner instructed: “Mark the documents as approved”. This approves this version in the coordinated OVS v0.6 package, including its incorporated amendments. OVS-P01–P05 are approved. The incorporated REQ v1.13, CFG v0.17 and TPR v0.16 changes are accepted within their approved successors; this does not create separate retrospective approvals of those intermediate versions. Earlier proposed/pending wording is drafting history superseded by this record. Static design work and conformance matrices remain open; CM and the separate template walkthrough remain deferred. Approval does not establish implementation, seed execution, testing, legal clearance or production readiness.

**OVS reference and owner-specific amendment (§§6, 7.1, 7.7, 9.3, 11.1).** Apply OVS v0.6 §4.1 to submitted/approved Plan reading and scoped downstream source progress. Preserve the accepted v1.28 departmental-plan position rules, Finance/governance actions, existing snapshots and historical evidence. Do not expose another department’s protected evidence or add a second work queue. Existing owner exports remain governed by their original permission.

Shared usability rules are owned once by **OVS-CHG-001 v0.6**, especially §§3–8 and 12–15. This module retains its domain lifecycle, facts, commands and existing authority except the explicit proposed read additions above. Implement the named changes in the cited owner surfaces; do not copy shared usability chapters into this document. This amendment takes effect under the controlling approval above.

| Control | Value |
|---|---|
| Version | 1.30 |
| v1.29 version (retained) | 1.29 |
| Date | 9 October 2026 |
| v1.29 date (retained) | 3 October 2026 |
| Status | Approved — 9 October 2026 |
| v1.29 status (retained) | Approved — 3 October 2026 |
| Approved on | 9 October 2026 |
| v1.29 approved on (retained) | 3 October 2026 |
| Approval record | Project Owner: “1, Approved” — 9 October 2026, answering the question put to the owner: approve NDS-CHG-001 v1.17, PLN-CHG-001 v1.30 and PLN-CHG-001 v1.31, in that order. |
| v1.29 approval record (retained) | Project Owner: “Mark the documents as approved” — 3 October 2026 |
| Supersession | v1.30 supersedes v1.29, approved 3 October 2026, which is retained as historical evidence. (v1.30 row read: On approval only: supersedes v1.29.) v1.31 supersedes v1.30. |
| v1.29 supersession (retained) | Supersedes v1.27, approved 25 September 2026, which is retained as historical evidence. v1.27 superseded v1.26, approved 25 September 2026, which is retained as historical evidence. v1.26 superseded v1.25, approved 23 September 2026. v1.25 superseded v1.24 and all earlier Planning implementation specifications in full. |
| Decision authority | Project Owner approval of the corrected 30% denominator, calculation fixtures and dependent contracts; attached `thirty_percent_reservation_rule.pdf`; official Act and Regulations provisions recorded in approved LAW-REG-001 v1.2 |
| UX basis | Planning Usability Blueprint v0.2, approved 13 September 2026; supersedes conflicting v1.18/PLN-UX-001 presentation. Prior proof of concept is historical evidence of a limited walkthrough only |
| Change scope | Domain change on the Project Owner decisions of 9 October 2026 (NDS-CHG-001 v1.17 §1.2): a Need-origin departmental plan entry starts from the accepted Need's estimated total cost, and Planning shows the change from it. Adds the entry reference and the prefill and change rules (§4.3), the `DepartmentalNeedAccepted.v3` consumer (§7.3), the funding-panel, certification and Procurement-review presentation (§§10.4, 10.5), the action-map row (§11.9), the isolated profile (§13.3), acceptance (§14.14), the owner dependency (§15.2), ledger and change rows (§§17.1, 17.4) and the proposed approval effect (§18.0A). The Need's estimate is never summed into any total. All v1.29 content is retained. |
| v1.28 change scope (retained under v1.29) | Workflow-guidance correction, on the Project Owner decision of 26 September 2026 ("Visible") about a Need accepted after its department's departmental plan was accepted, and the Project Owner instruction of 28 September 2026 to harmonize the accepted departmental plan page. Adds the §5.1.2 position rule, a §5.7 departmental-plan row and tracker rule, the outbound position contract to Departmental Needs (§7.3), a hand-off row (§7.7), U01 and U02–U05 variants and the heading rule for a plan nobody can edit (§§10.1A.2, 10.3, 10.4), action-map rows (§11.9), a negative fixture (§13.4), acceptance (§14.13), an owner dependency (§15.2), ledger and change rows (§§17.1, 17.4) and the v1.28 approval effect (§18.0). All v1.27 content is retained. |
| v1.27 change scope (retained) | Reconciliation and handoff version, on the Project Owner instruction of 25 September 2026 to reconcile the document disagreements flagged in the v1.26 review and implement every recommendation before handoff. Decides D2: an over-budget line and a missing procurement method block **Request plan funding confirmation**; a reservation shortfall blocks **Sign and submit Annual Plan** only (§5.3.1, §5.5.3.1, §5.6 item 4). Corrects the conflicting U01 and U07 wording and the U07 BASE schedule fixture (§§10.3, 10.6). Adds the state-by-responsibility next-step table (§5.7), the budget revision request record, command, errors and hand-off register (§§4.7, 7.2, 7.3, 7.7, 8), the UI-only UPDATE-OVER-BUDGET fixture (§10.2, §13.3), negative fixtures (§13.4), action-map rows (§11.9), acceptance (§14.12) and owner dependencies (§§15.2, 17.2). Also reconciles owner-document version citations to the document's approval record (note after the §1.2 table). All v1.26 content is retained; superseded sentences are kept beside their corrections. |
| v1.26 change scope (retained) | Targeted presentation update required by KT-STD-001 v1.8 §12.1 and requested for Claude Design: adds §10.1A (shared next-step and journey content) and a **Next step and journey** paragraph to each screen section in §§10.3–10.17, extends the §10.18 inventory and gate, and records the v1.26 approval effect in §18 with matching entries in §1.2 and §17.1. No field, state, responsibility, authority rule, command, service, event, error code or approval stage is added or changed. Items that would need a change outside §10 are listed in §10.1A.8 and are not made by this version. All v1.25 content is retained. |
| v1.25 change scope (retained) | Full approved v1.24 contract plus one material correction: the approved Budget remains a funding ceiling, while the 30% Planning target uses the verified AGPO-eligible value of the current complete APP. Every amendment recalculates the target; actual achievement remains downstream. No user task, approval stage or candidate-entitlement decision is added. |
| Evidence boundary | Requirements consolidation only. No production schema, repository, legal source verification or release certification is asserted. |
| Implementation status | Not implemented by this document. External owner amendments and verification gates remain in §15 and §17. |
| Reading rule | §§1–16 and §18 are the current requirements. §17 records provenance, dependencies and replacement mappings; earlier wording quoted there is historical, not an alternative implementation option. |

This approved successor retains the complete approved v1.24 business, authority, audit, classification-correction, forecast-deferral, simplicity and Stage 2 presentation contract. It corrects the reservation denominator that wrongly treated unused Budget headroom as procurement the entity was compelled to plan. PLN-REF-001 and PLN-UX-001 remain provenance records; implementers need not combine their operative wording with earlier Planning versions or the usability blueprint.

Proposed successor v1.28 closes a dead end found live on 26 September 2026: a Need accepted after its department's plan was accepted was pending input to a later update (§5.1.2), correctly, but every screen treated the plan as finished. v1.28 makes it the department's turn on the plan, the Planning workspace, My Work and the Need's own page. It also aligns the accepted plan page's tracker and heading with that turn. All v1.27 requirements are retained.

Approved successor v1.27 reconciles the v1.25 disagreement over which checks block a funding request, and adds the Planning-side runtime contract that the v1.26 screens depend on: the next-step table, the budget revision request hand-off and its fixture, action map and acceptance. Approved successor v1.26 adds only the next-step and journey content that KT-STD-001 v1.8 requires for Claude Design (§10.1A and the per-screen paragraphs in §§10.3–10.17). It retains every v1.25 requirement unchanged.

## 1. Governing decision and disposition register

### 1.1 Current governing decision

Procurement Planning produces one consolidated Annual Procurement Plan per Fiscal Year from accepted departmental submissions. Departmental Needs is an optional consultation channel. A departmental submission may contain current accepted Needs, direct departmental requirements, or both. Every accepted Need within the submission's defined coverage must be accounted for either as proceeding or as not proceeding with a recorded departmental reason.

The Head of User Department certifies the departmental submission. The Procurement Planner validates it, classifies proceeding requirements, and consolidates the resulting eligible sources into Plan Items. The first accepted departmental submission creates the initial Draft Annual Plan automatically. Consolidation can proceed incrementally; no all-department completion gate or mandatory nil declaration is introduced.

Finance confirms the consolidated Plan's per-Budget-Line affordability. This confirmation creates no reservation and is separate from Plan approval. The Plan is formally submitted with preparation accountability, countersigned through Accounting Officer adoption, and approved through exactly one configured statutory route. Publication transmits the exact approved content after the Treasury-submission evidence gate. Authoritative acknowledgement plus successful activation checks activates the Version; a published Version that fails those checks is explicitly held under §5.5.2.

An Active Version remains the governing Planning baseline until an acknowledged successor replaces it. A correction never reopens submitted content. Requisitions owns its authorisation and invokes Planning drawdown and Budget reservation commands. Budget owns reservation records, balances and transactional financial controls. Tender Preparation owns template binding and tender-document preparation; Tender Publication owns the tender's publication action. No Planning command creates a Requisition, Tender shell, STD binding, wizard configuration or Tender workflow.

The preparation-signature decision in §6 is a deliberate refinement of who performs the existing final submission action. It must not be implemented as an assumed equivalence between Procurement Planner and Head of Procurement Function.

### 1.2 Source basis and approval interpretation

The product owner approved the refinement register and subsequently approved the Planning Usability Blueprint v0.2, including supporting-detail readability and every actor journey. This successor incorporates those decisions and the approved KT-STD-001 v1.7 task-led presentation standard. The earlier proof of concept did not establish ordinary-user usability; no complete artboard rendering, representative-user validation or implementation is claimed. Detailed schema representations and cross-module payloads below make the approved rules implementable; coordinated owner amendments must adopt their matching sides before integration release.

Statutory propositions retain their supplied provenance, reconciled by approved LAW-REG-001 v1.1 and now governed by approved LAW-REG-001 v1.2. This consolidation performs no new legal research and does not promote unresolved interpretations or illustrative constants to verified production law. Required legal source/layout verification remains an explicit dependency.

| Source | Version used | Specific use / status |
|---|---|---|
| Procurement Planning | PLN-CHG-001 v1.18 | Complete predecessor; original domain, governance, fixture and 72 refinements carried forward |
| Approved usability design | Planning Usability Blueprint v0.2 | UX-01–20, readable supporting detail, all actor journeys; approved 13 September 2026 |
| Document standards | KT-STD-001 v1.7, approved | Current shared task-led design, technical-read, implementation and release standard; this module supplies its exact screen content and information priority |
| Document standards, workflow guidance | KT-STD-001 v1.8, approved 25 September 2026 | Supersedes v1.7. Adds the next-step block and journey tracker (§2.9), their restraint rules (§2.9.3), brief item 12 (§2.6.8) and the runtime next-step contract (§3B). Governs §10.1A and the per-screen next-step paragraphs of v1.26 |
| Workflow Guidance Standard | Approved 25 September 2026 | Source input to KT-STD-001 v1.8; worked example on this module's plan update. Its descriptions of the live build are observations, not Planning rules |
| Responsibilities | AUTH-ADR-001 v1.7 | Current scoped responsibility, acting authority and separation of duties |
| Budget & Funding | BUD-CHG-001 v1.10, approved (v1.26 read: BUD-CHG-001 v1.9, consolidated approved requirements) | Exact Money, whole-plan affordability, approved funding ceiling and Budget ownership; no Planning reservation and no AGPO planning denominator supplied from unused Budget headroom |
| Departmental Needs | NDS-CHG-001 v1.14, approved (v1.26 read: NDS-CHG-001 v1.13, consolidated approved requirements) | Source revisions, Quantity, distinct accepted disposition/Active usage and unchanged acceptance wire keys |
| Departmental Needs, estimated total cost | NDS-CHG-001 v1.17, proposed | Source of the Need-origin entry's starting amount and of the accepted estimate shown beside any change. Its proposed status is unchanged; this document neither approves nor rewrites it. |
| Strategy Alignment | STR-CHG-001 v1.8, consolidated approved requirements | Objective eligibility and approval snapshot; approval/implementation not inferred from its presence |
| Statutory register | LAW-REG-001 v1.2, approved (v1.26 read: proposed) | Denominator interpretation, official-source evidence and distinct planning/actual measures; production legal verification remains separate |
| Configuration | CFG-CHG-002 v0.13, approved (v1.26 read: proposed) | Five-tab System setup, exact responsibility/reference ownership, precise reservation-measure definitions, native UOM adapter and source verification evidence |
| 30% denominator review | `thirty_percent_reservation_rule.pdf`, 23 September 2026 | Approved Budget is a ceiling; Planning denominator is the verified eligible value of the current complete APP; actual achievement is a separate downstream measure |
| Requisitions | REQ-CHG-001 v1.7 baseline; v1.8 proposed | Retain agreed owner boundary; proposed v1.8 follow-up/consumption contracts are dependencies, not silently approved by Planning |
| Tender Preparation | TPR-CHG-001 v0.7 | Existing handoff consumer boundary; matching downstream successor/implementation still required |
| Tender Publication | TPUB-CHG-001 v0.3 internally | Tender publication caller and invitation-event ownership; uploaded filename says v0.1 |
| Integrated fixture | SEED-001 v1.3, approved | Shared actors, exact chronology, BASE/READY distinction, source quantities and dates |

**Owner-version reconciliation — v1.27.** Earlier versions of this document cited owner documents inconsistently: this table listed BUD v1.9 as approved, NDS v1.13, and LAW v1.2 and CFG v0.13 as proposed, while the control table, §17.2, §17.4 and the v1.25 approval effect (§18.3) state that LAW-REG-001 v1.2, CFG-CHG-002 v0.13 and BUD-CHG-001 v1.10 are approved, and §§4.1, 7.6 and 13.3 cite NDS v1.14 as approved. The current references are therefore **LAW-REG-001 v1.2, CFG-CHG-002 v0.13, BUD-CHG-001 v1.10, NDS-CHG-001 v1.14 and STR-CHG-001 v1.8, all approved**. Where a current rule in §§1–16 cites an earlier owner version, it is read as the current one; each such citation carries the reconciliation note. Citations in §17.3 and §17.4 remain historical provenance. This reconciliation follows the document's own approval record; it is not a fresh inspection of the owner documents, and any section number cited from an earlier owner version (for example CFG v0.11 §10) is confirmed against the current owner version when that document is next supplied.

**v1.28 note.** NDS-CHG-001 v1.15 is proposed alongside this version. It carries the receiving side of the §7.3 position contract and the Need page's own next step. Until it is approved, NDS-CHG-001 v1.14 remains the approved Departmental Needs reference. NDS-CHG-001 v1.15 was approved on 28 September 2026, the same day as this version, and is the current Departmental Needs reference.

### 1.3 Baseline section disposition

| Historical v1.17 material | Carry-forward disposition in this successor |
|---|---|
| §§1–3 cumulative history, purpose and ownership | Current rules in §§1–3; obsolete instructions removed; history preserved through §17 mappings |
| §4 model | Replaced by typed storage, projection and evidence contracts in §4 |
| §5 lifecycle/invariants | Replaced by §5; separate funding state, correction cohort, scope lock and publication recovery |
| §6 roles | §6; HOPF signs the existing final submission, four statutory capacities, correction-chain segregation |
| §§7–8 integrations/commands | §7; exact command inventory and coordinated producer/consumer contracts |
| §9 errors | §8; no Planning reservation-release error; profile-specific timing and explicit scope/correction/publication failures |
| §§10–12 UI/design/interaction | §§9–11; all 21 screen families and complete closed fixture pack incorporated |
| §13 audit | §12; immutable snapshots, append-only corrections and operational evidence |
| §14 seeds | §13 and §10.2; two items, three sources, KES 130m and corrected authority chronology |
| §15 acceptance, including duplicate AC-100 | §14 and §17.3; every old occurrence maps to a unique successor criterion |
| §§16–17 implementation/prohibitions | §§15–16; no copied obsolete reservation, optional-route or generic-period instructions |
| §§18–20 precedence/conformance/approval effect | §§17–18; actual source statuses and explicit external prerequisites |

The full decision-by-decision table is §17.4: 116 retained rows plus 7 Stage 2 presentation rows. Verification columns describe required work, not completed tests.

## 2. Purpose, outcomes and scope exclusions

Provide governed departmental requirements, incremental annual consolidation, source-backed procurement packages, affordability evidence, complete review, statutory approval, exact approved publication and controlled procurement eligibility. Departmental Needs is optional. Direct requirements are equally valid; no synthetic Need or bypass justification is created.

The MVP is single-year. It excludes asset disposal, STD/template binding, tender creation, technical specifications, supplier/candidate evaluation, Budget reservations, contract commitment, manual actual entry, planner-managed milestone forecasting and procurement-scope expansion through an APP amendment. Planning supplies only its own facts to reporting; award, supplier, delivery and payment facts belong to operational owners. Procurement progress is shown only where an owning module supplies authoritative evidence. Forecast cascades, reminders and unsupported completion tracking are future facilities under §15.3.

Every field below must serve its named consumer. Storage necessity does not imply routine display. Derived totals and statuses are never editable substitutes for authoritative records. No optional field, action, role or workflow may be added because a prototype happens to show it. Configuration belongs in the existing System setup surface and has no additional approval workflow.

The ordinary product must remain usable without knowledge of internal record types, resolver states, rule versions, source-verification mechanics or event history. The following presentation hierarchy is mandatory:

1. **Current task:** show what this actor must understand or decide now, the material issue and one primary action.
2. **Conditional supporting detail:** show only when applicable, when it changes the decision, or when the user deliberately opens it.
3. **Audit and configuration evidence:** retain for history, authorised inspection and System setup; never present it as ordinary planner input.

## 3. Ownership and dependency boundary

| Concern | Authority | Planning's permitted responsibility |
|---|---|---|
| Site identity, Fiscal Years, department tree, units and configured approval route | Configuration & Governance | Read exact configured values; never create alternative catalogues or user FY grants |
| Assignment and organisational scope | Shared AUTH resolver | Apply the same role-bound authority to reads, commands, tasks, counts, files and exports |
| Need facts and accepted revision | Departmental Needs | Consume the exact revision and six facts; account for it in the DPP without changing it |
| Need estimated total cost (v1.30) | Departmental Needs | Read the accepted revision's estimate to start a Need-origin entry's indicative amount and to show the change from it; never write it and never use it in any total |
| DPP funding specification and direct requirements | Planning | Capture and govern through departmental certification and validation |
| Decision not to proceed with an accepted Need in this FY | Planning | Retain the reason and certified disposition; expose it separately from Active Plan usage |
| Requirement classification and package formation | Planning | Classify proceeding entries and form compatible source-backed items |
| Budget Line identity, eligibility, approved amount and available funds | Budget & Funding | Read through the Budget service; use approved amount for affordability and available funds as a separate advisory |
| Finance task and confirmation evidence | Planning | Maintain one current plan-level review, immutable decisions and current-evidence evaluation |
| Funding reservation and its release | Budget, invoked by Requisition's governed authorisation or reversal | Never create, release or revalidate a reservation from Planning |
| Strategy selection and snapshot source | Strategy Alignment | Select exactly one eligible Objective; retain the returned approval-time immutable lineage |
| Plan adoption, statutory approval and publication evidence | Planning | Govern the exact immutable Version and preserve the authority used for each action |
| Requisition drawdown | Requisitions initiates; Planning owns the authoritative Plan allowance consumed | Accept authorised atomic drawdown/reversal calls; expose current balances without creating the Requisition |
| Tender preparation and template configuration | Tender Preparation | Consume no STD configuration in Planning; expose approved upstream lineage only |
| Milestone actual events | Module recording the real event | Receive authenticated, versioned events; never accept a Planning user's typed actual date |
| Statutory returns involving awards, supplier categories or payments | Reporting and the respective operational owners | Supply Planning facts and lineage; do not claim the Plan already stores all downstream facts |

The Budget Line eligibility call still requires the source Organisation Unit. The predecessor’s blanket prohibition on an Organisation Unit argument to any Budget contract must be corrected. Record eligibility is distinct from a user-permission dimension.

## 4. Canonical domain model

### 4.1 Shared types, storage classes and validation

The field tables are normative. Each field inherits the common rules here as well as its row. `A` means authoritative storage, `S` immutable evidence snapshot and `P` recalculated/read-only projection. A row listing several keys applies the same declared type/requiredness to each key unless it explicitly says otherwise. Server-generated means no business-user input. Framework audit fields are reused.

| Type/convention | Exact contract |
|---|---|
| ID | Opaque server-generated identifier or exact owner-supplied identifier; never parsed to infer authority or another record. A business reference, stable ID, exact Version ID and concurrency token are distinct. |
| Link mapping | A logical `x_id` maps one-to-one to the Frappe Link/Data field `x`; an object’s own ID maps to `name`. No compatibility alias is introduced. |
| Money | Exact decimal currency-unit value, never binary float or minor units under a shilling value. APIs use decimal strings. Currency precision comes from the Budget currency contract; KES uses two decimals in the fixture. Reject excess precision rather than rounding. Storage must retain at least 18 integral digits and the currency’s supported fractional digits. Missing/unsupported precision blocks the affected monetary write. |
| Quantity | Exact positive decimal string with governed UOM precision. Need quantities are copied exactly, never rounded or partially allocated. Direct quantities obey the same UOM rule. Use approved BUD v1.10/NDS v1.14 and CFG v0.13 precision/provider contracts (v1.26 read: BUD v1.9/NDS v1.14 and CFG v0.11); matching REQ adoption and integration evidence remain required. |
| Dates/instants | Business dates are ISO dates interpreted in site timezone; instants are UTC in services/audit and shown in Africa/Nairobi for the fixture. |
| Version token | Non-negative monotonic integer `record_version` on mutable aggregates/tasks; commands require the expected token. Display sequence numbers are never tokens. |
| Text | Trimmed nonblank text where required. Item title 5–160 characters, package description 10–1,000. Disposition and aggregation reasons 20–500. Other reasons identify an actionable issue and are capped at 1,000; no invented optional note. |
| Evidence | Exact owner record/version or protected attachment reference and content hash where files are frozen. Store identity, actor/capacity, timestamps and provenance; do not treat a filename as evidence that a file exists. |
| Historical rule | Draft fields freeze at certification/submission. Decisions, events and published files are append-only. A correction creates a successor/link, never an in-place historical edit. |
| Common command result | Exact aggregate/task ID, resulting record token, lifecycle/funding states, created evidence IDs and permitted next actions. Failure changes nothing. |

### 4.2 Intake and departmental roots

| Record/field | Class/type | Required/source | Editability/history | Consumer and validation |
|---|---|---|---|---|
| Fiscal Year `kentender_dpp_submission_open` | A/boolean | CFG | CFG maintenance only | Initial intake; at most one FY open for DPP intake |
| Fiscal Year `kentender_dpp_submission_closes_at` | A/instant | Optional CFG value | CFG maintenance/audit | Command-time close check even before scheduler; may precede the FY it governs |
| DPP `dpp_id`, `dpp_reference` | A/ID, reference | Server | Immutable | Root/route; reference pattern DPP-{site code}-{OU code}-{FY start}-{sequence} |
| DPP `fiscal_year`, `org_unit_id` | A/owner IDs | Required CFG | Immutable | Unique FY + OU; FY is record data, OU supplies departmental scope |
| DPP `current_version_id` | A/ID | Current candidate where present | Guarded pointer | Draft/submitted/correction navigation; does not replace accepted pointer |
| DPP `current_accepted_version_id` | A/ID | Nullable until accepted | Guarded pointer | Effective accepted submission and governed updates |
| DPP `current_state` | P/label | Derived | Never edited | Accepted plus candidate shown as Accepted — update in progress |
| DPP `record_version` | A/token | Server | Every aggregate mutation | Concurrent create/update guard |

There is no DPPSubmissionWindow record, lifecycle, opens-at field or approval. Initial reads create nothing.

### 4.3 DPP versions, entries and certified evidence

| Record/field | Class/type | Required/source | Editability/history | Consumer and validation |
|---|---|---|---|---|
| DPPVersion `dpp_version_id`, `dpp_id`, `version_number` | A/IDs, positive sequence | Server | Immutable identity | Display **Submission**; unique sequence within root |
| DPPVersion `based_on_version_id` | A/ID | Accepted predecessor for update | Set on copy | Preserves accepted baseline |
| DPPVersion `correction_of_dpp_version_id` | A/ID | Returned origin for correction | Set on copy | Fixed stable source cohort; incompatible-action history |
| DPPVersion `version_status` | A/enum | Server | Governed transitions | Draft, Submitted, Returned, Accepted, Superseded, Withdrawn; only Draft editable |
| DPPVersion `submission_id`, `record_version` | A/ID, token | Server; snapshot ID null before certification | Guarded | Exact certification and concurrency |
| DPPEntry `dpp_entry_id`, `dpp_version_id` | A/IDs | Server | New exact entry on copy | Exact certified source reference |
| DPPEntry `source_origin` | A/enum | Required at creation | Immutable | Accepted Departmental Need or Direct departmental requirement |
| DPPEntry `direct_source_id` | A/ID | Server; direct origin only | Generated once, carried through copies | Stable direct requirement identity; never derived from the new entry ID |
| DPPEntry `need_id`, `need_revision_id` | S/IDs | Need origin only, NDS | Exact read-only lineage | Current accepted revision under the cohort rule; existing event wire keys unchanged |
| DPPEntry `source_line_id` | P/tagged identity | Need ID or direct_source_id | Never entered | Stable identity paired with source_origin; no duplicate authoritative key |
| DPPEntry `title`, `description`, `expected_operational_result` | A or S/text | Required | Read-only NDS snapshot; departmental Draft edit for direct origin | Three of six source facts; direct title/description limits as above; outcome 10–1,000 characters |
| DPPEntry `quantity`, `unit_id`, `required_by_date` | A or S/Quantity, UOM ID, date | Required | Read-only NDS snapshot; direct Draft edit | Other three source facts; required-by inside FY; selectable UOM through CFG adapter |
| DPPEntry `budget_line_id`, `indicative_amount` | A/BUD ID, Money | Proceeding entry only | Departmental Draft edit | Eligible line for OU/FY, positive full estimate including incidentals; clear operative values when not proceeding |
| DPPEntry `currency` | P/currency code | Budget service | Never entered | Calculation/display; exact currency retained in certified evidence |
| DPPEntry `need_estimated_total_cost` | S/Money, nullable | Need origin only; the accepted revision's `estimated_total_cost` (NDS-CHG-001 v1.17 §4.3) | Read-only; follows the entry's exact accepted revision; frozen in the submitted snapshot at certification | Starting value and change reference. Never entered and never summed into any total. Null where the accepted revision has no estimate and for every direct entry |
| DPPEntry `not_proceeding_reason` | A/text | Need origin only when excluded | Draft set/restore; frozen at certification | 20–500 characters; presence derives non-proceeding disposition; no second editable status |
| DPPSubmission `dpp_submission_id`, `dpp_version_id`, `submission_number` | S/IDs, sequence | Server | Immutable | Number equals certified DPPVersion number |
| DPPSubmission `submitted_entry_snapshots`, `source_cohort` | S/ordered entry schema, tagged stable IDs | Certification | Immutable | Full facts, funding, dispositions and exact lineage; cohort is the certified set |
| DPPSubmission `attestation_text`, `submitted_by_user_id`, `authority_snapshot`, `submitted_at` | S/text, ID, AUTH evidence, instant | Certification | Immutable | HoD accountability; assignment/capacity/effective interval actually exercised |

Direct requirements have exactly the six source facts plus Budget Line and indicative amount; they have no Need link, bypass reason or generic attachment field. Need funding/disposition edits never edit NDS facts. Corrections update the exact accepted revision only within the stable cohort.

**Estimate prefill and change — v1.30.** These rules apply to a Need-origin entry. Direct entries are unaffected.

1. When Planning creates the entry, or refreshes it to the current accepted revision, it reads the revision's estimated total cost from the accepted payload (§7.3). If the entry has no operative `indicative_amount` and the revision has an estimate, the estimate becomes the entry's `indicative_amount`. Budget Line is never prefilled.
2. If the entry already has an operative `indicative_amount`, Planning never replaces it, including after a successor revision with a different estimate is accepted. The reference `need_estimated_total_cost` moves to the new revision's estimate.
3. The preparer may revise a prefilled amount like any other amount under this section. The amount the Head of User Department certifies is the operative `indicative_amount`.
4. Where `need_estimated_total_cost` is present and differs from `indicative_amount`, Planning shows beside the entry the accepted requirement's estimate and the change, which is the planning amount minus the accepted estimate, signed, in the Budget currency. The change requires no reason and creates no task, approval or return.
5. Certification freezes `need_estimated_total_cost` in `submitted_entry_snapshots` with the entry, so Procurement review and later evidence show the figure that applied at certification.
6. Excluding an entry (§5.1.4) clears the operative amount as before and leaves the reference. Restoring it starts again from rule 1: the amount starts from the accepted revision's estimate and never from the cleared planning amount.
7. DPP totals, the cost entered so far, Plan Item values, allocations, affordability checks and the 30% denominator use only operative `indicative_amount` values. The Need's estimate is never summed into any of them.
8. A prefilled amount is validated under the precision of the selected Budget Line's currency (`PLN_MONEY_PRECISION_INVALID`). Excess precision is never rounded.

A Need accepted before NDS-CHG-001 v1.17 has no estimate: nothing is prefilled, no change is shown, and the preparer enters the amount as in v1.29.

Initial/update certification uses the exact rendered text in §10.4. It names the department and financial year and certifies the full included and excluded requirements, quantities, required dates, funding and exclusion reasons. Correction certification additionally identifies the earlier submitted plan and its permitted requirements. Text and those exact identities are frozen with the decision; the user need not manage the underlying revision records. Unrelated new requirements are expressly outside the correction.

### 4.4 Departmental validation

`DPPValidationTask` stores generated task ID, exact submission ID, Open/Completed/Cancelled state and record token. FY/OU are resolved from the submitted record, not duplicated as authority. `DPPValidationDecision` stores decision ID, task/submission ID, Accept or Return, actor, exact AUTH assignment snapshot and decision instant. Acceptance contains one `{dpp_entry_id, requirement_type_id, procurement_category}` row per **proceeding** entry. Category is Goods, Works or Services; the finer type comes from the governed catalogue. New returns contain one or more `{dpp_entry_id, correction_required}` issues; `dpp_entry_id` is null for the whole submission. `correction_required` is the single required nonblank actionable comment, at most 1,000 characters, labelled **What needs to change?**. No second problem/issue input is required. Existing historical `{problem, correction_required}` values remain intact and are displayed separately when both contain distinct information; never discard or rewrite either. A legacy live API/storage adapter must be inspected and migrated explicitly before removing its duplicate-field requirement; do not guess an empty required field or duplicate the text into both fields. New versioned requests reject the obsolete duplicate input. This is a coordinated return-payload amendment, not a rename of existing frozen decisions. Decision rows are immutable. There is no claim, priority, score or generic note.

The Planner selects only `requirement_type_id` from the effective governed requirement-type catalogue. The system derives `procurement_category` from that catalogue entry and displays the category immediately beside the selector. A client cannot submit a category independently. Acceptance freezes both the selected type and derived category so downstream history remains reproducible.

An accepted classification is never edited in place. If the Planner later discovers that the classification—not a departmental source fact—is wrong, Planning records an immutable `DPPClassificationCorrection`:

| Field | Rule |
|---|---|
| `classification_correction_id` | Server-generated immutable identity. |
| `dpp_submission_id`, `dpp_entry_id` | Exact accepted certified submission and proceeding entry; excluded entries cannot be corrected. |
| `supersedes_classification_evidence_id` | Exact original acceptance row or latest effective correction. |
| `previous_requirement_type_id`, `previous_procurement_category` | Frozen prior effective classification. |
| `new_requirement_type_id`, `new_procurement_category` | Planner selects the governed type; server derives category. New values must differ from the prior classification. |
| `reason` | Required specific correction reason, 20–500 characters. |
| `corrected_by`, `authority_snapshot`, `corrected_at` | Exact Planner, exercised AUTH evidence and trusted instant. |

The effective classification projection uses the latest valid correction for new Planning work, but never rewrites an accepted decision, allocation, submitted Plan or Active Plan. If the source is unallocated, it becomes available with the corrected classification. If it is allocated only to a mutable Draft item, that item becomes **Source correction required** and must be dissolved and re-formed; no field is changed silently. If it is present in a submitted, approved or Active Plan, the current Version remains exact and operative while the Planner uses the applicable Plan correction or successor route to incorporate the corrected classification through full governance. Departmental recertification is not required unless a departmental fact is also wrong.

### 4.5 Annual roots and exact versions

| Record/field | Class/type | Required/source | Editability/history | Consumer and validation |
|---|---|---|---|---|
| AnnualProcurementPlan `plan_id`, `plan_reference`, `fiscal_year` | A/IDs, reference | Server/CFG | Immutable | One root per FY; PLN-{site code}-{FY start}-{sequence} |
| AnnualProcurementPlan `title` | P/text | Site name and FY | System display; snapshot at submission | {entity name} Annual Procurement Plan {FY period}; no PE selector/link field |
| AnnualProcurementPlan `active_version_id` | A/ID | Nullable | Activation transaction only | Sole governing baseline, never highest sequence |
| AnnualProcurementPlan `open_candidate_version_id` | A/ID | Nullable | Governed creation/transition | Initial or successor/correction candidate; one open chain only |
| AnnualProcurementPlan `record_version` | A/token | Server | Guarded | First-acceptance and activation races |
| PlanVersion `plan_version_id`, `plan_id`, `version_number` | A/IDs, sequence | Server | Immutable identity | Exact reviewed/publication version |
| PlanVersion `based_on_version_id` | A/ID | Actual Active predecessor where present | Copy/creation only | Activation compare-and-swap and cumulative allowance |
| PlanVersion `correction_of_plan_version_id` | A/ID | Returned, withdrawn or published-held origin where applicable | Copy only | Exact correction origin; not a fictional Active predecessor |
| PlanVersion `source_cohort` | S/tagged stable IDs | Formal submission/correction origin | Frozen | Corrections can substitute current revisions, not unrelated sources |
| PlanVersion `version_status` | A/enum | §5.2 | Governed only | Includes Withdrawn for correction and Published — activation held |
| PlanVersion `change_reason` | A/text | Ordinary successor required; correction inherits issue context | Planner Draft only | Explains substantive update; 20–1,000 characters |
| PlanVersion `project_name` | A/text | Optional, at most 160 characters | Planner Draft only; frozen | Whole-Plan project name in review/publication; blank for mixed portfolio |
| PlanVersion `preparation_signature_id`, `submitted_snapshot_id` | S/IDs | Formal HOPF submission | Immutable | Exact complete content signed and submitted |
| PlanVersion `record_version` | A/token | Server | Guarded | Every Draft/transition command |

### 4.6 Stable Plan Item, item version and allocations

`PlanItem` is the stable identity record (`plan_item_id`, generated reference, plan_id). `PlanItemVersion` is the exact content row with its own `plan_item_version_id`, `plan_item_id`, `plan_version_id` and record token; unique (plan_item_id, plan_version_id). The following fields belong to that exact content row. A copy retains stable identity, creates a new item-version ID and never creates an additional operative allowance.

| Field | Class/type | Required/source | Editability/history | Consumer and validation |
|---|---|---|---|---|
| `title`, `description` | A/text | Required | Planner Draft only | Package scope; 5–160 and 10–1,000 characters; scope-lock guard applies |
| `strategic_objective_id`, `reviewed_strategy_version_id`, `reviewed_strategy_path` | A + S/ID, ID, ordered lineage | Required before Finance request | Draft selection from STR; frozen | Exactly one eligible objective; full reviewed path; final approval snapshot must match |
| `strategy_approval_snapshot_id` | S/ID | Final approval only | STR-created immutable evidence | Review/publication/downstream exact lineage; deterministic retry |
| `procurement_category`, `requirement_type_id` | P/classification | Effective accepted classification evidence for all proceeding entries | Never manually overridden or rewritten; a correction supplies new source evidence for re-formation/succession | All combined sources compatible; Goods/Works/Services and governed finer type |
| `procurement_method_id` | A/CFG ID | Required | Planner Draft selection | Eleven-method catalogue; operational support requires complete verified profiles |
| `method_profile_version_id`, `schedule_profile_version_id` | S/CFG version IDs | Required for submission | Resolver selects; freezes at submission | Applicable-date basis, categories, conditions, counting and limits; no fallback |
| `method_condition_evidence` | A then S/list | Per selected profile | Planner Draft only | Rows contain condition ID, known fact/declaration, required evidence reference and specific authorization reference when due; no generic bypass |
| `plan_horizon` | P/fixed literal | Single year | No editable selector | Output only; reject unsupported multi-year payloads |
| `aggregation_indicator` | A/enum | Required | Planner Draft only | Not aggregated, Aggregated into this package, Common-user item arrangement |
| `aggregation_reason` | A/text | More than one source | Planner Draft only | 20–500 characters; absent for single source |
| `lotting_indicator`, `lot_count` | A/enum, integer | Indicator required; count for Packaged into lots | Planner Draft only | Single lot or Packaged into lots; positive count; no lot specification here |
| `reservation_category` | A/CFG ID | Required; explicit None allowed | Planner Draft only | Planned designation, not candidate entitlement |
| `county_resident_reservation` | A/boolean | Applicable county entity only | Planner Draft only | Separate verified county obligation calculation |
| `mandatory_restriction_results` | S/condition result list | Rule resolver | Never entered as an override | Known facts and applicable rule versions; no highest-advantage ranking |
| `estimate_basis` | A/text | Required before submission | Planner Draft only | 20–1,000 characters identifying market-survey basis and included incidental costs |
| `estimate_basis_reference` | A/evidence reference | Required before submission | Planner Draft only | Identifiable market-survey document/working-paper reference; text reference does not imply an attached file |
| `baseline_invitation_date` | A/date | Required for applicable profile | Planner Draft anchor; freezes at submission | Starts schedule calculation |
| `period_inputs` | A/list of profile period IDs and integer counts | Applicable periods required | Planner Draft only | Tendering, evaluation, approval buffer, notification buffer and standstill where applicable; counting rules/limits from profile |
| `estimated_delivery_period_days` | A/non-negative integer | Required | Planner Draft only | Calendar days; zero explicit; signing plus estimate must meet source boundary |
| `baseline_milestones`, `estimated_completion_date` | P then S/date map/date | Schedule calculation | Recompute Draft; freeze inputs/result at submission | Applicable ordered milestones; final boundary is earliest source required-by, not a Requisition value |
| `item_state` | A/enum | Server | Governed | Draft, Dissolved, Active, Removed in successor, Superseded; execution is separate |
| `quantity`, `unit_id`, `planned_value`, `funding_breakdown` | P/exact totals | Allocations | Never editable | No sum of unlike UOMs; positive value from full source estimates |
| `scope_lock`, `authorisation_hold`, `execution_information` | P/evidence-based | REQ and correction records | Never manually cleared | Permanent first-authorization lock; separate temporary unresolved-request hold; per-proceeding facts |

`PlanSourceAllocation` stores immutable generated allocation ID, exact item-version ID, stable item ID, exact accepted DPP entry/submission IDs, exact effective classification evidence ID with its type/category snapshot, source origin, stable source key, Need/revision IDs where applicable, full quantity/UOM, Budget Line, Money amount/currency and allocation state. Values are copied from accepted evidence, not user overrides. States are Draft, Active, Released, Removed in successor, Superseded. The allocation ID is exposed to REQ as `plan_item_line_id`. At most one effective allocation per stable source per admitted open Plan Version; Released is historical and may be re-formed. Accepted non-proceeding sources have no allocation. Ordinary copies preserve cumulative consumed capacity through stable identities. A later classification correction never rewrites the stored snapshot.

### 4.7 Financial and governance evidence

| Record | Required typed fields and owner | Consumers, immutability and invariants |
|---|---|---|
| FinancialBasis | Generated ID; FY ID; currency/precision; sorted lines of Budget root/version/line/revision IDs, approved Money amount, planned Money amount, funding identity and eligibility result; digest | BUD supplies authoritative statement; PLN freezes comparison evidence; digest is technical, never user input |
| FinanceTask | ID, exact Plan Version ID, basis ID, Open/Completed/Cancelled enum, token | At most one **Open** per Version; replacement attempts retain history; whole-plan review |
| FinanceDecision | ID, task/basis IDs, Confirm/Return, actor/AUTH evidence, instant, required return reason | Immutable; creates no reservation, commitment or ledger event |
| FinanceBasisReuse | ID, current Plan Version ID, earlier decision ID, matching basis ID, validation instant | Explicit reuse link; does not claim Finance reviewed changed non-financial content |
| FundingEvidence | Projection of Not requested/Awaiting confirmation/Confirmed/Returned/Stale | Derive current basis validity; approval-time evidence remains separate |
| PreparationSignature | ID, exact submitted snapshot ID, HOPF actor/AUTH assignment/capacity, instant | Existing final submission accountability; no approval stage |
| PlanGovernanceTask | ID, exact Plan Version/snapshot IDs, AO or statutory stage, required configured capacity snapshot, Open/Completed/Cancelled, token | Task grants no authority; no generic stored scope as a substitute for AUTH |
| PlanDecision | ID, task/snapshot IDs, action, actor/AUTH/capacity, instant, reason on return; nullable affected_item_version_id for targeted return, validated against reviewed Plan; collective resolution reference for Board/Council decisions | Immutable; incompatible-action chain survives copies; no optional note field |
| LateActivationExplanation | ID, initial Plan Version ID, reason, actor/AUTH evidence, recorded instant, optional superseded explanation ID | AO-owned append-only record; at late adoption or later separate action; never rewrites publication/activation time |
| BudgetRevisionRequest (v1.27) | Generated ID; exact Draft Plan Version ID; Budget Line ID and revision; approved Money amount and planned Money amount at request time; over amount; requesting Planner actor/AUTH evidence; requested instant; BUD request reference returned by the owner; status Open / Revised / Declined / Withdrawn; outcome instant | Consumed by the §5.7 next-step answer, U07 and U01 (waiting line and since) and the §7.7 hand-off register. Created only by `RequestBudgetRevision`. At most one **Open** per Plan Version and Budget Line. Status changes only from the BUD outcome event or Planner withdrawal when the line already fits; history is immutable. Creates no Budget record, reservation or ledger event in Planning; the Budget revision itself is BUD-owned |

### 4.8 Downstream use, correction and operational evidence

| Record | Required typed fields | Validation / consumers |
|---|---|---|
| AuthorisedDrawdown | ID; REQ ID/exact Version ID; stable item and exact Plan/item-version IDs; list of allocation IDs and positive Quantity/Money drawdowns; actor/service correlation and instant | Inbound REQ only; cumulative source/item allowance; atomic with REQ authorization and BUD reservation; immutable |
| DrawdownReversal | ID; original drawdown ID; exact reversible line amounts/quantities; REQ reversal evidence and instant | Inbound REQ only; cannot exceed unreversed original use; never deletes first-authorization scope evidence |
| PlanItemCorrectionRequest | ID; requesting REQ/Version IDs; stable item/exact approved Plan Version IDs; reason; requester/authority; received instant; producer event/key; Open/In progress/Resolved/Closed without change; token | Record plus hold atomic; Planner dispositions; Resolve requires actual Active correction and replacement lineage; no-change requires reason |
| CorrectionDisposition | ID; request ID; action; actor/authority/instant; reason or Active corrected Version and exact replacement allocation mapping | Append-only; releases derived hold only after every request terminal; no stopped-REQ restart |
| ProceedingCoverage | Owner-supplied proceeding ID/type; authorized REQ/Version IDs; exact Plan/item/allocation IDs; covered quantity/value and current authorization/publication/reversal evidence | Read-only operational projection; never inferred from stable item link alone |
| MilestoneActualEvent | Producer + event ID; schema version; proceeding/REQ/Plan/item/allocation IDs; milestone; actual date; recorded instant; producer sequence; optional superseded event ID; source evidence reference | Authenticated owner only; duplicate ID no-op; correction same proceeding/milestone; preserves both facts; invitation path available, other six integrations future |

`ForecastRevision`, forecast-comparison and `MilestoneNotice` schemas are future-facility concepts under §15.3, not required MVP records. A greenfield reimplementation does not create them. Existing tested code may remain dormant, but it must have no exposed route/API, scheduled-job registration, notification producer or other runtime entry point.

### 4.9 Publication and external evidence

| Record | Required typed fields | Validation / consumer |
|---|---|---|
| ApprovedPlanSnapshot | ID; exact Plan Version; complete governed content; source/strategy/Finance/rule/decision evidence index; content digest | Immutable final approval output; exact web/PDF/JSON render source |
| PlanPublication | Stable publication ID; snapshot/Version ID; configured destination reference; schema version; manifest of filename/media type/hash/size; frozen file references | One logical publication per approved snapshot/destination; repeated attempts do not invent a new package |
| PublicationIntent | ID; publication ID; durable dispatch state; created instant; hold/recovery correlation | Commit with approval; external send only after commit and valid Treasury evidence/no hold |
| PublicationAttempt | ID; publication ID; attempt sequence; Pending/Acknowledged/Failed/Indeterminate; attempted instant; external reference; response evidence | Append-only attempts; indeterminate is not confirmed unpublished |
| PublicationAcknowledgement | Adapter event ID; publication/snapshot IDs; manifest/package hash; destination; public location; external reference; acknowledged instant | Authenticated exact-package correlation; duplicate event idempotent; mismatch cannot activate |
| TreasurySubmissionEvidence | ID; approved Version/document hash; submission instant; channel; destination; dispatch reference; supporting attachment; exact-document confirmation; recorded actor/AUTH/instant; superseded record ID and correction reason where applicable | AO only; immutable append/supersede; current invalid evidence holds transmission; own evidence per successor |
| PublicationHold/WithdrawalEvidence | IDs; exact Version/publication; reason; detected/requested actor or service/instant; authoritative reconciliation outcome; AO request and statutory decision references | Hold is not withdrawal; withdrawal only confirmed-unpublished with no outstanding attempt; preserve history |

The canonical public JSON is `KenTenderAnnualPlan.v1`: metadata (schemaVersion, publicationId, planId, planVersionId, versionNumber, fiscalYear, entity public name, approvedAt, publication character), header (title, optional projectName), items (stable/exact IDs and all applicable §4.6 governed fields), sources (approved exact source/allocation/funding facts), totals (currency and per-line/plan amounts), and approved governance/rule/Strategy evidence references suitable for public disclosure. Every Money/Quantity is a decimal string; dates ISO; IDs opaque; inapplicable values null with applicability stated. No ocid, disposal block or operational-event overwrite. Internal assignment IDs, confidential attachments and financial availability statements are not automatically public: the publication adapter contract must explicitly map each public field to the prescribed format and its lawful disclosure policy. The protected review pack includes the complete internal governed content/evidence index for the authorized reviewer. Web/PDF/JSON consistency is tested against one snapshot; exact external adapter serialization and verified Schedule column mapping remain release prerequisites in §15.

### 4.10 Uniqueness and concurrency

Enforce root uniqueness in storage, one open candidate chain per root, one open Finance review per Plan Version, exact entry membership and allocation uniqueness, event uniqueness by producer/event ID, and immutable decision replay. REQ enforces one open Requisition per stable Plan Item. Authorization, scope-lock checks, correction holds, drawdown/reversal and activation serialize on the same stable-item guard. A copied candidate creates proposed content only. No read, retry or second worker creates a second spendable allowance.

## 5. Lifecycle and business rules

### 5.1 Departmental submissions

#### 5.1.1 Content status and displayed status

Retain the DPP root, numbered DPPVersion and certified DPPSubmission concepts. Display the DPP counter as **Submission**. Display a Need counter as **Revision** and an Annual Plan counter as **Version**.

Only a DPPVersion with content status `Draft` is editable. `Returned` denotes the preserved reviewed version and the root's correction presentation, not an editable status on that reviewed record. The editable correction is a new numbered Draft. A returned initial submission and a returned update must both follow this rule.

The root exposes the latest accepted submission and, separately, the current open Draft or submitted candidate. If an accepted submission has an open candidate, show **Accepted — update in progress**, with both submission numbers available. Do not replace the fact of acceptance with **Not submitted — window closed**.

#### 5.1.2 Submission coverage and cut-off

The following agreed rules reconcile complete current-Need coverage with immutable correction membership:

| Operation | Requirements that must be accounted for |
|---|---|
| First submission of an initial DPP Draft | Every current accepted Need in the exact department and FY at command time, plus all direct entries retained in the Draft |
| Submission of a new update copied from an accepted DPP | The carried departmental requirements and every current accepted Need in the exact department and FY at command time |
| Resubmission after Procurement return | The stable source requirements in the returned certified submission; consume their current accepted revisions, preserve explicit exclusions and remove an upstream-withdrawn source from proceeding work with immutable withdrawal lineage |
| A different Need accepted while a submission is under review | Pending input to a subsequent DPP update; it does not rewrite or indefinitely invalidate the submission already being reviewed |

The coverage boundary is established by the submitted source set and certification transaction, not by a browser timestamp. A correction may replace an old revision of a covered Need with its current accepted revision. It may not use the correction route to introduce unrelated requirements after the initial window closes.

**v1.28 — the pending input is not silent.** The row *A different Need accepted while a submission is under review* and the update route of §5.1.3 leave a Need accepted after its department's plan outside every plan until the department creates an update. From v1.28 Planning states that position to the department and to Departmental Needs. For each current accepted Need of the department and Fiscal Year, Planning derives one position:

| Department's plan | Position |
|---|---|
| No departmental plan, or a Draft that will take the Need in (initial or update Draft) | No update needed |
| Draft correction whose fixed source cohort excludes the Need | After current submission |
| Submitted, not carrying the Need's current accepted revision | After current submission |
| Accepted with no open candidate, not carrying the current accepted revision | Update required (with the earlier revision it carries, if any) |
| Accepted and carrying the current accepted revision, or an initial plan withdrawn before acceptance | No update needed |

Planning publishes the positions to Departmental Needs (§7.3) after every departmental-plan command (Start, Submit, Withdraw, Return, Accept, Create update) and after every Need acceptance. A Need in *Update required* makes the plan's next step the department's turn (§5.7).

#### 5.1.3 Window rules

The existing Fiscal Year flag and close instant remain the only initial intake control. A root with no accepted predecessor requires an open window for initial submission, including reopening a withdrawn initial Draft. Existing Draft work remains readable and saveable after closure; closure does not delete it.

A copied correction of a submission validly made while the window was open may be resubmitted after closure, within the fixed coverage rule above.

**Agreed clarification:** once a department has an accepted DPP, it may prepare a governed update for changed requirements, including newly accepted Needs and new direct requirements. Eligibility is based on the accepted predecessor and update lifecycle, not on a requirement that the change originate from a Need event. The current source-change-only wording leaves direct requirements without a coherent mid-year update route. Updates remain subject to HoD certification and Procurement validation; they do not bypass Annual Plan succession.

#### 5.1.4 Not proceeding

| Rule | Exact agreed behaviour |
|---|---|
| Who records the outcome | Departmental Author or Head of User Department with authority over the Draft DPP's department |
| Allowed source | Need-origin entry only; an unsubmitted direct entry may instead be removed |
| User action | **Exclude from this year’s departmental plan** |
| Required input | **Reason for excluding this requirement**, 20–500 characters |
| Funding effect | Clear the current Draft's Budget Line and amount from operative funding specification; preserve earlier certified values in their immutable submissions |
| Source effect | Preserve the accepted Need identity, revision, all six facts and full quantity in the DPP snapshot |
| Readiness effect | The entry satisfies Need coverage, requires no funding or procurement classification, and is excluded from consolidation and monetary totals |
| Reversal before certification | **Include in this year’s departmental plan**; remove the current Draft disposition, require fresh funding completion and retain the change in audit history |
| Certification | The HoD certifies both proceeding and non-proceeding entries in the same DPP; no extra approval stage |
| Procurement acceptance | Accept the complete submission, including its exclusions; only proceeding entries become consolidation sources |
| Entire submission not proceeding | Permitted where at least one current accepted Need is accounted for; it is not an empty submission or a mandatory nil declaration |
| Empty Annual Plan | Acceptance can create the initial Draft with zero proceeding sources. Submission readiness requires at least one proceeding Plan Item; an empty Draft is not advertised as an approved Plan. |

Define a Planning-owned command `SetNeedPlanningDisposition` for the two Draft actions, with entry identity, expected version and idempotency key. The not-proceeding branch additionally requires the reason. Submitted or accepted dispositions can change only through a new DPP submission.

NDS v1.14's `NeedPlanningUsageChanged.v1` means Active Plan inclusion only. It must retain that meaning. The agreed `NeedPlanningDispositionChanged.v1` event records the separately accepted DPP disposition and its source revision, submission, reason, actor, decision time and ordering identity. Departmental Needs displays it as Planning information without changing Need lifecycle or the existing `Fully included`/`Not included` usage projection. This is a coordinated NDS contract addition, not an undisclosed extension of the existing event.

Draft exclusions do not publish an accepted disposition. An accepted exclusion does not remove an existing Active Plan dependency; that dependency changes only when the relevant Plan successor activates.

#### 5.1.5 DPP transitions

| Current condition | Action | Actor | Result and evidence |
|---|---|---|---|
| No DPP; permitted initial intake | Start departmental plan | Author or HoD | One root and Draft Submission 1; no creation from a read |
| Draft | Edit direct requirement, funding or Need disposition | Author or HoD | Draft changes only; source facts stay protected |
| Draft; initial coverage and window pass | Submit departmental plan | HoD | Immutable certified snapshot; one open validation task |
| Submitted; proceeding sources current | Accept departmental plan | Procurement Planner | Immutable classifications and decision; accepted DPP pointer advances; proceeding entries become available to Planning |
| Submitted; correction needed | Return to department | Procurement Planner | Reviewed snapshot preserved; new Draft correction created with structured issues |
| Correction Draft | Resubmit | HoD | New certification within the returned source cohort; no late unrelated additions |
| Accepted; no open candidate | Create update | Author or HoD | One new Draft copied from accepted content; accepted submission remains effective |
| Update Draft | Submit update | HoD | Same departmental governance; Annual Plan baseline unchanged |
| Mutable candidate | Withdraw departmental submission | HoD | Candidate withdrawn; previous accepted submission remains effective |
| Initial candidate withdrawn; no accepted predecessor; window open | Start departmental plan | Author or HoD | Same root; next numbered Draft; no revival of withdrawn evidence |

The same person may prepare and certify a DPP when holding both responsibilities. That person cannot accept or return the same certified submission as Procurement Planner.

#### 5.1.6 Accepted-classification correction

1. Before acceptance, the Planner may change the Requirement type selector freely within the governed catalogue; Category updates automatically from the selected type.
2. After acceptance, **Correct classification** is a new Planning-owned correction action, not an edit of the accepted decision and not a departmental return.
3. The action is permitted only for an accepted proceeding entry, an active Procurement Planner assignment, a current governed catalogue value and a genuinely changed classification with a specific reason.
4. The command rechecks the accepted submission, current correction head, authority, catalogue mapping and all affected allocations under one transaction. Concurrent or stale correction attempts fail without partial change.
5. The correction emits immutable evidence and a new effective classification projection. It never changes the certified title, description, expected result, quantity, unit, required-by date, Budget Line or amount.
6. An unallocated source needs no package repair. A source in a mutable Draft item marks that item **Source correction required**; the existing dissolve-and-re-form controls remain the only way to change the package classification.
7. A source in a Plan under governance, approved or Active does not mutate that Version. Where no procurement scope lock exists, the correction identifies the affected item and routes the Planner to the applicable returned correction or ordinary successor. The current Active Version stays in force until a fully governed replacement activates.
8. If the affected item already has a Requisition authorisation or later procurement scope lock, the correction is retained but cannot reclassify, dissolve, duplicate or replace that item through Planning. Show the exact Requisition/Tender evidence, place new authorisation for the affected item on hold and require the owning downstream correction/cancellation procedure. A Plan successor alone cannot change the issued procurement.
9. Method, schedule, reservation, restriction, Strategy applicability and readiness are recalculated on an eligible re-formed item. Prior calculations and decisions remain exact historical evidence.
10. If a source fact is wrong, the Planner must use the owning Departmental Needs or departmental-plan correction route instead. **Correct classification** cannot conceal or replace a source correction.
11. A correction cannot be used to combine incompatible sources, escape a scope lock, reset allowance, alter an issued Tender or imply that a later requirement is covered by an earlier procurement.

### 5.2 Annual Plan and funding state dimensions

#### 5.2.1 PlanVersion lifecycle

Use the reconciled PlanVersion statuses below, including the agreed publication-recovery outcomes. Do not introduce `Confirmed` or `Awaiting Finance` as additional Plan approval states.

| Plan status | Content editability | Meaning |
|---|---|---|
| Draft | Planner-owned fields editable under command guards | Consolidation or correction in progress; may have any funding-evidence state |
| Awaiting Accounting Officer | Locked | Formally submitted exact Plan content; awaiting adoption |
| Awaiting statutory approval | Locked | AO has adopted; awaiting the configured authority |
| Returned | Locked | Historical reviewed Version; correction is a different Draft |
| Approved — publication pending | Locked | Statutory approval recorded; activation not yet complete |
| Publication failed | Locked | Approval retained; retry/reconciliation required |
| Withdrawn for correction | Locked | Confirmed-unpublished approved Version withdrawn by its statutory authority after AO request; copied Draft correction preserves all prior evidence |
| Published — activation held | Locked | Exact publication confirmed, but activation checks failed; provides no new Requisition authority and permits one governed correction successor |
| Active | Baseline locked | Current governing baseline; append-only owner-supplied operational evidence may appear separately |
| Superseded | Historical baseline and operational evidence preserved | Replaced by an acknowledged successor |
| Cancelled | Locked historical candidate | Open draft/update chain abandoned without changing the Active predecessor |

`Indeterminate` belongs to publication-attempt state. The screen must distinguish an uncertain external result from a confirmed failed attempt even if both are held outside Active status. **Approved — awaiting Treasury submission evidence** is a pending reason within Approved — publication pending. A publication hold is a recorded control over transmission, not an unrecorded withdrawal of approval. A Published — activation held Version retains its historical evidence when a correcting successor becomes Active and records the explicit replacement link; it must never be described as having been Active.

#### 5.2.2 Funding-evidence state

| Funding state | Derivation | Available next action |
|---|---|---|
| Not requested | No confirmation basis or current review | Request plan funding confirmation when pre-Finance readiness passes |
| Awaiting confirmation | One open review for the current financial basis | Finance confirms or returns; Planner may continue permitted Draft work |
| Confirmed | An affirmative decision matches the applicable financial basis | Formal Plan submission, subject to the remaining gates |
| Returned | Latest review was returned and no replacement request is current | Correct Draft and request again |
| Stale | Existing affirmative evidence no longer matches the applicable financial basis | Request fresh confirmation in Draft, return a submitted Version for correction, or use the Active reassessment path below |

The UI may show **Awaiting Finance** as a work-status label while `PlanVersion.version_status` remains `Draft`. It must not imply Plan approval or baseline locking.

#### 5.2.3 Annual Plan transitions

| Current condition | Action | Actor | Required result |
|---|---|---|---|
| First DPP accepted; no Annual Plan | Project proceeding entries | System | Create/reuse one Annual Plan and initial Draft atomically with acceptance |
| Draft | Form, edit or dissolve Plan Items | Procurement Planner | Update eligible source allocations and readiness; Budget unchanged |
| Draft; pre-Finance readiness passes | Request plan funding confirmation | Procurement Planner | One current plan-level review against an immutable financial basis |
| Draft; review open | Confirm plan funding | Finance Confirmation Officer | Record immutable confirmation; Plan remains Draft |
| Draft; review open | Return to planner | Finance Confirmation Officer | Record actionable reason; Plan remains Draft |
| Draft; current confirmation and all submission gates pass | Sign and submit Annual Plan | Head of Procurement Function under §6 | Lock exact Plan, record preparation signature and create AO task |
| Awaiting Accounting Officer | Adopt and submit | Accounting Officer | Record adoption of the exact Version; create one statutory task |
| Awaiting Accounting Officer | Return for correction | Accounting Officer | Preserve reviewed Version; create next Draft correction |
| Awaiting statutory approval | Approve Annual Procurement Plan | Configured statutory authority | Record approval and Strategy snapshot; enqueue publication of exact approved content |
| Awaiting statutory approval | Return for correction | Configured statutory authority | Preserve adopted Version; create next Draft correction; subsequent submission restarts at AO |
| Approved — publication pending; Treasury evidence missing | Record Treasury submission | Accounting Officer | Append evidence for the exact approved Version; release this prerequisite only if valid |
| Approved — publication pending; prerequisites met and no hold | Transmit and reconcile acknowledgement | System | Record authoritative publication evidence; activate only if activation checks also pass |
| Publication failed or indeterminate | Retry exact approved payload / reconcile | System; System Manager technical retry | No payload edit and no new procurement decision |
| Material defect found before publication completes | Hold publication | System on detected invalidity; authorised AO correction request | Hold new transmission, preserve outstanding-attempt state and reconcile any in-flight attempt |
| Confirmed unpublished; no outstanding transmission | Request withdrawal for correction | Accounting Officer | Record reason and request to the configured statutory approving authority; content stays locked |
| Confirmed unpublished; valid AO request | Withdraw for correction | Configured statutory approving authority | Preserve approved evidence as Withdrawn for correction and create one copied Draft; repeat full governance |
| Published — activation held; no open correction candidate | Prepare a corrected plan | Procurement Planner | One linked Draft correction; held Version cannot authorise Requisitions; full governance applies |
| Active; no open candidate | Prepare plan update | Procurement Planner | Copy to one Draft successor; predecessor remains operational |
| Draft successor or correction of that successor | Cancel update | Procurement Planner | Cancel the open candidate chain; predecessor unchanged; no reservation release |
| Successor publication acknowledged; all activation checks pass | Activate successor | System | Atomically change Active pointer, preserve balances and history, apply approved removals and publish eligibility/usage changes |

The approved Head of Procurement Function decision replaces the current Planner's final submission action; it does not add a second final submission, professional-review approval or separate approval state. The required preparation signature must be represented in the consolidated requirements and corresponding role-to-action contract.

### 5.3 Financial basis and confirmation

#### 5.3.1 Basis and verdicts

The financial basis comprises Fiscal Year, each operative Procurement Budget Line, currency, total planned against that line and the approved amount against which the comparison is made. Capture the Budget version/revision references needed to reproduce the comparison. Exact fingerprint serialization belongs in the service contract; no fingerprint is an editable business field.

| Comparison | Effect |
|---|---|
| Planned total exceeds approved amount | Blocking for affirmative Finance confirmation and formal Plan submission. **From v1.27 also blocking for Request plan funding confirmation** (pre-Finance readiness, §5.6 item 4) |
| Planned total exceeds currently available amount but is within approved amount | Advisory only; no Finance failure and no reservation |
| Referenced line no longer eligible or currency/source funding identity changed | Current eligibility/basis must be re-evaluated; do not reuse a confirmation by comparing totals alone |

Pre-Finance readiness excludes the test **funding already confirmed**. Otherwise `RequestPlanFundingConfirmation` would depend on its own result. Formal submission adds that test to the remaining readiness requirements.

**v1.27 decision (D2).** Pre-Finance readiness includes the live per-line comparison of planned total against approved amount, using the non-mutating `check_plan_affordability` read (§5.3.3). This is not circular: it uses the Budget's approved amounts, not a Finance decision. An over-budget Draft therefore cannot be sent to Finance; Finance could only return it. The Planner's recovery is to reduce the plan or to use **Request budget revision** (§7.2). Decision-time validation (§5.3.3) still governs Confirm plan funding, so an approved amount that changes after the request still fails the positive decision atomically. U10-OVER-APPROVED remains the presentation of that case and of an Active reassessment that cannot be confirmed (§5.3.4). Current availability below the planned amount remains advisory only.

#### 5.3.2 Review history and Draft edits

Replace the ambiguous lifetime rule “one Finance task exists per Version” with **at most one open Finance task per Plan Version**. Completed and cancelled reviews remain immutable history. Every replacement review covers the whole Plan, never an individual item. A repeated idempotency key returns its original review or decision.

The Planner may edit a Draft while Finance is reviewing it. A change to the financial basis cancels the obsolete open review or makes a completed confirmation stale in the same transaction. A non-financial edit does not invalidate Finance evidence, although it may independently fail source, Strategy, method or schedule readiness. Finance sees the basis it is deciding, not an unexplained mixture of old and new totals.

Source-set changes that leave every per-line amount and financial eligibility fact unchanged do not, by themselves, require a second affordability confirmation. The old Finance decision remains an affordability decision; new source content still receives the required preparation, adoption and statutory governance. The reuse record explicitly links the current Plan's financial basis to the earlier confirmation rather than relabelling the earlier evidence as if Finance reviewed a different Plan snapshot.

#### 5.3.3 Command-time concurrency

BUD `check_plan_affordability` is expressly non-mutating and takes no lock. PLN must not claim that calling it alone establishes a locked approval basis.

**Agreed coordinated contract:** Budget supplies `validate_plan_affordability_for_decision`, distinct from the ordinary display/read call. It participates in the caller's decision transaction, locks or otherwise serialises the relevant authoritative Budget basis, validates the expected line revisions and returns the comparison snapshot. It creates no Budget financial record, reservation or ledger event. Planning records the Finance decision only if that same transaction remains valid. Budget owns the locking and validation; Planning does not query or lock another module's tables directly.

This contract needs a matching BUD amendment. The read-only/no-lock promise for `check_plan_affordability` remains unchanged. A stale Budget change must fail the attempted positive decision atomically rather than produce a confirmation on a basis that was already obsolete at commit.

#### 5.3.4 Stale evidence during governance and after activation

| Plan condition | Recovery |
|---|---|
| Draft | Recompute readiness and request a new Finance review |
| Awaiting AO or statutory approval | Positive decision blocked; the responsible governance actor can return the Version; correction can reuse or replace funding evidence under the stated basis rules |
| Approved but publication incomplete, or Published — activation held | Hold/reconcile and use the explicit §5.5.2 recovery route; never edit approved content or assume a timed-out attempt was unpublished |
| Active; approved amount changed but unchanged Plan remains affordable | Use `RequestPlanFundingConfirmation` for reassessment of the exact Active content; append new Finance evidence; do not modify the approved baseline or repeat Plan approval |
| Active; unchanged Plan exceeds the revised approved amount | Reassessment cannot confirm it; Planner prepares a governed successor to change the Plan; earlier authorisations are not silently reversed |
| Active; source or substantive Plan content needs correction | Use the source/DPP and Plan successor route, not a funding reassessment |

While current funding evidence for an Active Plan is stale, new Requisition authorisation remains blocked. Existing authorised Requisitions and their reservations are not revoked by a Planning evidence-state change. The agreed Active reassessment closes the otherwise missing recovery path and must appear in the roles, service, UI and acceptance contracts.

No reassessment overwrites the original Finance statement attached to the approved Plan. Readers can distinguish **Funding checked at approval** from **Latest funding check**.

### 5.4 Corrections, successors, scope and procurement coverage

#### 5.4.1 Stable requirement identity and exact revision identity

Three identities must not be conflated:

| Identity | Purpose |
|---|---|
| Stable departmental source | Identifies the same requirement through DPP corrections and updates; Need ID for a Need-origin requirement, a generated persistent direct-source key for a direct requirement |
| DPP entry revision | Identifies the exact certified source facts, funding and disposition in a particular DPP submission |
| Plan allocation revision | Identifies the exact approved quantity/value/source representation used by a particular Plan Version and downstream authorisation |

The baseline's use of a direct entry's new `dpp_entry_id` as its stable source identity fails when the entry is copied. Persist or carry a stable direct-source key through copies. Section 4.3 fixes the representation as direct_source_id carried through exact DPP entries.

Similarly, distinguish stable Plan Item identity from the record representing that item in an exact Plan Version. Requisition uniqueness and cumulative consumption use stable identity; audit evidence uses version-specific identity. Do not create new spendable capacity by copying rows into a successor.

#### 5.4.2 Source-cohort rule

For an Annual Plan correction, preserve the stable source cohort of the returned submission. Permit replacement of a source's old DPP entry revision with its current accepted DPP entry revision. Where the source has been authoritatively withdrawn or accepted as not proceeding, permit its removal from the correction with the exact upstream evidence. Do not admit unrelated newly accepted sources.

These permissions do not override §5.4.6's procurement-scope lock. A revised source ID, copied Plan Version or apparently current DPP submission cannot enlarge a package that has already reached Requisition authorisation. Source revision substitution must preserve the authorised procurement scope or follow the separately governed correction route; it is not an automatic scope-expansion mechanism.

This consolidates the replacement of “exactly the same sources” where that wording incorrectly means the same obsolete revision identifiers. All submitted evidence remains immutable. The correction is a new Draft with new allocations and a new submission.

An accepted DPP correction affecting a mutable item marks it **Source correction required**. The Planner dissolves and re-forms the affected Draft item; the system never silently replaces the allocation. While the Plan is under governance, block positive decisions and enable return. An unrelated new DPP does not block the submitted Plan.

#### 5.4.3 Pending inputs

`Pending addition` remains a derived presentation state. Derivation must consider whether the open Draft is eligible to admit the source, not merely whether a Draft exists. A governance-correction Draft with a closed source cohort may coexist with pending unrelated inputs.

Normal initial consolidation Drafts and ordinary Plan-update Drafts can admit eligible pending sources before their own submission. Submitted Versions and correction Drafts cannot absorb unrelated inputs. On acceptance of a later DPP, no read, notification or event creates a second open Plan Version.

#### 5.4.4 Successor activation and balances

The Active predecessor remains authoritative during successor drafting, correction and governance. At activation:

1. Verify that the candidate is based on the still-current Active predecessor, where one exists, and that no conflicting candidate already won activation. For an initial Plan or a correction of a Published — activation held Version, use the explicit origin and Active-predecessor rules in §5.5.2.3; never invent an Active predecessor.
2. Preserve exact immutable authorisation references to the earlier Plan Version.
3. Carry stable source and item identity into the successor; net drawdown is cumulative across the chain, not reset to zero.
4. Reject any reduction below already consumed quantity/value and any forbidden change to funding identity on a source with retained downstream use.
5. Apply approved whole-item removals only when current downstream checks allow them.
6. Treat an approved removal as an explicit accounted-for exclusion; do not immediately place the same source back in the consolidation queue.
7. Change the Active pointer and publish usage/eligibility changes atomically. No Budget reservation is released by this transaction.

Also enforce §5.4.6 at successor submission and activation. The checks above against reductions below consumption are necessary but insufficient: an increase or added source must also be rejected for an item whose procurement scope is locked. An authorised or published predecessor does not make additional successor sources part of its downstream proceeding.

A cancelled successor does not reverse predecessor consumption or release Requisition reservations. A Draft successor's copied allocations are proposed capacity, not a second operative allowance.

#### 5.4.5 Requisition correction request

REQ §7.4A's statement that an Active Plan may still be “open to correction” must be removed. An Active baseline is never directly editable.

The agreed inbound `PlanItemCorrectionRequest` records requesting Requisition and Version, affected stable Plan Item and exact approved Version, reason, requester, received time and idempotency identity. Its states are **Open**, **In progress**, **Resolved** and **Closed without change**. Procurement Planner is the responsible actor; the task grants no additional authority.

For a Planning-owned fact, the Planner uses a Plan successor. For a Need fact, correction starts in Departmental Needs and passes through a newly accepted DPP; for DPP funding/direct-requirement facts, correction starts in a DPP update. Planning does not use the request as permission to edit another module's facts.

**Resolve** is allowed only after a referenced correcting Plan Version is Active and the correction result identifies the replacement eligible lineage. It notifies Requisitions through the neutral response contract so that a fresh Draft can be created; the stopped Version remains immutable. **Close without change** requires a reason and informs the requester; it does not silently revive or authorise the stopped Requisition. REQ must define the permitted requester follow-up for this outcome in its corresponding amendment.

**Approved resolution — PLN-RI-029: Plan Item authorisation hold while upstream correction requests remain unresolved.**

| Question | Approved rule |
|---|---|
| Start of hold | When an authorised upstream correction request is successfully recorded against the stable Plan Item. Recording the request and making the hold effective are atomic. |
| Work held | New Requisition authorisations against that item. Read access and investigation remain available; a correction request alone does not grant any edit authority. |
| Scope | Item-specific. Other Plan Items and the APP remain usable, subject to their own existing gates. |
| Existing downstream proceedings | Existing authorised Requisitions and published Tenders remain unchanged. Revocation, reservation release and Tender cancellation require the respective module's governed action. |
| Multiple requests | One effective hold is derived while any request affecting that stable item is Open or In progress. Closing one request cannot release another request's hold. No separate discretionary clear-hold action exists. |
| Release | Every relevant request must be Resolved against an Active corrected baseline or Closed without change with a recorded reason, using the Planner-owned disposition commands above. Then recalculate current eligibility; clearing the hold does not override funding, scope or other eligibility failures. |
| Stopped Requisition | It does not restart automatically. Its stopped Version stays immutable; subsequent work follows the Requisition correction/restart contract. |

Recheck the hold inside Requisition authorisation under the same stable-item concurrency guard used to record/dispose of correction requests. A request acknowledged as recorded must not be bypassed by a stale eligibility response. Preserve the distinct scope restriction in §5.4.6: disposing of a correction request does not permit enlarging an already-authorised procurement package.

Required verification: an open request blocks authorisation only for its item; existing authorisations, reservations and published Tenders remain unchanged; two unresolved requests require two valid dispositions; a Draft correction cannot release the hold; a reasoned no-change disposition does not restart the stopped Requisition; hold release re-evaluates all other eligibility gates; concurrent request recording and authorisation cannot bypass the committed hold.

#### 5.4.6 Later Needs after procurement has commenced — MVP scope boundary

**Reported scenario.** The user created a new departmental Need, progressed it through departmental planning and revised the APP to absorb it into a Plan Item that already had a published Tender. The later Need appeared subsumed despite having no corresponding route to fulfilment. This is a user-reported behavioural defect; it has not been independently reproduced against code or the live application in this review.

**Operational assessment.** A later requirement for the same kind of goods or services is a realistic case, for example additional laptops required after an earlier laptop tender was published. Keep later Needs and governed APP updates in the MVP. Prevent their absorption into an existing package already taken into procurement.

**MVP invariant:** once any Requisition for a stable Plan Item has been authorised, an APP update shall not add departmental sources to that item or increase its procurement scope. Publication is not the first protection point: authorisation is the earlier boundary at which the exact operational package and drawdown are fixed. This is an intentionally restrictive product rule; it is not a claim that legislation prohibits every formally governed tender amendment or contract variation.

| Concern | Required behaviour |
|---|---|
| Lock scope | Protect source membership and the authorised package against added quantities, increased value ceilings representing additional procurement, and scope expansion disguised as a title/description or source-revision change. Apply the rule to the stable item through all successor Versions. |
| Existing downstream work | Preserve the original source allocations, approved quantity/value, Requisition drawdown and Tender linkage. An APP successor never rewrites the issued Tender or enlarges its coverage. |
| Later Need | Use normal Need acceptance, DPP update, HoD certification and Procurement validation. Form a separate Plan Item for the additional requirement in an eligible APP successor; do not attach it to the locked item. |
| Further governance | Apply the normal Finance assessment, APP preparation/adoption/statutory approval and publication/activation requirements. Once eligible, the new item follows its own Requisition and subsequent procurement proceeding. |
| Thresholds and splitting | Apply the relevant method conditions and anti-splitting assessment to the additional procurement, including related procurements where the controlling rule requires it. A separate item is not permission to use a lower-value method merely by separating records. |
| Planning inclusion | Derive from the exact new source allocation in the Active APP. It means the requirement is planned, not procured or fulfilled. |
| Procurement coverage | Derive from exact source allocations and quantities included in the authorised Requisition and downstream issued package. A tender attached to an older version of the same item is not evidence of coverage for a later source. |
| Fulfilment | Derive only from the relevant downstream delivery/acceptance evidence when that capability exists. Planning inclusion or tender publication alone never marks a Need fulfilled. |
| Remaining original allowance | This rule does not cancel the existing allowance or prohibit otherwise eligible sequential drawdowns within its original scope. It prohibits enlargement or the introduction of later sources. |
| Scope of the restriction | It is item-specific. Other items, new Needs and legitimate APP updates remain possible. Read-only owner-supplied operational dates do not enlarge procurement scope. |
| Published-Tender changes | Any lawful amendment, cancellation/replacement or later contract variation belongs to its own governing module and procedure. APP approval alone authorises none of those actions. Scope expansion through such procedures is outside this MVP recommendation. |

Do not unlock the item merely because an APP successor has a new identifier or a newer DPP source revision. Revocation or cancellation does not silently reopen the scope through Planning; any future reopening/replacement mechanism requires an explicit coordinated contract. This rule does not redefine the existing Requisition-owned reversal of unused drawdown and reservation.

**Enforcement:** resolve the authoritative Requisition-authorisation and downstream-use evidence server-side. Enforce the item restriction during source formation/re-formation, source substitution, relevant item saves, APP submission and successor activation. Requisition authorisation and APP activation must serialise against the same stable-item scope/lineage guard so a concurrent authorisation cannot be bypassed by a previously prepared scope-expanding successor. Disabling an editor control alone is insufficient. A rejected command leaves allocations, totals, workflow state, drawdown and publication evidence unchanged.

**Required error:** `PLN_ITEM_SCOPE_LOCKED` — **This item already has an authorised requisition. Add extra requirements as a separate item in a plan update.**

**Core regression:** take an original source through an Active APP, authorised Requisition and published Tender; introduce a different accepted Need; attempt to absorb it through a DPP and APP successor. Absorption must fail. The same new Need must successfully form a separate Plan Item, complete ordinary APP governance and become eligible for its own Requisition. The original Tender retains its original source set and quantity/value. Until the new item has its own downstream coverage, no view or status may present the old Tender as covering or fulfilling the new Need.

Repeat the lock test with authorisation completed but the Tender not yet published, with a partial original drawdown, with a copied successor identity, with a same-source revision carrying increased quantity, and with authorisation racing successor activation. Preserve the existing no-partial-Need-allocation rule: this change does not authorise inventing a residual quantity from an accepted Need without a separately defined source treatment.

### 5.5 Schedules, operational evidence, publication and method conditions

#### 5.5.1 Single-year scope and delivery feasibility — RI-034–039

**MVP scope is single-year procurement with completion within the target financial year.** Remove the selectable Multi-year option and reject multi-year submissions server-side. If the prescribed output requires a horizon indicator, retain a fixed Single year value without an editable control. Multi-year procurement is an explicit future facility, not an undocumented partially supported option.

The departmental required-by date is the upstream completion boundary. A combined item's baseline completion boundary is the earliest required-by date among its proceeding sources. Requisition may select an earlier operational delivery date but cannot extend the Plan or source boundary. The laptops therefore retain a Plan boundary of 31 December 2027 and may use the earlier Requisition delivery date of 30 September 2027. Planning must not depend on a not-yet-created Requisition to derive its baseline.

| Input or rule | Approved requirement |
|---|---|
| Schedule profile | Resolve a versioned method/procedure profile defining applicable milestones, their order, counting rules, legally verified minimum/maximum periods, and separately labelled internal planning assumptions |
| Missing profile | Permit Draft preparation; block Sign and submit Annual Plan for an affected item. Do not silently substitute Open Tender rules |
| Estimated delivery or implementation period | Required non-negative integer calendar days, entered by the Planner for the package. A profile may supply an editable default. Zero means an explicit same-day estimate; it is never the missing-value fallback |
| Feasibility calculation | Baseline contract-signing date plus estimated delivery/implementation period must be on or before the source-derived completion boundary |
| Failure | Block Plan submission and identify the item, estimated completion date and required-by boundary. Correct the procurement start, an inaccurate estimate or the source deadline through its governed departmental route; never silently extend a deadline |
| Meaning of result | Estimated completion is a feasibility calculation; it does not replace the approved source-derived baseline completion boundary |
| After activation | MVP keeps the approved baseline readable. Owner-supplied expected/actual dates may be displayed separately; no Planner forecast input exists |
| Future cascade | When separately approved, propose remaining eligible forecast changes, validate every affected adjacency and allow a reasoned final-milestone change |
| Historical evidence | Lock baseline and resolved rule-profile evidence at submission. Any future forecast facility must retain revision history after supersession |

Profiles belong in the existing System setup surface under Configuration & Governance. Specify method and procedure, milestones and sequence, counting rules, statutory limits with source references, internal default periods/buffers, effective dates and Version. Administrator/System Manager maintains them under existing configuration authority; no new approval workflow is introduced. Referenced Versions are immutable and changes audited. The work includes records, maintenance screens, resolver, validations, verified seeds and acceptance coverage, not only a new configuration field.

Multi-year support will require full package value and completion horizon, annual funding allocations, separation of approved and anticipated future funds, authority to commit future obligations, and corresponding Budget/Requisition contracts. It remains outside this MVP.

#### 5.5.1A Actuals and distinct variance measures — RI-032, 038

Record actuals **per procurement proceeding**, linked to the exact Plan Version and source allocations, quantities and values that the proceeding covers. Show each proceeding beneath the Plan Item. Do not collapse different Tender dates into an unqualified item-level actual. Sequential drawdowns within the original allowance remain permitted.

For example, two Tenders for 100 and 150 laptops may have invitation actuals on 1 May and 1 September. Both must remain visible. Selecting either as the actual for the entire 250-laptop item loses material information.

- A repeated event ID is idempotent; a different Tender's event is a separate fact.
- A correction references and supersedes the earlier event; it does not overwrite it. Define producer ordering and correction linkage so replay cannot restore obsolete evidence.
- Preserve the exact baseline Version used in every MVP comparison. Never substitute the latest APP after the event. Any future forecast comparison must also identify and preserve its exact forecast revision.
- Planning accepts actuals only from the module owning the real event. TPR/TPUB already defines the invitation actual path; the other six operational event integrations remain future owning-module work.
- Aggregate item-level milestone dates are outside the MVP.

| Measure | Formula and meaning |
|---|---|
| Baseline lateness | Actual milestone date − baseline milestone date. Positive is late; negative is early |
| Forecast error | **Future facility only.** If separately approved, actual milestone date − identified forecast date. Positive is later than that forecast |
| Duration variance | Planned elapsed days − actual elapsed days. Negative means the stage took longer; this is the convention recorded in the supplied LAW register |
| Elapsed days | Calculate between the explicitly defined start and end events using the applicable profile counting rule |
| Missing evidence | Show Not available when required actuals or comparison evidence are absent; show Not applicable for an inapplicable stage. Neither is zero |

Use explicit labels, not an unexplained Variance heading. A stage may start and finish late yet take fewer days than planned. Statutory duration fields must not be populated with simple milestone-date lateness. Preserve the distinction in views, review packs, publication/report mappings and tests.

#### 5.5.1B Future reminders — RI-040

This facility is not implemented in the v1.24 MVP. The rules below are retained for a separately approved future implementation after authoritative milestone ownership and actual/expected-date integrations exist. The MVP creates no schedule-driven Planning reminders, reminder records, scheduled checks or notification producers.

| Concern | Approved rule |
|---|---|
| Recipients | Currently authorised Procurement Planners through shared notifications; recheck read authority |
| Approaching period | Governed configuration; initial operational default 7 calendar days, expressly not a statutory period |
| Date passed | Scheduled date passed — actual not recorded. Missing evidence is not proof that the event did not happen |
| Unsupported actual integration | Actual tracking not yet available; do not imply the system verifies completion |
| Identity | One notification per recipient, stable Plan Item, proceeding where applicable, and milestone; no per-day duplicate key |
| Repeated runs | Update the same unresolved notification rather than creating another |
| Reforecast | Update the same record; make it inactive outside the reminder window and reactivate it when due. Retain history |
| Actual received | Resolve the corresponding notice. Reading or acknowledging a notice does not record completion |
| Transition to proceedings | Retire the corresponding pre-procurement reminder on transfer of responsibility. Retain reminders for any original allowance that has not transferred; never notify twice for the same covered work |
| Workflow effect | No approval task, lifecycle transition or procurement hold; a missed reminder blocks nothing |

#### 5.5.2 Approved publication and recovery — RI-041–045

Approval commits the exact immutable content identity and a durable publication intent. External transmission occurs afterwards. A remote website call cannot be made part of the local database rollback by placing it inside ApproveAnnualPlan.

##### 5.5.2.1 Publication package

The MVP publishes the Annual Procurement Plan using the Third Schedule layout identified by the requirements, subject to the source/layout verification in §17.2. Provide an accessible web presentation and downloadable PDF, plus a precisely versioned **KenTender Annual Plan JSON schema** with an explicit field mapping. All representations derive from one approved snapshot.

Freeze publication files and their hashes. Retries resend the exact approved files under the same publication identity. Preserve Annual Plan ID, exact Plan Version ID and stable Plan Item IDs. Disposal content is excluded. Owner-supplied operational dates appear separately; they never rewrite the approved publication. Approved successors create new publications and retain predecessors.

The adapter acknowledgement identifies the exact package, its hash, public location and acknowledgement timestamp. A generic success response is insufficient. Distinguish confirmed failure, authoritative success and indeterminate result. Record external success even if activation checks fail. Activate once only when authoritative acknowledgement and all current activation checks pass.

**Full OCDS publication is deferred to a separate future facility.** Remove the current “OCDS-shaped” contract and do not label the MVP JSON OCDS-compliant. Do not manufacture one contracting-process identifier per Plan Item. One Plan Item can support separate proceedings. The future facility must define the supported OCDS version, extensions, registered identifier prefix, planning/proceeding relationships and downstream release history. The official OCDS overview organises data around contracting processes; its release reference describes immutable releases: [OCDS overview](https://standard.open-contracting.org/latest/en/primer/how/), [release reference](https://standard.open-contracting.org/latest/en/schema/reference/).

##### 5.5.2.2 Treasury submission evidence

Transmission to Treasury remains external in the MVP. The Accounting Officer uses **Record Treasury submission** against the exact approved Plan Version; this records an external action, not another approval.

| Field or control | Required contract |
|---|---|
| Submission evidence | Submission date/time, transmission channel, destination, dispatch/reference number and supporting attachment |
| Content identity | Link to the immutable approved document and system-generated hash; require confirmation that this was the document submitted |
| Audit | Record officer and recording timestamp automatically; distinguish submission time from recording time |
| Gate | Approved — awaiting Treasury submission evidence is the pending reason until valid evidence exists |
| Required proof | Submission/dispatch evidence; no extra Treasury approval or receipt-acknowledgement gate |
| Correction | Append a superseding evidence record with a reason; never overwrite the earlier record |
| Invalidated evidence | Hold transmission before publication; reconcile any outstanding attempt under §5.5.2.3 |
| Successor | Its own newly approved document requires its own evidence; predecessor evidence cannot satisfy the gate |

Treasury submission recorded, entity website publication acknowledged and State Portal publication are distinct facts. None proves the others. Automated Treasury transmission and acknowledgement handling are explicitly future facilities. This design follows the supplied LAW register; independent legal applicability verification remains a prerequisite.

##### 5.5.2.3 Material defect and withdrawal for correction

| Publication condition | Approved recovery |
|---|---|
| Confirmed unpublished; no outstanding transmission | Hold transmission. AO requests withdrawal with a mandatory reason; the configured statutory approving authority performs Withdraw for correction. Preserve the approved Version as Withdrawn for correction and create one copied Draft |
| Outcome unknown or transmission in flight | Hold further transmission and reconcile the existing attempt. No withdrawal or replacement candidate while publication remains uncertain |
| Confirmed published and valid for activation | Preserve publication and activate through the existing guarded process; subsequent correction uses a governed successor |
| Confirmed published but activation checks fail | Published — activation held. Preserve the external fact; the Version provides no new Requisition authority. Permit one linked correction successor without forcing defective content Active |

A system-detected material defect or authorised correction request places transmission on hold immediately. A hold is not a withdrawal of statutory approval. Coordinate hold, worker dispatch and reconciliation so an in-flight attempt can never be classified as confirmed unpublished merely because the local worker stopped.

The confirmed-unpublished correction repeats applicable checks, Finance confirmation/basis evaluation, Head-of-Function signature, AO adoption and statutory approval. Preserve all earlier content, signatures and publication history. Normal correction-cohort and scope-lock rules apply; no new requirement is smuggled into the correction. An existing Active predecessor remains operational subject to its own current eligibility.

A correcting candidate linked to a Published — activation held Version records both that correction origin and the actual current Active predecessor, if one exists. Activate against the current authoritative baseline and cumulative consumption, not against a fictional Active state for the held Version. On success, retain the held Version's true history and explicit replacement relationship. Technical retry authority cannot withdraw approval, edit the approved content or fabricate publication.

#### 5.5.3 Reservation calculations and method eligibility — RI-047–049

##### 5.5.3.1 Planned reservation allocations

Each obligation has its own calculation. For the 30% AGPO **planning** target, the denominator is the eligible value of the current complete Annual Procurement Plan (APP), not the entity's approved Budget ceiling and not unused Budget headroom.

`eligible_current_app_value = sum(estimated value of every current Plan Item included by the exact verified AGPO rule)`

`required_planned_allocation = applicable percentage × eligible_current_app_value`

`remaining_planned_allocation = max(required_planned_allocation − qualifying_planned_allocation, 0)`

The approved Budget remains a separate funding ceiling and affordability control. The APP may lawfully plan less than that ceiling. Planning must neither invent purchases to exhaust the Budget nor omit genuinely expected eligible procurement merely to reduce the denominator.

| Concern | Approved rule |
|---|---|
| Denominator | Use the exact current complete APP Version. Sum each Plan Item's estimated value only where the exact verified obligation says it is eligible. Name and evidence every exclusion; never include unused Budget headroom |
| Qualifying allocation | Sum only the planned value explicitly reserved for categories eligible under that obligation |
| Partial package | Count only its expressly allocated qualifying amount. MVP requires a separately identified Plan Item for that allocation; a lotting flag does not make the full package qualifying |
| Complete-plan safeguard | Before positive submission, the APP must contain all genuinely expected procurement known for the period and every proceeding accepted requirement must be included or explicitly disposed of under the existing coverage controls |
| Amendment | An approved APP amendment that adds, removes or changes eligible procurement recalculates the denominator, target, qualifying amount and shortfall for the successor Version. It never rewrites the earlier snapshot |
| County requirement | Separate applicable calculation with legally verified denominator and eligible categories; never combine 20% and 30% into one target |
| Overlap | Count once within each measure; count towards both only where verified rules permit. Do not infer eligibility from a generic reservation label |
| Display | Eligible planned procurement; target percentage; required allocation; planned qualifying allocation; remaining allocation; exact Plan Version and exact rule Version. Show the Budget ceiling only in Funding |
| Submission | Incomplete Drafts permitted. Block Sign and submit Annual Plan where a verified mandatory planning allocation is unmet or its calculation basis is missing. **v1.27 (D2):** an unmet allocation does not block Request plan funding confirmation. Finance's verdict is affordability only, and a designation choice changes no per-line amount, so the funding check and the allocation correction may proceed in parallel |
| Override | A justification does not waive the mandatory allocation |
| Later gates | Preserve submission-time budget/rule Versions and recheck subsequent positive decisions; do not rewrite historical results |

Example: a complete current APP with KES 130 million of eligible planned procurement requires KES 39 million at 30%. If KES 50 million is explicitly and validly designated for qualifying enterprises, the planned target is met and the qualifying share is 38.46%. A separate approved Budget ceiling of KES 160 million does not change that denominator.

This consolidates the replacement of the blanket advisory-only rule in PLN and CFG. It can require further qualifying allocations before a complete Plan enters approval, without requiring every department to submit where the intake and coverage rules already permit that result. The measure is **planned allocation**, not proof of actual procurement achievement. Actual achievement uses `qualifying_actual_procurement_value ÷ applicable_actual_procurement_value` from authoritative downstream facts; Planning must not derive it from estimates. Exact eligible categories, county basis and permissible overlap remain legal-verification prerequisites; absence of verified mandatory configuration cannot be reported as success. Keep the optional market-price index separate.

##### 5.5.3.2 Planned designation and candidate entitlement

The Planner selects the intended reservation group from the governed catalogue as part of ordinary Plan governance. Planning separately checks mandatory restrictions using known facts such as funding source, category and estimated value.

Remove automatic “highest advantage” ranking from Planning and delete the reason-only override. A mandatory restriction cannot be bypassed by narrative. Candidate eligibility and the application of candidate-level preferences belong to the downstream module using verified candidate evidence and applicable rules; this is an explicitly deferred downstream facility.

Planned reservation, mandatory procurement restrictions and candidate preference entitlement are distinct concepts and cannot be represented by one overloaded reservation_category field. An approved designation changes only through governed Plan succession; after procurement starts it must also respect the scope lock and cannot silently alter issued eligibility conditions.

##### 5.5.3.3 Method conditions

For each admitted method, Configuration & Governance holds a versioned, legally verified eligibility profile: applicable categories, value/cumulative limits, required circumstances, evidence and any particular authorisation with its actor and required stage.

Selecting a method shows its specific conditions and evidence requirements. Validate facts the system can establish; reject failed mandatory conditions. Conditions requiring judgement need structured declarations and supporting evidence reviewed through existing Plan governance. A declaration is not independently verified truth, and a generic justification is not a universal substitute.

Permit Draft work, but block submission where required planning evidence or a complete method eligibility/schedule profile is absent. APP approval does not substitute for a separately required authorisation. Before actual use, the responsible procurement module rechecks current facts and authorisations.

The eleven-method catalogue remains; catalogue membership does not imply operational support. A method is eligible for submission only when its required conditions, evidence and schedule profile are implemented. Exact legal values and applicability must be verified under §17.2.

### 5.6 Retained formation and readiness invariants

1. Form only source-backed items from current accepted **proceeding** DPP entries. Each admitted source is allocated once at full quantity/value in the submitted candidate; non-proceeding entries, explicitly approved removals and unrelated pending inputs are excluded from that allocation requirement.
2. Combination requires the same FY, Procurement Budget Line and currency, compatible UOM and procurement treatment, identical effective accepted category and requirement type—including any immutable §5.1.6 correction—and the required aggregation reason. Multiple departments may contribute; the source OU still governs Budget Line eligibility. No blank item, partial Need or fabricated residual source is permitted.
3. Item quantity/value and funding breakdown equal exact source allocations. Estimates include applicable incidental costs and have an identifiable market-survey basis. An item cannot gain capacity by dissolving and re-forming consumed sources under a different identity.
4. Pre-Finance readiness requires a nonempty proceeding Plan, eligible allocations, complete package/classification/Strategy/designation/structure and a valid calculable schedule. **v1.27 (D2) makes two tests explicit:** every Plan Item has a selected procurement method, because its schedule is calculated from that method's profile (§5.5.1), failing with `PLN_PLAN_CONTENTS_INCOMPLETE` naming the item; and every operative Budget Line's planned total is within its approved amount (§5.3.1), failing with `PLN_PLAN_NOT_AFFORDABLE`. A selected method whose profile is missing or unverified still blocks only Sign and submit Annual Plan (§5.5.1, §5.5.3.3). A reservation shortfall is not a pre-Finance test (§5.5.3.1). It excludes current Finance confirmation to avoid circularity. Draft saves remain possible with displayed blockers. Formal submission additionally requires current affordability, verified applicable method/reservation rules, complete required evidence, valid route and HOPF signature.
5. Only the Planner classifies departmental proceeding requirements and forms/edits items. Departmental users certify their requirements, not procurement classification or Strategy selection.
6. A splitting detection advisory is a prompt for assessment, never authority to waive a mandatory method/cumulative limit. Record the related item set, triggering rule Version and reasoned confirmation/aggregation response. Re-evaluate after relevant changes; mandatory conditions still block. Lotting or planned reservation alone is not a blanket anti-splitting exemption.
7. The approved schedule remains immutable. Owner-supplied operational dates are separate read-only evidence and never update one unqualified item actual. Missing supported evidence is Not available; unsupported evidence is omitted from ordinary views.
8. An Active predecessor is retained while an update proceeds, subject to its own live funding, remaining allowance and correction-hold gates. Read access, pending work or a successor alone cannot create or revoke procurement authority.


### 5.7 Next-step guards and state-by-responsibility table — v1.27

This section is the Planning implementation of KT-STD-001 v1.8 §3B. Every command guard in §7.2 returns `allowed`, a §8 reason code, the figures and the fixes; the next-step answer is computed from those guards on the server. The table states, for each state, the formal stage (§10.1A.1 and §10.1A.2), who holds it, and what every other actor with read access sees. Presentation is §10.1A and the per-screen paragraphs.

**Annual Plan**

| Plan condition (§5.2) | Stage | Holder and kind | Blockers and fixes | Everyone else with read access |
|---|---|---|---|---|
| Draft; pre-Finance readiness fails | Preparation | Procurement Planner: Your turn, blocked | Every failing §5.6 item 4 test together, including `PLN_PLAN_NOT_AFFORDABLE` (fixes: Request budget revision; Reduce a purchase) and `PLN_PLAN_CONTENTS_INCOMPLETE` (fix: Choose a procurement method) | Waiting: plan being prepared by the Planner |
| Draft; Open budget revision request; line still over | Preparation (Blocked) | Procurement Planner: Waiting on Budget Officer, since the request instant | Reduce a purchase stays available as Draft editing | Budget Officer: Your turn in BUD; others Waiting |
| Draft; pre-Finance readiness passes; funding Not requested, Returned or Stale | Preparation | Procurement Planner: Your turn — Send to Finance for funding review | — | Waiting |
| Draft; funding Awaiting confirmation | Funding confirmation | Finance Confirmation Officer: Your turn | — | Planner and others: Waiting on the Finance Confirmation Officer |
| Draft; funding Confirmed; a formal-submission gate fails | Signature (Blocked) | Procurement Planner: Your turn, blocked, where the fix is Planning work (for example `PLN_RESERVATION_SHORTFALL`); Administrator or System Manager route where the fix is setup (§10.16) | Every failing gate together | Head of Procurement Function: Waiting, naming the blocker |
| Draft; funding Confirmed; all formal gates pass | Signature | Head of Procurement Function: Your turn | — | Waiting |
| Awaiting Accounting Officer | AO adoption | Accounting Officer: Your turn; blocked for the positive decision when §6.3 evidence is stale (Return remains) | Stale funding, source or Strategy evidence (§5.3.4, §6.3) | Waiting |
| Awaiting statutory approval | {Capacity} approval | Configured statutory authority: Your turn | As above | Waiting |
| Approved — publication pending; Treasury evidence missing | Publication | Accounting Officer: Your turn — Record the Treasury submission | `PLN_TREASURY_EVIDENCE_REQUIRED` | Waiting |
| Approved — publication pending; prerequisites met, no hold | Publication | System | — | Waiting for website publication |
| Publication failed or indeterminate | Publication (Blocked) | Authorised technical operator: Your turn — Retry publication or Check publication result | `PLN_PUBLICATION_FAILED` / `PLN_PUBLICATION_UNKNOWN` | Waiting on an authorised technical operator |
| Material defect held; confirmed unpublished | Publication (Blocked) | Accounting Officer: Your turn — Request withdrawal for correction | `PLN_PUBLICATION_HELD` | Waiting |
| Withdrawal requested | Publication (Blocked) | Configured statutory authority: Your turn — Withdraw for correction | — | Accounting Officer: Waiting |
| Withdrawn for correction | Correction Draft restarts at Preparation | Procurement Planner: Your turn — Continue the correction | — | Waiting |
| Published — activation held; no open correction | Publication (Blocked) | Procurement Planner: Your turn — Prepare a corrected plan | `PLN_ACTIVATION_HELD` | Waiting |
| Active | In force | Done: In force since the activation instant | — | Done |
| Returned, Superseded, Cancelled | Not drawn | Not involved (historical) | — | Not involved |

An Active reassessment (§5.3.4) is Finance work outside the approval lifecycle: the Finance Confirmation Officer's Your turn, with no tracker. A Draft update or correction follows the Draft rows while the Active predecessor stays Done.

**Departmental plan**

| DPP condition (§5.1) | Stage | Holder and kind | Blockers | Everyone else |
|---|---|---|---|---|
| Draft, initial or correction | Preparation | Departmental Author or Head of User Department: Your turn; the Head of User Department certifies | `PLN_NEED_COVERAGE_INCOMPLETE`, `PLN_ENTRY_INCOMPLETE`, `PLN_WINDOW_CLOSED` for an initial submission (fix per §10.1A.7 D3) | Waiting |
| Submitted | Procurement review | Procurement Planner: Your turn | `PLN_CLASSIFICATION_INCOMPLETE`; a stale source permits Return only | Certifier: Waiting; a Planner who certified it: Waiting (segregation, §6.4) |
| Accepted; no open candidate | Accepted | Done | — | Done |
| Accepted; update in progress | Preparation (update candidate) | As Draft | As Draft | Accepted submission remains effective |
| Accepted; no open candidate; one or more current accepted Needs of the department in *Update required* (v1.28) | Preparation (the next update) | Departmental Author or Head of User Department: Your turn — **Add {need list} to this plan**, sentence **It was accepted after this plan was accepted. Create an update to add it, then fund it and resubmit.** (plural: **They were … add them, then fund them …**), primary action Create update | — | Procurement Planner: Waiting — **Waiting for the department to add {need list} to its plan**, since the latest such Need's acceptance; Auditor and other readers: Not involved; technical reader: Waiting |

A technical reader is never given Your turn or a fix (KT-STD-001 v1.8 §3B.6). A Budget Officer's Your turn for a revision request is presented by BUD, not by Planning.

**v1.28 — tracker for an update the department still owes.** In the row above, the accepted submission stays effective, but the next step is the department's. The tracker therefore shows **Preparation: Current**, holder the department's Departmental Authors and Heads of User Department by name, and the later stages Not started. It does not show every stage Done beside a Your turn. The row *Accepted; no open candidate* (Done) applies only when no current accepted Need is in *Update required*. {need list} names one or two Need references (**NDS-MOH-2027-0005**, **NDS-MOH-2027-0005 and NDS-MOH-2027-0006**) and counts three or more (**3 accepted needs**). The departmental update request built under FU-V127-05 follows the same tracker rule; its full contract remains owed (§15.2).

## 6. Roles, permissions and segregation

All rows are subject to current AUTH assignment, OU scope, task and segregation. Read authority is not implied by possession of a link. Departmental users see their permitted source/Plan information, not other departments' protected evidence.

| Actor | Workspace emphasis | Allowed work | Explicit boundary |
|---|---|---|---|
| Departmental Author | Own departmental Drafts/corrections | Direct/source funding and disposition Draft work | No HoD certification unless separately assigned |
| Head of User Department | Departmental certification/updates | Certify/submit within current substantive or acting authority | Cannot validate own certified Submission as Planner |
| Procurement Planner | DPP validation, classification correction, consolidation, pending requirements and Plan corrections | Classify/reclassify under §5.1.6; package work, Finance request and successor/correction management | No source-fact editing, accepted-decision mutation or final HOPF signature unless separately assigned; no procurement creation or MVP forecast maintenance |
| Head of Procurement Function | Plan ready for preparation signature | Complete review; Sign and submit Annual Plan | This is preparation accountability, not an added approval stage |
| Finance Confirmation Officer | Current plan-level review/reassessment | Confirm plan funding or Return to planner | No editing the Plan or reserving money |
| Accounting Officer | Adoption, Treasury evidence, late explanation and withdrawal requests | Existing governed actions | Does not impersonate the statutory authority |
| Configured statutory authority | Exact Plan adoption/withdrawal request | Approve, return or confirmed-unpublished withdrawal as allowed | Board/Council record collective resolution and authorised recording actor |
| Auditor/authorised reader | Plan and evidence navigation | Read-only history, permitted review pack | No business decision |
| Administrator/System Manager | Technical read under KT-STD-001 v1.7 §3A.6 | Read all Planning records site-wide through registered routes; no business command. Separately granted setup/publication-recovery authority uses the owning contract. | Technical read supplies no Planning decision or publication retry authority |

If a user holds multiple responsibilities, render permitted actions together and enforce incompatible action history across the correction chain. Do not select one role label and hide the others' legitimate work. Do not add an assignee picker to route around an unavailable or conflicted actor.

#### 6.1 Exactly one statutory route

Use the four capacities stated by the supplied LAW register: **Cabinet Secretary**, **County Executive Committee Member**, **Board**, and **Council**, resolved to the exact applicable configured legal capacity. Board and Council decisions retain their collective resolution reference and authorised recording actor. They are alternatives, not sequential approvals.

Missing or ambiguous configuration prevents formal Plan submission and is rechecked at adoption. Detecting it before submission avoids placing a Plan into a route that cannot complete. Configuration never permits `None` as a successful route.

Approved CFG v0.11 defines the four route values, county applicability, complete configuration inputs and owner maintenance. Implement its required fields and central AUTH mappings under §17.2. Planning must not invent a local approver registry. An in-flight governance task retains its exact required capacity and evidence; configuration edits cannot silently convert that task into a different approval route.

#### 6.2 Preparation signature

The earlier LAW register conflated the Head of Procurement Function with the Procurement Planner. Approved LAW v1.1 corrects that document-level ambiguity. KT-STD distinguishes Mercy Kilonzo’s Planner responsibility from Charles Mutiso’s preparation-signature responsibility. The distinct roles below remain mandatory in implementation.

**Approved implementation decision:** the Procurement Planner retains consolidation, item editing and Finance-request work. Once funding and readiness pass, the existing final submission action becomes **Sign and submit Annual Plan**, performed by the Head of Procurement Function. It records preparation accountability for the exact snapshot and sends that snapshot to the Accounting Officer. The Plan remains Draft until this command. Do not insert an additional **Approved by Head of Procurement Function** state or a separate professional-review workflow.

The Head of Procurement Function receives the exact read and submission capability necessary for this action, not an implicit Procurement Planner assignment. If one person holds both responsibilities, that person may draft and sign as preparer; subsequent Finance and governance conflicts are still checked against all actions actually taken. The fixture uses Mercy for consolidation and Charles for signing, with Finance by Josphat, adoption by Amina and statutory decision by Daniel.

This role-to-action mapping is incorporated in §§4.7, 6 and 7.2 under the recorded approval. It is grounded in the supplied signature extract, not presented as independently verified current legal advice; the recorded legal-source verification dependency remains open.

#### 6.3 Return commands must remain usable when evidence is stale

Positive and corrective decisions need different predicates:

| Predicate | Positive adoption/approval | Return for correction |
|---|---|---|
| Current authority, scope, task and state | Required | Required |
| Expected version and idempotency | Required | Required |
| Maker-checker | Required | Required |
| Current source eligibility | Required | Failure may be the reason for return; must not block return |
| Current Strategy eligibility | Required | Failure may be the reason for return; must not block return |
| Current funding evidence | Required | Failure may be the reason for return; must not block return |
| Correctly configured next stage | Required before forwarding | A missing next stage must not prevent returning the current task |
| Actionable correction reason | Not invented for affirmative decision | Required |

Apply the same distinction to DPP validation and Finance return. Otherwise stale evidence can prevent the very command required to fix it.

#### 6.4 Segregation over the evidence chain

| Earlier action on the candidate or correction chain | Later action prohibited for that user |
|---|---|
| Certify a DPP submission | Accept or return that DPP submission as Planner |
| Author Annual Plan content, form/dissolve items, request Finance, or sign formal submission | Confirm/return Finance; adopt/return as AO; approve/return as statutory authority |
| Confirm or return Finance | Adopt/return as AO; approve/return as statutory authority |
| Adopt or return as AO | Approve/return as statutory authority |

A governance return preserves the incompatible-action history through every linked correction. Creating a new Draft or changing an actor's role label does not reset it. A new independently governed successor after activation starts its own candidate chain while preserving predecessor audit history. Technical read follows KT-STD-001 v1.7 §3A.6 and is never a business-decision exception.

### 6.5 Complete actor journeys and reusable review

The following actor contract supplements the permission matrix; it creates no new authority, task stage or role. Canonical commands remain in §7. The all-actor work is implemented through the existing route families in §9 and complete screen compositions in §10. References to sketches in the approved blueprint are replaced here by the named screen family.

| Actor / task | Information and actions | Outcome / correction |
|---|---|---|
| Departmental Author — Prepare requirements | Reuse U02–U05. Included requirements, missing funding, excluded requirements and comments. **Add a requirement**, **Save draft**, and permitted inclusion/exclusion actions. | Saved work remains Draft. Explain that the HoD submits. Correct the affected row directly; no invented Author-to-HoD approval task. |
| Head of User Department — Certify the departmental plan | Same working plan, read as a complete review. Included and excluded requirements, dates, quantities, funding and reasons. Retain certification checkbox and **Submit departmental plan** / **Resubmit departmental plan**. | Submitted to Procurement for validation. Show required corrections in context. Do not invent a separate HoD “Return” decision: the HoD may correct permitted Draft work or leave it for the Author. Eligible withdrawal remains HoD-only. |
| Procurement Planner — Validate or correct classifications | U06 shows certification, included/excluded requirements and funding. Before acceptance select **Requirement type**; Category appears automatically. **Accept departmental plan** or **Return to department**. On an accepted proceeding row, **Correct classification** records a reasoned superseding classification without reopening departmental content. | Acceptance makes proceeding requirements available for consolidation; it does not approve annual procurement. Classification correction preserves the accepted decision and source facts, and identifies any item that must be dissolved/re-formed or taken through a Plan successor. |
| Procurement Planner — Prepare, update and monitor | Reuse U07–U09. Pending requirements, purchases, classification provenance, specific missing work and Finance status. **Prepare plan update**, **Continue update**, **Cancel plan update** where allowed. Correction requests remain within item context. | Current governing plan remains in force until replacement activation. Corrected source facts or classifications require explicit permitted removal/re-formation of affected Draft items; no silent substitution. Recovery details are in §11. |
| Finance Confirmation Officer — Confirm or reassess funding | U10. Approved amount, proposed amount and difference per budget line; current availability separately. **Confirm plan funding** or **Return to planner**. Reassessment title: **Check funding again for the current plan**. | Record affordability only; no reservation or Plan approval. If the decision basis changed, show that the review is no longer current and link to a replacement when one exists. Never silently switch to different amounts. |
| Head of Procurement Function — Sign and submit | Reuse AO review with title **Review and submit the annual procurement plan**. Complete purchases, funding confirmation, issues and changes. **Sign and submit Annual Plan**; secondary **Back to annual plan**. | Preparation signature sends the exact plan to the AO. No extra HOPF approval stage or invented return task. Draft defects remain preparation work; editing requires a separate Planner assignment. |
| Accounting Officer — Adopt and submit | Approved U11 AO review/return. Complete proposed plan, funding, changes and material issues. **Adopt and submit** or **Return for correction**. | Adoption sends to the configured statutory authority. It does not itself permit procurement. A returned plan comes back for the required review after correction. |
| Accounting Officer — Record external evidence and request withdrawal | U13 and §11. **Record Treasury submission**, **Correct submission details**, **Explain late start of the annual plan** when applicable; **Request withdrawal for correction** only for confirmed-unpublished eligible content. | Evidence recording is not Treasury approval. A withdrawal request goes to the existing statutory authority. AO cannot declare publication successful, change activation dates or withdraw a published plan through this route. |
| Cabinet Secretary / County Executive Committee Member — Statutory decision | Reuse AO review: **Approve the annual procurement plan**. Show AO adoption and earlier evidence. **Approve Annual Procurement Plan** or **Return for correction**. | Approval begins publication prerequisites; procurement eligibility still depends on activation and current checks. Return repeats the established correction/governance path. Eligible withdrawal uses §11. |
| Board of Directors / Council — Collective statutory decision | Same complete review plus U11 collective decision. Identify the body and authorised recorder; require the resolution reference. **Record approval** or **Record return for correction**. | Record the body’s actual decision, not a personal approval by the recorder. Existing statutory commands and required evidence remain authoritative. No member-by-member voting workflow is introduced. |
| Auditor / authorised reader — Inspect the plan and evidence | Same review without decision controls. **Current plan**, **History**, **Changes**, **View departmental requirement**, **Download review pack**; contextual back-navigation. | Preserve the exact historical values being inspected; separately label current warnings. Reader permission and departmental scope still apply. No checkboxes, confirmation tasks or authority to edit. |
| Administrator / System Manager — Maintain setup | Existing System setup tabs; focused tasks for entity/approval route, responsibilities, intake, funding sources, rules and schedule profiles. **Save changes**; affected-action explanation before saving. | Direct maintenance under CFG/AUTH permissions; no setup approval workflow. Source verification requires evidence, not a green-status toggle. Historical rule versions remain immutable. Reminder configuration is future-only under §15.3 and has no MVP control. |
| System Manager / authorised technical operator — Recover publication | Same publication record as U13, with the permitted recovery action for its actual state: **Retry publication** or **Check publication result**. | Technical commands retry the same approved content or read/reconcile an existing attempt. They do not edit the plan, bypass checks or supply business approval. Technical read access alone does not grant retry authority. |

Use only actual authorised person names returned by AUTH/task ownership. Where no person can be resolved, show the responsible role and a configuration issue; never invent an assignee. Multiple responsibilities appear together without a role selector; the command still checks incompatible prior actions. Board/Council are alternative collective routes, not member-by-member voting stages. Audit and technical readers have no business decision controls.

## 7. Service, command and cross-module contracts

### 7.1 Common envelope and reads

Each mutating request carries `{aggregate_id, expected_version, idempotency_key, payload}`. The server derives actor, site and AUTH assignment, never trusts supplied actor/capacity or task visibility. The relevant aggregate/task token and exact business Version are both checked inside the transaction. A matching replay returns the original result; reused key with different payload is rejected. Creation serializes on the natural root key. Protected reads return one typed authorization verdict with data; masked records disclose no existence. Financial year is a filter/operation input, never a permission grant.

| Read contract | Inputs beyond authenticated context | Exact result / consumer |
|---|---|---|
| ResolvePlanningContext | Optional FY/department filters | One site, current responsibility-bound OU scopes, configured FY options and verdict; no PE selection or stored user authority |
| GetPlanningWorkspace | FY and allowed department filter | Independent Active/candidate links, actionable work, departmental status and eligible/pending sources; same predicate for counts/rows |
| GetDepartmentalPlan / GetDppEntryEditor | Exact root/Submission/entry identity | Six source facts, dispositions, source-cohort coverage, funding eligibility, accepted/current pointers and authorized commands |
| GetDPPValidationTask | Task ID | Exact full certified snapshot, selected requirement types, server-derived categories, non-proceeding evidence and positive/return guards |
| GetAcceptedDPPClassification | Accepted submission/entry ID | Original acceptance classification, ordered correction history, current effective type/category, affected allocations and exact permitted correction/recovery action |
| GetAnnualPlan / GetPlanItem | Stable ID plus exact Plan Version or item-version ID | Complete §4 content, sources, funding history/current validity, readiness, changes and decisions; never silently switch to latest |
| GetPlanGovernanceTask / GetPlanReviewPack | Exact task/Version ID | One complete protected review snapshot and evidence index; same field coverage in screen/export; status-labelled unapproved pack |
| GetSourceEvidence | Exact DPP submission/entry and optional Need revision, parent Plan Version | Source facts, Budget allocation, certification/acceptance and reviewed Strategy lineage; preserve caller return context |
| GetFinanceTask | Task ID or Active Version reassessment context | Whole-plan exact financial basis, as-at statement, approved/available distinction and immutable history |
| GetPublicationTask | Publication/Version ID | Approved package, Treasury history, attempts, confirmed/unknown result, hold/withdrawal/activation outcome and allowed recovery actions |
| GetRequisitionEligiblePlanItem.v2 | Stable item ID and requesting record/OU context | Eligible or specific blocked result; exact §4 lineage, all contributing OUs, strategy/path, category/type/method/designation/structure, source facts, baseline dates, approved/drawn/remaining amounts, current funding, holds and evaluation instant |
| GetRegulatoryReference | Reference kind, FY, method/category and rule-specific applicability inputs | CFG-owned exact Version, effective interval, applicability basis, verification state, limits/conditions/counting; not a blanket FY-only lookup |

### 7.2 Command catalogue

All commands inherit §7.1, field rules in §4, state rules in §5, and segregation in §6. Returns use corrective predicates and must remain available when stale evidence prevents a positive decision. A command returns the common committed result and the specific evidence/objects listed below. Input fields not on the allow-list are rejected, not silently accepted.

| Command / actor | Payload and allowed state | Atomic effect and guards |
|---|---|---|
| OpenDepartmentalPlan — Author/HoD | FY, OU; permitted initial intake or existing authorized Draft | Create/reuse unique root/Draft; reopening withdrawn initial creates next number while intake open |
| SaveNeedFunding — Author/HoD | Draft entry ID, Budget Line, indicative_amount | Change only funding; source facts protected; reject not-proceeding funding mutation until restore |
| SetNeedPlanningDisposition — Author/HoD | Draft Need entry ID; Do not proceed + 20–500 reason, or Restore | Set reason and clear operative funding, or restore and require fresh completion; audit; no accepted event before DPP acceptance |
| SaveDirectRequirement — Author/HoD | Draft entry/new direct source; six facts, Budget Line, indicative_amount | Generate stable direct_source_id on first creation only; validate selectable UOM/date/funding |
| RemoveDirectRequirement — Author/HoD | Current Draft direct entry ID | Remove unsubmitted direct entry only; no upstream Need or financial mutation |
| CreateDepartmentalPlanUpdate — Author/HoD | Accepted DPP ID | One copied Draft; admitted changed/new Needs and direct requirements; accepted pointer retained |
| WithdrawDepartmentalSubmission — HoD | Mutable candidate ID, reason | Withdraw candidate without downstream consumption; accepted predecessor retained; submitted evidence never reopened |
| SubmitDepartmentalPlan — HoD | Draft Submission ID; certification acknowledgement | Recheck applicable cohort/window/coverage, full quantities, proceeding funding and authority; freeze snapshot; create validation task |
| ReturnDepartmentalPlan — Planner | Open task; one or more exact entry/whole-submission targets and single correction_required comments under §4.4 | Preserve reviewed submission; record decision and create next Draft correction in same cohort |
| AcceptDepartmentalPlan — Planner | Open task; one governed requirement_type_id for each proceeding entry | Derive/validate category server-side; recheck source validity and segregation; accept complete submission including exclusions; atomically create/reuse initial APP and source projections |
| CorrectAcceptedRequirementClassification — Planner | Accepted proceeding entry, expected classification evidence head, new requirement_type_id, reason 20–500 characters | Derive category from governed catalogue; append immutable correction; update only the effective classification projection; mark an unlocked mutable item Source correction required, identify the required Plan successor where eligible, or hold and identify the downstream owner route when scope-locked; never alter source facts, any existing Plan Version or procurement record |
| FormPlanItems — Planner | Draft Version, selected exact accepted entry IDs; Separate or Combined; aggregation reason when combined | Allocate each admitted source once/full; compatibility and source/scope-lock guards; no Budget mutation |
| DissolvePlanItem — Planner | Mutable exact item-version ID | Preserve item/history, mark allocations Released, recompute financial basis/open review; no reservation release |
| SavePlanItem — Planner | Draft exact item-version; §4.6 editable fields only | Resolve profiles and recompute schedule/readiness; no source/quantity/value override; enforce permanent scope guard |
| SavePlanVersionDetails — Planner | Draft Version; optional project_name, required successor change_reason | Whole-Plan fields only; no per-item project or new Project record |
| ConfirmSplittingAdvisory — Planner | Draft Version; current related-item/rule finding; reasoned response | Retain assessment evidence; mandatory method rules remain blocking; stale finding rejected |
| RequestPlanFundingConfirmation — Planner | Draft or exact unchanged Active Version; expected financial basis references | Pre-Finance readiness for Draft; whole-plan review/reassessment; at most one open task; explicit reuse/cancellation history |
| RequestBudgetRevision — Planner (v1.27) | Draft Version; exact Budget Line ID; expected financial basis references | Allowed only while that line's planned total exceeds its approved amount (`PLN_BUDGET_REVISION_NOT_REQUIRED` otherwise) and no Open request exists for the same Version and line (`PLN_BUDGET_REVISION_ALREADY_REQUESTED`). Creates one BudgetRevisionRequest (§4.7) and calls BUD `ReceiveBudgetRevisionRequest` (§7.3) in one transaction; the line, approved, planned and over amounts are server-derived, never supplied. No Budget change, reservation or Plan state change. The Planner's next step becomes Waiting on the Budget Officer. If the line later fits because the Planner reduced the plan, the Planner may withdraw the Open request through BUD's withdrawal contract; the outcome event records Withdrawn |
| ConfirmPlanFunding — Finance | Open task, expected basis ID | BUD decision-time validation; immutable whole-plan confirmation; no Budget financial record; Plan lifecycle unchanged |
| ReturnFromFinance — Finance | Open task; actionable reason | Immutable return; Draft remains Draft; Active reassessment does not reopen Active content |
| SubmitConsolidatedPlan — HOPF | Ready Draft; exact complete snapshot confirmation | **Sign and submit Annual Plan**; preparation signature, content lock and AO task; no extra HOPF approval state |
| AdoptAndSubmitPlan — AO | Open AO task; late-initial explanation if FY already begun | Adopt exact reviewed Version; recheck positive predicates; create one configured statutory task |
| ApproveAnnualPlan — statutory capacity | Open statutory task; collective resolution for Board/Council | Positive checks, matching STR snapshot, immutable approved content and durable publication intent; no synchronous external send |
| ReturnPlanVersion — current governance actor | Open task; actionable reason; optional exact affected_item_version_id in reviewed Plan; required collective resolution where applicable | Preserve returned evidence, create numbered correction Draft and incompatible-action chain; full resubmission restarts at AO after HOPF signature |
| SubmitCorrectedPlan — HOPF | Ready correction Draft | Same final-submission service/guards as SubmitConsolidatedPlan, including Finance basis evaluation and new preparation signature; no governance bypass |
| BeginPlanUpdate — Planner | Current Active Version; change_reason | Create sole ordinary successor; preserve Active pointer and balances |
| BeginHeldPlanCorrection — Planner | Published—activation-held origin; current actual Active predecessor if any; reason | One linked Draft correction; hold origin never treated as Active; fixed correction cohort |
| RemovePlanItemInSuccessor — Planner | Draft successor item ID; reason | Proposed whole-item exclusion only after current downstream-use checks; no consumed source/funding identity erasure |
| CancelPlanUpdate — Planner | Draft update/correction chain; reason | Cancel candidate chain; prior Active and all reservations unchanged |
| AuthoriseRequisitionDrawdown — REQ service | REQ/Version, exact eligible Plan/item/allocation IDs, positive per-source quantity/value; transaction correlation | Serialize item, holds, balances and activation; atomically authorize REQ + drawdown + BUD reservation through owners; first authorization permanently fixes scope |
| ReverseRequisitionDrawdown — REQ service | Original drawdown ID, permitted reversal quantities/amounts, REQ reversal evidence | Exact unused/unreversed capacity only; coordinate Budget reversal through REQ; preserve first authorization and issued history |
| ReceivePlanItemCorrectionRequest — REQ service | Request envelope in §4.8 | Idempotently record and hold item authorizations atomically; no change to existing authorizations/Tenders |
| StartPlanItemCorrection — Planner | Open request ID | In progress; hold remains; route edits to actual source owner |
| ResolvePlanItemCorrectionRequest — Planner | Request ID, correcting Active Version and replacement lineage | Immutable resolution and neutral REQ notification; no release against Draft; recompute aggregate hold |
| ClosePlanItemCorrectionWithoutChange — Planner | Request ID, required reason | Immutable no-change outcome, REQ notification and hold recomputation; no automatic restart |
| RecordTenderMilestoneActual — authenticated event owner | §4.8 event envelope | Validate exact proceeding/coverage, ordering and correction lineage; invitation event integration; no user-entered actuals |
| RecordTreasurySubmission — AO | Exact approved Version; §4.9 evidence and document confirmation | Append evidence; validate own Version/document; release transmission prerequisite only if current/valid |
| CorrectTreasurySubmissionEvidence — AO | Prior evidence ID; corrected evidence; reason | Append superseding record; preserve old; hold/reconcile any affected in-flight publication |
| HoldPlanPublication — system on invalidity / AO correction request | Exact publication, reason/evidence | Hold new dispatch; preserve in-flight uncertainty; no withdrawal of approval |
| RequestPlanWithdrawal — AO | Confirmed-unpublished approved Version; reason | Record request to exact statutory authority; no outstanding transmission; content locked |
| WithdrawApprovedPlanForCorrection — statutory authority | Valid AO request; resolution reference when collective | Confirm still unpublished/no outstanding attempt; retain approval/withdrawal and create one copied correction Draft |
| PublishAnnualPlan — system worker | Durable publication ID | Post-commit only; Treasury/hold checks; send exact immutable manifest under stable deduplication identity; record attempt |
| ReconcilePublication — system / technical System Manager | Existing attempt/publication ID | Read authoritative destination result; never set success manually; unknown remains held |
| RetryPublication — system / technical System Manager | Confirmed safely retryable publication ID | Same frozen files/identity; indeterminate must reconcile first; no business approval or payload edit |
| ReceivePublicationAcknowledgement / ActivatePlanVersion — system | Exact signed/validated acknowledgement and current aggregate tokens | Preserve publication even on invalid activation; activation checks all sources/basis/locks/allowances/predecessor; switch once or Published—activation held |
| RecordLateActivationExplanation — AO | Initial late Version; explanation; prior explanation reference if correcting | Append accountability; never falsify instant, block acknowledgement or rewrite published content |

### 7.3 Coordinated integration payloads and ownership

These are required matching owner contracts, not claims that uninspected providers already implement them. Shared writes participate in a single supported transaction/serialization contract; if infrastructure cannot guarantee the stated atomicity, integration remains blocked until a coordinated design is adopted. A read-only display check is never a substitute.

| Provider/contract | Request / event fields | Required result and boundary |
|---|---|---|
| NDS DepartmentalNeedAccepted.v2 | Existing event ID/ordering and Need/FY/OU; **accepted_version_id**, **version_number**; six facts | Map unchanged wire keys to internal revision identity; opaque generated -V identifiers unchanged; deduplicate |
| NDS DepartmentalNeedAccepted.v3 (v1.30; required NDS-CHG-001 v1.17 §7.1A) | The `.v2` fields plus `estimated_total_cost`, a decimal string in the Budget currency of the Need's Fiscal Year, or null | Planning consumes `.v3` after the coordinated cutover that withdraws `.v2`, and applies the §4.3 prefill and change rules. A null value prefills nothing. Wire keys and identifiers are unchanged. The superseded-Need event's embedded payload follows (NDS-CHG-001 v1.17 §7.1A) |
| PLN NeedPlanningDispositionChanged.v1 → NDS | event_id, schema_version, producer_sequence, need_id, need_revision_id, dpp_submission_id, disposition, reason when excluded, actor, decision_at | Emit after accepted DPP disposition only; separate from Active usage and Need lifecycle |
| PLN NeedPlanningUsageChanged.v1 → NDS | Existing agreed Active inclusion envelope with exact activated allocation/reversal lineage | Preserve Fully included/Not included semantics; a DPP exclusion cannot clear an existing Active dependency |
| BUD eligible-line resolver | FY, source OU, currency/source context | Exact eligible line identities and authoritative revisions; OU is record eligibility, not user FY authority |
| BUD check_plan_affordability | FY, exact per-line planned Money totals | Non-mutating, non-locking current display statement; approved versus available distinguished |
| BUD validate_plan_affordability_for_decision | Transaction context; FY; per-line totals/currency; expected Budget/line revisions | BUD serializes authoritative basis; returns immutable comparison statement or stale failure; no reservation/ledger write |
| PLN reservation-measure resolver | Exact current Plan Version; exact obligation/rule Version; every current Plan Item value and applicability facts | Eligible current APP value, included/excluded item evidence, required/qualifying/remaining planned allocation and calculation snapshot. Budget supplies Money and affordability facts only; unused headroom is never included |
| STR objective selection and approval snapshot | FY/Plan period, objective ID, reviewed Strategy Version/path, exact Plan Version/item ID and idempotency identity | Current eligible choice for reads; deterministic final-approval snapshot matching reviewed lineage or atomic failure |
| REQ drawdown/reversal and correction response | Exact envelopes in §§4.8/7.2; stable and exact identities distinct | One-open rule per stable item; no automatic stopped-Version resurrection; owner amendment defines fresh Draft follow-up |
| TPR/TPUB invitation actual | Authoritative tender publication event, exact proceeding/REQ/Plan/allocation coverage, actual date and ordered correction fields | Existing invitation path recognized; additional milestone owners must implement their own contract later |
| CFG profile resolver | Rule kind, method/procedure/category, FY and legally applicable date/facts | Immutable selected Version, effective interval, conditions, limits, counting, internal assumptions and legal verification; ambiguity/gaps block |
| Publication adapter | Stable publication identity, exact approved snapshot/manifest, destination; reconciliation by same identity | Exact manifest/hash-bound authoritative acknowledgement, confirmed failure or unknown; no guessed success |
| BUD ReceiveBudgetRevisionRequest (v1.27; required BUD-CHG-001 correction) | Planning request ID, idempotency key, FY, exact Budget Line and revision, approved, planned and over Money amounts, Plan Version reference, requesting actor | BUD records the request and creates the Budget Officer's My Work item for a Budget revision under BUD's own revision and approval rules. Returns the BUD request reference. Planning never changes a Budget amount |
| BUD BudgetRevisionRequestOutcome.v1 → PLN (v1.27; required BUD-CHG-001 correction) | Planning request ID, BUD request reference, outcome Revised / Declined / Withdrawn, resulting Budget Line revision when Revised, decision actor and instant, ordering identity | Planning updates the BudgetRevisionRequest status idempotently and recomputes readiness and the next-step answer; no Planning decision is inferred from the outcome |
| PLN need position → NDS `project_need_planning_intake` (v1.28; NDS-CHG-001 v1.15 §8.2) | need_id, need_revision_id, position (No update needed / Update required / After current submission), departmental plan reference, carried revision when Update required, source event ID and time | Published per §5.1.2 after every departmental-plan command and every Need acceptance, and skipped unless Departmental Needs confirms the revision is the Need's current accepted revision. NDS stores it read-only; no Need lifecycle, usage or disposition change. Departmental Needs never reads Planning's records. |

### 7.4 Strategy timing and unchanged event naming

The Draft stores the selected Objective identity and its resolved Strategy version. The submitted Plan stores the exact title/path that governance actors reviewed. At final statutory approval, call STR `create_strategy_snapshot` with the consumer record/version, Objective, expected status and approval correlation. Store its deterministic returned lineage only if it agrees with the reviewed selection and remains eligible. Otherwise fail the positive approval atomically and allow return for correction.

The snapshot call belongs to final Plan approval, not item formation, Finance confirmation, AO adoption or publication retry. It must not append duplicate Strategy snapshot evidence on retry. An Active Plan retains its approved lineage when Strategy later changes. A new or corrected selection must use the current eligible Strategy version; a copied successor must explicitly validate the eligibility rule applicable to every item before new approval.

NDS v1.14 retains `accepted_version_id` and `version_number` in `DepartmentalNeedAccepted.v2`. Planning maps those wire keys to its internal Need-revision fields and shows **Revision** to the user. Do not rename wire keys or generated `-V{nnn}` references merely because the display counter changed.

REQ owns one open Requisition per stable `plan_item_id`, not per department. Planning must use that same rule and the producer's documented drawdown command name. REQ calls `AuthoriseRequisitionDrawdown`; the predecessor lists `RecordRequisitionDrawdown`. The canonical command is AuthoriseRequisitionDrawdown in §7.2; no compatibility alias is retained.

### 7.5 No MVP forecast or milestone-notification service

The MVP registers no `PreviewForecastCascade`, `ConfirmForecastCascade` or `CheckApproachingMilestones` service and no forecast/reminder scheduler job. Existing tested implementation may remain dormant, but it must not be routed, scheduled, invoked by setup, or treated as release scope. A greenfield implementation does not create it. Command-time intake closure remains independent of the ordinary hourly cleanup scheduler.

### 7.6 Readable presentation and retained wire contracts

User labels in §§8–10 do not rename command IDs, event enums, status values, generated references or historical attestations. Read projections provide the exact record, allowed command, authorised destination and relevant reason; UI copy cannot invent the next actor or a successful state. A business action invokes its existing owner command once. Pages, tabs, disclosures and evidence downloads create no business record.

For new departmental returns, use the single-comment contract in §4.4. For whole-Plan returns, the existing actionable `reason` is the same **What needs to change?** input. Optional affected-item context is an explicit nullable exact item-version reference in the same reviewed Plan; it does not create item-level approval or partially return the Plan. Validate it server-side; freeze it with the decision. If old wire/storage has no such field, add it through an inspected versioned migration; never encode a selectable item as an unvalidated free-text identifier. Finance returns remain whole-plan decisions with one actionable reason. A comment may name an affected line from the reviewed statement without introducing an additional required selector or new Finance approval scope.

The accepted NDS disposition contract matches approved NDS v1.14: schema_version is integer 1; producer_sequence is allocated transactionally per stable Need’s disposition stream; disposition is exactly `Proceeding` or `Not proceeding this financial year`. Reason is null for Proceeding or 20–500 characters for exclusion. Actor is the Procurement acceptance actor; decision_at is its UTC instant. Emit one event per Need-origin entry after complete DPP acceptance, including restored/unchanged proceeding entries with their current accepted Submission provenance; no direct-entry event. Retries reuse exact event IDs. Disposition and usage have independent ordering/replay; unknown versions, gaps and unknown source revisions reconcile without synthetic records. User-facing Include/Exclude labels do not change these enums or make Draft work an accepted disposition.

CFG v0.13 owns the native UOM selectable/precision adapter, date-sensitive rule resolver and reservation-measure definitions. Never assume a UOM `enabled` database column. BUD v1.10 owns exact currency metadata, Budget ceilings and decision-time affordability (v1.26 read: BUD v1.9); it does not supply unused headroom as the 30% Planning denominator. Source, Budget and responsibility reads use owner services with matching scope. Documentation approval does not establish repository compatibility.


### 7.7 Hand-off register — v1.27

Each row is one KT-STD-001 v1.8 §3B.4 hand-off. The My Work item is created in the same transaction as the event and clears only on the stated state change, never on view. **Notification:** none from Planning in any row. PLN23-AC-001 excludes a Planning notification producer from the MVP, so the My Work item is the hand-off. A later notification facility requires its own approval.

| Event | Next holder | Their My Work item | Sender's waiting-on item | Clears when |
|---|---|---|---|---|
| SubmitDepartmentalPlan | Procurement Planner | Review {department}'s departmental plan | Head of User Department: Waiting for Procurement review | Accepted, returned or withdrawn |
| ReturnDepartmentalPlan | Head of User Department and Departmental Author for that department | Correct and resubmit {department}'s departmental plan, with the return comment | None | Resubmitted or withdrawn |
| AcceptDepartmentalPlan | Procurement Planner | Add accepted requirements to the annual plan | Head of User Department: Waiting for planning | Every proceeding source is allocated in the current Draft or becomes a pending input to a later update (§5.4.3) |
| A Need enters *Update required* (§5.1.2) (v1.28) | Departmental Author and Head of User Department for that department | **Update {department} departmental plan**, stage **{need list} not in plan**, action **Create update** | Procurement Planner: none; the U01 register status reads **Accepted · {n} accepted need(s) not in plan** | An update that carries the Need is created, or the Need leaves the department's current accepted sources |
| RequestBudgetRevision | Budget Officer (BUD-owned item) | Revise {line name} for the plan update, with the over amount | Procurement Planner: Waiting for {name} (Budget Officer) to revise the budget line | BudgetRevisionRequestOutcome received |
| BudgetRevisionRequestOutcome, Revised or Declined | Procurement Planner | Continue plan update, with the outcome | None | Funding confirmation requested, or the update is cancelled |
| RequestPlanFundingConfirmation | Finance Confirmation Officer | Confirm funding for {plan} Version {n} | Procurement Planner: Waiting for Finance | Confirmed, returned, or cancelled by a financial-basis change (§5.3.2) |
| ReturnFromFinance | Procurement Planner | Correct the plan returned by Finance, with the reason | None | Funding confirmation requested again, or the update is cancelled |
| ConfirmPlanFunding | Head of Procurement Function | Sign and submit the annual plan | Procurement Planner: Waiting for signature | Signed, or the confirmation becomes Stale |
| SubmitConsolidatedPlan / SubmitCorrectedPlan | Accounting Officer | Adopt the annual plan | Head of Procurement Function and Planner: Waiting for adoption | Adopted or returned |
| AdoptAndSubmitPlan | Configured statutory authority (§6.1) | Approve the annual plan, or record the Board or Council decision | Accounting Officer: Waiting for approval | Approved or returned |
| ReturnPlanVersion (AO or statutory) | Procurement Planner | Correct the returned plan, with the comment | None | Correction submitted or cancelled |
| ApproveAnnualPlan with Treasury evidence missing | Accounting Officer | Record the Treasury submission | None | Valid evidence recorded |
| Publication failed or indeterminate | Authorised technical operator | Retry publication / Check publication result | Accounting Officer: Waiting on publication recovery | Acknowledgement or confirmed result reconciled |
| Material defect hold, confirmed unpublished | Accounting Officer | Request withdrawal for correction | None | Request recorded or hold released |
| RequestPlanWithdrawal | Configured statutory authority | Decide the withdrawal request | Accounting Officer: Waiting for the withdrawal decision | Withdrawn |
| WithdrawApprovedPlanForCorrection | Procurement Planner | Continue the correction | None | Correction submitted or cancelled |
| Published — activation held | Procurement Planner | Prepare a corrected plan | None | Correction Draft created |
| ReceivePlanItemCorrectionRequest | Procurement Planner | Resolve the planning change for {purchase} | REQ-owned waiting item | Resolved or closed without change |
| ActivatePlanVersion | Requisition raisers for its items (REQ-owned item) | Purchase ready for requisition | None | Defined by REQ-CHG-001 (required correction) |

Returns are separate rows and carry the returner's comment. A Revised budget outcome does not itself move the Plan: the Planner's next step is recomputed, and it becomes Your turn only if every line then fits.

## 8. Error contract

Return `{code, message, field_errors, affected_record_ids, expected/current token when safe, support_reference}`. Only authorized identifiers/data may appear. Page-load authorization/configuration failures are typed inline states, not stock framework modals. Corrective commands use their own predicates. Profile-specific numeric facts appear as labelled parameters, never universal guessed constants.

| Code | User-facing message |
|---|---|
| PLN_NO_CONTEXT | Procurement Planning is not available for your responsibilities or the current setup. |
| PLN_WINDOW_CLOSED | Initial departmental-plan submissions are closed. |
| PLN_NEED_COVERAGE_INCOMPLETE | Include each required departmental need or record why it is not included this year. |
| PLN_ENTRY_INCOMPLETE | Complete the highlighted requirement fields before submitting. |
| PLN_BUDGET_LINE_INELIGIBLE | Choose a budget line available to this department for this financial year. |
| PLN_DPP_STALE | This departmental plan has changed. Refresh before continuing. |
| PLN_CLASSIFICATION_INCOMPLETE | Choose a requirement type for each included requirement. |
| PLN_CLASSIFICATION_UNCHANGED | Choose a different requirement type to correct this classification. |
| PLN_CLASSIFICATION_CORRECTION_STALE | This classification was already corrected. Refresh before continuing. |
| PLN_CLASSIFICATION_CORRECTION_BLOCKED | This classification cannot be corrected through this action. Follow the source, plan or procurement correction shown. |
| PLN_SOURCE_UNAVAILABLE | One or more selected requirements are no longer available to add. |
| PLN_SOURCE_INCOMPATIBLE | These requirements cannot be combined. Add them as separate purchases. |
| PLN_SOURCE_CORRECTION_REQUIRED | A departmental requirement has changed. Review the change before rebuilding the affected draft purchase. |
| PLN_CORRECTION_COHORT_VIOLATION | This requirement belongs in a later update. It cannot be added to the current correction. |
| PLN_DISSOLUTION_BLOCKED | This item can no longer be removed from the draft. |
| PLN_OBJECTIVE_INELIGIBLE | Choose a strategic objective currently available for this plan. |
| PLN_STRATEGY_REVIEW_CHANGED | The selected strategy has changed since submission. Return the plan for correction. |
| PLN_SCHEDULE_INVALID | Review the highlighted dates and the rule shown for them. |
| PLN_PROFILE_PERIOD_INVALID | The highlighted period does not meet the procurement rule shown. |
| PLN_DELIVERY_BOUNDARY_INSUFFICIENT | Estimated completion is after the department’s required date. Review the schedule or request a departmental correction. |
| PLN_DELIVERY_PERIOD_REQUIRED | Enter the estimated delivery or implementation period in calendar days. |
| PLN_MULTI_YEAR_UNSUPPORTED | Multi-year procurement is not supported in this release. |
| PLN_BASELINE_LOCKED | This submitted plan cannot be edited. Use the available correction or update action. |
| PLN_ACTUAL_NOT_WRITABLE | Actual dates must come from the process that recorded the event. |
| PLN_PLAN_NOT_AFFORDABLE | The planned amount exceeds the approved budget on the lines shown. |
| PLN_BUDGET_REVISION_NOT_REQUIRED | This budget line is within its approved amount. No budget revision is needed. |
| PLN_BUDGET_REVISION_ALREADY_REQUESTED | A budget revision has already been requested for this line. |
| PLN_FINANCE_STALE | Funding needs to be checked again. Follow the action shown for this plan. |
| PLN_REVIEW_STALE | This review has changed. Refresh before deciding. |
| PLN_SEGREGATION_CONFLICT | You cannot make this decision because of your earlier role in this plan. An authorised, independent decision-maker is required. |
| PLN_STATUTORY_ROUTE_UNCONFIGURED | The plan’s approving authority is not configured. A KenTender administrator must complete this setting. |
| PLN_COLLECTIVE_RESOLUTION_REQUIRED | Enter the Board or Council resolution reference for this decision. |
| PLN_PLAN_CONTENTS_INCOMPLETE | Complete the highlighted purchase details and required evidence. |
| PLN_METHOD_NOT_ADMISSIBLE | The selected method does not meet the applicable procurement conditions. |
| PLN_METHOD_EVIDENCE_REQUIRED | Provide the evidence required for the selected procurement method. |
| PLN_RESERVATION_REQUIRED | Choose who this procurement is reserved for, or None if no designation applies. |
| PLN_RESERVATION_SHORTFALL | Reserved procurement is below the required amount. Review the shortfall shown. |
| PLN_REFERENCE_UNAVAILABLE | A required procurement rule or calculation basis is missing or unverified. The setting shown needs attention. |
| PLN_MONEY_PRECISION_INVALID | Enter the amount using the decimal places allowed for this currency. |
| PLN_ITEM_SCOPE_LOCKED | This item already has an authorised requisition. Add extra requirements as a separate item in a plan update. |
| PLN_ITEM_AUTHORISATION_HELD | New requisition authorisations are on hold for this item until its correction requests are resolved. |
| PLN_CORRECTION_NOT_ACTIVE | Record completion only after the corrected plan becomes the current plan. |
| PLN_REMOVAL_BLOCKED | This item is already used in procurement and cannot be removed through Planning. |
| PLN_ALLOWANCE_EXCEEDED | The requested quantity or amount exceeds what remains under the original plan item. |
| PLN_TREASURY_EVIDENCE_REQUIRED | Record evidence that this approved plan was sent to Treasury before website publication. |
| PLN_PUBLICATION_FAILED | The plan was not published. The approved document is unchanged. |
| PLN_PUBLICATION_UNKNOWN | We could not confirm whether publication succeeded. Check the existing attempt before trying again. |
| PLN_PUBLICATION_HELD | Publication is on hold. Review the issue shown. |
| PLN_PUBLICATION_ACK_MISMATCH | The publication confirmation does not match this approved plan. |
| PLN_WITHDRAWAL_NOT_PERMITTED | Withdrawal requires confirmation that the plan was not published and that no publication attempt is still pending. |
| PLN_ACTIVATION_HELD | The plan was published, but it is not available for new procurement. The issues shown must be corrected. |
| PLN_LATE_EXPLANATION_REQUIRED | Explain why this initial plan is being adopted after the financial year started. |
| PLN_STALE_WRITE | This record changed after you opened it. Refresh before continuing. |
| PLN_IDEMPOTENCY_CONFLICT | This action could not be processed. Refresh before trying again; contact support if the problem continues. |

PLN_RESERVATION_RELEASE_FAILED is removed. Fixed seven-day/thirty-day/fourteen-day timing errors are replaced by PLN_PROFILE_PERIOD_INVALID with the actual resolved rule details. An unknown publication result is never presented as confirmed failure. Unavailable detail records use the same masked Not available response whether absent or unauthorized.

User text is the presentation contract; existing machine codes remain stable. Field errors additionally identify the exact permitted field/row and required action. Amounts, dates and reasons are separately labelled, not embedded in a long unstructured paragraph. A read-only viewer sees the responsible role rather than an edit instruction they cannot perform. Consumer screens must adopt the changed scope/hold wording while retaining the existing codes; no change to enforcement semantics is implied. Prior recorded messages are history.

## 9. UI architecture, navigation and presentation

### 9.1 User-task structure

The interface starts with the person’s work, not the domain record hierarchy. Use the existing Planning workspace and exact-record routes. Assigned reviews open directly on the reviewed document, without a dashboard, version selector or readiness screen as an intermediate step. Browser navigation is read-only. Use one coherent review page with accessible supporting detail; no mandatory sequence of evidence screens.

The workspace shows **Annual procurement plan**, relevant **Your actions**, and role-relevant departmental or preparation work. The current governing plan remains visible even when there are no tasks. Omit an empty Your actions section. For an initial plan, show **No current plan yet** and **Draft plan**. Where an update exists, show **Current plan** and **Plan update** as independent labelled rows. A task opens the exact version for that decision; a Current plan link resolves the actual Active pointer, not the highest version number.

Each action row states the required outcome, affected document/department, actual responsible person or role, and one main action. Show only relevant facts. Waiting work is status on its document, not a duplicate disabled task. Names precede codes; references and sequence numbers remain available as secondary labelled information. Do not require users to interpret root/candidate/revision relationships to locate editable work.

### 9.2 Canonical routes and action entry points

| Surface | Existing route family | Business actions / navigation |
|---|---|---|
| U01 workspace | /app/procurement-planning | Explicit Start departmental plan or Prepare plan update; reads/filtering create nothing |
| U02–U05 departmental plan | Existing DPP record and entry routes | Working plan with inline funding, direct-entry form and same-page HoD certification; history opens exact submissions |
| U06 departmental review | /app/procurement-planning/dpp-review/{task_id}; accepted evidence through the existing DPP history route | Accept departmental plan / Return to department; accepted proceeding rows permit Correct classification under §5.1.6 |
| U07/U08 preparation | /app/annual-procurement-plan/{plan_reference} with exact Version | Add selected requirements within plan; funding request, permitted update/cancellation |
| U09 purchase editor | /app/procurement-plan-item/{plan_item_id} with exact item/Plan Version | Edit permissible purchase facts; no editable inherited scope |
| U10 Finance | /app/procurement-planning/finance/{task_id} | Whole-plan confirmation/return/reassessment |
| U11 governance review | /app/procurement-planning/review/{task_id}; exact Plan read route for readers | Actor-specific signature/adoption/approval/return; shared complete content |
| U12 departmental evidence | Existing exact source evidence detail | Contextual read and Return to plan review; no new approval stage |
| U13 publication | /app/procurement-planning/publication/{publication_id} | AO submission evidence and eligible withdrawal request; authorised technical recovery |
| U14/U16 monitoring | Exact Plan/item/proceeding/correction context | Read authoritative progress and process Planning correction requests; no REQ/Tender creation. U15 forecasting is deferred |
| C01–C04 setup | /app/system-setup and existing local sections | CFG/AUTH-authorised maintenance; no Planning configuration registry |
| U21 shared states | Applicable requested route | Inline denied/masked/loading/error/changed-state response |

Concrete parameter names must match the inspected repository. There are no duplicate route aliases or new record types merely to implement a different composition. Existing entry/formation/certification routes may still resolve exact records but must support the same-page task presentation and preserve back context. Source navigation never silently changes the Plan being reviewed.

### 9.3 Supporting-detail readability contract

1. Present the actor's result or required decision first. Show evidence only after the result and explanation only when it helps the user act.
2. An ordinary page may have one dominant task, one visible issue summary and one primary action. Secondary actions must be genuinely secondary; history, export and evidence navigation never compete with the current decision.
3. Keep every material qualification, excess, unavailable mandatory evidence and blocked decision visible near the affected purchase or decision. Collapsing detail must not hide anything that changes the verdict.
4. Show a field only when the actor can change it, must decide from it, or needs it to understand a material consequence. Omit blank, None, Not applicable, default and single-value facts unless their absence itself matters.
5. Derived facts are read-only and visually secondary. Do not display calculation inputs repeatedly on every item when the decision is made once at annual-plan level.
6. Configuration and audit facts—rule versions, source checks, resolver status, internal submission numbers, event identifiers and fixture labels—stay in System setup, History or authorised technical detail. If configuration blocks work, replace that machinery with one plain-language issue and the responsible recovery action.
7. Long descriptions/reasons begin with a faithful short preview and an adjacent **Read full description** / **Read full reason** disclosure. The full governed text remains available and included in the review pack.
8. Use at most one disclosure level in ordinary work. Names lead; references, actor/time evidence and version provenance are secondary. Avoid horizontal navigation through evidence categories.
9. Establish contrast through heading weight, spacing, rules and restrained shading. Values are visually distinct from labels; warnings use explicit language, not colour alone.
10. Action areas do not obscure content or keyboard focus. Wide comparisons use a compact first view plus exact detail, never a dense grid of every stored attribute.

The rule for every proposed field is: **Why does this actor need this fact at this moment?** If the answer is storage, traceability, configuration or possible future use, it does not belong in the ordinary first view.

### 9.4 Visible language mapped to stable records

| Internal concept / condition | User-facing wording | Meaning that must remain clear |
|---|---|---|
| Active Plan | Current plan | The governing Active version, not merely approved or published |
| Initial candidate Draft | Draft plan | Still being prepared; cannot authorise procurement |
| Successor Draft | Plan update — Draft | Existing current plan remains in force |
| Candidate under governance | Awaiting Accounting Officer / Awaiting Cabinet Secretary (or actual configured body) | Actual stage and authority; no generic Candidate Version headline |
| Returned plus copied Draft | Changes requested / Continue correction | Opens the editable correction; reviewed version is in History |
| DPP accepted plus update | Accepted — update in progress | Earlier accepted submission remains separately accessible |
| DPPClassificationCorrection | Correct classification | Appends a Procurement-owned correction; it does not edit the accepted departmental plan or the purchase |
| Need exclusion | Not included this year | Departmental plan disposition, not a withdrawal of the Need or approved Annual Plan |
| Add/reverse exclusion | Exclude from this year’s departmental plan / Include in this year’s departmental plan | Explicit reason and renewed funding completion as applicable |
| DPP indicative_amount | Estimated cost (KES in fixture) | Full amount, not unit price; currency from Budget |
| source / source allocation | Departmental requirement / Departmental allocation | Exact underlying identities retained in detail and audit |
| FormPlanItems | Add selected requirements | Explicit allocation into draft plan; no procurement created |
| DissolvePlanItem | Remove item and return requirements | Only permitted Draft removal; no Budget release |
| Funding evidence stale | Funding needs to be checked again | Exact recovery depends on Draft/review/Active/publication state |
| Readiness finding | Concrete missing work or issue | “Choose a procurement method”, not “Complete readiness” |
| BeginHeldPlanCorrection | Prepare a corrected plan | New governed correction; no edit to published content |
| Final approval by authorised collective recorder | Record approval / Record return for correction | Body’s decision, not recorder’s personal approval |

Internal enums, API commands and opaque IDs remain as specified in §§4–7. The UI must not send the visible label as a replacement enum. Historical certifications and errors already recorded remain evidence, not text to bulk rewrite.

### 9.5 Complete review coverage

The screen can be concise without reducing the reviewed document. Each group has a named location below. Required evidence that cannot be loaded is visible as unavailable; it cannot be silently omitted to enable a decision. Screen and exported review pack cover the same exact content.

| Content | Full required evidence | Location |
|---|---|---|
| Proposed purchase | Full title/description, purpose from sources, type/category, full quantity/UOM, planned amount, estimate basis and incidental-cost statement | U09/U11 purchase summary and Cost estimate |
| Departmental requirements | Department; six source facts; full quantity/date/funding; exact Need revision or direct-source identity; DPP submission; certification, acceptance, original/effective classification with correction history, and exclusion history where applicable | U06 classification evidence, U11 allocations and U12 exact requirement |
| Strategy | Objective title/reference, complete reviewed path and exact Strategy version; approval snapshot where created | Purchase Strategy |
| Budget | Per-line planned and approved totals, source, current availability, currency, as-at statement, confirmation actor/time, current versus approval evidence | U10 / U11 Funding |
| Method | Selected method/procedure, complete conditions, rule version/source verification, known facts, necessary judgement/evidence and specific authorisation if required | Procurement method and conditions |
| Reservation / lots | Designation, restrictions, applicable county allocation, eligible current APP value, required/qualifying/remaining amount, exact rule and Plan Versions, aggregation reason, lotting/count, fixed Single year | Summary exceptions plus purchase Reservation and lots |
| Schedule | Approved milestone dates, source deadline, estimate, anchor/periods, rule counting/bounds and internal assumptions | Schedule; detailed periods remain accessible |
| Proposed update | Complete before/after field values and source change evidence; unchanged scope clearly identified | Changes, visible before decision when applicable |
| Accountability | Exact certification/signature/adoption/approval, capacity, actual actor and time; return reasons and collective resolution | Decision history and current decision |
| Progress / corrections | Exact proceeding coverage, owner-supplied operational dates where supported, separate scope restriction/hold and request outcomes | U14/U16; U15 deferred |
| Publication | Exact approved package, submission evidence, external result and activation separately | U13 |

### 9.6 Surface and variant inventory

U01–U16, C01–C04 and U21 remain the 21 catalogued surface families. They are not 21 steps. U15 is retained only as an explicitly deferred future family; every other applicable MVP variant below must be implemented and tested.

| Family | Required variants |
|---|---|
| U01 | No plan; draft; current only; current plus update; work waiting; assigned decision; no actionable work |
| U02–U05 | New/existing Draft; incomplete/complete; Author versus HoD; source/direct origin; exclusions; correction; accepted plus update; closed initial intake; withdrawal; authority change |
| U06 | Included/excluded requirements; type/category derivation; classification missing; accept; targeted/whole-plan return; stale source; separation-of-duty conflict; accepted classification; correction/history/stale attempt |
| U07/U08 | Unallocated/fully allocated; one or multiple selections; separate/combined; incompatible selection; pending unrelated requirements; update cancellation |
| U09 | Single/combined purchase; classification provenance; required condition evidence; missing profile; dates valid/invalid; lots; scope restriction; source correction; classification correction |
| U10 | Within approved; low availability; excess; stale task; return; repeat review; current-plan reassessment; immutable history |
| U11/U12 | HOPF; AO; individual/collective statutory authority; full reader; update/initial; source/historical detail; late initial adoption; return; unavailable evidence |
| U13 | Treasury evidence missing/recorded/corrected; sending; confirmed failure; unknown; published and Active; published but held; eligible withdrawal request/decision |
| U14/U16 | No proceeding; one/multiple/partial proceedings; owner-supplied actual evidence where supported; multiple requests and permitted outcomes. No U15 MVP artboard |
| C01–C04 | First-run/configured entity; intake changes; funding catalogues; versioned rules, source verification and schedule profiles; missing/unsupported configuration. No reminder configuration in MVP |
| U21 | Loading, empty, filtered-empty, denied, masked, load failure, changed record/authority, unsaved work, uncertain command result |

### 9.7 Workflow reduction and protected decisions

One assigned decision opens one coherent review. HoD certification remains on the complete departmental plan; no separate page is required merely to repeat it. One selected source goes directly through explicit Add selected requirements; multiple selection asks separate/combine only where meaningful. Returned work opens its correction directly; History preserves the original. Departmental funding edits stay beside the requirement. None of these reductions removes certification, signature, approval, applicable method judgement, return reasons or audit evidence.

There is no new Author handover approval, HoD return stage, HOPF approval or business Publish button. Actions that commit a decision have the consequence immediately beside them. Do not layer an unnecessary checkbox, confirmation modal and final click over the same statement. Retain the specifically required HoD certification and Treasury document-match acknowledgements.

### 9.8 Approval and evidence boundary

The Project Owner approved Planning Usability Blueprint v0.2, including all actors and structured supporting detail, on 13 September 2026. The earlier focused prototype established limited navigation and simulated decision behaviour only. It did not prove ordinary-user usability. This specification supplies complete implementable screen contracts; participant testing, accessibility, browser behaviour and release evidence remain required in §§14–15. Production uses the existing Frappe/Vue environment, not the prototype’s framework, role harness or client-only state.

## 10. Complete screen and static design contract

This is the complete Stage 2 Planning presentation input. Supply **KT-STD-001 v1.7 §2 plus this section only** to the design tool. **From v1.26, supply KT-STD-001 v1.8 §2 in place of v1.7 §2**; v1.8 retains all of v1.7 §2 and adds §2.9. Every reference to KT-STD-001 v1.7 in this section is read as v1.8 for design purposes. Section 11.9 remains the excluded functional action map. This rewrite changes presentation architecture only; it creates no field, state, responsibility, authority rule, command, service, event or approval stage.

### 10.1 Shared experience contract

Use the approved KenTender content area and Frappe shell. Apply KT-STD-001 v1.7's archetypes, structured density and visual hierarchy. Fixture actor, scope, time and scenario stay outside the artboard.

**Required archetypes.** U01 is a Work workspace. U02–U05, U07 and U09 are Forms/editors with subordinate summaries. U06, U10 and U11 are Reviews/decisions. U08 and focused confirmations are Dialogs/panels. U12 and U13 are Record details with state-specific actions. U14 is a monitoring Register/detail. U16 is a correction Work workspace/detail. C01–C04 are Setup owner surfaces. U21 supplies shared states. U15 remains deferred with no MVP artboard.

**Information priority.** Level 1 is the actor's required work, current plan/result, material blocker and lawful next action. Level 2 is the purchase, source, funding, schedule or governance evidence needed for the current task. Level 3 is exact lineage, rule provenance, calculations, immutable history and technical evidence. Complete evidence remains available, but only Level 1 and the task-relevant part of Level 2 lead the first view.

**Orientation.** Business names lead. References and Version evidence sit beneath or in a quiet orientation line. Group related context where meaning remains unambiguous; do not place Financial year, reference, Version and status into a large empty context box. Never repeat the same Plan facts in header, summary and table without a distinct task purpose.

**Component choice.** Use task rows for assigned actions, result blocks for current decision outcomes and tables only for genuine repeated comparison or registers. A small purchase or action set does not become a wide grid by default. Put filters with the records they filter. Use one disclosure depth for Level 3 evidence. A count or status summary orients; it never substitutes for complete review content.

**Material issues.** Budget excess, reservation shortfall, stale or unavailable mandatory evidence, deadline conflict, scope restriction and active procurement remain visible beside the affected task or purchase. Passing calculations and provenance move to supporting evidence when they do not change the current decision.

**Actions.** Each task region has one visually dominant action. Filters, History, export and evidence navigation do not compete with it. Consequences sit beside decisions. A blocked action includes its reason and recovery or is absent. Corrective, destructive and navigation actions remain visually distinct.

**Visual restraint.** Use typography, reading order, spacing and alignment before borders. Do not use nested cards, repeated full-width accent rules, equal-sized KPI tiles, uppercase section headings or apparent selected rows without an actual selection state. Preserve professional density and readable monetary alignment.

**Definite fixtures.** Every action below has one visible treatment in its named variant. A variant replaces only the stated base regions and retains the rest. No “when permitted”, “where relevant” or unresolved optional layout is delegated to the designer. Technical read follows KT-STD-001 v1.7 §3A.6.

### 10.1A Shared next-step and journey content — added in v1.26

This subsection supplies the content required by KT-STD-001 v1.8 §2.6.8 item 12 and §2.9 for every Planning record screen. It is presentation of existing states, actors and checks. It creates no state, stage, command, error code, permission or approval step. The per-screen **Next step and journey** paragraphs in §§10.3–10.17 apply it.

**Wording status.** Stage labels come from the §5.2.3 and §5.1.5 transitions and the §6.1 route capacities. Marker words and the Finance confirmation states come from KT-STD-001 v1.8 §2.9 and §5.2.2. Actors, times and figures come from §10.2 or the named variant. Headlines and fix labels in **bold** are new wording approved through this document; the designer does not write them.

**Design-readiness rule.** A variant marked **Pending D{n}** depends on a Project Owner decision in §10.1A.7, and a variant marked **Awaiting fixture** depends on an exact fixture value. Neither is sent to design until that input exists, consistent with §10.18.

#### 10.1A.1 Annual Plan journey tracker

One row with seven formal stages, in this order. Budget fit is a computed condition, not a stage (KT-STD-001 v1.8 §2.9.2).

| # | Stage label | Formal step (§5.2.3) | Holder when current |
|---|---|---|---|
| 1 | **Preparation** | Form, edit or dissolve Plan Items; request plan funding confirmation | Procurement Planner — Mercy Kilonzo |
| 2 | **Funding confirmation** | Confirm plan funding / Return to planner | Finance Confirmation Officer — Josphat Mwangi |
| 3 | **Signature** | Sign and submit Annual Plan | Head of Procurement Function — Charles Mutiso |
| 4 | **AO adoption** | Adopt and submit / Return for correction | Accounting Officer — Amina Hassan |
| 5 | **{Capacity} approval** | Approve Annual Procurement Plan / Return for correction | Configured statutory authority — Daniel Rotich in the Ministry fixture |
| 6 | **Publication** | Record Treasury submission; transmit and reconcile acknowledgement | As stated per U13 variant |
| 7 | **In force** | Activation (end state) | None |

- **Stage 5 always applies.** §6.1 requires exactly one configured statutory route and never permits none, so every Plan passes through stage 5. Its label follows the configured capacity: **Cabinet Secretary approval** (Ministry fixture), **County Executive Committee Member approval**, **Board decision** or **Council decision** (U11-COLLECTIVE).
- **Markers.** **Done**, **Current**, **Blocked** and **Not started**, each shown as text. Only the current stage names its holder. Accent on the current stage only; status colour only on Blocked and Done (KT-STD-001 v1.8 §2.9.3 rule 6).
- **Links.** Upstream link **{n} departmental requirements included**; BASE reads **3 departmental requirements included** and moves focus to Requirements ready to add. Downstream link **{n} requisitions raised**, shown only at In force; its count comes from U14 owner evidence.
- **Reduced form.** One line: **Stage {n} of 7: {label} — {holder}**, or **Stage 7 of 7: In force**. Required on U13 and wherever a variant says **reduced**.
- **Placement.** Directly below the page header and above the first working region; the tracker comes first, then the next-step block when drawn (KT-STD-001 v1.8 §2.9.3 rule 7).
- **Finance return.** The Plan stays Draft (§5.2.3). The tracker shows Preparation Current and Funding confirmation Not started. The return is stated by the Finance confirmation line (**Returned**) and in Changes and history.
- **Governance return and withdrawal.** The correction Draft's tracker restarts at Preparation Current. The returning stage is not marked; the return and its comment stay in Changes and history.

#### 10.1A.2 Departmental plan journey tracker

Four stages from §5.1.5, in order: **Preparation** (Departmental Author or Head of User Department), **Certification** (Head of User Department), **Procurement review** (Procurement Planner) and **Accepted**. Same markers, placement and reduced-form rules as §10.1A.1. No upstream or downstream link. **v1.28:** an accepted plan whose department still owes an update (§5.7) shows Preparation Current with the department as holder, not every stage Done.

#### 10.1A.3 Budget fit and Finance confirmation on U07

The U07 Plan checks entry **Funding: Not yet checked** is removed from every U07 variant (KT-STD-001 v1.8 §2.6.6 and §3B.3) and replaced by two separate facts:

1. **Budget fit, checked now.** The live comparison defined by §5.3.1, placed in the Plan checks working region. Columns Budget line; Approved; This plan; Difference. BASE rows: **Digital health infrastructure programme** (MOH-BL-DHI-2027) KES 100,000,000 / KES 80,000,000 / **Within by KES 20,000,000**; **Digital health workforce development** (MOH-BL-HWD-2027) KES 60,000,000 / KES 50,000,000 / **Within by KES 10,000,000**. When every line fits, show the result line **Within each approved budget line** with the table under **View budget lines**. When a line exceeds its approved amount, the table is open and that row reads **Over by KES {amount}**.
2. **Finance confirmation.** One labelled line using the §5.2.2 funding-evidence state names exactly: **Not requested**, **Awaiting confirmation**, **Confirmed**, **Returned** or **Stale**. Confirmed keeps the existing separately labelled Checked by and Checked at (U07-FINANCE-COMPLETE). Budget fit and Finance confirmation are never merged.

The approved Budget ceiling (KES 160,000,000) appears in neither, as in §5.5.3.1.

#### 10.1A.4 Screens that carry neither component

Stated under KT-STD-001 v1.8 §2.9.3 rule 4:

- **U01 Planning workspace** is a Work workspace. Its task rows keep their plain-language narrative, which states a blocked Plan's headline (§10.3).
- **U03, U04 and U08** are a funding panel, dialogs, a direct-requirement form and a focused panel.
- **U09 Purchase editor.** The purchase belongs to the Plan record; the Plan's next step is stated once, on U07. U09 keeps its own purchase-level issue line.
- **U12 departmental evidence** is a pinned evidence view with no lifecycle of its own.
- **U14 procurement progress** is a monitoring register.
- **U16 correction requests** is a correction workspace; each request keeps its own status text.
- **C01–C04** are setup owner surfaces. A Planning-side missing setting is a blocker in the host screen's next-step block (§10.1A.5), using the existing §10.16 panel content.
- **U21 dialogs and page states.** Loading, denied, masked and load-failure states replace protected content, including both components. U21-TECHNICAL-DETAIL follows §10.1A.6.

#### 10.1A.5 Blocker catalogue

Every blocker uses an existing §8 code; no code is added. Figures and fixes come from the guard (KT-STD-001 v1.8 §3B.1).

| Existing code (§8) | Blocks (current v1.25 rule) | Headline pattern | Fix controls and owner |
|---|---|---|---|
| `PLN_PLAN_NOT_AFFORDABLE` | Confirm plan funding and Sign and submit Annual Plan (§5.3.1). **v1.27 (D2): also Request plan funding confirmation** (§5.6 item 4). | **Over budget by KES {over} on {line name}** | **Request budget revision from {Budget Officer name}** (hand-off to Budget Officer; `RequestBudgetRevision`, §7.2, §7.7); **Reduce a purchase** (Procurement Planner; moves focus to Purchases) |
| `PLN_RESERVATION_SHORTFALL` | Sign and submit Annual Plan (§5.5.3.1). **v1.27 (D2): not the funding request**; §10.3 and §10.6 are corrected to match. | **Reserved procurement is below the required allocation by KES {shortfall}** | **Review reserved procurement** (Procurement Planner; existing link) |
| `PLN_PLAN_CONTENTS_INCOMPLETE` (method not chosen) | **v1.27 (D2): Request plan funding confirmation** (§5.6 item 4) | **{n} purchase needs a procurement method** / **{n} purchases need a procurement method** | **Choose a procurement method** (Procurement Planner; opens that purchase) |
| `PLN_WINDOW_CLOSED` | Submit initial departmental plan (§5.1.3) | **Initial submissions are closed** | Per D3: the §10.16 C02 panel content, naming Administrator or System Manager |
| `PLN_REFERENCE_UNAVAILABLE` / `PLN_STATUTORY_ROUTE_UNCONFIGURED` | The affected action named in §10.16 | **{Setting} is not set up** | Per D3: **Open System setup** when the actor holds setup access; otherwise the §10.16 text **Ask your KenTender administrator to complete this setting.** |

The blocked block lists every blocker together, one fix control each, and states only the headline figure. Supporting figures appear once, in the working region: the budget-fit table, the reservation allocation block or the purchase row. With one blocker, the headline names it. With two or more, the headline gives the count and each blocker follows as its own line with its fix (D1).

#### 10.1A.6 Technical readers and other readers

For Administrator and System Manager (U21-TECHNICAL-DETAIL) the next-step line is never Your turn and carries no fix; it states the Waiting or Done line for the record's state, and the tracker shows the same markers as for any reader (KT-STD-001 v1.8 §3B.6; §3A.6 unchanged). An Auditor or other reader is Not involved: no next-step line; the tracker shows the exact selected Version's markers.

#### 10.1A.7 Project Owner decisions

| # | Question | Status in v1.26 |
|---|---|---|
| D1 | With several blockers, does the headline name the first or give a count? | **Proposed:** count when two or more, e.g. **2 things stop this plan going to Finance**, with each blocker on its own line; name it when there is one. Settled by approval of v1.26. |
| D2 | Which checks block **Request plan funding confirmation**? | **Decided in v1.27 (Project Owner instruction, 25 September 2026, to implement the recommendations):** an over-budget line and a missing procurement method block the request; a reservation shortfall blocks Sign and submit Annual Plan only. Implemented in §5.3.1, §5.5.3.1, §5.6 item 4, §10.3 and §10.6. No variant remains Pending D2. The v1.26 analysis follows for the record: **Open.** Under v1.25 §5.6 item 4 and PLN18-AC-123, pre-Finance readiness excludes affordability and does not name the reservation shortfall; §5.3.1 and §5.5.3.1 make those two block Finance confirmation and signature. Approved §10.3 and §10.6 present the shortfall as blocking the Finance request, and the live build blocks the request when over budget. A missing method appears to block pre-Finance readiness through §5.6 item 4's calculable-schedule test, but the U07 BASE fixture shows Schedule passing while the infrastructure method is unchosen. Resolving D2 changes §5.3.1, §5.5.3.1 and §5.6 item 4, which v1.26 does not do. Variants marked **Pending D2** wait for it. |
| D3 | Who reopens departmental intake, and who owns the missing-setting hand-off? | **Answered by v1.25:** intake is the Fiscal Year flag and close instant (§5.1.3), a System setup setting whose responsible role is Administrator or System Manager (§10.16 C02, §6.5). Missing settings follow the §10.16 panel. **Proposed:** configuration blockers use that in-product route rather than a new hand-off command, as a deliberate exception to KT-STD-001 v1.8 §3B.4 under its §1 precedence rule, because a request-to-administrator command would be a new CFG/AUTH facility. Settled by approval of v1.26. |
| D4 | Does an over-budget Draft notify the Budget Officer automatically? | **Proposed:** no; only when the Planner uses **Request budget revision**. A Draft is mutable and the Planner may instead reduce a purchase. Settled by approval of v1.26; the command itself is §10.1A.8 work. |
| D5 | The live build shows a required allocation of KES 42,600,000 and 43.66%; §10.2 gives KES 39,000,000 and 38.46%. | **Resolved.** Both follow §5.5.3.1. §10.2 is Version 1 at KES 130,000,000. The build is a Version 2 update whose four purchases total KES 142,000,000: 30% is KES 42,600,000, and a KES 62,000,000 qualifying allocation is 43.66%. The difference is data, not calculation; the build's purchase references are not the §10.2 fixture. No v1.26 change. |

#### 10.1A.8 Work outside §10 that v1.26 does not make

**v1.27 status:** every item below is now made: D2 and the next-step table in §§5.3.1, 5.5.3.1, 5.6 and 5.7; the command, record, errors, owner contracts and hand-off register in §§4.7, 7.2, 7.3, 7.7 and 8; the action-map rows in §11.9; the fixture in §10.2 and §§13.3–13.4; acceptance in §14.12. The BUD-CHG-001 receiving side and the REQ-CHG-001 requisition item remain owner-document corrections (§15.2, §17.2). The v1.26 list is retained below.

These are required before the affected controls can be implemented or pass the §10.18 review condition that every interactive control is mapped in §11.9. They are not made by v1.26:

- **§5:** the D2 decision; the state-by-responsibility next-step table (KT-STD-001 v1.8 §7 row 5).
- **§7:** a hand-off command for **Request budget revision**, with the matching BUD-CHG-001 receiving side and hand-off register rows (KT-STD-001 v1.8 §3B.4). The statutory row is now determinable from §6.1.
- **§11.9:** action-map rows for **Request budget revision from {name}**, **Reduce a purchase** and **Choose a procurement method**. **Review reserved procurement** is already mapped.
- **§13 / SEED-001:** the fixtures for the new variants in §10.18.
- **§14:** dead-end matrix and hand-off acceptance (KT-STD-001 v1.8 §6).

### 10.2 Closed fixture pack

**Fixture provenance, outside all artboards:** BASE uses the supplied integrated Plan/source amounts and corrected actor chronology. READY, UPDATE, PUBLICATION, EXECUTION and CONFIG are explicit UI-only scenario variants for showing agreed states. They are not approved production seeds, actual transactions or legal verification. READY changes the laptop designation to Youth solely to exercise the allocation UI; it must not silently replace the baseline's None designation. Production admission still requires verified eligibility. All names are shared fixture actors.

| Shared field | Exact display value |
|---|---|
| Plan title | Ministry of Health Annual Procurement Plan 2027/28 |
| Plan reference | PLN-MOH-2027-001 |
| Financial Year | FY 2027/28 |
| Department A | Digital Health |
| Department B | Human Resources Management and Development |
| DHI DPP | DPP-MOH-DHI-2027-001 |
| HRMD DPP | DPP-MOH-HRMD-2027-001 |
| Budget | MOH-BUD-2027-001 |
| Budget Version | Version 1 |
| Approved Budget ceiling | KES 160,000,000 |
| Objective reference | OBJ-MOH-2023-001 |
| Objective title | Strengthen interoperable national digital health services |
| Objective path | Digital health systems › Health policy, standards and regulation › Digital health governance |
| Strategy Version | STR-MOH-2023-001-V1 |
| Project name | Not applicable |

| Item | Reference | Category | Quantity | Unit | Value | Required by | Method | Structure |
|---|---|---|---:|---|---:|---|---|---|
| National digital health infrastructure upgrade | PPI-MOH-2027-021 | Services | 1 | Programme | KES 80,000,000 | 31 Aug 2027 | Open Tender | Not aggregated; Single lot |
| Clinical training and deployment laptops for digital health rollout | PPI-MOH-2027-033 | Goods | 250 | Each | KES 50,000,000 | 31 Dec 2027 | Open Tender | Aggregated; Single lot |

Separate Aggregation and Lotting into labelled fields when rendered; the last column above supplies two distinct fixture values, not a combined UI field. Requirement type is Non-consulting services for infrastructure and Goods for laptops. Both have fixed Plan horizon Single year.

| Source | Need reference | Revision | Department | Quantity | Unit | Required by | DPP entry | Budget Line | Amount |
|---|---|---:|---|---:|---|---|---|---|---:|
| National digital health infrastructure upgrade | NDS-MOH-2027-0001 | 1 | Digital Health | 1 | Programme | 31 Aug 2027 | DPPE-MOH-DHI-2027-001 | MOH-BL-DHI-2027 | KES 80,000,000 |
| Clinical training laptops for digital health rollout | NDS-MOH-2027-0003 | 2 | Human Resources Management and Development | 100 | Each | 31 Dec 2027 | DPPE-MOH-HRMD-2027-001 | MOH-BL-HWD-2027 | KES 20,000,000 |
| Clinical deployment laptops for digital health rollout | NDS-MOH-2027-0004 | 1 | Digital Health | 150 | Each | 31 Dec 2027 | DPPE-MOH-DHI-2027-002 | MOH-BL-HWD-2027 | KES 30,000,000 |

All three sources are Accepted Departmental Need, DPP Submission 1, proceeding. DHI has 2 requirements/KES 110,000,000; HRMD has 1/KES 20,000,000. Across the Plan: 2 Plan Items, 3 sources, 2 departments, KES 130,000,000. Do not sum different units into one quantity.

Infrastructure source description: **Procure and implement national digital health infrastructure across priority health facilities.** Expected operational result: **Priority health facilities can use secure and interoperable digital health services.** Package description: **Procure and implement the national digital health infrastructure upgrade as one integrated FY 2027/28 programme.**

Laptop training description, UI-only complete-detail text: **Provide the laptops required for clinical workforce training in the national digital-health rollout.** Expected operational result: **Clinical training teams can use the common digital-health platform during training.** Deployment description, UI-only: **Provide laptops for field deployment of the national digital-health platform.** Expected operational result: **Deployment teams can configure and support digital-health services at participating facilities.**

Laptop package description: **Procure and deploy one common laptop specification for clinical training and field digital-health deployment across two departments.** Aggregation reason: **Both departments require the same laptop specification for the same national digital-health rollout; combining secures better unit pricing and one delivery schedule.**

Estimate basis, UI-only text for both package detail examples: **Market survey estimate includes delivery, installation where applicable and other identified incidental costs.** Supporting basis reference: **Market survey working paper**. This is not an actual attachment; render it as text in the static fixture, not as a working download link.

| Budget Line | Line name | Funding source | Approved | Planned | Reserved | Committed | Available |
|---|---|---|---:|---:|---:|---:|---:|
| MOH-BL-DHI-2027 | Digital health infrastructure programme | Government of Kenya | KES 100,000,000 | KES 80,000,000 | KES 0 | KES 0 | KES 100,000,000 |
| MOH-BL-HWD-2027 | Digital health workforce development | Government of Kenya | KES 60,000,000 | KES 50,000,000 | KES 0 | KES 0 | KES 60,000,000 |

BASE reservation panel: Eligible planned procurement **KES 130,000,000**; Target **30%**; Required allocation **KES 39,000,000**; Planned qualifying allocation **KES 0**; Remaining allocation **KES 39,000,000**; Plan basis **PLN-MOH-2027-001, Version 1** and exact rule Version in separate fields; result **Required allocation not met**. Both package designations None. READY changes laptop planned designation to **Youth**, qualifying allocation to **KES 50,000,000**, remaining allocation to **KES 0**, qualifying share of eligible planned procurement to **38.46%** and result to **Required allocation met**. The Budget ceiling **KES 160,000,000** remains a separate Funding fact and is not used in this calculation. County requirement: **Not applicable**. Mandatory restrictions: **No additional restriction applies**.

**UPDATE-OVER-BUDGET scenario — v1.27, UI-only.** An explicit UI scenario variant like READY and UPDATE. It is not an approved production seed, actual transaction or legal verification. It exists so that U07-UPDATE-OVER-BUDGET, U07-WAITING-BUDGET-REVISION and the matching U01 rows can be drawn. It replaces the live build's development data (PPI-MOH-2027-001 to 004 and the purchase named "testing requisitions"), which is not used anywhere.

| Scenario fact | Exact display value |
|---|---|
| Current plan | PLN-MOH-2027-001 Version 1, READY-derived, current plan since 10 Dec 2026, 15:05 EAT (U01-CURRENT) |
| Update | Version 2, started by Mercy Kilonzo on 15 Dec 2026, 09:00 EAT |
| Reason for updating the plan | **Add the workforce certification requirements accepted from Human Resources Management and Development.** |
| HRMD departmental update | DPP-MOH-HRMD-2027-001 Submission 2; prepared and certified by Dr Peter Kimani on 14 Dec 2026, 10:00 EAT; accepted by Mercy Kilonzo on 14 Dec 2026, 15:00 EAT |
| Purchases formed | Mercy Kilonzo, 15 Dec 2026, 09:30 EAT |
| Request budget revision (waiting variant only) | Mercy Kilonzo, 15 Dec 2026, 10:00 EAT, to Josphat Mwangi as Budget Officer |

| Item | Reference | Category | Quantity | Unit | Value | Required by | Method | Budget Line | Change in Version 2 |
|---|---|---|---:|---|---:|---|---|---|---|
| National digital health infrastructure upgrade | PPI-MOH-2027-021 | Services | 1 | Programme | KES 80,000,000 | 31 Aug 2027 | Open Tender | MOH-BL-DHI-2027 | Unchanged |
| Clinical training and deployment laptops for digital health rollout | PPI-MOH-2027-033 | Goods | 250 | Each | KES 50,000,000 | 31 Dec 2027 | Open Tender | MOH-BL-HWD-2027 | Unchanged |
| Digital health workforce certification programme | PPI-MOH-2027-051 | Services | 1 | Programme | KES 10,000,000 | 31 Dec 2027 | Open Tender | MOH-BL-HWD-2027 | Added |
| Digital health training assessment materials | PPI-MOH-2027-052 | Goods | 1 | Lot | KES 2,000,000 | 31 Dec 2027 | Open Tender | MOH-BL-HWD-2027 | Added |

Sources for the added items are direct departmental requirements DPPE-MOH-HRMD-2027-002 (certification programme; Requirement type Non-consulting services) and DPPE-MOH-HRMD-2027-003 (assessment materials; Requirement type Goods), both proceeding in HRMD Submission 2. Package descriptions repeat the item titles. Designations: laptops **Youth** as READY; the two added items **None**.

Budget fit: **Digital health infrastructure programme** approved KES 100,000,000, this plan KES 80,000,000, **Within by KES 20,000,000**; **Digital health workforce development** approved KES 60,000,000, this plan KES 62,000,000, **Over by KES 2,000,000**. Finance confirmation **Not requested**. Reservation panel, UI-only as READY: Eligible planned procurement **KES 142,000,000**; Target **30%**; Required allocation **KES 42,600,000**; Planned qualifying allocation **KES 50,000,000**; Remaining allocation **KES 0**; qualifying share **35.21%**; result **Required allocation met**. Schedule: **All purchases meet their departmental deadlines**, a UI-only result using the §10.2 profile assumptions. Every purchase's Current work reads **Ready**. The only failing pre-Finance test is the HWD line.

**Schedule fixture, UI-only calculation example:** Profile names **Open Tender — services** and **Open Tender — goods**, Version 1. Profile periods: tendering 21 calendar days, evaluation 30 calendar days, award approval buffer 5 days, notification buffer 2 days, standstill 14 days. Internal buffer labels include **Planning assumption**. Profile legal-source status is **Production verification pending** in CONFIG; do not display the profile as a verified legal reference. READY is a simulated complete-check presentation, not evidence that those production dependencies are resolved.

| Milestone | Infrastructure baseline | Laptop baseline |
|---|---|---|
| Invitation or advertisement | 1 May 2027 | 15 May 2027 |
| Bid opening | 22 May 2027 | 5 Jun 2027 |
| Evaluation completion | 21 Jun 2027 | 5 Jul 2027 |
| Tender award approval | 26 Jun 2027 | 10 Jul 2027 |
| Notification of award | 28 Jun 2027 | 12 Jul 2027 |
| Contract signing | 12 Jul 2027 | 26 Jul 2027 |
| Delivery or implementation completion | 31 Aug 2027 | 31 Dec 2027 |

Estimated delivery/implementation period: infrastructure **30 calendar days**, estimated completion **11 Aug 2027**; laptops **60 calendar days**, estimated completion **24 Sep 2027**. Source boundaries remain the final baseline dates above. These period values are explicit UI fixture assumptions, not amendments to source Needs.

| Actor/evidence | Exact fixture value |
|---|---|
| Departmental Author | Grace Wanjiku |
| DHI certifier | Julia Njeri; 25 Nov 2026, 10:30 EAT |
| HRMD certifier | Dr Peter Kimani; 25 Nov 2026, 11:00 EAT |
| Planner | Mercy Kilonzo |
| DHI acceptance | Mercy Kilonzo; 27 Nov 2026, 14:00 EAT |
| HRMD acceptance | Mercy Kilonzo; 27 Nov 2026, 14:05 EAT |
| Finance | Josphat Mwangi; 4 Dec 2026, 10:00 EAT |
| Preparation signature, READY scenario | Charles Mutiso; 7 Dec 2026, 10:00 EAT |
| AO adoption, READY scenario | Amina Hassan; 8 Dec 2026, 10:00 EAT |
| Statutory approval, READY scenario | Daniel Rotich; 9 Dec 2026, 11:00 EAT; Cabinet Secretary |
| Publication acknowledgement, PUBLICATION scenario | 10 Dec 2026, 15:00 EAT |

When rendered, actor and time are separate labelled fields. Plan-level stage evidence appears only for stages already reached in the selected artboard. Do not show an approval on a Draft screen.

### 10.3 U01 — Planning workspace

**Archetype and purpose:** Work workspace. See the governing/draft annual plan, act on current Planning work and then browse departmental plans.

**Fixture — outside the artboard:** Mercy Kilonzo; Procurement Planner; 3 Dec 2026, 09:00 EAT; BASE Draft Plan Version 1; no Active Plan; no assigned decision task.

**Primary question and action.** What is the current Planning position, and what must Mercy do next? **Continue plan** is primary in the BASE fixture.

**Information priority.** Level 1: Draft Plan, reservation shortfall and Continue/Review action. **v1.27:** Level 1 is the Draft Plan, the pre-Finance blocker (missing procurement method) and Continue; the reservation shortfall follows as the second, quieter issue. Level 2: accepted departmental plans. Level 3: submission/version history on record routes.

**Header and orientation.** Title **Annual procurement planning**; description **Prepare departmental requirements, organise the annual plan and follow its approval.** Beneath it, compact Financial year selector **FY 2027/28**. No header action in BASE.

**Annual plan work.** Dominant first region. Show title **Draft annual procurement plan** with muted **PLN-MOH-2027-001 · Version 1**. Beside/beneath it show compact facts **2 purchases · KES 130,000,000 estimated cost** and narrative **This plan is being prepared. It cannot yet be used to authorise procurement.** Put primary enabled **Continue plan** at right.

Directly beneath, one visible issue block: **Reserved procurement is below the required allocation by KES 39,000,000. Resolve this before sending the plan to Finance.** Put enabled **Review reserved procurement** beside/below it. Do not repeat the full target/qualifying calculation on the workspace.

**v1.27 correction (D2).** The sentence above conflicted with §5.5.3.1: the shortfall blocks signature, not the funding request. The issue region now shows two issues in this order. First, dominant: **1 purchase needs a procurement method. Choose it before sending the plan to Finance.** with enabled **Choose a procurement method**. Second, quieter: **Reserved procurement is below the required allocation by KES 39,000,000. Resolve this before the plan can be signed and submitted.** with enabled **Review reserved procurement**. The superseded sentence is retained above as history only and is not drawn.

**Departmental plans.** Quieter secondary register below. No global filters in this fixed two-row fixture. Table:

| Department | Status | Requirements | Estimated cost | Action |
|---|---|---|---|---|
| Digital Health | Accepted | 2 | KES 110,000,000 | View departmental plan |
| Human Resources Management and Development | Accepted | 1 | KES 20,000,000 | View departmental plan |

Both action links are enabled. Submission numbers are absent from this summary. Below the table show **2 departmental plans**.

**U01-CURRENT.** READY-derived Current Plan Version 1 at 10 Dec 2026, 15:05 EAT. Replace the dominant region with **Current annual procurement plan**, muted reference/Version, **KES 130,000,000 approved value**, and narrative **This is the plan currently in force.** Primary row action **View current plan**. Put secondary enabled **Prepare plan update** at region right. No issue or empty action region.

**U01-CURRENT-UPDATE.** Keep the current Plan as a compact read-only baseline. Above it, make **Continue plan update** the Level 1 task: muted **Version 2**, Proposed value **KES 130,000,000**, affected purchase **Clinical training and deployment laptops for digital health rollout**, change **Description updated**, primary **Continue update**. Visible text **The current plan remains in force while this update is reviewed.** Remove Prepare plan update.

**U01-NO-PLAN.** Mercy; 26 Nov 2026, 09:00 EAT; no accepted DPP. Dominant empty result **No annual plan yet** with **The draft annual plan will appear after Procurement accepts a departmental plan.** No Continue or Create action. Departmental register shows supplied submissions or **No departmental plans to display.**

**U01-DEPARTMENT-AUTHOR.** Grace; DHI Author; DPP Draft. Header **Procurement planning** / **Prepare your department’s procurement requirements and follow their review.** Dominant task row **Digital Health departmental plan · FY 2027/28**, status narrative **Draft — complete the requirements and funding details**, primary **Continue departmental plan**. With no DPP and open intake: **No departmental plan yet** plus primary **Start departmental plan**. Annual Plan position follows as a quieter read-only result; no Planner action.

**U01-HOD.** Julia; acting HoD DHI; Draft ready for certification. Dominant heading **1 departmental plan requires your decision**. Task row **Digital Health · FY 2027/28**, narrative **Review the complete departmental plan and submit it to Procurement**, primary **Review departmental plan**. The plan register follows quietly. No Start action.

**U01-LATE-NEED (v1.28).** The department's Head of User Department or Departmental Author; accepted departmental plan; one Need accepted after it. Task row headline **Add {need} to the departmental plan**; supporting sentence **Accepted after {department}'s departmental plan was accepted.**; action **Create update**, which opens the departmental plan. The departmental-plan register row reads Status **Accepted · 1 accepted need not in plan**. The own-plan spotlight's action reads **Create update**. **Awaiting fixture:** the exact Need reference and acceptance instant for the static artboard.

**U01-ASSIGNED-DECISION.** A task link does not render this workspace first; it opens the exact U06, U10 or U11 task. This variant has no separate artboard.

**Comprehension acceptance.** The governing/draft Plan and next lawful action are identifiable before departmental-plan rows. The current issue is attached to the Plan it blocks. References do not compete with names, and no empty task panel appears.

**Next step and journey — added in v1.26.** Neither component (§10.1A.4). The Plan task row narrative carries the next-step answer. U01 BASE is unchanged; its issue block is already the plain-language blocker, and its wording "before sending the plan to Finance" is subject to D2. **v1.27:** D2 is decided and the U01 BASE issue region is corrected above. Two row variants for the over-budget update, using the v1.27 UPDATE-OVER-BUDGET fixture (§10.2). They were Pending D2 and Awaiting fixture in v1.26; both are resolved in v1.27:

- **U01-CURRENT-UPDATE-OVER-BUDGET:** Mercy, 15 Dec 2026, 09:50 EAT. Narrative **Over budget by KES 2,000,000 on Digital health workforce development**; primary **Continue update**. Proposed value **KES 142,000,000**; muted **Version 2**.
- **U01-CURRENT-UPDATE-WAITING-BUDGET:** Mercy, 15 Dec 2026, 10:05 EAT. Narrative **Waiting for Josphat Mwangi (Budget Officer) to revise the budget line**, with since **15 Dec 2026, 10:00 EAT**; action **View update**.

### 10.4 U02–U05 — Departmental plan preparation and certification

**Archetype and purpose:** Form/editor with a review variant. Complete, exclude or add departmental requirements and let the HoD certify the whole plan on the same page.

**Shared information priority.** For the Author, Level 1 is incomplete requirement work and Save; Level 2 is the requirement/funding register; Level 3 is accepted-source history. For the HoD, Level 1 is certification consequence and Submit; Level 2 is complete included/excluded content; Level 3 is earlier submission history. Do not give summary counts, filters and certification equal weight.

**Fixture — outside the artboard:** Grace as Author and Julia as acting HoD for Digital Health; FY 2027/28; BASE requirements; use the exact actor/time stated per variant below.

**U02-AUTHOR-DRAFT.** Grace; 24 Nov 2026, 15:10 EAT. Header title **Your departmental procurement plan**; description **Review what your department needs this year. Select a budget line and enter the estimated cost for each requirement you intend to include.** No header action. Context row: Department **Digital Health**; Financial year **FY 2027/28**; Status **Draft**.

Below context place a summary strip with Requirements **2**; Cost entered so far **KES 30,000,000**; Requirements needing details **1**. The label must say “entered so far”; no complete departmental total is shown.

Section **Requirements** follows. Table columns: Requirement; Quantity; Unit; Required by; Estimated cost; Status; Action.

| Requirement title | Reference beneath title | Quantity | Unit | Required by | Estimated cost | Status | Action |
|---|---|---|---|---|---|---|---|
| National digital health infrastructure upgrade | NDS-MOH-2027-0001 · Revision 1 | 1 | Programme | 31 Aug 2027 | Not entered | Funding details needed | Enter funding details |
| Clinical deployment laptops for digital health rollout | NDS-MOH-2027-0004 · Revision 1 | 150 | Each | 31 Dec 2027 | KES 30,000,000 | Included | Review details |

The title/reference pairs form one displayed Requirement cell. Each action is enabled at row right. Beneath the table place enabled secondary **Add a requirement**. Footer: enabled **Save draft** at right. Beneath the footer, no certification action for the Author. Above it show **Your Head of Department must review and submit this plan.**

**U03-FUNDING.** Expand directly beneath the infrastructure row; keep the rest of U02 visible. Panel heading **Funding details**. Show a compact source summary: Requirement title; **1 Programme**; Required by **31 Aug 2027**, with **View requirement details** for the full six source facts. Then fields Budget line, selected **Digital health infrastructure programme**, with **MOH-BL-DHI-2027** beneath as muted text; Estimated cost (KES) **80,000,000**. Helper directly beneath amount: **Enter the full estimated cost, including applicable delivery and other incidental costs.** Panel footer **Cancel** / primary **Save details**. Beneath those buttons place secondary text link **Correct the source requirement**, followed by **Source changes require their own Departmental Needs review.**

**U03-FUNDING-PREFILLED (v1.30).** Variant of U03-FUNDING for a requirement whose accepted revision has an estimate. Estimated cost (KES) starts with that estimate, **80,000,000**, and Budget line starts blank. The helper beneath the amount is unchanged: **Enter the full estimated cost, including applicable delivery and other incidental costs.** The amounts are equal, so no change line appears. Nothing else in U03-FUNDING changes.

**U03-FUNDING-CHANGED (v1.30).** The preparer changes Estimated cost (KES) to **85,000,000** (**new content**, §13.3). A muted line directly beneath the helper reads **Accepted requirement estimate: KES 80,000,000. Change: +KES 5,000,000.** A reduction reads **−KES**. The line is absent when the amounts are equal, when the accepted revision has no estimate and for a direct requirement. The line is information only and adds no required input.

**U03-EXCLUDE.** Standard dialog over U02. Heading **Exclude from this year’s departmental plan**; exact infrastructure name/reference; multiline **Reason for excluding this requirement**, value **The department will pursue this requirement in a later annual planning cycle.** Beneath it: **This requirement stays on record. Its budget line and amount will be cleared from this draft.** Footer Cancel / primary **Exclude requirement**.

**U03-EXCLUDED-ROW.** Replace the infrastructure row Status with **Not included this year**, amount with **Not applicable**, action **Include in this year’s departmental plan**. Put the full exclusion reason in an always-visible row detail directly beneath. No budget line/type/classification is displayed as operative.

**U03-REINCLUDE.** Dialog heading **Include in this year’s departmental plan**; exact source identity; text **Select a budget line and enter the estimated cost again before submitting.** Fields Budget line blank and Estimated cost (KES) blank (v1.30: Estimated cost starts from the accepted requirement's estimate when it has one, as in §4.3 rule 6, and never from the cleared planning amount). Footer Cancel / primary **Include requirement**. No old operative funding is prefilled.

**U04-DIRECT.** Grace; 24 Nov 2026, 15:20 EAT. Header **Add a requirement**; description **Add a departmental requirement that was not created through Departmental Needs.** Context Department **Digital Health**; Financial year **FY 2027/28**. Form top to bottom: Requirement title **Digital health platform security assessment**; Description **Assess the security of the national digital health platform and provide a prioritised remediation report**; Expected result **The Ministry receives a prioritised and actionable security remediation plan**; Quantity **1** and Unit **Programme** side by side; Required by **31 Oct 2027**; Budget line **Digital health infrastructure programme**, with code beneath; Estimated cost (KES) **20,000,000**. Footer Cancel / primary **Add requirement**. No Need, bypass reason, Strategy, method or attachment field.

**U04-EDIT.** Same values and arrangement; title becomes the requirement title with reference beneath from the actual saved direct entry. Header status Draft. Footer far-left **Remove requirement**, then **Back to departmental plan**, right-aligned primary **Save requirement**. The static design fixture must supply the saved reference returned by the executable fixture; it may not invent one. This variant is incomplete for design generation until that owner-generated reference is supplied.

**U05-HOD.** Julia; 25 Nov 2026, 10:15 EAT; complete DHI Draft, total KES 110,000,000. Use U02 header/context but title **Review Digital Health’s departmental plan**; description **Check the requirements and submit the complete departmental plan to Procurement.** Summary Requirements **2**; Included cost **KES 110,000,000**; Excluded requirements **0**. The requirement table shows both rows Included, exact amounts 80m/30m and actions **View details**. Below table place section **Certification** with exact text: **I certify that this plan records Digital Health’s procurement requirements for FY 2027/28. I confirm the quantities, required dates and funding details for the included requirements, and the reasons for excluding the others.** Checkbox **I confirm this certification** starts unchecked. Footer **Back** / primary **Submit departmental plan**, disabled until checked; put **Confirm the certification to submit this plan.** immediately above the disabled button.

**Estimate change at certification (v1.30).** In the requirements table, a row whose Estimated cost differs from the accepted requirement's estimate carries, beneath its Estimated cost, the same muted line as U03-FUNDING-CHANGED: **Accepted requirement estimate: KES {amount}. Change: {+/−}KES {amount}.** No column is added. The certification text and checkbox are unchanged, and the line adds no required input or blocker.

**U05-CORRECTION.** Same layout for the already-created correction Draft. Visible notice **Your plan needs a correction** above the table; below it list the full Procurement comment beside the affected deployment row: **Explain how the KES 30,000,000 estimate for the deployment laptops was calculated, or correct the amount.** Context rows Returned submission **Submission 1**; Correction submission **Submission 2**. Certification text is the correction text from PLN v1.19 §10.6. Footer primary **Resubmit departmental plan**, disabled until the confirmation checkbox is checked. Section **For your next departmental update** follows the corrected coverage table and contains any explicitly supplied unrelated requirement; this fixture supplies no row, so render only the heading, explanatory text **Finish this correction first. New requirements belong in the next update.**, and no add action.

**U05-ALL-EXCLUDED.** Independent Draft with the same two requirements both excluded, each with a supplied full reason; included cost **KES 0**; Excluded requirements **2**. The current fixture supplies only the infrastructure exclusion reason, so a complete artboard requires a second exact laptop reason from the fixture builder before generation. No empty-submission error is shown.

**U02-CLOSED.** Grace; initial intake closed. Retain editable U02 rows and Save draft. Above footer: **Initial submissions are closed. You can keep editing this draft, but it cannot be submitted now.** No Submit action. **U05-CORRECTION-CLOSED** retains Resubmit under the fixed returned-coverage rule. **U02-ACCEPTED-UPDATE** shows status **Accepted — update in progress**, action **Continue update**, and links **View accepted departmental plan** / **History** below context; no second DPP may be started.

**Visual check.** The page presents requirements before certification. Funding opens next to the chosen row. The Author never sees a fake submit control; the HoD sees one certification and one submission action.

**Next step and journey — added in v1.26.** Tracker §10.1A.2. On U02-AUTHOR-DRAFT it is in reduced form, because the summary strip and table already fill the first view.

| Variant | Kind | Headline and sentence | Holder / since | Fixes | Replaces | Tracker |
|---|---|---|---|---|---|---|
| U02-AUTHOR-DRAFT | Your turn | **Enter funding details for 1 requirement** | — | Existing row action **Enter funding details** | Context row Status **Draft** | Reduced: **Stage 1 of 4: Preparation — Grace Wanjiku**. The existing sentence "Your Head of Department must review and submit this plan." is retained. |
| U02-CLOSED | Your turn, blocked | **Initial submissions are closed**. Sentence: the existing "You can keep editing this draft, but it cannot be submitted now." | — | Per D3: **Ask your KenTender administrator to complete this setting.** (§10.16 C02); no button for Grace | The standalone closed-intake sentence above the footer | Preparation: Blocked, Grace Wanjiku. Others: Not started. |
| U02-ACCEPTED-UPDATE | Your turn | **Continue the departmental update** | — | Existing **Continue update** | Nothing; formal status "Accepted — update in progress" stays | Preparation: Current (update candidate). Others: Not started. |
| U05-HOD | Your turn | **Certify and submit the departmental plan** | — | Existing **Submit departmental plan** | Nothing | Preparation: Done. Certification: Current, Julia Njeri. Others: Not started. |
| U05-CORRECTION | Your turn | **Correct and resubmit the departmental plan**. Procurement's comment stays beside the affected row. | — | Existing **Resubmit departmental plan** | Notice heading "Your plan needs a correction" | Preparation: Current, per §10.1A.1 return rule applied to §10.1A.2. **Awaiting fixture:** the viewing actor. |
| U05-CORRECTION-CLOSED | As U05-CORRECTION | As U05-CORRECTION; closure does not block a returned correction (§5.1.3) | — | As U05-CORRECTION | As U05-CORRECTION | As U05-CORRECTION |
| U05-ALL-EXCLUDED | Awaiting fixture | — | — | — | — | — |
| U02-ACCEPTED-LATE-NEED (v1.28), department | Your turn | **Add {need list} to this plan**, with the §5.7 sentence | — | Existing **Create update** | The separate notice "{n} accepted needs are not in this plan" (removed; KT-STD-001 v1.8 §2.9.3 rule 1) | Preparation: Current, the department's people. Others: Not started. |
| U02-ACCEPTED-LATE-NEED (v1.28), Procurement Planner | Waiting on someone | **Waiting for the department to add {need list} to its plan** | Since the latest such Need's acceptance | None | As above | As above |

**Heading on a plan nobody can edit (v1.28).** On a submitted or accepted plan the header no longer asks anyone to review and submit. Title **{Department}'s departmental plan**. Description, submitted: **Submitted to Procurement for review. It cannot be changed while Procurement reviews it.** Description, accepted: **Accepted by Procurement for this financial year.** What to do next is the next step's to say. The U02/U05 titles above apply only to an editable Draft.

### 10.5 U06 — Procurement review of a departmental plan

**Archetype and purpose:** Review/decision. Validate one certified submission, classify included requirements and accept or return it; the accepted-evidence variant permits a separately recorded Procurement-owned classification correction.

**Fixture — outside the artboard:** Mercy; DHI Submission 1; certified by Julia Njeri on 25 Nov 2026, 10:30 EAT; review 27 Nov 2026, 13:45 EAT; BASE.

**Primary question and action.** Are the certified requirements complete and correctly classified for annual-plan preparation? **Accept departmental plan** is primary; Return is corrective.

**Information priority.** Level 1: decision required, any missing classification/stale source and decision actions. Level 2: complete certified requirements with the single Planner classification input. Level 3: immutable certification and classification history.

**Header.** Title **Review Digital Health’s departmental plan**; description **Check the certified requirements before adding them to the annual plan.** Muted **DPP-MOH-DHI-2027-001 · Submission 1 · FY 2027/28**; badge **Awaiting Procurement review**. Immediately show **Decision required — classify every included requirement, then accept the complete submission or return it for correction.** No header action.

**Certification orientation.** Quiet line **Certified by Julia Njeri on 25 Nov 2026, 10:30 EAT** with **View certification** for capacity and the full immutable statement.

**Below certification — requirements.** Summary Included requirements **2**; Included cost **KES 110,000,000**; Excluded requirements **0**. Use one row/card per requirement rather than a nine-column grid. The first line contains Requirement, Quantity/Unit, Required by and Estimated cost. The second line contains Budget line and the only Planner input: Requirement type. Category appears immediately beside it as read-only derived text. Infrastructure type is **Non-consulting services** → Category **Services**; deployment laptops type **Goods** → Category **Goods**. Helper: **Choose the requirement type. Category is set automatically.** Each row has **View requirement**. No type/category control appears on an excluded row.

**Below requirements — decision.** Text **Accepting makes the included requirements available for annual plan preparation. It does not approve the Annual Procurement Plan.** Footer **Return to department** / primary **Accept departmental plan**, both enabled.

**Estimate change on U06 (v1.30).** A requirement row whose frozen Estimated cost differs from the accepted requirement's estimate shows beneath its Estimated cost, on the first line of the row, **Accepted requirement estimate: KES {amount}. Change: {+/−}KES {amount}.**, read from the certification snapshot (§4.3 rule 5). It informs the Planner's validation. It adds no required input, decision, return reason or blocker, and Accept departmental plan stays enabled. A row with equal amounts, no estimate or a direct requirement shows nothing.

**U06-RETURN.** Dialog **What needs to change?**. Context selector begins **Clinical deployment laptops for digital health rollout**; options Whole departmental plan and the two exact included requirements. One multiline comment containing **Explain how the KES 30,000,000 estimate for the deployment laptops was calculated, or correct the amount.** Footer Cancel / primary Return to department.

**U06-EXCLUDED.** Independent certified submission with infrastructure excluded using the §10.4 reason and deployment included. Table shows the excluded row Status **Not included this year**, Estimated cost **Not applicable**, Requirement type **Not applicable**, and the full reason in row detail. Included summary 1 / KES 30,000,000 / excluded 1.

**U06-CLASSIFICATION-MISSING.** Base with infrastructure Requirement type blank. Visible row error **Select the requirement type before accepting this departmental plan.** Accept disabled; Return enabled.

**U06-ACCEPTED-CLASSIFICATION.** Separate history on the same lawful DPP root **DPP-MOH-DHI-2027-001**, using distinct Submission **3**, certified by Julia on 28 Nov 2026, 10:00 EAT and accepted/classified by Mercy on 29 Nov 2026, 15:00 EAT; it must not reuse Submission 1 or its 27 Nov acceptance event. Header title **View accepted requirement classifications**; Status **Accepted**. The table shows each proceeding Requirement, accepted Requirement type, derived Category, Classified by, Classified at and Action. The infrastructure row shows accepted type **Works**, Category **Works**, with **Correct classification** enabled. Excluded rows, if any, show **Not applicable** and no action. Beneath the table state **The certified departmental requirement will not change. A correction records a new procurement classification and keeps the earlier decision in history.** The wrong classification has already formed separate Draft item **PPI-MOH-2027-044** on 29 Nov 2026, 15:10 EAT; no submitted or Active Plan uses it.

**U06-CORRECT-CLASSIFICATION.** Open a focused panel over U06-ACCEPTED-CLASSIFICATION. Heading **Correct requirement classification**. Context shows the exact requirement title/reference and certified submission. Read-only Current requirement type **Works**; Current category **Works**. Required New requirement type selector **Non-consulting services**; read-only New category **Services** updates immediately from the governed catalogue. Required **Reason for correction** contains **The requirement is for a managed technical service and contains no construction work.** Below, impact text **This requirement is already in a draft purchase. The purchase will need to be rebuilt before the plan can continue. The accepted departmental submission will not change.** Footer Cancel / primary **Save classification correction**. Successful fixture: corrected by Mercy on 30 Nov 2026, 09:20 EAT; result links **Review affected purchase** and shows the old/new classification and reason in History. A stale correction uses `PLN_CLASSIFICATION_CORRECTION_STALE`; no value is saved.

**Classification design-asset gate.** `U06-ACCEPTED-CLASSIFICATION` and `U06-CORRECT-CLASSIFICATION` are two separate required static artboards. U09's response to an already-recorded correction does not replace either one. Implementation of **Correct classification** is blocked until both artboards use the exact fixture above, have been reviewed against this contract and appear in the design inventory. A text-only requirement is not a design source.

**U06-STALE-SOURCE.** Base with notice **A source requirement changed after this submission was certified. Return it to the department for correction.** Show exact source/revision in a visible affected row. Accept absent; Return enabled. This static variant requires the owner fixture to supply the changed revision/value; it cannot display an invented difference.

**U06-SEGREGATION.** Isolated actor who certified the same submission. Replace decision section with **You cannot review a departmental plan you certified.** Both decision actions absent; read-only content remains.

**Comprehension acceptance.** Mercy can identify the whole-submission decision, incomplete classification and corrective route before provenance. Requirement type is the only selected input and Category is visibly derived. Missing evidence removes acceptance without removing Return. Classification correction never resembles editing the certified submission.

**Next step and journey — added in v1.26.** Tracker §10.1A.2.

| Variant | Kind | Headline and sentence | Holder / since | Fixes | Replaces | Tracker |
|---|---|---|---|---|---|---|
| U06 | Your turn | **Classify every included requirement, then accept or return the submission** | — | Existing Accept / Return | Badge "Awaiting Procurement review" and the "Decision required — …" sentence | Preparation: Done. Certification: Done. Procurement review: Current, Mercy Kilonzo. |
| U06-CLASSIFICATION-MISSING | Your turn | **Select the requirement type for 1 requirement, then accept** | — | The existing row error stays at the row | As U06 | As U06 |
| U06-STALE-SOURCE | Your turn | **A source requirement changed after certification. Return the submission to the department.** | — | Existing **Return to department** | Existing notice "A source requirement changed…" | As U06. **Awaiting fixture** (existing). |
| U06-SEGREGATION | Waiting on someone | **Waiting for Procurement review by another Procurement Planner**. The existing "You cannot review a departmental plan you certified." is retained. | **Awaiting fixture:** the other Planner's name, or the role where none resolves (§6.5) | None | Nothing | As U06 |
| U06-ACCEPTED-CLASSIFICATION | Done | **Accepted by Mercy Kilonzo on 29 Nov 2026, 15:00 EAT** | — | None; **Correct classification** stays a row action | Header Status **Accepted** | All four stages Done |

U06-RETURN, U06-EXCLUDED and U06-CORRECT-CLASSIFICATION keep the tracker and next-step line of their parent variant; the dialog and panel themselves carry neither.

### 10.6 U07 — Annual plan preparation

**Archetype and purpose:** Form/editor workspace. Organise accepted departmental requirements into purchases and prepare the exact Draft or update.

**Fixture — outside the artboard:** Mercy; BASE Draft Plan PLN-MOH-2027-001 Version 1; 3 Dec 2026, 09:15 EAT; both plan items already formed unless a variant says otherwise.

**Primary question and action.** What purchase work blocks the Draft from moving to Finance? **Edit purchase** or the exact Plan-check recovery leads; Save draft remains the page action.

**Information priority.** Level 1: current purchase work and blocking Plan checks. Level 2: purchase/source values and requirements ready to add. Level 3: exact departmental acceptance and version history.

**Header.** Title **Prepare the annual procurement plan**. Beneath, Plan name then muted **PLN-MOH-2027-001 · Version 1 · FY 2027/28** and badge **Draft**. No header action.

**Page order.** Show Purchases first, followed by one concise Plan checks section. History is a secondary disclosure. Do not create an Approval and publication section while the Planner is still preparing the Draft.

**Purchases section.** Omit Project name when blank. If the Planner deliberately adds one, show it as secondary Plan information above the table. Table columns Purchase; Quantity; Unit; Estimated cost; Required by; Current work; Action:

| Purchase title | Reference beneath title | Quantity | Unit | Estimated cost | Required by | Current work | Action |
|---|---|---|---|---|---|---|---|
| National digital health infrastructure upgrade | PPI-MOH-2027-021 | 1 | Programme | KES 80,000,000 | 31 Aug 2027 | Choose a procurement method | Edit purchase |
| Clinical training and deployment laptops for digital health rollout | PPI-MOH-2027-033 | 250 | Each | KES 50,000,000 | 31 Dec 2027 | Review the required reserved allocation | Edit purchase |

Both Edit purchase links are enabled. Beneath, section **Requirements ready to add** contains **All three departmental requirements are included in the two purchases above.** No Add selected requirements action in this formed state.

**Plan checks.** Place immediately after Purchases, before any secondary source register. Show only results that determine the next action: Funding **Not yet checked**; Reserved procurement **KES 39,000,000 more qualifying allocation required**; Schedule **Both purchases meet their departmental deadlines**. Render the reservation shortfall as the dominant issue with its exact correction link; passing Schedule is quieter. Detailed calculations are supporting evidence. **Send to Finance for funding review** is absent while a blocking check fails.

**v1.27 correction (D2).** Funding is replaced by §10.1A.3 (v1.26). The Schedule result above conflicted with the infrastructure row's **Choose a procurement method**: without a method there is no profile and no calculable schedule (§5.5.1). Schedule now reads **Clinical training and deployment laptops meet their departmental deadline. The infrastructure schedule is calculated once a procurement method is chosen.** The missing method is the pre-Finance blocker, stated once in the next-step block (see the U07 table below), and it is why **Send to Finance for funding review** is absent. Reserved procurement stays visible as an issue with **Review reserved procurement**, with the added text **Resolve this before the plan can be signed and submitted.**; it is no longer the dominant pre-Finance issue. The superseded wording is retained above as history only and is not drawn.

**Changes and history.** Collapsed by default. Expanded text **This is the first version of the annual plan.** Below, exact departmental acceptance history for DHI and HRMD from §10.2 in separate rows.

**Footer.** Enabled **Save draft** at right. When every preparation check passes, add one primary **Send to Finance for funding review**; never show Submit/Approve here.

**U07-UNALLOCATED.** Before formation. Purchases table empty state **No purchases have been added yet.** Below it Requirements ready to add table contains all three exact sources from §10.2. Columns Select; Requirement; Department; Quantity; Unit; Estimated cost; Action. Every checkbox starts unchecked; View requirement is enabled. Primary **Add selected requirements** disabled with helper **Select at least one requirement.** After one or more selections it becomes enabled; this selected-state variant must state which rows are checked.

**U07-ONE-SELECTED.** Only infrastructure checked. Add selected requirements enabled. No separate grouping-choice panel.

**U07-TWO-SELECTED.** Training and deployment laptop rows checked. Add selected requirements enabled; selecting it opens U08-COMBINE.

**U07-WAITING-FINANCE.** READY Draft after request. Funding section notice **Finance is reviewing the funding.** Separate Requested from **Josphat Mwangi** and Requested at with the actual task time supplied by the fixture. No Send action. Because that request time is absent from §10.2, the artboard cannot be generated until the fixture builder supplies it.

**U07-FINANCE-COMPLETE.** READY, after 4 Dec 2026 10:00 EAT. Funding result **Within each approved budget line**; Checked by **Josphat Mwangi**; Checked at **4 Dec 2026, 10:00 EAT**. Approval section notice **Ready for the Head of Procurement Function to sign and submit**; Responsible person **Charles Mutiso**. No Planner handover/approval action.

**U07-UPDATE.** UPDATE Plan Version 2, current Version 1 remains in force. Header title **Prepare plan update**, Status **Draft update**, separate Current plan **Version 1**. Required field **Reason for updating the plan** uses the exact reason supplied by UPDATE fixture; no reason is provided in §10.2, so generation waits for that value. Purchases show proposed content. Changes and history starts open and lists Purchase, Field, Current value, Proposed value. Cancellation action **Cancel plan update** at far left; Save draft at right. Section **For a later plan update** contains pending unrelated sources and **Finish this correction first. These requirements cannot be added to the plan currently under correction.** Exact rows require their owner fixture.

**Comprehension acceptance.** Purchases and the exact blocking work lead. Mercy can tell why Finance submission is unavailable and where to correct it without interpreting readiness enums. Funding/governance remain one Plan; no stepper or generic Review required label.

**Next step and journey — added in v1.26.** Tracker §10.1A.1 in full. Budget fit and Finance confirmation follow §10.1A.3 in every variant. The tracker is the KT-STD-001 v1.8 §2.9.2 orientation row, not the stepper this section's comprehension check prohibits.

| Variant | Kind | Headline and sentence | Holder / since | Fixes | Replaces | Tracker |
|---|---|---|---|---|---|---|
| U07 (BASE) — **v1.27, supersedes the v1.26 row below** | Your turn, blocked | **1 purchase needs a procurement method**. Sentence **You can request the funding check once a method is chosen.** | — | **Choose a procurement method** | Plan checks entry Funding "Not yet checked"; the reservation issue stays in Plan checks as a signature blocker | Preparation: Blocked, Mercy Kilonzo. Others: Not started. Upstream **3 departmental requirements included**. Budget fit: both lines within. Finance confirmation: **Not requested**. |
| U07 (BASE) — v1.26 row, superseded by D2 and retained as history | Your turn, blocked | **2 things stop this plan going to Finance**. Sentence **You can request the funding check once both are resolved.** Lines: **Reserved procurement is below the required allocation by KES 39,000,000**; **1 purchase needs a procurement method**. The count and lines follow D2. | — | **Review reserved procurement**; **Choose a procurement method** | Plan checks entries Funding "Not yet checked" and Reserved procurement; the reservation figures stay in the reservation allocation block | Preparation: Blocked, Mercy Kilonzo. Others: Not started. Upstream **3 departmental requirements included**. Budget fit: both lines within. Finance confirmation: **Not requested**. |
| U07-UNALLOCATED | Your turn | **Add the accepted requirements to purchases** | — | Existing **Add selected requirements**, keeping its disabled helper | Nothing | Preparation: Current, Mercy Kilonzo. Others: Not started. |
| U07-ONE-SELECTED / U07-TWO-SELECTED | Your turn | As U07-UNALLOCATED | — | As above, enabled | Nothing | As U07-UNALLOCATED |
| U07-WAITING-FINANCE | Waiting on someone | **Waiting for Josphat Mwangi (Finance Confirmation Officer) to confirm plan funding** | Since: the request instant, **Awaiting fixture** (existing) | None | Notice "Finance is reviewing the funding." and the separate Requested from field. Finance confirmation: **Awaiting confirmation**. | Preparation: Done. Funding confirmation: Current, Josphat Mwangi. Others: Not started. |
| U07-FINANCE-COMPLETE | Waiting on someone | **Waiting for Charles Mutiso (Head of Procurement Function) to sign and submit** | Since 4 Dec 2026, 10:00 EAT | None | Notice "Ready for the Head of Procurement Function to sign and submit" and the Responsible person field. Finance confirmation: **Confirmed**, with existing Checked by / Checked at. | Preparation: Done. Funding confirmation: Done. Signature: Current, Charles Mutiso. Others: Not started. |
| **U07-UPDATE-OVER-BUDGET** (new; v1.27 fixture UPDATE-OVER-BUDGET, Mercy, 15 Dec 2026, 09:45 EAT) | Your turn, blocked | **Over budget by KES 2,000,000 on Digital health workforce development**. Sentence **You can request the funding check once every budget line fits. Choose one way to fix it.** | — | **Request budget revision from Josphat Mwangi** (hand-off; invokes `RequestBudgetRevision` directly with server-derived line and amounts; no form); **Reduce a purchase** | Plan checks Funding "Not yet checked". Budget fit open, with MOH-BL-HWD-2027 **Over by KES 2,000,000**. Finance confirmation: **Not requested**. | Preparation: Blocked, Mercy Kilonzo. Others: Not started. The existing header orientation keeps Current plan **Version 1**. |
| **U07-WAITING-BUDGET-REVISION** (new; v1.27 fixture UPDATE-OVER-BUDGET, Mercy, 15 Dec 2026, 10:05 EAT) | Waiting on someone | **Waiting for Josphat Mwangi (Budget Officer) to revise the budget line** | Since 15 Dec 2026, 10:00 EAT | None. **Reduce a purchase** stays available as ordinary Draft editing. | As U07-UPDATE-OVER-BUDGET | Preparation: Blocked, Mercy Kilonzo. The budget revision is not a Plan stage. |
| U07-UPDATE | Awaiting fixture (existing) | The kind follows the fixture's checks. If they pass: Your turn, **Send the update to Finance for funding review**. | — | Existing footer primary | The "Draft update" badge stays as formal status | Preparation: Current. Others: Not started. |

**v1.27:** D2 decided that an over-budget Draft may not be sent to Finance, so both variants stand and the following v1.26 contingency no longer applies. If D2 decides that an over-budget Draft may be sent to Finance, U07-UPDATE-OVER-BUDGET and U07-WAITING-BUDGET-REVISION are withdrawn before design and the overrun is shown as a material issue in Budget fit alongside the existing **Send to Finance for funding review**.

**Fixture constraint for the new variants.** v1.27 supplies this fixture as UPDATE-OVER-BUDGET in §10.2, meeting the constraint below. The fixture builder supplies the full Version 2 purchase list and references. It keeps §10.2's PPI-MOH-2027-021 (KES 80,000,000 on MOH-BL-DHI-2027) and PPI-MOH-2027-033 (KES 50,000,000 on MOH-BL-HWD-2027), and adds accepted-source purchases on MOH-BL-HWD-2027 totalling KES 12,000,000, so that line plans KES 62,000,000 against KES 60,000,000 approved. The live build's references (PPI-MOH-2027-001 to 004) and its purchase named "testing requisitions" are development data and are not used.

**First-view check (U07 update family).** Header, tracker (one row), blocked block (headline, sentence and two buttons), the Reason field and the Project name field; the Purchases heading must still start within the 1024 px view. Otherwise the tracker uses its reduced form. In UPDATE-OVER-BUDGET, Project name is blank and omitted (§10.6 Purchases section), and Changes and history starts open, listing the two added purchases with Current value **Not in the current plan**.

### 10.7 U08 — Add selected requirements

**Archetype and purpose:** Focused panel. Choose how multiple compatible departmental requirements become purchases before committing their full scope.

**Fixture — outside the artboard:** Mercy; U07-TWO-SELECTED; laptop training and deployment sources; BASE amounts; 3 Dec 2026, 09:25 EAT.

**Panel placement.** Open a focused panel above the U07 Requirements ready to add table; retain the selected rows visibly highlighted behind/below it. Heading **How should these requirements be added?**

**Selected requirements.** First table columns Requirement; Department; Quantity; Unit; Estimated cost. Rows: training laptops / HRMD / 100 / Each / KES 20,000,000; deployment laptops / Digital Health / 150 / Each / KES 30,000,000. Each full title and reference appears in one Requirement cell.

**Choice.** Below table, radio options left to right/stacked: **Keep separate**; **Combine into one purchase**. Combine selected in this fixture. Then required multiline **Reason for combining**, filled with the exact aggregation reason in §10.2.

**Resulting purchase.** Below choice, shaded preview with separately labelled Purchases **1**; Total quantity **250 Each**; Estimated cost **KES 50,000,000**; Purchase title **Clinical training and deployment laptops for digital health rollout**. Footer Cancel / primary **Add to plan**, enabled.

**U08-SEPARATE.** Same two sources, Keep separate selected. Preview Purchases **2**, with one row per exact source; no combination reason field. Add to plan enabled.

**U08-INCOMPATIBLE.** Isolated selected sources with different budget lines, supplied by the fixture builder. Visible message **These requirements use different budget lines and cannot be combined.** Combine option disabled; Keep separate selected and Add to plan enabled if each passes its own checks. Do not use the BASE laptop pair for this incompatible result because both use MOH-BL-HWD-2027.

**U08-DUPLICATE/INCOMPLETE.** If an exact source is already fully allocated or its cohort changed, show the named source and concrete problem above the choice; Add to plan absent. The artboard requires actual source/version facts from the respective test profile.

**Comprehension acceptance.** Selected sources, grouping choice and the resulting purchase are readable in that order. No partial-quantity control or implicit combining is introduced.

**Next step and journey — added in v1.26.** Neither component (§10.1A.4). U08 opens over U07, whose tracker and next-step line stay in place behind it.

### 10.8 U09 — Purchase editor

**Archetype and purpose:** Form/editor. Complete the few decisions needed to prepare one Draft purchase while retaining complete supporting evidence.

**Fixture — outside the artboard:** Mercy; laptop item PPI-MOH-2027-033 in BASE/READY as stated per variant; Draft Plan Version 1; 3 Dec 2026, 09:40 EAT.

**Primary question and action.** What must be completed or corrected for this purchase? **Save draft** is primary; the current blocking issue names the exact recovery.

**Information priority.** Level 1: current blocker and affected section. Level 2: editable purchase, cost, method and dates plus complete included requirements. Level 3: Strategy/classification/rule provenance and milestone calculations.

**Header.** Title **Clinical training and deployment laptops for digital health rollout**. Beneath, muted **PPI-MOH-2027-033 · Plan Version 1** and badge **Draft**. No header action. Immediately show BASE issue **Reserved procurement is below the required amount**; READY has no issue.

**Sections top to bottom:** Purchase details; Included requirements; Estimated cost; Procurement approach; Dates; Supporting details. Keep the first five open. Supporting details starts collapsed and contains Strategy provenance, classification provenance, applicable rule evidence and detailed milestone calculations. A material issue is never moved into Supporting details.

**Purchase details.** Editable Title and multiline Description using §10.2 laptop package text. Beneath them, one compact read-only summary **Goods · 250 Each · Required by 31 Dec 2027**. Quantity, Unit and required date come from the included requirements. Do not display Plan horizon. **View classification details** is a secondary link; it opens accepted Requirement type, derived Category, actor/time and correction history without making any of them editable here.

**Included requirements.** Table columns Requirement; Department; Quantity; Unit; Required by; Allocation. Two exact laptop source rows from §10.2. References/revisions and Budget line remain in row detail. Beneath the table show **Combined purchase** and a short faithful preview of the reason with **Read full reason**. Do not repeat derived totals beside every source.

**Estimated cost.** Planned amount **KES 50,000,000**; a short Estimate basis preview; Supporting document **Market survey working paper** only when an actual accessible record exists. Full basis remains available through **Read full basis**.

**Strategy evidence.** Supporting detail only. Show the selected objective title first. Objective reference, path and Strategy version appear only after **View strategy evidence**. The absence of an applicable objective remains a visible issue when it blocks submission.

**Procurement approach.** Method selector **Open Tender**. Show a condition-specific input only when the selected method actually requires the Planner to supply it. Never display **Procedure — Planning example**, Method support/status, Rule version or Source check. If the method cannot yet be used, show one plain issue such as **Open Tender cannot be confirmed until the applicable method rule is verified in System setup**, followed by the responsible recovery action. Applicable rule/version/source evidence remains in Supporting details for authorised inspection.

**Reservation and lots.** Show Planned designation only when the Planner must choose one or one has been selected. Omit **None**. Do not repeat annual required allocation, qualifying allocation or shortfall on the purchase: those are one Plan-level check in U07/U11. Show County requirement only for an applicable county entity and only when it changes the item decision. Show Mandatory restrictions only when a restriction exists. Show Lotting only when the Planner chooses multiple lots or must resolve a lotting issue; omit Single lot and Lot count 1.

**Dates.** Target invitation date **15 May 2027**; Expected delivery period **60 calendar days**; Expected completion **24 Sep 2027**; Departmental deadline **31 Dec 2027**. Show result **Expected to meet the departmental deadline**. Place **View calculated dates** beneath; it opens the milestone table in Supporting details. Use **Adjust dates** only where the Planner can lawfully change an input.

**Footer.** Far left enabled **Remove purchase**; secondary **Back to annual plan**; right-aligned primary **Save draft**. The removal dialog explains that eligible requirements return to the Draft Plan and that no funds are released. Save remains available for permissible Draft work while Plan-level submission is blocked by a visible issue.

**U09-INVALID-SCHEDULE.** Same item; Expected delivery period **160 calendar days**; Expected completion **2 Jan 2028**; Departmental deadline **31 Dec 2027**. Visible error immediately above Dates: **Expected completion is after the department’s required date.** Save draft disabled; enabled **Review dates** focuses that section.

**U09-REMOVE.** Dialog heading **Remove this purchase?** with exact item name/reference. Table lists both included requirements. Text **These requirements will return to this draft plan so they can be added again. No funds are released.** Footer Cancel / primary **Remove purchase**.

**U09-LOCKED.** Independent current/update context with an authorised requisition. Visible issue above Departmental requirements: **This item already has an authorised requisition. Add extra requirements as a separate item in a plan update.** Exact requisition/version comes from owner fixture and appears as labelled evidence. Add source, quantity/value increase and Remove item controls absent. Permitted narrative controls and Save follow §5.4.6.

**U09-SOURCE-CORRECTION.** Draft item with an accepted source correction. Above requirements, table Field; Plan currently uses; Latest accepted source. Exact changed source/revisions/values come from the profile. Under table show the prescribed removal/re-formation steps and their individual actions. No one-click Replace source action.

**U09-CLASSIFICATION-CORRECTION.** Separate Draft item **PPI-MOH-2027-044 — National digital health infrastructure upgrade** using the successful U06-CORRECT-CLASSIFICATION fixture. Header issue **A requirement classification was corrected after this purchase was created.** Beneath it show Requirement; Plan currently uses **Works / Works**; Current classification **Non-consulting services / Services**; Corrected by **Mercy Kilonzo**; Corrected at **30 Nov 2026, 09:20 EAT**. Explain **Remove this draft purchase and add its requirements again so method, reservation and schedule checks use the corrected classification.** Enabled **View classification history** and the existing **Remove item and return requirements** action. Save cannot clear the issue and no classification field becomes editable.

**U09-CLASSIFICATION-LOCKED.** Independent item with exact authorised Requisition or published Tender supplied by its owner fixture. Show **This purchase is already in procurement and cannot be reclassified through Planning.** Separately label the corrected classification, exact current Plan classification and Requisition/Tender evidence. Explain **The correction is recorded, but it has not changed the existing procurement. Follow the correction or cancellation process shown for that procurement.** Actions **View classification history** and the exact authorised downstream **View procurement** link only. Remove/re-form, add-source and Save-as-correction controls are absent; new authorisation is held. Do not generate this variant until the downstream owner supplies the exact record and permitted correction route.

**Comprehension acceptance.** Mercy identifies the blocker, editable decision and affected section before supporting provenance. Purchase, sources, cost, method and deadline remain readable without opening Supporting details. No scope/deadline conflict is hidden and no audit label competes with editable work.

**Next step and journey — added in v1.26.** Neither component (§10.1A.4). The purchase-level issue lines stay as they are, and the Plan-level blocker is not repeated here.

### 10.9 U10 — Funding review and reassessment

**Archetype and purpose:** Review/decision. Compare the complete Plan against approved Budget lines and record only the Finance affordability result.

**Fixture — outside the artboard:** Josphat Mwangi; Finance Confirmation Officer; READY Plan Version 1; requested review before 4 Dec 2026, 10:00 EAT; exact request/as-at times must come from the owner fixture.

**Primary question and action.** Is each planned amount within its approved Budget line? **Confirm plan funding** is primary when the comparison passes; Return is corrective.

**Information priority.** Level 1: affordability result, any excess and decision actions. Level 2: approved/planned/difference comparison. Level 3: current balances and immutable review history.

**Header.** Title **Check funding for the annual plan**; description **Confirm whether each planned amount is within its approved budget line.** Plan title beneath; muted **PLN-MOH-2027-001 · Version 1**; badge **Your decision required**. Immediately show **Decision required — confirm affordability or return the Plan to the Planner.** No header action.

**Statement context.** Immediately below, show Budget **MOH-BUD-2027-001** and **Amounts as at** from the exact task fixture. Budget version and request timestamp remain in **Review details** and immutable history; they do not compete with the affordability decision.

**Main comparison.** Table columns Budget line; Line name; Approved amount; Planned amount; Difference; Result; Action.

| Budget line | Line name | Approved amount | Planned amount | Difference | Result | Action |
|---|---|---|---|---|---|---|
| MOH-BL-DHI-2027 | Digital health infrastructure programme | KES 100,000,000 | KES 80,000,000 | KES 20,000,000 | Within budget | View details |
| MOH-BL-HWD-2027 | Digital health workforce development | KES 60,000,000 | KES 50,000,000 | KES 10,000,000 | Within budget | View details |

**Below comparison.** Collapsed supporting section **Current balances**. When opened, show Funding source; Reserved; Committed; Currently available and the exact task snapshot time. Current balances are advisory and visually separated from the approved-versus-planned decision.

**Decision area.** Text **Confirming records affordability. It does not reserve funds or approve the plan.** Footer enabled **Return to planner** / primary enabled **Confirm plan funding**.

**U10-LOW-AVAILABILITY.** Change DHI Currently available to **KES 10,000,000** while Approved stays 100m and Planned 80m. Visible note below that row: **Current availability is lower than the planned amount. The plan is still within the approved budget, so funding confirmation is permitted.** Both decision actions remain enabled.

**U10-OVER-APPROVED.** Independent DHI Approved **KES 70,000,000**, Planned **KES 80,000,000**, Difference **KES -10,000,000**, Result **Exceeds approved amount**. Visible issue **Digital Health exceeds its approved budget by KES 10,000,000.** Confirm plan funding absent; Return enabled.

**U10-CHANGED.** Retain the original statement read-only. Above it show **The amounts for this review have changed.** The original task decisions are absent. If the exact replacement task is supplied and authorised, show enabled **Open updated funding review** below the notice; otherwise show Responsible role **Procurement Planner** and no link.

**U10-RETURN.** Dialog heading **What needs to change?**; context **Whole annual plan** read-only; reason **Reduce the planned amount or obtain an approved budget revision for the Digital Health line.** Footer Cancel / Return to planner.

**U10-REASSESS.** Title **Check funding again for the current plan**; description **The approved budget has changed. Check the existing plan against the revised budget.** Exact Active Plan content read-only. Use a supplied revised Budget version/as-at statement, never the original READY values unless the profile declares them. Decision actions Confirm plan funding / Return to planner; no Plan approval control.

**U10-HISTORY.** Reader layout below the current comparison. Separate blocks **Funding checked at approval** and **Latest funding check**, each with Review; Budget version; Plan version; Outcome; Person; Date/time. No link implies review of another snapshot.

**Comprehension acceptance.** Josphat sees the whole-Plan affordability result and any excess before balances/provenance. Approved, planned, difference and result remain directly comparable. Current availability is secondary; reservation and general compliance do not contaminate the Finance verdict.

**Next step and journey — added in v1.26.** Tracker §10.1A.1.

| Variant | Kind | Headline and sentence | Holder / since | Fixes | Replaces | Tracker |
|---|---|---|---|---|---|---|
| U10 / U10-LOW-AVAILABILITY | Your turn | **Confirm plan funding or return the plan to the planner** | — | Existing footer actions | Badge "Your decision required" and the "Decision required — …" sentence | Preparation: Done. Funding confirmation: Current, Josphat Mwangi. Others: Not started. |
| U10-OVER-APPROVED | Your turn | **Return the plan to the planner**. The existing issue "Digital Health exceeds its approved budget by KES 10,000,000." stays above the comparison. | — | Existing **Return to planner** | As U10 | As U10 |
| U10-CHANGED | Replacement supplied: Your turn, **Open the updated funding review**. Otherwise: Waiting on someone, **Waiting for the Procurement Planner to request a new funding check** | Mercy Kilonzo, or the role where none resolves; since **Awaiting fixture** | Existing link when supplied | The Responsible role field | As U10 |
| U10-RETURN | Dialog: neither component; parent U10 unchanged behind it | — | — | — | — | — |
| U10-REASSESS | Your turn | **Check the current plan against the revised budget** | — | Existing actions | Nothing | Not drawn. Reassessment of an Active Plan is outside the approval lifecycle (§5.3.4); the existing header says "current plan". |
| U10-HISTORY | Not involved | — | — | — | — | All seven stages Done or In force. **Awaiting fixture:** the viewer. |

### 10.10 U11 — Complete annual-plan review and decisions

**Archetype and purpose:** Review/decision. Give every governance actor the same decision-ready Plan, visible material issues and complete evidence, changing only the actor's lawful decision and consequence.

**Fixture — outside the artboard:** READY Plan Version 1. Primary AO fixture: Amina Hassan, 8 Dec 2026, 10:00 EAT immediately before adoption; variants below provide their own actor/time and stage.

**Shared information priority.** Level 1: actual decision, consequence and material blocker. Level 2: decision summary, complete purchase coverage and accountability required for that actor. Level 3: source, rule, calculation and decision history. Download is secondary and never competes with the decision.

**Shared review composition.** Header title/description changes by actor below. Beneath, Plan title and quiet orientation **PLN-MOH-2027-001 · Version 1 · FY 2027/28 · {Current stage}**. Put **Download review pack** as a secondary header action. Immediately state the actor's decision question/consequence from the applicable variant before the Decision summary; do not defer it until after multiple evidence sections.

**First section — Decision summary.** Show Estimated cost **KES 130,000,000**; Purchases **2**; Departments **2**; Funding **Within approved budget**; Reserved procurement **Required allocation met**; Schedule **All purchases meet departmental deadlines**. Immediately below show **No blocking issues** or the exact blocking issues. Then table Purchase; Purpose; Quantity; Unit; Required by; Estimated cost. Each purchase has **Review purchase**; no purchase starts expanded.

**Second section — Accountability.** Two compact labelled rows:

- Funding: **Within each approved budget line**; Checked by **Josphat Mwangi**; Checked at **4 Dec 2026, 10:00 EAT**.
- Preparation: **Signed**; Signed by **Charles Mutiso**; Capacity **Head of Procurement Function**; Signed at **7 Dec 2026, 10:00 EAT**. This row is absent in the HOPF-before-signature variant.

Reserved procurement and schedule details do not repeat here when both pass; they remain under **Review Plan checks**. Any shortfall, unsupported method or late completion is visible in the Decision summary.

Below: **Funding confirmation does not set money aside.** Do not repeat the no-blocking-issues notice already shown in the Decision summary.

**Third section — Purchase evidence.** Selecting **Review purchase** opens one level of detail beneath that row. For infrastructure, show full package description and source-grounded purpose, 1 Programme, Digital Health, 31 Aug 2027 and KES 80m. For laptops, show package description, short aggregation reason, source rows, quantities 100/150 Each, departments, dates and allocations 20m/30m. References, revisions, DPP entry identities and full source text sit under **View departmental evidence**. No purchase opens automatically.

Within each open purchase, show Estimated cost; Procurement approach; Expected completion; Departmental deadline. Strategy, rule evidence, classification provenance, reservation calculations, lotting defaults and the detailed milestone table sit under **Supporting evidence**. Material method/source/schedule issues remain visible in the closed purchase row.

**Fourth section — Funding evidence.** Table Budget line; Approved; Planned; Difference; Result. **View current balances** opens funding source, availability and the as-at instant. Do not repeat the full Finance workspace.

**Fifth section — Changes and history.** Starts collapsed. Changes states **First annual plan** for the initial Plan. When opened, show the immutable decision-history table and exact actors/times. Do not display a future decision as a synthetic history row; the current decision is already stated beside its action.

**Decision area placement.** Show the actor statement near the top as orientation, but keep the buttons after the Decision summary and purchase table so the actor reviews material content before acting. Audit evidence follows after the action area. All blockers remain visible and positive action remains server-gated by complete evidence.

**U11-HOPF.** Charles; 7 Dec 2026, 10:00 EAT before signature. Header **Review and submit the annual procurement plan**; description **Review the complete plan before sending it to the Accounting Officer.** Stage **Funding checked**. Omit Preparation completed row; decision statement **I confirm that this complete annual procurement plan is ready for Accounting Officer adoption.** Footer **Back to annual plan** / primary **Sign and submit Annual Plan**, enabled. No Return action.

**U11-AO.** Amina base. Header **Review the annual procurement plan**; description **Review the proposed purchases. If you adopt the plan, it will go to the Cabinet Secretary for approval.** Stage **Awaiting Accounting Officer**. Statement **By selecting Adopt and submit, you adopt the complete plan shown here and send it to the Cabinet Secretary for approval.** Footer Return for correction / primary Adopt and submit, enabled.

**U11-STATUTORY.** Daniel; 9 Dec 2026, 11:00 EAT before decision. Header **Approve the annual procurement plan**; description **Review the plan adopted by the Accounting Officer.** Stage **Awaiting Cabinet Secretary**. Add AO history row completed by Amina on 8 Dec 2026, 10:00 EAT. Statement **By selecting Approve Annual Procurement Plan, you approve the complete plan shown here. Publication and activation checks must still be completed.** Footer Return for correction / primary Approve Annual Procurement Plan.

**U11-COLLECTIVE.** Isolated Council entity/authorised recorder fixture, not Ministry default. Header **Record the Council’s decision**; Stage **Awaiting Council decision**. Above decision area, read-only Decision belongs to **Council** and Recorded by from exact AUTH fixture; because that recorder identity is not in §10.2, the artboard waits for it. Required field **Resolution reference**, value **COUNCIL/APP/2027/01**. Statement **Record approval only if the Council approved this plan.** Footer Record return for correction / primary Record approval. No personal-approval wording or member voting UI.

**U11-READER.** Naomi Chebet, Auditor, 10 Dec 2026. Header **Annual procurement plan**; description **Review the plan and its recorded evidence.** Stage from exact selected current/historical version. Same complete content. No decision statement/footer. Header has Download review pack. Historical variant shows **Historical plan — read only** immediately below context and enabled **View current plan** at upper right beside Download review pack.

**U11-RETURN.** Standard 520 px dialog over the actor’s exact review. Heading **What needs to change?** Context selector **Clinical training and deployment laptops for digital health rollout**; choices Whole plan and the two purchases. Required comment **Explain why the two departments need the same laptop specification before combining their purchases.** Beneath: **The plan will return to Procurement for correction and will be submitted for review again. The plan you reviewed and your comment will remain in history.** Footer Cancel / Return for correction.

**U11-STALE-EVIDENCE.** AO base with visible issue replacing “no blocking issues”: **The budget has changed since Finance checked this plan. Procurement must obtain a new funding check before you can adopt it.** Add separately labelled Checked Budget version and Current Budget version from owner fixture. Adopt absent; Return enabled. If evidence is unavailable, show **Required funding evidence could not be loaded.** with Try again above the decision area; Adopt absent.

**U11-LATE-ADOPTION.** AO after FY start. Visible facts Financial year started **1 Jul 2027**; Adoption date **[current server date]** supplied by scenario. Required multiline **Why is this initial plan being submitted after the financial year started?** placed immediately above decision statement. No editable backdate. Artboard cannot be generated until actual scenario date/reason are supplied.

**U11-UPDATE.** Complete Version 2 review. Under summary, open section **Changes** before purchase details; table Purchase; Field; Current value; Proposed value plus full source/monetary effects from UPDATE fixture. Decision history includes the linked current Version 1 separately. No unchanged scope is omitted merely because only one field changed.

**Visual check.** Every decision actor receives the same concise decision summary and can reach the same complete evidence. Only header, prior accountability, decision statement and actual buttons vary. A decision never precedes a hidden material issue, but ordinary evidence does not need to be simultaneously expanded.

**Next step and journey — added in v1.26.** Tracker §10.1A.1. The next-step line sits in the header region where v1.25 places the actor statement for orientation. The decision statement itself stays beside the buttons, because it states the consequence (KT-STD-001 v1.8 §2.6.5), not status. The **{Current stage}** token in the orientation line is removed, because the tracker carries it.

| Variant | Kind | Headline and sentence | Holder / since | Fixes | Replaces | Tracker |
|---|---|---|---|---|---|---|
| U11-HOPF | Your turn | **Sign and submit the annual plan** | — | Existing primary | Stage "Funding checked" | Preparation: Done. Funding confirmation: Done. Signature: Current, Charles Mutiso. Others: Not started. |
| U11-AO | Your turn | **Adopt and submit the plan, or return it for correction** | — | Existing actions | Stage "Awaiting Accounting Officer" | Stages 1–3: Done. AO adoption: Current, Amina Hassan. Others: Not started. |
| U11-STATUTORY | Your turn | **Approve the annual plan, or return it for correction** | — | Existing actions | Stage "Awaiting Cabinet Secretary" | Stages 1–4: Done. Cabinet Secretary approval: Current, Daniel Rotich. Others: Not started. |
| U11-STALE-EVIDENCE | Your turn | **Return the plan for a new funding check**. The existing issue stays in the Decision summary. | — | Existing **Return for correction** | As U11-AO | Stages 1–3: Done. AO adoption: Blocked, Amina Hassan. Others: Not started. |
| **U11-PLANNER** (new) | Waiting on someone | **Waiting for Amina Hassan (Accounting Officer) to adopt or return the plan** | Since 7 Dec 2026, 10:00 EAT | None | — | As U11-AO |
| U11-READER | Not involved | — | — | — | Orientation stage token | Markers for the exact selected Version. **Awaiting fixture:** the stage. |
| U11-READER, historical | Not involved | — | — | — | — | Not drawn; "Historical plan — read only" stays |
| U11-RETURN | Dialog: neither component; parent unchanged behind it | — | — | — | — | — |
| U11-COLLECTIVE / U11-LATE-ADOPTION / U11-UPDATE | Awaiting fixture (existing) | Follow the U11-STATUTORY and U11-AO patterns | — | — | — | Stage 5 label **Council decision** for U11-COLLECTIVE |

**U11-PLANNER** is Mercy Kilonzo viewing her own submitted Plan in the U11-READER layout, READY, 8 Dec 2026 before adoption. It exists because no v1.25 artboard answers where a submitted Plan stands for its Planner. Its content is otherwise U11-READER.

### 10.11 U12 — Exact departmental evidence

**Archetype and primary question:** Detail/evidence. **What exact departmental requirement and decision does this Plan use?** Level 1 is the pinned requirement identity, status and six source facts; Level 2 is funding, certification and Procurement disposition; Level 3 is record lineage. This is a reading surface, not a table-shaped workflow.

**Purpose:** Inspect the exact accepted source and departmental decision used by the reviewed Plan, then return to the same review context.

**Fixture — outside the artboard:** Opened from U11 laptop allocation: training laptops NDS-MOH-2027-0003 Revision 2; HRMD DPP Submission 1; Peter/Mercy evidence from §10.2; READY review context.

**Header.** Eyebrow/link **Return to plan review** above title. Title **Departmental requirement**. Full requirement title beneath; Need reference **NDS-MOH-2027-0003**; Revision **2**. Badge **Accepted for planning**. No mutation action.

**First section — Requirement details.** Show six labelled rows in order: Requirement title; Description; Expected result; Quantity **100**; Unit **Each**; Required by **31 Dec 2027**, using exact §10.2 text.

**Second section — Departmental funding.** Department **Human Resources Management and Development**; Budget line name **Digital health workforce development**; Budget line **MOH-BL-HWD-2027**; Amount **KES 20,000,000**.

**Third section — Certification and Procurement review.** Certification status **Certified**; Certified by **Dr Peter Kimani**; Capacity **Head of User Department**; Certified at **25 Nov 2026, 11:00 EAT**. Procurement disposition **Proceeding**; Accepted by **Mercy Kilonzo**; Accepted at **27 Nov 2026, 14:05 EAT**. Display the exact certification text from the owner fixture; if not supplied, the artboard waits rather than inventing it.

**Fourth section — Record details.** Collapsed. Expanded facts Departmental plan **DPP-MOH-HRMD-2027-001**; Submission **1**; DPP entry **DPPE-MOH-HRMD-2027-001**; Plan item **PPI-MOH-2027-033**; Plan version **1**.

Footer contains enabled **Return to plan review**, restoring the originating purchase.

**U12-NEWER-SOURCE.** Same pinned Revision 2 values. Above Requirement details show **A newer accepted requirement is available.** Under it enabled **View the newer requirement**. The current Plan evidence remains Revision 2; no value is replaced.

**U12-HISTORICAL-PLAN.** Header notice **Historical plan — read only**. Upper-right enabled **View current plan**. All source and decision values remain the exact historical snapshot. No business controls.

**U12-UNAVAILABLE.** Parent review retains allocation identity; replace detail content with **Departmental requirement evidence could not be loaded.** and enabled **Try again** plus **Return to plan review**. Do not show guessed or current source facts.

**Visual check.** The full six source facts appear before funding and decisions. The user can distinguish pinned source evidence from a newer source or current plan without losing review context.

**Next step and journey — added in v1.26.** Neither component (§10.1A.4). U12's own Return to plan review restores the parent review with its tracker and next-step line.

### 10.12 U13 — Publication evidence and recovery

**Archetype and primary question:** Detail/evidence with a focused next action. **What has happened to this approved Plan, and what—if anything—must I do now?** Level 1 is the four-step status and the one lawful next action; Level 2 is the evidence for the current step; Level 3 is transmission and recovery history. Do not present all recovery mechanics as parallel controls.

**Purpose:** Record external submission evidence, observe publication/activation separately and use only state-appropriate recovery.

**Fixture — outside the artboard:** Approved Plan Version 1. Primary AO fixture: Amina Hassan; 10 Dec 2026, 13:45 EAT before Treasury evidence. PUBLICATION variants supply later states.

**Header.** Title **Complete publication of the annual plan**; description **Record when the approved plan was sent to the National Treasury and attach the submission evidence.** Plan title, reference **PLN-MOH-2027-001**, Version **1**, state **Approved — Treasury submission details needed** on separate rows. Upper-right links **View approved plan**, **Download approved plan**, **Download Plan data** in that order; enabled.

**Publication status.** Four rows in this order: Plan approval **Approved**; Treasury submission **Details not yet recorded**; Website publication **Not started**; Use for procurement **This plan is not yet active**. Each row has its own label and state. Immediately below, enabled primary **Record Treasury submission** for Amina.

**U13-TREASURY-FORM.** Standard form over/after header. Read-only Plan/reference/version. Fields: Date and time sent **10 Dec 2026, 14:00 EAT**; Submission channel **Official correspondence**; Destination **National Treasury**; Dispatch/reference number **MOH/APP/2027/001**; Submission evidence file **Treasury-dispatch-evidence-example.pdf** labelled **Illustrative fixture file**. Checkbox **I confirm that this approved plan is the document submitted** starts unchecked. Footer Cancel / Record submission disabled; helper **Confirm the document match to record this submission.** Checked variant enables Record submission.

**U13-EVIDENCE-RECORDED.** Status rows: Plan approval Approved; Treasury submission Recorded; Website publication Not started/next actual state; Use for procurement Not active. Beneath Treasury row show separate Date/time sent **10 Dec 2026, 14:00 EAT**; Recorded by **Amina Hassan**; Channel **Official correspondence**; Destination **National Treasury**; Dispatch reference **MOH/APP/2027/001**. Enabled **View submission evidence**; no Record button.

**U13-SENDING.** Website publication **Publication is in progress**; Use for procurement Not active. Show attempt started at and responsible system from exact attempt fixture. No retry/check/manual-success button.

**U13-FAILED.** Website publication **The plan was not published**; Use for procurement Not active. Show confirmed failure time/code/message from owner fixture. For a separately authorised technical operator show primary **Retry publication**; for AO/reader show Responsible role **Authorised technical operator** and no button. Technical read alone does not create retry authority.

**U13-UNKNOWN.** Website publication **We could not confirm whether publication succeeded.** Below: **Check the existing attempt before trying again.** Authorised technical operator gets **Check publication result** only. No Retry or manual success.

**U13-ACTIVE.** Website publication **Published**; Use for procurement **Current plan**. Separately labelled Publication acknowledged at **10 Dec 2026, 15:00 EAT**; Activated at from exact owner fixture. Enabled **View published plan** / **View current plan**. No preparation action.

**U13-PUBLISHED-HELD.** Website publication Published; Use for procurement **Published, but not available for new procurement**. Show exact failed mandatory check above actions. Planner gets **Prepare a corrected plan** if current guards allow; Current predecessor and action **View current plan** are separate.

**U13-UNPUBLISHED-DEFECT.** State **Publication is on hold**. Show exact confirmed defect/reason and evidence that no publication occurred. AO gets **Request withdrawal for correction**. No action for unknown/published content.

**U13-WITHDRAWAL-REQUEST.** State **Withdrawal requested — awaiting Cabinet Secretary**. Show request reason, Requested by **Amina Hassan** and request time from the exact withdrawal fixture. Daniel’s authority variant shows one enabled primary action: **Withdraw for correction**. No second business action appears.

**U13-WITHDRAWN.** State **Withdrawn for correction**; Plan approval **Historical approval retained**; Website publication Not published; Use for procurement Not active. Planner gets **Continue correction**; readers get **View withdrawn plan** only.

**U13-CORRECT-EVIDENCE.** Form heading **Correct submission details**. First block **Previous submission evidence** read-only with every recorded field. Second block repeats editable fields. Required **Reason for correction** blank. Footer Cancel / Save corrected details, disabled until a reason/change is entered. No overwrite language.

**U13-WITHDRAWAL-REQUEST-DIALOG.** AO dialog over U13-UNPUBLISHED-DEFECT. Header **Request withdrawal for correction**. Show exact approved Plan name, reference and Version **1**; Publication status **Confirmed not published**. Required **Reason for withdrawal** starts blank. Text **The approved plan will remain in history. If the request is approved, a correction draft will repeat the required review and approval.** Footer left **Cancel**; right primary **Request withdrawal for correction**, disabled until a valid reason is entered.

**U13-WITHDRAWAL-DECISION-DIALOG.** Cabinet Secretary dialog over U13-WITHDRAWAL-REQUEST. Header **Withdraw this plan for correction?** Show the exact Plan name, reference, Version **1**, request reason, Requested by **Amina Hassan**, request time and Publication status **Confirmed not published**. Text **The approved plan will remain in history. A correction draft will be prepared and will repeat the required review and approval.** Footer left **Cancel**; right primary **Withdraw for correction**, enabled. No editable reason and no return action.

**Visual check.** Approval, external submission, publication and activation are four distinct rows. Each state exposes exactly one valid recovery path and never treats unknown as failure.

**Next step and journey — added in v1.26.** Tracker always in **reduced** form: **Stage 6 of 7: Publication — {holder}**. The four publication status rows stay as the Level 2 working region, because they are the working detail of stage 6, not a second tracker. The header state row (for example "Approved — Treasury submission details needed") is replaced by the next-step line.

| Variant | Kind | Headline | Holder / since |
|---|---|---|---|
| U13 | Your turn | **Record the Treasury submission** | — |
| U13-TREASURY-FORM, unchecked and checked | Neither component; a form state of U13 | — | — |
| U13-EVIDENCE-RECORDED | Waiting on someone | **Waiting for website publication** | System; since **Awaiting fixture** |
| U13-SENDING | Waiting on someone | **Publication is in progress** | Responsible system and start time from the existing attempt fixture |
| U13-FAILED, authorised technical operator | Your turn | **Retry publication** | — |
| U13-FAILED, AO or reader | Waiting on someone | **Waiting for an authorised technical operator to retry publication** | Since: failure time from the existing fixture |
| U13-UNKNOWN, authorised technical operator | Your turn | **Check the publication result** | — |
| U13-UNKNOWN, AO or reader | Waiting on someone | **Waiting for an authorised technical operator to check the publication result** | Since: attempt time from the fixture |
| U13-ACTIVE | Done | **In force since {Activated at}**; the tracker reads **Stage 7 of 7: In force** | Activated at from the existing owner fixture |
| U13-PUBLISHED-HELD, Planner | Your turn | **Prepare a corrected plan** | — |
| U13-UNPUBLISHED-DEFECT, AO | Your turn | **Request withdrawal for correction** | — |
| U13-WITHDRAWAL-REQUEST, AO | Waiting on someone | **Waiting for Daniel Rotich (Cabinet Secretary) to decide the withdrawal** | Since: request time from the existing fixture |
| U13-WITHDRAWAL-REQUEST, Daniel | Your turn | **Withdraw the plan for correction** | — |
| U13-WITHDRAWN, Planner | Your turn | **Continue the correction**; the tracker restarts at Preparation on the correction Draft | — |
| U13-CORRECT-EVIDENCE and both U13 dialogs | Neither component | — | — |

### 10.13 U14 — Procurement progress

**Archetype and primary question:** Monitoring register with drill-down. **Which planned purchases have authorised procurement coverage, and where is attention needed?** Level 1 is coverage, stage and holds; Level 2 is proceeding evidence and uncovered scope; Level 3 is Planning lineage and owner-supplied actuals. Summary rows must scan as statuses, not as a dense evidence ledger.

**Purpose:** Show how much of each current Plan purchase is covered by authorised requisitions and what operational evidence is available.

**Fixture — outside the artboard:** Mercy; Current Plan Version 1; EXECUTION initial and later isolated profiles; exact clock and proceeding identities supplied per profile.

**Header.** Title **Procurement progress**; description **Follow authorised procurement against the current annual plan.** Context Plan title; reference **PLN-MOH-2027-001**; Version **1**; Status **Current plan**; Financial year **FY 2027/28**. No Create Requisition/Tender action.

**Purchase summary.** One row per exact purchase with Purchase; Planned quantity/value; Covered by authorised requisitions; Procurement stage; Action. Do not create a Completion column unless an owning module supplies authoritative completion evidence. Initial values:

- Infrastructure: Planned **1 Programme / KES 80,000,000**; Covered **0 / KES 0**; Procurement stage **Not started**.
- Laptops: Planned **250 Each / KES 50,000,000**; Covered **0 / KES 0**; Procurement stage **Not started**.

Show enabled **View purchase details**. A material hold appears in the row. Internal original allowance and proceeding identities remain under **Planning evidence**; no generic “remaining” number replaces quantity/value facts.

**U14-PARTIAL.** Laptop row: Covered **100 Each / KES 20,000,000**; Not yet covered **150 Each / KES 30,000,000**; stage from the exact Requisition/Tender owner evidence. No completion placeholder is shown when tracking is unsupported.

**U14-FULL-COVERAGE.** Laptop Covered **250 Each / KES 50,000,000**; Not yet covered **0 Each / KES 0**; two proceeding details under **View procurement evidence**. Tender publication never appears as delivered or completed.

**U14-ACTUALS.** Under a purchase place table Milestone; Approved date; Actual date; Days after approved date. Use only owner-supplied actuals. Missing supported actual displays **No date recorded**; unsupported fields are omitted; not-applicable displays **Not applicable** only where the applicable owner explicitly supplies that state. Beneath, separate Stage durations table From; To; Planned elapsed days; Actual elapsed days; Difference, only when both actual endpoints exist. Forecast comparison is absent from the MVP.

**U14-HOLD.** Visible above affected purchase: **New requisitions are on hold while these requests remain unresolved.** Show unresolved request count and exact links to U16. Existing proceedings remain listed; no auto-restart action.

**Visual check.** The first view answers what is planned, what is covered and what has started. Completion appears only from authoritative evidence. Different units never combine; unsupported fields are omitted rather than filled with intimidating placeholders.

**Next step and journey — added in v1.26.** Neither component (§10.1A.4); U14 is a monitoring register. Its rows keep their own coverage and hold statements.

### 10.14 U15 — Update expected dates

**MVP decision:** U15 is not implemented in this release. Planner-managed forecast cascades require reliable milestone ownership and downstream actuals that are not yet established. Showing a multi-row forecasting tool without those integrations would create work whose accuracy cannot be sustained.

The approved schedule remains readable in U09/U11. When a downstream module supplies an authoritative revised expected date, U14 may display it as read-only evidence with its source. A future forecast facility must preserve approved dates and actuals, identify the owning event, preview any cascade and require a reason. It requires separate approval, complete owner integration and representative-user testing before implementation. No placeholder **Update expected dates** action appears in the MVP.

### 10.15 U16 — Plan correction requests

**Archetype and primary question:** Correction workspace with focused detail. **What must change, what is held, and what is the lawful next step?** Level 1 is the issue and consequence; Level 2 is affected scope and permitted resolution; Level 3 is request identity, versions and history. Internal orchestration never leads the first view.

**Purpose:** Tell the Planner what downstream issue affects the purchase, what work is held and what lawful correction is available. Preserve separate requests and holds without exposing internal orchestration.

**Fixture — outside the artboard:** Mercy; current laptop item; UI-COR-01 Open and UI-COR-02 In progress; isolated EXECUTION profile.

**Header.** Title **Planning change required**. Beneath: purchase **Clinical training and deployment laptops for digital health rollout**; reference **PPI-MOH-2027-033**; Current plan version **1**. No header action.

**Visible notice.** **New requisitions for this purchase are on hold until the planning issue is resolved.** In the authorised-requisition profile add: **A requisition has already been authorised. Extra requirements must be added as a separate purchase in a plan update.**

**Issues table.** Columns What needs to change; Status; Requested from; Action. Row 1: **Confirm the funding allocation**; Status **Needs review**; Requested from the exact Requisition/Tender owner; action **Review issue**. Row 2: **Correct the description without increasing the planned scope**; Status **Correction in progress**; action **Continue correction**. Request IDs, exact versions and timestamps remain in issue detail/history.

**U16-OPEN-DETAIL.** Show Full requested change; Affected purchase; Requested by; Requested at; Originating record. Footer action **Prepare plan correction**. No manual scope unlock.

**U16-COMPLETE.** Request detail includes Correcting Plan; Version; Activation date. Enabled **Record correction completed** only when that referenced Plan is Active. Dialog states the exact correcting Plan and request; footer Cancel / Record correction completed.

**U16-NO-CHANGE.** Dialog **Close without a plan change**; exact request and origin; required Reason **The reviewed allocation is correct; no plan change is required.** Footer Cancel / Close request. This resolves only that request.

**U16-MULTIPLE.** One issue completed while the other remains unresolved. Hold notice remains and states **1 issue still needs attention**. No “Resume requisitions” action.

**U16-ADDITIONAL-REQUIREMENT.** Visible section beneath requests titled **Requirement not yet in the current plan**. Exact additional source from owner update: Digital Health; **50 Each**; **KES 10,000,000**; accepted DPP update reference required from fixture. Three labelled results: Annual plan **Not yet in the current annual plan**; Procurement **No procurement recorded**; Completion **No completion evidence**. Action **Add as a separate item in a plan update** opens/points to eligible pending work; it does not create an update on navigation.

**U16-PERMANENT-SCOPE.** Resolved request with permanent restriction retains visible affected item, restriction, origin/evidence and remaining allowed actions; no restored-scope badge.

**Visual check.** The Planner sees the required change and lawful next action before request mechanics. Each request keeps its own evidence in detail. The hold remains until every issue resolves; a stopped downstream process never appears restarted by Planning.

**Next step and journey — added in v1.26.** Neither component (§10.1A.4). Each request keeps its own status text.

### 10.16 C01–C04 — System setup ownership

**Purpose:** Direct an authorised maintainer to the exact CFG-owned task without redefining setup inside Planning.

**Fixture — outside the artboard:** Administrator or System Manager; use the matching approved CFG v0.11 §10 fixture and route *(Version reference reconciled in v1.27; see the note after the §1.2 table.)*; Planning supplies only the business-side error/link variants below.

C01–C04 are owner surfaces, not Planning artboards. Generate or revise them from KT-STD-001 v1.7 §§2 and 10 plus CFG v0.11 §10. *(Version reference reconciled in v1.27; see the note after the §1.2 table.)* Their archetype is setup/maintenance: lead with the setting that blocks work, its consequence and the authorised repair task; keep configuration provenance and history secondary. Do not combine this Planning design section with CFG’s design section or copy a partial setup form into Planning.

**Planning-side missing-setting panel.** On the affected Draft/review, place the concrete issue immediately above the affected action. Show separate labels Setting; Affected action; Responsible role. If the actor also holds authorised setup access, place enabled **Open System setup** below and route to the exact CFG section. Otherwise show **Ask your KenTender administrator to complete this setting.** No disabled setup controls appear in Planning.

Named variants:

- **C01-ROUTE-MISSING:** Setting **Annual Plan approval authority**; Affected action **Adopt and submit**; Responsible role **Administrator or System Manager**.
- **C02-DPP-CLOSED:** Setting **Departmental plan submissions**; Affected action **Submit initial departmental plan**; responsible role as above. Existing permitted Draft save and returned correction remain visible.
- **C03-METHOD-MISSING:** Setting **Applicable procurement method rule**; affected purchase exact title/reference; Affected action **Send plan for governance review**.
- **C04-SCHEDULE-MISSING:** Setting **Applicable procurement schedule**; affected purchase exact title/reference; Affected action **Submit annual plan**.

Technical readers follow KT-STD §3A.6 for Planning data. Setup maintenance follows CFG/AUTH. Publication retry appears in U13 only to a separately authorised technical operator; it is not acquired from technical read.

**Visual check.** The business page names the missing setting and owner in place. Setup uses one complete owner contract and gains no Planning-local registry or approval workflow.

**Next step and journey — added in v1.26.** Owner surfaces carry neither component. The Planning-side missing-setting panel above becomes the blocker in the host screen's next-step block, with the same Setting, Affected action and Responsible role content and the same fix (§10.1A.5, D3). It is not drawn as a separate panel beside a next-step block.

### 10.17 U21 — Shared states and supporting actions

**Purpose:** Render loading, access, empty, failure, stale and focused confirmation states without ambiguous controls.

**Fixture — outside the artboard:** Each variant is independent and names its base surface/actor below.

**Page-state placement.** These are state variants of the parent archetype, not generic blank cards. Preserve the parent page's orientation and hierarchy wherever disclosure is authorised. Loading, denied, masked and load-failure replace protected page content. Empty and filtered-empty retain their authorised header/filters. Command errors appear below record context and above the affected form/content. A focused confirmation uses the standard 520 px dialog over its exact parent.

**U21-LOADING-WORKSPACE.** Parent/fixture: U01; verdict/data pending. Visible text **Loading procurement planning…** Composition/actions: Actual-structure skeleton only; no stale rows/actions.

**U21-LOADING-REVIEW.** Parent/fixture: U11; exact review pending. Visible text **Loading plan review…** Composition/actions: Review skeleton only; no Plan title or decision controls until authorised data arrives.

**U21-DENIED.** Parent/fixture: Ordinary actor with no Planning responsibility; never technical reader. Visible text **You do not have access to Procurement Planning.** Composition/actions: Below: This area needs one of these responsibilities: Departmental Author, Head of User Department, Procurement Planner, Head of Procurement Function, Finance Confirmation Officer, Accounting Officer, configured statutory decision-holder or Auditor. Then: Ask your KenTender administrator to check your assignment in System setup. No protected content/action.

**U21-MASKED.** Parent/fixture: Ordinary actor without existence disclosure; never technical reader. Visible text **This record is not available to you.** Composition/actions: Only enabled Go to procurement planning. No title/reference.

**U21-LOAD-FAILURE.** Parent/fixture: Authorised U01 or U11 read failed. Visible text **Procurement Planning could not be loaded.** Composition/actions: Below: Try again. If the problem continues, contact support. Enabled Try again; no guessed empty state or unsupplied support reference.

**U21-NO-TASKS.** Parent/fixture: U01 Mercy with current plan and no action. Visible text **No additional content.** Composition/actions: Omit Your actions section completely; current plan remains.

**U21-FILTERED-EMPTY.** Parent/fixture: U07 Requirements ready to add with unmatched search. Visible text **No requirements match this search.** Composition/actions: Retain filters; enabled Clear filters; no Add action.

**U21-CHANGED-ACTION.** Parent/fixture: Any open decision whose record/authority changed. Visible text **This action is no longer available. The record or your authority changed after you opened it.** Composition/actions: Enabled Refresh; decision action absent; retain only currently authorised content.

**U21-SAVE-FAILED.** Parent/fixture: U02/U07/U09 editable form. Visible text **Your changes were not saved.** Composition/actions: Retain authorised inputs; show exact field/general errors; same save action available for a new explicit attempt under existing idempotency rules.

**U21-UNCERTAIN-DECISION.** Parent/fixture: U06/U10/U11/U13 command result unknown. Visible text **We could not confirm the result. Checking the existing request…** Composition/actions: All conflicting decision/write actions disabled; preserve exact displayed snapshot until original result resolves.

**U21-HISTORICAL.** Parent/fixture: U11 reader exact older Plan Version. Visible text **Historical plan — read only.** Composition/actions: No mutation; enabled View current plan only when exact current target is authorised.

**U21-LATE-ACTIVATION.** Dialog over the initial plan activation context. Heading **Explain late start of the annual plan**. Separate read-only facts Financial year started **1 Jul 2027**; Plan became active **2 Jul 2027, 09:00 EAT**. Required multiline Explanation **Publication acknowledgement was received after the financial year began.** Footer Cancel / primary Record explanation. No editable date or update-plan variant.

**U21-CANCEL-UPDATE.** Dialog over U07-UPDATE with exact Plan/reference/Version 2. Heading **Cancel this plan update?** Text **The current plan and existing procurement will remain unchanged.** Required Reason from UPDATE fixture; because no exact reason is supplied in §10.2, generation waits for it. Footer **Keep update** / primary **Cancel plan update**.

**U21-REMOVE-DRAFT-ITEM.** Dialog uses U09-REMOVE exact laptop item and source rows. If a server guard blocks removal, replace the primary action with the concrete visible reason and no remove button; do not draw a disabled action without its explanation.

**U21-TECHNICAL-WORKSPACE.** Administrator or System Manager; same FY and BASE data. Use U01 with all authorised plans/departments site-wide and row actions renamed **View**. Create/start/continue/edit/decision actions absent. Technical search is the shared owner surface, not a Planning-specific duplicate.

**U21-TECHNICAL-DETAIL.** Administrator/System Manager on any U02/U06/U07/U09/U10/U11/U13/U16 route. Render the same full facts for the exact status; all business mutation/decision controls absent. Read/navigation disclosures and exact evidence links remain. The U13-FAILED and U13-UNKNOWN authorised-operator variants show the separately granted publication-recovery command stated in those variants. Every other technical-reader variant omits it.

**Visual check.** Every state has one definite action set. Technical readers never receive ordinary denied/masked treatment, and technical read never displays a business decision button.

**Next step and journey — added in v1.26.** Loading, denied, masked and load-failure states replace protected content, including both components. U21-TECHNICAL-WORKSPACE carries neither, as U01. U21-TECHNICAL-DETAIL follows §10.1A.6. The dialogs U21-LATE-ACTIVATION, U21-CANCEL-UPDATE and U21-REMOVE-DRAFT-ITEM carry neither; their parent pages are unchanged behind them.

### 10.18 Complete design inventory and review gate

Each row is required design evidence. A variant marked as waiting for an exact fixture is not sent to design until that input exists.

| Family | Required compositions |
|---|---|
| U01 | Planner BASE; current; current+update; no plan; Author Draft/no plan; HoD action; direct-task navigation evidence. From v1.26: current+update over budget and waiting on budget revision (v1.27: D2 decided; UPDATE-OVER-BUDGET fixture in §10.2). |
| U02–U05 | Author Draft; funding; exclude/excluded/reinclude; direct add/edit; HoD certification; correction; all-excluded; closed initial intake; correction after close; accepted+update. |
| U06 | BASE validation with type-to-category derivation; return; excluded; missing classification; stale source with exact change; segregation; accepted classifications; correction panel; corrected history/stale attempt. |
| U07 | Formed Draft; unallocated; one/two selected; waiting Finance with exact request; Finance complete; update with exact reason/pending inputs. From v1.26: every variant carries §10.1A.3 Budget fit and Finance confirmation; new U07-UPDATE-OVER-BUDGET and U07-WAITING-BUDGET-REVISION (v1.27: D2 decided; UPDATE-OVER-BUDGET fixture in §10.2). v1.27 corrects the BASE Schedule result and the BASE next-step content. |
| U08 | Combine; keep separate; incompatible with exact lines; duplicate/cohort failure with exact evidence. |
| U09 | BASE/READY with classification provenance; invalid schedule; remove; locked with exact requisition; source correction with exact values; classification correction with exact old/new values; classification correction on a scope-locked item only when exact downstream evidence/route is supplied. |
| U10 | Within approved; low availability; over approved; changed; return; reassessment with revised basis; history. |
| U11 | HOPF; AO; statutory; collective with exact recorder; reader/current/historical; return; stale/unavailable evidence; late adoption with exact date/reason; update with exact differences. From v1.26: U11-PLANNER. |
| U12 | Pinned source; newer-source notice; historical plan; unavailable. |
| U13 | Missing/recorded Treasury evidence; form unchecked/checked; sending; failed AO/technical; unknown AO/technical; Active; published-held; unpublished defect; withdrawal request/decision/withdrawn; correction form/dialog. |
| U14 | Initial; partial/full coverage with exact proceeding IDs; actual/missing/unsupported; hold. |
| U15 | Deferred future facility; no MVP composition or action. |
| U16 | Two requests with exact origins; detail; correcting Plan; no-change; multiple unresolved; additional requirement with exact DPP; permanent scope. |
| C01–C04 | Generate from CFG v0.11 §10; Planning-side missing route/intake/method/schedule panels only. |
| U21 | Loading; denied; masked; failure; no tasks; filtered empty; changed; save failure; uncertain; historical; late activation; cancel update with reason; remove; technical workspace/detail. |

Before design generation confirm the KT-STD-001 v1.7 §§2 and 10 gates, including named archetype, primary question, Level 1–3 hierarchy, first-view content, definite action hierarchy and representative-user comprehension. Additionally: reconcile each fixture against current NDS v1.14, CFG v0.13, BUD v1.10 and STR v1.8 owner facts (v1.26 read: CFG v0.11, BUD v1.9); keep the canonical 27 November DPP acceptances distinct from NDS’s 4/5 January exclusion profiles; never depict the May 2027 schedules as legally ready while CFG-XD-001 remains unresolved.

From v1.26, also confirm the KT-STD-001 v1.8 §2.8 additions: each record-screen variant has the next-step kind, headline, holder and fixes stated in §§10.3–10.17; the tracker and next-step block follow every §2.9.3 restraint rule and name the elements they replace; and the first working region stays within the first 1440 × 1024 view. A **Pending D{n}** variant is not sent to design until §10.1A.7 records the decision.

Each artboard ends its review with: named archetype and primary question; correct top-to-bottom ordering; a visibly dominant Level 1; exact visible facts; definite action states; material issues outside collapsed detail; every interactive control mapped in §11.9; no invented identity/time/source/legal value. Compare the first viewport at 1440 × 1024 and the complete page at desktop and narrow layouts, then run the representative-user tasks in §14.5. A complete contract is not usability evidence.

## 11. Functional interaction requirements — excluded from design prompts

### 11.1 Navigation, full review and export

1. Resolve authorisation with data before painting content. A denied module remains a route-addressable inline state. Mask unauthorised record existence. Counts and rows use the same scope and snapshot.
2. Exact Version context is carried through item/source/evidence drilldown, browser history and review-pack download. Back returns to the same section, row and scroll position where practical. A link to a newer source never replaces the reviewed source silently.
3. The review pack includes all governed values, field mappings and an evidence index for that exact Version, visibly labelled with its approval status. Optional inaccessible attachments use the owning access policy; they do not disappear without indicating that required review evidence is unavailable.
4. Decision controls depend on server authority/state/readiness, not whether the user opened every accordion or downloaded the pack. No click-through attestation is added.
5. All full-width tables wrap long names. Source/package tables use a summary and accessible detail instead of arbitrarily omitting mandatory fields or forcing a 17-column grid into the viewport.
6. Domain-invalid positive decisions are unavailable with a specific reason. Corrective return actions retain their own predicates; stale source/funding/Strategy evidence must not disable the action needed to correct it.
7. Visible semantic section links, keyboard-operable disclosures, focus restoration and accessible error summaries follow KT-STD. Sticky action areas must not obscure content or keyboard focus.

### 11.2 Departmental and package work

Initial DPP creation/submission follows the intake flag and close instant; accepted departmental updates and permitted corrections follow their distinct lifecycle. An accepted Need has complete source facts and is either proceeding or explicitly not proceeding. Funding/classification completeness applies only to proceeding entries. Direct requirements are legitimate first-class departmental requirements, not bypasses.

Single-source formation has no redundant radio choice. Combining checks all approved compatibility conditions. New accepted requirements appear as eligible unallocated sources or as clearly separate pending inputs; no second candidate is created by reads/events. Source correction does not silently rewrite allocated Draft content.

Saving package edits recalculates schedule/readiness from the resolved profile. Missing rules permit only Draft operations that the domain allows. Fixed Single year is not an editable choice. Required method evidence appears from the verified profile; conditions and evidence are reviewed rather than presumed satisfied by a threshold.

Scope lock is authoritative from first Requisition authorisation and checked at every relevant server command. A copied successor row cannot regain an add-source action or reset allowance. A UI-disabled control is not the enforcement mechanism. Only source facts owned by Planning can be corrected there.

### 11.3 Finance and governance

Finance sees one current review per Version and immutable history. Approved line amounts are blocking affordability limits; current available is advisory. Every decision uses Budget-owned atomic basis validation and creates no financial reservation. Active reassessment is clearly labelled as financial evidence for unchanged approved content.

HOPF preparation, AO adoption and statutory approval use the same complete Plan content and distinct commands. Actor/capacity and exact Version are rechecked at commit. Same-user conflicts survive copied corrections. Route changes and new actor assignments do not erase incompatible historical actions.

Board/Council evidence records collective authority and required resolution reference, not merely the login user's signature. No generic committee or additional approval is inferred from a visual card. New confirmation text in §10 is UI wording for the agreed action, not a new legal certification requirement.

### 11.4 Publication and recovery

The Treasury form records external dispatch, not Treasury approval. Each successor has its own evidence. Invalidating that evidence holds new transmission and reconciles outstanding attempts. A technical Check publication result may only invoke the authoritative adapter's read/reconciliation; it cannot set success manually. Its exact adapter contract is a prerequisite.

Only confirmed-unpublished content may follow AO request/statutory withdrawal. Unknown publication state cannot offer withdrawal or a competing replacement candidate. Acknowledged but invalid content remains Published — activation held and exposes a correction successor without obtaining procurement eligibility. Preserve an existing Active predecessor separately.

The UI never hides external publication merely because activation failed. Public-view/PDF/JSON identity is exact and operational updates remain separate. The review pack is not confused with the approved publication or Treasury attachment.

### 11.5 Execution evidence and corrections

Proceeding evidence belongs to the owning Requisition, Tender or later operational record and exact source allocations. Selection of a Plan Item does not grant coverage to later requirements. The MVP summary identifies planned scope, authorised coverage and current procurement stage. No sum of unlike units, no completion badge from publication and no placeholder field for evidence the system cannot obtain.

Planning does not ask the Planner to maintain milestone forecasts in this release. U15, forecast cascades and forecast-driven reminders remain future facilities under §15.3. Owner-supplied actual or expected dates may be shown read-only with their source; they never rewrite the approved schedule.

Multiple correction requests share one effective item hold until every request reaches a permitted terminal outcome. The scope lock remains independently effective afterwards. Resolved must identify an Active correction; Draft correction is not resolution. A stopped Requisition is never auto-restarted.

### 11.6 Configuration

Complete first-run API inputs and read projections for route and county applicability. Required configuration is visible and editable through existing authorised setup actions. Funding sources/reference/profile readers use owning services, not deep table access. CFG-authorised staff record actual source-verification evidence; no checkbox alone establishes legal correctness.

The fifth tab groups the agreed settings; final owner schemas and source-verification permissions are defined by approved CFG v0.13 (v1.26 read: CFG v0.11) and must be implemented through that owner. Effective dates, immutable referenced Versions and the applicable-date resolver are not replaced by ordinary overwrite forms. If a reference is already used, an update creates a new Version.

Each module intake flag is independent; open/close uses its own control, single-open-year rule and audit. At command time, reaching the close instant blocks applicable initial submissions even before the hourly cleanup job runs. Closing the window does not make a previously accepted DPP disappear or forbid permitted updates.

### 11.7 Minimal task steps and complete decisions

Assigned task links land directly on their exact review. Funding edits expand beside the departmental requirement. Draft corrections created by Return are the default actionable destination; the original stays in History. One-source addition has no redundant formation choice. Multiple selections explicitly choose Separate/Combined and preview the effect. No business mutation occurs merely from a page load, evidence disclosure or newer-record link.

Approval/signature/adoption text sits beside its specific action and identifies the actual consequence. Preserve HoD and Treasury acknowledgements; do not add a generic checklist of opened screens, a forced download or duplicate confirmation dialog. An explicit decline/return still records its required reason. Do not invent a HoD return task, HOPF approval, per-member collective vote, assignee picker or Planner-to-HOPF approval stage.

New departmental return feedback follows §4.4; Plan/Finance return contexts follow §7.6. A single clear comment is stored once; old distinct problem/correction fields remain accessible as historical evidence. Migration must account for every required field/consumer before removing old input requirements. Changing visible text alone cannot change a wire enum or legal/accountability attestation already signed.

### 11.8 Readability, failure recovery and scope

Supporting details use §9.3’s structure, not a single paragraph containing actor, amount, date and status. Content groups may be disclosed; material exceptions must remain visible. No routine label requires understanding “candidate”, “source cohort”, “rebase”, “lineage”, “payload” or “stale” to finish the task. Technical terms remain appropriate in authorised diagnostic evidence when needed.

Preserve still-authorised unsaved input across validation/save failure. Report unsaved versus saved state accurately; do not introduce unsupported autosave or navigation-triggered writes. On ambiguous command response, query/replay the original command identity under existing idempotency rules before offering another decision. Never manufacture success or create duplicate approval tasks. If authority is revoked, clear protected presentation as required and do not retain inaccessible content in the browser merely to preserve edits.

Use route-level and record-level authority before rendering. Administrator/System Manager technical read follows KT-STD-001 v1.7 §3A.6, including shared search and conformance registration; Auditor/business reads retain their owner scopes. Read access is not business-decision authority. Deep-link, export and optional evidence access enforce the same protected snapshot. Do not remove server checks to make a sketch easier to use.

### 11.9 Complete design-to-interaction map — excluded from design prompts

This table is the behavioral counterpart to §10. It changes no command, state or permission. Every mutation continues to use §7’s envelope, expected version, idempotency and current server checks.

| Screen / control | Destination or result | Existing contract and safeguard |
|---|---|---|
| U01 Financial year/filter controls | Refresh authorised work/current plan for selected local view. | §11.1; never authority or stored global context. |
| Start/Continue/View departmental plan | Open exact U02–U05 DPP root/version in current permitted mode. | §§11.1–11.2; no Annual Plan creation from page load. |
| Continue/View/Prepare plan update | Open exact U07 initial/current/successor; Prepare invokes existing guarded successor start. | §§5.2, 11.1–11.2; current Plan remains active. |
| Review reserved procurement / section links | Move focus to exact U09/U07 section on same Plan/version. | Navigation only; no waiver or state change. |
| Request budget revision from {name} (v1.27) | Invoke `RequestBudgetRevision` for the exact over-budget line of the displayed Draft Version; on success show U07-WAITING-BUDGET-REVISION. | §7.2, §7.7; line and amounts server-derived; idempotency key; `PLN_BUDGET_REVISION_NOT_REQUIRED` / `PLN_BUDGET_REVISION_ALREADY_REQUESTED` shown in the error summary; no Budget or Plan state change. |
| Estimated cost on the funding panel (v1.30) | Starts from the accepted requirement's estimate; the preparer may change it; Save details saves it. | §7.2 SaveNeedFunding; §4.3 prefill and change rules; `PLN_MONEY_PRECISION_INVALID`; no change to Budget, Need or Plan state. |
| Reduce a purchase (v1.27) | Move focus to the Purchases section of the same Draft Version. | Navigation only; editing then uses existing Edit purchase / SavePlanItem. |
| Choose a procurement method (v1.27) | Open exact U09 for the named purchase with focus on Procurement approach. | Navigation only; method is saved by existing SavePlanItem. |
| Tracker upstream link {n} departmental requirements included (v1.27) | Move focus to Requirements ready to add on the same Plan Version. | Navigation only. |
| Tracker downstream link {n} requisitions raised (v1.27) | Open U14 for the current Plan. | Navigation only; count from REQ owner evidence. |
| Create update — plan next step, U01 task and spotlight (v1.28) | Invoke the existing `CreateDepartmentalPlanUpdate` on the accepted plan; the new Draft takes the pending Needs in. | §§5.1.3, 7.2; Author/HoD only; clears the §7.7 item once the update carries the Need. |
| Enter/Review funding details | Expand U03 for exact DPP entry; Save details performs governed entry update. | §§7.2, 11.2; Budget owner validation; no Need amount mutation. |
| Correct source requirement | Open exact authorised NDS source route, preserving unsaved-work warning/context. | §§7.3, 11.2; separate NDS review; no silent source substitution. |
| Exclude / Include requirement | Open reason or renewed-funding form and commit DPP entry disposition. | §5.1.4; reason required for exclusion; cleared funding not auto-restored. |
| Add/Edit/Remove direct requirement | Open U04; create/update/remove permitted DPP direct entry. | §§4.3, 7.2, 11.2; no Need/bypass field. |
| Save DPP draft | Persist permitted DPP content without submission. | §7.2; current token/coverage checks. |
| Submit/Resubmit departmental plan | Certify and submit exact DPP version after checked acknowledgement. | §§5.1, 7.2; HoD authority/coverage; correction exception explicit. |
| Accept DPP / Return to department | Commit Planner validation or open contextual return reason. | §§5.1, 6.3, 7.2, 7.6; return remains usable when positive evidence stale. |
| View source classifications | Open exact accepted DPP classification evidence and history for every source without changing the purchase. | §§4.4, 7.1, 11.1; preserve accepted and corrected values separately. |
| Correct classification / Save classification correction | Open U06 correction panel, derive Category from the new governed type and append the immutable correction. | §§4.4, 5.1.6, 7.2; exact authority/head check; no departmental or Plan mutation. |
| Add selected requirements | One source forms one item; multiple compatible sources open U08 then form exact items. | §§5.2, 7.2, 11.2; complete-source allocation, cohort and scope guards. |
| Keep separate / Combine / Add to plan | Preview and commit exact formation; reason required for aggregation. | §§4.6, 5.2; preview is non-mutating; no partial quantities. |
| Edit purchase / Save draft | Open U09 and persist permitted PlanItemVersion/PlanVersion facts. | §§5.2, 7.2; owner services and current tokens. |
| Remove item and return requirements | Open U09 dialog; dissolve only eligible Draft item. | §5.2/5.4; no Budget release; authorised procurement blocks scope reset. |
| Adjust schedule / Save schedule edits | Show/recalculate exact schedule and persist permitted Draft values. | §5.5.1; source deadlines/rules unchanged. |
| Send to Finance / Request new funding check | Create exact U10 task/reassessment for frozen Plan basis. | §§5.3, 7.2; no reservation or automatic approval. |
| View Finance line details | Expand exact frozen line/source/current-balance evidence. | Read only; no task-basis substitution. |
| Confirm plan funding / Return to planner | Commit affordability or contextual whole-plan return. | §§5.3, 6.3, 7.2/7.6; excess blocks confirm, not return. |
| Sign and submit Annual Plan | Record HOPF preparation signature and create AO task. | §§5.2, 6.2, 7.2; no HOPF approval state. |
| Adopt and submit | Record AO adoption and create one configured statutory task. | §§5.2, 6.1, 7.2; current positive checks/segregation. |
| Approve APP / Record collective decision | Commit exact statutory decision and resolution evidence where required. | §§5.2, 6.1, 7.2; no personalisation of collective decision. |
| Return for correction | Open U11 reason/context form and return whole reviewed version. | §§6.3, 7.6; targeted comment is not partial approval. |
| Download review pack / Plan data | Export exact authorised reviewed snapshot/status. | §§7.1, 11.1; same scope/content, no prerequisite to decide. |
| View departmental/source/current/historical evidence | Open U12 or exact owner route; Return restores section/focus. | §§7.3, 11.1; pinned version never silently replaced. |
| Record/Correct Treasury submission | Open U13 form and append/correct exact external evidence. | §5.5.2; acknowledgement required; prior evidence preserved. |
| Retry publication / Check publication result | Retry same approved content after confirmed failure, or reconcile existing unknown attempt. | §5.5.2; separately authorised technical command; unknown is not failure. |
| Request/Withdraw for correction | Open reason/decision form and create governed correction only for confirmed-unpublished content. | §5.5.2.3; approval retained historically; full governance repeats. |
| View procurement progress | Open U14 for exact Current Plan/item. | §§7.1, 11.5; no Requisition/Tender creation. |
| Start/Continue/Prepare correction | Open or create the exact governed correction path for U16 request. | §5.4.5; no navigation-triggered update. |
| Record correction completed / Close without change | Resolve exact request only after Active correction or required no-change reason. | §5.4.5; other requests keep hold; no stopped-REQ restart. |
| Add extra requirement as separate item | Navigate to pending source in eligible plan update. | §5.4.6; no mutation on navigation or original-item scope increase. |
| Open System setup | Open exact authorised CFG v0.11 section. *(Version reference reconciled in v1.27; see the note after the §1.2 table.)* | Owner navigation only; absent without setup access. |
| Clear filters / disclosures / Read full text | Change local presentation, expand exact stored content, restore focus. | KT-STD §§3, 2.7; no mutation/authority. |
| Cancel/Back/Close | Return to exact parent/context without committing the pending action. | No write; preserve safe authorised work where specified. |
| Try again/Refresh | Repeat owner read or reload current state. | No inferred success/absence; changed commands require new explicit decision. |
| Uncertain result recovery | Resolve/replay original idempotency identity before another action. | §7.1; conflicting actions disabled; no duplicate task/decision. |
| Technical record search/read | Resolve exact registered Planning route and render read-only in every state. | KT-STD v1.7 §3A.6; all business commands absent. |

Any control introduced by implementation but absent here is omitted until its purpose, destination/result, authority, error behavior and audit effect are approved. The UI wording maps to stable command/event identities in §§4–7; no display label renames the wire contract.

## 12. Audit and historical integrity

| Event | Evidence visible in context |
|---|---|
| DPP certification/validation | Exact Submission, source revisions, certification/disposition, actor/capacity, time and outcome |
| Finance review | Exact financial basis, Budget Versions, currentness separately, reviewer and decision |
| Preparation/adoption/approval | Exact Plan Version, capacity, signature/decision and required collective evidence |
| Correction/withdrawal | Original immutable content, actionable reason, authorised decision and copied successor link |
| Publication | Approved document, Treasury evidence history, actual adapter outcomes, acknowledgement and activation outcome |
| Upstream correction | Origin Version, affected stable item, hold state and exact resolution evidence |
| Classification correction | Accepted submission/entry, original and corrected type/category, governed catalogue Version, correction reason, superseded evidence, actor/authority/time, affected allocations and required recovery route |

History is a readable record of evidence, not a developer event dump. Raw event IDs, digests, SQL fields and concurrency tokens stay out of the ordinary product view. Their server preservation remains mandatory.

Every command records its exact input/output identities, expected/resulting token, actor or authenticated producer, exercised authority, prior/resulting states, idempotency correlation, decision reason/evidence where required and instant. Audit derives actor/time server-side. Financial-basis reuse, source substitution/exclusion, scope protection, every correction request disposition, Treasury corrections, publication reconciliation/withdrawal and activation failure are distinguishable. Preserve immutable earlier versions, decisions and files. Reversal is a linked record, never erasure. A failed transaction cannot leave a signature, allocation, drawdown or pointer partially committed.

## 13. Deterministic seed contract

The single closed visual fixture pack is §10.2. Its context and explicit overrides apply to every artboard. Preserve the original three sources and two Plan Items; the security-assessment direct requirement is isolated. Use the corrected Julia/Peter/Grace scopes and chronology in PLN-REF §11.3.

| Fixture concern | Required resolution for implementation |
|---|---|
| BASE reservation None/None | This is a blocked mandatory-allocation case under the new rule, not an approval happy path |
| READY Youth designation | Proposed UI-only calculation/layout example. Requires verified category/method applicability and a separately approved integrated seed amendment before production-style happy-path testing |
| Schedule periods and profiles | Exact visual arithmetic supplied; legal/profile verification remains pending. Never seed the display example as verified production configuration |
| Estimate/source narrative additions | UI-only complete-detail examples identified in §10.2; reconcile with authoritative source fixtures before integrated tests |
| Programme UOM for direct assessment | Deliberate valid-UOM UI fixture correction; confirm deliverable semantics in final shared seed, no new UOM catalogue |
| Publication artifacts and correction IDs | Static example references; no claim of real documents or transactions |
| Active/execution cases | Independent UI snapshots, not outcomes generated by submitting the intentionally blocked BASE data |

No fixture may be repaired by granting an actor retroactive authority, relaxing a mandatory validation or assigning a false qualifying category. Positive path integration depends on the prerequisites in §15; error and review-layout design can proceed without claiming those prerequisites have been met.

### 13.1 Corrected authority and dependency order

Adopt this fixture correction consistently in KT-STD, NDS, PLN, SEED, relevant downstream fixtures, tests and artboards. These are changes to test/design fixtures, not permission to alter real historical audit evidence.

| Fixture fact or action | Agreed value, EAT |
|---|---|
| Julia's acting Digital Health authority | 1 October through 30 November 2026 inclusive; remove Planning's conflicting 26–30 November-only period |
| Peter's Digital Health authority | From 1 December 2026; remove the extra pre-26-November assignment introduced only to accommodate the inconsistent fixture |
| Peter's HRMD authority | Separate substantive assignment throughout the scenario |
| Digital Health laptop Need acceptance | Julia, 25 November 2026 at 09:30 |
| HRMD laptop Need acceptance | Peter, 25 November 2026 at 10:00 |
| Digital Health DPP certification | Julia, 25 November 2026 at 10:30; includes the infrastructure and laptop entries |
| HRMD DPP certification | Peter, 25 November 2026 at 11:00 |
| Digital Health DPP acceptance | Mercy, 27 November 2026 at 14:00; creates the initial Draft APP atomically |
| HRMD DPP acceptance | Mercy, 27 November 2026 at 14:05; adds its sources to that Draft |
| Later handover | Peter may take Digital Health actions from December; Julia remains the actor on her earlier evidence |

Use explicit instants to demonstrate dependency ordering, not coincident timestamps with assumed execution order. The shared assignment record must also include Grace's actual departmental scopes needed by the fixture, already specified in this specification; do not rely on a UI's claimed department. Command-time AUTH checks and maker-checker rules apply. Test an outgoing officer submitting from an old open page after expiry. Verify every source was accepted before its certified inclusion, all actions occur within valid authority and the intake clocks permit the intended action.

### 13.2 Command execution and scenario separation

Use the complete fixture pack in §10.2. The integrated BASE has 2 items, 3 sources, 2 departments and KES 130,000,000 of eligible planned procurement; Budget ceilings are KES 100m and 60m, while planned amounts are KES 80m and 50m. BASE has no qualifying reservation and must remain a blocked-readiness case under the illustrative 30%/KES 39m calculation. READY changes laptop designation to Youth and qualifying amount to KES 50m only as an explicitly labelled UI scenario, not proof of legally verified category eligibility. Production happy-path seeds require verified rules and matching configuration.

Seeds call the same authorized commands as the UI. DHI acceptance at 27 Nov 2026 14:00 EAT creates the APP; HRMD acceptance follows at 14:05. Julia’s October–November DHI assignment and Peter’s December DHI handover are separate from Peter’s HRMD responsibility. Do not backdate real evidence to repair fixtures. Enabled UOM Programme is used for the isolated security-assessment example; no invented Service UOM. Preserve full source quantities and deadline boundaries. No Requisition is required to calculate a Plan schedule.

Reset/replay is deterministic and idempotent, fails on conflicting authoritative data, and never creates a business role for Administrator, a second PE, FY user grants, legacy aliases or direct governed-state writes. All invitation actuals are absent before Tender publication; the supported invitation event then populates only its proceeding’s evidence. Other six actual integrations remain explicitly unavailable. Test the later-Need scenario with authorized/published original coverage and a separate new item; never merge it into the locked package.

### 13.3 Usability verification scenarios

The §10.2 integrated fixture is retained. The following are isolated presentation/interaction profiles, not concurrent mutations of its shared records. Use existing legitimate actors and owner commands; none claims that the source rules are production Verified.

| Profile | Exact setup / expected work |
|---|---|
| AO ordinary review | READY before Amina’s adoption; 2 items, 3 requirements, KES 130m; Finance and Charles signature only already recorded |
| AO return | Same exact reviewed Plan; targeted laptop combination comment from §10.10; copied correction remains separate evidence |
| Department funding | DHI Draft infrastructure funding missing, laptops KES 30m; incomplete total identified; Julia only certifies when all required content is complete |
| Need estimate prefill and change (v1.30) | Isolated profile on the DHI Draft. The infrastructure Need's estimate, KES 80,000,000, starts the entry at KES 80,000,000 with Budget line blank, and the preparer saves it with the eligible Budget line. The deployment-laptops Need's estimate, KES 30,000,000, starts the entry at KES 30,000,000, and the preparer revises it to KES 35,000,000 (**new content**), so the entry shows the accepted estimate and the change +KES 5,000,000. Certification freezes both references and U06 shows the same. Plan Item values use KES 35,000,000 and never the Need estimate. A Need without an estimate prefills nothing |
| Department correction | Existing returned submission with laptop amount comment; new Draft in the same coverage; unrelated accepted Need remains for next update |
| Finance availability | Independent DHI approved100m/planned80m/available10m; confirm permitted. HWD approved60m/planned50m/available60m |
| Finance excess | Separate DHI approved70m/planned80m; exact10m excess; confirm blocked, return available |
| Finance reassessment | Current Plan unchanged; legitimately revised authoritative Budget basis; original and latest evidence kept separate |
| Collective authority | Explicit configured Council or Board variant with legitimate recorder assignment and resolution; never mutate the Ministry’s default Cabinet Secretary actor to pretend authority |
| Publication recovery | Separate missing-evidence, confirmed-failure, unknown and published-held profiles; no injected success or reuse of one live publication identity across incompatible histories |
| Extra requirement | 50 additional laptops/KES10m after original item authorisation; pending approved-DPP input forms a separately governed Plan Item; existing Tender covers none |
| Readability/history | Long complete description and distinct historical problem/correction fields; full text accessible without expanding every group or losing review context |
| Access/retry | Acting assignment expires or record changes after load; owner responses enforce scope and idempotency; failed save preserves only still-authorised input |
| Over-budget plan update (v1.27) | UPDATE-OVER-BUDGET in §10.2: Version 2 adds HWD items of KES 10m and KES 2m; HWD approved 60m, planned 62m; Request plan funding confirmation fails with `PLN_PLAN_NOT_AFFORDABLE`; RequestBudgetRevision creates one Open request and the waiting state; a second request fails with `PLN_BUDGET_REVISION_ALREADY_REQUESTED`; reducing the plan to fit makes a further request fail with `PLN_BUDGET_REVISION_NOT_REQUIRED` |
| Classification correction | Isolated history on DPP-MOH-DHI-2027-001 Submission 3: Julia certifies 28 Nov 10:00, Mercy accepts Works/Works on 29 Nov 15:00, Draft item PPI-MOH-2027-044 forms 15:10, then Mercy corrects to Non-consulting services/Services on 30 Nov 09:20 with §10.5 reason; Submission 1 and accepted Submission 3 remain unchanged; item marked Source correction required; stale repeat rejected |

These supplement rather than silently change SEED v1.3. Every production field value must come from the actual owner. The approved NDS v1.14 source/revision chronology and CFG v0.13 (v1.26 read: CFG v0.11) date/precision rules apply; remaining date applicability and primary-law verification gaps are not fixed by moving the fixture’s FY or declaring READY.

### 13.4 Negative fixtures for the dead-end test — v1.27

KT-STD-001 v1.8 §8.7 requires blocked and returned states, not only the happy path. Planning's negative fixtures, each an isolated profile under §13.3:

| Required kind | Planning fixture |
|---|---|
| Blocked by a computed condition | UPDATE-OVER-BUDGET (§10.2); BASE with the missing infrastructure method |
| Returned with comments | Department correction (U05-CORRECTION); Finance return (U10-RETURN); AO return (U11-RETURN) |
| Rejected | Not applicable: Planning has no rejection outcome, only returns (§5.2.3) |
| Accepted upstream, not yet taken up downstream | U07-UNALLOCATED: three accepted sources not yet in purchases |
| Accepted upstream after the downstream plan was accepted (v1.28) | The dead-end matrix profile *Departmental plan accepted — a need accepted after it*: an accepted departmental plan and one later accepted Need; the department must hold Your turn with Create update. The static artboard fixture is Awaiting fixture. |
| Superseded while downstream work was in progress | U09-LOCKED and U16 with an authorised requisition, using their existing owner fixtures |

The dead-end matrix (§14.12) runs every §5.7 state against every §8.3 actor able to read it, using these profiles.

## 14. Acceptance contract

Each result below is a normative acceptance requirement, not a test already run. IDs are unique in this successor. The full decision-specific regressions in §17.4 also supplement the baseline and UX criteria. Cross-module requirements pass only with the corresponding provider/consumer implementation and evidence.

Forecast-editing and reminder requirements **PLN18-AC-119, PLN18-AC-124–131, PLN18-UX-20–22, PLN19-UX-035 and PLN18-RI-030/039/040** are retained as future-facility requirements only. They are explicitly excluded from the v1.24 MVP release gate and must not create forecast schemas, routes, APIs, controls, scheduler registrations, notification producers, reminder work or placeholder tracking. All other listed criteria remain MVP requirements unless their row expressly states a future dependency.

### 14.1 Corrected baseline acceptance set

| ID | Required result |
|---|---|
| PLN18-AC-001 | One site is resolved without a PE selector; zero or missing assignments/configuration fail closed, multiple role-bound OU assignments remain distinct, and configured FY options grant no authority. |
| PLN18-AC-002 | Workspace reads and direct routes create no record. |
| PLN18-AC-003 | One DPP root is created idempotently per Fiscal Year and Organisation Unit. |
| PLN18-AC-004 | Every current accepted Need appears once with six read-only facts, including expected operational result, and no Budget, Strategy or classification from Needs. |
| PLN18-AC-005 | A direct-only DPP can be created and submitted without any Need. |
| PLN18-AC-006 | A mixed DPP retains distinct source origins and creates no synthetic Need. |
| PLN18-AC-007 | Direct requirement input is limited to the eight defined values. |
| PLN18-AC-008 | Need-origin edits are limited to Planning funding and the defined set/restore disposition; all six accepted source facts and full quantity remain protected. |
| PLN18-AC-009 | Initial/update submission accounts for every Need in the applicable command-time cohort; correction uses its fixed stable cohort. Proceeding entries require valid full quantities, dates and funding; non-proceeding Needs require reasons. Truly empty DPP submission rejects. |
| PLN18-AC-010 | HoD submission records the exact certification and routes to DPP validation, not the AO. |
| PLN18-AC-011 | A DPP return preserves the certified Submission and provides actionable entry-level correction. |
| PLN18-AC-012 | Acceptance requires classification only for proceeding entries; accepts certified exclusions too, atomically creates/reuses the initial Draft APP and projects proceeding sources without forming items. |
| PLN18-AC-013 | The initial APP has no separate start/window-close/all-department/nil gate. It distinguishes eligible unallocated sources, accounted exclusions and unrelated pending inputs; empty Draft may exist but cannot be submitted. |
| PLN18-AC-014 | Single and separate formation allocate every source once and at full quantity. |
| PLN18-AC-015 | Combined formation rejects incompatible sources and requires the defined aggregation reason. |
| PLN18-AC-016 | No blank or source-less Plan Item can be created. |
| PLN18-AC-017 | Each Plan Item has exactly one eligible Active Strategic Objective and no Value Commitment. |
| PLN18-AC-018 | Plan Item inputs include required estimate/method evidence, planned lotting and the estimated delivery period. They exclude contract specifications, Value Commitment, recommended-method override, generic notes and manually entered actuals. |
| PLN18-AC-019 | Baseline dates are computed from the target invitation date and the governed periods, never independently typed; the computed schedule is chronological and the delivery boundary check passes before submission. |
| PLN18-AC-020 | Plan Item value and funding breakdown equal the exact source allocations. |
| PLN18-AC-021 | Finance task data is protected before serialization and displays a current As-at position. |
| PLN18-AC-022 | Finance confirmation atomically validates the authoritative Budget basis and records one complete decision or none; no Planning reservation or ledger event is created. |
| PLN18-AC-023 | Need acceptance, DPP actions and Plan formation create no reservation. |
| PLN18-AC-024 | Financial evidence freshness uses line identities/eligibility, currency, planned totals and applicable approved-basis values/revisions; narrative/Strategy/schedule or financially equivalent source changes do not independently stale it. Reuse is explicit and other readiness checks remain independent. |
| PLN18-AC-025 | HOPF, AO and statutory reviewers can inspect every governed field and exact source/evidence in a complete read-only view and matching protected review pack. |
| PLN18-AC-026 | The Accounting Officer adopts or returns the complete consolidated Plan. |
| PLN18-AC-027 | Exactly one statutory authority approves or returns the same Accounting-Officer-adopted Version. |
| PLN18-AC-028 | Every return requires one actionable correction and preserves the submitted snapshot. |
| PLN18-AC-029 | This approval authorises only the exact system publication payload and does not itself activate the Plan. |
| PLN18-AC-030 | Approval commits durable intent; external transmission follows valid exact-Version Treasury evidence and hold checks. Authoritative acknowledgement is recorded; activation occurs once only when every current activation predicate passes. |
| PLN18-AC-031 | Confirmed failure safely retries identical approved files; indeterminate results reconcile first and cannot permit withdrawal or a competing replacement. |
| PLN18-AC-032 | At most one Version is Active and at most one candidate chain is open; no Active is fabricated for an initial or published-held correction. |
| PLN18-AC-033 | An Active predecessor remains the baseline until a valid successor activates; its independent current affordability, allowance, scope and correction-hold checks continue to apply. |
| PLN18-AC-034 | Requisition eligibility exposes exact remaining quantity/value and creates no Requisition. |
| PLN18-AC-035 | Active item removal is blocked by drawdown, Tender handoff, commitment or contract. |
| PLN18-AC-036 | Planning has no actual-milestone entry, Monitoring Officer action or custom support workspace. |
| PLN18-AC-037 | All counts, queues, details and actions use the same Fiscal Year, Organisation Unit and task predicates, and a record hidden from a list is unreachable by direct route. |
| PLN18-AC-038 | Same idempotency key returns the original result; concurrent different commands yield one winner and one stale result. |
| PLN18-AC-039 | Unauthorized OU/responsibility/detail routes mask existence. FY mutation rules use configured intake and record state, never user grants; no second PE is modeled for testing. |
| PLN18-AC-040 | Seed reset and rerun produce the exact baseline without duplicates or semantic drift. |
| PLN18-AC-041 | HOPF performs the existing final Sign and submit action; Planner remains distinct. No professional-review approval, generic committee or publication-approver stage is introduced. |
| PLN18-AC-042 | Board and Council each preserve collective resolution reference and the authorized actor/capacity recording that decision. |
| PLN18-AC-043 | Publication is an idempotent system action; any technical retry reuses the exact approved payload. |
| PLN18-AC-044 | Shared AUTH resolves exact role-bound assignments and departmental subtrees on the single site; Frappe roles, User Permission, task possession and FY grants never substitute for business authority. |
| PLN18-AC-045 | Requisition eligibility exposes every source allocation, expected operational result and exact remaining quantity and value. |
| PLN18-AC-046 | The Need-origin combined item (`PPI-MOH-2027-033`) and the direct-requirement fixture (§10.4) each produce equivalent, complete approved source lineage regardless of origin. |
| PLN18-AC-047 | Draft dissolution preserves history, releases only proposed source allocations and recomputes/cancels obsolete Finance work where the basis changes; Budget balances remain unchanged. |
| PLN18-AC-048 | Dissolution after submission rejects atomically; there is no Planning reservation-release operation or release-failure dependency. |
| PLN18-AC-049 | Only REQ invokes governed Budget reservation/reversal services; PLN drawdown participates in the same coordinated atomic transaction and preserves exact lineage. |
| PLN18-AC-050 | Correction preserves returned evidence and stable cohort, permits current accepted revision substitution or evidenced upstream exclusions, blocks unrelated additions, respects scope lock and repeats HOPF submission then AO/statutory governance. |
| PLN18-AC-051 | Correction evaluates the defined financial basis; current evidence is explicitly reused and stale evidence requires fresh confirmation; no Planning reservations exist. |
| PLN18-AC-052 | Acceptance of a DPP successor never rewrites an allocated source; mutable Draft items require dissolve and re-form, submitted Plans require return, and Active Plans wait for a successor. |
| PLN18-AC-053 | A withdrawn initial DPP can reopen only as the next Submission while the initial window is Open. |
| PLN18-AC-054 | A closed intake leaves late initial requirements visible with accurate inclusion information but supplies no initial-submission bypass; a department with an accepted predecessor retains its governed update path. |
| PLN18-AC-055 | Combined Plan Items reject different Budgets or currencies. |
| PLN18-AC-056 | Sequential Requisitions may use remaining original allowance, subject to one open Requisition per stable Plan Item across all departments and the item-specific hold/scope gates. |
| PLN18-AC-057 | The maker-checker matrix blocks every prohibited same-user action pair and no unlisted approval level is introduced. |
| PLN18-AC-058 | Concurrent first-DPP acceptance creates exactly one Annual Plan root and one open Version. |
| PLN18-AC-059 | Planning has one navigation entry and no role-specific work-queue menu. |
| PLN18-AC-060 | The Financial Year select is server-authorised, visible and changeable; local storage never grants access or permanently binds a year. No Procuring Entity selector exists on any Planning screen. |
| PLN18-AC-061 | Draft, Accounting Officer, statutory approval and Active surfaces render the same generated Annual Plan title and the governance surfaces use the exact immutable fixture row and total. |
| PLN18-AC-062 | Combined completion uses the earliest source required-by date; signing plus required non-negative estimated delivery period is feasible; an earlier downstream REQ date never defines the Planning baseline. |
| PLN18-AC-063 | A user with different responsibilities in different OUs cannot exercise either responsibility outside its own assignment. |
| PLN18-AC-064 | A site-wide Planner responsibility and an OU-scoped departmental responsibility coexist without narrowing or broadening each other. |
| PLN18-AC-065 | One parent-OU assignment covers its descendants and never a sibling outside that subtree. |
| PLN18-AC-066 | Tasks route eligible work but cannot authorize a user who lacks the matching role-bound assignment. |
| PLN18-AC-067 | Decision evidence stores the exact User Responsibility Assignment exercised. |
| PLN18-AC-068 | A Plan Item cannot reach Finance request without an explicit `reservation_category`; `None` is accepted and recorded as a choice. |
| PLN18-AC-069 | Reservation calculations use the eligible value of the exact current complete APP Version and exact verified rule Version; verified mandatory shortfall or missing basis blocks formal submission, while incomplete Drafts remain editable. |
| PLN18-AC-070 | Method eligibility checks mandatory value/cumulative limits, category, circumstances, evidence and any separate authorization; a within-threshold method can still be ineligible. |
| PLN18-AC-071 | Each rule resolves using its verified applicability date/basis and exact effective Version; FY-only or current-date assumptions cannot silently select every legal rule. |
| PLN18-AC-072 | Missing mandatory method/schedule/reservation configuration or basis blocks the affected submission/action. Optional market-price index absence is separately labelled and is not a reservation waiver. |
| PLN18-AC-073 | Related procurements trigger a splitting assessment under the applicable rule. Planner confirmation records analysis but cannot waive a failed mandatory method/cumulative condition. |
| PLN18-AC-074 | Splitting confirmation retains related records, rule Version and justification; legitimate unbundling is accepted only under verified applicable rules, not inferred from a lotting flag. |
| PLN18-AC-075 | Source amounts are full exact estimated costs including applicable incidentals; Finance compares them with approved Budget amounts and reserves nothing. |
| PLN18-AC-076 | A late initial adoption requires an AO explanation; when the FY boundary is crossed later, acknowledgement/activation records the real instant and requires a subsequent append-only AO explanation without falsifying history. |
| PLN18-AC-077 | Accessible web, PDF and versioned KenTender Annual Plan JSON derive from one immutable approved snapshot; no OCDS compliance claim or fabricated per-item ocid exists. |
| PLN18-AC-078 | No asset disposal record, field, screen or plan item exists in this module. |
| PLN18-AC-079 | Planning does not produce downstream statutory returns or automated regulator/Treasury submissions; it supplies explicit Planning facts and exact lineage to owning contracts. |
| PLN18-AC-080 | At most one open Finance task exists per Plan Version, always whole-plan; completed/cancelled review history is preserved and replacement/Active reassessment is supported. |
| PLN18-AC-081 | No Planning command creates, holds, releases or revalidates a funding reservation, and Budget balances are identical before and after a complete plan cycle from formation through publication. |
| PLN18-AC-082 | Plan submission is blocked when planned value exceeds a Procurement Budget Line's approved amount, and the failing lines and exact excesses are returned. |
| PLN18-AC-083 | Plan submission is not blocked when planned value exceeds currently available funds; the shortfall is displayed as an advisory to the Planner, Finance Confirmation Officer and Accounting Officer. |
| PLN18-AC-084 | Adoption always creates exactly one statutory-approval task; no configuration permits a plan to reach publication without statutory approval. |
| PLN18-AC-085 | Exactly one of Cabinet Secretary, applicable CECM, Board or Council is configured; missing/ambiguous route blocks formal submission and adoption, while authorized return remains available. |
| PLN18-AC-086 | Dissolving a Draft Plan Item and cancelling a Draft successor change no Budget balance. |
| PLN18-AC-087 | Financial-basis reuse links the current Version to the earlier immutable decision and validated identical basis; substantive Plan changes still repeat their own governance. |
| PLN18-AC-088 | `Pending addition` is derived at read time and appears in no stored field, schema column or fixture. |
| PLN18-AC-089 | Every item records fixed Single year, aggregation and lotting before readiness; Packaged into lots requires positive lot count; no selectable or API-enabled multi-year path exists. |
| PLN18-AC-090 | The published plan carries, for every item, the breakdown, planned dates, horizon, aggregation indicator, lotting indicator, estimated value with budget and funding source, and procurement method required by the plan contents rules. |
| PLN18-AC-091 | Catalogue options are not proof of supported methods: each selected method needs complete applicable eligibility and schedule profiles; no threshold-only auto-selection bypass exists. |
| PLN18-AC-092 | Need exclusion has a 20–500 character reason, preserves six facts/full quantity, clears operative funding, requires no classification/allocation and emits accepted disposition separately from Active usage. |
| PLN18-AC-093 | An accepted Need that is neither planned nor marked not proceeding blocks departmental plan submission. |
| PLN18-AC-094 | Departmental plan intake is governed solely by the Fiscal Year flag and its close instant; no `DPPSubmissionWindow` DocType, route, command, seed or test exists. |
| PLN18-AC-095 | No disposal item, field, column or screen exists in this module, and the accounting officer adopts the procurement plan alone. |
| PLN18-AC-096 | No valuation, disposal committee, bidder, proceeds-accounting or asset write-off record exists in this module. |
| PLN18-AC-097 | County obligations are separately applied only to the relevant entity under verified denominator/category/overlap rules; mandatory unmet allocation blocks submission, and non-county UI omits the control. |
| PLN18-AC-098 | No submission/adoption/publication path bypasses the configured statutory route; in-flight tasks retain their exact capacity and are not silently re-routed by configuration changes. |
| PLN18-AC-099 | Actuals are recorded per exact procurement proceeding/source coverage; duplicate events are idempotent and corrections supersede linked evidence; baseline lateness and elapsed-duration variance remain distinct. Forecast comparison is future-only. |
| PLN18-AC-100 | Optional Project name belongs to the whole Plan Version; per-item execution information is derived from current exact proceeding evidence and never infers fulfilment from publication. |
| PLN18-AC-101 | The governed eleven-method catalogue is retained without two-stage/framework Plan selections; Open Tender is the initial choice only where complete applicable conditions/profiles permit its use. |
| PLN18-AC-102 | Every proceeding item inherits Goods/Works/Services and governed requirement type; method conditions evaluate the correct category and all required evidence. |
| PLN18-AC-103 | Low-value and other cumulative limits use the verified scope/period and related procurements required by the controlling rule, not a new record ID or split line as a reset. |
| PLN18-AC-104 | No Planning highest-advantage ranking or reason-only preference override exists; planned designation, mandatory restrictions and future candidate entitlement are distinct. |
| PLN18-AC-105 | Mandatory procurement restrictions derive from verified applicable rules and known funding/category/value facts; fixed unverified currency thresholds are not hard-coded or waived by narrative. |
| PLN18-AC-106 | Lotting and planned reservation are distinct; only explicitly qualifying allocation counts, with separate items for partial qualification in this MVP and no inferred universal splitting exemption. |
| PLN18-AC-107 | The exact approved publication carries the intended invitation-to-treat characterization and verified prescribed Plan field mapping; source-layout verification remains a prerequisite. |
| PLN18-AC-108 | No disposal record, field, column, screen or plan item exists in this module. |
| PLN18-AC-109 | Every reporting field maps to its actual Planning, Budget, REQ, Tender, award, supplier, implementation or payment owner, or an explicit future missing source; the Plan does not pretend to contain them all. |
| PLN18-AC-110 | Departmental Needs is never a precondition for a departmental plan entry, and no command, screen or validation requires a Need reference on a direct requirement. |
| PLN18-AC-111 | The Annual Plan section and independent Active/candidate links remain visible whenever their records exist, regardless of whether an actionable card is present. |
| PLN18-AC-112 | Every page resolves its authorisation verdict before rendering; a denied actor sees the inline Forbidden panel with no header, filter, content or empty state painted, and no permission modal appears on page load. |
| PLN18-AC-113 | The Forbidden panel names the responsibilities that open the surface and directs the user to a KenTender administrator; it names no line manager or supervisor. |
| PLN18-AC-114 | Selecting this module without access pushes its own route, highlights it in navigation, and lands on its Forbidden state; the module is never hidden and route and view never diverge. |
| PLN18-AC-115 | Server-side schedule rules use the selected method/procedure profile with verified counting/minimum/maximum limits and separately labelled internal assumptions; no universal hard-coded floors or fallback profile. |
| PLN18-AC-116 | Applicable baseline dates derive from the invitation anchor and profile periods; final completion boundary derives from source required-by dates. No independent baseline date editor exists. |
| PLN18-AC-117 | Submitting a Plan Version blocked by `PLN_DELIVERY_BOUNDARY_INSUFFICIENT` is rejected, naming the affected Plan Item. |
| PLN18-AC-118 | A locked baseline field cannot be changed by any command once the owning Version has left Draft; only a Plan successor can produce a new baseline. |
| PLN18-AC-119 | **Future facility — excluded from v1.24 MVP.** Forecast changes require reason, exact current schedule token and append-only revisions for changed rows only; preserve baseline, actuals and comparison references. |
| PLN18-AC-120 | No human role/API path supplies actuals directly; only authenticated owning-module events with exact proceeding/source lineage are accepted. |
| PLN18-AC-121 | Before publication the fixture has no actual event evidence; show Not available rather than zero. Invitation events later populate their own proceeding; unsupported six milestone integrations are labelled explicitly. |
| PLN18-AC-122 | Single year is fixed/read-only, aggregation and lotting are governed editable Draft fields, and lot count appears only for Packaged into lots; no multi-year justification control remains. |
| PLN18-AC-123 | Pre-Finance readiness checks applicable package/structure/source/schedule fields but does not require an existing Finance confirmation; formal submission adds current financial and mandatory rule/evidence gates. |
| PLN18-AC-124 | **Future facility — excluded from v1.24 MVP.** Forecasts initialize from baseline exactly once on activation; absent before activation; supersession preserves last forecasts and revision history rather than nulling them. |
| PLN18-AC-125 | **Future facility — excluded from v1.24 MVP.** Changing a forecast proposes all eligible later milestones by the same delta; excluded rows and explicit individual overrides remain visible and the resulting full schedule is validated. |
| PLN18-AC-126 | **Future facility — excluded from v1.24 MVP.** A milestone with a recorded actual date is never returned as an includable or excludable row in a cascade proposal, and a direct attempt to include one is rejected. |
| PLN18-AC-127 | **Future facility — excluded from v1.24 MVP.** Confirming a cascade writes one forecast revision per included row, all sharing one cascade identity, atomically. |
| PLN18-AC-128 | **Future facility — excluded from v1.24 MVP.** A final-milestone or other single-row forecast change is valid with a reason and null cascade ID; a multirow accepted set shares one cascade ID. |
| PLN18-AC-129 | **Future facility — excluded from v1.24 MVP.** Forecast confirmation validates every affected adjacency, including included/excluded boundaries and individual overrides, under the applicable profile; late completion forecasts remain recordable and flagged. |
| PLN18-AC-130 | **Future facility — excluded from v1.24 MVP.** Workspace/Active schedule-health counts derive from exact applicable item/proceeding forecast evidence; no Active plan means absent count, and unlike quantities or proceeding dates are not collapsed. |
| PLN18-AC-131 | **Future facility — excluded from v1.24 MVP.** Daily checks inspect every applicable outstanding milestone and update one unresolved notice per recipient/item/proceeding/milestone, without per-day duplicates, blocking work or inferring completion. |
| PLN18-AC-132 | Internal defaults come from complete effective-dated method/procedure profiles; missing profiles block submission instead of silently falling back to 5/2-day buffers or Open Tender rules. |
| PLN18-AC-133 | The baseline schedule card shows the computed result before the period inputs, and the period-adjustment disclosure loads closed by default. |
| PLN18-AC-134 | The computed baseline table updates immediately on a target-date or period change, before any save command is issued. |

### 14.2 Complete UX and state coverage

These are required future verification checks, not executed test results. Each UI acceptance ID is unique and referenced in §17. PLN18 IDs are retained stable acceptance identifiers, not a requirement to recreate v1.18’s superseded screen labels. The additional v1.19 usability checks are in §14.4.

| ID | Required result |
|---|---|
| PLN18-UX-01 | Workspace retains Active and candidate links independently when no action row exists; every admitted lifecycle/publication state has correct content and next action |
| PLN18-UX-02 | No read/filter/navigation creates a Plan/DPP; one site has no PE selector; FY is a view/operation filter and never a permission grant |
| PLN18-UX-03 | All counters, source quantities, department counts and monetary totals match the exact fixture/Version; facts are separately labelled |
| PLN18-UX-04 | DPP accounts for every current accepted Need at its applicable coverage cut-off; excluded Needs retain facts/reason and need no operative funding/classification |
| PLN18-UX-05 | Direct requirement and Need-funding forms enforce ownership, supported UOMs and Draft rules; copying direct entries preserves stable identity |
| PLN18-UX-06 | Certified/returned DPP evidence is immutable; the correction Draft opens as working content while prior accepted/returned submissions remain accessible in History; acting authority expiry blocks stale commands |
| PLN18-UX-07 | Formation gives one-source users no redundant choice, verifies combined compatibility and blocks duplicate/partial/unauthorised source allocation |
| PLN18-UX-08 | Pending unrelated requirements cannot enter a submitted/correction cohort; source revision updates never silently rewrite existing allocations |
| PLN18-UX-09 | Scope lock and temporary correction hold are separately visible/enforced; new Need cannot inherit an old Tender; separate new item path remains usable |
| PLN18-UX-10 | Method eligibility/schedule profiles control fields and checks; missing support blocks submission with exact explanation, without Open Tender fallback |
| PLN18-UX-11 | Single-year scope, explicit non-negative delivery period and source-derived boundary are reflected consistently; date arithmetic updates before save |
| PLN18-UX-12 | Finance uses complete per-line statement and exact evidence history; low available is advisory, over-approved blocks; no Planning action reserves/releases Budget funds |
| PLN18-UX-13 | Finance review iterations and Active reassessment keep original evidence distinct; source/basis races cannot yield an invalid positive decision |
| PLN18-UX-14 | Every governed field and required evidence is reachable from complete review for the exact Version; full review pack matches and is labelled with approval status |
| PLN18-UX-15 | HOPF/AO/statutory actions are correctly separated; collective reference and same-user chain segregation enforced; stale evidence still allows authorised return |
| PLN18-UX-16 | Treasury evidence gate, append-only correction, exact document match and successor-specific evidence work without an extra Treasury approval stage |
| PLN18-UX-17 | Confirmed failure, unknown outcome and published-held are distinct; no unsafe withdrawal/blind retry; hold/dispatch concurrency preserves the external truth |
| PLN18-UX-18 | Web/PDF/JSON publication derives from one immutable snapshot; no disposal or OCDS-compliance claim; activation does not occur on generic success |
| PLN18-UX-19 | Exact proceeding coverage and separate actuals displayed; partial drawdown retains remaining allowance; publication never implies full fulfilment |
| PLN18-UX-20 | **Future facility — excluded from v1.24 MVP.** Forecast error and forecast-history comparisons have correct signs/bases; missing versus inapplicable distinct; historical comparisons reproducible |
| PLN18-UX-21 | **Future facility — excluded from v1.24 MVP.** Cascade supports individual overrides and final-row revision; every affected adjacency checked; commit atomic; late forecasts allowed; already-actual rows immutable |
| PLN18-UX-22 | **Future facility — excluded from v1.24 MVP.** Reminders deduplicate, reforecast without flooding, resolve only from actual evidence and navigate to the exact work; later milestones not starved by earlier missing actuals |
| PLN18-UX-23 | Multiple correction requests retain the shared hold; only permitted terminal outcomes release it; no Draft resolution, scope unlock or stopped-Requisition resurrection |
| PLN18-UX-24 | Reservation denominator/qualifying amount/remaining allocation reflect the eligible current complete APP basis; overlap/category rules are verified; missing mandatory configuration blocks |
| PLN18-UX-25 | No Planning highest-advantage ranking or reason-only override; planned designation and candidate entitlement remain distinct |
| PLN18-UX-26 | Initial/configured entity setup can save every mandatory route/county field; domain, API, UI and validation agree |
| PLN18-UX-27 | DPP intake controls are complete; independent module flags, advance-FY close dates and command-time deadlines work without relying on scheduler execution |
| PLN18-UX-28 | Funding/reference/profile maintenance is usable under existing setup authority, immutable when referenced, historically resolvable and auditable; no configuration approval. Reminder maintenance is future-only. |
| PLN18-UX-29 | Optional Project name and late initial activation explanation have exact ownership/history; normal in-year successor not mislabelled late; acknowledgement processing not blocked by later explanation |
| PLN18-UX-30 | Permission verdict precedes content; denial/masked/error/empty/config-missing states distinct; counts/files and deep links enforce matching scope |
| PLN18-UX-31 | Keyboard navigation, focus return, table wrapping, scroll and non-obscuring action footer verified across all required artboards; no unlabelled fact concatenation |
| PLN18-UX-32 | All baseline artboards map to replacements, all 72 RI rows map to surfaces or explicit nonvisual obligations, and new test IDs replace contradictory old assertions |

### 14.3 Critical end-to-end acceptance journeys

1. Direct-only and mixed DPPs complete ordinary governance with no Need requirement on direct sources; initial closure, valid corrections, accepted-DPP updates and non-proceeding coverage each follow their own gates.
2. Two first departmental acceptances race and produce one APP/Draft; source allocations remain complete and unique. A source correction changes no submitted evidence; unrelated later Needs remain pending for a permitted update.
3. Finance repeated review, concurrent Budget revision and Active reassessment preserve exact evidence and never alter Budget ledger/balances. Stale positive decisions fail; authorized correction returns succeed.
4. Mercy consolidates, Charles signs, Amina adopts and Daniel approves through the configured capacity. Same-user incompatibilities survive correction copies. Board/Council variants require collective evidence; missing route cannot complete.
5. Publication intent commits separately from external transmission. Treasury evidence gates exact-Version dispatch; crash/unknown/duplicate callbacks, hold races, confirmed-unpublished withdrawal and published-held corrections preserve external fact and activate at most once.
6. Original Need → accepted DPP → Active APP → authorized REQ → published Tender; later Need cannot be absorbed into that stable item, including copied-Version, increased-revision, partial-drawdown and activation-race variants. Its separate new item succeeds through normal governance and becomes eligible for its own proceeding. The old Tender covers/fulfils none of the new source.
7. Two unresolved correction requests hold only the affected item. One disposition cannot clear the other; Draft correction cannot resolve; no-change closure requires reason and restarts no stopped REQ. Permanent procurement-scope lock remains after hold release.
8. Two sequential Tender proceedings retain different owner-supplied actuals and exact coverage; corrected events never overwrite another proceeding. Missing values are not zero. Forecast comparison and reminder behavior is a future-facility journey excluded from the v1.24 MVP.
9. Full authorized review/export exposes all fields and immutable evidence, source back-navigation restores context, failures have actionable copy, and none of these controls requires opening every accordion. Complete every §10 artboard/state at the prescribed viewport before release.

### 14.4 Additional v1.19 usability acceptance

These 40 checks supplement the 134 retained business criteria and 32 retained UX checks. They verify the approved task changes, not new procurement approval stages. All are required results, not recorded passes. Stable PLN18 IDs remain valid regression identifiers; PLN19 IDs identify this amendment.

| ID | Required result |
|---|---|
| PLN19-UX-001 | An authorised assigned-task link opens the exact complete review directly; no workspace, version-choice or readiness screen is a prerequisite. Reload/back retains that context. |
| PLN19-UX-002 | Opening task, evidence, filters or document links creates no DPP, Plan update, review or procurement; missing task authority produces the correct protected response. |
| PLN19-UX-003 | Funding/preparation uses separately labelled result, actor and time; allocations/budgets use legible tables. Material deficits and missing required evidence remain visible before the decision even when detail is collapsed. |
| PLN19-UX-004 | Every §9.5 field, full description/reason and exact evidence reference is reachable in screen and review pack; summaries cannot replace or change authoritative meaning. Keyboard/contrast/wrapping and focus return work. |
| PLN19-UX-005 | Current plan resolves only the Active pointer; Draft/update/awaiting authority states remain distinct with exact references accessible. No newer version silently replaces the current or reviewed plan. |
| PLN19-UX-006 | Ordinary task labels follow §9.4 and errors follow §8; machine commands, enums, codes and generated identities remain unchanged. Historical signed text is not bulk rewritten. |
| PLN19-UX-007 | Return creates the normal correction Draft atomically and the next permitted action opens it directly; original reviewed content remains immutable in History with its exact decision. |
| PLN19-UX-008 | Correction certification/review preserves the admitted requirements and repeat governance; unrelated later requirements are explicitly pending, not silently inserted or made an endless blocking input. |
| PLN19-UX-009 | New departmental returns require one actionable correction comment and validated exact entry or whole-submission scope; no duplicate problem input. Legacy distinct issue/correction text survives migration and historical display. |
| PLN19-UX-010 | Plan return item context belongs to the exact reviewed Plan; whole-Plan return and immutable reason remain. Invalid foreign-item context fails atomically; no partial approval or unvalidated free-text ID. |
| PLN19-UX-011 | Inline Need funding edits update only the DPP-owned line/amount; six source facts remain read-only. Direct creation contains exactly its six source facts and funding, with no invented Need or estimate-evidence field. |
| PLN19-UX-012 | HoD can inspect all included/excluded content and certify on the same plan with required acknowledgement. Author-only sessions cannot submit or gain a new handover approval command. |
| PLN19-UX-013 | Exclude labels state the departmental-plan scope, require the reason and preserve the full Need while clearing operative funding; monetary/classification/formation totals exclude it without hiding it. |
| PLN19-UX-014 | Include reverses only a permitted Draft exclusion and requires fresh funding completion; no old funding silently returns. Accepted disposition/Active usage events retain their distinct approved owner semantics. |
| PLN19-UX-015 | One-source addition uses an explicit command without a redundant Separate/Combined screen. Multiple selections require a meaningful explicit choice and preview, not inferred automatic combination. |
| PLN19-UX-016 | Combined creation enforces complete compatibility, full-source scope, uniqueness and required reason; invalid Combined selection explains the actual cause and leaves valid Separate work available. |
| PLN19-UX-017 | One purchase editor exposes every decision the Planner must make, derives source quantities/amounts and provides a concise calculated schedule; complete governed evidence remains reachable without displaying every stored field in the first view. |
| PLN19-UX-018 | Schedule preview updates before save; source boundary, estimated completion and forecast remain distinct. Missing or unsupported profiles cannot silently select Open Tender/default rules or allow a positive submission. |
| PLN19-UX-019 | Each missing-work notice names the affected record/field/amount and authorised recovery. Actual waiting role/person is shown; no generic readiness badge is the sole explanation. |
| PLN19-UX-020 | No-work workspace retains current/update access while omitting empty Your actions; non-action readers see relevant state/responsibility instead of an unusable decision button. |
| PLN19-UX-021 | A later accepted requirement after first item authorisation cannot expand that item through an update, new source revision or copied row; user sees the separate-item path and correct consequence. |
| PLN19-UX-022 | Guided pending-source navigation creates nothing until the explicit permitted update/add action; original tender coverage and remaining original scope never imply coverage/fulfilment of the additional requirement. |
| PLN19-UX-023 | Validation/save failure preserves still-authorised entered work and correctly identifies what was not saved; access loss removes protected display. No false success or unsupported autosave appears. |
| PLN19-UX-024 | Uncertain decision response resolves/replays the same command identity before another attempt; concurrency/authority changes and duplicate requests cannot create two decisions or approvals. |
| PLN19-UX-025 | Every role and all 21 catalogued surface families map to an MVP task/state or an explicit future deferral; multiple responsibilities expose relevant actions without role switching and without bypassing incompatible-action history. |
| PLN19-UX-026 | All actor variants share complete document evidence but show only the current role/state actions and actual next authority; read permission alone never implies edit, retry or approval power. |
| PLN19-UX-027 | HoD certification, Planner acceptance and HOPF signature remain three distinct accountabilities; no HoD return task, HOPF approval state or extra Planner handover approval is created. |
| PLN19-UX-028 | HOPF submission freezes the exact complete plan and creates the AO task; HOPF without Planner authority cannot edit preparation fields. Stale evidence blocks positive submission, not the applicable correction path. |
| PLN19-UX-029 | Finance main comparison is approved versus planned per line. Low current availability remains advisory; an approved-amount excess blocks confirmation with exact deficit and an available authorised return. |
| PLN19-UX-030 | Active reassessment reviews unchanged exact Plan content, retains original versus latest evidence and creates no reapproval or reservation. Budget/source races cannot yield an invalid positive confirmation. |
| PLN19-UX-031 | Individual statutory approval records the configured capacity and retained AO evidence; approval does not display Current plan until activation succeeds. |
| PLN19-UX-032 | Board/Council variants identify the body and authorised recorder and require the applicable resolution for collective decisions; no personal approval inference, role impersonation or member-voting workflow. |
| PLN19-UX-033 | AO Treasury evidence matches the exact approved document and records dispatch only; correction appends history. Late initial adoption/activation explanations occur in their correct contexts without backdating or ordinary-update duplication. |
| PLN19-UX-034 | Publication failure, unknown outcome and published-held remain distinct; only safe retry/reconciliation/eligible withdrawal actions appear for authorised actors. No blind retry, manual success or forced activation exists. |
| PLN19-UX-035 | **Future facility — excluded from the v1.24 MVP.** When separately approved, forecast changes preview all eligible affected rows, individual overrides and approved-date comparison; actual rows remain protected and commit is atomic. |
| PLN19-UX-036 | Multiple correction requests retain the hold until each permitted terminal outcome; resolution requires correcting Active content, no-change requires reason, permanent scope remains and stopped REQ never auto-restarts. |
| PLN19-UX-037 | Auditor/reader follows exact historical departmental and Finance evidence and exports only authorised content; current warnings never overwrite the past and decision controls are absent. |
| PLN19-UX-038 | CFG-owned setup exposes complete route/intake/catalogue/profile/verification tasks under existing authority, with no extra approval chain or legal-verification checkbox bypass; denied/masked/loading states are distinct. Reminder setup is future-only and absent from the MVP. |
| PLN19-UX-039 | Participant records cover ordinary and correction journeys for each decision/operational role with tasks stated without button coaching; observed behaviour, assistance and misunderstanding are recorded separately from interpretation. |
| PLN19-UX-040 | Any approval/certification/scope/coverage misunderstanding blocks usability acceptance; repeated confusion or coaching dependence is revised and retested. Document/prototype approval cannot mark participant, accessibility or release checks passed. |

### 14.5 Representative-user task verification

Use disposable scenario data and the actual role context. Begin with a small formative round including people unfamiliar with procurement software; include real AO and actual Board/Council decision recorders where those routes apply. A proxy test may find defects but cannot establish usability for an unrepresented actor. No recruitment, testing or result is claimed by this document.

| Role / scenario | Task to give without naming interface controls | Observe |
|---|---|---|
| AO ordinary | Assess the submitted annual plan and explain your decision | Purchase purpose, cost, funding, source evidence and next authority understood |
| AO correction | Ask Procurement to justify combining the laptop requirements | Targeted meaningful comment; knows whole Plan returns |
| Department preparation | Prepare the department’s requirements using supplied estimates | Can complete missing funding and distinguish Author work from HoD submission |
| Department correction | Correct the questioned laptop amount and resubmit as HoD | Finds editable work without learning versions; repeats correct certification |
| Planner consolidation | Organise the three requirements into justified annual purchases | Explicit separate/combined choice, full quantities, concrete remaining work |
| Planner extra Need | Plan 50 more laptops after the original item has an authorised requisition and tender | Separate governed item; old tender not mistaken for new coverage |
| HoD exclusion | Review the included and excluded requirements and submit | Exclusion reasons and full certification scope understood |
| Planner validation | Classify and accept a departmental plan or return an unclear amount | Validation distinguished from final Plan approval |
| Planner classification correction | Correct a wrongly accepted Works classification to Non-consulting services and continue the affected purchase | Finds accepted evidence, understands Category derivation, preserves departmental facts and explicitly rebuilds rather than editing the purchase |
| Finance availability | Review approved/planned/available amounts with low availability | Affordability and reservation distinguished |
| Finance reassessment | Check unchanged current Plan against a revised budget | Old/latest evidence and no reapproval understood |
| HOPF | Review and sign the prepared annual plan | Preparation accountability and AO next step understood |
| Statutory individual | Decide after AO adoption | Approval and later activation distinguished |
| Collective recorder | Record the supplied body resolution against this plan | Recorder does not mistake the decision as personal approval |
| AO external evidence | Record that the exact approved plan was sent to Treasury | Dispatch, receipt and approval distinguished |
| Technical recovery | Investigate an uncertain publication result | Checks existing attempt before retrying |
| Audit | Find the reviewed departmental facts and original Finance evidence | Historical context and protected export preserved |
| Setup | Repair missing rule evidence or intake configuration | Correct owner surface and evidence, no approval/verification shortcut |
| Operational correction | Resolve one of two Planning correction requests | Other request hold and permanent scope remain understood; no stopped downstream process appears restarted |

Record role/experience, task, first action, completion, wrong turns, assistance, exact misunderstood consequence, participant quote, observed cause, proposed correction and retest. Facilitation can advance a static sketch in response to a chosen action but may not teach the action. Time is diagnostic, not an arbitrary click/speed quota. Missing sketch functionality and misunderstanding are different findings.

Any mistaken understanding of approval, certification, included scope or procurement coverage is a blocking design finding. Repeated confusion or completion that depends on coaching requires revision/retest. Verify keyboard use, assistive technology, realistic screen sizes, loading/saving and error recovery in the implemented application. A small successful round supports progression; it is not proof of population-wide adoption. Preserve these results separately from automated domain/contract tests.

### 14.6 Explicit design-contract acceptance

| ID | Required result |
|---|---|
| PLN20-AC-001 | Every MVP composition in U01–U14, U16 and U21 states purpose, external fixture, header, top-to-bottom regions, exact values/actions and visual acceptance under KT-STD v1.7 §§2 and 10. U15 is explicitly deferred. |
| PLN20-AC-002 | C01–C04 are generated from CFG v0.11’s complete owner design section; Planning shows only its exact missing-setting consequence and authorised link, without a competing partial setup contract. *(Version reference reconciled in v1.27; see the note after the §1.2 table.)* |
| PLN20-AC-003 | Each actor variant has one definite action set; HOPF, AO, individual/collective authority, Finance, departmental actors, readers and technical readers cannot inherit another actor’s controls. |
| PLN20-AC-004 | Primary and alternate fixtures are isolated and internally consistent; canonical 27 Nov DPP acceptance is not conflated with NDS’s 4/5 Jan exclusions or conditional Plan activation. |
| PLN20-AC-005 | Every fact selected for display has a clear label or table heading and every name/reference pair has defined hierarchy; this does not require every stored fact to be displayed. No prose instruction or internal schema term is rendered as business content. |
| PLN20-AC-006 | Every material funding, reservation, scope, evidence, timing or publication issue is visible before its affected action; collapsed history/technical detail never changes a decision verdict. |
| PLN20-AC-007 | Every control in §10 maps to an existing navigation/read/command outcome in §11.9, including filters, Cancel/Back, disclosures, retries and uncertain-result recovery. |
| PLN20-AC-008 | A variant missing an owner-generated identity, timestamp, reason, rule or changed value is not sent to design; no designer-generated fixture or false successful state fills the gap. |
| PLN20-AC-009 | Departmental Draft/correction/certification and Planner validation layouts retain full included/excluded content, exact coverage, certification and contextual return without adding a handover/approval stage. |
| PLN20-AC-010 | Annual Plan, Finance, governance and publication layouts keep current/Draft/update, approved/planned/available, signature/adoption/approval, and approval/publication/activation as separate facts. |
| PLN20-AC-011 | Technical reader layouts conform to KT-STD v1.7 §3A.6 and shared search/conformance registration, with business commands absent; separately granted setup or publication recovery remains owner-controlled. |
| PLN20-AC-012 | All required MVP desktop/narrow artboards pass explicit composition comparison, keyboard/focus/error checks and representative-user tasks; specification approval does not count as participant evidence. |

### 14.7 Classification provenance and correction acceptance

| ID | Required result |
|---|---|
| PLN21-AC-001 | Before DPP acceptance, the Planner selects one governed Requirement type for each proceeding entry; the server derives Category from the same effective catalogue entry and rejects a client-supplied or mismatched category. |
| PLN21-AC-002 | U06 displays Requirement type and derived Category together with plain helper text. U09 shows a compact classification summary and links to exact source-classification evidence; Quantity and Unit are visibly derived from included requirements. Single-year horizon is enforced without a routine field. |
| PLN21-AC-003 | Correcting an accepted classification appends one immutable reasoned correction against the exact current evidence head, preserves the original acceptance and certified departmental facts, and rejects unchanged, stale, excluded-entry or unauthorised requests atomically. |
| PLN21-AC-004 | An unallocated source uses the corrected effective classification; an affected mutable Draft item becomes Source correction required and cannot continue until explicitly dissolved and re-formed. No item classification changes in place. |
| PLN21-AC-005 | A submitted, approved or Active Plan retains its exact classification and authority. Without a scope lock, incorporation requires the applicable fully governed Plan correction/successor and the current Active Version remains in force until successor activation. With a Requisition/Tender scope lock, Planning records the correction and hold but cannot reclassify, dissolve, duplicate, reset or alter the existing procurement; only the exact downstream lawful route may resolve it. |
| PLN21-AC-006 | Correction history, affected-item recovery, re-evaluated compatibility/method/reservation/schedule rules, scope-locked blocking, stale concurrency, audit/export and the isolated §13 fixture pass server, UI, accessibility and representative-Planner tests without departmental recertification unless a source fact changed. |

### 14.8 Simplicity and directness acceptance

| ID | Required result |
|---|---|
| PLN22-AC-001 | Every ordinary screen separates current task, conditional supporting detail and audit/configuration evidence. Storage necessity alone never causes routine display. |
| PLN22-AC-002 | An ordinary page has one dominant task, one visible issue summary and no more than one primary action. History, export and evidence links remain secondary. |
| PLN22-AC-003 | Blank, None, Not applicable, default and single-value facts are omitted unless their absence materially affects the current decision. |
| PLN22-AC-004 | U09 first view contains only Purchase details, Included requirements, Estimated cost, Procurement approach, Dates and current material issues. Strategy provenance, classification provenance, rule evidence and milestone calculations are supporting detail. |
| PLN22-AC-005 | U09 never renders Procedure — Planning example, resolver support/status, Rule version or Source check as ordinary business fields. A blocking configuration problem is replaced by one plain issue and its recovery owner/action. |
| PLN22-AC-006 | Annual reserved-procurement calculations appear once at Plan level. Purchase pages show only an applicable designation or item-specific restriction; they omit None, inapplicable county fields, no-restriction messages, Single lot and Lot count 1. |
| PLN22-AC-007 | U10 first view contains Budget line, Approved, Planned, Difference and Result. Availability and basis provenance are supporting detail and do not change the affordability meaning. |
| PLN22-AC-008 | U11 opens with a decision summary, visible material issues and concise purchase rows. No purchase starts expanded; the decision does not require scrolling through audit evidence or opening every disclosure. |
| PLN22-AC-009 | U14 shows only authoritative planned scope, authorised coverage and procurement-stage evidence. Unsupported completion/actual fields are omitted, never represented by repeated placeholders. |
| PLN22-AC-010 | U15, forecast cascades and forecast-driven reminders have no MVP route, control, artboard or acceptance gate. The approved schedule remains readable and owner-supplied operational dates may be read-only. |
| PLN22-AC-011 | U16 leads with the required change, affected purchase, hold consequence and lawful next action. Request IDs, versions and timestamps remain in detail/history. |
| PLN22-AC-012 | Ordinary actors can complete their representative task without interpreting candidate, cohort, resolver, rule-version, source-check, event or internal submission terminology. Any coaching dependence or repeated misunderstanding blocks usability acceptance. |
| PLN22-AC-013 | The implementation and visual review demonstrate that complete evidence remains reachable while the first view contains only facts needed for the actor’s current decision. |

### 14.9 v1.23 consistency acceptance

| ID | Required result |
|---|---|
| PLN23-AC-001 | The MVP has no forecast record schema, forecast/cascade route or API, U15 action, scheduled milestone check, reminder configuration control or Planning notification producer. Existing tested code, if retained temporarily, is unreachable and unregistered; a greenfield implementation does not create it. |
| PLN23-AC-002 | `U06-ACCEPTED-CLASSIFICATION` and `U06-CORRECT-CLASSIFICATION` exist as separate reviewed static artboards using the exact §10.5 fixture before **Correct classification** is implemented. U09 is not accepted as a substitute for either design source. |

### 14.10 v1.24 Stage 2 presentation acceptance

| ID | Required result |
|---|---|
| PLN24-AC-001 | No field, state, command, authority, validation, integration, audit or evidence requirement changes solely because of this presentation rewrite. |
| PLN24-AC-002 | Every MVP composition names its archetype and primary user question and implements the Level 1–3 information hierarchy in §10.1. |
| PLN24-AC-003 | U01 leads with the current Plan or immediate task; counts and issues support that task and do not become an equal-weight dashboard grid. |
| PLN24-AC-004 | U02–U09 distinguish preparation, review and focused-choice surfaces; the current issue and one primary action are evident before supporting evidence. |
| PLN24-AC-005 | U10 and U11 put the actual decision, consequence, material blockers and concise decision basis before provenance and history. |
| PLN24-AC-006 | U12 and U13 present one coherent evidence story: pinned source truth for U12 and approval-to-activation state with one lawful next action for U13. |
| PLN24-AC-007 | U14 and U16 scan as monitoring and exception workspaces: coverage/stage/holds or required change/consequence appear before internal records. |
| PLN24-AC-008 | C01–C04 and U21 inherit the parent archetype and preserve orientation; setup ownership or an exceptional state never becomes an unstructured generic panel. |
| PLN24-AC-009 | Colour, borders, cards, badges, uppercase text and repeated metadata are restrained; emphasis communicates task, issue, state or consequence rather than decoration. |
| PLN24-AC-010 | At 1440 × 1024 and the prescribed narrow layout, a representative actor can identify within the first view what this is, what matters now and what they can do; §14.5 testing verifies comprehension without coaching. |

### 14.11 v1.25 reservation-denominator acceptance

| ID | Required result |
|---|---|
| PLN25-AC-001 | The 30% planning denominator is the eligible value of the exact current complete APP Version; unused Budget headroom is never included. |
| PLN25-AC-002 | The Budget ceiling and APP value may differ. Affordability still blocks overspend, but the system neither invents procurement to consume a Budget nor treats unplanned headroom as planned procurement. |
| PLN25-AC-003 | Every current Plan Item is included or excluded from the obligation by the exact verified rule, with an inspectable reason; omitted expected procurement cannot silently reduce the denominator. |
| PLN25-AC-004 | An approved APP amendment recalculates the successor Version's eligible value, required allocation, qualifying allocation and remaining allocation without rewriting the predecessor snapshot. |
| PLN25-AC-005 | The closed fixture calculates 30% × KES 130,000,000 = KES 39,000,000; KES 50,000,000 qualifying allocation yields 38.46% and zero remaining allocation. |
| PLN25-AC-006 | Actual achievement uses authoritative downstream actual procurement values and is never inferred from APP estimates. County-resident and other obligations remain separately calculated. |

### 14.12 v1.27 reconciliation and workflow-guidance acceptance

| ID | Required result |
|---|---|
| PLN27-AC-001 | Request plan funding confirmation fails with `PLN_PLAN_NOT_AFFORDABLE`, naming every affected line, while any operative line's planned total exceeds its approved amount. Confirm plan funding and Sign and submit Annual Plan keep their own checks (§5.3.1, §5.3.3). |
| PLN27-AC-002 | Request plan funding confirmation fails with `PLN_PLAN_CONTENTS_INCOMPLETE`, naming the purchase, while any Plan Item has no selected method. A selected method with a missing or unverified profile blocks only Sign and submit Annual Plan. |
| PLN27-AC-003 | A reservation shortfall does not block Request plan funding confirmation and does block Sign and submit Annual Plan with `PLN_RESERVATION_SHORTFALL`. |
| PLN27-AC-004 | U07 shows live Budget fit per line and a separate Finance confirmation line using the §5.2.2 state names; no screen reports a computable result as "Not yet checked". |
| PLN27-AC-005 | For every §5.7 state and every §8.3 actor able to read the record, the read returns the stated next-step kind, holder, since and blockers. The dead-end matrix is clean across the §13.4 fixtures. |
| PLN27-AC-006 | RequestBudgetRevision succeeds only for an over-budget line with no Open request for the same Version and line; it is idempotent; it creates one BudgetRevisionRequest and one BUD request; it changes no Budget amount, reservation or Plan state; and it changes the Planner's next step to Waiting on the Budget Officer. |
| PLN27-AC-007 | Every §7.7 row creates the next holder's My Work item and the sender's waiting-on item in the event transaction, and clears each only on its stated state change. Planning sends no notification. |
| PLN27-AC-008 | A BudgetRevisionRequestOutcome updates the request status idempotently and recomputes readiness; the Planner's next step becomes Your turn only if every line then fits. |
| PLN27-AC-009 | Administrator and System Manager never receive Your turn or a fix from any Planning next-step answer. |
| PLN27-AC-010 | U01 BASE and U07 BASE present the missing method as the pre-Finance blocker and the reservation shortfall as a signature blocker, and the U07 BASE Schedule result does not claim a calculated schedule for a purchase without a method. |

### 14.13 v1.28 acceptance

| ID | Required result |
|---|---|
| PLN28-AC-001 | For each §5.1.2 plan state, the derived position of every current accepted Need is exactly the one stated, and it is published to Departmental Needs after every departmental-plan command and every Need acceptance; a revision that is not the Need's current accepted revision is not published. |
| PLN28-AC-002 | An accepted plan with a Need in *Update required* gives the department Your turn — Add {need list} to this plan, with Create update; the Procurement Planner reads the Waiting line with since; an Auditor is Not involved; a technical reader reads Waiting. The dead-end matrix asserts the department's turn, because the KT-STD-001 v1.9 §3B.7 rules alone accept a Done answer. |
| PLN28-AC-003 | In that state the tracker shows Preparation Current, the next step's stage is preparation, and the page heading does not ask anyone to review and submit. |
| PLN28-AC-004 | U01 shows the U01-LATE-NEED task row and register status; My Work shows the §7.7 item; all three clear once an update carries the Need, and return if that update is withdrawn. |
| PLN28-AC-005 | A Need accepted while the plan is with Procurement reads *After current submission* until that submission is accepted, then *Update required*. |

### 14.14 v1.30 acceptance

| ID | Required result |
|---|---|
| PLN30-AC-001 | A Need-origin entry created or refreshed from an accepted revision that has an estimate, and that has no operative `indicative_amount`, takes the estimate as its `indicative_amount`. Budget Line stays unselected, and the entry stays incomplete until a Budget Line is chosen. |
| PLN30-AC-002 | An entry with an operative `indicative_amount` is never overwritten by a refresh or by a successor revision. The reference moves to the new revision's estimate. |
| PLN30-AC-003 | Where the reference differs from the operative amount, the funding panel, the register, certification and U06 show the accepted estimate and the signed change. No reason, task, return or blocker results. Equal amounts, a missing estimate and direct entries show nothing. |
| PLN30-AC-004 | Certification freezes `need_estimated_total_cost` in the submitted snapshot. A later revision of the Need does not alter the frozen figure. |
| PLN30-AC-005 | DPP totals, the cost entered so far, Plan Item values, allocations, affordability, the 30% denominator and every other sum use only operative `indicative_amount` values and never the Need estimate. |
| PLN30-AC-006 | Excluding an entry clears the operative amount and keeps the reference. Restoring it starts the amount from the accepted revision's estimate, never from the cleared planning amount. |
| PLN30-AC-007 | A prefilled amount whose decimal places exceed the selected Budget Line's currency is rejected with `PLN_MONEY_PRECISION_INVALID` and is not rounded. |
| PLN30-AC-008 | A Need accepted before NDS-CHG-001 v1.17 prefills nothing and shows no change; a direct requirement has no reference. Planning never writes a Need field. |
| PLN30-AC-009 | Planning consumes `DepartmentalNeedAccepted.v3` after the declared cutover and accepts no `.v2` shape afterwards; a null estimate is valid. |

## 15. Implementation, dependencies and verification

### 15.1 Implementation constraints

Apply KT-STD-001 v1.7 §§4–6: explicit Frappe domain records/services; existing Vue 3 Desk mounting and scoped components; native ERPNext configuration/catalogues; server authorization and exact version/idempotency enforcement; focused tests followed by affected-module/cross-app and release gates. Do not port the proof-of-concept stack or global CSS resets into Desk. Register surfaces centrally, use stable accessible selectors and return to the owning workspace.

Inspect the actual implementation during re-implementation; the uploaded documents’ build assertions are not verified facts. Record concrete repository/test targets against the stable RI IDs after inspection. Do not invent those paths now. Cutover must remove superseded schema, roles, fields, commands and routes after dependency/reference checks and required evidence; preserve immutable records and never delete ERPNext/HRMS records as a Planning cleanup.

### 15.2 Required sequence and open owner work

| Order | Work unit | Exit evidence |
|---|---|---|
| 1 | Incorporate the approved governing decisions; reconcile CFG/AUTH/LAW dependencies | One route catalogue, named preparation actor, recorded approval and explicit dependency dispositions |
| 2 | Finalise stable identities, versioned content, state fields and immutable evidence | Field-purpose tables, uniqueness definitions and correction/lineage examples |
| 3 | Implement DPP coverage, disposition, classification provenance/correction, windows and accepted-source projection | Both U06 classification artboards approved first; initial, returned, not-proceeding, type/category derivation, correction concurrency, affected-item recovery, withdrawn-source and late-addition tests |
| 4 | Implement Plan/Funding state separation and Budget decision-basis contract | No-reservation full-cycle test; stale-basis race; repeat review; Active reassessment |
| 5 | Implement signature, adoption, statutory route and return guards | Each positive/negative transition and same-user conflict tested on original and correction Versions |
| 6 | Implement successor activation and Requisition contracts | No balance reset, no duplicate source capacity, exact reversal, one-open-Requisition and correction-request tests |
| 7 | Implement the agreed schedule, publication and reporting boundaries after their prerequisites | Method profiles, deterministic calculations, exact publication package/acknowledgement, Treasury evidence, recovery paths and report data ownership contracts |
| 8 | Implement the task-led Stage 2 compositions and all MVP actor variants; reconcile seeds and acceptance criteria | Every screen state maps to the same lifecycle; archetype and Level 1–3 hierarchy are visible; both U06 classification artboards present; one integrated fixture; unique criterion IDs; no contradictory required outcomes; no forecast/reminder runtime entry point |
| 9 | Run the prescribed release gate | KT-STD §4–6 evidence, affected cross-module tests, schema scan and reviewed screens |

Do not repair a fixture by weakening a domain invariant. Do not mark a code change verified solely because an old test passed: the old acceptance contract itself contains mutually exclusive outcomes. Preserve the intended assertion, replace the superseded assertion, and keep an explicit old-to-new test mapping in the final register.

These are retained approved baseline requirements plus the v1.21 classification additions, v1.22 simplicity changes and v1.23 consistency corrections, not implementation claims. No item below is claimed complete merely because its design has been agreed.

| Dependency | Responsible specification / owner | Exit evidence before affected implementation or verification |
|---|---|---|
| Primary legal verification | LAW / Configuration & Governance | Exact primary sources, editions and dates; resolved method, schedule, reservation, route and publication applicability; checked Schedule layout; unresolved points explicitly blocked |
| Configuration completion | CFG / kentender_core | Approved CFG v0.13 (v1.26 read: CFG v0.11) supplies the owner specification; implement and verify its fields, services, surfaces and historical rules. No new configuration approval chain |
| Canonical domain and API contract | PLN with BUD, NDS, STR, REQ, TPR and TPUB | PLN-side identities, storage classes, field rules, commands and envelopes are defined in §§4–8. Provider amendments must adopt matching precision, schemas, transactional behavior and versioning; integration tests must prove them |
| Budget decision and reservation-measure services | BUD with PLN | Atomic financial-basis validation without Planning financial reservations; exact Budget ceiling and Money facts from BUD; eligible-current-APP calculation and snapshot from PLN; consistent decimal amounts across modules |
| Source disposition and correction response | NDS / PLN / REQ | Distinct accepted-disposition versus Active-usage events; correction outcome and stopped-Requisition follow-up; no automatic resurrection or scope expansion |
| Scope-locked classification correction | PLN with REQ, TPR and TPUB | Exact affected-procurement identity, new-authorisation hold and lawful correction/cancellation owner route; existing Requisition/Tender content never rewritten by Planning |
| Publication package and adapter | PLN publication owner | Exact KenTender JSON schema and human-readable mappings; immutable approved files; hash-bound acknowledgement; Treasury evidence; failure/indeterminate reconciliation; withdrawal and activation-held correction contracts |
| Full artboard review and revamp | PLN UX plus affected CFG surfaces | The required content/state specification is integrated in §§9–11; all-actor Blueprint v0.2 is approved. Remaining full artboard rendering, representative-user validation and production review-pack parity require evidence |
| Integrated seed reconciliation | SEED / KT-STD and module seed owners | Agreed actor chronology and source ordering; 2 items, 3 sources and KES 130 million default Plan; valid UOMs; methods/profiles and mandatory reservation allocation readiness reconciled |
| Acceptance replacement map | PLN and affected module owners | Unique successor IDs and complete old-occurrence mappings are provided in §§14/17.3; implementation must replace the tests and record real results |
| Budget revision request (v1.27) | BUD-CHG-001 with PLN | BUD adopts `ReceiveBudgetRevisionRequest`, the Budget Officer's My Work item, withdrawal, and `BudgetRevisionRequestOutcome.v1` (§7.3); integration tests prove idempotency and outcome ordering |
| Requisition hand-off item (v1.27) | REQ-CHG-001 | REQ defines the Purchase ready for requisition item created on ActivatePlanVersion (§7.7) |
| Need position contract (v1.28) | NDS-CHG-001 v1.15 | NDS adopts `project_need_planning_intake` and the Need page's position and next step (NDS-CHG-001 v1.15 §§4.11, 5.5, 8.2); a backfill publishes positions for Needs accepted before the contract existed |
| Need estimate contract (v1.30) | NDS-CHG-001 v1.17 | NDS adopts `estimated_total_cost` and publishes `DepartmentalNeedAccepted.v3` (NDS-CHG-001 v1.17 §§4.3, 7.1A). Planning consumes `.v3` in the same coordinated cutover that withdraws `.v2`. Needs accepted before the cutover keep a null estimate |
| Implementation evidence | Repository/application owners | Inspected actual schema/services/UI; meaningful regressions for the changed rules; prescribed KT-STD release evidence. No claims based solely on documents describing the build |

The integrated Plan's original amounts do not excuse a reservation shortfall under RI-047. Reconcile its qualifying designations and eligible-current-APP denominator against verified rules; if the original fixture is intentionally below target, label it a blocked-readiness scenario and provide a separate valid approval fixture. Do not falsify category eligibility, omit genuinely expected eligible procurement or alter the denominator to force the old happy path to pass.

### 15.3 Explicit facilities to be implemented later

| Future facility | Current MVP boundary | Required future scope |
|---|---|---|
| Multi-year procurement | Single year only; server rejects unsupported multi-year submission | Whole-package estimate and horizon, annual allocations, future-funding status, commitment authority and BUD/REQ contracts |
| Full OCDS publication | KenTender Annual Plan JSON, accessible web view and PDF; no OCDS compliance claim | Supported OCDS version/extensions, registered prefix, planning/proceeding relationships and full release history |
| Automated Treasury transmission and acknowledgement | AO records external submission evidence | Transmission adapter, exact document correlation, receipt/reconciliation and exception handling |
| Aggregate Plan Item milestone actuals | Separate proceeding-level actuals | Explicit aggregation semantics for partial, sequential, cancelled and corrected proceedings |
| Six remaining milestone actual integrations | Invitation actual path only is presently specified end to end | Owning operational modules publish authenticated, versioned, correctable events with exact source/proceeding lineage |
| Full completion and fulfilment derivation | Factual procurement-stage evidence; Completion tracking not yet available where unsupported | Downstream delivery/acceptance evidence and complete quantity coverage; never infer fulfilment from publication |
| Planner-managed schedule forecasting and reminders | Approved schedule remains readable; no forecast schema, U15 route/action, cascade API/service, scheduler registration, reminder configuration or notification producer in MVP | Authoritative milestone owners, downstream actual/expected-date integration, explicit schemas and API, governed cascade behavior, job and notification ownership, configuration UX, complete artboards and separate representative-user approval |
| Candidate-level preference entitlement | Planned designation and mandatory restrictions only | Candidate eligibility evidence and applicable highest-advantage treatment in the responsible downstream module |
| Statutory returns using downstream facts | Website publication and Planning facts as specified; no claim that all report data already exists | Reporting contracts with the actual award, supplier, implementation and payment owners |
| Expansion of procurement scope through tender amendment, cancellation/replacement or contract variation | No later Need absorbed into a scope-locked item; separate-item governed route remains | Independently specified lawful downstream procedures and exact source/quantity treatment; not an APP-only amendment |
| Scope-locked classification correction resolution | Planning records the corrected classification and holds new authorisation; it does not alter an authorised Requisition or issued Tender | REQ/TPR/TPUB must define the lawful correction, cancellation or replacement decision, authority, evidence and return signal before the locked UI variant or automated resolution ships |

### 15.4 Release evidence

Require focused red-green evidence for every changed acceptance criterion, clean module and affected cross-module contract suites, production asset build, the prescribed browser smoke/own-request checks, all approved artboards compared by first viewport and complete page at 1440 × 1024 and the prescribed narrow layout, and a schema/repository scan proving superseded constructs removed. Re-run broad testing only for a concrete affected shared contract or the release gate. Prototype walkthrough or document approval is not release evidence. Record the §14.5 participant results separately from automated and browser verification.

## 16. Prohibited shortcuts

- No second PE, PE selector, FY user grant, local role authority, task-as-permission or client-only lifecycle guard.
- No mandatory Need, partial accepted-Need allocation, fabricated residual source, source-less item or direct-source identity regenerated on copy.
- No Planning Budget reservation, release, revalidation, commitment or ledger mutation.
- No optional statutory approval, role equivalence between Planner/HOPF, extra HOPF approval stage, or correction-chain segregation reset.
- No editable submitted/approved/Active baseline, source-cohort expansion through correction, allowance reset, or later source absorbed into a scope-locked item.
- No client-entered Category, in-place accepted-classification edit, purchase-editor classification override, silent item reclassification or departmental resubmission merely to correct a Procurement-owned classification.
- No implicit procurement coverage/fulfilment from a plan inclusion, stable item ID or old Tender badge.
- No universal method timing, missing-profile fallback, hard-coded unverified legal thresholds, Budget-ceiling reservation denominator, incomplete-APP denominator or reason-only waiver of mandatory rules.
- No Planning candidate highest-advantage ranking, preference override, multi-year partial support, OCDS claim or fabricated contracting-process IDs.
- No user actual entry, unqualified aggregate item actual, missing-to-zero variance or later-forecast substitution.
- No routine business-screen field for Procedure — Planning example, resolver status, Rule version, Source check, fixture labels, event IDs or internal configuration provenance.
- No repeated Plan-level reservation arithmetic on each purchase; no display of None, Not applicable, no restriction, Single lot or Lot count 1 merely to prove stored values exist.
- No forecast schema, U15 route/editor, cascade API/service, scheduled milestone job, reminder configuration, Planning notification producer or unsupported completion placeholder in the MVP.
- No synchronous external publication inside approval, blind unknown-outcome retry/withdrawal, fabricated acknowledgement or forced activation of defective published content.
- No summary-only governance, forced accordion/download prerequisite, omitted required evidence, internal lifecycle navigation as a user task, redundant return fields, duplicate sidebar/chrome, delimiter-crammed facts, or prototype harness in production.
- No disposal payload, unauthorized export disclosure, silent dependency amendment, invented implementation evidence or weakening rules to make old seeds/tests pass.

## 17. Traceability, precedence and full re-implementation table

### 17.1 Precedence and incorporation ledger

This approved successor replaces v1.24 and all earlier operative Planning content. The approved Blueprint v0.2 controls the incorporated usability direction; its approval is not evidence of implementation. The original v1.17 file, approved refinement register and original UI specification remain historical source artifacts. AUTH owns authority, CFG owns catalogues/rules/setup, BUD owns financial facts and transactions, NDS owns Need revisions, STR owns objective/snapshot evidence, REQ owns requisition authorisation and invocation of Budget reservation commands; Budget owns the reservation records and financial balances, and TPR/TPUB own tender preparation/publication facts. This document cannot silently amend their implementations.

| Incorporated source | Current location and treatment |
|---|---|
| PLN-REF-001 governing decision and ownership | §§1 and 3 |
| PLN-REF-001 departmental/Plan/Finance/correction decisions | §§4–5 and 7–8 |
| PLN-REF-001 preparation/statutory/segregation decisions | §6 and command/acceptance tables |
| PLN-REF-001 method/schedule/publication/reservation decisions | §5.5 with corresponding model/API/error/UI requirements |
| PLN-REF-001 full 72-row register | §17.4, preserved IDs and full old issue/replacement/verification content; current target sections/screens added |
| Original PLN-UX-001 presentation and state inventory | Retained coverage, with conflicting layout/copy replaced by the approved Blueprint v0.2 in §9 |
| Original PLN-UX-001 fixture and surface coverage | §10 retains the closed fixture and all MVP families; U15 is explicitly deferred rather than rendered as unsupported work |
| PLN-UX-001 functional/evidence/seed/acceptance rules | §§11–14 |
| Approved Usability Blueprint v0.2 | UX-01–20 incorporated across §§4, 6–11, 13–15 and §17.4; representative testing remains outstanding |
| Project Owner classification clarification, 17 September 2026 | PLN21-CHG-001–003 retained in §§4–15 and §17.4 |
| Project Owner end-to-end simplicity review, 17 September 2026 | PLN22-CHG-001–013 across §§2, 6, 9–11 and 14–17; ordinary UI reduced without weakening evidence or server guards |
| Project Owner consistency correction, 17 September 2026 | PLN23-CHG-001–002 across §§4–7, 9–17; forecast/reminder deferral completed and both U06 classification artboards made a release prerequisite |
| Earlier prototype walkthrough | §9.8 historical limited navigation evidence; superseded as the usability design baseline |
| Every v1.17 acceptance occurrence | Corrected result in §14.1 and exact mapping below; duplicate AC-100 occurrences disambiguated |
| KT-STD-001 v1.8 §12.1 required correction and Project Owner instruction of 25 September 2026 (targeted update for Claude Design) | v1.26 §10.1A and the per-screen next-step paragraphs in §§10.3–10.17, §10.18 additions; work outside §10 listed in §10.1A.8 |
| Project Owner instruction of 25 September 2026 to reconcile the flagged disagreements and implement all recommendations before handoff | v1.27: D2 in §§5.3.1, 5.5.3.1, 5.6; §5.7; §§4.7, 7.2, 7.3, 7.7, 8; corrections in §§10.3, 10.6; fixture in §10.2; §§11.9, 13.3, 13.4, 14.12, 15.2, 17.2; owner-version reconciliation in §1.2 and the cited current rules |
| Project Owner decision of 26 September 2026 ("Visible") and instruction of 28 September 2026 (harmonize the accepted plan page) | v1.28: §§5.1.2, 5.7, 7.3, 7.7, 10.1A.2, 10.3, 10.4, 11.9, 13.4, 14.13, 15.2, 17.4, 18.0 |
| Project Owner decisions of 9 October 2026 on the Need's estimated total cost (NDS-CHG-001 v1.17 §1.2) | v1.30: §§3, 4.3, 7.3, 10.4, 10.5, 11.9, 13.3, 14.14, 15.2, 17.4, 18.0A |

### 17.2 Owner alignment and unresolved integration work

For this approved successor, current inspected documentation references are NDS v1.14, STR v1.8, BUD v1.10, CFG v0.13 and KT-STD v1.7. **From v1.26, KT-STD-001 v1.8 (approved 25 September 2026) supersedes v1.7 for this document.** v1.27 requires matching BUD-CHG-001 and REQ-CHG-001 corrections (§15.2). Their consolidated status does not claim cross-app code is implemented. Where historical rows below name predecessor versions, retain them as provenance and apply the current contract in §§1–16.

This is the current status of the owner-document work first identified in v1.18. The historical 72-row register remains below, with old section citations identified as provenance. Approval of an owner document does not prove that its APIs, schemas, legal checks or seed commands are implemented.

| Owner document | Document status / incorporated boundary | Remaining evidence or coordinated work |
|---|---|---|
| LAW v1.1 | Approved successor corrects preparation-role equivalence, obligation headings, quotation/provenance and statutory correction tracking | Exact instrument editions, amendments, applicability, prescribed Plan layout and outstanding verification items; no new legal verification in this document |
| CFG v0.11 | Approved successor covers four routes, county flag, five-tab maintenance, independent intake/deadline enforcement, funding sources, rules/verification, schedule profiles and native metadata adapters. Its reminder concepts remain future dependencies for Planning | Implement/verify owning MVP services and scoped UI; preserve explicit applicability-date/fixture conflict; no permissive fallback or source verification by document approval; expose no Planning reminder configuration in this MVP |
| BUD v1.9 | Approved whole-plan decision validation, exact Money, Budget ceiling and Budget reservation ownership | Prove locking/basis validation and exact amounts at the real boundary. BUD does not turn unused headroom into the 30% APP denominator. Shared Charles Mutiso fixture remains canonical; previously flagged BUD editorial naming/Need-selection corrections do not create a new actor or Need funding field |
| NDS v1.11 | Approved source/Quantity and separate accepted-disposition versus Active-usage contract; unchanged accepted_version_id/version_number wire keys | Planning emits exact §7.6 disposition schema/ordering; inspect existing usage transport before any breaking schema change; prove withdrawal/source race gates through owners |
| SEED v1.3 | Approved common source identities, dates, actors and BASE/READY distinction | Align actual commands and permission chronology with approved NDS/CFG owners; no contradictory scenario states coexisting under one stable record |
| AUTH v1.7 | Existing responsibilities, acting authority and segregation govern all task variants | Inspect actual assignments/current scopes, central route registration and protected reads. No local approver registry or role switch workaround |
| STR v1.7 | Retained selection/path and final-approval snapshot ownership | Confirm exact current provider schema/eligibility and snapshot idempotency; no new Planning strategy lifecycle |
| REQ v1.8 | Proposed sibling successor, not approved by this Planning document | Adopt matching correction-outcome/fresh-Draft, one-open, scope/hold wording, exact drawdown and financial contracts before affected integration; no auto-restart or scope expansion |
| TPR/TPUB | Existing preparation/publication owners; remaining successor work | Prove exact handoff/consumption and invitation event contracts; future milestone owners remain explicit |
| Planning publication adapter | Frozen web/PDF/JSON package and exact acknowledgement under §5.5.2 | Final schemas, protected package/export mapping, Treasury evidence, read reconciliation, unknown/failure recovery and activation race tests |
| Return feedback contracts | Approved UX-05 single actionable comment; §4.4/§7.6 define new input and historical treatment | Inspect actual endpoints/columns/callers; migrate versioned command payloads without losing old problem/correction text or adding duplicate required fields |

All approved usability changes use existing command ownership and governance except the explicitly documented return-input/context amendment. Renamed user labels do not rename machine codes, enums or records. This full Planning successor is the implementation specification; sibling owner requirements remain authoritative for their records. Unresolved integration remains blocked at the affected contract, not waived because the screen looks complete.

### 17.3 Old-to-new acceptance mapping

Every old acceptance-row occurrence maps below. “Retained/re-expressed” preserves its non-conflicting intent subject to the current rules; “Replaced” removes its old assertion and uses the explicit result in §14.1. No duplicate legacy identifier is treated as one test.

| v1.17 criterion occurrence | v1.18 criterion | Disposition |
|---|---|---|
| PLN-AC-001 | PLN18-AC-001 | Replaced |
| PLN-AC-002 | PLN18-AC-002 | Retained/re-expressed |
| PLN-AC-003 | PLN18-AC-003 | Retained/re-expressed |
| PLN-AC-004 | PLN18-AC-004 | Retained/re-expressed |
| PLN-AC-005 | PLN18-AC-005 | Retained/re-expressed |
| PLN-AC-006 | PLN18-AC-006 | Retained/re-expressed |
| PLN-AC-007 | PLN18-AC-007 | Retained/re-expressed |
| PLN-AC-008 | PLN18-AC-008 | Replaced |
| PLN-AC-009 | PLN18-AC-009 | Replaced |
| PLN-AC-010 | PLN18-AC-010 | Retained/re-expressed |
| PLN-AC-011 | PLN18-AC-011 | Retained/re-expressed |
| PLN-AC-012 | PLN18-AC-012 | Replaced |
| PLN-AC-013 | PLN18-AC-013 | Replaced |
| PLN-AC-014 | PLN18-AC-014 | Retained/re-expressed |
| PLN-AC-015 | PLN18-AC-015 | Retained/re-expressed |
| PLN-AC-016 | PLN18-AC-016 | Retained/re-expressed |
| PLN-AC-017 | PLN18-AC-017 | Retained/re-expressed |
| PLN-AC-018 | PLN18-AC-018 | Replaced |
| PLN-AC-019 | PLN18-AC-019 | Retained/re-expressed |
| PLN-AC-020 | PLN18-AC-020 | Retained/re-expressed |
| PLN-AC-021 | PLN18-AC-021 | Retained/re-expressed |
| PLN-AC-022 | PLN18-AC-022 | Replaced |
| PLN-AC-023 | PLN18-AC-023 | Retained/re-expressed |
| PLN-AC-024 | PLN18-AC-024 | Replaced |
| PLN-AC-025 | PLN18-AC-025 | Replaced |
| PLN-AC-026 | PLN18-AC-026 | Retained/re-expressed |
| PLN-AC-027 | PLN18-AC-027 | Retained/re-expressed |
| PLN-AC-028 | PLN18-AC-028 | Retained/re-expressed |
| PLN-AC-029 | PLN18-AC-029 | Retained/re-expressed |
| PLN-AC-030 | PLN18-AC-030 | Replaced |
| PLN-AC-031 | PLN18-AC-031 | Replaced |
| PLN-AC-032 | PLN18-AC-032 | Replaced |
| PLN-AC-033 | PLN18-AC-033 | Replaced |
| PLN-AC-034 | PLN18-AC-034 | Retained/re-expressed |
| PLN-AC-035 | PLN18-AC-035 | Retained/re-expressed |
| PLN-AC-036 | PLN18-AC-036 | Retained/re-expressed |
| PLN-AC-037 | PLN18-AC-037 | Retained/re-expressed |
| PLN-AC-038 | PLN18-AC-038 | Retained/re-expressed |
| PLN-AC-039 | PLN18-AC-039 | Replaced |
| PLN-AC-040 | PLN18-AC-040 | Retained/re-expressed |
| PLN-AC-041 | PLN18-AC-041 | Replaced |
| PLN-AC-042 | PLN18-AC-042 | Replaced |
| PLN-AC-043 | PLN18-AC-043 | Retained/re-expressed |
| PLN-AC-044 | PLN18-AC-044 | Replaced |
| PLN-AC-045 | PLN18-AC-045 | Retained/re-expressed |
| PLN-AC-046 | PLN18-AC-046 | Retained/re-expressed |
| PLN-AC-047 | PLN18-AC-047 | Replaced |
| PLN-AC-048 | PLN18-AC-048 | Replaced |
| PLN-AC-049 | PLN18-AC-049 | Replaced |
| PLN-AC-050 | PLN18-AC-050 | Replaced |
| PLN-AC-051 | PLN18-AC-051 | Replaced |
| PLN-AC-052 | PLN18-AC-052 | Retained/re-expressed |
| PLN-AC-053 | PLN18-AC-053 | Retained/re-expressed |
| PLN-AC-054 | PLN18-AC-054 | Replaced |
| PLN-AC-055 | PLN18-AC-055 | Retained/re-expressed |
| PLN-AC-056 | PLN18-AC-056 | Replaced |
| PLN-AC-057 | PLN18-AC-057 | Retained/re-expressed |
| PLN-AC-058 | PLN18-AC-058 | Retained/re-expressed |
| PLN-AC-059 | PLN18-AC-059 | Retained/re-expressed |
| PLN-AC-060 | PLN18-AC-060 | Retained/re-expressed |
| PLN-AC-061 | PLN18-AC-061 | Retained/re-expressed |
| PLN-AC-062 | PLN18-AC-062 | Replaced |
| PLN-AC-063 | PLN18-AC-063 | Retained/re-expressed |
| PLN-AC-064 | PLN18-AC-064 | Retained/re-expressed |
| PLN-AC-065 | PLN18-AC-065 | Retained/re-expressed |
| PLN-AC-066 | PLN18-AC-066 | Retained/re-expressed |
| PLN-AC-067 | PLN18-AC-067 | Retained/re-expressed |
| PLN-AC-068 | PLN18-AC-068 | Retained/re-expressed |
| PLN-AC-069 | PLN18-AC-069 | Replaced |
| PLN-AC-070 | PLN18-AC-070 | Replaced |
| PLN-AC-071 | PLN18-AC-071 | Replaced |
| PLN-AC-072 | PLN18-AC-072 | Replaced |
| PLN-AC-073 | PLN18-AC-073 | Replaced |
| PLN-AC-074 | PLN18-AC-074 | Replaced |
| PLN-AC-075 | PLN18-AC-075 | Replaced |
| PLN-AC-076 | PLN18-AC-076 | Replaced |
| PLN-AC-077 | PLN18-AC-077 | Replaced |
| PLN-AC-078 | PLN18-AC-078 | Retained/re-expressed |
| PLN-AC-079 | PLN18-AC-079 | Replaced |
| PLN-AC-080 | PLN18-AC-080 | Replaced |
| PLN-AC-081 | PLN18-AC-081 | Retained/re-expressed |
| PLN-AC-082 | PLN18-AC-082 | Retained/re-expressed |
| PLN-AC-083 | PLN18-AC-083 | Retained/re-expressed |
| PLN-AC-084 | PLN18-AC-084 | Retained/re-expressed |
| PLN-AC-085 | PLN18-AC-085 | Replaced |
| PLN-AC-086 | PLN18-AC-086 | Retained/re-expressed |
| PLN-AC-087 | PLN18-AC-087 | Replaced |
| PLN-AC-088 | PLN18-AC-088 | Retained/re-expressed |
| PLN-AC-089 | PLN18-AC-089 | Replaced |
| PLN-AC-090 | PLN18-AC-090 | Retained/re-expressed |
| PLN-AC-091 | PLN18-AC-091 | Replaced |
| PLN-AC-092 | PLN18-AC-092 | Replaced |
| PLN-AC-093 | PLN18-AC-093 | Retained/re-expressed |
| PLN-AC-094 | PLN18-AC-094 | Retained/re-expressed |
| PLN-AC-095 | PLN18-AC-095 | Retained/re-expressed |
| PLN-AC-096 | PLN18-AC-096 | Retained/re-expressed |
| PLN-AC-097 | PLN18-AC-097 | Replaced |
| PLN-AC-098 | PLN18-AC-098 | Replaced |
| PLN-AC-100 (occurrence 1) | PLN18-AC-099 | Replaced |
| PLN-AC-101 | PLN18-AC-100 | Replaced |
| PLN-AC-102 | PLN18-AC-101 | Replaced |
| PLN-AC-103 | PLN18-AC-102 | Replaced |
| PLN-AC-104 | PLN18-AC-103 | Replaced |
| PLN-AC-105 | PLN18-AC-104 | Replaced |
| PLN-AC-106 | PLN18-AC-105 | Replaced |
| PLN-AC-107 | PLN18-AC-106 | Replaced |
| PLN-AC-108 | PLN18-AC-107 | Replaced |
| PLN-AC-109 | PLN18-AC-108 | Retained/re-expressed |
| PLN-AC-110 | PLN18-AC-109 | Replaced |
| PLN-AC-099 | PLN18-AC-110 | Retained/re-expressed |
| PLN-AC-100 (occurrence 2) | PLN18-AC-111 | Replaced |
| PLN-AC-111 | PLN18-AC-112 | Retained/re-expressed |
| PLN-AC-112 | PLN18-AC-113 | Retained/re-expressed |
| PLN-AC-113 | PLN18-AC-114 | Retained/re-expressed |
| PLN-AC-114 | PLN18-AC-115 | Replaced |
| PLN-AC-115 | PLN18-AC-116 | Replaced |
| PLN-AC-116 | PLN18-AC-117 | Retained/re-expressed |
| PLN-AC-117 | PLN18-AC-118 | Retained/re-expressed |
| PLN-AC-118 | PLN18-AC-119 | Replaced |
| PLN-AC-119 | PLN18-AC-120 | Replaced |
| PLN-AC-120 | PLN18-AC-121 | Replaced |
| PLN-AC-121 | PLN18-AC-122 | Replaced |
| PLN-AC-122 | PLN18-AC-123 | Replaced |
| PLN-AC-123 | PLN18-AC-124 | Replaced |
| PLN-AC-124 | PLN18-AC-125 | Replaced |
| PLN-AC-125 | PLN18-AC-126 | Retained/re-expressed |
| PLN-AC-126 | PLN18-AC-127 | Retained/re-expressed |
| PLN-AC-127 | PLN18-AC-128 | Replaced |
| PLN-AC-128 | PLN18-AC-129 | Replaced |
| PLN-AC-129 | PLN18-AC-130 | Replaced |
| PLN-AC-130 | PLN18-AC-131 | Replaced |
| PLN-AC-131 | PLN18-AC-132 | Replaced |
| PLN-AC-132 | PLN18-AC-133 | Retained/re-expressed |
| PLN-AC-133 | PLN18-AC-134 | Retained/re-expressed |

### 17.4 Full changes for re-implementation

The 123 rows below comprise 72 refinements, 20 usability changes, 6 v1.20 composition changes, 3 v1.21 classification changes, 13 v1.22 simplicity changes, 2 v1.23 consistency corrections and 7 v1.24 Stage 2 presentation changes. None is marked implemented or tested. “Baseline/owner references” preserves the original reviewed-section references from PLN-REF-001; those numbers are provenance, not current navigation. “Current target” gives the current local sections and screen families. Stable acceptance IDs remain regression requirements; future forecast criteria are expressly outside the v1.24 MVP gate under §14. External owner changes remain subject to §15.

| Change ID | Decision origin | Existing requirement or defect | Approved replacement | Current target / screens | Baseline/owner references | Acceptance ID and required verification |
|---|---|---|---|---|---|---|
| PLN-RI-001 | Reconciliation | Historical dispositions are retained alongside contradictory operative rules | Separate concise historical disposition from current rules; remove superseded instructions from all operative sections | §§1, 17–18; All | PLN §§1, 12–20 | **PLN18-RI-001** — No mutually exclusive current rule survives the section-by-section reconciliation |
| PLN-RI-002 | Reconciliation | Approval effect still permits optional statutory approval and obsolete concepts | Rewrite approval effect from the final current decisions; do not copy cumulative obsolete authorisations | §§1, 17–18; U01/U11/U13 | PLN §20 | **PLN18-RI-002** — Each authorised action exists in the current lifecycle and domain tables |
| PLN-RI-003 | Reconciliation | Finance confirmation, dissolution, correction and cancellation still create/release reservations in some clauses | Remove every Planning reservation mutation, reference requirement and release-failure path; reservation stays at Requisition | §§3, 4.7, 5.2–5.3, 7–8; U02/U07/U09/U10 | PLN §§9, 12–17; AC-022, 047–049, 075, 081; BUD §§8, 12.6 | **PLN18-RI-003** — Entire Planning cycle leaves Budget balances and ledger byte-equivalent; Planning reservation calls rejected |
| PLN-RI-004 | Agreed refinement | Awaiting Finance and Confirmed are treated as Plan states absent from the enum | Keep Plan lifecycle and funding-evidence state separate as §5 specifies | §§3, 4.7, 5.2–5.3, 7–8; U01/U07/U10 | PLN §§4.8, 4.11, 5.2, 8, 11–12 | **PLN18-RI-004** — Every displayed state resolves from an admitted Plan/funding combination |
| PLN-RI-005 | Agreed refinement | One Finance task ever per Version conflicts with review iterations | At most one open plan-level task; retain completed/cancelled attempts and immutable decisions | §§3, 4.7, 5.2–5.3, 7–8; U10 | PLN §§4.11, 13; AC-080 | **PLN18-RI-005** — Repeat review after return or staleness succeeds without parallel open tasks or overwritten evidence |
| PLN-RI-006 | Agreed refinement | Finance freshness alternates between source-set and per-line-total rules | Define the financial basis, separate non-financial readiness, explicitly link reused confirmation | §§3, 4.7, 5.2–5.3, 7–8; U10/U11 | PLN §§4.11, 5.2, 7.3, 12.10; AC-024, 087 | **PLN18-RI-006** — Narrative edit preserves confirmation; total, currency or relevant approved-basis change invalidates it |
| PLN-RI-007 | Agreed refinement | Active stale Finance evidence blocks eligibility without a clear recovery | Permit plan-level reassessment of unchanged Active content; changed substantive content uses successor | §§3, 4.7, 5.2–5.3, 7–8; U07/U10 | PLN §§7.4, 8, 12.12 | **PLN18-RI-007** — New authorisation blocked while stale, restored after valid reassessment, existing authorisations untouched |
| PLN-RI-008 | Agreed refinement | PLN claims a locked Finance check while BUD's read call explicitly locks nothing | Add Budget-owned decision-basis validation contract; retain non-locking display read | §§3, 4.7, 5.2–5.3, 7–8; U10 | BUD §9.1; PLN §§7.3, 8.2 | **PLN18-RI-008** — Budget revision racing Finance cannot commit an already-obsolete positive decision |
| PLN-RI-009 | Reconciliation | Mandatory and optional statutory routes coexist | Exactly one applicable route; no None; missing/ambiguous configuration fails closed | §§4.7, 6–8; U11/C01 | PLN §§4.12, 17, 20; AC-084–085 | **PLN18-RI-009** — No path to approval/publication skips statutory authority |
| PLN-RI-010 | Reconciliation | Three-route descriptions omit Council identified by LAW | Include Council as an alternative configured capacity and collective-resolution treatment | §§4.7, 6–8; U11/C01 | LAW §§1, 8; PLN §§4.12, 6, 11.14; CFG/AUTH | **PLN18-RI-010** — Council route resolves one task; Board/Council decision preserves collective evidence |
| PLN-RI-011 | Agreed refinement | Planner submission is equated with Head-of-Function preparation signature | Transfer existing final submission to Head of Procurement Function as Sign and submit; preserve Planner consolidation | §§4.7, 6–8; U01/U11 | PLN §§5–6, 8, 11–14; KT-STD §8.3; LAW §1 | **PLN18-RI-011** — Mercy drafts; Charles signs; no extra approval state; no implicit role equivalence |
| PLN-RI-012 | Agreed refinement | Every decision rechecks evidence in a way that can block return | Positive decisions require current evidence; returns require authority/task/segregation but can cite stale evidence | §§4.7, 6–8; U06/U10/U11 | PLN §§12.6, 12.9–12.10 | **PLN18-RI-012** — Stale source, Strategy or funding blocks adoption but permits authorised return |
| PLN-RI-013 | Reconciliation | Copying corrections could reset maker-checker history | Preserve incompatible-action history across correction chain; include preparation signer | §§4.7, 6–8; U11 | PLN §6.1; §8.4 of this draft | **PLN18-RI-013** — Same user cannot author one Version and approve its correction |
| PLN-RI-014 | Agreed refinement | Returned is used both for immutable reviewed content and editable work | Reviewed DPP/Plan remains Returned; new numbered Draft is editable; root display can remain correction-oriented | §§4.2–4.4, 5.1, 7–8; U02/U07/U11 | PLN §§4.2–4.5, 5.1–5.2, 12 | **PLN18-RI-014** — Original snapshot unchanged after correction save/resubmit |
| PLN-RI-015 | Agreed refinement | Post-window successor eligibility is limited ambiguously to authoritative source changes | Accepted DPP may have governed updates for direct requirements and new Needs; no late initial bypass | §§4.2–4.4, 5.1, 7–8; U01/U02/C02 | PLN §§5.1, 12.2; NDS §§5, 7 | **PLN18-RI-015** — Closed window blocks new initial submission but permits valid accepted-DPP update |
| PLN-RI-016 | Agreed refinement | Every current accepted Need is required on every resubmission despite frozen corrections | Define initial/update cut-off and stable correction cohort; unrelated new Needs wait for next update | §§4.2–4.4, 5.1, 7–8; U05/U06 | PLN §§5.1, 7.1, 12.2 | **PLN18-RI-016** — New Need during review neither rewrites nor indefinitely blocks the existing submission |
| PLN-RI-017 | Agreed refinement | Not-proceeding field has no command and contradicts funding/classification/allocation invariants | Add guarded set/restore action and exclusions to every relevant gate and total | §§4.2–4.4, 5.1, 7–8; U02/U03/U05 | PLN §§4.4, 5.3, 8, 11–12; AC-008–009, 092–093 | **PLN18-RI-017** — Excluded Need remains fully accounted for, has reason, needs no funding, forms no item |
| PLN-RI-018 | Agreed refinement | Not proceeding must reach NDS but its only usage event means Active inclusion | Add separate accepted-disposition event/projection; preserve existing usage semantics | §§4.2–4.4, 5.1, 7–8; U02/U12/U14 | PLN §7.1; NDS §§4.7, 7.2 | **PLN18-RI-018** — DPP exclusion visible separately; it never clears an existing Active dependency |
| PLN-RI-019 | Reconciliation | Need display rename risks changing existing event keys/opaque identifiers | Map unchanged accepted_version_id/version_number wire keys to internal revision fields | §§4.2–4.4, 5.1, 7–8; U03/U12 | NDS v1.10 §§4.3, 7.1; PLN §§4, 7 | **PLN18-RI-019** — Existing v2 event and -V reference consumed without migration or contract bump |
| PLN-RI-020 | Agreed refinement | Direct source identity derives from an entry ID that changes on copy | Preserve one generated stable direct-source key across DPP revisions | §§4.3, 4.5–4.8, 5.4, 7–8; U04/U12 | PLN §§4.4, 4.10, 7 | **PLN18-RI-020** — Correction/successor recognises one requirement rather than duplicate new capacity |
| PLN-RI-021 | Agreed refinement | Stable Plan Item identity and per-Version row identity are conflated | Specify distinct stable item/source identity and exact versioned snapshots | §§4.3, 4.5–4.8, 5.4, 7–8; U07/U14 | PLN §§4.9–4.10, 7.4; REQ §5.1 | **PLN18-RI-021** — Old authorisation lineage stays exact; successor retains cumulative drawdown |
| PLN-RI-022 | Agreed refinement | Frozen source set prevents replacing stale revision IDs in a correction | Preserve stable cohort, allow current accepted revision substitution and documented upstream exclusions | §§4.3, 4.5–4.8, 5.4, 7–8; U07/U12 | PLN §§4.8, 5.2, 7.1, 12.10 | **PLN18-RI-022** — Same-source correction passes; unrelated new source is rejected |
| PLN-RI-023 | Agreed refinement | Pending addition means no Draft exists, although correction Draft cannot admit new inputs | Derive pending status from candidate eligibility and cohort as well as allocation | §§4.3, 4.5–4.8, 5.4, 7–8; U01/U07 | PLN §§5.2, 8.1, 12.7 | **PLN18-RI-023** — Pending sources remain visible beside an open correction Draft |
| PLN-RI-024 | Reconciliation | Concurrent first-DPP acceptance and read-created records remain high-risk invariants | Preserve single transactional root creation and no mutation from reads | §§4.3, 4.5–4.8, 5.4, 7–8; U01/U06 | PLN §§5.3, 8.2; AC-002, 058 | **PLN18-RI-024** — Concurrent acceptances create one Annual Plan and initial Draft |
| PLN-RI-025 | Agreed refinement | Successor copies can reset balances; removed sources can reappear as unallocated | Carry consumption across stable identity; explicit removal excludes source from immediate re-formation | §§4.3, 4.5–4.8, 5.4, 7–8; U07/U14 | PLN §§5.3, 7.4, 12.12 | **PLN18-RI-025** — Successor cannot increase remaining allowance by copying; removal cannot silently undo itself |
| PLN-RI-026 | Reconciliation | One open Requisition uses different uniqueness keys | Use one per stable Plan Item, matching REQ-owned invariant | §§4.3, 4.5–4.8, 5.4, 7–8; U14 | PLN §7.4; REQ §§5.1, 7.5 | **PLN18-RI-026** — Two departments cannot open parallel Requisitions for one combined item |
| PLN-RI-027 | Agreed refinement | PLN RecordRequisitionDrawdown differs from REQ AuthoriseRequisitionDrawdown | Adopt one exact versioned contract, atomic with Budget reservation and reversal | §§4.3, 4.5–4.8, 5.4, 7–8; U14 | PLN §8.2; REQ §9.1–9.1A | **PLN18-RI-027** — Consumer/provider signature and all-or-nothing transaction tests pass |
| PLN-RI-028 | Agreed refinement | Inbound correction commands lack a complete request lifecycle | Define request identity, state, ownership, source routing and resolution against an Active correction | §§4.3, 4.5–4.8, 5.4, 7–8; U16 | PLN §8.2; REQ §7.4A | **PLN18-RI-028** — Request cannot resolve on a Draft; stopped Requisition is never edited or resurrected |
| PLN-RI-029 | Agreed refinement | Plan Item authorisation hold while upstream correction requests remain unresolved — previously unspecified, now resolved by product-owner agreement | Apply one effective hold on new Requisition authorisations for the affected stable item from successful request recording until every request is resolved against an Active correction or closed without change with a reason; recalculate eligibility; preserve existing proceedings and stopped-Version evidence | §§4.3, 4.5–4.8, 5.4, 7–8; U14/U16 | This register §7.5; PLN §7.4 and correction-request services; REQ §7.4A and authorisation gate | **PLN18-RI-029** — Item-only hold; existing authorisations/Tenders untouched; multiple requests cannot clear each other; no release on Draft correction; no automatic restart; concurrent recording/authorisation cannot bypass hold |
| PLN-RI-030 | Reconciliation | Forecasts must be null on Superseded Versions | **Future facility only:** if forecasting is separately approved, preserve its last forecasts and append-only revision history after supersession. The MVP creates no forecast records | §§5.5, 14, 15.3; future U15 | PLN §4.9; AC-123 | **PLN18-RI-030 — future-only**; excluded from the v1.24 MVP gate |
| PLN-RI-031 | Reconciliation | All actual writers declared absent despite invitation event path | Document invitation publisher and distinguish pre-event fixtures from unsupported milestones | §§4.8, 5.5, 7; U14 | PLN §§4.9, 8.2, 18; TPR §9.5; TPUB §§8–9 | **PLN18-RI-031** — Publication event writes invitation actual once; pre-publication fixture remains null |
| PLN-RI-032 | Agreed refinement | Multiple sequential Requisitions/Tenders can overwrite one item-level actual | Record actuals per proceeding with exact Plan/source/quantity lineage; repeated event ID is idempotent, different Tender is separate, correction supersedes a linked event. Display proceedings separately; defer aggregate item actuals | §§4.8, 5.5, 7; U14 | §10.1A; PLN actual contract; REQ/TPR/TPUB | **PLN18-RI-032** — Two sequential Tenders retain different dates; duplicate replay changes nothing; correction cannot overwrite another proceeding or compare against a later forecast |
| PLN-RI-033 | Agreed refinement | Strategy snapshot timing and reviewed path are under-specified | Retain reviewed lineage; create deterministic STR snapshot at final approval; mismatch fails atomically | §§4.6, 7.4; U09/U11 | PLN §§4.9, 7.2, 8; STR §§7–8, 12.6 | **PLN18-RI-033** — Approval snapshot equals reviewed selection; retry creates no duplicate snapshot |
| PLN-RI-034 | Agreed refinement | Planning completion depends on downstream Requisition; fixtures use conflicting derivation | Use departmental boundaries; combined baseline is earliest required-by; REQ may choose earlier | §§4.6, 4.8, 5.5, 7–8; U09/U11 | PLN §4.9, DES-09/09A, §14.5; REQ §5.2; SEED §§3.6, 5.3 | **PLN18-RI-034** — Planning can complete without a Requisition; REQ cannot extend source/Plan boundary |
| PLN-RI-035 | Agreed refinement | Multi-year flag has no complete funding or completion semantics | MVP single-year completion within target FY only; remove selectable Multi-year and reject unsupported submission. Explicit future facility requires whole-package horizon/value, annual funding and future commitment authority | §§4.6, 4.8, 5.5, 7–8; U09 | §10.1; §12.2; PLN §§4.4, 4.9, 7.3–7.4; NDS/REQ/BUD | **PLN18-RI-035** — No UI/API multi-year bypass; fixed single-year output where required; future facility is clearly documented, with no one-year affordability comparison against an unexplained multi-year total |
| PLN-RI-036 | Agreed refinement | Universal seven-/fourteen-day floors ignore method/procedure applicability | Implement governed method/procedure schedule profiles and complete System setup maintenance surface: sequence, counting, verified limits, internal defaults, legal references, effective dates and immutable Versions; missing profile blocks submission | §§4.6, 4.8, 5.5, 7–8; U09/U11/C04 | §10.1; §11.4; PLN §4.9; CFG services/UI/seeds | **PLN18-RI-036** — Different methods resolve appropriate profiles; missing/ambiguous rules fail the affected gate; no Open Tender fallback; submitted profile history survives configuration change |
| PLN-RI-037 | Agreed refinement | Sensible implementation allowance is an undefined blocker | Require Planner's non-negative integer Estimated delivery or implementation period in calendar days; zero explicit, never fallback. Signing plus period must meet the source-derived boundary at submission | §§4.6, 4.8, 5.5, 7–8; U09/U11 | §10.1; PLN invariant 12a; AC-116; method profiles | **PLN18-RI-037** — Exact-date boundary passes and one-day excess blocks; missing period rejects; zero requires explicit entry; deadline is never silently extended |
| PLN-RI-038 | Agreed refinement | Date lateness and elapsed-duration variance are conflated | In MVP, baseline lateness = actual minus baseline and duration variance = planned elapsed minus actual elapsed. Per proceeding, retain fixed source/rule Versions; missing is Not available and inapplicable is Not applicable. Forecast error is future-only | §§4.6, 4.8, 5.5, 7–8; U14 | §10.1A; LAW §1; PLN §4.9; views/exports | **PLN18-RI-038** — Early/on-time/late signs agree across UI/export; late finish with shorter duration reports both correctly; no missing-to-zero or MVP forecast comparison |
| PLN-RI-039 | Agreed refinement | Cascade validates only included rows; final milestone has no edit path | **Future facility only:** validate every affected adjacency in a resulting forecast schedule and allow a last-milestone single-row revision | §§14, 15.3; future U15 | PLN invariant 12c; §§8.2, 11.16–11.16A, 12.12 | **PLN18-RI-039 — future-only**; excluded from the v1.24 MVP gate |
| PLN-RI-040 | Agreed refinement | Daily deduplication conflicts with one unresolved notice; first missing actual hides later dates | **Future facility only:** define milestone checks, deduplicated notices, reforecast handling and actual-event resolution after owner integrations exist | §§14, 15.3; future U15/configuration | §10.1B; PLN §8.3 and AC-130; CFG/shared notifications | **PLN18-RI-040 — future-only**; excluded from the v1.24 MVP gate |
| PLN-RI-041 | Agreed refinement | Approved but unpublished or externally uncertain invalid Plan has no correction route | Hold/reconcile; confirmed-unpublished AO request and statutory Withdraw for correction create copied Draft with full governance. Unknown outcome forbids withdrawal/replacement. Published with failed activation becomes Published — activation held and permits governed correction successor | §§4.9, 5.5.2, 7–8; U13/U07 | §5; §10.2.3; PLN §§5.2, 7.1, 8.2, 12.11; publication adapter | **PLN18-RI-041** — Hold/dispatch race cannot misclassify unpublished; no edits to approval; no uncertain cancellation; held Version has no new authorisation capacity; correction can activate without first activating defective content |
| PLN-RI-042 | Agreed refinement | Publication runs inside ApproveAnnualPlan as if external transmission were locally atomic | Commit approval and durable intent; apply Treasury/hold gates, transmit and reconcile separately; record exact acknowledgement then activate once only if activation checks pass | §§4.9, 5.5.2, 7–8; U13 | §10.2; PLN §8.2; PlanPublication | **PLN18-RI-042** — Crash after external success, duplicate callback and concurrent retry preserve exact evidence; invalid acknowledged candidate is held without false activation or duplicate publication |
| PLN-RI-043 | Agreed refinement | Treasury submission is external but its publication prerequisite has no evidence | AO Record Treasury submission: exact approved Version/document hash, time, channel, destination, dispatch reference, attachment and confirmation. Gate website transmission on valid evidence; append corrections; require own evidence per successor; automate later | §§4.9, 5.5.2, 7–8; U13 | §10.2.2; PLN §§2.1, 4.13, 7.5A; LAW §5 | **PLN18-RI-043** — Approval intent waits for evidence; predecessor evidence cannot satisfy successor; invalidation holds/reconciles; no Treasury approval or receipt gate; website/State Portal facts not inferred |
| PLN-RI-044 | Reconciliation | Procurement publication payload includes disposal items | Remove disposal section and references from procurement payload | §§4.9, 5.5.2, 7–8; U13 | PLN §4.13; AC-078, 095, 109 | **PLN18-RI-044** — Payload/schema includes no asset-disposal content |
| PLN-RI-045 | Agreed refinement | OCDS-shaped is undefined and one Plan Item is wrongly assumed to equal one contracting process | MVP publishes accessible web view, PDF and exact versioned KenTender Annual Plan JSON from one immutable approved snapshot, with exact package hash acknowledgement. Defer full OCDS; preserve stable Plan/item and exact Version IDs; operational facts separate | §§4.9, 5.5.2, 7–8; U13 | §10.2.1; §12.2; PLN §4.13; publication adapter | **PLN18-RI-045** — All formats match approved snapshot/schema; retries resend exact files; acknowledgement matches package; no disposal; no OCDS-compliance claim or fabricated per-item ocid |
| PLN-RI-046 | Reconciliation | Plan claims to hold every fact required by statutory returns | Replace blanket claim with field ownership/dependency mapping; awards, supplier data and payments stay downstream | §§4.9, 5.5.2, 7–8; U14/U21 | PLN §2.1, §7.5A; AC-110; LAW §5 | **PLN18-RI-046** — Each return column maps to actual owner or an explicit missing future source |
| PLN-RI-047 | Corrected in v1.25 | Earlier refinement wrongly made the complete approved Budget, including unused headroom, the 30% planning denominator | Use the eligible value of the exact current complete APP Version; qualifying categories only; separate county basis and verified overlap. Separate item for partial qualifying allocation. Mandatory verified allocation shortfall or missing basis blocks submission; approved amendment recalculates the successor snapshot; actual achievement remains downstream | §§4.6, 5.5.3, 7–8; U07/U11/C03 | Attached 30% review; LAW v1.2 §5.1; CFG v0.13 §§4.7, 10.7; BUD supplies ceiling only | **PLN25-AC-001–006** — 130m eligible APP value yields 39m target; 50m qualifying is 38.46%; no unused Budget headroom, category/lotting overcount, invented overlap or incomplete-APP suppression; missing mandatory rules fail; Draft remains editable; history exact |
| PLN-RI-048 | Agreed refinement | Plan data is used to rank future bidder entitlement with a reason-only override | Separate planned designation, mandatory restrictions and candidate entitlement; remove Planning highest-advantage selection and override. Candidate verification/preference treatment is downstream future work; designation updates respect governance and scope lock | §§4.6, 5.5.3, 7–8; U09/U11 | §10.3.2; §11.2; PLN invariant 24aa; LAW §4.2; downstream procurement | **PLN18-RI-048** — No ranking or override control/API; mandatory restrictions not waived by reason; no Tender eligibility mutation through APP update; candidate entitlement not asserted from a Plan category |
| PLN-RI-049 | Agreed refinement | Method admissibility relies on value while conditional requirements are missing | Versioned eligibility checklist per method, with conditions, evidence, limits and any specific authorisation actor/stage. Automated facts and judgement declarations distinguished. Missing complete profile/evidence blocks submission; downstream rechecks before use | §§4.6, 5.5.3, 7–8; U09/U11/C03 | §10.3.3; §11.4; PLN §4.9/invariant 25; CFG; LAW §§2–3 | **PLN18-RI-049** — Within-threshold but missing condition fails; generic reason is insufficient; catalogue membership not operational support; APP approval does not substitute for required separate authorisation |
| PLN-RI-050 | Reconciliation | OU argument prohibited even for Budget Line eligibility | Permit source OU on Budget record-eligibility service; keep it out of site-wide Strategy resolution | §§3, 7.3; U03/U04 | PLN §§7.2–7.3, 17; BUD §9.1 | **PLN18-RI-050** — Entity-wide and department-owned lines resolve correctly without broadening user authority |
| PLN-RI-051 | Agreed refinement | Workspace strip only describes Draft or Active and not coexistence | Show Active baseline and open candidate distinctly; specify every governance/publication state and actor action | §§9–11; U01/U07 | PLN §§11.2, 11.18, 12.1 | **PLN18-RI-051** — Initial governance, publication failure and Active-plus-successor remain directly navigable |
| PLN-RI-052 | Reconciliation | Multi-PE selectors and tests survive a one-site-one-PE model | Remove PE selection and simulated cross-PE cases; preserve OU, responsibility and FY-operation tests | §§9–11; U01/C01 | PLN §§8.1, 12.1, 15–16 | **PLN18-RI-052** — No second PE/context selector or user FY grant exists |
| PLN-RI-053 | Reconciliation | Task summaries join unrelated facts with delimiters | Use labelled facts per KT-STD §2.2; retain only legitimate identifier lineage/status-count notation | §§9–11; All | PLN §11, especially DES-01 | **PLN18-RI-053** — Artboards have exact distinct fields and no inferred package details |
| PLN-RI-054 | Agreed refinement | Governance artboards omit material submitted content and evidence | Complete read-only Plan/package/source/schedule/method/funding/reservation/change review and exact review pack; next-session full Planning artboard revamp for completeness, usability and UX, including affected System setup surfaces | §§9–11; U11/U12 | §§11.1, 11.4, 12.1; PLN §§11.13–11.14, 12.10 | **PLN18-RI-054** — Every governed field/evidence accessible without losing decision context; correct Version/export/history; decision guards; no forced click-through; full requirements-to-artboard coverage |
| PLN-RI-055 | Reconciliation | AC-100 duplicated; old ACs prohibit required lotting and require forbidden reservations | Create one uniquely identified acceptance set and an old-to-new criterion map | §§14, 17.3; All | PLN §15 | **PLN18-RI-055** — Unique identifiers; no contradictory expected results; every changed rule has coverage |
| PLN-RI-056 | Reconciliation | Infrastructure seed evaluation interval is 31 days despite 30-day maximum | Derive baseline from selected periods; reconcile seed and MVP schedule artboard dates | §§10.2, 13; U09/U11 | PLN §14.5; DES-09/14 | **PLN18-RI-056** — Seed uses same schedule calculation and validation as product commands |
| PLN-RI-057 | Reconciliation | Integrated Plan has two items/KES130m, several screens show one/KES80m without clear profile | Align default integrated Plan or mark each alternate artboard profile explicitly | §§10.2, 13; U01/U07/U10/U11 | PLN §§11, 14; SEED §§3–5 | **PLN18-RI-057** — Default Plan has 2 items, 3 sources, KES130m; Finance line totals 80m and 50m |
| PLN-RI-058 | Reconciliation | Direct fixture uses Service, absent from governed UOM register | Choose a documented valid unit consistently or approve catalogue addition with semantic reason | §§10.2, 13; U04 | PLN DES-04 and §14.7; KT-STD §8.5 | **PLN18-RI-058** — Direct fixture passes actual enabled-UOM validation |
| PLN-RI-059 | Agreed refinement | Actor assignments conflict and acceptance/submission timing does not prove order | Use §11.3 canonical timeline: Julia DHI Oct–Nov, Peter DHI from Dec and HRMD throughout; 25 Nov DPPs certified Julia 10:30/Peter 11:00 after source acceptance; Mercy accepts 27 Nov 14:00/14:05 | §§10.2, 13; U02/U05/U06/U11 | §11.3; PLN §14.2–14.4; NDS §14; SEED §3; KT-STD/shared fixtures | **PLN18-RI-059** — Exact command-time role/scope, source-before-certification and deterministic first APP creation; expired outgoing actor denied from old page; real historical records never backdated |
| PLN-RI-060 | Reconciliation | Seed method/category catalogues retain earlier subsets or labels | Reconcile fixture prerequisites with the final approved catalogues; no invented local catalogue | §§10.2, 13; U09/C03/C04 | PLN §§4.9, 14.1; LAW §§2–4; CFG | **PLN18-RI-060** — Every selectable value exists and has the required effective-dated rule |
| PLN-RI-061 | Agreed refinement | Domain fields drift from reported build with no governing contract | Exact decimal currency-unit amounts and explicit precision; no float or silent rounding; stable versus revision identity; calculated projections versus immutable snapshots; task authority from Version/capacity/AUTH; full field-purpose/type/ownership/history tables | §4; All | §11.2; PLN §1.1 and §4; BUD/REQ amount contracts | **PLN18-RI-061** — Money round-trips exactly, excess decimals reject; source identity survives copies; historical calculations reproducible; no unused scope authority or display-number substitution; actual build reconciled against approved contract |
| PLN-RI-062 | Reconciliation | Referenced versions, ownership and approval statuses are asserted inconsistently | Use NDS1.10, internal TPUB0.3 and supplied approved CFG0.9; track actual control status and remove stale missing-owner/corrected-build claims | §§1.2, 15, 17.2; All | §1; §11.4; PLN §§1, 18, 20; SEED §1.2; TPR §9.5 | **PLN18-RI-062** — Dependency matrix cites actual sources; CFG ownership recognised; implementation assertions distinguished from verified findings |
| PLN-RI-063 | Agreed refinement | LAW counts, verbatim claims and role/entitlement inferences are inconsistent | Traceable LAW correction: verify Schedule layout before count change; remove numeric reporting heading and identify obligations; correct HOPF/Planner distinction; separate source, interpretation and design; record verification status | §§1.2, 15, 17.2; U11/U13/C03 | §11.4; LAW §§1, 4, 5, 8 | **PLN18-RI-063** — Original layout checked before remapping; each obligation has owner/recipient/timing; summaries not labelled verbatim; no unsupported role equivalence or candidate-entitlement inference |
| PLN-RI-064 | Agreed refinement | CFG dependency initially missing; supplied approved v0.9 has incomplete surfaces/contracts and stale rule policies | Use approved CFG v0.10, which supersedes the originally supplied v0.9 owner baseline. Implement its route/county, DPP intake, catalogue/profile/history and close-time requirements; retain primary legal verification prerequisite | §§1.2, 15, 17.2; C01/C02/C03/C04 | §11.4; §12.1; CFG §§4, 7, 10–14; PLN §18; LAW | **PLN18-RI-064** — Every mandatory field operable in UI/API; configured consumers use explicit services; rule gaps fail correctly; advance-FY close dates work; no scheduler-only closure; legal sources and production seed applicability recorded |
| PLN-RI-065 | Agreed refinement | Project name, execution status, late activation explanation and override lack actionable contracts | Optional Draft Plan Project name for one project; read-only proceeding execution facts with incomplete-completion label; AO late-initial-activation explanation at late adoption or append-only follow-up after boundary crossed; remove preference override | §§4.5–4.8, 7–8; U07/U14/U21 | §11.2; PLN §§4, 5.3, 8, 15; LAW §1; downstream status owners | **PLN18-RI-065** — Mixed portfolio permits blank project; publication is not fulfilment; partial/multiple proceedings explicit; late explanation actor/time retained without blocking acknowledgement; normal in-year successor not mislabelled late |
| PLN-RI-066 | Reconciliation | Finance-shortfall page treats current availability as the blocking amount; some required load states absent | Correct exact copy to approved-amount failure; specify Loading/Not configured and distinguish advisory availability | §§8–11; U10/U21 | PLN §11.18; KT-STD §§3–3A | **PLN18-RI-066** — Within-approved/low-availability case allows confirmation; configuration failure is never an empty success |
| PLN-RI-067 | Agreed refinement | User reports a later Need was absorbed through an APP update into a Plan Item with a published Tender | Lock procurement scope from first Requisition authorisation: reject later source additions and package enlargement across all successor identities; retain normal APP updates for other/new items | §§4.8, 5.4.6, 7–8, 14.3; U09/U14/U16 | This register §7.6; PLN §§4.9–4.10, 5.3, 7.4, 8.2, 12.7–12.12; REQ authorisation contract | **PLN18-RI-067** — Authorised-but-unpublished and published cases reject added sources, increased quantities and scope-text substitution; direct API and copied-Version paths cannot bypass |
| PLN-RI-068 | Agreed refinement | Additional requirement can reach Planning with no executable procurement route | Form a separate Plan Item for the new requirement after normal departmental governance; include it in a governed APP successor, assess funding, activate and allow its own Requisition/procurement | §§4.8, 5.4.6, 7–8, 14.3; U01/U07/U08/U14 | This register §7.6; PLN §§5.1–5.2, 7, 12; REQ §9.1 | **PLN18-RI-068** — Later Need progresses through separate-item route without modifying the original Tender or blocking the whole APP |
| PLN-RI-069 | Reconciliation | Item-level Tender linkage can falsely imply that later sources are covered or fulfilled | Separate Active Plan inclusion, exact source/quantity procurement coverage and downstream fulfilment evidence; never infer coverage from a shared stable item ID or publication badge | §§4.8, 5.4.6, 7–8, 14.3; U02/U12/U14 | This register §7.6; PLN §4.14; NDS §4.7; REQ drawdown and TPR/TPUB lineage projections | **PLN18-RI-069** — New Need is planned but has no procurement/fulfilment coverage until its own exact downstream evidence exists; original Tender covers only original issued sources/quantities |
| PLN-RI-070 | Agreed refinement | Successor creation or concurrent authorisation can bypass a UI-only restriction | Recheck authoritative scope lock in formation, substitution, saves, submission and activation; serialise activation and Requisition authorisation using the stable-item guard; preserve original allowances and lineage | §§4.8, 5.4.6, 7–8, 14.3; U08/U09/U11 | This register §§7.2, 7.4, 7.6; PLN/REQ services and optimistic-concurrency contracts | **PLN18-RI-070** — Racing authorisation/successor expansion yields no state with a locked item enlarged; rejection is atomic; partial original drawdown and copied IDs do not reset protection |
| PLN-RI-071 | Agreed refinement | Separate additional procurement could be treated as automatic threshold avoidance or APP approval as permission to change an issued Tender | Retain method conditions and anti-splitting assessment; keep published-Tender amendment/cancellation and contract variation in their own lawful procedures; exclude scope expansion through those mechanisms from this MVP | §§4.8, 5.4.6, 7–8, 14.3; U07/U09/U11 | This register §7.6; PLN invariant 25–26; LAW §§2–3, 7; TPUB §8.2 and relevant downstream owners | **PLN18-RI-071** — New item does not automatically qualify for a lower-value method; APP amendment never mutates published package content, simulates an addendum or extends a contract |
| PLN-RI-072 | Agreed refinement | The reported end-to-end absorption defect lacks a named regression and actionable rejection | Add the §7.6 regression suite and PLN_ITEM_SCOPE_LOCKED with exact user copy; retain the separate-item happy path as the permitted outcome | §§4.8, 5.4.6, 7–8, 14.3; U01/U07/U09/U14 | This register §7.6; PLN §§9, 11–12, 14–16; integrated NDS/REQ/TPR/TPUB tests | **PLN18-RI-072** — Published original Tender plus later Need cannot reproduce false absorption; separate new item succeeds; historical source, quantity, drawdown and Tender evidence remain exact |
| PLN-UX-001 | Approved Blueprint v0.2 UX-01 — Direct decision entry | Users must navigate workspace/version/readiness screens before reviewing an assigned plan | Open the exact assigned review directly, with purpose, complete proposed purchases and actor-specific decision; no navigation-triggered records | §§6.5, 9.1–9.2, 10.4, 11.7; U01/U11 | Blueprint v0.2 UX-01; PLN v1.18 corresponding U/C families | **PLN19-UX-001 / PLN19-UX-002** — An authorised assigned-task link opens the exact complete review directly; no workspace, version-choice or readiness screen is a prerequisite. Reload/back retains that context. Opening task, evidence, filters or document links creates no DPP, Plan update, review or procurement; missing task authority produces the correct protected response. |
| PLN-UX-002 | Approved Blueprint v0.2 UX-02 — Readable complete supporting evidence | AO detail is dense prose or an unstructured complete-field dump | Use result-first labelled facts, compact comparison tables and accessible grouped detail; keep all material exceptions visible and full text/export complete | §§9.3–9.5, 10.4–10.5, 11.8; U09–U12 | Blueprint v0.2 UX-02; PLN v1.18 corresponding U/C families | **PLN19-UX-003 / PLN19-UX-004** — Funding/preparation uses separately labelled result, actor and time; allocations/budgets use legible tables. Material deficits and missing required evidence remain visible before the decision even when detail is collapsed. Every §9.5 field, full description/reason and exact evidence reference is reachable in screen and review pack; summaries cannot replace or change authoritative meaning. Keyboard/contrast/wrapping and focus return work. |
| PLN-UX-003 | Approved Blueprint v0.2 UX-03 — Business labels and meaningful states | Candidate/Submission/Revision/status combinations dominate ordinary work | Use Current plan, Draft plan, Plan update and specific waiting authority; exact identities remain secondary and available; machine values unchanged | §§4.3, 7.6, 8, 9.4, 10.2–10.3; All | Blueprint v0.2 UX-03; PLN v1.18 corresponding U/C families | **PLN19-UX-005 / PLN19-UX-006** — Current plan resolves only the Active pointer; Draft/update/awaiting authority states remain distinct with exact references accessible. No newer version silently replaces the current or reviewed plan. Ordinary task labels follow §9.4 and errors follow §8; machine commands, enums, codes and generated identities remain unchanged. Historical signed text is not bulk rewritten. |
| PLN-UX-004 | Approved Blueprint v0.2 UX-04 — Correction as the working task | Users must understand returned and copied versions to find editable work | Open the already-created correction Draft and targeted comments; retain exact accepted/returned content in History; preserve repeat governance and cohort | §§4.3, 5.1, 9.7, 10.6, 11.7; U02/U05/U06/U11 | Blueprint v0.2 UX-04; PLN v1.18 corresponding U/C families | **PLN19-UX-007 / PLN19-UX-008** — Return creates the normal correction Draft atomically and the next permitted action opens it directly; original reviewed content remains immutable in History with its exact decision. Correction certification/review preserves the admitted requirements and repeat governance; unrelated later requirements are explicitly pending, not silently inserted or made an endless blocking input. |
| PLN-UX-005 | Approved Blueprint v0.2 UX-05 — One actionable return comment | Issue and Correction required duplicate input; target ambiguous | Store one required correction comment with validated entry/item or whole-document context; inspect and migrate live payloads explicitly; preserve all historical distinct text | §§4.4, 7.6, 10.4, 10.6, 11.7; U06/U10/U11 | Blueprint v0.2 UX-05; PLN v1.18 corresponding U/C families | **PLN19-UX-009 / PLN19-UX-010** — New departmental returns require one actionable correction comment and validated exact entry or whole-submission scope; no duplicate problem input. Legacy distinct issue/correction text survives migration and historical display. Plan return item context belongs to the exact reviewed Plan; whole-Plan return and immutable reason remain. Invalid foreign-item context fails atomically; no partial approval or unvalidated free-text ID. |
| PLN-UX-006 | Approved Blueprint v0.2 UX-06 — Departmental work in context | Funding and certification force separate screens and repeated facts | Edit funding inline; reuse accepted Need facts; direct entry has exactly its source/funding fields; HoD reviews and certifies on the complete plan | §§9.2, 9.7, 10.6; U02–U05 | Blueprint v0.2 UX-06; PLN v1.18 corresponding U/C families | **PLN19-UX-011 / PLN19-UX-012** — Inline Need funding edits update only the DPP-owned line/amount; six source facts remain read-only. Direct creation contains exactly its six source facts and funding, with no invented Need or estimate-evidence field. HoD can inspect all included/excluded content and certify on the same plan with required acknowledgement. Author-only sessions cannot submit or gain a new handover approval command. |
| PLN-UX-007 | Approved Blueprint v0.2 UX-07 — Clear inclusion/exclusion actions | Restore to planned requirements obscures effect and can imply approved APP inclusion | Use explicit Include/Exclude from this year’s departmental plan; retain reason/full source, clear operative funding and require fresh completion on reversal | §§5.1.4, 7.6, 9.4, 10.6; U03/U05/U06 | Blueprint v0.2 UX-07; PLN v1.18 corresponding U/C families | **PLN19-UX-013 / PLN19-UX-014** — Exclude labels state the departmental-plan scope, require the reason and preserve the full Need while clearing operative funding; monetary/classification/formation totals exclude it without hiding it. Include reverses only a permitted Draft exclusion and requires fresh funding completion; no old funding silently returns. Accepted disposition/Active usage events retain their distinct approved owner semantics. |
| PLN-UX-008 | Approved Blueprint v0.2 UX-08 — Simple addition and combination | Form Plan Items exposes record mechanics and unnecessary single-source choices | Add selected requirements inside annual plan; one source has no choice screen; multiple sources explicitly separate/combine with preview, compatibility and justification | §§9.7, 10.3, 10.7, 11.2; U07/U08 | Blueprint v0.2 UX-08; PLN v1.18 corresponding U/C families | **PLN19-UX-015 / PLN19-UX-016** — One-source addition uses an explicit command without a redundant Separate/Combined screen. Multiple selections require a meaningful explicit choice and preview, not inferred automatic combination. Combined creation enforces complete compatibility, full-source scope, uniqueness and required reason; invalid Combined selection explains the actual cause and leaves valid Separate work available. |
| PLN-UX-009 | Approved Blueprint v0.2 UX-09 — One understandable purchase editor | Package/source/method/schedule information was fragmented; v1.21 then overcorrected by displaying every evidence field at once | Keep the Planner’s purchase decisions together, derive inherited quantities/cost and schedule, and place complete source/strategy/rule evidence in one supporting disclosure | §§9.3, 10.8, 11.2; U09 | Blueprint v0.2 UX-09; v1.21 U09 | **PLN19-UX-017 / PLN19-UX-018 / PLN22-AC-004–006** — First view exposes every required decision, not every stored field; no duplicate source input, silent method fallback or hidden blocker. |
| PLN-UX-010 | Approved Blueprint v0.2 UX-10 — Actionable work and waiting | Generic readiness/funding badges do not identify next task or actor | Show specific missing fields, affected amounts and permitted recovery; resolve actual waiting owner; no duplicate empty/disabled work queue | §§8, 9.1, 10.2–10.3, 10.8, 10.12; U01/U07/U10/U21 | Blueprint v0.2 UX-10; PLN v1.18 corresponding U/C families | **PLN19-UX-019 / PLN19-UX-020** — Each missing-work notice names the affected record/field/amount and authorised recovery. Actual waiting role/person is shown; no generic readiness badge is the sole explanation. No-work workspace retains current/update access while omitting empty Your actions; non-action readers see relevant state/responsibility instead of an unusable decision button. |
| PLN-UX-011 | Approved Blueprint v0.2 UX-11 — Extra requirement guided to separate item | Later Need can be mistaken as covered by existing tender or added to locked scope | Guide to eligible pending requirement and explicit governed update/separate item in same context; current plan/proceeding remains exact | §§5.4, 10.7, 10.10; U07/U09/U14/U16 | Blueprint v0.2 UX-11; PLN v1.18 corresponding U/C families | **PLN19-UX-021 / PLN19-UX-022** — A later accepted requirement after first item authorisation cannot expand that item through an update, new source revision or copied row; user sees the separate-item path and correct consequence. Guided pending-source navigation creates nothing until the explicit permitted update/add action; original tender coverage and remaining original scope never imply coverage/fulfilment of the additional requirement. |
| PLN-UX-012 | Approved Blueprint v0.2 UX-12 — Safe contextual feedback | Technical errors and uncertain responses encourage duplicate action or lost work | Use plain field/record notices, protect still-authorised input, resolve original command outcomes, preserve access/state checks and idempotency | §§7.1, 8, 10.12, 11.8; All/U21 | Blueprint v0.2 UX-12; PLN v1.18 corresponding U/C families | **PLN19-UX-023 / PLN19-UX-024** — Validation/save failure preserves still-authorised entered work and correctly identifies what was not saved; access loss removes protected display. No false success or unsupported autosave appears. Uncertain decision response resolves/replays the same command identity before another attempt; concurrency/authority changes and duplicate requests cannot create two decisions or approvals. |
| PLN-UX-013 | Approved Blueprint v0.2 UX-13 — Every actor covered | Initial blueprint covers only three principal journeys | Provide task/information/action/outcome mapping for every Planning role; share review patterns and render all permitted responsibilities without role switching | §§6.5, 9.6, 10, 14.5; All | Blueprint v0.2 UX-13; PLN v1.18 corresponding U/C families | **PLN19-UX-025 / PLN19-UX-026** — Every role and every catalogued family maps to an MVP task/state or explicit future deferral; multiple responsibilities remain available without role switching or incompatible-action bypass. Read permission never implies edit, retry or approval power. |
| PLN-UX-014 | Approved Blueprint v0.2 UX-14 — HoD, Planner validation and HOPF accountability | Remaining internal review steps could gain invented handovers/approvals | Same-page HoD certification, explicit Planner validation/classification, distinct HOPF preparation signature; no invented HoD return or HOPF approval stage | §§6.2, 6.5, 10.4, 10.6, 11.7; U05/U06/U11 | Blueprint v0.2 UX-14; PLN v1.18 corresponding U/C families | **PLN19-UX-027 / PLN19-UX-028** — HoD certification, Planner acceptance and HOPF signature remain three distinct accountabilities; no HoD return task, HOPF approval state or extra Planner handover approval is created. HOPF submission freezes the exact complete plan and creates the AO task; HOPF without Planner authority cannot edit preparation fields. Stale evidence blocks positive submission, not the applicable correction path. |
| PLN-UX-015 | Approved Blueprint v0.2 UX-15 — Finance comparison and reassessment | Availability, affordability and approval are visually conflated | Show approved/planned/result per line, availability separately; low balance advisory, excess blocking; unchanged-current-plan reassessment and immutable evidence history | §§5.3, 10.8, 11.3; U10 | Blueprint v0.2 UX-15; PLN v1.18 corresponding U/C families | **PLN19-UX-029 / PLN19-UX-030** — Finance main comparison is approved versus planned per line. Low current availability remains advisory; an approved-amount excess blocks confirmation with exact deficit and an available authorised return. Active reassessment reviews unchanged exact Plan content, retains original versus latest evidence and creates no reapproval or reservation. Budget/source races cannot yield an invalid positive confirmation. |
| PLN-UX-016 | Approved Blueprint v0.2 UX-16 — Individual and collective statutory decisions | Recorder role could be mistaken for personal or member-by-member approval | Use the same full review with actual configured capacity; collective body, recorder and resolution explicitly distinct; same required approval/return/withdrawal evidence | §§6.1, 6.5, 10.4, 10.9; U11/U13 | Blueprint v0.2 UX-16; PLN v1.18 corresponding U/C families | **PLN19-UX-031 / PLN19-UX-032** — Individual statutory approval records the configured capacity and retained AO evidence; approval does not display Current plan until activation succeeds. Board/Council variants identify the body and authorised recorder and require the applicable resolution for collective decisions; no personal approval inference, role impersonation or member-voting workflow. |
| PLN-UX-017 | Approved Blueprint v0.2 UX-17 — Publication and AO recovery | Approval, dispatch, publication and activation create unclear tasks and unsafe retries | Structure progress and responsible actor; AO evidence/late explanation, technical failure versus unknown and guarded statutory withdrawal/published-held correction | §§5.5.2, 8, 10.9, 10.12; U13/U21 | Blueprint v0.2 UX-17; PLN v1.18 corresponding U/C families | **PLN19-UX-033 / PLN19-UX-034** — AO Treasury evidence matches the exact approved document and records dispatch only; correction appends history. Late initial adoption/activation explanations occur in their correct contexts without backdating or ordinary-update duplication. Publication failure, unknown outcome and published-held remain distinct; only safe retry/reconciliation/eligible withdrawal actions appear for authorised actors. No blind retry, manual success or forced activation exists. |
| PLN-UX-018 | Approved Blueprint v0.2 UX-18 — Planner operational exceptions | Updates, source corrections and multiple holds lacked coherent recovery; the proposed forecast editor lacked reliable owner integrations | Keep progress and requests in item context; retain explicit source correction and aggregate unresolved hold; defer Planner forecast editing/reminders to a separately approved future facility | §§5.4–5.5, 10.13–10.15, 11.5, 15.3; U09/U14/U16 | Blueprint v0.2 UX-18; PLN v1.18 corresponding U/C families | **PLN19-UX-035 / PLN19-UX-036** — PLN19-UX-035 is future-only under §14; multiple correction requests retain the hold until each permitted terminal outcome, no-change requires reason, permanent scope remains and stopped REQ never auto-restarts. |
| PLN-UX-019 | Approved Blueprint v0.2 UX-19 — Readers, setup and access | Read-only and technical actors risk business controls or incomplete maintenance | Provide exact historical audit reading, complete CFG-owned MVP setup/verification tasks and accessible denied/masked states; no business power from technical read access | §§6.5, 9.5, 10.5, 10.11–10.12, 11.6; U12/C01–C04/U21 | Blueprint v0.2 UX-19; PLN v1.18 corresponding U/C families | **PLN19-UX-037 / PLN19-UX-038** — Auditor/reader follows exact historical departmental and Finance evidence and exports only authorised content; current warnings never overwrite the past and decision controls are absent. CFG-owned MVP setup exposes complete route/intake/catalogue/profile/verification tasks; reminder setup is future-only and absent. |
| PLN-UX-020 | Approved Blueprint v0.2 UX-20 — Usability acceptance separate from completeness | Document/POC approval is treated as proof users can work unaided | Retain full regression coverage; test role journeys without coaching, record comprehension and failures, and require retest of blocking or repeated confusion | §§9.8, 13.3, 14.4–14.5, 15.4; All | Blueprint v0.2 UX-20; PLN v1.18 corresponding U/C families | **PLN19-UX-039 / PLN19-UX-040** — Participant records cover ordinary and correction journeys for each decision/operational role with tasks stated without button coaching; observed behaviour, assistance and misunderstanding are recorded separately from interpretation. Any approval/certification/scope/coverage misunderstanding blocks usability acceptance; repeated confusion or coaching dependence is revised and retested. Document/prototype approval cannot mark participant, accessibility or release checks passed. |
| PLN20-CHG-001 | Project Owner instruction, 15 Sept 2026 | PLN v1.19 screen sections compressed content and behavior into dense prose without sufficient placement or action-state instructions. | Replace §10 in full with KT-STD v1.6 compositions for every U family; retain the exact domain and approved UX decisions. | §§9–10; U01–U16/U21 | KT-STD-001 v1.6 §§2.6–2.8 | PLN20-AC-001, 005–006 |
| PLN20-CHG-002 | Project Owner instruction, 15 Sept 2026 | Actor and state alternatives left the designer to decide which action/content appeared. | Give each actor/state a stable variant, external fixture, exact visible regions and definite enabled/disabled/absent controls. | §§10.3–10.17; All | KT-STD-001 v1.6 §§2.6–2.8; PLN v1.19 §10 | PLN20-AC-003–004, 008–010 |
| PLN20-CHG-003 | Project Owner instruction, 15 Sept 2026 | Some variants lacked exact identities, times, reasons or changed facts and invited invention. | Block design generation for that variant until the owner fixture supplies the named value; preserve truthful incomplete/error presentation. | §§10.4–10.18; affected variants | KT-STD-001 v1.6 §2.8 | PLN20-AC-004, 008 |
| PLN20-CHG-004 | Owner-document reconciliation | C01–C04 duplicated a partial CFG setup contract. | Use CFG v0.11 §10 as the only setup design input; keep Planning-side issue/owner/link compositions. | §10.16; C01–C04 | CFG-CHG-002 v0.11 §10 | PLN20-AC-002 |
| PLN20-CHG-005 | KT-STD conformance | Interactive purposes were scattered across runtime prose. | Add one complete design-to-interaction map outside design prompts, preserving existing command, authority and idempotency contracts. | §11.9; All controls | KT-STD-001 v1.6 §2.6; PLN §§5–8 | PLN20-AC-007 |
| PLN20-CHG-006 | Shared-standard adoption | Technical read used older/local language and could be confused with business or recovery authority. | Adopt KT-STD v1.6 §3A.6, explicit read-only Planning variants and shared registration; keep setup/publication recovery separately granted. | §§6, 10.17, 11.8–11.9, 14.6; U13/U21 | KT-STD-001 v1.6 §3A.6 | PLN20-AC-011–012 |
| PLN21-CHG-001 | Project Owner clarification, 17 Sept 2026 | U09 displayed Category, Requirement type, quantity, unit and horizon as unexplained read-only values; U06 did not visibly show how Category was established. | Select only governed Requirement type during U06 and derive/display Category immediately. In U09 use a compact classification summary linked to provenance; derive quantity/unit from included requirements and enforce Single year without a routine horizon field. | §§4.4, 9–11; U06/U09 | Approved v1.20 §§4.4, 10.5, 10.8 | **PLN21-AC-001–002 / PLN22-AC-004** — No independent Category input; provenance remains reachable without adding routine read-only clutter. |
| PLN21-CHG-002 | Gap resolution | Accepted classification was immutable but no lawful Planning-owned correction path existed; a departmental update would wrongly make the department correct a Procurement-owned fact. | Append an immutable reasoned classification correction against the accepted proceeding entry, preserve the acceptance and departmental facts, derive Category server-side and enforce authority/concurrency. | §§4.4, 5.1.6, 6–8, 12; U06 | Approved v1.20 classification and correction invariants | **PLN21-AC-003** — Original evidence remains exact; unchanged/stale/excluded/unauthorised corrections reject atomically; department recertifies only if its facts changed. |
| PLN21-CHG-003 | Reimplementation completeness | Downstream items and Plan Versions could silently retain or acquire conflicting classification after a correction. | Use corrected classification only for new work; mark affected unlocked Draft items for explicit dissolve/re-form; require full Plan correction/successor for unlocked governed content; hold rather than alter a Requisition/Tender scope-locked item; recalculate all dependent rules and expose complete UI/history/tests. | §§5.1.6, 7, 10–15; U06/U09 | Approved v1.20 source-correction, scope-lock, item-formation and Plan-succession rules | **PLN21-AC-004–006** — No in-place Plan or procurement mutation; Active baseline remains in force; eligible recovered item uses corrected classification; locked procurement requires its exact owner route; complete audit and tests. |
| PLN22-CHG-001 | Project Owner end-to-end simplicity review | The interface treated stored domain, audit and configuration facts as equal to the actor’s immediate task. | Enforce three visibility levels: current task, conditional supporting detail and audit/configuration evidence. Storage necessity does not imply routine display. | §§2, 9.3, 14.8; All | v1.21 §§9–10 and 17 Sept 2026 review | **PLN22-AC-001–002** — Ordinary pages lead with one task, one issue summary and one primary action. |
| PLN22-CHG-002 | Project Owner end-to-end simplicity review | Blank/default/inapplicable values were displayed to prove completeness, increasing density without helping decisions. | Omit blank, None, Not applicable, no-restriction and single-value defaults unless their absence changes the decision. | §§9.3, 10.6–10.10, 16; U07/U09/U11 | v1.21 U07/U09/U11 | **PLN22-AC-003** — Default and inapplicable data are absent from ordinary first views. |
| PLN22-CHG-003 | Project Owner end-to-end simplicity review | U01 repeated four reservation calculations before the user could reach the Plan. | Replace the calculation block with one plain shortfall statement and one recovery action; keep full arithmetic in Plan check detail. | §10.3; U01 | v1.21 §10.3 | **PLN22-AC-001, 006** — Workspace states the issue and action without duplicating the calculation. |
| PLN22-CHG-004 | Project Owner end-to-end simplicity review | Departmental funding and validation repeated full source/certification content and used an over-wide classification table. | Use a compact requirement summary with on-demand source/certification evidence; render requirement review as readable rows/cards with Requirement type as the sole classification input. | §§10.4–10.5; U03/U06 | v1.21 §§10.4–10.5 | **PLN22-AC-001, 012–013** — Departmental actors complete ordinary work without navigating record mechanics. |
| PLN22-CHG-005 | Project Owner end-to-end simplicity review | U07 mixed purchase formation, funding, approval, publication, project defaults and history in one preparation view. | Lead with Purchases and one concise Plan checks section; omit blank Project name and the premature Approval/publication section; keep History secondary. | §10.6; U07 | v1.21 §10.6 | **PLN22-AC-002–003** — Draft preparation exposes only current work and checks. |
| PLN22-CHG-006 | Project Owner end-to-end simplicity review | U09 exposed seven open sections and user-hostile fields including Procedure — Planning example, resolver status, Rule version, Source check and repeated reservation arithmetic. | Redesign U09 around Purchase details, Included requirements, Estimated cost, Procurement approach, Dates and current issues. Move evidence to one Supporting details disclosure; delete fixture/configuration leakage and default fields from the ordinary view. | §§9.3, 10.8, 11.2, 16; U09 | v1.21 §10.8 and supplied design review | **PLN22-AC-004–006** — Planner completes purchase decisions without reading system internals. |
| PLN22-CHG-007 | Project Owner end-to-end simplicity review | U10 made current balances and basis provenance visually equivalent to the affordability decision. | Keep approved, planned, difference and result in the first view; place availability and immutable basis provenance in supporting detail/history. | §10.9; U10 | v1.21 §10.9 | **PLN22-AC-007** — Finance’s decision basis is immediately understandable. |
| PLN22-CHG-008 | Project Owner end-to-end simplicity review | U11 required governance actors to traverse five dense evidence sections and automatically expanded purchase detail before reaching their decision. | Use decision summary, visible issues, concise purchase rows and actor statement first. Start all evidence closed while keeping every material issue visible and complete evidence reachable. | §§10.10, 11.3; U11 | v1.21 §10.10 | **PLN22-AC-008, 013** — Complete review no longer means simultaneous display of all evidence. |
| PLN22-CHG-009 | Project Owner end-to-end simplicity review | Publication business work and technical recovery risked appearing as one workflow. | Retain AO evidence and four business states in U13; expose retry/reconciliation only to the separately authorised technical operator and keep adapter mechanics out of ordinary copy. | §§10.12, 11.4; U13 | v1.21 §10.12 | **PLN22-AC-001–002, 012** — AO can complete publication evidence without technical terminology or unsafe controls. |
| PLN22-CHG-010 | Project Owner end-to-end simplicity review | U14 displayed unsupported completion/actual states and dense variance tables as routine Planning information. | First view shows planned scope, authorised coverage and current procurement stage. Completion/actual evidence appears only when an authoritative owner supplies it; unsupported fields are omitted. | §§10.13, 11.5; U14 | v1.21 §10.13 | **PLN22-AC-009** — No placeholder tracking or false completion inference. |
| PLN22-CHG-011 | Project Owner MVP boundary decision | U15 required the Planner to maintain a six-row forecast cascade without established downstream ownership or reliable actual integrations. | Defer U15, forecast cascades and forecast-driven reminders. Keep the approved schedule readable and permit only owner-supplied operational dates as read-only evidence until the future facility is separately approved. | §§2, 10.14, 11.5, 14, 15.3, 16; U15 | v1.21 §10.14 and forecast acceptance set | **PLN22-AC-010** — No MVP U15 route, control, artboard, reminder or release gate. |
| PLN22-CHG-012 | Project Owner end-to-end simplicity review | U16 led with request IDs, origin versions and orchestration states rather than the required correction. | Lead with what must change, affected purchase, hold consequence and lawful next action; retain request mechanics in detail/history. | §§10.15, 11.5; U16 | v1.21 §10.15 | **PLN22-AC-011** — Planner understands the issue and consequence without internal request terminology. |
| PLN22-CHG-013 | Reimplementation completeness | Existing composition and UX criteria could force the dense UI and deferred forecast facility back into implementation. | Amend conflicting acceptance wording, add 13 simplicity criteria, update inventory/interactions/prohibitions and require representative-user proof that complete evidence remains reachable without first-view overload. | §§10.18, 11, 14–17; All | v1.21 §§10–18 | **PLN22-AC-012–013** — Implementation passes simplicity/directness testing without weakening legal or server-side controls. |
| PLN23-CHG-001 | Project Owner consistency correction, 17 Sept 2026 | Forecasting was described as deferred, but four forecast/reminder acceptance criteria remained in the MVP gate and service/configuration entries still appeared current. | Make the deferral complete: no MVP forecast schema, route, API/service, U15 control, scheduler registration, reminder configuration or notification producer. Mark every affected legacy criterion future-only. Existing tested code may remain unreachable; greenfield work does not implement it. | §§4.8, 5.5, 7.5, 9–11, 14–16; future U15 | v1.22 §§4–17 and consistency review | **PLN23-AC-001** — Repository, route, service, scheduler, UI, configuration and acceptance inventories expose no forecast/reminder runtime entry point. |
| PLN23-CHG-002 | Project Owner consistency correction, 17 Sept 2026 | The accepted-classification history and correction panel were required in §10.5, but neither had a static design source; U09 only showed the downstream response. | Require two separate exact-fixture artboards, `U06-ACCEPTED-CLASSIFICATION` and `U06-CORRECT-CLASSIFICATION`, and block implementation of **Correct classification** until both are reviewed and inventoried. | §§10.5, 10.18, 14.9, 15.2; U06 | v1.22 §10.5 and design review | **PLN23-AC-002** — Both reviewed artboards exist; U09 is not accepted as a substitute. |
| PLN24-CHG-001 | Project Owner Stage 2 instruction, 21 Sep 2026 | Planning remained compositionally complete but still read as a dense specification translated into screens. | Adopt KT-STD v1.7 archetypes, primary questions and Level 1–3 information hierarchy across the complete Planning surface inventory without changing function. | §§9–10, 14.10; All | KT-STD-001 v1.7 §§2, 10; retained v1.23 function | **PLN24-AC-001–002** — Function remains exact and every composition has a task-led hierarchy. |
| PLN24-CHG-002 | Stage 2 workspace review | U01 could still become an equal-weight dashboard of counts, checks and lists. | Make the current Plan or immediate task dominant; attach issues and counts to that work and keep departmental plans secondary. | §10.3; U01 | v1.23 §10.3 | **PLN24-AC-003** — First view communicates current work and next action. |
| PLN24-CHG-003 | Stage 2 preparation/review review | Departmental and annual-plan preparation surfaces did not consistently distinguish editing, review and focused choices. | Assign form/editor, review/decision and dialog archetypes to U02–U09; put issue and action before evidence and retain all governed content. | §§10.4–10.8; U02–U09 | v1.23 §§10.4–10.8 | **PLN24-AC-004** — Users understand the immediate task before supporting evidence. |
| PLN24-CHG-004 | Stage 2 decision-screen review | Finance and governance evidence could still compete visually with the actual decision. | Put verdict, consequence, blockers and concise decision basis first; move provenance/history to reachable supporting levels. | §§10.9–10.10; U10–U11 | v1.23 §§10.9–10.10 | **PLN24-AC-005** — Decision purpose and consequence dominate without hiding material facts. |
| PLN24-CHG-005 | Stage 2 evidence/progress review | Detail, publication and monitoring screens lacked a single explicit question and could regress to record dumps. | Give U12–U14 detail/evidence or monitoring archetypes; preserve pinned truth, four-step publication state and coverage/stage scanning. | §§10.11–10.13; U12–U14 | v1.23 §§10.11–10.13 | **PLN24-AC-006–007** — Evidence and progress read as coherent stories, not undifferentiated tables. |
| PLN24-CHG-006 | Stage 2 exception/setup review | Corrections, setup issues and shared states could become generic panels detached from their parent task. | Give U16 a correction-workspace hierarchy and require C01–C04/U21 to inherit the parent archetype, orientation and action hierarchy. | §§10.15–10.17; U16/C01–C04/U21 | v1.23 §§10.15–10.17 | **PLN24-AC-007–008** — Exceptions preserve context and expose one lawful next step. |
| PLN24-CHG-007 | Stage 2 visual and verification review | Correct content could still be rendered with excessive cards, borders, badges, uppercase labels and equal emphasis. | Require visual restraint plus first-viewport and narrow-layout comprehension checks in the design and release gates. | §§10.1, 10.18, 14.5, 14.10, 15.4 | KT-STD-001 v1.7 §10 | **PLN24-AC-009–010** — Emphasis conveys importance and representative users identify context, priority and action without coaching. |
| PLN25-CHG-001 | Project Owner correction following the attached 30% reservation-rule review, 23 September 2026 | v1.24 treated the approved annual Budget, including unused headroom, as the compulsory 30% Planning denominator. | Use the eligible value of the exact current complete APP Version; keep the Budget as a separate ceiling and affordability control. | §§1, 5.5.3.1, 7.3, 9.5, 10.2–10.8, 13.2, 14.11, 15–18 | Attached review; approved LAW v1.2, CFG v0.13 and BUD v1.10 | **PLN25-AC-001–003, 005** |
| PLN25-CHG-002 | Completeness and anti-manipulation safeguard | A current-APP denominator could be understated by omitting expected procurement or become stale after an amendment. | Require complete coverage, evidenced item inclusion/exclusion and automatic recalculation for each approved successor APP Version while preserving historical snapshots. | §§5.1, 5.5.3.1, 13–15 | Existing coverage and succession controls | **PLN25-AC-003–004** |
| PLN25-CHG-003 | Measure separation | Planning allocation and actual achievement risked being reported from the same estimated values. | Keep planned allocation in PLN; calculate actual achievement only from authoritative downstream actual procurement values; retain county and other obligations separately. | §§2, 5.5.3.1, 7.3, 9.5, 14.11 | Proposed LAW v1.2 and CFG v0.13 | **PLN25-AC-006** |
| PLN28-CHG-001 | Project Owner report and decision, 26 Sep 2026 ("Visible") | A Need accepted after its department's plan was accepted was correctly pending for a later update (§5.1.2) but no screen said so: the plan read Done, U01 offered only Start departmental plan, and the Need's page was silent. | Derive and publish each accepted Need's position (§5.1.2, §7.3); make *Update required* the department's Your turn with Create update and the Planner's Waiting line (§5.7). | §§5.1.2, 5.7, 7.3; U02–U05 | FU-V127-07 | **PLN28-AC-001–002, 005** |
| PLN28-CHG-002 | Same | The department had no task and no My Work item. | U01-LATE-NEED task row, register status and spotlight action; §7.7 hand-off row. | §§7.7, 10.3, 11.9; U01 | FU-V127-07 | **PLN28-AC-004** |
| PLN28-CHG-003 | Project Owner instruction, 28 Sep 2026 (harmonize) | The accepted plan's tracker showed every stage Done beside Your turn, and its heading asked the Head of Department to review and submit. | Preparation Current for an owed update (§5.7, §10.1A.2); the §10.4 heading rule for a plan nobody can edit. | §§5.7, 10.1A.2, 10.4; U02–U05 | FU-V127-06 item 4 | **PLN28-AC-003** |
| PLN28-CHG-004 | Dead-end conformance | The §3B.7 matrix passed a Done answer for this state. | Add the §13.4 profile and assert the department's turn. | §§13.4, 14.13 | KT-STD-001 v1.9 §3B.7 | **PLN28-AC-002** |
| PLN30-CHG-001 | Project Owner decisions, 9 October 2026 (NDS-CHG-001 v1.17 §1.2) | A Need-origin entry started with no cost, so the departmental plan was the first place any cost was entered | Start the entry's amount from the accepted Need's estimate; Budget Line stays unselected | §§3, 4.3, 7.3; U03 | NDS-CHG-001 v1.17 §§4.3, 7.1A | **PLN30-AC-001–002, 006–007** — Prefill only where no operative amount exists; never overwrite. |
| PLN30-CHG-002 | Same | A revised planning amount gave the Head of User Department and the Procurement Planner no view of how far it moved from the requirement as accepted | Show the accepted estimate and the signed change on the funding panel, the register, certification and U06; no reason and no task | §§4.3, 10.4, 10.5, 11.9; U02–U06 | NDS-CHG-001 v1.17 §11.19 | **PLN30-AC-003** — Information only. |
| PLN30-CHG-003 | Same | Certified evidence did not record the figure the department started from | Freeze `need_estimated_total_cost` in the submitted snapshot | §4.3; U06 | — | **PLN30-AC-004** — Frozen at certification. |
| PLN30-CHG-004 | Same | A second amount could be mistaken for plan value | State that the Need's estimate is never summed into any total, and that older Needs and direct requirements are unaffected | §§4.3, 7.3, 13.3, 15.2 | NDS-CHG-001 v1.17 §§5.4, 7.1A | **PLN30-AC-005, 008–009** — Totals use operative amounts only. |

## 18. Approval effect

### 18.0A v1.30 approval effect

**PLN-CHG-001 v1.30 is approved by the Project Owner** (Project Owner instruction on 9 October 2026: **“1, Approved”**). It supersedes v1.29 and makes binding: the §4.3 entry reference and the prefill and change rules; the §7.3 `.v3` consumer; the U03-FUNDING-PREFILLED and U03-FUNDING-CHANGED variants and the estimate-change lines on U05 and U06 (§§10.4, 10.5); the §11.9 row; the §13.3 profile; PLN30-AC-001–009; PLN30-CHG-001–004; and the §15.2 dependency.

Recorded for the Project Owner: the decisions of 9 October 2026 are quoted in NDS-CHG-001 v1.17 §1.2: the estimate is required before a Need is submitted, and Planning shows the change from the accepted estimate and nothing more. Every string in bold that v1.30 adds in §§10.4 and 10.5 is new wording for review. Open owner decisions are listed in the change report that accompanies this version. This approval effect is not artboard approval, implementation or release evidence.

### 18.0 v1.28 approval effect

**PLN-CHG-001 v1.28 is approved by the Project Owner** (Project Owner instruction on 28 September 2026: **Mark them as approved.**). It supersedes v1.27 and makes binding: the §5.1.2 position rule; the §5.7 departmental-plan row and tracker rule; the §7.3 position contract to Departmental Needs; the §7.7 hand-off row; the U01-LATE-NEED and U02-ACCEPTED-LATE-NEED variants and the §10.4 heading rule; the §11.9 row; the §13.4 profile; PLN28-AC-001–005; and PLN28-CHG-001–004. NDS-CHG-001 v1.15 carries the matching receiving side (§15.2).

Recorded for the Project Owner: every headline and sentence in bold that v1.28 adds is new wording for review. **Project Owner decision, 28 September 2026: "Approved"** — the new wording in bold that v1.28 adds (§§5.7, 7.7, 10.3, 10.4). This settles the wording; it does not approve the document, which remains Proposed. The Project Owner then approved v1.28 on 28 September 2026 (control table). FU-V127-03, FU-V127-04, FU-V127-05 and FU-V127-06 items 1–3 remain owed and are not made by this version. This approval effect is not artboard approval, implementation or release evidence.

### 18.1 v1.27 approval effect (retained)

**PLN-CHG-001 v1.27 is approved by the Project Owner** as the reconciliation and handoff version. It supersedes v1.26. Approval makes the following binding:

- D2 as recorded in §10.1A.7: an over-budget line and a missing procurement method block Request plan funding confirmation; a reservation shortfall blocks Sign and submit Annual Plan only;
- the corrected U01 BASE and U07 BASE content and schedule result in §§10.3 and 10.6;
- the next-step table (§5.7), the BudgetRevisionRequest record, `RequestBudgetRevision` command, two error codes, owner contracts and hand-off register (§§4.7, 7.2, 7.3, 7.7, 8);
- the UI-only UPDATE-OVER-BUDGET fixture (§10.2) and negative fixtures (§13.4); and
- the §11.9 action-map rows and PLN27-AC-001–010; and
- the owner-version reconciliation in §1.2: LAW-REG-001 v1.2, CFG-CHG-002 v0.13, BUD-CHG-001 v1.10, NDS-CHG-001 v1.14 and STR-CHG-001 v1.8 are the current approved references.

With approval, every §10 variant introduced in v1.26 has its content, fixture and action mapping, and may go to Claude Design except variants still marked Awaiting fixture from v1.25 or v1.26. The BUD-CHG-001 and REQ-CHG-001 corrections in §15.2 remain required before the budget revision hand-off and the requisition item are integrated. Approval is not artboard approval, legal verification, implementation or release evidence.

### 18.2 v1.26 approval effect (retained)

**PLN-CHG-001 v1.26 is approved by the Project Owner** as a targeted presentation update. It supersedes v1.25. Approval makes the following binding:

- §10.1A and the per-screen next-step paragraphs in §§10.3–10.17 are the Planning content required by KT-STD-001 v1.8 §2.6.8 item 12 and §2.9, and are supplied to Claude Design with KT-STD-001 v1.8 §2;
- the U07 **Funding: Not yet checked** entry is replaced by the separate Budget fit and Finance confirmation facts of §10.1A.3;
- decisions D1, D3 and D4 are settled as recorded in §10.1A.7, and D5 is recorded as resolved; and
- U07-UPDATE-OVER-BUDGET, U07-WAITING-BUDGET-REVISION, U11-PLANNER and the two U01 row variants are added to the design inventory.

Approval does not decide D2, and changes no §§1–9 or §§11–17 rule other than the entries in §1.2 and §17.1 that record this version. Variants marked Pending D2 or Awaiting fixture are not design inputs until that input exists. The work in §10.1A.8 remains required before the affected controls are implemented. Approval is not artboard approval, implementation or release evidence.

### 18.3 v1.25 approval effect (retained)

**PLN-CHG-001 v1.25 is approved by the Project Owner.** It supersedes v1.24 and all earlier Planning implementation wording in full.

This approval retains v1.24's business, authority, governance, integration, audit, classification-correction, simplicity and Stage 2 presentation requirements, except that every 30% planning calculation, fixture, service boundary and acceptance result now uses the eligible value of the current complete APP rather than unused Budget headroom. Existing stable acceptance IDs remain traceable; PLN25-AC-001–006 govern this correction.

Approval is a requirements/design decision, not current-law verification, repository compatibility, completed actor testing, passed accessibility checks, migration proof or production deployment authorisation. Exact domain and owner prerequisites in §15/§17.2 remain. Approved CFG v0.13, BUD v1.10 and LAW v1.2 provide the coordinated owner contracts. Required future facilities remain explicitly deferred in §15.3.

Reimplementation must preserve immutable accepted classifications and Plan Versions while introducing the superseding correction record and effective projection. Existing machine identities and lawful accountability remain exact. Readable provenance never overwrites prior signed text. Complete evidence remains reachable, but it must not be reproduced wholesale in the ordinary first view. Do not ship contradictory earlier wording alongside this successor or force users to reconstruct the simplified UI from addenda.
