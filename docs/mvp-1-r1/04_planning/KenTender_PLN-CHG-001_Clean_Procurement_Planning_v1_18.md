# PLN-CHG-001 — Clean Procurement Planning

| Control | Value |
|---|---|
| Version | **1.18** |
| Date | 11 September 2026 |
| Status | **Consolidated successor for controlled adoption** |
| Supersedes | PLN-CHG-001 v1.17 as the implementation specification once this consolidated successor is adopted |
| Decision authority | The 72 approved decisions in PLN-REF-001 v0.1; the agreed UX direction and instruction to fold it into this successor |
| UX basis | PLN-UX-001 v0.1; focused workspace/AO/source-evidence proof of concept accepted by the product owner (“This is good”) |
| Change scope | Replacement governing rules, complete current model and command catalogue, corrected acceptance set, integrated static/functional UI specification and full re-implementation change table |
| Evidence boundary | Requirements consolidation only. No production schema, repository, legal source verification or release certification is asserted. |
| Implementation status | Not implemented by this document. External owner amendments and verification gates remain in §15 and §17. |
| Reading rule | §§1–16 and §18 are the current requirements. §17 records provenance, dependencies and replacement mappings; earlier wording quoted there is historical, not an alternative implementation option. |

This is a single Procurement Planning specification. The detailed rules, visual inputs, acceptance requirements and full 72-row change table are incorporated below. PLN-REF-001 and PLN-UX-001 remain provenance records; implementers need not combine their operative wording with v1.17. Citations bearing an explicit document ID refer to that historical or dependency document, not to this document’s section numbers.

## 1. Governing decision and disposition register

### 1.1 Current governing decision

Procurement Planning produces one consolidated Annual Procurement Plan per Fiscal Year from accepted departmental submissions. Departmental Needs is an optional consultation channel. A departmental submission may contain current accepted Needs, direct departmental requirements, or both. Every accepted Need within the submission's defined coverage must be accounted for either as proceeding or as not proceeding with a recorded departmental reason.

The Head of User Department certifies the departmental submission. The Procurement Planner validates it, classifies proceeding requirements, and consolidates the resulting eligible sources into Plan Items. The first accepted departmental submission creates the initial Draft Annual Plan automatically. Consolidation can proceed incrementally; no all-department completion gate or mandatory nil declaration is introduced.

Finance confirms the consolidated Plan's per-Budget-Line affordability. This confirmation creates no reservation and is separate from Plan approval. The Plan is formally submitted with preparation accountability, countersigned through Accounting Officer adoption, and approved through exactly one configured statutory route. Publication transmits the exact approved content after the Treasury-submission evidence gate. Authoritative acknowledgement plus successful activation checks activates the Version; a published Version that fails those checks is explicitly held under §5.5.2.

An Active Version remains the governing Planning baseline until an acknowledged successor replaces it. A correction never reopens submitted content. A forecast revision never changes approved baseline content. Requisition authorisation owns operational drawdown and the creation of Budget reservations. Tender Preparation owns template binding and tender-document preparation; Tender Publication owns the tender's publication action. No Planning command creates a Requisition, Tender shell, STD binding, wizard configuration or Tender workflow.

The preparation-signature decision in §6 is a deliberate refinement of who performs the existing final submission action. It must not be implemented as an assumed equivalence between Procurement Planner and Head of Procurement Function.

### 1.2 Source basis and approval interpretation

The product owner approved the refinement register, resolved every outstanding product decision and accepted the focused UX proof of concept. This successor records those decisions without claiming that the entire set of artboards has been rendered, user-tested or implemented. Detailed schema representations and cross-module payloads below make the approved rules implementable; coordinated owner amendments must adopt their matching sides before integration release.

Statutory propositions are attributed to the supplied LAW-REG-001 v1.0. This consolidation performs no new legal research and does not promote unresolved interpretations or illustrative constants to verified production law. Required legal source/layout verification remains an explicit dependency.

| Source | Version used | Specific use |
|---|---|---|
| Procurement Planning | PLN-CHG-001 v1.17 | Baseline rules, domain tables, lifecycle, UI, seed and acceptance criteria |
| Document standards | KT-STD-001 v1.4 | Document precedence, data-purpose gate, closed design input, authorisation states, common verification and fixtures |
| Responsibilities | AUTH-ADR-001 v1.7 | Role-bound responsibility assignments, organisational authority and segregation |
| Budget & Funding | BUD-CHG-001 v1.7 | Affordability, reservation ownership and Budget service boundaries |
| Departmental Needs | NDS-CHG-001 v1.10 | Current revision naming, unchanged event wire keys, accepted sources and Active Plan usage; its header remains proposed |
| Strategy Alignment | STR-CHG-001 v1.7 | Selection eligibility, lineage and the approval-time snapshot contract |
| Statutory register | LAW-REG-001 v1.0 | Supplied approved analysis of the Act and Regulations, including Council and the preparation signature |
| Configuration & Governance | CFG-CHG-002 v0.9, approved 3 September 2026 | Read in full when supplied during RI-064; existing catalogues, authority, fields, services and artboards reconciled in §17.2 |
| Requisitions | REQ-CHG-001 v1.7 | One-open-Requisition rule, authorised drawdown, Budget reservation and upstream correction |
| Tender Preparation | TPR-CHG-001 v0.7 | Publication-consumption acknowledgement and invitation actual-date event |
| Tender Publication | TPUB-CHG-001 v0.3 internally | Publication caller and invitation actual-date trigger; uploaded filename says v0.1 |
| Integrated fixture | SEED-001 v1.2 | Shared source allocations, amounts and downstream chronology |

### 1.3 Baseline section disposition

| v1.17 material | Disposition in v1.18 |
|---|---|
| §§1–3 cumulative history, purpose and ownership | Current rules in §§1–3; obsolete instructions removed; history preserved through §17 mappings |
| §4 model | Replaced by typed storage, projection and evidence contracts in §4 |
| §5 lifecycle/invariants | Replaced by §5; separate funding state, correction cohort, scope lock and publication recovery |
| §6 roles | §6; HOPF signs the existing final submission, four statutory capacities, correction-chain segregation |
| §§7–8 integrations/commands | §7; exact command inventory and coordinated producer/consumer contracts |
| §9 errors | §8; no Planning reservation-release error; profile-specific timing and explicit scope/correction/publication failures |
| §§10–12 UI/design/interaction | §§9–11; all 21 screen families and complete closed fixture pack incorporated |
| §13 audit | §12; immutable snapshots, append-only corrections and operational evidence |
| §14 seeds | §13 and §10.1; two items, three sources, KES 130m and corrected authority chronology |
| §15 acceptance, including duplicate AC-100 | §14 and §17.3; every old occurrence maps to a unique successor criterion |
| §§16–17 implementation/prohibitions | §§15–16; no copied obsolete reservation, optional-route or generic-period instructions |
| §§18–20 precedence/conformance/approval effect | §§17–18; actual source statuses and explicit external prerequisites |

The full decision-by-decision table is §17.4. All 72 decisions are agreed; their verification columns describe required work, not completed tests.

## 2. Purpose, outcomes and scope exclusions

Provide governed departmental requirements, incremental annual consolidation, source-backed procurement packages, affordability evidence, complete review, statutory approval, exact approved publication and controlled procurement eligibility. Departmental Needs is optional. Direct requirements are equally valid; no synthetic Need or bypass justification is created.

The MVP is single-year. It excludes asset disposal, STD/template binding, tender creation, technical specifications, supplier/candidate evaluation, Budget reservations, contract commitment, manual actual entry and procurement-scope expansion through an APP amendment. Planning supplies only its own facts to reporting; award, supplier, delivery and payment facts belong to operational owners. Explicit future facilities are listed in §15.3.

Every field below must serve its named consumer. Derived totals and statuses are never editable substitutes for authoritative records. No optional field, action, role or workflow may be added because a prototype happens to show it. Configuration belongs in the existing System setup surface and has no additional approval workflow.

## 3. Ownership and dependency boundary

| Concern | Authority | Planning's permitted responsibility |
|---|---|---|
| Site identity, Fiscal Years, department tree, units and configured approval route | Configuration & Governance | Read exact configured values; never create alternative catalogues or user FY grants |
| Assignment and organisational scope | Shared AUTH resolver | Apply the same role-bound authority to reads, commands, tasks, counts, files and exports |
| Need facts and accepted revision | Departmental Needs | Consume the exact revision and six facts; account for it in the DPP without changing it |
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
| Quantity | Exact positive decimal string with governed UOM precision. Need quantities are copied exactly, never rounded or partially allocated. Direct quantities obey the same UOM rule. BUD/NDS/REQ must agree precision at their boundaries before release. |
| Dates/instants | Business dates are ISO dates interpreted in site timezone; instants are UTC in services/audit and shown in Africa/Nairobi for the fixture. |
| Version token | Non-negative monotonic integer `record_version` on mutable aggregates/tasks; commands require the expected token. Display sequence numbers are never tokens. |
| Text | Trimmed nonblank text where required. Item title 5–160 characters, package description 10–1,000. Disposition, aggregation and forecast reasons 20–500. Other reasons identify an actionable issue and are capped at 1,000; no invented optional note. |
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
| DPPEntry `quantity`, `unit_id`, `required_by_date` | A or S/Quantity, UOM ID, date | Required | Read-only NDS snapshot; direct Draft edit | Other three source facts; required-by inside FY; enabled UOM |
| DPPEntry `budget_line_id`, `indicative_amount` | A/BUD ID, Money | Proceeding entry only | Departmental Draft edit | Eligible line for OU/FY, positive full estimate including incidentals; clear operative values when not proceeding |
| DPPEntry `currency` | P/currency code | Budget service | Never entered | Calculation/display; exact currency retained in certified evidence |
| DPPEntry `not_proceeding_reason` | A/text | Need origin only when excluded | Draft set/restore; frozen at certification | 20–500 characters; presence derives non-proceeding disposition; no second editable status |
| DPPSubmission `dpp_submission_id`, `dpp_version_id`, `submission_number` | S/IDs, sequence | Server | Immutable | Number equals certified DPPVersion number |
| DPPSubmission `submitted_entry_snapshots`, `source_cohort` | S/ordered entry schema, tagged stable IDs | Certification | Immutable | Full facts, funding, dispositions and exact lineage; cohort is the certified set |
| DPPSubmission `attestation_text`, `submitted_by_user_id`, `authority_snapshot`, `submitted_at` | S/text, ID, AUTH evidence, instant | Certification | Immutable | HoD accountability; assignment/capacity/effective interval actually exercised |

Direct requirements have exactly the six source facts plus Budget Line and indicative amount; they have no Need link, bypass reason or generic attachment field. Need funding/disposition edits never edit NDS facts. Corrections update the exact accepted revision only within the stable cohort.

Initial/update certification: **I certify that this Departmental Procurement Plan accounts for the current accepted Departmental Needs within this submission’s coverage, including those not proceeding with recorded reasons, and the direct requirements shown. The proceeding requirements’ quantities, required-by dates, Budget Lines and indicative amounts are ready for Procurement validation.** Correction certification identifies the returned Submission and its fixed coverage rather than falsely certifying unrelated later Needs.

### 4.4 Departmental validation

`DPPValidationTask` stores generated task ID, exact submission ID, Open/Completed/Cancelled state and record token. FY/OU are resolved from the submitted record, not duplicated as authority. `DPPValidationDecision` stores decision ID, task/submission ID, Accept or Return, actor, exact AUTH assignment snapshot and decision instant. Acceptance contains one `{dpp_entry_id, requirement_type_id, procurement_category}` row per **proceeding** entry. Category is Goods, Works or Services; the finer type comes from the governed catalogue. Return contains one or more `{dpp_entry_id, problem, correction_required}` issues; a submission-wide issue may omit entry ID. Decision rows are immutable. There is no claim, priority, score or generic note.

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
| `procurement_category`, `requirement_type_id` | P/classification | Accepted proceeding entries | Never manually overridden | All combined sources compatible; Goods/Works/Services and governed finer type |
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

`PlanSourceAllocation` stores immutable generated allocation ID, exact item-version ID, stable item ID, exact accepted DPP entry/submission IDs, source origin, stable source key, Need/revision IDs where applicable, full quantity/UOM, Budget Line, Money amount/currency and allocation state. Values are copied from accepted evidence, not user overrides. States are Draft, Active, Released, Removed in successor, Superseded. The allocation ID is exposed to REQ as `plan_item_line_id`. At most one effective allocation per stable source per admitted open Plan Version; Released is historical and may be re-formed. Accepted non-proceeding sources have no allocation. Ordinary copies preserve cumulative consumed capacity through stable identities.

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
| PlanDecision | ID, task/snapshot IDs, action, actor/AUTH/capacity, instant, reason on return, collective resolution reference for Board/Council decisions | Immutable; incompatible-action chain survives copies; no optional note field |
| LateActivationExplanation | ID, initial Plan Version ID, reason, actor/AUTH evidence, recorded instant, optional superseded explanation ID | AO-owned append-only record; at late adoption or later separate action; never rewrites publication/activation time |

### 4.8 Downstream use, correction and operational evidence

| Record | Required typed fields | Validation / consumers |
|---|---|---|
| AuthorisedDrawdown | ID; REQ ID/exact Version ID; stable item and exact Plan/item-version IDs; list of allocation IDs and positive Quantity/Money drawdowns; actor/service correlation and instant | Inbound REQ only; cumulative source/item allowance; atomic with REQ authorization and BUD reservation; immutable |
| DrawdownReversal | ID; original drawdown ID; exact reversible line amounts/quantities; REQ reversal evidence and instant | Inbound REQ only; cannot exceed unreversed original use; never deletes first-authorization scope evidence |
| PlanItemCorrectionRequest | ID; requesting REQ/Version IDs; stable item/exact approved Plan Version IDs; reason; requester/authority; received instant; producer event/key; Open/In progress/Resolved/Closed without change; token | Record plus hold atomic; Planner dispositions; Resolve requires actual Active correction and replacement lineage; no-change requires reason |
| CorrectionDisposition | ID; request ID; action; actor/authority/instant; reason or Active corrected Version and exact replacement allocation mapping | Append-only; releases derived hold only after every request terminal; no stopped-REQ restart |
| ProceedingCoverage | Owner-supplied proceeding ID/type; authorized REQ/Version IDs; exact Plan/item/allocation IDs; covered quantity/value and current authorization/publication/reversal evidence | Read-only operational projection; never inferred from stable item link alone |
| MilestoneActualEvent | Producer + event ID; schema version; proceeding/REQ/Plan/item/allocation IDs; milestone; actual date; recorded instant; producer sequence; optional superseded event ID; source evidence reference | Authenticated owner only; duplicate ID no-op; correction same proceeding/milestone; preserves both facts; invitation path available, other six integrations future |
| ForecastRevision | Generated revision ID; exact Plan/item IDs; proceeding ID where schedule responsibility transferred; milestone; prior/new dates; reason; cascade ID if multirow; actor/instant; prior revision ID | Active operational schedule only; append-only; baseline and actual unchanged; preserve on supersession |
| ComparisonBasis | Exact baseline Version/milestone and forecast revision ID used for a proceeding comparison | Freeze reference for comparison; never compare an actual to a later reforecast silently |
| MilestoneNotice | Shared-notification identity: recipient + stable item + proceeding if any + milestone; derived due/status/history | One evolving notice; no daily duplicates; no approval task, blocking state or proof of completion |

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

The canonical public JSON is `KenTenderAnnualPlan.v1`: metadata (schemaVersion, publicationId, planId, planVersionId, versionNumber, fiscalYear, entity public name, approvedAt, publication character), header (title, optional projectName), items (stable/exact IDs and all applicable §4.6 governed fields), sources (approved exact source/allocation/funding facts), totals (currency and per-line/plan amounts), and approved governance/rule/Strategy evidence references suitable for public disclosure. Every Money/Quantity is a decimal string; dates ISO; IDs opaque; inapplicable values null with applicability stated. No ocid, disposal block or operational actual/forecast overwrites. Internal assignment IDs, confidential attachments and financial availability statements are not automatically public: the publication adapter contract must explicitly map each public field to the prescribed format and its lawful disclosure policy. The protected review pack includes the complete internal governed content/evidence index for the authorized reviewer. Web/PDF/JSON consistency is tested against one snapshot; exact external adapter serialization and verified Schedule column mapping remain release prerequisites in §15.

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

#### 5.1.3 Window rules

The existing Fiscal Year flag and close instant remain the only initial intake control. A root with no accepted predecessor requires an open window for initial submission, including reopening a withdrawn initial Draft. Existing Draft work remains readable and saveable after closure; closure does not delete it.

A copied correction of a submission validly made while the window was open may be resubmitted after closure, within the fixed coverage rule above.

**Agreed clarification:** once a department has an accepted DPP, it may prepare a governed update for changed requirements, including newly accepted Needs and new direct requirements. Eligibility is based on the accepted predecessor and update lifecycle, not on a requirement that the change originate from a Need event. The current source-change-only wording leaves direct requirements without a coherent mid-year update route. Updates remain subject to HoD certification and Procurement validation; they do not bypass Annual Plan succession.

#### 5.1.4 Not proceeding

| Rule | Exact agreed behaviour |
|---|---|
| Who records the outcome | Departmental Author or Head of User Department with authority over the Draft DPP's department |
| Allowed source | Need-origin entry only; an unsubmitted direct entry may instead be removed |
| User action | **Do not proceed this financial year** |
| Required input | **Reason for not proceeding**, 20–500 characters |
| Funding effect | Clear the current Draft's Budget Line and amount from operative funding specification; preserve earlier certified values in their immutable submissions |
| Source effect | Preserve the accepted Need identity, revision, all six facts and full quantity in the DPP snapshot |
| Readiness effect | The entry satisfies Need coverage, requires no funding or procurement classification, and is excluded from consolidation and monetary totals |
| Reversal before certification | **Restore to planned requirements**; remove the current Draft disposition, require fresh funding completion and retain the change in audit history |
| Certification | The HoD certifies both proceeding and non-proceeding entries in the same DPP; no extra approval stage |
| Procurement acceptance | Accept the complete submission, including its exclusions; only proceeding entries become consolidation sources |
| Entire submission not proceeding | Permitted where at least one current accepted Need is accounted for; it is not an empty submission or a mandatory nil declaration |
| Empty Annual Plan | Acceptance can create the initial Draft with zero proceeding sources. Submission readiness requires at least one proceeding Plan Item; an empty Draft is not advertised as an approved Plan. |

Define a Planning-owned command `SetNeedPlanningDisposition` for the two Draft actions, with entry identity, expected version and idempotency key. The not-proceeding branch additionally requires the reason. Submitted or accepted dispositions can change only through a new DPP submission.

