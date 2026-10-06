# OVS-CHG-001 — Oversight Visibility of Downstream Procurement Stages

| Control | Value |
|---|---|
| Document ID | OVS-CHG-001 |
| Version | 0.1 |
| Date | 3 October 2026 |
| Status | **Proposed — new document; Project Owner review required** |
| Approved on | Not yet approved |
| Approval record | None for v0.1 |
| Supersedes | None. This is the first version. |
| Change type | New cross-module change unit. Three Project Owner decisions are recorded in §1.1; the rest is proposed for review. It changes who sees what in Bid Evaluation, adds a stage summary to the Tender record, and adds one read-only register of procurement meetings. It adds no lifecycle state, command, approval, task or stored field. |
| Governing standard | KT-STD-001 v1.14 (approved) |
| Owner documents affected | EVL-CHG-001 v0.4, BOP-CHG-001 v0.10, PRC-CHG-001 v0.10, AWD-CHG-001 v0.4, TPR-CHG-001 v0.15 (v0.16 is proposed and not yet registered), KT-STD-001 v1.14. Each needs a matching version; §17.1 names them. |
| Authorities relied on | AUTH-ADR-001 v1.10, REQ-CHG-001 v1.12, SEED-001 v1.3 |
| Origin | A Project Owner review of the live Tender page for TND-MOH-2027-002, 3 October 2026, signed in as Charles Mutiso (Head of Procurement Function): the bid evaluation page showed only the committee list and the words "Report delivered". |

**Controlling decision.** KenTender is a decision-making system, so a person who oversees a procurement must be able to see what was decided, by whom, on what basis and when, without being a member of the committee that decided it. For the Accounting Officer and the Head of Procurement Function this document sets one rule for every downstream stage: **they see status only until the stage owner's delivery point, and all details after it, read-only.** It also makes the Tender record the place where the whole story can be read, and adds one read-only register so that meetings can be counted by type and by the Tender's owning department.

---

## 1. Governing decision and disposition register

### 1.1 Project Owner decisions recorded in this document

The Project Owner was asked three questions on 3 October 2026: what the Head of Procurement Function and Accounting Officer may see before the Evaluation report is delivered; what they may see after; and which department a meeting counts under. The Project Owner's instruction, verbatim:

> "- sees status only before delivery
> - all details after delivery
> - tender's owning department"

| ID | Decision | Where applied |
|---|---|---|
| OVS-DEC-1 | Before delivery, an overseeing reader sees status only. | §5.2, §5.3 |
| OVS-DEC-2 | After delivery, an overseeing reader sees all details. | §5.2, §5.3 |
| OVS-DEC-3 | A meeting belongs to the Tender's owning department. | §5.8 |

"Delivery" here means the Evaluation committee's signed report being sent to the Head of Procurement Function, the state EVL-CHG-001 v0.4 names **Report sent** (EVL-CHG-001 v0.4 §5.5: "The final required valid signature commits **Report sent** and one durable delivery event for the Head of Procurement."). It does not mean Bid Opening. Applying the same pattern to Bid Opening and Award is a proposal, not an instruction; see OVS-OD-5.

### 1.2 What this document decides, and the earlier items it answers

| # | Item | Source | Disposition in this document |
|---|---|---|---|
| 1 | After the report is delivered and Award has taken over the review, the Head of Procurement Function's evaluation page shows only the committee list and "Report delivered". The decision and the report are not shown. | Observed in the build (Appendix A). EVL-CHG-001 v0.4 §9.8 defines the Head's review board only while the review is open and defines no page for the state after Award takes over (AWD-CHG-001 v0.4 §3, Entry contract). | Replaced by the oversight view (§5.3, §10 OVS-DES-02). |
| 2 | The Accounting Officer has no defined way to read a delivered report. | EVL-CHG-001 v0.4 §3: "Appointment access contains no automatic right to read bids or alter findings." The document is silent on a delivered report. | Resolved by OVS-DEC-2 (§5.3). The EVL-CHG-001 v0.4 §3 sentence about appointment access stands; this adds a right that comes from delivery, not from appointment. |
| 3 | The Tender record links to Bid opening, Bid evaluation and Award but shows nothing from them. | BOP-CHG-001 v0.10 §9; the build's `kt_tender_record_links` hook (Appendix A). TPR-CHG-001 v0.15 §10.17 draws no downstream content. | A "Later stages" section on the Tender record (§5.7, §10 OVS-DES-01). |
| 4 | There is no way to count procurement meetings by type or department. | PRC-CHG-001 v0.10 §2 (Excluded: "reporting dashboards"), §9 ("no menu entry, Home tile, independent register"); BOP-CHG-001 v0.10 §9 ("There is no generic Proceedings menu."). | One read-only register, "Procurement meetings" (§5.8, §10 OVS-DES-03). This lifts the register exclusion only. It adds no scheduling, agenda, resolution, quorum or approval function. |
| 5 | Neither the Proceeding, the Evaluation case nor the Opening case carries a department. | Appendix A. PRC-CHG-001 v0.10 §4: "The owner reference resolves Tender and site context; these are displayed, not independently editable copies." | The department is read from the Tender at read time (OVS-DEC-3); nothing is stored (§4). |
| 6 | A technical reader is shown status only in the build, while EVL-CHG-001 v0.4 §9.10 gives technical readers the D07-SENT content. | Pre-existing; Appendix A. | Not changed here. Reported in §17.3 (C5). |

### 1.3 Open owner decisions

Each has a recommendation. None is encoded as decided; the proposed text in this document follows the recommendation and is marked **(proposed)**.

