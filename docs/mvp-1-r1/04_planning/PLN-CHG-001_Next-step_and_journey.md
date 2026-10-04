# PLN-CHG-001 — Next-step and journey content (§2.6.8 item 12)

| Control | Value |
|---|---|
| Status | **Draft for Project Owner review.** Not approved. Not a design input until approved. |
| Proposed home | PLN-CHG-001 v1.26 (Proposed): new §10.1A, plus a **Next step and journey** paragraph at the end of each screen section in §10.3–§10.17 |
| Governs against | KT-STD-001 v1.8 (Proposed) §2.6.8 item 12, §2.9, §3B; Workflow Guidance Standard (approved 25 Sep 2026) |
| Base | PLN-CHG-001 v1.25 §10 and §10.2 closed fixture pack. All v1.25 content is retained; this adds to it. |
| Date | 25 September 2026 |

**Wording status.** Stage labels and marker words come from §5.2.1 and §5.2.3. Actors, times and figures come from §10.2, or from the approved Workflow Guidance Standard where this says so. Headlines and fix labels shown in **bold** are new proposed wording. The Project Owner approves them here; the designer never writes them.

---

## 10.1A Shared next-step and journey definitions

### 10.1A.1 Annual Plan journey tracker

The tracker has one row with seven formal stages, in this order. Budget fit is a computed condition, so it is not a stage (KT-STD-001 §2.9.2).

| # | Stage label | Formal step (§5.2.3) | Holder when current |
|---|---|---|---|
| 1 | **Preparation** | Form, edit and request funding confirmation | Procurement Planner — Mercy Kilonzo |
| 2 | **Funding confirmation** | Confirm plan funding / Return to planner | Finance Confirmation Officer — Josphat Mwangi |
| 3 | **Signature** | Sign and submit Annual Plan | Head of Procurement Function — Charles Mutiso |
| 4 | **AO adoption** | Adopt and submit | Accounting Officer — Amina Hassan |
| 5 | **Cabinet Secretary approval** | Approve Annual Procurement Plan | Configured statutory authority — Daniel Rotich |
| 6 | **Publication** | Record Treasury submission; transmit and reconcile | As stated per U13 variant |
| 7 | **In force** | Activation (end state) | None |

- Stage 5 takes its label from the configured authority. It reads **Cabinet Secretary approval** for the Ministry fixture and **Council decision** for U11-COLLECTIVE. Whether and when this stage applies is decided by PLN-CHG-001's route rules, not by this section.
- The markers are **Done**, **Current**, **Blocked** and **Not started**, each shown as text. Only the current stage names its holder. The accent is used on the current stage only. Status colour is used only on Blocked and Done.
- The upstream link reads **{n} departmental requirements included**; BASE is **3 departmental requirements included**, linking to Requirements ready to add. The downstream link reads **{n} requisitions raised** and appears only when the stage is In force. Its count comes from U14's owner evidence.
- **Reduced form**, for use under the first-view budget: one line reading **Stage {n} of 7: {label} — {holder}**. It is required on U13, and wherever a variant below says **reduced**.
- **Placement:** directly below the page header and above the first working region. The tracker comes first, then the next-step block when one is drawn.
- **Returned and withdrawn Versions:** the correction Draft's tracker restarts at Preparation (Current). The returning stage is not marked on the tracker; the return and its comment stay in Changes and history.

### 10.1A.2 Departmental plan journey tracker

There are four stages: **Preparation** (Departmental Author) · **Certification** (Head of User Department) · **Procurement review** (Procurement Planner) · **Accepted**. It follows the same marker, placement and reduced-form rules as §10.1A.1. There is no upstream or downstream link.

### 10.1A.3 Budget fit and Finance confirmation (U07, replaces the Funding cell)

The Plan checks cell **Funding: Not yet checked** is removed from every U07 variant and replaced by two separate facts:

1. **Budget fit, checked now.** This is the live computed result, shown in the working region as a small table with the columns Budget line; Approved; This plan; Difference. BASE rows are MOH-BL-DHI-2027 / KES 100,000,000 / KES 80,000,000 / **Within by KES 20,000,000**, and MOH-BL-HWD-2027 / KES 60,000,000 / KES 50,000,000 / **Within by KES 10,000,000**. When every line fits, the result line reads **Within each approved budget line**, and the table sits under **View budget lines**.
2. **Finance confirmation.** This is one labelled line showing the funding-evidence state from §5.2.2: **Not requested**, **Requested from Josphat Mwangi**, **Confirmed by Josphat Mwangi on {instant}**, **Returned** or **Stale**. It is never merged with budget fit.

