# CFG-CHG-002 — Site Configuration and System Setup

| Control | Value |
|---|---|
| Document ID | CFG-CHG-002 |
| Version | 0.11 |
| Date | 14 September 2026 |
| Status | **Consolidated approved requirements** |
| Approval basis | Project Owner approval of the System setup usability amendment and KT-STD-001 v1.5 on 14 September 2026, with instruction to incorporate into the full document. |
| Predecessor | CFG v0.10, approved 12 September 2026; retained as historical evidence. |
| Module / implementation owner | Configuration and Governance / `kentender_core`, with native ERPNext/Frappe records where they exist. |
| Change basis | Complete approved CFG v0.10; approved System setup usability amendment v0.1 (14 changes); adopted approved KT-STD-001 v1.5. Earlier PLN v1.18, LAW v1.1, SEED v1.3 and FU-22 trace is retained. |
| Standards | **KT-STD-001 v1.5**, approved and inspected 14 September 2026, is the shared standard going forward; AUTH-ADR-001 v1.7 is the supplied authority baseline, subject to KT-STD §3A.6 and the named AUTH owner follow-up in §17.4. |
| Purpose | One usable setup surface for entity details, financial years, independent submission periods, funding sources, source-backed rules, procurement schedules and reminders. |
| Approval effect | Supersedes CFG v0.10 in full as the consolidated implementation contract. Document approval is separate from legal source verification, implementation, integration, usability and release evidence. |
| Full change table | §17.2 retains 26 predecessor changes; §17.3 records 14 usability changes and one standards-adoption change: 41 rows in total. |
| Acceptance coverage | §14 retains 59 predecessor criteria and adds 28 usability plus 4 standards-adoption criteria: 91 in total. |

## 1. Governing decisions

One KenTender site represents one Procuring Entity. The entity is configured at first run and is never selected as a global context. Use ERPNext Fiscal Year and UOM, the AUTH-owned responsibility model and one System setup page. Administrator or System Manager maintains configuration directly on save; there is no configuration approval workflow, Reference Data Manager or local business-approver registry.

The five existing tabs remain. **Procurement settings** contains Funding sources, Procurement rules, Procurement schedules and Reminders. The domain term ScheduleProfile remains unchanged; its user-facing section is Procurement schedules. Versioned configuration and source-verification evidence do not create Draft/Submitted/Approved configuration states.

LAW v1.1 separates legal source, interpretation and product controls. A saved or approved document, configured route or successful test does not make a legal rule Verified. Missing mandatory applicable configuration blocks the affected positive business action. Optional market-price-index absence is distinct from mandatory reservation readiness.

Everyday setup has a short, named task and one primary action. Specialist rule maintenance has structured evidence and explicit consequences. A business actor encounters only the configuration issue relevant to the owning business task. Saving configuration, verifying its source and passing a current business decision remain distinct results. No approval/state-transition facility is missing from this scope: setup deliberately uses direct saves; immutable versions and append-only source checks have the explicit transitions in §§4–5, not a business approval lifecycle.

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

### 3.1 Current standard and explicit domain exceptions

KT-STD-001 v1.5 is approved, inspected and adopted. Shared design, authorization presentation, technical read, implementation and release mechanics are inherited by citation. Technical read uses §3A.6; do not maintain a weaker local grant. The following explicit exceptions preserve approved CFG v0.10 domain decisions under KT-STD §1 and §12:

| ID | Standard provision | CFG domain rule and reason |
|---|---|---|
| CFG11-EX-001 | §3A.6 read-only technical routes and absent commands | Administrator/System Manager retain the setup-maintenance commands assigned by CFG and AUTH; otherwise this configuration surface would have no maintainer. This exception is limited to authorised configuration/responsibility maintenance and does not grant business procurement commands. Technical business-record access remains governed by §3A.6. |
| CFG11-EX-002 | §8.5 shared UOM fixture says all other units disabled | Preserve native accounting/payroll and historical UOM usage; keep the specified procurement choices selectable through the owner adapter without blanket disabling other native units. CFG §§3, 4.4 and 13 govern this domain compatibility requirement. |
| CFG11-EX-003 | §2.3 prohibits nested-set repair controls | Retain only the Administrator-only, missing-root recovery in §4.4 and its AUTH invariants. No raw nested-set fields, general repair tool, reparent/delete or ambiguous-tree repair is exposed. This is the existing bootstrap recovery exception, not a new tree editor. |

The actual supplied AUTH v1.7 does not contain AUTH-DES-09, the `/app/technical-search` design, or the §9 conformance-gate specification cited by KT-STD v1.5. The approved standard is controlling; obtain the matching owner specification and implementation evidence as CFG-XD-002 (§17.4). Do not infer that the search/gate already exists, recreate it in CFG, or defer the mandated read right because the owner specification is absent.

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

| Actor | Allowed configuration work / experience | Limits |
|---|---|---|
| Administrator | Entity, years/submission periods, funding, rules, schedules, calendars, reminders and source-check recording; AUTH-owned organisation/responsibility maintenance. | Direct maintenance under CFG11-EX-001; exceptional missing-root repair under CFG11-EX-003. Business technical access is governed by KT-STD-001 v1.5 §3A.6. |
| System Manager | The same ordinary maintenance and evidence recording; AUTH-permitted organisation/responsibility work. | No missing-root repair action; show the Administrator escalation. Business technical access is governed by KT-STD-001 v1.5 §3A.6. |
| Business actors | Owner-authorised relevant values, deadlines, current issues and decision evidence inside their business record/review. | Business responsibility alone gives no setup mutation or full setup access; each owner supplies its permitted correction/return path. |
| Auditor | Owner-authorised historical configuration evidence, separating the source check used at the decision from any current warning. | No setup mutation or new unrestricted configuration browser. |
| Technical reader examining records | Inherits KT-STD-001 v1.5 §3A.6. | Search/read-entry registration is mandatory; do not duplicate the common technical-read contract here. |
| Authenticated system service | Registered reads, current decision validation and scheduled expiry under fixed contracts. | No arbitrary rule edit, business task, self-asserted legal verification or wait-for-cleanup deadline bypass. |

Setup maintenance authority is checked on every CFG command and native write. A legal adviser may prepare evidence for an authorised recorder; this creates no separate verifier role, second-person approval, AO sign-off or configuration approval chain. The recorder remains accountable for the exact source check.

Shared page verdict/navigation and technical-read rules are inherited from KT-STD-001 v1.5 §§3A.1–3A.6. The setup-specific denied state is for a user without setup authority; it is not used to deny a technical reader. Technical navigation controls such as opening a record are read affordances; domain writes remain limited to the configuration exception above.

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

### 7.3 One-form rule creation and recoverable partial saves

The Add rule UI is one form. It does not turn CreateRegulatoryReference and SaveRegulatoryReferenceVersion into an undocumented atomic transaction. Before the first write, PreviewConfigurationVersion validates the candidate's supported structure, selectors and proposed values without requiring a persisted set. Preview uses the proposed key/kind and any owner-valid context; missing future applicability facts are explicit, not invented. Structurally saveable pending legal evidence is a visible incompleteness result, not a prohibition on storing the baseline's allowed pending version.

| Step / outcome | Required service orchestration and UI result |
|---|---|
| Initial validation | Reject structural/unsupported-schema defects before set creation; expose completeness and impact separately. A preview never establishes legal usability. |
| Create set | Call CreateRegulatoryReference with its own idempotency key. Retain the returned stable ID and root token. The user-defined reference key remains distinct from the generated record ID. |
| Save first version | Call SaveRegulatoryReferenceVersion with a separate key and the returned set ID/token. Show the exact saved version only after this command succeeds. |
| Set saved; version failed | Display “Rule created; version not saved”; retain entered values and set ID/token; retry only the version operation. The set is real, not rolled back or a persisted Draft. |
| Ambiguous timeout | Recover/replay the exact original operation with its original key and canonical payload before another write. A changed payload requires an explicitly reviewed new operation/key. |
| Resumed empty set | List shows No version saved and Add first version; refresh through the authoritative set read before writing. Do not create a duplicate set to resume. |
| Version saved; later source-check failure | Keep the successful immutable version. Report only the source-check failure; retry the separate verification operation with its exact target/prior-event identity. |

No new combined service or approval state is implied. Each existing command remains individually atomic and idempotent. Permission, current tokens and rule conflicts are revalidated by the committing service even after preview. Display copy maps to the original service names and enums; aliases are not new endpoints.

### 7.4 Shared technical-read integration

Apply KT-STD-001 v1.5 §3A.6. Register CFG record families and their exact-version entry points with the owned Technical record search and technical-read conformance gate: site configuration; module submission controls/change evidence; funding sources; regulatory reference sets/versions/source-check evidence; schedule profiles/versions; calendar versions; reminder settings and authorised audit/history views. Native Fiscal Year/Company/UOM and AUTH-owned unit/assignment registrations remain with their owners; reuse their routes instead of duplicate results.

Inspect the repository for actual DocType identifiers and registration APIs; the names above are logical requirements, not assumed installed tables. Implement the shared owner requirement through CFG-XD-002, and include CFG conformance evidence at release.

## 8. Error and readiness contract

