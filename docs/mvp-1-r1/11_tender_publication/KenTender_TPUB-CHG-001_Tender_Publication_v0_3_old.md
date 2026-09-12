# TPUB-CHG-001 — Tender Publication

| Control | Value |
|---|---|
| Document ID | TPUB-CHG-001 |
| Version | 0.3 |
| Date | 10 September 2026 |
| Status | Proposed for approval |
| Supersedes | v0.2, approved 10 September 2026 — superseded in full by this domain correction; re-approval required |
| First product | `IT-EQUIPMENT-OPEN-V1` — the same installed template TPR-CHG-001 uses; this module renders nothing new |
| Starts from | One immutable `TenderPublicationHandoff v1.1`, per TPR-CHG-001 v0.7 (pending re-approval) |
| Ends at | One published Tender, open for its configured tendering period, or one cancelled Tender — never a bid, never an opening |
| Standards | Governed by KT-STD-001 v1.3 and STD-STD-001 v1.1. Sections not restated here are inherited from them. |
| Implementation authority | None. This document does not authorise code, migration, deployment or production use. |
| Change type | Full audit against KT-STD-001, not just the sections already checked: §12.8's state table split states across three separate tables and wrote two-sentence messages, both undeclared departures from §11's one-sentence rule and from the single State/Message/Action table TPR-CHG-001 §13.9 already uses — rebuilt as one table matching that pattern, and `TPUB_THRESHOLD_UNRESOLVABLE` recategorised from a generic error to Not-configured, per §3A.1's four-state page model. The same audit found this document's overall section numbering — and TPR-CHG-001's, which it was built from — does not match KT-STD-001 §7's canonical 18-section skeleton, undeclared; not fixed here, since resequencing this document alone would diverge further from its sibling documents rather than less — flagged in §21 pending a decision that affects more than this file. Earlier: several artboards described list content as "one row: X · Y · Z" with no table or column headers ever specified — fixed in the workspace's two sections and the detail view's Addenda and Inquiries lists, each now a named-column table; §12.8 was first built as a paragraph citing KT-STD-001 §3 for content that section explicitly delegates back to this document, rather than actually supplying it. Earlier (v0.2): replaced Addendum's single free-text field with structured `affected_area`/`affected_reference`/`previous_text`/`revised_text`/`reason`, checked against live values at issuance; rebuilt the Authorise Publication screen to show what is being procured, the full readiness result and warning set, the approval trail, and links to the actual documents, instead of four shallow fields; extended the same six requirement panels TPR-CHG-001 §13.5 shows at Tender Prep approval to both the Authorise and detail screens, in place of a bare count. Earlier still (v0.1): established the module. |

## 1. Governing decision

Tender Publication is the first module downstream of Tender Preparation, and the first point in the KenTender chain where the Accounting Officer — not the Head of Procurement Function — is the statutorily named actor. Four things were settled in scoping, before this document was drafted, and are treated here as fixed:

| Decision | Why |
|---|---|
| Scope stops at "published, waiting." Tender opening, bid submission and evaluation are separate future modules. | Tender opening is a large, formal, separately-actored statutory event (Act §78) with its own committee; folding it into Publication would blur two different bodies of law into one module. |
| The existing site-wide Accounting Officer actor, Amina Hassan (KT-STD-001 §8.3), is reused. No new registry actor is created. | She is already load-bearing — PLN-CHG-001 already has her performing "Accounting Officer adoption" as an explicit, timestamped action, not a passive accountability field. Publication follows that precedent rather than inventing a second pattern. |
| Advertisement (Act §96) and document provision (Act §98) are statutorily the Accounting Officer's, not the Head of Procurement Function's. Modelled here as an explicit action — **Authorise publication** — mirroring the PLN-CHG-001 precedent above, with Charles Mutiso and Brian Wafula still doing the operational preparation underneath it per Regulation 33(3)(d). | The Act names her; Regulation 33 names the procurement function's operational role. Both are real and both are modelled — one as an action, one as the work behind it. |
| Cancellation authority (Act §63) reaches across the full pre-award span — Bid Submission, Tender Opening and Evaluation, not just Publication's own window — even though this document can only implement the part it can see. | §63(1) reads "at any time, prior to notification of tender award." Publication's own end-state does not bound the statute; a later module must plug into the same command, not build its own. |

Two things checked directly against the Second Schedule and found unresolvable from source rather than assumed:

- The exact Kshs thresholds for national and international advertising are not stated as numbers in this document. Three direct attempts at the primary source (Kenya Law's consolidated Act and Regulations, and Treasury's own gazetted PDF) returned every surrounding section correctly but not the Second Schedule table itself. Rather than substitute a superseded figure — an old 2006 threshold matrix under the repealed 2005 Act surfaced during this research, using different section numbers entirely, and is not used here — the threshold is treated as **configuration**, read from CFG-CHG-002 at the moment of authorisation. See §7.2 and §21.
- International tendering (Act §89) is out of scope. Nothing in the current chain — SEED-001, REQ-CHG-001, TPR-CHG-001 — models a procurement where domestic competition is judged insufficient, and this document does not introduce that judgement.

## 2. Purpose and scope

### 2.1 Included

- Consuming one `TenderPublicationHandoff v1.1` and calling `AcknowledgeTenderPublicationConsumed`, closing the contract TPR-CHG-001 §9.5 has held open since v0.5.
- One explicit Accounting Officer action, **Authorise publication**, that determines the applicable advertising channels from the configured threshold, publishes the Invitation and issued Tender through them, and sets `publication_consumed_at`.
- Addenda to a published Tender (Act §75), including the mandatory deadline extension when an amendment lands inside the final third of the remaining preparation time, and the duty to respond to a candidate's inquiry about an addendum without naming the source (Regulation 56).
- Cancellation (Act §63): the Accounting Officer's decision, the Head of Procurement Function's optional recommendation (Regulation 48(1) — "may," not "shall"), the PPRA report, and publication of the cancellation through the same channels the tender was advertised on (Regulation 49(1)(p)).
- The one write path back to Planning this module triggers: `PublishTenderMilestoneActual` for `actual_invitation_date`, exactly as TPR-CHG-001 §9.5 already defines it — this document does not redefine that contract, only becomes its caller.