The budget ceiling (KES 160,000,000) stays out of both, as it does out of the reservation calculation.

### 10.1A.4 Screens that carry neither component

These are stated explicitly under rule 4 of KT-STD-001 §2.9.3:

- **U01 Planning workspace:** a Work workspace, so it carries neither. Its task rows keep their plain-language work state. A blocked Plan's row states the blocker's headline in its narrative (see U01 below).
- **U03, U04 and U08:** a funding panel, dialogs, a direct-requirement form and a focused panel respectively. None carries either component.
- **U09 Purchase editor:** the purchase is part of the Plan record. The Plan's next step is stated once, on U07. U09 keeps its own purchase-level issue line.
- **U12 departmental evidence:** a pinned-source evidence view with no lifecycle of its own.
- **U14 procurement progress:** a monitoring register.
- **U16 correction requests:** a correction workspace. Each request keeps its own status text.
- **C01–C04:** setup owner surfaces. The Planning-side missing-setting panel is a blocker in the host screen's next-step block, not a separate panel (see §10.1A.5).
- **U21 dialogs and page states:** carry neither. Page states replace protected content, including both components.

### 10.1A.5 Blocker catalogue used below

These are the proposed guard reason codes, to be added to §5 and §8. Figures and fixes come from the guard (KT-STD-001 §3B.1).

| Reason code (proposed) | Headline pattern | Fix controls, owner |
|---|---|---|
| `PLN_BUDGET_LINE_EXCEEDED` | **Over budget by KES {over} on {line name}** | **Request budget revision from {Budget Officer name}** (hand-off, Budget Officer); **Reduce a purchase** (Procurement Planner; moves focus to Purchases) |
| `PLN_RESERVATION_SHORTFALL` | **Reserved procurement is below the required allocation by KES {shortfall}** | **Review reserved procurement** (Procurement Planner; opens the purchase named in Current work) |
| `PLN_METHOD_NOT_SELECTED` | **{n} purchase needs a procurement method** | **Choose a procurement method** (Procurement Planner; opens that purchase) |
| `PLN_SETTING_MISSING` | **{Setting} is not set up** | **Open System setup** when the actor holds setup access. Otherwise the fix names Administrator or System Manager, and the hand-off command is an open question (§10.1A.7). |
| `PLN_INTAKE_CLOSED` | **Initial submissions are closed** | Open question: which responsibility reopens intake (§10.1A.7) |

The blocked block lists every blocker together, one fix control each. It states the headline figure only. The supporting figures appear once, in the working region: the budget-fit table, the reservation allocation block, or the purchase row.

### 10.1A.6 New variants this section requires

| ID | Purpose | Fixture needed before design |
|---|---|---|
| **U07-UPDATE-OVER-BUDGET** | The defect case: a plan update over budget on one line | SEED-001 negative fixture. It uses the approved Workflow Guidance Standard figures: MOH-BL-HWD-2027 approved KES 60,000,000, this plan KES 62,000,000, over KES 2,000,000; purchase **testing requisitions** (PPI-MOH-2027-003), KES 2,000,000. Its purchase list and references must be reconciled with §10.2, whose laptop item is PPI-MOH-2027-033. The fixture builder supplies the full Version 2 purchase list. |
| **U07-WAITING-BUDGET-REVISION** | After Mercy requests the revision | Request instant (the `since` value), from the same negative fixture |
| **U11-PLANNER** | Mercy viewing her own submitted Plan (Awaiting AO or statutory approval). Today no artboard answers this, so it is a dead end. | Reader layout of U11, Mercy, READY, 8 Dec 2026 before adoption |

### 10.1A.7 Open questions for the Project Owner

1. Should the headline for a blocked Draft with several blockers be the first blocker, or a count ("**2 things stop this plan going to Finance**")? The draft below uses the count when there are two or more.
2. Does `PLN_METHOD_NOT_SELECTED` block pre-Finance readiness (§5.3.1)? U07 lists "Choose a procurement method" as current work but does not say whether it blocks the Finance request.
3. Who reopens departmental intake (U02-CLOSED)? Which responsibility owns the missing-setting hand-off (C01–C04)?
4. Should an over-budget Draft notify the Budget Officer automatically? The Workflow Guidance Standard proposes not: only when Mercy requests a revision.
5. The screenshot of the live build shows a required allocation of KES 42,600,000 and a 43.66% share. §10.2 and RES-IMP-001 give KES 39,000,000 and 38.46%. The build or its data needs checking; this section uses §10.2.

---

## Per-screen next step and journey