| Code | Exact user-facing message |
|---|---|
| CFG_PE_NOT_CONFIGURED | Configure this site's procuring entity before using KenTender. |
| CFG_PE_ALREADY_CONFIGURED | This site already has a procuring entity. |
| CFG_PE_CODE_IMMUTABLE | The entity code cannot be changed after configuration. |
| CFG_APPROVAL_ROUTE_REQUIRED | Select who approves this entity's Annual Procurement Plan. |
| CFG_ENTITY_APPLICABILITY_CONFLICT | The county answer does not match the entity details. |
| CFG_APPROVAL_APPLICABILITY_UNVERIFIED | The approval authority's supporting evidence must be completed before Plan approval. |
| CFG_TIMEZONE_UNSUPPORTED | This release uses Africa/Nairobi as the operational timezone. |
| CFG_ACCOUNTING_COMPANY_UNRESOLVED | The accounting company must be configured before you can add a financial year. |
| CFG_ROOT_UNIT_MISSING | The top-level organisation unit is missing. |
| CFG_ROOT_UNIT_CONFLICT | The organisation structure cannot be repaired automatically. |
| CFG_FY_ALREADY_EXISTS | This financial year already exists. |
| CFG_FY_DATES_INVALID | Financial-year dates must run from 1 July to 30 June. |
| CFG_FY_IN_USE | This financial year cannot be disabled while the listed records or intake controls use it. |
| CFG_INTAKE_CLOSE_INSTANT_INVALID | Enter a closing time later than the current time. |
| CFG_INTAKE_NOT_OPEN | {Activity label} submissions are not open for this financial year. |
| CFG_INTAKE_EXPIRED | {Activity label} submissions closed at {displayed close instant}. |
| CFG_FUNDING_SOURCE_DUPLICATE | A funding source with this name already exists. |
| CFG_FUNDING_SOURCE_DISABLED | This funding source is unavailable for new selection. |
| CFG_REFERENCE_MISSING | No {rule name} version covers the required date. |
| CFG_REFERENCE_AMBIGUOUS | Versions of {rule name} overlap for the required date. |
| CFG_REFERENCE_UNVERIFIED | Sources for {rule name} must be checked before this action can continue. |
| CFG_REFERENCE_INCOMPLETE | Complete the listed details in {rule name} before using it for this action. |
| CFG_REFERENCE_IMMUTABLE | Create a new version to change this saved version. |
| CFG_APPLICABILITY_BASIS_MISSING | The {date label} is needed to check this rule. |
| CFG_SCHEMA_UNSUPPORTED | This rule uses a condition or format that is not available in this release. |
| CFG_PROCEDURE_UNSUPPORTED | This procurement procedure is not available in this release. |
| CFG_SCHEDULE_PROFILE_MISSING | Complete the applicable procurement schedule before Plan submission. |
| CFG_CALENDAR_REQUIRED | Select a verified working-day calendar for this interval. |
| CFG_VERIFICATION_EVIDENCE_REQUIRED | Complete the source, applicability and interpretation evidence before recording a verified source check. |
| CFG_SUPERSESSION_INVALID | Select valid earlier versions and check the dates this replacement will cover. |
| CFG_CONFIGURATION_CHANGED | The settings have changed since this check was made. |
| CFG_AUTHORITY_REQUIRED | You are not authorised to change site configuration. |
| CFG_VERSION_CONFLICT | This information has changed since you opened it. |
| CFG_IDEMPOTENCY_CONFLICT | We could not save these changes with this request. |

Interpolation uses server-resolved safe labels; it is not placeholder product copy. Activity labels are Departmental needs, Departmental plan and Disposal plan; the composed messages append “submissions”. Optional index absence is an ordinary **Not published** projection, not CFG_REFERENCE_MISSING for a mandatory control. Return field-specific validation details with the error; never expose protected record identities in a denied response. Missing legal applicability and implementation support remain visibly distinct.

### 8.1 Readiness labels and authorised recovery

Primary messages remain one plain sentence; supporting facts and permitted actions are separately labelled. Interpolation uses authorised server-resolved facts, never invented labels or protected identifiers. Existing codes/enums remain unchanged.

| Condition | Display label / explanation | Recovery |
|---|---|---|
| Pending verification | Source check needed | Check sources for an authorised maintainer; list missing evidence. |
| Verified evidence | Sources verified | Still show completeness, date applicability and implementation support separately; no universal Ready badge. |
| Rejected verification | Source check rejected | Show recorded reason and effect on new decisions separately from historical evidence. |
| Incomplete payload | Details missing | Saved version: Create new version. Unsaved form: focus missing controls. Recording a source check cannot alter immutable values. |
| Unsupported method/condition | Not available in this release | Name the missing capability/owner contract in authorised details; no enable switch. |
| Missing basis/date coverage or overlap | Date needed / No rule covers this date / Rule versions overlap | Show the exact owner-required date and authorised rule details; obtain owner facts or Review versions. Never substitute a date/latest version. |
| Stale configuration/form | Review latest details before continuing / saving | Reload current facts; retain proposed inputs for explicit review; do not overwrite or auto-resubmit. |
| Idempotency conflict | Review the latest record and try again. | Recover the original operation result before a new operation/key. Put technical code under Details. |
| Missing Company | Exact missing or ambiguous accounting association | Offer the authorised actual native setup route when resolved; never infer Company by name or add a local selector. |
| Missing root | Administrator repair or System Manager escalation | Only Administrator may invoke the specified repair; ambiguity remains a support issue. |
| Business action blocked by configuration | Short problem, affected action and setup-owner contact | Inside the owning business record, retain that owner’s permitted return/correction action; do not require the AO to navigate setup. |
| Optional price index absent | Not published | Informational for the optional index alone; mandatory reservation and other checks still apply. |

For the approved route-evidence example, the business-facing primary sentence is “Plan approval is unavailable because the approval authority's supporting evidence is incomplete.” Its separate helper is “Ask your KenTender administrator to complete it.” The consuming module owns access and available actions. Technical reader presentation follows KT-STD §3A.6, not ordinary business scope masking.

## 9. UI architecture and routes

One Vue 3 surface in the existing Frappe Desk shell at `/app/system-setup`. Use AUTH/KT-STD-001 v1.5 navigation, authorization and component rules. No new SPA shell or proof-of-concept stack.

| Anchor | Tab / content |
|---|---|
| #procuring-entity | Procuring entity |
| #fiscal-years | Financial years |
| #organisation-structure | Organisation structure — AUTH v1.7's native tree and details |
| #users-and-responsibilities | Users and responsibilities — AUTH v1.7 |
| #procurement-settings | Procurement settings; sections Funding sources, Procurement rules, Procurement schedules, Reminders |

A local section/record parameter within Procurement settings restores the selected list/detail/version on refresh and Back. Use `#procurement-settings/{section}/{id}` and optional `/versions/{version_id}` for exact version detail; sections are funding-sources, procurement-rules, schedule-profiles and reminders. Calendar editing opens from a WorkingDays profile through `/calendars/{id}` inside this tab; it is not a sixth tab.

Default is the first incomplete structural setup tab; once entity/root exist, honor the requested tab, otherwise entity. Incomplete regulatory verification is shown in the affected rule/profile, not a forced wizard that prevents other setup work. First run disables the other four tabs. Missing root leaves entity/FY/procurement settings accessible but disables responsibilities and shows the AUTH repair state in Organisation structure.

Register one mount in the shared surface registries, preserve authorized native ERPNext access, and remove superseded KenTender configuration navigation without deleting native accounting routes. Back returns to Configuration and Governance. Maintain exact route/view alignment for forbidden direct loads.

Visible labels do not rename the stable anchors, service names or section keys. The existing schedule-profiles key displays Procurement schedules; Manage intake becomes Submission periods. Rule detail/source-check/new-version navigation preserves the exact selected record and version. Calendar editing remains contextual inside Procurement settings. No global setup score, extra wizard or per-role technical dashboard is introduced.

## 10. Static design contract

### 10.1 Supply, page header and fixture context

Supply KT-STD-001 v1.5 §2 plus this section only to the design tool. The common shell, typography, spacing and closed-input rules are inherited from that standard. This section supplies CFG-specific visible content. Runtime behavior is in §11, excluded from design prompts.

Page eyebrow **CONFIGURATION AND GOVERNANCE**. Title **System setup**. Description **Manage this site's details, financial years, responsibilities and procurement settings.** No page-header action. Five tabs in order: **Procuring entity**, **Financial years**, **Organisation structure**, **Users and responsibilities**, **Procurement settings**. Procurement settings section links: **Funding sources**, **Procurement rules**, **Procurement schedules**, **Reminders**.

Fixture context outside every CONFIG artboard: Administrator; `administrator@moh.example.test`; Ministry of Health; 24 November 2026, 09:15 EAT; breadcrumb Home > Configuration and Governance > System setup. The selected local tab/section is specified below. The System Manager and business/Auditor variants use their role label outside the artboard; no invented individual identity.

Separate fixture worlds:

