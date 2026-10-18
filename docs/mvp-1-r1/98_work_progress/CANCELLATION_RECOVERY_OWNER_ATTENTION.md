# Cancellation recovery — what needs the Project Owner's attention

Started 18 October 2026 while building the whole-Tender cancellation recovery (PLN v1.32, TPR v0.21/v0.22, REQ v1.20, BUD v1.17). It is a running list, kept in plain words. Each item says what was found, what I did about it, and what only you can decide. Nothing here is a claim that something was released or deployed.

## Decisions (answered by the Project Owner, 18 October 2026)

1. **Who runs the recovery worker where there is no scheduler: the Technical Operator, by hand** (`make cancellation-recovery-run SITE=<site>`). The development site has no scheduler, so a recovery stays Pending there until a technical operator runs it. Nothing else was changed.
2. **Migrate the development site now, and reconcile.** Done the same day; figures are in the evidence map ("The development site"). The two cancelled demo Tenders were recovered: KES 37,000,000 of reservations released.
3. **Canonical seed and the two cancelled demo Tenders (T10, T11):** the owner's "migrate now" answer accepted the changed figures. The seed and SEED-002 are unchanged, so a reseed registers the two recoveries as Pending and a technical operator runs the worker. SEED-002 and the Analytics expected values should be re-read at the next reseed.
4. **The support operator** is the existing technical operator (chosen at the start); no new role.
5. **A new consequence found on 18 October:** on the development site the canonical world check now fails on one line, "a recorded event is later than the anchor", because the recovery's Budget events are dated 18 October. It will do the same after any real action; a reseed takes a new anchor.

**Still open, not asked yet:** cancelling a Tender after its submission period has closed is still not possible (the approved text lists it; Bid Opening says it waits for Bid Opening and Evaluation to approve their side).

## Found and fixed (already in the code)

1. **After an Annual Plan update was activated, a purchase that had already been drawn from read as undrawn and could be drawn again up to its full ceiling.** The plan copies each source allocation as a new row when it makes a successor, but the amount drawn was added up by the old row's name. Now it is added up by the stable identity (plan item and allocation id). A test proves it (and fails with the old counting). A read-only check on the test site's copy of the development data found no allocation drawn beyond its ceiling, so nothing to repair there; run the same check on any site whose plans have had updates activated after requisitions were authorised.
2. A Planning schema test list had not followed an earlier Needs change (`need_estimated_total_cost`), so that test was already failing. Fixed.

## Found, already failing before this work, not changed