Each subsection below is appended to the matching v1.25 screen section. The "Replaces" column names the v1.25 element removed under rule 1 of §2.9.3. Nothing else on the artboard changes.

### U02–U05 — Departmental plan (append to §10.4)

The tracker is §10.1A.2, in reduced form on U02-AUTHOR-DRAFT only, because the summary strip and table already fill the first view.

| Variant | Kind | Headline and sentence | Holder / since | Fixes | Replaces | Tracker |
|---|---|---|---|---|---|---|
| U02-AUTHOR-DRAFT | Your turn | **Enter funding details for 1 requirement** | — | Existing row action **Enter funding details** | Context row "Status Draft" | Reduced: **Stage 1 of 4: Preparation — Grace Wanjiku**. The sentence "Your Head of Department must review and submit this plan." is retained. |
| U02-CLOSED | Your turn, blocked | **Initial submissions are closed**. Sentence: the existing text "You can keep editing this draft, but it cannot be submitted now." | — | Pending open question 3 | The standalone closed-intake sentence above the footer | Preparation Blocked |
| U02-ACCEPTED-UPDATE | Your turn | **Continue the departmental update** | — | Existing **Continue update** | Nothing. The formal status "Accepted — update in progress" stays. | Preparation Current (update candidate) |
| U05-HOD | Your turn | **Certify and submit the departmental plan** | — | Existing **Submit departmental plan** | Nothing | Preparation Done · Certification Current — Julia Njeri |
| U05-CORRECTION | Your turn | **Correct and resubmit the departmental plan**. Procurement's comment stays beside the affected row. | — | Existing **Resubmit departmental plan** | Notice heading "Your plan needs a correction" | Certification Current. **The fixture must state the viewing actor.** |
| U05-ALL-EXCLUDED | Awaiting fixture | — | — | — | — | — |

### U06 — Procurement review (append to §10.5)

| Variant | Kind | Headline and sentence | Holder / since | Fixes | Replaces | Tracker |
|---|---|---|---|---|---|---|
| U06 | Your turn | **Classify every included requirement, then accept or return the submission** | — | Existing Accept / Return | Badge "Awaiting Procurement review" and the "Decision required — …" sentence | Preparation Done · Certification Done · Procurement review Current — Mercy Kilonzo |
| U06-CLASSIFICATION-MISSING | Your turn | **Select the requirement type for 1 requirement, then accept** | — | The row error stays at the row | As U06 | As U06 |
| U06-STALE-SOURCE | Your turn | **A source requirement changed after certification. Return the submission to the department.** | — | Existing **Return to department** | Notice "A source requirement changed…" | As U06. Awaiting fixture. |
| U06-SEGREGATION | Waiting on someone | **Waiting for Procurement review by another Procurement Planner**. The existing sentence "You cannot review a departmental plan you certified." is retained. | **The fixture must name the person** | None | Nothing | As U06 |
| U06-ACCEPTED-CLASSIFICATION | Done | **Accepted by Mercy Kilonzo on 29 Nov 2026, 15:00 EAT** | — | None. **Correct classification** stays a row action. | Header "Status Accepted" | All four Done |

### U07 — Annual plan preparation (append to §10.6)

The tracker is §10.1A.1 in full. Budget fit and Finance confirmation follow §10.1A.3 in every variant.

