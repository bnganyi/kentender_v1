# TRUST-OPS-001 — Sealed-Bid Incident Recovery Procedure

**Draft v0.1 — proposed 11 October 2026; approved 11 October 2026 as the draft procedure.** This document drafts the incident-recovery procedure that TRUST-ADR-001 v0.5 §2B item 6 records as production-readiness item **PR-001**. It is a procedure for people, not a change to the product: it describes how a failure in sealed-bid handling is declared, investigated and recovered **without anyone reading a sealed bid**. It is not operational until the Project Owner approves it and it has been tested as §11 requires.

| Control | Value |
|---|---|
| Document ID | TRUST-OPS-001 |
| Title | Sealed-Bid Incident Recovery Procedure |
| Version | 0.1 |
| Date | 11 October 2026 |
| Status | Approved — 11 October 2026 as the draft procedure; not operational until tested (§11) |
| Approved on | 11 October 2026 |
| Approval record | Project Owner, 11 October 2026: “Mark the documents as approved”, answering the report of the proposed set BDS-CHG-001 v0.16, TPR-CHG-001 v0.20, STD-TPL-001 v0.17, BOP-CHG-001 v0.15, TRUST-ADR-001 v0.6, AUTH-ADR-001 v1.15, SEED-002 v0.7 and TRUST-OPS-001 v0.1. The proposals each carries in full are approved with it. |
| Supersedes | Nothing (first version) |
| Owner | Project Owner (approval); Opening access support (operation) |
| Implements | Register item PR-001; TRUST-ADR-001 v0.5 §2B items 4 to 6 |
| Depends on | TRUST-ADR-001 v0.5 (proposed); BOP-CHG-001 v0.14 (proposed) §6 and the incident workflow; BDS-CHG-001 v0.15 (proposed) §12.3; AUTH-ADR-001 v1.14 (proposed) §8 |
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
4. **Two people for any decision that changes the course of an opening.** Support restores services; the Accounting Officer decides how a paused opening proceeds; the committee chair runs the ceremony. No one person does all three (BOP-CHG-001 v0.14 §6; support never acts for the committee).
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

1. **Who may work an incident.** Only a Technical Operator whose assignment is in force. Administrator, System Manager and every other role cannot open an incident’s details.
2. **How access is given.** There is none to grant: the assignment is the authority. A person without it cannot be given the details by sharing a screen or a file; if more help is needed it is arranged by assigning a holder (an ordinary responsibility assignment).
3. **What support may do.** Read the incident summary on the opening page; open the incident’s **details** by an explicit request that names a purpose (*Investigate the problem*, *Record the resolution*); read the diagnostics of §6; restore services under §7; record that an incident is resolved or cannot be fixed.
4. **What is recorded.** Every opening of the details is recorded with the person, the time, the incident, the action, the purpose and the outcome — also when it was refused — and an export of incidents is recorded the same way. A page refresh records nothing. The trail holds no incident content and is read only by the Auditor and the Accounting Officer.
5. **What support may not do.** Read, search, export or restore a sealed bid or its attachments; count bids; look up a bidder; read sealed tables through the database; copy a package off the server; or accept a request to do any of these from anyone, including a senior officer. A request to do so is itself recorded as part of the incident (§8) and refused.

## 6. Permitted diagnostics

| Diagnostic | Why it is permitted | Never includes |
|---|---|---|
| Service availability and health status | Shows what is down | Any bid or bidder |
| Incident reference, kind, timing, notice state and attempts | Shows what happened and when | The identity of a bid |
| Error codes and service logs **with sealed content redacted** | Shows why a service failed | Bid content, signatures, attachments |
| Queue depth, job states, scheduler state | Shows whether work is stuck | Payloads |
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
5. Record the resolution (or that the incident cannot be fixed) and tell the Chair; the Chair then uses **Retry opening**.

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
3. **The Accounting Officer’s options** are those the Bid Opening decision item and the Tender lifecycle already provide (BOP-CHG-001 §7 and TPR-CHG-001 for cancellation); this draft does not enumerate or extend them. The Accounting Officer records the decision and reason.
4. **Tell the bidders.** When an opening is delayed or not held, the Procuring Entity communicates to bidders through the Tender’s existing notice route. **Not verified against the primary source:** any legal minimum for such a notice or for a revised opening time.
5. **Never** open by hand, in person or by any route outside the opening process because the system cannot. If the opening cannot be done with the controls intact it is not done.

