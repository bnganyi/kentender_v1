# CFG-CHG-002 — Site Configuration and System Setup

**Current approval record — 1 October 2026.** The Project Owner instructed: “Mark all the proposed documents as approved”. This approves CFG-CHG-002 v0.16 in full, including its incorporated amendments. This record supersedes earlier pending/proposed approval wording and conditional predecessor-authority statements retained below as drafting history. Earlier versions remain historical. Approval does not establish implementation completion, test success, legal verification or production release; existing operating gates and substantive follow-ups remain in force.

| Control | Value |
|---|---|
| Document ID | CFG-CHG-002 |
| Version | 0.16 |
| Date | 25 September 2026 |
| Status | **Approved requirement — Project Owner approved 1 October 2026** |
| Approval record | Project Owner, 1 October 2026: “Mark all the proposed documents as approved”. |
| Approval basis | Retains the complete CFG v0.15 ownership correction and adds the minimum public portal support/legal-link configuration required by TPR v0.10 and BDS v0.7. |
| Predecessor | CFG v0.15, proposed 24 September 2026; retained unchanged as historical evidence. |
| Module / implementation owner | Configuration and Governance / `kentender_core`, with native ERPNext/Frappe records where they exist. |
| Change basis | Complete CFG v0.15 configuration contract plus one bounded **Supplier portal** settings section. Installed-template projection, artboards, routes and inspection acceptance remain solely with STD-TPL-001 v0.9. |
| Standards | **KT-STD-001 v1.7** is the current shared standard; **AUTH-ADR-001 v1.9** is the approved authority baseline. KT-STD v1.7 approval does not by itself claim that CFG's pre-existing presentation contract has completed a Stage 2 rewrite or representative-user verification. |
| Purpose | One usable setup surface for entity details, financial years, submission periods, funding sources, source-backed rules, procurement schedules, reminders and the public supplier portal's support/legal destinations. |
| Approval effect | On approval, supersedes CFG v0.15 in full as the consolidated configuration contract. It neither owns nor duplicates the separate **STD Templates** module. |

## 1. Governing decisions

One KenTender site represents one Procuring Entity. The entity is configured at first run and is never selected as a global context. Use ERPNext Fiscal Year and UOM, the AUTH-owned responsibility model and one System setup page. Administrator or System Manager maintains configuration directly on save; there is no configuration approval workflow, Reference Data Manager or local business-approver registry.

The five existing tabs remain. **Procurement settings** contains Funding sources, Procurement rules, Procurement schedules, Reminders and Supplier portal. The domain term ScheduleProfile remains unchanged; its user-facing section is Procurement schedules. Versioned configuration and source-verification evidence do not create Draft/Submitted/Approved configuration states.

Approved LAW v1.2 separates legal source, interpretation and product controls and records the corrected planning/actual measure distinction. A saved or approved document, configured route or successful test does not make a legal rule Verified. Missing mandatory applicable configuration blocks the affected positive business action. Optional market-price-index absence is distinct from mandatory reservation readiness.

Installed-template inspection is deliberately outside System setup. STD-TPL-001 v0.9 owns the **STD Templates** menu, `/app/std-templates` routes, installed-release projection, artboards, verification evidence and blockers. CFG continues to own effective procurement rules that Tenders snapshots, but it does not describe or project what any installed template release supports.

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
| Public supplier-portal support contact and legal/accessibility destinations | CFG stores one active bidder-safe projection. TPR/BDS render it; CFG does not own Tender content, candidate notices, portal authentication or submission. |

Excluded: installed-template inspection or administration; procurement decisions; candidate entitlement/evaluation; disposal approval-route design; accounting transactions; financial reservations; actual milestone entry; arbitrary policy scripts; electronic government-system integration implementation; and multi-entity operation. The required e-procurement operating-model review in LAW v1.2 remains a named production dependency; a setting in this page cannot authorize an independent replacement government platform.

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

KT-STD-001 v1.7 is approved, inspected and controlling. Shared design, authorization presentation, technical read, implementation and release mechanics are inherited by citation. Technical read uses §3A.6; do not maintain a weaker local grant. Its approval does not silently make an older CFG artboard Stage 2-conformant; that requires CFG-owned presentation and verification evidence. The following explicit exceptions preserve approved CFG v0.10 domain decisions under KT-STD §1 and §12:

| ID | Standard provision | CFG domain rule and reason |
|---|---|---|
| CFG11-EX-001 | §3A.6 read-only technical routes and absent commands | Administrator/System Manager retain the setup-maintenance commands assigned by CFG and AUTH; otherwise this configuration surface would have no maintainer. This exception is limited to authorised configuration/responsibility maintenance and does not grant business procurement commands. Technical business-record access remains governed by §3A.6. |
| CFG11-EX-002 | §8.5 shared UOM fixture says all other units disabled | Preserve native accounting/payroll and historical UOM usage; keep the specified procurement choices selectable through the owner adapter without blanket disabling other native units. CFG §§3, 4.4 and 13 govern this domain compatibility requirement. |
| CFG11-EX-003 | §2.3 prohibits nested-set repair controls | Retain only the Administrator-only, missing-root recovery in §4.4 and its AUTH invariants. No raw nested-set fields, general repair tool, reparent/delete or ambiguous-tree repair is exposed. This is the existing bootstrap recovery exception, not a new tree editor. |

Approved AUTH v1.9 now supplies AUTH-DES-09, the `/app/technical-search` design, the owner read contracts and the §9 registration/conformance hooks required by KT-STD v1.7 §3A.6. This resolves the former **document-owner** portion of CFG-XD-002. Actual shared-search implementation, module registration and conformance evidence remain release requirements; CFG must not recreate a parallel search or infer that documentation proves deployment.

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
| `disposal_plan` | `kentender_disposal_plan_open` | `kentender_disposal_plan_closes_at` | DSP's own intake actions/timing, to be reconciled with LAW v1.2. No Procurement Planning payload fields. |

All flags default false. For each row, add namespaced `kentender_{module_key}_intake_changed_by`, `_changed_at` and `_revision`, server-managed. Replace the old shared `kentender_flag_changed_by/at` projection with these per-module fields; migrate existing evidence with provenance rather than inventing actors. Append `IntakeChange` evidence containing module, target FY, affected previous FY if any, before/after flags and close instants, reason, actor, instant and command identity.

One mutable `IntakeControl` record per module key stores a monotonic control token and provides a unique serialization lock; it is not a window, FY wrapper or business lifecycle. Flags on native Fiscal Years remain authoritative; the control holds no duplicate open-year pointer. All writes acquire this control before touching FY flags. Opening one year atomically closes the prior open year for the same module. Needs, DPP and disposal may each have a different open year.

When opening, `closes_at` is null or strictly after the server instant. It belongs to the selected FY's intake configuration and need not fall between that FY's dates. On explicit/scheduled close, clear the current close field and preserve it in `IntakeChange`. On reaching the instant, effective intake is closed even if the physical flag has not yet been cleaned up. Hourly cleanup records the observed cleanup instant and scheduled effective-close instant separately; never backdate the audit event.

`effective_open = flag AND not FY.disabled AND (closes_at is null OR now < closes_at)`. Re-evaluate after acquiring the module control and before the dependent write. FY disable requires all flags off, no KenTender references and the native accounting validation to pass. Do not manipulate accounting dates to satisfy procurement examples.

### 4.4 Organisation Units, Company and UOM

AUTH v1.9 owns the single-root tree, descendant scope, Active/Inactive unit semantics, generated identifiers and responsibility commands, including Scheduled-only assignment updates. Use the native Frappe tree inside the existing tab. No reparent/delete controls or HRMS-department authority shortcuts.

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

