**Implement the internal Bid Submissions module**

**1\. Objective**

Replace the current Coming Soon page with a functional submission register that:

- Lists tenders in the submission lifecycle
- Preserves sealed-bid confidentiality before authorised opening
- Shows actual active submissions after opening
- Provides read-only access to the complete submitted electronic bid
- Creates the authoritative input for the future Evaluation module

This module must not evaluate, rank or qualify bids.

**2\. Fixed implementation approach**

Use a dedicated Frappe Page inside the real Procurement Desk shell.

- Port only the approved Stitch central content and page-scoped styles.
- Do not use an iframe.
- Do not reproduce Stitch navigation or toolbars.
- Use API-driven state and section-level rendering.
- Reuse existing Frappe routing, permissions and application components.
- Remove the Planned badge from Bid Submissions only after the complete functional route is available.
- Replace its Coming Soon destination with the implemented page.

Do not ask for a reduced/full implementation choice. Implement the complete scope below.

**3\. Inspect before implementation**

Identify:

- Existing bidder-workspace submission records
- Submission version and resubmission behaviour
- Withdrawal and supersession handling
- Submission receipts
- Sealed submission snapshots
- Published tender section manifest
- Submitted section-response storage
- Evidence and attachment storage
- Tender submission and opening dates
- Current tender permissions and organisational scope
- Existing audit-event service
- Existing bid-opening model or workflow, if any
- Approved Bid Submissions Stitch designs

Produce a short mapping of the actual repository models to these requirements before changing code.

Do not create another copy of submitted bid contents.

**4\. Authoritative data source**

The module must read the immutable submission version created by the Bidder Workspace.

It must never render:

- Bidder drafts
- Current editable bidder responses
- Live bidder-profile values
- Current tender configuration in place of the published version
- Reconstructed submissions assembled from unrelated current records

Use the exact published tender version and submission snapshot bound to the receipt.

Bidder identity must come from the submitted bidder snapshot. Subsequent profile changes must not alter the opened bid.

**5\. Active submission selection**

For each bidder and permitted offer:

- Show the latest valid submission received before the deadline.
- Exclude drafts.
- Exclude withdrawn submissions.
- Exclude versions superseded by a valid resubmission.
- Preserve withdrawn and superseded versions in authorised audit history.
- Keep main and permitted alternative offers distinct.
- Preserve submitted lot selections.

Use explicit version and status relationships already present in the repository. Do not infer versions from timestamps alone when version links exist.

**6\. Submission lifecycle**

Implement or reuse this tender-level state:

Receiving submissions

→ Closed and sealed

→ Opening in progress

→ Opened

→ Released to evaluation

Rules:

- Receiving submissions: tender is published and the submission deadline has not passed.
- Closed and sealed: the deadline has passed and no authorised opening has completed.
- Opening in progress: an existing governed opening workflow has started but not completed.
- Opened: the authorised opening event has completed.
- Released to evaluation: the opened register has been formally released to the evaluation workflow.

Do not use the current time alone to expose submissions. Passing the deadline changes the tender to closed and sealed; it does not open bids.

Do not implement evaluation in this task.

**7\. Minimum bid-opening record**

Reuse the existing opening workflow if one exists.

If no opening model exists, add only the minimum governed record required:

- Tender
- Scheduled opening date and time
- Opening status
- Opened date and time
- Authorised opening user
- Active submission version identifiers included in the opening register
- Register completion timestamp
- Audit reference

The opening record must reference the immutable submitted versions. It must not duplicate their contents.

The opening action must:

1. Run server-side.
2. Verify the user has bid-opening authority.
3. Verify the tender deadline has passed.
4. Verify the scheduled opening time has arrived.
5. Verify the tender has not already been opened.
6. Resolve the active submissions transactionally.
7. Create or complete the immutable opening register.
8. Record the opening audit event.
9. Return only the completed register result.

Prevent duplicate opening through server-side locking or the repository's existing transactional pattern.

Do not build a committee-management subsystem in this task. If an existing approval or committee workflow exists, respect it rather than bypassing it.

**8\. Confidentiality rules**

Before completed authorised opening, no internal API or page may return:

- Bidder names
- Bidder identifiers
- Number of submissions
- Submission timestamps
- Selected lots
- Alternative-offer information
- Prices
- Documents
- Evidence
- Response data
- Submission activity patterns

This prohibition applies to:

- Landing-page APIs
- Sealed-status APIs
- Search results
- Error messages
- Administrator users
- Direct URLs
- Frontend page source
- Client-side state

System Administrator status must not bypass the sealed state.

**9\. Screen 1 - Bid Submissions landing page**

Replace the Coming Soon page.

Header:

- Title: Bid Submissions
- Description: View tenders receiving submissions and access bids after authorised opening.

Controls:

- Search by tender reference or title
- Submission-stage filter

Table columns:

- Tender
- Procuring Entity
- Submission Deadline
- Opening Date
- Submission Stage
- Action