### 2.2 Excluded

- Bid submission, the electronic tender box, and everything the Bidder Workspace's own screens already cover on the supplier-facing side. This document does not redesign Screens A–D; it names where its own output — the published Invitation and issued Tender — must reach them, and leaves the reconciliation as a named dependency in §21.
- Tender opening (Act §78): the committee, the register, the minutes, the three-password electronic tender box (Regulation 57(2)). A documented deferral, per the scoping discussion.
- Evaluation, award, and every milestone from `actual_bid_opening_date` onward. Unchanged from TPR-CHG-001 §9.5's own boundary.
- General informal candidate-PE communication. The Regulations name exactly one structured inbound channel before submission — Regulation 56's inquiry-about-an-addendum mechanism — and this document builds only that one. It does not invent a general-purpose question-and-answer feature the primary source does not require.
- International tendering (Act §89), restricted tendering, and every method other than Open Tender. Matches every other document in this chain.
- A named individual tenderer-notification path for cancellation. Reachable in principle once Bid Submission exists; unreachable in this release because nothing yet produces a named tenderer to notify. See §7.5 and §21.

## 3. Simple journey

1. Tender Preparation approves a Tender. `TenderPublicationHandoff v1.1` is created, unconsumed.
2. The Accounting Officer authorises publication. KenTender determines the advertising channels from the configured threshold, publishes the Invitation and issued Tender through them, and acknowledges consumption — closing TPR-CHG-001's waiting contract and writing `actual_invitation_date` to Planning.
3. The Tender sits open for its configured tendering period. Zero or more addenda may be issued during this window; each is published the same way the Tender itself was.
4. Either the tendering period runs its course — ownership passes to Bid Submission, not yet built — or the Accounting Officer cancels, which this document handles start to finish for the pre-submission case.

There is no fifth step. Publication does not touch a bid, because none exists yet.

## 4. Responsibility boundary

| Information or action | Owner | Publication's treatment |
|---|---|---|
| Tender content, schedules, evaluation and contract contracts | `TenderPublicationHandoff v1.1` | Inherit read-only and immutable. Publication renders and distributes; it never edits a value the handoff carries. |
| Advertising channel determination | Configured threshold, CFG-CHG-002 | Resolved automatically at authorisation from the Tender's authorised value against the effective-dated threshold. Not an officer judgement call. |
| Decision to publish | Accounting Officer | One explicit, attributed action — **Authorise publication** — per §1's precedent from PLN-CHG-001. |
| Advertisement production and distribution | Head of Procurement Function / Procurement Officer | Operational execution under Regulation 33(3)(d): the system generates the listing and files; Charles or Brian confirm it went out through every required channel. |
| Addendum content | Head of Procurement Function | Drafted by either officer, issued by Charles, per the same asymmetry TPR-CHG-001 already uses between them. |
| Cancellation decision | Accounting Officer | Sole decision-maker, per Act §63(1). |
| Cancellation recommendation | Head of Procurement Function | Optional input, per Regulation 48(1); never required, never binding. |
| PPRA termination report | Accounting Officer, via the procurement function | Tracked as a compliance deadline (14 days, Act §63(2)) inside this module; actual transmission to PPRA is outside KenTender's system boundary in this release. |
| Milestone-actual write-back | TPR-CHG-001 §9.5 | Publication triggers it by setting `publication_consumed_at`; it does not reimplement it. |

## 5. Roles and permissions

No new actor. Both roles this module uses are already in KT-STD-001 §8.3:

- **Accounting Officer** (Amina Hassan, site-wide) — authorises publication; decides cancellation.
- **Head of Procurement Function** (Charles Mutiso, site-wide) — issues addenda; may recommend cancellation; confirms operational distribution.
- **Procurement Officer** (Brian Wafula, site-wide, Tender Preparation and Publication) — may draft addendum content for Charles to issue. This is the same actor TPR-CHG-001 v0.5 added; his scope note is extended here from "Tender Preparation only" to also cover Publication, since the officer preparing a Tender is the natural person to also spot when it needs correcting mid-window. See §21 for the KT-STD-001 registry text this requires.

No Frappe User Permission, capability profile or operational-scope assignment participates in any authorization decision in this module, matching every document in this chain since AUTH-ADR-001 v1.6.

## 6. Installed dependency

### 6.1 What this module consumes

One `TenderPublicationHandoff v1.1`, exactly as TPR-CHG-001 §7.6 defines it: Tender, Version, Requisition handoff and template binding; every inherited requirement snapshot and stable ID; every officer value and generated schedule; the Invitation and issued-Tender files and their digests; the structured supplier-response schema; the evaluation contract; the contract-obligation projection; the readiness result and warning set; the approval decision; and the package digest.

Publication treats every one of these as read-only. It adds a publication record alongside the handoff; it does not open the handoff itself.

### 6.2 Compatibility test

| Check | Requirement |
|---|---|
| Handoff status | Approved, unconsumed. A consumed handoff cannot be authorised twice — see TPUB-AC-002. |
| Handoff digest | Matches the digest recorded at Tender approval. A mismatch blocks authorisation as a Blocking finding, never a silent republish. |
| Advertising threshold configuration | Resolvable for the Tender's authorised value at the moment of authorisation, per CFG-CHG-002. Unresolvable configuration blocks authorisation; it is never defaulted to "below threshold" by omission. |
| Tendering-period configuration | The Plan Item's `tendering_period_days` (PLN-CHG-001 §4) is readable. Publication does not compute this value; it reads what Planning already governs. |

## 7. Canonical domain model

### 7.1 TenderPublication

| Field | Control and rule |
|---|---|
| `publication_id` | Generated, read-only. |
| `tender_version_id` | Required Link to the one approved Tender Version. Unique — at most one active TenderPublication per Version, mirroring TPR-CHG-001's own "at most one active Tender consumption" invariant. |
| `handoff_digest` | Copied from the handoff at authorisation; immutable afterward. |
| `authorised_by` | The Accounting Officer who authorised publication. Read-only once set. |
| `authorised_at` | Read-only once set. |
| `advertising_threshold_snapshot` | The configured threshold value CFG-CHG-002 held at authorisation, copied in — not a live reference. Configuration changing next year must never silently reclassify a Tender already published. |
| `advertising_channels` | Generated Set: `State Portal`, `Own website`, `Notice board`, and, only when the authorised value meets or exceeds the snapshot threshold, exactly one of `Two national newspapers`, `Two TV and two radio stations`. Never officer-selected. |
| `publication_consumed_at` | Set exactly once, atomically with the channel determination above. Triggers TPR-CHG-001 §9.5. |
| `tendering_period_days` | Copied read-only from the Plan Item at authorisation, for display only — Planning remains the owner of the schedule itself. |
| `status` | `Published`, `Cancelled`. Generated, never directly set. |