Administrator and System Manager may record verification evidence under the existing maintenance authority, including evidence prepared by the responsible legal owner. The recorder is accountable for the stated check; this is not legal correctness created by a checkbox. No new reviewer role or second-person approval is introduced. Approval of LAW v1.2 is not a bulk verification event. Withdrawing confidence appends Pending or Rejected and blocks affected new positive decisions; it does not rewrite historical approvals.

### 4.7 Typed regulatory payloads

Each kind has its own validated rows. Unsupported keys/operators, free-form SQL/expressions and unknown condition codes are rejected. Source applicability is checked before values are consumed.

| Kind / row | Exact governed values and semantics |
|---|---|
| Method eligibility | `method_id`, `procedure_id`, category Goods/Works/Services, currency, nullable minimum/maximum decimal amounts with explicit inclusive booleans, `value_basis` PerRequest/PerItemPerFiscalYear/ApprovedBudgetAllocation, condition rows, required evidence and required authorization role/stage codes. Null bound means SourceNoBound only with verified evidence; otherwise status Missing. Never treat missing as unlimited. |
| Method condition | Stable `condition_code`, readable requirement text, legal reference IDs, input fact code, comparator and typed expected value, evidence type Record/Attachment/OwnerDecision, actor role code where authorization required, check stage Planning/Initiation/Tender/Contract. Supported fact/operator pairs come from the code-owned consumer registry below. |
| Reservation obligation | Stable `obligation_code`; `measure_stage` PlanningAllocation/ImplementationAchievement; percentage; `denominator_basis` EligibleCurrentAPPValue/ApplicableActualProcurementValue; eligible planned-designation codes; applicability predicates; county flag; exact overlap policy Independent/MutuallyExclusive/SpecifiedOverlap plus referenced other obligation codes; source references. Each obligation and stage is calculated separately. PlanningAllocation uses the eligible value of the exact current complete APP; ImplementationAchievement uses authoritative downstream actual procurement facts and cannot be produced from Plan estimates. |

For `EligibleCurrentAPPValue`, the consuming Planning service sums the estimated value of every current Plan Item included by the exact verified rule. The calculation stores the exact Plan Version, rule Version and per-item inclusion/exclusion evidence. Unused Budget headroom is never included. An approved APP amendment recalculates the successor snapshot. For `ApplicableActualProcurementValue`, the downstream reporting owner supplies actual procurement values with proceeding lineage; CFG does not convert planned estimates into actuals. County-resident and any other obligation retain separate bases and overlap rules.
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

### 4.9A Public supplier-portal settings

One `PublicPortalSettings` record owns only the public support contact and controlled notice destinations rendered by TPR/BDS.

| Field | Rule |
|---|---|
| `supplier_support_email` | Required verified-format organisation email; rendered as **Supplier support**. It is not a candidate notice address. |
| `supplier_support_phone` | Optional governed phone; when absent the portal omits the phone line rather than showing a dash. |
| `supplier_support_hours` | Optional plain text, maximum 160 characters; operational availability only, never a deadline extension or promise of immediate response. |
| `privacy_notice_url` | Required absolute HTTPS destination controlled or formally adopted by the Procuring Entity. |
| `portal_terms_url` | Required absolute HTTPS destination for the active Terms of portal use. |
| `accessibility_statement_url` | Required absolute HTTPS destination for the active accessibility statement/contact route. |
| `record_version`, `updated_by`, `updated_at` | Optimistic-concurrency and server-derived audit facts. |

The bidder-safe projection returns the four visible labels, safe destinations/contact text, record Version and `Complete`/`Incomplete` with exact missing fields. It contains no HTML, scripts, tracking parameters, internal contact notes or Tender-specific content. Saving a URL does not approve the legal text at that destination; the accountable Procuring Entity adopts and maintains that publication outside this simple configuration record.

Public Tender reading remains available when the projection is Incomplete. New **Start bid** and production **Submit bid** are unavailable until all required values resolve, because suppliers must have accessible support and governing notices before protected participation. Existing Drafts and receipts remain readable and unchanged. This is not a general website-content editor, consent manager, notification-preference centre or production-submission switch.

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

Mandatory reservation target missing or shortfall is blocking under the consuming PLN rule. An absent optional price index returns NotPublished with no reservation waiver. A reference status alone does not calculate the eligible current APP value, perform downstream actual-achievement measurement or determine candidate eligibility. BUD supplies the Budget ceiling and affordability facts only; it does not supply unused headroom as a Planning denominator.

## 6. Actors, permissions and segregation

| Actor | Allowed configuration work / experience | Limits |
|---|---|---|
| Administrator | Entity, years/submission periods, funding, rules, schedules, calendars, reminders, public supplier-portal settings and source-check recording; AUTH-owned organisation/responsibility maintenance. | Direct maintenance under CFG11-EX-001; exceptional missing-root repair under CFG11-EX-003. Business technical access is governed by KT-STD-001 v1.7 §3A.6. |
| System Manager | The same ordinary maintenance, public portal settings and evidence recording; AUTH-permitted organisation/responsibility work. | No missing-root repair action; show the Administrator escalation. Business technical access is governed by KT-STD-001 v1.7 §3A.6. |
| Business actors | Owner-authorised relevant values, deadlines, current issues and decision evidence inside their business record/review. | Business responsibility alone gives no setup mutation or full setup access; each owner supplies its permitted correction/return path. |
| Auditor | Owner-authorised historical configuration evidence, separating the source check used at the decision from any current warning. | No setup mutation or new unrestricted configuration browser. |
| Technical reader examining records | Inherits KT-STD-001 v1.7 §3A.6. | Search/read-entry registration is mandatory; do not duplicate the common technical-read contract here. |
| Authenticated system service | Registered reads, current decision validation and scheduled expiry under fixed contracts. | No arbitrary rule edit, business task, self-asserted legal verification or wait-for-cleanup deadline bypass. |

Setup maintenance authority is checked on every CFG command and native write. A legal adviser may prepare evidence for an authorised recorder; this creates no separate verifier role, second-person approval, AO sign-off or configuration approval chain. The recorder remains accountable for the exact source check.

Shared page verdict/navigation and technical-read rules are inherited from KT-STD-001 v1.7 §§3A.1–3A.6. The setup-specific denied state is for a user without setup authority; it is not used to deny a technical reader. Technical navigation controls such as opening a record are read affordances; domain writes remain limited to the configuration exception above.

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
| UpdatePublicPortalSettings | Support email/optional phone/hours, three required HTTPS destinations, record token | Save one complete replacement atomically; Administrator or System Manager. No legal-text editing, candidate-notice or submission-enable side effect. |

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
| GetPublicPortalSettings | Setup authority | Editable values, completeness, token and audit. |
| GetPublicPortalInformation | Public/TPR/BDS allowlisted read | Bidder-safe labels/destinations, completeness and record Version only; no setup audit or mutation authority. |

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

Apply KT-STD-001 v1.7 §3A.6 and AUTH v1.9 §8–9. Register CFG record families and their exact-version entry points with the owned Technical record search and technical-read conformance gate: site configuration; module submission controls/change evidence; funding sources; regulatory reference sets/versions/source-check evidence; schedule profiles/versions; calendar versions; reminder settings; public portal settings; and authorised audit/history views. Native Fiscal Year/Company/UOM and AUTH-owned unit/assignment registrations remain with their owners; reuse their routes instead of duplicate results.

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
| CFG_PORTAL_SUPPORT_EMAIL_REQUIRED | Enter the email suppliers should use for support. |
| CFG_PORTAL_URL_INVALID | Enter a complete HTTPS address for {notice label}. |
| CFG_PUBLIC_PORTAL_INCOMPLETE | Complete the supplier support and public-notice links before suppliers start or submit bids. |
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

