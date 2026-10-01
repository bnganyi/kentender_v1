# AWD-CHG-001 — Award

| Control | Value |
|---|---|
| Version | 0.4 |
| Date | 30 September 2026 |
| Status | **Proposed requirements — Project Owner review** |
| Supersedes | v0.3; prior versions retained |
| Revision | Resolves the reviewed workflow, dialog, language and ownership gaps; change records in §§18.1–18.3 |
| Basis | Award scope accepted in the conversation on 30 September 2026; this detailed document is not yet approved |
| Product | MVP 1: Open Tender for straightforward IT goods; one lot; KES; fixed price; lowest evaluated responsive tender |
| Starts with | The exact signed Evaluation report and supporting record delivered to the Head of Procurement |
| Ends with | A recorded no-award outcome, or delivery of the Award package to Contracting when the applicable conditions permit |
| Standards | KT-STD-001 v1.12 approved; TRUST-ADR-001 v0.1 approved; source and proposed interface versions identified in §17 |
| Implementation / verification / release | Not started / Not started / Not approved |

## 1. Governing decision and disposition

**KenTender prepares the award decision from the signed Evaluation report, supports the Head of Procurement’s professional opinion and the Accounting Officer’s decision, issues the required notifications, and controls when the procurement may proceed to contracting. People exercise judgment and take responsibility for their decisions. The system handles routine checks, document preparation, delivery and tracking.**

The ordinary workflow is:

**Receive Evaluation report → sign professional opinion → record award decision and issue notices → record supplier acceptance and complete the required wait → send to Contracting.**

Receipt, checks, preparation, tracking and final delivery are automatic. There is no separate acceptance of the incoming report, approval to start Award, approval of each notice, or approval to send an eligible package to Contracting. An officer reviews a consolidated result and any outstanding issue, with access to the underlying evidence.

The award notice and supplier’s acceptance do not create a contract. Contract preparation, signature and performance remain with Contracting and Contract Management.

## 2. Purpose, outcomes and exclusions

Award shall produce an attributable professional opinion, a reasoned Accounting Officer decision, correct bidder notices with delivery evidence, the supplier’s written response, and a complete next-stage record. It must also give an honest outcome when no award can proceed.

For an unresolved lowest-price tie, section 131(a) of the checked 2022 Act identifies competitive negotiation as a possible lawful route, subject to its conditions. HOP refers the unresolved tie and possible route to AO in the signed opinion with **No current recommendation**. AO uses **Record no award** and records a concrete HOP next action: **Prepare a lawful next procurement step for the Accounting Officer’s decision.** That follow-up is outside MVP 1; no separate referral action is required. The product neither selects a winner nor starts negotiation.

MVP 1 excludes negotiation, revised offers, discretionary scoring, multiple lots, selecting an alternative supplier directly, changing the submitted tender sum, contract drafting/signing, performance-security verification, invoicing and contract administration. A lawful route outside this scope requires a separately controlled process; it cannot be simulated by editing this Award record.

The system uses explicit rules and calculations. AI interpretation must not decide compliance, select a supplier, resolve a legal restriction or compose an unsupported reason. Draft narrative uses recorded facts and approved wording; the responsible officer supplies judgment.

## 3. Ownership and dependencies

| Owner | Award uses | Boundary |
|---|---|---|
| Evaluation | Exact report version, all required signatures, recommendation or qualified outcome, bid comparison, reasons, annexes and later correction notices | Findings, rankings and submitted amounts remain read-only. Returns follow EVL’s correction process. |
| Tenders | Issued documents and definitions, effective addenda, validity, published notice/acceptance/security terms, authoritative suspension and cancellation events | Tenders owns validity extensions and pre-notification cancellation. Award does not create a competing cancellation command. |
| Bid Submission / supplier authority | Current submitted bid identity, organisation, mandatory notice contacts, authorised supplier users and retained authority evidence | An account or representative role alone does not confer authority to accept an award. |
| Budget | Authoritative current funding position and any applicable restriction | Award checks funding; it cannot create a reservation, move money or clear a funding restriction. |
| Award | Professional opinion, decision, award notices, acceptance, debrief correspondence, restriction record and Contracting delivery | No re-evaluation or contract formation. |
| Trust | Exact-document signing and verification, trusted timestamps and recovery | A normal authenticated decision is not described as an advanced electronic signature. Test proof is visibly labelled. |
| Procurement Proceedings | Indexed, retained source records and their access rules | Indexing does not create a new approval or copy confidential material into a public view. |
| Contracting | Durable receipt and subsequent contract preparation, security checks, signing and statutory contract publication/reporting | Must recheck current authority and restrictions before contracting. An Award package is not permission to ignore later events. |

**Entry contract.** EVL’s successful delivery creates one Award case and the Head of Procurement’s **Prepare professional opinion** task against the exact report. The EVL **Review evaluation report** task, if already created by its delivery contract, becomes this same linked work item; do not create two acknowledgements. A failed Award receive leaves a durable delivery retry with the original identity and a named technical incident owner. It does not ask the committee to sign again. An empty opening produces no Evaluation report and therefore no Award case.

## 4. Canonical domain model

These records are the complete MVP 1 Award write model. The publication obligation belongs to Contracting under §5.8 and AWD-IF-05; it is not an additional Award record. Do not add fields without a named rule or output.

| Record | Required facts and validation | Used by |
|---|---|---|
| Award case | Generated identity; tender and lot; source report identity/version and artifact hashes; received time; current decision-cycle number and stage; record revision; references to open issues, opinion, decision and delivery | Every screen, command and history. One case per tender/lot; source revisions remain linked. |
| Decision cycle | Sequential number within the same case; predecessor cycle; authorising AO correction record when not the initial cycle; report/opinion/decision references; stage and terminal outcome | Current work and tracker in §5.9. Initial receipt creates cycle 1 automatically; no separate case, manual start or approval is added. A completed cycle remains immutable. |
| Professional opinion | Numbered version; exact report; HOP identity; conclusion; reason; addressed issues; exact document; personal signature proof and time | AO decision and package. Conclusion: Recommend award / No current recommendation. Return for correction is a separate action, not an opinion that must be signed. A signed version is immutable. |
| Decision | Numbered version; AO identity and time; exact opinion/report; Award / No award / Return for correction; reasons; supplier, current submitted bid and amount only for Award; approved notice batch and terms | Notices, authority status, package. An Award must match the supported recommendation and published treatment. |
| Retained decision event and delivery record | One immutable `AwardDecisionRecorded v1` event per committed Award/No award decision version; payload defined in §5.8; stable event identity, recipient, retained delivery attempts/results and durable recipient receipt | Created atomically with the decision by the §7 commands. Failed delivery retries the same event; no duplicate event on command retry. Receipt completes event delivery, not publication. This technical delivery record adds no user entry or approval. |
| Notice batch and recipient record | Exact decision/version; generated notice bytes and version; recipient bid/organisation; contact snapshot; required channels; issue identity/time; channel attempts, outcomes and authoritative giving evidence | Delivery, bidder view and legal clocks. One logical recipient notice per decision and bidder; retries retain that identity. |
| Supplier response | Notice identity/version; Accept / Decline; authorised person and authority evidence; exact written response; receipt time; late flag | Acceptance display and eligibility to proceed. One operative acceptance per current notice; later correspondence remains separately recorded. |
| Issue / restriction | Source event identity; type; scope; authoritative evidence; effective and received times; responsible owner; open/resolved state; reasoned resolution with evidence | Decision, notice and Contracting guards. Types: Source correction, Funding, Validity, Delivery, Debrief, Review/order, Supplier response, Service failure, Rules and notice audience. The last type covers an unverified legal/rule profile or unresolved recipient treatment. Review/order also records the basis: Authoritative order / Reported challenge. It is consumed by the hold label and resolution guards in §5.6; unsupported authority evidence cannot be classified as an authoritative order. |
| Correspondence | Bidder and case; request/reply; attachments; received/sent times; closure reason/time; immutable original content | Debrief and related records. No unseen edit of sent correspondence. |
| Contracting package | Exact report, opinion, decision, notice batch, giving evidence, response, published contract mappings/terms, restriction history and current check results; package version/hash; durable recipient receipt | Contracting and proceedings. No package assembled from a mixture of versions. |

Clocks are derived from retained authoritative events and the applicable legally verified rules, not entered as arbitrary dates. A clock record retains its rule/version, triggering evidence, timezone, calendar treatment, calculated deadline and any lawful revision. The issued tender supplies its acceptance period and related terms; Award cannot invent a different period.

## 5. Lifecycle and business rules

### 5.1 Receive and prepare

The incoming package must identify every required report signature and the exact report/annex set. A missing, mismatched or unverifiable artifact creates a source issue automatically. HOP sees the reason and owner; there is no **Report source issue** step for something the system already detected. HOP may save a draft or return the report, but cannot sign an opinion whose required source record is incomplete or unverifiable.

Read-only checks cover source completeness, current tender status, validity, funding, the recommendation’s consistency with the published award method, outstanding corrections and supplier identity. Distinguish an established restriction from an unavailable check. Neither permits an unsupported positive decision.

The supported product is template key `IT-EQUIPMENT-OPEN-V1`, product profile `GOODS-IT-SIMPLE-V1`, as confirmed in approved STD-TPL-001 v0.10. Do not assume that its release 1.1 is installed or that a current deployment supports Award merely because the document names it.

### 5.2 Professional opinion

The system prepares the opinion from the signed report, ranking, proposed outcome and known issues. HOP reviews those facts and writes the professional conclusion and reasons. It must be possible to disagree with the committee while preserving its recommendation verbatim.

HOP personally signs the exact opinion through the shared signing service. A successful proof completes HOP’s current opinion task and creates the AO’s **Decide award** task atomically with the signed opinion. In a post-decision correction cycle, it creates **Decide correction** instead; the original decision remains on hold. There is no second **Submit opinion** action. Failed or uncertain signing preserves the draft and resolves through the original signing attempt; it is never shown as signed.

HOP uses **Return report** for a disagreement requiring changed findings or a different ranking. This sends the stated issue to Evaluation before a positive decision; HOP does not sign an opinion merely to return the report. A factual report with no current recommendation, including expired validity, can receive a signed opinion and a reasoned no-award decision. Signing that opinion must not be blocked merely because a positive award is blocked.

### 5.3 Accounting Officer decision

