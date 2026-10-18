# TRUST-OPS-001 — Sealed-Bid Incident Recovery Procedure

**Controlling approval — 18 October 2026.** The Project Owner instructed, verbatim: **“Mark the documents as approved”**, following delivery of BOP v0.16, TPR v0.24, PRC v0.14, AWD v0.9 and TRUST-OPS v0.2 and the implementation handoff. This approves all five complete successors together, including their incorporated predecessor content and current requirements, screen variants, owner bindings, fixtures and acceptance criteria. It creates no separate retrospective approval of intermediate proposals. Earlier Proposed/pending wording and approval effects retained below are history for their named versions. Approval does not certify implementation, deployment, migrations, integrated tests, accepted operational drills, legal clearance or production readiness; their evidence conditions remain in force.

**Current successor v0.2 — Approved, 18 October 2026.** Prepared on the Project Owner's instruction “Proceed”, following review of failed-opening recovery and cancellation. This complete successor retains unrelated predecessor content. Current amendments and this control table govern this approved successor; earlier version introductions, approval effects and baseline claims below are history for their named versions. Approved v0.2 now supersedes v0.1. Requirements approval is distinct from implementation, accepted drills, legal clearance and production release.

**Current implementation entry point.** Rule §9.1; service/event binding §9.2; screen variants §9.3; fixtures §11.1; acceptance §11.2; verification §11.3; impact §14.1. Changed IDs: `TRUST-OPS-OF-AC-001`–`TRUST-OPS-OF-AC-012`.

**Draft v0.1 — proposed 11 October 2026; approved 11 October 2026 as the draft procedure.** This document drafts the incident-recovery procedure that TRUST-ADR-001 v0.5 §2B item 6 records as production-readiness item **PR-001**. It is a procedure for people, not a change to the product: it describes how a failure in sealed-bid handling is declared, investigated and recovered **without anyone reading a sealed bid**. The predecessor was approved as a draft procedure; operational use still requires the tested and accepted §11 evidence. This v0.2 amendment is Proposed.

| Control | Value |
|---|---|
| Document ID | TRUST-OPS-001 |
| Title | Sealed-Bid Incident Recovery Procedure |
| Version | 0.2 |
| Date | 18 October 2026 |
| Status | Approved — 18 October 2026 |
| Approved on | 18 October 2026 |
| Approval record | Project Owner, 18 October 2026: “Mark the documents as approved”. Complete coordinated successor approved; implementation and release evidence remain separate. |
| Supersedes | Approved v0.2 supersedes approved v0.1. |
| Owner | Project Owner (approval); Opening access support (operation) |
| Implements | Register item PR-001; TRUST-ADR-001 v0.5 §2B items 4 to 6 |
| Depends on | Approved TRUST-ADR v0.6, BDS v0.16 and their confidentiality controls; BOP v0.16 / TPR v0.24 / PRC v0.14 / AWD v0.9 coordinated approved successors for this route; current AUTH controls (preserve approved v1.16 funding changes). |
| Owner instruction | The Project Owner instructed on 10 October 2026 (quoted in part, verbatim): “Have Claude Code draft PR-001’s recovery procedure. It should cover incident declaration, authorised support access, permitted diagnostics, recovery without exposing sealed contents, evidence preservation, escalation when opening cannot proceed, and closure review. Test the procedure before production. Any exceptional access to sealed contents remains a separately reviewed design.” |

**What is new content for the Owner’s review.** Everything in this draft that is not taken from the documents named in the control table is the drafter’s proposal and is marked **[New]**: the severity classes, the time targets, the post-incident review period, the drill schedule and the evidence retention. They are not decided facts. Nothing here is a statement of law; where a legal consequence is mentioned it is marked **not verified against the primary source**.

## 1. Purpose and scope