One Vue 3 surface in the existing Frappe Desk shell at `/app/system-setup`. Use AUTH v1.9 and KT-STD-001 v1.7 navigation, authorization and component rules. No new SPA shell or proof-of-concept stack.

| Anchor | Tab / content |
|---|---|
| #procuring-entity | Procuring entity |
| #fiscal-years | Financial years |
| #organisation-structure | Organisation structure — AUTH v1.9's native tree and details |
| #users-and-responsibilities | Users and responsibilities — AUTH v1.9, including Scheduled-only editing |
| #procurement-settings | Procurement settings; sections Funding sources, Procurement rules, Procurement schedules, Reminders and Supplier portal |

A local section/record parameter within Procurement settings restores the selected list/detail/version on refresh and Back. Use `#procurement-settings/{section}/{id}` and optional `/versions/{version_id}` for exact version detail; sections are funding-sources, procurement-rules, schedule-profiles, reminders and supplier-portal. Calendar editing opens from a WorkingDays profile through `/calendars/{id}` inside this tab; it is not a sixth tab. `/app/system-setup/tender-formats` and its detail route are removed; authorised inspection uses `/app/std-templates` under STD-TPL-001 v0.9.

Default is the first incomplete structural setup tab; once entity/root exist, honor the requested tab, otherwise entity. Incomplete regulatory verification is shown in the affected rule/profile, not a forced wizard that prevents other setup work. First run disables the other four tabs. Missing root leaves entity/FY/procurement settings accessible but disables responsibilities and shows the AUTH repair state in Organisation structure.

Register one mount in the shared surface registries, preserve authorized native ERPNext access, and remove superseded KenTender configuration navigation without deleting native accounting routes. Back returns to Configuration and Governance. Maintain exact route/view alignment for forbidden direct loads.

Visible labels do not rename the stable anchors, service names or section keys. The existing schedule-profiles key displays Procurement schedules; Manage intake becomes Submission periods. Rule detail/source-check/new-version navigation preserves the exact selected record and version. Calendar editing remains contextual inside Procurement settings. No global setup score, extra wizard or per-role technical dashboard is introduced.

## 10. Static design contract

### 10.1 Supply, page header and fixture context

For CFG-owned artboards, supply **KT-STD-001 v1.7 §2 and CFG §10 in full** to the design tool. Do not supply only an individual subsection. KT-STD supplies the task-led composition standard, shared Desk shell, content width, typography, spacing, controls, table/card treatment, states and responsive/accessibility rules. CFG §10 supplies every CFG-specific visible label, value, order, hierarchy, action and variant. The design tool must not search §§4–9 or §§11–18, STD-TPL-001, TPR-CHG-001, BDS-CHG-001 or the installed ZIP to complete a CFG artboard.

The two AUTH-owned tabs are the only split-owner exception. Produce those artboards from **KT-STD-001 v1.7 §2 + AUTH-ADR-001 v1.9 §13 + CFG §10.1 and §10.12**. AUTH §13 supplies their tab-body compositions, including the Scheduled-assignment edit variant; CFG supplies the current five-tab page header and CFG-owned common states. Do not merge the AUTH and CFG prompts or ask the design tool to reconcile superseded wording.

The following source map is normative:

| Information needed | Supplied to the design tool from | Not supplied by / implementation authority |
|---|---|---|
| Shared task-led hierarchy, shell, type, spacing, controls, tables/cards, responsive and accessibility composition | KT-STD-001 v1.7 §2 | No module document may restate or override it silently. |
| CFG screen content, exact fixture values, placement, actions and visual variants | This §10 | Sections outside §10 are implementation and acceptance material, not missing design facts. |
| Organisation structure and Users and responsibilities tab bodies | AUTH-ADR-001 v1.9 §13, framed by CFG §10.1/§10.12 | AUTH owns the assignment composition, including Scheduled editing; CFG owns the shared System setup frame. |
| Runtime permissions, mutations, status derivation and error handling | §§5–9 and §11 | Excluded from design prompts; their visible results are already closed in §10. |

Page eyebrow **CONFIGURATION AND GOVERNANCE**. Title **System setup**. Description **Manage this site's details, financial years, responsibilities and procurement settings.** No page-header action. Five tabs in order: **Procuring entity**, **Financial years**, **Organisation structure**, **Users and responsibilities**, **Procurement settings**. Procurement settings section links, in order: **Funding sources**, **Procurement rules**, **Procurement schedules**, **Reminders**.

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

Conflict specimen: Entity type **County Government**, county answer **No**; inline message **The county answer does not match the entity details.** Missing-authority specimen: blank authority and **Select who approves this entity's Annual Procurement Plan.** Missing-root variants are specified in §10.12.

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
| Reservation rules | Measure; Annual target; What the target is measured against; Who qualifies; How targets overlap | Obligation code **ANNUAL-TARGET-EXAMPLE**; Measure **Planned allocation**; Target **30%**; Measured against **Eligible value of the current Annual Plan**; Eligible planned designation **Youth**; County applicability **All**; How targets overlap **Not yet established**; Related obligations; Applicability conditions; Source references. Notice **Illustrative values; source checks are still needed.** |
| Exclusive preference | Which purchases are restricted?; Eligible suppliers; Conditions | Restriction code; Category; Method; Currency; Comparison; Amount; Funding-origin condition; Local-origin condition; Eligible party classification; Source reference. Amount blank. Notice **Required conditions not yet completed.** |
| Preference margins | Margin; Qualifying conditions; Evaluation basis | Scheme; Procedure; Margin; Origin condition; Shareholding from; Shareholding to; Lower bound included; Upper bound included; Evaluation basis; Source reference. Margin blank. Notice **Used during evaluation; this does not decide supplier entitlement in Planning.** |
| Market price index | Published prices; Publication and coverage | Item; Category; Unit; Currency; Price; Observation date; Publication date; Publication reference; Applies from; Applies until. CONFIG has no price rows and **Not published**. |
| Approval applicability | Entity facts; Plan approval authority; Supporting instrument | Entity type **National Government Ministry**; County applicability **Non-county**; Required entity evidence **Not yet established**; Plan approval authority **Cabinet Secretary**; Required business capacity **Configured statutory capacity**; Source reference. |
| Publication obligations | What must be published or reported?; Who is responsible?; When and where? | Obligation **LAW-OB-009**; Accountable actor; Recipient; Channel; Trigger; Due rule; Days; Reporting period; Which date determines the rule to use?; Integration or evidence requirement; Source reference. Notice **Operating-model verification required.** |

Bound status choices: **Value specified**, **No limit stated in the verified source**, **Not yet established**. Value basis choices where applicable: **Per request**, **Per item per financial year**, **Approved budget allocation**. Reservation measure choices are **Planned allocation** and **Actual achievement**. Their non-interchangeable measurement labels are **Eligible value of the current Annual Plan** and **Applicable actual procurement value**. For the AGPO planning rule, the first is fixed by the controlled interpretation rather than offered as an arbitrary administrator choice. Overlap choices **Targets apply independently**, **Targets are mutually exclusive**, **Specified overlap**, with a separately labelled Related obligations selector for the last. The incomplete display value **Not yet established** is not an additional governed overlap enum.

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

### 10.10A C05 — Supplier portal settings

**Purpose.** Give suppliers one trustworthy support route and the public notices governing their use of the portal without turning System setup into a website editor.

**Fixture outside the artboard.** System Manager; Ministry of Health; 25 September 2026, 12:00 EAT; complete saved settings.

**Page position.** Inside **Procurement settings**, after Reminders. The local section navigation labels it **Supplier portal**. It is not a sixth top-level tab.

**Header.** Heading **Supplier portal**. Description **Set the support contact and public information links shown to suppliers.** No header action or readiness dashboard.

