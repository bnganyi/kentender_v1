# System check, 18 October 2026 — does it still do what the requirements say, and does it flow?

Done after the cancellation recovery build, at the Project Owner's instruction: "We have done a lot of updates to the documentation and enhancements to the system across all modules … check if the system still fulfills its requirements, flows logically and simply till the end. Fix any issues arising and record those that require my attention later."

This page says what was run, what it showed, what I fixed, and what is left for you. It is written in plain words; test names are given only so a developer can find them. It is a **running record** — the section "Where this stands" at the end says how far the check has got.

## What was run

- Every Python test module, one at a time, on the test site `kentender-test.local` (a copy of the development site), each under the shared lock so nothing overlaps. A module is a test file. The sweep started with the modules that belong to a feature's own acceptance gate, then the guards and cross-module modules, then the rest.
- The browser journeys that walk a feature as the real people through the real menu, for the cancellation recovery (its four screens) and the design-match gates that the recent changes made due.
- Nothing was run on the development site.

## Real defects found and fixed

| What was wrong | What it did | Fix |
|---|---|---|
| Bid Opening's technical record search returned its two routes as text, but the search calls each route as a function | Searching a Bid Opening case or Proceeding reference as a technical user would fail with "'str' object is not callable" | The routes are functions that return the Desk route, like every other module's (commit `0ed72b09`) |
| The rows of an existing-contract commitment entry (Budget) had no write guard although the entry itself does | A direct insert or delete of one of its rows would bypass the Budget commands | The row carries the Budget family like its parent (commit `0ed72b09`) |
| Drawn planning allowance was added up by the allocation's record name | After an Annual Plan update was activated, a purchase that had already been drawn on could be drawn on again up to its full ceiling | Counted by plan item and allocation identity; proved by a test that fails with the old counting (found during the cancellation work, commit `39a56355`) |
| The commitments card on the Budget line was never registered as a departure from the design board | The Budget design-match gate failed on the line detail | Registered with its reason and authority, and the check now passes the registration (cancellation work, `ca31368a`) |

## Stale tests fixed (no product change)

`test_calendar` (the default executed-year stage is now the contracts stage where Contract Management is installed), `test_business_action`, `test_exception_record` and `test_master_data` (a Procuring Entity now needs a reporting currency), `test_portal_runtime` (the portal navigation is spread over several lines, and the CSRF check compared with the wrong mention of the script), `test_whitelisted_principal_parameters` (the staff home unit endpoint names the person whose home unit is set, not the acting person; added to the reviewed list with that reason), and the cancellation recovery integration test (it assumed no other recovery on the site was due). Commit `0ed72b09` and the cancellation commits.

## Decided by the Project Owner, 18 October 2026, and done

1. **Old-era tests: retire them. The eight empty Core scaffold tests: delete them.** Done (commit `46516c37`): nine Python tests for the retired Demands module, the Civic Ledger and Stitch Desk chrome, the first seed packs and the multi-entity migration, plus the four generic workspace browser specs, are removed; the Stitch Desk make target keeps only its browser spec. The eight scaffold files are deleted, so the Strategy tests no longer collide with `_Test Fiscal Year` rows.
2. **`can_configure` stays for technical operators, with full auditability.** Done (`46516c37`): the technical-read conformance test names it beside `can_retry` as a reviewed technical action, and a new test (`TestMaintenanceByATechnicalOperatorIsAudited`) shows a System Manager's creating, renaming and saving a publication rule each write an Audit Event naming that person.
3. **Migrate the development site.** Done: see `CANCELLATION_RECOVERY_EVIDENCE_MAP.md`, "The development site".
4. **The Technical Operator runs the recovery worker by hand** where there is no scheduler.
5. **Commit.** Everything is committed; nothing is pushed.

## Second round of decisions (answered by the Project Owner, 18 October 2026)

