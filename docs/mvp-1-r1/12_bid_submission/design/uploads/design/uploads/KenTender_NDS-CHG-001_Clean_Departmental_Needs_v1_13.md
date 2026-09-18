# NDS-CHG-001 — Clean Departmental Needs

| Control | Value |
|---|---|
| Document ID | NDS-CHG-001 |
| Version | 1.13 |
| Change type | Rewrites the complete static design contract as explicit screen compositions and definite state variants; adds the matching functional action map; adopts KT-STD-001 v1.6. Retains all approved business rules and the corrected exclusion fixture. Full 44-row re-implementation table in §18.2. |
| Date | 15 September 2026 |
| Editorial correction | 15 September 2026: separate the accepted-exclusion fixture from the canonical Proceeding acceptance event; see NDS12-CHG-011. No business rule or approval lifecycle change. |
| Status | **Consolidated approved requirements** |
| Approval basis | Approved NDS v1.12 and its retained 15 September fixture correction; Project Owner instruction on 15 September 2026 to persist the agreed composition standard and revise Departmental Needs. |
| Supersedes | v1.12 and earlier Departmental Needs implementation specifications in full; predecessors retained as historical evidence. |
| Module | Departmental Needs |
| Standards | Governed by approved KT-STD-001 v1.6, including §§2.6–2.8 explicit composition and §3A.6 technical read; AUTH v1.7 remains the inspected owner baseline subject to the named shared-owner follow-up. |
| Implementation posture | Clean correction in place; no compatibility layer |

**Controlling decision:** Departmental Needs is an optional consultation channel through which users propose one plain-language anticipated requirement at a time. Acceptance makes a Need available to Procurement Planning; it is not a prerequisite for the HoD to plan a direct departmental requirement. Departmental Needs does not classify procurement, approve expenditure, reserve funds, create a Plan Item, create a Procurement Requisition or initiate a Tender.

## 1. Governing decision

This complete successor consolidates approved NDS v1.12 with the Project Owner’s 15 September 2026 instruction to apply the agreed explicit screen-composition standard. It is the current Departmental Needs implementation contract. It retains the optional consultation channel, six source facts, immutable revision governance and AUTH v1.7 assignments, with approved CFG v0.10, BUD v1.8 and SEED v1.3 ownership. It incorporates all ten changes in the Project Owner-approved Departmental Needs Usability Amendment v0.1. Planning v1.18 remains the established business-contract source; proposed Planning v1.19 supplies the coordinated readable presentation but is not approved by this document. Earlier §1.1 rows are historical dispositions; current sections control implementation. The complete §11 replaces cryptic layout prose with explicit placements and exact variants. §12.10 maps each control to its existing behavior. This authoring correction introduces no new Need field, lifecycle step or business role.

The existing application is corrected in place. Usable code and the proven Claude Design → Vue 3 → Frappe Desk page pattern may be reused. Removed legacy concepts are removed under the existing controlled cutover. Usability labels do not rename technical IDs, enums or event keys. Preserve historical source data, decisions and submitted wording; no mass rewrite of evidence.

Completion requires one coherent result across schema, services, permissions, screens, fixtures and tests. A field, action, object, service, queue or screen not defined here is outside this module.

### 1.1 Conflict and disposition register

| Earlier item | Disposition in v1.4 |
|---|---|
| One Need containing several item lines | Replace with one Need for one requirement. Quantity and unit belong directly to the Need. |
| Planner combine, split or partially allocate Need lines | Remove from Departmental Needs. When Planning uses an accepted Need, it uses the current accepted revision and full accepted quantity. |
| `Partially included` Planning usage | Remove. The projection is only `Not included` or `Fully included`. |
| Delivery or use location | Remove. No approved current rule, decision or downstream contract consumes it. |
| Supporting attachments | Remove. No approved current departmental-review decision requires a document. |
| Indicative estimate, Procurement Budget Line, funding source and currency on a Need | Remove. Funding specification belongs to the DPP entry in Procurement Planning, not consultation intake. |
| Free-text `Other` unit | Remove. Units come only from the governed ERPNext `UOM` catalogue. |
| Requirement type or procurement category on a Need | Remove. Procurement Planning owns classification. |
| Strategy reference on a Need | Remove. A Plan Item selects its Strategic Objective in Procurement Planning. |
| Generic source, authority, evidence, notes or contact fields | Remove. None has a named current consumer and effect. |
| Budget Officer and Accounting Officer Departmental Needs workspaces | Remove. They have no Departmental Needs decision or task. |
| Procurement Planner Departmental Needs landing page | Remove. Planners work in Procurement Planning and may open an accepted Need read-only. |
| Four summary cards, separate action/waiting sections and advanced register filters | Replace with one role-appropriate table and minimal search/status filters. |
| Shared-task claim, release and support-lookup workflows | Remove. Review work is a scoped departmental queue; an authorised decision atomically completes the task. |
| `/departmental-needs`, `/desk/departmental-needs` and legacy `/demands` routes | Replace with the canonical Frappe Desk routes in section 10. No redirect or alias. |
| Accepted Need treated as permanently unchangeable | Correct. The accepted revision is immutable, but a separately reviewed successor may replace it. |
| Direct withdrawal of an accepted Need | Retain only through a reviewed withdrawal request. An Active Plan dependency must be cleared first. |
| Scheduled Needs intake window with opening and closing instants | Remove. MVP 1 uses one manually maintained **Needs submission open** flag on the applicable ERPNext Fiscal Year. |
| Planning source payload includes Strategy, requirement type or generic source evidence | Correct the payload. Those values are not owned by Departmental Needs. No Planning screen redesign is required. |
| Accepted Need as the exclusive source of a DPP entry or Plan Item | Remove. Planning also permits a HoD or authorised departmental plan preparer to capture a direct departmental requirement. It does not create a synthetic Need. |
| `business_justification` as a separate field that stops at Departmental Needs | Replace with `expected_operational_result`; the value is carried read-only into Planning and downstream lineage. |
| Separate Departmental Review Delegate role | Remove. An acting HoD uses the same Head of User Department responsibility through one dated User Responsibility Assignment. |
| Separate Needs Configuration Manager role | Remove. Administrator or System Manager maintains the Needs-submission flag directly in System setup; no business approval is created. |
| Separate Role, User Permission, User Scope Assignment or capability records as authority | Remove. Use one role-bound User Responsibility Assignment and the AUTH-ADR-001 v1.7 resolver. |
| Financial Year or PE/FY Context assigned to each user | Remove. Assign durable site-wide or department scope once. Derive the creation year from the one ERPNext Fiscal Year whose Needs-submission flag is Open. |
| PE selector and PE key repeated on Needs configuration | Remove. The site has one PE; it is never selected and no PE/FY Context exists. |
| Browser-stored PE/FY selection required before module entry | Remove. The module opens without it; any PE, department or FY control is a visible, changeable local filter only. |
| Separate **Review tasks** work-queue menu | Remove. Pending departmental reviews appear inside the ordinary Departmental Needs workspace for the HoD. |
| Legacy Demand migration and compatibility | Prohibited. Departmental Needs remains a clean domain. |

New in v1.10 — internals of the v1.9 rename, and workspace states:

| Earlier item | Disposition in v1.10 |
|---|---|
| v1.9 renamed `need_version_id` without saying whether the generated record name `{need_reference}-V{nnn}` follows | **Keep the suffix.** It is an opaque identifier pinned by Planning lineage and seed data; renaming every row and pin for a label buys nothing (§4.3). |
| v1.9 renamed the concept without saying whether `DepartmentalNeedAccepted.v2` wire keys change | **Keep the keys** (`accepted_version_id`, `version_number`) and the `.v2` contract version; consumers read keys, not the word (§7.1). |
| §11.15 lists no filtered-empty variant, yet the workspace renders one when search or status filters match nothing | **Add** the variant with the copy the build carries. |
| Workspace copy the build had drifted from — the no-access heading, the loading text, the closed-intake strip value and the **Accept updated revision** button | **Correct the build** to this document; no text change here. |
| A departmental plan's counter cited as a "DPP version" | **Cite** it as a Submission, per PLN-CHG-001 v1.18 §4.2. |

New in v1.6:

| Earlier item | Disposition in v1.6 |
|---|---|
| Needs-submission flag as a bare Boolean with no close instant | **Correct.** CFG-CHG-002 v0.10 §4.2 adds `kentender_needs_submission_closes_at`. v1.4's §11.2 fixture already displayed **Open until 25 Nov 2026, 23:59 EAT** while its domain model carried only a Boolean; the field makes the artboard and the model agree. It is one optional datetime, not an intake-window lifecycle, and Departmental Needs reads it only. |
| NDS-BR-003 making existing Draft and Returned revisions read-only when intake closes | **Correct.** Closing blocks creation and initial submission; existing Drafts and Returned corrections stay editable. A draft that can be neither finished nor cleanly abandoned is dead weight, and preserving editable work permits an explicitly reopened intake without losing its history. Submission remains blocked until intake reopens. |
| KenTender-governed ERPNext `UOM` catalogue | Replace with ERPNext `UOM` per CFG-CHG-002 v0.10 §4.4. Needs use CFG v0.10’s native UOM adapter and its logical `selectable`/precision result; no native `enabled` column is assumed. |
| `Procurement Budget Line` as the Budget & Funding record name | Rename to `Procurement Budget Line` per BUD-CHG-001 v1.8 §1.1. The identifiers themselves are unchanged. |
| Procuring Entity row in the artboard context strips and fixture-context lines | **Remove.** KT-STD-001 §2.3 prohibits a Procuring Entity row on any artboard. |
| Restated closed-input rules, verification protocol, release evidence and universal prohibitions | **Remove.** Cite KT-STD-001 v1.4. |
| Bespoke fixture actors `amina.hassan@moh.example.test` and `auditor.moh@example.test` | Replace with the KT-STD-001 §8.3 shared register. Amina Hassan duplicated Mercy Kilonzo's assignment exactly and is dropped; the Auditor is Naomi Chebet. |
| Citations of AUTH-ADR-001 v1.5, CFG-CHG-002 v0.5, Budget & Funding v1.1 and Strategy Alignment v1.3 | Update to AUTH-ADR-001 v1.6, CFG-CHG-002 v0.6, BUD-CHG-001 v1.3 and STR-CHG-001 v1.6. |

## 2. Purpose and outcomes

Departmental Needs shall provide:

- wider consultation on requirements that departments may consider for procurement planning;
- a simple way for a departmental requester to state one anticipated requirement;
- clear departmental authority with Fiscal Year owned by each Need and governed by one simple open/closed submission flag;
- departmental maker-checker review;
- immutable accepted revisions that Procurement Planning can consume safely;
- controlled correction of an accepted Need through a successor revision;
- separate read-only accepted Planning disposition and Active Plan usage without changing Need lifecycle; and
- a reviewed withdrawal path that protects an Active Plan dependency.

Departmental Needs is not the gatekeeper for departmental procurement planning. A department may prepare a DPP entirely from direct departmental requirements, entirely from accepted Needs, or from both.

### 2.1 Scope exclusions

The module shall not contain:

- procurement category, requirement type, method, lot, schedule, specification, bill of quantities or Terms of Reference;
- a Strategic Objective, Outcome, Indicator, Target or Value Commitment;
- unit price, tax calculation, market estimate or cost breakdown;
- funding availability, reservation, commitment, Finance confirmation or payment data;
- a Plan Item editor, Procurement Requisition, Tender or contract action;
- delivery location, source reference, authority reference, evidence field, attachment, generic note or contact;
- several item rows inside one Need;
- a scoring model, completion percentage, dashboard chart or performance card;
- editable technical identifiers, hashes, audit actors or timestamps;
- a duplicate Planner, Budget Officer, Accounting Officer or System Administrator landing page;
- a custom Frappe shell, header, breadcrumb, global selector or navigation system; or
- legacy Demand fields, routes, adapters, aliases, fallback records or migrated fixtures.

### 2.2 Data-purpose gate

No stored field is permitted unless all three conditions are documented before implementation:

1. a current operational decision or output uses the field;
2. the screen, rule or service consuming it is named; and
3. its validation and system effect are defined.

“Useful later”, “normally captured”, “helpful context” and “the design showed it” are not sufficient reasons. An undocumented field is omitted, not added as optional data.

The six requester-entered values in section 4.3 pass this gate:

| Value | Current consumer and effect |
|---|---|
| Title | Identifies the Need in queues, selectors, details and Planning lineage. |
| Description | Tells the departmental reviewer and Planner what is required. |
| Expected result | States what should improve or become possible; it is reviewed by the HoD and carried read-only into Planning and downstream lineage. |
| Quantity | Supplies the full accepted quantity projected into the departmental plan. |
| Unit | Gives meaning to the quantity and is projected into the departmental plan. |
| Required by | Supports departmental review and the Planning schedule guard. |

## 3. Fixed ownership and dependency boundary

- Configuration & Governance owns the site PE, Organisation Unit, ERPNext Fiscal Year, timezone, unit catalogue (ERPNext `UOM`) and the namespaced Needs-submission flag. `kentender_core` owns the business-role registry, User Responsibility Assignment, Organisation Unit scope resolution and administration surface. Departmental Needs never assigns Fiscal Years to users.
- Departmental Needs owns Need identity, revisions, review decisions and withdrawal requests. It owns no intake-window record.
- Strategy Alignment owns Strategic Objectives. A Need stores no Strategy reference.
- Budget & Funding owns Budget records, line eligibility, currency/precision, funding positions, reservations and commitments; CFG owns the funding-source catalogue. Departmental Needs stores none of those monetary/funding values. Planning selects its DPP entry’s Budget Line and estimate.
- Procurement Planning owns requirement classification, DPP entries, direct departmental requirements, Plan Items, source allocations, Finance tasks and Plan inclusion. It cannot edit a Need.
- Procurement Requisitions and Tendering consume approved Planning lineage later. A Need creates neither record.

| Information or decision | Owner | Departmental Needs relationship |
|---|---|---|
| Site PE, OU, Fiscal Year, timezone and unit | Configuration & Governance | Resolve exact governed records; do not invent fallbacks or PE choices. |
| Business responsibility and organisational scope | `kentender_core` under AUTH-ADR-001 v1.7 | Resolve the exact active role-bound assignment and OU subtree. |
| Needs submission open/closed flag | Configuration & Governance on ERPNext Fiscal Year | Gate initial Need creation and initial submission; direct audited setup action with no approval. |
| Need and accepted Need revision | Departmental Needs | Create, review, revision and publish. |
| Strategic Objective | Strategy Alignment / Procurement Planning | No Need field or write. |
| Requirement classification, direct requirement and Plan treatment | Procurement Planning | Consume an accepted Need when used, or capture a direct departmental requirement without creating a Need. |
| Planning usage | Procurement Planning | Publish `Not included` or `Fully included` back as a read-only projection. |
| Procurement Budget Line identity, funding source, currency and position | Budget & Funding | Selected through the Budget contract by Procurement Planning; no Need field or write. |
| DPP indicative amount | Procurement Planning | Captured on the DPP entry; no Need field or write. |
| Funding reservation | Budget & Funding, called by Requisitions | Created only at successful REQ authorisation, never at Need or Planning events. |
| Accepted DPP disposition | Procurement Planning | Project proceeding/not-proceeding after Procurement accepts the complete DPP; preserve reason and exact source/submission lineage independently of Active usage. |

The permitted dependency paths are:

**Configuration & Governance → Departmental Needs consultation → Procurement Planning DPP entry**

**Configuration & Governance / Budget & Funding → Procurement Planning direct requirement or accepted-Need enrichment → Procurement Requisitions**

Departmental Needs shall not import a downstream DocType controller or query a downstream table directly.

## 4. Canonical domain model

All identifiers are generated by the server. Framework audit fields remain framework-managed and are not repeated as user data.

### 4.1 Fiscal Year Needs-submission control

Departmental Needs creates no intake-window DocType. MVP 1 consumes the following CFG-owned fields on canonical ERPNext Fiscal Year:

| Field | Operational purpose and system effect |
|---|---|
| `kentender_needs_submission_open` | Configured flag, default 0; commands use CFG’s effective-open verdict, not this Boolean alone. |
| `kentender_needs_submission_closes_at` | Optional UTC datetime. Intake is effectively closed at this instant even before scheduler cleanup. Read-only to Departmental Needs. |

At most one Fiscal Year may have the flag enabled. Administrator or System Manager changes both fields directly through the Fiscal Years section of System setup, governed by CFG-CHG-002 v0.10. The server records who changed them and when.

Effective open = flag enabled, FY not disabled, and close instant absent or server now strictly before it. Resolve and revalidate through CFG after acquiring the relevant control and before the dependent write. At equality the action is closed; hourly cleanup is not the enforcement boundary. CFG retains effective-close and observed cleanup instants separately in its own audit.

The close instant is one optional datetime on the flag, not an intake-window lifecycle. There is no `opens_at`, no `Scheduled` state, no approval step, and no title, description, reason, source-reference or attachment field. Departmental Needs never writes either field and exposes no configuration route or page action for them.

### 4.2 DepartmentalNeed

The stable identity and scope of one requirement.

| Field | Operational purpose and system effect |
|---|---|
| `need_id` | Immutable internal identity used by services and lineage. |
| `need_reference` | Generated on first save as `NDS-{PE code}-{FY start}-{4 digits}`; used by routes and users. |
| `org_unit_id` | Defines the owning department and review scope. Required and immutable. |
| `financial_year_id` | References the canonical native ERPNext Fiscal Year and defines the planning/date boundary. Required and immutable. This local field name does not introduce a KenTender Fiscal Year object. |
| `owner` (Frappe framework field) | Defines whose Need appears in **My needs** and who may correct it. Fixed on first save; do not create a duplicate originator field. |
| `current_state` | System-maintained root state: `Draft`, `Submitted`, `Returned`, `Accepted for planning`, `Not taken forward` or `Withdrawn`. |
| `current_revision_id` | Points to the newest Draft or decided revision for display and editing. |
| `current_accepted_revision_id` | Points to the accepted revision available to Planning. Empty until first acceptance. |
| `record_version` | Monotonic optimistic-concurrency token checked by every write. |

If an accepted Need has an open successor, `current_state` remains `Accepted for planning`; the successor's separate status is shown as `Draft update`, `Update submitted` or `Update returned`. This prevents an unaccepted edit from replacing the source available to Planning.

### 4.3 DepartmentalNeedRevision

One revision of the requirement. Draft content is mutable only until submission. Submitted content is immutable.

| Field | Operational purpose and system effect |
|---|---|
| `need_revision_id` | Immutable reference used in review, events and Planning lineage. |
| `need_id` | Links the revision to its stable Need. |
| `revision_number` | Generated sequence within the Need. |
| `based_on_revision_id` | Identifies the revision copied to create this correction or accepted successor. Empty only for the first Draft. |
| `revision_status` | `Draft`, `Submitted`, `Returned`, `Accepted`, `Not taken forward`, `Withdrawn` or `Superseded`. |
| `title` | Short queue and detail label. Required for first save; 5–160 characters. |
| `description` | Plain-language statement of what is required. Required for submission; 10–1,000 characters. |
| `expected_operational_result` | Plain-language statement of what should improve or become possible after the requirement is met. Required for submission; 10–1,000 characters. |
| `indicative_quantity` | Full quantity projected to Planning. Required for submission; an exact positive decimal string with governed UOM precision and whole-number rules under §4.9; no universal three-decimal limit. |
| `unit_id` | Governed unit giving meaning to the quantity. Required for submission. |
| `required_by_date` | Date the department needs the requirement. Required and inside the target FY. |
| `content_hash` | Generated when the revision is submitted and used for idempotency, staleness and downstream lineage. |

Revision records keep the generated name `{need_reference}-V{nnn}` (for example `NDS-MOH-2027-0001-V001`). The suffix is an opaque identifier referenced by Planning lineage and seed data, not a label, and is not renamed with the counter.

### 4.4 DepartmentalNeedReviewTask

One open departmental decision task for one submitted revision.

| Field | Operational purpose and system effect |
|---|---|
| `review_task_id` | Immutable task reference used by the review route and command. |
| `need_id` | Links the task to the stable Need. |
| `need_revision_id` | Fixes the exact immutable content under review. |
| `task_type` | `Initial acceptance`, `Successor acceptance` or `Withdrawal`. |
| `org_unit_id` / `financial_year_id` | Fixes the departmental queue and permission scope. The site PE is implicit. |
| `status` | `Open`, `Completed` or `Cancelled`. |
| `decision_token` | Server-generated optimistic token preventing two decisions on the same task. |

The task is available only to users with an active Head of User Department responsibility assignment whose OU subtree contains the Need. The task routes eligible work but grants no authority. Its Fiscal Year comes from the Need; it is not a user permission or assignment dimension. The task is not described as assigned to a named person until a decision actor completes it. There is no claim, release, priority, score, due-date or free-text task note.

### 4.5 DepartmentalNeedDecision

An immutable record created only by a successful command. It contains decision ID, Need ID, revision or withdrawal-request ID, action, actor, exact User Responsibility Assignment ID and snapshot, timestamp, required reason when applicable, prior state, resulting state, content hash and command correlation ID.

Reasons exist only for:

- `Return for correction`;
- `Do not take forward`;
- `Request withdrawal`; and
- `Decline withdrawal`.

There is no generic reason, comment or evidence field on the Need.

### 4.6 NeedWithdrawalRequest

The minimal request to stop using an accepted Need.

| Field | Operational purpose and system effect |
|---|---|
| `withdrawal_request_id` | Immutable generated reference used by queue, route and audit. |
| `need_id` | Identifies the accepted Need. |
| `accepted_revision_id` | Fixes the revision the requester asks to withdraw. |
| `requested_by_user_id` | Enforces requester authority and maker-checker. |
| `reason` | Explains the business change to the departmental reviewer; 20–1,000 characters. |
| `status` | `Awaiting review`, `Awaiting planning clearance`, `Approved` or `Declined`. |
| `planning_dependency_version` | Identifies the Planning dependency result used by the current decision check. System-generated. |

There is at most one open withdrawal request for an accepted Need. The Need remains `Accepted for planning` until approval succeeds.

### 4.7 NeedPlanningUsageProjection

Planning owns authoritative Active inclusion. NDS stores a read-only projection **per stable Need and exact accepted revision**, retaining old-revision entries after a successor is accepted.

| Field / metadata | Purpose and effect |
|---|---|
| `need_id`, `accepted_revision_id` | Exact represented source. Never substitute the current accepted pointer for an event’s original revision. |
| `usage` | Only `Not included` or `Fully included`. These are confirmed Planning facts, not local defaults on timeout. |
| `active_plan_id`, exact Active Plan Version, `active_plan_item_id`, exact item/allocation references | Reproduce full-source inclusion and authorized navigation; clear current inclusion references only on the matching authoritative removal/replacement event. Retain prior evidence in history. |
| `source_event_id`, ordered-delivery metadata | Deduplicate effects and maintain a per-Need **usage-stream** high-water mark under §7.5. An arbitrary UUID alone does not establish order. |
| Synchronization metadata | Last confirmed event/observation and synchronization health. Transport state is not a third usage value or Need lifecycle status. |

A newly accepted Revision 2 may have no confirmed inclusion while Revision 1 remains Fully included. The stable Need detail must disclose that older revision’s Active dependency. No projection alone authorizes withdrawal; §5.3 uses the current authoritative Planning contract across all revisions.

### 4.8 NeedPlanningDispositionProjection

This separate read-only projection records the outcome of **Procurement acceptance of a complete certified DPP Submission**. It is not a Need review decision, Active usage, funding reservation or fulfilment result.

| Field / metadata | Purpose and system effect |
|---|---|
| `need_id`, `need_revision_id` | Exact accepted Need source in the certified DPP; stable source and immutable revision are distinct. |
| `dpp_submission_id` | Exact accepted Submission; its FY/OU and Need revision must agree. Human reference and Submission number come from Planning, not a guessed ID format. |
| `disposition` | `Proceeding` or `Not proceeding this financial year`; owner-generated at DPP acceptance. No user-editable NDS status. |
| `reason` | Exact certified exclusion reason, 20–500 characters when not proceeding; null for Proceeding. Preserve each earlier accepted reason in history. |
| `actor`, `decision_at` | Actor/time of Procurement acceptance, labelled **DPP accepted by** / **DPP accepted**. These are not falsely attributed as the person/time that originally drafted the exclusion reason. |
| `event_id`, `schema_version`, `producer_sequence` | Exact event identity, supported schema and ordered per-Need disposition stream. Separate from usage-stream ordering. |
| Retained event and revision history | Reproduce each accepted disposition and its source. An old-revision event never overwrites a newer revision’s display. |
| Synchronization metadata | No event, pending refresh, current and failed/gapped sync are explicit technical observation states; none is inferred as Proceeding or Not included. |

