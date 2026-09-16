# CFG-CHG-002 — Site Configuration and System Setup

| Control | Value |
|---|---|
| Document ID | CFG-CHG-002 |
| Version | 0.10 |
| Date | 12 September 2026 |
| Status | **Approved** |
| Approved on | 12 September 2026 |
| Approval record | Project Owner approval in this review: “Approved”. |
| Predecessor | v0.9, approved 3 September 2026; retained as historical evidence |
| Module / implementation owner | Configuration and Governance / `kentender_core`, with native ERPNext/Frappe records where they exist |
| Change basis | PLN-CHG-001 v1.18; approved LAW-REG-001 v1.1 and SEED-001 v1.3; FU-22 and the agreed cross-document review |
| Standards | KT-STD-001 v1.4 and AUTH-ADR-001 v1.7, the supplied inspected baselines. Later standards versions reported by implementation tooling have not been inspected. |
| Purpose | Complete one site-configuration surface, independent module intake controls, funding catalogue, historically resolvable procurement rules, method/schedule profiles and operational reminders. |
| Approval effect | Supersedes v0.9 in full. Document approval is separate from rule verification, implementation, integration and release evidence. |
| Full change table | §17.2; every predecessor acceptance occurrence is mapped in §14.1. |

## 1. Governing decisions

One KenTender site represents one Procuring Entity. The entity is configured at first run and is never selected as a global context. Use ERPNext Fiscal Year and UOM, the AUTH-owned responsibility model and one System setup page. Administrator or System Manager maintains configuration directly on save; there is no configuration approval workflow, Reference Data Manager or local business-approver registry.

The existing four tabs remain. A fifth tab, **Procurement settings**, contains funding sources, procurement rules, schedule profiles and reminders. Versioned configuration and source-verification evidence do not create Draft/Submitted/Approved configuration states.

LAW v1.1 separates legal source, interpretation and product controls. A saved or approved document, configured route or successful test does not make a legal rule Verified. Missing mandatory applicable configuration blocks the affected positive business action. Optional market-price-index absence is distinct from mandatory reservation readiness.

## 2. Scope and boundaries

| Included here | Owning boundary |
|---|---|
| Site identity, approval-route setting and county applicability | CFG stores configuration; LAW establishes applicability; AUTH resolves business capacity. |
| Fiscal years and independent Needs, departmental-plan and disposal-plan intake flags | CFG owns configuration and command-time availability; each business module defines which operations depend on it. |
| Organisation root and System setup containers | CFG owns records/bootstrap; AUTH owns hierarchy semantics, maintenance commands and responsibility surfaces. |
| Funding source catalogue | CFG identity, enablement and history; BUD owns eligibility, allocation and balances. |
| Regulatory reference versions, verification evidence and date resolution | CFG owns schemas, selection and provenance; consuming modules own business checks and transaction effects. |
| Method conditions, schedule profiles and reminders | Complete governed maintenance and read contracts, without an editable workflow engine. |

Excluded: procurement decisions, candidate entitlement/evaluation, disposal approval-route design, accounting transactions, financial reservations, actual milestone entry, arbitrary policy scripts, electronic government-system integration implementation and multi-entity operation. The required e-procurement operating-model review in LAW v1.1 remains a named production dependency; a setting in this page cannot authorize an independent replacement government platform.

## 3. Constraints, ownership and compatibility

| ID | Requirement |
|---|---|
| CFG10-EC-001 | Retain the existing project fiscal-year contract: 1 July–30 June, generated from a start year. The display FY 2027/28 means 1 July 2027–30 June 2028. This is not overridden to fit a seed. |
| CFG10-EC-002 | Operational timezone in this MVP is Africa/Nairobi. Store instants UTC and display EAT. Business dates remain dates. No alternate timezone is offered in this successor. |
| CFG10-EC-003 | Share ERPNext Fiscal Year, Company and UOM. Preserve accounting/payroll use, native permissions and records. Do not remove native accounting routes or mass-disable unrelated UOMs as a KenTender cleanup. |
| CFG10-EC-004 | Every consuming command uses owner services in its decision transaction; no deep imports or direct writes to another module's tables. |
| CFG10-EC-005 | Exact code/schema mapping must be inspected in the current repository. Logical contract fields here do not assert that native ERPNext has an `enabled` UOM field or a particular precision API. |

Site Company association must resolve to the authoritative configured ERPNext Company before adding a Fiscal Year. Reuse the actual accounting integration setting; never infer a Company merely from a matching display name. If missing or ambiguous, return the exact setup defect and retain native accounting configuration as its owner. The existing Company association contract is an implementation-inspection dependency, not a new KenTender Company catalogue.

## 4. Canonical domain model

### 4.1 Shared types and command evidence

| Type / convention | Required contract |
|---|---|
| ID / version | Opaque owner-generated identity; stable record ID, immutable version ID and mutable concurrency token are distinct. Never parse a business reference for authority. |
| `record_version` | Monotonic integer for mutable configuration roots/settings. Supplied as `expected_version` by writes; compare atomically. |
| Text | Trimmed nonblank where required. Names 2–160 characters unless explicitly different; reasons 20–1,000 characters; source references 1–500; source title/interpretation text 1–2,000. Reject oversized input. |
| Date interval | Inclusive `effective_from`; nullable inclusive `effective_until`; from must not exceed until. Evaluate as site business dates. |
| Instant | UTC ISO instant; server-derived for audit, EAT presentation. An intake closes at the exact instant, including equality. |
| Money / rate / quantity | Decimal strings; Money currency/precision from BUD, Quantity/UOM precision from owner, percentage 0–100 with at most four decimal places. No binary-float tolerances or silent rounding. |
| Evidence | Exact record/version or stored attachment with hash; source locator, edition, provision and provenance. A filename/URL alone is not proof of a retrieved document. |
| Storage marks | A = authoritative mutable field; S = immutable version/evidence; P = derived read projection. Framework audit metadata is reused. |

### 4.2 Site Procuring Entity — Single

| Field | Storage / type | Requiredness and validation |
|---|---|---|
| `pe_name` | A / text | Required official legal name, 2–200 characters. |
| `pe_code` | A / text | Required uppercase code, 3–20 characters, letters/digits/hyphen; first-run only, immutable afterwards. |
| `pe_type` | A / enum | National Government Ministry; State Department; State Corporation; County Government; County Corporation; Constitutional Commission; Public University; Other Public Entity. |
| `ppra_registration` | A / text | Optional, 1–200 if supplied; never proof of current E-GPS registration. |
| `timezone` | A / IANA value | Africa/Nairobi only in this MVP; read-only field in the screen. |
| `statutory_approval_route` | A / enum | Exactly one: Cabinet Secretary, County Executive Committee Member, Board of Directors, Council. No None. |
| `entity_is_county` | A / boolean | Required explicit value; used with actual entity facts and verified applicability rules. |
| `configured_by`, `configured_at` | S / actor, instant | Server-set once at first successful configuration. |
| `record_version` | A / token | Server-managed on each material edit. |
| `root_unit_id`, `accounting_company_id` | P / owner ID | Owner-resolved links; no PE foreign key introduced on transactions. |
| `approval_applicability` | P / result | Verified / Verification required / Configuration conflict, with exact rule/evidence IDs or missing facts. This is not an entity lifecycle. |

First save creates the Single values and one AUTH-compliant root Organisation Unit atomically. Root initial name/code are the entity name/code. A failed root creation rolls back configuration. Later entity renaming does not rewrite historical legal snapshots or silently rename another owner's unit. Stable PE code repair is not exposed; never create an alias or repurpose this site as another entity.

Type consistency is structural before legal applicability: County Government and County Corporation require the county flag; National Government Ministry, State Department and Constitutional Commission reject it. State Corporation is the national category here; use County Corporation for its county counterpart. Public University and Other Public Entity require actual establishment/jurisdiction evidence to resolve county applicability; do not derive it from the label. This matrix is a configuration consistency rule, not a legal finding about every institution.

First run may save a structurally valid entity with legal route applicability pending so administrators can complete setup. Positive procurement governance cannot use an unverified or conflicting route. The chosen route is reconciled through an Approval applicability reference (§4.7); no generic local approval exemption.

### 4.3 Fiscal Year and module intake fields

ERPNext owns `year`, `year_start_date`, `year_end_date`, `disabled` and Company association. Add year 2027 generates `2027-2028`, 1 July 2027–30 June 2028; derive FY 2027/28 for display. Phase Upcoming/Current/Past is a read projection from the server date. No stored current-year toggle or PE/FY wrapper.

| Module key | Open field | Optional close instant | Distinct owning workflow |
|---|---|---|---|
| `needs` | `kentender_needs_submission_open` | `kentender_needs_submission_closes_at` | NDS creation/submission rules, including its stated correction exceptions. |
| `dpp` | `kentender_dpp_submission_open` | `kentender_dpp_submission_closes_at` | PLN initial departmental intake; returned-cohort corrections and accepted-DPP updates follow PLN rules independently. |
| `disposal_plan` | `kentender_disposal_plan_open` | `kentender_disposal_plan_closes_at` | DSP's own intake actions/timing, to be reconciled with LAW v1.1. No Procurement Planning payload fields. |

All flags default false. For each row, add namespaced `kentender_{module_key}_intake_changed_by`, `_changed_at` and `_revision`, server-managed. Replace the old shared `kentender_flag_changed_by/at` projection with these per-module fields; migrate existing evidence with provenance rather than inventing actors. Append `IntakeChange` evidence containing module, target FY, affected previous FY if any, before/after flags and close instants, reason, actor, instant and command identity.

One mutable `IntakeControl` record per module key stores a monotonic control token and provides a unique serialization lock; it is not a window, FY wrapper or business lifecycle. Flags on native Fiscal Years remain authoritative; the control holds no duplicate open-year pointer. All writes acquire this control before touching FY flags. Opening one year atomically closes the prior open year for the same module. Needs, DPP and disposal may each have a different open year.

When opening, `closes_at` is null or strictly after the server instant. It belongs to the selected FY's intake configuration and need not fall between that FY's dates. On explicit/scheduled close, clear the current close field and preserve it in `IntakeChange`. On reaching the instant, effective intake is closed even if the physical flag has not yet been cleaned up. Hourly cleanup records the observed cleanup instant and scheduled effective-close instant separately; never backdate the audit event.