These eight things were put to you. Your answers, verbatim: “1. All are approved. Harmonize 2. Approved. Mark them as such 3. Fix them now as part of document hygiene 4. Update the cancellation documents 5. This will be checked in another session 6. Leave it 7. This will be checked in another session 8. This will be checked in another session”. Under each item below, **Answer** says what was done. Items 5, 7 and 8 belong to another session; item 6 is left as it is. Nothing here has been pushed or released.

### 0. Already fixed: seven buttons missing from a checklist (Bid Submission)

Bid Submission keeps a checklist of every button and link a supplier can see, with the action each one performs. Seven links the supplier screens show were missing from it: the "previous" and "next" links between the bid's tasks (Tender documents, Company and declarations, Requirements), the "Review" button on a finished task, "Hand over bid", "View complete bid", and "New supplier? Create a login". None of them changes anything; they only open another page. A test checks that nothing is missing from the checklist, and it was failing for these seven. I added all seven, each with the page it opens. Nothing for you to decide.

### 1. Which of these three documents did you approve?

The master list of documents (the "register") and the documents themselves disagree about whether three of them are approved. I cannot tell which is right; only you know.

| Document | The register says | The document itself says |
|---|---|---|
| Installed STD Template Runtime v1.1 | Approved | Proposed; v1.0 "was proposed on 25 September 2026 and never approved" |
| Statutory Correction Register v1.2 (the 30% reservation correction) | Approved | "Proposed for approval" |
| Roadmap Coverage Assessment v1.3 | Approved | Carries no approval |

Three older documents (the Planning journey reference, SEED-001 and SEED-OPS-001) are labelled "historical" in the register while their own files say "Approved". That is only a difference in labelling; I would leave it.

**Why it matters:** the register is what everyone reads to know what is in force.
**What I need:** for each document, "approved" or "not approved". I will then correct whichever side is wrong, through the normal document change steps. If you do not remember approving it, the safe answer is "not approved".

**Answer: “All are approved. Harmonize.” Done in the working tree and the register.**
- **Installed STD Template Runtime v1.1** and **Statutory Correction Register v1.2** now say in their own headers that they are approved, on the dates the register already recorded (26 September and 23 September 2026). Nothing was written about how or in what words they were approved, because I do not have those words; the headers say so plainly and quote your 18 October answer as the reason they were brought into line.
- **Roadmap Coverage Assessment v1.3 needed nothing, and I was wrong to list it.** Its file says “Approved — 3 October 2026”. The document checker could not read that header, and I took the checker's silence for an absence. The register was right.

### 2. Seven newer document versions are waiting for your approval

These files exist and are marked "Proposed": Strategy v1.11, Seed runbook v1.25, Procurement Proceedings v0.13, Bid Evaluation v0.9, Award v0.8, Contract Management v0.12 and the Gate 1 handoff v1.2. The register correctly still lists the older approved versions. Some code has already been built to the newer text.
**Why it matters:** until you approve them, the built behaviour and the approved text can differ.
**What I need:** nothing from me. This is your approval queue; I am telling you it is seven items long.

**Answer: “Approved. Mark them as such.” Done.** Each of the seven files now carries the approval, dated 18 October 2026 and quoting your words, and the register lists each as the current version. Approval is not evidence of code, tests or release, so no implementation, verification or release field was changed. Four things you should know:
- **Gate 1 handoff:** v1.1 was already approved on 1 October 2026 (the register said so). v1.2 now replaces it. Some sentences in the v1.2 body still read as if it were waiting for approval; they are left as written.
- **Seed runbook v1.25:** the register still labels the runbook “Historical provenance” because the seed specification retired it as a live rule document on 8 October. I changed only its version and approval date. If you want it back as a live document, say so.
- **Strategy v1.11, section 18.6:** it lists defaults that were proposed for your confirmation. Your blanket approval settles them as taken; tell me if you meant to look at any of them separately.
- **Several approved bodies still contain sentences written while they were waiting**, such as “proposed for approval”. I did not rewrite them. They are history, and rewriting them is a separate, optional tidy-up.