The reason passes §2.2’s purpose gate because it explains a specific accepted Planning decision. It is displayed read-only inside **Planning information**, never copied into a generic Need note, Need decision reason or source payload.

### 4.9 Shared identity, Quantity and historical types

| Type | Required rule |
|---|---|
| Stable identity | `need_id` survives all revisions. Exact revision IDs and content hashes fix source content. Display reference/Revision number never replaces exact identity. |
| Revision names / accepted event wire keys | Keep `{need_reference}-V{nnn}` names and `DepartmentalNeedAccepted.v2` keys `accepted_version_id`, `version_number`. The Need UI says **Revision**. Planning says DPP **Submission** and Annual Plan **Version**. No rename-only ID migration or hidden dual-read fields. |
| Quantity | Positive plain decimal string, no binary float, exponent, commas, NaN/Infinity or epsilon. Governed UOM precision defines maximum fractional scale; whole-number units reject fractional quantities. Reject excess precision rather than round. Storage and arithmetic retain at least 18 integral digits plus supported fractional digits; reject overflow. |
| UOM basis | Native UOM ID/display label and owner-returned precision/whole-number constraint with reproducible metadata reference. CFG adapter maps actual native fields; do not invent an `enabled`/precision column or a parallel catalogue. Submission/acceptance retains its exact UOM basis with the immutable content. |
| Hash | Hash canonical exact submitted facts, including Quantity/UOM basis; preserve the agreed producer serialization and historical hash. Numeric representation changes cannot silently recalculate old accepted hashes. Publish actual code mapping and coordinated cutover evidence before release. |
| Money boundary | There is **no Need Money field or Budget service call**. FU-30’s NDS work covers removal of float/epsilon quantity paths and exact source handoff. BUD/PLN/REQ own their monetary values and precision. Shared tests must verify both without introducing funds into NDS. |
| Date / instant | Required-by is an ISO date inside the target FY. Decision/event instants are ISO UTC; UI uses Africa/Nairobi. Server/producer authority determines actors and times. |

Drafts may omit not-yet-required values; a provided value must satisfy its type/range. Changing Draft UOM never rounds a saved quantity automatically. If new rules make it invalid, explain and require explicit correction before submission. Current UOM eligibility is rechecked at acceptance through the owner contract; older immutable revisions remain readable with their retained basis even after catalogue change.

The logical accepted payload now requires exact Quantity strings. Inspect the actual v2 producer/consumer wire type before implementation: if an existing numeric payload differs, perform a coordinated documented producer/consumer cutover or explicitly approved new event version. Do not silently change an existing wire schema, emit both types under one undocumented contract, or call this a harmless label rename. The supplied source documents do not prove the live wire type.

### 4.10 User labels and unchanged identities

| Source field | Visible label | Meaning / guidance |
|---|---|---|
| `title` | Requirement title | Give the requirement a short, recognisable name. |
| `description` | Description | Describe what is needed. |
| `expected_operational_result` | Expected result | What will the department be able to do when this need is met? |
| `indicative_quantity` | Quantity | Enter the total quantity needed. |
| `unit_id` | Unit | Select the unit that describes the quantity. |
| `required_by_date` | Required by | When does the department need it? |

There are still exactly six requester-entered source facts. Department/FY identify authorised immutable context, not added requirement fields. Description and Expected result remain distinct; no additional justification or budget field. First-save title and submission limits in §4.3 remain unchanged. Internal enums, `accepted_version_id`/`version_number` keys and opaque `-Vnnn` identifiers remain intact. The updated labels are presentation only and do not require rehashing historical evidence.

## 5. Lifecycle and business rules

### 5.1 Initial Need lifecycle

| Current state | Command | Result | Authorised actor |
|---|---|---|---|
| No record | Save Draft | Draft Revision 1 and generated Need reference | Departmental Author |
| Draft | Save Draft | Updated Draft | Departmental Author who owns the Need |
| Draft | Submit | Submitted | Departmental Author who owns the Need |
| Draft | Withdraw | Withdrawn | Departmental Author who owns the Need |
| Submitted | Return for correction | Submitted revision becomes Returned; copied successor Draft is created; root displays Returned | Head of User Department |
| Submitted | Accept for planning | Submitted revision becomes Accepted; root becomes Accepted for planning | Head of User Department |
| Submitted | Do not take forward | Submitted revision and root become Not taken forward | Head of User Department |
| Returned | Save correction | Returned successor Draft updated; root remains Returned | Departmental Author who owns the Need |
| Returned | Resubmit | Successor Draft becomes Submitted | Departmental Author who owns the Need |
| Returned | Withdraw | Successor and root become Withdrawn | Departmental Author who owns the Need |

### 5.2 Accepted successor lifecycle

| Current accepted state | Command | Result |
|---|---|---|
| Accepted for planning; no open successor | Create update | Copy accepted revision into one Draft successor. Accepted revision remains effective. |
| Draft update | Save / Submit update | Save the successor or lock and route it for departmental review. |
| Draft update | Cancel update | Successor becomes Withdrawn; earlier accepted revision remains effective. |
| Update submitted | Return | Submitted successor becomes Returned and a copied correction Draft is created. Earlier accepted revision remains effective. |
| Update submitted | Accept proposed changes | Successor becomes Accepted; earlier accepted revision becomes Superseded; new accepted event is published atomically. |
| Update submitted | Decline proposed changes | Successor becomes Not taken forward; earlier accepted revision remains effective. |

There may be only one open successor per Need. No command edits or deletes the content of an Accepted, Superseded, Submitted, Returned, Not-taken-forward or Withdrawn revision. Only the named audited lifecycle transitions can change its status; a correction creates a new Draft copy. An open withdrawal request blocks new successor creation, and an open successor blocks a new withdrawal request; see §5.3.

### 5.3 Accepted withdrawal lifecycle

| Current request state | Live Planning dependency | Decision | Result |
|---|---|---|---|
| Awaiting review | No Active inclusion of any revision of this Need | Approve | Need and accepted revision become Withdrawn; withdrawal event is published. |
| Awaiting review | Active Plan inclusion | Evaluate | Request becomes Awaiting planning clearance; Need remains Accepted. |
| Awaiting planning clearance | Still included | Re-evaluate | No state change. |
| Awaiting planning clearance | Inclusion cleared | Approve | Need and accepted revision become Withdrawn. |
| Awaiting review or clearance | Any | Decline | Request becomes Declined; Need remains Accepted. |

Planning clearance is performed through its governed successor route. A Draft or submitted DPP alone is not an Active Plan dependency; withdrawal can invalidate that source without mutating the certified snapshot. The decision checks the stable Need **across all accepted revisions**, not just the revision named by the request or the local usage card.

The display check is read-only and not a commit guarantee. Approval uses Planning’s owner-controlled decision validation in §8.3, serialized with Plan activation and Need changes until NDS withdrawal and outbox commit. Unknown, stale, failed or gapped dependency evidence blocks approval; never treat absence of a local projection as clearance. Concurrent activation/withdrawal must produce one valid ordering, not an Active allocation of a withdrawn source.

The request pins the current accepted revision. A changed accepted pointer fails approval with a stale-source result, preserving the request for explicit resolution. To avoid orphaned update tasks, an accepted successor and a withdrawal request are mutually exclusive open changes; creation of either checks this under the stable Need lock. Existing inconsistent data must be reconciled explicitly, not silently cancelled. A blocked withdrawal can still be **declined with reason**, completing the request and leaving the Need accepted; it cannot be approved until Planning clears every dependency.

### 5.4 Invariants

| ID | Rule and enforcement |
|---|---|
| NDS-BR-001 | Every Need resolves to one authorised Organisation Unit and one target Fiscal Year. The site PE is implicit. Missing or ambiguous OU authority or an ineligible Fiscal Year fails closed. |
| NDS-BR-002 | Initial creation and initial submission require CFG’s effective-open verdict on the same Fiscal Year, rechecked server-side inside the write transaction. Reaching `kentender_needs_submission_closes_at` closes intake with the same effect as a manual close. Existing authorised records remain readable after the flag is closed. |
| NDS-BR-003 | Closing Needs submission blocks initial creation and initial submission only. Existing Draft and Returned initial revisions remain **editable and saveable**, so work in progress survives a closed intake and is ready if intake reopens. Submission stays blocked while the flag is closed. Accepted revisions, successor proposals and withdrawal requests are governed by their own lifecycle and are not affected by the flag. |
| NDS-BR-004 | One Need represents one requirement and has exactly one quantity, one unit and one required-by date. It has no funding specification. |
| NDS-BR-005 | The Departmental Author who owns the Need edits the initial Draft or returned correction. The Head of User Department decides the submitted revision. |
| NDS-BR-006 | The actor who submitted the revision cannot decide that revision. Maker-checker is rechecked on the server. |
| NDS-BR-007 | Submission requires all six fields in section 4.3 and a current governed unit. |
| NDS-BR-008 | Need creation, submission and acceptance do not select or validate a Procurement Budget Line, capture an amount, check funding or create a reservation. |
| NDS-BR-009 | Required-by is inside the target FY and quantity is positive. |
| NDS-BR-010 | Submit creates one immutable content hash, one open review task and one durable notification event in the same transaction. |
| NDS-BR-011 | Return and decline require a 20–1,000 character reason. Accept has no invented reason field. |
| NDS-BR-012 | Accept means suitable for departmental procurement planning only. It creates no Plan Item, reservation, Requisition or Tender. |
| NDS-BR-013 | When Procurement Planning consumes a Need, it consumes the current Accepted revision for new source incorporation and cannot edit, split, partially include or inflate its quantity. Exact older revisions remain immutable historical/Active references until governed replacement. This rule does not prohibit a Planning-owned direct departmental requirement. |
| NDS-BR-014 | Planning usage is separate from Need lifecycle and accepted DPP disposition. Only authoritative Active inclusion/removal changes usage; exclusion never clears a dependency. |
| NDS-BR-015 | Accepting a successor atomically supersedes the earlier accepted revision and publishes exact old/new lineage. It does not rewrite a DPP or Active Plan. |
| NDS-BR-016 | An accepted withdrawal remains pending while any accepted revision of this stable Need has an authoritative Active Plan dependency; a newer accepted pointer or disposition does not clear an older revision’s inclusion. |
| NDS-BR-017 | Generated references, revision numbers, statuses, hashes and audit data are never client-editable. |
| NDS-BR-018 | Every write checks record revision, decision token and idempotency key under one transaction. |
| NDS-BR-019 | Counts, rows, direct routes, services and exports use the same server-side scope predicate before data is materialised. |
| NDS-BR-020 | No legacy Demand schema, state, route, service, permission, test or fixture is used. |
| NDS-BR-021 | A direct departmental requirement is created and governed in Procurement Planning. It does not create, impersonate or backfill a Departmental Need. |

## 6. Roles, assignments and permissions

| Business responsibility | Central scope classification | Permitted work |
|---|---|---|
| Departmental Author | Organisation Unit | View own Needs; create and edit own Draft/Returned Need; submit, resubmit and withdraw before acceptance; propose an update or withdrawal of own accepted Need. |
| Head of User Department | Organisation Unit | View Needs in the assigned OU subtree; decide submitted Needs, successor updates and withdrawal requests, except own submitted revision. |
| Procurement Planner | Site-wide | Read current accepted Need revisions through the typed source contract and exact read-only deep link; no Need decision and no separate intake-window workspace. |
| Auditor | Site-wide or approved OU oversight scope | Read scoped Needs, revisions, decisions and lineage; no business mutation. |
| Administrator / System Manager | KT-STD-001 v1.6 §3A.6 | Technical access is inherited from the controlling standard; NDS adds no business command or local exception. Separate setup maintenance remains CFG/AUTH-owned. |

User Responsibility Assignment is the sole source of the role-to-site-wide/OU relationship. Frappe Roles are synchronized framework projections and Frappe User Permission, User Scope Assignment, Capability Profile and Operational Scope Assignment grant no Departmental Needs authority. Organisation Unit assignment includes that node and its descendants in the site tree. Fiscal Year eligibility derives from the open Needs-submission flag for initial creation and submission, or from the existing Need for later reads and decisions.

All ordinary business scope/masking clauses below are subject to KT-STD-001 v1.6 §3A.6; they do not restrict a technical reader. Register this module’s root/revision/task/withdrawal read routes and record types with the shared technical search and conformance gate; do not duplicate its implementation.

No global browser context is required to enter Departmental Needs. Visible department and Financial Year filters are local and changeable; no PE control is provided. It does not grant authority, cannot permanently bind later visits and is not required for a direct record or review-task route.

A temporary acting HoD receives the same Head of User Department responsibility through a dated Acting User Responsibility Assignment for the exact OU. Do not create a delegate role or another approval level.

### 6.1 Actor journeys and decision boundaries

| Actor | Normal work | Correction / exception |
|---|---|---|
| Departmental Author | Create own six-field requirement and submit; inspect the result | Open returned correction directly; propose an accepted update or request withdrawal, one open accepted-source change at a time |
| Head of User Department | Open full submitted requirement and accept, return or decline | Compare proposed changes with accepted facts; decide update or withdrawal without deciding own submitted work |
| Procurement Planner | Read exact accepted source from the existing Planning record | Historical source stays pinned; return to originating Planning context; no source editing or Needs review task |
| Auditor | Read scoped Need, exact revisions, decisions and Planning information | Inspect earlier evidence without silently replacing it with current values; no mutation |
| Administrator / System Manager | Authorised technical read and existing CFG/AUTH setup | Diagnose scope/intake through owner settings; technical access supplies no Need decision |

People with multiple responsibilities see permitted work together, without a role switch. HoD responsibility by itself grants no Author creation/edit rights. Finance, AO, statutory authorities, suppliers and bidders receive no additional Departmental Needs work. Use responsible role names when a task has no uniquely assigned person; do not invent a personal assignee. Current server authority and maker-checker control every action.

## 7. Procurement Planning integration

### 7.1 Accepted source payload

`DepartmentalNeedAccepted.v2` contains only:

- event ID and accepted time;
- Need ID and reference;
- accepted revision ID, number and content hash;
- PE, OU and FY IDs;
- title, description and expected operational result;
- indicative quantity and governed unit ID/display value;
- required-by date.

It does not contain Procurement Budget Line, indicative amount, funding source, currency, Strategy, requirement type, procurement method, location, attachment, source reference, generic evidence or notes.

Wire keys are unchanged by the v1.9 rename: the accepted revision travels as `accepted_version_id` and `version_number`, and the contract stays at `.v2`. Consumers read the keys, not the word.

`DepartmentalNeedSuperseded.v1` identifies the Need, earlier accepted revision/hash, successor accepted revision/hash and the successor accepted payload. `DepartmentalNeedWithdrawn.v1` identifies the withdrawn accepted revision and withdrawal decision. Delivery is transactional-outbox, idempotent and ordered per Need.

### 7.2 Planning treatment and disposition

PLN-CHG-001 v1.18 owns DPP coverage, funding enrichment, classification, governance and Active usage. A Need is optional consultation; a DPP can consist of accepted Needs, direct requirements or both. Direct requirements create no synthetic Need, review or bypass reason.

| Boundary | Required behavior |
|---|---|
| New/current accepted source | Project exactly one Need-origin DPP entry within the appropriate source coverage; retain the six facts, full quantity and exact revision/hash read-only. |
| Initial DPP coverage | PLN v1.18’s current accepted source cohort for that department/FY; every Need in coverage is accounted for as proceeding or reasoned not proceeding. |
| Returned certified DPP | Preserve its stable source cohort; refresh exact revisions within that cohort. An unrelated later accepted Need belongs to a subsequent governed update, not a silent rewrite of the certified submission. |
| Proceeding Need-origin entry | Planning adds eligible Budget Line and exact indicative amount. Budget validates **source OU**, not the user’s broad permission scope. NDS has no Budget field or funding call. |
| Not proceeding entry | Planning retains all six source facts/full quantity and a 20–500 character reason, clears operative funding and excludes the entry from consolidation/totals. It satisfies coverage without a Plan Item. |
| Draft restoration | Planning’s **Restore to planned requirements** removes the current Draft exclusion; funding must be completed again. No accepted-disposition event yet. |
| Certification / Procurement acceptance | HoD certifies proceeding and excluded entries together; Procurement accepts the whole Submission. Only that acceptance publishes the disposition event, for both possible outcomes. No extra NDS approval stage. |
| Entire covered submission excluded | Permitted under PLN readiness; NDS does not force a proceeding source, funding field or empty-plan approval. |
| Accepted Need successor | Makes the old source stale for new/current Planning use; preserves historical certified/approved content. Planning governs source refresh and succession. An older revision can remain represented in an Active Plan and block withdrawal. |
| Accepted withdrawal | Invalidates unconsumed/non-Active source eligibility through the owner event; certified/approved history is retained. Active dependency must be cleared before withdrawal can commit. |
| Later extra scope | Normal Need acceptance and DPP update remain available. PLN’s permanent first-authorised-REQ scope lock prevents adding new scope to the locked item; the additional requirement needs its own eligible Plan Item. Need acceptance promises no fulfilment or Tender coverage. |

### 7.3 Ownership correction and preserved payload

Planning owns DPP Budget selection/indicative amount for both origins. Budget owns financial positions and line eligibility, while CFG owns the funding-source catalogue. Any wording in another document describing a “Need and its selected Budget Line” must be read as the **Need-origin DPP entry’s selection**, not a Need field; this owner boundary takes precedence. The BUD v1.8 narrative still needs the narrow editorial clarification logged in §18.3.

`DepartmentalNeedAccepted.v2` remains the six source facts and accepted identity/lineage described in §7.1. It contains no Planning reason, disposition, money or classification. Existing wire identity keys and opaque `-V{nnn}` suffixes remain. Optional direct requirements keep DPP lineage and never produce an NDS event.

### 7.4 New accepted-disposition event

`NeedPlanningDispositionChanged.v1` is produced by **Planning**, delivered through its transactional outbox only after the complete DPP acceptance transaction commits, and consumed by `project_need_planning_disposition`. It is distinct from `NeedPlanningUsageChanged.v1`.

| Wire field | Type / required meaning |
|---|---|
| `event_id` | Globally unique opaque event identity, bound to immutable payload; duplicate identity with different payload is invalid. |
| `schema_version` | Integer 1 for this agreed event schema. Unknown versions are rejected/quarantined, not guessed. |
| `producer_sequence` | Positive monotonic integer in this stable Need’s **disposition stream**; allocated transactionally with the owner event. |
| `need_id`, `need_revision_id` | Stable source and exact accepted source revision in the accepted DPP. Must exist and belong together; current pointer equality is not required for historical replay. |
| `dpp_submission_id` | Exact accepted DPP Submission; authorized owner lookup supplies display reference/number, FY/OU and outcome verification. |
| `disposition` | Exact enum `Proceeding` or `Not proceeding this financial year`. |
| `reason` | 20–500 characters for Not proceeding this financial year; JSON null for Proceeding. No arbitrary note or inherited old exclusion reason. |
| `actor` | Trusted actor identity of the Procurement acceptance, with authority provenance resolvable from the owner decision. Browser-supplied author identity is not trusted. |
| `decision_at` | Owner-recorded UTC acceptance instant. Order uses producer sequence, never wall-clock comparison alone. |

For each accepted Submission, emit one event per Need-origin entry in that certified coverage, including proceeding entries so that a later accepted restoration supersedes an earlier exclusion. Unchanged outcomes can still carry the new accepted Submission’s provenance. Direct entries emit no Need event. Same acceptance retry returns the same event IDs, not a new apparent decision.

No event is published merely because a Draft reason is entered, a HoD certifies, a Submission is returned, or an unaccepted exclusion is removed. An accepted exclusion does not alter Need state from **Accepted for planning**, and never makes it **Not taken forward** or **Withdrawn**. Only a later accepted DPP disposition changes the current accepted-disposition projection; only an Active Plan transition changes usage.

### 7.5 Delivery, ordering, replay and dependency safety

| Case | Consumer requirement |
|---|---|
| Authentication | Registered Planning producer only; validate schema, immutable payload, exact Need/revision and matching DPP FY/OU/acceptance via owner contract or verifiable owner envelope. A shared site ID in legacy accepted payload is routing context, never a user authority grant. |
| Duplicate | Same event ID and payload is a no-op with prior acknowledgement. Different payload under the same ID/sequence conflicts; preserve evidence and reject. |
| Independent streams | Maintain separate sequence/high-water marks for usage and disposition per stable Need. An exclusion with a high disposition sequence must not suppress a later usage event with its own lower number. |
| Out of order / gap | Retain pending event; do not guess omitted transitions or apply a misleading current result. Replay through the Planning owner contract or obtain an authoritative versioned complete snapshot; mark the card refreshing/unavailable meanwhile. |
| Missing source event | If the exact NDS revision has not arrived, defer for reconciliation; create no synthetic Need or remapped revision. A superseded revision that exists remains a valid historical projection target. |
| Replay | Rebuild from authenticated retained stream or owner snapshot; keep immutable prior events/reasons/lineage. Rebuild changes projection metadata only, never Need content, review decisions or source hashes. |
| Usage transition | Preserve Fully included/Not included semantics and exact activated allocation/reversal lineage. A new Plan Version that still includes the same full Need updates exact lineage without a false temporary removal. |
| Historical read | A request for Revision 1 displays its own disposition and usage; current Revision 2 is labelled separately. A late Revision 1 event never becomes Revision 2’s disposition. |
| Withdrawal | Local usage/disposition are information. The Planning owner’s current serialized stable-Need dependency verdict is the approval gate under §8.3. |

The existing usage event’s business payload/meaning is not silently extended to carry dispositions. The actual current usage envelope must be inspected: reliable ordering may be supplied in the existing owner transport metadata. If additional required wire fields would break consumers, agree an explicit versioned change before release. A `source_event_id` UUID is deduplication identity, not a monotonic sequence. The new disposition schema above is the coordinated producer/consumer target, not a claim that the supplied repository already implements it.

## 8. Service and command contracts

All contracts are typed, versioned and server-authorised. Mutating commands require an idempotency key and expected record or decision token.

### 8.1 Read contracts

| Contract | Required input | Output and effect |
|---|---|---|
| `resolve_needs_scope` | Actor and required Departmental Needs responsibility | Exact authorised site-wide/OU scopes and matching assignment IDs from the AUTH-ADR-001 v1.7 resolver. No Fiscal Year permission or fallback authority. |
| `list_needs_financial_years` | Actor | ERPNext Fiscal Years represented by existing Needs visible in the actor's authorised OU scope. This supplies browsing filters only. |
| `list_need_create_targets` | Actor | Authorised OUs combined with the one ERPNext Fiscal Year whose effective Needs intake is Open. Zero, one or several OU targets drive the exact Create behaviour in section 12.1. |
| `get_needs_workspace` | Optional OU, Fiscal Year, status, search and paging filters | Authorised role-specific rows and counts across the actor's durable scope from one predicate. Filters are optional and non-authoritative. |
| `get_departmental_need` | Need reference and optional accepted revision | Authorised detail, current accepted source, open successor, revision-specific Planning usage/disposition, earlier-revision Active dependencies and synchronization status. No mutation. |
| `get_departmental_review_task` | Review task ID and decision token | Exact immutable revision, requester, scope and permitted decision labels. |
| `get_needs_submission_state` | None | The effectively open Fiscal Year and its close instant, or Closed when none is effectively open; include the owner observation time/control revision and authorized display metadata. |
| `get_current_accepted_need` | Need ID/reference, expected context and optional expected hash | Current accepted payload or typed stale/not-accepted error for Planning. |
| `check_accepted_need_withdrawal_dependency` | Need ID and accepted revision | Current complete Active Plan dependencies across all revisions of the stable Need, exact lineage and revision token. No mutation; this display check does not authorize a later commit. |