`effective_open = flag AND not FY.disabled AND (closes_at is null OR now < closes_at)`. Re-evaluate after acquiring the module control and before the dependent write. FY disable requires all flags off, no KenTender references and the native accounting validation to pass. Do not manipulate accounting dates to satisfy procurement examples.

### 4.4 Organisation Units, Company and UOM

AUTH v1.7 owns the single-root tree, descendant scope, Active/Inactive unit semantics, generated identifiers and responsibility commands. Use the native Frappe tree inside the existing tab. No reparent/delete controls or HRMS-department authority shortcuts.

`RepairOrganisationRoot` is Administrator-only, idempotent, and recreates only a demonstrably missing root under the AUTH invariants. It must not reparent, delete or silently repair ambiguous existing trees. System Manager has ordinary configuration maintenance but does not gain this exceptional repair authority.

Read selectable UOMs from an adapter over native ERPNext UOM, including the applicable whole-number/precision constraint. The adapter's logical `selectable` projection must map to actual repository/native fields; this document does not require an invented native column. Keep Each, Programme, Set, Lot, Kilogram, Litre, Metre, Square Metre, Cubic Metre and Service Month as the shared fixture choices. Do not globally disable other units used by accounting or existing transactions.

### 4.5 FundingSource

| Field | Storage / type | Rule |
|---|---|---|
| `id` | S / generated ID | Stable identity returned to BUD and other consumers. |
| `funding_source_name` | A / text | Required, 2–160; case/whitespace-normalized uniqueness across enabled and disabled entries. |
| `enabled` | A / boolean | Default true for new entry; disabling prevents new selection, not historical reads. |
| `record_version` | A / token | Optimistic concurrency. |

Create, rename, enable and disable are direct configuration saves with audit. No free-text substitute in consuming records. No delete action. A rename preserves stable ID; previously frozen funding snapshots keep their exact old display name. Read-by-ID returns disabled historical records when authorized; “enabled only” applies to new-selection lists. BUD decides the effect on its own Draft/Active line eligibility; disabling does not rewrite budgets, plans or balances.

### 4.6 RegulatoryReference and immutable versions

Reuse the existing Regulatory Reference concept, not a parallel Planning register. A stable set has generated ID, unique `reference_key`, display name, `reference_kind` and mutable `record_version`. Keys/kinds become immutable after first version. Supported kinds: Method eligibility, Reservation rules, Exclusive preference, Preference margins, Market price index, Approval applicability, Publication obligations. Display names may change with audit; issued snapshots retain their names.

| Version field | Storage / type | Required contract |
|---|---|---|
| `id`, `reference_id`, `version_number` | S / IDs, positive integer | Owner-generated, unique within set. Display version is not a write token. |
| `effective_from`, `effective_until` | S / date interval | Required start, optional end. Independent from FY labels. |
| `applicability_basis` | S / enum | FiscalYearStart, PlanSubmissionDate, PlanApprovalDate, ProceedingAuthorizationDate, InvitationDate or ContractSigningDate. Verified for this rule; never arbitrarily chosen by a consumer. |
| `applicability` | S / typed selector | Entity type set, county applicability All/County/NonCounty, category set where relevant, method/procedure IDs where relevant, currency where values apply. Empty means all only where the schema explicitly permits it. |
| `source_evidence` | S / structured list | Instrument title/ID, edition, provision, source URL and attached document identity/hash when held; exact effective/amendment basis. Pending versions may have gaps exposed as missing fields. |
| `interpretation` | S / text | Required for a usable version; maps source to rule, date basis and exceptions. Never executable code. |
| `supersedes_version_ids` | S / ID list | Exact same-set predecessors for correction/replacement; acyclic and strictly older. Empty for non-overlapping initial coverage. |
| `change_reason` | S / reason | Required for successor/correction; not added to ordinary funding-source saves. |
| `payload_schema_version`, typed rows | S / supported schema, child rows | Valid structural schema; absent mandatory legal values make the version incomplete, not guessed. |
| `created_by`, `created_at` | S / actor, instant | Server evidence. |
| `verification`, `completeness`, `selection_status` | P / result | Derived from append-only verification events, schema/consumer support and interval context. No configuration approval state. |

Every saved version is immutable, even before first use. An unsaved editor is local form state, not a persisted Draft workflow. Corrections use Create new version. This simpler rule guarantees referenced-history protection and removes a race between first use and editing. Verification evidence is appended separately; it cannot mutate a version's legal payload.

`ReferenceVerificationEvent` fields: generated event ID; exact version ID; outcome Pending/Verified/Rejected; reviewer actor; recorded UTC instant; source-check date; exact instrument/edition/provisions and source document hash; effective-date and amendment check; applicability/date-basis explanation; interpretation/evidence reference; unresolved points; required change reason; previous verification event ID. Verified requires complete source/effect/applicability evidence, no unresolved mandatory points and a supported payload. Pending/Rejected records the missing/contradictory point. The latest event at the decision instant is the current status; earlier verification IDs remain in consumer evidence.

Administrator and System Manager may record verification evidence under the existing maintenance authority, including evidence prepared by the responsible legal owner. The recorder is accountable for the stated check; this is not legal correctness created by a checkbox. No new reviewer role or second-person approval is introduced. Approval of LAW v1.1 is not a bulk verification event. Withdrawing confidence appends Pending or Rejected and blocks affected new positive decisions; it does not rewrite historical approvals.

### 4.7 Typed regulatory payloads

Each kind has its own validated rows. Unsupported keys/operators, free-form SQL/expressions and unknown condition codes are rejected. Source applicability is checked before values are consumed.

| Kind / row | Exact governed values and semantics |
|---|---|
| Method eligibility | `method_id`, `procedure_id`, category Goods/Works/Services, currency, nullable minimum/maximum decimal amounts with explicit inclusive booleans, `value_basis` PerRequest/PerItemPerFiscalYear/ApprovedBudgetAllocation, condition rows, required evidence and required authorization role/stage codes. Null bound means SourceNoBound only with verified evidence; otherwise status Missing. Never treat missing as unlimited. |
| Method condition | Stable `condition_code`, readable requirement text, legal reference IDs, input fact code, comparator and typed expected value, evidence type Record/Attachment/OwnerDecision, actor role code where authorization required, check stage Planning/Initiation/Tender/Contract. Supported fact/operator pairs come from the code-owned consumer registry below. |
| Reservation obligation | Stable `obligation_code`, percentage, `denominator_basis` AnnualProcurementBudget/AnnualProcurementValue, eligible planned-designation codes, applicability predicates, county flag, exact overlap policy Independent/MutuallyExclusive/SpecifiedOverlap plus referenced other obligation codes, source references. Each annual target is calculated separately. Actual procurement value cannot be produced from Plan estimates. |
| Exclusive preference | Stable restriction code; category/method/currency; comparator and amount; funding-origin and local-origin condition codes; eligible party classification code; source references. It constrains procurement where applicable; does not award candidate entitlement. |
| Preference margin | Stable scheme code; procedure; decimal margin; origin/shareholding conditions with explicit open/closed endpoints; evaluation basis; source references. Gaps/overlaps are rejected as usable unless an explicit source-supported outcome is recorded. Downstream consumer only. |
| Market price | Native item/category/UOM reference, currency, exact price, observation/publication date, applicable period, publication reference. Optional display dataset; not an entitlement/approval control. |
| Approval applicability | Entity classification/facts, allowed procurement approval route, required governing-instrument evidence and AUTH capacity code, source references. Does not prescribe DSP's separate route or establish a business assignment. |
| Publication obligation | LAW obligation ID, accountable actor role, recipient/channel codes, applicability/date basis, trigger event, due rule (Immediate/CalendarDaysAfter/WorkingDaysAfter/PeriodEndPlusDays), nonnegative days where applicable, period definition, source references and integration/evidence contract code. No outbound adapter credentials or self-issued government-system authorization. |

For Method conditions, minimum supported facts are Category, EstimatedPackageValue, CumulativeItemFiscalYearValue, ApprovedBudgetAllocation, FundingOrigin, EntityCountyStatus and a method-specific OwnerConditionResult. The first three numeric facts use exact owner snapshots. OwnerConditionResult requires a registered method/condition code with a concrete owning validator, input schema, evidence and authorized stage; it cannot be a user-supplied true/false declaration. New legal circumstances require a reviewed code registry addition and tests, not an administrator-authored script. Metadata editing cannot make an unimplemented method supported.

Supported comparators are Equal, NotEqual, In, NotIn, LessThan, LessThanOrEqual, GreaterThan and GreaterThanOrEqual. Numeric comparisons require matching currency/UOM dimensions and exact decimals; set comparisons require an enum-set value; booleans allow Equal/NotEqual only. A row without a supported typed comparison is incomplete, never automatically true. Cross-condition combination is explicit All (every condition required) or Any (one complete supported branch required), stored as ordered groups with no nested arbitrary expression.

Required condition evidence may be NotYetDue for a later stage, clearly labelled; the stage's positive action cannot pass without it when due. Missing known Planning-stage conditions block Planning readiness. CFG returns evaluation inputs and explanations; the owning module performs and records the legal/business check.

### 4.8 Method/procedure support and schedule profiles

The code-owned ProcedureSupport registry identifies `method_id`, `procedure_id`, supported category set, owning app/service, supported condition codes, milestones, and allowed consumer actions. It is read-only in setup. A known catalogue procedure may be Not implemented; administrators may retain a pending profile for it, but no positive business action can use it. An entirely unknown procedure ID is rejected. The UI-only Planning example is presentation fixture text, not an executable procedure ID. A catalogue entry or profile save cannot enable an unsupported proceeding. Return Supported/Not implemented with the exact missing owner contract.

A ScheduleProfile has stable ID/name and immutable numbered versions. Versions carry the common interval, applicability basis/selectors, source/interpretation, supersession and audit fields in §4.6 plus exact linked reference-version IDs. Each profile version has these rows:

| Field | Type / rule |
|---|---|
| `milestone_code`, `sequence`, `applies` | One unique row per supported milestone; ordered invitation, opening, evaluation completion, award approval, notification, signing, completion. Not-applicable rows require the profile's explicit supported procedure basis. |
| `from_milestone`, `to_milestone` | Explicit interval endpoints for each calculated constraint; no implicit meaning inferred from a row label. |
| `counting_rule` | CalendarDays or WorkingDays; count excludes the start date and includes the end date unless a separately implemented, source-verified convention is specified. No unsupported convention fallback. |
| `calendar_version_id` | Required for WorkingDays; owner-governed immutable business-day calendar with weekend definition and holiday dates. Missing calendar blocks calculation; do not assume weekdays alone. |
| `minimum`, `maximum` | Nullable nonnegative integers, explicit bound status VerifiedValue/SourceNoBound/Missing and exact legal-reference IDs. Min must not exceed max when both exist. |
| `default_days` | Nullable nonnegative integer; usable profiles require an explicit value for each calculated interval. It must satisfy verified bounds. |
| `default_basis` | LegalRequirement or PlanningAssumption; legal defaults link exact sources, internal defaults labelled as assumptions. |
| `allows_override` | Boolean; an override still satisfies all bounds/counting rules and the owning module's amendment authority. |
| `estimated_delivery_default_days` | Optional nonnegative calendar-day integer. Null means not configured; never silently zero. Planner's explicit period remains required by PLN. |

Invitation is the anchor. Completion is the source-derived boundary; do not calculate it as merely signing plus profile delivery days. Estimated completion is calculated separately and compared with the boundary. Preserve profile/version and calendar IDs in each reviewed baseline. Later forecasts use the specified owner rules and retain their comparison bases; profiles cannot overwrite actuals.

For WorkingDays, `BusinessDayCalendarVersion` stores immutable ID/name/version, effective interval, weekday exclusions, exceptional holiday dates with source evidence and revision/supersession linkage. Maintenance uses the same direct configuration authority and source-evidence rules; it is opened only when a WorkingDays profile needs it. Calendar interpretation remains legally verified owner work, not a new national-calendar claim.

### 4.9 Reminder settings

One configuration record stores `approaching_milestone_days` (integer 0–365, default 7), `record_version` and framework audit. Unit is Calendar days. This is an operational product setting; seven days is not a statutory procurement deadline. A zero value means notification begins on the milestone date; it does not disable overdue handling. Save applies to subsequent daily evaluations; it does not create a new task, duplicate notices or change historical notification events. PLN owns one evolving reminder per recipient/item/proceeding/milestone and its daily job.

### 4.10 Resolver input, result and history

`ResolveProcurementConfiguration` accepts registered `consumer`, `action`, purpose/reference key, category/method/procedure, currency, entity configuration token, FY ID and owner-validated business fact/evidence IDs. The service resolves dates from those facts using the applicable reference's declared date basis. It never accepts an arbitrary unvalidated client date as authoritative.

For the current submission/approval/authorization action, its date is the server date in the action transaction. A future or historical invitation/signing date comes from the exact owner record/reviewed version. FiscalYearStart comes from ERPNext FY. If the required event/date is not yet known, return MissingBasis with its field and owner; do not substitute today's date or FY start. Initial lookup may return the applicable basis requirements so a Draft can gather the facts.

Result fields: status Resolved/Missing/Ambiguous/Unverified/Incomplete/Unsupported/Conflict/MissingBasis; explanation code and actionable field/owner details; actual applicability date/basis; selected set/version IDs; verification-event IDs; profile/calendar IDs; configuration revision tokens; exact typed payload; required conditions/evidence/stages; and rule-resolution hash over the canonical input/result. An optional reference returns NotPublished separately. The consumer stores exact evidence with the decision, not only a display label.

Historical reads by exact version ID return the immutable payload and the verification event used by the original decision, plus a separate current-verification warning where relevant. They do not recalculate history using current rules. Current positive actions revalidate their applicable configuration and tokens atomically. Submitted content stays frozen; if current mandatory checks cannot pass, allow the owning return/correction path rather than silently changing the reviewed version.

## 5. Save, selection and state-transition rules

| Operation / condition | Required result |
|---|---|
| First-run save | Structurally valid entity + root created atomically; source-applicability gaps are visible for completion, not false legal approval. |
| Entity route/county edit | Save audit and new token; invalidate cached current checks. Existing task capacity/snapshots remain exact; positive decision revalidates compatibility, with owning return/correction on conflict. |
| Open intake | Lock module control, validate token/year/current clock, close prior same-module year, open target, record reason and one correlated evidence set atomically. |
| Change open close time | Same module lock; future/null close value; reason; no change to other modules. |
| Close/expire intake | Effective availability false; no downstream record creation/deletion or rewriting of existing submitted/accepted content. |
| Save reference/profile/calendar version | Validate supported structure, selectors and supersession; append immutable version. Missing legal evidence is shown Pending, not a Draft approval state. |
| Record verification | Append evidence for the exact immutable version; only a fully supported/evidenced version can project Verified. |
| Correct prior rule | New version with reason and exact superseded IDs; old payload/decision pins retained. Never overwrite the effective dates of an old record. |
| Disable funding source | New selection unavailable; stable ID and historical reads retained; no silent financial or Planning mutation. |

**Selection algorithm:** (1) validate authenticated consumer and owner facts; (2) identify exact reference key/kind and matching selectors; (3) obtain the declared applicability date; (4) collect intervals covering that date; (5) within an explicitly declared supersession chain, discard a matching ancestor only where the matching successor covers that date; (6) require exactly one remaining candidate; (7) require usable payload, applicable support and Verified evidence for mandatory production use. A more recent creation timestamp, larger version number or narrower-looking selector is never an implicit priority rule.

An unrelated overlap is rejected on save when detectable; resolution still returns Ambiguous if conflicting legacy/configuration data exists. An intentional correcting overlap requires explicit predecessor linkage and a preview identifying affected date ranges. Outside the successor's interval, the old version may still resolve. A gap returns Missing for the affected date, not the latest version. A new Pending successor that explicitly replaces a currently selected interval blocks affected positive use until verified; show this impact before save, never silently fall back to the old verified payload.

Backdated source corrections require their recorded source-effective date, current recorded-at instant, reason and supersession link. Historical decisions retain their pins and may be flagged for owner review; CFG cannot retroactively approve or reverse business records. No immutable version is physically deleted. Scalar save, interval conflict checks, reference selection and positive decisions must serialize against the relevant roots/control tokens so configuration cannot change between validation and commit.

Mandatory reservation target missing or shortfall is blocking under the consuming PLN rule. An absent optional price index returns NotPublished with no reservation waiver. A reference status alone does not perform the BUD annual denominator calculation or downstream candidate evaluation.

## 6. Actors, permissions and segregation

| Actor | Allowed work | Limits |
|---|---|---|
| Administrator | All ordinary configuration maintenance, source-verification evidence recording, and governed missing-root repair | No business procurement decision without the applicable AUTH assignment and domain checks. |
| System Manager | Entity, FY/intake, funding, rules/profiles/calendars/reminders and source-verification evidence; AUTH-permitted unit/assignment maintenance | Missing-root repair remains Administrator-only; no local grant of statutory capacity. |
| Business actors / Auditor | Owner-authorized configuration values/evidence through their business record, review pack or historical read | No setup mutation or full setup page merely because a module consumes a rule. |
| Authenticated system service | Registered read/decision validation; scheduled expiry under the fixed service contract | No arbitrary rule edits or self-asserted verification. |

Setup authorization resolves before page content renders. Unauthorized routes show the inline Forbidden state and retain correct route/navigation selection. Do not render protected tabs/data and then hide them. Configuration maintenance authority is checked on every API command and native record write; a business task never grants it.

No configuration approval chain, AO sign-off, independent legal-review role or mandatory second operator is introduced. Verification recording is an audited assertion backed by exact evidence under the same maintenance authority. It cannot be a generic checkbox or a bulk effect of document approval.

## 7. Service and command contracts

### 7.1 Common envelope

All mutations require authenticated actor, expected root/control token (except first insert), idempotency key and typed payload. Same key/same canonical payload returns original result; same key/different payload returns CFG_IDEMPOTENCY_CONFLICT. Return exact affected IDs, new tokens, evidence IDs and next permitted actions. Failure has no partial effect. Services reject unknown keys, unsupported schemas and any attempt to set server audit/state fields.

| Command | Payload beyond common envelope | Required result / authority |
|---|---|---|
| ConfigureProcuringEntity | Name, code, type, registration, timezone, statutory route, county boolean | Entity/root atomic; Admin or System Manager. Missing route and type/county conflict rejected. |
| UpdateProcuringEntity | Changed editable fields; entity token | Code prohibited; route/county rechecked and current decisions invalidated by token. |
| AddFiscalYear | Start year, idempotency key | Native year generated and configured Company attached; unique/native validation enforced. |
| SetFiscalYearDisabled | FY ID, disabled boolean, FY token | Exact KenTender/native blockers; no shared-record destruction. |
| OpenNeedsSubmission / CloseNeedsSubmission | FY ID; optional close instant for Open; reason; intake-control token | Names retained; internally use `needs` control and corresponding flags. |
| OpenDepartmentalPlanIntake / CloseDepartmentalPlanIntake | FY ID; optional close instant for Open; reason; `dpp` control token | Same atomic semantics; no source-coverage decisions in CFG. |
| OpenDisposalPlanIntake / CloseDisposalPlanIntake | FY ID; optional close instant for Open; reason; `disposal_plan` control token | Same configuration pattern; DSP action applicability/timing remains its own rule. |
| UpdateIntakeCloseInstant | Registered module key, open FY ID, new future/null instant, reason, control token | Changes only that open control; cannot silently move the open year. |
| CloseExpiredIntakes | System service, current server instant | Idempotent per observed expiry; same per-module lock; exact effective and cleanup instants. |
| RepairOrganisationRoot | Idempotency key | Administrator-only; existing valid root is no-op, ambiguity fails. |
| CreateFundingSource | Name, enabled boolean | Unique stable identity; no approval/reason field. |
| UpdateFundingSource | ID, name and/or enabled, token | Audited rename/enable/disable; old snapshots preserved. |
| CreateRegulatoryReference | Unique key, name, kind | Empty stable set, no legal eligibility until a usable version resolves. |
| RenameRegulatoryReference | Set ID, new display name, token | Audit name only; key/kind and frozen consumer names remain unchanged. |
| SaveRegulatoryReferenceVersion | Set ID/token, §4.6 fields, typed payload | New immutable numbered version after schema/overlap/supersession checks; Pending until adequate verification evidence. |
| RecordReferenceVerification | Exact version ID, expected prior verification-event ID, complete §4.6 evidence | Append verified/pending/rejected event; no legal payload mutation. |
| SaveScheduleProfileVersion | New/existing profile identity, parent token, common version fields and §4.8 rows | Immutable version; method/consumer/counting/bound requirements validated. |
| SaveBusinessDayCalendarVersion | New/existing calendar identity, token, date interval, weekend/holiday rows with evidence, supersession | Immutable calendar; referenced source rules verified under the same evidence contract. |
| UpdateReminderSettings | Integer approaching days, token | Save scalar setting; no downstream notification creation. |

