**KenTender**

**Workflow Guidance Standard**

Next steps, dead ends and hand-offs on every record screen

| **Field**                      | **Value**                                                                                                                    |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| Status                         | Approved (25 September 2026), with the restraint note in Section 5.4 added at approval                                       |
| Intended home                  | KT-STD-001 version 1.8 (Proposed), §2.9 and §3B; this document was written when KT-STD-001 was believed to be at version 1.4 |
| Date                           | 25 September 2026                                                                                                            |
| Worked example                 | Plan update PLN-MOH-2027-001, version 2 (Ministry of Health Annual Procurement Plan 2027/28)                                 |
| Viewing persona in the example | Mercy Kilonzo, Procurement Planner                                                                                           |
| Source inputs                  | Screen capture of the Prepare plan update page; Claude Code session findings on the plan update and on workflow guidance     |
| Reconciliation status          | Reconciled against KT-STD-001 v1.7 in preparing KT-STD-001 v1.8; not yet reconciled against PLN-CHG-001                      |

# 1\. Purpose

A user looking at any record in KenTender asks four questions: what stage is this at, is it my turn, if not whose turn is it, and if nothing can move, why not. Today each screen answers these in its own way, and some screens do not answer them at all. This standard defines one way for every module to answer them, so that no record screen leaves a user with disabled buttons and no explanation.

The problem was stated from the Procurement Planner's seat: "I do not know where the plan I'm working on stands." The worked example throughout this document is that plan.

## 1.1 The pattern observed

Every snag found in the session that produced this standard was the same failure: the system knew the next step, or knew why there was not one, but did not tell the person looking at the screen.

| **Observed failure**                      | **What the system knew**                                                 | **What the screen showed**                                                     |
| ----------------------------------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------ |
| The need looked stranded after acceptance | The next step existed                                                    | Nothing; the next step was only available on a page the user was never sent to |
| "Awaiting validation" status              | Which role and person must validate                                      | A status with no actor named                                                   |
| Finished review                           | The review was complete                                                  | "Decision required", which was no longer true                                  |
| Plan update blocked by budget             | The plan exceeds an approved budget line, by how much, and on which line | "Funding: Not yet checked", and only Cancel plan update and Save draft buttons |

In each case the server usually had the answer. There is simply no rule that the answer must reach the screen. This standard is that rule.

# 2\. Worked example: plan update PLN-MOH-2027-001 version 2

## 2.1 What is happening

Nothing can happen next on this plan update until the plan fits its budget. The update is over budget, but the screen does not say so.

| **Fact**                                           | **Value**                                                                     |
| -------------------------------------------------- | ----------------------------------------------------------------------------- |
| Budget line                                        | Digital health workforce development (MOH-BL-HWD-2027)                        |
| Approved amount on the line                        | KES 60,000,000                                                                |
| Amount the update's purchases put against the line | KES 62,000,000                                                                |
| Overrun                                            | KES 2,000,000                                                                 |
| Purchase whose cost equals the overrun             | testing requisitions (PPI-MOH-2027-003), KES 2,000,000                        |
| Consequence                                        | The site will not allow the next step, "request a funding check from Finance" |
| Buttons shown                                      | Cancel plan update; Save draft                                                |
| Reason the server already sends                    | "The planned amount exceeds the approved budget on the lines shown"           |
| What the screen shows instead                      | "Funding: Not yet checked"                                                    |

The server already produces the reason; the screen does not display it. That is a real defect, and it is the defect this standard is designed to make impossible.

## 2.2 How to move it forward

The planner must pick one of two routes.

| **Route**           | **What it involves**                                                                        | **Who acts**                                                                                  |
| ------------------- | ------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Increase the budget | Revise the budget in Budget & Funding so the line holds at least KES 62,000,000             | Budget Officer (Josphat Mwangi) prepares the revision; Budget Approver (Beatrice) approves it |
| Shrink the plan     | Lower an estimated cost with Edit purchase, or leave the new requirement out of this update | Procurement Planner (Mercy Kilonzo)                                                           |

## 2.3 The rest of the path after the budget fits

1. Mercy Kilonzo requests the funding check.
2. Finance confirms it (Josphat Mwangi, as Finance Confirmation Officer).
3. The Head of the Procurement Function signs and submits (Charles Mutiso).
4. The Accounting Officer approves (Amina Hassan), and the statutory approver too if the route requires it (Daniel).
5. The update becomes the plan in force.
6. Only then can a requisition be raised for "testing requisitions".

The route rules that decide whether statutory approval applies must be taken from PLN-CHG-001 itself; this document does not restate them.