The AO reviews the same signed report and opinion, including any dissent, restrictions, proposed supplier, submitted sum, evaluated amount and notice previews. The two amounts remain distinctly labelled when evaluation adjustments apply. No corrected arithmetic silently changes the submitted tender sum or award amount.

The AO can:

- **Award and notify bidders**: record the reasoned award decision and authorise the exact generated notice batch in one action;
- **Return for correction**: state the specific issue and return it to HOP without issuing a notice; or
- **Record no award**: record why an award cannot currently be made and its next disposition.

The decision is an attributable authenticated AO act under the shared authority model. MVP 1 does not invent a statutory signature requirement for this decision. Where the verified issued form requires a signature, the same action obtains exact-target Trust proof before commitment; it does not add another business approval.

There is no supplier picker, price editor or routine tender committee approval. For a positive decision, the supported supplier must be the eligible lowest evaluated responsive tenderer under the published rules. A tie without an applicable published resolution, an unresolved material discrepancy, unsupported funding or no current recommendation prevents the positive action. The AO can still return or record no award with reasons.

A return is not a final award decision. A committed Award or No award is a downstream decision for EVL’s post-decision correction rule. The return action completes the AO task and sends HOP a single **Resolve returned decision** task. HOP either revises the opinion, or sends the identified source matter to Evaluation. A changed source report makes an uncommitted opinion or decision draft out of date. Preserve the draft text for comparison, but require review against the new report. Retain any signed opinion as superseded and require a new signed opinion. Returning to Evaluation closes the superseded opinion/decision task and links the existing Evaluation correction task; receipt of its successor report creates one current HOP opinion task.

### 5.4 Notices and delivery

Generate the successful bidder’s notice and every unsuccessful bidder’s notice from one decision, the signed findings and the issued forms. Include the tender, decision, successful supplier, correct amount where the form requires it, the recipient’s result and reasons, applicable response deadlines, and the published review/debrief information. Do not expose another bidder’s confidential evidence or internal deliberations.

The audience reconciles to all persons who submitted tenders under the applicable section 87 treatment. Use BDS’s authoritative submission and withdrawal history, not the candidate-registration list or Evaluation’s responsive-only list. The verified audience rule must explicitly settle withdrawn/replaced submissions; replacements must not receive duplicate notices. Missing contact or unresolved audience treatment prevents issue and names HOP as the business owner. Draft-only candidates do not become unsuccessful bidders.

Issue the complete authorised batch as one coordinated operation. A supplier cannot be deliberately notified ahead of the other required recipients. Where the approved channel includes the portal, publish every recipient’s notice atomically, then dispatch the corresponding external channel jobs together. Physical or other required channels retain their own evidence. A queued job, email service acceptance, portal creation or read receipt is not automatically legal proof of giving; the verified channel rules decide that fact.

Record **Notices awaiting confirmation** until every required recipient/channel has the required giving evidence. Only then show **All bidders have been notified**. Before then show **A required notice is not yet confirmed.** with the specific delivery or evidence problem. These labels are projections of the legal-evidence result, never aliases for an email-send status. Retry delivery automatically using the same logical notices. HOP handles a bad address through a recorded correction from the authoritative contact owner; technical support handles service failure. Contact correction changes delivery routing only, never signed content or the supplier’s identity. Preserve the old address and every attempt.

The authoritative notification status distinguishes **Not issued**, **Issue in progress**, **Issued**, and **Unknown**. Once any required notice is given, the pre-notification cancellation route is unavailable. This is the chosen conservative MVP treatment of the section 63 cut-off, recorded in the legal operating profile; it is not a claim that the Act defines a separate first-recipient event. A shared serialised issue/cancellation transition prevents cancellation from racing with publication or an external send. A worker must verify that transition before the first outward effect. In-progress or unknown status cannot be treated as no notification. Recover an interrupted issue before allowing either route to proceed.

No additional HOP **Release notices** approval follows the AO’s action. If signing, receipt or sending fails, show precisely which fact is complete; a signed opinion, recorded decision and given notice are three different facts.

### 5.5 Acceptance, waiting period and validity

The successful supplier’s active Authorised Signatory can provide written acceptance of the exact award notice using **Accept award**, or a written refusal using **Decline award** and a reason. Show: **Accepting this award does not create a contract.** A representative can read the notice and submit a debrief request but cannot accept or decline for the organisation without that authority.

Acceptance records identity, authority, exact wording and trusted time. It does not re-sign the original bid. The verified notice/form determines whether additional signature proof is required. A late response is retained as **Received after the deadline** and creates HOP review. In MVP 1 it cannot satisfy the timely-acceptance condition in §5.8; HOP records the next action, and any change to the award requires the AO correction route. No local extension, backdating or reason-only override makes it timely. Show **Your response was received after the deadline. It cannot be used to proceed with this award.** Once the reply deadline has passed with no response, close the supplier’s response task and create **Resolve supplier response** for HOP. Timely acceptance or refusal completes the supplier’s response task. A late response is still retained after the task closes; it updates the same HOP issue rather than creating another task. Do not call silence a refusal or automatically select the next bidder.

Apply the section 135 minimum of fourteen days following giving of the section 87 notice, the period specified in the notice, current tender validity and any additional applicable published/legal rule. The precise counting, deemed-service and holiday rules must be verified in the legal operating profile before production. Do not use a generic fourteen-day browser timer as legal clearance. In a batch with delayed giving, conservatively prevent progress until all affected recipients’ applicable minimum periods have ended; retain each calculation.

The system checks conditions again at decision, actual issue and Contracting delivery. A decision recorded before expiry does not authorise giving a notice after expiry. Tenders owns any lawful extension under section 88. The checked 2022 Act, section 88, permits an AO extension before expiry, once only, for no more than thirty days, with written notice to every tenderer. Tenders supplies the extension decision, prior-extension count, duration and notice evidence, checked against the effective legal profile; Award cannot retrospectively revive an expired tender.

Expiry never erases the record or prevents a factual no-award outcome. Show **Tender validity has expired. No award can proceed.** A pending notice batch or delivery is stopped from further positive advancement and referred to HOP. Already given notices remain visible. HOP records the facts and proposed next action; AO decides any change to the award or procurement outcome; the system does not pretend they were withdrawn.

### 5.6 Debrief, review and suspension

A bidder’s **Request explanation** opens correspondence for HOP about that bidder’s result. HOP prepares and sends a reasoned response using the recorded findings and permitted disclosure. This request is not a filing with the Review Board, does not waive review rights and does not itself impose a statutory suspension. Show the published formal review information separately.

Use the issued tender and verified rules for debrief deadlines and any consequent waiting-period extension. Do not invent universal three-day or five-day rules. A missing applicable rule or unresolved effect on the waiting period prevents Contracting delivery until HOP records the supported disposition. HOP uses **Send and close** to send the final response. Close the request only after the required dispatch evidence is recorded, complete its task, preserve the conversation and show **This request is closed.** If dispatch fails, show **The reply has not been sent. This request remains open.** and retry the same reply; do not require HOP to approve it again. Later correspondence is a new linked request; it cannot silently alter the closed response or existing clocks.

HOP uses **Record restriction** to record received Board/court notices and orders with their source, effective time and scope. It invokes `RecordExternalAwardRestriction`; system-originated events use `ReceiveAwardRestriction`. The system immediately applies an authoritative suspension or restriction to the affected case and informs Contracting if already delivered. A reported challenge awaiting verification creates an internal precautionary hold, clearly distinguished from a statutory suspension. HOP records verification and the supported outcome. A reported challenge can be resolved as unsubstantiated with evidence, or linked to a verified authoritative order. An authoritative order can be marked ended only from the operative release/expiry evidence and checks for continuing restrictions. These records do not grant HOP power to revoke an order or change the award. No hold ends through silence or an unsupported timer.

An order is not cleared merely because fourteen days passed or a displayed hearing date ended. Resumption requires the operative disposition and checks for any continuing order or appeal restriction. The system does not decide legal merits.

### 5.7 Corrections, no award and cancellation

Before a downstream decision, HOP may return a report through EVL’s reasoned return contract. Preserve the prior report and all signatures. The new Evaluation report creates a numbered successor, fresh committee signatures and a new opinion; it never replaces bytes underneath existing proof.

After an Award or No award decision, a new opening supplement or Evaluation correction creates HOP’s **Review report correction** or **Review opening update** task and an immediate hold on further issue/delivery. Preserve the original decision and notices. HOP records the impact and proposed next action. The automatic hold needs no separate approval. HOP may close a non-material issue with evidence that the current decision remains supported. A change to that decision, or authority to obtain corrected evaluation after a decision, goes to AO as **Decide correction**. AO records any changed award decision through a new numbered decision with its lawful basis. If a changed award requires renewed evaluation, use the controlled Evaluation correction route authorised by that disposition, not the ordinary pre-decision reopen. No direct ranking edit or supplier substitution is allowed. A changed decision issues no notices by itself. Revised notices and any restarted/extended clocks require a verified legal treatment. Only when that treatment, exact revised batch, recipients and clocks are complete may the AO correction action authorise the batch, in the same action as the corrected decision when all inputs are ready; otherwise the new decision is retained on hold with notification authorisation absent. Once the missing treatment is settled, the same AO correction command may authorise the exact batch without creating a duplicate award decision. Dispatch then uses IssueAwardNotices and the same guards as ordinary issue. If that treatment is outside MVP 1, hold the case for the named lawful process; do not invent an override.

**Record no award** closes the current decision cycle and its opinion/decision tasks with a reason and one concrete next task for HOP, such as resolve funding, review whether the tender should be cancelled, or arrange a new procurement. Store that task’s action, owner and completion evidence; free text such as “arrange a lawful next step” is insufficient. It is not itself statutory cancellation and sends no successful-award notice. Any required communication of termination is owned by Tenders under its section 63 process. A later correction creates only a linked HOP review item while the current cycle remains Closed. Only an evidenced AO instruction through RecordAwardCorrectionDecision may authorise a successor cycle on the same case. It records the lawful basis, exact sources and required correction; it does not revive validity, reverse cancellation, alter the closed cycle or permit an award. The new cycle starts in Opinion, blocked if a corrected report is required. There is no successor case and no automatic reopening merely because correspondence arrived.