### 8.2 Commands

| Command | Purpose and required controls |
|---|---|
| `save_need_draft` | Create the originator's Draft after scope, effective-intake and concurrency checks; update an existing owned Draft after scope/state/concurrency checks even when intake has closed. First save generates the Need reference. |
| `submit_need_revision` | Validate all six values, governed unit, maker-checker route and intake/correction eligibility; lock the revision and create one review task. |
| `return_need_revision` | Recheck reviewer scope and maker-checker; require a reason; mark the submitted revision Returned and create one copied correction Draft. |
| `accept_need_revision` | Recheck exact reviewer task, current unit, content hash and concurrency; accept initial or successor revision and publish lineage. |
| `decline_need_revision` | Recheck exact reviewer task; require a reason; close the initial Need or successor without changing an earlier accepted revision. |
| `withdraw_unaccepted_need` | Withdraw the originator's Draft or returned correction. |
| `create_accepted_need_successor` | Copy the originator's current accepted revision into the only permitted Draft successor. |
| `cancel_accepted_need_successor` | Withdraw the originator's Draft successor and leave the earlier accepted revision current. |
| `request_accepted_need_withdrawal` | Create the only open withdrawal request with a required reason and one review task. |
| `decide_accepted_need_withdrawal` | Recheck reviewer, maker-checker and live Planning dependency; approve, block for clearance or decline atomically. |
| `project_need_planning_usage` | Apply authenticated ordered usage event to its exact revision, preserve independent disposition and earlier-revision lineage; §7.5. |
| `project_need_planning_disposition` | Apply §7.4’s authenticated accepted-disposition event, with separate ordering, deduplication and history; no Need lifecycle or usage mutation. |

Notifications are durable post-commit effects for submit, return, accept, decline and withdrawal decisions. They are not separate business records or user-entered messages.

### 8.3 Owner integration and decision contracts

| Contract / ownership | Required behavior |
|---|---|
| Planning disposition/usage read and replay | Owner-authorized exact Need/revision and DPP/Plan evidence, stable stream identities and complete snapshot/replay point. Physical service names and existing transport metadata must be mapped in the coordinated PLN/NDS implementation; no direct Planning table read. |
| `validate_accepted_need_withdrawal_for_decision` — Planning provider, logical new contract | Trusted NDS transaction/request context, stable Need and pinned accepted revision, expected owner dependency revisions. Serialize the complete stable-Need dependency with Plan activation until NDS decision/outbox commit. Return complete exact Active references or confirmed clear; fail closed on stale/unknown state. No Planning mutation or local cached clearance. |
| Current-source validation at Planning activation | Planning validates NDS accepted eligibility through the owner contract under compatible serialization; no Active source may race past committed withdrawal. Specify shared lock order in implementation and test both outcomes. |
| CFG intake/UOM provider | Resolve effective-open and native UOM selectable/precision facts; at the affected command revalidate exact owner facts through CFG’s registered decision contract. No invented native columns, fallback FY or scheduler-only enforcement. |

The new withdrawal validator makes the existing live-dependency invariant enforceable at commit; matching Planning implementation is required before claiming that race is closed. NDS does not acquire another owner’s table locks directly or assume a remote read plus later local commit is atomic. If an equivalent existing owner contract already provides these guarantees, map it explicitly instead of creating a duplicate endpoint.

### 8.4 One user submission action and safe multi-command execution

A new form offers **Save draft** and **Submit for review**. The latter must not require a prior manual Save click. Reuse the existing commands; this specification does not introduce a wrapper business record, approval task or unproven cross-command transaction.

| Step / outcome | Required implementation result |
|---|---|
| Select context | Resolve actual current Author scope and effective-open FY. With multiple departments, require the same-form selection before any write. One target is prefilled; never default to the first of several targets. |
| Submit intention | Validate visible completeness to avoid predictable partial saves; server command validation remains authoritative. Capture a stable payload for this attempt; do not send changed text under a reused key. |
| New unsaved form | Call `save_need_draft` with its original creation idempotency key. On a confirmed result, retain the exact Need/revision/token and replace the new-form route with that identity. Then invoke `submit_need_revision` with a distinct stable submission key bound to that saved revision. |
| Existing edited Draft | Save changed content under its expected token, then submit the confirmed saved revision. If there are no edits to save, invoke Submit directly. Initial/returned-initial versus accepted-update rules are rechecked at each relevant command. |
| Save fails | Do not invoke Submit. Report **Your changes were not saved.** Preserve still-authorised input and field errors. No new task or alleged submitted status. |
| Save succeeds, Submit fails | Retain the created/saved Draft and exact record route. Report **Your draft was saved, but it was not submitted.** Show the actual reason, such as closed initial intake; retry uses this Draft, never a new root. |
| Save result unknown | Resolve/replay the same creation/save request with its unchanged key/payload before submitting or creating another record. Do not infer failure from timeout. No different-payload retry under the old key. |
| Submit result unknown | Resolve/replay the original Submit identity; keep decision controls pending until its authoritative outcome is known. No duplicate task/notification and no success inferred from a spinner ending. |
| Record/authority changes | Re-read protected current state and show the permitted next action. Do not automatically overwrite another edit or resubmit changed content the user has not reviewed. Remove protected display if access is lost. |
| Confirmed submission | The Submit transaction alone freezes the revision/hash, task and outbox atomically. Navigate to the submitted detail with **Awaiting Head of Department review** or the accepted-record **Your changes are awaiting review** notice. |

Persist/recover technical attempt correlation through the existing supported request/idempotency mechanism; inspect actual RPC return/status contracts before implementing. Browser refresh or repeated clicks must not generate a second root/task for the same unresolved attempt. Do not store this state as extra requirement fields or introduce autosave. A first successful save fixes the department/FY; changing a filter or the form selector later cannot transfer ownership.

### 8.5 Presentation of decisions and owner evidence

`accept_need_revision` is presented as **Accept for planning** initially and **Accept proposed changes** for an update. `decline_need_revision` is **Do not take forward** initially and **Decline proposed changes** for an update. The underlying lifecycle, reasons, authority, hashes and event semantics are unchanged. Removing the repeated Accept confirmation dialog changes no decision predicate; place its consequence directly beside the action. Reviewed withdrawal retains its existing focused confirmation and current owner validation.

Planning card labels are a projection of the exact owner evidence, never new statuses written to the Need. Departmental plan Included corresponds to accepted Proceeding; Not included this year corresponds to its accepted exclusion. Current annual plan Included/Not included reflects confirmed Active usage for the displayed exact revision. An earlier revision still in use is explicitly identified; unknown or missing synchronization is never mapped to Not included. Owner link permission and authoritative all-revision withdrawal checks remain separate from the readable card.

## 9. Error contract

| Code | Required result | User-facing explanation / recovery |
|---|---|---|
| `NDS_CONTEXT_REQUIRED` | No authorised Organisation Unit can be resolved. Create no record. | No department is available for you to create a need. Ask your administrator to check your assignment. |
| `NDS_SCOPE_DENIED` | Actor lacks the exact current role-bound User Responsibility Assignment for the record's OU scope. Disclose no protected record data. | You no longer have permission to perform this action. Recheck access; mask record existence where required. |
| `NDS_INTAKE_NOT_OPEN` | Needs submission is closed for the target Fiscal Year. | New submissions are closed. You can save changes to an existing draft and submit if submissions reopen. |
| `NDS_FIELD_REQUIRED` | Return exact missing field identifiers; create no task or state change. | Complete the highlighted fields before submitting. Use the actual plain field labels. |
| `NDS_REQUIRED_BY_OUTSIDE_FY` | Required-by is outside the target FY. | Choose a required-by date within the financial year shown. |
| `NDS_UNIT_INELIGIBLE` | Unit is absent or inactive. | This unit is no longer available. Select an available unit. |
| `NDS_MAKER_CHECKER` | Revision maker attempted its decision. | Another authorised Head of Department must review your submission. |
| `NDS_STATE_CONFLICT` | Command is invalid for the current Need/revision state. | This requirement has changed. Refresh to see the available actions. |
| `NDS_OPEN_SUCCESSOR_EXISTS` | Another accepted successor is already open. | An update is already in progress. Open it to continue if you have permission. |
| `NDS_STALE_WRITE` | Record revision or decision token is stale. Overwrite nothing. | This record has changed since you opened it. Refresh before continuing; retain still-authorised edits separately. |
| `NDS_WITHDRAWAL_ALREADY_OPEN` | One open withdrawal request already exists. | A withdrawal request is already being reviewed. Open it to see the current position. |
| `NDS_ACTIVE_PLAN_DEPENDENCY` | Accepted withdrawal is blocked by the returned Active Plan and Plan Item. | This need is still included in the current annual plan. Procurement must complete the applicable plan change before withdrawal can be approved. |
| `NDS_IDEMPOTENCY_CONFLICT` | The same key was reused with a different payload. | This request could not be safely retried. Check the original result before trying again. |
| `NDS_SOURCE_STALE` | Requested accepted revision/hash is no longer current. | A newer accepted revision is available. Refresh to view the current requirement. |
| `NDS_NOT_ACCEPTED` | No current accepted revision exists. | This need has not been accepted for planning. |
| `NDS_QUANTITY_PRECISION_INVALID` | Quantity exceeds UOM precision/whole-number/range rules or is not an exact decimal string. No rounding or mutation. | Enter a valid quantity for the selected unit. Show its actual whole-number, decimal-place or size limit; do not round. |
| `NDS_PLANNING_EVENT_INVALID` | Producer, schema, identity, reason or accepted DPP source context is invalid. Reject/quarantine without altering projections. | Planning information could not be updated. Show this only in a relevant authorised view; retain valid known information and log technical details. |
| `NDS_PLANNING_SYNC_PENDING` | Missing source/event or stream gap requires owner reconciliation. Retain last-confirmed information with its limitation; infer no clearance. | Planning information is being updated. The last confirmed result is shown where available. |
| `NDS_PLANNING_DEPENDENCY_UNAVAILABLE` | Current serialized Planning dependency cannot be established. Withdrawal approval commits nothing. | We cannot check the annual plan right now. Try again before approving withdrawal. |
| `NDS_OPEN_SOURCE_CHANGE_EXISTS` | An accepted successor or withdrawal is already open. Resolve that change before opening the other kind. | An update or withdrawal request is already open. Complete or cancel it using the permitted action before starting another. |

Errors are stable service results, not inferred from button visibility or free-text exception messages. Display readable copy and a support reference where needed, not raw codes, hashes, payloads or stack traces. Known failures and unknown outcomes differ: never say a save failed when its result is unconfirmed. Apply §8.4 recovery first; preserve permitted input without retaining protected content after access revocation. Planning projection errors do not turn an accepted Need into a failed Need.


## 10. UI architecture, menu and routes

**Departmental Needs** is one top-level KenTender module entry placed after **Budget & Funding** and before **Procurement Planning** in the business-flow menu.

There is no separate menu item for **Review tasks**, **My needs**, a departmental register or another work queue. The Departmental Needs workspace presents the role-appropriate content:

- a Departmental Author sees **My needs** and **Create need**;
- a Head of User Department sees **Needs requiring your decision** followed by the departmental register; and
- a user holding both roles sees both sections on the same workspace.

Procurement Planners use the existing Procurement Planning workspace. A Planning deep link may open NDS-UI-06 read-only for the exact accepted Need; it does not create a Planner landing page.

| Screen | Canonical route | Purpose |
|---|---|---|
| NDS-UI-01 Departmental Needs workspace | `/app/departmental-needs` | Present My needs and/or Needs requiring your decision according to the actor's role. |
| NDS-UI-02 Department review projection | `/app/departmental-needs?view=department` | Deep-linkable in-page reviewer projection; not a menu entry or separate queue application. |
| NDS-UI-03 Need editor | `/app/departmental-needs/new` or `/app/departmental-needs/{need_reference}/edit` | Create, correct or propose an accepted successor using the same six fields. |
| NDS-UI-04 Need detail | `/app/departmental-needs/{need_reference}` | Read Need state, revision-specific Planning information/Active usage and permitted next actions. |
| NDS-UI-05 Review task | `/app/departmental-needs/review/{review_task_id}` | Inspect the complete submitted revision and make one departmental decision. |
| NDS-UI-06 Accepted source detail | `/app/departmental-needs/{need_reference}/accepted/{revision_number}` | Read-only exact accepted revision for Planning lineage. |
| NDS-UI-07 Withdrawal review | `/app/departmental-needs/review/{review_task_id}/withdrawal` | Inspect the full accepted Need, request reason and live Planning dependency. |

The Needs-submission flag is maintained only in the Fiscal Years section of `/app/system-setup` under CFG-CHG-002 v0.10. Departmental Needs exposes no configuration route or page action.

The proven Vue-in-Frappe page pattern and approved KenTender design tokens shall be reused. This document does not authorise a second application shell, custom header, breadcrumb, global context selector or general Procurement Home dashboard.

## 11. Complete screen and static design contract

This is the full replacement design input for Departmental Needs. Assemble it with KT-STD-001 v1.6 §2. The instructions below specify the pictured content and its arrangement; functional action mappings are in §12.10 and are excluded from design prompts.

### 11.1 Shared composition and fixture rules

Use the established KenTender content column, spacing, typography and components. Frappe supplies the surrounding shell. All fixture lines below are outside the rendered artboard.

For each full-page screen:

- Put the title at the upper left. Place the exact description directly beneath it when one is specified. Put header actions at the upper right, in the stated order.
- Put the record reference on its own smaller muted line below the requirement name. Give Revision and Status separate labelled values; never print the instruction “secondary” in the UI.
- Render read-only Department and Financial year as separate labelled facts in a compact shaded group below the header. A selector is used only when that artboard explicitly specifies one.
- Place each page section below the preceding section in the stated order. Use a visible section heading and restrained background/border contrast to distinguish supporting detail.
- In a requirement form or read-only requirement section, place Requirement title, Description and Expected result in that vertical order, each full width. Put Quantity and Unit side by side on the next row, with Required by on the following row. Show complete fixture text; none of these six review facts starts collapsed.
- Place the form/decision footer below all task content, separated by a top border. Its primary action is right-aligned; secondary actions sit to its left in stated order. A destructive secondary action stays at the far left. The footer never covers a field or table row.
- Unless a screen specifies an expanded variant, History and Planning decisions and history start collapsed beneath the main task sections. Critical issues never sit inside them. Each disclosure has its stated content available on the same page.

The Author and HoD use one existing workspace route. The separate artboards below show its actor-specific content; they do not introduce separate menus or a role switch. NDS-DES-10 remains reserved and has no screen. Finance, AO, statutory actors and suppliers receive no new Departmental Needs screen.

The exact six source fields remain Requirement title, Description, Expected result, Quantity, Unit and Required by. Do not add financial, Strategy, classification, supplier, attachment, location or generic-note fields. Quantities use the supplied unit; reference codes are read-only identity. The entire user-entered description/reason is present in these short fixtures. A separate long-content variant in §11.17 specifies expansion controls without truncating the stored text.

The business artboards use the existing named actor assignments. Technical-read variants are separately specified under KT-STD-001 v1.6 §3A.6. No conditional permission expression is a design instruction: each pictured button state below is definite.

### 11.2 NDS-DES-01 — Author workspace

**Purpose:** Find existing needs and continue the work requiring the Author’s action.

**Fixture — outside the artboard:** Grace Wanjiku; Departmental Author in Digital Health and HRMD; 24 Nov 2026, 15:00 EAT; Digital Health selected as the local list filter; no open proposal on accepted infrastructure.

**Header.** Title **My needs** at the upper left; description **Describe your department’s requirements and follow their review.** beneath it. Place **Create need** at the upper right, aligned with the title; enabled.

**Below the header — submission information.** Use four separately labelled facts in one compact group: Department **Digital Health**; Financial year **FY 2027/28**; New submissions **Open**; Closes at **25 Nov 2026, 23:59 EAT**. No entity row or department code appears in this primary group.

**Below submission information — filters.** First row, left to right: wide search input with placeholder **Search title or reference**; Status selector **All statuses**; Financial year selector **All financial years**. Second row: Department selector **Digital Health** at the left; **Clear filters** at the right. No role switch.

**Below filters — needs table.** Columns left to right: Requirement, Quantity, Required by, Status, Action. In Requirement, place the full title on line one and the exact reference beneath in smaller muted text. Keep dates and quantities readable; let titles wrap. Render exactly these two rows:

| Requirement title | Reference beneath title | Quantity | Required by | Status | Action |
|---|---|---|---|---|---|
| National digital health infrastructure upgrade | NDS-MOH-2027-0001 | 1 Programme | 31 Aug 2027 | Accepted for planning | View |
| Clinical deployment laptops for digital health rollout | NDS-MOH-2027-0004 | 150 Each | 31 Dec 2027 | Draft | Continue |



The two Requirement columns in this specification supply the two text lines of the single displayed Requirement cell. No separate Reference column appears. No annual-plan marker appears in this primary 24 November fixture. Place **View** and **Continue** at the right of their rows as enabled navigation links.

**Below the table.** Left-aligned text **2 needs**. No pagination or page-size control in this two-row fixture; no extra summary cards.

**Visual check.** Header action, submission facts, filters, two readable rows and count appear in that order. A reader can distinguish the requirement title, reference, state and next action without interpreting prose instructions printed as cell content.

### 11.3 NDS-DES-02 — HoD work in the shared workspace

**Purpose:** Review pending departmental requirements and browse the department’s existing needs.

**Fixture — outside the artboard:** Dr Peter Kimani; Head of User Department, HRMD; 24 Nov 2026, 15:00 EAT; no Departmental Author assignment in this fixture.

**Header.** Title **Departmental Needs**; description **Review submitted requirements and view the department’s needs.** below. No header action.

**Below the header.** Separate context facts Department **Human Resources Management and Development** and Financial year **FY 2027/28**.

**First content section.** Heading **Needs requiring your decision**, then a full-width table. Column order: Requirement, Submitted by, Quantity, Required by, Review, Action. Requirement uses title then muted reference. One row: Digital health workforce certification programme; NDS-MOH-2027-0002 beneath; Grace Wanjiku; 1 Programme; 31 Dec 2027; Initial requirement; enabled **Review** link at the right. Below: **1 need awaiting review**.

**Second content section.** Place **All departmental needs** below the decision section. Beneath that heading, put a wide **Search title or reference** input and a Status selector **All statuses** on one row. Then render columns Requirement, Requester, Quantity, Required by, Status, Action:

| Requirement title | Reference beneath title | Requester | Quantity | Required by | Status | Action |
|---|---|---|---|---|---|---|
| Digital health workforce certification programme | NDS-MOH-2027-0002 | Grace Wanjiku | 1 Programme | 31 Dec 2027 | Awaiting Head of Department review | View |
| Clinical training laptops for digital health rollout | NDS-MOH-2027-0003 | Grace Wanjiku | 200 Each | 31 Dec 2027 | Changes requested | View |



Both View links are enabled. Below the table show **2 department needs**. No second queue, creation button, role switch or record-edit control.

**Visual check.** Pending work leads the page. The departmental register follows as a separate, quieter section. The 0003 row shows 200 Each at this dated moment.

### 11.4 NDS-DES-03 — Create a departmental need

**Purpose:** Describe one departmental requirement and submit it for review.

**Fixture — outside the artboard:** Grace Wanjiku; both approved Author assignments retained; 24 Nov 2026, 10:05 EAT; new unsaved form, Department already selected as Digital Health; initial submissions open.

**Header.** Title **Create a departmental need**. Under it, **Describe one requirement for your department. Your Head of Department will review it for procurement planning.** No header action, generated reference or revision badge.

**Below the header — context.** Department selector at the left, selected **Digital Health**, with choices **Digital Health** and **Human Resources Management and Development**. Read-only Financial year **FY 2027/28** alongside it. This is the same-form selection already permitted for Grace’s two Author assignments; no preliminary modal.

**Below context — form.** Place the fields in the stated vertical order, with each helper directly beneath its control.

**Requirement content.** Use the six-field arrangement in §11.1 with these exact controls and values.

| Label | Value | Control / helper |
|---|---|---|
| Requirement title | National digital health infrastructure upgrade | Single-line text; Give the requirement a short, recognisable name. |
| Description | Procure and implement national digital health infrastructure across priority health facilities. | Multiline text; Describe what is needed. |
| Expected result | Priority health facilities can use secure and interoperable digital health services. | Multiline text; What will the department be able to do when this need is met? |
| Quantity | 1 | Numeric quantity; Enter the total quantity needed. |
| Unit | Programme | Unit selector; Select the unit that describes the quantity. |
| Required by | 31 Aug 2027 | Date input; When does the department need it? |



**Footer.** Below the content, show **Cancel** / **Save draft** / **Submit for review**, in that order. **Submit for review** is the right-aligned primary action. All listed controls are enabled in this fixture; all unlisted mutation controls are absent.

**Visual check.** Context is distinct from six user-entered source fields. Quantity and Unit share a row; Required by follows. The primary submission action is visible on the complete new form without a separate prior-save screen.

### 11.5 NDS-DES-04 — Returned correction

**Purpose:** Read the reviewer’s request and correct the existing returned draft.

**Fixture — outside the artboard:** Grace; HRMD; NDS-MOH-2027-0003; correction Revision 2; 24 Nov 2026, 14:15 EAT; initial submissions open.

**Header.** Full title **Clinical training laptops for digital health rollout**. Reference **NDS-MOH-2027-0003** beneath; separate badge **Changes requested** and Revision **2**. No header action.

**Immediately below the header.** Highlighted block headed **What needs to change**. Show the full recorded reason: **Confirm the number of trainees to be supported and revise the laptop quantity if the approved training cohort has changed.** Beneath, separate facts Returned by **Dr Peter Kimani** and Returned at **24 Nov 2026, 13:35 EAT**.

**Below the reason.** Read-only Department **Human Resources Management and Development** and Financial year **FY 2027/28**, then the complete editable form.

**Requirement content.** Use the six-field arrangement in §11.1 with these exact controls and values.

| Label | Value | Control / helper |
|---|---|---|
| Requirement title | Clinical training laptops for digital health rollout | Single-line text; Give the requirement a short, recognisable name. |
| Description | Laptop computers for clinical training during the national digital health rollout. | Multiline text; Describe what is needed. |
| Expected result | Provide the equipment required for staff training on the deployed digital health services. | Multiline text; What will the department be able to do when this need is met? |
| Quantity | 200 | Numeric quantity; Enter the total quantity needed. |
| Unit | Each | Unit selector; Select the unit that describes the quantity. |
| Required by | 31 Dec 2027 | Date input; When does the department need it? |



**Below the fields.** A collapsed **History** disclosure. Expanded content: Revision **1**; Decision **Returned for correction**; Decided by **Dr Peter Kimani**; Decided at **24 Nov 2026, 13:35 EAT**; Correction required, with the exact full reason above. Each fact is separately labelled.

**Footer.** At the far left place **Withdraw need**. Below the content, show **Withdraw need** / **Save changes** / **Resubmit for review**, in that order. **Resubmit for review** is the right-aligned primary action. All listed controls are enabled in this fixture; all unlisted mutation controls are absent.

**Visual check.** The correction request is visible before the editable facts. Quantity remains 200 in this pictured state; the later 100-Each correction belongs to its separate dated fixture. Historical wording is not rewritten.

### 11.6 NDS-DES-05 — Submitted detail

**Purpose:** Confirm submission and read the requirement while review is pending.

**Fixture — outside the artboard:** Grace; HRMD; NDS-MOH-2027-0002 Revision 1; 24 Nov 2026, 12:25 EAT; submitted at 12:20 EAT.

**Header.** Title **Digital health workforce certification programme**; muted reference **NDS-MOH-2027-0002** underneath. Separate Revision **1** and badge **Awaiting Head of Department review**. No header action.

**Below the header.** Notice **Your requirement has been submitted. The details cannot be edited while it is under review.** Then separately labelled Department **Human Resources Management and Development**, Financial year **FY 2027/28**, Submitted by **Grace Wanjiku**, Submitted at **24 Nov 2026, 12:20 EAT**.