NDS v1.10's `NeedPlanningUsageChanged.v1` means Active Plan inclusion only. It must retain that meaning. The agreed `NeedPlanningDispositionChanged.v1` event records the separately accepted DPP disposition and its source revision, submission, reason, actor, decision time and ordering identity. Departmental Needs displays it as Planning information without changing Need lifecycle or the existing `Fully included`/`Not included` usage projection. This is a coordinated NDS contract addition, not an undisclosed extension of the existing event.

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
| Active | Baseline locked | Current governing baseline; controlled forecast and append-only operational evidence may change separately |
| Superseded | Historical baseline and forecast history preserved | Replaced by an acknowledged successor |
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
| Published — activation held; no open correction candidate | Prepare correction successor | Procurement Planner | One linked Draft correction; held Version cannot authorise Requisitions; full governance applies |
| Active; no open candidate | Prepare plan update | Procurement Planner | Copy to one Draft successor; predecessor remains operational |
| Draft successor or correction of that successor | Cancel update | Procurement Planner | Cancel the open candidate chain; predecessor unchanged; no reservation release |
| Successor publication acknowledged; all activation checks pass | Activate successor | System | Atomically change Active pointer, preserve balances and history, apply approved removals and publish eligibility/usage changes |

The approved Head of Procurement Function decision replaces the current Planner's final submission action; it does not add a second final submission, professional-review approval or separate approval state. The required preparation signature must be represented in the consolidated requirements and corresponding role-to-action contract.

### 5.3 Financial basis and confirmation

#### 5.3.1 Basis and verdicts

The financial basis comprises Fiscal Year, each operative Procurement Budget Line, currency, total planned against that line and the approved amount against which the comparison is made. Capture the Budget version/revision references needed to reproduce the comparison. Exact fingerprint serialization belongs in the service contract; no fingerprint is an editable business field.

| Comparison | Effect |
|---|---|
| Planned total exceeds approved amount | Blocking for affirmative Finance confirmation and formal Plan submission |
| Planned total exceeds currently available amount but is within approved amount | Advisory only; no Finance failure and no reservation |
| Referenced line no longer eligible or currency/source funding identity changed | Current eligibility/basis must be re-evaluated; do not reuse a confirmation by comparing totals alone |

Pre-Finance readiness excludes the test **funding already confirmed**. Otherwise `RequestPlanFundingConfirmation` would depend on its own result. Formal submission adds that test to the remaining readiness requirements.

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

While Active funding evidence is stale, retain v1.17's eligibility gate on new Requisition authorisation. Existing authorised Requisitions and their reservations are not revoked by a Planning evidence-state change. The agreed Active reassessment closes the otherwise missing recovery path and must appear in the roles, service, UI and acceptance contracts.

No reassessment overwrites the original Finance statement attached to the approved Plan. Readers can distinguish **Funding evidence at approval** from **Current funding confirmation**.

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
| Scope of the restriction | It is item-specific. Other items, new Needs and legitimate APP updates remain possible. Existing controlled forecast updates do not by themselves enlarge procurement scope. |
| Published-Tender changes | Any lawful amendment, cancellation/replacement or later contract variation belongs to its own governing module and procedure. APP approval alone authorises none of those actions. Scope expansion through such procedures is outside this MVP recommendation. |

Do not unlock the item merely because an APP successor has a new identifier or a newer DPP source revision. Revocation or cancellation does not silently reopen the scope through Planning; any future reopening/replacement mechanism requires an explicit coordinated contract. This rule does not redefine the existing Requisition-owned reversal of unused drawdown and reservation.

**Enforcement:** resolve the authoritative Requisition-authorisation and downstream-use evidence server-side. Enforce the item restriction during source formation/re-formation, source substitution, relevant item saves, APP submission and successor activation. Requisition authorisation and APP activation must serialise against the same stable-item scope/lineage guard so a concurrent authorisation cannot be bypassed by a previously prepared scope-expanding successor. Disabling an editor control alone is insufficient. A rejected command leaves allocations, totals, workflow state, drawdown and publication evidence unchanged.

**Required error:** `PLN_ITEM_SCOPE_LOCKED` — **This Plan Item already has an authorised Requisition. Create a separate Plan Item for the additional requirement.**

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
| After activation | A later forecast is allowed and flagged. Do not reject an honest late forecast merely because the baseline feasibility gate would have failed |
| Cascade | Always propose the remaining eligible forecast changes. Validate every affected adjacency in the resulting schedule, including included/excluded row boundaries. Allow a final-milestone single-row change with a reason |
| Historical evidence | Lock baseline and resolved rule-profile evidence at submission. Initialise forecasts on activation; retain the last forecasts and append-only revisions after supersession |

Profiles belong in the existing System setup surface under Configuration & Governance. Specify method and procedure, milestones and sequence, counting rules, statutory limits with source references, internal default periods/buffers, effective dates and Version. Administrator/System Manager maintains them under existing configuration authority; no new approval workflow is introduced. Referenced Versions are immutable and changes audited. The work includes records, maintenance screens, resolver, validations, verified seeds and acceptance coverage, not only a new configuration field.

Multi-year support will require full package value and completion horizon, annual funding allocations, separation of approved and anticipated future funds, authority to commit future obligations, and corresponding Budget/Requisition contracts. It remains outside this MVP.

#### 5.5.1A Actuals and distinct variance measures — RI-032, 038

Record actuals **per procurement proceeding**, linked to the exact Plan Version and source allocations, quantities and values that the proceeding covers. Show each proceeding beneath the Plan Item. Do not collapse different Tender dates into an unqualified item-level actual. Sequential drawdowns within the original allowance remain permitted.

For example, two Tenders for 100 and 150 laptops may have invitation actuals on 1 May and 1 September. Both must remain visible. Selecting either as the actual for the entire 250-laptop item loses material information.

- A repeated event ID is idempotent; a different Tender's event is a separate fact.
- A correction references and supersedes the earlier event; it does not overwrite it. Define producer ordering and correction linkage so replay cannot restore obsolete evidence.
- Preserve the exact baseline Version and identified forecast revision used in a comparison. Never substitute the latest APP or a forecast revised after the event.
- Planning accepts actuals only from the module owning the real event. TPR/TPUB already defines the invitation actual path; the other six operational event integrations remain future owning-module work.
- Aggregate item-level milestone dates are outside the MVP.

| Measure | Formula and meaning |
|---|---|
| Baseline lateness | Actual milestone date − baseline milestone date. Positive is late; negative is early |
| Forecast error | Actual milestone date − identified forecast date. Positive is later than that forecast |
| Duration variance | Planned elapsed days − actual elapsed days. Negative means the stage took longer; this is the convention recorded in the supplied LAW register |
| Elapsed days | Calculate between the explicitly defined start and end events using the applicable profile counting rule |
| Missing evidence | Show Not available when required actuals or comparison evidence are absent; show Not applicable for an inapplicable stage. Neither is zero |

Use explicit labels, not an unexplained Variance heading. A stage may start and finish late yet take fewer days than planned. Statutory duration fields must not be populated with simple milestone-date lateness. Preserve the distinction in views, review packs, publication/report mappings and tests.

#### 5.5.1B Reminders — RI-040

Run a daily check against every applicable outstanding milestone, independently, so a missing earlier actual cannot hide later reminders. Before a proceeding exists, use the item's current forecast or approved baseline if unrevised. Once proceedings exist, follow their identified schedules and exact baseline lineage.

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

Freeze publication files and their hashes. Retries resend the exact approved files under the same publication identity. Preserve Annual Plan ID, exact Plan Version ID and stable Plan Item IDs. Disposal content is excluded. Operational forecasts and actuals appear separately; they never rewrite the approved publication. Approved successors create new publications and retain predecessors.

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

Each obligation has its own calculation. For the annual-procurement-budget target, Budget & Funding supplies the complete approved annual procurement budget and exact Version. Do not use Plan total, available funds or only the lines used in the current Plan as the denominator.

| Concern | Approved rule |
|---|---|
| Qualifying allocation | Sum only planned value explicitly reserved for categories eligible under that obligation |
| Partial package | Count only its expressly allocated qualifying amount. MVP requires a separately identified Plan Item for that allocation; a lotting flag does not make the full package qualifying |
| County requirement | Separate applicable calculation with legally verified denominator and eligible categories; never combine 20% and 30% into one target |
| Overlap | Count once within each measure; count towards both only where verified rules permit. Do not infer eligibility from a generic reservation label |
| Display | Required allocation; Planned qualifying allocation; Shortfall; Budget basis, including exact Version |
| Submission | Incomplete Drafts permitted. Block Sign and submit Annual Plan where a verified mandatory planning allocation is unmet or its calculation basis is missing |
| Override | A justification does not waive the mandatory allocation |
| Later gates | Preserve submission-time budget/rule Versions and recheck subsequent positive decisions; do not rewrite historical results |

Example: an annual procurement budget of KES 100 million, Plan total KES 40 million and qualifying allocation KES 12 million yields 30% of Plan value but only 12% of the annual budget. The former must not be reported as satisfying a 30% annual-budget requirement.

This consolidates the replacement of the blanket advisory-only rule in PLN and CFG. It can require further qualifying allocations before a partially consolidated Plan enters approval, without requiring every department to submit. The measure is **planned allocation**, not proof of actual procurement achievement. Awards and implementation results remain downstream. Exact eligible categories, county basis and permissible overlap remain legal-verification prerequisites; absence of verified mandatory configuration cannot be reported as success. Keep the optional market-price index separate.

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
2. Combination requires the same FY, Procurement Budget Line and currency, compatible UOM and procurement treatment, identical accepted category and requirement type, and the required aggregation reason. Multiple departments may contribute; the source OU still governs Budget Line eligibility. No blank item, partial Need or fabricated residual source is permitted.
3. Item quantity/value and funding breakdown equal exact source allocations. Estimates include applicable incidental costs and have an identifiable market-survey basis. An item cannot gain capacity by dissolving and re-forming consumed sources under a different identity.
4. Pre-Finance readiness requires a nonempty proceeding Plan, eligible allocations, complete package/classification/Strategy/designation/structure and a valid calculable schedule. It excludes current Finance confirmation to avoid circularity. Draft saves remain possible with displayed blockers. Formal submission additionally requires current affordability, verified applicable method/reservation rules, complete required evidence, valid route and HOPF signature.
5. Only the Planner classifies departmental proceeding requirements and forms/edits items. Departmental users certify their requirements, not procurement classification or Strategy selection.
6. A splitting detection advisory is a prompt for assessment, never authority to waive a mandatory method/cumulative limit. Record the related item set, triggering rule Version and reasoned confirmation/aggregation response. Re-evaluate after relevant changes; mandatory conditions still block. Lotting or planned reservation alone is not a blanket anti-splitting exemption.
7. Forecasts are operational records initialized at activation; immutable baseline remains exact. Preserve history on supersession. Per-proceeding actuals do not update one unqualified item actual. Missing comparisons are Not available; inapplicable milestones are Not applicable.
8. An Active predecessor is retained while an update proceeds, subject to its own live funding, remaining allowance and correction-hold gates. Read access, pending work or a successor alone cannot create or revoke procurement authority.

## 6. Roles, permissions and segregation

All rows are subject to current AUTH assignment, OU scope, task and segregation. Read authority is not implied by possession of a link. Departmental users see their permitted source/Plan information, not other departments' protected evidence.

| Actor | Workspace emphasis | Allowed work | Explicit boundary |
|---|---|---|---|
| Departmental Author | Own departmental Drafts/corrections | Direct/source funding and disposition Draft work | No HoD certification unless separately assigned |
| Head of User Department | Departmental certification/updates | Certify/submit within current substantive or acting authority | Cannot validate own certified Submission as Planner |
| Procurement Planner | DPP validation, consolidation, pending requirements, corrections | Package work, Finance request, successor/correction management and forecasts | No final HOPF signature unless separately assigned; no procurement creation |
| Head of Procurement Function | Plan ready for preparation signature | Complete review; Sign and submit Annual Plan | This is preparation accountability, not an added approval stage |
| Finance Confirmation Officer | Current plan-level review/reassessment | Confirm plan funding or Return to planner | No editing the Plan or reserving money |
| Accounting Officer | Adoption, Treasury evidence, late explanation and withdrawal requests | Existing governed actions | Does not impersonate the statutory authority |
| Configured statutory authority | Exact Plan adoption/withdrawal request | Approve, return or confirmed-unpublished withdrawal as allowed | Board/Council record collective resolution and authorised recording actor |
| Auditor/authorised reader | Plan and evidence navigation | Read-only history, permitted review pack | No business decision |
| Administrator/System Manager | Setup; technical publication work if granted | Configuration and supported technical retry | Technical access supplies no business authority |

If a user holds multiple responsibilities, render permitted actions together and enforce incompatible action history across the correction chain. Do not select one role label and hide the others' legitimate work. Do not add an assignee picker to route around an unavailable or conflicted actor.

#### 6.1 Exactly one statutory route

Use the four capacities stated by the supplied LAW register: **Cabinet Secretary**, **County Executive Committee Member**, **Board**, and **Council**, resolved to the exact applicable configured legal capacity. Board and Council decisions retain their collective resolution reference and authorised recording actor. They are alternatives, not sequential approvals.

Missing or ambiguous configuration prevents formal Plan submission and is rechecked at adoption. Detecting it before submission avoids placing a Plan into a route that cannot complete. Configuration never permits `None` as a successful route.

CFG v0.9 §4.1 already defines the four route values and county applicability. Complete their configuration inputs, review snapshots and central AUTH responsibility mappings as specified in §17.2. Planning must not invent a local approver registry. An in-flight governance task retains its exact required capacity and evidence; configuration edits cannot silently convert that task into a different approval route.

#### 6.2 Preparation signature

LAW §1 quotes the Third Schedule preparation signature as Head of Procurement Function, but LAW-REG-001 §1.1 then equates that office with the Procurement Planner. KT-STD §8.3 explicitly distinguishes Mercy Kilonzo's Planner responsibility from Charles Mutiso's Head of Procurement Function responsibility. The role mapping therefore remains a real gap even within the supplied documents.

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

A governance return preserves the incompatible-action history through every linked correction. Creating a new Draft or changing an actor's role label does not reset it. A new independently governed successor after activation starts its own candidate chain while preserving predecessor audit history. Technical read-all access is never a business-decision exception.

## 7. Service, command and cross-module contracts

### 7.1 Common envelope and reads

Each mutating request carries `{aggregate_id, expected_version, idempotency_key, payload}`. The server derives actor, site and AUTH assignment, never trusts supplied actor/capacity or task visibility. The relevant aggregate/task token and exact business Version are both checked inside the transaction. A matching replay returns the original result; reused key with different payload is rejected. Creation serializes on the natural root key. Protected reads return one typed authorization verdict with data; masked records disclose no existence. Financial year is a filter/operation input, never a permission grant.

| Read contract | Inputs beyond authenticated context | Exact result / consumer |
|---|---|---|
| ResolvePlanningContext | Optional FY/department filters | One site, current responsibility-bound OU scopes, configured FY options and verdict; no PE selection or stored user authority |
| GetPlanningWorkspace | FY and allowed department filter | Independent Active/candidate links, actionable work, departmental status, eligible/pending sources and schedule-health projection; same predicate for counts/rows |
| GetDepartmentalPlan / GetDppEntryEditor | Exact root/Submission/entry identity | Six source facts, dispositions, source-cohort coverage, funding eligibility, accepted/current pointers and authorized commands |
| GetDPPValidationTask | Task ID | Exact full certified snapshot, proceeding classifications, non-proceeding evidence and positive/return guards |
| GetAnnualPlan / GetPlanItem | Stable ID plus exact Plan Version or item-version ID | Complete §4 content, sources, funding history/current validity, readiness, changes and decisions; never silently switch to latest |
| GetPlanGovernanceTask / GetPlanReviewPack | Exact task/Version ID | One complete protected review snapshot and evidence index; same field coverage in screen/export; status-labelled unapproved pack |
| GetSourceEvidence | Exact DPP submission/entry and optional Need revision, parent Plan Version | Source facts, Budget allocation, certification/acceptance and reviewed Strategy lineage; preserve caller return context |
| GetFinanceTask | Task ID or Active Version reassessment context | Whole-plan exact financial basis, as-at statement, approved/available distinction and immutable history |
| GetPublicationTask | Publication/Version ID | Approved package, Treasury history, attempts, confirmed/unknown result, hold/withdrawal/activation outcome and allowed recovery actions |
| GetRequisitionEligiblePlanItem.v2 | Stable item ID and requesting record/OU context | Eligible or specific blocked result; exact §4 lineage, all contributing OUs, strategy/path, category/type/method/designation/structure, source facts, baseline dates, approved/drawn/remaining amounts, current funding, holds and evaluation instant |
| GetRegulatoryReference | Reference kind, FY, method/category and rule-specific applicability inputs | CFG-owned exact Version, effective interval, applicability basis, verification state, limits/conditions/counting; not a blanket FY-only lookup |
| PreviewForecastCascade | Exact Active item/proceeding and schedule token, milestone, proposed date | Delta and all subsequent not-yet-actual applicable rows, original/proposed values and full adjacency findings; no writes |

### 7.2 Command catalogue

All commands inherit §7.1, field rules in §4, state rules in §5, and segregation in §6. Returns use corrective predicates and must remain available when stale evidence prevents a positive decision. A command returns the common committed result and the specific evidence/objects listed below. Input fields not on the allow-list are rejected, not silently accepted.