| ID | Question | Recommendation |
|---|---|---|
| OVS-OD-1 | Which readers other than the Accounting Officer and the Head of Procurement Function gain the oversight read? Candidates: Procurement Officer outside the appointment, Head of User Department. | None. The Auditor already has an oversight read (EVL-CHG-001 v0.4 §3). A Head of User Department is scoped to an Organisation Unit and would need a department-scoped rule, which is a separate change. |
| OVS-OD-2 | What is "a meeting" for counting? | One session actually started: the single opening session of a Bid Opening, and each discussion session of a Bid Evaluation. A planned opening never held is listed as **Not held** and is not counted as held. Signing a report is not a meeting. |
| OVS-OD-3 | How does a cross-department Tender count? A Tender can have several contributing departments (REQ-CHG-001 v1.12 §5.1, `contributing_org_unit_ids`). | Count each meeting once, under the lead department (`lead_org_unit_id`). Show the contributing departments in their own column, and let a department filter match either. The overall total never counts a meeting twice. |
| OVS-OD-4 | Before delivery, may an overseeing reader see facts about an Evaluation meeting (date, duration, number present)? | Yes: these are facts about the meeting, not about the bids. Never the subject, notes, bid names or findings. |
| OVS-OD-5 | Does the same pattern apply to Bid Opening and Award? | Opening: keep BOP-CHG-001 v0.10's own rule (status only before the reveal, contextual read after it) and make the Accounting Officer's read explicit, because BOP-CHG-001 v0.10 §6 does not list it while the build allows it. Award: change nothing; the Tender summary shows only what Award already lets that reader see. |
| OVS-OD-6 | Does "all details" include the bidders' own submitted documents, and may the Accounting Officer download the delivered report? | Yes to both, read-only, through the existing evidence viewer; no bulk export of bids. EVL-CHG-001 v0.4 §9.10 already gives the auditor "Download report". |
| OVS-OD-7 | Should an oversight read of bid detail be logged as an event? | No. TPR-CHG-001 v0.15 §9 and BOP-CHG-001 v0.10 §9 say opening a page creates no business event. A read-access log would be a new stored record and needs a named consumer first (KT-STD-001 §7, Data-purpose gate). |
| OVS-OD-8 | Does Bid Opening get its own list or menu entry? | No. The Procurement meetings register lists openings, and the Tender record links to each opening. |
| OVS-OD-9 | Which meeting types does the register cover? | Only Bid Opening and Bid Evaluation, the two Proceeding types that exist (PRC-CHG-001 v0.10 §20). The site, contract-implementation and review meetings in the earlier Proceedings functional design are outside this change. |
| OVS-OD-10 | Where does the Tender record change go in the version line? TPR-CHG-001 v0.16 is proposed (2 October 2026) and not registered. | A separate TPR-CHG-001 version after v0.16, so v0.16 is not widened. |

### 1.4 New content for review

Everything in this document that does not come from a source is listed here so it can be checked.

| Kind | New content |
|---|---|
| Identifiers | OVS-CHG-001, OVS-DEC-1 to 3, OVS-OD-1 to 10, OVS-DES-01 to 03, OVS-AC-001 onward, OVS-IF-01 to 03 |
| Service and hook names | `GetTenderStageSummaries`, `kt_tender_stage_summaries`, `ListProcurementMeetings` |
| Route and menu | `/app/procurement-meetings`, menu label **Procurement meetings** under Tender Management |
| Screen wording | Every label, sentence and empty-state text in §10 not quoted from EVL-CHG-001 v0.4 |
| Register columns and filters | As listed in §5.8 and OVS-DES-03 |
| State wording | **In session** and **Session ended** for an Evaluation session (§4.2) |
| Placement | The "Later stages" section sits directly after the Tender's current facts (§10 OVS-DES-01) |

---

## 2. Purpose, outcomes and scope exclusions

**Outcome.** An Accounting Officer or Head of Procurement Function can answer, from the system and without borrowing a committee member's access: what happened at the opening; what the committee decided and why; what Award did; and how many meetings of which kind took place in a department.

**Included**

- The oversight read of Bid Evaluation for the Accounting Officer and the Head of Procurement Function (§5.2–5.4).
- The reachability of Bid Opening and Award from the Tender (§5.5, §5.6).
- The "Later stages" section of the Tender record (§5.7).
- The read-only Procurement meetings register (§5.8).
- A shared rule in KT-STD-001 so future stages follow the same pattern (§17.1).

**Excluded**

- Any new command, state, approval, task, hand-off or notification.
- Any change to who may act. This document grants no authority to appoint, sign, return, decide or correct.
- Any change to bid confidentiality before the delivery point.
- Any change to technical-reader behaviour (§17.3, C5).
- Scheduling, agendas, resolutions, quorum, meeting types other than Bid Opening and Bid Evaluation, dashboards, trends or charts. KT-STD-001 v1.14 §2.2 forbids inventing metrics; the register shows counts of recorded meetings only.
- Supplier-facing screens.

---

## 3. Ownership and dependency boundary

Each stage owner keeps its data, its disclosure rule and its screens. This document asks each owner to publish one more read; it does not move ownership.

| Concern | Owner | This document asks for |
|---|---|---|
| Evaluation record, report, who may read it | EVL-CHG-001 | The oversight read (§5.3) and a Report sent view for overseeing readers |
| Opening record and its reader rule | BOP-CHG-001 | The Accounting Officer named as a reader after the reveal; a stage summary |
| Award record | AWD-CHG-001 | A stage summary only |
| Tender record and its sections | TPR-CHG-001 | A "Later stages" section that composes the owners' summaries; the lead department made explicit |
| Proceeding records (sessions, attendance) | PRC-CHG-001 | The Procurement meetings register |
| Cross-cutting rule for overseeing readers | KT-STD-001 | A short shared section |

