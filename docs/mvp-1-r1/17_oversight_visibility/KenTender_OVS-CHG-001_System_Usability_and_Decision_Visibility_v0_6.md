# OVS-CHG-001 — System Usability and Decision Visibility

**Controlling approval — 3 October 2026.** The Project Owner instructed: “Mark the documents as approved”. This approves this version in the coordinated OVS v0.6 package, including its incorporated amendments. OVS-P01–P05 are approved. The incorporated REQ v1.13, CFG v0.17 and TPR v0.16 changes are accepted within their approved successors; this does not create separate retrospective approvals of those intermediate versions. Earlier proposed/pending wording is drafting history superseded by this record. Static design work and conformance matrices remain open; CM and the separate template walkthrough remain deferred. Approval does not establish implementation, seed execution, testing, legal clearance or production readiness.

| Control | Value |
|---|---|
| Document ID | OVS-CHG-001 |
| Version | 0.6 |
| Date | 3 October 2026 |
| Status | Approved — 3 October 2026 |
| Supersedes | OVS-CHG-001 v0.5, proposed |
| Approved on | 3 October 2026 |
| Approval record | Project Owner: “Mark the documents as approved” — 3 October 2026 |
| Design readiness | Requirements only; not a closed-input design prompt. D1–D7 remain tracked in §14.1. |
| Approval | Approved by the Project Owner on 3 October 2026 |
| Scope | All MVP 1 modules, internal decision makers and operational users, with supplier access within its existing boundary |
| Related-document status | The 3 October files.zip upload is the source for the supplied owners. The second upload supplies CTX v1.0, TRUST v0.1, SEED v1.3 and older STD-TPL v0.13. STD-TPL v0.15 has now been supplied and its approval confirmed. Current CM sources and the separate template walkthrough change remain outstanding. The accompanying impact schedule identifies versions, predecessors and gaps; no approval is inferred from upload. |
| Change boundary | This document replaces the narrow downstream oversight proposal. It specifies a complete usability change without inventing procurement approvals or changing statutory decision powers. |

## 1. Purpose and governing direction

KenTender must help people do their daily work and understand the decisions already made. Information must remain findable and useful after submission, approval, return, hand-off, completion or cancellation. Moving a task to another person or module must not make the underlying record disappear.

An authorised user must be able to answer:

1. What is the current position?
2. What was decided, by whom, when and why?
3. What evidence and earlier decisions support it?
4. What remains outstanding, who is responsible and what can I do?
5. How do I find this record again?

The Project Owner's recorded Evaluation decisions remain: oversight readers see status only before report delivery and all details after delivery. Meetings are attributed to the Tender's owning department. This revision proposes the explicit administrative facts, role scope and navigation needed to apply those decisions usefully.

The change applies the same usability principles throughout MVP 1. Each module retains its own disclosure boundary and authority. Evaluation's delivery boundary is not a universal rule for other stages.

## 2. Scope and limits

Included: role-appropriate workspaces; actionable work lists; searchable registers; persistent record views; readable decisions and evidence; connected navigation; progress and outstanding obligations; history and version selection; useful empty/error states; accessible interactions; and the Procurement meetings register.

Coverage includes Configuration, Strategy, Budget and Funding, Departmental Needs, Procurement Planning, Requisitions, Tenders, Supplier/Bid Submission, Opening, Evaluation, Award, Proceedings and all three Contract Management stages. Existing stores, assets and accounting functions appear through their authoritative records and authorised links. Future modules inherit the standard when specified; this request does not create them.

Excluded: new procurement approval layers, duplicate tasks, a second ledger, new supplier qualification or performance-scoring schemes, generic meeting administration, unrestricted bid disclosure, a new enterprise reporting warehouse, and assumed access to eGP or IFMIS. Automated decisions and calculations remain governed by their owner requirements. This is a usability change, not authority to alter legal or commercial rules.

## 3. Canonical ownership

Business records, decisions, tasks, permissions and state transitions remain owned by their modules. Shared views compose published owner reads and never calculate competing outcomes. Displayed values link to the authoritative record and version.

No duplicate business store is required by this change. Search indexes or read caches, if needed, are rebuildable and permission-aware; they are not evidence or accounting authority. Every stored extension must have a demonstrated gap and named consumer. Where immutable evidence associations are missing, specify the smallest owner-owned addition rather than substituting current working data for historical evidence.

AUTH v1.10 and KT-STD v1.14 have been checked in the uploaded bundle. Their registered permission model, next_step, Home and My Work remain authoritative. CTX v1.0 was supplied in the second ZIP; its obsolete PE/permission model is replaced in the proposed CTX v1.1, preserving context as a non-authoritative local filter. Reuse existing services where adequate; the names in this request describe proposed contracts, not confirmed installed APIs.

## 4. Role and disclosure contract

Access derives from current assigned responsibility and scope, not a technical role label alone. Existing independently authorised access remains intact. The table specifies proposed usability coverage, not new authority to decide or approve.

