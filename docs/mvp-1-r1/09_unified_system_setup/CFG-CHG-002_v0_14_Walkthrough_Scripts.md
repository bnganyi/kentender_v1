# System setup — representative-user walkthrough scripts

**For:** the facilitator running CFG-CHG-002 v0.14 §11.4 sessions with real users.
**Status:** prepared 25 Sep 2026; **no session has been run yet**. Results are owed (FU-06) and go in the results table at the end, then into the tracker's acceptance map (CFG-UX-AC-27, CFG-UX-AC-28, CFG10-AC-036, CFG10-AC-058).

Automated browser tests already cover keyboard and focus, errors at the field, pending buttons, 200% zoom, narrow year cards and footers (the System setup gates). These sessions answer a different question: **can a person new to KenTender do the task and explain what happened, without help?**

## How to run a session

- One participant at a time, 20–30 minutes, their own login with the stated role. Never share the Administrator password on screen.
- Read the task aloud exactly as written. Do not use the words "intake", "reference set", "payload" or "version id" — if the screen needs them, that is a finding.
- Ask the participant to think aloud. Do not help. If they are stuck for two minutes, note it as a detour, give the smallest hint, and carry on.
- After each task, ask the "check questions" and write their answer in their own words.
- Record: completed yes/no, time, detours (where they looked first), explanations they asked for, and every wrong prediction.
- Use a prepared test site for anything marked **test site only**. The standard site (`make seed-canonical`) must be restored afterwards.

Start page for all sessions: `http://<site>/app/system-setup`.

---

## Session 1 — Administrator or System Manager new to KenTender

**Setup:** standard site. Pick a start year that does not exist yet (for example 2031).

**Tasks (read aloud):**
1. "Add the financial year that starts in July 2031."
2. "Let departments start sending their procurement needs for that year."
3. "Change the last day departments can send them to 15 March 2032, 5 pm."

**Check questions:**
- "Which modules does what you just did affect? Which does it not affect?"
- "If another year was already open for needs, what happened to it?"
- "What would a department see now?"

**Pass signals:** finds Financial years without a hint; opens submissions from the year's own page; predicts that only departmental needs are affected (not budgets or disposal plans), and that an earlier open year stops taking needs. **Watch for:** looking for a "Save" or "Approve" step; asking what "submission" means.

**Clean up:** disable the added year from its page, or reseed.

## Session 2 — Setup maintainer: disable a funding source

**Setup:** test site only — a funding source that is already used by a saved budget line (for example "Development partner" on the standard site's budget).

**Tasks:**
1. "Stop people choosing <source> for new budget lines."
2. "Find where you can still see that this source was used before."

**Check questions:** "Does this change budgets already saved? Can someone still pick it on a new budget line?"

**Pass signals:** says existing budget lines keep the source and new lines cannot select it; finds the source still listed, marked not available for new selection.

## Session 3 — Setup maintainer with source material: correct a rule

**Setup:** test site only. Give the participant a printed extract of the Act/Regulations for the reservation rule (30% of the eligible value of the current Annual Plan; county 20%). Prepare a rule whose name was saved but whose version failed ("Rule created; version not saved" — create it and cancel the version).

**Tasks:**
1. "The reservation rule's county percentage is wrong. Put in the figure from this extract, from 1 July 2027."
2. "Someone started a rule yesterday and the details never saved. Finish it."
3. "You have checked the source but the gazette reference isn't to hand yet. Record that."

**Check questions:**
- "Is the rule saved? Is it verified? Is it complete? Can Planning use it?" (four separate answers expected)
- "What happens to the rule that was in force before?"
- "What still needs to be done before this is fully verified?"

**Pass signals:** keeps the four states apart (no "it's ready"); reads the "what it replaces" line before saving; records the check as "Pending" and names the missing evidence.

## Session 4 — Setup maintainer: inspect a working-day schedule

**Setup:** standard site; open **Procurement settings → Schedules**, pick Open Tender / Goods.

**Task:** "Explain to a new colleague how long the bid period is for this schedule, and what could make it wrong."

**Check questions:** "Counted from what, to what? Calendar or working days? Is that the law or our planning assumption? What happens if the holiday calendar isn't verified?"

**Pass signals:** names both endpoints of an interval; distinguishes a legal minimum from a planning default; knows that a working-day interval depends on the verified calendar.

## Session 5 — Administrator or System Manager: edit a scheduled assignment

**Setup:** standard site before 1 Oct 2026, or any date before Julia Njeri's acting period starts. Julia Njeri is scheduled as acting Head of User Department, Digital Health, from 1 Oct to 30 Nov 2026 (authority MOH/HR/ACT/2026/041).

**Tasks:**
1. "Julia's acting appointment has been moved to start on 5 October. Update it."
2. "Now look at Grace Wanjiku's responsibility as Departmental Author. Change its start date."

**Check questions:** "Did Julia lose the assignment at any point? What would happen if you cleared the start date? Where can you see what changed?"

**Pass signals:** edits without revoking and re-creating; says clearing the start date makes it active immediately; finds one history entry with before and after; correctly finds **no** edit action on Grace's assignment because it has started.

**Clean up:** reseed, or set Julia back to 1 Oct.

## Session 6 — Accounting Officer or business reviewer: meet a configuration block

**Setup:** test site only. Planning screen for a plan whose reservation rule has no verified source check (the Planning test world, or mark the rule's latest check "Rejected" on a copy).

**Task:** "Approve this plan." (They should not be able to.)

**Check questions:** "Why can't you? Who fixes it? What can you do meanwhile?"

**Pass signals:** names the cause (the rule's source isn't verified) and the owner (the setup maintainer) without opening System setup; does not ask for System setup access to finish their own task.

## Session 7 — System Manager and Auditor

**7a — Missing organisation root (System Manager). Setup:** test site only, with the root organisation unit missing.
**Task:** "Add a new department."
**Pass signals:** reads that only the Administrator can repair the structure and says they will ask one; does not look for a way around it.

**7b — Past decision, current rejection (Auditor). Setup:** test site only — a plan approved while the reservation rule was verified, and a later check on the same rule version recorded as "Rejected".
**Task:** "Was this plan approved on a valid rule?"
**Pass signals:** separates "valid at the time of the decision" from "rejected now"; does not conclude that the old approval was wrong or has been recalculated.

---

## Results

| Session | Participant (role, not name) | Date | Completed | Time | Detours | Wrong predictions / questions | Facilitator notes |
|---|---|---|---|---|---|---|---|
| 1 | | | | | | | |
| 2 | | | | | | | |
| 3 | | | | | | | |
| 4 | | | | | | | |
| 5 | | | | | | | |
| 6 | | | | | | | |
| 7a | | | | | | | |
| 7b | | | | | | | |