| World | Supplied state | Use |
|---|---|---|
| CONFIG | Entity configured; FY 2027/28 Needs open until 25 Nov 2026, 23:59 EAT; departmental plans open until 30 Nov 2026, 23:59 EAT; disposal closed. FY 2026/27 all three closed. | Ordinary setup screens. |
| CONFIG-FIRST | No entity or root configured; inputs blank except fixed timezone. | First-run screen. |
| CONFIG-SWAP | Departmental plans open for FY 2026/27 with no closing date and closed for FY 2027/28; other activities as CONFIG. | Cross-year opening consequence. |
| CONFIG-RULES | Method eligibility and Reservation rules Version 1, 1 Jul 2027–30 Jun 2028, sources pending and fields incomplete. Exact source values are in §10.6. | Rule list, detail, source-check and correction specimens. |
| CONFIG-EMPTY | No years, funding sources, rules or schedules for the individual empty-state artboard. | Each empty screen separately. |

CONFIG values demonstrate presentation. They are not a verified legal dataset or evidence of an integrated positive business chain. For unsupplied editable legal values show blank controls; for saved missing values use the exact missing-value wording below. Do not invent source attachments, legal amounts, implementation support or affected-record counts.

### 10.2 C01 — Procuring entity

Configured heading **Procuring entity**. Description **This site represents one procuring entity. Its code is fixed after setup.**

| Label | Configured value | Control |
|---|---|---|
| Entity name | Ministry of Health | Text |
| Entity code | PE-MOH | Read-only in configured screen; text in first run |
| Entity type | National Government Ministry | Select: National Government Ministry; State Department; State Corporation; County Government; County Corporation; Constitutional Commission; Public University; Other Public Entity |
| PPRA registration | PPRA/PE/2019/0114 | Optional text |
| Timezone | Africa/Nairobi | Read-only |
| Who approves the Annual Procurement Plan? | Cabinet Secretary | Select: Cabinet Secretary; County Executive Committee Member; Board of Directors; Council |
| Is this a county entity? | No | Explicit Yes / No choice |

Supporting group **Setup record**: Configured by **Administrator**; Configured at **29 Jun 2026, 10:10 EAT**; Top-level organisation unit **Ministry of Health**; Unit code **PE-MOH**, each a separate labelled row.

Visible group **Plan approval authority**: status **Source check needed**; text **The approval authority's supporting evidence must be completed before Plan approval.** Link **View procurement rules**. Footer **Save changes**, inactive in the unchanged variant. Saved notice **Site details saved**.

First run: heading **Configure this site**; description **Enter the procuring entity's details to set up this site.** Blank inputs for name, code, type, registration, approval authority and county answer; Timezone **Africa/Nairobi**. Footer **Configure site**. Other four tabs unavailable. Successful first-run notice **Site configured** and the separate source-check group above. No setup approval badge or generic site-ready badge.

Conflict specimen: Entity type **County Government**, county answer **No**; inline message **The county answer does not match the entity details.** Missing-authority specimen: blank authority and **Select who approves this entity's Annual Procurement Plan.** Missing-root variants are specified in §10.11.

### 10.3 C02 / CUX-01 — Financial years and submission periods

Heading **Financial years**. Description **Set when departments can submit needs and plans.** Action **Add financial year**.

| Financial year | Period | Phase | Departmental needs | Departmental plans | Disposal plans | Action |
|---|---|---|---|---|---|---|
| FY 2027/28 | 1 Jul 2027–30 Jun 2028 | Upcoming | Open; separately labelled Closes at: 25 Nov 2026, 23:59 EAT | Open; separately labelled Closes at: 30 Nov 2026, 23:59 EAT | Closed | Submission periods |
| FY 2026/27 | 1 Jul 2026–30 Jun 2027 | Current | Closed | Closed | Closed | Submission periods |

Text below table **Each activity can be open for one financial year at a time.** Footer **2 financial years**. Filter **Include disabled years**. Collapsible **Shared accounting settings**, text **Financial years and units of measure are shared with accounting.** Link **Manage units of measure**.

Year detail heading **Submission periods**. Separate fact rows Financial year **FY 2027/28**; Period **1 Jul 2027–30 Jun 2028**; Financial year enabled **Yes**. Table:

| Activity | Status | Closes at | Actions |
|---|---|---|---|
| Departmental needs | Open | 25 Nov 2026, 23:59 EAT | Change closing time; Close submissions |
| Departmental plans | Open | 30 Nov 2026, 23:59 EAT | Change closing time; Close submissions |
| Disposal plans | Closed | Not set | Open submissions |

Each open-ended open row displays **No closing date**. Scheduled-expiry variant shows **Closed**, with separate **Closed at** value **25 Nov 2026, 23:59 EAT** for Departmental needs. A **Change history** disclosure lists Activity, Financial year, Change, Previous value, New value, Reason, Changed by, Changed at as separate columns or labelled fields in each entry.

Year-level action **Disable financial year** is separate from submission actions. Blocked variant heading **This financial year cannot be disabled**; reason **Departmental needs submissions are still open.** Additional blockers supplied by an actual named record fixture have individual labelled rows; do not invent references. Footer **Cancel** and unavailable **Disable financial year**. Unreferenced/all-closed variant shows **Disable FY 2027/28?**, text **This year will be unavailable for new use.**, buttons **Cancel** / **Disable financial year**. Disabled-year detail shows Financial year enabled **No**, action **Enable financial year**.

Add-year dialog: heading **Add financial year**; Start year **2028**, numeric field; preview Financial year **FY 2028/29**, Period **1 Jul 2028–30 Jun 2029**, separately labelled. Footer **Cancel** / **Add financial year**. Duplicate variant **This financial year already exists.**, link **View financial year**. Company defect **The accounting company must be configured before you can add a financial year.** Supporting detail **No accounting company is linked to this site.** An authorised standard accounting link is a runtime integration variant; omit it from the closed CONFIG specimen because its exact native route is not supplied.

Narrow-width composition uses a card per year with separate Year, Period, Phase and three activity rows, preserving every deadline and action label. No omitted disposal status, concatenated metadata line, Company selector, editable dates or current-year toggle.

### 10.4 C02 / CUX-02 — Open, close and change deadline forms

One focused form per action; the parent year detail supplies its context. Year and Activity each have a separate read-only field. An optional **Close automatically on** control has an explicit **EAT** label. Helper **Leave the closing date blank to keep submissions open until you close them.** Required **Reason** uses the supplied specimen text below; production entry behavior is in §11.

| Form heading | Year | Deadline specimen | Reason specimen | Primary action |
|---|---|---|---|---|
| Open departmental needs submissions | FY 2027/28 | 25 Nov 2026, 23:59 EAT | Annual needs call issued under circular MOH/PROC/2026/07. | Open submissions |
| Close departmental needs submissions | FY 2027/28 | No deadline input | Needs call closed on the date announced in circular MOH/PROC/2026/07. | Close submissions |
| Open departmental plan submissions | FY 2027/28 | 30 Nov 2026, 23:59 EAT | Annual departmental procurement planning call. | Open submissions |
| Close departmental plan submissions | FY 2027/28 | No deadline input | The announced departmental submission period has ended. | Close submissions |
| Open disposal plan submissions | FY 2027/28 | Blank | Disposal intake opened for the declared fixture scenario. | Open submissions |
| Close disposal plan submissions | FY 2027/28 | No deadline input | The announced disposal intake period has ended. | Close submissions |
| Change closing time | FY 2027/28; Departmental plans | 30 Nov 2026, 23:59 EAT | The announced submission deadline has been extended. | Save closing time |

Every form includes **Cancel**. Close-needs supporting text **Existing needs remain available under the Departmental Needs rules.** Close-departmental-plans text **Existing submissions and permitted updates remain available.** Close-disposal text **Existing records remain available under the Disposal rules.** These are initial-submission controls, not record-closing actions.

CONFIG-SWAP open-departmental-plans form shows visible consequence **This will close departmental plan submissions for FY 2026/27.** Second sentence **Departmental needs and disposal plan submissions will stay as they are.** Place this above the primary action within the same form. No second confirmation screen.

Deadline error **Enter a closing time later than the current time.** Expiry variant **Departmental needs submissions closed at 25 Nov 2026, 23:59 EAT.** Concurrent-change variant **These submission settings have changed since you opened them.** Action **Review latest settings**. Display the user's retained reason in the form.

### 10.5 C03-A — Funding sources

Heading **Funding sources**. Description **Maintain the sources used in procurement budgets.** Action **Add funding source**.

| Name | Available for new selection | Action |
|---|---|---|
| Government of Kenya | Yes | Edit |
| Development partner | Yes | Edit |
| Appropriation in Aid | Yes | Edit |

Editor labels **Funding source name**, **Available for new selection**; new specimen name **Development partner**, availability **Yes**. New footer **Cancel** / **Add funding source**. Existing footer **Cancel** / **Save changes**. Availability helper **Turning this off prevents new selection; existing records keep their funding history.** Disabled specimen **Development partner**, availability **No**, action **Edit**. Duplicate message **A funding source with this name already exists.** Empty heading **No funding sources yet**; description **Add the sources used by this site's procurement budgets.**; action **Add funding source**. No budget amount, reason or approval controls.

### 10.6 C03-B / CUX-03 — Procurement rules and versions