| Variant | Kind | Headline and sentence | Holder / since | Fixes | Replaces | Tracker |
|---|---|---|---|---|---|---|
| U07 (BASE) | Your turn, blocked | **2 things stop this plan going to Finance**. Sentence: **You can request the funding check once both are resolved.** Items: **Reserved procurement is below the required allocation by KES 39,000,000**; **1 purchase needs a procurement method** (the second item depends on open question 2). | — | **Review reserved procurement**; **Choose a procurement method** | The Plan checks "Reserved procurement" line (its figures stay in the reservation allocation block) and "Funding: Not yet checked" | Preparation **Blocked** — Mercy Kilonzo; stages 2–7 Not started. Upstream: **3 departmental requirements included** |
| U07-UNALLOCATED | Your turn | **Add the accepted requirements to purchases** | — | Existing **Add selected requirements**, which keeps its disabled helper | Nothing | Preparation Current — Mercy Kilonzo |
| U07-ONE-SELECTED / U07-TWO-SELECTED | Your turn | As U07-UNALLOCATED | — | As above, enabled | Nothing | As above |
| U07-WAITING-FINANCE | Waiting on someone | **Waiting for Josphat Mwangi (Finance Confirmation Officer) to confirm plan funding** | Since: request instant, **awaiting fixture** | None | Notice "Finance is reviewing the funding." and the separate "Requested from" field | Preparation Done · Funding confirmation Current — Josphat Mwangi |
| U07-FINANCE-COMPLETE | Waiting on someone | **Waiting for Charles Mutiso (Head of Procurement Function) to sign and submit** | Since 4 Dec 2026, 10:00 EAT | None | Notice "Ready for the Head of Procurement Function to sign and submit" and the "Responsible person" field. The Finance confirmation line keeps Checked by / Checked at. | Preparation Done · Funding confirmation Done · Signature Current — Charles Mutiso |
| **U07-UPDATE-OVER-BUDGET** (new) | Your turn, blocked | **Over budget by KES 2,000,000 on Digital health workforce development**. Sentence: **You can request the funding check once every budget line fits. Choose one way to fix it.** | — | **Request budget revision from Josphat Mwangi** (hand-off; opens the request with the line and figure prefilled); **Reduce a purchase** | Plan checks "Funding: Not yet checked". Budget fit shows the table with MOH-BL-HWD-2027 **Over by KES 2,000,000**. Finance confirmation: **Not requested**. | Preparation **Blocked** — Mercy Kilonzo. In the header orientation line, Current plan Version 1 stays in force. |
| **U07-WAITING-BUDGET-REVISION** (new) | Waiting on someone | **Waiting for Josphat Mwangi (Budget Officer) to revise the budget line** | Since: request instant, **awaiting fixture** | None. **Reduce a purchase** stays available as ordinary Draft editing. | As U07-UPDATE-OVER-BUDGET | Preparation **Blocked** — Mercy Kilonzo. The budget revision is not a Plan stage. |
| U07-UPDATE | Awaiting fixture | The kind follows the fixture's checks. If they pass: Your turn, **Send the update to Finance for funding review** | — | Existing footer primary | "Draft update" badge stays (formal status) | Preparation Current |

**First-view check (U07-UPDATE family).** Header, then the tracker (one row), the blocked block (headline, sentence and two buttons), the Reason field and the Project name field. With these, the Purchases heading must still start within the 1024 px view. If it doesn't, the tracker switches to its reduced form.

### U09 — Purchase editor (append to §10.8)

Neither component (§10.1A.4). The purchase-level issue lines stay as they are. The Plan-level blocker is not repeated.

### U10 — Funding review (append to §10.9)

| Variant | Kind | Headline and sentence | Holder / since | Fixes | Replaces | Tracker |
|---|---|---|---|---|---|---|
| U10 / U10-LOW-AVAILABILITY | Your turn | **Confirm plan funding or return the plan to the planner** | — | Existing footer actions | Badge "Your decision required" and the "Decision required — …" sentence | Preparation Done · Funding confirmation Current — Josphat Mwangi |
| U10-OVER-APPROVED | Your turn | **Return the plan to the planner**. The existing issue line "Digital Health exceeds its approved budget by KES 10,000,000." stays above the comparison. | — | Existing **Return to planner** | As U10 | As U10 |
| U10-CHANGED | If a replacement is supplied: Your turn, **Open the updated funding review**. Otherwise: Waiting on someone, **Waiting for the Procurement Planner to request a new funding check** | Mercy Kilonzo; since **awaiting fixture** | Existing link, if supplied | "Responsible role Procurement Planner" field | As U10 |
| U10-REASSESS | Your turn | **Check the current plan against the revised budget** | — | Existing actions | Nothing | Not drawn: reassessment is outside the approval lifecycle. The header states "current plan". |
| U10-HISTORY | Not involved | — | — | — | — | All seven Done / In force. **The fixture must state the viewer.** |

### U11 — Annual plan review (append to §10.10)

The next-step line sits in the header region, where v1.25 places the actor's decision statement for orientation. The decision statement itself stays beside the buttons, because it is the consequence (§2.6.5), not status. The **{Current stage}** token in the orientation line is removed, since the tracker carries it.