### 7.2 Advertising threshold — configuration, not a stored constant

CFG-CHG-002 owns one effective-dated value: the national advertising threshold, per Act §96(2) and Regulation 85(1)'s Second Schedule. Publication reads it; it does not define it, cache it beyond the one snapshot in §7.1, or fall back to a hardcoded number if it is missing. This is a required addition to CFG-CHG-002 — see §21.

### 7.3 Addendum

| Field | Control and rule |
|---|---|
| `addendum_id` | Generated, read-only, sequential per Tender. |
| `publication_id` | Owning TenderPublication. |
| `affected_area` | Required Select: `Invitation detail`, `Technical requirement`, `Goods/delivery schedule`, `Submission or opening detail`, `Evaluation or contract term`, `Other`. A structured statement of which part of the issued package this addendum touches — never left implicit in free text. |
| `affected_reference` | Required. When `affected_area` names a structured handoff row, this is that row's exact stable ID (`technical_requirement_id`, a goods-schedule line, an evidence requirement ID). When it does not — a location inside the Invitation's prose, for instance — this is a required exact reference to that location (section and paragraph), still not free-floating. |
| `previous_text` | Required text: exactly what the affected area said before this addendum. Where `affected_reference` resolves to a handoff-owned row, this must match that row's current published value — checked, not merely asserted by the officer. |
| `revised_text` | Required text: exactly what it says after. |
| `reason` | Required text, distinct from the correction itself. What was wrong, not just what changed. |
| `issued_by` | Head of Procurement Function. Required. |
| `issued_at` | Read-only once set. |
| `deadline_extension_triggered` | Generated Yes/No: Yes when `issued_at` falls within the final third of the remaining time to the current submission deadline, or later, per Act §75(5). |
| `revised_submission_deadline` | Generated only when triggered. Publication proposes the extension; it does not silently apply one without recording why. |

An addendum is a structured correction to one identified thing, not a notice. `content` as a single free-text field — v0.1's original shape — could describe any change to anything, which meant `TPUB_INVALID_...` had nothing checkable to reject against and a reader had no way to know what actually changed without parsing prose. `affected_area` and `affected_reference` give the same enforcement TenderEvidenceRequirement already has in TPR-CHG-001 §7.4 — a link to something real, not a description of something real.

### 7.4 Inquiry

| Field | Control and rule |
|---|---|
| `inquiry_id` | Generated, read-only. |
| `addendum_id` | Required Link. An Inquiry exists only about an Addendum — Regulation 56(1)'s own scope, not a general question box. |
| `question` | Required text, from a candidate. How a candidate submits one is outside this document's boundary — see §21. |
| `response` | Required text. |
| `affects_requirements` | Required Yes/No, set by the responding officer. |
| `published_to_all_candidates` | Generated Yes, only when `affects_requirements` is Yes, per Regulation 56(2) — copied to every candidate without naming the source. |

### 7.5 Cancellation

| Field | Control and rule |
|---|---|
| `cancellation_id` | Generated, read-only. |
| `publication_id` | Owning TenderPublication. Setting this closes it — `status` becomes `Cancelled`, terminal. |
| `ground` | Required Select, the exact eight grounds Act §63(1)(a)–(i) lists. Not free text — a cancellation with no listed ground is not a cancellation this module permits. |
| `reason` | Required text, the specific circumstances. |
| `recommended_by` | Optional Link to Head of Procurement Function, per Regulation 48(1). Absence is valid. |
| `decided_by` | Required Link to Accounting Officer. |
| `decided_at` | Read-only once set. |
| `ppra_report_due_by` | Generated: `decided_at` + 14 days, per Act §63(2). Tracked as a compliance deadline; KenTender does not transmit to PPRA in this release. |
| `candidate_notice_due_by` | Generated: `decided_at` + 14 days, per Act §63(4). |
| `tenderer_notice_status` | Generated: `Not applicable — no tenderers exist` in every fixture this release, since Bid Submission does not exist yet. |

## 8. Officer actions

### 8.1 Authorise publication

The Accounting Officer's one action. Preconditions: the compatibility test in §6.2 passes with zero Blocking findings.

On confirmation, the system, atomically:

1. resolves the advertising threshold snapshot and channel set, per §7.1–7.2;
2. publishes the Invitation and issued Tender to every resolved channel — State Portal and own website are system-executed; notice-board posting and, above threshold, newspaper or broadcast placement are recorded as confirmed by the Head of Procurement Function, since KenTender cannot itself post a physical notice or place a broadcast advertisement;
3. creates the TenderPublication record; and
4. calls `AcknowledgeTenderPublicationConsumed`, setting `publication_consumed_at` and triggering TPR-CHG-001 §9.5.

No partial publication exists. A failure at any step leaves the handoff unconsumed and no TenderPublication record behind.

### 8.2 Issue addendum

Available only while `status` is `Published`. The Head of Procurement Function issues; the Procurement Officer may draft `affected_area`, `affected_reference`, `previous_text`, `revised_text` and `reason` for Charles to review and issue. `previous_text` is checked against the affected row's current published value where `affected_reference` names a structured one — a mismatch blocks issuance, since it means the officer is correcting something that has already changed underneath them. On issuance, the system re-publishes the affected document through every channel the original Tender used — not a subset chosen per addendum — and evaluates the deadline-extension rule in §7.3 automatically.

An addendum cannot alter the substance of the tender, per Act §75(1). Publication does not evaluate "substance" as a judgement call; it enforces the one thing it can check mechanically — `affected_reference` can never point at a field the handoff itself owns as immutable content (§6.1). Adding a missing internal delivery point to an already-correct address is in scope; rewriting a technical requirement is not an addendum, it is the upstream correction route in TPR-CHG-001 §10.4.