| Reader | Required working visibility | Boundary |
|---|---|---|
| Accounting Officer | Site-wide progress, authorised decisions, reasons, evidence and outstanding responsibilities | Stage-specific disclosure; no unfinished Evaluation findings through oversight access |
| Head of Procurement Function | Procurement oversight and existing operational actions, including delivered Evaluation records after Award takes over | Same disclosure discipline; existing secretary or other appointment access is evaluated separately |
| Head of User Department | Department-scoped needs, funding/planning context already authorised, requisitions, procurement progress, disclosed outcomes, delivery and contract obligations relevant to that department | Match authoritative owning/contributing department links; do not disclose unrelated departments' records or unreleased bid content |
| Procurement and operational staff | Records within their current duties, completed work they remain entitled to read, and actions they currently own | Appointment, assignment and organisational scope remain controlling |
| Committee members and secretary | Their existing appointed working views, records and actions | This oversight change must not replace their working access with an oversight-only view |
| Finance, receiving, inspection and contract personnel | Relevant commitments, accepted/rejected deliveries, invoices, payment position, obligations and supporting records | Existing functional responsibilities; financial approval is not proof of payment |
| Auditor | Readable evidence and history within authorised audit scope | No new decision or amendment powers |
| Supplier | Own submissions, notices, clarifications, contracts, deliveries and invoice/payment information already permitted by the owner | No competitor content or internal deliberations; no newly inferred entitlement |
| Administrator/technical support | Existing technical access only | Preserve KT-STD v1.14 §3A.6 technical read and owner sealed-custody restrictions; conflicting procurement clauses are recorded in the impact schedule for explicit resolution |

Departmental visibility is part of this change, not a future usability patch. After disclosure, a department head can inspect the relevant outcome and reasons; bidder-level evidence requires the owner's explicit permission. Showing department progress must not require appointment to an evaluation committee.

For Evaluation oversight, pre-delivery administrative facts are: state, assigned committee, relevant dates/deadlines, existing responsible role/next action, and meeting date/duration/attendance counts. Do not include bidder identities, bid counts, prices, findings, clarification content or discussion notes. Appointment-related disclosures remain controlled by their owner. This administrative set is the explicit proposed interpretation of “status only.”

Opening uses its own reveal rule. Award uses its own professional-opinion and decision disclosure rules. Contract Management uses permissions for each contract record and event. Authorised bid counts disclosed at Opening are not retroactively hidden by Evaluation's restrictions; the Evaluation view must not reveal additional protected content.

### 4.1 Proposed minimum read additions by owner

**The read additions below are approved.** HoD Opening, Evaluation and Award summaries are covered by OVS-P01–P03, approved 3 October 2026.

These are the exact business-read additions for the coordinated owner amendments; they do not add workflow roles or rights to approve. They apply on approval of OVS and the matching owner amendment. All existing valid access is retained.

| Owner | New or clarified read |
|---|---|
| STR | Active AO, HOPF and HoD responsibilities can read approved current and historical Strategy versions and their recorded approval reasons. No general Draft or pending review access is added. |
| BUD | AO/HOPF can read approved current/historical allocations and authoritative commitment/reservation position. HoD can read the allocation and funding facts attributable to their scoped departmental sources through existing consumer relationships; do not infer department ownership from a shared budget line or expose unrelated lines. Draft allocation/approval task access is unchanged. |
| NDS | AO/HOPF can read submitted/decided Needs, decisions and lineage site-wide; unsent author Drafts remain under existing access. HoD/Author retain existing scoped reads. |
| PLN | AO/HOPF retain their existing governed review access and can read submitted and approved Plan versions/decisions; HoD retains scoped DPP/source information and receives disclosed downstream position for those sources. No other department's confidential supporting evidence is added. |
| REQ | AO receives read-only authorised Requisitions and their decision/history. Existing HoD/contributor rights remain; onward progress uses the consumed immutable handoff, not a new guessed join. |
| TPR/BOP | HoD receives administrative progress and revealed Opening summary for a Tender with an authorised lead/contributing-OU relationship. AO receives explicit contextual Opening read after reveal. Neither office gains decryption or ceremony power. |
| EVL | AO/HOPF receive §§4 and 7 full delivered-version oversight. HoD receives administrative progress before delivery and a scoped summary of the delivered recommendation/outcome and its recorded reasons after delivery, with correction/expiry status. This adds no full bid, committee notes or full report access to HoD. |
| AWD | HoD receives scoped status, final AO decision/outcome/date and a disclosed decision-reason summary after that decision is recorded. Unissued notices, supplier correspondence, draft opinion and unfinished AO deliberation remain outside this added read. No change to AO/HOPF's existing Award authority. |
| PRC | Meeting metadata and counts follow §11; full minutes follow the owning stage's independent permission. |
| CFG/BDS | No new business audience: retain authorised configuration context and own-organisation supplier reads. Apply navigation/history/recovery requirements without opening sealed content. |
| CM | Apply §10; exact functional and evidence-read mappings await the current CM sources. Do not invent Finance, inspection or contracting grants from this matrix. |

Contributor matching uses the actual source version consumed by the Tender, with current AUTH scope (including authorised descendants). TPR must expose the certified lead and contributor identifiers through its read, without an independently editable duplicate. STR/BUD/REQ and departmental additions must be explicit in their owner hooks; holding a URL or an office label alone is insufficient.

