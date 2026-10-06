# HOME-CHG-001 — Home

| Control | Value |
|---|---|
| Document ID | HOME-CHG-001 |
| Version | 0.6 |
| Status | Approved — 4 October 2026 |
| v0.6 proposed status (retained) | Proposed — 4 October 2026; v0.4 is the approved version |
| v0.5 status (retained) | Proposed — 4 October 2026; v0.4 is the approved version |
| v0.4 status (retained) | Approved — 4 October 2026 |
| v0.4 proposed status (retained) | Proposed — 4 October 2026; v0.3 was Proposed and never approved; approval of v0.4 required |
| Approved on | 4 October 2026 |
| Approval record | v0.6: Project Owner, 4 October 2026, verbatim: “Yes”, answering “Shall I apply this pass, and then approve KT-STD v1.22, HOME v0.6 and ANL v0.8 together?”. Approves v0.6 including the v0.5 content it incorporates; no separate approval of v0.5. (Proposed record read: None for v0.6. None for v0.5. v0.4: Project Owner, 4 October 2026, verbatim: “Mark the three documents as approved and give them to me to download”. Approves v0.4 in full. None recorded for v0.3. (Proposed record read: None for v0.4. None recorded for v0.3.)) |
| v0.3 status (retained) | Proposed; requirements and static design contract in this document |
| Date | 4 October 2026 |
| Owner | kentender_core |
| Supersedes | HOME-CHG-001 v0.5 and v0.4 on approval only. v0.5 read: HOME-CHG-001 v0.4 on approval only. v0.4 read: HOME-CHG-001 v0.3 on approval only. v0.3 superseded HOME-CHG-001 v0.2 and its separate design-prompt extract   |
| Sources | KT-STD-001 v1.22 (v0.4 read: KT-STD-001 v1.19; v0.3 read: KT-STD-001 v1.15); OVS-CHG-001 v0.6; AUTH-ADR-001 v1.11; CTX-CHG-001 v1.1; TPR-CHG-001 v0.17; EVL-CHG-001 v0.5; AWD-CHG-001 v0.5; REQ-CHG-001 v1.14; NDS-CHG-001 v1.16; BOP-CHG-001 v0.11; ANL-CHG-001 v0.6 |
| v0.5 change type | Surface correction only, following KT-STD-001 v1.22 §2.4 and D-HOME-03: the orientation band and every region sit on one white sheet over Frappe's grey ground, separated by headings, spacing and rules, with no tinted fill. Content, counts, rows, actions and states are unchanged. |
| v0.6 change type | Composition change on D-HOME-04 (Option C): §10B replaces §10A as design input with a main column and rail, summary columns, two-line rows, relative timings with exact times, **Your turn** only where blocked, a single oversight count, removal of Find a record (D-HOME-05), and the Accounting Officer brief HOME-DES-29 (D-HOME-07). §5.1 items 2, 4, 6 and 7 are amended; a new item 8 sets priority for empty main columns. Content, counts, actions, permissions and states are otherwise unchanged. |
| v0.4 change type | Composition and design change on the v0.4 review and the Project Owner decisions of 4 October 2026 (§1, D-HOME-01 and D-HOME-02): orientation band with greeting, responsibilities and region counts; new **Coming up** region; rows led by business name with module identity; in-place Show more replacing Previous/Next; oversight summary linking to Analytics; technical-reader and wider Find a record links; KT-STD-001 v1.19 visual language; cross-module fixtures for Charles Mutiso and Dr Peter Kimani. Adds §§4–9 rows and notes, §10A, §11 rows, §13.1, §14 rows, §16, §17.1 and §18.0. All v0.3 content is retained; superseded rules are marked in place. No owner workflow, task, decision or permission is added. |

**Controlling decision:** Home shows the user’s work first, then what they are waiting for, records they oversee, and recently completed actions. It opens existing owner records; it creates no business task or decision. This document contains the complete Home requirement, design input, fixture and acceptance contract. There is no companion requirements or prompt document.

**Controlling decision added in v0.4:** Home opens with who the user is and how much is theirs: a greeting, every active responsibility and the count of their actions, waits and overseen records. Each row leads with the business name and its module, then the action and its timing. A **Coming up** region shows scheduled events and owner deadlines in the next 14 days. Home stays item-level; aggregate views are in Procurement Analytics, which Home links to.

## 1. Governing decision and disposition register

| Earlier item / review finding | Disposition in v0.3 |
|---|---|
| Separate prompt and shared-hierarchy companion | Retired as inputs to this change. Design input is §10 of this document with KT-STD §2, assembled at use; no saved duplicate. |
| Ad hoc document structure and incomplete alternate screen briefs | Use the applicable KT-STD §7 sections and the twelve-part screen brief. |
| Routine report delivery labelled as attention for AO | Show the current Award responsibility in a read-only oversight row. Delivery is quieter evidence. |
| Inconsistent five-item cap / View all / full-list instruction | Five entries per region per page, with region-specific Previous/Next controls and complete authorised count. No new cross-module View all route. |
| Home illustrated only through Tenders | Home provider coverage includes all approved internal modules; design remains a small representative fixture, not a module restriction. |
| Submitted Tender described as completed | “Recently completed actions” explicitly describes the user’s action, not completion of the procurement. |
| D-HOME-01 — v0.4 review proposed a Coming up region of 14 days. Project Owner, 4 October 2026, asked “Coming up region: add it, and is 14 days the right window?”, answered verbatim: “Yes” | §5.1 Coming up rules; §10A. KT-STD-001 v1.19 §3B.5 adds the region. |
| D-HOME-02 — Project Owner, 4 October 2026, asked “Summary figures in the header: acceptable on Home?”, answered verbatim: “Acceptable” | Orientation band counts in §5.1. Counts only; no chart. §2's “not an Analytics dashboard” is retained. |
| v0.4 review — rows led by references | KT-STD-001 v1.19 §2.6.4 requires a task row to lead with the business name and keep the reference subordinate. §10A rows lead with the record title and module; every fixture record now has a title. |
| v0.4 review — fixtures only from Tenders | §10A adds Charles Mutiso (cross-module Head of Procurement Function work) as the complete brief and Dr Peter Kimani (departmental work); Brian Wafula and Amina Hassan become variants. |
| v0.4 review — Previous/Next paging | Replaced by in-place **Show more** (§5.1). The five-entry first page and complete count are retained. |
| v0.4 review — barren technical and empty views | Technical readers get **Technical record search** and **Procurement Analytics** links; Find a record adds Strategy, Budget & Funding and Procurement Analytics. |
| D-HOME-03 — rendered HOME-DES-11 with tinted regions was rejected by the Project Owner. Project Owner, 4 October 2026, choosing between rendered Option A (Frappe workspace cards) and Option B (light grey ground with one bordered white sheet), answered verbatim: “Option B” | §10A.1 surfaces follow KT-STD-001 v1.22 §2.4: one bordered white sheet on Frappe's `--gray-50` ground; no tinted region. |
| D-HOME-04 — Claude Design review of the rendered HOME-DES-11 found weak figures, unbalanced space and a list-like structure, caused mainly by §10A fixing layout and by unchecked composition. Project Owner, 4 October 2026, on the five adjustments to the Claude Design review (main column for oversight-only users; figures in heading colour; module name kept visible on the quiet line; relative times with the exact time always visible; Coming up kept in the main column), answered verbatim: “Yes”; on the Option C brief and render: “Approved” | §5.1 amendments and §10B. Layout detail sits in the design section and the design-system workspace template; requirements keep content and priority. |
| D-HOME-05 — Find a record repeated Frappe's sidebar navigation and lengthened the rail. Claude Design recommended removing Find a record as duplicate navigation; the amendment adds an empty-rail rule and moves Technical record search to the header for technical readers. Project Owner, 4 October 2026, answered verbatim: “Apply” | Removed from §5.1, §9, §10B and §11; **Technical record search** stays for technical readers in the header row; an empty rail lets the main column span 12 columns. |
| D-HOME-06 — Option C was refined with Claude Design and rendered. Project Owner, 4 October 2026, presenting the render: “We have iterated with Claude Design to come up with the attached” | §10B matches the render: summary columns with left rules instead of bordered cards, a tinted badge for Coming up relative dates, a warning callout for reasons, and unfilled rail icons. KT-STD-001 v1.22 §2.6.7 lets the actions summary carry the page's task rule. |
| D-HOME-07 — v0.6 had no Accounting Officer brief with real decisions; HOME-DES-23 showed the AO with nothing to do. Project Owner, 4 October 2026, verbatim: “Before approving, I did not see any accounting officer persona in Home. This is one of the most important roles as the ultimate authority” | §10B adds scenario H12 and the complete brief HOME-DES-29, using owner action titles from TPR, AWD and EVL; HOME-DES-23 remains the no-pending-decision variant. |

**Explicit proposed exception:** KT-STD v1.15 §3B.5 limits Home to next-step answers and hand-off items. Under its §1 exception mechanism, this change adds one read-only **Records you oversee** region using approved OVS §4.1 projections. It does not expand personal work or owner permissions. The exception is fully defined here; approval of this document would authorise it. Other KT-STD rules remain controlling. (v0.4: no longer an exception. KT-STD-001 v1.16 §3B.5 and later include the read-only Records you oversee region; this paragraph is retained as history.)