Allowed stages:

- Receiving submissions
- Closed and sealed
- Opening in progress
- Opened
- Released to evaluation

Actions:

- View tender for receiving submissions
- View sealed status for closed and sealed tenders
- View opening status during opening
- Open register after opening

Do not show submission or bidder counts before opening.

After opening, the landing page may show the number of active bids opened if included by the approved design. It must come from the immutable opening register.

Scope all tenders by the user's Procuring Entity and tender permissions.

**10\. Screen 2 - Closed and sealed**

Show:

- Tender reference and title
- Procuring Entity
- Submission deadline
- Scheduled opening date and time
- Status: Closed and sealed

Main state:

- Title: Bids remain sealed
- Text: Submitted bids cannot be viewed until the authorised bid-opening process is completed.

For an authorised opening user, show Open submitted bids only when:

- The submission deadline has passed
- The scheduled opening time has arrived
- Required existing opening authorization is complete
- Opening has not already completed

For other users, show:

Waiting for authorised bid opening.

Do not reveal whether any submissions exist.

**11\. Opening confirmation dialog**

When the authorised user selects Open submitted bids, show the approved confirmation dialog.

Display:

- Tender reference
- Tender title
- Submission deadline
- Scheduled opening time

Message:

Opening will make the submitted bids visible to authorised users and create the official submission register. This action will be recorded.

Actions:

- Cancel
- Open bids

Do not add:

- A checkbox
- Signature fields
- Technical confirmation codes
- Bidder names
- Submission counts

The dialog is not the security control. Server-side authorization and lifecycle validation remain authoritative.

**12\. Screen 3 - Opened Submission Register**

Render only from a completed opening record.

Header:

- Tender reference and title
- Procuring Entity
- Status: Opened
- Opened date and time
- Active bids opened count

Table columns:

- Tenderer
- Submission Receipt
- Submitted At
- Lots
- Offer Type
- Status
- Action

Offer types:

- Main offer
- Alternative offer, only where permitted

Status:

- Opened

Actions:

- View bid
- View receipt

Additional links:

- View opening record
- View submission audit history
- Back to Bid Submissions

Do not show:

- Evaluation scores
- Rankings
- Responsive or non-responsive outcomes
- Qualified or disqualified status
- Corrected prices
- Award status

The active register excludes withdrawn and superseded submissions.

**13\. No-bid state**

Only after completed authorised opening, if the opening register contains no active submissions, show:

- Title: No bids were received
- Text: No active bid submissions were recorded for this tender.

Never return or display this state before opening.

**14\. Screen 4 - Submitted Bid overview**

Header:

- Tenderer legal name at submission
- Tender reference and title
- Submission receipt reference
- Submitted date and time
- Applicable lots
- Offer type
- Status: Opened
- Label: Read-only submitted bid

Generate the section list from the published tender's submission manifest.

Table columns:

- Bid Section
- Submission Status
- Action

Status:

- Submitted

Action:

- Review

Possible IT STD sections may include:

- Tender Documents and Addenda
- Form of Tender
- Confidential Business Questionnaire
- Statutory Declarations
- Tender Security
- Preliminary Requirements and Evidence
- Qualification and Capability
- Technical Proposal and Implementation Plan
- Requirements Compliance
- Price Schedule

These are examples only. Do not hard-code them as the universal section list.

Actions:

- View submission receipt
- Back to Submission Register

**15\. Screen 5 - Read-only section review**

Implement a reusable read-only mode for submitted sections.

Prefer reusing the existing Bidder Workspace section renderers where practical, with:

- Submission snapshot as the data source
- All editing disabled
- No save or completion actions
- No bidder-workspace navigation
- Internal procurement submission context retained

Display:

- Section name
- Tenderer
- Tender reference
- Submission receipt
- Submitted response - read only

Render submitted:

- Structured field values
- Declarations
- Tables
- Repeating records
- Lots
- Price schedules
- Requirements responses
- Evidence references
- Certification details

Evidence actions:

- View
- Download

Navigation:

- Previous section
- Back to Submitted Bid
- Next section

For Price Schedule:

- Preserve submitted currencies
- Show submitted line items and totals
- Do not convert currencies
- Do not recalculate or correct prices

For evidence:

- Retrieve the attachment version bound to the submitted snapshot
- Do not resolve to a newer bidder-profile document

Do not show:

- Edit controls
- Save buttons
- Evaluation fields
- Comments
- Scores
- Pass or Fail
- Qualified or Compliant
- Internal IDs, hashes, manifests or storage paths

**16\. Submission receipt**

Provide a read-only receipt view containing:

- Tender reference
- Tender title
- Tenderer legal name at submission
- Receipt reference
- Submission version
- Submitted date and time
- Applicable lots
- Offer type
- Submission status

Do not expose technical digests or internal identifiers.

**17\. Opening record**