### 8.3 Respond to inquiry

Available only against an existing Addendum. If the response affects requirements, the system copies it to every candidate without disclosing who asked, per Regulation 56(2). If it does not, the response is recorded but not separately broadcast — Regulation 56(2)'s copy duty applies specifically to responses that affect requirements, not every reply.

### 8.4 Cancel

Available while `status` is `Published`. The Accounting Officer selects one of Act §63(1)'s eight grounds, gives a reason, and may first receive Charles's recommendation — never required. On decision, the system publishes the cancellation notice through every channel the Tender was advertised on (Regulation 49(1)(p)), sets both 14-day compliance deadlines (§7.5), and closes the TenderPublication as `Cancelled`, terminal. Reopening a cancelled Tender is not a Publication command — a cancelled procurement that still needs to happen starts over in Tender Preparation.

## 9. Readiness and lifecycle

### 9.1 Lifecycle

| Current state | Action | Actor | Result |
|---|---|---|---|
| Approved, handoff unconsumed | Authorise publication | Accounting Officer | Creates the TenderPublication, publishes through every resolved channel, consumes the handoff. |
| Published | Issue addendum | Head of Procurement Function | Creates an Addendum, re-publishes, evaluates the deadline-extension rule. |
| Published, addendum exists | Respond to inquiry | Head of Procurement Function or Procurement Officer | Records the response; copies to all candidates if it affects requirements. |
| Published | Cancel | Accounting Officer | Closes the TenderPublication as `Cancelled`; publishes the cancellation; sets both compliance deadlines. |
| Published | — | System | At the configured submission deadline, ownership passes to Bid Submission — not yet built. Publication defines no command for this transition; there is nothing yet on the other side to hand off to, the same open seam TPR-CHG-001 §9.5 already lives with. |

### 9.2 Core invariants

- At most one active TenderPublication per Tender Version.
- `publication_consumed_at` is set exactly once; a repeated authorisation attempt against an already-consumed handoff is rejected, not silently accepted.
- An addendum never edits a field the handoff owns; it is a new record, never a patch to inherited content.
- A cancellation is terminal. No command reopens it.
- Every advertising-channel determination is generated from configuration at the moment of authorisation, never officer-selected, never defaulted.

## 10. Services, commands and errors

| Command | Actor | Preconditions | Effect |
|---|---|---|---|
| `AuthorisePublication(tender_version_id)` | Accounting Officer | §6.2 compatibility test passes | Per §8.1. |
| `IssueAddendum(publication_id, content)` | Head of Procurement Function | `status = Published` | Per §8.2. |
| `RespondToInquiry(addendum_id, question, response, affects_requirements)` | Head of Procurement Function, Procurement Officer | Addendum exists | Per §8.3. |
| `CancelPublication(publication_id, ground, reason, recommended_by?)` | Accounting Officer | `status = Published` | Per §8.4. |
| `AcknowledgeTenderPublicationConsumed(tender_version_id, publication_date, correlation_id)` | System, internal | Called once, from within `AuthorisePublication` | Satisfies TPR-CHG-001 §9.5's contract exactly as that document defines it. |

### 10.1 Errors

| Code | Trigger |
|---|---|
| `TPUB_HANDOFF_ALREADY_CONSUMED` | `AuthorisePublication` against a handoff with an existing TenderPublication. |
| `TPUB_HANDOFF_DIGEST_MISMATCH` | The stored handoff digest no longer matches what Tender Preparation approved. |
| `TPUB_THRESHOLD_UNRESOLVABLE` | CFG-CHG-002's advertising threshold cannot be read for the Tender's authorised value. Never defaults; always blocks. |
| `TPUB_NOT_PUBLISHED` | `IssueAddendum` or `CancelPublication` against a TenderPublication that is not `Published`. |
| `TPUB_ADDENDUM_NOT_FOUND` | `RespondToInquiry` against a non-existent Addendum. |
| `TPUB_ADDENDUM_STALE_REFERENCE` | `IssueAddendum`'s `previous_text` does not match `affected_reference`'s current published value — the officer is correcting something that has already changed. |
| `TPUB_INVALID_CANCELLATION_GROUND` | `CancelPublication` with a ground outside Act §63(1)'s eight listed grounds. |

### 10.2 Consistency and audit

- Every command is idempotent by a caller-supplied idempotency key, matching KT-STD-001's universal convention.
- `authorised_by`, `issued_by` and `decided_by` are drawn from the acting session's own `User Responsibility Assignment`, never a free-text or selected field — the same registered-permission-hooks model AUTH-ADR-001 v1.6 established and TPR-CHG-001 v0.5 already adopted.

## 11. UI architecture and routes

Publication is deliberately thin. There is no five-task workspace here — one authorisation screen, one addendum form, one cancellation form.

| Route | Purpose |
|---|---|
| `/tender-publication` | Workspace: Tenders with an unconsumed handoff, awaiting authorisation; Tenders currently published. |
| `/tender-publication/:id/authorise` | The one Accounting Officer action, §8.1. |
| `/tender-publication/:id` | Published Tender detail: channels used, addenda issued, inquiries answered. |
| `/tender-publication/:id/addendum/new` | §8.2. |
| `/tender-publication/:id/cancel` | §8.4. |

No route in this module renders the Invitation or issued Tender itself — those are STD-TPL-001's render outputs, consumed and distributed here, never re-rendered.

## 12. Static Claude Design contract

### 12.1 Global rules

Create only the screens and dialogs listed below at 1440 × 1024; dialogs at 520 px over a dimmed parent artboard. Use the exact control types, labels, editability and fixture values stated. Do not add dashboards, charts, comments, count cards, a Procuring Entity row or column, or any field not defined here.

Read-only inherited values appear as plain values with the caption **From approved Tender**. Generated values (advertising channels, deadline-extension results, both compliance deadlines) appear as plain values, never editable or disabled inputs — per KT-STD-001 §2.2, generated identifiers and generated results may be displayed but never rendered as fields a user could mistake for input.

### 12.2 Shared Ministry of Health fixture

Continues TPR-CHG-001 §13.2's fixture exactly. Fixture context — actor, identifier, timestamp and breadcrumb — is data outside every artboard below, confirming location only; it is never rendered.