The version/verification services share an explicit target kind Reference/ScheduleProfile/BusinessDayCalendar where applicable; reference/profile/calendar IDs cannot be interchanged. AUTH supplies existing Organisation Unit and responsibility commands. No alias to the retired context/window services is added.

### 7.2 Reads, previews and decision validation

| Service | Input | Exact response / purpose |
|---|---|---|
| GetSiteConfiguration | Authenticated request | Safe entity identity/timezone, root presence, FY/intake projections and configuration tokens; setup-only maintenance details require setup authority. |
| ListFiscalYears | Authorized filters, paging | Dates/phase; each module's configured and effective intake, close instant/control token; reference blockers only where authorized. |
| PreviewFiscalYear | Start year | Generated name/dates/Company and duplicate/setup errors; no writes. |
| GetIntakeAvailability | Registered module key, FY ID, authenticated consumer/action | Effective-open, actual close instant, reason code, control token; consumer determines whether its action requires initial intake. |
| ValidateIntakeForCommand | Same plus owner action transaction | Acquire module lock; validate final current server clock and relevant token before dependent write; no browser-only check. |
| ListFundingSources / GetFundingSource | Selection list filters / exact ID | Enabled-only selection list; exact-ID historical read includes disabled flag and current name. |
| ListSelectableUOMs | Search/paging or exact native ID | Owner-mapped selectable UOM and precision/whole-number constraints; no parallel unit data. |
| ListRegulatoryReferences / GetReferenceVersion | Kind/date/status filters / exact version ID | Sets, versions, effective scope, immutable payload, source/verification evidence and usage summary. |
| PreviewConfigurationVersion | Proposed version and owner-valid example context | Schema/completeness defects, overlaps/gaps, supersession effects and selection impact; no persisted Draft or approval. |
| ResolveProcurementConfiguration | §4.10 context | Exact chosen version/status, date basis, conditions, evidence and revision tokens. |
| ValidateProcurementConfigurationForDecision | Same context plus expected resolution hash/version/evidence IDs within owner transaction | Serialized current check; matching decision basis or explicit stale/unverified/conflict error. No business record creation. |
| ListProcedureSupport / GetScheduleProfile | Method/category/action / exact ID or applicability context | Code-owned support and exact immutable profile/calendar; no Open Tender fallback. |
| GetBusinessDayCalendar | Exact calendar/version ID, authorized consumer | Immutable weekend/holiday/source fields, verification and history; selection uses the same declared applicability contract. |
| GetReminderSettings | Authorized module read | Threshold, unit Calendar days and token. |

Business-role scope continues to be enforced by the consumer; receiving configuration does not authorize access to a Plan, Budget or Requisition. CFG does not lock another app's business tables directly. Cross-module transaction ordering must be established with BUD/PLN/REQ to avoid deadlocks and tested for configuration changes concurrent with decisions.

## 8. Error and readiness contract

| Code | Exact user-facing message |
|---|---|
| CFG_PE_NOT_CONFIGURED | Configure this site's procuring entity before using KenTender. |
| CFG_PE_ALREADY_CONFIGURED | This site already has a procuring entity. |
| CFG_PE_CODE_IMMUTABLE | The entity code cannot be changed after configuration. |
| CFG_APPROVAL_ROUTE_REQUIRED | Select the authority that approves this entity's Annual Procurement Plan. |
| CFG_ENTITY_APPLICABILITY_CONFLICT | County applicability does not match the entity details. Review the configuration. |
| CFG_APPROVAL_APPLICABILITY_UNVERIFIED | The selected approval route needs verified applicability evidence before Plan approval can proceed. |
| CFG_TIMEZONE_UNSUPPORTED | This release uses Africa/Nairobi as the operational timezone. |
| CFG_ACCOUNTING_COMPANY_UNRESOLVED | Configure the site's accounting Company before adding a financial year. |
| CFG_ROOT_UNIT_MISSING | The root organisation unit is missing. Ask Administrator to run the governed repair. |
| CFG_ROOT_UNIT_CONFLICT | The organisation structure cannot be repaired automatically. Review the listed conflicting records. |
| CFG_FY_ALREADY_EXISTS | This financial year already exists. |
| CFG_FY_DATES_INVALID | Financial-year dates must run from 1 July to 30 June. |
| CFG_FY_IN_USE | This financial year cannot be disabled while the listed records or intake controls use it. |
| CFG_INTAKE_CLOSE_INSTANT_INVALID | The closing time must be later than the current server time. |
| CFG_INTAKE_NOT_OPEN | {Intake label} is not open for this financial year. |
| CFG_INTAKE_EXPIRED | {Intake label} closed at {displayed close instant}. |
| CFG_FUNDING_SOURCE_DUPLICATE | A funding source with this name already exists. |
| CFG_FUNDING_SOURCE_DISABLED | This funding source is unavailable for new selection. |
| CFG_REFERENCE_MISSING | No applicable {reference name} is configured for the required date. |
| CFG_REFERENCE_AMBIGUOUS | More than one applicable {reference name} exists. Review the overlapping versions. |
| CFG_REFERENCE_UNVERIFIED | {Reference name} needs source verification before this action can proceed. |
| CFG_REFERENCE_INCOMPLETE | Complete the listed fields in {reference name} before using it for this action. |
| CFG_REFERENCE_IMMUTABLE | This version is read-only. Create a new version to change it. |
| CFG_APPLICABILITY_BASIS_MISSING | The {basis label} needed to select this rule is not available. |
| CFG_SCHEMA_UNSUPPORTED | This rule uses a condition or schema that this release does not support. |
| CFG_PROCEDURE_UNSUPPORTED | This procurement procedure is not implemented in this release. |
| CFG_SCHEDULE_PROFILE_MISSING | Configure a complete applicable schedule profile before Plan submission. |
| CFG_CALENDAR_REQUIRED | Select a verified business-day calendar for this working-day interval. |
| CFG_VERIFICATION_EVIDENCE_REQUIRED | Complete the source, applicability and interpretation evidence before recording verification. |
| CFG_SUPERSESSION_INVALID | Select valid earlier versions and review the affected effective dates. |
| CFG_CONFIGURATION_CHANGED | Configuration changed after this review. Refresh the checks before continuing. |
| CFG_AUTHORITY_REQUIRED | You are not authorised to change site configuration. |
| CFG_VERSION_CONFLICT | This record changed after you opened it. Refresh and review the latest version. |
| CFG_IDEMPOTENCY_CONFLICT | This request identifier was already used for different changes. |

Interpolation uses server-resolved safe labels; it is not placeholder product copy. Intake labels are Needs submission, Departmental-plan intake and Disposal-plan intake. Optional index absence is an ordinary **Not published** projection, not CFG_REFERENCE_MISSING for a mandatory control. Return field-specific validation details with the error; never expose protected record identities in a denied response. Missing legal applicability and implementation support remain visibly distinct.

## 9. UI architecture and routes

One Vue 3 surface in the existing Frappe Desk shell at `/app/system-setup`. Use AUTH/KT-STD navigation, authorization and component rules. No new SPA shell or proof-of-concept stack.

| Anchor | Tab / content |
|---|---|
| #procuring-entity | Procuring entity |
| #fiscal-years | Fiscal years |
| #organisation-structure | Organisation structure — AUTH v1.7's native tree and details |
| #users-and-responsibilities | Users and responsibilities — AUTH v1.7 |
| #procurement-settings | Procurement settings; sections Funding sources, Procurement rules, Schedule profiles, Reminders |

A local section/record parameter within Procurement settings restores the selected list/detail/version on refresh and Back. Use `#procurement-settings/{section}/{id}` and optional `/versions/{version_id}` for exact version detail; sections are funding-sources, procurement-rules, schedule-profiles and reminders. Calendar editing opens from a WorkingDays profile through `/calendars/{id}` inside this tab; it is not a sixth tab.

Default is the first incomplete structural setup tab; once entity/root exist, honor the requested tab, otherwise entity. Incomplete regulatory verification is shown in the affected rule/profile, not a forced wizard that prevents other setup work. First run disables the other four tabs. Missing root leaves entity/FY/procurement settings accessible but disables responsibilities and shows the AUTH repair state in Organisation structure.

Register one mount in the shared surface registries, preserve authorized native ERPNext access, and remove superseded KenTender configuration navigation without deleting native accounting routes. Back returns to Configuration and Governance. Maintain exact route/view alignment for forbidden direct loads.

## 10. Closed UI specification and artboard inventory

### 10.1 Shared presentation and fixture provenance

Supply this section with KT-STD v1.4's shared shell/design inputs; AUTH v1.7 supplies its two complete owned tabs. These are specifications to render, not a claim that artboards have already been tested. Use 1440 × 1024 desktop artboards and the existing approved typography/spacing/components. At narrow widths keep labels readable and place wide data in a labelled scroll region; do not truncate legal evidence silently.

Page eyebrow **CONFIGURATION AND GOVERNANCE**; title **System setup**; description **Configure this site's identity, financial years, responsibilities and procurement settings.** No page-header action. Five tabs in §9 order. Local section headings own their relevant actions; no count cards, approval buttons, Draft badges, PE switcher or generic all-settings form.

Default actor Administrator, `administrator@moh.example.test`; fixture clock 24 November 2026, 09:15 EAT. Entity Ministry of Health, PE-MOH, National Government Ministry, Africa/Nairobi, PPRA/PE/2019/0114, Cabinet Secretary, County entity unchecked. Setup recorded 29 June 2026, 10:10 EAT. These are shared test identities, not real registration proof.

Procurement-rule examples below are explicitly **Production verification pending**. Their dates/values demonstrate fields only, not legally verified configuration or a valid integrated approval chain. Empty source attachments render as **Not attached**, with no download link. SEED v1.3's approved integrated READY design still needs its exact configuration/provider prerequisites and date reconciliation.

### 10.2 C01 / CFG-DES-01–02 — Entity, configured and first run

Heading **Procuring entity**; text **This site represents one procuring entity. The code is fixed once the site is configured.**