Provide a read-only opening record containing:

- Tender reference and title
- Scheduled opening time
- Actual opening time
- Authorised opening user or existing opening body
- Number of active bids opened
- Active submission receipt references
- Opening status

Only show bidder names and receipt references after opening.

The opening record is not an evaluation report.

**18\. Audit history**

Use the existing audit service.

Audit at least:

- Bid-opening attempt
- Successful opening
- Failed or rejected opening attempt
- Opened register viewed
- Submitted bid viewed
- Submitted evidence downloaded
- Withdrawn or superseded history accessed
- Release to evaluation when implemented

Audit records must reference the tender, user, action and timestamp without copying bid contents into logs.

**19\. Permissions**

Use separate server-side capabilities for:

- View submission-stage tender metadata
- Conduct bid opening
- View opened register
- View opened bid
- Download submitted evidence
- View withdrawn and superseded versions
- Release opened register to evaluation

Apply:

- Procuring Entity scope
- Tender assignment or access
- Lifecycle state
- Specific action permission
- Sealed-bid restrictions

Frontend visibility is not authorization.

Direct URLs and download endpoints must enforce the same rules.

**20\. Lots and alternatives**

- Show only lots included in the submitted snapshot.
- Do not split one bidder into separate bidder rows merely because it submitted multiple lots.
- Keep main and alternative offers distinct.
- Do not show an alternative offer when the tender did not permit it.
- Preserve the submitted offer-to-lot relationship.

**21\. Relationship to Evaluation**

Bid Submissions owns:

- Receipt
- Sealed submission version
- Resubmission and supersession
- Withdrawal
- Bid opening
- Opening register
- Read-only submitted bid

Evaluation will own:

- Preliminary examination
- Responsiveness
- Qualification
- Technical evaluation
- Financial evaluation
- Clarifications during evaluation
- Scoring and recommendation

Do not add evaluation buttons or statuses to this module.

If Released to evaluation is not yet implemented, preserve it as a supported future lifecycle state without fabricating a release action.

**22\. APIs or server methods**

Follow repository conventions, but provide equivalent server-side operations for:

- List permitted tenders and derived submission stage
- Get sealed tender status without submission metadata
- Open submitted bids
- Get completed opening register
- Get submitted bid overview
- Get immutable submitted section response
- View submission receipt
- View opening record
- Download submitted evidence
- View authorised submission-version history

Do not use one broad endpoint that returns bid contents before verifying lifecycle and permission.

**23\. Fixtures**

Create coherent development fixtures using actual bidder-workspace submission flows:

1. Published tender still receiving submissions
2. Closed tender with sealed submissions
3. Opened tender with at least three active bidders
4. Valid bidder resubmission that supersedes an earlier version
5. Withdrawn submission excluded from the active register
6. Multi-lot submission
7. Permitted alternative offer
8. Opened tender with no active bids
9. User who can view tender metadata but cannot open bids
10. Authorised opening user

Do not create internal submission records directly if the existing bidder submission service can create them correctly.

Development data may be torn down and reseeded.

**24\. Tests**

Add tests for:

**Landing page**

- Tender scope and permission filtering
- Correct derived submission stages
- Search and stage filters
- Correct actions by stage
- No pre-opening submission counts

**Sealed confidentiality**

- No bidder metadata returned before opening
- No direct bid-detail access before opening
- No evidence download before opening
- Administrator cannot bypass sealing
- No-bid state unavailable before opening

**Opening**

- Deadline and scheduled time enforced
- Opening permission enforced
- Existing authorization respected
- Duplicate opening prevented
- Active versions resolved correctly
- Opening record created atomically
- Audit event recorded

**Register**

- Only active opened submissions shown
- Withdrawn and superseded versions excluded
- Correct bidder snapshot
- Correct receipt, lot and offer information
- No evaluation data shown

**Submitted bid**

- Sections generated from the published manifest
- Responses come from the immutable submission snapshot
- Evidence uses the submitted attachment version
- All content is read-only
- Multiple currencies remain separate
- No technical identifiers displayed

**Permissions and audit**

- Entity and tender scope enforced
- Opened-bid view permission enforced
- Evidence-download permission enforced
- Audit-history permission enforced
- Bid view and evidence download audited

**Empty states**

- Sealed state does not reveal zero submissions
- No-bid state appears only after opening
- Appropriate state when no permitted tenders exist

Run the relevant Bidder Workspace regression tests to ensure internal viewing does not change bidder submission, withdrawal or resubmission behaviour.

**25\. Delivery report**

Provide a concise report containing:

- Files changed
- Existing submission models reused
- Any minimum opening model added
- Submission-version selection rule
- Sealed-data protections
- Permissions applied
- Routes and server methods
- Read-only renderer approach
- Fixtures created
- Tests executed and results
- Genuine remaining gaps

Do not expand the task into Evaluation, Awards, contract formation, document-generation architecture or a generic reporting framework.