| Command / actor | Payload and allowed state | Atomic effect and guards |
|---|---|---|
| OpenDepartmentalPlan — Author/HoD | FY, OU; permitted initial intake or existing authorized Draft | Create/reuse unique root/Draft; reopening withdrawn initial creates next number while intake open |
| SaveNeedFunding — Author/HoD | Draft entry ID, Budget Line, indicative_amount | Change only funding; source facts protected; reject not-proceeding funding mutation until restore |
| SetNeedPlanningDisposition — Author/HoD | Draft Need entry ID; Do not proceed + 20–500 reason, or Restore | Set reason and clear operative funding, or restore and require fresh completion; audit; no accepted event before DPP acceptance |
| SaveDirectRequirement — Author/HoD | Draft entry/new direct source; six facts, Budget Line, indicative_amount | Generate stable direct_source_id on first creation only; validate enabled UOM/date/funding |
| RemoveDirectRequirement — Author/HoD | Current Draft direct entry ID | Remove unsubmitted direct entry only; no upstream Need or financial mutation |
| CreateDepartmentalPlanUpdate — Author/HoD | Accepted DPP ID | One copied Draft; admitted changed/new Needs and direct requirements; accepted pointer retained |
| WithdrawDepartmentalSubmission — HoD | Mutable candidate ID, reason | Withdraw candidate without downstream consumption; accepted predecessor retained; submitted evidence never reopened |
| SubmitDepartmentalPlan — HoD | Draft Submission ID; certification acknowledgement | Recheck applicable cohort/window/coverage, full quantities, proceeding funding and authority; freeze snapshot; create validation task |
| ReturnDepartmentalPlan — Planner | Open task; structured issues | Preserve reviewed submission; record decision and create next Draft correction in same cohort |
| AcceptDepartmentalPlan — Planner | Open task; classifications for proceeding entries | Recheck source validity and segregation; accept complete submission including exclusions; atomically create/reuse initial APP and source projections |
| FormPlanItems — Planner | Draft Version, selected exact accepted entry IDs; Separate or Combined; aggregation reason when combined | Allocate each admitted source once/full; compatibility and source/scope-lock guards; no Budget mutation |
| DissolvePlanItem — Planner | Mutable exact item-version ID | Preserve item/history, mark allocations Released, recompute financial basis/open review; no reservation release |
| SavePlanItem — Planner | Draft exact item-version; §4.6 editable fields only | Resolve profiles and recompute schedule/readiness; no source/quantity/value override; enforce permanent scope guard |
| SavePlanVersionDetails — Planner | Draft Version; optional project_name, required successor change_reason | Whole-Plan fields only; no per-item project or new Project record |
| ConfirmSplittingAdvisory — Planner | Draft Version; current related-item/rule finding; reasoned response | Retain assessment evidence; mandatory method rules remain blocking; stale finding rejected |
| RequestPlanFundingConfirmation — Planner | Draft or exact unchanged Active Version; expected financial basis references | Pre-Finance readiness for Draft; whole-plan review/reassessment; at most one open task; explicit reuse/cancellation history |
| ConfirmPlanFunding — Finance | Open task, expected basis ID | BUD decision-time validation; immutable whole-plan confirmation; no Budget financial record; Plan lifecycle unchanged |
| ReturnFromFinance — Finance | Open task; actionable reason | Immutable return; Draft remains Draft; Active reassessment does not reopen Active content |
| SubmitConsolidatedPlan — HOPF | Ready Draft; exact complete snapshot confirmation | **Sign and submit Annual Plan**; preparation signature, content lock and AO task; no extra HOPF approval state |
| AdoptAndSubmitPlan — AO | Open AO task; late-initial explanation if FY already begun | Adopt exact reviewed Version; recheck positive predicates; create one configured statutory task |
| ApproveAnnualPlan — statutory capacity | Open statutory task; collective resolution for Board/Council | Positive checks, matching STR snapshot, immutable approved content and durable publication intent; no synchronous external send |
| ReturnPlanVersion — current governance actor | Open task; actionable reason | Preserve returned evidence, create numbered correction Draft and incompatible-action chain; full resubmission restarts at AO after HOPF signature |
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
| ConfirmForecastCascade — Planner | Active exact schedule/token, proposed rows and inclusion/overrides, reason | Recompute against current actuals and every affected adjacency; one transaction, revision per changed row; no baseline/actual edits; final milestone permitted |
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
| PLN NeedPlanningDispositionChanged.v1 → NDS | event_id, schema_version, producer_sequence, need_id, need_revision_id, dpp_submission_id, disposition, reason when excluded, actor, decision_at | Emit after accepted DPP disposition only; separate from Active usage and Need lifecycle |
| PLN NeedPlanningUsageChanged.v1 → NDS | Existing agreed Active inclusion envelope with exact activated allocation/reversal lineage | Preserve Fully included/Not included semantics; a DPP exclusion cannot clear an existing Active dependency |
| BUD eligible-line resolver | FY, source OU, currency/source context | Exact eligible line identities and authoritative revisions; OU is record eligibility, not user FY authority |
| BUD check_plan_affordability | FY, exact per-line planned Money totals | Non-mutating, non-locking current display statement; approved versus available distinguished |
| BUD validate_plan_affordability_for_decision | Transaction context; FY; per-line totals/currency; expected Budget/line revisions | BUD serializes authoritative basis; returns immutable comparison statement or stale failure; no reservation/ledger write |
| BUD annual procurement budget basis | FY and applicability date/budget revision context | Complete approved annual amount/currency/version including unused lines; no PLN-total denominator |
| STR objective selection and approval snapshot | FY/Plan period, objective ID, reviewed Strategy Version/path, exact Plan Version/item ID and idempotency identity | Current eligible choice for reads; deterministic final-approval snapshot matching reviewed lineage or atomic failure |
| REQ drawdown/reversal and correction response | Exact envelopes in §§4.8/7.2; stable and exact identities distinct | One-open rule per stable item; no automatic stopped-Version resurrection; owner amendment defines fresh Draft follow-up |
| TPR/TPUB invitation actual | Authoritative tender publication event, exact proceeding/REQ/Plan/allocation coverage, actual date and ordered correction fields | Existing invitation path recognized; additional milestone owners must implement their own contract later |
| CFG profile resolver | Rule kind, method/procedure/category, FY and legally applicable date/facts | Immutable selected Version, effective interval, conditions, limits, counting, internal assumptions and legal verification; ambiguity/gaps block |
| Publication adapter | Stable publication identity, exact approved snapshot/manifest, destination; reconciliation by same identity | Exact manifest/hash-bound authoritative acknowledgement, confirmed failure or unknown; no guessed success |

### 7.4 Strategy timing and unchanged event naming

The Draft stores the selected Objective identity and its resolved Strategy version. The submitted Plan stores the exact title/path that governance actors reviewed. At final statutory approval, call STR `create_strategy_snapshot` with the consumer record/version, Objective, expected status and approval correlation. Store its deterministic returned lineage only if it agrees with the reviewed selection and remains eligible. Otherwise fail the positive approval atomically and allow return for correction.

The snapshot call belongs to final Plan approval, not item formation, Finance confirmation, AO adoption or publication retry. It must not append duplicate Strategy snapshot evidence on retry. An Active Plan retains its approved lineage when Strategy later changes. A new or corrected selection must use the current eligible Strategy version; a copied successor must explicitly validate the eligibility rule applicable to every item before new approval.

NDS v1.10 retains `accepted_version_id` and `version_number` in `DepartmentalNeedAccepted.v2`. Planning maps those wire keys to its internal Need-revision fields and shows **Revision** to the user. Do not rename wire keys or generated `-V{nnn}` references merely because the display counter changed.

REQ owns one open Requisition per stable `plan_item_id`, not per department. Planning must use that same rule and the producer's documented drawdown command name. REQ calls `AuthoriseRequisitionDrawdown`; the predecessor lists `RecordRequisitionDrawdown`. The canonical command is AuthoriseRequisitionDrawdown in §7.2; no compatibility alias is retained.

### 7.5 Daily operational checks

CheckApproachingMilestones evaluates every applicable outstanding milestone independently under §5.5. It uses current authorized recipients and one shared evolving notification identity. The default approach window is seven calendar days of operational configuration, not legislation. It never changes Plan state, authorizes procurement or marks an activity complete. Command-time intake closure is enforced independently of the hourly cleanup scheduler.

## 8. Error contract

Return `{code, message, field_errors, affected_record_ids, expected/current token when safe, support_reference}`. Only authorized identifiers/data may appear. Page-load authorization/configuration failures are typed inline states, not stock framework modals. Corrective commands use their own predicates. Profile-specific numeric facts appear as labelled parameters, never universal guessed constants.

| Code | User-facing message |
|---|---|
| PLN_NO_CONTEXT | Procurement Planning is not available for your current responsibilities or configuration. |
| PLN_WINDOW_CLOSED | The initial departmental-plan submission window is closed. |
| PLN_NEED_COVERAGE_INCOMPLETE | Account for every accepted Need within this submission’s coverage before submitting. |
| PLN_ENTRY_INCOMPLETE | Complete the highlighted requirement fields before submitting. |
| PLN_BUDGET_LINE_INELIGIBLE | Select an Active Procurement Budget Line available to this department and financial year. |
| PLN_DPP_STALE | This departmental plan changed; reload and review the current Submission. |
| PLN_CLASSIFICATION_INCOMPLETE | Classify every proceeding requirement before accepting the plan. |
| PLN_SOURCE_UNAVAILABLE | One or more selected requirements are no longer available for item formation. |
| PLN_SOURCE_INCOMPATIBLE | The selected requirements cannot form one Plan Item; create separate items. |
| PLN_SOURCE_CORRECTION_REQUIRED | A departmental source changed; dissolve and re-form the affected Draft item before continuing. |
| PLN_CORRECTION_COHORT_VIOLATION | This correction cannot include an unrelated requirement; use a subsequent plan update. |
| PLN_DISSOLUTION_BLOCKED | This Plan Item is no longer in a mutable Draft and cannot be dissolved. |
| PLN_OBJECTIVE_INELIGIBLE | Select an Active Strategic Objective valid for this Plan. |
| PLN_STRATEGY_REVIEW_CHANGED | The Strategy selection no longer matches the reviewed evidence; return the Plan for correction. |
| PLN_SCHEDULE_INVALID | Correct the highlighted schedule to meet its applicable sequencing and period rules. |
| PLN_PROFILE_PERIOD_INVALID | The highlighted period does not meet the selected procedure’s rules. |
| PLN_DELIVERY_BOUNDARY_INSUFFICIENT | Estimated completion exceeds the required-by date; review the schedule or correct the source through its departmental process. |
| PLN_DELIVERY_PERIOD_REQUIRED | Enter the estimated delivery or implementation period in calendar days. |
| PLN_MULTI_YEAR_UNSUPPORTED | Multi-year procurement is not supported in this release. |
| PLN_FORECAST_REASON_REQUIRED | State why the forecast date is changing before saving. |
| PLN_CASCADE_INCLUDES_ACTUAL_MILESTONE | A milestone with a recorded actual cannot be reforecast. |
| PLN_BASELINE_LOCKED | The submitted baseline cannot be edited; prepare a governed correction or successor. |
| PLN_ACTUAL_NOT_WRITABLE | Actual dates must come from the process that recorded the event. |
| PLN_PLAN_NOT_AFFORDABLE | The planned total exceeds the approved amount on one or more Budget Lines. |
| PLN_FINANCE_STALE | Funding confirmation is no longer current; use the available reassessment or correction action. |
| PLN_REVIEW_STALE | This task has changed; reload before deciding. |
| PLN_SEGREGATION_CONFLICT | You cannot make this decision because you performed an incompatible earlier action. |
| PLN_STATUTORY_ROUTE_UNCONFIGURED | Configure the applicable statutory approval route before submitting this Plan. |
| PLN_COLLECTIVE_RESOLUTION_REQUIRED | Enter the collective resolution reference for this decision. |
| PLN_PLAN_CONTENTS_INCOMPLETE | Complete the highlighted package, structure and evidence fields before continuing. |
| PLN_METHOD_NOT_ADMISSIBLE | The selected method does not meet the applicable procurement conditions. |
| PLN_METHOD_EVIDENCE_REQUIRED | Provide the evidence required for the selected procurement method. |
| PLN_RESERVATION_REQUIRED | Select the planned reservation designation; choose None where no designation applies. |
| PLN_RESERVATION_SHORTFALL | The required reservation allocation is not met; review the displayed shortfall. |
| PLN_REFERENCE_UNAVAILABLE | Required procurement rules or their calculation basis are missing or unverified. |
| PLN_MONEY_PRECISION_INVALID | Enter an amount using the supported currency precision. |
| PLN_ITEM_SCOPE_LOCKED | This Plan Item already has an authorised Requisition. Create a separate Plan Item for the additional requirement. |
| PLN_ITEM_AUTHORISATION_HELD | New Requisition authorisations for this item are on hold while correction requests remain unresolved. |
| PLN_CORRECTION_NOT_ACTIVE | Resolve this request only after the correcting Plan Version is Active. |
| PLN_REMOVAL_BLOCKED | This item has downstream use and cannot be removed through Planning. |
| PLN_ALLOWANCE_EXCEEDED | The requested quantity or value exceeds the remaining original allowance. |
| PLN_TREASURY_EVIDENCE_REQUIRED | Record submission evidence for this exact approved Plan before website publication. |
| PLN_PUBLICATION_FAILED | Publication failed; the approved content is preserved for a safe retry. |
| PLN_PUBLICATION_UNKNOWN | The publication result is unknown and must be reconciled before withdrawal or replacement. |
| PLN_PUBLICATION_HELD | Publication is on hold; review the recorded issue before continuing. |
| PLN_PUBLICATION_ACK_MISMATCH | The publication evidence does not match this approved Plan. |
| PLN_WITHDRAWAL_NOT_PERMITTED | Withdrawal requires confirmed non-publication and no outstanding transmission. |
| PLN_ACTIVATION_HELD | Publication is confirmed, but this Version cannot be activated until the recorded issues are corrected. |
| PLN_LATE_EXPLANATION_REQUIRED | Explain why this initial Plan is being adopted after the financial year began. |
| PLN_STALE_WRITE | Another user changed this record; reload before continuing. |
| PLN_IDEMPOTENCY_CONFLICT | This request reference was already used for different content. |

PLN_RESERVATION_RELEASE_FAILED is removed. Fixed seven-day/thirty-day/fourteen-day timing errors are replaced by PLN_PROFILE_PERIOD_INVALID with the actual resolved rule details. An unknown publication result is never presented as confirmed failure. Unavailable detail records use the same masked Not available response whether absent or unauthorized.

## 9. UI architecture, menus and routes

| Screen | Existing route family / navigation anchor | Principal command entries |
|---|---|---|
| U01 Workspace | /app/procurement-planning | Explicit Start departmental plan or Prepare plan update; navigation otherwise read-only |
| U02/U05 DPP | Existing departmental Plan record route | Draft save, certify/submit, controlled withdrawal/update |
| U03/U04 Requirement | Existing DPP entry route | Save funding details; Add requirement; Draft disposition |
| U06 Validation | /app/procurement-planning/dpp-review/{task_id} | Accept departmental plan; Return to department |
| U07/U08 Plan/formation | /app/annual-procurement-plan/{plan_reference}, exact Version selection | Form items, request Finance, prepare/cancel update |
| U09 Item | /app/procurement-plan-item/{plan_item_id}, exact Version selection | Save Draft; permitted dissolve; navigate to source |
| U10 Finance | /app/procurement-planning/finance/{task_id} | Confirm plan funding; Return to planner |
| U11 Review | Existing Plan record for preparation; /app/procurement-planning/review/{task_id} for governance | Sign and submit; Adopt and submit; Approve; Return |
| U12 Source evidence | Contextual exact-record detail from review | Read-only; Return to Plan review |
| U13 Publication | /app/procurement-planning/publication/{publication_id} | Treasury evidence, safe retry/reconcile, withdrawal request/action |
| U14–16 Execution/correction | Exact Plan/item context and linked correction request | Forecast revision; correction disposition; successor navigation |
| C01–04 Configuration | /app/system-setup and its sections | Existing administrator-authorised configuration commands |

Concrete route parameters and command names must match the final canonical provider/consumer contracts. This table does not authorise duplicate route aliases or new task types. Exact Version selection must survive reload/back, source drilldown and download; the browser must not silently switch a historical review to the latest Version.

### 9.1 Workspace hierarchy

In order: page header and Financial Year filter; Annual Plan section; Your actions (only when actionable); departmental Plan status; pending requirements where relevant. The Plan section remains visible when Your actions is absent. It uses two labelled rows, not a collection of competing metrics cards.

Each row in Your actions comprises an outcome heading, a small labelled fact grid and one button. Unrelated facts must not be concatenated. Waiting work belongs on the relevant Plan/DPP status, not a duplicate disabled task queue.

### 9.2 Plan and review hierarchy

The Plan record has five local sections: **Overview**, **Plan Items**, **Funding and readiness**, **Governance and publication**, **Changes**. These can use existing horizontal tabs; no new sidebar. Version identity stays visible above them. Changes shows No earlier Version on the initial Plan.

U11 uses the same content in a review sequence with a compact section-link row: **Plan Items**, **Sources**, **Funding**, **Method and schedule**, **Reservations**, **Changes**, **Decisions**. These are document anchors, not a seven-step workflow. Summary and all item rows appear before decision controls; complete sections may extend below the viewport. Direct-source detail uses the same read-only source pattern as Need detail with its applicable lineage.

### 9.3 Screen families

| Family | Purpose | Required variants |
|---|---|---|
| U01 | Role-aware workspace | No Plan; initial Draft; Active; Active + candidate; governance waiting/actionable; held publication |
| U02 | DPP content and history | Draft, submitted, accepted + update, returned + correction, intake closed |
| U03 | Need funding/disposition | Incomplete/complete, stale source, not proceeding |
| U04 | Direct requirement | New/edit, invalid fields, immutable submitted view |
| U05 | HoD certification | Complete, excluded Need, correction resubmission, expired acting authority |
| U06 | Procurement validation | Classification, structured return, source-invalid positive decision |
| U07 | Annual Plan overview | Initial/update Draft, funding states, pending sources, historical Version |
| U08 | Formation | One source, multiple separately/combined, incompatible selection, source correction |
| U09 | Item content | Single/combined, method/profile missing, period failure, scope lock, optional fields |
| U10 | Finance | Within approved, low available advisory, approved-amount excess, stale, reassessment/history |
| U11 | Complete review | HOPF, AO, statutory individual/collective, stale basis, return, read-only history |
| U12 | Exact source evidence | Need, direct requirement, reviewed revision versus newer current revision |
| U13 | Publication/recovery | Treasury missing/recorded, pending, failed, unknown, acknowledged, held, withdrawal |
| U14 | Execution and coverage | No proceeding, one proceeding, sequential partial proceedings, incomplete actuals |
| U15 | Forecast revision | Cascade, excluded row/adjacency failure, individual override, final milestone |
| U16 | Correction requests | Multiple open requests, In progress, Resolved, Closed without change, scope lock retained |
| C01 | Entity settings | First run/configured, required route, county flag, invalid configuration |
| C02 | DPP intake | Open/closed, future FY, change closes another year, close instant reached |
| C03 | Funding/reference catalogues | List, missing mandatory record, detail/history, new revision, disabled funding source |
| C04 | Eligibility/schedule profiles | Complete/missing, internal versus statutory defaults, Version history, reminder threshold |
| U21 | Shared page states | Loading, no results, no records, forbidden, masked record, configuration failure, load error |

### 9.4 Shared identity and state fields

| Display concept | Source and display rule |
|---|---|
| Annual Plan reference | Stable Plan reference; separate Version label/value |
| DPP reference | Stable departmental Plan reference; counter shown as Submission |
| Need reference | Stable Need reference plus exact Revision |
| Active Plan | Exact currently governing Version; never inferred from highest Version number |
| Candidate Version | Exact open Draft/governance/publication candidate; show its relationship to Active or correction origin |
| Plan status | Approved lifecycle label; do not use Confirmed as a Plan status |
| Funding status | Not requested, Awaiting confirmation, Confirmed, Returned or Stale, labelled Funding evidence |
| Current eligibility | Separate live result with reason; not an editable badge or an approval claim |
| Amounts | Exact decimal currency-unit values; labelled currency; right-aligned; source quantities and UOM separate |
| Changes | Exact old/new values and source Versions; no unlabelled “updated” badge |
| Historical evidence | Immutable reviewed values; current warnings appear separately, never replace them |

No technical digest, concurrency token or idempotency key is a user field. The publication service must still retain hashes and exact identities. Public names/references must not be constructed by parsing identifier strings.

### 9.5 Full package review coverage

The following is the minimum read-only detail, not a summary substitute. Each applicable field from the final canonical domain contract must also have a named location before implementation.