## 10. Closure review

1. **When an incident may close.** Support has recorded the resolution (or the Accounting Officer has decided under §9), the service is verified by the §6 diagnostics, the evidence set is complete and its digest recorded.
2. **Who reviews.** The Accounting Officer and the Auditor, with the Incident lead presenting.
3. **Within. [New]** Five working days of closure for a Critical or High incident.
4. **The review confirms:** the timeline against the targets; that no step in §7.4 was taken; that every access to details is in the trail with a purpose; what the root cause was; what changes (service, procedure, test) follow; and whether the register or a requirement document needs a change.
5. **Outcome.** A short written review filed with the incident’s evidence; follow-up actions have an owner and a date. A breach of §7.4 is reported to the Project Owner.

## 11. Testing before production

The procedure is not operational until it has been tested and the Owner has accepted the results.

1. **Tabletop exercises** (all roles in a room, a scripted scenario, no systems touched): (a) Package mismatch at the start of an opening; (b) opening profile down at the deadline; (c) submission service down in the last hour before a deadline; (d) a request from a senior officer to “just look” at a bid; (e) the Incident lead is unavailable. Pass: each role states its next action, the right person decides, and (d) is refused and recorded.
2. **Technical drills on a non-production site that carries test data only** — one per row of §7.2, using the test controls that already exist for opening-profile, notice-delivery and issuer faults. Pass: the incident opens once, the notice is delivered or re-sent, the diagnostics of §6 are enough to restore, nothing outside §6 is used, the Chair can retry, and the access trail shows exactly the reads made.
3. **Access drill.** Prove, on the non-production site, that Administrator and a System Manager cannot read an incident, its details, its count or the trail; that the support holder can read details only after naming a purpose; and that a refused attempt is recorded.
4. **Restore drill.** Restore a backup into sealed custody on a non-production site; show integrity by digest comparison only.
5. **Evidence.** Each exercise produces a dated record: scenario, participants, steps, result, defects. **[New]** Repeat the tabletop yearly and after any change to the opening or custody services.
6. **Sign-off.** The Owner accepts the results in writing; failures are fixed and the failed exercise repeated.

## 12. Exceptional access to sealed contents (not provided)

No exceptional access to a sealed bid exists in the MVP and none is created here. If the Owner ever wants one, it needs its own design, reviewed separately, which must preserve the authorised-opening controls and define at least: who may ask and who must approve (dual control, never the requester); the reason; the narrowest scope; the shortest expiry; the evidence it must leave; how the bidders’ confidentiality and the opening’s integrity are protected; and its legal basis (**not verified against the primary source**). The existence of this section is not a design for it. Its absence does not justify an administrator bypass.

## 13. Open decisions for the Project Owner

1. Approve the severity classes, time targets and the five-working-day review period (§4, §10) or give others.
2. Name the Platform operator and the Incident lead arrangement (§3).
3. Fix the evidence retention period (§8 item 5); the statutory period, if any, is not verified.
4. Decide whether the Head of Procurement Function should be a standing recipient of Critical incident notices (§9 item 2 shows them as informed only).
5. Accept the test plan (§11) and set when it must pass relative to the production switch.

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

## 15. Approval effect

**v0.1 approval effect (approved 11 October 2026).** v0.1 is approved by the Project Owner. Approval establishes this as the draft incident-recovery procedure for the MVP, subject to §11. It does not establish that the procedure has been tested, that any production gate is met, or that PR-001 is closed: PR-001 closes only when the procedure has been tested and its results accepted.