**Requirement content.** Below the context group, place a section headed **Requirement details**. Use the six-field arrangement in §11.1 with these complete read-only values.

| Label | Read-only value |
|---|---|
| Requirement title | Digital health workforce certification programme |
| Description | Professional certification programme for staff supporting national digital health services. |
| Expected result | Build internal capacity to operate and support national digital health platforms. |
| Quantity | 1 |
| Unit | Programme |
| Required by | 31 Dec 2027 |



**Below the requirement.** Collapsed **History**; expanded, one supplied event with Event **Submitted for review**, Revision **1**, Actor **Grace Wanjiku**, At **24 Nov 2026, 12:20 EAT**. No named personal assignee, edit or decision footer.

**Visual check.** Submitted state and full facts are visible. This page contains no requester mutation or invented review-stage stepper.

### 11.7 NDS-DES-06 — Initial HoD review

**Purpose:** Read the complete submission and make the departmental decision.

**Fixture — outside the artboard:** Peter; HRMD; open task for NDS-MOH-2027-0002 Revision 1; 24 Nov 2026, 12:35 EAT.

**Header.** Title **Review departmental need**. Full requirement name **Digital health workforce certification programme** on the next line, followed by smaller reference **NDS-MOH-2027-0002**. Separate Revision **1**. No header action.

**Below the header.** Read-only facts Requester **Grace Wanjiku**, Department **Human Resources Management and Development**, Financial year **FY 2027/28**, Submitted at **24 Nov 2026, 12:20 EAT**.

**Requirement content.** Below the context group, place a section headed **Requirement details**. Use the six-field arrangement in §11.1 with these complete read-only values.

| Label | Read-only value |
|---|---|
| Requirement title | Digital health workforce certification programme |
| Description | Professional certification programme for staff supporting national digital health services. |
| Expected result | Build internal capacity to operate and support national digital health platforms. |
| Quantity | 1 |
| Unit | Programme |
| Required by | 31 Dec 2027 |



**Below all six facts.** Section **Your decision**. Immediately above its action row, show **Accepting makes this requirement available for departmental procurement planning. It does not approve spending or start procurement.**

**Footer.** Below the content, show **Return for correction** / **Do not take forward** / **Accept for planning**, in that order. **Accept for planning** is the right-aligned primary action. All listed controls are enabled in this fixture; all unlisted mutation controls are absent.

**Visual check.** All submitted facts precede the decision area. No acceptance reason, checklist, acknowledgement or repeated confirmation is drawn.

### 11.8 NDS-DES-07 — Accepted requirement and Planning status

**Purpose:** Read accepted facts and distinguish departmental disposition from current annual-plan inclusion.

**Fixture — outside the artboard:** Grace; Digital Health; NDS-MOH-2027-0001 Revision 1; 5 Jan 2027, 10:15 EAT; independent conditional Active profile; no later exclusion, open update or withdrawal in this primary profile.

**Header.** Title **National digital health infrastructure upgrade**, muted reference **NDS-MOH-2027-0001** beneath. Separate badge **Accepted for planning** and Revision **1**. At upper right show enabled secondary actions **Create update**, then **Request withdrawal**; no review decision action.

**Below the header.** Context group with separate rows Department **Digital Health**, Financial year **FY 2027/28**, Accepted by **Julia Njeri**, Capacity **Acting Head of User Department**, Accepted at **24 Nov 2026, 14:00 EAT**.

**Below context — Planning status.** Heading **Planning status**, followed by two labelled rows: Departmental plan **Included**; Current annual plan **Included**. Below the rows show **These statuses do not confirm that the requirement has been purchased or delivered.**

**Requirement content.** Below the context group, place a section headed **Requirement details**. Use the six-field arrangement in §11.1 with these complete read-only values.

| Label | Read-only value |
|---|---|
| Requirement title | National digital health infrastructure upgrade |
| Description | Procure and implement national digital health infrastructure across priority health facilities. |
| Expected result | Priority health facilities can use secure and interoperable digital health services. |
| Quantity | 1 |
| Unit | Programme |
| Required by | 31 Aug 2027 |



**Below the requirement.** Collapsed **Planning decisions and history**. Expanded, show the following groups in order; each listed fact occupies its own labelled row:

- **Departmental decision:** Requirement revision **1**; Department **Digital Health**; Financial year **FY 2027/28**; Submission **1**; Accepted by Procurement **Mercy Kilonzo**; Accepted at **27 Nov 2026, 14:00 EAT**. Enabled **View departmental plan** link beneath this group.
- **Annual plan:** Plan **PLN-MOH-2027-001**; Version **1**; Item **National digital health infrastructure upgrade**; Item reference **PPI-MOH-2027-021**. Enabled **View annual plan item** link beneath this group.

No additional footer action. No fulfilment, purchase-completed or financial-position badge.

**Visual check.** The two Planning results are visually independent. Their exact source evidence is readable on expansion; the acceptance record remains visible above. This primary profile contains no January exclusion event.

### 11.8A NDS-DES-07A — Planning status variants

**Purpose:** Show each confirmed or unavailable Planning outcome without an ambiguous optional layout.

**Fixture — outside the artboard:** Each variant below is an isolated copy of NDS-DES-07. Same Need 0001, accepted Revision 1 and acceptance facts, except OLDER specifies a later accepted revision. Each has its own stated owner evidence; no cross-profile event reuse.

**Shared variant placement.** Replace the two rows in the Planning status section with the exact values below. Put the full Reason directly beneath those rows when supplied. Place the stated warning below the reason and above Requirement details; it starts visible. Keep the six complete accepted facts and header acceptance badge. The two header actions Create update / Request withdrawal are enabled in NONE, PROCEEDING, EXCLUDED, STILL-ACTIVE and RESTORED, which have no open source change. For REFRESHING and UNAVAILABLE use the same header actions as the last-confirmed STILL-ACTIVE base; no withdrawal-approval control exists on this Author page.

**Exact standalone variants:**

**NDS-DES-07A-NONE.** Fixture outside artboard: 25 Nov 2026, 10:05 EAT; NDS-SC-DISPOSITION-NONE.

- Departmental plan: **No accepted departmental decision recorded**.
- Current annual plan: **Not included**.
- No reason or warning. Both departmental-plan and annual-plan links absent. Planning decisions and history shows Requirement revision 1 and “No accepted departmental decision recorded”; no fabricated decision event.

**NDS-DES-07A-PROCEEDING.** Fixture outside artboard: 28 Nov 2026, 09:00 EAT; proceeding BASE, no activation.

- Departmental plan: **Included**.
- Current annual plan: **Not included**.
- Show “This requirement is in the accepted departmental plan but not the current annual plan.” Departmental evidence: DHI Submission 1; Mercy Kilonzo; 27 Nov 2026, 14:00 EAT. View departmental plan enabled; annual-plan item link absent.

**NDS-DES-07A-EXCLUDED.** Fixture outside artboard: 4 Jan 2027, 14:15 EAT; NDS-SC-DISPOSITION-EXCLUDED, no activation.

- Departmental plan: **Not included this year**.
- Current annual plan: **Not included**.
- Reason: The department will pursue this requirement in a later annual planning cycle. Evidence: DHI Submission 2; Mercy Kilonzo; 4 Jan 2027, 14:00 EAT. View departmental plan enabled; annual-plan item link absent.

**NDS-DES-07A-STILL-ACTIVE.** Fixture outside artboard: 5 Jan 2027, 10:15 EAT; NDS-SC-EXCLUDED-STILL-ACTIVE.

- Departmental plan: **Not included this year**.
- Current annual plan: **Still included**.
- Same full exclusion reason. Evidence: DHI Submission 2; Mercy Kilonzo; 5 Jan 2027, 10:00 EAT. Both owner links enabled; Plan PLN-MOH-2027-001 Version 1, item PPI-MOH-2027-021. Warning: The annual plan has not yet been updated. Withdrawal cannot be approved while this requirement remains included.

**NDS-DES-07A-RESTORED.** Fixture outside artboard: 6 Jan 2027, 10:15 EAT; NDS-SC-RESTORED, successor of STILL-ACTIVE.

- Departmental plan: **Included**.
- Current annual plan: **Included**.
- No current reason. Evidence: DHI Submission 3; Mercy Kilonzo; 6 Jan 2027, 10:00 EAT. Both owner links enabled. Same Active plan/item retained. History keeps Submission 2 exclusion and its full reason separately from Submission 3 restoration.

**NDS-DES-07A-OLDER.** Fixture outside artboard: 15 Dec 2026, 10:30 EAT; independent NDS-SC-OLDER-REVISION-ACTIVE after owner-confirmed Revision 2 acceptance.

- Departmental plan: **No accepted departmental decision recorded**.
- Current annual plan: **Not included**.
- Display Requirement details for Revision 2 with Required by 15 Sep 2027. Separate visible block: “The current annual plan still uses the previously accepted details.” Label Included requirement revision: 1; Earlier required-by date: 31 Aug 2027. Enabled View earlier requirement and View annual plan item beneath that block. No departmental-plan link for Revision 2. Header Create update / Request withdrawal enabled; no open successor remains in this isolated profile. Replace the acceptance context with Accepted by Dr Peter Kimani, Capacity Head of User Department, Accepted at 15 Dec 2026, 10:15 EAT. This is the isolated successor-acceptance fixture specified in §14.5; the canonical Revision 1 acceptance remains unchanged.

**NDS-DES-07A-REFRESHING.** Fixture outside artboard: 5 Jan 2027, 10:16 EAT; refresh in progress from STILL-ACTIVE.

- Departmental plan: **Not included this year — last confirmed**.
- Current annual plan: **Still included — last confirmed**.
- Above the two rows show “Updating Planning information…” and separate Last confirmed: 5 Jan 2027, 10:15 EAT. Retain the full exclusion reason, still-Active warning and both still-authorised owner links. No new current result is shown.

**NDS-DES-07A-UNAVAILABLE.** Fixture outside artboard: 5 Jan 2027, 10:17 EAT; failed refresh from STILL-ACTIVE.

- Departmental plan: **Not included this year — last confirmed**.
- Current annual plan: **Still included — last confirmed**.
- Show “Planning information is temporarily unavailable.” Then “Withdrawal cannot be approved until the required check succeeds.” Last confirmed: 5 Jan 2027, 10:15 EAT. Enabled Try again directly below. Retain reason, still-Active warning and both still-authorised links.

**UNAVAILABLE-NO-SNAPSHOT variant.** Same unavailable heading, explanation and Try again position, but both rows read **Unavailable**. Last confirmed, owner links and decision evidence are absent because no authorised snapshot is supplied. Do not display Not included.

**Expanded evidence treatment.** Each Department, Financial year, Submission, Acceptor and Acceptance time mentioned above gets its own labelled row, using the section order in NDS-DES-07. The compact prose above is fixture instruction, not a line to print on the page.

**Visual check.** Every variant specifies both statuses and its complete link/action treatment. The 4 January exclusion, 5 January still-Active exclusion and 27 November canonical inclusion retain distinct fixture evidence. No status implies fulfilment.

### 11.9 NDS-DES-08 — Propose changes to an accepted Need

**Purpose:** Edit a proposed update while keeping accepted facts clearly distinguishable.

**Fixture — outside the artboard:** Grace; Digital Health; NDS-MOH-2027-0001, accepted Revision 1 and Draft update Revision 2; 15 Dec 2026, 09:10 EAT.

**Header.** Title **Update accepted need**. Full infrastructure requirement name below; reference **NDS-MOH-2027-0001** on a separate muted line. Badge **Draft update**; separate Proposed revision **2**, Accepted revision **1**. No header action.

**Below the header.** Visible notice **The previously accepted requirement remains in effect until these changes are accepted.** Then read-only Department **Digital Health** and Financial year **FY 2027/28**.

**Requirement content.** Use the six-field arrangement in §11.1 with these exact controls and values.

| Label | Value | Control / helper |
|---|---|---|
| Requirement title | National digital health infrastructure upgrade | Single-line text; Give the requirement a short, recognisable name. |
| Description | Procure and implement national digital health infrastructure across priority health facilities. | Multiline text; Describe what is needed. |
| Expected result | Priority health facilities can use secure and interoperable digital health services. | Multiline text; What will the department be able to do when this need is met? |
| Quantity | 1 | Numeric quantity; Enter the total quantity needed. |
| Unit | Programme | Unit selector; Select the unit that describes the quantity. |
| Required by | 15 Sep 2027 | Date input; When does the department need it? |



**Footer.** At the far left place **Cancel update**. Below the content, show **Cancel update** / **Save draft** / **Submit update for review**, in that order. **Submit update for review** is the right-aligned primary action. All listed controls are enabled in this fixture; all unlisted mutation controls are absent.

**Accepted-detail variants.** Use the NDS-DES-07 requirement-detail arrangement with accepted Revision 1, but an isolated 15 December context with owner-confirmed no accepted DPP decision / Not included unless the named profile supplies other results. Replace its two header actions with exactly one notice and link beneath the context group:

- **NDS-DES-08-DRAFT:** 15 Dec 2026, 09:10 EAT; notice **Update in progress**; enabled **Continue update**.
- **NDS-DES-08-SUBMITTED:** 15 Dec 2026, 09:50 EAT; notice **Your changes are awaiting review**; enabled **View proposed changes**. Show Submitted at **15 Dec 2026, 09:45 EAT** in the proposed-change detail.
- **NDS-DES-08-RETURNED:** isolated returned-update presentation at 15 Dec 2026, 11:00 EAT; notice **Changes requested**; enabled **Correct and resubmit**. Full correction reason **Check the required-by date against the programme schedule.** appears beneath the notice. This alternate specimen does not alter the canonical acceptance chronology.

No Create update or Request withdrawal appears in these three open-update variants. Other-author read variant retains the accepted facts and update state but all three maker links are absent.

**Visual check.** The editor identifies the proposal and keeps its consequence visible. Accepted-detail variants keep accepted facts primary rather than replacing them with unaccepted edits.

### 11.10 NDS-DES-09 — HoD review of proposed changes

**Purpose:** Compare the proposed change and decide while seeing the complete proposal.

**Fixture — outside the artboard:** Peter; DHI authority effective from 1 Dec; NDS-MOH-2027-0001 Revision 2, submitted by Grace 15 Dec 2026, 09:45 EAT; review at 10:05 EAT.

**Header.** Title **Review proposed changes**; full infrastructure requirement name beneath; reference **NDS-MOH-2027-0001** on its own muted line. Separate Proposed revision **2** and Previously accepted revision **1**. No header action.

**Below the header.** Context facts Requester **Grace Wanjiku**, Department **Digital Health**, Financial year **FY 2027/28**, Submitted at **15 Dec 2026, 09:45 EAT**.

**First content section — What changed.** Place this comparison above the full proposal:

| Field | Previously accepted | Proposed |
|---|---|---|
| Required by | 31 Aug 2027 | 15 Sep 2027 |



**Requirement content.** Below the context group, place a section headed **Requirement details**. Use the six-field arrangement in §11.1 with these complete read-only values.

| Label | Read-only value |
|---|---|
| Requirement title | National digital health infrastructure upgrade |
| Description | Procure and implement national digital health infrastructure across priority health facilities. |
| Expected result | Priority health facilities can use secure and interoperable digital health services. |
| Quantity | 1 |
| Unit | Programme |
| Required by | 15 Sep 2027 |



**Below the proposal — Your decision.** Show two separate sentences above the buttons: **Accepting updates the requirement available to Planning. Existing departmental and annual plans do not change automatically.** Then **Declining the changes keeps the previously accepted requirement.**

**Footer.** Below the content, show **Return for correction** / **Decline proposed changes** / **Accept proposed changes**, in that order. **Accept proposed changes** is the right-aligned primary action. All listed controls are enabled in this fixture; all unlisted mutation controls are absent.

**Visual check.** The changed field leads the content, but the full proposal remains visible. There is no generic Do not take forward action for this update.

### 11.11 NDS-DES-10 — Reserved — no Needs configuration screen

**Purpose:** Retain the retirement of local Needs setup.

**Fixture — outside the artboard:** No artboard is supplied or drawn.

No screen, local settings action, intake wizard or configuration approval form. Submission-period maintenance remains the existing CFG System setup surface. This reserved identifier is not a missing design task.

### 11.12 NDS-DES-11 — Request withdrawal

**Purpose:** Explain why the accepted requirement should be withdrawn.

**Fixture — outside the artboard:** Grace; NDS-MOH-2027-0001 Revision 1; 5 Jan 2027, 10:20 EAT; no open update or withdrawal before this request. Parent: NDS-DES-07A-STILL-ACTIVE.

**Dialog composition.** Centre the standard 520 px dialog over the dimmed accepted-detail parent. At the top place **Request withdrawal**. Below, show the full infrastructure requirement name; put reference **NDS-MOH-2027-0001** and Accepted revision **1** on separate labelled rows.

Below identity, show **Explain why this accepted requirement should no longer be available for procurement planning.** Then one full-width multiline field **Reason for withdrawal**. Its exact value is **The programme will not proceed in FY 2027/28 because implementation responsibility has moved outside the department.**

At the bottom, right-align enabled **Cancel** followed by primary **Request withdrawal**. No other field or decision control.

**NDS-DES-11-REQUESTED.** On the accepted-detail parent after a confirmed request, remove Create update and Request withdrawal; below context show **Withdrawal requested — awaiting Head of Department review**. Keep accepted source facts and the separately confirmed Planning results. The blocked request uses **Waiting for a Planning change** instead, with the still-Active warning visible in the same region. No new Planning task is drawn.

**NDS-DES-11-OPEN-UPDATE.** Use NDS-DES-08-DRAFT accepted detail; its Continue update link is enabled. Below that notice show **An update is already in progress. Complete or cancel it before requesting withdrawal.** Request withdrawal is absent.

**Visual check.** The request contains one reason field and a clear target. The post-request page still shows accepted facts.

### 11.13 NDS-DES-12 — Withdrawal review

**Purpose:** Read the withdrawal reason and full requirement, then understand whether withdrawal can be approved.

**Fixture — outside the artboard:** Peter; DHI; NDS-WDR-MOH-2027-0001 for infrastructure Revision 1; 5 Jan 2027, 10:30 EAT; primary profile retains Active inclusion.

**Header.** Title **Review withdrawal request**. Full infrastructure requirement name beneath. Separate smaller labelled references Need **NDS-MOH-2027-0001**, Withdrawal request **NDS-WDR-MOH-2027-0001**, Accepted revision **1**. Badge **Waiting for a Planning change**. No header action.

**First section — Withdrawal request.** Place separately labelled Requested by **Grace Wanjiku** and Requested at **5 Jan 2027, 10:20 EAT** at its top. Beneath show the complete Reason for withdrawal: **The programme will not proceed in FY 2027/28 because implementation responsibility has moved outside the department.**

**Second section — Planning status.** Show **Withdrawal cannot be approved yet. This requirement is still included in the current annual plan. Procurement must review the necessary plan change before withdrawal can proceed.** Separate facts Responsible role **Procurement Planner**, Plan **PLN-MOH-2027-001**, Plan version **1**, Item **National digital health infrastructure upgrade**, Item reference **PPI-MOH-2027-021**. Put enabled **View annual plan item** beneath them.

**Third section — Accepted requirement.** Separate Department **Digital Health**, Financial year **FY 2027/28**, then the full read-only facts below.

**Requirement content.** Below the context group, place a section headed **Requirement details**. Use the six-field arrangement in §11.1 with these complete read-only values.

| Label | Read-only value |
|---|---|
| Requirement title | National digital health infrastructure upgrade |
| Description | Procure and implement national digital health infrastructure across priority health facilities. |
| Expected result | Priority health facilities can use secure and interoperable digital health services. |
| Quantity | 1 |
| Unit | Programme |
| Required by | 31 Aug 2027 |



**Footer.** Below the content, show **Decline withdrawal** / **Close**, in that order. No primary decision action appears. All listed controls are enabled in this fixture; all unlisted mutation controls are absent.

**NDS-DES-12-CLEAR.** Separate owner-confirmed no-Active-inclusion profile across every accepted revision; same request/clock/Need. Replace the Waiting for a Planning change badge with **Awaiting review**. Replace the entire Planning-status section with **This requirement is not included in the current annual plan.** Remove plan/item facts and their link. Footer: enabled **Decline withdrawal**, primary enabled **Approve withdrawal**. Keep the full request and requirement sections.

**NDS-DES-12-UNAVAILABLE.** Separate provider-failure profile at the same review clock. Badge **Awaiting review**. Planning-status section reads **Planning information could not be checked. Withdrawal cannot be approved until the check succeeds.** Put enabled **Try again** immediately below. No confirmed plan/item facts or link in this no-snapshot specimen. Footer: enabled **Decline withdrawal** / **Close**; Approve withdrawal absent.

**Visual check.** Each state has one exact footer. The blocked explanation precedes the complete accepted requirement, and approval is visibly absent in blocked/unavailable variants.

### 11.14 NDS-DES-13 — Reason and confirmation dialogs

**Purpose:** Capture an existing required reason or confirm the specified withdrawal/cancellation.

**Fixture — outside the artboard:** Each dialog is an independent state over its named parent, not a sequential chain. Use the standard centred 520 px dialog; exact record identity comes from the explicitly named parent below.

**Shared placement.** Title at top left; full requirement name immediately beneath; Need reference and Revision on separately labelled muted rows. Put the explanatory sentence next, then the one multiline reason field when specified. Footer at bottom right: Cancel followed by the named primary action. Every listed action is enabled in its supplied complete fixture. No reason field on confirmation-only dialogs.

**NDS-DES-13-RETURN-INITIAL.** Parent: Isolated initial review of training laptops 0003 Revision 1 by Peter at 24 Nov 2026, 13:30 EAT; six facts from NDS-DES-04, quantity 200. Heading **What needs to change?**. Field **Correction required**, exact text **Check how many staff need laptops and update the quantity.**. Footer **Cancel** / **Return for correction**. The reason field is full width; it is the only input.

**NDS-DES-13-RETURN-UPDATE.** Parent: NDS-DES-09; infrastructure 0001 Revision 2. Heading **What needs to change?**. Field **Correction required**, exact text **Check the required-by date against the programme schedule.**. Footer **Cancel** / **Return for correction**. The reason field is full width; it is the only input.

**NDS-DES-13-DECLINE-INITIAL.** Parent: NDS-DES-06; certification 0002 Revision 1. Heading **Do not take forward**. Field **Why are you declining this requirement?**, exact text **The requirement is already covered by an existing enterprise service for FY 2027/28.**. Footer **Cancel** / **Do not take forward**. The reason field is full width; it is the only input.

**NDS-DES-13-DECLINE-UPDATE.** Parent: NDS-DES-09; infrastructure 0001 Revision 2. Heading **Decline proposed changes**. Field **Why are you declining these changes?**, exact text **The previously accepted delivery date is still required for the programme.**. Footer **Cancel** / **Decline proposed changes**. The reason field is full width; it is the only input.

**NDS-DES-13-DECLINE-WITHDRAWAL.** Parent: NDS-DES-12; infrastructure 0001 Revision 1. Heading **Decline withdrawal**. Field **Reason**, exact text **The requirement remains valid and must remain available for departmental procurement planning.**. Footer **Cancel** / **Decline withdrawal**. The reason field is full width; it is the only input.

**NDS-DES-13-WITHDRAW-DRAFT.** Parent NDS-DES-04, training laptops 0003 correction Revision 2. Heading **Withdraw this need?**. Text **This withdraws the unaccepted requirement. Earlier submissions and decisions remain in history.** Footer **Cancel** / primary **Withdraw need**.

**NDS-DES-13-CANCEL-UPDATE.** Parent NDS-DES-08, infrastructure 0001 proposed Revision 2. Heading **Cancel these proposed changes?**. Text **The previously accepted requirement will remain in effect.** Footer **Cancel** / primary **Cancel update**.

**NDS-DES-13-APPROVE-WITHDRAWAL.** Parent NDS-DES-12-CLEAR, infrastructure 0001 accepted Revision 1. Heading **Approve withdrawal?**. Text **This withdraws the accepted requirement. Earlier decisions remain in history.** Footer **Cancel** / primary **Approve withdrawal**.

