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

## Needs your attention

1. **Technical readers and "can configure".** The conformance test says a technical reader (System Manager) must get view-only access on every read. The Tender publication read gives them `can_configure` = true, which is what shows the "configure the publication rule" link in the "Publication not configured" state. Either the rule is relaxed for this link (it opens System setup, where they act under setup's own authority) or the link is removed for technical readers. I did not change it. Test: `test_technical_read_conformance`.
2. **Bid Submission's action register is behind its screens.** Seven actions the reads now show have no entry in the register: Company and declarations, Hand over bid, New supplier? Create a login, Requirements, Review, Tender documents, View complete bid. Test: `test_acceptance_gaps` (one failure of 27). It needs someone who knows which command each maps to.
3. **Old-era tests that can no longer pass** (listed in the next section). Each tests a concept that has since been retired. My recommendation is to retire them rather than patch them; that is your call because it deletes tests.
4. **The document register still says most implementation is "Not evidenced" or "Planned"**, though the code exists and many modules have passing tests (register as of 15 October: for example Planning "Not implemented", Requisitions "Not evidenced", Tenders "Planned"). The register's own rule forbids using approval as evidence, which is right, but nothing has moved those fields as evidence arrived. The cancellation recovery now has an acceptance map you can use as the model for moving them.

## The requirement documents themselves

I ran the document change protocol's two checkers over the registered documents (register check and consistency check). Nothing was edited; documents change only through a new version you approve.

**The register and the files disagree on status (6 errors).**
- STD-TPL-IMP-001 v1.1: the register says approved; the file says it is proposed and that v1.0 "was proposed on 25 September 2026 and never approved".
- LAW-REG-001 v1.2: the register says approved; the file says "Proposed for approval — 30% reservation interpretation correction".
- KT-RCA-001 v1.3: the register says approved; the file carries no approval.
- PLN-JOURNEY-REF, SEED-001 and SEED-OPS-001: the files say Approved; the register calls them "Historical provenance".

**Newer versions sit on disk, all still proposed (seven).** STR-CHG-001 v1.11, SEED-OPS-001 v1.25, PRC-CHG-001 v0.13, EVL-CHG-001 v0.9, AWD-CHG-001 v0.8, CM-CHG-001 v0.12 and G1-REG-001 v1.2. The register correctly lists the approved versions. Some code is already built to them ("built ahead of approval").

**The four approved cancellation documents have defects of their own.** These came with the files you approved; I added only the approval records.
- PLN v1.32 uses `PLN_CANCELLATION_RECOVERY_PENDING` and `PLN_CANCELLATION_RECOVERY_CONFLICT`, REQ v1.20 uses `REQ_CANCELLATION_RECOVERY_INVALID` and `REQ_CANCELLATION_RECOVERY_PENDING`, and BUD v1.17 uses `BUDGET_CANCELLATION_RECOVERY_INVALID` and `BUDGET_CANCELLATION_RECOVERY_CONFLICT`, none of them defined in that document's own error table. The code defines them.
- BUD v1.17 defines the identifier `BUD24-XD-002` twice (lines 2130 and 2142). PLN v1.32 has a table row with six cells under a seven-cell header (line 1948).
- TPR v0.22 uses `TND_CANCEL_TOO_LATE` (line 747) without defining it.
- LAW-REG-001 has a table row with the wrong number of cells (line 396); EVL-CHG-001's control table has no Version row.
Each needs a corrected version; I recommend one small correction version per document, to be approved with the next set.

The checker also reports about 300 warnings, nearly all of them the register citing an older version of a document in its history text, which is expected.

## Old-era tests that cannot pass (not changed)

LEGACY_PLACEHOLDER

## Where this stands

STATUS_PLACEHOLDER