| Context | Exact value |
|---|---|
| Tender | `TND-MOH-2027-033` |
| Authorised value | KES 50,000,000.00 |
| Approved | 20 Apr 2027, by Charles Mutiso |
| Accounting Officer | Amina Hassan · `amina.hassan@moh.example.test` |
| Advertising channels (resolved) | State Portal, Own website, Notice board, Two national newspapers |
| Tendering period | 21 days |

### 12.3 TPUB-DES-01 — Tender Publication workspace

Fixture context — outside the artboard: Amina Hassan · Accounting Officer · 20 Apr 2027, 10:05 EAT · Frappe header breadcrumb: **Home > Tender Publication**

Title **Tender Publication**. Subtitle **Publish approved Tenders and manage them while open.**

Two sections. Each is a table with the named columns below — not a bulleted list, not a card grid; "one row" in earlier drafts of this document meant one row of a table that was never actually specified, which is exactly the ambiguity this revision closes.

1. **Awaiting authorisation.** Visible only to the Accounting Officer.

   | Tender | Item | Authorised value | Approved | Readiness | Action |
   |---|---|---:|---|---|---|
   | `TND-MOH-2027-033` | Business laptops, 250 Each | KES 50,000,000.00 | Charles Mutiso, 20 Apr 2027 | 0 Blocking · 1 Warning | **Authorise Publication** |

2. **Published.**

   | Tender | Item | Authorised value | Published | Channels |
   |---|---|---:|---|---|

   Zero rows in this fixture instant. The table's own empty state is defined once, with exact copy, in §12.8 — not restated or improvised per screen.

Do not show a value dashboard, a channel-selection control, or a Procuring Entity row or column.

### 12.4 TPUB-DES-02 — Authorise publication

Fixture context — outside the artboard: Amina Hassan · Accounting Officer · 15 May 2027, 07:58 EAT · Frappe header breadcrumb: **Home > Tender Publication > Authorise Publication**

Title **Authorise Publication**. Subtitle **Review the approved Tender before it becomes public. This action cannot be undone once channels are notified.**

Sections:

1. **Tender summary**

   | Field | Source and control |
   |---|---|
   | Tender reference | `TND-MOH-2027-033` — **From approved Tender**, plain value. |
   | Requisition | `REQ-MOH-2027-033-001` · Ministry of Health — **From approved Tender**, plain value. |
   | Authorised value | KES 50,000,000.00 — **From approved Tender**, plain value. |
   | Procurement method | Open Tender — **From approved Tender**, plain value. |
   | Tendering period | 21 days — **From approved Tender**, plain value. |
   | Latest delivery date | 30 Sep 2027 — **From approved Tender**, plain value. |

2. **What is being procured** — read-only, drawn from the handoff's inherited snapshot, not retyped. The same six panels TPR-CHG-001 §13.5 shows the Head of Procurement Function at approval — the Accounting Officer sees exactly what he saw, not a rollup of it:

   | Panel | Content |
   |---|---|
   | Goods and delivery | Business laptops · 250 Each · Ministry of Health Headquarters, Afya House, Nairobi · latest delivery 30 Sep 2027 |
   | Technical requirements | `TRQ-MOH-033-001` — mid-range processor, 16 GB memory, 512 GB solid-state storage, pre-loaded security configuration, three-year warranty and on-site support |
   | Warranty and support | 36 months, on-site |
   | Related services | No related services. |
   | Acceptance requirements | No acceptance requirements beyond delivery. |
   | Supporting materials | No supporting materials. |

   Each populated panel shows its stable IDs, exactly as TPR-CHG-001 §13.5 requires — this artboard does not re-typeset the requirement, it renders the same inherited rows.

3. **Approval trail** — from the handoff's own approval decision, not re-entered:

   | Field | Value |
   |---|---|
   | Prepared by | Brian Wafula, Procurement Officer · 20 Mar 2027 |
   | Approved by | Charles Mutiso, Head of Procurement Function · 20 Apr 2027, 10:00 EAT |
   | Readiness at approval | **0 Blocking · 1 Warning** |
   | Warning | Confirm that manufacturer authorisation is proportionate for this item. |

   The Warning is shown, not hidden — TPR-CHG-001 §10.1 never dismisses one, and the Accounting Officer is the last person able to read it before it becomes irreversible.

4. **Documents** — links to the two files the handoff carries, opened from their own digest, never re-rendered here: **View Invitation**, **View issued Tender**.

5. **Advertising channels** — State Portal, Own website, Notice board, Two national newspapers. Generated plain list, per §7.1–7.2. Not a selection control.

Do not summarise sections 1–4 into a single collapsed card, and do not gate the **Authorise Publication** control behind opening the document links — a reviewer who chooses not to open them is still permitted to decide, the same way Charles's own approval task in TPR-CHG-001 never forces a click-through.

One control: **Authorise Publication**. No cancel-in-place, no draft state — this is a single confirm-and-commit action per §13's functional contract.

### 12.5 TPUB-DES-03 — Published Tender detail

Fixture context — outside the artboard: Charles Mutiso · Head of Procurement Function · 23 May 2027, 12:00 EAT · Frappe header breadcrumb: **Home > Tender Publication > TND-MOH-2027-033**

Title **`TND-MOH-2027-033`**. Status badge **Published**.

Sections:

1. **What is being procured** — the same six panels as §12.4's Authorise Publication screen, current as of publication; an officer drafting an addendum from this screen is looking at what they would actually be correcting, not a stale copy:

   | Panel | Content |
   |---|---|
   | Goods and delivery | Business laptops · 250 Each · Ministry of Health Headquarters, Afya House, Nairobi · latest delivery 30 Sep 2027 |
   | Technical requirements | `TRQ-MOH-033-001` — mid-range processor, 16 GB memory, 512 GB solid-state storage, pre-loaded security configuration, three-year warranty and on-site support |
   | Warranty and support | 36 months, on-site |
   | Related services | No related services. |
   | Acceptance requirements | No acceptance requirements beyond delivery. |
   | Supporting materials | No supporting materials. |