| Detail section | Required fields and evidence | Location |
|---|---|---|
| Requirement and scope | Title, description, requirement type, procurement category, full quantity, unit, planned value, estimate basis, incidental-cost inclusion statement where applicable | U09/U11 item detail |
| Departmental sources | Department, DPP/Submission, entry origin, exact Need/Revision or direct-source reference, full six source facts, quantity, unit, required-by, line/amount, certification/acceptance evidence | U11 summary and U12 detail |
| Strategy | Objective reference/title and reviewed hierarchy path, exact Strategy Version and snapshot evidence when created | U09/U11 item detail |
| Funding | Budget/Version, line reference/name, funding source, allocation amounts; financial statement and evidence freshness separately | U10 and U11 Funding |
| Method | Selected method/procedure, profile Version, known-fact checks, judgement declarations, required evidence, any separate authorisation with actor and required stage | U09/U11 Method |
| Reservation and structure | Planned designation, mandatory restrictions, applicable county designation, fixed horizon, aggregation indicator/reason, lotting/count | U09/U11 item detail |
| Schedule | Applicable milestones, baseline dates, all input periods and defaults, counting rule, legal constraints versus internal estimates, estimated delivery/implementation period, estimated completion and source boundary | U09/U11 Schedule |
| Operational evidence | Proceeding identity, exact source coverage/quantities/values, original Plan Version, available actuals and comparison basis | U14 |
| Correction and lock | Scope lock since first authorisation; separate unresolved correction hold; request state, reason, owner, affected item and outcome evidence | U09/U14/U16 |

Estimate basis is required review content under RI-054; its entry/storage contract is defined in §4.6, rather than inferred from a generic attachment component. Method evidence is permitted where the agreed method profile requires it; no blanket ban on item evidence may hide that requirement.

### 9.6 Annual Plan visibility and action matrix

The Plan remains reachable regardless of whether the user has work. A new read or navigation action creates nothing.

| Condition | Workspace labels | Authorised action | Other readers |
|---|---|---|---|
| No Version exists | No Annual Plan yet | Departmental actions where permitted; no Create Annual Plan control | Explanation of first accepted DPP creating the Draft |
| Initial Draft | Candidate Version; No Active Plan yet | Continue Plan; request funding when ready; HOPF opens full review | View candidate |
| Active only | Active Plan | Planner: Prepare plan update; current funding reassessment if required | View Active Plan |
| Active plus Draft successor | Active Plan and Candidate Version | Continue update; Cancel update only where allowed | Independently view either |
| Awaiting AO/statutory approval | Candidate Version with exact stage | Open decision for eligible task holder | View submitted Version and waiting owner |
| Returned plus copied Draft | Returned Version link and correction Draft | Continue correction; inspect required changes | View both exact Versions |
| Approved; Treasury evidence absent | Approved — awaiting Treasury submission evidence | AO: Record Treasury submission | View publication status |
| Approved; ready/attempt in progress | Approved — publication pending | System transmission; no business Publish button | View publication status |
| Confirmed transmission failure | Publication failed | System Manager: Retry exact approved payload, if safe to retry | View failure and unchanged approved content |
| Outcome unknown | Publication result unknown | Reconciliation of existing attempt; no blind retry or withdrawal | Explanation of uncertainty |
| Confirmed unpublished with material defect | Publication on hold; approved content retained | AO request; statutory Withdraw for correction | View request/hold |
| Published but activation failed | Published — activation held | Planner: Prepare correction successor, once no other candidate exists | Publication evidence and no new authority from this Version |
| Withdrawn for correction | Withdrawn for correction | Navigate to copied Draft; no edit to withdrawn Version | View approval and withdrawal history |
| Superseded/Cancelled | Exact historical status | None that edits the historical Version | View reviewed evidence and replacement link |

On the Active-plus-candidate view, eligibility refers to Active content, not Draft totals. A held published Version is not listed as Active. With no Active predecessor, say No Active Plan yet; do not fake a baseline to make the layout uniform.

### 9.7 Departmental lifecycle

| Condition | User sees | Action |
|---|---|---|
| No accepted predecessor; initial intake open | No departmental plan yet | Start departmental plan |
| Initial Draft; intake closed | Draft retained; Initial submission closed | Continue editing; submission unavailable with explanation |
| Accepted plus open update | Accepted Submission and update Submission | Continue update, or view accepted evidence |
| Submitted | Certified immutable facts and Awaiting validation | Eligible Planner sees Review submission |
| Returned | Exact reviewed Submission plus copied correction and issues | Correct and resubmit within its source cohort |
| Accepted; intake closed | Accepted; no false “missed window” state | Prepare departmental update for eligible new/changed requirements |
| Need not proceeding | Accepted source facts retained; reason; excluded from funding totals | Restore to planned requirements only in Draft |

Use KT-STD §3/§3A for page behaviour. The following supplies exact domain-specific copy.

| Condition | Heading | Text / action |
|---|---|---|
| Source changed | Source correction required | This requirement has a newer accepted source. Review the change before continuing. Action: View source change |
| Scope locked | Additional requirements need a separate Plan Item | This Plan Item already has an authorised Requisition. Create a separate Plan Item for the additional requirement. Action: View pending requirements; no automatic new item |
| Correction hold | New Requisition authorisations are on hold | An unresolved correction request affects this Plan Item. Existing authorised proceedings are unchanged. Action: View correction requests |
| Missing schedule/method rules | Procurement rules are not configured | The selected method does not have all required eligibility and schedule rules. You can save this Draft. Submission is unavailable. |
| Delivery infeasible | Estimated completion exceeds the required-by date | Show Estimated completion and Required by as separate labelled dates. Action: Review schedule |
| Financial excess | Plan exceeds the approved budget | Show each Budget Line's Planned amount, Approved amount and Excess. Return remains available |
| Low available balance only | Current availability is below the planned amount | The Plan is within the approved amount. Confirmation does not reserve funds. |
| Mandatory allocation shortfall | Required reservation allocation is not met | Show Required allocation, Planned qualifying allocation, Shortfall and Budget basis. Action: Review reservation allocations |
| Stale positive-decision basis | Review basis has changed | Refresh the current checks before deciding. The submitted content remains unchanged. Return for correction remains available where authorised |
| Publication unknown | Publication result is unknown | The destination may have received this Version. Its result must be reconciled before withdrawal or replacement. |
| Published held | Published Plan cannot be activated | Publication is confirmed, but activation checks failed. This Version cannot authorise new Requisitions. Action: Review activation issues |
| Missing actual | Scheduled date passed — actual not recorded | Show scheduled date and proceeding separately; do not state the activity did not occur |
| Unsupported actual tracking | Actual tracking not yet available | Show as a status, never a zero-duration result |
| Late initial activation | Late activation explanation required | The initial Plan became Active after the financial year began. Action for AO: Record late activation explanation |

### 9.8 Proof-of-concept acceptance and production interpretation

The product owner accepted the focused workspace → AO review → exact source evidence flow, with simulated adoption/return and independent Active/draft navigation: https://kentender-planning-review.rbnganyi.chatgpt.site . This establishes UX direction, not production technology or backend behavior. Production uses existing Frappe/Vue components and KT-STD-001. Do not copy the demonstration’s React stack, client-only decisions, scenario/role harness, fixed FY, incomplete export behavior or simplified history as product requirements.

Retain the useful interaction pattern: persistent Active and candidate access, readable complete review, expandable detail, exact source drilldown, return-context/focus restoration, clear decision consequence and reasoned correction. Full labels and distinct facts follow KT-STD even where the prototype compresses them. The optional proof-of-concept empty Your actions panel does not replace the required production rule to omit that section when nothing is actionable. Every governed source and both return destinations remain available.

Only the focused flow was rendered and walked through. The remaining artboard/state variants below are specifications requiring implementation visual verification. No production release, user-study outcome, complete accessibility pass or exact 1440 × 1024 sign-off is implied.

## 10. Static design contract — visual input only

Supply KT-STD-001 §2 plus this section only to the design tool. This section includes the necessary fixture values; other sections contain runtime rules and must not be pasted into the visual prompt. Artboard context is outside the image. Use the existing visual system; no substitute palette, logo, application shell or custom sidebar.

Each full page is 1440 × 1024 with the standard 1200 px content column. Use normal vertical overflow: provide additional artboards for lower sections in the order specified. Do not reduce type or truncate evidence to fit. Ordinary confirmation/input dialogs use the standard 520 px width. The multi-row forecast review is a full page within Plan context. That replaces the baseline's 640 px dialog exception.

### 10.1 Closed fixture pack

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
| Annual procurement budget | KES 160,000,000 |
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

BASE reservation panel: Target **30%**; Required allocation **KES 48,000,000**; Planned qualifying allocation **KES 0**; Shortfall **KES 48,000,000**; Budget basis **MOH-BUD-2027-001, Version 1** in separate reference/Version fields; result **Required allocation not met**. Both package designations None. READY changes laptop planned designation to **Youth**, qualifying allocation to **KES 50,000,000**, shortfall to **KES 0**, share of annual budget to **31.25%** and result to **Required allocation met**. County requirement: **Not applicable**. Mandatory restrictions: **No additional restriction applies**. Do not display the annual-budget percentage as a percentage of Plan value.

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

### 10.2 U01 — Workspace: render first

Context outside artboard: Mercy Kilonzo, Procurement Planner; 3 Dec 2026, 09:00 EAT; BASE Draft; Home > Procurement Planning.

Header: eyebrow **PROCUREMENT PLANNING**; title **Annual procurement planning**; description **Prepare departmental requirements, review the Annual Plan and follow its approval.** Below: inline **Financial Year** select **FY 2027/28**. No PE or role selector.

Section **Annual Plan**. First line: **No Active Plan yet**. Text: **Version 1 is being prepared. It does not authorise procurement.** Below, one candidate row with labelled values: **Version: 1**, **Status: Draft**, **Funding evidence: Not requested**, **Plan Items: 2**, **Planned value: KES 130,000,000**. Reference **PLN-MOH-2027-001** on its own labelled line. Right action **Continue Plan**.

Section **Your actions**: heading **Complete Plan readiness**; labelled facts **Version: 1**, **Blocking issue: Required reservation allocation not met**, **Shortfall: KES 48,000,000**. Action **Review readiness**.

Section **Departmental plans** with columns **Department**, **Accepted Submission**, **Open Submission**, **Requirements**, **Value**, **Status**, **Action**. DHI: 1, None, 2, KES 110,000,000, Accepted, View. HRMD: 1, None, 1, KES 20,000,000, Accepted, View. The two long department names wrap. No generic late-submission warning.

**U01-B Active plus candidate:** outside context 11 Dec 2026, 09:00 EAT, UPDATE based on READY. Active row: Version 1, Active, Funding evidence Confirmed, Plan Items 2, Approved value KES 130,000,000; action **View Active Plan**. Candidate row: Version 2, Draft update, Funding evidence Confirmed, Plan Items 2, Planned value KES 130,000,000; action **Continue update**. Text **The Active Plan remains in force while Version 2 is reviewed.** Your actions heading **Continue Plan update** with Changed field **Procurement description**, Affected item **National digital health infrastructure upgrade**; action **Review changes**. Departments unchanged. This narrative-only update has unchanged financial basis; it demonstrates separation of current funding from substantive Plan governance.

**U01-C no work:** U01-B with no candidate and no Your actions section. Active row remains, with **Prepare plan update** for Mercy. **U01-D no Plan:** outside context Mercy, 27 Nov 2026, 13:55 EAT; replace Annual Plan content with heading **No Annual Plan yet for FY 2027/28**, text **The Draft Annual Plan is created when the first departmental plan is accepted.** No create action. Department table has DHI Submission 1 Awaiting validation and HRMD Submission 1 Awaiting validation; separate work row **Validate Digital Health departmental plan**, Submitted by Julia Njeri, Submitted 25 Nov 2026, 10:30 EAT, Requirements 2, Value KES 110,000,000, action **Review submission**.

**U01-E departmental user:** Grace, 25 Nov 2026, 10:05 EAT, DHI Draft example. Work row **Complete Digital Health departmental plan**, Submission 1, Requirements 2, Specified value KES 30,000,000, action **Continue**. No other department's protected values or Plan approval action. **U01-F governance user:** Amina, READY Awaiting Accounting Officer, 8 Dec 2026, 09:55 EAT. Work row **Review Annual Plan for adoption**, Version 1, Plan Items 2, Value KES 130,000,000, Submitted by Charles Mutiso, Submitted 7 Dec 2026, 10:00 EAT, action **Open decision**. Candidate remains visible; no Active Plan row falsely marked active.

### 10.3 U07 — Annual Plan overview and sections

Context: Mercy, BASE, 3 Dec 2026, 09:05 EAT. Header eyebrow **ANNUAL PROCUREMENT PLAN**, shared title, separate Reference and Version fields, Draft badge. Local tabs in order **Overview**, **Plan Items**, **Funding and readiness**, **Governance and publication**, **Changes**. Select Overview.

Overview summary: Plan Items 2; Departmental sources 3; Departments 2; Planned value KES 130,000,000; Funding evidence Not requested. Panel **Before submission**: Required reservation allocation not met; KES 48,000,000 shortfall. Button **Review readiness**. Panel **Preparation**: Project name empty optional input; label **Project name (if applicable)**, helper **Leave blank when this Plan covers several projects or a general portfolio.** Footer **Back to workspace**, **Save draft**. Finance action **Request plan funding confirmation** appears in Funding and readiness where the financial-review prerequisites pass; final **Sign and submit Annual Plan** appears only on Charles's review variant.

**Plan Items tab artboard:** columns **Plan Item**, **Category**, **Quantity**, **Unit**, **Planned value**, **Required by**, **Readiness**, **Action**; both shared item rows, readiness **Review required**, action **Edit**. References below titles only as genuine identity context. Below: **Accepted requirements not yet allocated**; BASE formed example has **No unallocated requirements**, text **All three accepted requirements are represented in the two Plan Items.** No empty formation button.

**Unallocated variant:** before formation, summary 0 items/KES 0, 3 unallocated requirements/KES 130m; source list uses shared three source rows with checkbox, Requirement, Department, Quantity, Unit, Amount. Primary **Form Plan Items**. **Pending correction-cohort variant:** separate section **Pending for a later update**, text **These requirements cannot be added to this correction Version.** Do not blend those rows into the selectable source list.

**Funding and readiness tab:** show full Budget table from §10.1; affordability outcome **Within approved amounts**; reservation BASE panel; **Method and schedule checks: Production configuration not verified** as a blocked configuration example, not a green pass. This BASE screen is deliberately not a submission-ready fixture. **Changes tab initial:** heading **No earlier Version**, text **This is the first Version of the Annual Plan.** UPDATE variant shows field Procurement description, old shared description, new **Procure and implement the national digital health infrastructure upgrade across the priority facilities identified in the departmental requirement.** Source set, quantities and value: **Unchanged**.

### 10.4 U11 — Complete governance review: render second

Produce four viewport artboards for the same read-only review: **summary**, **expanded item and sources**, **funding/method/schedule/reservations**, **changes/decisions**. Keep the exact Plan Version in the header of each. Use READY outside-artboard fixture context so the positive-decision layout can be reviewed without asserting production legal verification.

Header: eyebrow **ACCOUNTING OFFICER ADOPTION**; shared Plan title; Reference PLN-MOH-2027-001; Version 1; status **Awaiting Accounting Officer**. Header secondary action **Download review pack**. Summary labelled values: **Plan Items 2**, **Sources 3**, **Departments 2**, **Planned value KES 130,000,000**, **Funding evidence Confirmed**, **Readiness No blocking issues**. Fixture provenance remains outside the artboard; production screens show the actual computed readiness result.

Section-link row: **Plan Items**, **Sources**, **Funding**, **Method and schedule**, **Reservations**, **Changes**, **Decisions**. No numbered stepper.

**Summary viewport:** Plan Items table columns **Plan Item**, **Category**, **Quantity**, **Unit**, **Value**, **Required by**, **Detail**; shared two items, detail **View full details**. Source summary below lists all three source names, department, quantity, unit, amount and **View source evidence**. Separate readiness facts **Funding: Within approved amounts**, **Reserved allocation: KES 50,000,000 against KES 48,000,000 required**, **Method and schedule: Complete**. These are labelled facts, not one concatenated sentence.

**Expanded item viewport:** laptop heading and read-only labelled fields for full package description, Goods requirement type/category, 250 Each, KES 50m, Single year, Objective reference/title/path and Strategy Version. Structure fields: Aggregated, shared aggregation reason, Single lot; Planned designation Youth; Mandatory restrictions text from fixture. Estimate basis text/reference from fixture. Two source rows include their exact Needs/Revisions, DPPs/Submission 1, departments, quantities/units, required-by, line and amounts. Buttons **View source evidence**. No ellipsis hiding the description or hierarchy.

**Funding/method/schedule viewport:** both complete Budget rows, Statement as at **4 Dec 2026, 10:00 EAT**, Confirmed by **Josphat Mwangi**. Separate full reservation panel READY. Method **Open Tender**; Procedure profile **Open Tender — goods**; Profile Version **1**; Conditions **Complete**; Evidence **Method eligibility record**; required specific authorisation **Not required**. Schedule shows both baseline dates and source boundary for the selected laptop item, then all five period inputs as read-only values, estimated period 60 calendar days and estimated completion 24 Sep 2027. Internal buffers have Planning assumption labels; no invented legal citation. The production screen will display exact verified profile evidence instead of the example wording.

**Changes/decisions viewport:** initial Changes **No earlier Version**. Decisions table columns **Stage**, **Actor**, **Capacity**, **Decision**, **Date**: Finance/Josphat Mwangi/Finance Confirmation Officer/Confirmed/4 Dec 2026 10:00; Preparation/Charles Mutiso/Head of Procurement Function/Signed and submitted/7 Dec 2026 10:00. Current-stage panel: **Accounting Officer adoption**, **Amina Hassan**, **Awaiting decision**. No future statutory outcome. Decision statement: **I adopt the complete consolidated Annual Procurement Plan Version 1 and submit it for the configured statutory approval.** Footer secondary **Return for correction**, primary **Adopt and submit**. The footer must not obscure the final content rows.

**HOPF variant:** context Charles, 7 Dec 2026 09:55; eyebrow **PLAN PREPARATION SIGNATURE**; Plan status Draft; Funding Confirmed; no Preparation decision row yet. Statement **I confirm that the complete Annual Procurement Plan Version 1 is ready for Accounting Officer adoption.** Primary **Sign and submit Annual Plan**; secondary **Back to Annual Plan**. Do not add a Head-of-Function approval badge or task stage.

**Statutory variant:** Daniel, 9 Dec 2026 10:55; eyebrow **STATUTORY APPROVAL**; status Awaiting statutory approval; Capacity **Cabinet Secretary**; append Amina's adoption evidence. Primary **Approve Annual Procurement Plan**; secondary **Return for correction**. **Collective authority variant:** outside-artboard scenario explicitly configured Council; display Governing body **Council**, Required capacity **Authorised Council decision recorder**, **Resolution reference** required input **COUNCIL/APP/2027/01**; actor Daniel as UI-role variant only. Do not imply his default Cabinet Secretary assignment can act as Council.

**Stale basis variant:** retained submitted content; notice **Review basis has changed**, text **The current Budget basis no longer matches the funding confirmation. The submitted content remains unchanged.** Separate Funding evidence at submission **Confirmed**, Current funding evidence **Stale**. Positive action unavailable; Return for correction available to eligible decision actor. Do not replace the historical statement with new amounts.