For a valid Tenders cancellation event, close pending Award tasks, preserve all work and show **This tender was cancelled. Award ended.** The shared Evaluation cancellation wording remains **Evaluation ended**. An invalid, stale or unavailable cancellation status cannot close a case. After notification, use the applicable authoritative legal disposition; do not force the event through the pre-notification cancellation command.

### 5.8 Send to Contracting

Automatically deliver when all of these are established:

1. A current supported award decision and its exact opinion/report exist.
2. All required notices have been given, with evidence.
3. The current award has timely, valid written acceptance.
4. Every applicable waiting period has ended.
5. Tender validity and the notice’s contracting window remain current.
6. No unresolved source correction, funding restriction, relevant debrief effect, review/order or service uncertainty prevents progress.
7. The package is complete and the Contracting receiver can durably accept it.

The package includes the issued requirement and supplier response mappings needed for the contract, delivery/warranty commitments, applicable reservation treatment, published performance-security terms, tender-security references, and all current restrictions. Eligibility-only declarations do not become contract obligations.

Contracting owns performance-security submission/verification before contract signing, statutory contract publication/reporting under section 138 under the AO’s responsibility, and the documented security-release/forfeiture process or its named institutional owner. Assigning publication work to Contracting does not defer its legal trigger until contract signature or full Award-package delivery. The verified operating profile must specify the trigger, deadline and recipient owner. The triggering decision/event creates a durable publication obligation for that owner even if contract preparation is still waiting; unavailable delivery is an incident, not a postponed legal deadline.

**Publication owner contract (AWD-IF-05).** Committing an initial or corrected Award/No award decision atomically retains an `AwardDecisionRecorded v1` event for durable delivery to Contracting, independently of the full Award package and its eligibility gates. The event contains a stable event identity, case/tender/lot, cycle and decision version, decision outcome, AO and recorded time, exact decision/document references, applicable legal-profile version, and supplier/amount when applicable. A return for correction is not an award decision event. Contracting’s proposed `ReceiveAwardPublicationEvent` operation records one receipt per event and creates or updates its own publication obligation when the verified profile makes that event a publication trigger. Receipt alone is not publication; a No award event must not manufacture a contract-publication obligation. Other legal triggers remain with their owning service and must be retained and assessed under the same verified profile. Contracting owns the obligation’s trigger evidence, legal rule/version, due time, responsible owner, linked decision versions and completion evidence. Its proposed `RecordContractAwardPublication` operation discharges the obligation only with evidence of the required publication/reporting. A corrected decision preserves earlier obligations and evidence and applies the verified correction treatment. Failed delivery retains the original event for retry and names a technical incident owner; it cannot move the legal trigger or deadline. These are proposed Contracting operations, not Award commands or an additional business approval.

Award only passes the requirements and evidence; it does not demand performance security as a new precondition to the Award handoff. A missed acceptance date does not automatically forfeit tender security. For a declined award, HOP records whether section 136 refusal-to-contract treatment may apply and refers any procurement decision to AO. A section 87 award decline is not automatically classified as refusal to sign a contract. Section 136’s next-lowest-tenderer and security consequences, and its expired-validity exception, require the supported legal determination by the responsible owner. MVP 1 neither substitutes a supplier nor forfeits security from the decline action.

**Sent to Contracting** requires a durable recipient record and one **Prepare contract** task for the designated Contracting owner. An unavailable receiver leaves **Waiting to proceed**, preserves the package and retries automatically. It never asks HOP to approve transmission. Recheck every eligibility condition before each delivery attempt. If circumstances change during an outage, keep the package on hold and show the current reason; restoration of service alone does not authorise delivery. Later orders, corrections or validity changes are delivered as separate immutable updates with required consumer acknowledgement and a task; they do not rewrite the original package. Contracting must check the current authoritative status immediately before any positive contracting action.

### 5.9 Stages, next steps and work items

The internal record has five journey labels: **Opinion → Decision → Notices → Acceptance and wait → Send to Contracting**. Stage markers are Done, Current, Blocked or Not started. Stored stages are Opinion, Decision, Notices, Waiting to proceed, Sent to Contracting and Closed. Conditions such as suspended, overdue or awaiting correction do not create extra stages. After durable delivery all five journey markers are Done; the separate next step names the Contracting owner. **Closed** is a terminal outcome for that decision cycle; the case displays the current cycle’s stage. A successor is possible only under §5.7, preserving the earlier terminal outcome; do not mark unperformed stages Done. Supplier views use their own result and next action, without the internal journey tracker. The Acceptance and wait stage covers the supplier response and all conditions to proceed; it must not imply that acceptance waits until the minimum period ends.

| Current stage | Completion or return | Next stage |
|---|---|---|
| Opinion | Exact current opinion signed | Decision |
| Decision | AO records Award and authorises notices | Notices |
| Decision | AO returns comments | Opinion |
| Opinion or Decision | Report returned to Evaluation before a committed decision | Opinion, blocked pending corrected report |
| Notices | All required giving evidence received | Waiting to proceed |
| Waiting to proceed | Every §5.8 condition met and recipient receipt recorded | Sent to Contracting |
| Decision | AO records No award | Closed; named follow-up task remains |
| Any stage before delivery | Valid authoritative cancellation | Closed; preserve completed work and mark the interrupted journey stage Blocked |

A hold preserves the current stage and marks the affected journey stage Blocked. A supplier can respond to their current issued notice while delivery to another bidder remains pending, unless a restriction prevents that response; the recorded response does not complete the Notices stage. A later restriction after delivery preserves Sent to Contracting and its completed tracker while identifying the receiving owner’s outstanding task.

**Tracker mapping.** Opinion, Decision and Notices mark their corresponding journey step Current (or Blocked), earlier performed steps Done and later steps Not started. In Waiting to proceed, while any §5.8 condition 1–6 is unmet, Acceptance and wait is Current for an ordinary pending reply/wait or Blocked for an unresolved restriction; Send to Contracting is Not started. Once conditions 1–6 hold, Acceptance and wait is Done and Send to Contracting is Current while the system prepares/transmits the package, or Blocked if package preparation or receiver availability fails. Receiver unavailability is assessed under condition 7, not double-counted as condition 6 uncertainty. Every retry rechecks 1–6; if one fails, markers return to the corresponding Acceptance and wait condition without erasing the earlier events. Receipt makes all five Done. Closed cycles retain performed steps and their terminal explanation.

**Correction-cycle mapping.** A review item alone does not change the current cycle’s stage or its source versions. HOP and AO tasks are displayed alongside that cycle’s held tracker. The following rules apply to both an Award cycle and a No award cycle:

| Event / owner action | Case and cycle result | Task and tracker |
|---|---|---|
| Source correction received | Existing cycle stays at Notices, Waiting to proceed, Sent to Contracting or Closed, as applicable | HOP Review report correction / Review opening update. Undelivered award remains held; delivered/closed tracker stays historical. |
| HOP confirms no material effect | Close only that review item; retain current cycle and decision | Recheck other guards before resuming; no new cycle or AO approval. |
| HOP proposes corrected evaluation or changed decision | Existing cycle remains unchanged and held | AO Decide correction; no marker reset yet. |
| AO authorises reconsideration or corrected evaluation | Create one numbered successor cycle on the same case, linked to that instruction; retain predecessor unchanged | Opinion Current, or Opinion Blocked awaiting the authorised corrected report; later steps Not started. Existing EVL owner receives the correction task. |
| Corrected report received | Attach it to the authorised successor cycle only | HOP Prepare professional opinion; Opinion Current. |
| Fresh opinion signed | Successor moves to Decision | AO Decide correction; Opinion Done, Decision Current. |
| AO records supported replacement Award | Successor moves to Notices; predecessor remains historical | Notices Blocked while required treatment is unresolved; Current once the exact batch is ready for AO authorisation and during issue. No dispatch until exact revised-notice authorisation exists. |
| AO returns the successor opinion | Successor returns to Opinion; original decision and hold retained | HOP Resolve returned decision; fresh signed opinion returns to Decide correction. |
| AO records No award | Successor moves to Closed | Opinion/Decision Done; later steps Not started; concrete HOP follow-up. |
| AO declines reconsideration | Existing cycle unchanged; close the proposal with reason | Any independently supported hold remains; no automatic resumption or reopening. |

These are existing correction responsibilities expressed as one linked cycle, not a second routine approval workflow. The current-cycle pointer changes only on the authorised successor event. Cancellation cannot be reversed through this route.

The shared KT-STD-001 §3B next-step projection is authoritative. It includes current stage, holder, available action, blocking reason, resolving owner and linked task. Return all outstanding issues, even when only one leads the headline. Lead with cancellation or a restriction that prevents the actor’s next action. Otherwise lead with their available work, followed by the next scheduled event. Show all outstanding issues and their owners; a delivery outage must not hide an explanation request that HOP can still answer. Viewing a record never completes a task.

| Situation | Next-step text | Holder / task or scheduled outcome |
|---|---|---|
| Report received | Prepare the professional opinion. | HOP / Prepare professional opinion |
| Opinion signed | Decide the award. | AO / Decide award |
| Unresolved equal-price outcome | Review the equal-price outcome. | HOP / Prepare professional opinion |
| AO return | Resolve the Accounting Officer’s comments. | HOP / Resolve returned decision |
| Awaiting corrected report | Evaluation is correcting the report. | Evaluation chair / existing EVL correction task |
| Notice failure | A required notice is not yet confirmed. | HOP / Resolve notice delivery for address or evidence; technical operator / Restore notice delivery for service failure |
| Acceptance pending | The supplier must reply by the date in the notice. | Authorised Signatory / Respond to award |
| Accepted, wait current | The required waiting period is still running. | System / scheduled eligibility check |
| Debrief open | Respond to the bidder’s request. | HOP / Respond to request |
| Review/order active | This award is on hold. | HOP / Review restriction |
| Validity expired | Tender validity has expired. No award can proceed. | HOP / Resolve expired validity |
| Supplier declined | Review the supplier’s response. | HOP / Resolve supplier response |
| Response overdue | The supplier has not replied by the deadline. | HOP / Resolve supplier response |
| Post-decision correction review | Review the report correction before this award proceeds. | HOP / Review report correction |
| AO correction decision | Decide the reported correction. | AO / Decide correction |
| Correction received after No award | Review the correction to the closed award record. | HOP / Review report correction; cycle remains Closed pending AO instruction |
| Revised-notice treatment unresolved | Confirm the required notice treatment before this award proceeds. | HOP / Resolve revised notice treatment, with the legal-rule owner’s input |
| Exact revised batch ready for authorisation | Authorise the revised notices. | AO / Decide correction |
| Late response — supplier view | Your response was received after the deadline. It cannot be used to proceed with this award. | Supplier / read-only response and notice; HOP / Resolve supplier response |
| Awaiting authorised corrected report | Evaluation is correcting the report. | Evaluation chair / existing EVL correction task; HOP waits |
| Corrected report received | Prepare the professional opinion on the corrected report. | HOP / Prepare professional opinion |
| Receiver unavailable | Contracting is unavailable. KenTender will check that the award can still proceed before sending it. | Technical operator / Restore Contracting delivery |
| Delivered | Contracting has received the award. | Contracting owner / Prepare contract |
| No award | No award was made. | HOP / the recorded next action |
| Cancelled | This tender was cancelled. Award ended. | None; closed, reason and record available |