**Composition, top to bottom.**

1. Information panel: **These details appear on public Tender and bid pages. They do not change a Tender, candidate notice or submission status.**
2. Section **Supplier support** with fields in this order:
   - **Support email** `tendersupport@health.go.ke`;
   - **Support phone (optional)** `+254 20 271 7077`;
   - **Support hours (optional)** `Monday–Friday, 08:00–17:00 EAT`.
   Helper **Support hours do not extend a procurement deadline.**
3. Section **Public information** with three full-width URL controls:
   - **Privacy and data use** `https://health.example.test/kentender/privacy`;
   - **Terms of portal use** `https://health.example.test/kentender/terms`;
   - **Accessibility** `https://health.example.test/kentender/accessibility`.
   Each has secondary **Open link** only when its saved/current value is a valid HTTPS address. Opening creates no save.
4. Footer: primary **Save changes**. No Publish, Approve, Preview website or Enable bid submission action.

**Incomplete variant.** Privacy and data use is blank. Amber result above the form: **Complete the supplier support and public-information links before suppliers start or submit bids.** Inline error **Enter a complete HTTPS address for Privacy and data use.** Preserve the other values. Save remains available only after all required fields validate.

**Invalid-link variant.** Terms value `http://example.test/terms`. Inline error **Enter a complete HTTPS address for Terms of portal use.** No Open link for that row.

**Saved variant.** Green confirmation **Supplier portal settings saved.** Beneath it show **Used by Tenders and Bid Submission** as supporting text, not a readiness/approval badge.

**Narrow layout.** Stack every field and its Open link. Keep Save changes after the final field; the footer must not cover it. Do not truncate URLs without an accessible full value.

**Visual check.** A new administrator can explain where each value appears, distinguish support hours from Tender deadlines and predict that saving these settings does not publish or enable a bid.

### 10.11 STD Templates ownership boundary

Installed-template inspection is not part of System setup. Do not design or implement a Tender-format list, detail, preview or release action in this module. STD-TPL-001 v0.9 §11 is the complete design and implementation authority for the separate **STD Templates** menu and `/app/std-templates` routes.

### 10.12 Common states, AUTH tabs and business evidence

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

Organisation structure and Users and responsibilities: include the supplied AUTH v1.9 owned design compositions alongside C01–C04, with the shared five-tab header above. This does not introduce an alternative assignment form. The Scheduled responsibility-detail variant shows secondary **Edit scheduled assignment** beside **Revoke responsibility**; its focused dialog is AUTH-DES-04 or AUTH-DES-05 prefilled, titled **Edit scheduled assignment**, with the AUTH notice and primary **Save changes**. Active, Expired and Revoked details have no Edit action. Missing-root variants are as above. The Administrator repair control is a domain recovery action, not a nested-set editor; no raw tree fields or generic repair tools are drawn. Technical search is AUTH-DES-09, not a duplicate CFG screen.

### 10.13 Complete artboard inventory

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
| C05 | Supplier portal complete, incomplete, invalid-link and saved variants at desktop and narrow widths. |
| AUTH / common | AUTH v1.9 AUTH-DES-01–09: organisation structure; assign Permanent and Acting responsibility; Active and Scheduled responsibility details; Scheduled-only Edit dialog and changed-history state; revoke dialog; both root-repair role variants; loading, empty, Forbidden and load error; separate Technical record search. |
| Owner evidence | Named business blocked-action and Auditor historical-read compositions; technical-read routes conforming to KT-STD §3A.6. |

Do not draw setup approval controls, a generic all-settings editor, JSON/scripts, a global year or entity selector, legal-validity checkbox, invented implementation switch, price-index waiver for mandatory rules, or unsupplied reference/usage counts. Critical issues appear above the relevant action; source history and long supporting explanations use structured labelled detail.

## 11. Functional interaction requirements — excluded from design prompts

Shared page behavior, accessibility, verdict resolution and technical read are inherited from KT-STD-001 v1.7 §§3–3A. CFG-specific interactions below are implementation requirements, not design-prompt content.

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
| Supplier portal | One focused form saves the support email, optional phone/hours and three controlled HTTPS destinations atomically. **Open link** checks the entered destination in a new browser context without saving. TPR/BDS consume only the allowlisted public projection; no setup audit, mutation authority or submission-control value is exposed. |
| AUTH-owned tabs | Use AUTH v1.9 owner commands, assignment scopes, eligibility and artboards. A Scheduled assignment may be changed through `UpdateScheduledResponsibility`; the owner record refuses editing once the assignment has ever been Active, Expired or Revoked. Missing-root repair remains Administrator-only, never generic tree repair. |

### 11.2 Current facts, forms and failures

Preselect already known context: year, activity, selected kind/version. Do not populate reasons, legal values, check dates or verification results from CONFIG examples in production. The user-defined reference key may be suggested from the entered name and edited before initial creation; validate uniqueness/format through the existing owner contract. The key and generated identity remain distinct, and key/kind are immutable after first version.

Opening/changing an intake uses its current module token. The owner command rechecks the current server instant after acquiring the relevant control; at the deadline it is closed, independent of cleanup. Returned-plan corrections and accepted-plan updates retain their PLN predicates. The browser does not authorise an initial action or convert closure into a record lifecycle transition.

Show a preview's schema errors, incompleteness and coverage separately. A pending successor replacing usable coverage must show “Saving this replacement will block {affected action} until its sources are verified” before save. Use known authorised usage; explicitly report unavailable usage rather than show zero. Display actual old/new dates and matching scope. The commit still rechecks current tokens, overlap, supported schema and authoritative owner facts.

A structurally valid incomplete version may be saved Pending under §4.6. Unsupported structure cannot be saved by removing validation. On saved records, missing legal payload is corrected by a new version, while missing verification evidence is recorded through a new source-check event. No source-check form mutates the payload or treats approval of LAW/SEED/this document as verification.

Preserve unsaved values on validation, stale-token and retry errors. For concurrent changes, reload authoritative details and present the retained proposal for explicit review; never silently merge, overwrite or resubmit it. Return focus to the relevant trigger after cancel and to the first actionable error after failure. Success retains current list/detail location and displays the exact changed row/version. Do not claim a multi-command creation rolled back when its first command succeeded.

Supplier-portal validation is server-authoritative and repeated on every write. Normalise the support email for comparison without changing the displayed address; reject non-HTTPS, credential-bearing or malformed public destinations. Optional phone and hours may be omitted without synthetic placeholders. An incomplete configuration does not hide public Tenders or invalidate an existing supplier Draft, receipt or historical notice. It blocks only a new **Start bid** and production **Submit bid** through the owning TPR/BDS command checks, using `CFG_PUBLIC_PORTAL_INCOMPLETE`. Completing the record immediately restores those actions without republishing a Tender or rebuilding a template.

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
| Administrator / System Manager | Complete Supplier portal settings, deliberately enter one invalid link, then inspect the public Tender footer at desktop and narrow widths. | Can identify where the values are used, correct the error without losing other entries, and distinguish support/legal information from Tender publication, candidate notices and bid-submission enablement. |
| Administrator / System Manager | Edit Julia Njeri's Scheduled acting assignment, then inspect an Active assignment. | Can change the Scheduled assignment without revoking it, understands that clearing Effective from activates it immediately, sees one before/after history event and correctly finds no Edit action on an assignment that has started. |
| AO / business reviewer | Encounter a configuration block. | Can identify cause, owner and permitted next step without opening System setup. |
| System Manager / Auditor | Missing-root escalation / past decision with current source rejection. | Correct repair-role boundary and past-versus-current evidence interpretation. |

## 12. Audit and historical integrity