1. **Purpose.** When something that holds, moves or opens a sealed bid fails, people need one agreed way to say so, to find out what is wrong, to put it right, and to prove afterwards what was done — while the bids stay sealed and unread.
2. **In scope.** Failures of: the sealed bid-submission service and its hand-off; the tender box and its custody service; the opening profile, credential and attendance services; a package that is unreadable or does not match what was received at the deadline; and any failure that stops an opening from starting or continuing.
3. **Out of scope.** Reading, copying, restoring for inspection or otherwise gaining access to the contents of a sealed bid, its count or the identity of a bidder, outside an authorised opening. **No such access exists in the MVP and this procedure does not create one.** Any exceptional access to sealed contents is a separately reviewed design that preserves the authorised-opening controls (§12). Its absence does not justify an administrator bypass.
4. **Operational recovery is not content access.** Restarting a service, repairing a connection, re-issuing a credential under custody control, restoring a database from backup into the same sealed custody, or re-running a failed hand-off all restore a *service*. None of them needs a person to see a bid, and a step that would is not part of recovery (§7.4).

## 2. Principles

1. **Fail closed.** If a sealed read, package, key or custody service fails, the operation stops and the bid stays sealed and unread.
2. **No administrator bypass.** Administrator and System Manager status grants no access to incident records, incident details or sealed bids (AUTH-ADR-001 v1.14 §8).
3. **Least information.** Support works from the diagnostics in §6, which carry no bid content, no bid count and no bidder identity. Where a diagnostic could imply participation (an opaque envelope identifier, an incident of kind “A bid could not be opened”), it is shown only to those who must have it and its reading is recorded (§5 item 4).
4. **Keep technical recovery and business authority separate.** Support restores services and records findings; the appointed chair alone uses the ordinary guarded retry/resume route; the Accounting Officer makes any lawful Tender cancellation decision. These are distinct responsibilities, not a new two-person approval of routine recovery. Existing committee/custody participation and segregation rules still apply.
5. **Everything is evidenced.** Every declaration, access, diagnostic, change, decision and closure leaves a record (§8) that contains no sealed content.
6. **Application restrictions are not infrastructure custody.** The application hides sealed records from users and technical accounts; it cannot stop a database or infrastructure operator. The production custody controls of TRUST-ADR-001 §1 and §4 are what bind that operator and are deferred to the support module. This procedure does not claim otherwise.

## 3. Roles

| Role | Who holds it | What it does in an incident |
|---|---|---|
| **Opening access support** | A Technical Operator assignment in force (the current holders, `notify.holders()`) | Receives the incident, works the diagnostics of §6, restores the service, records the resolution or that it cannot be fixed. Never acts for the committee. |
| **Chair** | The appointed chair of the opening | Runs the ceremony; may re-send the notice to support (**Notify support**); waits for support’s resolution before **Retry opening**. |
| **Accounting Officer** | Holder of the Accounting Officer responsibility | Decides how to proceed with a paused opening that support cannot recover (§9); reads the incident details and the access trail. |
| **Auditor** | Holder of the Auditor responsibility | Reads the access trail; takes part in the closure review (§10). |
| **Platform operator** | The infrastructure team that runs the servers (not an application role) | Restores infrastructure on support’s request. Stays outside the application’s restrictions, which is why §2 item 6 and §7.4 bind them by procedure. **[New]** Named by the Owner before production. |
| **Incident lead** | **[New]** One member of Opening access support named at declaration | Owns the incident record until closure and keeps the evidence log (§8). |

Administrator and System Manager are **not** incident roles. A technical account without the Opening access support assignment sees no incident, no incident count and no decision item.

## 4. Declaring an incident

1. **What triggers one.** The system opens an incident by itself for: *Opening profile unavailable*, *Credential unavailable*, *Attendance service unavailable*, *Package unreadable* and *Package mismatch* (Bid Opening); and, for Bid Submission, the kinds *Submission service* (electronic signing or submission is unavailable), *Production submission gate*, *Submission close* (the deadline passed and nothing closed) and *Submission attempt* (to reconcile). A person declares one by telling Opening access support (or the Chair, who uses **Notify support**) when something not covered by those triggers stops a sealed operation.
2. **One incident per problem.** The same problem never opens a second incident; a retry of the notice re-sends the same one.
3. **Recorded at declaration.** Incident reference, kind, time raised, who is assigned, how support was notified and whether the notice was delivered. No bid content, count or bidder identity is recorded.
4. **Severity. [New]** *Critical* — an opening or a submission deadline is at risk within the next two hours, or a package is unreadable or mismatched. *High* — a sealed service is down with no deadline within two hours. *Routine* — degraded but working. The Incident lead sets the class; the Accounting Officer may raise it.
5. **Time targets. [New]** Critical: support acknowledges within 15 minutes and the Incident lead is named within 30. High: acknowledged within 1 hour. Routine: next working day. A missed target is itself recorded and escalated one step (§9).
6. **Who is told.** The assigned support holders (in-app notice that links to the opening page, never to the incident record); the Chair of an affected opening; the Accounting Officer for any Critical incident.