Tasks use source-event identities so retries cannot duplicate them. A new issue cannot be cleared by resolving an unrelated older issue. Expired/replaced authority removes action access and routes the task to the current holder through the shared responsibility service; it never makes Administrator the business substitute.

### 5.10 Fixed issue outcomes

Record restriction requires **Basis for hold**: **Authoritative order** or **Reported challenge**. The first requires the retained issuing authority, operative instruction and evidence; uncertainty uses Reported challenge. The choice classifies the evidence and resulting hold, not a user-created legal power.

Record outcome / Review correction uses the fixed choices below. The server shows only choices applicable to the selected issue and current evidence; no free-text Outcome or generic Override is accepted.

| Outcome | Required basis and effect |
|---|---|
| No material effect | Source correction only; evidence explains why existing findings/decision remain supported. Close that issue only. |
| Request corrected evaluation | Source correction; reason identifies the exact defect. Create AO Decide correction; retain hold until authorised successor work is complete. |
| Request decision review | Proposed change to procurement/award outcome, including expired validity or supplier response; evidence and proposed next action required. Create AO Decide correction after a committed decision, otherwise the current Decide award task. No decision changes here. |
| Restriction ended | Review/order issue; operative authority evidence and continuing-restriction checks required. End that restriction only. |
| Reported challenge not substantiated | Reported challenge only; verification evidence required. Close the precautionary hold, not any separate authoritative order. |
| Owner correction confirmed | Funding, validity, rules/audience, delivery or service issue; authoritative owner receipt required. Refresh guards; never manufacture missing acceptance or change a source value. |
| Further action required | Any unresolved issue; name the next action, responsible existing owner and evidence needed. Keep the issue open; no new approval merely to retain a hold. |

For decline (V06) or no response by the deadline (V07), **Record next action** always records **Request decision review**, with the saved response or missed-deadline evidence attached automatically and HOP’s reason and next action. No Outcome selector or repeated evidence entry is required. HOP can record a proposed next action for decline/late response, but cannot mark it timely or replace the supplier. The AO correction command permits **Request corrected evaluation**, **Authorise reconsideration**, **Record corrected award**, **Record no award**, **Return for correction**, **Decline reconsideration**, or **Authorise revised notices** only as applicable under §§5.7–5.9. **Record corrected award and notify bidders** is the combined screen label for **Record corrected award**, with exact revised-batch authorisation recorded by the same command when all inputs are ready; it is not a separate outcome or approval. Return for correction in a successor Decision stage returns the opinion to HOP in Opinion with specific comments; it does not reopen Evaluation directly. Corrected Award requires a current signed report and fresh signed opinion. Authorise revised notices requires a recorded corrected award and verified exact batch/clock treatment; retries retain the same decision and notice identities.

## 6. Responsibilities and access

HOP prepares/signs the opinion, deals with returned matters, resolves correspondence and records evidenced restrictions. HOP records evidence and proposes next actions. AO decides changes to the award or procurement outcome. HOP may record that an evidenced restriction has ended without making a new award decision; the source authority remains controlling. Evaluation members retain their own module’s correction responsibilities; they acquire no Award decision power. An active supplier signatory acts only for their organisation and own notice. Representatives see their organisation’s notices and permitted correspondence.

Auditors have authorised read access without decisions or unrestricted exports. Technical operators see safe operation identifiers, service outcomes and recovery controls; no bids, prices, opinions or business decisions are disclosed merely by technical role. Public users see only a separately authorised public publication. Never expose the internal award record through a public URL.

Recheck active responsibility, scope, supplier link and signature authority at every action, not just page load. Use AUTH’s existing enforcement; add no per-tender permission grants or new committee approval role.

## 7. Service and command contracts

All writes require a current record revision, active authority and a retry identity. A duplicate accepted command returns its original result. Conflicting concurrent writes return the current record without partially changing it. Receipt of an external event deduplicates by its source identity. Signing commands bind the exact document, version and purpose; stale proof cannot complete a changed action.

| Command / service | Actor and input | Required result and boundary |
|---|---|---|
| `ReceiveEvaluationReport` | System; exact EVL delivery package | One case/source version and HOP task, or durable failure with automatic incident. Never manual source-issue reporting. |
| `SaveProfessionalOpinion` | HOP; conclusion/reasons, source revision | Draft saved; inherited facts unchanged. |
| `SignProfessionalOpinion` | HOP; frozen draft and personal proof | Immutable signed opinion and AO task together: Decide award for the initial cycle, Decide correction after a committed decision. Uncertain proof resolves against the same attempt. |
| `ReturnEvaluationReport` | HOP; issue/reason, pre-decision authority status | EVL return receipt and linked waiting task; no silent reopen after a decision. |
| `RecordAwardDecision` | AO; Award / No award / Return, reasons, exact sources and notice preview set | Attributable decision or return, completing the current AO task. Each committed Award/No award atomically retains its `AwardDecisionRecorded v1` event and delivery record (§§4, 5.8); Return creates no such event. Command retries reuse the original event. Award queues the authorised batch; No award records its concrete HOP follow-up task. Allowed only in Decision with the current signed opinion; an existing committed Award/No award uses the correction route. Required form signature, if applicable, belongs to this same action. |
| `IssueAwardNotices` | System; committed authorisation and batch | Serialised cancellation/status check; coordinated issue, recipient proofs and recoverable attempts. |
| `RetryNoticeDelivery` | System/assigned technical recovery; same notice, corrected authorised route if needed | No new decision or duplicate notice. HOP’s **Correct contact** invokes the contact owner’s correction command and returns its receipt. |
| `RespondToAward` | Active supplier signatory; exact current notice, Accept / Decline and written response | Immutable response and receipt; late/changed-version cases held for review. |
| `RequestAwardExplanation` | Supplier user for own bid; request and evidence | One HOP task and private correspondence. |
| `SaveAwardExplanation` | HOP; request identity and draft reply | Saves only a draft not yet authorised for dispatch. Send and close freezes the exact reply for all delivery attempts; failed or uncertain delivery does not make it editable. |
| `SendAwardExplanation` | HOP; exact final reply and evidence | Retained reply and delivery result; closes request and task only after required dispatch evidence. Failed dispatch retries the same reply and leaves the request open. |
| `RecordAwardIssueDisposition` | HOP; issue, one §5.10 outcome, evidence and proposed next action where required | Applies the outcome’s defined effect; cannot override another owner, legal order, source finding or decision. |
| `RecordExternalAwardRestriction` | HOP; external notice/order or reported challenge, source evidence, basis for hold, scope and times | Records authoritative restriction or precautionary hold distinctly; retains document and routes any uncertainty for review. |
| `ReceiveAwardRestriction` | Authoritative producer; event/evidence | Immediate scoped hold/update and owner task; late receipt preserves effective and received times. |
| `RecordAwardCorrectionDecision` | AO; HOP impact record, lawful basis, exact changed sources | A §5.10 correction outcome and its linked cycle/decision; no mutation of prior decision/notice. Each newly committed corrected Award/No award atomically retains its `AwardDecisionRecorded v1` event and delivery record (§§4, 5.8). Returns, correction instructions, reconsideration outcomes and notice-only authorisations create no decision event unless a new Award/No award decision is committed; command retries reuse the original event. New decisions issue no notices without explicit recorded authorisation within this command for the verified exact revised batch. The initial combined award-and-notify action remains unchanged. A correction instruction retains the hold and original award until the corrected report and fresh opinion support a further AO decision. Unsupported treatment stays held. |
| `RefreshAwardEligibility` | System on event and deadline | Recomputed next step and guards; unknown remains unknown. |
| `DeliverAwardPackage` | System; frozen eligible package | One durable Contracting receipt/task; retry same package identity after failure. |
| `GetAwardAuthorityStatus` | Authorised Tenders/EVL/Contracting consumer | Separate decision and notification facts with revision/evidence; Unknown on unavailable authority, never a fabricated negative. |
| `GetAwardWorkspace`, `GetAwardRecord`, `GetSupplierAwardNotice` | Authorised reader | Scoped projection, current next step and permitted actions; no browser inference. |

The authority-status service returns separate canonical fields. Decision status is **No decision recorded / Award recorded / No award recorded / Unknown**, with current and historical decision references; a return does not become a committed decision. Notification status uses exactly **Not issued / Issue in progress / Issued / Unknown** from §5.4. “No notification issued” is explanatory text for Not issued, not another value. Before an Award case exists, authoritative negative values must come from a durable tender-level record. The tender-level decision status reflects the latest committed decision across all cycles until another is committed. Tender-level notification status cannot return to Not issued after any prior issue; each batch separately retains its own status. Historical decisions/notices remain visible after a successor cycle, so a new cycle cannot make Tenders or EVL infer that no earlier decision or notification occurred. Absence of a case or a failed lookup is insufficient. Tenders and Award share the serialisation needed for cancellation/issue; EVL checks the distinct decision boundary.

## 8. Error contract