Every mutation records actor, target, command, expected/resulting token, exact payload/result identity, idempotency key, UTC recorded instant, outcome and material before/after facts; reasons only where specified. A replay returns the first successful evidence and creates no duplicate semantic event. Failed writes leave no partial entity/root, intake swap or version/verification result.

Immutable rule/profile/calendar versions, verification events and consumer decision pins survive all corrections. Current source-confidence withdrawal is separately visible from the earlier verification used at a decision. Entity/funding renames do not rewrite frozen legal documents. Scheduled expiry records both its intended close instant and actual cleanup instant. No administrator action creates approval evidence in another module.

Every Supplier portal update appends the prior and resulting public projection, actor, instant and record Version. Public reads expose only the current allowlisted labels/destinations and completeness; they never expose prior values, setup actors, audit events or internal record identifiers. A support or legal-link correction affects later page renders only and does not rewrite a publication, candidate-notice destination snapshot, submitted Bid, receipt or historical audit evidence.

Current decisions must serialize configuration validation through the decision transaction. A verification withdrawal/route change racing with a decision yields either the earlier valid serialized decision with its evidence, or a blocked/retry result; never a decision claiming evidence from a different configuration snapshot. Define root-lock order consistently in the affected integration pack.

## 13. Seed and fixture reconciliation

Use shared AUTH/KT-STD identities, ERPNext Company Ministry of Health, two native years FY 2026/27 and FY 2027/28, and the existing single PE/root. PE configured 29 June 2026, 10:10 EAT. Seed authority and business state through owning commands under an isolated controlled clock. No direct governed-state insertion.

At the 24 November 2026 visual fixture instant, Needs intake for FY 2027/28 closes 25 November 2026 at 23:59 EAT; DPP initial intake closes 30 November 2026 at 23:59 EAT; disposal Closed. These advance-year close instants are valid configuration and do not change the FY's July–June dates. Dispose timing examples remain separate pending the DSP owner amendment.

Seed Government of Kenya, Development partner and Appropriation in Aid funding records by stable owner IDs; keep the approved shared UOM choices selectable without disabling unrelated shared units. Calendar/profile examples and historical numeric thresholds remain Production verification pending. The approved SEED v1.3 test provenance label does not map to Verified production configuration.

**Concrete cross-document date conflict:** FY 2027/28 begins 1 July 2027. The shared laptop procurement example has invitation 15 May 2027 and bid opening 5 June 2027; infrastructure has invitation 1 May 2027 and opening 22 May 2027. These dates precede the configured FY. The supplier/profile examples also start rule applicability on 1 July 2027, so an InvitationDate resolver cannot select those versions for the May dates. Advance departmental planning in November 2026 is a different fact and does not automatically authorize pre-FY procurement proceedings.

Retain this as CFG-XD-001: PLN/SEED/REQ/TPR/LAW owners must reconcile the scenario dates, period assignment and any legally supported pre-FY procedure before claiming an integrated positive run. Do not silently move dates into 2028, relabel FY 2026/27, backdate reference coverage or waive date guards. Approved SEED v1.3 already retains actual FY-bound reconciliation as an execution dependency; this document identifies its precise conflicting values.

Seed acceptance also requires Grace's real two-OU assignments, Julia/Peter's approved authority windows, explicit infrastructure Need acceptance before certification and the approved DPP order. CFG does not manufacture missing historical evidence. A separate county-configured test world is required for county calculations; one site may represent a county entity without becoming a multi-entity site.

The approved shared fixture standard is KT-STD-001 v1.7 §8. CFG11-EX-002 expressly preserves shared UOM usage. CONFIG-FIRST, CONFIG-SWAP and CONFIG-EMPTY are isolated UI scenarios defined in §10.1, not additions to the integrated positive seed. CONFIG-SWAP has one DPP year open, never two. Production forms do not adopt the specimen reasons/check dates as automatic defaults. Technical fixtures follow KT-STD §3A.6.

Seed the complete public projection through `UpdatePublicPortalSettings` using `tendersupport@health.go.ke`, `+254 20 271 7077`, `Monday–Friday, 08:00–17:00 EAT`, `https://health.example.test/kentender/privacy`, `https://health.example.test/kentender/terms` and `https://health.example.test/kentender/accessibility`. Also provide one isolated incomplete fixture with the Privacy and data use destination absent and one invalid-link proposal using `http://example.test/terms` for form validation. These are controlled test values shared with BDS §10.1, not production defaults, legal approval or proof that the destinations are live.

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
| CFG10-AC-019 | CFG-AC-019 | Opening needs submission confers no business authority; Administrator business-record access conforms to KT-STD-001 v1.7 §3A.6, with no fixture business-role grant. |
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
| CFG10-AC-047 | Reservation basis | Eligible-current-APP Planning basis, applicable-actual-procurement achievement basis, Budget ceiling, county basis and overlap policies remain separate; no missing-to-zero, unused-headroom or planned-to-actual fallback. |
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
8. Save complete Supplier portal settings, read the bidder-safe projection, render all four public footer actions, then prove that an incomplete projection preserves Tender reading and existing Draft/receipt access while blocking new Start/production Submit.
9. Walk all five tabs, relevant dialogs, source history and exact old-to-new acceptance mapping; record actual build/test/browser evidence.

Use focused tests for changed invariants, then affected cross-module/release gates under KT-STD-001 v1.7. No old green test overrides the amended contract.

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
| CFG-UX-AC-24 | Technical access conforms to KT-STD-001 v1.7 §3A.6 and AUTH v1.9, with shared search and read-entry registration; business/Auditor reads stay owner-authorised and cannot mutate setup. |
| CFG-UX-AC-25 | Each listed failure maps to a short problem/action message with current scope/date where relevant; saved, verified, complete and supported are not collapsed into one status. |
| CFG-UX-AC-26 | Business users receive an actionable owner-routed explanation inside their record; denied setup routes reveal no protected tabs/data and name the required technical roles. |
| CFG-UX-AC-27 | Critical impacts/errors remain visible; supporting detail uses structured labels. Keyboard, focus return, first-error focus, 200% zoom and narrow layouts have recorded browser evidence. |
| CFG-UX-AC-28 | The full CFG v0.11 incorporates all 14 usability changes alongside retained baseline requirements and dependencies; representative-user evidence is recorded separately from document approval. |

### 14.5 Standards-adoption acceptance criteria

| ID | Required result |
|---|---|
| CFG11-AC-029 | Current control, authority, design, interaction and release references cite approved KT-STD-001 v1.7; older references appear only as historical trace, not the current standard. This criterion does not by itself claim completion of a CFG Stage 2 presentation rewrite. |
| CFG11-AC-030 | CFG record types/read entry points are registered with the KT-STD §3A.6 shared search and AUTH v1.9 conformance mechanism; actual implementation evidence is recorded before release. |
| CFG11-AC-031 | The three §3.1 exceptions are explicit and narrowly enforced: authorised setup writes remain operable, unrelated native UOMs remain usable, and missing-root recovery exposes no generic nested-set controls. |
| CFG11-AC-032 | A CFG-owned design package consists of KT-STD v1.7 §2 plus CFG §10 in full, with runtime behavior confined to §11; AUTH-owned tab bodies use AUTH v1.9 through the exact §10.1 exception. Each independent visible fact remains distinguishable and no fixture/diagnostic internals are rendered as product content. |

### 14.6 Additional focused smoke sequence