**Return dialog:** title **Return Plan Version for correction?**; text **The reviewed Version remains unchanged. A copied Draft will be prepared for correction and will repeat the required governance.** Required **Correction required**, value **Review the funding allocation against the revised approved Budget Line amount.** Buttons Cancel / Return for correction. No category, assignee or optional notes.

### 10.5 U12 — Source evidence within review

Render as a full content detail view with parent Plan reference/Version and **Return to Plan review** at top and bottom. Header **Source evidence**. Selected source **Clinical training laptops for digital health rollout**. Display all six facts from §10.1, then separate Reference **NDS-MOH-2027-0003**, Revision **2**, Department **Human Resources Management and Development**, Departmental Plan **DPP-MOH-HRMD-2027-001**, Submission **1**, DPP entry **DPPE-MOH-HRMD-2027-001**, Budget Line **MOH-BL-HWD-2027**, Planning amount **KES 20,000,000**. Evidence: Need accepted by Peter, **25 Nov 2026, 10:00 EAT**; certified by Peter **25 Nov 2026, 11:00 EAT**; accepted for Planning by Mercy **27 Nov 2026, 14:05 EAT**.

Newer-current-revision variant: top neutral notice **You are viewing the source revision used in this Plan. A newer accepted revision exists.** Links **View newer accepted revision** and **Return to reviewed revision**; preserve the original six facts. Direct-source variant replaces Need reference/revision with **Source origin: Direct departmental requirement** and exact DPP-entry evidence, without an empty Need field or bypass reason.

### 10.6 U02–U06 — Departmental preparation, certification and validation

**U02 Draft:** Grace, DHI, 25 Nov 2026 10:05 EAT. Eyebrow **DEPARTMENTAL PROCUREMENT PLAN**, title **Digital Health departmental plan**, reference DPP-MOH-DHI-2027-001, Submission 1, status Draft. Context fields Department Digital Health; Financial Year FY 2027/28; Initial submission Open until 30 Nov 2026, 23:59 EAT. Header actions **View accepted needs**, **Add direct requirement**. Requirements rows: infrastructure 1 Programme, 31 Aug 2027, line Not selected, amount Not specified, status Funding incomplete, action Complete; deployment laptops 150 Each, 31 Dec 2027, line MOH-BL-HWD-2027, amount KES 30,000,000, status Ready, action View. Source references on separately labelled lines. Below, Requirements 2 and Specified value KES 30,000,000. Notice **1 requirement needs funding details**. Footer **Back to workspace**, **Save draft**. Grace has no certification button.

**U02 accepted plus update:** accepted Submission 1 and Draft Submission 2 in separate rows; accepted counts 2/KES 110m. Status **Accepted — update in progress**. Actions **View accepted Submission**, **Continue update**. Intake Closed; no “missed window” status. **Returned variant:** heading **Correction required**, issue **Confirm the deployment laptop amount against the accepted departmental requirement.** Links **View returned Submission 1**, **Continue correction — Submission 2**. No editable controls on returned Submission 1.

**U03 Need funding:** title **Complete funding details**; six infrastructure facts and exact Need Revision from §10.1, all read-only. Fields Procurement Budget Line select **MOH-BL-DHI-2027**, Line name **Digital health infrastructure programme**, Indicative amount input **80,000,000**, Currency read-only **KES**. Footer Cancel / Save funding details. Secondary action **Do not proceed this financial year**. Its dialog: heading **Do not proceed this financial year?**, required **Reason for not proceeding**, value **The department will pursue this requirement in a later annual planning cycle.** Buttons Cancel / Do not proceed. Resulting Draft row status **Not proceeding this financial year**, full Need facts/quantity preserved, funding Not required, reason displayed; action **Restore to planned requirements**. Restoration variant has line/amount Not selected/Not specified, not silently restored old funding. Not-proceeding entries are in a distinct section of U02/U05/U06 and excluded from financial totals.

**U04 Direct requirement:** isolated UI fixture, not loaded into BASE. Title **Add direct requirement**. Read-only Department Digital Health; Financial Year FY 2027/28. Fields: Title **Digital health platform security assessment**; Description **Assess the security of the national digital health platform and provide a prioritised remediation report.**; Expected operational result **The Ministry receives a prioritised and actionable security remediation plan.**; Quantity **1**; Unit **Programme**; Required by **31 Oct 2027**; Procurement Budget Line **MOH-BL-DHI-2027**; Indicative amount **20,000,000**; Currency KES read-only. Programme describes this packaged assessment deliverable; it replaces the undefined Service UOM for this UI fixture. Footer Cancel / Add requirement. Edit variant Save requirement / Remove direct requirement, only in Draft. No Need link, bypass reason, Strategy or method fields.

**U05 Certification:** Julia, 25 Nov 2026 10:25 EAT, DHI completed BASE submission. Same requirements as U02, infrastructure now fully funded; total KES 110m. Heading **Departmental certification**. Text **I certify that this Submission records Digital Health's current procurement requirements for FY 2027/28, including the accepted Needs and direct requirements shown. I confirm the proceeding requirements' quantities, required-by dates and funding details, and the recorded reasons for any Needs not proceeding.** Checkbox **I confirm this certification**. Footer Back / Submit departmental plan. Exclusion variant shows deployment laptops not proceeding, value total KES 80m and the exact reason above. Correction variant context Submission 2, closed intake, heading **Certify corrected Submission**, text **I certify the corrected requirements and dispositions within the returned Submission's source scope.** Checkbox same; footer **Resubmit departmental plan**. No newly accepted unrelated source in the correction's certified table.

**U06 Validation:** Mercy, 27 Nov 2026 13:55 EAT. Title **Validate Digital Health departmental plan**; reference and Submission separate; status Awaiting validation. Certified by Julia, Certified 25 Nov 2026 10:30 EAT; Requirements 2; Value KES 110m. Read-only full submitted source/funding detail, with only **Requirement type** classification selects: infrastructure Non-consulting services, deployment Goods. Each row has View source evidence. Certification text from U05. Footer Return to department / Accept departmental plan. Not-proceeding variant has no classification input or funding requirement for the excluded row.

**DPP return dialog:** title **Return departmental plan for correction?**; fields **Affected requirement** select deployment laptop title, **Issue** value **The indicative amount needs correction.**, **Correction required** value **Confirm and update the deployment laptop amount.** Buttons Cancel / Return to department. **Expired acting authority variant:** inline command notice **Your authority to submit this departmental plan has changed. Refresh to see the actions currently available.** Preserve read access only if still authorised. Do not reassign the decision or offer a bypass.

### 10.7 U08/U09 — Formation and package editing

**U08 multi-source formation:** within Annual Plan content, title **Form Plan Items**; two selected laptop source rows from §10.1, with department, quantity, unit, line and amount in separate columns. Choices **Create one Plan Item for each selected requirement**, **Create one combined Plan Item**; combined selected. Preview labelled fields Selected requirements 2, Plan Items to create 1, Quantity 250, Unit Each, Value KES 50,000,000. Field **Aggregation reason** contains the shared reason. Footer Cancel / Create Plan Item. Single-source variant has no formation-choice radio group and directly creates one item from the chosen source. Incompatible variant message **These requirements cannot be combined because their Procurement Budget Lines differ.** Combined choice unavailable; one-each remains available if individually valid. No partial quantity/value input.

**U09 editor:** header **PLAN ITEM**, laptop title/reference, Draft Version 1. Section order **Requirement and sources**, **Package details**, **Method and eligibility**, **Reservation and structure**, **Baseline schedule**. Two sources visible with full details available via View source evidence. Package title and description use §10.1; Strategic Objective select with separate hierarchy and Version read-only; Aggregation reason required. Quantity 250, Each, KES 50m and funding allocations read-only. Project name is Plan-level, not duplicated here.

Method select Open Tender; Procedure profile Open Tender — goods; Profile Version 1. CONFIG variant notice **Procurement rules are not configured** with text from §8. A separate positive-layout fixture shows **Eligibility conditions** with rows **Category: Goods**, **Value: KES 50,000,000**, **Evidence: Complete**. Do not invent universal checkboxes for every method. Evidence controls appear only in an explicitly supplied condition-specific variant. Required declaration example label **Circumstances supporting the selected method** and value **Method eligibility record** is confined to a conditional-method UI variant, not shown for default Open Tender.

Structure: Planned reservation select None for BASE, Youth for READY; Mandatory restrictions read-only example text; Plan horizon Single year read-only; Aggregation Aggregated; Lotting Single lot. Packaged into lots variant adds Lot count **2**, not lot specifications or partial source allocation. No highest-advantage ranking or override reason.

Schedule: Target invitation date 15 May 2027; computed laptop table; Estimated delivery or implementation period **60**, unit **Calendar days**; Estimated completion **24 Sep 2027**; Required by **31 Dec 2027**; outcome **Within the required-by date**. Disclosure **Adjust periods** collapsed by default; expanded artboard uses five periods from §10.1 with planning-assumption labels on buffers. Feasibility failure variant period **160**, completion **2 Jan 2028**, required-by unchanged; exact heading **Estimated completion exceeds the required-by date**. Footer Back to Annual Plan / Dissolve Plan Item / Save draft. Submission happens at Plan level.

**Locked-item variant:** Active-derived item with first authorised Requisition **REQ-MOH-2027-033-001**, date **15 Mar 2027**. Panel **Procurement scope locked**; text **This Plan Item already has an authorised Requisition. Create a separate Plan Item for the additional requirement.** Show exact original sources/allowance; no add-source, increase-quantity or dissolve-to-reset control. Link **View procurement proceedings**. A permitted narrative correction must still preserve scope and follow the agreed governance; the UI cannot decide that by merely allowing free text.

### 10.8 U10 — Finance confirmation and history

Context Josphat, 4 Dec 2026 09:58 EAT; title **Confirm Plan funding**; Plan reference/Version 1, Plan status Draft, Funding evidence Awaiting confirmation. Summary Plan Items 2, Planned value KES 130m, Budget Lines 2. Table columns **Budget Line**, **Funding source**, **Approved amount**, **Planned amount**, **Within approved amount**, **Currently available**. Use shared two rows, both Yes. Each line has **View allocations**, which opens its Plan Items and exact source amounts read-only. Below **Statement as at: 4 Dec 2026, 09:58 EAT**; notice **The Plan is within the approved amount on every Budget Line.** Quiet text **Confirmation records affordability. It reserves no funds.** Footer Return to planner / Confirm plan funding.

Finance does not display a green “Plan compliant” badge from its own result. BASE may have reservation readiness unresolved independently; show **Other Plan readiness checks are reviewed before submission**, with View Plan readiness link, rather than putting the 30% target inside the financial verdict.

Low-availability variant: DHI available **KES 10m** with other downstream financial records explaining that current position; approved stays100m, planned80m, Yes. Message from §8; Confirm remains available. Excess variant DHI approved **KES 70m**, planned80m, Excess **KES 10m**, result No; Confirm unavailable; Return available. These are independent financial scenarios, not mutations of the shared BASE Budget.

History viewport: **Funding evidence at approval** and **Current funding confirmation** separate panels. History table Review, Basis, Outcome, Actor, Time. Example Review1 Confirmed/Josphat/4 Dec; Review2 Awaiting confirmation/current revised Budget basis/no decision. Do not display Review2 as overwriting Review1. Active reassessment title **Reassess funding for Active Plan Version 1**, Plan content read-only and no reapproval button. Finance return dialog required **Correction required**, value **Reduce the planned amount or obtain an approved Budget revision for the Digital Health line.**

### 10.9 U13 — Publication, Treasury evidence and recovery

Header **PLAN PUBLICATION**, shared title/reference/Version1, status as variant below. Sections **Approved document**, **Treasury submission**, **Website publication**, **Activation**. Approved document offers **View approved Plan**, **Download approved Plan**, **Download Plan data**. No editable destination, payload, hash, manual acknowledgement or business Publish button. Status/facts remain visible when a user has no action.

| Artboard variant | Exact prominent content | Action shown for context actor |
|---|---|---|
| U13-A Treasury missing | Approved — awaiting Treasury submission evidence; Website publication Not attempted; Activation Not active | Amina: Record Treasury submission |
| U13-B evidence recorded | Treasury submission recorded; Submitted 10 Dec 2026, 14:00 EAT; Recorded by Amina Hassan; Channel Official correspondence; Destination National Treasury; Dispatch reference MOH/APP/2027/001 | View submission evidence |
| U13-C in progress | Approved — publication pending; Last attempt 10 Dec 2026, 14:55 EAT; Result Awaiting acknowledgement | No retry while attempt outstanding |
| U13-D confirmed failure | Publication failed; Result Confirmed not received; Approved document Unchanged | System Manager: Retry exact approved payload |
| U13-E unknown | Publication result is unknown; The destination may have received this Version. Its result must be reconciled before withdrawal or replacement. | System Manager: Check publication result, read/reconcile operation only |
| U13-F success | Website publication Acknowledged; Acknowledged 10 Dec 2026, 15:00 EAT; Activation Active; Treasury submission Recorded | View published Plan; View Active Plan |
| U13-G published held | Published — activation held; Website publication Acknowledged; Activation issue Current funding evidence is stale; This Version cannot authorise new Requisitions | Mercy: Prepare correction successor |
| U13-H unpublished defect | Publication on hold; Website publication Confirmed unpublished; Reason Funding basis changed; Withdrawal request Not recorded | Amina: Request withdrawal for correction |
| U13-I withdrawal requested | Confirmed unpublished; Requested by Amina Hassan; Reason Funding basis changed; Awaiting Cabinet Secretary decision | Daniel: Withdraw for correction |
| U13-J withdrawn | Withdrawn for correction; Original approval retained; Correction Draft Version 2 | View approved Version 1; Open correction Version 2 |

Each artifact's URI, acknowledgement reference and attachment metadata in a production screen come from authoritative records. For the static success artboard use acknowledgement **ACK-MOH-2027-001-A1** and link label only **View published Plan**; do not invent a live public URL.

**Treasury form:** title **Record Treasury submission**; read-only Plan/Version and approved document; required Submitted at **10 Dec 2026, 14:00 EAT**, Channel **Official correspondence**, Destination **National Treasury**, Dispatch/reference number **MOH/APP/2027/001**, attachment display **Treasury-dispatch-evidence-example.pdf**. Required checkbox **I confirm that the approved Plan Version shown here is the document submitted.** Footer Cancel / Record submission. Attachment name is an explicit static fixture, not a claim the file exists. Evidence correction variant title **Correct Treasury submission evidence**, required Reason **Correct the dispatch reference.**, prior record retained in read-only panel.

**Withdrawal request dialog:** required Reason **The approved funding basis changed before publication.**, context Confirmed unpublished, buttons Cancel / Request withdrawal. **Withdrawal decision dialog:** text **The approved Version and its signatures will remain in history. A copied Draft will repeat the required governance.** Required reason from request visible, decision reason field **Return this unpublished Version for correction of the funding basis.** Buttons Cancel / Withdraw for correction. No equivalent control in unknown/published variants.

### 10.10 U14/U15/U16 — Active execution, forecasts and correction

**U14 Active overview:** READY-derived visual scenario, 10 Dec 2026 15:05 EAT. Active Version1, Approved value130m, Plan Items2, Departments2, Funding Confirmed. Both package rows. Separate columns **Remaining quantity**, **Unit**, **Remaining value**, **New Requisition eligibility**, **Detail**. Infrastructure1/Programme/80m, laptops250/Each/50m, eligibility **Available subject to current checks**. Show **Prepare plan update** to Mercy. No Create Requisition/Tender.

**Execution variant:** outside artboard 1 Sep 2027, independent UI fixture. Laptop original allowance250 Each/50m; authorised proceedings cover100 Each/20m and150 Each/30m. Proceeding references **UI-PROC-A** and **UI-PROC-B**, explicitly supplied UI-only identities. A invitation actual1 May2027, B1 Sep2027. Each row has proceeding reference, source-coverage link, original Plan Version1, authorised quantity, unit, authorised value, stage **Tender published**. Remaining undrawn quantity0/value0. Full item fulfilment **Completion tracking not yet available**. Do not render one Plan Item invitation actual or infer delivery. An alternate partial state with only A has remaining150 Each/30m. These examples illustrate the agreed model and are not the existing full-250 Requisition fixture.

Selected proceeding A source coverage: HRMD source NDS-0003 Revision2,100 Each/20m. B: DHI source NDS-0004 Revision1,150 Each/30m. Source full quantity remains unchanged; these proceedings select existing original allocations, not a new residual Need. Actuals table columns **Milestone**, **Baseline**, **Forecast used**, **Actual**, **Baseline lateness (days)**, **Forecast error (days)**. Unavailable later actuals show **Actual tracking not yet available**. Separate stage-duration table **Stage**, **Planned elapsed days**, **Actual elapsed days**, **Duration variance (days)**; no numeric result without both endpoints.

**U15 forecast page:** title **Revise forecast**, context Infrastructure item, Active Version1, selected milestone Bid opening. Field New forecast date **5 Jun 2027**. Table Include, Milestone, Current forecast, Proposed forecast. Rows: Bid opening22May→5Jun; Evaluation21Jun→5Jul; Award26Jun→10Jul; Notification28Jun→12Jul; Signing12Jul→26Jul; Completion31Aug→14Sep. All included; proposed dates editable. Required Reason **Tender preparation confirmed a two-week delay in issuing the invitation.** Footer Cancel / Confirm forecast revision. Read-only Baseline completion31Aug; forecast completion14Sep; **Forecast is later than the approved completion boundary**. No baseline edit.

Excluded-adjacency failure variant: Notification kept28Jun while Signing moved26Jul and a verified scenario rule flags the resulting gap; display **The proposed dates do not meet the selected schedule profile. Review the highlighted interval.** The fixture does not assert a new universal legal maximum. Final-milestone variant has one row Completion31Aug→14Sep, Reason **Implementation is forecast to finish two weeks later.**, same Confirm action, no false no-action state. Already-actual milestones are absent from editable rows.

**U16 correction requests:** title **Plan Item correction requests**, laptop context. Separate status panels **Procurement scope: Locked since first authorisation** and **New Requisition authorisations: On hold**. Table Request, Origin, State, Reason, Outcome. UI-only requests **UI-COR-01**, origin Requisition review, Open, **Confirm the funding allocation.**; **UI-COR-02**, origin Requisition review, In progress, **Correct the source description without enlarging the procurement scope.**. Actions per row View request; eligible work action **Prepare Plan correction** or **Open correction Version**. Detail includes requesting Requisition/Version, source and received time in production; static incomplete metadata is shown as **Not recorded in this UI example**, not fabricated real evidence.

Resolved variant: UI-COR-01 Resolved, Corrected Active Version2; UI-COR-02 still In progress; hold remains. Close without change dialog required Reason **The reviewed source allocation is correct; no Plan change is required.** Complete closure does not clear the separate scope lock or auto-restart a stopped Requisition. A stopped Requisition is linked read-only through the existing downstream restart contract.