For technical readers, this change preserves the supplied approved policy. KT-STD §3A.6 and procurement owner restrictions are inconsistent in places. The proposed resolution is specified in §4.2. It requires approval, not another undisclosed inference. Business-role usability can be verified independently.

### 4.2 Proposed technical-reader reconciliation

Preserve KT-STD's Administrator/System Manager read-only access to ordinary business records. Distinguish that responsibility from a limited technical operator or incident-support assignment, which sees only its permitted operational information. Neither role can decide, sign, attest, impersonate a member or release the tender box through technical access.

Before governed opening, sealed bid contents remain excluded under BDS and TRUST. An authorised support surface shows safe health/status information, not decryptable content; a permitted technical page verdict is not permission to reveal sealed contents. Keys and signing credentials are never ordinary record data. Production custody and proof gates remain unchanged.

After governed release, Administrator/System Manager reads the ordinary owner business record under KT-STD's technical-read policy; no command or personal work item is added. A technical operator without that technical-reader status does not gain the same read. Existing committee conflict and supplier boundaries continue to apply to their business identities.

The coordinated KT-STD, AUTH, BOP, PRC, AWD and TRUST amendments must express this distinction consistently. This resolves the proposed policy text; it does not record Project Owner approval or prove production confidentiality. The TRUST test adapter expressly makes no infrastructure-administrator confidentiality guarantee.

## 5. Everyday entry points and finding work

### 5.1 Workspace

Reuse the existing home/workspace and My Work mechanisms. Show work requiring the user's action, recorded due dates, and links to the relevant module registers. Do not create a second task engine or duplicate an owner task as a visibility task.

A task identifies the record, action, responsible person/role and due date where one exists. A missing due date is not “overdue.” Completing an action removes or updates the task under the owner's rules; the record remains accessible through its register.

Users with oversight responsibilities can reach progress and outstanding matters within their scope without pretending those matters are assigned to them. Keep “My work” separate from records they oversee.

### 5.2 Registers and search

Every module register includes authorised active and historical records. Provide clear **Active** and **All records** choices and search by reference/title; use supplier, department, status, date or outcome filters only where applicable and backed by existing data. Display active filters, filtered result count and **Clear filters**. **Approved incorporated dependency — OVS-P04.** The TPR v0.16 work-summary change is incorporated and approved in TPR v0.17; preserve its separately labelled counts. In the proposed design, counts cover the whole permitted queue: those counts are filter controls, not filtered result totals. Meeting totals follow §11 filters. Do not replace either meaning with the other. Completed, cancelled and returned records remain findable.

Module navigation remains visible under KT-STD §3A.3 and opens an explanatory access state; protected record existence is separately masked. Scope search before returning rows, suggestions or totals. Do not leak protected record titles through autocomplete. Existing global search should link to authorised records if supported; global search is not a prerequisite for usable module registers.

Preserve filters, sort order and page position on returning from a record. A no-result state distinguishes no matching records from a source-loading failure. Search must not depend on remembering an internal database identifier.

## 6. Persistent record and decision view

Each record has a consistent structure, adapted to its business purpose:

| Area | Required content |
|---|---|
| Identity and position | Plain title, business reference, current state, applicable owner/department and material dates |
| Action or outstanding work | Existing action for the actor; responsible role/person and outstanding matter for an authorised observer; no invented task |
| Current disclosed decision | Clearly named decision type, outcome, decision maker, date, concise recorded reasons and qualifications |
| Supporting information | Source data, report, evidence and relevant upstream/downstream record links |
| History | Prior decisions and versions, return/cancellation reasons, changes and their authority |

Keep material reasons visible, not only in a downloadable file. Long evidence and detailed comparisons open on demand. Use **Not recorded** when a missing expected fact matters; omit inapplicable fields. Do not infer approval, acceptance or payment from an unrelated status.

A recommendation, professional opinion, final award decision, acceptance certificate and payment are different facts. Label each correctly. Display current process state alongside the latest disclosed decision when they differ.

Historical access follows current permission and applicable retention rules. A former office holder does not retain access merely because a report was once delivered to them.

## 7. Versioned evidence and corrections

A delivered Evaluation report exposes its exact report version, evaluated bid versions, findings, reasons, clarifications and dispositions, due diligence, committee record and signatures to the authorised oversight reader. All submitted documents belonging to those evaluated bid versions are included, even if not individually cited.

The owner must provide immutable associations between the delivered version and its supporting records. A time filter alone is not sufficient. Later submissions and unfinished correction material do not inherit the earlier delivery's disclosure.

On return, keep the previous delivered outcome readable with **Returned for correction**, the return reason and **A corrected report is being prepared**. When the correction is delivered, present it as current and retain earlier versions through a labelled selector. Preserve selected version and return path across evidence links and downloads.

A new correction notice or upstream update may be displayed under the owner's disclosure rule without silently replacing the signed report. Cancellation, suspension and expiry remain visible with their authorised reasons. A report with no current recommendation must not imply a winner.

Evidence downloads recheck current permission, including direct file URLs. No bulk bid export is added. Existing security/access logging continues; viewing creates no business approval, decision or task-completion event.