1. Walk all everyday tasks as Administrator and System Manager, including the differing root-repair outcomes.
2. Exercise Add rule set-success/version-failure, exact-key replay and empty-set resume; confirm one set and exact saved version with no misleading success.
3. Correct a usable rule with a pending successor, inspect the inline consequence and attempt the affected owner decision; retain past evidence.
4. Walk source-check Pending, Verified-incomplete and Rejected outcomes; distinguish payload correction from evidence recording.
5. Inspect schedule endpoints, explicit missing values and working-day calendar; retain unsupported-procedure blocks.
6. Run the §11.4 representative-user tasks and the §3A.6 conformance gate, including shared technical search registration; record results against individual acceptance IDs.
7. Open the AUTH v1.9 Scheduled responsibility detail, change each permitted field through the owner dialog, test immediate activation and a stale version, then prove that Active, Expired and Revoked assignments cannot be edited through UI, command or direct record write.

These supplement §14.3 and the retained configuration criteria. No test completion is asserted by this document.

### 14.7 AUTH v1.9 reconciliation acceptance criteria

| ID | Required result |
|---|---|
| CFG12-AC-013 | Organisation structure, Users and responsibilities and Technical record search use AUTH v1.9 AUTH-DES-01–09; no superseded AUTH composition or duplicate CFG assignment/search screen remains. |
| CFG12-AC-014 | Only a Scheduled responsibility detail shows **Edit scheduled assignment**; the prefilled owner dialog permits every AUTH-approved field change, uses **Save changes**, records one appended before/after history event and omits Edit for Active, Expired and Revoked assignments. |
| CFG12-AC-015 | AUTH v1.9 resolves the former missing owner specification for AUTH-DES-09 and the registration hooks. Release still requires actual shared-search implementation, CFG record registration and technical-read conformance evidence. |

### 14.8 v0.16 Supplier portal acceptance criteria

| ID | Required result |
|---|---|
| CFG16-AC-001 | Supplier portal is one section inside the existing **Procurement settings** tab, after Reminders; no sixth top-level tab or duplicate public-content module exists. |
| CFG16-AC-002 | Administrator and System Manager can read and update the one active record; other actors receive no setup mutation authority. |
| CFG16-AC-003 | Support email, Privacy and data use, Terms and Accessibility are required; support phone and hours are optional and produce no placeholder when absent. |
| CFG16-AC-004 | Each public destination is an absolute HTTPS URL without embedded credentials; invalid input retains every entered value, identifies the exact field and creates no partial update. |
| CFG16-AC-005 | One successful save atomically updates all fields, advances the record Version and appends material before/after audit evidence. Exact idempotent replay creates no duplicate event. |
| CFG16-AC-006 | `GetPublicPortalInformation` exposes only the current bidder-safe labels/destinations, completeness and record Version; setup audit, prior values and mutation authority are absent. |
| CFG16-AC-007 | Public Tender reading remains available when the projection is incomplete. New **Start bid** and production **Submit bid** fail closed through their owning command checks with the canonical safe message. |
| CFG16-AC-008 | Completing the settings restores later Start/Submit eligibility without republishing a Tender, rebuilding a template or mutating an existing Draft, receipt or historical candidate notice. |
| CFG16-AC-009 | The page contains no Tender publication, candidate-notice, legal-content editor, approval, Publish, Activate or production-submission switch. |
| CFG16-AC-010 | TPR v0.10 and BDS v0.7 render the exact allowlisted projection; neither hard-codes placeholder contact details nor stores a second editable copy. |
| CFG16-AC-011 | C05 complete, incomplete, invalid-link and saved variants satisfy KT-STD desktop, 200% zoom, keyboard/focus/error and narrow-width evidence requirements. |
| CFG16-AC-012 | The complete and isolated incomplete/invalid fixtures are created through the owner command and are never installed as production defaults or represented as legal approval. |

## 15. Implementation constraints and required owner work

Apply KT-STD-001 v1.7 §§4–6. Use the existing Frappe Single, native ERPNext extensions, shared Vue Desk mount and AUTH v1.9 hooks. Inspect the repository before claiming current field names, DocType migrations, native Company association or UOM precision mapping. Native writes and fixture/bootstrap paths must enforce the same invariants; a page-only check is insufficient.

Use one lockable module-control row rather than relying on an unavailable database-specific partial index. All supported write paths participate in the lock/transaction; add appropriate DB uniqueness constraints for module key, FY identifiers, reference keys, set/version numbers and funding normalized name. Establish cross-owner lock ordering for CFG/BUD/PLN/REQ, meaningful rollback tests and exact immutable evidence persistence.

| Dependency | Exit evidence |
|---|---|
| LAW verification | LAW-V-001–011 resolved for each production-used rule; current edition, applicability/date basis, sources and interpretations recorded. Unneeded/future rules remain explicitly unsupported, not defaulted. |
| BUD provider boundary | BUD v1.10 Budget-ceiling, affordability, atomic decision-validation and precision contracts; no annual Planning denominator service; actual native Company association verified. |
| NDS/PLN intake consumers | Exact initial action predicates and correction exceptions, close-instant checks in owner transactions, independent availability. |
| REQ/TPR/TPUB consumers | Current config validation and immutable evidence pins at relevant positive decisions; no profile admission without an implemented procedure. |
| TPR/BDS public portal consumers | One CFG-owned allowlisted projection; public reads remain available when incomplete, while new Start/production Submit recheck completeness server-side. No copied settings, placeholder contacts or local mutation routes. |
| AUTH/KT-STD | Approved KT-STD v1.7 and AUTH v1.9, current route/capacity mappings, shared five-tab shell, Scheduled-edit enforcement, domain exceptions, Technical record search implementation, CFG record registration and conformance evidence. |
| Native UOM/calendar support | Inspected field/precision mapping and supported source-verified counting/calendar provider; no assumed native fields. |
| SEED date/scenario correction | CFG-XD-001 resolved in a controlled matching fixture amendment before affected positive-chain evidence. |
| Government operating model | LAW-V-008/LAW-OB-009 evidence and permitted integration/handoff design; no configuration checkbox used as authorization. |
| STD Templates separation | STD-TPL-001 v0.9 owns the installed-release registry, read projections, `/app/std-templates` routes, previews, verification results and blockers. System setup registers no template list/detail route, projection or action. |

Release requires actual schema/service/UI inspection, focused and affected contract tests, production asset build, applicable full artboard comparison and a dependency-aware cutover scan. Preserve native accounting/HRMS and immutable historical records. This document does not supply a deployed schema or claim integration tests passed.

Current sibling-document compatibility must be checked against the exact controlling NDS, STR, BUD, PLN, REQ, TPR and STD-TPL versions and release records used by the implementation while preserving their owner boundaries. Prior follow-up rows are documentary lineage, not proof that every provider contract or integration test is complete.

Add focused failure/replay checks for §7.3 and `UpdatePublicPortalSettings`, plus affected cross-app tests for the standards/CFG changes. Complete the §10 inventory and §11.4 user walkthroughs in the existing shell. No second prototype stack or duplicate common technical-read implementation is authorised.

## 16. Prohibited shortcuts

Do not reintroduce PE/FY context records, multiple PEs, global FY authority, local approver registries, Reference Data Manager, configuration approval workflow, module window lifecycles or duplicate ERPNext Company/Fiscal Year/UOM catalogues. Do not expose raw policy scripts or an arbitrary JSON configuration editor as the business surface. Do not reintroduce installed-template list/detail routes, projections, previews or actions in System setup; use the separate **STD Templates** module. Do not turn Supplier portal settings into a rich-text legal-content editor, candidate-notification centre, publication approval, consent engine or production-submission switch. Do not hard-code placeholder contacts in TPR/BDS or expose CFG audit/history through the public projection.

Do not rely on hourly expiry, browser time, old cached rules, method names or latest-version sorting for a positive decision. Do not overwrite referenced versions, treat missing bounds as unlimited, use optional price-index behavior for mandatory reservation rules, infer candidate entitlement in Planning or calculate actual procurement achievement from a Plan designation.