| Label | Configured value | Control / first-run difference |
|---|---|---|
| Entity code | PE-MOH | Read-only after configuration; first run input. |
| Entity name | Ministry of Health | Text input. |
| Entity type | National Government Ministry | Select with all eight §4.2 options. |
| PPRA registration | PPRA/PE/2019/0114 | Optional text; blank first-run variant. |
| Timezone | Africa/Nairobi | Read-only. |
| Statutory approval route | Cabinet Secretary | Required select with all four options; helper: Select the authority that approves this entity's Annual Procurement Plan. |
| County entity | Unchecked | Checkbox, explicit validation against entity facts. |

Read-only configuration evidence uses separate labels Configured by, Configured at, Root organisation unit and Root unit code. Route evidence panel: **Approval applicability** / **Verification required** / **Complete the applicable approval-route reference in Procurement settings before Plan approval.** Link **View procurement rules** after configuration. This panel does not claim setup approval.

Configured footer **Save changes**, disabled until modified. First-run heading **Configure this site** and text **Enter the entity details to create this site's configuration and root organisation unit.** Footer **Configure site**; other four tabs disabled. No skip, cancel, entity list, deletion or approval step. Omitted route displays CFG_APPROVAL_ROUTE_REQUIRED at that control. Conflict variant: County Government selected with County entity unchecked displays the exact §8 conflict message; no silent checkbox correction.

### 10.3 C02 / CFG-DES-03–06 — Fiscal years and intake

Heading **Financial years**; description **Financial years are shared with accounting. Each intake can be open for one year at a time.** Action **Add financial year**.

| Financial year | Period | Phase | Needs intake | Departmental-plan intake | Action |
|---|---|---|---|---|---|
| FY 2027/28 | 1 Jul 2027 – 30 Jun 2028 | Upcoming | Open until 25 Nov 2026, 23:59 EAT | Open until 30 Nov 2026, 23:59 EAT | Manage intake |
| FY 2026/27 | 1 Jul 2026 – 30 Jun 2027 | Current | Closed | Closed | Manage intake |

Footer **2 financial years**; link **Manage units of measure** with text **Units are shared with accounting and maintained in the standard units list.** Do not add a Company selector, date editor or current-year switch.

**Manage intake** opens the selected year's focused panel, with year/period read-only and three rows: Needs submission, Departmental-plan intake, Disposal-plan intake. Columns Intake, Status, Closes at, Action. Disposal default Closed. The panel also shows Financial year enabled Yes and a footer action **Disable financial year**, separate from intake actions. Its confirmation lists exact references/open flags/native blockers; when blocked the confirmation action is unavailable and the reason remains visible. Unreferenced/all-closed variant offers Cancel / Disable financial year. Disabled years are available through **Include disabled years**; their detail shows **Enable financial year**, invoking the native re-enable validation without inventing a new lifecycle. Each open row has **Change closing time** and its exact **Close…** action; each closed row its exact **Open…** action. This exposes disposal without cramming a third intake column into the main table or implying its business procedure is verified.

**Add financial year:** 520 px dialog, Start year **2028** numeric input; server-preview fields Financial year **FY 2028/29**, Period **1 Jul 2028 – 30 Jun 2029**, separate labels. Buttons Cancel / Add financial year. Duplicate/native Company defects appear inline; dates never editable.

| Dialog | Exact content / fixture |
|---|---|
| Open needs submission | Text: Departments can use the initial needs intake for FY 2027/28 under the Needs workflow rules. Close automatically on: 25 Nov 2026, 23:59. Reason: Annual needs call issued under circular MOH/PROC/2026/07. Buttons Cancel / Open needs submission. |
| Close needs submission | Text: Initial needs intake will close. Existing records remain available under the Needs workflow rules. Reason: Needs call closed on the date announced in circular MOH/PROC/2026/07. Buttons Cancel / Close needs submission. |
| Open departmental-plan intake | FY 2027/28 read-only. Close automatically on: 30 Nov 2026, 23:59. Reason: Annual departmental procurement planning call. Buttons Cancel / Open departmental-plan intake. |
| Close departmental-plan intake | Text: Existing submissions and governed updates remain available under their Planning rules. Reason: The announced departmental submission period has ended. Buttons Cancel / Close departmental-plan intake. |
| Open disposal-plan intake | Text: Disposal-plan intake uses its separately configured annual process. Close automatically on: blank. Reason: Disposal intake opened for the declared fixture scenario. Buttons Cancel / Open disposal-plan intake. The value is UI-only; no assertion of correct statutory timing. |
| Close disposal-plan intake | Text: Initial disposal-plan intake will close. Existing records remain available under the Disposal workflow rules. Reason: The announced disposal intake period has ended. Buttons Cancel / Close disposal-plan intake. |
| Change closing time | Intake and year read-only; Close automatically on prefilled with current instant; Reason: The announced intake deadline has been extended. Buttons Cancel / Save closing time. |

Optional close helper: **Leave blank to keep intake open until you close it.** The instant is shown in EAT and sent as exact UTC, with no rounding to end-of-day. Replacement variant for DPP: heading **This will close FY 2026/27**; text **Departmental-plan intake can be open for one financial year at a time. The previous year's intake will close when you continue.** Show only if that same module has another open year. Expired-at-submit variant shows the exact server close instant and retains the user's reason; no scheduler wait.

### 10.4 C03-A — Funding sources

Procurement settings has four section links in order Funding sources, Procurement rules, Schedule profiles, Reminders. Funding sources heading; description **Maintain the funding sources used by Budget and downstream records.** Action **Add funding source**.

| Name | Enabled | Action |
|---|---|---|
| Government of Kenya | Yes | Edit |
| Development partner | Yes | Edit |
| Appropriation in Aid | Yes | Edit |

Editor fields Funding source name and Enabled only. Add form defaults enabled, footer Cancel / Add funding source. Existing editor footer Cancel / Save changes; no approval or unrelated reason. Disable helper **Unavailable for new selection; existing records retain their funding history.** A disabled row remains visible with Enabled No and Edit; an exact historical detail remains resolvable. Duplicate variant uses §8 message at the name field. Empty: **No funding sources yet** / **Add the sources used by this site's procurement budgets.** / Add funding source.

### 10.5 C03-B — Procurement rules list and version detail

Heading **Procurement rules**; text **Maintain rule versions, legal sources and applicability evidence.** Primary **Add reference set**; each set detail provides **Add reference version**. Filter Reference kind, Search, Verification; default All. List columns Reference set, Applies from, Applies until, Version, Source verification, Action.

Rows: Method eligibility / 1 Jul 2027 / 30 Jun 2028 / 1 / Production verification pending / View; Reservation rules / same interval/version/status / View. Empty field is an em dash with a separate completeness explanation where relevant, never a false unlimited value. An optional Market price index empty result says **Not published** with text **No optional price index is available for this period.**

Set detail includes **Edit reference name**, opening Reference name with Cancel / Save changes; key and kind are read-only after first version. New set dialog: Reference name **Method eligibility**, Reference key **METHOD-ELIGIBILITY**, Reference kind **Method eligibility**; Cancel / Add reference set. Version detail shows Reference set, Version, Effective from/until, Applicability basis, Entity applicability, Category, Method/procedure, Currency, Source instrument, Edition, Provision, Source document, Interpretation, Source verification, Completeness. Each is separately labelled, not packed into a dot-separated metadata line.

CONFIG source values: Source instrument **Public Procurement and Asset Disposal Regulations — source verification pending**; Edition **Verification required**; Provision **Verification required**; Source document **Not attached**; Interpretation **Applicability review is outstanding.**; Verification **Production verification pending**. Do not present these placeholders as a usable source-evidence payload.

Saved detail is read-only with **Create new version**, **Record source verification** and **View usage and history**. New-version form starts with copied values, exact superseded version selected and Reason **Correct the rule's effective scope using the cited source.**; footer Cancel / Save reference version. Before save, show the preview's affected interval and consumers, including **Affected actions will be blocked until this replacement is verified** when applicable. This is explanatory feedback, not approval.

### 10.6 C03-C — Typed rule editors

Render only the selected kind's fields from §4.7, with explicit labels; never a JSON text editor. Show a completeness list above the footer. Every row supports Add row/Remove row before save; saved rows are immutable.

| Kind | Exact field labels / CONFIG example |
|---|---|
| Method eligibility | Method Open Tender; Procedure Planning example; Category Goods; Currency KES; Value basis Approved budget allocation; Minimum/Maximum status Missing; Amount blank; Inclusive controls available only with a value; Required conditions list **Required conditions not yet completed**. |
| Method condition | Condition; Requirement; Checked at; Input fact; Comparison; Expected value; Required evidence; Required authority; Source reference. Selectors come from supported registry. An unavailable condition says **This condition needs an implemented owner check.** |
| Reservation rules | Obligation code **ANNUAL-TARGET-EXAMPLE**; Target **30%**; Denominator **Annual procurement budget**; Eligible planned designation **Youth** in this isolated editor example; County applicability All; Overlap policy **Verification required**. Text **Illustrative values; production verification pending.** Saving incomplete evidence does not verify it. |
| Exclusive preference | Restriction code; Category; Method; Currency; Comparison; Amount; Funding-origin condition; Local-origin condition; Eligible party classification; Source reference. CONFIG Amount blank; **Required conditions not yet completed**. |
| Preference margins | Scheme; Procedure; Margin; Origin condition; Shareholding from/to; Lower/upper inclusive; Evaluation basis; Source reference. CONFIG Margin blank; **Used by the evaluation owner; no Planning entitlement calculation.** |
| Market price index | Item; Category; Unit; Currency; Price; Observation date; Publication date; Publication reference; Applies from/until. CONFIG has no rows and Not published. |
| Approval applicability | Entity type; County applicability; Required entity evidence; Procurement approval route; AUTH capacity; Source reference. CONFIG National Government Ministry / NonCounty / Verification required / Cabinet Secretary / configured statutory capacity. |
| Publication obligations | Obligation; Accountable actor; Recipient/channel; Trigger; Due rule; Days; Reporting period; Integration/evidence contract; Source reference. CONFIG LAW-OB-009 with **Operating-model verification required**. No credential fields or “integration authorized” toggle. |

A percentage/amount example is never silently seeded into production. The fully verified visual variant, if required for a later design session, must supply an explicit exact evidence fixture; this section does not invent one.

### 10.7 C03-D — Source verification and history