Heading **Procurement rules**. Description **Maintain procurement rules and their supporting sources.** Primary **Add rule**. Filters **Rule kind**, **Search**, **Source check**; default **All**.

| Rule | Applies from | Applies until | Version | Source check | Details | Action |
|---|---|---|---|---|---|---|
| Method eligibility | 1 Jul 2027 | 30 Jun 2028 | 1 | Source check needed | Details missing | View |
| Reservation rules | 1 Jul 2027 | 30 Jun 2028 | 1 | Source check needed | Details missing | View |

Empty heading **No procurement rules yet**; description **Add rules for the procurement procedures supported by this release.**; action **Add rule**. Empty-set recovery specimen: Rule **Method eligibility**, Version **No version saved**, action **Add first version**. Optional Market price index specimen: **Not published**, text **No price index has been published for this period.**

Saved detail heading **Method eligibility**. Separate rows: Rule kind **Method eligibility**; Version **1**; Applies from **1 Jul 2027**; Applies until **30 Jun 2028**; Source check **Source check needed**; Details **Details missing**. Visible issue **Complete the rule details and source checks before using this version.**

Supporting groups are **Rule details**, **When this rule applies**, **Sources and interpretation**, **Usage and history**. In the pending CONFIG specimen:

| Group | Label | Display value |
|---|---|---|
| Rule details | Method | Open Tender |
| Rule details | Procedure | Planning example |
| Rule details | Category | Goods |
| Rule details | Currency | KES |
| When this rule applies | Which date determines the rule to use? | Not yet established |
| When this rule applies | Entity applicability | Not yet established |
| When this rule applies | County applicability | Not yet established |
| Sources and interpretation | Source instrument | Public Procurement and Asset Disposal Regulations — source verification pending |
| Sources and interpretation | Edition | Not yet established |
| Sources and interpretation | Provisions | Not yet established |
| Sources and interpretation | Source document | Not attached |
| Sources and interpretation | Interpretation | Applicability review is outstanding. |
| Usage and history | Usage | Not supplied in this isolated example. |

Saved detail actions **Create new version**, **Check sources**, **View usage and history**. Secondary **Edit rule name** has Rule name **Method eligibility**, buttons **Cancel** / **Save changes**; Rule identifier **METHOD-ELIGIBILITY** and Rule kind **Method eligibility** are separate read-only fields on saved detail.

Add-rule form heading **Add procurement rule**; fields **Rule name**, **Rule kind**, then the selected kind's groups in §10.7 and the common version fields below. **Rule kind** offers exactly seven options: **Method eligibility**, **Reservation rules**, **Exclusive preference**, **Preference margins**, **Market price index**, **Approval applicability**, **Publication obligations**. **Method condition** is not a Rule kind option; condition groups and their rows appear only inside **Method eligibility**. Identifier group **Rule identifier**, editable specimen **METHOD-ELIGIBILITY** before first creation; this is a user-defined stable key, not the generated record ID. New-rule specimen name and kind **Method eligibility**. Footer **Cancel** / **Save rule version**. Partial-save variant heading **Rule created; version not saved**; text **Your entries are retained so you can finish saving this version.**; primary **Save rule version**. No successful-ready badge.

Common version fields: **Applies from**, **Applies until**, **Which date determines the rule to use?**, **Entity types**, **County applicability**, and relevant **Categories**, **Method**, **Procedure**, **Currency**. Date-basis choices: Financial year start; Plan submission date; Plan approval date; Proceeding authorisation date; Invitation date; Contract signing date. Source fields: **Instrument**, **Edition**, **Provisions**, **Source URL**, **Source document**, **Effective dates and amendments**, **Interpretation**. Existing-source document display **Not attached**; blank inputs for unsupplied values. No fabricated document link.

New-version specimen heading **Method eligibility — new version**, status **Unsaved changes**. Separate fields Earlier version **1**; Applies from **1 Jul 2027**; Applies until **30 Jun 2028**; **Reason for change** blank. Supporting **Earlier versions this replaces** lists Method eligibility Version 1. Footer **Cancel** / **Save new version**.

Visible effect group **Effect of this replacement**: Coverage replaced **Version 1, for matching applicability within the displayed period**; Current readiness **Version 1 already needs source checks**; Historical decisions **Keep the exact evidence used at the time**; Usage **Not supplied in this isolated example**. Notice **The replacement will not be usable for affected new decisions until its required details and source checks are complete.** A separate live-data impact variant uses the exact warning **Saving this replacement will block {affected action} until its sources are verified.** Its action label, date coverage and authorised usage come from the named live context; no made-up count is supplied to CONFIG.

### 10.7 C03-C — Kind-specific rule editors

Only the selected rule kind's group appears. Common sources/date fields are in §10.6. Method-condition groups are an embedded, repeatable part of **Method eligibility**, not a selectable eighth kind. Each editable condition or other typed row has **Add row** / **Remove row** controls. A visible **Details to complete** list uses the missing field labels. No JSON or script editor.

| Kind | Group headings | Exact field labels / supplied CONFIG values |
|---|---|---|
| Method eligibility | Which purchases qualify?; Value range; Conditions and evidence | Method **Open Tender**; Procedure **Planning example**; Category **Goods**; Currency **KES**; Value measured against **Approved budget allocation**; Minimum status **Not yet established**; Minimum amount blank; Minimum included; Maximum status **Not yet established**; Maximum amount blank; Maximum included. **Conditions and evidence** contains repeatable Condition groups. Each group has **Conditions required: All / Any** and repeatable rows with **Condition**, **Requirement**, **Checked at**, **Fact to check**, **Comparison**, **Expected value**, **Required evidence**, **Required authority**, **Source reference**. Missing specimen **Required conditions not yet completed.** Unsupported row variant **This condition is not available in this release.** |
| Reservation rules | Annual target; What the target is measured against; Who qualifies; How targets overlap | Obligation code **ANNUAL-TARGET-EXAMPLE**; Target **30%**; Measured against **Annual procurement budget**; Eligible planned designation **Youth**; County applicability **All**; How targets overlap **Not yet established**; Related obligations; Applicability conditions; Source references. Notice **Illustrative values; source checks are still needed.** |
| Exclusive preference | Which purchases are restricted?; Eligible suppliers; Conditions | Restriction code; Category; Method; Currency; Comparison; Amount; Funding-origin condition; Local-origin condition; Eligible party classification; Source reference. Amount blank. Notice **Required conditions not yet completed.** |
| Preference margins | Margin; Qualifying conditions; Evaluation basis | Scheme; Procedure; Margin; Origin condition; Shareholding from; Shareholding to; Lower bound included; Upper bound included; Evaluation basis; Source reference. Margin blank. Notice **Used during evaluation; this does not decide supplier entitlement in Planning.** |
| Market price index | Published prices; Publication and coverage | Item; Category; Unit; Currency; Price; Observation date; Publication date; Publication reference; Applies from; Applies until. CONFIG has no price rows and **Not published**. |
| Approval applicability | Entity facts; Plan approval authority; Supporting instrument | Entity type **National Government Ministry**; County applicability **Non-county**; Required entity evidence **Not yet established**; Plan approval authority **Cabinet Secretary**; Required business capacity **Configured statutory capacity**; Source reference. |
| Publication obligations | What must be published or reported?; Who is responsible?; When and where? | Obligation **LAW-OB-009**; Accountable actor; Recipient; Channel; Trigger; Due rule; Days; Reporting period; Which date determines the rule to use?; Integration or evidence requirement; Source reference. Notice **Operating-model verification required.** |

Bound status choices: **Value specified**, **No limit stated in the verified source**, **Not yet established**. Value basis choices where applicable: **Per request**, **Per item per financial year**, **Approved budget allocation**. Reservation measurement choices **Annual procurement budget**, **Annual procurement value**. Overlap choices **Targets apply independently**, **Targets are mutually exclusive**, **Specified overlap**, with a separately labelled Related obligations selector for the last. The incomplete display value **Not yet established** is not an additional governed overlap enum.

Method fact choices: Category; Estimated package value; Cumulative item value for the financial year; Approved budget allocation; Funding origin; County status; Result of the supported method check. Comparisons: Equal to; Not equal to; In; Not in; Less than; Less than or equal to; Greater than; Greater than or equal to. Stage choices: Planning; Initiation; Tender; Contract. Evidence choices: Record; Attachment; Owner decision. The source-supported selector choices and available fact/comparison combinations belong to the supported rule kind.

### 10.8 C03-D / CUX-04 — Source checks and history

Heading **Check sources**. Fixed target facts in separate rows: Record kind **Procurement rule**; Rule **Method eligibility**; Version **1**. Result select: **Source check needed**, **Sources verified**, **Source check rejected**; CONFIG selection **Source check needed**. Source-check date **12 Sep 2026**. These are presentation labels for the existing outcomes, not an approval workflow.

| Group | Field labels | CONFIG pending specimen |
|---|---|---|
| 1. Source documents | Instrument and edition; Provisions; Source document | Blank inputs; document status **Not attached** |
| 2. What the source establishes | Effective dates and amendments; Applicability and date basis; Interpretation evidence | Blank inputs |
| 3. Outstanding work and record | Unresolved points; Reason for this entry | Unresolved points **The applicable amended source and interpretation have not been established.** Reason **Record the remaining verification work for this reference version.** |