## 8. Connected navigation and progress

The internal Tender record has **Decisions and progress** for available, authorised Opening, Evaluation and Award records. Show each stage's status, latest disclosed outcome, actor/date, recorded reason, outstanding matter and authoritative links. One primary **View record** link is supplemented by **View report** or **View supporting records** when applicable. Existing actions remain available in the owner view.

Replace the old three header links only when their equivalent authorised navigation works. Preserve unrelated links and consumers. The overview is a working section, not a second journey tracker or parallel approval process.

A hand-off names the receiving responsibility and actual next action when disclosed. Prefer **Charles Mutiso is preparing the professional opinion** to **The report is now with Award** when the owner supplies that assignment. Do not invent a person or claim an action is underway merely because assigned.

Each record supplies a reliable route back to its register and contextually relevant related records. Deep links work on refresh and direct load. A missing optional module or absent related record is handled without a broken link. A summary failure is shown only after the owner has established permission to know that stage exists; do not infer protected existence from an exception. Denied stages are omitted; failures for already-authorised stages show **We could not load this stage** and **Try again**. Other sections remain usable.

## 9. Coverage by business area

The following are required user questions and candidate existing sources to reconcile with fresh owner documents. They do not assert that every source field exists today.

| Area | User must be able to understand and reach |
|---|---|
| Configuration and responsibility | Applicable entity/year/context, current responsibility and why an action is unavailable |
| Strategy | Approved direction and the supporting decision; related planning context where a link exists |
| Budget and Funding | Current authorised provision, recorded commitments/availability and reasons for funding decisions, without a competing calculation |
| Departmental Needs | Submitted need, disposition and recorded relationship to later procurement; absence of a relationship is not invented rejection |
| Procurement Planning | Current plan/version, included items, changes and approval reasons, and linked requisitions where present |
| Requisitions | Requested requirement, owning/contributing departments, decisions, return reasons and resulting Tender links |
| Tender preparation/publication | Current issued version, amendments, dates, publication evidence and progress into later stages |
| Supplier submission | Own draft/submitted state, receipt evidence, applicable amendment and outstanding permitted response; internal readers retain sealing boundaries |
| Bid Opening | Schedule, actual opening record, authorised opened facts, minutes and exceptions |
| Evaluation | Current working state; after disclosure, recommendation, reasons, comparison, report versions and supporting records |
| Award | Professional opinion, authorised final decision, notifications, restrictions and resulting contract relationship |
| Proceedings | Relevant meeting record, attendance, conclusions and signatures according to owner permissions |
| Contract Stage 1 | Contract source, agreed terms, signing/effectiveness position, responsibilities and prerequisites |
| Contract Stage 2 | Delivery, custody versus acceptance, inspection results, defects, corrective obligations and performance exceptions |
| Contract Stage 3 | Invoice/payment position from accounting, remaining obligations, final acceptance and close-out decisions, surviving claims/warranties |

Do not force a sequential dependency where the owner allows independent entry, optional upstream records or parallel work. Missing links are shown honestly; they are not filled with fabricated historical records.

## 10. Contract Management independence

Contract Management has its own accessible register and contract record. Existing signed contracts can be managed without KenTender Tender or Award records or modules. No synthetic Tender, Award or prior approval is created simply to make navigation work.

The same decision/evidence/outstanding-work structure applies across all three contract stages. Optional links to a KenTender Tender enrich context but are not access or installation prerequisites. Shared identity, responsibility, trust and ERPNext dependencies remain as specified by Contract Management.

ERPNext Accounts is the first-deployment accounting source. Distinguish invoice received, liability recorded, payment approved, payment recorded and confirmed settlement where those states are supported by verified records. Do not infer cash payment from a credit adjustment or procurement approval. Link to the authoritative permitted accounting record; do not reproduce a second ledger.

External-contract opening balances and history are labelled as reconciled starting information under CM rules, not replayed as new stock or accounting transactions. CM owner amendments carry these requirements; CM delivery does not block release of corrected Evaluation visibility.

## 11. Procurement meetings register

One read-only register covers Opening and Evaluation sessions. It does not introduce scheduling, agendas, quorum or generic contract meetings. Readers are site-scoped AO/HOPF, authorised auditors, and department heads within their authorised departmental scope. Administrator and System Manager have site-wide read-only access to this register under KT-STD §3A.6 and the proposed reconciliation in §4.2. They see the same safe session metadata, never sealed contents, keys or signing credentials. A limited technical operator has no register access solely through that assignment. Other operational readers retain their owner-defined access. The coordinated policy is approved; it adds no meeting commands.

| Concern | Rule |
|---|---|
| Rows | One per session actually started; a planned opening recorded Not held appears once without being counted as held |
| Held total | Count each distinct started session once, including aborted-after-start and ongoing sessions; signing is not a meeting |
| Department | Resolve owning/lead and contributing departments from authoritative source relationships. Verify whether ownership is immutable; if reassignment is supported, use owner history for attribution at the meeting date. Never silently change historical totals |
| Department filter | Matches lead or contributor within reader scope; totals group once under lead department, labelled **Grouped by lead department** |
| Date filter | Inclusive site dates of actual start; Not held uses the recorded scheduled date labelled Scheduled. Undated rows appear only with no date filter |
| Present | Distinct people with recorded attendance during the session, not current online users |
| Duration | End minus start; blank while ongoing or when trusted timestamps are missing |
| Totals | Apply permission, owner verdict and filters before aggregation and pagination; totals cover all matching rows, not just the page |
| Failure | Hide unverifiable rows and show **Some meeting records could not be loaded. Totals are incomplete.** Never claim a partial total is complete |