2. **Advertising** — channels: State Portal, Own website, Notice board, Two national newspapers. Authorised by Amina Hassan, 15 May 2027, 08:00 EAT.
3. **Addenda.** A table, one row per addendum — not "one row" undefined; this fixture happens to have exactly one:

   | Addendum | Affected area | Issued | Deadline extension |
   |---|---|---|---|
   | `ADD-MOH-2027-033-001` | Goods/delivery schedule | Charles Mutiso · 22 May 2027, 09:00 EAT | Not triggered |

   Expanding a row shows:

   | Field | Value |
   |---|---|
   | Affected reference | `SRC-MOH-033-001`, `SRC-MOH-033-002` |
   | Previous | Ministry of Health Headquarters, Afya House, Nairobi |
   | Revised | Ministry of Health Headquarters, Afya House, 3rd Floor, Procurement Stores, Nairobi |
   | Reason | The general Headquarters address omitted the internal delivery point; without it, delivery risked being misdirected within the building. |

4. **Inquiries.** A table, one row per inquiry, grouped under its owning addendum:

   | Addendum | Question | Response | Affects requirements | Answered by |
   |---|---|---|---|---|
   | `ADD-MOH-2027-033-001` | Do suppliers who already downloaded the original Tender need to resubmit anything given the delivery-location correction? | No resubmission is required. The addendum applies to every copy already issued. | No | Brian Wafula · 23 May 2027, 11:00 EAT |

Actions: **Issue Addendum**, **Cancel**. Both visible per §4's responsibility boundary — Cancel to the Accounting Officer only.

### 12.6 TPUB-DES-04 — Issue addendum

Dialog, 520 px, over the artboard in §12.5.

| Field | Control |
|---|---|
| Affected area | Required select: `Invitation detail`, `Technical requirement`, `Goods/delivery schedule`, `Submission or opening detail`, `Evaluation or contract term`, `Other`. |
| Affected reference | Required text or lookup, per §7.3 — a structured handoff row's stable ID when the area names one. |
| Previous text | Required textarea — what it currently says. Not pre-filled; the officer states it, and issuance checks it against the live value per §8.2. |
| Revised text | Required textarea — what it will say. |
| Reason | Required textarea — why, distinct from what changed. |

One control: **Issue**. Generated results (`deadline_extension_triggered`, `revised_submission_deadline`) never appear in this dialog — they are computed on issuance and shown afterward on the detail artboard, per §12.5.

### 12.7 TPUB-DES-05 — Cancel

Dialog, 520 px, over the artboard in §12.5. Fixture context — outside the artboard: Amina Hassan · Accounting Officer · 4 Jun 2027, 13:58 EAT.

| Field | Control |
|---|---|
| Ground | Required select, the exact eight grounds Act §63(1)(a)–(i) lists. Fixture value: **Inadequate budgetary provision**. |
| Reason | Required textarea. |
| Recommendation | Plain value, shown only when `recommended_by` is set. Absent in this fixture — the field itself is omitted, not shown empty, per KT-STD-001 §2.2's rule against representing an absent value as an empty control. |

One control: **Cancel Tender**. No secondary confirmation dialog — Act §63 already requires a ground and a reason; a second "are you sure" step adds friction the statute does not.

### 12.8 State variants

KT-STD-001 §3 requires exact copy for every loading, empty, forbidden and error state, stated by "the owning change unit" — this document, not KT-STD-001 itself. §11 requires each message to be one plain sentence; TPR-CHG-001 §13.9 already shows the working pattern — a single State/Message/Action table, one sentence per message, the instruction in its own column, not folded into the sentence. The previous version of this section split states into separate tables and wrote two-sentence messages; both diverged from that pattern without saying so, which KT-STD-001 §12 calls a defect, not a decision. Rebuilt to match.

Page-load states (workspace and detail-view entry) resolve per §3A.1 — nothing renders until the verdict arrives, and Forbidden or Not-configured is never a modal, per §3A.2. Command-validation states (`TPUB_ADDENDUM_STALE_REFERENCE`, `TPUB_INVALID_CANCELLATION_GROUND`) bind to their dialog's own control per §11, and are listed here for their exact copy only, not as page states.

| State | Message | Action |
|---|---|---|
| Workspace, Awaiting authorisation, zero rows | No Tenders awaiting authorisation. | None |
| Workspace, Published, zero rows | No Tenders currently published. | None |
| Detail view, Addenda, zero rows | No addenda issued. | None |
| Detail view, Inquiries, zero rows | No inquiries recorded. | None |
| Forbidden, Authorise Publication | You do not have access to Authorise Publication. This area needs one of these responsibilities: Accounting Officer. Ask your KenTender administrator to assign one in System setup. | None |
| Forbidden, Issue Addendum | You do not have access to Issue Addendum. This area needs one of these responsibilities: Head of Procurement Function. Ask your KenTender administrator to assign one in System setup. | None |
| Forbidden, Cancel | You do not have access to Cancel Tender. This area needs one of these responsibilities: Accounting Officer. Ask your KenTender administrator to assign one in System setup. | None |
| Not configured, advertising threshold (`TPUB_THRESHOLD_UNRESOLVABLE`) | The advertising threshold is not configured. | Contact your KenTender administrator |
| Handoff already consumed (`TPUB_HANDOFF_ALREADY_CONSUMED`) | This Tender has already been published. | Refresh the workspace |
| Handoff changed since review (`TPUB_HANDOFF_DIGEST_MISMATCH`) | This Tender's approved package has changed since it was reviewed. | Return to Tender Preparation to re-approve |
| Addendum reference stale (`TPUB_ADDENDUM_STALE_REFERENCE`) | The text you are correcting has already changed. | Reload and confirm the current wording |
| Invalid cancellation ground (`TPUB_INVALID_CANCELLATION_GROUND`) | Select one of the listed grounds. | None — form remains open |
| Stale write | Another user changed this Tender. | Reload |
| Load failure | Tender Publication could not be loaded. | Try again |

**Cancelled Tender** is a content variant, not a page state: §12.5's artboard, loaded against a cancelled TenderPublication, replaces the status badge with **Cancelled**, replaces the Actions row with the cancellation's ground, reason and decision timestamp, and removes both action controls — a cancelled Tender accepts no further command, per TPUB-AC-013.