| Code | User-facing message | Resolution |
|---|---|---|
| `AWD_SOURCE_INCOMPLETE` | The evaluation report is incomplete. The Head of Procurement has been notified. | Automatic source issue; EVL owner fixes source. |
| `AWD_RECORD_CHANGED` | This record has changed. Review the latest version before continuing. | Reload comparison, preserve unsaved narrative. |
| `AWD_AUTHORITY_REQUIRED` | You are not authorised to take this action. | Current holder shown where disclosure is allowed. |
| `AWD_SIGNATURE_UNAVAILABLE` | Signing is unavailable. Your draft has been saved. | Technical recovery; no false signature. |
| `AWD_NO_SUPPORTED_AWARD` | An award cannot be made from the current report. Review the recorded reasons. | Return or reasoned no-award outcome. |
| `AWD_VALIDITY_EXPIRED` | Tender validity has expired. No award can proceed. | HOP records facts and proposed action; AO decides any change to the award or procurement outcome. |
| `AWD_NOTICE_FAILED` | A required notice is not yet confirmed. | Exact recipient/channel visible only to permitted users; retry owner named. |
| `AWD_ON_HOLD` | This award is on hold. Review the reason and responsible officer. | Resolve source-specific restriction. |
| `AWD_RESPONSE_LATE` | Your response was received after the deadline. It cannot be used to proceed with this award. | Store response, HOP task. |
| `AWD_NOTICE_CHANGED` | The award notice has changed. Review the current notice before replying. | No response recorded against unseen new terms. |
| `AWD_RULE_UNVERIFIED` | The applicable rules have not been confirmed. The award cannot proceed yet. | Named legal-rule owner resolves release/rule evidence. |
| `AWD_CONTRACTING_UNAVAILABLE` | Contracting is unavailable. KenTender will check that the award can still proceed before sending it. | Durable retry and incident. |
| `AWD_STATUS_UNAVAILABLE` | The current tender status could not be confirmed. The system will check again when service is restored. | Fail closed; named incident owner. |

Messages must distinguish a business restriction from technical unavailability. Do not display internal table names, provider payloads, hashes or stack traces.

## 9. UI architecture, menu and routes

| Surface | Route | Purpose |
|---|---|---|
| Award workspace | `/app/award` | Actor’s work list; no journey tracker or record-level guidance block |
| Award record | `/app/award/{award_id}` | Opinion, decision, notices, outstanding work and history on one task-led page |
| Supplier notice | `/supplier/awards/{notice_id}` | Own result, notice, response and explanation request |
| Linked documents | Existing authorised document viewer | Exact version and permitted download; no unrestricted object URLs |

Opinion, decision, delivery detail and correspondence are sections of the record, not additional approval workspaces. My Work uses the same task identities and next-step result. No new dashboard, separate acceptance register or generic workflow designer is needed.

## 10. Static design contract

**Closed input:** KT-STD-001 v1.12 §2 plus this section alone. All fixtures below are synthetic design/test data, not live procurement evidence. Use the shared visual system and prescribed artboard sizes. Do not place requirement IDs, actor-context notes, technical keys or this instruction on the artboard. In test mode the visible environment notice is **Test environment — no live award notices are sent.**

### 10.1 Common fixture and composition

Site: Ministry of Health. Tender: **TND-MOH-2027-033**, **Supply and delivery of business laptops**. Award record: **AWD-MOH-2027-033**. Supplier: **Afya Digital Supplies Limited**. Bid: **BID-MOH-2027-033-001**, **Submitted version 1**. Quantity **250 Each**; submitted tender sum **KES 46,400,000**; evaluated amount **KES 46,400,000**; recommendation **Award to Afya Digital Supplies Limited**. Warranty **36 months**. Report **Evaluation report 1**, received **16 Jun 2027, 14:07 EAT**; committee signatures **3 of 3**. Valid until **10 Oct 2027, 11:00 EAT**. No outstanding source or funding issue in the ordinary branch.

Actors: **Charles Mutiso**, Head of Procurement; **Amina Hassan**, Accounting Officer; **Mary Wanjiku**, Afya’s Authorised Signatory; **David Ouma**, Afya’s Supplier Representative; **Daniel Otieno**, Technical operator. These are distinct people. Fixtures below use EAT. No extra actor or role is implied. For every unspecified internal variant instant use 18 Jun 2027, 10:00 EAT; V03/V04 instead use 11 Oct 2027, 09:00 EAT, V08 uses 20 Jun 2027, 11:00 EAT, V10 uses 2 Jul 2027, 09:01 EAT, and V11 uses 17 Jun 2027, 09:30 EAT. These are isolated branches.

Internal records use the formal-record archetype, one next-step block and the compact journey **Opinion / Decision / Notices / Acceptance and wait / Send to Contracting**. Place the task and next action first, the report/opinion/decision or recipient result second, and source detail/history behind named disclosures. Use ordinary document sections rather than one card per fact. Supplier notice uses the external record archetype and has no internal tracker. Workspace uses a work list, no metrics, tracker or next-step block.

### 10.2 Required artboards

| Board | Actor / instant; exact leading content | Working content and actions | Journey markers |
|---|---|---|---|
| D01 Workspace | Charles; 17 Jun 2027, 08:55. Title **Award** | One row: AWD-MOH-2027-033; tender title; **Prepare professional opinion**; **Charles Mutiso**. Action **Open award**. Empty variant: **You have no award tasks.** | None |
| D02 Opinion | Charles; 17 Jun, 09:00. **Prepare the professional opinion.** | Common report and recommendation facts. Conclusion **Recommend award**. Reason **The signed report identifies Afya Digital Supplies Limited as the lowest evaluated responsive tenderer. No unresolved issue prevents the proposed award.** Actions **Save draft**, **Sign opinion**, **Return report**. Disclosures **Evaluation report**, **Bid comparison**, **Outstanding issues**, **History**. | Opinion Current; rest Not started |
| D03 Decision | Amina; 17 Jun, 10:00. **Decide the award.** | Common facts; **Professional opinion 1**, **Signed by Charles Mutiso, 17 Jun 2027, 09:10 EAT**; exact D02 reason. Decision reason **I accept the recommendation in the signed evaluation report and professional opinion.** Preview **Successful bidder notice — Afya Digital Supplies Limited**. Actions **Award and notify bidders**, **Return for correction**, **Record no award**; disclosures **Professional opinion**, **Evaluation report**, **Notice preview**. | Opinion Done; Decision Current; rest Not started |
| D04 Supplier notice | Mary; 17 Jun, 10:10. **Your tender was successful.** | Tender, Afya, amount, notice **Award notice 1**; **Reply by 24 Jun 2027, 17:00 EAT**; **Accepting this award does not create a contract.** Actions **View notice**, **Accept award**, **Decline award**, **Request explanation**. Acceptance dialog: **Accept this award?**; **I accept Award notice 1 on behalf of Afya Digital Supplies Limited.** Buttons **Accept award**, **Back**. Decline dialog: **Decline this award?**, field **Reason**, buttons **Decline award**, **Back**. | None |
| D05 Wait | Charles; 18 Jun, 09:05. **The required waiting period is still running.** | **Supplier accepted, 18 Jun 2027, 09:00 EAT**; **All bidders have been notified**; **Earliest permitted date and time: 2 Jul 2027, 09:00 EAT**; **KenTender will send the award to Contracting when all conditions are met.** Read actions **View decision**, **View notices**, **View acceptance**. | Opinion/Decision/Notices Done; Acceptance and wait Current; Send to Contracting Not started |
| D06 Delivered | Charles; 2 Jul, 09:00. **Contracting has received the award.** | **Received 2 Jul 2027, 09:00 EAT**; **Next: Prepare contract**; **Contracting owner: Charles Mutiso**. Actions **View award package**, **Open Contracting**. No claim that a contract exists. | All five Done |
| D07 Explanation | Charles; isolated branch 18 Jun, 10:00. **Respond to the bidder’s request.** | Request from David Ouma: **Please explain the recorded award result.** Reply field labelled **Response**. Actions **Save reply**, **Send and close**. Closed variant: **This request is closed.**; reply **The recorded result follows the signed evaluation report. Your tender was successful at KES 46,400,000.**; **Closed 18 Jun 2027, 10:15 EAT**; **View correspondence**. | Same as D05; open request shown alongside current wait |

The ordinary fixture has one submitted bidder. Do not fabricate an unsuccessful recipient in D03. The unsuccessful-notice board below uses a separate isolated two-bid fixture.

### 10.3 Required variants and dialogs

Each internal variant retains D02’s tender/record header, except V18 which uses its stated tender 036 and award record AWD-MOH-2027-036. Retain only common facts relevant to that variant’s task. Replace the next-step text and actions as stated; do not retain an enabled positive action from another board. The full common record remains available through the named disclosures.