**Visual check.** Only Return/Decline dialogs contain reason inputs. Initial acceptance and update acceptance have no additional confirmation artboard.

### 11.15 NDS-DES-14 — Shared workspace and error states

**Purpose:** Make empty, blocked and failed states understandable without displaying contradictory content.

**Fixture — outside the artboard:** Each named variant independently replaces its stated parent. Shared-state actors inherit that parent unless explicitly changed.

**Page-state placement.** Loading, denied, masked-detail and load-failure variants occupy the existing page content area; no protected header, filters, rows or empty-success message appears behind them. Empty/filtered-empty and closed-intake variants retain their permitted workspace header. Inline form/command notices sit beneath the form header and above its first field or fact group.

**NDS-DES-14-LOADING.** Parent/fixture: Any Needs route, verdict pending.

- Visible text: **Loading departmental needs…**
- Composition and controls: Existing-shape skeleton only; no controls.

**NDS-DES-14-EMPTY-AUTHOR.** Parent/fixture: Author workspace; Grace, Digital Health filter, no records in isolated fixture; intake open.

- Visible text: **No departmental needs yet. Describe the first requirement for your department.**
- Composition and controls: Retain enabled Create need in header. Replace table/count with this text; no duplicate empty-area action.

**NDS-DES-14-EMPTY-READER.** Parent/fixture: Auditor workspace; isolated no-record scope.

- Visible text: **No departmental needs to display.**
- Composition and controls: No Create action. Replace list rows/count with this text; retain permitted filters.

**NDS-DES-14-FILTERED-EMPTY.** Parent/fixture: NDS-DES-01; Search value Unmatched requirement.

- Visible text: **No needs match your filters. Adjust your search or clear the filters.**
- Composition and controls: Retain header and filters. Replace table/count with text; existing Clear filters enabled; no second copy.

**NDS-DES-14-CLOSED-WORKSPACE.** Parent/fixture: NDS-DES-01; isolated close-instant profile at 25 Nov 2026, 23:59 EAT, existing draft retained.

- Visible text: **New submissions are closed. You can view existing needs and save changes to existing drafts.**
- Composition and controls: Create need absent. Submission facts: FY 2027/28; New submissions Closed; Closed at 25 Nov 2026, 23:59 EAT. Existing row navigation remains enabled.

**NDS-DES-14-CLOSED-EDITOR.** Parent/fixture: NDS-DES-04; isolated unaccepted correction at the same close instant.

- Visible text: **New submissions are closed. You can save changes to this draft and submit if submissions reopen.**
- Composition and controls: Withdraw need and Save changes enabled; Resubmit for review disabled. Keep full form and reason; place explanation directly above footer.

**NDS-DES-14-DENIED.** Parent/fixture: Ordinary user without any Needs access; not Administrator/System Manager.

- Visible text: **You do not have access to Departmental Needs.**
- Composition and controls: Below heading: This area needs Departmental Author, Head of User Department or Auditor access. Then: Ask your KenTender administrator to check your assignment in System setup. No action or protected content.

**NDS-DES-14-MASKED-DETAIL.** Parent/fixture: Ordinary actor without existence permission; never technical reader.

- Visible text: **This requirement is not available to you.**
- Composition and controls: Only Back to Departmental Needs beneath the message; no reference/title.

**NDS-DES-14-LOAD-FAILURE.** Parent/fixture: Any authorised Needs route; no successful data response.

- Visible text: **Departmental Needs could not be loaded. Try again. If the problem continues, contact support.**
- Composition and controls: Enabled Try again below the text; no invented support reference.

**NDS-DES-14-SAVE-FAILED.** Parent/fixture: NDS-DES-03; write failure on complete form.

- Visible text: **Your changes were not saved.**
- Composition and controls: Retain entered values; Cancel, Save draft and Submit for review enabled after failure. Field validation specimen below is separate.

**NDS-DES-14-PARTIAL-SUBMIT.** Parent/fixture: NDS-DES-03; isolated newly saved infrastructure NDS-MOH-2027-0001 Draft Revision 1, initial submit rejected because intake closed.

- Visible text: **Your draft was saved, but it was not submitted.**
- Composition and controls: Below notice show the closed-editor explanation. Show saved reference NDS-MOH-2027-0001 and Revision 1 on separate labelled rows. Save draft enabled; Submit for review disabled. The displayed identifier is the prescribed result of this isolated save fixture, not a client-generated identifier.

**NDS-DES-14-SUBMIT-UNKNOWN.** Parent/fixture: NDS-DES-03; submission response unknown.

- Visible text: **We could not confirm whether submission succeeded. Checking the existing request…**
- Composition and controls: Submit for review and other initiating writes disabled while checking; preserve entered facts. No success state or second submission button.

**NDS-DES-14-REVIEW-CHANGED.** Parent/fixture: NDS-DES-06; stale task response.

- Visible text: **This review has already changed. Refresh to see the current result.**
- Composition and controls: Enabled Refresh beneath notice; decision buttons absent until refreshed.

**NDS-DES-14-AUTHORITY-CHANGED.** Parent/fixture: Formerly permitted open form; command denied and current read denied.

- Visible text: **You no longer have permission to perform this action.**
- Composition and controls: Remove protected form content; Back to Departmental Needs enabled beneath message.

**NDS-DES-14-QUANTITY-ERROR.** Parent NDS-DES-03; Quantity entered **0**. Inline under Quantity: **Enter a quantity greater than zero.** Retain all other values. Footer Cancel / Save draft / Submit for review remains visible; Submit for review is not shown as successful. No modal.

**NDS-DES-14-NO-OPEN-YEAR.** Existing-author workspace with no effective open year. Use the CLOSED-WORKSPACE explanation and omit Create need. Display New submissions **Closed**; no target financial year or closing timestamp is invented. Existing-record filters and permitted row links remain.

**Visual check.** Denial/failure never looks like an empty successful list. Each variant specifies the pictured button treatment; technical access follows its separate variant rather than ordinary denial.

### 11.16 NDS-DES-15 — Department choice within the new form

**Purpose:** Choose the department on the same form without a separate preliminary step.

**Fixture — outside the artboard:** Grace; the two actual Author assignments; 24 Nov 2026, 10:05 EAT; initial intake open.

**NDS-DES-15-MULTIPLE.** Use NDS-DES-03 exactly, but Department starts unselected with placeholder **Select department**. Choices: **Digital Health**; **Human Resources Management and Development**. Keep read-only Financial year **FY 2027/28** beside it. The six fields retain their supplied values. Footer Cancel enabled; Save draft and Submit for review disabled while this required choice is empty. No Continue button or choice dialog.

**NDS-DES-15-SINGLE.** Isolated reduced-assignment fixture with only Digital Health eligible, not the canonical two-assignment Grace seed. Replace the selector with read-only Department **Digital Health**. Keep all other NDS-DES-03 content and enabled footer actions.

**NDS-DES-15-PERSISTED.** Named existing Draft, deployment laptops NDS-MOH-2027-0004 Revision 1 at 24 Nov 2026, 15:00 EAT. Heading **Clinical deployment laptops for digital health rollout**; muted reference and badge Draft. Department **Digital Health** read-only; FY **2027/28** read-only. Use all six deployment facts from the explicit table below. Footer Withdraw need / Save changes / Submit for review, enabled; Submit for review primary.

**Requirement content.** Use the six-field arrangement in §11.1 with these exact controls and values.

| Label | Value | Control / helper |
|---|---|---|
| Requirement title | Clinical deployment laptops for digital health rollout | Single-line text; Give the requirement a short, recognisable name. |
| Description | Laptop computers for deployment at priority facilities during the national digital health rollout. | Multiline text; Describe what is needed. |
| Expected result | Provide endpoint equipment required to use the deployed digital health services. | Multiline text; What will the department be able to do when this need is met? |
| Quantity | 150 | Numeric quantity; Enter the total quantity needed. |
| Unit | Each | Unit selector; Select the unit that describes the quantity. |
| Required by | 31 Dec 2027 | Date input; When does the department need it? |



**NDS-DES-15-NO-TARGET.** Isolated actor with existing readable needs but no eligible create target. Retain the existing workspace and row links; Create need absent. Beneath its header show **You do not have an eligible department for creating a need. Ask your KenTender administrator to check your Departmental Author assignment.** Do not show an empty create form or a department selector with no choices.

**Visual check.** The canonical multi-assignment actor sees a real same-form choice. The single-target and persisted forms show a fixed owner; no financial-year chooser appears.

### 11.17 NDS-DES-01–15 supplements — Reader, history and content variants

**Purpose:** Complete actor and state coverage with explicit compositions.

**Fixture — outside the artboard:** Each supplement below names its parent, actor and independent state.

**NDS-DES-01-SUBMITTED.** Grace; Digital Health; 24 Nov 2026, 16:05 EAT. Use the Author workspace with its two rows; change deployment 0004 status to **Awaiting Head of Department review** and action to enabled **View**. No Draft Continue link remains on that row. Infrastructure row unchanged; no annual-plan marker.

**NDS-DES-01-RETURNED.** Grace; HRMD filter; 24 Nov 2026, 14:15 EAT. Replace table rows with certification 0002 (1 Programme; 31 Dec 2027; Awaiting Head of Department review; View) and training laptops 0003 (200 Each; 31 Dec 2027; Changes requested; Correct and resubmit). Use their full titles and references from NDS-DES-02. Context Department HRMD; remaining open-intake facts unchanged. Footer **2 needs**.

**NDS-DES-01-PLAN-INCLUDED.** Grace; Digital Health; 5 Jan 2027, 10:15 EAT; independent conditional Active profile with one infrastructure record displayed. One row: full infrastructure title/reference; 1 Programme; 31 Aug 2027; Accepted for planning; View. Directly below the acceptance status, smaller text **Annual plan: Included**. Count **1 need**. Intake is Closed; Create need absent. This marker is absent in the primary 24 November artboard.

**NDS-DES-01-PLAN-NOT-INCLUDED.** Same one-record layout, 4 Jan 2027, 14:15 EAT no-activation exclusion profile. Marker **Annual plan: Not included**. Full source remains Accepted for planning. No financial or fulfilment label.

**NDS-DES-01-OPEN-PROPOSAL.** One-record infrastructure workspace, 15 Dec 2026, 09:10 EAT; no activation, initial intake Closed. Status **Accepted for planning**, followed by secondary **Update in progress**; action **Continue update**. Submitted variant at 09:50 replaces secondary status with **Changes awaiting review** and action **View**. Neither replaces the accepted badge or adds a separate planning-status column.

**NDS-DES-02-DUAL-ROLE.** Isolated regression fixture: Grace is Author in DHI and acting HoD in HRMD. Use one workspace titled **Departmental Needs**. Header Create need enabled for her DHI Author assignment. First section **Needs requiring your decision** displays **No needs awaiting your decision** because the supplied HRMD pending item is her own submission. Below it place **My needs** using the two DHI rows from NDS-DES-01, then **All departmental needs** using the HRMD register rows from NDS-DES-02. No role-switch control. This isolated profile does not alter the canonical HoD assignments.

**NDS-DES-07-PLANNER.** Mercy Kilonzo, Procurement Planner; exact accepted infrastructure Revision 1; same independent Active context as NDS-DES-07. Use its context, six read-only facts, Planning status and expanded-evidence composition. Header Create update / Request withdrawal absent. Above the title place enabled **Back to procurement planning**. No mutation footer.

**NDS-DES-07-AUDITOR.** Naomi Chebet, Auditor; same exact accepted source/clock. Use NDS-DES-07 with no header mutations or decision footer. Above title place **Back to Departmental Needs**. Keep Planning decisions and history collapsed; expanded contents exactly as NDS-DES-07. No setup controls.

**NDS-DES-07-HISTORICAL.** Naomi; isolated older-revision profile after Revision 2 acceptance. Heading **Planning status for Revision 1**; full infrastructure requirement name and source reference beneath. Revision 1 facts retain Required by **31 Aug 2027**. Above them a visible notice **A newer accepted revision is available.** Enabled **View current accepted requirement** beneath the notice. Keep the older Active plan evidence labelled Included requirement revision **1**. No redirect-like replacement of the pictured values or mutation footer.

**NDS-DES-TECHNICAL-REGISTER.** Administrator; 24 Nov 2026, 15:00 EAT. Title **Departmental Needs**. Use the existing register filters Search title or reference, Department **All departments**, Financial year **All financial years**, Status **All statuses**, and Clear filters. Display all four dated records: infrastructure Accepted for planning, certification Awaiting Head of Department review, training laptops Changes requested with 200 Each, deployment laptops Draft with 150 Each. Use full titles, source references, quantities and dates already specified above; one View link per row. No Create need, decision section or command footer. System Manager variant has the same composition. Technical search remains the shared standard's existing surface, not a new Needs search screen.

**NDS-DES-TECHNICAL-DETAIL.** Administrator or System Manager; exact certification Revision 1 and open review task at 24 Nov 2026, 12:35 EAT. Use the six facts and context of NDS-DES-06, but title **Digital health workforce certification programme**. All decision controls and their decision area are absent; a read-only **History** disclosure below facts shows the submission event from NDS-DES-05. Existing editor-route variant uses training correction Revision 2 at 14:15: same full values and return reason as NDS-DES-04, all fields read-only and all command controls absent. Below History, place a collapsed **Technical details** group. In the review-task specimen its expanded rows are Need reference **NDS-MOH-2027-0002**, Requested revision **1**, Review **Initial requirement**, Task status **Open**. In the editor-route specimen its rows are Need reference **NDS-MOH-2027-0003**, Requested revision **2**, Revision status **Draft**. No unsupplied token or task identifier is drawn in either specimen.

**NDS-DES-LONG-CONTENT.** Isolated compact-preview layout over NDS-DES-04; same Grace/14:15 fixture and exact stored text. Show the Description preview **Laptop computers for clinical training…** followed directly by enabled **Read full description**. Show the correction-reason preview **Confirm the number of trainees to be supported…** followed directly by enabled **Read full reason**. The expanded variant displays the full original description and full original recorded reason from NDS-DES-04 in their same positions; replace each expansion link with **Show less**. All other fields remain visible. This short-source fixture explicitly demonstrates the expansion layout; it does not invent or rewrite long source text.

**NDS-DES-TERMINAL.** Separate initial-decline specimen for certification 0002 Revision 1; read-only layout of NDS-DES-05, badge **Not taken forward**; decision reason **The requirement is already covered by an existing enterprise service for FY 2027/28.** shown in a visible block beneath context. Withdrawal-terminal specimen for the unaccepted training correction uses badge **Withdrawn** and the same complete six source facts. Decline facts: Decided by Dr Peter Kimani; Decided at 24 Nov 2026, 12:40 EAT. Withdrawal facts: Withdrawn by Grace Wanjiku; Withdrawn at 24 Nov 2026, 14:20 EAT. Display these as separate labelled rows below their state. These alternate owner-command fixtures do not change the canonical seed. No edit, submit or review controls in either state.

**Visual check.** Every actor reuses a named composition, with explicit additions/removals. Technical readers are never sent to the ordinary denied/masked variant. No new business role, configuration page or dashboard is supplied.


## 12. Functional interaction requirements — excluded from design prompts

### 12.1 NDS-UI-01 — Requester workspace

- Enter the workspace directly from the actor's Departmental Author or Head of User Department responsibility assignments. Do not require a global context, a pre-entry selection screen, a Frappe User Permission or a Financial Year assignment.
- Load all of the actor's authorised own Needs across assigned departments and Fiscal Years. If the actor is an HoD, also load the in-page decision section under the same route. Search matches title or reference; department, Fiscal Year and status are optional local filters. There is no PE filter.
- One department may display directly. Several remain available through ordinary changeable filters; they do not block page entry. The last valid filter may be remembered for convenience but is never authority and always has a visible reset.
- Derive create targets by combining active Departmental Author OU assignments with the one ERPNext Fiscal Year for which CFG returns effective Needs intake Open. Do not use a Fiscal Year permission, the list's current FY filter or a browser-stored context.
- If the flag is Open and exactly one authorised OU exists, **Create need** opens NDS-UI-03 immediately with that department and Fiscal Year. If several OUs exist, open the same NDS-UI-03 form with the required inline **Department** selector defined in NDS-DES-15; no separate dialog or Continue step. Lock the department after first persistence. If none exists or submission is Closed, omit the action and show the exact closed/no-scope message while retaining existing rows.
- **Continue** and **Correct and resubmit** route to the actor's editable current revision. **View** routes to NDS-UI-04.
- Submitted, accepted, terminal and another actor's revisions are never editable through a direct URL.
- Closing Needs submission blocks new creation and initial submission, keeps existing initial Draft/Returned Needs editable and saveable; it does not hide accepted or historical authorised records.
- Changing, clearing or restoring any local filter immediately changes the view and never changes a record's ownership or the actor's authority.

### 12.2 NDS-UI-02 — Department review

- The in-page decision section returns only Open tasks in the actor's exact effective OU review scope after maker-checker exclusion, across every Fiscal Year represented by those tasks.
- The department register returns authorised Needs in that same OU scope. Optional local filters may narrow by Fiscal Year; they do not grant actions outside an Open task.
- An acting HoD sees only tasks within the exact OU subtree and effective period of the dated Acting assignment. The Frappe role label alone grants no cross-department access.
- **Review** carries the stable task ID and current decision token to NDS-UI-05 or NDS-UI-07.
- A successful decision removes the task from the queue. A concurrent decision returns `NDS_STALE_WRITE` and reloads the current neutral result.
- Counts, queue rows and register rows use the same database scope predicate.

### 12.3 NDS-UI-03 — Need editor

- First save requires resolved context and a valid title. It creates the root and Draft Revision 1, then replaces the route with the generated Need reference. **Submit for review** is available directly on a complete new form; the UI executes the save-then-submit contract in §8.4 without a prior manual Save step.
- A partial Draft may be saved after the title is valid. Submission requires all six values.
- Unit options come from the governed active unit catalogue.
- Submit revalidates assignment, state, unit, FY date, maker-checker route and intake/correction rule on the server. It performs no Budget service call.
- Disable the initiating action while pending. Each underlying command has its own stable idempotency identity and payload; retries of that command reuse them. Resolve an unknown save or submit outcome before creating another record or task, as specified in §8.4. A successful save followed by rejected submission retains the saved Draft and states both outcomes explicitly.
- Field errors bind to the plain labels in §4.10 and preserve still-authorised input. A business-rule error appears in the error summary and moves focus there. On stale data, reload the authoritative state without silently overwriting either version; reapply edits only through a permitted explicit save. Remove protected content if access is revoked.
- A successful initial submit or resubmit routes to NDS-UI-04. A successful accepted-update submit routes to NDS-UI-04 while the earlier accepted revision remains displayed as current.
- Return creates a copied successor Draft server-side. The returned editor loads that copy and the immutable return reason; it never unlocks the submitted snapshot.
- **Cancel** on a new unsaved form creates no mutation. **Cancel update** confirms and withdraws the open Draft successor, leaving the accepted revision current. Withdrawal before acceptance requires confirmation and routes to the read-only terminal detail after success.

### 12.4 NDS-UI-04 and NDS-UI-06 — Need detail

- Detail resolves the stable Need, current root state, current accepted revision, open successor state, accepted DPP disposition, revision-specific Active usage and synchronization health independently.
- A Submitted revision shows the exact immutable submitted content and no requester mutation.
- Accepted detail shows the exact accepted revision even when a Draft/Submitted successor exists. The successor is represented by a clear status notice and a link available only to its maker.
- **Create update** appears only to the originator when the Need is Accepted and neither an open successor nor withdrawal request exists.
- **Request withdrawal** appears only to the originator when the Need is Accepted and neither an open withdrawal nor successor exists.
- **View Plan Item** uses the exact route returned by the Planning usage projection. It is absent only when there is no confirmed current or older-revision inclusion to link; an older Active dependency retains its separately labelled authorized link.
- The Planning deep link to NDS-UI-06 fixes the accepted revision in the route. If it is superseded, the page remains historically readable and clearly labels the current accepted revision without redirecting or rewriting the requested revision.
- Direct links enforce the same scope as service reads and return Not found when existence disclosure is unauthorised.

### 12.5 NDS-UI-05 — Review task

- Load the exact immutable submitted revision identified by the task, not mutable root fields.
- Render all six requester-entered fields before the decision area. For an update, show the changed facts first in the comparison table, with the complete proposed requirement on the same page. Do not require opening every disclosure before enabling an otherwise permitted decision.
- Initial decisions are **Accept for planning**, **Return for correction** and **Do not take forward**. Update decisions are **Accept proposed changes**, **Return for correction** and **Decline proposed changes**. Return and decline use the appropriate reason dialog in §11.14. Acceptance executes from one explicit action, with the exact consequence beside it in §§11.7 and 11.10; no repeated confirmation dialog. Requirement name and revision stay visible.
- No Accept reason, recommendation, checklist or score is collected.
- Decision commands revalidate task token, assignment, maker-checker, Need state and unit under one transaction.
- Accept initial revision routes to accepted detail. Accept successor routes to the new accepted detail and publishes supersession lineage.
- Returning an initial or successor revision creates the next Draft copy atomically and notifies the maker.
- Declining an initial revision closes the Need. Declining a successor leaves the earlier accepted revision current.

### 12.6 NDS-UI-07 — Withdrawal review

- Load the exact request, complete accepted Need revision and a fresh Planning dependency result.
- The page never relies on a cached button state to authorise approval.
- If an Active Plan dependency exists, the command records/retains `Awaiting planning clearance`, returns the exact Plan/Plan Item reference and exposes no Departmental Needs action that edits Planning.
- **View Plan Item** navigates only. The existing Planning amendment process clears the dependency.
- Approve validates all stable-Need dependencies through §8.3 until the withdrawal/outbox commit. An accepted exclusion, newer revision or local Not included card never substitutes for that validation. Unavailable owner evidence disables approval with the stated recovery message.
- Decline requires the exact decision dialog reason, leaves the accepted revision current and completes the review task.
- The requester cannot decide their own withdrawal request.

### 12.7 Needs-submission state consumption

Consume CFG’s effective-open verdict, exact FY and optional close instant; revalidate within initial create/submit commands. Do not merely read a potentially uncleared Boolean. At the close instant, initial creation, initial submission and resubmission of an unaccepted Returned initial Need are blocked even before hourly cleanup.

Existing initial Draft/Returned content stays editable and saveable; retain **Save draft/Save changes** and **Continue/Correct and resubmit**, with **Submit for review/Resubmit for review** disabled and the explanation **New submissions are closed. You can save changes to this draft and submit if submissions reopen.** Existing accepted successor proposals and reviewed withdrawals follow their separate lifecycle and are not blocked by this initial-intake flag. No closure event rewrites, deletes or hides history.

No Need command changes the flag or close field. NDS has no intake editor. CFG supplies independently governed Needs and DPP flags: an open Needs flag neither opens DPP intake nor overrides a returned DPP’s fixed source cohort or an Active Plan Item’s scope lock.

### 12.8 Common page behaviour and accessibility

- Use semantic headings, labels, tables, status text and keyboard-operable controls. Colour is never the only carrier of state.
- Dialog focus is trapped and restored. Validation focus moves to the first invalid control or error summary.
- Loading, empty, intake-closed, no-authorised-context and error states use the exact copy in NDS-DES-14.
- All dates display in `Africa/Nairobi`; service and audit instants remain UTC.
- Do not wait for `networkidle` on a Frappe Desk page. Tests wait for DOM content plus the exact page-ready selector.
- Route changes unmount the Vue app and cancel stale requests. Returning to a cached Desk page re-resolves context and authorization.

### 12.9 Planning information behavior and accessibility

NDS-UI-04/06 obtain disposition and usage for the displayed exact revision; provide separate older-revision Active dependency rows when relevant. The card is read-only for Author, HoD, Planner, Auditor and technical reader alike. No NDS button sets/restores a Planning disposition, changes its reason, edits a DPP or clears usage. Navigation uses the owner-authorized exact Submission/Plan route; missing permission removes that link without expanding access or inventing a URL.