**Additional Need variant:** explicit UI-only Need **UI-NEED-ADDITIONAL-01**, title **Additional deployment laptops**, Department Digital Health, quantity50 Each, valueKES10m, requiredby31Dec2027, accepted into DPP update. Panel **Pending requirement**; Planning coverage **Not yet in an Active Plan**; Procurement coverage **No proceeding recorded**; Fulfilment **No evidence recorded**. Attempt to add to original locked item shows exact scope-lock message. Action **View pending requirements**, then ordinary formation into a distinct item. Never show the original Tender as covering these50.

### 10.11 C01–C04 — Affected System setup artboards

Context Administrator; shared System setup shell and existing four tabs retained. Add a fifth local tab **Procurement settings**, specified here to house the agreed catalogue/profile maintenance. This is a presentation addition, not a new governance module. Default tab remains the first incomplete required configuration. No Save for approval or configuration Draft badge.

**C01 first run:** fields Entity code PE-MOH; Entity name Ministry of Health; Entity type National Government Ministry; PPRA registration PPRA/PE/2019/0114; Timezone Africa/Nairobi; **Statutory approval route** select Cabinet Secretary; **County entity** unchecked. Help **Select the authority that approves this entity's Annual Procurement Plan.** Footer Configure site. Configured variant Entity code read-only; footer Save changes. Route options exactly Cabinet Secretary, County Executive Committee Member, Board of Directors, Council. No None. A conflict variant type County Government with County entity unchecked shows **County applicability does not match the entity details. Review the configuration.** Final permitted mapping depends on verified applicability rules; do not silently derive jurisdiction from a label.

**C02 Fiscal years:** separate columns Financial year, Period, Phase, Needs intake, Departmental-plan intake, Actions. FY2026/27 Current: Needs Closed, DPP Closed. FY2027/28 Upcoming: Needs Open until25Nov2026 23:59, DPP Open until30Nov2026 23:59. Use **Manage departmental-plan intake** action to a focused dialog; do not force every module's unrelated fields into a row menu. Dialog Open departmental-plan intake; Financial year read-only FY2027/28; Close automatically on30Nov2026 23:59; Reason **Annual departmental procurement planning call.** Replacement notice names another year only in explicit variant. Buttons Cancel/Open departmental-plan intake. Close dialog reason **The announced departmental submission period has ended.** Text **Existing submissions and governed updates remain available under their Planning rules.** No Plan creation button.

**C03 Procurement settings:** section links Funding sources; Procurement rules; Schedule profiles; Reminders. Funding sources table Name, Enabled, Action: Government of Kenya/Yes/Edit; Development partner/Yes/Edit; Appropriation in Aid/Yes/Edit. Button Add funding source. Editor Funding source name, Enabled; Save changes. No unrelated justification or approval fields.

Procurement rules list columns Reference set, Applies from, Applies until, Version, Source verification, Action. CONFIG rows **Method eligibility**,1Jul2027,30Jun2028,1,Production verification pending,View; **Reservation rules**,same dates/version/status,View. Button Add reference version. Detail labels Reference set, Version, Applicability basis, Effective from/until, Source instrument, Provision, Source document, Verification status, Rule values. CONFIG verification shows pending; Source instrument **Public Procurement and Asset Disposal Regulations — source verification pending**, Provision **Verification required**, Source document **Not attached**. No UI toggle asserting legal verification without the defined owner/evidence contract. A referenced Version is read-only with **Create new version**, not an edit-in-place form.

**C04 Schedule profile:** title **Schedule profile**, name Open Tender — goods, Method Open Tender, Procedure Planning example, Version1, Effective dates1Jul2027–30Jun2028. Table Milestone, Sequence, Applies, Counting rule, Minimum, Maximum, Default, Basis. Use seven milestone names from §10.1 in order; internal buffer defaults5/2 labelled Planning assumption; statutory bound cells **Verification required** in CONFIG. Below Estimated delivery period default **Not set**. Required profile completeness notice **This profile cannot support Plan submission until its required rules and sources are complete.** No approval button.

Method eligibility detail includes the governed category/value conditions, required circumstances, evidence, and any specific authorisation actor/stage; CONFIG shows **Required conditions not yet completed** rather than a fake complete checklist. Reminder setting: **Approaching milestone threshold**, numeric **7**, unit **Calendar days**, helper **Operational reminder period; not a statutory procurement deadline.** Footer Save changes.

### 10.12 U21 — Common state artboards and supporting forms

| Variant | Exact heading | Exact text | Control |
|---|---|---|---|
| Loading workspace | Loading Procurement Planning… | Approved skeleton rows only | None |
| Loading review | Loading Plan review… | Approved skeleton sections only | None |
| Module forbidden | You do not have access to Procurement Planning | This area needs one of these responsibilities: Departmental Author, Head of User Department, Procurement Planner, Head of Procurement Function, Finance Confirmation Officer, Accounting Officer, the configured statutory approver or Auditor. Ask your KenTender administrator to assign one in System setup. | None |
| Setup forbidden | You do not have access to System setup | This area needs Administrator or System Manager access. | None |
| Masked record | This record isn't available to you | It may not exist, or you may not have access to it. | Go to Procurement Planning |
| Load error | Procurement Planning could not be loaded | Try again. If the problem continues, contact support with the reference shown. | Try again |
| Missing mandatory config | Procurement rules are not configured | Required configuration is missing or incomplete. Draft work can continue where permitted; the affected submission is unavailable. | Back to Annual Plan |
| No accepted sources | No accepted departmental requirements | Accepted requirements will appear here after Procurement validation. | None |
| No search results | No requirements match this search | Change the search or clear the filters. | Clear filters |
| No validation tasks | No departmental plans awaiting validation | New submissions will appear here. | None |
| No current correction request | No correction requests | No upstream correction request is recorded for this Plan Item. | None |
| Historical Version | Historical Plan Version | This Version is read-only. Its reviewed evidence is preserved. | View current Active Plan, only where one exists and is readable |
| Complete action changed elsewhere | This action is no longer available | The record changed after you opened it. Refresh to see its current state. | Refresh |

**Late explanation dialog:** title **Record late activation explanation**; Initial Plan Version1, Financial year started1Jul2027, Activated2Jul2027 09:00 EAT, read-only UI scenario values; required Explanation **Publication acknowledgement was received after the financial year began.**; Cancel/Record explanation. Historical explanation view displays Recorded by Amina Hassan and recorded timestamp as separate fields. No retroactive activation date editor.

**Cancel update dialog:** title **Cancel Plan update?**, text **The open update will be cancelled. The Active Plan and existing procurement proceedings will remain unchanged.**, buttons Keep update/Cancel update. **Dissolve Draft item dialog:** title **Dissolve Plan Item?**, text **Its eligible sources will return to this Draft's unallocated requirements. This action does not release Budget funds.**, Cancel/Dissolve Plan Item. Do not show either where the server's source/scope/downstream guards prohibit it.

### 10.13 Static output and review order

Render U01-A/B/C/D first, then all four U11 review viewports and U12. Follow with U07, departmental U02–06, U08–10, publication U13, execution/correction U14–16, setup C01–04 and common U21 variants. Use exact family/variant IDs in exported filenames; viewport suffixes are -top, -items, -checks and -decisions. Each screen's state is identified in its external fixture context. Do not combine contradictory scenario values on one artboard.

The single static prompt is this §10 plus KT-STD §2. Values assigned to the UI-only scenario profiles are intentional supplied fixture content, not invitations to invent further data. Keep scenario provenance outside the artboard; ordinary product labels must describe the user's actual record. If an unlisted value is needed, omit that optional visual detail; do not mark a mandatory real requirement complete. Critical omitted evidence must instead be represented by its stated incomplete state.

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

### 11.5 Execution, notifications and forecasts

Milestone actuals belong to proceedings and exact source allocations. Selection of a Plan Item does not grant coverage to later requirements. Status-count summaries must identify whether they describe procurement coverage, remaining allowance or fulfilment. No sum of unlike units; no completed badge from publication.

Forecast proposals validate all resulting adjacencies, including omitted rows, and commit atomically. Individual proposed dates may be adjusted; a final milestone is a valid single-row revision. Already-actual milestones are immutable. Late forecasts are recorded and flagged, not suppressed to preserve a green schedule.

Notification identity and reforecast/resolution follow RI-040. Opening a reminder navigates to the exact item/proceeding and milestone. Read/acknowledge does not record completion. A pre-procurement reminder is retired only for work that transfers to a proceeding; remaining original allowance is not silently forgotten.

Multiple correction requests share one effective item hold until every request reaches a permitted terminal outcome. The scope lock remains independently effective afterwards. Resolved must identify an Active correction; Draft correction is not resolution. A stopped Requisition is never auto-restarted.

### 11.6 Configuration

Complete first-run API inputs and read projections for route and county applicability. Required configuration is visible and editable through existing authorised setup actions. Funding sources/reference/profile readers use owning services, not deep table access. No user can certify a legal rule's correctness through an unspecified checkbox.

The fifth tab groups existing/new agreed settings; final field schemas and source-verification permissions remain part of CFG amendment. Effective dates, immutable referenced Versions and the applicable-date resolver are not replaced by ordinary overwrite forms. If a reference is already used, an update creates a new Version.

Each module intake flag is independent; open/close uses its own control, single-open-year rule and audit. At command time, reaching the close instant blocks applicable initial submissions even before the hourly cleanup job runs. Closing the window does not make a previously accepted DPP disappear or forbid permitted updates.

## 12. Audit and historical integrity

| Event | Evidence visible in context |
|---|---|
| DPP certification/validation | Exact Submission, source revisions, certification/disposition, actor/capacity, time and outcome |
| Finance review | Exact financial basis, Budget Versions, currentness separately, reviewer and decision |
| Preparation/adoption/approval | Exact Plan Version, capacity, signature/decision and required collective evidence |
| Correction/withdrawal | Original immutable content, actionable reason, authorised decision and copied successor link |
| Publication | Approved document, Treasury evidence history, actual adapter outcomes, acknowledgement and activation outcome |
| Forecast correction | Exact baseline, forecast revisions and shared cascade reason; never rewritten actuals |
| Upstream correction | Origin Version, affected stable item, hold state and exact resolution evidence |

History is a readable record of evidence, not a developer event dump. Raw event IDs, digests, SQL fields and concurrency tokens stay out of the ordinary product view. Their server preservation remains mandatory.

Every command records its exact input/output identities, expected/resulting token, actor or authenticated producer, exercised authority, prior/resulting states, idempotency correlation, decision reason/evidence where required and instant. Audit derives actor/time server-side. Financial-basis reuse, source substitution/exclusion, scope protection, every correction request disposition, Treasury corrections, publication reconciliation/withdrawal and activation failure are distinguishable. Preserve immutable earlier versions, decisions and files. Reversal is a linked record, never erasure. A failed transaction cannot leave a signature, allocation, drawdown or pointer partially committed.

## 13. Deterministic seed contract

The single closed visual fixture pack is §10.1. Its context and explicit overrides apply to every artboard. Preserve the original three sources and two Plan Items; the security-assessment direct requirement is isolated. Use the corrected Julia/Peter/Grace scopes and chronology in PLN-REF §11.3.

| Fixture concern | Required resolution for implementation |
|---|---|
| BASE reservation None/None | This is a blocked mandatory-allocation case under the new rule, not an approval happy path |
| READY Youth designation | Proposed UI-only calculation/layout example. Requires verified category/method applicability and a separately approved integrated seed amendment before production-style happy-path testing |
| Schedule periods and profiles | Exact visual arithmetic supplied; legal/profile verification remains pending. Never seed the display example as verified production configuration |
| Estimate/source narrative additions | UI-only complete-detail examples identified in §10.1; reconcile with authoritative source fixtures before integrated tests |
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

Use the complete fixture pack in §10.1. The integrated BASE has 2 items, 3 sources, 2 departments and KES 130,000,000; Budget amounts are KES 100m and 60m, planned KES 80m and 50m. BASE has no qualifying reservation and must remain a blocked-readiness case under the illustrative 30%/KES 48m calculation. READY changes laptop designation to Youth and qualifying amount to KES 50m only as an explicitly labelled UI scenario, not proof of legally verified category eligibility. Production happy-path seeds require verified rules and matching configuration.

Seeds call the same authorized commands as the UI. DHI acceptance at 27 Nov 2026 14:00 EAT creates the APP; HRMD acceptance follows at 14:05. Julia’s October–November DHI assignment and Peter’s December DHI handover are separate from Peter’s HRMD responsibility. Do not backdate real evidence to repair fixtures. Enabled UOM Programme is used for the isolated security-assessment example; no invented Service UOM. Preserve full source quantities and deadline boundaries. No Requisition is required to calculate a Plan schedule.

Reset/replay is deterministic and idempotent, fails on conflicting authoritative data, and never creates a business role for Administrator, a second PE, FY user grants, legacy aliases or direct governed-state writes. All invitation actuals are absent before Tender publication; the supported invitation event then populates only its proceeding’s evidence. Other six actual integrations remain explicitly unavailable. Test the later-Need scenario with authorized/published original coverage and a separate new item; never merge it into the locked package.

## 14. Acceptance contract

Each result below is a normative acceptance requirement, not a test already run. IDs are unique in this successor. The full 72 decision-specific regressions in §17.4 (PLN18-RI-001–072) are also part of this contract and supplement the baseline and UX criteria. Cross-module requirements pass only with the corresponding provider/consumer implementation and evidence.

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
| PLN18-AC-046 | The Need-origin combined item (`PPI-MOH-2027-033`) and the direct-requirement fixture (§10.6) each produce equivalent, complete approved source lineage regardless of origin. |
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
| PLN18-AC-069 | Annual-budget reservation calculations use complete approved annual budget/Version; verified mandatory shortfall or missing basis blocks formal submission, while incomplete Drafts remain editable. |
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
| PLN18-AC-099 | Actuals are recorded per exact procurement proceeding/source coverage; duplicate events are idempotent and corrections supersede linked evidence; baseline lateness, forecast error and elapsed-duration variance are distinct. |
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
| PLN18-AC-119 | Forecast changes require reason, exact current schedule token and append-only revisions for changed rows only; preserve baseline, actuals and comparison references. |
| PLN18-AC-120 | No human role/API path supplies actuals directly; only authenticated owning-module events with exact proceeding/source lineage are accepted. |
| PLN18-AC-121 | Before publication the fixture has no actual event evidence; show Not available rather than zero. Invitation events later populate their own proceeding; unsupported six milestone integrations are labelled explicitly. |
| PLN18-AC-122 | Single year is fixed/read-only, aggregation and lotting are governed editable Draft fields, and lot count appears only for Packaged into lots; no multi-year justification control remains. |
| PLN18-AC-123 | Pre-Finance readiness checks applicable package/structure/source/schedule fields but does not require an existing Finance confirmation; formal submission adds current financial and mandatory rule/evidence gates. |
| PLN18-AC-124 | Forecasts initialize from baseline exactly once on activation; absent before activation; supersession preserves last forecasts and revision history rather than nulling them. |
| PLN18-AC-125 | Changing a forecast proposes all eligible later milestones by the same delta; excluded rows and explicit individual overrides remain visible and the resulting full schedule is validated. |
| PLN18-AC-126 | A milestone with a recorded actual date is never returned as an includable or excludable row in a cascade proposal, and a direct attempt to include one is rejected with `PLN_CASCADE_INCLUDES_ACTUAL_MILESTONE`. |
| PLN18-AC-127 | Confirming a cascade writes one `PlanItemForecastRevision` per included row, all sharing one `cascade_id`, atomically — a failure on any included row leaves every row in the batch unwritten. |
| PLN18-AC-128 | A final-milestone or other single-row forecast change is valid with a reason and null cascade ID; a multirow accepted set shares one cascade ID. |
| PLN18-AC-129 | Forecast confirmation validates every affected adjacency, including included/excluded boundaries and individual overrides, under the applicable profile; late completion forecasts remain recordable and flagged. |
| PLN18-AC-130 | Workspace/Active schedule-health counts derive from exact applicable item/proceeding forecast evidence; no Active plan means absent count, and unlike quantities or proceeding dates are not collapsed. |
| PLN18-AC-131 | Daily checks inspect every applicable outstanding milestone and update one unresolved notice per recipient/item/proceeding/milestone, without per-day duplicates, blocking work or inferring completion. |
| PLN18-AC-132 | Internal defaults come from complete effective-dated method/procedure profiles; missing profiles block submission instead of silently falling back to 5/2-day buffers or Open Tender rules. |
| PLN18-AC-133 | The baseline schedule card shows the computed result before the period inputs, and the period-adjustment disclosure loads closed by default. |
| PLN18-AC-134 | The computed baseline table updates immediately on a target-date or period change, before any save command is issued. |

### 14.2 Complete UX and state coverage

These are required future verification checks, not executed test results. Each UI acceptance ID is unique and referenced in §17.

| ID | Required result |
|---|---|
| PLN18-UX-01 | Workspace retains Active and candidate links independently when no action row exists; every admitted lifecycle/publication state has correct content and next action |
| PLN18-UX-02 | No read/filter/navigation creates a Plan/DPP; one site has no PE selector; FY is a view/operation filter and never a permission grant |
| PLN18-UX-03 | All counters, source quantities, department counts and monetary totals match the exact fixture/Version; facts are separately labelled |
| PLN18-UX-04 | DPP accounts for every current accepted Need at its applicable coverage cut-off; excluded Needs retain facts/reason and need no operative funding/classification |
| PLN18-UX-05 | Direct requirement and Need-funding forms enforce ownership, supported UOMs and Draft rules; copying direct entries preserves stable identity |
| PLN18-UX-06 | Certified/returned DPP evidence is immutable; corrected Draft and accepted-plus-update remain separately visible; acting authority expiry blocks stale commands |
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
| PLN18-UX-20 | Baseline lateness, forecast error and duration variance have correct signs/bases; missing versus inapplicable distinct; historical comparisons reproducible |
| PLN18-UX-21 | Cascade supports individual overrides and final-row revision; every affected adjacency checked; commit atomic; late forecasts allowed; already-actual rows immutable |
| PLN18-UX-22 | Reminders deduplicate, reforecast without flooding, resolve only from actual evidence and navigate to the exact work; later milestones not starved by earlier missing actuals |
| PLN18-UX-23 | Multiple correction requests retain the shared hold; only permitted terminal outcomes release it; no Draft resolution, scope unlock or stopped-Requisition resurrection |
| PLN18-UX-24 | Reservation denominator/qualifying amount/shortfall reflect the complete Budget basis; overlap/category rules verified; missing mandatory configuration blocks |
| PLN18-UX-25 | No Planning highest-advantage ranking or reason-only override; planned designation and candidate entitlement remain distinct |
| PLN18-UX-26 | Initial/configured entity setup can save every mandatory route/county field; domain, API, UI and validation agree |
| PLN18-UX-27 | DPP intake controls are complete; independent module flags, advance-FY close dates and command-time deadlines work without relying on scheduler execution |
| PLN18-UX-28 | Funding/reference/profile/reminder maintenance is usable under existing setup authority, immutable when referenced, historically resolvable and auditable; no configuration approval |
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
8. Two sequential Tender proceedings retain different actuals and exact coverage; corrected events never overwrite another proceeding. Forecast comparisons pin the applicable revision; missing values are not zero; reminders do not duplicate on daily runs or reforecast.
9. Full authorized review/export exposes all fields and immutable evidence, source back-navigation restores context, failures have actionable copy, and none of these controls requires opening every accordion. Complete every §10 artboard/state at the prescribed viewport before release.