Do not claim a source is verified through an unsupported checkbox, an approved fixture or this document's approval. Do not change fiscal-year dates to accommodate an inconsistent example. Do not remove native accounting routes or disable unrelated UOMs while removing retired KenTender surfaces.

Inherit the product-wide prohibitions from KT-STD-001 v1.7 §§2.3 and 10, subject only to the explicitly named CFG domain exceptions in §3.1. Do not collapse saved, sources verified, details complete and implemented support into one misleading badge. Do not seed reasons/source-check dates into production forms, silently duplicate a rule after a partial save, or replace a named owner issue with a generic “contact support” dead end when an authorised next step is known.

## 17. Traceability and full change register

### 17.1 Precedence and scope of amendment

AUTH v1.9 supplies the approved authority baseline and Technical record search owner contract; approved KT-STD v1.7 controls shared design/verification and §3A.6 technical read, subject to the explicit CFG §3.1 domain exceptions; approved LAW v1.2 identifies source/application verification and the corrected reservation-measure boundary; this CFG successor controls configuration schemas/surfaces; each business module controls its lifecycle. Approved SEED v1.3 controls shared fixtures subject to its explicitly retained prerequisites. When a precise inconsistency is found, record it and amend the owner; do not reinterpret its approval as permission to bypass a domain guard.

The retained v0.10 work implemented the CFG document requirements from PLN v1.18 §17.2 and FU-22. This successor incorporates the approved usability amendment, the current KT-STD v1.7 authority and AUTH v1.9 reconciliation. It preserves earlier retirement decisions for CTX-CHG-001 and obsolete KenTender registers, while making current implementation gaps explicit. No external file is claimed updated by this document alone.

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
| CFG11-CHG-012 | CFG-UX-012 | AUTH tabs and technical-read journeys may be omitted from CFG review; §§6, 10.10. | Include AUTH-owned organisation/responsibility screens and Administrator-only repair. Cite KT-STD v1.6 §3A.6 for technical read/search/conformance; preserve setup authority with explicit exception. | §§3.1, 6, 7.4, 10.11; AUTH-owned/technical routes | CFG-UX-AC-23–24 |
| CFG11-CHG-013 | CFG-UX-013 | Error states expose mechanisms or send business users into setup; §§8, 10.10. | Message states problem, affected action and authorised next step; separate status dimensions; show diagnostic details on demand; no protected data on denied routes. | §§8, 10.11, 11.3; consumer presentation | CFG-UX-AC-25–26 |
| CFG11-CHG-014 | CFG-UX-014 | Completeness could be treated as usability proof; §§10–11, 14–15. | Short structured supporting detail, keyboard/focus/zoom/error handling and role-based scenario testing; carry full register/acceptance coverage into v0.11, retaining unresolved dependencies. | §§10–11, 14–18; inventory/evidence | CFG-UX-AC-27–28 |
| CFG11-CHG-015 | 14 September 2026 standards-adoption instruction | Current references used KT-STD v1.4 and deferred §3A.6 as uninspected. | Approve/adopt supplied v1.5; replace local technical-read restatements with controlling citation; retain explicit setup/UOM/root-recovery exceptions; record AUTH owner gap; apply closed-input rules. | Control; §§3.1, 6–11, 13–18 | CFG11-AC-029–032 |

### 17.4 Approved v0.12 Tender-format and authority-reconciliation changes

| ID | Required replacement | Target | Acceptance |
|---|---|---|---|
| CFG12-CHG-001 | Add the read-only installed Tender-format projection without moving template ownership into CFG. | §4.11 | CFG12-AC-001–003 |
| CFG12-CHG-002 | Add owner read services for list and exact release detail; no write or activation service. | §7.2 | CFG12-AC-001–003 |
| CFG12-CHG-003 | Add Tender formats under Procurement settings and canonical list/detail routes. | §9 | CFG12-AC-001, 009 |
| CFG12-CHG-004 | Replace the outline-only Tender-format prompt with CFG-DES-05A and CFG-DES-05B: exact placement, closed fixtures, section order, labels, values, tasks, mappings, actions, states and narrow-screen treatment. | §10.11 | CFG12-AC-004–005, 008–010 |
| CFG12-CHG-005 | Expose immutable previews/review pack without bid content or mutation. | §§10.11, 11.5 | CFG12-AC-002, 007 |
| CFG12-CHG-006 | Make an Unavailable/failed release visibly unusable by Tenders with no override. | §§4.11, 10.11, 11.5 | CFG12-AC-003, 006, 009 |
| CFG12-CHG-007 | Add complete design inventory, browser evidence and owner dependency. | §§10.13, 14.6–15 | CFG12-AC-010 |
| CFG12-CHG-008 | State the complete design-input boundary and the AUTH-only exception; identify the owner projections and immutable assets that supply runtime facts without making their documents additional design inputs. | §§10.1, 10.11, 11.5 | CFG12-AC-011–012 |
| CFG12-CHG-009 | Replace the superseded AUTH v1.7 baseline with approved AUTH v1.9 and include its Scheduled-only responsibility editing composition and owner command. | Control; §§3.1, 6, 10.1, 10.12–10.13, 11.1 | CFG12-AC-013–014 |
| CFG12-CHG-010 | Close the former AUTH-DES-09 document-owner gap while retaining actual Technical record search implementation, module registration and conformance as separate release evidence. | §§3.1, 14.8, 15, 17.5 | CFG12-AC-015 |
| CFG12-CHG-011 | Adopt KT-STD v1.7 as the current shared authority without claiming that citation alone completes CFG's Stage 2 presentation rewrite or user verification. | Control; §§3.1, 10.1, 14.5, 15–18 | CFG11-AC-029–032 |

### 17.5 v0.13 reservation-measure correction

| ID | Earlier problem | v0.13 correction | Location | Verification |
|---|---|---|---|---|
| CFG13-CHG-001 | `AnnualProcurementBudget` permitted the approved Budget ceiling, including unused headroom, to become the 30% Planning denominator. | Replace it with `EligibleCurrentAPPValue`; define exact Plan/rule Version and per-item inclusion evidence. | §§4.7, 5, 10.7 | CFG13-AC-001–003 |
| CFG13-CHG-002 | `AnnualProcurementValue` did not distinguish planned estimates from actual procurement achievement. | Add explicit PlanningAllocation and ImplementationAchievement stages with separate denominators and owners; forbid planned-to-actual inference. | §§4.7, 5, 10.7, 14 | CFG13-AC-004 |
| CFG13-CHG-003 | The setup UI presented the denominator as an open-ended administrator choice. | Use plain labels and fix the AGPO planning measure to **Eligible value of the current Annual Plan** under the controlled interpretation. | §10.7 | CFG13-AC-005 |

| ID | Required result |
|---|---|
| CFG13-AC-001 | The AGPO Planning rule resolves only to `EligibleCurrentAPPValue`; no approved Budget amount or unused headroom is accepted as its denominator. |
| CFG13-AC-002 | The resolver returns the exact obligation/rule Version and enough applicability data for Planning to evidence every included or excluded current Plan Item. |
| CFG13-AC-003 | A successor APP Version causes a new calculation snapshot; historical decisions retain their earlier Plan/rule Versions. |
| CFG13-AC-004 | Actual achievement accepts authoritative downstream actual procurement values only and cannot be calculated from APP estimates. County and other obligations remain separate. |
| CFG13-AC-005 | Ordinary setup copy says **Planned allocation**, **Actual achievement**, **Eligible value of the current Annual Plan** and **Applicable actual procurement value**; it does not expose obsolete denominator choices. |

### 17.6 v0.14 Tender-format reservation-scope reconciliation