A refresh never creates a Need decision, accepted-disposition event, Plan Item, reservation or fulfilment record. Show loading/failure independently from known Need facts. A pending or failed Planning read must not replace **Accepted for planning** with an error state or assert **Not included**. Keyboard focus remains stable while the card refreshes; announce the result through an accessible status region, and restore focus after the retry. Reasons wrap as ordinary text with no clipping; preserve meaning without exposing raw event/hash/sequence fields.

The record card presents **Departmental plan** and **Current annual plan** as separate labelled results, with concise explanations and exact reason, actor, date and revision evidence in supporting detail. Use §11.8A for all combinations and unknown states. The workspace omits the blanket Planning usage column; only accepted rows may show optional secondary annual-plan status from confirmed owner evidence. Historical older-revision inclusion is labelled explicitly. Test the two results with representative users; completeness alone does not establish usability.

### 12.10 Complete design-to-interaction map — excluded from design prompts

This is the behavior counterpart to §11. It is not passed to the static design tool. All commands retain §§8.1–8.5 and the existing authority/state/idempotency contracts; the composition rewrite changes no command semantics.

| Screen/control | Navigation or visible result | Existing contract / guard |
|---|---|---|
| Workspace Create need | Open the new form; show inline department choice for multiple eligible targets. | §12.1; list_need_create_targets; NDS-UI-03; no write on opening. |
| Search, Department, Status, Financial year filters | Narrow the current authorised register; Clear filters resets local values. | §§12.1–12.2; existing list read; no ownership/context change. |
| Continue / Correct and resubmit | Open the current editable draft or server-created returned copy. | §12.3; NDS-UI-03; exact maker/current revision. |
| View in a register | Open the selected Need’s current authorised detail. | §12.4; NDS-UI-04; current root and source states remain distinct. |
| Review in decision section | Open the exact review task and submitted revision, or withdrawal review. | §12.2; NDS-UI-05/07; stable task ID, current token and maker-checker. |
| Department selector on new form | Select one allowed create target on this form; no intermediate page. | §8.4 and §12.3; required before first save; fixed after persistence. |
| Six field controls and Unit selector | Edit the draft’s source values; unit choices from the owner. | §§4.3, 4.10, 12.3; exact quantity/date/text rules; no Budget call. |
| Cancel on new unsaved form | Return to the existing workspace without creating a Need. | §12.3; no persistence. |
| Save draft / Save changes | Persist permitted draft values and stay on the saved form. | §§8.4, 12.3; first save returns generated root/revision; retained partial draft. |
| Submit for review / Resubmit for review | Save then submit as one user intention; open submitted detail on confirmed success. | §8.4; separate underlying keys/results; retain saved Draft if submission fails. |
| Return for correction | Open the appropriate reason dialog; confirmed Return records reason and produces the correction copy. | §12.5; preserve exact submitted snapshot; no unlock. |
| Do not take forward | Open initial-decline reason dialog; confirm to end only the unaccepted initial Need. | §12.5; existing decline command and reason. |
| Accept for planning | Perform the one guarded initial acceptance; open accepted detail. | §12.5; no second modal, acceptance reason or spending approval. |
| Create update | Create/open the permitted draft successor using accepted facts. | §12.4; originator, Accepted state, no other open source change. |
| Continue update / View proposed changes | Open the exact editable draft or read-only submitted proposal. | §§12.3–12.4; maker access, fixed revision; accepted facts remain current. |
| Submit update for review | Save/submit the existing successor and return to accepted detail with pending-update notice. | §§8.4, 12.3; initial intake closure does not bar accepted successor flow. |
| Accept proposed changes | Accept the exact submitted successor, open the new accepted detail. | §12.5; source supersession only; plans do not change automatically. |
| Decline proposed changes | Open update-decline reason dialog; confirm to end the successor. | §12.5; retain previous accepted revision. |
| Withdraw need on unaccepted draft/correction | Open focused confirmation; confirmed withdrawal opens terminal detail. | §12.3; existing pre-acceptance command only. |
| Cancel update | Open focused confirmation; confirmed cancellation ends only the draft successor. | §12.3; retain accepted Need and return to accepted detail. |
| Request withdrawal | Open one-reason dialog; confirmed request shows accepted detail and actual request state. | §12.6 and §8.3; originator/open-change guard; no Planning task. |
| Decline withdrawal | Open reason dialog; confirmed decline ends the request and retains accepted Need. | §12.6; reviewer authority/maker-checker. |
| Approve withdrawal | Open focused confirmation; confirm rechecks all accepted-revision dependencies through commit. | §8.3 and §12.6; fresh clear owner result; no cached-clearance authority. |
| Cancel in any decision/confirmation dialog | Dismiss without applying that decision; return focus to its trigger. | Shared standard §3; existing parent state retained. |
| Close in withdrawal review | Return to the existing Needs workspace without a decision. | Navigation only; no clearance/withdrawal mutation. |
| View departmental plan / View annual plan item | Open the exact owner-authorised DPP Submission or Plan Item represented by the evidence. | §12.9 and owner-returned targets; navigation only; no guessed route or approval. |
| View earlier requirement / View current accepted requirement | Open the explicitly selected immutable accepted revision. | NDS-UI-06; §12.4; keep historical version distinct from current. |
| Back to procurement planning | Return to the originating authorised Planning record/context. | Existing owner entry context; no generic Procurement Home. |
| Back to Departmental Needs | Open the existing Needs workspace and resolve current access. | NDS-UI-01; no record mutation. |
| History / Planning decisions and history / Technical details | Expand/collapse the named same-page section. | Authorised exact version/evidence reads; no business command or forced download. |
| Read full description / Read full reason / Show less | Expand the original stored text in place, or return to its faithful preview. | No text rewriting; keyboard focus remains on the expansion control. |
| Try again on load or Planning failure | Repeat the corresponding read/check and replace the error only when resolved. | §§12.8–12.9; missing/unavailable does not become Not included. |
| Refresh after a changed review | Reload the task’s authoritative current result and permitted controls. | §12.5; no replayed decision or fabricated success. |
| Unknown submission result | Recover the original request identity/result before another mutation. | §8.4; pending initiating controls stay disabled; no duplicate root/task. |
| Terminal detail | Show final state and preserved evidence read-only. | Existing lifecycle §§5.1–5.3; no new terminal command. |

The primary Author workspace omits the optional annual-plan marker. Its explicit PLAN-INCLUDED and PLAN-NOT-INCLUDED variants exercise the existing optional presentation only with confirmed exact-revision owner data. Closed-intake editor/workspace variants, return/cancellation dialogs, maker-only links and all mixed Planning states retain their existing runtime predicates; the designer does not choose these predicates.

## 13. Audit and historical integrity

- Framework audit fields identify record creation and technical updates. DepartmentalNeedDecision records business transitions.
- Draft autosaves or routine saves do not create user-authored notes. Material command audit includes actor, exact User Responsibility Assignment ID and snapshot, command, correlation ID, record token, prior/result state and submitted content hash.
- Submitted content is immutable. Return creates a copied Draft successor; it never makes the submitted row editable.
- Accepted content is immutable. A replacement becomes effective only through successor acceptance.
- Decision reasons remain attached to their exact decision and revision. They are not copied into the next Draft as an editable field.
- Planning events preserve exact Need/revision/hash, DPP acceptance and Active allocation/reversal lineage. Keep separate immutable disposition and usage evidence, original reason and producer actor/time. Log consumer receipt/reconciliation separately; do not impersonate the Planning actor as an NDS reviewer. Projection updates never change Need content, state, accepted pointer, quantity or review decision history.
- Timestamps and actors are system-generated. A client cannot supply or amend them.
- Submitted, accepted, superseded, terminal and withdrawal records are not physically deleted.
- Auditor and System Administrator reads do not imply a business action. Standard technical access logging applies; no invented support-reason form is required.

## 14. Deterministic seed contract

### 14.1 Configuration prerequisites

| Fixture | Exact value |
|---|---|
| Site Procuring Entity | `PE-MOH` — Ministry of Health; configured once and not repeated on OU records |
| ERPNext Fiscal Year | `2027-2028` — displayed FY 2027/28 · 1 Jul 2027 to 30 Jun 2028 |
| OU 1 | `OU-MOH-DHI` — Digital Health |
| OU 2 | `OU-MOH-HRMD` — Human Resources Management and Development |
| Unit 1 | Native UOM **Programme**, selectable; owner-defined reproducible precision |
| Unit 2 | Native UOM **Each**, selectable and whole-number under the declared fixture adapter |
| Needs submission | `2027-2028.kentender_needs_submission_open = 1`, closing 25 Nov 2026, 23:59 EAT |
| Design clock | `2026-11-24T12:00:00Z` · 24 Nov 2026, 15:00 EAT unless an artboard states another exact time |

All actors come from the KT-STD-001 §8.3 shared register. The site PE, ERPNext Fiscal Year, Needs-submission flag and close instant, OUs, units of measure and assignments come from Configuration & Governance. Seeds fail if any authoritative prerequisite differs; they do not invent fallback records.

### 14.2 Actors and assignments

| Actor | Exact assignment |
|---|---|
| `grace.wanjiku@moh.example.test` · Grace Wanjiku | Two Departmental Author User Responsibility Assignments: OU-MOH-DHI and OU-MOH-HRMD; no PE or Fiscal Year assignment |
| `peter.kimani@moh.example.test` · Dr Peter Kimani | Head of User Department for OU-MOH-HRMD throughout the fixture; separate OU-MOH-DHI assignment effective from 1 Dec 2026. No parent assignment grants November DHI authority; no FY assignment |
| `julia.njeri@moh.example.test` · Julia Njeri | Acting Head of User Department assignment for OU-MOH-DHI from 1 Oct to 30 Nov 2026 with authority reference |
| `mercy.kilonzo@moh.example.test` · Mercy Kilonzo | Site-wide Procurement Planner; accepted-source contract and exact detail link only |
| `naomi.chebet@moh.example.test` · Naomi Chebet | Site-wide Auditor; read-only across Fiscal Years |

No actor receives authority merely because they are Administrator or because a filter contains a value. Administrator maintains the Needs-submission flag as audited setup, not as a Need decision.

### 14.3 Default Needs

The following is the **post-acceptance baseline at 25 Nov 2026, 10:05 EAT**, not the 24 Nov design-clock workspace. NDS-DES-01/02/04 show the earlier explicitly dated Draft/Returned states. Neither snapshot implies an Active Plan.

| Reference | Department | Title | Quantity | Required by | State | Planning usage |
|---|---|---|---:|---|---|---|
| `NDS-MOH-2027-0001` | Digital Health | National digital health infrastructure upgrade | 1 programme | 31 Aug 2027 | Accepted for planning | Not included — confirmed BASE |
| `NDS-MOH-2027-0002` | HR Management and Development | Digital health workforce certification programme | 1 programme | 31 Dec 2027 | Submitted | Not included |
| `NDS-MOH-2027-0003` | HR Management and Development | Clinical training laptops for digital health rollout | 100 each | 31 Dec 2027 | Accepted for planning | Not included — confirmed BASE |
| `NDS-MOH-2027-0004` | Digital Health | Clinical deployment laptops for digital health rollout | 150 each | 31 Dec 2027 | Accepted for planning | Not included — confirmed BASE |

Exact descriptions and expected operational results:

| Reference | Description | Expected result |
|---|---|---|
| NDS-MOH-2027-0001 | Procure and implement national digital health infrastructure across priority health facilities. | Priority health facilities can use secure and interoperable digital health services. |
| NDS-MOH-2027-0002 | Professional certification programme for staff supporting national digital health services. | Build internal capacity to operate and support national digital health platforms. |
| NDS-MOH-2027-0003 | Laptop computers for clinical training during the national digital health rollout. | Provide the equipment required for staff training on the deployed digital health services. |
| NDS-MOH-2027-0004 | Laptop computers for deployment at priority facilities during the national digital health rollout. | Provide endpoint equipment required to use the deployed digital health services. |

**Explicit v1.11 fixture resolution:** NDS-MOH-2027-0001 Revision 1 is accepted by **Julia Njeri**, acting HoD for DHI, on **24 Nov 2026 at 14:00 EAT**. This retains the original acceptance instant and corrects the unauthorized November Peter attribution. The NDS owner decision resolves SEED v1.3’s missing authoritative infrastructure-acceptance prerequisite at specification level; shared seed adoption and executable evidence remain required. NDS-MOH-2027-0002 is submitted by Grace Wanjiku on 24 Nov 2026 at 12:20 EAT.

NDS-MOH-2027-0003 Revision 1 is returned by Dr Peter Kimani on 24 Nov 2026 at 13:35 EAT with the exact NDS-DES-04 reason. Revision 2, the server-created editable copy, corrects the quantity to 100 each, is resubmitted by Grace Wanjiku on 25 Nov 2026 at 09:00 EAT and accepted by Dr Peter Kimani, as Head of User Department for Human Resources Management and Development, on 25 Nov 2026 at 10:00 EAT.

NDS-MOH-2027-0004 Revision 1 is submitted by Grace Wanjiku on 24 Nov 2026 at 16:00 EAT at a quantity of 150 each and accepted by Julia Njeri, as Acting Head of User Department for Digital Health, on 25 Nov 2026 at 09:30 EAT. Both acceptances land inside the intake window, which closes 25 Nov 2026 at 23:59 EAT.

### 14.4 BASE and conditional Planning integration

SEED-001 v1.3 governs the shared distinction: the default Plan with None/None planned designations remains blocked Draft; an Active Budget and accepted DPP do not make it Active. BASE therefore has confirmed **Not included** usage for each Need, supplied through the Planning owner baseline/read contract, not inferred from missing events.

On 25 Nov 2026 Julia certifies DHI at 10:30 EAT and Peter certifies HRMD at 11:00. Mercy accepts the DHI Submission 1 on 27 Nov at 14:00 and HRMD at 14:05. In the proceeding BASE scenario, each Need in the accepted source cohort emits its own Proceeding disposition at that DPP acceptance;0002 remains unaccepted and emits none. Infrastructure0001 and deployment 0004 refer to DHI Submission 1; training 0003 Revision 2 refers to HRMD Submission 1. Exact root/Submission IDs come from the owner fixture and are not guessed from display labels.

The 27 Nov 2026, 14:00 EAT acceptance of DHI Submission 1 retains its Proceeding disposition for infrastructure 0001 Revision 1. It is not reused as an exclusion event. The no-Active-inclusion exclusion variant instead uses the distinct later DHI Submission 2 acceptance on 4 Jan 2027, 14:00 EAT in NDS-SC-DISPOSITION-EXCLUDED (§14.6A). The still-Active exclusion is a different isolated profile with its own Submission 2 acceptance on 5 Jan 2027, 10:00 EAT. Each builder supplies separate exact submission/event identities; a matching display number across isolated profiles does not make their evidence interchangeable. Annual-plan inclusion still requires the separate authoritative activation described below; DPP acceptance alone does not produce it.

A separate conditional Active scenario, after all owner readiness/legal/configuration/date gates pass, includes infrastructure 0001 Revision 1 in `PPI-MOH-2027-021` and training 0003 Revision 2 plus deployment 0004 Revision 1 in `PPI-MOH-2027-033`, with exact Active Plan `PLN-MOH-2027-001`/Version1 and allocation identities from Planning. Each source is Fully included only after actual Plan activation. This conditional profile supplies NDS-DES-07 and the blocked withdrawal artboard; it never forces BASE Active or loads Active usage into November screens.

Need source quantities are Programme 1, Each 100 and Each 150; laptops require31 Dec 2027 in Needs/Planning. REQ’s operational30 Sep 2027 date is a later owner field and never overwrites these source dates. Funding selection is entirely Planning-owned; BUD v1.8’s fresh HWD Entity-wide line supports both departments, with reservations 20m/30m created only at REQ authorisation and never projected as NDS funding data.

Retain SEED/CFG’s unresolved cross-module fiscal-year/applicability prerequisite (CFG-XD-001) and LAW v1.1 verification gates for positive downstream claims. NDS acceptance and these read-only cards do not resolve those legal/date dependencies.

### 14.5 Isolated successor and withdrawal fixtures

The successor profile copies NDS-MOH-2027-0001 Revision 1 into Revision 2 and changes only:

| Field | Revision 1 | Revision 2 |
|---|---|---|
| Required by | 31 Aug 2027 | 15 Sep 2027 |

Acceptance emits the exact supersession event without altering Revision 1. For the explicitly isolated NDS-DES-07A-OLDER / historical-read artboards, Peter accepts infrastructure Revision 2 on 15 Dec 2026 at 10:15 EAT, after the 09:45 submission and 10:05 review. This fixture supplies the missing displayed acceptance facts; it does not change the canonical Revision 1 acceptance or imply automatic Planning inclusion.

The withdrawal profile creates `NDS-WDR-MOH-2027-0001` with the exact NDS-DES-11 reason. Its blocked variant uses the Active Plan dependency in section 14.4; its cleared variant uses an authoritative Planning result with no Active inclusion of **any** accepted revision, with exact dependency revision evidence. Merely injecting a local Not included projection is not a valid withdrawal test.

Terminal-state, stale-write, concurrent-decision, expired-delegation, open/closed-flag and sibling-OU isolation records exist only in named isolated test profiles. They are not added to the default four-row workspace fixture.

Direct departmental requirement fixtures belong to Procurement Planning and create no Departmental Needs seed record. The Planning integration profile must prove a DPP containing only direct requirements and another containing both source origins without changing the four Needs above.

### 14.6 Retired — see SEED-001

This section previously held a bare, ungrounded `SRC-KEBS-ICT-00X` profile — no real Need IDs, no accepting actor, no Fiscal Year, keyed to an entity that cannot exist under one-site-one-PE. It duplicated and conflicted with `NDS-MOH-2027-0003` and `NDS-MOH-2027-0004`, both specified above with stable IDs, actors and acceptance dates, which are the ones that actually feed Planning's harmonized combined Plan Item. SEED-001 v1.3 is the cross-module reference for the complete chain those two Needs now feed.

### 14.6A Isolated disposition and synchronization profiles

| Profile | Precondition / exact result |
|---|---|
| NDS-SC-DISPOSITION-NONE | Accepted Need; owner confirms both an empty accepted-disposition history and no Active inclusion. Card says no accepted decision, not implicit Proceeding. |
| NDS-SC-DISPOSITION-EXCLUDED | Independent BASE-derived profile with no Plan activation. After canonical DHI Submission 1, create and certify a later DHI Submission 2 through PLN’s accepted-update lifecycle; Mercy Kilonzo accepts it on 4 Jan 2027, 14:00 EAT. Infrastructure 0001 Revision 1 receives Not proceeding this financial year with the exact reason from NDS-DES-07A. Need remains Accepted; owner confirms usage Not included. This Submission 2 and its acceptance event have their own owner-generated identities, distinct from both canonical Submission 1 and the 5 Jan still-Active profile. |
| NDS-SC-EXCLUDED-STILL-ACTIVE | Independent conditional Active baseline; later DHI Submission 2 accepted 5 Jan 2027, 10:00 with exclusion. Preserve Fully included and block withdrawal. |
| NDS-SC-RESTORED | Successor to preceding isolated profile: DHI Submission 3 accepted 6 Jan 2027, 10:00, Proceeding/reason null; retain prior exclusion in history. No usage change from this event. |
| NDS-SC-OLDER-REVISION-ACTIVE | Revision 2 accepted through the normal December successor profile; Revision 1 remains represented in the prior Active Plan. Current card labels both; withdrawal remains blocked. |
| NDS-SC-ORDERING | Deliver sequence 2 before 1, exact replay, changed-payload duplicate, missing source, unsupported schema and usage/disposition interleaving. No false current projection or lifecycle change. |
| NDS-SC-CLOSE-INSTANT | At exactly 25 Nov 2026, 23:59 EAT with physical flag still 1, initial create/submit fail while Draft saves pass. A separate accepted successor can submit under its lifecycle. |
| NDS-SC-UOM-PRECISION | Each whole-number fixture rejects 1.5; a separately declared selectable fractional native UOM accepts its exact supported scale and rejects one extra digit. No global three-decimal assumption or float tolerance. |
| NDS-SC-WITHDRAWAL-RACE | Owner-valid Plan activation races withdrawal; shared serialization admits one valid outcome. Provider failure or stale revision leaves the Need accepted and no withdrawal event. |
| NDS-SC-OPEN-CHANGE-RACE | Concurrent successor/withdrawal creation yields one open accepted-source change, never orphaned review tasks. |

These profiles do not invent live external decisions. They are deterministic owner-command fixtures or explicitly identified provider-contract tests. Exact event IDs, per-stream sequences and DPP identities are frozen by the executable fixture builders; until supplied and validated, the document defines expected behavior rather than claiming end-to-end success. The isolated later DPP updates use PLN’s accepted-update lifecycle after intake closes.

### 14.7 Seed execution rules

- Seed keys and timestamps are deterministic and idempotent.
- Seed scripts call domain builders or public commands that enforce the same invariants as production setup.
- Default, Planning usage, successor, withdrawal and negative profiles are independently selectable and resettable.
- No seed creates a legacy Demand, partial Need allocation, reservation, Requisition or Tender.
- No test changes the process clock, current accepted revision or Planning usage without restoring its isolated transaction or fixture namespace.

## 15. Acceptance contract

All 61 v1.10 criteria remain mapped within the 85 retained v1.11 criteria below (61 original plus 24 added in v1.11). This successor reconciles those criteria and adds 20 usability criteria in §15.2, for 105 in total. These are required implementation results, not claims of tests run in this document review. Prior IDs are traceability, not a second operative contract.