| Variant | Exact content and available actions | Journey / actor |
|---|---|---|
| V01 Returned | **Resolve the Accounting Officer’s comments.** Comment: **Explain the unresolved funding concern before recommending an award.** Fields **Conclusion**, **Reason**. **Save draft**, **Sign opinion**, **Return report**. | Charles; Opinion Current, later stages Not started; prior versions in History |
| V02 Source problem | **The evaluation report is incomplete. The Head of Procurement has been notified.** Detail **One required annex is unavailable.** **View source issue**, **Return report**. | Charles; Opinion Blocked; later stages Not started |
| V03 Expired report | **Tender validity has expired. No award can proceed.** Conclusion **No current recommendation**; reason **Tender validity expired before an award could be notified.** **Save draft**, **Sign opinion**, **View evaluation report**. | Charles; Opinion Current; later stages Not started |
| V04 No award | **No award was made.** Reason **Tender validity expired before an award could be notified.** **Next: Charles Mutiso to review whether the tender should be cancelled.** **View decision**, **View evaluation report**. | Charles; Opinion/Decision Done; remaining stages Not started; outcome Closed |
| V05 Delivery failure | **A required notice is not yet confirmed.** Afya; channel **Email**; result **Delivery failed**; owner **Charles Mutiso**; reason **The notice address was rejected.** **Correct contact**, **View notice**, **View delivery history**. | Charles; Opinion/Decision Done; Notices Blocked; remaining Not started |
| V06 Supplier declined | **Review the supplier’s response.** **Declined by Mary Wanjiku, 18 Jun 2027, 09:00 EAT**; reason **We cannot meet the delivery commitment.** **Record next action**, **View response**. Note **The Accounting Officer must decide the next procurement action.** | Charles; first three Done; Acceptance and wait Blocked; Send to Contracting Not started |
| V07 No response | **The supplier has not replied by the deadline.** **Reply deadline: 24 Jun 2027, 17:00 EAT**. **Record next action**, **View notice**. | Charles, 24 Jun 17:01; same markers as V06 |
| V08 Review hold | **This award is on hold.** **Review Board suspension received 20 Jun 2027, 11:00 EAT**; **Responsible officer: Charles Mutiso**. **View restriction**, **Record outcome**. Read-only source **Review Board suspension notice**. | Charles; same markers as V06 |
| V09 Post-decision correction | **Review the report correction before this award proceeds.** **Evaluation reported a material calculation issue.** **Review correction**, **View original decision**. | Charles; same markers as V06 |
| V10 Receiver failure | **Contracting is unavailable. KenTender will check that the award can still proceed before sending it.** **Technical operator Daniel Otieno is restoring delivery.** **View award package**. | Charles; first four Done; Send to Contracting Blocked |
| V11 Cancelled | **This tender was cancelled. Award ended.** **View cancellation**, **View history**. | Charles; Opinion Done; Decision Blocked; Notices/Acceptance and wait/Send to Contracting Not started; outcome Closed |
| V12 Signing unavailable | **Signing is unavailable. Your draft has been saved.** **Technical operator Daniel Otieno is restoring signing.** **Save draft**, **View opinion**. | Charles; Opinion Blocked; remaining Not started |
| V13 Supplier representative | D04 content; **Mary Wanjiku must respond for Afya Digital Supplies Limited.** **View notice**, **Request explanation** only. | David; no tracker |
| V14 Unsuccessful bidder | Tender **TND-MOH-2027-037**, same goods title. **Your tender was unsuccessful.** Afya submitted/evaluated **KES 46,400,000**; successful supplier **Jirani Office Supplies Limited**, evaluated/award **KES 45,900,000**. Reason **Your tender met the requirements. Another responsive tender had a lower evaluated price.** **View notice**, **Request explanation**. | Mary; isolated fixture; no tracker |
| V15 Rule/status unavailable | **The applicable rules have not been confirmed. The award cannot proceed yet.** **Responsible officer: Charles Mutiso**; **View outstanding issue**. Status-service alternative: **The current tender status could not be confirmed. The system will check again when service is restored.** owner **Daniel Otieno**. | Charles; Opinion Blocked; later stages Not started |
| V16 Technical incident | **Restore notice delivery**; **Operation: Award notice delivery**; **Result: Service unavailable**; **Assigned to Daniel Otieno**. **Retry operation**, **View service history**. No tender, supplier, price or business documents. | Daniel; technical work view; no Award journey |
| V17 Correction decision | **Decide the reported correction.** Issue **Evaluation reported a material calculation issue.** Proposal **Request a corrected evaluation report addressing the calculation issue.** Reason **The reported calculation issue may affect the recommendation.** Action **Request corrected evaluation**; **View original decision**, **View correction**. | Amina; first three Done; Acceptance and wait Blocked; Send to Contracting Not started |
| V18 No single recommendation | **Review the equal-price outcome.** Tender **TND-MOH-2027-036**, **Supply and delivery of office laptops**. Afya Digital Supplies Limited and Jirani Office Supplies Limited each **KES 46,400,000**, joint position **1**. **The published tender has no tie-break rule.** **Negotiation is outside MVP 1.** Opinion reason **Refer the unresolved tie to the Accounting Officer for a lawful next step.** Conclusion **No current recommendation**. **Save draft**, **Sign opinion**, **View evaluation report**. | Charles; Opinion Current; later stages Not started |
| V19 Correction authorised | **Evaluation is correcting the report.** **Decision cycle 2**. Reason **The reported calculation issue may affect the recommendation.** **View correction instruction**, **View prior decision**. | Charles; Opinion Blocked, later steps Not started; 18 Jun 2027, 10:05 EAT |
| V20 Corrected report received | **Prepare the professional opinion on the corrected report.** **Decision cycle 2**, **Evaluation report 2**, **Received 19 Jun 2027, 09:00 EAT**. Corrected result **No current recommendation**; reason **The calculation discrepancy remains unresolved.** **Save draft**, **Sign opinion**, **View evaluation report**, **View prior decision**. | Charles; Opinion Current; later steps Not started; 19 Jun 2027, 09:05 EAT |
| V21 Correction after No award | **Review the correction to the closed award record.** **No award was made.** **Decision cycle 1 — Closed**. **Review correction**, **View prior decision**. | Charles; Opinion/Decision Done; later steps Not started; 11 Oct 2027, 10:00 EAT |
| V22 Late response | **Your response was received after the deadline. It cannot be used to proceed with this award.** **Received 24 Jun 2027, 17:01 EAT**; **Reply deadline 24 Jun 2027, 17:00 EAT**. **View response**, **View notice**. | Mary; no tracker; isolated branch |
| V23 Corrected opinion decision | **Decide the reported correction.** **Decision cycle 2**, **Evaluation report 2**, **Professional opinion 2**, **Signed by Charles Mutiso, 19 Jun 2027, 09:10 EAT**. Conclusion **No current recommendation**; reason **The calculation discrepancy remains unresolved.** **Record no award**, **Return for correction**, **View prior decision**. | Amina; Opinion Done, Decision Current; later steps Not started; 19 Jun 2027, 09:15 EAT |
| V24 Revised notices held | **Confirm the required notice treatment before this award proceeds.** **Decision cycle 2**, **Corrected award decision 2**, Afya, **KES 46,400,000**. **The rules for revised notices have not been confirmed.** **View corrected decision**, **View outstanding issue**. | Charles; Opinion/Decision Done; Notices Blocked; later steps Not started; isolated branch 19 Jun 2027, 10:00 EAT |
| V25 Revised notices ready | **Authorise the revised notices.** **Decision cycle 2**, **Corrected award decision 2**, Afya, **KES 46,400,000**. **Revised notice 2**; **Reply by 26 Jun 2027, 17:00 EAT**; **The waiting period will be calculated after notices are given.** **Authorise revised notices**, **View notice preview**, **View corrected decision**. | Amina; Opinion/Decision Done; Notices Current; later steps Not started; isolated branch 19 Jun 2027, 10:00 EAT |


V23 positive alternative is a separate synthetic branch: keep cycle/report/opinion 2 and the same instants; conclusion **Recommend award to Afya Digital Supplies Limited**, amount **KES 46,400,000**, reason **The corrected report confirms the recommendation.** Use V25’s exact revised notice preview, reply deadline and waiting-period message. Do not show an earliest permitted date before the required giving evidence exists. Actions **Record corrected award and notify bidders**, **Return for correction**, **Record no award**. Opinion Done, Decision Current; later steps Not started.

On Charles’s internal record, the **Outstanding issues** disclosure includes **Record restriction**. Its dialog contains **Basis for hold**, choices **Authoritative order**, **Reported challenge**, then **Source**, **Received at**, **Effective from**, **Scope**, **Evidence**, and **Reason**; buttons **Save restriction**, **Back**.

**Record outcome** on V08 uses a dialog with **Outcome** choices **Restriction ended**, **Further action required**. **Review correction** on V09 and V21 uses choices **No material effect**, **Request corrected evaluation**, **Request decision review**, **Further action required**. Both dialogs also show **Reason**, **Evidence** and **Next action**, buttons **Save outcome**, **Back**. The reported-challenge variant shows **Basis for hold: Reported challenge**, **Outcome** choices **Reported challenge not substantiated**, **Further action required**, and the same fields/buttons. V08 shows **Basis for hold: Authoritative order**. No outcome is preselected. **Correct contact** uses the existing supplier-contact form; no new Award contact editor is shown.

Other required dialog text: **Return report** — field **Reason**, buttons **Return report**, **Back**; **Return for correction** — field **Reason**, buttons **Return for correction**, **Back**; **Record no award** — fields **Reason**, **Next action**, buttons **Record no award**, **Back**; **Record next action** — fields **Reason**, **Next action**, buttons **Save**, **Back**; **Request explanation** — field **Your request**, buttons **Send request**, **Back**. No invented confirmation checkbox, separate notice approval, progress percentage, compliance score or celebratory contract-success message.

## 11. Functional interaction requirements — excluded from design prompts

**Save restriction** invokes `RecordExternalAwardRestriction`. **Save outcome**, or **Save** in the next-action dialog, invokes `RecordAwardIssueDisposition`. The V17 action **Request corrected evaluation** invokes `RecordAwardCorrectionDecision` through the AO and records the correction instruction. It does not create a replacement award or require approval to keep the existing hold. Workspace links and **Open award** use authorised projections. Document/view/history actions open retained versions read-only. Supplier **View notice** never exposes another recipient’s letter.

**Save draft** invokes `SaveProfessionalOpinion`; **Sign opinion** invokes `SignProfessionalOpinion`; **Return report** invokes `ReturnEvaluationReport`. D03’s three decisions invoke `RecordAwardDecision` with the corresponding outcome. In V23, Record no award and Return for correction invoke `RecordAwardCorrectionDecision` for the successor cycle. V25’s Authorise revised notices invokes that same correction command against the exact verified notice batch and the existing corrected decision; it does not create another decision. V24 has no issue action while treatment remains unverified. The positive V23 alternative uses Record corrected award and notify bidders, invoking RecordAwardCorrectionDecision with the exact verified batch in one action. Signing/decision previews retain the exact target until commitment; a changed target requires a fresh review and, where needed, fresh proof.

**Accept award** and **Decline award** invoke `RespondToAward`. **Request explanation** opens the request dialog and **Send request** invokes `RequestAwardExplanation`; **Save reply** invokes `SaveAwardExplanation`; **Send and close** invokes `SendAwardExplanation`. Closing waits for the defined dispatch result. Duplicate clicks return the same receipt. Late supplier responses are stored with the late warning; stale notice versions require review of the new notice first.

**Record next action** on V06/V07 opens the Reason/Next action dialog. On **Save**, `RecordAwardIssueDisposition` receives the fixed outcome **Request decision review**, selected issue identity, retained decline response or missed-deadline evidence, and the entered reason and next action. The server verifies that evidence against the current notice and response record. **Record outcome** and **Review correction** open their specified outcome/evidence/reason/next-action form for the same command. This form cannot lift another owner’s restriction or change a decision. A proposal to change a decision or authorise corrected evaluation creates AO’s **Decide correction** task and invokes `RecordAwardCorrectionDecision` only through that actor. **Correct contact** uses the authoritative contact-owner service. **Retry operation** invokes the assigned technical recovery, never a business decision. **Open Contracting** is shown only after a durable authorised destination exists.