## 15. Implementation, dependencies and verification

### 15.1 Implementation constraints

Apply KT-STD-001 v1.4 §§4–6: explicit Frappe domain records/services; existing Vue 3 Desk mounting and scoped components; native ERPNext configuration/catalogues; server authorization and exact version/idempotency enforcement; focused tests followed by affected-module/cross-app and release gates. Do not port the proof-of-concept stack or global CSS resets into Desk. Register surfaces centrally, use stable accessible selectors and return to the owning workspace.

Inspect the actual implementation during re-implementation; the uploaded documents’ build assertions are not verified facts. Record concrete repository/test targets against the stable RI IDs after inspection. Do not invent those paths now. Cutover must remove superseded schema, roles, fields, commands and routes after dependency/reference checks and required evidence; preserve immutable records and never delete ERPNext/HRMS records as a Planning cleanup.

### 15.2 Required sequence and open owner work

| Order | Work unit | Exit evidence |
|---|---|---|
| 1 | Incorporate the approved governing decisions; reconcile CFG/AUTH/LAW dependencies | One route catalogue, named preparation actor, recorded approval and explicit dependency dispositions |
| 2 | Finalise stable identities, versioned content, state fields and immutable evidence | Field-purpose tables, uniqueness definitions and correction/lineage examples |
| 3 | Implement DPP coverage, disposition, windows and accepted-source projection | Initial, returned, not-proceeding, withdrawn-source and late-addition tests |
| 4 | Implement Plan/Funding state separation and Budget decision-basis contract | No-reservation full-cycle test; stale-basis race; repeat review; Active reassessment |
| 5 | Implement signature, adoption, statutory route and return guards | Each positive/negative transition and same-user conflict tested on original and correction Versions |
| 6 | Implement successor activation and Requisition contracts | No balance reset, no duplicate source capacity, exact reversal, one-open-Requisition and correction-request tests |
| 7 | Implement the agreed schedule, publication and reporting boundaries after their prerequisites | Method profiles, deterministic calculations, exact publication package/acknowledgement, Treasury evidence, recovery paths and report data ownership contracts |
| 8 | Implement the reviewed artboards and reconcile seeds and acceptance criteria | Every screen state maps to the same lifecycle; one integrated fixture; unique criterion IDs; no contradictory required outcomes |
| 9 | Run the prescribed release gate | KT-STD §4–6 evidence, affected cross-module tests, schema scan and reviewed screens |

Do not repair a fixture by weakening a domain invariant. Do not mark a code change verified solely because an old test passed: the old acceptance contract itself contains mutually exclusive outcomes. Preserve the intended assertion, replace the superseded assertion, and keep an explicit old-to-new test mapping in the final register.

These are approved work requirements, not unanswered product-decision rows. No item below is claimed complete merely because its design has been agreed.

| Dependency | Responsible specification / owner | Exit evidence before affected implementation or verification |
|---|---|---|
| Primary legal verification | LAW / Configuration & Governance | Exact primary sources, editions and dates; resolved method, schedule, reservation, route and publication applicability; checked Schedule layout; unresolved points explicitly blocked |
| Configuration completion | CFG / kentender_core | Existing v0.9 reconciled under §17.2; complete fields, services, maintenance surfaces, historical rules, errors and seeds; no new configuration approval chain |
| Canonical domain and API contract | PLN with BUD, NDS, STR, REQ, TPR and TPUB | PLN-side identities, storage classes, field rules, commands and envelopes are defined in §§4–8. Provider amendments must adopt matching precision, schemas, transactional behavior and versioning; integration tests must prove them |
| Budget decision and annual denominator services | BUD with PLN | Atomic financial-basis validation contract without Planning reservations; authoritative complete annual-budget basis and Version; consistent decimal amounts across modules |
| Source disposition and correction response | NDS / PLN / REQ | Distinct accepted-disposition versus Active-usage events; correction outcome and stopped-Requisition follow-up; no automatic resurrection or scope expansion |
| Publication package and adapter | PLN publication owner | Exact KenTender JSON schema and human-readable mappings; immutable approved files; hash-bound acknowledgement; Treasury evidence; failure/indeterminate reconciliation; withdrawal and activation-held correction contracts |
| Full artboard review and revamp | PLN UX plus affected CFG surfaces | The required content/state specification is integrated in §§9–11; focused UX direction is accepted. Remaining full artboard rendering, actual-user validation and production review-pack parity require evidence |
| Integrated seed reconciliation | SEED / KT-STD and module seed owners | Agreed actor chronology and source ordering; 2 items, 3 sources and KES 130 million default Plan; valid UOMs; methods/profiles and mandatory reservation allocation readiness reconciled |
| Acceptance replacement map | PLN and affected module owners | Unique successor IDs and complete old-occurrence mappings are provided in §§14/17.3; implementation must replace the tests and record real results |
| Implementation evidence | Repository/application owners | Inspected actual schema/services/UI; meaningful regressions for the changed rules; prescribed KT-STD release evidence. No claims based solely on documents describing the build |

The integrated Plan's original amounts do not excuse a reservation shortfall under RI-047. Reconcile its qualifying designations and complete Budget denominator against verified rules; if the original fixture is intentionally below target, label it a blocked-readiness scenario and provide a separate valid approval fixture. Do not falsify category eligibility or reduce the annual denominator to force the old happy path to pass.

### 15.3 Explicit facilities to be implemented later

| Future facility | Current MVP boundary | Required future scope |
|---|---|---|
| Multi-year procurement | Single year only; server rejects unsupported multi-year submission | Whole-package estimate and horizon, annual allocations, future-funding status, commitment authority and BUD/REQ contracts |
| Full OCDS publication | KenTender Annual Plan JSON, accessible web view and PDF; no OCDS compliance claim | Supported OCDS version/extensions, registered prefix, planning/proceeding relationships and full release history |
| Automated Treasury transmission and acknowledgement | AO records external submission evidence | Transmission adapter, exact document correlation, receipt/reconciliation and exception handling |
| Aggregate Plan Item milestone actuals | Separate proceeding-level actuals | Explicit aggregation semantics for partial, sequential, cancelled and corrected proceedings |
| Six remaining milestone actual integrations | Invitation actual path only is presently specified end to end | Owning operational modules publish authenticated, versioned, correctable events with exact source/proceeding lineage |
| Full completion and fulfilment derivation | Factual procurement-stage evidence; Completion tracking not yet available where unsupported | Downstream delivery/acceptance evidence and complete quantity coverage; never infer fulfilment from publication |
| Candidate-level preference entitlement | Planned designation and mandatory restrictions only | Candidate eligibility evidence and applicable highest-advantage treatment in the responsible downstream module |
| Statutory returns using downstream facts | Website publication and Planning facts as specified; no claim that all report data already exists | Reporting contracts with the actual award, supplier, implementation and payment owners |
| Expansion of procurement scope through tender amendment, cancellation/replacement or contract variation | No later Need absorbed into a scope-locked item; separate-item governed route remains | Independently specified lawful downstream procedures and exact source/quantity treatment; not an APP-only amendment |

### 15.4 Release evidence

Require focused red-green evidence for every changed acceptance criterion, clean module and affected cross-module contract suites, production asset build, the prescribed browser smoke/own-request checks, all approved artboards compared at 1440 × 1024, and a schema/repository scan proving superseded constructs removed. Re-run broad testing only for a concrete affected shared contract or the release gate. Prototype walkthrough is not release evidence.

## 16. Prohibited shortcuts

- No second PE, PE selector, FY user grant, local role authority, task-as-permission or client-only lifecycle guard.
- No mandatory Need, partial accepted-Need allocation, fabricated residual source, source-less item or direct-source identity regenerated on copy.
- No Planning Budget reservation, release, revalidation, commitment or ledger mutation.
- No optional statutory approval, role equivalence between Planner/HOPF, extra HOPF approval stage, or correction-chain segregation reset.
- No editable submitted/approved/Active baseline, source-cohort expansion through correction, allowance reset, or later source absorbed into a scope-locked item.
- No implicit procurement coverage/fulfilment from a plan inclusion, stable item ID or old Tender badge.
- No universal method timing, missing-profile fallback, hard-coded unverified legal thresholds, Plan-total reservation denominator or reason-only waiver of mandatory rules.
- No Planning candidate highest-advantage ranking, preference override, multi-year partial support, OCDS claim or fabricated contracting-process IDs.
- No user actual entry, unqualified aggregate item actual, missing-to-zero variance, later-forecast substitution, or per-day duplicate reminder.
- No synchronous external publication inside approval, blind unknown-outcome retry/withdrawal, fabricated acknowledgement or forced activation of defective published content.
- No summary-only governance, forced accordion/download prerequisite, omitted required evidence, duplicate sidebar/chrome, delimiter-crammed facts, or prototype harness in production.
- No disposal payload, unauthorized export disclosure, silent dependency amendment, invented implementation evidence or weakening rules to make old seeds/tests pass.

## 17. Traceability, precedence and full re-implementation table

### 17.1 Precedence and incorporation ledger

This successor replaces conflicting operative v1.17 content. The original v1.17 file, approved refinement register and original UI specification remain historical source artifacts. AUTH owns authority, CFG owns catalogues/rules/setup, BUD owns financial facts and transactions, NDS owns Need revisions, STR owns objective/snapshot evidence, REQ owns requisition authorization and its Budget reservation, and TPR/TPUB own tender preparation/publication facts. This document cannot silently amend their implementations.

| Incorporated source | Current location and treatment |
|---|---|
| PLN-REF-001 governing decision and ownership | §§1 and 3 |
| PLN-REF-001 departmental/Plan/Finance/correction decisions | §§4–5 and 7–8 |
| PLN-REF-001 preparation/statutory/segregation decisions | §6 and command/acceptance tables |
| PLN-REF-001 method/schedule/publication/reservation decisions | §5.5 with corresponding model/API/error/UI requirements |
| PLN-REF-001 full 72-row register | §17.4, preserved IDs and full old issue/replacement/verification content; current target sections/screens added |
| PLN-UX-001 presentation, routes, state/action inventory | §9 |
| PLN-UX-001 closed artboard/fixture pack | §10, all 21 families |
| PLN-UX-001 functional/evidence/seed/acceptance rules | §§11–14 |
| Product-owner acceptance of proof of concept | §9.8; direction accepted, full implementation/visual verification still required |
| Every v1.17 acceptance occurrence | Corrected result in §14.1 and exact mapping below; duplicate AC-100 occurrences disambiguated |

### 17.2 Matching LAW/CFG and other owner amendments

**LAW correction.** Correct LAW-REG-001 through a traceable successor, retaining its approved predecessor. Separate source provision, interpretation and KenTender implementation decision.

| Issue | Required disposition |
|---|---|
| Sixteen-column description versus seventeen enumerated entries | Inspect original Schedule layout, grouped headings and guidance notes before correcting numbering; do not mechanically replace the count |
| Six-obligation heading versus eight listed rows | Remove the numeric heading claim. Give every obligation an identifier, responsible actor, recipient, timing and implementing owner; distinguish Treasury actions from the entity's own obligations |
| Head of Procurement Function equated with Planner | Correct now to the agreed separate preparation/signature responsibility; see §8.2 |
| Verbatim label | Restrict to exact transcription; label reorganised tables, summaries and mappings accurately |
| Candidate entitlement inferred at planning | Apply §10.3.2 and retain the exact downstream legal-verification requirement |
| Source status | Record instrument edition, provision, amendments, effective dates, exact source location and verification status. Approval of the earlier register is not proof of current legal accuracy |

Editorial corrections and the approved role correction need not await all primary-source verification. Questions of legal applicability remain unverified until the evidence is obtained and recorded.

**CFG evidence now available.** Approved CFG v0.9 already defines the four statutory routes and county flag (§4.1), independent module intake flags (§4.2), funding sources (§4.4), regulator references and historical retention (§4.4A), and Administrator/System Manager maintenance without approval. Remove claims in PLN that those catalogues have no owner. Extend this baseline rather than creating parallel registries.

| CFG gap or contradiction | Required matching change |
|---|---|
| Mandatory route omitted from ConfigureProcuringEntity and first-run artboard | Add the actual required input and validation to the service and configuration journey; first-run UI must be able to satisfy the mandatory domain rule |
| County flag absent from entity artboard | Provide its control and define consistency validation with entity facts and applicable rules |
| DPP/disposal intake fields exist, but service/UI detail mainly covers Needs | Complete DPP maintenance commands, field states, errors, audit and Fiscal Years controls. Identify disposal counterparts for its owning module; do not import disposal into the Procurement Planning payload |
| Funding sources and regulator register described as maintained in System setup, without complete surfaces/services | Specify the field tables, maintenance actions, consumers, validation, errors and artboards; reuse the existing configuration authority |
| Missing method/schedule/reminder settings | Add method-condition profiles, procedure schedule profiles, default periods and 7-day operational reminder threshold under §§10.1, 10.1B and 10.3.3 |
| Reservation shortfall and missing target always non-blocking | Replace CFG §4.4A and AC-032's reservation treatment with §10.3.1. Optional price-index absence remains separate |
| Every rule resolved by FY only | Define the legally applicable selection date for each rule and its effect on Draft, submitted and downstream procurement; snapshot the selected Version. Do not assume today's date or FY works for every rule |
| Closing instant must belong to intake year despite advance-year fixtures | Clarify that it belongs to that year's intake configuration; it need not fall inside the FY dates. Validate current server time against both flag and close instant at command time, independent of the hourly scheduler |
| Thin historical register specification | Complete record identity, effective-period overlap/gap handling, immutable referenced Versions, correction/supersession, exact resolver inputs/outputs and audit evidence |
| Incomplete seed and acceptance coverage | Supply configuration required by the shared fixture; map every new mandatory domain rule to service, UI, seed and tests. Do not treat approved seed figures as independently verified production law |

Primary-source verification must cover method admissibility and thresholds, cumulative limits, schedule/counting rules, reservation eligibility/denominators/overlap, approval-route applicability, publication prerequisites and the prescribed Plan format. Record unresolved interpretation as such. A missing mandatory rule blocks the affected submission/action with a specific configuration error; never fill it with a guessed constant or a permissive fallback.

The artboard specification in §10 explicitly includes the **affected System setup surfaces**, as well as all Procurement Planning artboards. Reconcile CFG's older KT-STD/AUTH references and stale control wording during its amendment; preserve the agreed absence of a configuration approval workflow.

Do not mark those external controlled documents updated by this PLN-only consolidation. The role correction and catalog ownership reconciliation are agreed; primary legal applicability/layout verification and actual provider implementations remain open. CFG C01–C04 requirements are incorporated in §10 as coordinated owner work, not a new Planning configuration registry.

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