**Record source verification** opens a full-width detail form with exact target reference/version read-only. Fields Outcome (Pending, Verified, Rejected); Source check date; Instrument and edition; Provisions; Source document; Effective/amendment basis; Applicability and date-basis explanation; Interpretation evidence; Unresolved points; Reason. Prefilled CONFIG: Outcome Pending, Source check date 12 Sep 2026, Unresolved points **The applicable amended source and interpretation have not been established.**, Reason **Record the remaining verification work for this reference version.** Other missing source fields remain blank with requiredness reflecting the selected outcome. Footer Cancel / Record verification. Verified validates all required evidence; no tick box declaring correctness.

History table columns Version, Effective period, Recorded at, Recorded by, Supersedes, Verification, Action. Verification history is a separate table Outcome, Recorded at, Recorded by, Evidence, Reason. Historical usage table Consumer, Record reference, Exact version, Decision date, Action. The evidence view labels **Verification at decision** separately from **Current verification**. A rejected-current variant says **New affected decisions are blocked; historical evidence is retained.** History does not provide a restore-overwrite button.

### 10.8 C04 — Schedule profiles and calendars

List heading **Schedule profiles**; description **Define supported procedure intervals and their legal and operational bases.** Button **Add schedule profile**. Row Open Tender — goods / Open Tender / Planning example / Version 1 / 1 Jul 2027–30 Jun 2028 / Production verification pending / View. Support column or detail field shows **Not implemented** for an unsupported procedure; do not imply that this illustrative procedure can authorize procurement.

Detail labels Name **Open Tender — goods**, Method **Open Tender**, Procedure **Planning example**, Category **Goods**, Version **1**, Effective from **1 Jul 2027**, Effective until **30 Jun 2028**. Applicability basis **Invitation date — verification required**. This is UI-only pending evidence. Seven-row table:

| Milestone | Sequence | Applies | Counting rule | Minimum | Maximum | Default | Basis |
|---|---:|---|---|---|---|---:|---|
| Invitation or advertisement | 1 | Yes | Anchor date | Not applicable | Not applicable | — | Planner anchor |
| Bid opening | 2 | Yes | Calendar days | Verification required | Verification required | 21 | Illustrative profile |
| Evaluation completion | 3 | Yes | Calendar days | Verification required | Verification required | 30 | Illustrative profile |
| Tender award approval | 4 | Yes | Calendar days | Verification required | Verification required | 5 | Planning assumption |
| Notification of award | 5 | Yes | Calendar days | Verification required | Verification required | 2 | Planning assumption |
| Contract signing | 6 | Yes | Calendar days | Verification required | Verification required | 14 | Illustrative profile |
| Delivery or implementation completion | 7 | Yes | Source boundary | Not applicable | Not applicable | — | Earliest source required-by date |

Row detail exposes From milestone, To milestone, Counting convention, Legal reference, Bound status, Bound value and Inclusive/override details where defined. Estimated delivery period default **Not set**; notice **This profile cannot support Plan submission until its required rules and sources are complete.** New-version footer Save schedule profile; existing version Create new version / Record source verification. No approval action.

WorkingDays variant exposes **Business-day calendar** selector and **View calendar**. Missing calendar uses CFG_CALENDAR_REQUIRED. Calendar editor fields Calendar name, Effective from/until, Weekend days, Holiday date, Holiday name, Source evidence, Supersedes, Reason; saved version is read-only. UI-only example weekend Saturday/Sunday, no holiday rows and **Production verification pending**; it cannot satisfy WorkingDays readiness. Do not infer verified Kenyan holiday coverage from an empty list.

### 10.9 Reminders

Heading **Reminders**. Field **Approaching milestone threshold**, value **7**, numeric integer, unit **Calendar days**. Helper **Operational reminder period; not a statutory procurement deadline.** Footer Save changes. Range error **Enter a whole number from 0 to 365.** No edit to business deadlines or daily notification history.

### 10.10 Common states, failures and ownership tabs

| State | Exact heading / text | Action |
|---|---|---|
| Loading | Loading System setup…; approved skeleton, no stale success content. | None |
| Forbidden | You do not have access to System setup. / This area needs Administrator or System Manager access. Ask your KenTender administrator to grant it. | None |
| Load error | System setup could not be loaded. / Try again. If the problem continues, contact support. | Try again |
| Empty FY | No financial years yet. / Add the first financial year for this site. | Add financial year |
| Empty rules | No procurement rules yet. / Add the reference sets needed by the supported procurement procedures. | Add reference set |
| Empty profiles | No schedule profiles yet. / Add a profile for a supported procurement procedure. | Add schedule profile |
| Stale form | This record changed after you opened it. Refresh and review the latest version. | Refresh; preserve unsaved values for explicit review, never auto-overwrite. |
| Overlap/gap | Exact §8 error and affected version/date details. | Review versions |
| Source incomplete | Production verification pending. / Complete the listed source and applicability evidence. | Record source verification |
| Read-only version | This version is read-only. Create a new version to change it. | Create new version |
| Missing root | AUTH v1.7 repair composition, Admin repair action only; System Manager sees the same problem and escalation text. | Repair organisation root for Admin |

Organisation structure and Users and responsibilities retain AUTH v1.7's complete layouts and commands. Only the shared five-tab shell/header changes. Supply those owned artboards alongside this section; do not ask the designer to infer assignment/scope rules from the CFG tables.

## 11. Functional interaction and accessibility

Authorization precedes content, counts and tabs. Restore route/hash/detail focus on Back, refresh and browser navigation without duplicate mounts. Dialog Cancel returns focus to its trigger; Save retains location and shows the changed row/version. Failed writes retain inputs and move focus to the first actionable error. Required fields have persistent labels; disabled controls explain their condition. No state is conveyed by colour alone.

Entity save and FY server preview validate in place. Intake panels use the current control token; a changed other-year intake invalidates a stale open request. The command rechecks the clock even if its preview was valid. Closing initial intake never makes accepted DPPs disappear or blocks the independently permitted update route by a generic flag check.

Rule editors show only supported kind-specific controls. Preview computation is server-authoritative; local presentation can update quickly but cannot declare final readiness. New immutable version appears in history on successful save; actual method/legal readiness requires the exact verification/support result. Selecting Verified exposes the full evidence requirements, with no hidden auto-completion.

Tables use distinct labelled reference/version/date fields; long legal explanations remain readable in a detail view. Shared sticky footers must not cover the final form field or table row. Focus, keyboard navigation, error announcements, 200% zoom and narrow-screen overflow require browser evidence. Full artboard rendering/user validation remains implementation work; completeness of this specification alone is not usability proof.

## 12. Audit and historical integrity

Every mutation records actor, target, command, expected/resulting token, exact payload/result identity, idempotency key, UTC recorded instant, outcome and material before/after facts; reasons only where specified. A replay returns the first successful evidence and creates no duplicate semantic event. Failed writes leave no partial entity/root, intake swap or version/verification result.

Immutable rule/profile/calendar versions, verification events and consumer decision pins survive all corrections. Current source-confidence withdrawal is separately visible from the earlier verification used at a decision. Entity/funding renames do not rewrite frozen legal documents. Scheduled expiry records both its intended close instant and actual cleanup instant. No administrator action creates approval evidence in another module.

Current decisions must serialize configuration validation through the decision transaction. A verification withdrawal/route change racing with a decision yields either the earlier valid serialized decision with its evidence, or a blocked/retry result; never a decision claiming evidence from a different configuration snapshot. Define root-lock order consistently in the affected integration pack.

## 13. Seed and fixture reconciliation

Use shared AUTH/KT-STD identities, ERPNext Company Ministry of Health, two native years FY 2026/27 and FY 2027/28, and the existing single PE/root. PE configured 29 June 2026, 10:10 EAT. Seed authority and business state through owning commands under an isolated controlled clock. No direct governed-state insertion.

At the 24 November 2026 visual fixture instant, Needs intake for FY 2027/28 closes 25 November 2026 at 23:59 EAT; DPP initial intake closes 30 November 2026 at 23:59 EAT; disposal Closed. These advance-year close instants are valid configuration and do not change the FY's July–June dates. Dispose timing examples remain separate pending the DSP owner amendment.

Seed Government of Kenya, Development partner and Appropriation in Aid funding records by stable owner IDs; keep the approved shared UOM choices selectable without disabling unrelated shared units. Calendar/profile examples and historical numeric thresholds remain Production verification pending. The approved SEED v1.3 test provenance label does not map to Verified production configuration.

**Concrete cross-document date conflict:** FY 2027/28 begins 1 July 2027. The shared laptop procurement example has invitation 15 May 2027 and bid opening 5 June 2027; infrastructure has invitation 1 May 2027 and opening 22 May 2027. These dates precede the configured FY. The supplier/profile examples also start rule applicability on 1 July 2027, so an InvitationDate resolver cannot select those versions for the May dates. Advance departmental planning in November 2026 is a different fact and does not automatically authorize pre-FY procurement proceedings.

Retain this as CFG-XD-001: PLN/SEED/REQ/TPR/LAW owners must reconcile the scenario dates, period assignment and any legally supported pre-FY procedure before claiming an integrated positive run. Do not silently move dates into 2028, relabel FY 2026/27, backdate reference coverage or waive date guards. Approved SEED v1.3 already retains actual FY-bound reconciliation as an execution dependency; this document identifies its precise conflicting values.

Seed acceptance also requires Grace's real two-OU assignments, Julia/Peter's approved authority windows, explicit infrastructure Need acceptance before certification and the approved DPP order. CFG does not manufacture missing historical evidence. A separate county-configured test world is required for county calculations; one site may represent a county entity without becoming a multi-entity site.

## 14. Acceptance and smoke contract

### 14.1 Complete predecessor replacement map

Each old occurrence has a unique successor ID. The amended assertion supersedes the earlier wording; no test result is claimed here.