**Permitted dependency paths.** Tenders calls each owner's published summary read through a hook; it never reads an owner's tables. (The build's `record_links` docstring states the same boundary: "Each owner decides whether this reader may see its link; Tenders reads nothing of theirs." This is an observation, not a rule of TPR-CHG-001 v0.15.) The register calls each owner's published per-row reader verdict; PRC does not decide who may see an Evaluation or Opening row (PRC-CHG-001 v0.10 §6: "The owner applies the stricter disclosure rule at each read").

---

## 4. Canonical domain model

**No stored record or field is added.** Every item below is a read model assembled at request time from existing records. This follows KT-STD-001 §7 (Data-purpose gate and Default to omit).

### 4.1 Stage summary (read model)

Returned by each stage owner for one Tender and one reader. The Tender record shows it; it is never stored by Tenders.

| Field | Meaning | Consumer and validation |
|---|---|---|
| `stage` | One of Bid opening, Bid evaluation, Award | Section heading; fixed list |
| `status_label` | The owner's own plain status wording | Badge; taken from the owner, never composed by Tenders |
| `disclosure` | `status_only` or `full` | Decides whether `facts` carry detail; the owner sets it from §5.2 |
| `facts` | Ordered label and value pairs, each its own fact | Facts grid; the owner returns only facts the reader may see (§10 OVS-DES-01 lists them) |
| `recorded_at` | The recorded instant of the latest material fact | "Recorded" line, in site time (KT-STD-001 v1.14 §3) |
| `route` | The owner's canonical route for this Tender | Action link; absent when the reader cannot open the record |
| `empty` | True when the stage has no record yet | The stage is omitted from the section |

### 4.2 Meeting row (read model)

One row per session actually started, assembled from Proceeding and Proceeding Session (PRC-CHG-001 v0.10 §4 and PRC-CHG-001 v0.10 §20.1) and the owning Tender.

| Field | Source | Consumer and validation |
|---|---|---|
| Type | Proceeding type: Bid Opening or Bid Evaluation | Register column and filter |
| Tender | Owner reference resolved to the Tender | Register column, link |
| Department | The Tender's lead department (`lead_org_unit_id`), read at request time | Register column and filter; see §5.8 |
| Contributing departments | The Tender's `contributing_org_unit_ids`, read at request time | Register column |
| Session number | Order of the session within its proceeding | Register column; 1 for an opening |
| Started, Ended | The trusted session instants | Register columns; never entered by hand (PRC-CHG-001 v0.10 §4) |
| Duration | Ended minus Started | Register column; blank while in progress |
| Present | Count of people recorded present in the session | Register column |
| State | For an opening, the Proceeding state in PRC-CHG-001 v0.10 §5's own words: In session, Session ended, Awaiting attestations, Finalized, Not held, Aborted after start. For an Evaluation session, **In session** or **Session ended** (PRC-CHG-001 v0.10 §20 names no session states; these two words are proposed). | Register column and filter. A meeting counts as held once it has an actual start, which is every state except Pending and Not held. |
| Record route | The owner's route for the proceeding | Row action |

**Why the department is read, not stored.** The lead department is frozen into the Tender when it is created (REQ-CHG-001 v1.12 §5.1 freezes the certified lead in each submitted Version). Copying it onto the Proceeding would create a second value that can drift, which PRC-CHG-001 v0.10 §4 already forbids. Reading it costs one join through the owner reference.

### 4.3 Meeting totals (read model)

Counts by Type and by Department over exactly the rows the reader can see (AUTH-ADR-001 v1.10 §5.4: "Counts shall not disclose records that rows cannot show.").

---

## 5. Lifecycle and business rules

### 5.1 Who is an overseeing reader

The **Accounting Officer** and the **Head of Procurement Function**. Both are site-wide roles (AUTH-ADR-001 v1.10 §4.4; TPR-CHG-001 v0.15 §6). They are readers by responsibility, not by appointment.

- A person who also holds an appointment (for example the Head of Procurement Function as Evaluation secretary) keeps that appointment's access. Rights are the union; this document only adds.
- The **Auditor** already has an oversight read and is unchanged (EVL-CHG-001 v0.4 §3 and EVL-CHG-001 v0.4 §9.10).
- **Administrator and System Manager** are unchanged (§17.3, C5).
- No other role gains anything (OVS-OD-1).

### 5.2 The rule (OVS-DEC-1, OVS-DEC-2)

| Period | An overseeing reader sees |
|---|---|
| Before the delivery point | **Status only.** The stage's state, the next-step answer for that reader, dates and deadlines, and the committee roster. No bidder names, counts, amounts, findings, clarification content, discussion subjects or notes. |
| From the delivery point | **All details**, read-only. Everything a committee member sees in the delivered report and committee record (§5.3). No command, no task, no editable field. |

**The delivery point.** The Evaluation case reaches **Report sent** (EVL-CHG-001 v0.4 §7.1). A report version that has been delivered stays readable for ever, including after a return for correction (EVL-CHG-001 v0.4 §5.6: "The original report and notice stay accessible.").

### 5.3 Bid Evaluation, state by state

"Status only" is as defined in §5.2. "Full" is the read-only content in §5.3.1.

| Evaluation state or condition | Accounting Officer and Head of Procurement Function see |
|---|---|
| Preparing | Status only (unchanged from EVL-CHG-001 v0.4 §9.10). |
| Reviewing, including checks running, clarification, discussion | Status only. |
| Signing | Status only. |
| Report sent, review open or with Award | Full. |
| Returned for correction, case back in Reviewing | Every delivered report version: full. The version being prepared: status only, with a line that says so. |
| Report sent, later opening update or correction notice recorded | Full, including the update or notice. |
| No evaluation required (no bids) | Full: nothing is sealed. This is the content the build already shows. |
| Cancelled before delivery | Status only, plus the cancellation facts (instruction, authority, date, reason). Partial findings stay sealed. |
| Cancelled after delivery | Full; cancellation added as a fact. Delivery is not reversed (EVL-CHG-001 v0.4 §9.1 tracker rule). |
| Suspended (condition) | The state's own rule above, plus the recorded instruction. |
| Delivered report records **No current recommendation — tender validity expired** | Full, showing that wording. |

#### 5.3.1 What "full" contains

Read-only, in the order EVL-CHG-001 v0.4 §9.12 already fixes for the report, with the summary first and signatures last:

1. Tender and committee, including appointment and replacement history and the separate secretary.
2. The opened bid inventory: bidder names and submitted totals.
3. Per-bid eligibility and technical findings with reasons and evidence references.
4. The financial comparison and position.
5. Clarifications and replies, and their dispositions.
6. The committee record: sessions, attendance, attributed conclusions and any recorded disagreement.
7. Due diligence, or its stated basis.
8. The recommendation or outcome, with reasons and qualifications.
9. Signatures, report versions and history, and any correction notice.
10. The supporting evidence, including the bidders' submitted documents, through the existing read-only viewer (OVS-OD-6, **proposed**).

#### 5.3.2 What does not change

- The committee roster, declarations and appointment history stay visible to the Accounting Officer and the Head of Procurement Function in every state, as today, because they do the appointing and secretary assignment.
- A declared conflict's description stays visible to the Accounting Officer, as today.
- A committee-only action (record finding, sign, raise a concern, return) is never offered to an overseeing reader who is not the recipient. The recipient's own review actions (Open report, Return for correction) are unchanged (EVL-CHG-001 v0.4 §9.8, D07-HOP).

### 5.4 After Award takes the review

AWD-CHG-001 v0.4 §3 (Entry contract) turns the Head of Procurement Function's evaluation review into Award's **Prepare professional opinion**. From then the Evaluation page offers the Head and the Accounting Officer the read-only Report sent view of §5.3, and a plain pointer to the Award record. The Evaluation page raises no review task of its own (§5.9).

### 5.5 Bid Opening (OVS-OD-5, proposed)

- Rule unchanged: no pre-opening sealed-box facts to a general reader; contextual read after the reveal (BOP-CHG-001 v0.10 §6, HOPF row).
- BOP-CHG-001 v0.10 §6 does not list the Accounting Officer as a reader after the reveal, but the build allows it (Appendix A). The proposal is to state it, so the document and the build agree.
- Reachability: the opening record is reached from the Tender's "Later stages" section (§5.7) and from the Procurement meetings register (§5.8). No new opening route (BOP-CHG-001 v0.10 §9).

### 5.6 Award

No change to Award's reader rules (AWD-CHG-001 v0.4 §6). Award publishes a stage summary (§4.1) from its own fields and its own disclosure. Its routes are unchanged (AWD-CHG-001 v0.4 §9).

### 5.7 The Tender record's "Later stages" section

- Shown on the internal Tender record for any reader for whom at least one owner returns a summary.
- Each stage appears only once its record exists. Before the opening exists there is no row (BOP-CHG-001 v0.10, the build's link rule).
- A reader sees exactly what the owner returns. If the owner returns `status_only`, the section shows the status and the reason.
- The section replaces the three header buttons "Bid opening", "Bid evaluation" and "Award". Their links move into the section. KT-STD-001 v1.14 §2.9.3 rule 1: "Replace, never add."
- It is not part of the journey tracker. It is a titled working section, a facts grid per stage, with no stepper, timeline or card per stage.
- Reading it creates no event.

### 5.8 The Procurement meetings register

- **Rows.** One per session actually started (OVS-OD-2, **proposed**), meaning a session with an actual start. A planned opening that was never held appears once, state **Not held**, with no start or end, and is not counted as held.
- **Department (OVS-DEC-3).** The Tender's lead department. A Tender with contributing departments shows them in a separate column, and a department filter matches the lead or any contributor (OVS-OD-3, **proposed**). The total counts each meeting once.
- **Readers.** Accounting Officer and Head of Procurement Function (site-wide), Auditor (site-wide or approved oversight scope), and technical readers under KT-STD-001 §3A.6. No other role (OVS-OD-1).
- **What a row shows.** The facts in §4.2. A row never shows a session's subject, notes, a bidder's name, a count of bids or a finding, in any state (OVS-OD-4, **proposed**). The register therefore discloses nothing before delivery that the Evaluation record would withhold.
- **The row's link.** Opens the owner's record. The owner then applies §5.2; the register grants no access to the record.
- **Totals.** By Type and by Department, over the visible rows only (AUTH-ADR-001 v1.10 §5.4).
- **Filters.** Type, Department, State, From date, To date, and a search on Tender reference or title. Totals follow the filters.
- **Scope check.** The register is built through the shared authorisation resolver, never a raw query. AUTH-ADR-001 v1.10 §5.4: "A report that cannot apply the shared conditions is prohibited, not exempt."
- **Empty and error states.** Standard register states (KT-STD-001 v1.14 §3A); a reader without a listed role gets the standard Forbidden panel (§8).

### 5.9 Next steps, hand-offs and My Work

This document adds none (KT-STD-001 v1.14 §3B).

- No new `next_step` kind, holder or primary action.
- Opening an oversight view clears no task. In particular, the Head of Procurement Function's Award task is cleared only by Award's own rules.
- The Procurement meetings register is a Register archetype. It carries no tracker and no next-step block (KT-STD-001 v1.14 §2.9.3 rule 4).

### 5.10 Dead-end matrix

| Screen and state | Reader | Where they can go |
|---|---|---|
| Evaluation, status only | Accounting Officer, Head of Procurement Function | The line says bid details are shared when the report is sent; Back to evaluations; the committee setup actions they already hold. |
| Evaluation, Report sent | Accounting Officer | View report, View committee record, View award (when it exists), Back to evaluations. |
| Evaluation, Report sent | Head of Procurement Function | The same, plus the existing review actions while the review is open. |
| Tender, Later stages, status only | Either | The stage's record, which then shows its own status-only view. |
| Procurement meetings, no rows | Either | Clear filters; the empty state states the filters in force. |

---

## 6. Roles and permissions

| Responsibility | Access added by this document | Limit |
|---|---|---|
| Accounting Officer | Full read of a delivered Evaluation report and committee record; the Later stages section; the Procurement meetings register | Read-only. No bid access before delivery. No new authority. |
| Head of Procurement Function | The same | Read-only beyond their existing review and secretary work. |
| Auditor | The Procurement meetings register and the Later stages section | Unchanged elsewhere. No new export right. |
| Technical reader | The register | Per KT-STD-001 v1.14 §3A.6; the register rows carry no bid content. |
| Everyone else | None | Forbidden panel or protected Not found, as today. |

Authority comes only from AUTH-ADR-001 v1.10 registered hooks and `User Responsibility Assignment`. No Frappe User Permission or role label alone confers any of this.

---

## 7. Service and command contracts

No command is added. All items below are reads; reads create no record, task, decision or event.

| Service | Owner | Required result |
|---|---|---|
| `GetTenderStageSummaries` (hook `kt_tender_stage_summaries`) | Tenders composes; BOP, EVL and AWD each answer | For one Tender and the signed-in reader, the ordered stage summaries of §4.1. Each owner decides its own `disclosure`. A stage the reader may not know exists returns nothing. The existing hook `kt_tender_record_links` stays until the section replaces the buttons, then is retired in the same TPR version. |
| `ResolveEvaluation` | EVL | For an overseeing reader at or after the delivery point, returns the committee, the comparison, the outcome and the report summary a member receives, with no `work` actions. Before the delivery point it returns what it returns today. |
| `ReadEvaluationReport` | EVL | Any overseeing reader may read a delivered report version. A version still being prepared is protected Not found to them. |
| `ReadEvaluationEvidence` | EVL | An overseeing reader may open evidence linked from a delivered report. |
| `ListEvaluationWork` | EVL | The register adds an **Outcome** column for evaluations at or after the delivery point, blank before it. |
| `ListProcurementMeetings` | PRC | Rows and totals of §4.2–4.3 for the signed-in reader and the filters in §5.8. For every row, calls the owner's reader verdict; a row the owner denies is omitted and not counted. |

All reads recheck the active responsibility at the time of the read (AWD-CHG-001 v0.4 §6 states the same recheck rule for Award).

---

## 8. Error contract

No new error code. The existing copy applies:

| Case | Behaviour | Source |
|---|---|---|
| An overseeing reader requests a bid-level or report read before the delivery point | Protected **Not found** with no title or bidder detail | EVL-CHG-001 v0.4 §9.10 (Not found) |
| A reader without a listed responsibility opens the register | The standard Forbidden panel naming the responsibilities that can read: **Accounting Officer, Head of Procurement Function, authorised auditor** | KT-STD-001 v1.14 §3A.4 |
| A guessed URL | No access; the owner's verdict decides | BOP-CHG-001 v0.10 §6 |
| An owner summary cannot be read | That stage shows **We could not load this stage.** with Try again; the other stages still show | New wording (§1.4) |

---

## 9. UI architecture, menu and routes

| Surface | Route | Purpose |
|---|---|---|
| Tender record, Later stages section | `/app/tenders/{tender_id}` | The stage summaries of §5.7 |
| Bid evaluation record | `/app/tenders/{tender_id}/evaluation` | Unchanged route; the oversight view of §5.3 |
| Bid opening record | `/app/tenders/{tender_id}/opening` | Unchanged route |
| Award record | `/app/award/{award_id}` | Unchanged route |
| Procurement meetings | `/app/procurement-meetings` | The register of §5.8 |

**Menu.** One entry, **Procurement meetings**, under Tender Management after **Awards**. No Opening entry (OVS-OD-8). Implementation constraint: check the new route's slug against readable doctype names before binding it, because a Page route loses to a same-named doctype list view.

---

## 10. Static design contract

Supply this section with KT-STD-001 v1.14 §2 and nothing else. **All values are design fixtures**, not evidence of a real procurement event. They use the EVL-CHG-001 v0.4 scenario: Tender `TND-MOH-2027-033`, **Supply and delivery of business laptops**, Afya Digital Supplies Limited, **KES 46,400,000.00**; actors from KT-STD-001 v1.14 §8.3: Amina Hassan (Accounting Officer), Charles Mutiso (Head of Procurement Function), Naomi Chebet (Auditor), Grace Wambui, Peter Mugo and Ruth Achieng (committee), Brian Wafula (secretary). A second department for the register comes from KT-STD-001 v1.14 §8.2; no unregistered department is invented.

### OVS-DES-01 — Tender record, Later stages section

- **Archetype.** A section of the existing Record detail (TPR-CHG-001 v0.15 §10.10), not a page.
- **Primary question.** What has happened to this Tender since it closed for bids?
- **Placement (proposed).** Directly after the Tender's current facts, before the documents row.
- **Replaces.** The header buttons **Bid opening**, **Bid evaluation**, **Award**.
- **Level 1.** Section title **Later stages**.
- **Level 2.** One block per stage that exists, in this order: Bid opening, Bid evaluation, Award. Each block has the stage name, the owner's status badge, a facts grid and one action. Each fact is its own label and value, never joined with a separator.

| Stage | Facts when disclosure is full | Facts when disclosure is status only | Action |
|---|---|---|---|
| Bid opening | Opened (date and time); Bids opened (number); Minutes (owner wording); Committee members (number) | Opening scheduled for (date and time) | **View opening record** |
| Bid evaluation | Committee appointed (date); Report delivered (date and time); Outcome (owner wording); Recommended bidder; Evaluated total; Meetings held (number) | Committee appointed (date); Evaluation deadline (date); line **Bid details are shared with you when the committee's report is sent.** | **View evaluation** |
| Award | Stage (Award's wording); Outcome (Award's wording); Decision recorded (date and time); Notices (Award's wording) | Stage (Award's wording) | **View award** |

- **Level 3.** Nothing beyond the owner's record, reached by the action.
- **Tracker and next-step.** None. This section is not the journey tracker (§5.7).
- **Variants.** Before the opening exists: no section. Only Bid opening exists: one block. Owner summary fails: the block shows **We could not load this stage.** and **Try again**.

### OVS-DES-02 — Bid evaluation record for an overseeing reader

- **Archetype.** Record detail, reusing D07-SENT (EVL-CHG-001 v0.4 §9.8) read-only.
- **Primary question.** What did the committee decide, and on what basis?
- **Report sent variant, Amina Hassan.**
  - Guidance: Done, **The committee report was sent to Charles Mutiso on 16 Jun 2027, 14:07 EAT.** Tracker: Prepare, Review and Report all Done, no holder (EVL-CHG-001 v0.4 §9, tracker rule).
  - Level 2: the report summary of EVL-CHG-001 v0.4 §9.12 (Recommendation: Afya Digital Supplies Limited; Evaluated total: KES 46,400,000.00; Eligibility; Technical compliance; Clarification; Due diligence), then the signature list (Grace 14:05, Peter 14:06, Ruth 14:07). **Report 1** is current.
  - Secondary actions: **View report**, **View committee record**, **Download report**, **View award** (when an Award case exists).
  - New line while Award holds the review: **The report is now with Award.** (replaces the D07-SENT sentence "The Head of Procurement will review the report.", which would be stale).
  - No Complete, Sign, Return or finding action.
- **Report sent variant, Charles Mutiso, review open.** D07-HOP unchanged (Open report primary, Return for correction secondary).
- **Report sent variant, Charles Mutiso, with Award.** The Amina variant, with the guidance headline Done.
- **Status only variant (Reviewing or Signing).** Guidance and tracker as today for that state; the committee roster; the line **Bid details are shared with you when the committee's report is sent.**; Back to evaluations. No bidder, count, amount or finding.
- **Returned variant.** Guidance Waiting on someone, **Waiting for the corrected report.** Report 1 shown read-only with **Report 1 · Returned**; line **Report 2 is being prepared. Report 1 remains available.**
- **Cancelled before delivery.** The cancellation facts (instruction, authority, received, reason); no partial findings.
- **Evaluation workspace (D01).** Adds an **Outcome** column for evaluations at or after the delivery point.

### OVS-DES-03 — Procurement meetings register

- **Archetype.** Register. No tracker, no next-step block.
- **Primary question.** How many meetings of each kind took place, in which department, and where is the record?
- **Level 1.** Title **Procurement meetings**.
- **Level 2.**
  - A totals area: **Meetings held** by Type, then by Department, each its own small table (Department; Bid opening; Bid evaluation; Total).
  - A filter row: **Type**, **Department**, **State**, **From**, **To**, search **Find a tender**; **Clear filters**.
  - The table, one row per meeting, columns: **Type**, **Tender**, **Department**, **Contributing departments**, **Session**, **Started**, **Ended**, **Duration**, **Present**, **State**, **Record**.
- **Level 3.** The owner's record, reached by **View record**.
- **Empty state.** **No meetings match these filters.** with **Clear filters**.
- **Forbidden.** The standard panel naming Accounting Officer, Head of Procurement Function and authorised auditor (§8).
- **Never shown.** A session's subject, notes, a bidder's name, a count of bids, a finding.

---

## 11. Functional interaction requirements — excluded from design prompts

| Control | Destination or operation | Result |
|---|---|---|
| Later stages: View opening record, View evaluation, View award | The summary's `route` | Opens the owner's record; the owner applies §5.2. No event. |
| Later stages: Try again | Re-calls `GetTenderStageSummaries` for that stage | Replaces only that block. |
| Evaluation: View report | `ReadEvaluationReport` for the delivered version | Opens the exact delivered version, read-only. |
| Evaluation: View committee record | Existing committee record read | Read-only. |
| Evaluation: Download report | The existing report download | Allowed to an overseeing reader only for a delivered version. |
| Evaluation: View award | The Award route when a case exists | Absent otherwise. |
| Register: filters, Clear filters | `ListProcurementMeetings` | Rows and totals follow the filters together. |
| Register: View record | The owner's route | The owner applies its own rule. |

Routes preserve context on direct load, refresh and browser back and forward. After a server change the visible page is refreshed in place. A skeleton shows only where the screen has nothing yet.

---

## 12. Audit and historical integrity

- No read adds an audit event (OVS-OD-7).
- Nothing stored changes, so no history is rewritten. The delivered report, its signatures and its digest are unchanged.
- The register shows trusted session instants as recorded; it never edits them.

---

## 13. Seed contract

The canonical seed stages `bid_opening`, `bid_evaluation` and `award` (SEED-OPS-001) are the first fixtures. Missing fixtures are stated as **Awaiting fixture** and added, with their actors drawn from KT-STD-001 v1.14 §8.3.

| Fixture | Needed for |
|---|---|
| A Tender with an opening held and an evaluation in each of Preparing, Reviewing, Signing, Report sent, Returned | OVS-DES-01, OVS-DES-02 |
| A Tender whose evaluation is cancelled before delivery, and one after | §5.3 |
| A Tender with no bids | §5.3 |
| Tenders owned by two different departments | OVS-DES-03 |
| A Tender with contributing departments | OVS-OD-3 |
| An opening that was planned and never held | §5.8 |

**Negative fixtures.** An Accounting Officer and a Head of Procurement Function who are not appointed and not the recipient; a Procurement Officer with no appointment; a Head of User Department; a department-scoped reader with no Evaluation responsibility.

---

## 14. Acceptance contract

| ID | Required result |
|---|---|
| OVS-AC-001 | Before the delivery point, the Accounting Officer and the Head of Procurement Function (neither appointed) see no bidder name, count, amount, finding or clarification content, in the page, the API payload, the report endpoint, the evidence endpoint and a guessed URL. |
| OVS-AC-002 | At the delivery point, the same two readers see the full content of §5.3.1, read-only, without refreshing the session or being appointed. |
| OVS-AC-003 | A delivered report version stays readable after a return for correction; the version being prepared does not, until it is delivered. |
| OVS-AC-004 | After Award takes the review, the Head of Procurement Function's evaluation page shows the report summary, the signatures, View report and a pointer to Award. It no longer shows only the roster. |
| OVS-AC-005 | No overseeing reader is offered a record, sign, raise-a-concern or return action they do not already hold. |
| OVS-AC-006 | Opening an oversight view clears no task and creates no event. |
| OVS-AC-007 | A cancelled-before-delivery evaluation shows cancellation facts and no partial findings to an overseeing reader. |
| OVS-AC-008 | A no-bids evaluation shows its full content to an overseeing reader. |
| OVS-AC-009 | The Tender record shows a Later stages block for each stage that exists and none for a stage that does not. |
| OVS-AC-010 | The three header buttons are gone; each stage's link is in its block. |
| OVS-AC-011 | A reader sees in a block exactly the facts the owner returns, and a status-only block shows the stated line. |
| OVS-AC-012 | One owner failing shows that block's error; the other blocks still show. |
| OVS-AC-013 | The register lists one row per session started, and a never-held opening once as Not held. |
| OVS-AC-014 | The department shown for a meeting equals the Tender's lead department, for every row. |
| OVS-AC-015 | A cross-department Tender appears once in the total, under its lead department, and under a contributing department's filter. |
| OVS-AC-016 | No register row, total or filter result exposes a session subject, note, bidder name, bid count or finding in any state. |
| OVS-AC-017 | Totals equal the number of visible rows under the same filters; a row an owner denies is neither shown nor counted. |
| OVS-AC-018 | A reader without a listed responsibility sees the Forbidden panel, and a Head of User Department sees it too (OVS-OD-1). |
| OVS-AC-019 | The register uses the shared authorisation resolver; a test fails the build if it uses a raw query that skips it. |
| OVS-AC-020 | A technical reader reads the register and sees no bid content. |
| OVS-AC-021 | No stored field or record is added: the data model before and after is identical. |
| OVS-AC-022 | Every state in §5.3 and every row of §5.10 resolves to a screen with a way out. |
| OVS-AC-023 | First paint and at least one interactive re-render are verified on the Tender record, the Evaluation record and the register, signed in as each of Amina Hassan, Charles Mutiso and Naomi Chebet. |
| OVS-AC-024 | The slug of the new route does not collide with a readable doctype list view. |

---

## 15. Implementation and test constraints

- Business rules in Python services; controllers stay thin; no rule in browser code.
- Each owner builds its own summary and its own disclosure; Tenders and the register never read an owner's tables.
- Reuse the `kt_tender_record_links` pattern for the summary hook.
- Tests for disclosure drive the real endpoints as the real personas, not only a service call, so a missed route cannot pass. Run on the test site, not the dev site (the repository's AGENTS.md, section 8.2).
- Follow KT-STD-001 v1.14 §§4–6.

## 16. Prohibited shortcuts

- Deciding "status only" or "full" in the browser.
- Granting an overseeing reader a bid role, an appointment or a User Permission to make the page work.
- Copying the department onto the Proceeding, the Evaluation case or the Opening case.
- Counting a meeting by a raw query that skips the resolver.
- Adding the register to a dashboard, chart or trend.
- Putting a subject, note or bidder name into the register "for context".
- Reading an owner's tables from Tenders or from the register.
- Adding a read-access log without a named consumer.

---

## 17. Traceability and precedence

### 17.1 Required corrections in other documents

None is assumed. Each below must be made as its own approved version.

| Document | Needed version | Section | What must change |
|---|---|---|---|
| KT-STD-001 | v1.15 | New §3A.7 and §12 | State the overseeing-reader pattern once: status only before an owner's delivery point, all details after, read-only, no task, no event. Modules cite it. |
| EVL-CHG-001 | v0.5 | §3 | Add the delivery-based read for the Accounting Officer and Head of Procurement Function beside the appointment sentence. |
| EVL-CHG-001 | v0.5 | §5.5, §7.1 | Define the delivery point as Report sent. |
| EVL-CHG-001 | v0.5 | §9.8, §9.10 | Add the overseeing-reader variants of OVS-DES-02, including the state after Award takes the review. |
| EVL-CHG-001 | v0.5 | §9.2 (D01), §10 | Add the Outcome column and the View report, View award controls. |
| EVL-CHG-001 | v0.5 | §11.3 | Add OVS-AC-001 to 008 equivalents. |
| BOP-CHG-001 | v0.11 | §6 | Name the Accounting Officer as a reader after the reveal. |
| BOP-CHG-001 | v0.11 | §9 | Reword "There is no generic Proceedings menu" to allow the Procurement meetings register; state the Later stages link. |
| PRC-CHG-001 | v0.11 | §2, §9 | Lift the "reporting dashboards" and "independent register" exclusions for one read-only register; keep every other exclusion. |
| PRC-CHG-001 | v0.11 | §6, §7, §20.1 | Add the register readers, `ListProcurementMeetings` and its owner-verdict rule. |
| AWD-CHG-001 | v0.5 | §9 | Add the stage summary. No disclosure change. |
| TPR-CHG-001 | after v0.16 | §4.1 | State `lead_org_unit_id` and `contributing_org_unit_ids` as Tender facts (Appendix A: the build holds them; the document does not list them). |
| TPR-CHG-001 | after v0.16 | §7.1, §9, §10.10, §10.17 | `GetTender` returns stage summaries; add the Later stages section; reconcile with the §10.17 statements in §17.3 (C4). |
| SEED-001 / SEED-OPS-001 | next | Fixtures | Add the fixtures of §13. |
| Baseline register KT-DOC-CTRL-001 | on approval | Documents, interfaces, decisions, delivery items | Add OVS-CHG-001; add interfaces OVS-IF-01 (Tenders to stage owners), OVS-IF-02 (EVL oversight read), OVS-IF-03 (PRC register to owners); record OVS-DEC-1 to 3; add delivery items. Next free identifiers to be taken from the register. |

### 17.2 Precedence

KT-STD-001 v1.14 prevails on any rule it states. Each owner document prevails on its own data and disclosure until its corrected version is approved; where this document and an unchanged owner document differ, the owner document stands and the difference is reported, not silently resolved.

### 17.3 Conflicts and discrepancies found

| ID | Conflict or discrepancy | Handling |
|---|---|---|
| C1 | EVL-CHG-001 v0.4 §3: "Appointment access contains no automatic right to read bids or alter findings." against OVS-DEC-2 | Not a contradiction if read as appointment-based. Needs the EVL v0.5 wording of §17.1. |
| C2 | PRC-CHG-001 v0.10 §2 and §9 exclude a register and dashboards | This document lifts the register exclusion only. Needs PRC v0.11. |
| C3 | BOP-CHG-001 v0.10 §9: "There is no generic Proceedings menu." | The register is a read-only list, not a Proceedings workspace; wording needs BOP v0.11. |
| C4 | TPR-CHG-001 v0.15 §10.17: "No upstream/downstream link is supplied for these artboards; draw none." and "No separate card, timeline or task-navigation stepper is drawn." | Those statements govern the journey tracker. The Later stages section is a working section, not a tracker, stepper or per-stage card. The owner must confirm that reading (OVS-OD-10). |
| C5 | EVL-CHG-001 v0.4 §9.10 gives technical readers the D07-SENT content; the build shows technical readers status only (Appendix A) | Pre-existing, not changed here. For the documentation owner. |
| C6 | BOP-CHG-001 v0.10 §6 does not list the Accounting Officer as an opening reader; the build allows it | OVS-OD-5. |
| C7 | TPR-CHG-001 v0.15 §4.1 does not list the lead or contributing department; the build holds both | Appendix A is an observation, not a rule. TPR needs to state them. |
| C8 | The register lists TPR-CHG-001 v0.15 as current; `KenTender_TPR-CHG-001_Tenders_v0_16.md` exists as a proposed version and is not registered | Pre-existing. For the documentation owner. |

---

## 18. Approval effect

Approval of v0.1 would authorise: the oversight read for the Accounting Officer and the Head of Procurement Function after the Evaluation delivery point; the Later stages section; the Procurement meetings register; and the shared rule of §17.1 as proposed corrections to be made in their own versions. It would not by itself change any owner document, create any record, establish implementation, test success or release, or approve any open decision in §1.3 not stated by the Project Owner.

Implementers must not retain, once the corrected owner documents are approved: the "setup only" view as the whole of a delivered report for an overseeing reader; the three header buttons on the Tender record; or any department value copied onto a Proceeding or case.

---

## Appendix A — Observations from the build (not rules)

Recorded 3 October 2026 from the repository at branch `mvp1/dev`. These show why the problem occurs. They are observations, not requirements, and none becomes a rule without the Project Owner's decision.

| # | Observation | Where |
|---|---|---|
| A1 | An Evaluation reader is a "bids" reader only if eligible, secretary or auditor and not technical. The Accounting Officer and Head of Procurement Function can read the case but are not bids readers. | `kentender_procurement/kentender_procurement/bid_evaluation/services/reads.py`, `access()` |
| A2 | The comparison, discussion items and outcome are built only for bids readers. | same file, `resolve()` |
| A3 | Any reader without bids access is routed to the "setup only" view, which shows the roster and the text "Report delivered". | `public/js/bid_evaluation/screens/index.js`, `pick()`; `screens/record.js`, `setupOnly()` |
| A4 | The Done sentence "The committee report was sent to …" carries no action, so no View report button is offered after Award takes the review. The recipient can still read the report because `access()` allows a delivered recipient. | `bid_evaluation/services/next_steps.py`, around line 169; `reads.py`, `access()` |
| A5 | The Tender record's links come from `kt_tender_record_links`, which returns only a label and a route. | `hooks.py` (line 146); `bid_opening/desk_links.py`; `bid_evaluation/desk_links.py`; `award/desk_links.py`; `tenders/services/read.py`, `record_links()` |
| A6 | The opening reader roles include the Accounting Officer. | `bid_opening/services/reads.py`, `READER_ROLES` |
| A7 | The Proceeding record has an owner type and owner ID but no department; the Evaluation, Opening and Award case records carry the Tender reference and title but no department. The Tender record holds `lead_org_unit` and `contributing_org_unit_ids`. | the doctype definitions of Proceeding, Evaluation Case, Bid Opening Case, Award Case and Tender |
| A8 | A repository search found no register or cross-tender read of Proceeding records. Hits in other modules were not inspected. | repository search |
| A9 | The sidebar under Tender Management lists Tenders, Evaluation and Awards. | The Project Owner's screenshot of 3 October 2026; the sidebar definition file was not read |

## Appendix B — Documents read for this change

**Read in full:** none of the owner documents was read end to end in this session.

**Read in part (sections named):**

| Document | Sections read |
|---|---|
| EVL-CHG-001 v0.4 | Control table; sections 1, 3, 5.5, 6, 7.1 (partly), 9.8, 9.10, 9.12; section 10 (interaction map, partly) |
| BOP-CHG-001 v0.10 | Control table; sections 6, 8 (partly), 9, 10.6, 17 |
| PRC-CHG-001 v0.10 | Control table; sections 1, 2, 4, 5, 6, 9, 20.1, 20.3 |
| AWD-CHG-001 v0.4 | Control table; sections 3 (Entry contract), 5.9, 6, 9 |
| TPR-CHG-001 v0.15 | Control table; sections 4.1, 6, 7.1, 9, 10.10, 10.17 |
| KT-STD-001 v1.14 | Control table; sections 2.9.3, 3A.6, 3B.2, 7, 8.2, 8.3 |
| AUTH-ADR-001 v1.10 | Sections 4.3, 4.4, 5.4 |
| REQ-CHG-001 v1.12 | Section 5.1 (the department fields) |
| KT-DOC-CTRL-001 | Document list and structure |

**Not read:** the rest of each document above; TPR-CHG-001 v0.16 (identified as proposed, its content not read); the earlier Proceedings functional design except its headings and excluded-scope statements; SEED-001 v1.3 and SEED-OPS-001 v1.21; STD-TPL, BDS, CTX-CHG-001 and the register's interface, decision and delivery-item entries. The legal sources were not consulted; this document states no legal proposition.