Default columns: Type, Tender, Department (contributors as secondary text), Session, Meeting date, Duration, Present, State, View record. Filters: Type, Department, State, From, To and Find a tender. Omit department selection for a reader with only one applicable scope where it adds no value.

Rows never expose bidder identities, bid counts, findings or discussion content. The record link applies the owner's own permission; register access grants no additional record access. Missing attribution shows **Department not recorded**. No rows or aggregate counts are disclosed outside reader scope.

## 12. Interaction, language and accessibility

- Use familiar business words and consistent labels. Explain what happened and what the user can do. Avoid internal codes, module hand-off jargon and technical errors in user-facing copy.
- Keep forms limited to information the task needs. Reuse authoritative values; never ask users to re-enter a fact already held. Preserve entered values on validation or recoverable network failure.
- Show field-level errors and a useful page-level explanation. Prevent accidental duplicate submission; never show success until the owner confirms it. Retry follows the owner's idempotency rules.
- Do not add confirmation dialogs for ordinary navigation or read access. Retain confirmations only where the existing action warrants them. Permission failures must not suggest borrowing another person's account.
- Make loading, no records, no matches, unavailable data, permission denial and genuinely completed work distinct states. A blank amount is not zero. Stale values must be labelled and must not drive a decision as current.
- Support keyboard navigation, visible focus, labelled fields and controls, readable contrast and zoom without hiding essential actions. Never communicate status through colour alone. Tables have readable headers and a usable narrow-screen/zoom layout.
- Preserve filters, selected versions and record context through browser back/forward and refresh. After a change refresh affected facts and task state without discarding unrelated user input.
- Use site time consistently and show timezone for significant instants. Label currencies and units. Preserve exact authoritative monetary values and existing rounding rules.

## 13. Read and action contracts

| Contract | Required result |
|---|---|
| Owner register/search | Authorised active and historical rows, supported filters, stable pagination and scoped result count |
| Owner record read | Identity, current state, disclosed decisions, evidence/history and independently authorised actions |
| Tender stage summaries | Owner-defined disclosure per stage; status, version reference where applicable, labelled facts, disclosed outcome/reason/actor/date, outstanding matter and permitted links |
| Evaluation oversight read | Delivered-version projection under §§4 and 7; never replaces committee working access or exposes an unfinished correction |
| Report/evidence read | Exact requested authorised version and its supporting records; permission rechecked at download |
| Meeting register read | §11 rows and totals with owner-applied scope and disclosure |
| My Work/next-action read | Existing authoritative assignments and action destinations; no new task lifecycle |

A status-only summary contains only the permitted administrative facts. The owner determines whether a stage can be known to exist. References and links are validated server-side; browser hiding is not access control. Permission-aware batching is allowed; one remote call per row is not mandated. Scope changes invalidate affected cached access.

A new summary structure must be incorporated into the canonical owner/interface definitions during reconciliation, rather than added as contradictory prose beside an old response schema.

## 14. Design deliverables and fixtures

Produce one consistent design specification after source reconciliation, using the current KT-STD format. Separate static screen content from functional behaviour. Do not send old v0.1/v0.2 screen lists alongside this replacement as concurrent instructions.

| Surface | Required variants |
|---|---|
| Workspace/My Work | Actor work; oversight outstanding matters; nothing requiring action; unavailable source |
| Module register | Active; historical; filtered no matches; scoped departmental view; load failure |
| Record detail | Actionable; waiting on another responsibility; completed; returned; cancelled; denied |
| Tender Decisions and progress | Opening only; evaluation protected; delivered outcome; corrected version pending; Award decision; partial load failure |
| Evidence/history | Exact delivered version; older version; uncited evaluated submission; denied unfinished correction; unavailable attachment |
| Procurement meetings | Populated totals; contributors; ongoing; Not held; scoped view; incomplete totals |
| Contract record — deferred design | Native Award source; independently registered signed contract; delivery/inspection exception; accounting status; surviving close-out obligation |
| Supplier submission record | Own current submission, permitted clarification and retained historical receipt; supplier contract/delivery/payment designs deferred with CM |

Use the supplied KT-STD v1.14 and SEED-OPS v1.21 people and four-bid canonical story. Keep exceptional test branches isolated; do not change the canonical one-supplier-to-four-supplier decision. Include a cross-department Tender, two Evaluation sessions, a Not held opening, a returned report and a standalone contract. Do not invent new authority assignments solely for screenshots.