The requirement panels' own empty values (Related services, Acceptance requirements, Supporting materials, §12.4 and §12.5) are plain content, not page states, and keep their exact copy inline where they're defined.

## 13. Functional interaction contract

- Authorising publication is a single confirm-and-commit action, not a multi-step wizard — the compatibility test in §6.2 is deterministic and either passes or blocks before the officer ever sees the confirm control.
- An addendum's re-publication is automatic and immediate on issuance; there is no separate "publish the addendum" step distinct from issuing it.
- A cancellation's channel-publication is likewise automatic on decision; there is no separate "notify" step an Accounting Officer must remember to trigger.

## 14. Audit and evidence

Every TenderPublication, Addendum and Cancellation record retains its full actor, timestamp and (for Cancellation) statutory-ground trail, permanently — matching KT-STD-001's universal audit standard. The 14-day PPRA and candidate-notice deadlines in §7.5 are visible on the record from the moment of cancellation, not computed only when queried.

## 15. Deterministic Ministry of Health walkthrough fixture

Governed by SEED-001 v1.1. Continues the exact chain: `TND-MOH-2027-033`, approved by Charles Mutiso, 20 Apr 2027.

### 15.1 On-schedule publication, with one addendum

| Event | Actor | Exact time and result |
|---|---|---|
| Handoff created | System | 20 Apr 2027, 10:00 EAT — `TenderPublicationHandoff v1.1`, unconsumed. |
| Publication authorised | Amina Hassan | 15 May 2027, 08:00 EAT — matches SEED-001 §5.4's existing "Published" milestone exactly. Authorised value KES 50,000,000 exceeds the configured national threshold; channels resolve to State Portal, own website and two national newspapers. `publication_consumed_at` = 15 May 2027, 08:00 EAT; `AcknowledgeTenderPublicationConsumed` fires, writing `actual_invitation_date` to Planning per TPR-CHG-001 §9.5 — the same write TPR-CHG-001's own fixture already asserts. |
| Addendum issued | Charles Mutiso | 22 May 2027, 09:00 EAT — `ADD-MOH-2027-033-001`. Affected area: Goods/delivery schedule (`SRC-MOH-033-001`, `SRC-MOH-033-002`). Previous: "Ministry of Health Headquarters, Afya House, Nairobi." Revised: "Ministry of Health Headquarters, Afya House, 3rd Floor, Procurement Stores, Nairobi." Reason: the original address omitted the internal delivery point. Issued with 8 days remaining of a 21-day tendering period — inside the final third (7 days) is not yet reached, so `deadline_extension_triggered` = No. |
| Inquiry answered | Brian Wafula | 23 May 2027, 11:00 EAT — a candidate asks whether suppliers who already downloaded the original Tender need to resubmit anything given the delivery-location correction. `affects_requirements` = No (clarificatory only — no requirement changed); response recorded, not separately broadcast. |

### 15.2 Pre-submission cancellation

A second, independent fixture, per the same one-scenario-per-lifecycle-state convention TPR-CHG-001 and REQ-CHG-001 already use.