## 5. Authorised support access

1. **Who may work an incident.** An actively assigned Opening access support holder works only their authorised incident through its purpose-named owner workflow. The AO may read the scoped evidence needed for their decision/review; the Auditor may read the authorised incident evidence and access trail for oversight, without recovery mutation. Administrator/System Manager status grants none of these rights. Additional business responsibilities are checked independently, not denied merely because the person also holds a technical role.
2. **How access is given.** The active scoped responsibility and owner predicate establish the permitted operation; there is no ad hoc incident permission grant. Support assignment alone confers no AO or Auditor authority. A person without it cannot be given the details by sharing a screen or a file; if more help is needed it is arranged by assigning a holder (an ordinary responsibility assignment).
3. **What support may do.** Read the incident summary on the opening page; open the incident’s **details** by an explicit request that names a purpose (*Investigate the problem*, *Record the resolution*); read the diagnostics of §6; restore services under §7; record that an incident is resolved or cannot be fixed.
4. **What is recorded.** Every opening of the details is recorded with the person, the time, the incident, the action, the purpose and the outcome — also when it was refused — and an export of incidents is recorded the same way. A page refresh records nothing. The trail holds no incident content and is read only by the Auditor and the Accounting Officer.
5. **What support may not do.** Read, search, export or restore a sealed bid or its attachments; count bids; look up a bidder; read sealed tables through the database; copy a package off the server; or accept a request to do any of these from anyone, including a senior officer. A request to do so is itself recorded as part of the incident (§8) and refused.

## 6. Permitted diagnostics

| Diagnostic | Why it is permitted | Never includes |
|---|---|---|
| Service availability and health status | Shows what is down | Any bid or bidder |
| Incident reference, kind, timing, notice state and attempts | Shows what happened and when | The identity of a bid |
| Error codes and service logs **with sealed content redacted** | Shows why a service failed | Bid content, signatures, attachments |
| Service health/job and scheduler status; aggregate queue depth only where it cannot reveal sealed participation | Shows whether infrastructure work is stuck; omit any per-Tender/per-envelope count or timing aggregate that reveals bid existence/count | Payloads, sealed record counts and participation inference |
| Version, configuration and release identifiers; installed template release | Shows what is running | Bid data |
| Digest and integrity checks **by comparison only** (the digest of what was received at the deadline against the digest of the package presented) | Proves a package matches without reading it | The package |
| The opaque envelope identifier, **for the support holder working that incident only** | Lets support locate the failing item | The bidder behind it |
| Time-source and clock checks | Opening and deadlines depend on trusted time | — |

If a diagnostic would require a step outside this table, the step is not permitted: stop and escalate under §9.

## 7. Recovery without exposing sealed contents

### 7.1 General method

1. Confirm the incident record and name the Incident lead.
2. Take only the diagnostics of §6, in this order: service health, recent errors, queue and scheduler, configuration and identifiers, integrity by digest comparison.
3. Choose the least change that restores the service; make it; record it (§8).
4. Verify by the same diagnostics, never by looking at a bid.
5. Record the resolution (or that the incident cannot be fixed) and tell the Chair; the Chair may use **Retry opening** only if recovery is verified, the opening is nonterminal and all owner guards pass; otherwise the existing AO decision route remains.

### 7.2 By failure