| ID | Prior criterion / source | Required result |
|---|---|---|
| NDS11-AC-001 | NDS-AC-001 | One Need contains exactly the six requester-entered values in section 2.2 and no item child table or funding field. |
| NDS11-AC-002 | NDS-AC-002 | OU authority is explicit and server-authorised; the site PE is implicit and the target Fiscal Year is derived from the one open Needs-submission flag or the existing record. First-record and current-FY fallbacks do not exist. |
| NDS11-AC-003 | NDS-AC-003 | Initial create/submit require CFG effective-open on the exact native FY; at/after close or disabled FY they fail atomically even before Boolean cleanup. |
| NDS11-AC-004 | NDS-AC-004 | A valid partial Draft saves after title; submission rejects every missing required value without side effects. |
| NDS11-AC-005 | NDS-AC-005 | Required-by is inside target FY. Quantity is an exact positive decimal string within supported UOM precision/whole-number and storage range. |
| NDS11-AC-006 | NDS-AC-006 | Unit comes through CFG’s selectable native UOM adapter; no guessed native enabled field, free-text Other, parallel unit catalogue or default precision. |
| NDS11-AC-007 | NDS-AC-007 | Need creation, submission, review, acceptance, payload and screens contain no Procurement Budget Line, indicative amount, funding source or currency. |
| NDS11-AC-008 | NDS-AC-008 | Need save, submit and acceptance create no funding reservation or availability check. |
| NDS11-AC-009 | NDS-AC-009 | Submit creates one immutable revision/hash, one scoped review task and one notification effect atomically and idempotently. |
| NDS11-AC-010 | NDS-AC-010 | A revision maker cannot decide that revision; expired or cross-scope review assignments fail closed. |
| NDS11-AC-011 | NDS-AC-011 | Return requires a reason, preserves the submitted revision and creates one copied correction Draft. |
| NDS11-AC-012 | NDS-AC-012 | Decline requires a reason. Accept collects no reason, score, recommendation or checklist. |
| NDS11-AC-013 | NDS-AC-013 | Accept for planning creates no Plan Item, Strategic Objective selection, classification, Requisition or Tender. |
| NDS11-AC-014 | NDS-AC-014 | New Planning incorporation uses the current accepted revision and full quantity; older exact revisions remain immutable historical/Active references until governed replacement. No partial Need inclusion. |
| NDS11-AC-015 | NDS-AC-015 | Usage remains only confirmed Not included/Fully included, independent from Need lifecycle and accepted DPP disposition; missing/failed sync is not default Not included. |
| NDS11-AC-016 | NDS-AC-016 | An accepted revision is immutable; an open successor does not replace it before acceptance. |
| NDS11-AC-017 | NDS-AC-017 | Successor acceptance atomically supersedes the earlier revision and publishes exact old/new lineage. |
| NDS11-AC-018 | NDS-AC-018 | Successor decline leaves the earlier accepted revision current. |
| NDS11-AC-019 | NDS-AC-019 | Maker-checked withdrawal cannot commit while any accepted revision of the stable Need remains represented in an Active Plan; approval uses serialized owner validation and fails closed on unavailable/stale evidence. |
| NDS11-AC-020 | NDS-AC-020 | Only Planning’s governed route clears Active dependencies. NDS adds no DPP/Plan mutation; an accepted DPP exclusion or newer Need revision never substitutes for clearance. |
| NDS11-AC-021 | NDS-AC-021 | Search, counts, rows, detail, export and service access use the same server-side OU scope and record-Fiscal-Year eligibility predicates. |
| NDS11-AC-022 | NDS-AC-022 | Departmental Author, Head of User Department, acting-HoD, Procurement Planner and auditor permissions match section 6; System Administrator can inspect all records and maintain the setup flag but cannot make a Need decision without the business role and OU scope. |
| NDS11-AC-023 | NDS-AC-023 | Budget Officer and Accounting Officer receive no Departmental Needs workspace, task or special action. |
| NDS11-AC-024 | NDS-AC-024 | The Planning source payload includes the expected operational result and contains no Procurement Budget Line, amount, funding source, currency, Strategy, requirement type, generic evidence, location or attachment. |
| NDS11-AC-025 | NDS-AC-025 | All retained NDS-DES-01–15 identifiers plus NDS-DES-07A render their revised explicit scenarios/clock, six facts and exclusions. DES-15 is the inline department-choice variant; reserved configuration artboard remains unbuilt. |
| NDS11-AC-026 | NDS-AC-026 | Breadcrumb and Frappe header remain outside every Claude Design artboard and use the existing framework components. |
| NDS11-AC-027 | NDS-AC-027 | Runtime behaviour is implemented from section 12, not inferred from static design output. |
| NDS11-AC-028 | NDS-AC-028 | Concurrent/idempotent commands preserve one effect; accepted successor and withdrawal creation serialize to one open source change; projection events use separate ordered streams. |
| NDS11-AC-029 | NDS-AC-029 | No delivery location, attachment, source reference, notes, contact, Strategy, classification or line-item field exists. |
| NDS11-AC-030 | NDS-AC-030 | No `/demands`, `/departmental-needs` or `/desk/departmental-needs` compatibility route exists. |
| NDS11-AC-031 | NDS-AC-031 | Reuse the Planning owner’s existing source/enrichment/disposition UI. NDS supplies read-only Planning information on existing details, never a duplicate editor or workspace. Proposed PLN v1.19 is not approved through this document. |
| NDS11-AC-032 | NDS-AC-032 | A fresh environment creates the exact clean schema and selectable seed profiles without a legacy prerequisite. |
| NDS11-AC-033 | NDS-AC-033 | Cancelling a Draft accepted successor withdraws only that successor and leaves the earlier accepted revision current. |
| NDS11-AC-034 | NDS-AC-034 | A HoD or authorised departmental plan preparer can create a Planning-owned direct departmental requirement without a Departmental Need. |
| NDS11-AC-035 | NDS-AC-035 | A DPP and its Plan Items may be formed entirely from direct departmental requirements, entirely from accepted Needs, or from both source origins. |
| NDS11-AC-036 | NDS-AC-036 | A direct departmental requirement creates no synthetic Need, Need review task, bypass reason or Need audit event. |
| NDS11-AC-037 | NDS-AC-037 | Accepted-Need entries retain Need/revision/hash lineage; direct entries retain DPP-entry lineage and are never presented as accepted Needs. |
| NDS11-AC-038 | NDS-AC-038 | Expected result is present in the immutable Accepted revision and `DepartmentalNeedAccepted.v2`. |
| NDS11-AC-039 | NDS-AC-039 | The Need ID remains the stable source-line identity through Planning. |
| NDS11-AC-040 | NDS-AC-040 | Planning receives the expected operational result read-only and receives no supplier obligation or Tender parameter. |
| NDS11-AC-041 | NDS-AC-041 | Only Departmental Author and Head of User Department perform Need lifecycle actions. |
| NDS11-AC-042 | NDS-AC-042 | An acting HoD uses the same responsibility through a dated Acting User Responsibility Assignment; no delegate role or extra approval level exists. |
| NDS11-AC-043 | NDS-AC-043 | Administrator or System Manager opens or closes Needs submission directly from the System setup Fiscal Years section; there is no intake-window workflow or Need decision. |
| NDS11-AC-044 | NDS-AC-044 | One role-bound User Responsibility Assignment and the shared AUTH resolver enforce durable site-wide/OU scope without Frappe User Permission, User Scope Assignment or a Fiscal Year grant as authority. |
| NDS11-AC-045 | NDS-AC-045 | The Need-origin (`NDS-MOH-2027-0003`, `NDS-MOH-2027-0004`) and an equivalent direct-Planning entry preserve equivalent source facts. |
| NDS11-AC-046 | NDS-AC-046 | Departmental Needs opens directly without a global context or pre-entry selection screen. |
| NDS11-AC-047 | NDS-AC-047 | With one eligible Open intake target, **Create need** opens the editor immediately with no intermediate choice. |
| NDS11-AC-048 | NDS-AC-048 | With several authorised OUs and one open Fiscal Year, choose Department within the new Need form, with no separate modal/Continue step. PE and Fiscal Year are not selectable; Department becomes immutable after first save. |
| NDS11-AC-049 | NDS-AC-049 | A Departmental Author assigned to one OU can create in the one open Fiscal Year without annual access provisioning. |
| NDS11-AC-050 | NDS-AC-050 | Choosing or filtering a future, closed or different Fiscal Year never binds later visits, hides other authorised records or prevents creation when administrators later open an eligible year. |
| NDS11-AC-051 | NDS-AC-051 | HoD decision work appears inside the ordinary Departmental Needs workspace and no separate **Review tasks** work-queue menu exists. |
| NDS11-AC-052 | NDS-AC-052 | `NeedsIntakeWindow`, `PEFiscalYearContext`, PE selectors and repeated PE keys are absent from the Departmental Needs schema and UI. |
| NDS11-AC-053 | NDS-AC-053 | CFG’s owner command keeps at most one Needs flag configured open and applies confirmed switch semantics atomically. NDS consumes effective eligibility without editing either year. |
| NDS11-AC-054 | NDS-AC-054 | Closing Needs submission blocks Create need and Submit, leaves Save draft enabled on an existing Draft or Returned revision, and changes no Accepted, Withdrawn or historical record. |
| NDS11-AC-055 | NDS-AC-055 | At exact closes_at, create/initial submit fail even if physical flag remains 1; CFG audit preserves scheduled effective-close versus actual cleanup time without backdating. |
| NDS11-AC-056 | NDS-AC-056 | A create or submit command issued after the flag closed but before page reload is rejected server-side. |
| NDS11-AC-057 | NDS-AC-057 | Selectable/precision UOM facts come from the owner-mapped native adapter; no invented enabled column, KenTender UOM DocType or other_unit field. |
| NDS11-AC-058 | NDS-AC-058 | No Procuring Entity row, selector or column appears on any Departmental Needs screen. |
| NDS11-AC-059 | NDS-AC-059 | Every page resolves its authorisation verdict before rendering; a denied actor sees the inline Forbidden panel with no header, filter, content or empty state painted, and no permission modal appears on page load. |
| NDS11-AC-060 | NDS-AC-060 | The Forbidden panel names the responsibilities that open the surface and directs the user to a KenTender administrator; it names no line manager or supervisor. |
| NDS11-AC-061 | NDS-AC-061 | Selecting this module without access pushes its own route, highlights it in navigation, and lands on its Forbidden state; the module is never hidden and route and view never diverge. |
| NDS11-AC-062 | FU-24; PLN-RI-018 | NeedPlanningDispositionChanged.v1 is emitted only after complete DPP acceptance; Draft edits, certification, return and unaccepted restoration emit none. |
| NDS11-AC-063 | FU-24; schema | The new event has exact stable Need/revision/accepted Submission IDs, disposition/reason, actor/time, schema/event identity and per-Need disposition sequence; invalid source/FY/OU/producer/schema is rejected or reconciled without remapping. |
| NDS11-AC-064 | FU-24; separation | Accepted not-proceeding leaves Need Accepted for planning and preserves all six facts/full quantity; it never becomes Need Not taken forward/Withdrawn or changes Active usage. |
| NDS11-AC-065 | FU-24; accepted restoration | A later accepted Proceeding event replaces only that revision’s accepted disposition, uses reason null and preserves earlier accepted exclusion evidence/Submission identity. |
| NDS11-AC-066 | FU-24; direct sources | Each accepted covered Need-origin entry emits its disposition, including Proceeding; direct entries never create a Need event or synthetic Need. |
| NDS11-AC-067 | FU-24; independent order | Usage and disposition have separate per-Need high-water marks; an exclusion’s sequence cannot suppress a legitimate Active usage event from the other stream. |
| NDS11-AC-068 | FU-24; duplicate/gap | Same event/payload is a no-op; changed payload conflicts. Sequence gaps/out-of-order delivery and missing source trigger replay/pending status, never guessed current state or clearance. |
| NDS11-AC-069 | FU-24; exact history | Late events for an older revision update only its retained projection; exact historical route preserves that revision while clearly identifying the current accepted revision. |
| NDS11-AC-070 | FU-24; UI completeness | Planning information shows Departmental plan and Current annual plan independently, retaining the exact reason/Submission, acceptance actor/time and displayed revision. Owner-authorised links only; no editable reason/status or new queue. |
| NDS11-AC-071 | FU-24; no evidence/unavailable | Confirmed absence of an accepted departmental decision renders No accepted departmental decision recorded; pending/unconfirmed absence renders updating/unavailable. Missing or failed usage is unavailable, never Not included. Retry creates no business event or lifecycle change. |
| NDS11-AC-072 | FU-24; exclusion still Active | Accepted exclusion with existing Active inclusion shows both outcomes and the explicit withdrawal-blocked explanation; no inference of fulfilment or released procurement scope. |
| NDS11-AC-073 | Withdrawal integrity | Revision 2 accepted while Revision 1 remains Active still blocks stable-Need withdrawal; local current-revision Not included cannot bypass the older dependency. |
| NDS11-AC-074 | Withdrawal concurrency | Concurrent Planning activation and NDS withdrawal have one valid serialized outcome; stale/unavailable provider or caller rollback creates no withdrawn-but-Active source. |
| NDS11-AC-075 | Withdrawal governance | Blocked reviewer can Decline withdrawal with 20–1,000 character reason and maker-checker; no Approve while included. Decline leaves Need accepted and usage intact. |
| NDS11-AC-076 | Open change governance | Concurrent accepted-successor/withdrawal requests yield one open change with no orphan task. An old withdrawal pinned to a different accepted revision cannot approve silently. |
| NDS11-AC-077 | FU-30; Quantity | Exact Quantity strings persist and round-trip through NDS/PLN/REQ without float/epsilon; supported fractional unit succeeds, Each fractional quantity/excess precision/overflow fails without rounding. |
| NDS11-AC-078 | Wire/identity continuity | Revision UI labels retain opaque -Vnnn IDs and accepted_version_id/version_number keys. Actual numeric wire schema and content-hash mapping are inspected; any breaking change has a coordinated declared cutover, never silent v2 drift. |
| NDS11-AC-079 | Budget ownership | No Need Money field, Budget selection, eligibility call, reservation or funding projection is introduced; DPP source OU/funding belongs to PLN/BUD and reservations to REQ authorisation. |
| NDS11-AC-080 | CFG intake | Closed intake leaves existing initial Draft/Returned editable and saveable; only initial creation/submission/resubmission are blocked. Accepted updates/withdrawals retain their own lifecycle; Needs flag never overrides DPP intake. |
| NDS11-AC-081 | CFG UOM history | Current UOM eligibility/precision is checked at submission and acceptance; immutable old source values/basis remain readable after catalogue change and no automatic rounding or rehash occurs. |
| NDS11-AC-082 | Shared fixture authority | Julia accepts DHI infrastructure 0001 on 24 Nov14:00; DHI 0004 on 25 Nov09:30. Peter’s DHI authority starts 1 Dec and cannot author November DHI decisions; HRMD acceptance remains25 Nov10:00. |
| NDS11-AC-083 | Shared fixture chronology | 24 Nov artboards retain dated Draft/Returned states;25 Nov accepted baseline has no Active usage;27 Nov accepted dispositions remain distinct from conditional later Plan activation.100/150 laptop quantities and 31 Dec source dates agree with SEED v1.3. |
| NDS11-AC-084 | Read permissions / states | Technical read remains read-only and discoverable; ordinary Forbidden renders no header/filter/data. Planner uses accepted-source deep links, no new Needs workspace or OU requirement on its site-wide role. |
| NDS11-AC-085 | Document adoption | All 61 original criteria and all 85 v1.11 criteria retain traceability; this successor adds 20 usability criteria and ten change rows. Approval of the amendment is distinguished from approval of this full successor, implementation, passed tests, seed adoption and current-law verification. |

### 15.1 Minimum automated coverage

| Layer | Required evidence |
|---|---|
| Domain / permissions | Six-field validation, exact Quantity/UOM, immutable revisions, role/OU combinations, maker-checker, technical read, root and accepted pointers, mutually exclusive open changes. |
| Command / concurrency | Initial and successor lifecycles, Return-copy, decline, withdrawal; effective close instant before scheduler; active dependency across revisions; activation/withdrawal race and full rollback. |
| Owner contracts | Accepted/superseded/withdrawn source events; distinct disposition and usage streams; full schema, identity, gap/replay/duplicate and historical tests; exact producer/consumer wire mapping. |
| Cross-module precision | Shared NDS/PLN/REQ Quantity and BUD/PLN/REQ Money suites. No monetary field in Needs to satisfy a generic precision checklist. |
| Browser / UX | Same-form department choice; single user Submit with partial/unknown outcome recovery; one explicit Accept; update comparison and decision consequences; all actor journeys; keyboard/narrow-screen reading. Existing seven route families; accepted detail variants including older-revision dependency, unavailable provider, exact reason/provenance and links; blocked Decline withdrawal; no hidden route or unauthorized data flash. |
| Deterministic seed | Separate 24 Nov,25 Nov,accepted DPP and conditional Active scenarios; exact actors/authority and source dates; no forced BASE activation or fabricated production-law verification. |


### 15.2 Approved usability amendment coverage

These additional criteria implement NDS-UX-001–010. Retained NDS11-AC identifiers above remain active as reconciled in this successor; historical wording is not an alternative UI contract.

| ID | Approved source | Required result |
|---|---|---|
| NDS12-AC-001 | NDS-UX-001 | All six fields use the exact §4.10 user labels on create, correction, detail and review; text, quantity and date validation remain unchanged. |
| NDS12-AC-002 | NDS-UX-001 | Labels do not rename stored fields, stable IDs, accepted.v2 keys or historical submitted wording; no seventh requirement field appears. |
| NDS12-AC-003 | NDS-UX-002 | Author and HoD enter their work directly under one workspace; names lead references, reviewer tasks lead the register, and no role switch or blanket Planning usage column is required. |
| NDS12-AC-004 | NDS-UX-002 | Submitted, returned, accepted-with-update and terminal states show the correct next actor/action without replacing the accepted lifecycle; optional row annual-plan status requires confirmed evidence. |
| NDS12-AC-005 | NDS-UX-003 | A single eligible department is read-only; multiple eligible departments use the required unselected same-form selector with the same six fields and no Continue modal. |
| NDS12-AC-006 | NDS-UX-003 | Zero eligible targets creates nothing; filters do not grant or select create authority; first save fixes department and FY and subsequent requests cannot transfer ownership. |
| NDS12-AC-007 | NDS-UX-004 | From a complete unsaved form one Submit for review action saves once then submits the returned exact revision; edited saved drafts save first, unchanged drafts submit directly, and success creates one root, submitted snapshot, task and event set. |
| NDS12-AC-008 | NDS-UX-004 | Exercise save failure, save success/submit rejection including intake closing, unknown save and unknown submit outcomes, double click and retry. Preserve the confirmed Draft, resolve original command identities and never duplicate or falsely claim submission. |
| NDS12-AC-009 | NDS-UX-005 | Initial review shows six facts and the acceptance consequence beside one Accept for planning action; no extra Accept modal, reason, score, checkbox or mandatory disclosure checklist. |
| NDS12-AC-010 | NDS-UX-005 | Acceptance still enforces current task token, reviewer scope, maker-checker and atomic snapshot/task/outbox rules; a stale or unauthorised click cannot decide the task. |
| NDS12-AC-011 | NDS-UX-006 | Update review shows changed facts first and all six proposed facts on the page, labels Accept proposed changes and Decline proposed changes distinctly, and explains which requirement remains effective. |
| NDS12-AC-012 | NDS-UX-006 | Accepting an update changes the current accepted pointer with lineage; returning creates a copied correction; declining records its reason and preserves the earlier accepted requirement and downstream history. |
| NDS12-AC-013 | NDS-UX-007 | All §11.8A variants keep Departmental plan and Current annual plan separate, including excluded-but-still-included and newer-accepted/older-Active combinations, with readable exact supporting evidence. The no-Active exclusion uses its distinct 4 Jan 2027, 14:00 EAT Submission 2 event; neither the canonical 27 Nov Proceeding event nor the separate 5 Jan still-Active event is reused as its evidence. Match §14.6A profile identities as well as displayed dates. |
| NDS12-AC-014 | NDS-UX-007 | Confirmed empty, pending, failed and historical results remain distinct; authorised links open exact owner records and refresh never changes source state, creates a task or proves fulfilment/withdrawal clearance. |
| NDS12-AC-015 | NDS-UX-008 | Withdrawal review states the blocker, responsible function and permitted next action. Clear, blocked and unavailable owner results expose the correct controls; a permitted decline remains available without falsely clearing usage. |
| NDS12-AC-016 | NDS-UX-008 | Approve withdrawal retains the focused confirmation and authoritative all-revision serialized owner check at commit. Earlier Active inclusion, a race with activation or unknown evidence prevents approval despite a local Not included card. |
| NDS12-AC-017 | NDS-UX-009 | Errors use plain field/action text and recovery, with distinct known save failure, saved-but-not-submitted and unknown outcome states. Intake closure retains existing editable drafts but blocks initial submit/resubmit. |
| NDS12-AC-018 | NDS-UX-009 | Still-authorised input survives recoverable failure; stale results cannot overwrite newer records. Access revocation removes protected data. Error focus/announcements and safe retry work without raw service internals. |
| NDS12-AC-019 | NDS-UX-010 | Author, HoD, Planner source reader, Auditor and Administrator/System Manager technical reader receive the scoped shared detail/action combinations in §6.1; no new AO, Finance or supplier Need role/workspace is introduced. |
| NDS12-AC-020 | NDS-UX-010 | Complete facts, reasons, differences and history are readable with structured supporting detail, keyboard access, text status, adequate contrast and narrow-screen wrapping; no forced download. Record representative-user findings before claiming tested usability. |

### 15.3 Explicit design-contract acceptance coverage

| ID | Required result |
|---|---|
| NDS13-AC-001 | Each §11 artboard defines its purpose, external fixture, header, ordered regions, exact controls, supporting detail and visual check under KT-STD §§2.6–2.8. |
| NDS13-AC-002 | Design generation uses only KT-STD v1.6 §2 plus NDS §11; runtime action mapping remains in §12.10 and no permission/API/lifecycle algorithm is drawn. |
| NDS13-AC-003 | Primary Author workspace has exact action/filter placement, complete title/reference rows, no annual-plan marker and no unresolved optional content; its named variants provide distinct alternate layouts. |
| NDS13-AC-004 | Canonical Grace retains both Author assignments and sees the inline selector; single-target screen uses an explicitly isolated reduced-assignment fixture; no new creation step or authority. |
| NDS13-AC-005 | Initial, returned, submitted, accepted, update and withdrawal screens retain all six complete source facts, exact historical reasons and distinct decision consequences. |
| NDS13-AC-006 | Every Planning variant fixes both displayed results, source evidence and link/action treatment; preserve the canonical 27 Nov event and distinct 4 Jan and 5 Jan exclusion profiles. |
| NDS13-AC-007 | Every interactive control maps through §12.10 to its existing read/command/navigation result, including Cancel, Close, filters, disclosures, owner links and retries. |
| NDS13-AC-008 | Loading/empty/denied/error/closed/partial/unknown states are discrete artboards with definite controls; no failed result is represented as a successful empty list or guessed source absence. |
| NDS13-AC-009 | Technical variants conform to KT-STD v1.6 §3A.6 and shared conformance/search registration; ordinary masking and business assignment clauses cannot restrict technical read. |
| NDS13-AC-010 | All actor/state artboards are compared against the explicit compositions and tested for readable hierarchy, keyboard/focus and narrow layouts; document completion does not imply user acceptance. |

## 16. Implementation and test constraints

### 16.1 Frappe and UI implementation

- Implement domain records as explicit Frappe DocTypes with server-side controllers/services; do not store business state in client-only objects.
- Mount Vue 3 pages through the existing `frappe.ui.make_app_page()` → built bundle → `createApp().mount()` pattern already proven by the Strategy pilot.
- Port Claude Design markup and design tokens into scoped Vue single-file components. Design export runtime files remain design evidence under `docs/` and are not imported into production.
- Reuse the existing KenTender page header, context strip, fields, buttons, badges, tables, dialogs, states and token chain before creating a module-local component.
- Keep component styles scoped beneath one Departmental Needs root. Do not add Tailwind Preflight, a CDN, global element resets or rules that restyle Frappe Desk.
- Use Frappe RPC/resource APIs for authorised services. Do not expose writable DocType endpoints that bypass commands.
- Register only the canonical routes in section 10. Page controllers unmount Vue and detach listeners before remount.
- Add stable accessible test selectors to page-ready state, field controls, tables, dialogs and primary commands. Do not select by visual CSS classes.

### 16.2 Verification and release evidence

The verification protocol is KT-STD-001 §5; release evidence is KT-STD-001 §6.

Additional evidence for this document:

- repository scan proving `NeedsIntakeWindow`, `PEFiscalYearContext`, every Frappe User Permission read and every Fiscal Year user grant are absent from Departmental Needs code, seeds and fixtures;
- a Cartesian-product regression proving one user's Author and acting-HoD assignments do not cross Organisation Units; and
- a browser journey proving a departmental user creates a Need from one ordinary assignment with no pre-entry context step.

### 16.3 Required AUTH-ADR-001 v1.7 correction slice

Implement this correction as one controlled slice. Do not combine it with unrelated Planning or Tender work.

1. Replace every Departmental Needs use of Frappe User Permission, User Scope Assignment or module-local scope logic with the shared AUTH-ADR-001 v1.7 resolver and role-bound assignment ID.
2. Remove `Financial Year` and PE from `required_dimensions()`, remove every FY/PE grant check and remove any `allowed_years` identity gate. Retain record, OU, flag, state and maker-checker controls.
3. Make `selectable_financial_years()` return ERPNext Fiscal Years represented by existing authorised records. This function supplies filters only.
4. Implement `list_need_create_targets()` separately. It combines active Departmental Author OU assignments with the one ERPNext Fiscal Year whose Needs-submission flag is Open.
5. Replace all list, count, detail, task, file, export and command scope checks in the same controlled cutover; no fallback to an older store is permitted.
6. Stop seeds and profiles from creating Frappe User Permission, User Scope Assignment or Financial Year access as Departmental Needs authority; create exact User Responsibility Assignments instead.
7. After production code and seeds no longer read the old stores, clean obsolete rows under the AUTH migration plan. Never run cleanup first.
8. Add a Cartesian-product regression: Grace may be Author in OU-DHI while acting HoD in OU-HRMD and must not exercise either responsibility in the other OU.
9. Verify Grace can browse FY 2026/27 and FY 2027/28 without an annual permission edit, can create only while the applicable Fiscal Year flag is Open, and is never trapped by a remembered year.
10. Verify a parent-OU HoD assignment covers its two named descendants but never a sibling outside that subtree.
11. Remove `NeedsIntakeWindow`, its routes, commands, seeds and tests. Remove all PE/FY Context reads.
12. Verify closing the flag blocks initial creation and submission while leaving existing Draft and Returned revisions editable and saveable, and that opening another Fiscal Year leaves at most one open flag after one atomic command.
13. Verify that reaching `kentender_needs_submission_closes_at` has the same effect as a manual close, and that a create or submit command issued after the flag closed but before page reload is rejected server-side.