| Event | Actor | Exact time and result |
|---|---|---|
| Publication authorised | Amina Hassan | 1 Jun 2027, 08:00 EAT — `TND-MOH-2027-034` (a distinct fixture Tender, to avoid overwriting 15.1's chain). |
| Cancelled | Amina Hassan | 4 Jun 2027, 14:00 EAT — ground: `Inadequate budgetary provision`, per Act §63(1)(b). `ppra_report_due_by` = 18 Jun 2027; `candidate_notice_due_by` = 18 Jun 2027. `tenderer_notice_status` = `Not applicable — no tenderers exist`, since no Bid Submission module exists to have produced one. Cancellation notice published through the same channels — State Portal, own website, two national newspapers. |

## 16. Acceptance contract

| ID | Criterion |
|---|---|
| TPUB-AC-001 | Authorising publication against a handoff that fails the §6.2 compatibility test produces zero side effects — no TenderPublication record, no channel publication, no consumption. |
| TPUB-AC-002 | Authorising publication against an already-consumed handoff is rejected with `TPUB_HANDOFF_ALREADY_CONSUMED`, not silently accepted as a second publication. |
| TPUB-AC-003 | The advertising channel set is generated entirely from the configured threshold snapshot at authorisation; no command or role can directly set it. |
| TPUB-AC-004 | Setting `publication_consumed_at` calls `AcknowledgeTenderPublicationConsumed` exactly once per TenderPublication, matching TPR-CHG-001 TPR-AC-042's own idempotency requirement from the other side of the same contract. |
| TPUB-AC-005 | An addendum issued with the remaining time to the submission deadline inside the final third of the original preparation period sets `deadline_extension_triggered` = Yes and generates `revised_submission_deadline`; one issued outside that window does not. |
| TPUB-AC-006 | An addendum can never alter a field the handoff itself owns — tested by attempting to address it against every field in §7.1 of TPR-CHG-001's inherited snapshot and confirming rejection. |
| TPUB-AC-006A | `IssueAddendum` with a `previous_text` that does not match `affected_reference`'s current published value is rejected with `TPUB_ADDENDUM_STALE_REFERENCE`, not silently accepted or silently corrected. |
| TPUB-AC-006B | The Authorise Publication screen renders the approved Tender's full readiness result — every Warning, not a count alone — sourced from the handoff, tested against the actual rendered output, not assumed present because the data exists. |
| TPUB-AC-006C | The Authorise Publication and published-Tender-detail screens render all six requirement panels — Goods and delivery, Technical requirements, Warranty and support, Related services, Acceptance requirements, Supporting materials — with actual content or an explicit empty state for each; no panel is replaced by a count. |
| TPUB-AC-006D | Every list surface in §12 (workspace sections, Addenda, Inquiries) renders as a table with the named columns stated in §12; no surface renders as an undifferentiated row of concatenated values. Every empty, forbidden and error state on those surfaces uses the exact copy in §12.8, not improvised text. |
| TPUB-AC-007 | An inquiry response with `affects_requirements = Yes` is copied to every candidate without the responding officer or system exposing who asked; one with `affects_requirements = No` is not broadcast. |
| TPUB-AC-008 | A cancellation requires one of Act §63(1)'s eight listed grounds; no free-text ground is accepted. |
| TPUB-AC-009 | Cancellation is decided only by the Accounting Officer; a Head of Procurement Function recommendation is accepted when present and has no effect on whether the decision is valid when absent. |
| TPUB-AC-010 | Cancellation publishes its notice through every channel the original advertisement used, tested against the actual published output, not assumed from the advertisement record. |
| TPUB-AC-011 | Both the 14-day PPRA-report and candidate-notice deadlines are generated at the moment of cancellation, not computed only on a later query. |
| TPUB-AC-012 | `tenderer_notice_status` reads `Not applicable — no tenderers exist` in every fixture this release; no command or fixture asserts a named tenderer notification, since no module yet produces one. |
| TPUB-AC-013 | A cancelled TenderPublication accepts no further command — not another addendum, not a second cancellation, not a reopening. |

## 17. Test and smoke contract

Test order: (1) contract tests against `TenderPublicationHandoff v1.1` exactly as TPR-CHG-001 §7.6 defines it; (2) the §6.2 compatibility test, including the deliberately-unresolvable-configuration case; (3) domain and command tests against every acceptance criterion in §16; (4) render tests confirming the Invitation and issued Tender reach every resolved channel unchanged from TPR-CHG-001's own digest; and (5) the two fixtures in §15, loaded independently.

| ID | Smoke test |
|---|---|
| TPUB-SMOKE-01 | Load 15.1's on-schedule fixture; verify the TenderPublication, one Addendum and one Inquiry match §15.1 exactly. |
| TPUB-SMOKE-02 | Verify `AcknowledgeTenderPublicationConsumed` fires exactly once and TPR-CHG-001's own milestone-actual assertion (TPR-AC-042) is satisfied by this module's call, not a separate mechanism. |
| TPUB-SMOKE-03 | Attempt authorisation with the advertising-threshold configuration deliberately absent; verify `TPUB_THRESHOLD_UNRESOLVABLE` and zero side effects. |
| TPUB-SMOKE-04 | Load 15.2's cancellation fixture; verify both compliance deadlines, the published cancellation notice across every original channel, and `tenderer_notice_status`. |
| TPUB-SMOKE-05 | Attempt a second `AuthorisePublication` against 15.1's already-consumed handoff; verify rejection. |
| TPUB-SMOKE-06 | Attempt `IssueAddendum` and `CancelPublication` against 15.2's already-cancelled TenderPublication; verify both are rejected. |

## 18. Required walkthrough before implementation

A GO walkthrough by a practising Procurement Officer and Accounting Officer, run against the fixtures in §15, is required before implementation, matching KT-STD-001's universal verification protocol. This document adds no template release evidence of its own — it consumes STD-TPL-001's, unchanged.

## 19. Implementation constraints

No production code, migration, deployment or DocType is authorised by this document. Implementation may proceed only after this document is approved and the required corrections in §21 exist or are explicitly deferred by the Project Owner.

## 20. Cutover

Not applicable. There is no prior Tender Publication mechanism to cut over from.

## 21. Traceability and precedence

This document conforms to:

1. **KT-STD-001 v1.3** for document structure, shared fixtures, page-state rules and universal prohibitions;
2. **STD-STD-001 v1.1** for the three-layer separation and the parameter rule;
3. **AUTH-ADR-001 v1.6** for role-bound responsibility assignment and registered permission hooks;
4. **CFG-CHG-002 v0.9**, extended per §21, for the effective-dated advertising threshold this document reads but never defines;
5. **STD-TPL-001 v0.6** (pending re-approval), for the Invitation and issued Tender this document publishes unchanged;
6. **TPR-CHG-001 v0.7** (pending re-approval), for the exact `TenderPublicationHandoff v1.1` contract and the `AcknowledgeTenderPublicationConsumed`/§9.5 seam this document closes; and
7. **SEED-001 v1.1**, for the exact harmonized identifiers §15's fixtures extend.

Public Procurement and Asset Disposal Act, 2015 §63, §74, §75, §78, §89, §96, §97, §98, and the Public Procurement and Asset Disposal Regulations, 2020, Regulations 48, 49, 56, 57, 85 and 86, read directly from Kenya Law's consolidated text rather than inferred from summary, control every statutory citation in this document.

**Required corrections in other documents.**

- **CFG-CHG-002** needs the effective-dated national advertising threshold added as a governed configuration value, per §7.2. This document cannot supply the actual Kshs figure — see §1's account of that research.
- **KT-STD-001 §8.3** needs Brian Wafula's scope note extended from "Tender Preparation only" to "Tender Preparation and Tender Publication," per §5.
- **Bid Submission**, when it exists, needs to supply the "candidate obtained tender documents" registry this document's §7.4 and §7.5 currently have no source for, and the named-tenderer notification path Act §63(4) requires once a submission exists. Named here as a tracked dependency, the same way TPR-CHG-001 named PLN-CHG-001's missing inbound handler.
- **Not a correction owed by another document, but a decision owed to the whole chain.** KT-STD-001 §7's canonical change-unit skeleton has 18 named sections in a fixed order. Neither this document nor TPR-CHG-001, which it was structurally modelled on, follows that order — both use an expanded, differently-sequenced structure (this document has 22 sections; TPR-CHG-001 has 23), without ever stating the departure or a reason for it, which KT-STD-001 §12 itself calls "a defect, not a decision." Resequencing this document alone would not fix that — it would just diverge from its own sibling documents in a third way. This needs a decision at the KT-STD-001 or project level: reconcile the skeleton to what's actually been built, reconcile the documents to the skeleton, or state the departure explicitly once, centrally, rather than per document.

## 22. Approval effect and next action

On approval, TPUB-CHG-001 v0.3 supersedes v0.2 in full and becomes the Tender Publication requirements document for the first IT-equipment slice, closing the seam TPR-CHG-001 §9.5 has held open since v0.5. v0.2 was itself approved on 10 September 2026; this domain correction supersedes that approval and requires its own.

Approval authorises: the `AuthorisePublication`, `IssueAddendum`, `RespondToInquiry` and `CancelPublication` commands and their error contract in §10; the domain model in §7; and the two fixtures in §15. It does not authorise code, migration, deployment or production use, and it does not resolve the required corrections named in §21 — those remain open, tracked, and are the next actions, not blockers to this document's own approval.