All rows below are **agreed at decision level and incorporated in this document**. None is marked implemented or tested. “Baseline/owner references” preserves the original reviewed-section references from PLN-REF-001; those numbers are provenance, not v1.18 navigation. “Current target” gives the new local sections and screen families. PLN18-RI acceptance IDs are stable regression requirements; required results are stated in full. External owner changes remain subject to §15.

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
| PLN-RI-030 | Reconciliation | Forecasts must be null on Superseded Versions | Preserve last forecasts and append-only revision history after supersession | §§4.8, 5.5, 7; U07/U14/U15 | PLN §4.9; AC-123 | **PLN18-RI-030** — Archived forecast values/history unchanged by successor activation |
| PLN-RI-031 | Reconciliation | All actual writers declared absent despite invitation event path | Document invitation publisher and distinguish pre-event fixtures from unsupported milestones | §§4.8, 5.5, 7; U14 | PLN §§4.9, 8.2, 18; TPR §9.5; TPUB §§8–9 | **PLN18-RI-031** — Publication event writes invitation actual once; pre-publication fixture remains null |
| PLN-RI-032 | Agreed refinement | Multiple sequential Requisitions/Tenders can overwrite one item-level actual | Record actuals per proceeding with exact Plan/source/quantity lineage; repeated event ID is idempotent, different Tender is separate, correction supersedes a linked event. Display proceedings separately; defer aggregate item actuals | §§4.8, 5.5, 7; U14 | §10.1A; PLN actual contract; REQ/TPR/TPUB | **PLN18-RI-032** — Two sequential Tenders retain different dates; duplicate replay changes nothing; correction cannot overwrite another proceeding or compare against a later forecast |
| PLN-RI-033 | Agreed refinement | Strategy snapshot timing and reviewed path are under-specified | Retain reviewed lineage; create deterministic STR snapshot at final approval; mismatch fails atomically | §§4.6, 7.4; U09/U11 | PLN §§4.9, 7.2, 8; STR §§7–8, 12.6 | **PLN18-RI-033** — Approval snapshot equals reviewed selection; retry creates no duplicate snapshot |
| PLN-RI-034 | Agreed refinement | Planning completion depends on downstream Requisition; fixtures use conflicting derivation | Use departmental boundaries; combined baseline is earliest required-by; REQ may choose earlier | §§4.6, 4.8, 5.5, 7–8; U09/U11 | PLN §4.9, DES-09/09A, §14.5; REQ §5.2; SEED §§3.6, 5.3 | **PLN18-RI-034** — Planning can complete without a Requisition; REQ cannot extend source/Plan boundary |
| PLN-RI-035 | Agreed refinement | Multi-year flag has no complete funding or completion semantics | MVP single-year completion within target FY only; remove selectable Multi-year and reject unsupported submission. Explicit future facility requires whole-package horizon/value, annual funding and future commitment authority | §§4.6, 4.8, 5.5, 7–8; U09 | §10.1; §12.2; PLN §§4.4, 4.9, 7.3–7.4; NDS/REQ/BUD | **PLN18-RI-035** — No UI/API multi-year bypass; fixed single-year output where required; future facility is clearly documented, with no one-year affordability comparison against an unexplained multi-year total |
| PLN-RI-036 | Agreed refinement | Universal seven-/fourteen-day floors ignore method/procedure applicability | Implement governed method/procedure schedule profiles and complete System setup maintenance surface: sequence, counting, verified limits, internal defaults, legal references, effective dates and immutable Versions; missing profile blocks submission | §§4.6, 4.8, 5.5, 7–8; U09/U11/C04 | §10.1; §11.4; PLN §4.9; CFG services/UI/seeds | **PLN18-RI-036** — Different methods resolve appropriate profiles; missing/ambiguous rules fail the affected gate; no Open Tender fallback; submitted profile history survives configuration change |
| PLN-RI-037 | Agreed refinement | Sensible implementation allowance is an undefined blocker | Require Planner's non-negative integer Estimated delivery or implementation period in calendar days; zero explicit, never fallback. Signing plus period must meet source-derived boundary at submission; later late forecasts remain recordable | §§4.6, 4.8, 5.5, 7–8; U09/U11 | §10.1; PLN invariant 12a; AC-116; method profiles | **PLN18-RI-037** — Exact-date boundary passes and one-day excess blocks; missing period rejects; zero requires explicit entry; deadline not silently extended; Active late forecast can be recorded |
| PLN-RI-038 | Agreed refinement | Date lateness and elapsed-duration variance are conflated | Baseline lateness = actual minus baseline; forecast error = actual minus identified forecast; duration variance = planned elapsed minus actual elapsed. Per proceeding, fixed source/rule Versions; missing is Not available and inapplicable is Not applicable | §§4.6, 4.8, 5.5, 7–8; U14 | §10.1A; LAW §1; PLN §4.9; views/exports | **PLN18-RI-038** — Early/on-time/late signs agree across UI/export; late finish with shorter duration reports both correctly; no missing-to-zero substitution or future forecast comparison |
| PLN-RI-039 | Agreed refinement | Cascade validates only included rows; final milestone has no edit path | Validate every affected adjacency in the resulting schedule and allow a last-milestone single-row revision | §§4.6, 4.8, 5.5, 7–8; U15 | PLN invariant 12c; §§8.2, 11.16–11.16A, 12.12 | **PLN18-RI-039** — Shift predecessor while successor excluded catches violation; final milestone can change with reason |
| PLN-RI-040 | Agreed refinement | Daily deduplication conflicts with one unresolved notice; first missing actual hides later dates | Check every applicable outstanding milestone daily; configurable initial 7-calendar-day approach window; one evolving notice per recipient/item/proceeding/milestone; explicit missing-actual text, reforecast inactivation/reactivation and actual-event resolution | §§4.6, 4.8, 5.5, 7–8; U14/U21/C04 | §10.1B; PLN §8.3 and AC-130; CFG/shared notifications | **PLN18-RI-040** — Repeated runs and reforecasts do not flood; later milestones still checked; actual resolves only its notice; unsupported integration labelled; pre-procurement handover does not duplicate covered work |
| PLN-RI-041 | Agreed refinement | Approved but unpublished or externally uncertain invalid Plan has no correction route | Hold/reconcile; confirmed-unpublished AO request and statutory Withdraw for correction create copied Draft with full governance. Unknown outcome forbids withdrawal/replacement. Published with failed activation becomes Published — activation held and permits governed correction successor | §§4.9, 5.5.2, 7–8; U13/U07 | §5; §10.2.3; PLN §§5.2, 7.1, 8.2, 12.11; publication adapter | **PLN18-RI-041** — Hold/dispatch race cannot misclassify unpublished; no edits to approval; no uncertain cancellation; held Version has no new authorisation capacity; correction can activate without first activating defective content |
| PLN-RI-042 | Agreed refinement | Publication runs inside ApproveAnnualPlan as if external transmission were locally atomic | Commit approval and durable intent; apply Treasury/hold gates, transmit and reconcile separately; record exact acknowledgement then activate once only if activation checks pass | §§4.9, 5.5.2, 7–8; U13 | §10.2; PLN §8.2; PlanPublication | **PLN18-RI-042** — Crash after external success, duplicate callback and concurrent retry preserve exact evidence; invalid acknowledged candidate is held without false activation or duplicate publication |
| PLN-RI-043 | Agreed refinement | Treasury submission is external but its publication prerequisite has no evidence | AO Record Treasury submission: exact approved Version/document hash, time, channel, destination, dispatch reference, attachment and confirmation. Gate website transmission on valid evidence; append corrections; require own evidence per successor; automate later | §§4.9, 5.5.2, 7–8; U13 | §10.2.2; PLN §§2.1, 4.13, 7.5A; LAW §5 | **PLN18-RI-043** — Approval intent waits for evidence; predecessor evidence cannot satisfy successor; invalidation holds/reconciles; no Treasury approval or receipt gate; website/State Portal facts not inferred |
| PLN-RI-044 | Reconciliation | Procurement publication payload includes disposal items | Remove disposal section and references from procurement payload | §§4.9, 5.5.2, 7–8; U13 | PLN §4.13; AC-078, 095, 109 | **PLN18-RI-044** — Payload/schema includes no asset-disposal content |
| PLN-RI-045 | Agreed refinement | OCDS-shaped is undefined and one Plan Item is wrongly assumed to equal one contracting process | MVP publishes accessible web view, PDF and exact versioned KenTender Annual Plan JSON from one immutable approved snapshot, with exact package hash acknowledgement. Defer full OCDS; preserve stable Plan/item and exact Version IDs; operational facts separate | §§4.9, 5.5.2, 7–8; U13 | §10.2.1; §12.2; PLN §4.13; publication adapter | **PLN18-RI-045** — All formats match approved snapshot/schema; retries resend exact files; acknowledgement matches package; no disposal; no OCDS-compliance claim or fabricated per-item ocid |
| PLN-RI-046 | Reconciliation | Plan claims to hold every fact required by statutory returns | Replace blanket claim with field ownership/dependency mapping; awards, supplier data and payments stay downstream | §§4.9, 5.5.2, 7–8; U14/U21 | PLN §2.1, §7.5A; AC-110; LAW §5 | **PLN18-RI-046** — Each return column maps to actual owner or an explicit missing future source |
| PLN-RI-047 | Agreed refinement | Reservation share uses Plan total and always permits shortfall | Use complete approved annual procurement budget/Version for annual-budget obligation; qualifying categories only; separate county basis and verified overlap. Separate item for partial qualifying allocation. Mandatory verified allocation shortfall or missing basis blocks submission; snapshot and recheck | §§4.6, 5.5.3, 7–8; U07/U11/C03 | §10.3.1; PLN invariants 24/24a; LAW §4; CFG §4.4A/AC-032; BUD | **PLN18-RI-047** — 100m budget/40m Plan/12m qualifying reports 12% annual basis, not 30%; no category/lotting overcount; no invented overlap; missing mandatory rules fail; Draft remains editable; history exact |
| PLN-RI-048 | Agreed refinement | Plan data is used to rank future bidder entitlement with a reason-only override | Separate planned designation, mandatory restrictions and candidate entitlement; remove Planning highest-advantage selection and override. Candidate verification/preference treatment is downstream future work; designation updates respect governance and scope lock | §§4.6, 5.5.3, 7–8; U09/U11 | §10.3.2; §11.2; PLN invariant 24aa; LAW §4.2; downstream procurement | **PLN18-RI-048** — No ranking or override control/API; mandatory restrictions not waived by reason; no Tender eligibility mutation through APP update; candidate entitlement not asserted from a Plan category |
| PLN-RI-049 | Agreed refinement | Method admissibility relies on value while conditional requirements are missing | Versioned eligibility checklist per method, with conditions, evidence, limits and any specific authorisation actor/stage. Automated facts and judgement declarations distinguished. Missing complete profile/evidence blocks submission; downstream rechecks before use | §§4.6, 5.5.3, 7–8; U09/U11/C03 | §10.3.3; §11.4; PLN §4.9/invariant 25; CFG; LAW §§2–3 | **PLN18-RI-049** — Within-threshold but missing condition fails; generic reason is insufficient; catalogue membership not operational support; APP approval does not substitute for required separate authorisation |
| PLN-RI-050 | Reconciliation | OU argument prohibited even for Budget Line eligibility | Permit source OU on Budget record-eligibility service; keep it out of site-wide Strategy resolution | §§3, 7.3; U03/U04 | PLN §§7.2–7.3, 17; BUD §9.1 | **PLN18-RI-050** — Entity-wide and department-owned lines resolve correctly without broadening user authority |
| PLN-RI-051 | Agreed refinement | Workspace strip only describes Draft or Active and not coexistence | Show Active baseline and open candidate distinctly; specify every governance/publication state and actor action | §§9–11; U01/U07 | PLN §§11.2, 11.18, 12.1 | **PLN18-RI-051** — Initial governance, publication failure and Active-plus-successor remain directly navigable |
| PLN-RI-052 | Reconciliation | Multi-PE selectors and tests survive a one-site-one-PE model | Remove PE selection and simulated cross-PE cases; preserve OU, responsibility and FY-operation tests | §§9–11; U01/C01 | PLN §§8.1, 12.1, 15–16 | **PLN18-RI-052** — No second PE/context selector or user FY grant exists |
| PLN-RI-053 | Reconciliation | Task summaries join unrelated facts with delimiters | Use labelled facts per KT-STD §2.2; retain only legitimate identifier lineage/status-count notation | §§9–11; All | PLN §11, especially DES-01 | **PLN18-RI-053** — Artboards have exact distinct fields and no inferred package details |
| PLN-RI-054 | Agreed refinement | Governance artboards omit material submitted content and evidence | Complete read-only Plan/package/source/schedule/method/funding/reservation/change review and exact review pack; next-session full Planning artboard revamp for completeness, usability and UX, including affected System setup surfaces | §§9–11; U11/U12 | §§11.1, 11.4, 12.1; PLN §§11.13–11.14, 12.10 | **PLN18-RI-054** — Every governed field/evidence accessible without losing decision context; correct Version/export/history; decision guards; no forced click-through; full requirements-to-artboard coverage |
| PLN-RI-055 | Reconciliation | AC-100 duplicated; old ACs prohibit required lotting and require forbidden reservations | Create one uniquely identified acceptance set and an old-to-new criterion map | §§14, 17.3; All | PLN §15 | **PLN18-RI-055** — Unique identifiers; no contradictory expected results; every changed rule has coverage |
| PLN-RI-056 | Reconciliation | Infrastructure seed evaluation interval is 31 days despite 30-day maximum | Derive baseline from selected periods; reconcile seed and artboard dates | §§10.1, 13; U09/U11/U15 | PLN §14.5; DES-09/14 | **PLN18-RI-056** — Seed uses same schedule calculation and validation as product commands |
| PLN-RI-057 | Reconciliation | Integrated Plan has two items/KES130m, several screens show one/KES80m without clear profile | Align default integrated Plan or mark each alternate artboard profile explicitly | §§10.1, 13; U01/U07/U10/U11 | PLN §§11, 14; SEED §§3–5 | **PLN18-RI-057** — Default Plan has 2 items, 3 sources, KES130m; Finance line totals 80m and 50m |
| PLN-RI-058 | Reconciliation | Direct fixture uses Service, absent from governed UOM register | Choose a documented valid unit consistently or approve catalogue addition with semantic reason | §§10.1, 13; U04 | PLN DES-04 and §14.7; KT-STD §8.5 | **PLN18-RI-058** — Direct fixture passes actual enabled-UOM validation |
| PLN-RI-059 | Agreed refinement | Actor assignments conflict and acceptance/submission timing does not prove order | Use §11.3 canonical timeline: Julia DHI Oct–Nov, Peter DHI from Dec and HRMD throughout; 25 Nov DPPs certified Julia 10:30/Peter 11:00 after source acceptance; Mercy accepts 27 Nov 14:00/14:05 | §§10.1, 13; U02/U05/U06/U11 | §11.3; PLN §14.2–14.4; NDS §14; SEED §3; KT-STD/shared fixtures | **PLN18-RI-059** — Exact command-time role/scope, source-before-certification and deterministic first APP creation; expired outgoing actor denied from old page; real historical records never backdated |
| PLN-RI-060 | Reconciliation | Seed method/category catalogues retain earlier subsets or labels | Reconcile fixture prerequisites with the final approved catalogues; no invented local catalogue | §§10.1, 13; U09/C03/C04 | PLN §§4.9, 14.1; LAW §§2–4; CFG | **PLN18-RI-060** — Every selectable value exists and has the required effective-dated rule |
| PLN-RI-061 | Agreed refinement | Domain fields drift from reported build with no governing contract | Exact decimal currency-unit amounts and explicit precision; no float or silent rounding; stable versus revision identity; calculated projections versus immutable snapshots; task authority from Version/capacity/AUTH; full field-purpose/type/ownership/history tables | §4; All | §11.2; PLN §1.1 and §4; BUD/REQ amount contracts | **PLN18-RI-061** — Money round-trips exactly, excess decimals reject; source identity survives copies; historical calculations reproducible; no unused scope authority or display-number substitution; actual build reconciled against approved contract |
| PLN-RI-062 | Reconciliation | Referenced versions, ownership and approval statuses are asserted inconsistently | Use NDS1.10, internal TPUB0.3 and supplied approved CFG0.9; track actual control status and remove stale missing-owner/corrected-build claims | §§1.2, 15, 17.2; All | §1; §11.4; PLN §§1, 18, 20; SEED §1.2; TPR §9.5 | **PLN18-RI-062** — Dependency matrix cites actual sources; CFG ownership recognised; implementation assertions distinguished from verified findings |
| PLN-RI-063 | Agreed refinement | LAW counts, verbatim claims and role/entitlement inferences are inconsistent | Traceable LAW correction: verify Schedule layout before count change; remove numeric reporting heading and identify obligations; correct HOPF/Planner distinction; separate source, interpretation and design; record verification status | §§1.2, 15, 17.2; U11/U13/C03 | §11.4; LAW §§1, 4, 5, 8 | **PLN18-RI-063** — Original layout checked before remapping; each obligation has owner/recipient/timing; summaries not labelled verbatim; no unsupported role equivalence or candidate-entitlement inference |
| PLN-RI-064 | Agreed refinement | CFG dependency initially missing; supplied approved v0.9 has incomplete surfaces/contracts and stale rule policies | Use supplied CFG v0.9; remove missing-owner claims. Complete route/county first-run controls, DPP intake, catalogue services/UI, profile settings, historical rule resolution and close-time semantics; reconcile reservation gates; retain primary legal verification prerequisite | §§1.2, 15, 17.2; C01/C02/C03/C04 | §11.4; §12.1; CFG §§4, 7, 10–14; PLN §18; LAW | **PLN18-RI-064** — Every mandatory field operable in UI/API; configured consumers use explicit services; rule gaps fail correctly; advance-FY close dates work; no scheduler-only closure; legal sources and production seed applicability recorded |
| PLN-RI-065 | Agreed refinement | Project name, execution status, late activation explanation and override lack actionable contracts | Optional Draft Plan Project name for one project; read-only proceeding execution facts with incomplete-completion label; AO late-initial-activation explanation at late adoption or append-only follow-up after boundary crossed; remove preference override | §§4.5–4.8, 7–8; U07/U14/U21 | §11.2; PLN §§4, 5.3, 8, 15; LAW §1; downstream status owners | **PLN18-RI-065** — Mixed portfolio permits blank project; publication is not fulfilment; partial/multiple proceedings explicit; late explanation actor/time retained without blocking acknowledgement; normal in-year successor not mislabelled late |
| PLN-RI-066 | Reconciliation | Finance-shortfall page treats current availability as the blocking amount; some required load states absent | Correct exact copy to approved-amount failure; specify Loading/Not configured and distinguish advisory availability | §§8–11; U10/U21 | PLN §11.18; KT-STD §§3–3A | **PLN18-RI-066** — Within-approved/low-availability case allows confirmation; configuration failure is never an empty success |
| PLN-RI-067 | Agreed refinement | User reports a later Need was absorbed through an APP update into a Plan Item with a published Tender | Lock procurement scope from first Requisition authorisation: reject later source additions and package enlargement across all successor identities; retain normal APP updates for other/new items | §§4.8, 5.4.6, 7–8, 14.3; U09/U14/U16 | This register §7.6; PLN §§4.9–4.10, 5.3, 7.4, 8.2, 12.7–12.12; REQ authorisation contract | **PLN18-RI-067** — Authorised-but-unpublished and published cases reject added sources, increased quantities and scope-text substitution; direct API and copied-Version paths cannot bypass |
| PLN-RI-068 | Agreed refinement | Additional requirement can reach Planning with no executable procurement route | Form a separate Plan Item for the new requirement after normal departmental governance; include it in a governed APP successor, assess funding, activate and allow its own Requisition/procurement | §§4.8, 5.4.6, 7–8, 14.3; U01/U07/U08/U14 | This register §7.6; PLN §§5.1–5.2, 7, 12; REQ §9.1 | **PLN18-RI-068** — Later Need progresses through separate-item route without modifying the original Tender or blocking the whole APP |
| PLN-RI-069 | Reconciliation | Item-level Tender linkage can falsely imply that later sources are covered or fulfilled | Separate Active Plan inclusion, exact source/quantity procurement coverage and downstream fulfilment evidence; never infer coverage from a shared stable item ID or publication badge | §§4.8, 5.4.6, 7–8, 14.3; U02/U12/U14 | This register §7.6; PLN §4.14; NDS §4.7; REQ drawdown and TPR/TPUB lineage projections | **PLN18-RI-069** — New Need is planned but has no procurement/fulfilment coverage until its own exact downstream evidence exists; original Tender covers only original issued sources/quantities |
| PLN-RI-070 | Agreed refinement | Successor creation or concurrent authorisation can bypass a UI-only restriction | Recheck authoritative scope lock in formation, substitution, saves, submission and activation; serialise activation and Requisition authorisation using the stable-item guard; preserve original allowances and lineage | §§4.8, 5.4.6, 7–8, 14.3; U08/U09/U11 | This register §§7.2, 7.4, 7.6; PLN/REQ services and optimistic-concurrency contracts | **PLN18-RI-070** — Racing authorisation/successor expansion yields no state with a locked item enlarged; rejection is atomic; partial original drawdown and copied IDs do not reset protection |
| PLN-RI-071 | Agreed refinement | Separate additional procurement could be treated as automatic threshold avoidance or APP approval as permission to change an issued Tender | Retain method conditions and anti-splitting assessment; keep published-Tender amendment/cancellation and contract variation in their own lawful procedures; exclude scope expansion through those mechanisms from this MVP | §§4.8, 5.4.6, 7–8, 14.3; U07/U09/U11 | This register §7.6; PLN invariant 25–26; LAW §§2–3, 7; TPUB §8.2 and relevant downstream owners | **PLN18-RI-071** — New item does not automatically qualify for a lower-value method; APP amendment never mutates published package content, simulates an addendum or extends a contract |
| PLN-RI-072 | Agreed refinement | The reported end-to-end absorption defect lacks a named regression and actionable rejection | Add the §7.6 regression suite and PLN_ITEM_SCOPE_LOCKED with exact user copy; retain the separate-item happy path as the permitted outcome | §§4.8, 5.4.6, 7–8, 14.3; U01/U07/U09/U14 | This register §7.6; PLN §§9, 11–12, 14–16; integrated NDS/REQ/TPR/TPUB tests | **PLN18-RI-072** — Published original Tender plus later Need cannot reproduce false absorption; separate new item succeeds; historical source, quantity, drawdown and Tender evidence remain exact |

## 18. Approval effect

The product owner’s prior approvals settle the 72 decisions and the accepted proof-of-concept UX direction. This document folds them into one current, reviewable successor and supplies explicit implementation contracts and a full replacement table. It does not ask implementers to keep contradictory v1.17 paths or treat the old addenda as optional alternatives.

Controlled adoption of v1.18 authorizes implementation of this specification, coordinated owner-document amendments, complete artboard realization and the prescribed verification. It does not certify current law, approve unverified legal constants, mark downstream future facilities available, authorize production deployment, or imply that all detailed artboards were user-tested. The open prerequisites and future facilities remain exactly as listed in §15.

The deliverable is the consolidated Procurement Planning specification, including its full re-implementation change table. The original attachments and historical refinement/UI records remain preserved.