| Failure | Typical cause | Recovery (no content access) | Verification | If it cannot be fixed |
|---|---|---|---|---|
| *Opening profile unavailable* | Profile or rule service down or misconfigured | Restore or reconfigure the profile service; re-run its health check | Health check passes; the opening’s start guard clears | Escalate (§9) |
| *Credential unavailable* | Opening credential not issued or expired in custody | Re-issue under the custody method’s own controls (§12); never copy a key to a person | Credential reported ready | Escalate (§9) |
| *Attendance service unavailable* | Join or presence service down | Restore the service; members re-join | Presence recorded for the appointed members | Escalate (§9) |
| *Package unreadable* | Corruption in transit or storage, or a rendering fault | Re-fetch the package **from custody to the same sealed path** and compare its digest with the digest recorded at the deadline; re-run the renderer | Digest equals; the renderer reports success | Escalate (§9); the bid is never opened by hand |
| *Package mismatch* | Digest of the package differs from the digest recorded at the deadline | Treat as potential tampering: preserve everything (§8), do **not** retry blindly, restore the original from the sealed backup custody and compare again | Digest equals the deadline digest | Escalate immediately (§9) and tell the Auditor |
| Submission service down | Signing or custody adapter unavailable | Restore the adapter; the system leaves bids Draft/Ready and refuses to submit until it is back | Availability gate reports available | If the deadline passes during the outage, §9 |
| Close overdue | The scheduled close did not run | Run the close job under its own controls; check the hand-off is written | Close and hand-off records exist | Escalate (§9) |
| Submission attempt uncertain | Network loss between signing and receipt | Reconcile the attempt with the custody service’s record by correlation identifier | Attempt becomes Accepted or Failed | Escalate (§9) |

### 7.3 Restoring from backup

A restore may only put data back **into the same sealed custody**, to the same restricted paths, with the same access restrictions, by the Platform operator on support’s written request. A restored copy is never opened, queried or sampled to check it; its integrity is shown by digest comparison and by the application’s own health checks. The restore is recorded with the backup identifier, time and the person who ran it.

### 7.4 Steps that are never part of recovery

Opening a package “just to see”; querying sealed tables; counting envelopes; reading a signature or attachment; copying data to a laptop; sharing a screen of a bid; granting a person the committee’s opening credential; rewriting a digest so that a comparison passes; deleting an incident or an access event. Each is a breach of this procedure and is reported to the Accounting Officer and the Auditor.

## 8. Evidence preservation

1. **Keep, for every incident:** the incident record; the access events (§5 item 4); the command journal entries; the service and error logs for the period with sealed content redacted; the digests compared and their results; every configuration or release identifier changed; the backup identifiers used; the times of declaration, acknowledgement, each change and resolution; and the Incident lead’s dated log.
2. **Preserve before changing.** Take the evidence of the failing state (logs, identifiers, digests) *before* restarting or restoring anything.
3. **Keep it free of sealed content.** Evidence that would contain a bid is not evidence under this procedure; record that it was not taken and why.
4. **Integrity.** The evidence set is stored read-only and its digest is recorded in the incident record at closure.
5. **Retention. [New]** At least as long as the records of the opening it concerns are retained; the period is for the Owner to fix. **Not verified against the primary source:** any statutory retention period.
6. **Who may read it.** The Incident lead, the Accounting Officer and the Auditor. Not Administrator or System Manager by status.

## 9. Escalation when opening cannot proceed

1. **Support cannot fix it.** Support records that the incident cannot be fixed; the opening stays paused and the system gives the Accounting Officer the item **Decide how to proceed with the paused opening**.
2. **Ladder.** Support → Incident lead → Head of Procurement Function (informed) → Accounting Officer (decides). A missed time target (§4 item 5) moves the incident one step up.
3. **The Accounting Officer’s options** follow the explicit current outcome table below: existing lawful TPR cancellation when its guards pass, or retention of an unresolved case with exact blockers and named corrective holders. A technical finding may allow the chair’s ordinary guarded continuation of a nonterminal case; it requires no additional AO recovery approval. A Not held case cannot restart. No free-text decision creates a new lawful remedy.
4. **Tell the bidders.** When an opening is delayed or not held, the Procuring Entity communicates to bidders through the Tender’s existing notice route. **Not verified against the primary source:** any legal minimum for such a notice or for a revised opening time.
5. **Never** open by hand, in person or by any route outside the opening process because the system cannot. If the opening cannot be done with the controls intact it is not done.

### 9.1 Opening failure reconciliation — outcomes and ownership