# 3\. Core principle: guards return reasons, not booleans

The architectural change underneath every layer of this standard is this: the same server-side evaluation that decides whether an action is available must also produce the explanation.

Every guard, for example "a funding check needs the plan to fit its budget lines", returns a result made of: whether the action is allowed; a stable reason code; the figures behind the reason; and the fix options, each naming the role that can perform it. A disabled or hidden action with no reason then cannot be built, because the reason is what the guard returns.

In the worked example, the "Request funding check" action disappeared silently because its guard returned only true or false, and the reason text went only into an error message that nobody triggers.

| **Guard result field** | **Meaning**                                                         | **Example from the worked example**                                                       |
| ---------------------- | ------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| allowed                | Whether the viewer may perform the action now                       | false                                                                                     |
| reason_code            | Stable machine code for the blocking condition                      | BUDGET_LINE_EXCEEDED                                                                      |
| figures                | The values that make the reason concrete                            | Line MOH-BL-HWD-2027; approved KES 60,000,000; planned KES 62,000,000; over KES 2,000,000 |
| fixes                  | Each way the condition can be cleared, with the role that can do it | Revise budget (Budget Officer); reduce a purchase (Procurement Planner)                   |

The reason code names in this document are illustrative. The actual codes belong to each module's specification.

# 4\. Layer 1: the next-step contract

Every record endpoint returns one next_step object for the viewing user, always in the same shape. Each module already works out most of this information; the change is that the server hands every screen one next-step answer in a common shape, and a shared component draws it.

## 4.1 Fields

| **Field**      | **Meaning**                                                                             |
| -------------- | --------------------------------------------------------------------------------------- |
| kind           | One of: your turn; your turn but blocked; waiting on someone; done; not involved        |
| headline       | One plain sentence, for example "Over budget by KES 2,000,000 on one budget line"       |
| stage          | The current journey stage code, so the tracker and the next-step block always agree     |
| holder         | The role and named person who must act next, for example Budget Officer, Josphat Mwangi |
| since          | When the record entered this state, so the viewer can see how long it has waited        |
| blockers       | Every blocker at once, each with a reason code, the figures and the fix options         |
| fixes          | For each option: a label, the role who can do it, and a link or an action               |
| primary_action | The one action to show as the main button, if the viewer has one                        |

## 4.2 Rules

- **All blockers together.** Every blocker is returned at once, never one at a time, so a user does not fix one and then discover the next.
- **Fixed precedence.** When more than one kind could apply to a viewer, the order is: an available action, then a blocked action, then waiting, then done, then not involved.
- **Actionable links only.** A fix link is offered only if the named holder can actually open and act on the target page. The dead-end test (Section 6) verifies this.
- **Single source.** The next-step answer is produced by the same guards that enable or disable actions (Section 3). It is never computed separately for display.

## 4.3 The four cases, with example wording

| **Case**           | **Example wording**                                                                                                                      | **Shown with**                           |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| Your turn          | "Request the funding check"                                                                                                              | The action button                        |
| Blocked            | "Over budget by KES 2,000,000 on Digital health workforce development. The Budget Officer must revise the budget, or reduce a purchase." | Links or actions for each fix            |
| Waiting on someone | "Waiting for Procurement (Mercy Kilonzo) to validate"                                                                                    | Holder's name and how long it has waited |
| Done               | "Accepted by Mercy Kilonzo on 25 Sep"                                                                                                    | Who completed it and when                |

## 4.4 One record, different answers per viewer

The same plan update answers differently depending on who is looking at it.

| **Viewer**                                        | **Kind**           | **What they see**                                                            |
| ------------------------------------------------- | ------------------ | ---------------------------------------------------------------------------- |
| Mercy Kilonzo (Procurement Planner)               | Your turn, blocked | Over budget by KES 2,000,000; request a budget revision or reduce a purchase |
| Josphat Mwangi (Budget Officer)                   | Not involved yet   | Nothing, until Mercy requests a revision; then it is his turn                |
| Charles Mutiso (Head of the Procurement Function) | Waiting            | Plan update being drafted by Mercy Kilonzo; blocked on budget                |
| Amina Hassan (Accounting Officer)                 | Not involved yet   | Plan in force is version 1; version 2 is in preparation                      |

# 5\. Screen pattern

Every record page carries a standard next-step block in one place, in the same position, with the same look. Above it sits a journey tracker. The layout below shows the Prepare plan update page for Mercy Kilonzo under this standard.

## 5.1 Layout of the Prepare plan update page

**Prepare plan update**