Counting test: Tender A has lead department A, contributor B, one started Opening and two started Evaluation sessions. Tender B has lead B and one Not held Opening. Unfiltered there are four rows and three meetings held; filtering contributor B still returns those four rows and three held, with the three held sessions grouped under lead A and the Not held row grouped under lead B (zero held for B). Pagination does not change totals. For these isolated branches, department A is Digital Health and department B is Human Resources Management and Development. Mnemonics OU-MOH-DHI/HRMD are fixture aliases; resolve actual generated identities under SEED-OPS decision D3 rather than forcing those codes. At the June 2027 meeting dates, Dr Peter Kimani supplies the positive lead-A and lead/contributor-B views. SEED-OPS v1.21 §11 decision D4 retains his Directorate assignment from 1 September 2026; SEED v1.3 §3.1 also records his own Digital Health term from 1 December 2026. Retain his HRMD assignment. These are supplied-source facts, not new appointments or proof that the seed has run. Julia Njeri’s October–November 2026 acting term is an expired-access negative fixture at those dates, not a positive oversight persona. Tender A is an isolated branch of TND-MOH-2027-033; Tender B is a separate generated test record with its returned reference, not an invented canonical ID. Amina Hassan, Charles Mutiso and Naomi Chebet are the oversight personas. Preserve four bids in the canonical completed evaluation; the Not held branch has no opened bids. CM-specific fixtures await the missing CM sources.

### 14.1 Design-readiness disposition

This is the consolidated requirements authority, not a static design contract. Do not pass it to Claude Design as KT-STD §2 plus a design section. The v0.5 review D1–D5 and D7 are accepted and remain open as design deliverables; D6 is deferred with CM, not falsely closed by this revision. No prior v0.1 screen description is reinstated.

Complete the first design slice in the existing EVL, TPR and PRC design sections: delivered Evaluation record/evidence, Tender Decisions and progress, and Procurement meetings. Then complete the changed views in the remaining supplied owners. Each owner section must contain artboard ID, archetype, actor and task, Level 1/2/3 priorities, ordered composition, exact title/description/labels/values, exhaustive visible and absent actions, loading/empty/error/denied variants, first-view comprehension tests, and exact next-step/journey content or an explicit absence. Resolve each conditional requirement into named variants; the designer makes no access or layout decision.

The requirements author must supply exact dates, attendance, duration, report/stage outcomes and a stable display reference for each isolated fixture before design handoff. Generated runtime IDs are recorded by the seed; a human-facing fixture alias must be expressly labelled and must never force a database identity. Record the actor/state/event conformance matrix in each owning design section, including the source read, disclosure boundary, action authority and expected navigation. No matrix or closed fixture is claimed complete here.

The original KT-STD design checks remain the only handoff checks; no new business approval or runtime gate is added. CM and supplier contract/delivery/payment variants are deferred. Existing supplier submission/receipt/clarification views remain in the supplied-module scope.

## 15. Acceptance and completion

| ID | Required result |
|---|---|
| OVS-AC-001 | For each in-scope module, an authorised user can find active and historical records by business reference/title and return to the same register position |
| OVS-AC-002 | Submission, completion and hand-off update tasks without removing the authorised record, its decision, reasons or evidence |
| OVS-AC-003 | Record views distinguish current state, recommendation, opinion, final decision and recorded financial/acceptance events |
| OVS-AC-004 | AO/HOPF without committee appointment see only the defined administrative Evaluation facts before delivery, across all endpoints and downloads |
| OVS-AC-005 | After delivery they see the report and full defined supporting record, including uncited evaluated documents, without impersonation or appointment |
| OVS-AC-006 | Return and new correction work neither alter the old delivered projection nor expose unfinished findings/evidence; corrected delivery retains earlier versions |
| OVS-AC-007 | Existing committee, secretary and operational access/actions remain intact; oversight access alone grants no decision power |
| OVS-AC-008 | A department head sees relevant progress, disclosed outcomes and outstanding obligations, including authorised contributor relationships, but no unrelated departmental records |
| OVS-AC-009 | Permission revocation takes effect on subsequent reads/downloads; cached content and search suggestions do not leak across users/scopes |
| OVS-AC-010 | Stage summaries respect each owner's disclosure rule; omitted stages and failed authorised stages are distinguishable without leaking protected existence |
| OVS-AC-011 | Existing personal actions are reachable from the record; observer information creates no duplicate task, approval or notification |
| OVS-AC-012 | Meeting counts match §11 for ongoing, aborted, Not held, contributor, date-filter, pagination and partial-failure cases |
| OVS-AC-013 | A standalone signed contract remains usable without Tender/Award modules or fabricated upstream records |
| OVS-AC-014 | Contract/payment views display authoritative source states and do not equate invoice approval, credits or liability with confirmed cash settlement |
| OVS-AC-015 | Supplier users see their own permitted work/history and no competitor or internal committee content |
| OVS-AC-016 | Keyboard, focus, zoom, error recovery, duplicate-submit prevention and back/refresh journeys work on the representative surfaces in §14 |
| OVS-AC-017 | Cancellation, suspension, expiry, no bids and no current recommendation produce accurate outcomes and a useful route onward |
| OVS-AC-018 | Every applicable module has a recorded usability coverage result; an exclusion has a specific reason and owner, not a silent omission |

