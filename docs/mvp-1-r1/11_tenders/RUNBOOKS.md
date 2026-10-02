# Tenders (TPR-CHG-001 v0.12) — operational runbooks

Procedures for running, verifying and recovering the Tenders module on
`kentender.midas.com`, and for supporting it in production. Plain English;
command blocks are exact. Written for v0.8 on 19 Sep 2026 and updated for
v0.12 on 26 Sep 2026 (sections 9 and 10 are new; sections 1, 2, 5 and 8
changed). Sections 11 to 13 were added for the proposed v0.16 on 2 Oct 2026.

## 1. Running the module's gates

Focused Python (one module at a time, from `/home/midasuser/frappe-bench`):

```bash
bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tenders.tests.<module>
```

Every service test module in one run (from `apps/kentender_v1`):

```bash
make tenders-schema-gate SITE=kentender.midas.com      # schema, envelope, authorization, gateway contracts
make tenders-services-gate SITE=kentender.midas.com    # every Tenders service test module (includes the two below)
make tenders-dead-end-gate SITE=kentender.midas.com    # every Tender state x reader has a next step; writes evidence/v0_12/dead_end_matrix.md
```

Each of these refuses to start while a Playwright run is active
(`make tenders-preflight`). Since 26 Sep 2026 the Tenders and
Requisitions test wipes remove only test-world rows (fiscal years starting
in 2100 or later), so a Python run no longer deletes the canonical Tender
or Requisition; a Python run still writes for real (there is no rollback),
so reseed the canonical site afterwards (§2).

Component tests (from `apps/kentender_v1`):

```bash
npx vitest run --project tenders
```

One UI slice (vitest + that slice's Playwright spec, on the Tenders
Playwright world, then `restore_site`):

```bash
make ui-tenders-workspace-gate SITE=kentender.midas.com      # workspace + common states
make ui-tenders-start-gate SITE=kentender.midas.com
make ui-tenders-details-gate SITE=kentender.midas.com
make ui-tenders-requirements-gate SITE=kentender.midas.com
make ui-tenders-review-gate SITE=kentender.midas.com
make ui-tenders-approval-gate SITE=kentender.midas.com       # HOPF approval + Requisition correction states
make ui-tenders-authorisation-gate SITE=kentender.midas.com
make ui-tenders-publication-gate SITE=kentender.midas.com
make ui-tenders-published-gate SITE=kentender.midas.com
make ui-tenders-addendum-gate SITE=kentender.midas.com       # addendum + supplier clarification
make ui-tenders-cancel-gate SITE=kentender.midas.com
make ui-tenders-history-gate SITE=kentender.midas.com
```

Every board's design fidelity in one run:

```bash
make ui-tenders-fidelity-gate SITE=kentender.midas.com
```

Everything (vitest + every Tenders Playwright spec, including the
evidence pack and the persona pass, + fidelity):

```bash
make ui-tenders-release-evidence-gate SITE=kentender.midas.com
```

Before any UI run that fails oddly (teardown errors, a later spec failing
against state an earlier one left behind, a `NameError` naming an app),
check the background job queue first — it is almost always the real cause:

```bash
make ui-queue-check
```

Never run the Python test suite and a Tenders/Requisitions Playwright run
at the same time: both move the same site-wide DPP intake flag, and the
Requisitions Playwright world the Tenders world extends carries the same
restriction.

## 2. Reseeding the canonical site through Tenders