| Successor ID | Old ID | Required result |
|---|---|---|
| CFG10-AC-001 | CFG-AC-001 | First run shows the entity tab and disables the other four tabs; route/county inputs are present. |
| CFG10-AC-002 | CFG-AC-002 | Configuring the entity creates the PE and its root Organisation Unit in one transaction; a failure leaves neither. |
| CFG10-AC-003 | CFG-AC-003 | Creating a second Procuring Entity is impossible through the UI, the API and a fixture. |
| CFG10-AC-004 | CFG-AC-004 | `pe_code` cannot be changed after first save, through the UI or a direct API call. |
| CFG10-AC-005 | CFG-AC-005 | Renaming the entity does not alter the code, the root unit code or any previously issued document snapshot. |
| CFG10-AC-006 | CFG-AC-006 | No PE selector or PE/FY authority/context record is introduced; exact entity legal snapshots remain allowed. |
| CFG10-AC-007 | CFG-AC-007 | Retired KenTender context/year/register routes and models are removed after dependency checks; native ERPNext accounting routes and records remain available under their own permissions. |
| CFG10-AC-008 | CFG-AC-008 | Adding a fiscal year from start year 2028 generates 1 Jul 2028 – 30 Jun 2029 and attaches the site Company. |
| CFG10-AC-009 | CFG-AC-009 | Fiscal year dates cannot be overridden through the UI or a direct API call. |
| CFG10-AC-010 | CFG-AC-010 | Adding an existing fiscal year is rejected without creating a partial record. |
| CFG10-AC-011 | CFG-AC-011 | Concurrent needs-open commands serialize through its unique module control; one atomic swap, no two configured open years and no stale-token overwrite. |
| CFG10-AC-012 | CFG-AC-012 | A close instant in the past is rejected against the server clock, not the client clock. |
| CFG10-AC-013 | CFG-AC-013 | At the close instant effective intake is closed before cleanup; the hourly job clears it idempotently with distinct effective and recorded instants. |
| CFG10-AC-014 | CFG-AC-014 | Dependent commands recheck flag, FY enablement, exact close instant and token in the transaction; equality with the close instant is closed. |
| CFG10-AC-015 | CFG-AC-015 | Opening or closing needs submission creates no Departmental Need, Plan, Budget or task. |
| CFG10-AC-016 | CFG-AC-016 | Disable is blocked by any module flag, KenTender reference or native accounting validation, with exact authorized blockers. |
| CFG10-AC-017 | CFG-AC-017 | FY 2027/28 intake can be open while FY 2026/27 remains the current accounting year. |
| CFG10-AC-018 | CFG-AC-018 | No configuration submission/review/approval workflow exists; immutable versions and verification events are direct-save evidence, not business approval states. |
| CFG10-AC-019 | CFG-AC-019 | An Administrator who opens needs submission still cannot create, review or accept a Departmental Need without the applicable responsibility assignment. |
| CFG10-AC-020 | CFG-AC-020 | No `Reference Data Manager` role, `reference_data.*` capability string or configuration approval chain exists. |
| CFG10-AC-021 | CFG-AC-021 | Selectable UOM and precision come through the native owner adapter; no assumed enabled column, parallel catalogue, free-text unit or mass-disable of unrelated units. |
| CFG10-AC-022 | CFG-AC-022 | Missing-root repair preserves AUTH invariants and existing units, is Administrator-only, and refuses ambiguous structures; responsibilities are unavailable until resolved. |
| CFG10-AC-023 | CFG-AC-023 | Stale entity/set/control tokens fail atomically; same-key/same-payload returns original result, changed payload conflicts, and no duplicate semantic audit event is created. |
| CFG10-AC-024 | CFG-AC-024 | Route/hash/record-version detail survives direct load, refresh and Back/Forward across all five tabs without duplicate mount or focus loss. |
| CFG10-AC-025 | CFG-AC-025 | Loading, empty, forbidden and error states are visibly distinct and never appear as an empty successful table. |
| CFG10-AC-026 | CFG-AC-026 | ERPNext accounting and HRMS payroll continue to function after cutover; their Fiscal Year, Company and UOM records are shared, not duplicated or replaced. |
| CFG10-AC-027 | CFG-AC-027 | A new intake module is added through the reviewed CFG flag/control/schema pattern, not a local window lifecycle or new architecture record. |
| CFG10-AC-028 | CFG-AC-029 | Needs, DPP and disposal use separate controls/tokens/audit, may target different years, and cannot change one another. |
| CFG10-AC-029 | CFG-AC-030 | ConfigureProcuringEntity and first-run UI require a route from the four approved values; setup may expose pending applicability, but positive governance requires verified applicable capacity. |
| CFG10-AC-030 | CFG-AC-030a | Method rules require Goods/Works/Services and exact applicability facts; missing category or unsupported procedure cannot resolve admission. |
| CFG10-AC-031 | CFG-AC-030b | County-only obligations require county applicability; contradictory entity facts fail setup validation and unresolved jurisdiction cannot silently select a rule. |
| CFG10-AC-032 | CFG-AC-030c | All three intake kinds have complete UI/API open/close/update-clock paths, independently atomic; DSP timing remains its own verified boundary. |
| CFG10-AC-033 | CFG-AC-031 | Rule resolution uses the legally verified date basis, not FY alone; exact historical version/verification pins survive later supersession. |
| CFG10-AC-034 | CFG-AC-032 | Missing/unverified mandatory method or reservation rules block the affected positive action; a reservation shortfall blocks under PLN; absent optional price index returns NotPublished separately. |
| CFG10-AC-035 | CFG-AC-033 | Funding-source create/rename/enable/disable uses CFG services and stable IDs; new selection excludes disabled entries, historical reads remain available. |
| CFG10-AC-036 | CFG-AC-028 | All §10 CFG artboards and AUTH-owned tab compositions have closed fixtures, complete controls/states and traceable requirements; actual rendering/usability evidence remains required. |
| CFG10-AC-037 | CFG-AC-034 | Every page resolves its authorisation verdict before rendering; a denied actor sees the inline Forbidden panel with no header, filter, content or empty state painted, and no permission modal appears on page load. |
| CFG10-AC-038 | CFG-AC-035 | The Forbidden panel names the responsibilities that open the surface and directs the user to a KenTender administrator; it names no line manager or supervisor. |
| CFG10-AC-039 | CFG-AC-036 | Selecting this module without access pushes its own route, highlights it in navigation, and lands on its Forbidden state; the module is never hidden and route and view never diverge. |

### 14.2 Additional acceptance criteria

| ID | Concern | Required result |
|---|---|---|
| CFG10-AC-040 | Shared source evidence | Verified requires complete exact-version source, effective/amendment, applicability and interpretation evidence; no bulk verification from LAW/SEED approval. |
| CFG10-AC-041 | Immutable versions | Every saved reference/profile/calendar version is immutable; changes create an explicit successor and preserve consumer pins. |
| CFG10-AC-042 | Overlap/gap | Unrelated overlaps fail save/resolution; declared supersession is date-scoped, gaps fail and creation time/version number never supplies priority. |
| CFG10-AC-043 | Date basis | FiscalYearStart, submission, approval, authorization, invitation and signing resolve only from authoritative owner facts/current action clocks; missing date returns MissingBasis. |
| CFG10-AC-044 | Correction confidence | Pending/rejected replacement or confidence withdrawal blocks affected new positive decisions; historical decision evidence remains visible and unmodified. |
| CFG10-AC-045 | Positive decision race | Rule/route/intake verification and consumer write serialize; concurrent configuration edits cannot commit a decision on mixed evidence. |
| CFG10-AC-046 | Typed conditions | Unsupported condition code/schema/operator is rejected; owner-condition evidence cannot be supplied as an unchecked boolean. |
| CFG10-AC-047 | Reservation basis | Annual Budget denominator, procurement-value basis, county and overlap policies remain separate; no missing-to-zero or Plan-total fallback. |
| CFG10-AC-048 | Candidate boundary | Preference margins and highest-advantage entitlement stay downstream; a planned designation cannot decide candidate eligibility. |
| CFG10-AC-049 | Profile completeness | Seven milestone semantics, endpoints, min/max/defaults and assumptions are explicit; absent profile/mandatory bounds never use Open Tender or 5/2-day fallback. |
| CFG10-AC-050 | Working days | A WorkingDays interval requires a verified complete calendar/version; weekends alone or an empty holiday list are not legal verification. |
| CFG10-AC-051 | Delivery boundary | Source-derived completion boundary remains separate from signing-plus-explicit-delivery estimate, including explicit zero period and missing default. |
| CFG10-AC-052 | Reminder behavior | Threshold is integer 0–365 calendar days, default 7; save affects later evaluations without duplicate notices or changed statutory deadlines. |
| CFG10-AC-053 | Complete configuration UI | Funding, every reference kind, verification, history, profile/calendar and reminder maintenance are operable through §10 with exact authority/error states. |
| CFG10-AC-054 | Evidence read scope | Business users receive only owner-authorized configuration evidence; no setup-page access or business-record authority is granted by a configuration read. |
| CFG10-AC-055 | Entity changes | Route/county edit cannot relabel an in-flight task or approved snapshot; owner positive checks detect incompatibility and permit controlled correction. |
| CFG10-AC-056 | Seed FY conflict | CFG-XD-001 is explicitly resolved before any affected integrated positive claim; no date-guard waiver, FY relabel or fabricated backdated rule coverage. |
| CFG10-AC-057 | Government channel | Publication-obligation settings record applicable evidence; they cannot self-authorize government integration or close LAW-V-008. |
| CFG10-AC-058 | Usability evidence | Full relevant artboards, keyboard/focus/error paths, 200% zoom and narrow data overflow have real browser evidence, distinct from spec completeness. |
| CFG10-AC-059 | Historical funding | Disabling/renaming a source preserves exact historic snapshots and ID lookup, and creates no budget balance or Plan lifecycle change. |

### 14.3 Focused smoke sequence

1. Configure a new isolated site, including required route/county consistency; prove atomic entity/root failure and immutable code.
2. Add native FY, resolve Company and confirm shared accounting behavior; open Needs/DPP for different years and race concurrent same-module opens.
3. Cross the close instant before cleanup; prove relevant initial action denial and permitted PLN correction/update treatment through its owner.
4. Create/rename/disable funding source and verify historical lineage.
5. Save pending reference; attempt dependent positive decision and see explicit unverified result. Record genuine test evidence through the defined isolated test mechanism; do not label illustrative data production law.
6. Exercise immutable successor, overlap/gap, missing-date, revoked-confidence and decision/configuration races.
7. Resolve a supported profile, verify endpoints, explicit defaults and WorkingDays calendar requirements; test missing support without fallback.
8. Walk all five tabs, relevant dialogs, source history and exact old-to-new acceptance mapping; record actual build/test/browser evidence.

Use focused tests for changed invariants, then affected cross-module/release gates under KT-STD. No old green test overrides the amended contract.

## 15. Implementation constraints and required owner work

Use the existing Frappe Single, native ERPNext extensions, shared Vue Desk mount and AUTH hooks. Inspect the repository before claiming current field names, DocType migrations, native Company association or UOM precision mapping. Native writes and fixture/bootstrap paths must enforce the same invariants; a page-only check is insufficient.