This current successor coordinates BOP v0.16, TPR v0.24, PRC v0.14, AWD v0.9 and TRUST-OPS v0.2. All five were approved together on 18 October 2026. Its requirements are complete locally; the counterpart references identify ownership, not a separate source of unstated decisions.

**Three outcomes.** (1) A verified recovery lets the appointed chair retry/resume only a nonterminal opening, with the full roster and every existing custody/access guard. Before Start it remains Pending/Ready; after Start it remains the same interrupted ceremony and resumes at its last committed step. (2) A lawful TPR cancellation ends the proceeding and automatically records the correct BOP/PRC terminal outcome; it never becomes successful opening. (3) Where neither recovery nor lawful cancellation is currently supported, retain an owned unresolved case with the exact blocker, responsible holder and existing corrective route. Viewing a task, recording an incident, timing out or writing a referral never clears it. Technical failure alone neither selects a cancellation ground nor disqualifies a bidder.

**Completion and evidence.** In MVP 1, an unreadable/unverified/unaccounted current timely submission cannot be omitted or passed to Evaluation as opened. There is no generic exceptional-disposition control that converts that failure to successful opening. A future alternative needs its own legal basis and approved owner contract. A Not held identity cannot start/resume; a technical fix does not undo it. A Cancelled after start/Aborted after start identity cannot resume, attest, finalize or hand off. Preserve actual participation, already-opened records, submitted values, original receipts and still-sealed packages; cancellation authorises no further reveal or deletion. Existing evidence-retention duties continue.

**Cancellation and funds.** AO uses the existing TPR CancelTender action, with a verified applicable ground, current source revisions and authoritative pre-notification evidence. AWD Not issued must come from its durable tender-level authority record, including before an Award case exists; absence of a case is not proof. Issue in progress, Issued or Unknown blocks this route. TPR cancellation and Award issue serialize on the same Tender guard, with authority rechecked inside the transaction and before any outward notice effect. Preserve the approved PLN v1.32 / REQ v1.20 / BUD v1.17 resource recovery contract carried into TPR: exact unused source set only, both owner effects together, no commitment release, scope unlock or automatic replacement. A failed opening or unresolved incident alone releases nothing. Recovery of funding does not require opening a sealed bid or fabricating completed minutes; it still requires authoritative source and surviving-obligation checks. Cancellation-compliance, incident closure and financial-recovery completion remain separate facts.

**Authority versus readiness.** Current requirements approval is distinct from installed adapters, integration tests, accepted PR-001 drills and production legal/custody clearance. A historical reference to TPR v0.13/v0.14 is not the current implementation baseline. Report actual unavailable services through their owner guards. Preserve Trust L1/L2 and LAW-V-001: this amendment records no electronic-page/signature equivalence, operative password threshold, court-order status or permission to open real bids through a stand-in. BOP's existing independent-member and security-intake exclusion policies remain unchanged.

**Bounded recovery and terminal disposition.** Support records Unresolved / Recovered / Cannot recover with attributed diagnostic evidence and informs the appointed chair/AO through existing incident routes. Recovered means only that the technical obstacle has been removed; BOP rechecks every current guard before a chair action. Cannot recover retains the affected opening and its evidence and routes to the existing AO Tender decision. An incident lead is coordination responsibility, not a new business role or an extra approval. Support never selects a statutory ground or resumes/opens a bid for the committee.

| Opening condition | Next holder/action | Effect |
|---|---|---|
| Before Start, still nonterminal | Support resolves; chair retries existing Begin | No fabricated Start or retrospective attendance |
| Actual opening paused | Support resolves; chair resumes existing ceremony | Continue from last committed step only after roster/custody checks |
| Cannot recover or opening Not held | AO reviews existing TPR cancellation route with exact incident/context | Lawful cancellation, or visible unresolved case with all verified blockers and named owner routes; no automatic cancellation |
| TPR cancellation committed | BOP/PRC consume owner event and preserve custody/partial evidence; REQ runs independently guarded resource recovery | No restart, successful-opening handoff or manual funding release |
| No currently permissible disposition | AO retains business decision; HOPF coordinates legal-basis review, Award owner status reconciliation or support technical investigation as relevant | Case stays unresolved with next owner/action and review evidence, not a fabricated clearance |