The canonical world is the one the live dev site shows by default —
Ministry of Health, Fiscal Year 2027-2028, one Tender at "Submission
period ended" with an issued, confirmed addendum and one supplier
clarification answered to all registered candidates (v0.8 read: "one
answered inquiry").

```bash
cd /home/midasuser/frappe-bench && bench --site kentender.midas.com execute kentender_core.seeds.canonical.dry_run   # see what would be removed; deletes nothing
make seed-canonical SITE=kentender.midas.com THROUGH=tenders                # clear non-canonical rows, reseed through Tenders, validate
make seed-canonical-validate SITE=kentender.midas.com THROUGH=tenders       # validate only
```

`make seed-canonical` without `THROUGH=` stops at `requisitions` by
default (unchanged, so other modules' own gates are not affected); pass
`THROUGH=tenders` explicitly for the full chain including the canonical
Tender.

The clear step removes every Tender that is not on the canonical
Requisition, with its child-table rows, command-journal entries and
attached files, so a Tender left by an interrupted browser run does not
survive a reseed (SEED-OPS-001 v1.10 §3.1; before 26 Sep 2026 nothing in
the clear looked at Tenders).

**If it refuses with `REQ_PLAN_INELIGIBLE`** ("This Plan Item is not
currently eligible"): a Requisition was dropped earlier (a Tender
Playwright/test run, a manual delete) without releasing its Planning
drawdown, so the combined item still reads as fully drawn down with no
Requisition to show for it. Repair, then reseed:

```bash
cd /home/midasuser/frappe-bench && bench --site kentender.midas.com execute kentender_procurement.procurement_requisitions.seeds.kentender_mvp_v1.recover_orphaned_drawdowns --kwargs '{"commit": True}'
```

**To rebuild the canonical Tender from scratch** (its own rows are wrong,
not merely missing): `rebuild=True` resets Tenders before Requisitions
(it holds the handoff), then reseeds. The make target exposes it:

```bash
make seed-canonical SITE=kentender.midas.com THROUGH=tenders REBUILD=True
```

or, from `bench execute`:

```bash
cd /home/midasuser/frappe-bench && bench --site kentender.midas.com execute kentender_core.seeds.canonical.run --kwargs '{"through": "tenders", "rebuild": True}'
```

**If a reseed fails with a `NameError` naming an app** after the first
run of the day removed many leftover test rows: deleting users and audit
rows queues background jobs, and a large clean-up can fill the queue past
Frappe's limit of 500 so the next run is refused part-way (26 Sep 2026:
523 jobs after removing 44 users and 688 budget audit rows). Drain the
queue and run the reseed again:

```bash
make ui-queue-check FIX=1
```

A rerun of any of the above is idempotent: `removed={}` and every
module's own `idempotent: true` on a second call with nothing changed in
between.

## 3. The hourly submission-close scheduler job

`kentender_procurement.tenders.services.submission_close.close_due_submission_periods`
runs on Frappe's `hourly` schedule (`hooks.py`). It closes every Tender at
"Published — open" whose submission deadline has passed, one Tender per
transaction, and writes one immutable Tender Submission Handoff per
closure. It never runs as a business user — only Administrator or a
technical account.

**To force-close a specific Tender now** (dev/testing; the real command
the scheduler itself calls, `force=True` bypasses the deadline check):

```bash
cd /home/midasuser/frappe-bench && bench --site kentender.midas.com execute kentender_procurement.tenders.services.submission_close.close_tender_submission_period --kwargs '{"tender": "TDR-00001", "idempotency_key": "manual-close-1", "user": "Administrator", "force": True}'
```

**To run the same sweep the scheduler runs**, on demand:

```bash
cd /home/midasuser/frappe-bench && bench --site kentender.midas.com execute kentender_procurement.tenders.services.submission_close.close_due_submission_periods
```

A Tender already at "Submission period ended" replays the existing
handoff (`idempotent: true`) rather than closing twice.

## 4. Recovering from an interrupted or stuck Playwright run

Every Tenders Playwright spec (`tests/ui/smoke/tenders/*.spec.ts`) resets
its own fixture at the start of each test and restores the world in
`afterAll`. If a run was killed mid-test (Ctrl-C, a crashed browser, a CI
timeout), the Tenders Playwright world (and the Requisitions world it
extends) can be left mid-lifecycle. Recover with:

```bash
cd /home/midasuser/frappe-bench && bench --site kentender.midas.com execute kentender_procurement.tenders.seeds.playwright_ui_fixtures.restore_site
```

This wipes every Tender the Playwright actors (`pw.tnd.*`) own, then
delegates to Requisitions' own `restore_site()`, which does the same for
`pw.req.*` and puts the site's DPP intake flag back on whichever fiscal
year it was open on before the Playwright world moved it.

If a subsequent run still behaves oddly (a `NameError` naming an app, a
teardown error, a later spec failing against leftover state), check the
background job queue before reading any application code — `bench
execute` masks a real exception as `NameError` when the queue is
overloaded and a worker never drained it:

```bash
make ui-queue-check
```

After recovery, reseed the canonical site (§2) before resuming any
non-Tenders work, since a Tenders Playwright run never touches the
canonical Tender itself but can leave the shared Requisitions/Planning
world in its own Playwright-year state.

## 5. Production support: a channel confirmation was rejected for evidence

**Symptom:** a Head of Procurement Function reports "The selected file
cannot be used as publication evidence. Choose an allowed document or
image file." (`TND_PUBLICATION_EVIDENCE_INVALID`) when confirming a
publication or addendum channel. Since v0.12 the page also marks
**Confirm publication** as blocked on the Tender's journey and offers
**Choose evidence file** and **Confirm publication** as the next step.

**Why:** `kentender_core.services.file_integrity.check_file` rejects the
upload before the confirmation is recorded — either the file extension is
not on the allowed list for evidence (PDF, PNG, JPEG), or the antivirus
scan the file went through on upload came back infected/unclear. Nothing
is written: the channel stays "Awaiting confirmation" and the HoPF's
original evidence file, reference and notes are preserved in the dialog
so they never have to re-type them.

**What to check:**
1. Confirm the file's real type matches an allowed extension — a renamed
   `.docx` saved as `.pdf` still fails the content check, not just the
   extension.
2. Check `frappe.get_doc("File", <name>).is_private` and the site's
   antivirus/scan log if one is configured; a scan result other than
   "clean" is what the message is naming.
3. Ask the HoPF to re-attach a genuine PDF or image of the same evidence
   (a phone photo of the notice board is normal and accepted).

There is no override: this module never lets a channel confirm without a
passing evidence check, on any responsibility.

## 6. Production support: a conflicting or duplicate confirmation

**Symptom:** a HoPF reports "This channel is already confirmed" when they
try to confirm a channel, or two people submitted the same channel's
confirmation within moments of each other and one sees this instead of
success.

**Why:** confirmation is idempotent by design (§7.3 item 10): a repeat
submission with the *same* facts (available date/time, reference, URL,
evidence digest) silently returns the existing confirmation rather than
erroring, but a second submission with *different* facts for an
already-Confirmed channel is refused and the original confirmation is
preserved untouched — never silently overwritten, never merged.

**What to check:**
1. Open the channel's own "View confirmation" to see who confirmed it,
   when, and with what evidence — that is the authoritative record.
2. If the existing confirmation is wrong (wrong date, wrong file), there
   is no in-place correction: the only path is `withdraw_publication_authorisation`
   (only possible before *any* channel is confirmed) followed by
   re-authorising, or — once published — treating the wrong record as
   what it is and noting the discrepancy in the Tender's history for
   audit; this module does not retouch a Confirmed record.
3. Two people racing to confirm the same channel is expected and safe:
   whoever's request reaches the server first wins, the second gets this
   message, and no duplicate row is ever created (unique on subject +
   channel).

## 7. Production support: a failed confirmation transaction

**Symptom:** a HoPF reports the page showed an error while confirming a
channel, and the channel now looks stuck — but re-opening the dialog
lets them try again with the same file already usable (no "file already
used" error).

**Why:** every confirmation command runs inside one atomic transaction
(`envelope.atomic`): the confirmation row, the Tender's own state, the
outbox event and the command journal entry are written together or not
at all. A failure partway through (a database error, a timeout) rolls
the whole transaction back — the channel stays exactly where it was
before the attempt, and the uploaded evidence File row (created outside
the transaction, since Frappe's own upload is a separate request) is
still valid and reusable on the very next attempt rather than orphaned.

**What to check:**
1. `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tenders.tests.test_publication` —
   `test_a_failed_confirmation_transaction_leaves_no_confirmed_state_and_the_upload_reusable`
   is the exact regression test for this scenario; a failure there means
   the transaction boundary itself has broken.
2. Check `bench --site kentender.midas.com` logs
   (`/home/midasuser/frappe-bench/logs/`) around the reported time for the
   underlying database/infrastructure error — this module's own code has
   nothing further to add once the transaction has rolled back cleanly.
3. Ask the HoPF to simply retry the same confirmation; the same
   idempotency key is not required since nothing was recorded the first
   time.

## 8. Production support: an overdue cancellation obligation

**Symptom:** a cancelled Tender's compliance obligations (the PPRA
report, the candidate notice, or an original publication channel's own
notice obligation) show "Overdue" instead of "Outstanding" or "Recorded".

**Why:** every obligation carries a due date computed from the
cancellation decision date and the configured due rule (Immediate, or a
fixed number of days) at the moment of cancellation — `refresh_obligation_statuses`
recomputes each obligation's status (`Due` / `Recorded` / `Overdue`)
against the real clock every time the cancellation record is read, never
storing a stale status. "Overdue" means the due date has passed with no
compliance evidence recorded against that obligation yet.

**What to check:**
1. The obligation's own row shows exactly what is owed and by when. Since
   v0.12 the cancellation hands the evidence work to the Procurement
   Officer who prepared the approved Version (a "Record cancellation
   compliance evidence" item in their My Work), with the Accounting
   Officer shown as waiting on it. The notice channels may be evidenced by
   that Procurement Officer or by the Head of Procurement Function, each
   with their own attestation (FOLLOW_UPS FU-30); the PPRA report is
   recorded by the same holder; the candidate-notice obligation is
   recorded automatically once every candidate notice for the
   cancellation shows Delivered (v0.8 read: "Head of Procurement Function
   for the notice channels, Accounting Officer for the PPRA report and
   candidate notice").
2. This module never escalates or notifies on an overdue obligation
   itself (no consumer exists for that outbox event in this release —
   see FOLLOW_UPS FU-13); a support engineer's role here is confirming
   the obligation is genuinely outstanding (not a display bug) and
   routing the finding to the accountable actor, not clearing it in the
   system.
3. The only way an obligation leaves "Overdue" is the accountable actor
   recording real compliance evidence through `record_cancellation_compliance_evidence`
   (the Cancel Tender screen's **Record cancellation notice evidence** or
   **Record PPRA report evidence** action; v0.8 read: "Record evidence") — there is
   no administrative override to mark it Recorded without evidence, and
   Cancellation itself is final and can never be reversed to "undo" the
   obligation instead.

## 9. Production support: a candidate notice failed delivery

**Symptom:** a Procurement Officer or Head of Procurement Function sees
"1 candidate notice failed delivery; the Tender remains open." on a
supplier clarification (or on an addendum or cancellation), with a
**Retry notice** fix, and the delivery table shows the notice as Failed.

**Why:** every notice-bearing decision (a clarification answer sent to
candidates, an addendum becoming effective, a deadline change, a
cancellation) freezes its audience and content in the same transaction
as the decision, then sends one notice per registered candidate outside
it. A failed attempt is recorded as evidence and changes nothing else:
the answer stays sent, the addendum stays effective, the deadline and the
cancellation stand. Queued, Sent, Delivered and Failed stay distinct —
Sent means a provider accepted the message, not that the candidate
received it.

**What to check:**
1. Open the notice from the Tender's clarification, addendum or
   cancellation screen. The attempts table lists every attempt with its
   time, result and failure reason. Procurement, audit and technical
   readers also see the protected recipient; other readers do not.
2. Fix the cause outside Tenders. The destination is a snapshot taken
   from the Bid Submission candidate registration when the decision was
   made; Tenders cannot edit it. A wrong address is corrected in the
   registration and only affects later notices.
3. Use **Retry notice**. It resends the same notice to the same recipient
   with the same content and adds one attempt; it never creates a new
   notice, changes the audience or touches the Tender. Only a Failed
   notice can be retried.
4. Queued notices are sent by the every-few-minutes scheduler sweep
   (`candidate_notices.dispatch_pending`, Frappe's `all` schedule). To
   send them now:

```bash
cd /home/midasuser/frappe-bench && bench --site kentender.midas.com execute kentender_procurement.tenders.services.candidate_notices.dispatch_pending
```

**On the dev site** no outgoing email account is configured, so every
notice sent through the default email transport fails and a retry fails
again with the next attempt number. That is correct behaviour, not a
defect; the canonical seed and the tests use their own transports, which
supply the provider evidence for Delivered and Failed. The default email
transport can only ever record Sent: production needs a delivery provider
registered on the `kt_candidate_notice_transports` hook before any notice
can show Delivered (FOLLOW_UPS FU-35).

## 10. Production support: a material addendum and its cancellation review

**Symptom:** a Head of Procurement Function or Procurement Officer saved
an addendum that changes something an addendum may not change (for
example it increases a quantity, the value or the scope). The page says
"… cannot be issued as an addendum." and offers **Ask the Accounting
Officer to consider cancellation** and **Discard addendum draft**; there
is no Issue action.

**Why:** a material change cannot reach suppliers through an addendum;
the only lawful routes are to drop the proposal or to cancel the Tender
and start a newly governed one. The system never issues it, and the
published Tender is unchanged throughout.

**The procedure:**
1. The sender asks for the review with a reason of 20–1,000 characters.
   The Accounting Officer gets one "Consider cancellation of {Tender}"
   item in My Work; the sender sees a waiting line naming the Accounting
   Officer.
   A second request for the same proposal returns the first one.
2. While the review is open the proposal cannot be discarded; the page
   says to wait for the decision.
3. The Accounting Officer opens the item (it lands on Cancel Tender, with
   who asked and the proposed change) and either:
   - chooses **Cancel Tender**, which opens the normal cancellation
     decision (ground and reason) and, on commit, closes the review item;
     or
   - chooses **Close cancellation review** with a reason of 10–1,000
     characters. The Tender stays open, the proposal stays blocked, and
     the sender's page now shows the Accounting Officer's recorded reason
     with **Discard addendum draft** as the only step.
4. A closed review cannot be asked for again for the same proposal; the
   sender discards it. Discarding never affects an issued addendum or one
   awaiting channel confirmation.

**What to check if it looks stuck:** the Tender's History lists each
request, close and discard as a decision with its actor, time and reason;
an open "Consider cancellation of …" item in the Accounting Officer's My Work
means the review is still theirs. There is no administrative override
that issues a material addendum.

## 11. Setting and checking the submission-period numbers

**What it is:** every Open Tender has two numbers for the time between
publication and the submission deadline, held in System setup under the
Open Tender schedule's **Bid opening** interval. The **minimum** (7 days
since 2 Oct 2026; PPADA s.97(1) and PPADR 2020 reg. 86) blocks: a deadline
closer than that cannot be submitted, approved or authorised. The **usual
period** (21 days) never blocks: a shorter deadline needs a stated reason
that the Head of Procurement Function and Accounting Officer then see. The
form hints both numbers and pre-fills the deadline from the issue date.
The 7 comes from the Project Owner's research and is not yet confirmed by
counsel (FU-37); the schedule's verification status stays "Fixture-verified —
not production law".

**To read them on a site:**
```bash
cd /home/midasuser/frappe-bench
bench --site kentender.midas.com mariadb -e "select p.profile_reference, m.minimum_days, m.default_days, m.basis, m.statutory_reference from \`tabSchedule Profile Milestone\` m join \`tabProcedure Schedule Profile\` p on p.name=m.parent where m.milestone='bid_opening' and p.procurement_method='Open Tender' order by 1"
```
Expect minimum 7, default 21 and basis Planning assumption on the Goods,
Services and Works rows.

**A site seeded before 2 Oct 2026 shows minimum blank:** Tenders then
treats the schedule as having no verified minimum and blocks nothing. Run
the patch (it never overwrites a minimum an administrator entered):
```bash
bench --site <site> execute kentender_core.patches.v1_28.open_tender_preparation_minimum.execute
bench --site <site> clear-cache
```
**To change a number:** use System setup, Procurement schedules, create a
new version of the Open Tender schedule. Do not edit the database. Changing
the usual period never changes what blocks.

**If an officer asks why a deadline was refused:** a message reading "at
least 7 days after publication (the legal minimum)" means the minimum;
"State why the tendering period is N days, shorter than the usual 21" asks
for the reason and is not a refusal.

## 12. Production support: the Accounting Officer returned an approved Tender

**Symptom:** an Approved Tender shows, to the Accounting Officer, "Waiting
on … must reopen this Tender after … returned it", with no Authorise and no
Return action; the Head of Procurement Function has an item "Review Tender
… returned by the Accounting Officer".

**Why:** the Accounting Officer chose **Return to Head of Procurement
Function** with a reason. The approved Version is kept, nothing is
published, and the decision is in History with its reason.

**The procedure:**
1. The Head of Procurement Function opens the item (it lands on the Tender,
   which shows the reason) and chooses **Reopen for correction**. A copied
   Draft is created and the Procurement Officer gets "Correct reopened
   Tender …".
2. The officer corrects and resubmits; the Head of Procurement Function
   approves; the Accounting Officer gets a fresh authorisation task.
3. Reopening, or a Requisition correction request, clears the return item
   and the Accounting Officer's waiting line.

**What to check if it looks stuck:** the Head of Procurement Function's My
Work lists the item until the Tender is reopened. There is no way for the
Accounting Officer to withdraw a return; only the Head of Procurement
Function's Reopen clears it (FU-39 asks whether the Draft should appear at
the moment of return).

## 13. Production support: an approved Tender whose deadline is below the legal minimum

**Symptom:** an Approved Tender shows the Accounting Officer "Your turn,
blocked" with the deadline, the days it allows, the legal minimum and the
earliest allowed deadline; **Authorise publication** is absent. The Head of
Procurement Function's My Work lists "Reopen Tender … — submission deadline
too short".

**Why:** time passed after approval, or the Tender was approved before the
minimum was recorded, and the deadline no longer leaves the minimum after
the earliest publication (the later of the issue date and today). The
Officer's review and the Head of Procurement Function's approval stop this
for a new submission; this case is the drift after approval.

**The procedure:** either the Accounting Officer chooses **Return to Head
of Procurement Function** (section 12), or the Head of Procurement Function
chooses **Reopen for correction**. The officer then moves the deadline on
the Tender details page, resubmits, and the Head of Procurement Function
approves again. Nothing is overridden: authorisation and publication
confirmation recheck the minimum on the day.

**What to check:** the item clears by itself once the Tender is reopened or
authorised. If it never appears for a Tender that is blocked, check section
11 first: a blank minimum means nothing is checked.