| Variant | Kind | Headline and sentence | Holder / since | Fixes | Replaces | Tracker |
|---|---|---|---|---|---|---|
| U11-HOPF | Your turn | **Sign and submit the annual plan** | — | Existing primary | "· Funding checked" in the orientation line | 1–2 Done · Signature Current — Charles Mutiso |
| U11-AO | Your turn | **Adopt and submit the plan, or return it for correction** | — | Existing actions | "· Awaiting Accounting Officer" | 1–3 Done · AO adoption Current — Amina Hassan |
| U11-STATUTORY | Your turn | **Approve the annual plan, or return it for correction** | — | Existing actions | "· Awaiting Cabinet Secretary" | 1–4 Done · Cabinet Secretary approval Current — Daniel Rotich |
| U11-STALE-EVIDENCE | Your turn | **Return the plan for a new funding check**. The existing issue stays in the Decision summary. | — | Existing **Return for correction** | As U11-AO | AO adoption **Blocked** — Amina Hassan |
| **U11-PLANNER** (new) | Waiting on someone | **Waiting for Amina Hassan (Accounting Officer) to adopt the plan** | Since 7 Dec 2026, 10:00 EAT | None | — | 1–3 Done · AO adoption Current — Amina Hassan |
| U11-READER | Not involved | — | — | — | Orientation stage token | Markers per the exact selected Version; **the fixture must state the stage** |
| U11-READER · historical | Not involved | — | — | — | — | Not drawn. "Historical plan — read only" stays. |
| U11-COLLECTIVE / LATE-ADOPTION / UPDATE | Awaiting fixture | Follow the U11-STATUTORY / U11-AO pattern | — | — | — | Stage 5 label **Council decision** for COLLECTIVE |

### U13 — Publication and recovery (append to §10.12)

The tracker is always in **reduced** form: **Stage 6 of 7: Publication — {holder}**. The four publication status rows stay as the Level 2 working region, because they are the working detail of stage 6, not a second tracker. The header state row (for example "Approved — Treasury submission details needed") is replaced by the next-step line.

| Variant | Kind | Headline | Holder / since |
|---|---|---|---|
| U13 | Your turn | **Record the Treasury submission** | — |
| U13-TREASURY-FORM (and checked) | Your turn | Neither component: this is a form state of U13 | — |
| U13-EVIDENCE-RECORDED | Waiting on someone | **Waiting for website publication** | System; since **awaiting fixture** |
| U13-SENDING | Waiting on someone | **Publication is in progress** | Responsible system and start time from the attempt fixture |
| U13-FAILED (operator) | Your turn | **Retry publication** | — |
| U13-FAILED (AO / reader) | Waiting on someone | **Waiting for an authorised technical operator to retry publication** | Since: failure time from the fixture |
| U13-UNKNOWN (operator) | Your turn | **Check the publication result** | — |
| U13-ACTIVE | Done | **In force since {Activated at}**. The tracker becomes stage 7 of 7. | Activated at from the fixture |
| U13-PUBLISHED-HELD (Planner) | Your turn | **Prepare a corrected plan** | — |
| U13-UNPUBLISHED-DEFECT (AO) | Your turn | **Request withdrawal for correction** | — |
| U13-WITHDRAWAL-REQUEST (AO) | Waiting on someone | **Waiting for Daniel Rotich (Cabinet Secretary) to decide the withdrawal** | Since: request time from the fixture |
| U13-WITHDRAWAL-REQUEST (Daniel) | Your turn | **Withdraw the plan for correction** | — |
| U13-WITHDRAWN (Planner) | Your turn | **Continue the correction**. The tracker restarts at Preparation on the correction Draft. | — |
| U13-CORRECT-EVIDENCE, both dialogs | Neither component | — | — |

### U01 — Planning workspace (append to §10.3)

No tracker and no next-step block (§10.1A.4). The next-step answer feeds the Plan task row's narrative:

- U01 BASE is unchanged. Its existing issue block is already the plain-language blocker.
- **U01-CURRENT-UPDATE, blocked by budget** (row variant for the U07-UPDATE-OVER-BUDGET fixture): the narrative reads **Over budget by KES 2,000,000 on Digital health workforce development**, with primary **Continue update**.
- **U01-CURRENT-UPDATE, waiting on budget revision**: the narrative reads **Waiting for Josphat Mwangi (Budget Officer) to revise the budget line**, and the action is **View update**.

---

## Dependencies outside §10 (for the same v1.26)

- **§5:** the state-by-responsibility next-step table for each Plan and DPP state; the reason codes and fixes in §10.1A.5; the budget-fit / Finance-confirmation split (§5.2.2 gains "Budget fit" as a live computed fact).
- **§7:** a new hand-off command, `RequestBudgetRevision`, with its matching BUD-CHG-001 receiving side.
- **§5 or §7:** hand-off register rows from the Workflow Guidance Standard §7.2 (the statutory row is excluded).
- **§11.9:** action-map rows for **Request budget revision from {name}**, **Reduce a purchase**, **Review reserved procurement** and **Choose a procurement method**.
- **§13 / SEED-001:** the negative fixtures for the new variants in §10.1A.6.
- **§14:** dead-end matrix acceptance for every variant above.