Use one lockable module-control row rather than relying on an unavailable database-specific partial index. All supported write paths participate in the lock/transaction; add appropriate DB uniqueness constraints for module key, FY identifiers, reference keys, set/version numbers and funding normalized name. Establish cross-owner lock ordering for CFG/BUD/PLN/REQ, meaningful rollback tests and exact immutable evidence persistence.

| Dependency | Exit evidence |
|---|---|
| LAW verification | LAW-V-001–011 resolved for each production-used rule; current edition, applicability/date basis, sources and interpretations recorded. Unneeded/future rules remain explicitly unsupported, not defaulted. |
| BUD provider amendment | Complete annual Budget basis, source-OU eligibility, atomic decision validation and precision contracts; actual native Company association verified. |
| NDS/PLN intake consumers | Exact initial action predicates and correction exceptions, close-instant checks in owner transactions, independent availability. |
| REQ/TPR/TPUB consumers | Current config validation and immutable evidence pins at relevant positive decisions; no profile admission without an implemented procedure. |
| AUTH/KT-STD | Current route/capacity mappings, shared five-tab shell parity, root repair authority and actor fixtures preserved. |
| Native UOM/calendar support | Inspected field/precision mapping and supported source-verified counting/calendar provider; no assumed native fields. |
| SEED date/scenario correction | CFG-XD-001 resolved in a controlled matching fixture amendment before affected positive-chain evidence. |
| Government operating model | LAW-V-008/LAW-OB-009 evidence and permitted integration/handoff design; no configuration checkbox used as authorization. |

Release requires actual schema/service/UI inspection, focused and affected contract tests, production asset build, applicable full artboard comparison and a dependency-aware cutover scan. Preserve native accounting/HRMS and immutable historical records. This document does not supply a deployed schema or claim integration tests passed.

## 16. Prohibited shortcuts

Do not reintroduce PE/FY context records, multiple PEs, global FY authority, local approver registries, Reference Data Manager, configuration approval workflow, module window lifecycles or duplicate ERPNext Company/Fiscal Year/UOM catalogues. Do not expose raw policy scripts or an arbitrary JSON configuration editor as the business surface.

Do not rely on hourly expiry, browser time, old cached rules, method names or latest-version sorting for a positive decision. Do not overwrite referenced versions, treat missing bounds as unlimited, use optional price-index behavior for mandatory reservation rules, infer candidate entitlement in Planning or calculate actual procurement achievement from a Plan designation.

Do not claim a source is verified through an unsupported checkbox, an approved fixture or this document's approval. Do not change fiscal-year dates to accommodate an inconsistent example. Do not remove native accounting routes or disable unrelated UOMs while removing retired KenTender surfaces.

## 17. Traceability and full change register

### 17.1 Precedence and scope of amendment

AUTH v1.7 controls authority; KT-STD v1.4 controls shared design/verification; approved LAW v1.1 identifies source/application verification; this CFG successor controls configuration schemas/surfaces; each business module controls its lifecycle. Approved SEED v1.3 controls shared fixtures subject to its explicitly retained prerequisites. When a precise inconsistency is found, record it and amend the owner; do not reinterpret its approval as permission to bypass a domain guard.

This successor implements the CFG work in PLN v1.18 §17.2 and FU-22. It preserves earlier retirement decisions for CTX-CHG-001 and obsolete KenTender registers, while making current ownership/implementation gaps explicit. No external file is claimed updated by this document alone.

### 17.2 Full changes for re-implementation

| ID | v0.9 defect / gap | Required replacement | Current target / evidence |
|---|---|---|---|
| CFG10-CHG-001 | Duplicate change-type header and approval effect incorrectly naming v0.8. | One v0.10 control block, v0.9 predecessor and distinct approval/verification status. | Control, §18 |
| CFG10-CHG-002 | Scope said four concerns while omitting its catalogues/profiles. | Explicit configuration ownership and fifth Procurement settings tab. | §§1–3, 9–10 |
| CFG10-CHG-003 | Mandatory statutory route missing from Configure API and first-run UI. | Route and county required payload/control, conflict feedback and applicable capacity evidence. | §§4.2, 7, 10.2; old AC-030/030b |
| CFG10-CHG-004 | Type descriptive-only claim contradicted county/application branching. | Explicit structural county/type matrix and verified legal applicability; no jurisdiction inferred solely from label. | §4.2; entity-conflict tests |
| CFG10-CHG-005 | Editable arbitrary timezone contradicted Nairobi-only operational constraint. | Nairobi-only field and explicit unsupported-value error in this MVP. | §§3, 4.2, 8, 10.2 |
| CFG10-CHG-006 | Intake service/UI mainly Needs; DPP/disposal fields incomplete. | Independent complete open/close/update-clock commands, focused UI and per-module authority/consumer boundary. | §§4.3, 7, 10.3; old AC-029/030c |
| CFG10-CHG-007 | Shared audit fields obscure which module changed; partial-index portability unresolved. | Per-module audit fields, immutable change evidence and one unique serialization-control row per module. | §§4.3, 5, 12, 15; concurrency tests |
| CFG10-CHG-008 | Close instant ambiguously required inside FY; flag-only command check. | Advance-year close allowed; exact now < close condition in decision transaction, independent of cleanup. | §§4.3, 7, 13; old AC-012–014 |
| CFG10-CHG-009 | Initial-intake closure could suppress permitted Planning corrections/updates. | Consumer/action-specific predicates; CFG returns availability without rewriting domain workflow. | §§2, 4.3, 11 |
| CFG10-CHG-010 | Root repair role inconsistent with general maintenance matrix. | Explicit Administrator-only exception and ambiguity-safe repair. | §§4.4, 6–8; old AC-022 |
| CFG10-CHG-011 | Funding catalogue lacked complete services, history and disable semantics. | Stable identity, normalized uniqueness, CRUD-limited maintenance, selection/historical distinction and full editor. | §§4.5, 7, 10.4; old AC-033 |
| CFG10-CHG-012 | Reference rows thin and all rules resolved by FY. | Typed immutable versions, verified date basis, authoritative context and exact historical/decision evidence. | §§4.6–4.10, 5, 7; old AC-031 |
| CFG10-CHG-013 | Source verification unspecified and could appear as a checkbox. | Evidence-complete append-only verification under existing maintenance authority; no new approval role. | §§4.6, 6, 10.7 |
| CFG10-CHG-014 | Missing thresholds closed checks but missing target never blocked. | Mandatory missing/unverified reservation blocks affected action; optional price index separate. | §§5, 8; replacement AC-032 |
| CFG10-CHG-015 | Unverified legal figures appeared as production constants. | Remove embedded authoritative defaults; preserve historical candidates in LAW and require exact evidence. | §§4.7, 10.6, 13; LAW11 mapping |
| CFG10-CHG-016 | Supersession, overlaps, gaps and corrections undefined. | Exact chain/date selection, rejected unrelated overlap, visible gaps and immutable old evidence. | §§4.6, 5, 10.7 |
| CFG10-CHG-017 | No method-condition/procedure-support surface or typed contract. | Supported fact/evidence/condition registry, exact typed fields and explicit not-implemented outcomes. | §§4.7–4.8, 10.6 |
| CFG10-CHG-018 | No complete schedule/minimum/maximum/counting maintenance. | Immutable method/procedure profiles, seven milestones, endpoints/bounds/defaults/assumptions and calendars. | §§4.8, 10.8 |
| CFG10-CHG-019 | Operational reminder threshold absent. | Integer calendar-day setting, default 7, separate from statutory timing and PLN notice identity. | §§4.9, 10.9 |
| CFG10-CHG-020 | Configuration edit could silently affect in-flight task content/authority. | Frozen task/capacity/history plus current serialized positive-decision validation and owner correction path. | §§4.2, 4.10, 5, 12 |
| CFG10-CHG-021 | UOM enabled-field assumption and disable-all seed risk to shared accounting. | Native adapter/precision mapping, curated choices, preserved unrelated UOMs and native routes. | §§3, 4.4, 13, 15; old AC-021/026 |
| CFG10-CHG-022 | FY/profile dates and shared positive-chain dates incompatible. | Explicit CFG-XD-001; fixed native FY semantics and controlled matching seed reconciliation. | §13; no guard waiver |
| CFG10-CHG-023 | Government-system operating duty absent from setup ownership. | Publication obligation metadata and named LAW/architecture gate; no self-authorizing integration control. | §§2, 4.7, 15 |
| CFG10-CHG-024 | Incomplete artboards for configuration introduced in Planning. | Closed C01–C04-equivalent fixtures, every editor/error/history path, fifth-tab and AUTH parity. | §§9–11; replacement AC-028 |
| CFG10-CHG-025 | Existing acceptance IDs irregular and new behavior unmapped. | Unique successor ID for every old occurrence plus explicit added criteria and smoke sequence. | §14 |
| CFG10-CHG-026 | Legacy document assertions could be treated as code/test completion. | Actual repository/native mapping inspection and named provider/release evidence. | §§12, 15, 18 |

### 17.3 Follow-up dispositions

| Item | Disposition |
|---|---|
| FU-22 | Document amendment approved on 12 September 2026. Implementation and verification remain open and require their specified evidence. |
| CFG-XD-001 | Concrete pre-FY procurement/profile mismatch in §13; matching PLN/SEED/downstream/legal reconciliation required. |
| LAW-V-001–011 | Applicable legal source/interpretation work remains owned by LAW; CFG's schema does not establish legal correctness. |
| FU-23–25 / FU-30 | BUD/NDS/REQ/TPR and precision provider amendments remain required; TPUB and STR compatibility are explicitly included where relevant. |
| FU-26 | County fixture is a separate single-entity world and gates county-support evidence. |
| FU-27 | Later KT-STD technical-read citation cleanup requires the actual successor standard; do not cite uninspected §3A.6 as supplied authority. |

## 18. Approval effect

Approved on 12 September 2026, CFG v0.10 supersedes v0.9 as the controlled configuration contract. It adopts the complete five-tab setup, independent intake controls, typed/versioned references, evidence-based verification, date resolver, profiles/calendars and reminder setting described here. It preserves direct Administrator/System Manager maintenance with no configuration approval workflow and the explicit Administrator-only root repair exception.

Approval does not close legal applicability, CFG-XD-001, provider integration, native field/Company mapping, artboard/browser validation or production release evidence. It does not update sibling controlled documents automatically. Record concrete implementation/test evidence against §14 and §17.2, preserve the approved predecessor, and remove obsolete executable constructs only after dependency checks while retaining historical and native accounting data.