The server updates next-step guidance after every accepted command/event. A returning browser cannot approve an old record. Preserve typed reasons after safe validation failures, announce changes accessibly and retain keyboard focus. Follow KT-STD-001’s desktop, 200% zoom and 390 px verification requirements; no extra confirmation for a read or routine auto-check.

## 12. Audit and historical integrity

Record actor/service, authority evidence, command/event identity, trusted time, prior and resulting revision, exact source versions, reason, signature target/proof where applicable, and outcome. Retain original and corrected values rather than editing history.

Preserve report/opinion/decision/notice bytes, every giving attempt and proof, supplier responses, correspondence, clock calculations, source corrections, orders and package receipts. Record effective and received times separately for late external events. Access and exports follow the owning record’s rules. The proceedings index references these immutable records and their versions; it does not disclose them publicly.

A retry cannot create a second decision, second acceptance, second task or duplicate Contracting case. Recovery records its own technical outcome without replacing business evidence. Human-readable exports identify exact versions and distinguish test proof from real signatures.

## 13. Seed contract

Use KT-STD-001 §8’s existing internal actors and BDS v0.8’s Mary Wanjiku and David Ouma. No new user is introduced. HOP is Charles Mutiso, AO Amina Hassan, and technical operator Daniel Otieno. Contracting’s illustrative recipient is Charles in a separately authorised Contracting capacity; the Award role alone does not grant that future capability.

The ordinary source is EVL v0.4’s TND-MOH-2027-033 report 1, delivered 16 June 2027 at **14:07:01 EAT** with the exact three-member proof set. This specification does not alter that upstream fixture. Opinion signed 17 June at **09:10**; AO decision and coordinated test notices at **10:00**; Mary accepts 18 June at **09:00**. Reply deadline **24 June, 17:00** is an explicit issued-notice test term. The test profile permits Contracting delivery **2 July, 09:00**; this is deliberately later than fourteen days after the fixture’s giving time and is not a claim about statutory day-counting. Production clocks require §15’s verified profile.

Use synthetic Trust, delivery and Contracting adapters only, visibly labelled as in §10. The fixture must not email real bidders, prove production legal service, or imply a deployed Contracting module. Use the same commands as production; no direct lifecycle writes. A second run returns the same identities without new audit transitions.

Isolate each negative branch in a fresh scenario: incomplete source; AO return; source successor during opinion drafting/signing; expired validity; no responsive bid; unresolved tie; funding restriction; authority expiry; unsuccessful bidder; email failure; partial giving across two recipients; late acceptance that cannot qualify; correction after a closed No award cycle; authorised successor-cycle report/opinion and blocked revised notice authorisation; decline; silence; debrief closure and later correspondence; Board suspension; precautionary hold; post-decision correction; cancellation/issue race; unknown authority status; unavailable Contracting; and late restriction after package receipt. Do not mutate the ordinary timeline to manufacture them.

For V14, tender 037 is a separate two-bid fixture with both bids responsive, Afya at KES 46,400,000 and Jirani at KES 45,900,000. These figures are illustrative and must not overwrite EVL’s tender 036 tie fixture. Jirani’s notice is a synthetic recipient record with seeded contact evidence, not a new named human actor. The partial-giving branch uses this two-recipient fixture. V19–V23 form the isolated correction branch with a fresh signed report 2 and opinion 2. V24/V25 are separate synthetic branches: a complete corrected report/opinion supports unchanged Afya pricing, AO records decision 2, and the revised-notice treatment is respectively unverified or verified. V25’s reply deadline is an explicit issued-notice test term. Neither V25 nor the positive V23 branch has a pre-authorisation earliest permitted date: the wait is calculated only after actual giving evidence is retained. Its verified synthetic profile and complete proposed recipient set are fixture inputs, not evidence that notices have already been given. No live revised notice is authorised by this example.

## 14. Acceptance contract

These are required future tests, not claims of software verification.

| ID | Required result |
|---|---|
| AWD-AC-001 | EVL delivery produces one case and HOP task without acknowledgement; retry cannot duplicate them. Empty opening produces neither. |
| AWD-AC-002 | Missing annex/signature or unknown source verification automatically creates the exact issue and named owner; no positive advancement. |
| AWD-AC-003 | HOP signs only the exact opinion/report version; success and AO task are durable together. Failed/uncertain proof remains visibly unresolved. |
| AWD-AC-004 | AO sees dissent and distinct submitted/evaluated amounts; cannot edit findings, prices, supplier ranking or choose a different supplier. |
| AWD-AC-005 | An expired/qualified report supports a signed factual opinion and no-award decision while a positive decision/issue remains blocked. |
| AWD-AC-006 | A reasoned pre-decision return needs no signed return-opinion, preserves prior versions, closes superseded tasks, routes one correction task, and requires a fresh opinion after a changed report. |
| AWD-AC-007 | One AO action authorises the exact notice batch; no separate routine notice approval appears. Required form proof binds that same action. |
| AWD-AC-008 | Recipient reconciliation includes every required submitted tenderer, uses the verified withdrawal/replacement treatment, and excludes draft-only candidates. Each letter uses its recipient’s recorded result. |
| AWD-AC-009 | Coordinated issue, partial delivery, corrected contact and repeated retries preserve notice identity/content and all giving evidence; failures do not show all bidders notified. |
| AWD-AC-010 | Cancel-before-issue and issue-before-cancel interleavings cannot both succeed; in-progress/unknown status never supplies a false no-notification answer. |
| AWD-AC-011 | Mary can accept/decline her current notice; David cannot. Cross-supplier access, expired authority and stale notice attempts fail without a response side effect. |
| AWD-AC-012 | Timely acceptance, late acceptance, decline and no response have distinct outcomes; V06/V07 Save supplies Request decision review and the retained response/deadline evidence without an Outcome selector; no automatic runner-up or security forfeiture occurs. |
| AWD-AC-013 | Clock tests cover exact before/at/after boundaries, calendar/timezone rules, delayed giving to a second bidder and a lawful clock revision; no browser clock authorises contracting. |
| AWD-AC-014 | Validity is checked at decision, actual issue and delivery; a delayed worker cannot send a positive notice after expiry merely because its decision predates expiry. |
| AWD-AC-015 | Debrief closure retains exact correspondence; a later reply is linked separately. A request is never represented as a Review Board filing. Applicable waiting effects are preserved. Failed final-response dispatch leaves the request open and retries the same reply without another approval. |
| AWD-AC-016 | Authoritative suspension and precautionary hold remain distinguishable; neither clears by a timer. Evidence-backed resolution clears only its own issue. |
| AWD-AC-017 | A post-decision correction holds progress without another approval, preserves prior decision/notices, and requires a supported linked outcome. A corrected report requires a fresh signed opinion and Decide correction task; ordinary EVL return or Decide award cannot bypass the decision boundary. |
| AWD-AC-018 | No award and statutory cancellation are distinct. Valid cancellation closes tasks and retains history; unavailable status never closes the record. |
| AWD-AC-019 | Eligible package delivery requires all §5.8 conditions and durable consumer receipt/task; consumer failure preserves the package and named recovery, with no repeated approval. A newly arisen restriction blocks a retry even after service returns. |
| AWD-AC-020 | A later restriction reaches the existing Contracting case and stops affected positive actions; the original package remains unchanged. |
| AWD-AC-021 | Contract mappings, security terms and reservation lineage pass without re-keying; eligibility-only evidence does not become a new contract obligation. |
| AWD-AC-022 | Every §5.9 condition yields a current owner, permitted next action or scheduled outcome and an explanation. Stage transitions and task closure follow §5.9; displayed labels and markers match §10; a hold does not hide unrelated permitted work, and resolving one issue leaves others visible. |
| AWD-AC-023 | Every action in §10 maps to §7/§11; the complete artboards can be produced from §10 plus KT §2 without inventing facts, actions or roles. |
| AWD-AC-024 | Internal, supplier, auditor, public and technical access are tested across list/detail/document/export/API and writes; no access follows merely from knowing an ID. |
| AWD-AC-025 | Repeated commands, out-of-order events, stale revisions and uncertain signing results cannot create duplicate decisions, notices, responses, work items or consumer cases. |
| AWD-AC-026 | Production is unavailable without the verified legal/channel/signing profile; test proof cannot be relabelled as production evidence. |
| AWD-AC-027 | Registers, traceability and owner contracts agree on Proposed status and module boundaries; document approval is not implementation or release evidence. |
| AWD-AC-028 | Waiting to proceed maps to Acceptance and wait until conditions 1–6 hold, then Send to Contracting; receiver failure and a new restriction during retry produce the exact defined markers. |
| AWD-AC-029 | A correction to Closed creates review only. An authorised successor stays on the same case with a new cycle number; returned successor opinions route back through Opinion and Decide correction; prior decisions, notices and terminal outcomes remain unchanged and authority status retains their history. |
| AWD-AC-030 | Restriction basis and issue outcomes accept only the defined values and evidence-backed effects; HOP cannot change an award, clear another authority’s order or turn a late acceptance into a timely one. |
| AWD-AC-031 | Corrected decisions send nothing until verified revised-notice authorisation exists; authorising it later creates no duplicate decision. V25 is Notices Current when ready for authorisation; V24 remains Blocked. Neither pre-authorisation branch displays a calculated waiting deadline. Both §7 decision commands atomically retain one AwardDecisionRecorded v1 event and delivery record per new committed Award/No award version. Returns, instructions and notice-only authorisations create no extra decision event; retries reuse the original event; Contracting receives it idempotently, owns the applicable publication obligation and requires publication evidence to discharge it. Failed event delivery cannot shift the legal trigger/deadline; receipt alone cannot mark publication complete. The combined V23 action records one corrected decision and exact-batch authorisation. |

## 15. Implementation and test constraints

Apply KT-STD-001 §§4–6. Use shared authority, signing, task, notification, document and proceedings facilities; do not build parallel versions inside Award. Financial amounts use the exact published monetary precision and source values. Persist timestamps in UTC and display the site timezone. Use deterministic document generation and explicit rule versions.

**Production gates.** Before live use, record the applicable current law and official Goods STD version; settle outstanding LAW-V-001 applicability questions; verify notice forms, audience treatment, lawful channels and giving evidence, date-counting, debrief effects, review/resumption treatment, required signatures and security/publication ownership. Include the selected legal interpretation and reviewer/date in the controlled operating profile. Business users cannot relax it per tender.