Technical incident closure is distinct from successful opening and from cancellation compliance/funding completion. A retired-from-use failed service may remain a separately owned defect after the affected proceeding lawfully ends. An unresolved business case may retain technical findings and safe mitigations, but must not be closed as “opening resolved”. An AO decision to retain the case pending review is not cancellation, restoration or legal clearance.

### 9.2 Opening failure reconciliation — service and event bindings

The procedure calls no new cancellation or financial endpoint. Support's existing incident outcome write requires the exact incident revision, active assignment, outcome/reason, safe evidence references and retry identity; a duplicate accepted write returns its original outcome and changed facts conflict. It must not write BOP/TPR/PRC state itself. Chair/AO use existing owner commands, which enforce the current source revisions and permissions. All explicit detail reads/exports retain purpose and outcome audit; background refresh does not impersonate a user detail read. Incident closure records the verified technical or cancellation outcome references and remaining separately owned defects/obligations; it does not claim them complete.

### 9.3 Opening failure reconciliation — existing-screen variants

Use the existing incident details and opening/Tender pages. Support sees safe diagnostics, its exact assignment and Unresolved / Recovered / Cannot recover with evidence; it never sees a business Cancel Tender action merely from that assignment. The AO sees its scoped incident evidence and existing Tender decision. The Auditor reads evidence/access trail through authorised routes, without operational mutation. Incidents closed after cancellation display **Closed after tender cancellation**; this is a closure outcome/reason in the existing incident model, not a new ceremony status. Pending business disposition displays the actual unresolved cause and responsible holder, not “service restored”.

## 10. Closure review

1. **When an incident may close.** Either (a) technical recovery is verified by permitted diagnostics with the actual BOP continuation/remaining business status recorded, or (b) an authoritative TPR cancellation and BOP/PRC terminal receipt account for the failed proceeding without claiming that the service recovered. In both cases preserve the evidence set/digest and any remaining separately owned service defect, notice/report or financial-recovery work. A bare AO note, pending review, unresolved owner delivery or unsupported disposition is not resolution of the opening.
2. **Who reviews.** The Accounting Officer and the Auditor, with the Incident lead presenting.
3. **Within. [New]** Five working days of closure for a Critical or High incident.
4. **The review confirms:** the timeline against the targets; that no step in §7.4 was taken; that every access to details is in the trail with a purpose; what the root cause was; what changes (service, procedure, test) follow; and whether the register or a requirement document needs a change.
5. **Outcome.** A short written review filed with the incident’s evidence; follow-up actions have an owner and a date. A breach of §7.4 is reported to the Project Owner.

## 11. Testing before production

The procedure is not operational until it has been tested and the Owner has accepted the results.

1. **Tabletop exercises** (all roles in a room, a scripted scenario, no systems touched): (a) Package mismatch at the start of an opening; (b) opening profile down at the deadline; (c) submission service down in the last hour before a deadline; (d) a request from a senior officer to “just look” at a bid; (e) the Incident lead is unavailable. Pass: each role states its next action, the right person decides, and (d) is refused and recorded.
2. **Technical drills on a non-production site that carries test data only** — one per row of §7.2, using the test controls that already exist for opening-profile, notice-delivery and issuer faults. Pass: the incident opens once, the notice is delivered or re-sent, a recoverable service is restored using only §6 diagnostics and the Chair may retry only while BOP remains nonterminal and all guards pass. For an irrecoverable or terminal case, the scripted AO outcome/blocker and its task-clearing conditions must pass instead; the access trail shows exactly the reads made.
3. **Access drill.** Prove, on the non-production site, that Administrator and a System Manager cannot read an incident, its details, its count or the trail; that the support holder can read details only after naming a purpose; and that a refused attempt is recorded.
4. **Restore drill.** Restore a backup into sealed custody on a non-production site; show integrity by digest comparison only.
5. **Evidence.** Each exercise produces a dated record: scenario, participants, steps, result, defects. **[New]** Repeat the tabletop yearly and after any change to the opening or custody services.
6. **Sign-off.** The Owner accepts the results in writing; failures are fixed and the failed exercise repeated.