These IDs replace the proposed v0.2 acceptance list; reconciliation must update references to that list rather than retaining conflicting meanings.

Requirements are ready for approval when fresh owner sources have been reconciled, role/disclosure mappings and required fields are explicit, source gaps have dispositions, and canonical design fixtures are bound. Implementation is complete only when the applicable end-to-end journeys pass on the installed system with evidence. A document approval is not evidence of deployment or usability verification.

## 16. External changes and coordinated reconciliation

**Source reconciliation, 3 October 2026.** The uploaded files.zip contains 20 files. AUTH v1.3 is historical beside v1.10. OVS v0.1 in the archive is historical beside this conversation's v0.3 and this v0.6. NDS v1.15 and PLN v1.28 are approved successors missing from the register. REQ v1.13, CFG v0.17 and TPR v0.16 explicitly remain proposed in their supplied controls; their approved predecessors remain baseline. KT-STD v1.14 and SEED-OPS v1.21 are approved. The SEED-OPS opening approval statement controls over its retained proposed history. These are document findings, not verified build status.

The companion impact schedule and proposed owner successors use this upload, preserve its pending changes and record the scope of inspection. No older local module copy was substituted. The second upload supplies CTX, TRUST and SEED-001. STD-TPL v0.13 is older than the v0.15 registered in the first bundle; it is inspected as historical evidence only, not used to downgrade that baseline. The later standalone upload supplies approved v0.15 and closes the template baseline source gap.
The current Contract Management sources and separate template walkthrough change are deferred by the Project Owner on 3 October 2026. Retain these as scoped outstanding items; do not request them again until that work resumes.

The second bundle’s CTX v1.0 was read in full. Its global multi-PE selector, User Permission/User Scope Assignment access, PE Fiscal Year Context gate and mandatory context picker contradict the later AUTH/CFG/NDS baseline. Proposed CTX v1.1 replaces those clauses with site identity, registered responsibility access and optional module-owned filters. TRUST v0.1 was read in full; its sealed-custody and test/production separation inform §4.2. SEED v1.3 controls and affected chronology/lineage sections were checked against SEED-OPS v1.21 decisions; its entire older fixture is not claimed fully harmonised.

For supplied sources, the companion package contains the impact matrix, limited proposed owner amendments and reconciled registers. For remaining sources: establish the approved baseline and pending successor, resolve the remaining CM/template interface gaps, and complete the coordinated amendments. Preserve externally approved changes. Keep OVS proposed until the Project Owner approves the reconciled package.

| Owner group | Required coordinated change |
|---|---|
| KT-STD | Persistent usable records, register/history navigation, plain language, accessibility and owner-specific disclosure |
| AUTH/context/My Work | Departmental and operational read scopes, union of valid responsibilities, existing task/action projections |
| All module owners | Record/register usability, decisions/reasons/evidence/history and authoritative related links |
| EVL/BOP/AWD/TPR | Delivered-version read, reveal/decision boundaries and Tender Decisions and progress |
| PRC | Meeting register, counts, metadata and owner verdicts |
| CM/ERPNext interfaces | Independent entry, three-stage record usability and authoritative accounting links/status |
| Seed/design | Canonical cross-role, cross-department and historical fixtures |
| Roadmap and both registers | One coordinated proposed/approved version set, interface changes, implementation work and verification evidence |

### 16.1 STD-TPL v0.15 reconciliation

The standalone upload confirms approval on 3 October 2026. Preserve v0.15 unchanged; v0.13 is historical. The separate walkthrough change request is recorded as approved on 2 October in v0.15, but is not incorporated into this specification. Its full text is still needed to reconcile the interface and allocate the next template version. Approval of that separate change is reported from v0.15, not independently verified from the missing change request.

The proposed usability amendment for the next coordinated template successor is: apply OVS v0.6 to existing authorised template inspection and related-record navigation; retain the owner-controlled read surface and concern action in §11. Display evaluation evidence using the exact bid snapshot, published release, question wording, answer reading and rule reason in §§9.1 and 13.12. Do not substitute current Account facts for the business profile captured in the bid. Contract views use the explicit destinations in §9.2; an administrative fact marked Not carried forward is not a contract obligation. Preserve available historical outputs and the existing On/Off, integrity and withdrawal rules. No template editing or activation action, new approval gate, or access to another supplier's information is added.

The existing evaluation-display follow-up remains open. Structured discounts remain a separate future release. This reconciliation does not close the source's open questions, certify the renderer or infer runtime implementation. IF-020 and AUD-024/AUD-028 remain open specifically for walkthrough rebase and integration, not for absence of v0.15.

## 17. Delivery sequence and approval effect

The scope is the complete cross-system change. Implementation may be sequenced without quietly deferring modules out of scope:

1. Finish requirements review for supplied modules and record the explicit proposal dispositions below. CM and the separate template walkthrough remain deferred by the Project Owner on 3 October 2026.
2. Complete the owning documents’ static design sections and conformance matrices under §14.1 before approving those design inputs or sending them to Claude Design.
3. Correct disappearing delivered Evaluation information and its evidence access; implement the shared record/register/navigation pattern.
4. Apply it across existing MVP modules and deliver the Tender overview, departmental visibility and meetings register.
5. Apply and verify it across all three CM stages as CM is implemented, including independent contracts and ERPNext accounting views.
6. Run representative actor, department, oversight, auditor and supplier journeys; close the module coverage checklist and record deployment evidence.