## 17. Prohibited shortcuts

The universal list is KT-STD-001 §2.3 and §10. Additionally, for this document:

- Do not preserve the item child table as a hidden or single-row implementation.
- Do not store a Procurement Budget Line, indicative amount, funding source, currency, delivery location, attachment, `other_unit`, Strategy, classification, generic note, source reference or evidence "for later".
- Do not calculate or display budget availability inside Departmental Needs.
- Do not create a reservation, Plan Item, Requisition or Tender from a Need command.
- Do not require a synthetic Need, Need acceptance or bypass reason before Planning may capture a direct departmental requirement.
- Do not implement the direct-requirement editor inside Departmental Needs; it belongs to the DPP workspace in Procurement Planning.
- Do not edit an accepted or submitted snapshot in place.
- Do not let Planning query Departmental Needs tables or mutate a Need.
- Do not infer role authority from a UI tab, route, Frappe role label, ownership alone or Administrator status.
- Do not implement a Planner, Budget Officer, Accounting Officer or support dashboard in this module.
- Do not introduce `Partially included`, quantity override or a Plan allocation child table.
- Do not create `NeedsIntakeWindow`, `PEFiscalYearContext`, an `opens_at` field, a scheduled intake state or a repeated PE key.
- Do not write `kentender_needs_submission_open` or `kentender_needs_submission_closes_at` from Departmental Needs, and do not render an intake editor.
- Do not make an existing Draft or Returned revision read-only because intake closed.
- Do not add a separate menu item for a work queue. HoD decision work belongs inside the ordinary Departmental Needs workspace.
- Do not add legacy Demand fields or fixtures.

## 18. Traceability, full changes and remaining dependencies

### 18.1 Governing inputs and precedence

| Source | Controlling use / limitation |
|---|---|
| Approved NDS v1.11, 12 September 2026 | Complete domain, contracts, authority, seed, 85 acceptance criteria, 28 change rows and 12 outstanding owner dependencies carried forward and reconciled here. |
| Approved NDS Usability Amendment v0.1, 13 September 2026 | Ten NDS-UX decisions govern the readability and task changes in §§4.10, 6.1, 8.4–8.5, 9–12 and 15.2. Approval does not imply deployed code or participant-tested UX. |
| Proposed Planning v1.19 | Coordinated readable owner presentation; its proposed status remains unchanged. This NDS successor neither approves nor rewrites the Planning owner document. |
| Supplied NDS v1.10, header Proposed | Retained six-field consultation channel, revision/withdrawal governance, seven routes, static fixtures and 61 prior acceptance criteria. No unrecorded approval of v1.10 is inferred. |
| PLN v1.18 §§4, 5.1, 5.4, 7–8, 15, 17 | Accepted DPP disposition, fixed source cohort, optional direct requirements, exact source/full quantity, independent Active usage and procurement scope lock. |
| PLN-CHG-001_FOLLOW_UPS.md FU-24/FU-30 | New NDS disposition contract/display and cross-module precision work, interpreted without reintroducing Need monetary fields. |
| Approved CFG v0.10 | Effective intake close, native UOM/precision adapter and current owner decision validation; separate Needs/DPP controls. |
| Approved BUD v1.8 | Exact Money boundary outside NDS, source-OU line eligibility through Planning, REQ-stage reservation. The Need-origin selection wording receives the §7.3 ownership clarification. |
| Approved SEED v1.3 | Shared actor chronology, three accepted sources, BASE/conditional Active distinction, quantities/dates. Approved NDS v1.11 resolves the infrastructure acceptance actor/instant retained in §14.3; executable shared-seed adoption still requires evidence. |
| AUTH v1.7 / approved KT-STD v1.6 | AUTH-owned business assignments/maker-checker; current standard controls technical read and explicit design composition. Matching shared technical-search/conformance owner specification remains a named dependency. |
| Approved LAW v1.1 | Legal correction/verification status and positive downstream claim limits. This document creates no new legal conclusion or verification. |

Ownership controls the value/decision. NDS governs source lifecycle; PLN governs disposition/usage and its own immutable approvals; CFG governs setup; BUD governs financial positions. An event delivery or UI label never transfers that authority. No current code/test behavior is asserted from a requirements file alone.

### 18.2 Full change register for re-implementation

All 28 NDS11-CHG rows remain traceable to the approved v1.11 baseline; their historical counts and screen wording describe that baseline. The first ten NDS12-CHG rows below reconcile the operative usability contract; NDS12-CHG-011 records the 15 September 2026 editorial fixture correction. Implement this successor’s current sections and criteria wherever prior wording conflicts. NDS13-CHG-001–005 add the explicit design-contract corrections. Total: **44 change rows**.

| ID | Prior issue / gap | Complete required change | Locations | Verification |
|---|---|---|---|---|
| NDS11-CHG-001 | Single Planning projection could not express accepted exclusion | Add NeedPlanningDispositionProjection/event and retain independent Active usage and Need lifecycle. | §§3, 4.7–4.8, 7.4 | NDS11-AC-062–064 |
| NDS11-CHG-002 | Accepted-disposition producer timing unclear | Emit per covered Need at complete DPP acceptance, not Draft change or HoD certification; include Proceeding for later restoration. | §§7.2, 7.4 | NDS11-AC-062, 065–066 |
| NDS11-CHG-003 | No exact new event schema | Specify stable/exact IDs, accepted Submission, enums/reason, actor/time, schema/event identity and sequence. | §7.4 | NDS11-AC-063 |
| NDS11-CHG-004 | Planning reason could become generic Need data | Store exact certified reason only in read-only disposition evidence; never source facts, Need review reason or generic notes. | §§2.2, 4.8, 7.3–7.4 | NDS11-AC-007, 024, 064, 070 |
| NDS11-CHG-005 | Proceeding restoration could erase earlier exclusion | Later accepted Submission sets Proceeding/reason null while preserving older accepted reason/provenance. | §§4.8, 7.4–7.5 | NDS11-AC-065 |
| NDS11-CHG-006 | UUID presented as sufficient ordering | Separate per-Need usage/disposition sequence domains with payload-aware deduplication, gaps, replay and source reconciliation. | §§4.7–4.8, 7.5 | NDS11-AC-067–068 |
| NDS11-CHG-007 | Old revision event could be attributed to current revision | Keep revision-specific projections/history; historical routes stay pinned; show older Active inclusion separately. | §§4.7–4.8, 7.5, 12.4, 12.9 | NDS11-AC-069, 073 |
| NDS11-CHG-008 | Missing/failed projection looked like Not included | Explicit no accepted decision, refreshing, last-confirmed and unavailable states; no lifecycle default or cached withdrawal clearance. | §§4.7–4.8, 7.5, 11.8A, 12.9 | NDS11-AC-015, 071 |
| NDS11-CHG-009 | No complete Planning information composition | Add exact card and seven variants to existing detail, separate reasoned disposition from usage and limit links to owner-authorized targets. | §§11.8–11.8A, 12.9 | NDS11-AC-070–072 |
| NDS11-CHG-010 | Exclusion might imply Need declined/withdrawn/fulfilled | Keep Accepted for planning; display Not proceeding this financial year as accepted DPP information only; no fulfilment or Tender-coverage claim. | §§7.2, 7.4, 11.8A | NDS11-AC-064, 072 |
| NDS11-CHG-011 | Stable Need withdrawal checked only pinned/current revision | Check authoritative Active inclusion across all accepted revisions; older revision still blocks after successor acceptance. | §§4.7, 5.3, 8.1–8.3, 12.6 | NDS11-AC-019–020, 073 |
| NDS11-CHG-012 | Live dependency read left activation/withdrawal race | Require owner-held decision serialization through NDS commit; matching Planning provider/caller mapping and concurrency tests. | §§5.3, 8.3 | NDS11-AC-074 |
| NDS11-CHG-013 | Open successor and withdrawal could orphan work | Mutually exclude open accepted-source changes under the stable lock; stale pinned withdrawal cannot silently target a replacement revision. | §§5.2–5.3, 9, 12.4 | NDS11-AC-028, 076 |
| NDS11-CHG-014 | Blocked withdrawal hid a permitted decline action | Show Decline withdrawal and exact reason dialog with maker-checker; approval remains blocked until authoritative clearance. | §§5.3, 11.13–11.14, 12.6 | NDS11-AC-075 |
| NDS11-CHG-015 | Closed intake simultaneously made Drafts editable/read-only | Remove read-only contradictions from workspace, states and interaction rules; preserve save/correction while initial submit/resubmit stays blocked. | §§5 BR-003, 11.15, 12.1, 12.7 | NDS11-AC-054, 080 |
| NDS11-CHG-016 | Close instant depended on scheduler cleanup | Use CFG effective-open including disabled FY and exact instant; no backdated cleanup, no raw-Boolean gate. | §§4.1, 5 BR-002, 12.7 | NDS11-AC-003, 055–056, 080 |
| NDS11-CHG-017 | Native enabled UOM column assumed | Use CFG native owner adapter’s selectable/precision facts and preserve historical basis; no parallel catalogue or guessed field. | §§4.9, 8.3, 14.1 | NDS11-AC-006, 057, 081 |
| NDS11-CHG-018 | Quantity fixed at three decimals / float boundary | Exact decimal string and governed UOM scale/whole-number constraint, 18-integral-digit capacity, no rounding/epsilon/overflow. | §§4.3, 4.9 | NDS11-AC-005, 077 |
| NDS11-CHG-019 | Rename continuity could hide real wire-type changes | Keep -Vnnn IDs and accepted.v2 identity keys; inspect numeric wire/hash mapping and coordinate any breaking precision cutover explicitly. | §§4.9, 7.1, 7.5, 18.3 | NDS11-AC-078 |
| NDS11-CHG-020 | Funding reserved in Planning per ownership table | Correct reservation owner to Budget called at REQ authorisation; CFG owns catalogue and Planning owns DPP selection/estimate; Need stores no Money. | §§3, 4.9, 7.3 | NDS11-AC-007–008, 079 |
| NDS11-CHG-021 | Every accepted Need could rewrite an in-review DPP | Apply PLN v1.18 source-cohort rules, reasoned exclusions and accepted-update route; new unrelated source does not silently enter returned certified coverage. | §7.2 | NDS11-AC-014, 031, 066 |
| NDS11-CHG-022 | Need acceptance could imply inclusion in locked procurement scope | Normal acceptance/update remains allowed, but later new scope needs separate eligible Plan Item; NDS cannot unlock or enlarge a procured item. | §7.2 | NDS11-AC-013, 020, 072 |
| NDS11-CHG-023 | Peter granted November DHI authority in seed | Explicit separate HRMD and DHI-from 1-Dec assignments; Julia accepts infrastructure at existing24-Nov14:00 instant and DHI laptops25-Nov09:30. | §§11.8, 14.2–14.3 | NDS11-AC-082 |
| NDS11-CHG-024 | Seed/artboard mixed November drafts and later Active usage | Separate 24-Nov design,25-Nov accepted BASE,27-Nov accepted dispositions and conditional Active profiles; preserve 100/150 and 31-Dec source dates. | §§11.2–11.8A, 14.3–14.6A | NDS11-AC-025, 083 |
| NDS11-CHG-025 | No disposition/replay/dependency edge-case fixtures | Add ten isolated owner-contract scenarios for no decision, exclusions, restoration, older revision, order, precision, close and races. | §14.6A | NDS11-AC-062–083 |
| NDS11-CHG-026 | Forbidden shell/scope copy contradicted role model | Authorization-first inline Forbidden; no PE control or OU requirement on site-wide Planner; preserve technical-read and exact accepted-source routes. | §§6, 11.15, 12.4, 12.9 | NDS11-AC-058–061, 084 |
| NDS11-CHG-027 | Create context claimed three rows after PE removal | Correct two-row context description; retain exactly six user source values and existing routes. | §11.4 | NDS11-AC-001, 025 |
| NDS11-CHG-028 | No consolidated reimplementation table / acceptance carry-forward | Map all 61 prior criteria and add 24; full 28-row changes, owner dependencies and approval effect in one successor. | §§15, 18.2–18.3, 20 | NDS11-AC-085 |
| NDS12-CHG-001 | NDS-UX-001: Arcane field labels | Apply Requirement title, Description, Expected result, Quantity, Unit and Required by consistently; preserve all source keys, limits and six-field scope. | §§4.10, 9, 11.4–11.10, 12.3 | NDS12-AC-001–002 |
| NDS12-CHG-002 | NDS-UX-002: Workspace foregrounded internal states | Lead with names, actor tasks and useful statuses; one Author/HoD workspace; remove blanket usage column and show optional accepted-row evidence only. | §§6.1, 10, 11.2–11.3, 12.1–12.2 | NDS12-AC-003–004 |
| NDS12-CHG-003 | NDS-UX-003: Separate department-choice step | Put the authorised required Department selector in the new form; derive FY, prefill one target, lock ownership after save, preserve seven routes. | §§8.4, 11.4, 11.16, 12.1–12.3 | NDS12-AC-005–006 |
| NDS12-CHG-004 | NDS-UX-004: Correction and submission required needless steps | Directly open copied correction with the reason. One Submit intention orchestrates distinct save/submit commands, retains partial success and resolves unknown outcomes using original identities. No new approval or submission record. | §§8.4, 9, 11.4–11.5, 12.3 | NDS12-AC-007–008 |
| NDS12-CHG-005 | NDS-UX-005: Repeated acceptance confirmation | Place consequence beside one explicit initial Accept for planning action; preserve reviewer authority, transaction and source acceptance semantics. Remove only repeated Accept confirmation. | §§8.5, 11.7, 11.14, 12.5 | NDS12-AC-009–010 |
| NDS12-CHG-006 | NDS-UX-006: Update decisions confused with rejecting the Need | Show differences first plus full facts. Use Accept proposed changes and Decline proposed changes; state retained acceptance and preserve Return-copy, lineage and exact reasons. | §§5.2, 8.5, 11.9–11.10, 11.14, 12.5 | NDS12-AC-011–012 |
| NDS12-CHG-007 | NDS-UX-007: Planning evidence was difficult to interpret | Present Departmental plan and Current annual plan independently, with structured exact supporting evidence, all mixed/unknown/older-revision cases and authorised owner navigation. Never infer fulfilment. | §§8.5, 11.8–11.8A, 12.9 | NDS12-AC-013–014 |
| NDS12-CHG-008 | NDS-UX-008: Withdrawal blockers lacked a clear next action | State why withdrawal cannot proceed and Procurement’s existing responsibility; keep allowed decline, focused approval confirmation and all-revision current owner validation. No new clearance workflow. | §§9, 11.12–11.14, 12.6 | NDS12-AC-015–016 |
| NDS12-CHG-009 | NDS-UX-009: Technical errors and retry states confused users | Map all stable errors to plain explanation/recovery; distinguish failure, partial success and unknown result; preserve authorised edits, server closure rules, access protection and safe retry. | §§8.4, 9, 11.15, 12.3, 12.7–12.8 | NDS12-AC-017–018 |
| NDS12-CHG-010 | NDS-UX-010: Actor coverage and supporting detail lacked shared usability rules | Define all five actor group journeys with shared readable facts, changes, reasons and history. Structure supporting detail, retain full evidence and enforce keyboard/contrast/narrow-screen checks. No new business roles. | §§6.1, 11.1–11.17, 12.8–12.9, 15.2 | NDS12-AC-019–020 |
| NDS12-CHG-011 | Editorial fixture defect: §11.8A and §14.6A reused canonical DHI Submission 1 acceptance for an opposite disposition on infrastructure 0001 Revision 1 | Use distinct DHI Submission 2 accepted by Mercy Kilonzo on 4 Jan 2027, 14:00 EAT in the BASE-derived no-activation profile; require separate owner submission/event identities. Preserve canonical 27 Nov Proceeding, conditional activation and 5 Jan still-Active fixtures. Strengthen the existing variant criterion; no domain/lifecycle change. | §§11.8A, 14.4, 14.6A, 15.2 | NDS12-AC-013; NDS11-AC-083 |

| NDS13-CHG-001 | Dense, cryptic screen inventory replaced spatial instructions | Adopt KT-STD v1.6; rewrite all active NDS-DES compositions with ordered regions, labels, controls and visible hierarchy. | §11 in full; §18.1 | NDS13-AC-001–002 |
| NDS13-CHG-002 | Primary fixtures left action visibility and optional layout unresolved | Define exact Author/HoD layout and discrete status, failure, pending and content variants; keep all six source facts and exact record evidence. | §§11.2–11.17 | NDS13-AC-003, 005–006, 008 |
| NDS13-CHG-003 | Grace single-target wording conflicted with her two supplied Author assignments | Show canonical inline Department selector; reserve single-target read-only context for a named isolated profile. Complete isolated successor acceptance/terminal display facts without changing canonical events. | §§11.4, 11.8A, 11.16–11.17, 14.5 | NDS13-AC-004–006 |
| NDS13-CHG-004 | Control purposes scattered or implicit | Add complete action-to-result/contract map outside design input; preserve current commands, guarded multi-command submission and all owner boundaries. | §12.10 | NDS13-AC-007 |
| NDS13-CHG-005 | Older technical-read wording and vague reader compositions | Cite current standard §3A.6; remove conflicting assignment exception; specify reader/technical variants and require common owner registration evidence. | §§6, 11.17, 15.3, 18.3 | NDS13-AC-009–010 |

### 18.3 Owner dependencies and release evidence

| ID | Outstanding item / owner | Required result and claim limit |
|---|---|---|
| NDS11-XD-001 | FU-24 — PLN producer/NDS consumer | Implement the exact disposition schema and acceptance-time events for both outcomes; map actual DPP IDs, service/transport APIs and acceptance evidence. Projection/table/UI tests must pass before implementation closure. |
| NDS11-XD-002 | Usage ordering and owner replay — PLN/NDS | Inspect existing usage wire/transport; preserve its business semantics. Supply monotonic independent stream metadata and authoritative replay/snapshot; approve an explicit wire version change if required. Do not silently add dispositions to usage.v1. |
| NDS11-XD-003 | Stable-Need withdrawal transaction — PLN/NDS | Implement or map the §8.3 owner validator with activation serialization, all-revision dependency and current-source checks. Race/rollback tests are a release gate; a local projection/HTTP read is insufficient. |
| NDS11-XD-004 | FU-30 — NDS/PLN/REQ/BUD | Remove float/epsilon source-quantity paths; prove native UOM precision and exact source handoff. BUD/PLN/REQ prove Money separately. Inspect accepted.v2 actual JSON type/hash; coordinate incompatible changes and reconcile historical values without invented precision. |
| NDS11-XD-005 | Shared seed — NDS/SEED/KT-STD | Adopt Julia’s 24-Nov14:00 infrastructure acceptance and Peter’s DHI-from 1-Dec authority, separate dated snapshots, actual accepted DPP IDs, disposition streams and conditional Active profiles. This resolves the infrastructure fact in this approved owner document; executable cross-module evidence remains outstanding. |
| NDS11-XD-006 | Narrow BUD v1.8 ownership editorial | Its table still describes an “Accepted Need and selected Budget Line.” Clarify that selection belongs to the Need-origin DPP entry; do not add a Need field. The approved BUD file is not silently rewritten in this NDS review. |
| NDS11-XD-007 | CFG native metadata and intake integration | Verify actual UOM selectable/whole-number/precision fields, effective-open transaction control and cleanup audit. NDS does not own an intake editor or hard-code native fields. |
| NDS11-XD-008 | Data reconciliation — NDS owner | Inspect existing accepted hashes/quantities, stale projection IDs, gaps and simultaneous open successor/withdrawal records. Preserve submitted/accepted history; repair through controlled reconciliation, not blanket deletes/re-hashes. |
| NDS11-XD-009 | UI/artboard implementation — NDS UI owner | Implement the revised §§11–12 across all actor journeys, including §11.8A and all ten approved usability changes; verify reason readability, keyboard/retry behavior, authorized links and distinct statuses with representative users. This review establishes the specification, not completed artboards or tested UX. |
| NDS11-XD-010 | CFG/LAW/SEED positive downstream prerequisites | CFG-XD-001 FY/applicability and LAW v1.1 verification items remain. A passing NDS consultation/event test does not certify the entire procurement chain or current law. |
| NDS11-XD-011 | FU-25 REQ/TPR sibling review | REQ v1.8 has been produced as a proposed sibling successor, not approved through this NDS document; TPR and any remaining owner changes still require their own controlled review, including drawdown naming, scope/hold errors, correction outcomes and requester follow-up. This NDS edit supplies source/disposition boundaries but does not update those owners’ specifications. |
| NDS11-XD-012 | FU-27 common-standard citation cleanup | Consolidate technical-read citations with the actual later controlling standard when supplied; preserve existing AUTH technical read without inventing a new role or extra approval. |
| NDS12-XD-001 | UI/service orchestration — NDS implementation owner | Map §8.4 to actual save/submit RPC responses, command idempotency records and authorised outcome lookup/replay. Prove partial and unknown outcomes, no duplicate root/task, stale-write protection and effective close at each applicable command. No assumed atomic save-plus-submit or invented existing API. |
| NDS12-XD-002 | Usability validation — NDS product/UI owner | Conduct representative Author/HoD tasks and scoped reader checks against §15.2; retain observed completion, misunderstanding and recovery findings. Verify full evidence readability and all-actor access before claiming the redesign is usable in practice. |
| NDS13-XD-015 | Shared technical search/conformance — AUTH and kentender_core | KT-STD v1.6 retains §3A.6 and its AUTH-DES-09 / AUTH §9 conformance references; those details are absent from the supplied AUTH v1.7. Obtain the matching owner specification and implementation evidence; register NDS record types/read entries. Do not defer the mandated read right or build a duplicate module search. |

Future fulfilment derivation, tender amendment for scope expansion, accounting integration and new consultation attachment/classification workflows remain outside this module unless separately approved. No “Planning information” badge substitutes for those facilities.

## 19. E2E-REQ-001 conformance

| Non-drift control | Conformance |
|---|---|
| Structured data is authoritative | The Need is structured and contains no attachment substitute. |
| Fixed product forms | The Need has exactly six user-owned values. |
| No generic configuration engine | No schema, mapping, manifest or STD control exists. |
| Enter department data once | Accepted values pass to Planning with the same Need and revision IDs. |
| Procurement cannot silently rewrite | Planning receives accepted values read-only. |
| Downstream obligations are linked | The Need creates the first stable source ID; detailed obligations are added later at Requisition. |
| Minimum role-bound responsibilities | Four registered responsibilities cover the module; only Author and HoD make Need lifecycle decisions. Site-wide/OU responsibility assignments are durable and Fiscal Year is derived from the record/open flag. |
| No premature abstraction | No generic requirement model is introduced. |

## 20. Approval effect

NDS v1.13 consolidates the approved v1.12 requirements and its 15 September 2026 exclusion-fixture correction with the Project Owner's instruction to persist and apply the clearer screen-composition standard. It supersedes v1.12 and earlier implementation specifications in full. KT-STD-001 v1.6 is the current shared standard.

This revision replaces the entire static design section with explicit layouts and named state variants and adds the corresponding functional action map. It preserves the six-field optional consultation channel, source/disposition/Active-usage boundaries, accepted-update and withdrawal governance, existing service/event contracts and the canonical fixture chronology. It introduces no new business field, approval stage, role, module or prototype stack.

The full contract contains **115 acceptance criteria** (105 retained plus ten design-contract criteria), **44 change-register rows** (39 retained plus five design-contract changes), and **15 named owner/verification dependencies**. The companion usability amendment remains historical approved direction; the current full document supplies the operative detailed screen contract. No separate set of competing screen instructions is required.

Approval of this consolidated specification does not demonstrate rendered artboards, usability testing, shared-owner integration, source verification or production release. Complete those checks under the current standard and this document's acceptance/dependency tables. The corrected 4 January exclusion, 5 January still-Active fixture and 27 November canonical event remain separate evidence.