Visible pending explanation **This records outstanding work; it does not verify the rule.** Footer **Cancel** / **Record source check**. Verified-selected incomplete variant: visible **Complete the source, applicability and interpretation evidence before recording a verified source check.**, errors at the missing controls. No successful verified fixture is invented. Rejected variant reason specimen **The cited source does not establish the stated applicability.**; notice **Affected new decisions are blocked; historical evidence is retained.**

Rule/profile/calendar detail shows Source check, Details and Procedure support separately wherever relevant. **Sources verified** is not a global Ready state. A missing payload field on saved detail has **Create new version**; missing check evidence has **Check sources**.

History tables:

| Table | Columns |
|---|---|
| Version history | Version; Applies from; Applies until; Recorded at; Recorded by; Earlier versions replaced; Source check; Action |
| Source-check history | Result; Source-check date; Recorded at; Recorded by; Evidence; Reason |
| Usage | Consumer; Record reference; Exact version; Decision date; Action |

Authorised evidence detail labels **Source check at the decision** separately from **Current source check**. Current rejection notice **Affected new decisions are blocked; historical evidence is retained.** No restore-overwrite action.

### 10.9 C04 — Procurement schedules and working-day calendars

Heading **Procurement schedules**. Description **Set the time intervals used to prepare procurement schedules.** Action **Add procurement schedule**. List specimen uses separate columns Name **Open Tender — goods**; Method **Open Tender**; Procedure **Planning example**; Category **Goods**; Version **1**; Applies from **1 Jul 2027**; Applies until **30 Jun 2028**; Source check **Source check needed**; Action **View**. A distinct unsupported specimen shows Procedure support **Not available in this release**. The Planning example is presentation text, not a verified executable procedure.

Detail uses the same separately labelled facts plus **Which date determines the rule to use?** value **Invitation date — source check needed**. Sections **Milestones**, **Time intervals**, **Sources and interpretation**, **Usage and history**. Seven milestone rows:

| Milestone | Order | Applies | Role in this schedule |
|---|---|---|---|
| Invitation or advertisement | 1 | Yes | Starting date |
| Bid opening | 2 | Yes | Calculated milestone |
| Evaluation completion | 3 | Yes | Calculated milestone |
| Tender award approval | 4 | Yes | Calculated milestone |
| Notification of award | 5 | Yes | Calculated milestone |
| Contract signing | 6 | Yes | Calculated milestone |
| Delivery or implementation completion | 7 | Yes | Source requirement boundary |

The interval table has **From**, **To**, **Days counted**, **Minimum status**, **Minimum days**, **Maximum status**, **Maximum days**, **Default days**, **Default basis**. A selected interval editor uses those fields separately plus **Source reference**, **Override allowed** and **Counting convention**. To avoid inventing endpoints absent from the pending predecessor fixture, the CONFIG rows are:

| From | To | Days counted | Minimum status | Maximum status | Default days | Default basis |
|---|---|---|---|---|---|---|
| Not yet established | Bid opening | Calendar days | Not yet established | Not yet established | 21 | Not yet established |
| Not yet established | Evaluation completion | Calendar days | Not yet established | Not yet established | 30 | Not yet established |
| Not yet established | Tender award approval | Calendar days | Not yet established | Not yet established | 5 | Planning assumption |
| Not yet established | Notification of award | Calendar days | Not yet established | Not yet established | 2 | Planning assumption |
| Not yet established | Contract signing | Calendar days | Not yet established | Not yet established | 14 | Not yet established |

Minimum/Maximum days fields are blank in this pending specimen. Missing endpoint/default-basis values remain visible under **Details to complete**. Display **Estimated delivery period default: Not set** as a separate labelled fact. Notice **This schedule cannot support Plan submission until its required details and source checks are complete.** Legal-default basis options are **Legal requirement** and **Planning assumption**. The figures above remain illustrative, not production deadlines or legal defaults.

New editor heading **Add procurement schedule**; controls Name, Method, Procedure, Category; common version/date/applicability/source fields from §10.6; milestone and interval controls above. Footer **Cancel** / **Save schedule version**. Saved detail actions **Create new version**, **Check sources**, **View usage and history**. New-version footer **Cancel** / **Save new version** with Earlier versions this replaces and Reason for change. Empty heading **No procurement schedules yet**; text **Add a schedule for a procedure supported by this release.**; action **Add procurement schedule**.

Working-days variant: **Days counted: Working days**, **Working-day calendar** selector and **View calendar**. Missing-calendar message **Select a verified working-day calendar for this interval.** Calendar page remains in Procurement settings, with heading **Working-day calendar**; fields Calendar name; Applies from; Applies until; Weekend days; Holiday date; Holiday name; Source evidence; Earlier versions this replaces; Reason for change. Calendar fixture supplies weekend choices Saturday/Sunday, no holiday rows, Source check **Source check needed**; other unsupplied editor fields blank. Saved missing values read **Not yet established**. Footer for new calendar **Cancel** / **Save calendar version**. Saved actions **Create new version**, **Check sources**, **View usage and history**. Each holiday row has Add row/Remove row only in the unsaved editor. No legal-completeness claim from this specimen.

### 10.10 Reminders

Heading **Reminders**. Field **Remind users this many days before a milestone**, value **7**, numeric input. Unit **Calendar days**. Helper **This changes reminder timing, not procurement deadlines.** Second helper **Use 0 to begin reminders on the milestone date; overdue reminders still apply.** Footer **Save changes**. Error **Enter a whole number from 0 to 365.** No editable deadline or notification-history action.

### 10.11 Common states, AUTH tabs and business evidence

| State / audience | Heading and text | Actions |
|---|---|---|
| Loading | Loading System setup… | None |
| Non-technical actor denied setup | You do not have access to System setup. / This area needs Administrator or System Manager access. / Ask your KenTender administrator to grant it. | None |
| Load error | System setup could not be loaded. / Try again. If the problem continues, contact support. | Try again |
| Empty years | No financial years yet. / Add the first financial year for this site. | Add financial year |
| Stale form | This information has changed since you opened it. / Review the latest details before saving. | Review latest details |
| Saved immutable version | This version is read-only. / Create a new version to change it. | Create new version |
| Rules overlap | Rule versions overlap for the required date. | Review versions |
| No date coverage | No rule covers the required date. | Review versions |
| Missing root — Administrator | The top-level organisation unit is missing. | Repair organisation root |
| Missing root — System Manager | The top-level organisation unit is missing. / Ask an Administrator to repair it. | None |
| Ambiguous structure | The organisation structure cannot be repaired automatically. / Contact support with the listed conflicts. | No repair action |
| Business Plan approval blocked by evidence | Plan approval is unavailable because the approval authority's supporting evidence is incomplete. / Ask your KenTender administrator to complete it. | Only the actions supplied by the owning business record |
| Optional index absent | No price index has been published for this period. | None required |

The business/Auditor evidence composition is placed inside its owning record, not in a new setup page. Fields **Rule**, **Version used**, **Decision date**, **Source check at the decision**, **Current source check** have separately labelled values from that named owner fixture. No fabricated decision or new business action is supplied by CONFIG. Diagnostic details are under **Details**, separate from the plain explanation.

Organisation structure and Users and responsibilities: include the supplied AUTH v1.7 owned design compositions alongside C01–C04, with the shared five-tab header above. This does not introduce an alternative assignment form. Missing-root variants are as above. The Administrator repair control is a domain recovery action, not a nested-set editor; no raw tree fields or generic repair tools are drawn. Technical search is supplied by the current standard's owner surface, not a duplicate CFG screen.

### 10.12 Complete artboard inventory

Every row below is required design evidence; the four usability-amendment sketches are specimens, not substitutes for this inventory.

| Group | Required artboards / variants |
|---|---|
| C01 | Configured entity; first run; saved structural setup with source checks pending; county/type conflict; authority missing. |
| C02 / CUX-01 | Year overview and detail with all three activities; empty years; add-year preview; duplicate; missing Company; disabled years; blocked disable; eligible disable; re-enable. |
| C02 / CUX-02 | Each of six open/close forms; deadline edit; no closing date; cross-year replacement; exact expiry; stale submission settings. |
| C03-A | Funding list, empty, add, edit, disabled and duplicate. |
| C03-B / CUX-03 | Rule list, empty, set-only, add-first-version, each kind's add form, partial save, saved detail, rename, new version, replacement impact, date gap, overlap, stale input. |
| C03-C | All seven rule kinds and Method-condition groups; missing bounds, unsupported condition, optional index absence and publication operating-model gap. |
| C03-D / CUX-04 | Pending source check, verified-selected incomplete evidence, rejected source check, immutable version history, check history and historical/current evidence comparison. |
| C04 | Schedule list/empty/detail/add/successor, seven milestones, interval detail, missing support, missing endpoint/default/source, working-day calendar missing/add/detail/successor/history. |
| Reminders | Unchanged, edited, zero and invalid range. |
| AUTH / common | Owned organisation and responsibility screens; both root-repair role variants; loading, inline denied, load error and stale form. |
| Owner evidence | Named business blocked-action and Auditor historical-read compositions; technical-read routes conforming to KT-STD §3A.6. |