## 2. Purpose, outcomes and scope

Internal users can start an action, understand a blocker, see who holds their waiting work, inspect authorised progress and return to completed actions. Supplier users retain their portal. Home is not an Analytics dashboard, notification inbox or personal watchlist. (v0.4: the orientation band's counts describe the user's own regions and link to them; overseen aggregates stay in Procurement Analytics, linked from Records you oversee.)

The primary questions are: What needs my action? What prevents that action? Who am I waiting for? What remains outstanding in records I oversee? Where is the action I completed? Home performs no approval, task completion or acknowledgement.

## 3. Ownership and dependency boundary

Core composes existing owner reads for Strategy, Budget, Needs, Planning, Requisitions, Tenders, Opening, Evaluation and Award. Include an entry only where the owner provides the relevant actor-specific next step or hand-off item. A role does not make every record in its module a task. Contract Management is a later provider, including independent contracts; it must not require a Tender history.

The owner supplies the record, source revision/event, safe display facts, current holder, due date if any, permission verdict and destination. Core does not recompute guards, appoint holders, store a parallel task or infer activity from assignment. The requirements below define proposed composition, not installed API availability.

## 4. Canonical read model

These are transient response values, not new DocTypes or saved business fields.

| Value | Rule and consumer |
|---|---|
| Region | My work, Waiting on others, Records you oversee, Recently completed actions. Determines placement and paging. |
| Entry identity | Owner + root + exact task/action/event. Deduplicate the same work; preserve genuinely separate actions on one record. |
| Source identity | Exact revision/event plus current owner revision. Used to open the right record and detect superseded work. |
| Display | Safe title, recorded state, required action or outstanding matter, reason/comment, holder and since/completion instant. Include all material blockers supplied for that action. |
| Due | Optional actual owner deadline and rule basis. No overdue from age alone. |
| Destination | Owner-generated route and exact task/record/version arguments. Core validates the destination belongs to the expected owner and current viewer. |
| Coverage | Per-region applicable providers, complete/partial/unavailable verdict and returned-data time. A configured provider failure is not a missing-module zero. |
| Page | Five entries, opaque next/previous cursors and complete authorised count only when known. The count is not a sum of partial pages. |
| Module (v0.4) | Owner module of the entry. Determines the row's module icon and label. |
| Coming up entry (v0.4) | Owner Scheduled next-step answer (KT-STD-001 v1.19 §2.9.1) or recorded owner deadline in the §5.1 window: event label, instant, holder (System for scheduled events), record and destination. |
| Region count (v0.4) | Complete authorised count per region for the orientation band, or unavailable. Never computed from returned rows. |
| Responsibilities (v0.4) | Every active responsibility with its scope, from AUTH, for the orientation band (KT-STD-001 v1.19 §3A.5). |

## 5. Composition and business rules

| Region | Inclusion / order | Clearing |
|---|---|---|
| My work | Actor’s Your turn or Your turn, blocked answer or owner hand-off item. Actual overdue deadlines first, then recorded deadlines, then undated work by oldest recorded state entry; stable identity breaks ties. | Owner’s stated transition, never viewing Home. |
| Waiting on others | Actor’s explicit waiting-on item/answer, with holder and since. Oldest first. | Owner transition resolves or changes waiting. |
| Records you oversee | Authorised owner progress/outstanding-matter summary under current responsibility. Outstanding matters first by oldest recorded since; other disclosed updates newest first. All results are read-only. | Owner state changes the row; scope expiry removes it. |
| Recently completed actions | The actor’s completed owner action/event, newest first. The record can still be in progress. | Retained history remains in the owner record; this region pages through eligible action events. |

Empty regions are omitted only after a successful applicable read. An oversight-only reader sees progress without invented personal tasks. Do not duplicate the same entry in My work and oversight; retain My work and its material context. Distinct waiting/completion events remain distinguishable.

Paging is within the region on Home. Next/Previous replace only that region’s rows. A partial provider set has no complete total; label its coverage and keep usable rows. A destination read rechecks authority and current state. If the task cleared after Home loaded, open the current permitted record with its owner explanation rather than execute stale work. (v0.4: Next/Previous are replaced by Show more under §5.1; the cursor model is retained.)

### 5.1 v0.4 composition rules