### 3. Mistakes inside the four cancellation documents you approved

The four documents (Planning v1.32, Requisitions v1.20, Budget v1.17, Tenders v0.22) were already like this when you approved them; I only added the approval records. The mistakes are editorial, and the software is right:
- Each document names error messages (for example "cancellation recovery is pending") in its text but does not list them in its own table of error messages. The software defines the six recovery messages. Planning has two of these, Requisitions two, Budget two. The seventh, Tenders' "too late to cancel" message, is named in the Tenders text but is not in the software at all (the build does not yet allow cancelling after the submission period closes).
- Budget v1.17 gives the same identifier (BUD24-XD-002) to two different rows.
- Planning v1.32 has one table row with six cells under a seven-cell heading.
**Why it matters:** very little today. The document checker keeps flagging them, and a developer reading only the tables of messages would miss seven messages that exist.
**What I recommend:** do not create four new versions just for this. Fix them when each document next changes for a real reason, so you approve each only once.
**What I need:** "bundle them" (my recommendation) or "fix them now". If now, I prepare four small correction versions for you to approve.

**Answer: “Fix them now as part of document hygiene.” Four correction versions are written and wait for your approval (Proposed, not approved):**
- **Planning v1.33** adds the two recovery messages to its table and puts the six-cell row into its seven columns.
- **Requisitions v1.21** adds its two recovery messages.
- **Budget v1.18** adds its two recovery messages and relabels the second BUD24-XD-002 row as a status line.
- **Tenders v0.23** adds the “too late to cancel” message to its table.

Each is a patch of the approved version with nothing removed. Two things for you to read: the **wording of the Tenders “too late to cancel” message is new**, taken from nowhere in the approved text (the software does not have the message either); and Planning has two older wrong cross-references (“§8.3”) in the text that I left because they are not part of what you asked.

### 4. The register still says most work is "not evidenced"

For each document the register records whether the work is built, tested and released. For most modules it still says "Not evidenced" or "Planned" (as of 15 October, for example Planning "Not implemented", Requisitions "Not evidenced", Tenders "Planned"), although the code exists and thousands of tests pass. The register's own rule says approval must never count as evidence, which is right; but nothing has updated those fields as real evidence arrived.
**Why it matters:** anyone reading the register would think the system is far less built than it is.
**Options:** (A) leave it. (B) I update only the four cancellation documents now, using the evidence map I wrote, which shows 9 of 12 acceptance rows done and 3 partly done, with the test that proves each. (C) Update every module; that needs each module's evidence collected first, roughly a day or more of work.
**What I recommend:** B now, C as a separate piece of work later.
**What I need:** A, B or C.

**Answer: “Update the cancellation documents.” Done (option B), in the register.** For Planning, Requisitions, Budget and Tenders the register now says implementation “In progress” and verification “Pending”, with a pointer to the evidence map and its limits (9 of 12 rows shown, 3 only partly: a killed process, a race with an Award notice, and a closed year). I did not write “Implemented” or “Passed”, because three rows are only partly shown and your rule is that approval is not evidence. The four correction versions above are listed beside each entry as proposals awaiting approval.

### 5. The "walk through the menu as each person" tests fail on the current demo data

These browser tests log in as real people (Charles, Amina, the supplier, and so on) and click through from the menu, as a user would, for Home, Award, Bid Opening and Contracts. They were written for the older demo world and fail now. Some failures are stale details (a tender number that changed from 2027 to 2026, an old notification button, a hard-coded date, a count that is now 11 where the test says 9). One could be real: on the Bid Opening walk, the tender page shows no link to Bid Opening for the demo tender, and I have not found out why.
**Why it matters:** these are the only automated checks that a person can really get from the menu to the end of the job. Until they pass, the question "does it flow, start to finish" is answered by hand.
**What I recommend:** I bring them up to date one module at a time, starting with Award and Bid Opening (the Award walk already passes its first two steps), and I will tell you of any failure that turns out to be a real fault rather than a stale test.
**What I need:** a yes. It will take several hours.