Do not draw setup approval controls, a generic all-settings editor, JSON/scripts, a global year or entity selector, legal-validity checkbox, invented implementation switch, price-index waiver for mandatory rules, or unsupplied reference/usage counts. Critical issues appear above the relevant action; source history and long supporting explanations use structured labelled detail.

## 11. Functional interaction requirements — excluded from design prompts

Shared page behavior, accessibility, verdict resolution and technical read are inherited from KT-STD-001 v1.5 §§3–3A. CFG-specific interactions below are implementation requirements, not design-prompt content.

### 11.1 Task flow and supporting detail

Every focused form has one primary final action. Compute previews in the form; do not require a separate preview-button/confirmation chain. Keep blockers, replacement consequences and the affected activity/year above the action. Supporting data uses labelled rows under short headings; do not concatenate unrelated facts. Expand the group containing an error. Long source explanations remain available without dominating ordinary setup tasks.

| Task | Required behavior |
|---|---|
| Entity setup | First save remains atomic entity/root creation. Structural success and pending Plan-approval evidence are separate. All routes honor first-run/missing-root restrictions without introducing a setup approval process. |
| Add year | Debounced/server preview shows native generated year and period; Company is resolved by its owner. Duplicate links to the existing authorised year. No date or Company editing in this task. |
| Submission periods | Each named action has one form with exact FY/activity, reason and optional EAT deadline. Opening another year previews and commits the same-module swap. Closing/changing time never changes another module. |
| Year disable/re-enable | Separate from submission actions; exact native/KenTender blockers shown before disable. Disabled historical years remain discoverable. |
| Funding source | Name and availability only. Direct save; no added reason/approval. Preserve ID and historical snapshots, with BUD eligibility effects left to BUD. |
| Add rule | One form with relevant fields; follow §7.3 for prevalidation, separate command keys, partial failures and resumption. Keep the stable key visible under Rule identifier; generated IDs are never editable. |
| Correct version | Copy editable values from the selected predecessor, preserve exact replacement IDs and require a newly entered reason. Save creates another immutable version. |
| Check sources | Open on an exact, read-only target kind/version. Enter actual check date and evidence; append an event against the expected prior event. Successful version persistence is not successful source verification. |
| Schedule/calendar | Show endpoints, bounds, default basis, counting and support distinctly. Open calendar only for working-day context. Saved versions use the same correction/source-check pattern. |
| Reminders | One scalar save; retain calendar-day unit, 0–365 and zero semantics. No task creation or deadline mutation. |
| AUTH-owned tabs | Use owner commands, assignment scopes, eligibility and artboards. Missing-root repair remains Administrator-only, never generic tree repair. |

### 11.2 Current facts, forms and failures

Preselect already known context: year, activity, selected kind/version. Do not populate reasons, legal values, check dates or verification results from CONFIG examples in production. The user-defined reference key may be suggested from the entered name and edited before initial creation; validate uniqueness/format through the existing owner contract. The key and generated identity remain distinct, and key/kind are immutable after first version.

Opening/changing an intake uses its current module token. The owner command rechecks the current server instant after acquiring the relevant control; at the deadline it is closed, independent of cleanup. Returned-plan corrections and accepted-plan updates retain their PLN predicates. The browser does not authorise an initial action or convert closure into a record lifecycle transition.

Show a preview's schema errors, incompleteness and coverage separately. A pending successor replacing usable coverage must show “Saving this replacement will block {affected action} until its sources are verified” before save. Use known authorised usage; explicitly report unavailable usage rather than show zero. Display actual old/new dates and matching scope. The commit still rechecks current tokens, overlap, supported schema and authoritative owner facts.

A structurally valid incomplete version may be saved Pending under §4.6. Unsupported structure cannot be saved by removing validation. On saved records, missing legal payload is corrected by a new version, while missing verification evidence is recorded through a new source-check event. No source-check form mutates the payload or treats approval of LAW/SEED/this document as verification.

Preserve unsaved values on validation, stale-token and retry errors. For concurrent changes, reload authoritative details and present the retained proposal for explicit review; never silently merge, overwrite or resubmit it. Return focus to the relevant trigger after cancel and to the first actionable error after failure. Success retains current list/detail location and displays the exact changed row/version. Do not claim a multi-command creation rolled back when its first command succeeded.

### 11.3 Actor-specific evidence and recovery

Business/Auditor evidence stays in the owner's authorised record. Show the problem, affected action and maintainer contact; preserve owner-permitted return/correction. Do not make a business user maintain settings or acquire technical access to finish an ordinary task. Exact historical version and decision-time verification remain separately labelled from current warnings. Source-confidence withdrawal does not recalculate old approvals.

CFG setup commands remain available only through the explicit domain authority exception in §3.1. Technical business reads inherit KT-STD §3A.6 by reference, including record-type/read-entry registration. No local status whitelist, masking exception or bespoke technical queue/search is introduced.

### 11.4 User validation and browser evidence

Browser evidence must cover keyboard/focus, exact-error association and announcement, pending buttons, 200% zoom, narrow year cards/all three submission activities, readable rule/schedule tables and a footer that does not obscure the last field. Critical consequences remain visible even when supporting sections are collapsed.

| Participant | Scenario | Evidence to record |
|---|---|---|
| Administrator / System Manager new to KenTender | Add year; open departmental submissions; change the deadline. | Task completion, navigation detours, requests for explanation, and correct prediction of year/module effects without learning “intake”. |
| Setup maintainer | Disable a source; locate its historical record. | Understands selection availability versus existing budget/record history. |
| Setup maintainer with source material | Correct a rule, recover a partial save, record pending evidence. | Distinguishes saved, verified, complete and supported; recognises replacement effect and finds missing evidence. |
| Setup maintainer | Inspect a working-day schedule. | Can explain interval endpoints, legal limits, assumptions and calendar/support dependencies. |
| AO / business reviewer | Encounter a configuration block. | Can identify cause, owner and permitted next step without opening System setup. |
| System Manager / Auditor | Missing-root escalation / past decision with current source rejection. | Correct repair-role boundary and past-versus-current evidence interpretation. |

Record misunderstandings and revise the affected screen before accepting usability. Confusing save with verification, or a module submission change with a global FY switch, is a failed walkthrough. The approved amendment, closed specification and four sketches alone do not constitute user-validation evidence.

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

The approved shared fixture standard is KT-STD-001 v1.5 §8. CFG11-EX-002 expressly preserves shared UOM usage. CONFIG-FIRST, CONFIG-SWAP and CONFIG-EMPTY are isolated UI scenarios defined in §10.1, not additions to the integrated positive seed. CONFIG-SWAP has one DPP year open, never two. Production forms do not adopt the specimen reasons/check dates as automatic defaults. Technical fixtures follow KT-STD §3A.6.

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
| CFG10-AC-019 | CFG-AC-019 | Opening needs submission confers no business authority; Administrator business-record access conforms to KT-STD-001 v1.5 §3A.6, with no fixture business-role grant. |
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

Use focused tests for changed invariants, then affected cross-module/release gates under KT-STD-001 v1.5. No old green test overrides the amended contract.

### 14.4 Approved usability acceptance criteria

IDs CFG-UX-AC-01–28 are carried from the approved amendment without renumbering. The current standard citation in 24 replaces the earlier AUTH-only technical-read formulation.