Ministry of Health Annual Procurement Plan 2027/28, version 2

**Journey tracker**

| **Drafted**       | **Budget fit** | **Funding check** | **Submitted** | **AO approval** | **Statutory**  | **In force** |
| ----------------- | -------------- | ----------------- | ------------- | --------------- | -------------- | ------------ |
| Done<br><br>Mercy | Blocked        | Josphat           | Charles       | Amina           | If route needs | —            |

**Next-step block**

Next step: your turn, blocked

**Over budget by KES 2,000,000 on one budget line**

You can request the funding check once every budget line fits. Choose one way to fix it.

**\[ Request budget revision from Josphat Mwangi \] \[ Reduce a purchase \]**

**Budget fit, checked now**

| **Budget line**                      | **Approved**   | **This plan**  | **Difference**     |
| ------------------------------------ | -------------- | -------------- | ------------------ |
| Digital health workforce development | KES 60,000,000 | KES 62,000,000 | Over KES 2,000,000 |

**Finance confirmation:** not requested yet.

## 5.2 Budget fit and Finance confirmation are two separate facts

"Funding: Not yet checked" merges two different things. One is budget fit, which the system can compute at any moment from the draft, so it should show live, per budget line, while the planner edits. The other is Finance confirmation, a formal step a person performs. Showing the first as "not yet checked" when the server already knows the answer is what hid the problem in the worked example.

| **Fact**             | **Nature**                                                  | **When it is known**                     | **How it is shown**                                          |
| -------------------- | ----------------------------------------------------------- | ---------------------------------------- | ------------------------------------------------------------ |
| Budget fit           | Computed by the system                                      | At all times, from the current draft     | Live, per budget line, with approved, planned and difference |
| Finance confirmation | A formal step performed by the Finance Confirmation Officer | Only after it is requested and performed | As a stage in the journey tracker and a status line          |

## 5.3 Blocked states owned by someone else need a hand-off action

When the fix for a blocker belongs to another person, the blocked user needs a way to hand it to them inside the system. Without a "Request budget revision" action, the planner would have to phone the Budget Officer, and nothing in the system would record that the plan is waiting on him.

The action creates the hand-off, places an item in the Budget Officer's My Work, and changes the planner's view to "Waiting on Josphat Mwangi: budget revision". Every blocker whose fix belongs to another role must offer such an action, not only a link.

## 5.4 Restraint: these components must not overwhelm existing screens

Added at approval. The journey tracker and the next-step block exist to make existing screens easier to understand; they fail if they make those screens heavier. Claude Design must take every rule below into account, and KT-STD-001 v1.8 §2.9.3 carries the binding version of these rules.

| **Rule**                     | **What it means for a design**                                                                                                                                                                                                                                                                                  |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Replace, never add           | The next-step block is the screen's status narrative and joins its action area. It replaces any existing status line, badge, process-position sentence or check summary that says the same thing, such as "Where this requirement stands" or "Funding: Not yet checked". The next step is stated once per page. |
| Size to the state            | Only the blocked state gets a container. Your turn, waiting and done are text within existing regions. The figures behind a blocker appear once, where the actor fixes them; the block states only the headline figure.                                                                                         |
| The tracker is one row       | Stage labels and markers only. No card per stage, dates, past actors, descriptions or heavy connectors. Who acted and when stays in the existing history disclosure.                                                                                                                                            |
| Only where it has a job      | The tracker appears only on record detail, review or decision, and form or editor pages of records on the process spine. Never on registers, workspaces, setup pages, dialogs or table rows.                                                                                                                    |
| First-view budget            | Together, the two components must not push the page's first working region out of the first 1440 × 1024 view. If they would, the tracker reduces to a single line naming the current stage.                                                                                                                     |
| Quiet by default             | Neutral text and markers. Accent only on the current stage; status colour only on blocked and done markers, always with text. No added borders, bands or accent rules outside the blocked container.                                                                                                            |
| Existing layout is preserved | Both components sit below the page header and above the first working region. They do not reorder, restyle, resize or remove the page's other approved regions, apart from the elements they replace. Adding them is a targeted change, not a redesign.                                                         |
| Nothing invented             | Every headline, holder, stage, marker, figure and fix label comes from the change unit's variant. If a value is not supplied it is omitted; if nothing is supplied the component is not drawn.                                                                                                                  |