**Answer: “This will be checked in another session.”** Not touched here.

### 6. The development site's demo-data check now reports one problem

The demo data is built around one moment in time (the "anchor", 16 October 10:00). A check confirms that nothing in it is dated after that moment. When the recovery ran for the two cancelled demo tenders on 18 October, it recorded two Budget events dated 18 October, so the check now reports exactly that and nothing else. Any real use of the demo data does the same.
**Why it matters:** it is cosmetic for you, but it will show up whenever someone runs that check on the development site.
**Options:** (A) leave it until the next planned reseed, which sets a new anchor. (B) Reseed the development site now; that removes everything on the site that is not demo data.
**What I recommend:** A.
**What I need:** a yes to A, or tell me to reseed.

**Answer: “Leave it.”** Left as it is; the development site's demo-data check will keep reporting that one line until the next reseed.

### 7. Not all the Python tests were run

I ran 259 of 564 test files, including every file that belongs to a feature's own acceptance set. The other 305 (mostly Procurement and Contract Management) are not run. They take several hours because each builds a full tender-to-award world.
**Why it matters:** problems in the unrun files would not have been seen.
**What I recommend:** I run them in one long session and report only the failures, sorted into real faults, stale tests and site clutter, as I did for the first 259.
**What I need:** a yes, and an idea of when the test site can be mine for several hours.

**Answer: “This will be checked in another session.”** Not touched here. The 305 unrun files are still unrun.

### 8. Two small old problems I did not cause

- One check fails because Planning's demo-data file reaches into the Needs demo-data file, which the rules forbid (2 checks in the Needs architecture test). The fix is to move what they share into a neutral place; it is a few lines but touches both modules' demo data.
- One make target (`ui-req-authorised-gate`) names a browser test file that does not exist.
**What I recommend:** let me fix both; they are small.
**What I need:** a yes.

**Answer: “This will be checked in another session.”** Not touched here.

## Old-era tests, now retired

These tested things the system no longer has; the Project Owner said to retire them. They are removed in commit `46516c37` (their history stays in git and in the older trackers).

| Test module | What it expected |
|---|---|
| `test_dem_seed_004_orchestrator_demands`, `test_stable_platform_seed` | The retired Demands module |
| `test_module_registry` | Demand routes in the module registry |
| `test_kt_cl_shell_layout_guard`, `test_stitch_desk_chrome_gate` | The retired Civic Ledger and Stitch Desk chrome |
| `test_seed_v1`, `test_reference_data_seed_mvp1`, `test_kentender_mvp_v1_seed_contract` | The first seed packs |
| `test_backfill_pe_fy_context_links` | The multi-entity era |
| `workspace-clickability`, `-discoverability`, `-navigation`, `-shell` (browser) | Selectors that never worked (`data-id="[object Object]"`, an empty text pattern) |