| ID | Required result |
|---|---|
| CFG-UX-AC-01 | All five existing tab anchors and exact record/version links survive refresh and Back; visible titles use the new terminology with no duplicate setup shell. |
| CFG-UX-AC-02 | First-run entry, missing-root restrictions and ordinary deep links behave as specified; pending source checks never force an unrelated setup wizard. |
| CFG-UX-AC-03 | Configure site creates entity/root atomically, retains immutable code and displays source-check gaps independently of structural success. |
| CFG-UX-AC-04 | County/type conflicts and required Plan approval authority remain explicit; no silent type inference, route exemption or additional approval is introduced. |
| CFG-UX-AC-05 | Year creation shows the generated July–June period, exact duplicate/Company defects and no editable dates or local Company selector. |
| CFG-UX-AC-06 | All three submission periods are visible at desktop and narrow widths; disable/re-enable honours native and KenTender blockers and retains shared records. |
| CFG-UX-AC-07 | Opening, closing or changing a deadline requires one focused final action with reason; cross-year replacement identifies the affected year and changes only that module atomically. |
| CFG-UX-AC-08 | Expiry at the exact instant and stale control tokens are enforced server-side; inputs remain recoverable and permitted owner corrections/updates remain accessible. |
| CFG-UX-AC-09 | Funding creation/edit requires only the baseline name/availability fields, with normalized duplicate validation and no new approval/reason. |
| CFG-UX-AC-10 | Disabled sources cannot be newly selected where the catalogue governs selection; exact-ID historical reads and frozen names remain intact, with BUD eligibility still owner-controlled. |
| CFG-UX-AC-11 | Add rule renders one kind-specific form and prevalidates content; successful set/version commands return the exact new immutable version without inventing a Draft state. |
| CFG-UX-AC-12 | Set-success/version-failure and ambiguous-timeout scenarios retain/recover the original identity and keys; retry never duplicates a reference set, and an empty set can be completed later. |
| CFG-UX-AC-13 | Every field in all seven typed rule kinds remains represented with readable labels and supported selectors; precision, condition grouping, bound states and date bases are unchanged. |
| CFG-UX-AC-14 | No illustrative threshold, evidence placeholder, missing bound or approved document produces Verified/usable configuration; optional price-index absence stays informational. |
| CFG-UX-AC-15 | Every correction creates a new version with exact predecessor linkage and a real reason; old payloads and decision-time verification pins remain readable. |
| CFG-UX-AC-16 | Impact preview identifies coverage and known usage; a pending replacement of usable coverage warns before save and blocks affected new use without silently falling back. |
| CFG-UX-AC-17 | Check sources fixes target kind/version, groups all required fields and appends the exact selected outcome with actual recorder/check/recording evidence. |
| CFG-UX-AC-18 | Verified requires complete supported evidence and no unresolved mandatory point; pending/rejected remain distinct, and verification cannot change immutable payload fields. |
| CFG-UX-AC-19 | Schedule summary names each interval’s endpoints and separates defaults, bounds, counting and assumption/legal basis; invitation anchor and completion boundary remain distinct. |
| CFG-UX-AC-20 | Working-day rules require a supported verified exact calendar version; empty holiday examples, unsupported procedures and missing defaults cannot pass by display labels. |
| CFG-UX-AC-21 | Reminder control states calendar days and preserves default 7 with integer range 0–365; zero behavior is explicit. |
| CFG-UX-AC-22 | Reminder save changes subsequent evaluations only; it neither changes business deadlines nor creates duplicate tasks/notices. |
| CFG-UX-AC-23 | Both setup roles see authorised owned AUTH tabs; missing-root repair is actionable only for Administrator and refuses ambiguous trees. |
| CFG-UX-AC-24 | Technical access conforms to KT-STD-001 v1.5 §3A.6, with shared search and read-entry registration; business/Auditor reads stay owner-authorised and cannot mutate setup. |
| CFG-UX-AC-25 | Each listed failure maps to a short problem/action message with current scope/date where relevant; saved, verified, complete and supported are not collapsed into one status. |
| CFG-UX-AC-26 | Business users receive an actionable owner-routed explanation inside their record; denied setup routes reveal no protected tabs/data and name the required technical roles. |
| CFG-UX-AC-27 | Critical impacts/errors remain visible; supporting detail uses structured labels. Keyboard, focus return, first-error focus, 200% zoom and narrow layouts have recorded browser evidence. |
| CFG-UX-AC-28 | The full CFG v0.11 incorporates all 14 usability changes alongside retained baseline requirements and dependencies; representative-user evidence is recorded separately from document approval. |

### 14.5 Standards-adoption acceptance criteria

| ID | Required result |
|---|---|
| CFG11-AC-029 | Current control, authority, design, interaction and release references cite approved KT-STD-001 v1.5; v1.4 references appear only as historical trace, not the current standard. |
| CFG11-AC-030 | CFG record types/read entry points are registered with the KT-STD §3A.6 shared search and conformance mechanism; CFG-XD-002 owner specification and actual implementation evidence are recorded before release. |
| CFG11-AC-031 | The three §3.1 exceptions are explicit and narrowly enforced: authorised setup writes remain operable, unrelated native UOMs remain usable, and missing-root recovery exposes no generic nested-set controls. |
| CFG11-AC-032 | The design package consists of KT-STD v1.5 §2 plus CFG §10, with runtime behavior confined to §11; each independent visible fact has its own label and no fixture/diagnostic internals are rendered as product content. |

### 14.6 Additional focused smoke sequence

1. Walk all everyday tasks as Administrator and System Manager, including the differing root-repair outcomes.
2. Exercise Add rule set-success/version-failure, exact-key replay and empty-set resume; confirm one set and exact saved version with no misleading success.
3. Correct a usable rule with a pending successor, inspect the inline consequence and attempt the affected owner decision; retain past evidence.
4. Walk source-check Pending, Verified-incomplete and Rejected outcomes; distinguish payload correction from evidence recording.
5. Inspect schedule endpoints, explicit missing values and working-day calendar; retain unsupported-procedure blocks.
6. Run the §11.4 representative-user tasks and the §3A.6 conformance gate, including shared technical search registration; record results against individual acceptance IDs.

These supplement §14.3 and the retained 59 criteria. No test completion is asserted by this document.

## 15. Implementation constraints and required owner work

Apply KT-STD-001 v1.5 §§4–6. Use the existing Frappe Single, native ERPNext extensions, shared Vue Desk mount and AUTH hooks. Inspect the repository before claiming current field names, DocType migrations, native Company association or UOM precision mapping. Native writes and fixture/bootstrap paths must enforce the same invariants; a page-only check is insufficient.

Use one lockable module-control row rather than relying on an unavailable database-specific partial index. All supported write paths participate in the lock/transaction; add appropriate DB uniqueness constraints for module key, FY identifiers, reference keys, set/version numbers and funding normalized name. Establish cross-owner lock ordering for CFG/BUD/PLN/REQ, meaningful rollback tests and exact immutable evidence persistence.

| Dependency | Exit evidence |
|---|---|
| LAW verification | LAW-V-001–011 resolved for each production-used rule; current edition, applicability/date basis, sources and interpretations recorded. Unneeded/future rules remain explicitly unsupported, not defaulted. |
| BUD provider amendment | Complete annual Budget basis, source-OU eligibility, atomic decision validation and precision contracts; actual native Company association verified. |
| NDS/PLN intake consumers | Exact initial action predicates and correction exceptions, close-instant checks in owner transactions, independent availability. |
| REQ/TPR/TPUB consumers | Current config validation and immutable evidence pins at relevant positive decisions; no profile admission without an implemented procedure. |
| AUTH/KT-STD | Approved KT-STD v1.5, current route/capacity mappings, shared five-tab shell, domain exceptions, Technical record search/conformance registration and CFG-XD-002 owner evidence. |
| Native UOM/calendar support | Inspected field/precision mapping and supported source-verified counting/calendar provider; no assumed native fields. |
| SEED date/scenario correction | CFG-XD-001 resolved in a controlled matching fixture amendment before affected positive-chain evidence. |
| Government operating model | LAW-V-008/LAW-OB-009 evidence and permitted integration/handoff design; no configuration checkbox used as authorization. |

Release requires actual schema/service/UI inspection, focused and affected contract tests, production asset build, applicable full artboard comparison and a dependency-aware cutover scan. Preserve native accounting/HRMS and immutable historical records. This document does not supply a deployed schema or claim integration tests passed.

Current sibling-document compatibility must be checked against NDS v1.12, STR v1.8 and BUD v1.9, the consolidated approved requirements available in this review, while preserving their owner boundaries. PLN v1.19 and REQ v1.8 remain their separately controlled proposed successors unless separately approved; this CFG consolidation does not alter their status. Prior follow-up rows are documentary lineage, not proof that every provider contract or integration test is complete.

Add focused failure/replay checks for §7.3 and affected cross-app tests for the standards/CFG changes. Complete the §10 inventory and §11.4 user walkthroughs in the existing shell. No second prototype stack or duplicate common technical-read implementation is authorised.

## 16. Prohibited shortcuts

Do not reintroduce PE/FY context records, multiple PEs, global FY authority, local approver registries, Reference Data Manager, configuration approval workflow, module window lifecycles or duplicate ERPNext Company/Fiscal Year/UOM catalogues. Do not expose raw policy scripts or an arbitrary JSON configuration editor as the business surface.

Do not rely on hourly expiry, browser time, old cached rules, method names or latest-version sorting for a positive decision. Do not overwrite referenced versions, treat missing bounds as unlimited, use optional price-index behavior for mandatory reservation rules, infer candidate entitlement in Planning or calculate actual procurement achievement from a Plan designation.

Do not claim a source is verified through an unsupported checkbox, an approved fixture or this document's approval. Do not change fiscal-year dates to accommodate an inconsistent example. Do not remove native accounting routes or disable unrelated UOMs while removing retired KenTender surfaces.

Inherit the product-wide prohibitions from KT-STD-001 v1.5 §§2.3 and 10, subject only to the explicitly named CFG domain exceptions in §3.1. Do not collapse saved, sources verified, details complete and implemented support into one misleading badge. Do not seed reasons/source-check dates into production forms, silently duplicate a rule after a partial save, or replace a named owner issue with a generic “contact support” dead end when an authorised next step is known.

## 17. Traceability and full change register

### 17.1 Precedence and scope of amendment

AUTH v1.7 supplies the inspected authority baseline; approved KT-STD v1.5 controls shared design/verification and §3A.6 technical read, subject to the explicit CFG §3.1 domain exceptions; approved LAW v1.1 identifies source/application verification; this CFG successor controls configuration schemas/surfaces; each business module controls its lifecycle. Approved SEED v1.3 controls shared fixtures subject to its explicitly retained prerequisites. When a precise inconsistency is found, record it and amend the owner; do not reinterpret its approval as permission to bypass a domain guard.