### 11.1 Opening failure reconciliation — isolated verification fixtures

**Isolated OF-F01 — recovered paused opening.** Use the existing BOP Tender TND-MOH-2027-033, appointed roster and original immutable submissions; do not change canonical quantities, prices or the primary happy path. Inject a credential outage after one committed readout, before the next reveal. Record interruption and recovery as attributed events; resume once under the full roster. Replaying the recovery/resume cannot repeat that readout. This is an isolated reset branch, not an added event in the base fixture.

**OF-F02 — cannot recover after Start.** On a separate reset of that same fixture, make the next timely package irrecoverably unreadable. Keep the first readout/actual participation. Test (a) verified applicable cancellation ground supplied by the isolated profile plus durable AWD Not issued; (b) missing ground; (c) Unknown/Issue in progress/Issued; and (d) a concurrently queued notice. No actual source is asserted to establish a cancellation ground; the test supplies its ground evidence explicitly, rather than deriving it from the fault. In (a), cancellation consumes the exact source lineage and closes the partial proceeding, then runs the existing guarded resource recovery. In all blocked branches keep the case owned/unresolved, with no release or successful handoff. Reverse the race ordering and test both winners.

**OF-F03 — never held.** Use existing isolated TND-MOH-2027-035 and its attendance-service failure, with no Start. After the scheduled time, record Not held. Recovery cannot begin the same identity. Lawful cancellation attaches its event to that terminal record without a duplicate AO task or fabricated closed manifest. Retain the no-ground and unavailable-owner blocked variants.

The recovery/crash and replay tests use real BOP–TPR–PRC–AWD owner adapters; financial checks also use real REQ/Planning/Budget adapters. Simulated signing/custody may exercise their approved isolated boundary only and never certify live readiness. No fixture creates a second PE, unapproved staff role or production data reset.

### 11.2 Opening failure reconciliation — acceptance

Existing acceptance remains except the specifically superseded failed-opening completion/route wording. Map these additions to integrated evidence; repeated owner criteria may share one real scenario.

| ID | Required result |
|---|---|
| TRUST-OPS-OF-AC-001 | Recoverable pre-start failure stays nonterminal and creates no Start/attendance facts until the chair begins under current guards; Not held cannot retry Begin. |
| TRUST-OPS-OF-AC-002 | Recovery of an interrupted ceremony resumes from its last committed step with full roster/custody checks, no duplicate readout, and clears only that escalation instance on actual Resume. |
| TRUST-OPS-OF-AC-003 | An irrecoverable timely package cannot be skipped, disqualified or handed to Evaluation as opened. AO sees the existing cancellation route or every named current blocker. |
| TRUST-OPS-OF-AC-004 | No Award case exists: a verified durable Tender-level Not issued record may support cancellation; a null/missing/stale/unavailable lookup returns Unknown and blocks it without fabricating an Award case. |
| TRUST-OPS-OF-AC-005 | Cancellation/first-notice issue race, including queued retries and unknown send outcome, yields one valid fence winner. No notice dispatch follows committed cancellation; no cancellation passes Issue in progress, Issued or Unknown. |
| TRUST-OPS-OF-AC-006 | Verified cancellation before Start creates terminal Not held once; after actual Start it creates terminal partial BOP/PRC closure once. Preserve actual events, unopened custody, source/receipt times; no normal finalization/handoff. |
| TRUST-OPS-OF-AC-007 | Crash/duplicate/out-of-order cancellation delivery creates no repeated decision, PRC closure, task receipt, obligation or financial recovery. Failed consumer delivery is retained/retried and cannot permit further ceremony actions. |
| TRUST-OPS-OF-AC-008 | Missing ground/legal profile/integration or source status gives exact current reasons, responsible holders and permitted corrective routes. An open task cannot clear on page view, free-text referral or technical acknowledgement. |
| TRUST-OPS-OF-AC-009 | Scoped support, AO and Auditor reads follow the access matrix; Administrator/System Manager status adds no access. Detail read/export is purposeful/audited; protected packages, counts and identities do not leak. |
| TRUST-OPS-OF-AC-010 | A cancellation-based incident closure does not require falsely restored service; business case, failed service follow-up, cancellation compliance and financial recovery each retain their own actual outcome. |
| TRUST-OPS-OF-AC-011 | Integrated cancellation invokes approved exact-source Planning/Budget recovery without opening sealed bids, releasing commitments or changing scope. New procurement follows fresh ordinary REQ eligibility and approvals; unresolved opening alone releases nothing. |
| TRUST-OPS-OF-AC-012 | Production legal/custody and PR-001 drill gates remain enforced; original ordinary/empty opening, minutes/proofs, evaluation profile, Award funding and pre-consumption REQ revocation regressions still pass. |