| ID | Earlier problem | v0.14 correction | Location | Verification |
|---|---|---|---|---|
| CFG14-CHG-001 | Tender formats still described release 1.1 as **Unreserved only**, contradicting STD-TPL-001 v0.7. | Show `None`, Youth, Women and Persons with disabilities as the exact base treatments; show County residents separately with its applicability prerequisites. | §§1, 4.11, 10.11 | CFG14-AC-001–002 |
| CFG14-CHG-002 | The Unavailable fixture said all technical checks passed and only owner approval remained, although the template contract still requires isolated Women, Persons-with-disabilities and County-residents proof. | Show Youth Passed, remaining reservation variants Incomplete and owner decision Pending; keep the release Unavailable. | §§4.11, 10.11 | CFG14-AC-003 |
| CFG14-CHG-003 | Administrators could not see how reserved-Tender responses are evaluated or passed downstream. | Add the exact Youth fixture facts and separate reservation eligibility mapping, including non-contract and Award/reporting treatment. | §10.11 | CFG14-AC-005 |
| CFG14-CHG-004 | The Available variant could appear without proving every newly supported reservation treatment. | Require all base-category and County-residents gates plus exact manifest approval before Available. | §§4.11, 10.11, 14.9 | CFG14-AC-004 |
| CFG14-CHG-005 | Read-only inspection could drift again through a hard-coded supported-use string. | Add explicit projection fields and require list/detail content and blockers to come only from the exact installed release record. | §§4.11, 7.2, 11.5 | CFG14-AC-002, 006 |
| CFG14-CHG-006 | Current text retained stale LAW v1.1 and annual-Budget-basis wording after the approved LAW v1.2/BUD v1.10 correction. | Use LAW v1.2 and the BUD ceiling/affordability boundary with no annual Planning-denominator service. | §§2, 4.3, 4.6, 15, 17.1 | Dependency and obsolete-reference scan |

### 17.7 v0.15 STD Templates ownership correction

| ID | v0.14 problem | v0.15 correction | Verification |
|---|---|---|---|
| CFG15-CHG-001 | Installed templates appeared as a fifth local section inside Procurement settings although they are code-owned product releases, not site configuration. | Remove the Tender-format section and both `/app/system-setup/tender-formats` routes; use the separate **STD Templates** menu and `/app/std-templates` routes owned by STD-TPL-001 v0.8. | Menu/route inventory and absent-old-route test. |
| CFG15-CHG-002 | CFG duplicated the installed-release projection and could drift from the release manifest and product contract. | Remove `InstalledTenderFormatProjection` and its read services from CFG; use `InstalledSTDReleaseProjection v1` directly from the template owner. | Schema/service ownership scan. |
| CFG15-CHG-003 | CFG contained complete Tender-format artboards, variants, fixtures and acceptance criteria, creating two design authorities. | Remove the artboards, fixture world, inventory row, interaction contract and current acceptance criteria from CFG; STD-TPL-001 v0.8 §11 is the single complete design input. | Design inventory and cross-reference scan. |
| CFG15-CHG-004 | Approved v0.14 historical register rows could be mistaken for current implementation requirements. | Retain §§17.4 and 17.6 only as historical lineage; §17.7 expressly supersedes their current UI ownership, routes and projection. | Precedence review. |
| CFG15-CHG-005 | System Setup's purpose and role text still included template inspection. | Narrow current scope, navigation, actor permissions, dependencies and prohibitions to site setup and effective procurement configuration. | Current-section terminology scan. |

The v0.12 and v0.14 register entries below their historical headings explain how the earlier approved documents evolved; they do not reinstate a current System setup Tender-format surface after CFG15-CHG-001–004.

### 17.8 v0.16 public portal closure

| ID | v0.15 gap | v0.16 correction | Verification |
|---|---|---|---|
| CFG16-CHG-001 | Public supplier screens depended on support and legal/accessibility destinations with no owned configuration surface. | Add one bounded **Supplier portal** section inside Procurement settings and one active `PublicPortalSettings` record. | Route/section and schema ownership tests. |
| CFG16-CHG-002 | TPR/BDS could hard-code values or expose internal configuration data. | Define one bidder-safe allowlisted projection and prohibit copied editable values, setup audit and mutation authority in consumers. | Projection contract and negative-field tests. |
| CFG16-CHG-003 | Missing public information had no consistent operational effect. | Preserve Tender reading and existing Draft/receipt access; fail closed only for new Start and production Submit until the required projection is complete. | Complete/incomplete cross-module command tests. |
| CFG16-CHG-004 | URL, update and historical-integrity behavior was not closed. | Require atomic updates, HTTPS validation, Version/audit evidence and prospective-only rendering effects. | Validation, replay and no-retroactive-mutation tests. |
| CFG16-CHG-005 | The design contract did not identify exact placement, fields, states or narrow behavior. | Add C05 complete, incomplete, invalid-link and saved variants with exact field order and no invented actions. | Artboard and browser comparison. |

### 17.9 Follow-up dispositions

| Item | Disposition |
|---|---|
| FU-22 | Document amendment approved on 12 September 2026. Implementation and verification remain open and require their specified evidence. |
| CFG-XD-001 | Concrete pre-FY procurement/profile mismatch in §13; matching PLN/SEED/downstream/legal reconciliation required. |
| LAW-V-001–011 | Applicable legal source/interpretation work remains owned by LAW; CFG's schema does not establish legal correctness. |
| FU-23–25 / FU-30 | BUD/NDS/REQ/TPR and precision provider amendments remain required; TPUB and STR compatibility are explicitly included where relevant. |
| FU-26 | County fixture is a separate single-entity world and gates county-support evidence. |
| FU-27 | CFG standards-citation/document cleanup is incorporated and carried forward under current KT-STD v1.7, including §3A.6. AUTH v1.9 now supplies the previously missing owner specification; shared-search implementation, module registration and conformance evidence remain open. |


| Additional item | Disposition / required evidence |
|---|---|
| CFG-XD-002 — Technical-read implementation evidence | **Document-owner portion resolved by approved AUTH v1.9**, which supplies AUTH-DES-09 and §9 hooks/contracts. Still required before release: deployed shared search, CFG reference resolver/read probes, all-status route access, absent business commands and the KT-STD v1.7 §3A.6 conformance evidence. |
| CFG-UX-001–014 | Approved 14 September 2026 and incorporated into §§6–11, 14 and 17.3; implementation and user walkthrough evidence remain required. |
| Shared consumer copy | NDS/PLN/DSP and other consumers adopt readable activity/problem labels while preserving owner action predicates; changes to their controlled documents require their own amendment. |
| Latest standard going forward | Use approved KT-STD-001 v1.7 and AUTH-ADR-001 v1.9 for subsequent work. Older citations preserved inside historical registers do not select an obsolete current authority. |

## 18. Approval effect

CFG v0.16 is **proposed for Project Owner approval** as the complete successor to approved CFG v0.15.

Approval will retain the five-tab System setup contract, AUTH v1.9 reconciliation, approved reservation-measure correction and all site-configuration behaviour. It will add the bounded **Supplier portal** settings section and public allowlisted projection required by TPR v0.10 and BDS v0.7. It will continue to exclude installed-template inspection, projection, routes, artboards and acceptance ownership from CFG and recognise STD-TPL-001 v0.9 as the sole authority for the separate read-only **STD Templates** module.

Approval will not approve or activate a Tender-template release, publish a Tender, send a candidate notice or enable production bid submission. It will not by itself verify legal source applicability, resolve CFG-XD-001, complete the remaining CFG-XD-002 implementation evidence, deploy schemas, complete provider integration, establish the government operating model, complete CFG's Stage 2 presentation rewrite or prove artboard/browser/user acceptance. Preserve these separate gates and record real evidence.