**Correction to Section 5.1 under this note.** The layout in Section 5.1 shows "Budget fit" as a stage of the journey tracker. Under this note and KT-STD-001 v1.8 §2.9.2, budget fit is a computed condition, not a formal step: it appears as the blocked marker on the current stage and in the next-step block, not as a stage of its own. The per-line budget-fit table belongs in the page's working region, replacing the existing funding cell, rather than directly beneath the next-step block. Section 5.1 is otherwise retained as the illustration of the content involved.

# 6\. Layer 2: the "no dead ends" test

## 6.1 The rule

Every record screen, for every role that can see it, must show at least one of:

- an action that person can take now; or
- a plain statement of what is needed, who has to do it, and a link to where.

A page with only disabled buttons and no explanation fails. The rule is enforced by an automated check that walks each state as each user, in the same way the persona passes already run. It is cheap, and it would have caught every failure listed in Section 1.1.

## 6.2 How the test runs

The test runs at the API level first, because that is fast and can be exhaustive, and then as a thinner UI check that the shared component actually renders what the API returned. It enumerates every state in each module's workflow, every SEED-001 persona, and every record page. For each combination it asserts the following.

| **Assertion**                                                                      | **Fails when**                                                   |
| ---------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| The viewer has an enabled action, or a next_step with a named holder and a reason  | A page has only disabled buttons and no explanation              |
| Every disabled or hidden action the role could otherwise perform has a reason code | An action vanishes silently, as "Request funding check" did      |
| Every fix link opens a page where the named holder can act                         | A link points to a page the holder cannot open, or cannot act on |
| The stage in next_step matches the stage the tracker shows                         | The tracker and the next-step block disagree                     |

## 6.3 Negative fixtures

The happy-path seed alone will not exercise the failures actually encountered. Each module also supplies deliberate negative fixtures built on the SEED-001 scenario, including at least:

- a plan over budget on one line;
- a record returned with comments;
- a record rejected;
- a need accepted but not yet planned;
- a plan superseded while a requisition was in progress.

## 6.4 Output

The test produces a dead-end matrix: one row per state and persona, marked pass or fail with the reason. It runs in CI and blocks merges on failure. Run once against today's screens, the same matrix is the first dead-end audit of the current system.

# 7\. Layer 3: My Work covering every hand-off

## 7.1 The hand-off register

Every point where work passes from one person to another gets one row in a hand-off register, and each module's specification owns its own rows. Each row must put an item in the next holder's My Work, send a notification, and give the sender a "waiting on" item. Today this is patchy; the update prompt added in the originating session filled one gap. The audit also confirms that "waiting on" items appear for the person who is waiting.

## 7.2 Starting rows for Planning

| **Event**                             | **Next holder**                       | **Their My Work item**               | **Sender's "waiting on" item**                        | **Clears when**                |
| ------------------------------------- | ------------------------------------- | ------------------------------------ | ----------------------------------------------------- | ------------------------------ |
| Need accepted by Procurement          | Procurement Planner                   | Add accepted need to a plan          | Need author: waiting on planning                      | Need is included in a purchase |
| Budget revision requested from a plan | Budget Officer                        | Revise budget line for plan update   | Planner: waiting on budget revision                   | Revision submitted or declined |
| Budget revision submitted             | Budget Approver                       | Approve budget revision              | Budget Officer: waiting on approval                   | Approved or returned           |
| Budget revision approved              | Procurement Planner                   | Plan now fits; request funding check | None                                                  | Funding check requested        |
| Funding check requested               | Finance Confirmation Officer          | Confirm funding for plan update      | Planner: waiting on Finance                           | Confirmed or returned          |
| Finance confirmed                     | Head of the Procurement Function      | Sign and submit plan update          | Planner: waiting on submission                        | Submitted or returned          |
| Submitted                             | Accounting Officer                    | Approve plan update                  | Head of the Procurement Function: waiting on approval | Approved or returned           |
| Plan update in force                  | Requisition raisers for its purchases | Purchase ready for requisition       | None                                                  | Requisition raised             |

The statutory-approval row is deliberately left out. Whether it applies, and to whom, depends on the route rules in PLN-CHG-001, and it must be taken from that document rather than assumed.

## 7.3 Conventions

- **Items clear on state change.** My Work items clear when the underlying record changes state, never on "mark as read", so the list cannot drift from reality.
- **Returns are their own rows.** Every "returned" path is a separate register row that carries the returner's comment into the item, because returns are where people get lost.
- **Other hand-offs to audit.** The register must also cover, at minimum: plan accepted, update needed, and over budget, alongside the rows above.

# 8\. Layer 4: the journey tracker and Home

## 8.1 The journey tracker

Strategy, Budget, Need, departmental plan, annual plan, requisition and tender form the spine of the system. A small tracker on each record shows every stage, which are done, where the record is now, and who holds it. The need page's "Where this requirement stands" is an early version of this.