### 11.3 Opening failure reconciliation — implementation and release evidence

Build the complete allowed/blocked/recovered/cancelled journey against the current owner contracts. Real BOP–TPR–PRC–AWD tests must cover missing pre-case authority, both cancellation/notice race orders, failed delivery, stale sources, crash/replay and terminal-state denial. Resource-recovery integration uses real REQ/Planning/Budget owners. PR-001 must exercise cannot-recover, no-ground, Unknown/Issue in progress, Not held and cancellation-with-service-still-failed branches, not only successful repair. Preserve safe audit and custody evidence. Record environment, exact adapter versions, test command/result and each acceptance-to-evidence mapping. Accepted drills and legal/profile evidence remain separate prerequisites for live use; do not infer them from requirement approval. An unsupported runtime route stays visibly blocked, never silently enabled by removal of an old version reference.

## 12. Exceptional access to sealed contents (not provided)

No exceptional access to a sealed bid exists in the MVP and none is created here. If the Owner ever wants one, it needs its own design, reviewed separately, which must preserve the authorised-opening controls and define at least: who may ask and who must approve (dual control, never the requester); the reason; the narrowest scope; the shortest expiry; the evidence it must leave; how the bidders’ confidentiality and the opening’s integrity are protected; and its legal basis (**not verified against the primary source**). The existence of this section is not a design for it. Its absence does not justify an administrator bypass.

## 13. Predecessor operational particulars and remaining deployment evidence

The approved v0.1 draft contained severity/response targets, a review period and drill/retention proposals. This amendment changes none of those operational targets and invents no new time threshold. Confirm their operational adoption in the procedure's accepted deployment record, designate actual support/platform holders through existing arrangements, and retain §11's accepted drill evidence. Approval of a draft is not proof that a real operator has been named or an exercise passed. Do not reintroduce an extra AO business approval for ordinary technical recovery.

## 14. Traceability

| Requirement | Where this procedure serves it |
|---|---|
| Incident declaration | §4 |
| Authorised support access | §3, §5 |
| Permitted diagnostics | §6 |
| Recovery without exposing sealed contents | §1.4, §7 |
| Evidence preservation | §8 |
| Escalation when opening cannot proceed | §9 |
| Closure review | §10 |
| Test before production | §11 |
| Exceptional access remains a separately reviewed design | §1.3, §12 |

### 14.1 Opening failure reconciliation — change scope, precedence and closure

Current source set: BOP v0.15, TPR v0.23 (editorial proposal over approved v0.22), PRC v0.13, AWD v0.8, TRUST-OPS v0.1, TRUST-ADR v0.6, BDS v0.16, supplied LAW v1.2 and AUTH v1.15. Preserve the separately approved AUTH v1.16 funding controls; the older upload is not a replacement. This proposal changes only failed-opening decisions/recovery, incident access/closure and their owner bindings/tests. BDS, AUTH, TRUST-ADR, LAW, PLN v1.32, REQ v1.20 and BUD v1.17 are untouched. No legal verification item, production gate or implemented follow-up is closed by this document. Current external control registers, operating-profile evidence, code and test reports were not supplied for editing and are not claimed updated. Record successor statuses accurately in the actual current registers when implementing; do not overwrite them with stale copies.

## 15. Approval effect

**v0.1 approval effect (approved 11 October 2026).** v0.1 is approved by the Project Owner. Approval establishes this as the draft incident-recovery procedure for the MVP, subject to §11. It does not establish that the procedure has been tested, that any production gate is met, or that PR-001 is closed: PR-001 closes only when the procedure has been tested and its results accepted.