The 2022 revised Act was checked for the core allocation of responsibility and boundaries in §17. This is not a certification that all amendments, regulations or court orders effective on 30 September 2026 have been resolved. In particular, this document does not close the existing legal-verification item by restating the 2020 Regulations. No regulation-only deadline is silently hard-coded.

Integration release requires implemented counterpart contracts, licensed/approved signing where required, tested real notice channels, authoritative status/clock sources, the Contracting receiver and recovery tests. A test receiver demonstrates the proposed contract only. Pending counterpart documents and production gaps remain visible release dependencies; no new manual procurement gate is created to compensate for absent software.

## 16. Prohibited shortcuts

Do not repeat Evaluation’s automated checks manually; treat evidence supplied as evidence verified; alter a report under existing signatures; let an officer pick another bidder; change the submitted sum; introduce unpublished criteria; send selected bidders early; treat a queued email as proof of giving; infer no decision from no case; treat acceptance as contract signature; clear an order by elapsed time; forfeit security from silence; or show completion without a durable downstream receipt.

Do not add a second notice approval, a manual send-to-Contracting approval, arbitrary time prescriptions, a task-assignment subworkflow, an AI compliance decision, or unsupported **Override** action. Product-wide prohibitions in KT-STD-001 §2.3 also apply.

## 17. Traceability, precedence and coordinated work

### 17.1 Source and legal basis

| Source | Use and verified boundary |
|---|---|
| EVL-CHG-001 v0.4, approved 30 Sep 2026 | Signed report delivery; qualified reports; pre/post-decision correction distinction; deterministic evaluation; report 1 fixture. |
| STD-TPL-001 v0.10, approved 26 Sep 2026 | Confirmed template key/product profile and one-lot/KES/fixed-price scope; immutable response/evaluation/contract mappings. Its exact installed tender release still governs individual outputs. |
| TPR-CHG-001 v0.13 approved; v0.15 coordinated proposal | Tender authority, validity and proposed cancellation/status interface. The proposed changes remain unapproved. |
| BDS-CHG-001 v0.8 approved; v0.10 coordinated proposal | Submitted bid, contact, supplier authority and proposed post-submission interfaces. Existing proposals remain unapproved. |
| PRC-CHG-001 v0.9 approved; v0.10 coordinated proposal | Proceedings retention and proposed Evaluation records. Award additions require the matching contract below. |
| KT-STD-001 v1.12 approved; v1.13 proposed | Document/design/verification standard; existing actor identities. This document does not approve the pending Evaluation fixture amendment. |
| TRUST-ADR-001 v0.1; AUTH-ADR-001 effective controlled version | Personal proof, test/production separation and active authority. No pending AUTH revision is approved by reference. |
| Public Procurement and Asset Disposal Act, revised 2022, §§84–88 | Signed HOP professional opinion; AO consideration; published award method; notices, written acceptance and no contract on notice; validity extension. Printed pp.48–50. |
| Same Act, §§134–138, 142; §§167–168 | Contract preparation/signature boundary; fourteen-day minimum and validity; refusal-to-contract distinction; contract publication; performance security; review and suspension. Printed pp.66–69, 77–78. |
| Same Act, §63; LAW-REG-001 and existing LAW-V-001 | Pre-notification termination and controlled legal applicability. Current-law and operational-rule verification remains a release dependency. |

Official revised Act: https://pppkenya.go.ke/wp-content/uploads/2020/07/Public-Procurement-and-Asset-Disposal-Act-33-of-2015-Revised-2022.pdf

PPRA revised-edition landing page: https://ppra.go.ke/download/the-public-procurement-and-asset-disposal-act-revised-edition-2022/

Source review date: 30 September 2026. Statutory responsibility is not an assertion that the Act expressly authorises autonomous procurement decisions.

### 17.2 Required counterpart contracts

These are proposed coordinated changes. Listing them does not amend or approve their owners’ documents.

| ID | Owner / required change | Acceptance link |
|---|---|---|
| AWD-IF-01 | EVL + Award: bind exact report delivery to the same HOP work item; distinguish Return from committed Award/No award; implement pre-decision return and post-decision correction/status contracts. | AC-001–006, 017, 025 |
| AWD-IF-02 | Tenders + Award: durable tender-level decision/notification status from before any Award case; serialised issue/cancel transition; timely validity and cancellation events. | AC-010, 014, 018 |
| AWD-IF-03 | BDS + Award: authoritative submitted/withdrawn/replacement audience, mandatory contact correction receipts and current signatory authority for award responses. | AC-008–012, 024 |
| AWD-IF-04 | PRC: index exact opinion, decision, notice/giving proof, response, correspondence, restrictions and consumer receipts with source access rules. | AC-020–025 |
| AWD-IF-05 | Contracting: versioned receive/update acknowledgement, designated recipient task, current-status recheck; performance security, contract signing, section 138 publication/reporting through the §5.8 AwardDecisionRecorded v1 event and Contracting-owned receive/obligation/completion operations, with explicit trigger/deadline independent of package delivery or contract signature, and security disposition ownership. | AC-019–021, 031 |
| AWD-IF-06 | Legal/rules + Trust/notifications: verified live notice/signature/clock profile, effective rules and restrictions; retain LAW-V-001 until independently closed. | AC-009, 013–016, 026 |
| AWD-IF-07 | AUTH + Budget: scoped Award actions and supplier acceptance; read-only current funding response with explicit unknown/failure result. | AC-004, 022, 024 |

The baseline register and control workbook admit AWD v0.4 as **Project Owner review**, not approved. They record the proposed interfaces, delivery item and unresolved release dependencies. They do not change the existing Gate 1 implementation boundary or claim a revised roadmap has already been delivered in software.

### 17.3 Precedence

The issued tender and applicable law control the procurement. Source owners retain authority over their facts. This document owns Award behavior and its proposed interfaces. KT-STD-001 governs shared design and verification. Where an owner contract is not yet reconciled, record the discrepancy and block the affected production integration; do not resolve it through an undocumented UI assumption.

## 18. Approval effect

Approval of this version would establish the MVP 1 Award requirements and authorise controlled design and implementation against them. It would not approve a real procurement, certify the legal operating profile, approve pending counterpart revisions, activate production signing/notices or establish that Contracting is implemented.

The accepted high-level basis is retained. This detailed v0.4 remains **Proposed** until the Project Owner approves it. Implementation, verification and release must be recorded separately.


### 18.1 v0.2 change and preservation record

| Review point | Disposition in v0.2 |
|---|---|
| F1–F3 | Explicit marker mapping and correction-cycle table; Closed remains the prior cycle’s outcome; only an AO-authorised successor changes the current cycle. |
| F4–F6 | Fixed hold-basis/outcome choices, guards and matching dialog content; Rules and notice audience issue type added. |
| F7–F8 | HOP records/proposes, AO decides changed procurement outcomes; D06 labels Charles as Contracting owner. |
| F9–F12 | Common receiver message and technical task names; notification-completion wording tied to evidence; one canonical status vocabulary with explanatory text mapping. |
| F13–F15 | Corrected decision/notice authorisation separated explicitly; late acceptance cannot qualify; AO correction next step stated. |
| F16–F18 | V07’s explicit instant already overrides the unspecified-instant default; alternative tender header and transition/design references clarified. |
| F19 | New proposed v0.2; source v0.1 and its amendment preserved; this record identifies changes without claiming an unverified universal versioning rule. |
| L1–L5 | Tie route remains outside MVP; decline is not automatically refusal-to-contract; publication trigger cannot default to signature; conservative cancellation cut-off named; checked section 88 limits stated with effective-law verification retained. |

Preserved: accepted MVP scope and ordinary workflow; published-rule discipline; personal signed professional opinion; AO responsibility; original bids/amounts; no routine extra approval; supplier privacy; test/production separation; automatic receipt/delivery; legal operating-profile dependencies; pending counterpart approvals. Acceptance cases 001–027 are retained, with 028–031 added. No sibling document approval or production readiness is asserted.

Source preservation: v0.1 including the 30 September workflow amendment, SHA-256 `95149a1ce07eea8b7191515af3c43c12588da62424403fe82c0ba4a8d3886b82`. The earlier source remains retained; v0.2 was the proposed successor at that revision. The attached review remains an independent review record.


### 18.2 v0.3 change and preservation record

| Review point | Disposition in v0.3 |
|---|---|
| N1 | V06/V07 map to Request decision review with retained evidence; no new selector. §§5.10, 11; AC-012. |
| N2 | Notices is Current when the exact revised batch is ready for AO authorisation; dispatch still requires authorisation. §5.9; AC-031. |
| N3 | Removed the unsupported earliest date from V25 and the inherited V23 branch; seed and test wording use actual giving events. §§10, 13; AC-031. |
| N4 | Defined the durable Award decision event and Contracting-owned publication obligation, receive and completion operations. §§4, 5.8, 17.2; AC-031. |
| N5 | Added authoritative next-step mappings for V18, V21, V22, V24 and V25. §5.9; AC-022. |
| N6 | V17 and V19 display the same retained instruction reason. §10.3. |
| N7 | Combined corrected-award/notice label maps to the existing Record corrected award outcome and one command. §§5.10, 11; AC-031. |
| N8 | Tie referral uses the existing signed opinion and AO no-award next action; no new workflow. §§2, 10.3. |

Source preservation: v0.2, SHA-256 `da113f25103ac40fba601460b6b3ab10021ddc07982594bfce9b1b9f7851082a`. Prior versions and independent reviews remain retained. v0.3 was the proposed successor at that revision; approval, implementation and legal/interface verification remain outstanding. The 31 acceptance cases remain required future tests.


### 18.3 v0.4 change and preservation record

| Review point | Disposition in v0.4 |
|---|---|
| P1 | Added the retained decision event/delivery record to §4 and atomic creation to both §7 decision commands. Returns, instructions and notice-only authorisations do not create another decision event. AC-031 covers event creation and retry identity. |
| P2 | Named the HOP task Resolve revised notice treatment in §5.9, with legal-rule owner input. |
| P3 | Removed the duplicate full stop from V25. |

Source preservation: v0.3, SHA-256 `4e64d4e290446ac3a621a32896db7dcd5b93195a06182df59b4992d85c39898e`. Prior versions and independent reviews remain retained. v0.4 is the current proposed successor. Approval and the existing implementation, legal and interface verification requirements remain outstanding.