1. `test_departmental_needs_architecture` fails two checks (Planning's seed file imports the Needs seed and reads a Needs table). Both lines are in HEAD. It belongs to the seed work.
2. The Makefile target `ui-req-authorised-gate` names a spec, `requisitions-authorised.spec.ts`, that does not exist.
3. Requisitions `test_read` has one failing test, `test_the_procurement_task_leads_with_the_decision_and_its_financial_consequence`. It asserts that the whole site holds no Funding Reservation made by Procurement Requisitions, but the seeded test site carries 18 (the canonical world's own, 16 Active and 2 Partially Converted). The test file is unchanged by this work and the assertion could never pass on a seeded site. It should count only its own reservations.
4. Tenders `test_read` has five failing tests. Three (`test_the_journey_over_the_request_path`, `test_a_returned_draft_reads_as_returned_to_you_at_the_affected_task`, `test_record_read_per_role_and_state`) fail because the test builds a Tender whose submission deadline is earlier than seven days after today's publication date, so the review reports "Must fix: the submission deadline must be at least 7 days after publication" (the tests were written before the real-date anchor made "today" the publication date). One (`test_forbidden_verdict_and_role_queues`) expects exactly one approved requisition awaiting a Tender and finds the canonical world's own as well. One (`test_the_review_shows_digests_only_to_technical_readers_and_auditors`) does not find three digest labels (Evaluation contract, Contract projection, Response schema) in the Auditor's review; I did not establish why. None of these paths is touched by the recovery work; they belong to whoever owns those tests.
5. Planning `planning-publication.spec.ts` has three failing browser tests ("the Planner confirms publication and the plan becomes current…", "Save draft keeps everything typed…", "the recorded publication facts line up…"). In each, the **Confirm plan publication** button is disabled when the spec tries to press it. They fail on the publication form, which this work does not touch; the other tests in the same file and the rest of that run (42 passed, 2 skipped) are unaffected. I did not look for the cause.
6. The Budget design-match gate failed on the Budget line detail because the commitments card built on 16 October was never registered as a departure from the board. I registered it (`tests/ui/fidelity/departures/budget.js`, cited to BUD v1.16 §11.22) and passed it into the check, since the gate is one of the four this change makes due.

## Where the specifications disagree with themselves, and what I did

1. **Who registers the recovery.** The documents say both that Tenders records it and that Requisitions owns it. I made Requisitions own the record and Tenders call it inside the cancellation, because Requisitions must answer for the whole consumed lineage.
2. **A Draft while the recovery is pending.** The text allows preparing a Draft while Pending, but a Draft is limited by the amount that remains, and the whole allowance is held. A purchase whose only remaining allowance is held is not offered to start; a second requisition prepared earlier simply waits for the recovery (a test shows it refused with the Pending message, then authorised after the recovery completes).
3. **No terminal state besides Completed.** A recovery that needs attention keeps its source held until the owner corrects the cause. Nothing releases the hold by hand.
4. **Contract Management is not asked.** It runs without the tendering apps. The exclusion rests on three facts together: Award reports no notice issued or in progress, Award reports no contracting package, and Budget reports no commitment on the reservations.
5. **The old red warning on the cancel screen ("Cancellation is final… it does not restore the Requisition") is replaced by the approved text in section 5.7A.** TPR section 10.13 still carries the old sentence; the design board and the Playwright fidelity spec still show it.
6. **The new "Unused allowance and funding" section has no design board.** It is built from the specification's own wording; a departure from the boards should be recorded for it.
7. **The Planning text says to show the recovery "in U01 and the existing Plan Item detail/history surfaces".** U01 is the planning work queue, and the same text says there is to be no recovery task for anyone, so there is nothing to list there. I built the section on the two screens that describe one purchase (Procurement progress and the Plan Item itself) and nothing on U01. Please say if you meant something else for U01.

## What I added to the requirement documents

PLN v1.32, REQ v1.20 and BUD v1.17 carry your approval record, written at your instruction; each also gained a short "approval effect" entry (the Proposed files had none). That entry is new wording for you to read. TPR v0.21 is still an untracked file of another session; v0.22 carries it in full and is approved.

## Not done yet (listed so nothing is assumed)

Last updated 18 October 2026, when the build was committed.

**Done since the first version of this list:** the development site was migrated, reconciled and recovered (see the evidence map); the seed clear paths now remove a recovery with its holds and release rows (a reseed had been leaving orphan recoveries behind on the test site).

**Built, but not shown by a run**

- Killing the process in the middle of a recovery (only raised errors were used).
- Racing a cancellation against Award issuing a notice with two real connections. The order of locks and Award's re-read under the lock are shown; the race itself is not.
- A recovery for a Budget that has been closed, from Requisitions through to Planning (Budget's own handling of a closed Budget is tested).
- A cancelled failed opening, to see that nothing registers (there is no path that could).
- The Budget line in the Needs attention state, and browser back and forward on the new sections, in a real browser.

**Not built**

- The recovery on Planning's work queue (U01) and on the Requisitions workspace's "Ready to start" line. See the notes above.
- Cancelling after the submission period has closed.
- A design board for the new section.

**Not touched on purpose**

- The document register's implementation, verification and release fields (approval is not evidence).
- The canonical seed, SEED-002 and the Analytics expected values.
- TPR section 10.13 (still carries the old warning).