`test_departmental_needs_architecture` (2 checks, Planning's seed file importing the Needs seed) is not retired: it guards a real rule and was already failing.

## Where this stands

This is the detail behind the decisions above. You can skip it unless you want the evidence.

**How far it got.** I stopped the Python sweep at 259 of 564 test modules (about 2,750 tests): all 47 modules that belong to a feature's own acceptance gate, all of Core, Strategy, Budget and Suppliers, ten of Contract Management, and 72 of Procurement (Bid Opening, Bid Evaluation, Award, Planning, Tenders and Needs gates and guards). I did not run the other 305, mostly the less cross-module ones in Procurement, Contract Management and Home. The sweep only moves while I am actively working, and the heavy modules take 4 to 14 minutes each, so I chose to spend the time on rerunning failures cleanly and on the browser journeys instead. Run `make` targets or the module list in the scratch folder to finish it.

**What the sweep showed, module by module (34 failing of 259).**

| Group | Modules | What it was |
|---|---|---|
| Fixed in this check, now passing | 10 | Stale test expectations (and, for the Budget and Bid Opening items above, the real defects): `test_calendar`, `test_business_action`, `test_exception_record`, `test_master_data`, `test_typed_attachment`, `test_workflow_guard`, `test_portal_runtime`, `test_whitelisted_principal_parameters`, `test_command_write_coverage`, `test_departmental_needs_lifecycle` (a disposable fiscal year had no Budget currency, and the closed year was missing from the expected list) |
| Caused by the test site's own pollution, pass on a clean site | 12 | The 9 Strategy modules, `test_canonical_seed` (42 of 42 on a clean world), `test_dead_end_matrix` (Planning) and `test_evl_canonical_seed` |
| Real, left for you | 1 | `test_departmental_needs_architecture` (2 checks: Planning's seed file imports the Needs seed and reads a Needs table; already failing before this work; decision 8). `test_technical_read_conformance` passes since the owner's decision on `can_configure`, and `test_acceptance_gaps` in Bid Submission passes 27 of 27 since the seven missing entries were added (decision 0) |
| Old-era, retired by the owner's decision | 9 | Listed in the previous section |

**Test hygiene (the rule is "always remove test data").** The sweep left the shared test site unfit to validate its own canonical world. Causes found and what I did:
- Budget test classes removed their records but did not commit the removal, so each run left budgets, organisation units, users and fiscal years behind (28 budgets, 99 users, 15 units and 12 fiscal years had piled up). Fixed in the shared base class (commit `b174e984`); the module I measured now leaves nothing.
- Eight scaffold test files under Core's `doctype/` folders contained no tests but, when run, loaded ERPNext's test records and created 14 `_Test Fiscal Year` rows, which collided with the fiscal years the Strategy tests use. Deleted on the owner's instruction.
- Frappe's runner creates nine `…@example.com` test users. They are harmless to tests but make the canonical validation fail until removed.
- Planning's test world leaves `plnt.*` users and units (known, see the older note on it).
- Cancellation recoveries were left behind when a seed or fixture reset removed their Tender or Requisition (5 orphan rows on the test site, picked up by the recovery sweep with nothing to verify). The seed clear paths now remove a recovery with its holds and release rows, a test pins it, and the orphans are cleared.
After each cleaning (the seed's own `clear_non_canonical`, then setting the test clock) the canonical world validates again on the test site.

**Browser journeys** (test site, one spec group at a time, each after a clean-up):

| Journey | Result |
|---|---|
| Cancellation recovery, four screens | 2 of 2, no console errors |
| Design-match gates the changes made due | Tenders 18 of 18, Requisitions 5 of 5, Budget 12 of 12, Planning 42 passed, 3 failed on the publication form (see the other list) |
| Home, every persona | 6 passed, 4 failed, 30 did not run (the file runs in order and stops at the first failure). The failures are expectations of the old world: Charles has 11 actions where the spec says 9, and his fifth row opens a clarification where the spec expects the opening. I did not look for a product cause |
| Award, from the menu, the bell and the portal | After two stale-spec fixes below: the Head of Procurement signs the opinion from the menu, and the Accounting Officer awards from the bell, both pass. The supplier step then fails on a date the spec hard-codes for the old world (it expects 29 Oct 2026, the page says 22 Oct 2026), so the last step did not run |
| Bid Opening, from the menu | The first step fails: from the Tender page there is no link to Bid Opening for the profile the spec builds, and the rest did not run. I did not establish why |
| Contracts: canonical list and shell | 2 of 4: the contracts board still read "loading" after five seconds, and a clean-up call to the server timed out |

Two stale-spec fixes made while doing this (commit below): the canonical Tender, Award and Requisition are now numbered 2026 (the real-date world renamed them from 2027) in six specs, and the Award and Bid Opening walks used Desk's old notification bell where Home's "Notification" control is now the way in.

**What is left from the journeys:** see decision 5 above.