The tracker shows the record's own lineage, not the whole system. On a plan update, that is its approval stages (as in Section 5.1), plus an upstream link such as "5 needs included" and a downstream link such as "0 requisitions raised". Fan-in and fan-out appear as counts with links rather than as a tree, which keeps the tracker readable when one plan holds dozens of purchases. Each stage shows who acted and when, or who holds it now.

## 8.2 Home

Home is currently a placeholder, marked Planned in the navigation. It becomes the entry point, made of three lists fed by the same next_step data:

| **List**           | **Contents**                                                                         |
| ------------------ | ------------------------------------------------------------------------------------ |
| Your turn          | Items where the viewer can act, including blocked items with the reason shown inline |
| Waiting on others  | Items the viewer is waiting on, with the holder and how long it has waited           |
| Recently completed | Items the viewer finished or that finished on the viewer's behalf                    |

No new logic is needed for Home. It is a query over what Layers 1 and 3 already produce.

# 9\. Other defects on the Prepare plan update screen

These would fail a companion rule that every status and figure on a record page carries a defined meaning the user can read.

| **Element**                                                   | **Problem**                                                                 | **What the standard requires**                                         |
| ------------------------------------------------------------- | --------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| "Current work: Ready" column                                  | Does not say what the purchase is ready for                                 | State what it is ready for, or who acts next on it                     |
| "Remaining allocation KES 0" beside "Required allocation met" | No explanation of how the two relate                                        | A readable meaning for each figure in the reservation allocation panel |
| "Funding: Not yet checked"                                    | Merges live budget fit with Finance confirmation, and hides a known overrun | Split into the two facts in Section 5.2                                |
| Button row with only Cancel plan update and Save draft        | The next workflow action is absent with no explanation                      | A next-step block per Section 4                                        |

# 10\. Implementation order

1. **Guard reasons and the next-step contract** (Sections 3 and 4). The foundation every other layer reads from.
2. **The dead-end test and the next-step block** (Sections 5 and 6). Cheap, and together they would have caught everything encountered in the originating session. The first run doubles as the audit of current screens.
3. **The hand-off register and audit** (Section 7).
4. **The journey tracker, then Home** (Section 8).

# 11\. Placement in the document set

This affects every module, so it is written as one shared standard that each module's specification then follows. Otherwise each screen keeps solving it differently. Under the established KenTender discipline, new cross-cutting principles go into KT-STD-001 rather than being re-derived per document.

| **Document** | **Change**                                                                                                                                                                  | **Resulting status**                                                   |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| KT-STD-001   | New section defining the guard-reason principle, the next-step contract, precedence rules, the dead-end test and the hand-off register format                               | Version 1.8, Proposed (drafted 25 September 2026 from version 1.7)     |
| PLN-CHG-001  | Required correction: a state-by-role next-step table and Planning hand-off register rows; the budget-fit and Finance-confirmation split; the Request budget revision action | New version, Proposed (first, since it carries the defect encountered) |
| NDS-CHG-001  | Required correction: state-by-role next-step table and hand-off register rows                                                                                               | New version, Proposed                                                  |
| REQ-CHG-001  | Required correction: state-by-role next-step table and hand-off register rows                                                                                               | New version, Proposed                                                  |
| BUD-CHG-001  | Required correction: receiving side of the Request budget revision hand-off                                                                                                 | New version, Proposed                                                  |
| SEED-001     | Negative fixtures listed in Section 6.3                                                                                                                                     | New version, Proposed                                                  |

Each of these edits must preserve the full existing content of the document and weave the changes in as additions.

# 12\. Open questions

| **Question**                                                                                                       | **Why it is open**                                                                                                                    |
| ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| When does statutory approval apply to a plan update, and who performs it?                                          | Must be taken from the route rules in PLN-CHG-001, not assumed                                                                        |
| Should an over-budget draft notify the Budget Officer automatically, or only when the planner requests a revision? | This document proposes the latter, because the planner chooses between increasing the budget and shrinking the plan; needs a decision |
| Should waiting items escalate after a set time, and if so, what time?                                              | No timeline is defined here; any statutory or policy timelines must come from the governing texts                                     |
| What do the reservation allocation figures mean, and how should they be labelled?                                  | The screen's figures are not self-explanatory; their definitions belong to the Planning specification                                 |
| Exact section numbers in KT-STD-001 v1.4 and PLN-CHG-001 v1.15                                                     | This draft was written without those documents to hand                                                                                |