1. **Region order.** Orientation band; My work; Coming up; Waiting on others; Records you oversee; Recently completed actions; Find a record. (v0.6: Find a record is removed; navigation stays with Frappe's sidebar. **Technical record search** remains for technical readers as a header-row link.)
2. **Orientation band.** A greeting by site time — **Good morning** before 12:00, **Good afternoon** from 12:00 to 16:59, **Good evening** from 17:00 — with the user's first name; every active responsibility with its scope; one count per applicable region: **actions for you**, **items you're waiting on** and **records with outstanding matters**. A count appears only for a region applicable to the actor, and only when complete; otherwise the label reads **Count unavailable**. Selecting a count moves focus to its region. A successful all-empty read shows no counts (§10A HOME-DES-18A). (v0.6: each count is a summary column headed by its region name, in the order actions, waiting, oversight; the labels are unchanged; the column is the focus target for its region.)
3. **Coming up.** Entries in the 14 calendar days from the read date, in the site timezone: the actor's own Scheduled next-step answers, owner events the actor attends or chairs, and recorded owner deadlines on records the actor holds or oversees. An entry already shown in My work is not repeated. Earliest first. Each shows the record, the event, its exact date and time and a relative label: **Today**, **Tomorrow** or **In n days**. Read-only; it creates no task and clears when the owner event occurs or the deadline is met.
4. **Relative due labels.** A My work due date within 14 days also shows **Due today**, **Due tomorrow** or **Due in n days**; a passed owner deadline shows **Overdue since** with the date. Age alone never produces Overdue. (v0.6: received, submitted, since and outstanding times also show a relative form, computed server-side in site-timezone calendar days, with the exact time always visible: **Received today (18 June, 09:00)**, **Received yesterday (17 June, 11:00)**, **Received 2 days ago (16 June, 11:00)**; **Waiting 2 days (since 16 June, 15:30)**; **Outstanding 15 days (since 3 June, 10:00)**; due **Due tomorrow (18 June)**; Coming up **In 7 days (25 June, 11:00)**. The year is omitted when it is the read year. Never hover-only.)
5. **Show more.** Each region shows its first five entries, then **Showing 5 of n** and a text action **Show n − 5 more** (or **Show 5 more** when more than five remain), which appends the next cursor's rows in place. No page replacement, Previous or View all.
6. **Records you oversee.** Above its rows, **n records with outstanding matters** and the text link **See all in Procurement Analytics**, to the matching ANL-CHG-001 v0.6 tab, shown only when the actor's Analytics verdict permits it. (v0.6: superseded in part. The count line above the rows is removed; the count appears once, in its fact card. The text link **See all in Procurement Analytics** follows the rows.)
7. **Row anatomy.** Module icon and module name; business title as the lead; action or state line; material reason where blocked; timing (received, since, due or scheduled); reference as secondary text; one row action. (v0.6: required fields are unchanged; their placement belongs to the design section and the design-system work row. **Your turn** is shown only as **Your turn, blocked**; ordinary rows in My work carry no turn label.)
8. **Priority when the main work is empty (v0.6).** When My work and Coming up are both empty after a successful read, **Nothing needs your action right now.** leads, and Records you oversee becomes the Level 1 region for an actor who oversees records. Waiting, completed and Find a record stay Level 3.

## 6. Roles and permissions

Use AUTH and the owner’s current predicates. Multiple valid responsibility/scope pairs are unioned without a role/scope Cartesian product. Home grants no record permission. Technical readers receive no personal business action solely from Administrator/System Manager status; limited technical support does not confer ordinary business read. Supplier/public users are not given the internal Home projection. Ordinary module navigation follows KT-STD §3A; an entry point is not proof of record access. (v0.4: technical readers, including the Technical Operator under ANL-CHG-001 v0.6 D-ANL-10, see the orientation band without counts, **Technical record search** and **Procurement Analytics**; they still receive no personal business action.)

## 7. Service contract

**Proposed `GetHomeWorkspace` read:** inputs are region page cursors; actor and scope come from the authenticated server context. Output is the §4 response. First read covers all applicable approved providers; retries read the failed region or all regions after total failure. Pagination/retry never marks work read or complete. Reuse owner workspace reads, next-step answers and hand-off contracts; extend an owner’s safe read only through its canonical interface, not table scraping.

Owner transitions are the only creation/clearing events for work. Home emits no shared-service business event. A newly applicable provider must be included in coverage; a disabled/uninstalled module is distinguishable from a provider failure. Cache expiry/revocation follows AUTH; cached entries cannot survive a failed current permission verdict. (v0.4: GetHomeWorkspace also returns the Coming up region, region counts and responsibilities. Owners expose Scheduled answers and recorded deadlines through their existing Home feed; §17.1.)

## 8. Error contract

| Composition result | User language / treatment |
|---|---|
| Initial loading | **Loading your work…**; no empty claim or counts. |
| Partial region failure | **Some work in this section could not be loaded.** / **Try again**; safe rows retained, complete total omitted. |
| Entire region unavailable | **We could not load this section.** / **Try again**. |
| All applicable providers fail | **We could not load your work.** / **Try again**. |
| Internal entry denied | **This page is for internal users.** No business content. |
| Link denied or task changed | Owner’s current masked-access or changed-state response; do not expose the old entry after revocation. |
| v0.4: region count unavailable | **Count unavailable** in the orientation band; the region shows its own failure text. |
| v0.4: Coming up unavailable | **We could not load this section.** / **Try again** in Coming up only. |

These are Home response categories, not replacement owner error codes. Instants display in the configured site timezone; the shared fixture uses EAT.

## 9. UI architecture and routes

Proposed core route **`/app/home`**, menu **Home**, internal landing page. The existing supplier portal stays separate. Region paging is in this route; no View all page is introduced.

| Destination | Binding |
|---|---|
| Tender work/record | `/app/tenders/{tender_id}`; exact task/action context comes from TPR’s owner answer. |
| Delivered report | EVL’s owner-generated exact delivered-version destination; no working correction route substituted. |
| Other module work | Registered owner action/record destination from its canonical next-step/hand-off projection. |
| Find a record links | `/app/departmental-needs`, `/app/procurement-planning`, `/app/procurement-requisitions`, `/app/tenders`. (v0.6: removed from Home.) |
| v0.4: Find a record additions | `/app/strategy`, `/app/budget`, `/app/analytics`. (v0.6: removed from Home.) |
| v0.4: technical reader link | **Technical record search** `/app/technical-search` (KT-STD-001 v1.19 §3A.6). (v0.6: shown as a quiet header-row link for technical readers only.) |

No invented route for a missing report binding. That owner must supply the exact delivered artifact/version destination before implementation acceptance.

## 10. Static design contract

**v0.4: retained history, not design input.** This section is the v0.3 design contract, kept unchanged. It is superseded by §10A on approval of v0.4. Do not supply it to Claude Design.

Use KT-STD v1.15 §2 with **this section only** for design generation. All visible facts for these artboards are supplied here. The standard owns shared shell, tokens, archetypes and presentation rules. No separate prompt file or hierarchy companion is required.

### HOME-DES-01 — Brian’s work

1. **Identity/archetype/purpose:** Home; Work workspace; Brian finds and opens his own work.
2. **Fixture outside artboard:** Brian Wafula, Procurement Officer, site-wide; 17 June 2027, 10:00 EAT; isolated design-only scenario H1. Four distinct Tenders 040/034/039/037 and their action events, not one alternate state of the canonical Tender.
3. **Question/action:** What needs Brian’s action? Navigation only; cancellation-evidence **Continue** is dominant.
4. **Priority:** Level 1 My work and material reasons; Level 2 Waiting on others; Level 3 completed action and register links.
5. **Header:** **Home**; **Your work and the records you are following.** No header button or filter. Quiet data line **Updated 17 June 2027, 10:00 EAT**.
6. **Composition:** header; My work task rows; quieter Waiting on others row; quiet Recently completed actions row; quiet Find a record links. No table, chart or dashboard cards.
7. **Complete content:** **My work**: first row **Record cancellation notices and PPRA report for TND-MOH-2027-034**, **Your turn**, **Due 18 June 2027**, **Continue**; second row **Respond to clarification for TND-MOH-2027-040**, secondary **Supply of clinic peripherals**, **Your turn**, **Continue**. **Waiting on others**: **Waiting for Amina Hassan to consider cancellation of TND-MOH-2027-039**, **Accounting Officer · since 16 June 2027, 14:00 EAT**, **View record**. **Recently completed actions**: **Tender TND-MOH-2027-037 submitted for approval**, **You submitted this Tender on 16 June 2027, 09:00 EAT. It is awaiting publication authorisation by Amina Hassan.**, **View record**. **Find a record**: text links **Departmental needs**, **Procurement planning**, **Requisitions**, **Tenders**. The cancellation deadline is an owner-supplied fixture fact; no response deadline is recorded for 040.
8. **Actions:** first Continue primary row button; second Continue standard row button; View record and module destinations text links. All enabled. No Approve, Mark done, Assign, View all, paging controls or business action on Home.
9. **Supporting detail:** none copied onto Home; full source remains in owner record. Completed action is not labelled a completed Tender.
10. **Variants:** HOME-DES-02–09 are separate scenarios below, inheriting this brief with stated replacements. No conditional layout left to designer.
11. **Comprehension:** two own actions, Amina’s responsibility and Brian’s completed submission are distinguishable before following a link. Waiting/completion do not compete with current action.
12. **Next step/journey:** neither record component appears on this Work workspace. Row text is the supplied owner work state.

### HOME-DES-02 — Amina’s oversight

Inherit DES-01 shell and twelve-part brief; replace fixture with Amina Hassan, Accounting Officer, site-wide, 16 June 2027, 16:00 EAT, isolated H2. Replace data time accordingly. No personal work or waiting item. Under header show **Nothing needs your action right now.** Then **Records you oversee**: title **Supply and delivery of business laptops**, secondary **TND-MOH-2027-033**, main position **Award · Awaiting professional opinion by Charles Mutiso**, quiet fact **Evaluation report delivered 16 June 2027, 14:07 EAT**, enabled text link **View report**. No recently completed region. Find a record links unchanged. Level 1 no-personal-action orientation; Level 2 current Award responsibility; Level 3 delivery evidence and module links. First view must not imply Amina has a report-review task. No tracker/next-step component.

### HOME-DES-03 — Brian’s blocked response

Separate H3 branch, Brian at 17 June 2027, 10:00 EAT. Replace all work/waiting/completed content with one My work row **Respond to clarification for TND-MOH-2027-040**, secondary **Supply of clinic peripherals**, **Your turn, blocked**, visible reason **Issue an addendum before sending this answer.**, primary enabled **Continue**. No waiting or completion region. Find links unchanged. This is an owner-established published-change guard, not an unavailable service. Level 1 blocker and Continue; Level 2 record title; Level 3 links. First view states why responding is blocked; Continue opens the owner view containing Prepare addendum. No business fix is executed on Home; no next-step block/tracker.

### HOME-DES-04 — successful empty

Separate H4, Brian at 17 June 2027, 10:00 EAT; all applicable providers complete with no permitted entries. Header/time and Find links as DES-01. Show **Nothing needs your action right now.** No region headings, zero figures, tasks, paging or tracker. First view distinguishes a successful absence of personal work from load failure.

### HOME-DES-05 — partial waiting failure

Separate H5, Brian at DES-01 instant. Preserve DES-01 My work, Recently completed actions and Find links. Replace Waiting on others row with **We could not load this section.** and standard **Try again** button in that region. No waiting count or empty claim. Level 1 own work; Level 2 named section failure; Level 3 completion and links. Other sections’ known update time remains visible; no claim that waiting data was refreshed. No tracker.

### HOME-DES-06 — total failure

Separate H6, Brian at DES-01 instant; all applicable providers fail. Header title/description retained; omit update time, all region content and Find links. Show **We could not load your work.** and primary **Try again**. Only Retry is interactive inside artboard. No empty sentence or tracker. This does not remove Frappe’s outer navigation.

### HOME-DES-07 — technical reader

Separate H7, Administrator, technical only, 17 June 2027, 10:00 EAT; successful applicable read with no work/history/oversight entries. Same header/time and Find links; **Nothing needs your action right now.** No My work or business command. Level 1 no-personal-action orientation; Level 3 record navigation. No tracker.

### HOME-DES-08 — paging

Separate H8, Brian at DES-01 instant. My work has six authorised clarification actions for distinct references **TND-MOH-2027-050**, **051**, **052**, **053**, **054**, **055**, all undated; first page shows 050–054 in that order. Each exact title **Respond to clarification for [full reference]**, state **Your turn**, enabled standard **Continue**; 050’s Continue primary. No secondary title invented. Under My work **Showing 1–5 of 6 actions**, disabled **Previous**, enabled standard **Next**. No waiting/oversight/completion region. Find links/header/time as DES-01. Second-page variant HOME-DES-08B: only 055, **Showing 6 of 6 actions**, enabled Previous and disabled Next. Level 1 tasks; Level 2 paging; Level 3 links. Full references for abbreviated labels above use the common TND-MOH-2027- prefix. No View all or tracker.

### HOME-DES-09 — initial loading / denied

HOME-DES-09A, Brian at DES-01 instant, initial read pending: header/description, **Loading your work…**, no update time, regions, counts or inside-artboard actions. HOME-DES-09B, Jane Wanjiku, public observer, direct internal Home entry: title **Home**, **This page is for internal users.**, no record, action or update time. Level 1 loading/access explanation only; no next-step/tracker in either variant.

## 10A. Static design contract — v0.4

**v0.6: retained history, not design input.** §10B supersedes this section on approval of v0.6. Do not supply it to Claude Design.

### 10A.1 Prompt assembly, archetype and shared composition

Supply KT-STD-001 v1.19 §2 and **this section only** for design generation. §10 is retained history and is not supplied. Every artboard is a **Work workspace** (KT-STD-001 v1.19 §2.6.3), read-only apart from navigation and Continue, with no next-step block or journey tracker. Visual treatment follows KT-STD-001 v1.19 §2.6.11.

**Shared composition, top to bottom.**

1. **Orientation band**, on one tinted surface. Left: greeting as a heading; beneath it the responsibilities line. Right: one figure per applicable region, each a large number with its label beneath. Quiet text **Updated [instant]** at the bottom right. No header button or filter. (v0.5: the band has no tinted fill. It is the first section of the white sheet, closed by a 1px rule.)
2. **My work.** Task rows. The first row's **Continue** is the primary button; others are standard buttons.
3. **Coming up.** Compact rows with a date column on the left showing the relative label above the exact date and time.
4. **Waiting on others.** Compact rows.
5. **Records you oversee.** Summary line and Analytics link, then compact rows.
6. **Recently completed actions.** Compact rows.
7. **Find a record.** One line of text links with module icons.

Each region sits on its own lightly tinted surface with a section heading preceded by its region icon. A region with no entries after a successful read is omitted. (v0.5: superseded. All regions sit on one white sheet with a 1px border, over Frappe's `--gray-50` ground; each region starts with its icon and section heading and is separated from the next by spacing and a 1px rule. No region has a fill or its own border. Rows inside a region are separated by 1px rules.)

**Row anatomy.** Module icon chip and module name in small text; the business title as the row's lead; the action or state line beneath; a material reason in its own line where present; the timing (received, since, due or scheduled) right-aligned; the reference as secondary text under the title; one action at the far right. No icons other than the module chip in rows. In the briefs below, ` — ` separates a row's fields in display order; it is not rendered.

**Module icons**, from the design system's module icon list: Strategy, Budget & Funding, Needs, Planning, Requisitions, Tenders, Bid opening, Evaluation, Award and Procurement Analytics each have one icon, the same as on their own pages.

### 10A.2 Fixtures — outside the artboard

All scenarios are illustrative. Instants are EAT.

**H10 — Charles Mutiso, Head of Procurement Function, site-wide; 18 June 2027, 10:00.**

| Region | Module | Title | Action or state | Timing | Reference |
|---|---|---|---|---|---|
| My work | Requisitions | Clinic equipment requisition | Authorise requisition | Received 16 June 2027, 11:00 | None shown |
| My work | Award | Supply of printers | Prepare professional opinion | Received 16 June 2027, 14:07 | TND-MOH-2027-044 |
| My work | Award | Supply of monitors | Resolve notice delivery; reason **A required notice is not yet confirmed.** | Received 17 June 2027, 11:00 | TND-MOH-2027-045 |
| Coming up | Bid opening | Supply of network switches | Start opening | 25 June 2027, 11:00 | TND-MOH-2027-042 |
| Coming up | Evaluation | Supply of office desks | Evaluation deadline | 1 July 2027 | TND-MOH-2027-043 |
| Waiting on others | Tenders | Supply of UPS units | Waiting for Amina Hassan to decide publication | Since 16 June 2027, 15:30 | TND-MOH-2027-047 |
| Records you oversee | Evaluation | Supply of office desks | Committee review outstanding | Since 3 June 2027, 10:00 | TND-MOH-2027-043 |
| Records you oversee | Tenders | Supply of IT peripherals | Warranty requirement returned for correction; awaiting correction by Brian Wafula | Since 16 June 2027, 09:00 | TND-MOH-2027-041 |
| Recently completed | Tenders | Supply of UPS units | You approved this Tender package | 16 June 2027, 15:30 | TND-MOH-2027-047 |

Counts: 3 actions, 1 item waited on, 2 records with outstanding matters. My work order is oldest received first, because none has a due date. Charles chairs the 042 opening committee in H10. The 043 deadline is the EVL-displayed statutory evaluation deadline as an owner fact; no legal period is asserted here.

**H11 — Dr Peter Kimani, Head of User Department, Human Resources Management and Development; 18 June 2027, 10:00.** H11 uses only Peter's KT-STD-001 v1.19 §8.3 responsibility.

| Region | Module | Title | Action or state | Timing | Reference |
|---|---|---|---|---|---|
| My work | Needs | Staff training laptops | Decide whether this requirement is available to Procurement Planning | Submitted 17 June 2027, 14:00 | None shown |
| Records you oversee | Evaluation | Supply of office desks | Committee review outstanding | Since 3 June 2027, 10:00 | TND-MOH-2027-043 |
| Records you oversee | Tenders | Supply of IT peripherals | Warranty requirement returned for correction | Since 16 June 2027, 09:00 | TND-MOH-2027-041 |

Counts: 1 action, 0 items waited on, 2 records with outstanding matters. No Coming up or Recently completed entries.

**H1, H2, H3 and H8 titles (v0.4).** v0.3 scenarios keep their facts and gain titles: 034 **Supply of hospital beds**; 039 **Supply of field laptops**; 037 **Supply of desktop computers**; 040 **Supply of clinic peripherals** (v0.3); 050 **Supply of examination gloves**; 051 **Supply of syringes**; 052 **Supply of hospital linen**; 053 **Supply of oxygen cylinders**; 054 **Supply of wheelchairs**; 055 **Supply of thermometers**.

### 10A.3 HOME-DES-11 — Charles's Home

1. **Identity, archetype and purpose:** HOME-DES-11, Home; Work workspace; Charles sees his work across modules, what is coming up, what he is waiting for and what he oversees, then opens one.
2. **Fixture:** H10; route `/app/home`.
3. **Question and action:** What needs Charles's action, what is coming up and what is outstanding in records he oversees? Primary action: **Continue** on the first My work row.
4. **Priority:** Level 1 orientation band and My work. Level 2 Coming up and Waiting on others. Level 3 Records you oversee, Recently completed actions and Find a record.
5. **Orientation band:** heading **Good morning, Charles**; line **Head of Procurement Function, site-wide**; figures **3** **actions for you**, **1** **item you're waiting on**, **2** **records with outstanding matters**; quiet **Updated 18 June 2027, 10:00 EAT**.
6. **Composition:** §10A.1 order; all six regions present.
7. **Content:**
   - **My work**, three task rows in this order:
     - Requisitions — **Clinic equipment requisition** — **Authorise requisition** — **Your turn** — **Received 16 June 2027, 11:00 EAT** — primary **Continue**.
     - Award — **Supply of printers** — secondary **TND-MOH-2027-044** — **Prepare professional opinion** — **Your turn** — **Received 16 June 2027, 14:07 EAT** — standard **Continue**.
     - Award — **Supply of monitors** — secondary **TND-MOH-2027-045** — **Resolve notice delivery** — reason line **A required notice is not yet confirmed.** — **Your turn** — **Received 17 June 2027, 11:00 EAT** — standard **Continue**.
   - **Coming up**, two rows:
     - Date column **In 7 days** above **25 June 2027, 11:00 EAT**; Bid opening — **Supply of network switches** — secondary **TND-MOH-2027-042** — **Start opening** — text link **View record**.
     - Date column **In 13 days** above **1 July 2027**; Evaluation — **Supply of office desks** — secondary **TND-MOH-2027-043** — **Evaluation deadline** — text link **View record**.
   - **Waiting on others**, one row: Tenders — **Supply of UPS units** — secondary **TND-MOH-2027-047** — **Waiting for Amina Hassan to decide publication** — **Accounting Officer** — **Since 16 June 2027, 15:30 EAT** — text link **View record**.
   - **Records you oversee:** line **2 records with outstanding matters**; text link **See all in Procurement Analytics**. Rows: Evaluation — **Supply of office desks** — secondary **TND-MOH-2027-043** — **Committee review outstanding** — **Since 3 June 2027, 10:00 EAT** — **View record**; Tenders — **Supply of IT peripherals** — secondary **TND-MOH-2027-041** — **Warranty requirement returned for correction** — **Awaiting correction by Brian Wafula since 16 June 2027, 09:00 EAT** — **View record**.
   - **Recently completed actions**, one row: Tenders — **Supply of UPS units** — secondary **TND-MOH-2027-047** — **You approved this Tender package on 16 June 2027, 15:30 EAT. It is awaiting publication authorisation by Amina Hassan.** — **View record**.
   - **Find a record:** **Strategy**, **Budget & Funding**, **Departmental needs**, **Procurement planning**, **Requisitions**, **Tenders**, **Procurement Analytics**.
8. **Actions:** one primary Continue; two standard Continue; text links; figure links move focus. All enabled. No Show more, because no region exceeds five. No approve, assign, mark done or View all.
9. **Supporting detail:** none on Home; full detail is in each owner record.
10. **Variants:** HOME-DES-12 to HOME-DES-18 below.
11. **Comprehension:** the first view shows three actions from two modules, one blocked by an unconfirmed notice, the next two dates, and who holds the waited item. Oversight is visibly quieter than own work. The completed approval is not a completed Tender.
12. **Next step and journey:** neither appears.

### 10A.4 HOME-DES-12 — Brian's Home

HOME-DES-11 shell with H1 (v0.3), 17 June 2027, 10:00. Band: **Good morning, Brian**; **Procurement Officer, site-wide**; figures **2** **actions for you** and **1** **item you're waiting on** only (no oversight region applies). My work: Tenders — **Supply of hospital beds** — secondary **TND-MOH-2027-034** — **Record cancellation notices and PPRA report** — **Your turn** — **Due tomorrow, 18 June 2027** — primary **Continue**; Tenders — **Supply of clinic peripherals** — secondary **TND-MOH-2027-040** — **Respond to clarification** — **Your turn** — standard **Continue**. No Coming up region (the 034 deadline is already in My work). Waiting: Tenders — **Supply of field laptops** — secondary **TND-MOH-2027-039** — **Waiting for Amina Hassan to consider cancellation** — **Accounting Officer** — **Since 16 June 2027, 14:00 EAT** — **View record**. Recently completed: Tenders — **Supply of desktop computers** — secondary **TND-MOH-2027-037** — **You submitted this Tender on 16 June 2027, 09:00 EAT. It is awaiting publication authorisation by Amina Hassan.** — **View record**. Find a record as HOME-DES-11.

### 10A.5 HOME-DES-13 — Amina's oversight

H2 (v0.3), 16 June 2027, 16:00. Band: **Good afternoon, Amina**; **Accounting Officer, site-wide**; figures **0** **actions for you**, **0** **items you're waiting on**, **1** **record with outstanding matters**. Under the band, **Nothing needs your action right now.** Records you oversee: line **1 record with outstanding matters**, link **See all in Procurement Analytics**; row Award — **Supply and delivery of business laptops** — secondary **TND-MOH-2027-033** — **Award: awaiting professional opinion by Charles Mutiso** — quiet fact **Evaluation report delivered 16 June 2027, 14:07 EAT** — text link **View report**. No other regions. The first view must not imply Amina has a report-review task.

### 10A.6 HOME-DES-14 — Peter's Home

H11, 18 June 2027, 10:00. Band: **Good morning, Peter**; **Head of User Department, Human Resources Management and Development**; figures **1** **action for you**, **0** **items you're waiting on**, **2** **records with outstanding matters**. My work: Needs — **Staff training laptops** — **Decide whether this requirement is available to Procurement Planning** — **Your turn** — **Submitted 17 June 2027, 14:00 EAT** — primary **Continue**. Records you oversee: line **2 records with outstanding matters**, link **See all in Procurement Analytics**; rows as H11 with **View record**. No Coming up, Waiting or Recently completed region. Find a record as HOME-DES-11.

### 10A.7 HOME-DES-15 — Brian's blocked response

H3 (v0.3). Band as HOME-DES-12 with figures **1** **action for you** and **0** **items you're waiting on**. One My work row: Tenders — **Supply of clinic peripherals** — secondary **TND-MOH-2027-040** — **Respond to clarification** — **Your turn, blocked** — reason line **Issue an addendum before sending this answer.** — primary **Continue**. No other region except Find a record.

### 10A.8 HOME-DES-16 — Show more

H8 (v0.3), Brian. Band figures **6** **actions for you**, **0** **items you're waiting on**. My work shows five rows in order 050 to 054, each Tenders — title from §10A.2 — secondary full reference — **Respond to clarification** — **Your turn** — **Continue** (050 primary). Under them: **Showing 5 of 6** and text action **Show 1 more**. **HOME-DES-16B:** after Show 1 more, the 055 row (**Supply of thermometers**) is appended below 054 with focus on it; **Showing 6 of 6**; no Show more action.

### 10A.9 HOME-DES-17 — Technical Operator

Daniel Otieno, Technical Operator, site-wide read-only; 17 June 2027, 10:00; successful read. Band: **Good morning, Daniel**; **Technical Operator, site-wide**; no figures. **Nothing needs your action right now.** Find a record adds **Technical record search** as the first link. No business action. Administrator and System Manager see the same composition with their own name and responsibility line.

### 10A.10 HOME-DES-18 — Empty, failure, loading and access

- **HOME-DES-18A — successful empty (H4).** Band greeting and responsibility line, no figures; a small spot illustration above **Nothing needs your action right now.**; Find a record. No region headings or zeros.
- **HOME-DES-18B — Waiting region failed (H5).** HOME-DES-12 with the Waiting on others region showing **We could not load this section.** and standard **Try again**; its band figure reads **Count unavailable**. Other regions unchanged.
- **HOME-DES-18C — Coming up failed (H10 variant).** HOME-DES-11 with Coming up showing **We could not load this section.** and standard **Try again**. Coming up has no band figure.
- **HOME-DES-18D — total failure (H6).** Heading **Home**; spot illustration; **We could not load your work.**; primary **Try again**. No greeting, figures, update time or links.
- **HOME-DES-18E — loading (H9A).** Heading **Home**; **Loading your work…**; nothing else.
- **HOME-DES-18F — internal page denied (H9B, Jane Wanjiku).** Heading **Home**; spot illustration; **This page is for internal users.**; nothing else.

### 10A.11 Design inventory

| Artboard | Actor and scenario | Based on |
|---|---|---|
| HOME-DES-11 | Charles, H10 | Complete brief |
| HOME-DES-12 | Brian, H1 | HOME-DES-11 |
| HOME-DES-13 | Amina, H2 | HOME-DES-11 |
| HOME-DES-14 | Peter, H11 | HOME-DES-11 |
| HOME-DES-15 | Brian, H3 | HOME-DES-12 |
| HOME-DES-16 and 16B | Brian, H8 | HOME-DES-12 |
| HOME-DES-17 | Daniel Otieno | HOME-DES-11 |
| HOME-DES-18A to 18F | As stated | As stated |

Every artboard is 1440 × 1024. The first view of HOME-DES-11 must show the band, all of My work and Coming up.

## 10B. Static design contract — v0.6 (Option C)

### 10B.1 Prompt assembly, composition and shared components

Supply KT-STD-001 v1.22 §2 and **this section only** for design generation. HOME-DES-21 matches the Option C render the Project Owner accepted on 4 October 2026 (D-HOME-06). §§10 and 10A are retained history and are not supplied. Every artboard is a **Work workspace**, read-only apart from navigation and the row actions. No next-step block or journey tracker. Surfaces follow KT-STD-001 v1.22 §2.4: Frappe `--gray-50` ground, one white sheet with a 1px `--border-color` border, no tinted fill. Content follows HOME §5.1. In the briefs below, ` — ` separates a row's fields; it is not rendered.

**Composition.** A 12-column grid inside the sheet.

1. **Header row**, columns 1–12: greeting as the page heading, with the responsibilities line beneath it. Quiet **Updated [instant]** at the right of the same row. For technical readers only, the quiet text link **Technical record search** sits beside the update time.
2. **Summary row**, under the header: one summary column per applicable count, each spanning 4 columns, left-aligned in this order: actions, waiting, oversight.
3. **Main column**, columns 1–8: My work, then Coming up.
4. **Rail**, columns 9–12: Waiting on others, Records you oversee, Recently completed actions, in that order. Rail headings are 15 px. The rail uses text links, not buttons, except a region's **Try again**.
4A. **Empty rail.** When the rail has no regions, the main column spans all 12 columns.
5. **Empty main column.** When My work and Coming up are both empty after a successful read, the main column starts with **Nothing needs your action right now.** If the actor has overseen records, Records you oversee moves from the rail into the main column under that line.
6. **Narrow sheet.** When the sheet's content width is below 960 px, the rail stacks below the main column in the same order, and summary columns wrap two per row.
7. Regions are separated by spacing and a 1px `--border-color` rule. A region with no entries after a successful read is omitted.

**Summary column.** No box border or fill. Each column has a 3–4 px vertical rule at its left: the accent colour for the actions column (the page's single task rule under KT-STD-001 v1.22 §2.6.7) and a neutral grey for the others. Inside the column: the region's icon and region name as a small heading (**My work**, **Waiting on others**, **Records you oversee**); beneath it, the figure at 32–34 px in `--color-figure` (`#1b2c68`, KT-STD-001 v1.22 §2.4), with tabular digits, with its label to the right on the same baseline in `--text-muted`. On the actions column the icon sits in a tinted icon chip. The whole column is the focus target for its region. Where a count is incomplete, the column shows **Count unavailable** instead of the figure.

**Main-column work row.**
- **Line 1:** module icon chip with the indigo glyph; the **title** in bold; then the module name and the reference as quiet text. Separate those two items by spacing, with no delimiter character; omit the reference where none is shown.
- **Line 2:** the action or event, then the timing as quiet text. In Coming up, the relative label is a small tinted badge (**In 7 days**) followed by the exact date and time as quiet text (**25 June, 11:00**).
- **Reason line,** where present, on its own line as a warning callout: warning icon and text on a light warning tint, the status warning colour used because it is a real state (KT-STD-001 v1.22 §2.6.11 item 1).
- **One action,** vertically centred at the right. My work uses **Continue**: primary on the first row, standard on the others. Coming up uses the text link **View record**.
- **Your turn, blocked** appears on line 2 only for blocked work. Ordinary rows show no **Your turn**.

**Rail row.** Neutral module icon with no chip fill; the **title** as the link to the record; then the state, and the timing on its own quiet line. **See all in Procurement Analytics** carries the Analytics icon. All links are underlined, in `--color-accent-700`; figures are never underlined.

**Module icons** come from the design system's module icon list, as in §10A.1.

### 10B.2 Fixtures

The §10A.2 fixtures apply unchanged. Timings are shown under HOME §5.1 item 4 relative to each scenario's read time.

**H12 — Amina Hassan, Accounting Officer, site-wide; 18 June 2027, 10:00 (v0.6).** H12 shares the H10 world: Charles's H10 waiting item on 047 is Amina's publication task here; 045 is the award decision she recorded; 039 is the cancellation review Brian waits on in H1. New in H12: Tender 048, the 042 evaluation-committee appointment, and the 034 cancellation instant. Action titles are the owners' own: TPR-CHG-001 v0.17 §5.11, AWD-CHG-001 v0.5 §5.9 and EVL-CHG-001 v0.5 §7.1.

| Region | Module | Title | Action or state | Timing | Reference |
|---|---|---|---|---|---|
| My work | Evaluation | Supply of network switches | Appoint the evaluation committee | Received 14 May 2027, 10:00 | TND-MOH-2027-042 |
| My work | Tenders | Supply of field laptops | Consider cancellation | Received 16 June 2027, 14:00 | TND-MOH-2027-039 |
| My work | Tenders | Supply of UPS units | Authorise publication | Received 16 June 2027, 15:30 | TND-MOH-2027-047 |
| My work | Award | Supply of hospital laboratory analysers | Decide award | Received 17 June 2027, 16:00 | TND-MOH-2027-048 |
| Coming up | Evaluation | Supply of office desks | Evaluation deadline | 1 July 2027 | TND-MOH-2027-043 |
| Waiting on others | Tenders | Supply of hospital beds | Waiting for cancellation compliance evidence; held by Brian Wafula | Since 15 June 2027, 12:00; due 18 June 2027 | TND-MOH-2027-034 |
| Records you oversee | Award | Supply of printers | Awaiting professional opinion by Charles Mutiso | Since 16 June 2027, 14:07 | TND-MOH-2027-044 |
| Records you oversee | Award | Supply of monitors | A required notice is not yet confirmed; resolution by Charles Mutiso | Since 17 June 2027, 11:00 | TND-MOH-2027-045 |
| Records you oversee | Evaluation | Supply of office desks | Committee review outstanding | Since 3 June 2027, 10:00 | TND-MOH-2027-043 |
| Recently completed | Award | Supply of monitors | You recorded the award decision | 17 June 2027, 11:00 | TND-MOH-2027-045 |

Counts: 4 actions, 1 item waited on, 3 records with outstanding matters. My work order is oldest received first; none has a due date.

### 10B.3 HOME-DES-21 — Charles's Home (Option C)

1. **Identity, archetype and purpose:** HOME-DES-21, Home; Work workspace; Charles sees his work across modules, what is coming up, what he is waiting for and what he oversees, then opens one.
2. **Fixture:** H10, 18 June 2027, 10:00; route `/app/home`.
3. **Question and action:** what needs Charles's action first? Primary action: **Continue** on the first My work row.
4. **Priority:** Level 1: summary columns and My work. Level 2: Coming up. Level 3: the rail.
5. **Header:** **Good morning, Charles**; **Head of Procurement Function, site-wide**; **Updated 18 June 2027, 10:00 EAT**.
6. **Summary row:** **My work** **3** **actions for you** (accent rule, tinted icon chip); **Waiting on others** **1** **item you're waiting on**; **Records you oversee** **2** **records with outstanding matters**.
7. **Main column.**
   - **My work:**
     - Requisitions chip — **Clinic equipment requisition** — quiet **Requisitions** — line 2 **Authorise requisition**, quiet **Received 2 days ago (16 June, 11:00)** — primary **Continue**.
     - Award chip — **Supply of printers** — quiet **Award** and **TND-MOH-2027-044** — line 2 **Prepare professional opinion**, quiet **Received 2 days ago (16 June, 14:07)** — standard **Continue**.
     - Award chip — **Supply of monitors** — quiet **Award** and **TND-MOH-2027-045** — line 2 **Resolve notice delivery**, quiet **Received yesterday (17 June, 11:00)** — warning callout **A required notice is not yet confirmed.** — standard **Continue**.
   - **Coming up:**
     - Bid opening chip — **Supply of network switches** — quiet **Bid opening** and **TND-MOH-2027-042** — line 2 **Start opening**, badge **In 7 days**, quiet **25 June, 11:00** — **View record**.
     - Evaluation chip — **Supply of office desks** — quiet **Evaluation** and **TND-MOH-2027-043** — line 2 **Evaluation deadline**, badge **In 13 days**, quiet **1 July** — **View record**.
8. **Rail.**
   - **Waiting on others:** **Supply of UPS units** — **Waiting for Amina Hassan to decide publication**, **Waiting 2 days (since 16 June, 15:30)**.
   - **Records you oversee:**
     - **Supply of office desks** — **Committee review outstanding**, **Outstanding 15 days (since 3 June, 10:00)**.
     - **Supply of IT peripherals** — **Warranty requirement returned for correction; awaiting correction by Brian Wafula**, **Outstanding 2 days (since 16 June, 09:00)**.
     - Then the text link **See all in Procurement Analytics**. No count line above the rows.
   - **Recently completed actions:** **Supply of UPS units** — **You approved this Tender package on 16 June 2027, 15:30 EAT. It is awaiting publication authorisation by Amina Hassan.**
9. **Actions:** one primary **Continue**; two standard **Continue**; text links; the summary columns move focus to their regions. All enabled.
10. **Variants:** HOME-DES-21N, HOME-DES-29 and HOME-DES-22 to HOME-DES-28 below.
11. **Comprehension:** the summary columns stand apart from the page. The three actions read first, with the unconfirmed notice visible. The rail is visibly quieter. No row has a wide empty middle.
12. **Next step and journey:** neither appears.

**HOME-DES-29 — Amina's Home (Accounting Officer, H12).** A complete brief on the HOME-DES-21 composition.
1. **Identity, archetype and purpose:** HOME-DES-29, Home; Work workspace; Amina sees the decisions only she can take across modules, what she is waiting for and what she oversees, then opens one.
2. **Fixture:** H12; route `/app/home`.
3. **Question and action:** which decision needs Amina first? Primary action: **Continue** on the first My work row.
4. **Priority:** Level 1: summary row and My work. Level 2: Coming up. Level 3: the rail.
5. **Header:** **Good morning, Amina**; **Accounting Officer, site-wide**; **Updated 18 June 2027, 10:00 EAT**.
6. **Summary row:** **My work** **4** **actions for you** (accent rule, tinted icon chip); **Waiting on others** **1** **item you're waiting on**; **Records you oversee** **3** **records with outstanding matters**.
7. **Main column.**
   - **My work:**
     - Evaluation chip — **Supply of network switches** — quiet **Evaluation** and **TND-MOH-2027-042** — line 2 **Appoint the evaluation committee**, quiet **Received 35 days ago (14 May, 10:00)** — primary **Continue**.
     - Tenders chip — **Supply of field laptops** — quiet **Tenders** and **TND-MOH-2027-039** — line 2 **Consider cancellation**, quiet **Received 2 days ago (16 June, 14:00)** — standard **Continue**.
     - Tenders chip — **Supply of UPS units** — quiet **Tenders** and **TND-MOH-2027-047** — line 2 **Authorise publication**, quiet **Received 2 days ago (16 June, 15:30)** — standard **Continue**.
     - Award chip — **Supply of hospital laboratory analysers** — quiet **Award** and **TND-MOH-2027-048** — line 2 **Decide award**, quiet **Received yesterday (17 June, 16:00)** — standard **Continue**.
   - **Coming up:** Evaluation chip — **Supply of office desks** — quiet **Evaluation** and **TND-MOH-2027-043** — line 2 **Evaluation deadline**, badge **In 13 days**, quiet **1 July** — **View record**.
8. **Rail.**
   - **Waiting on others:** **Supply of hospital beds** — **Waiting for cancellation compliance evidence from Brian Wafula**, **Waiting 3 days (since 15 June, 12:00)**, **Due today (18 June)**.
   - **Records you oversee:**
     - **Supply of printers** — **Awaiting professional opinion by Charles Mutiso**, **Outstanding 2 days (since 16 June, 14:07)**.
     - **Supply of monitors** — **A required notice is not yet confirmed; resolution by Charles Mutiso**, **Outstanding 1 day (since 17 June, 11:00)**.
     - **Supply of office desks** — **Committee review outstanding**, **Outstanding 15 days (since 3 June, 10:00)**.
     - Then **See all in Procurement Analytics**.
   - **Recently completed actions:** **Supply of monitors** — **You recorded the award decision on 17 June 2027, 11:00 EAT. Required bidder notices are not yet confirmed.**
9. **Actions:** one primary and three standard **Continue**; text links; summary columns move focus. All enabled. Home itself takes no decision.
10. **Variants:** HOME-DES-23 remains the Accounting Officer with no pending decision (H2).
11. **Comprehension:** the first view shows four decisions only the Accounting Officer can take, from three modules, with the 35-day appointment first because it is oldest. The waited-on compliance evidence is due today. The award she recorded is not shown as a completed procurement.
12. **Next step and journey:** neither appears.

**HOME-DES-21N — narrow.** HOME-DES-21 at 1024 px with Frappe's sidebar collapsed. Summary columns wrap two per row. The rail regions stack below Coming up in the same order.

### 10B.4 Variants

- **HOME-DES-22 — Brian (H1), 17 June 2027, 10:00.**
  - Header **Good morning, Brian**; **Procurement Officer, site-wide**. Summary columns **2** **actions for you** and **1** **item you're waiting on**.
  - My work:
    - Tenders chip — **Supply of hospital beds** — quiet **Tenders** and **TND-MOH-2027-034** — line 2 **Record cancellation notices and PPRA report**, quiet **Due tomorrow (18 June)** — primary **Continue**.
    - Tenders chip — **Supply of clinic peripherals** — quiet **Tenders** and **TND-MOH-2027-040** — line 2 **Respond to clarification** — standard **Continue**.
  - No Coming up region.
  - Rail:
    - Waiting on others: **Supply of field laptops** — **Waiting for Amina Hassan to consider cancellation**, **Waiting 1 day (since 16 June, 14:00)**.
    - Recently completed actions: **Supply of desktop computers** — **You submitted this Tender on 16 June 2027, 09:00 EAT. It is awaiting publication authorisation by Amina Hassan.**
- **HOME-DES-23 — Amina with no pending decision (H2), 16 June 2027, 16:00.** HOME-DES-29 is the Accounting Officer's primary artboard; this variant shows the oversight-only state.
  - Header **Good afternoon, Amina**; **Accounting Officer, site-wide**. Summary columns **0** **actions for you**, **0** **items you're waiting on**, **1** **record with outstanding matters**.
  - Main column: **Nothing needs your action right now.**, then Records you oversee:
    - Award chip — **Supply and delivery of business laptops** — quiet **Award** and **TND-MOH-2027-033** — line 2 **Award: awaiting professional opinion by Charles Mutiso**, quiet **Evaluation report delivered 16 June, 14:07** — text link **View report**.
    - Then **See all in Procurement Analytics**.
  - No rail; the main column spans all 12 columns.
  - The first view must not imply Amina has a report-review task.
- **HOME-DES-24 — Peter (H11), 18 June 2027, 10:00.**
  - Header **Good morning, Peter**; **Head of User Department, Human Resources Management and Development**. Summary columns **1** **action for you**, **0** **items you're waiting on**, **2** **records with outstanding matters**.
  - My work: Needs chip — **Staff training laptops** — quiet **Needs** — line 2 **Decide whether this requirement is available to Procurement Planning**, quiet **Submitted yesterday (17 June, 14:00)** — primary **Continue**.
  - No Coming up region.
  - Rail:
    - Records you oversee:
      - **Supply of office desks** — **Committee review outstanding**, **Outstanding 15 days (since 3 June, 10:00)**.
      - **Supply of IT peripherals** — **Warranty requirement returned for correction**, **Outstanding 2 days (since 16 June, 09:00)**.
      - Then **See all in Procurement Analytics**.
- **HOME-DES-25 — Brian blocked (H3).**
  - HOME-DES-22 header. Summary columns **1** **action for you** and **0** **items you're waiting on**.
  - One My work row: Tenders chip — **Supply of clinic peripherals** — quiet **Tenders** and **TND-MOH-2027-040** — line 2 **Respond to clarification**, **Your turn, blocked** — reason line **Issue an addendum before sending this answer.** — primary **Continue**.
  - No rail; the main column spans all 12 columns.
- **HOME-DES-26 — Show more (H8).**
  - Brian; summary columns **6** **actions for you** and **0** **items you're waiting on**.
  - My work shows rows 050 to 054 in that order. Each is: Tenders chip — §10A.2 title — quiet **Tenders** and the full reference — line 2 **Respond to clarification** — **Continue**, primary on 050.
  - Then **Showing 5 of 6** and the text action **Show 1 more**.
  - **HOME-DES-26B:** row 055 (**Supply of thermometers**) is appended with focus on it; **Showing 6 of 6**; no further action.
- **HOME-DES-27 — Technical Operator.**
  - Daniel Otieno, 17 June 2027, 10:00. Header **Good morning, Daniel**; **Technical Operator, site-wide**. No summary columns.
  - Header row also shows the quiet link **Technical record search**.
  - **Nothing needs your action right now.** No rail; the main column spans all 12 columns.
- **HOME-DES-28 — states.**
  - **28A — successful empty (H4):** header, no summary columns. Main column: spot illustration and **Nothing needs your action right now.** No rail; the main column spans all 12 columns.
  - **28B — Waiting failed (H5):** HOME-DES-22 with the rail's Waiting on others showing **We could not load this section.** and a small standard **Try again**. The waiting card shows **Count unavailable**.
  - **28C — Coming up failed (H10):** HOME-DES-21 with Coming up showing **We could not load this section.** and standard **Try again**.
  - **28D — total failure (H6):** heading **Home**, spot illustration, **We could not load your work.**, primary **Try again**. Nothing else.
  - **28E — loading (H9A):** heading **Home**, **Loading your work…**. Nothing else.
  - **28F — denied (H9B, Jane Wanjiku):** heading **Home**, spot illustration, **This page is for internal users.** Nothing else.

### 10B.5 Design inventory

| Artboard | Actor and scenario | Based on |
|---|---|---|
| HOME-DES-21 and 21N | Charles, H10 | Complete brief |
| HOME-DES-22 | Brian, H1 | HOME-DES-21 |
| HOME-DES-29 | Amina, H12 | Complete brief |
| HOME-DES-23 | Amina, H2 | HOME-DES-21 |
| HOME-DES-24 | Peter, H11 | HOME-DES-21 |
| HOME-DES-25 | Brian, H3 | HOME-DES-22 |
| HOME-DES-26 and 26B | Brian, H8 | HOME-DES-22 |
| HOME-DES-27 | Daniel Otieno | HOME-DES-21 |
| HOME-DES-28A to 28F | As stated | As stated |

Every artboard is 1440 × 1024 except HOME-DES-21N at 1024 × 1024. The first view of HOME-DES-21 must show the header, the summary columns, all of My work and the start of Coming up, with the rail beside them.

## 11. Functional interaction requirements — excluded from design prompts

| Artboard/control | Exact read/destination and effect |
|---|---|
| 01 clarification Continue / 03/08 Continue | TPR `GetTender` on row’s distinct Tender/task, `/app/tenders/{tender_id}`. Owner refreshes guard; clarification uses its existing response view. 03 exposes owner’s Prepare addendum fix, never sends an answer. |
| 01 first Continue | TPR Tender 034 cancellation evidence view on its record; no new cancellation decision. |
| 01 View record, waiting | TPR Tender 039; current cancellation-request status and owner permission. |
| 01 View record, completion | TPR Tender 037; completed submission event remains history; current review is separate. |
| 02 View report | EVL exact delivered report of 033, read under approved OVS; retain previous delivered version during an unfinished correction. |
| Find a record links | §9’s four owner workspaces. No record is created and no permission is granted. (v0.6: removed from Home.) |
| 05 Try again | Retry Waiting region through GetHomeWorkspace; preserve other authorised regions. |
| 06 Try again | Retry all applicable providers with current permission. |
| 08 Previous/Next | Read that region’s cursor; replace its rows only; count remains six. Disabled end controls issue no read. |
| v0.4: orientation counts | Move focus to the region; no read. |
| v0.4: Show n more | Read that region's next cursor and append its rows; the count is unchanged; focus moves to the first appended row. |
| v0.4: Coming up View record | Owner record route for the event's record; no task is created. |
| v0.4: See all in Procurement Analytics | `/app/analytics/{tab}` per ANL-CHG-001 v0.6 §9.1, with no filters. |
| v0.4: Technical record search, Strategy, Budget & Funding, Procurement Analytics | §9 routes; navigation only. (v0.6: only Technical record search remains, in the header row for technical readers; navigation only.) |
| v0.4: Try again in Coming up | Retry the Coming up region only. |

## 13. Seed and actor/state conformance

All H scenarios are **illustrative artboard fixtures**, not runtime events or changes to the canonical seed. Shared actors follow KT-STD §8; the source TPR clarification/cancellation hand-offs are TPR §5.11. H2 uses EVL’s delivered-version fact and AWD’s linked professional-opinion work. H1’s completed submission and H2’s no-personal-work set are explicit isolated scenarios. In H1 Charles approved 037 at 17 June 2027, 09:00 EAT; Brian’s waiting-on-review item therefore cleared, and Amina holds the publication decision. H1’s 034 deadline is 18 June 2027 from its owner projection; sorting places it before undated 040. H3 and H8 do not reuse H1’s exact clarification event. Before runtime comparison create through owner commands and bind generated identities to each scenario; never overwrite the canonical Tender or disable owner checks.

| Scenario / chronological entry | Read/action; event and consumer | Guard / next holder / clearing / disclosure |
|---|---|---|
| H1: clarification received → Brian Home | GetHomeWorkspace → TPR GetTender; existing clarification action | Response remains Brian’s; clears on TPR answer/addendum transition, not Home read. |
| H1: cancellation decided → compliance pending | Same composition → TPR evidence record | Brian records evidence under owner deadline; clears when every required obligation is evidenced. |
| H1: review requested → Brian waiting | GetTender 039; no mutation | Amina acts; request ends on cancellation/closure with reason. No AO proxy action. |
| H1: Brian submitted → Charles approved → AO publication decision pending | GetTender 037 and submission event | Only Brian’s submission is completed; Charles’s approval cleared Brian’s review waiting item. Amina holds the next owner action. |
| H2: report delivered → Award receives | EVL delivered read; AWD linked professional-opinion task | Charles is holder; no duplicate EVL/AWD task; AO oversight has no unfinished findings. |
| H3: response affects published content | TPR guard and owner fix | Brian prepares required addendum; no answer sent from Home. |
| H4/H5/H6/H9A: empty/partial/failure/loading | Typed composition read; no event | Only complete successful reads establish empty. Unavailable coverage never zero. |
| H7/H9B: technical/public | AUTH plus owner reads/denial | No business task from technical role; public sees no internal entry. |
| H8: six actions → page 2 | Region cursor read; no event | Sixth action remains reachable; owner transitions alone clear it. |

### 13.1 v0.4 scenarios H10 and H11

H10 and H11 are illustrative artboard fixtures, not runtime events. H10 reuses record titles from ANL-CHG-001 v0.6 dataset A1 for recognisability but is a separate scenario: its notice-delivery task, Tender 047, the 042 opening appointment and the 043 evaluation deadline exist only in H10. Every new title and instant is listed in §10A.2.

| Scenario / entry | Read and owner source | Guard / clearing |
|---|---|---|
| H10: requisition submitted → Charles authorises | REQ procurement authorisation task | Clears on authorise, return or upstream correction. |
| H10: report received → professional opinion | AWD Prepare professional opinion | Clears on signed opinion or return. |
| H10: notice not confirmed → Charles resolves | AWD Resolve notice delivery | Clears when giving evidence is recorded. |
| H10: opening committee appointed → chair upcoming | BOP Start opening upcoming task | Coming up until the deadline; then BOP next step. |
| H10: Evaluation deadline recorded | EVL statutory evaluation deadline display (EVL-CHG-001 v0.5 §5.7) | Coming up until met; EVL alone states overdue. |
| H10: Charles approved 047 → AO decision | TPR waiting item and completed action | Waiting clears on publication decision or reopen. |
| H11: Need submitted → Peter decides | NDS Initial acceptance review task | Clears on accept, return or not taken forward. |
| H11: Peter's oversight | EVL and TPR HoD scoped summaries under OVS | Read-only; scope expiry removes rows. |
| H12: AO decisions across modules (v0.6) | EVL appointment, TPR publication and cancellation, AWD Decide award tasks; TPR AO waiting item; OVS oversight | Each clears on its owner decision; Home records none. |

## 14. Acceptance contract

| ID | Required result |
|---|---|
| HOME-AC-01 | Applicable approved modules contribute their existing work; no Tender-only implementation or second task store. |
| HOME-AC-02 | Personal, waiting, oversight and completed-action meanings remain distinct; all material blockers visible beside their action. |
| HOME-AC-03 | Owner transition clears work; Home viewing/navigation/paging never changes it. |
| HOME-AC-04 | Multiple scopes deduplicate the same action without losing distinct obligations; no role/scope cross-product. |
| HOME-AC-05 | Five-row pages reach every authorised result; totals never depend on page size or partial providers. |
| HOME-AC-06 | Loading, partial, total failure, empty and denied states match §10; permission expiry removes stale facts. |
| HOME-AC-07 | Delivered report navigation opens the exact authorised version; no correction draft is leaked. |
| HOME-AC-08 | First-view and keyboard/200% zoom checks preserve hierarchy, action meaning and paging. |
| HOME-AC-09 | The orientation band shows greeting, every active responsibility with scope and the complete count for each applicable region; an incomplete region shows Count unavailable; counts never derive from returned rows. |
| HOME-AC-10 | Coming up contains only owner Scheduled answers, events the actor attends or chairs and recorded deadlines within 14 calendar days, earliest first, with no duplicate of a My work entry; it creates and clears no task. |
| HOME-AC-11 | Every row leads with the business title and module; the reference is secondary. |
| HOME-AC-12 | Show more appends the next cursor's rows in place, reaches every authorised entry and leaves the count unchanged. |
| HOME-AC-13 | Relative labels use site-timezone calendar days; Overdue appears only for a passed owner deadline. |
| HOME-AC-14 | Technical readers see the Technical record search and Procurement Analytics links and no business action; the Analytics link in Records you oversee appears only when the Analytics verdict permits. (v0.6: technical readers see the Technical record search link in the header row and no business action; Procurement Analytics is reached through the Frappe sidebar. The Records you oversee Analytics link rule is unchanged.) |

## 15. Implementation and test constraints

Apply KT-STD §§4–6. Verify owner adapters, task-clearing boundaries, pagination, current permission and the §13 branches before internal customer review. Exact owner report destination and remaining provider bindings are implementation prerequisites, not proof of installed services. Design generation is possible from the closed §10 fixtures; rendered comparison and representative-user checks remain required before design acceptance. No runtime/test success is claimed by this document.

## 16. Prohibited shortcuts — v0.4

Apply KT-STD-001 v1.19 §10. Domain-specific prohibitions:

- Do not compute counts, due labels or Coming up entries in the browser.
- Do not create, clear or mark read any task from Home, including from Coming up.
- Do not show charts, distributions or overseen totals on Home; link to Procurement Analytics instead.
- Do not show Overdue from age alone.
- Do not lead a row with a reference when the owner supplies a title.

## 17. Traceability and precedence

KT-STD owns shared design mechanics and Home work semantics; OVS owns persistent visibility; AUTH owns scope; CTX owns local context; each business owner owns the record, guards and clearing events. The specific oversight exception is in §1. Universal rules are cited, not copied into a companion. This document supersedes the previous Home extract as a design input; approved source documents remain unchanged.

### 17.1 Required corrections in other documents — v0.4

| Document | Required correction |
|---|---|
| KT-STD-001 v1.18 | Add Coming up and the orientation band to §3B.5. Done in KT-STD-001 v1.19 (proposed). |
| TPR, BOP, EVL, AWD, REQ, NDS, PLN, STR, BUD | Expose Scheduled next-step answers and recorded deadlines relevant to the actor through the existing Home feed, with title, instant, holder and destination. |
| REQ-CHG-001 v1.14 | Define its hand-off register, including the Head of Procurement Function authorisation item title; HOME-DES-11 uses **Authorise requisition** from REQ-DES-08 as illustrative wording until then. KT-STD-001 v1.8 §12.2 already requires REQ hand-off rows. |
| ANL-CHG-001 v0.6 | Pre-existing finding, not changed here: ANL-DES-30 and v0.3 ANL-DES-08B show Peter **award notices awaiting delivery** for 045, while AWD-CHG-001 v0.5's OVS amendment adds no unissued notice to HoD read. Confirm whether notices awaiting delivery are within the HoD summary. |
| KT-DOC-CTRL-001 | Record HOME-CHG-001 v0.4 as Proposed. Not supplied for this change. |

## 18. Approval effect

### 18.0C v0.6 approval effect — approved 4 October 2026 (heading read: v0.6 approval effect (proposed))

v0.6 is approved by the Project Owner (4 October 2026, “Yes”, answering “Shall I apply this pass, and then approve KT-STD v1.22, HOME v0.6 and ANL v0.8 together?”). §10B, the Option C composition including the Accounting Officer brief HOME-DES-29, is the design input for every Home artboard, with the §5.1 v0.6 amendments, superseding §10A, v0.5 and v0.4. Design-system token values and components are approved in the design system. (Proposed text read: Approval of v0.6 would make §10B, the Option C composition, the design input for every Home artboard, with the §5.1 v0.6 amendments, superseding §10A and v0.5. It would not approve design-system token values or components, which are approved in the design system.)

### 18.0B v0.5 approval effect (proposed)

Approval of v0.5 would make the KT-STD-001 v1.22 surfaces the design input for every Home artboard. Everything else approved in v0.4 is unchanged.

### 18.0 v0.4 approval effect — approved 4 October 2026 (heading read: v0.4 approval effect (proposed))

v0.4 is approved by the Project Owner (4 October 2026, “Mark the three documents as approved and give them to me to download”). It authorises the orientation band, the Coming up region, Show more, the row anatomy, the added links and §10A as the design input, superseding v0.3 and its §10. The owner feed corrections in §17.1, workflow changes and implementation readiness are not approved by it. (Proposed text read: Approval of v0.4 would authorise the orientation band, the Coming up region, Show more, the row anatomy, the added links and §10A as the design input, superseding v0.3 and its §10. It would not approve KT-STD-001 v1.19, the owner feed corrections in §17.1, a workflow change or implementation readiness.)

### 18.1 v0.3 approval effect (retained)

Approval would authorise this Home composition, read contract and §1 oversight exception. It would not approve Analytics, modify a business workflow or establish implementation readiness. Exact owner adapter/route bindings and rendered acceptance remain to be completed.