Earlier verified improvements may be released independently. Do not label the complete usability change implemented while applicable module coverage remains open. CM-specific work remains tracked against CM readiness and does not hold back an independently verified Evaluation fix.

Approval of this request accepts its proposed usability scope and rules. It does not itself overwrite owner documents, approve stale version references, alter procurement law or prove implementation. Approval must name the supplied-module version set and dispositions OVS-P01–P05. Deferred CM/template work and open design work remain explicitly excluded from any readiness claim; requirements approval alone does not authorise an incomplete design prompt.

## 18. Single-source ownership and limited amendments

OVS owns common persistent visibility, finding records, decision/evidence presentation and its new read additions. KT-STD owns page archetypes, technical read, next_step, Home, My Work and common interaction rules; OVS cites these and does not fork them. Module owners own domain facts, decisions and permission enforcement. The companion owner amendments reference OVS v0.6 and replace only identified conflicting clauses or add owner-specific reads. They do not reproduce the shared usability chapters.

Approved predecessors remain historical and effective until their proposed successors are approved. A source supplied as proposed is rebased intact; OVS approval must not implicitly approve its unrelated pending changes. The impact schedule names these pending chains. No global “OVS overrides every owner” precedence rule is introduced.

### 18.1 Approved proposal dispositions

| ID | Proposal | Status and effect |
|---|---|---|
| OVS-P01 | HoD administrative Tender progress and revealed Opening summary, §4.1 TPR/BOP | Approved 3 October 2026; no decryption or ceremony authority |
| OVS-P02 | HoD Evaluation administrative progress and delivered outcome/reason summary, §4.1 EVL | Approved 3 October 2026; no full report, bids or committee notes |
| OVS-P03 | HoD final Award decision/reason summary, §4.1 AWD | Approved 3 October 2026; no draft opinion, unissued notices or correspondence |
| OVS-P04 | Preserve the separate TPR v0.16 queue-summary proposal | Approved in TPR v0.17; the intermediate v0.16 is not separately backdated as approved |
| OVS-P05 | Administrator/System Manager read reconciliation, §§4.2 and 11 | Approved 3 October 2026 with KT-STD, AUTH, BOP, PRC, AWD and TRUST |

### 18.2 Error, seed and traceability contracts

These additions are requirements contracts, excluded from design prompts until incorporated into the applicable static variants.

| Read outcome | Contract key | Exact user message and recovery |
|---|---|---|
| Authorised stage fails to load | OVS_STAGE_UNAVAILABLE | **We could not load this stage**; **Try again**. Keep other authorised stages usable. |
| Meeting read is incomplete | OVS_MEETINGS_INCOMPLETE | **Some meeting records could not be loaded. Totals are incomplete.**; **Try again**. Never show missing records as zero. |
| Evidence cannot be loaded | OVS_EVIDENCE_UNAVAILABLE | **We could not load this supporting record. Try again.**; **Try again** and **Back to report**. Preserve selected report version. |
| Record absent or its existence protected | Owner's existing masked-read key | Reuse the owner's identical absent/denied record response. Do not disclose existence or invent a competing error code. |
| Module entry denied | Owner's page verdict | Use KT-STD §3A.4 with the exact surface and responsibility list supplied in that owner's static design section. |

The three OVS keys describe proposed read outcomes; map them to existing equivalent owner keys where available instead of creating duplicates. They do not change command error contracts.

Seed ownership remains SEED/SEED-OPS, with §14 defining required isolated branches and the source-backed Peter/Julia chronology. Dates, values and generated reference bindings required for static artboards remain open under §14.1. Seed execution is not claimed.

Prohibited shortcuts: do not fabricate assignments or fixture values; substitute live Account data for signed bid snapshots; disclose unfinished corrections; treat unavailable data as zero; add a duplicate task/ledger; make a proposed read grant effective through a UI change; or send conditional requirements as finished design input.

| KT-STD §7 concern | OVS location / owner |
|---|---|
| Governing direction, scope and ownership | §§1–3; proposal dispositions §18.1 |
| Domain model and lifecycle | Existing owners retained; proposed read contracts §§6–8, 11, 13; no new business lifecycle |
| Roles and permissions | §§4–4.2 and 11 |
| Services and errors | §13 and §18.2; owner commands unchanged |
| Routes and static design | Existing owner routes; PRC proposed /app/procurement-meetings; static contracts open under §14.1 |
| Functional interaction, audit/history | §§5–8, 12–13; reads create no business decisions |
| Seed and acceptance | §§14–15 and §18.2 |
| Implementation, prohibited shortcuts | §§15, 17 and §18.2; KT-STD §§4–6 retained |
| Traceability and approval | §§16–18 and companion impact schedule |

Section numbering is retained to avoid breaking the coordinated owner references; this mapping makes the skeleton coverage explicit. The static design contract remains a recorded missing deliverable, not an omitted inapplicable section.