The retained v0.10 work implemented the CFG document requirements from PLN v1.18 §17.2 and FU-22. This successor incorporates the approved usability amendment and KT-STD v1.5 adoption. It preserves earlier retirement decisions for CTX-CHG-001 and obsolete KenTender registers, while making current ownership/implementation gaps explicit. No external file is claimed updated by this document alone.

### 17.2 Retained v0.10 changes for re-implementation

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

### 17.3 Approved v0.11 changes for re-implementation

All rows are requirements dispositions, not claims that code has been changed. The first 14 preserve the approved usability amendment IDs; the final row records the additional standards instruction. §10 replaces the predecessor UI contract in full so implementers do not choose between conflicting layouts.

| ID | Approval trace | Predecessor defect / gap | Required replacement | Target | Acceptance |
|---|---|---|---|---|---|
| CFG11-CHG-001 | CFG-UX-001 | Routine and specialist tasks share technical section names; §§9–10.1. | Keep five tabs/routes; use Financial years, Submission periods and Procurement schedules in display; short purpose per section; no forced wizard or score. | §§9–11; shell/navigation artboards | CFG-UX-AC-01–02 |
| CFG11-CHG-002 | CFG-UX-002 | First-run success and approval applicability are easy to conflate; §§4.2, 10.2. | Plain entity questions, explicit county answer, structural save result separate from outstanding source checks; retain atomic root creation and immutable code. | §§8, 10.2; entity variants | CFG-UX-AC-03–04 |
| CFG11-CHG-003 | CFG-UX-003 | FY administration mixes dates, accounting and intake; §§4.3, 10.3. | Generated year preview with owner-resolved Company; no date edits; all three submission statuses visible; separate disable/re-enable with blockers and native links. | §§10.3, 11; CUX-01/year detail | CFG-UX-AC-05–06 |
| CFG11-CHG-004 | CFG-UX-004 | Intake language and nested actions obscure effects; §§5, 7.1, 10.3. | One focused open/close/deadline form with named activity, EAT deadline, reason and inline cross-year consequence; atomic same-module swap; preserve owner correction exceptions. | §§8, 10.4, 11; CUX-02/expiry/stale variants | CFG-UX-AC-07–08 |
| CFG11-CHG-005 | CFG-UX-005 | Funding enabled flag can be mistaken for financial approval; §§4.5, 10.4. | Available for new selection; one name/availability form, no added reason or approval; disabled/historical source remains resolvable. | §10.5; funding variants | CFG-UX-AC-09–10 |
| CFG11-CHG-006 | CFG-UX-006 | Reference set/version split exposes storage mechanics; §§7.1–7.2, 10.5. | Add rule as one typed form; prevalidate, create set then save version with separate keys/results; preserve/reuse set on partial failure and offer Add first version. | §§7.3, 10.6, 11.2; creation/retry | CFG-UX-AC-11–12 |
| CFG11-CHG-007 | CFG-UX-007 | Technical labels dominate rule editors; §§4.7, 10.5–10.6. | Kind-specific field groups and readable date/condition/bound/target labels; expose exactly seven Rule kind choices and keep Method-condition groups/rows embedded within Method eligibility; retain every typed field, exact decimal and source requirement; no legal defaults. | §§8, 10.6–10.7; all rule kinds | CFG-UX-AC-13–14 |
| CFG11-CHG-008 | CFG-UX-008 | Version correction and impact demand model knowledge; §§4.6, 5, 10.5, 10.7. | Create new version with copied content, explicit predecessor/reason and inline refreshed impact. Preserve exact history; show pending replacement block before save. | §§10.6, 10.8, 11–12; CUX-03/history | CFG-UX-AC-15–16 |
| CFG11-CHG-009 | CFG-UX-009 | Full-width verification form lacks a reading hierarchy; §§4.6, 10.7. | Check sources with fixed target/version, three evidence groups, plain result labels and explicit effect. Append event; incomplete immutable payload corrected separately. | §§8, 10.8; CUX-04/outcome variants | CFG-UX-AC-17–18 |
| CFG11-CHG-010 | CFG-UX-010 | Schedule intervals and calendar rules are hard to interpret; §§4.8, 10.8. | From/To summary with default, required bounds and day type; assumption labels; calendar opened in context; distinguish implementation support from evidence and completeness. | §10.9; schedule/calendar variants | CFG-UX-AC-19–20 |
| CFG11-CHG-011 | CFG-UX-011 | Reminder threshold is internal terminology; §§4.9, 10.9. | Days-before-milestone wording, calendar-day unit and explicit zero behavior; one save with retained 0–365 validation. | §§8, 10.10; reminder variants | CFG-UX-AC-21–22 |
| CFG11-CHG-012 | CFG-UX-012 | AUTH tabs and technical-read journeys may be omitted from CFG review; §§6, 10.10. | Include AUTH-owned organisation/responsibility screens and Administrator-only repair. Cite KT-STD v1.5 §3A.6 for technical read/search/conformance; preserve setup authority with explicit exception. | §§3.1, 6, 7.4, 10.11; AUTH-owned/technical routes | CFG-UX-AC-23–24 |
| CFG11-CHG-013 | CFG-UX-013 | Error states expose mechanisms or send business users into setup; §§8, 10.10. | Message states problem, affected action and authorised next step; separate status dimensions; show diagnostic details on demand; no protected data on denied routes. | §§8, 10.11, 11.3; consumer presentation | CFG-UX-AC-25–26 |
| CFG11-CHG-014 | CFG-UX-014 | Completeness could be treated as usability proof; §§10–11, 14–15. | Short structured supporting detail, keyboard/focus/zoom/error handling and role-based scenario testing; carry full register/acceptance coverage into v0.11, retaining unresolved dependencies. | §§10–11, 14–18; inventory/evidence | CFG-UX-AC-27–28 |
| CFG11-CHG-015 | 14 September 2026 standards-adoption instruction | Current references used KT-STD v1.4 and deferred §3A.6 as uninspected. | Approve/adopt supplied v1.5; replace local technical-read restatements with controlling citation; retain explicit setup/UOM/root-recovery exceptions; record AUTH owner gap; apply closed-input rules. | Control; §§3.1, 6–11, 13–18 | CFG11-AC-029–032 |

### 17.4 Follow-up dispositions

| Item | Disposition |
|---|---|
| FU-22 | Document amendment approved on 12 September 2026. Implementation and verification remain open and require their specified evidence. |
| CFG-XD-001 | Concrete pre-FY procurement/profile mismatch in §13; matching PLN/SEED/downstream/legal reconciliation required. |
| LAW-V-001–011 | Applicable legal source/interpretation work remains owned by LAW; CFG's schema does not establish legal correctness. |
| FU-23–25 / FU-30 | BUD/NDS/REQ/TPR and precision provider amendments remain required; TPUB and STR compatibility are explicitly included where relevant. |
| FU-26 | County fixture is a separate single-entity world and gates county-support evidence. |
| FU-27 | CFG standards-citation/document cleanup is incorporated: supplied KT-STD v1.5 inspected, approved and adopted, including §3A.6. Cross-module implementation/owner conformance evidence remains open under CFG-XD-002; sibling files are not silently amended. |


| Additional item | Disposition / required evidence |
|---|---|
| CFG-XD-002 — AUTH owner specification | KT-STD v1.5 §3A.6 cites AUTH-DES-09 and AUTH §9 conformance that are absent from supplied AUTH v1.7. Obtain a matching AUTH owner specification, shared search implementation and registered conformance evidence; standard adoption is effective now. |
| CFG-UX-001–014 | Approved 14 September 2026 and incorporated into §§6–11, 14 and 17.3; implementation and user walkthrough evidence remain required. |
| Shared consumer copy | NDS/PLN/DSP and other consumers adopt readable activity/problem labels while preserving owner action predicates; changes to their controlled documents require their own amendment. |
| Latest standard going forward | Use approved KT-STD-001 v1.5 for subsequent work. Older citations preserved inside historical registers do not select an obsolete current standard. |

## 18. Approval effect

CFG v0.11 consolidates the approved CFG v0.10 contract, the System setup usability amendment approved on 14 September 2026, and the Project Owner's instruction on that date to approve and adopt supplied KT-STD-001 v1.5 and incorporate the amendment into this full document. It supersedes CFG v0.10 in full for implementation; the predecessor and approved amendment remain historical decision evidence.

The five-tab surface uses clearer task labels, one-form routine changes, complete submission-period visibility, structured rule/source/schedule detail and explicit owner-routed recovery. The full domain schema, direct configuration authority, immutable versions, append-only verification, exact applicability resolution, concurrent decision safeguards and native accounting protections remain controlling. All 14 usability changes and the standards-adoption change have implementation trace and acceptance coverage here.

Document approval does not verify legal source applicability, resolve CFG-XD-001 or CFG-XD-002, deploy schemas, complete provider integration, establish the government operating model or prove artboard/browser/user acceptance. Preserve these separate gates and record real evidence. This consolidation does not change the approval status or contents of sibling controlled documents. Adopt approved KT-STD-001 v1.5 going forward and carry any named owner correction through its own controlled update.
