# Progress — regression sweeps verdicts (Waves 1-4), 7 October 2026

Reads: `audit/regress-authorization.md`, `audit/regress-sod.md`, `audit/regress-state-machine.md`, `audit/regress-money-concurrency.md` (four read-only static sweeps at HEAD `3a37da4e`) and the integration gate (`INT-A.md`, `INT-B.md`, test site `kentender-test.local`).

This file is an OVERLAY read by `merge_progress.py` after the work-package files: a row here replaces the row status, keeps the red test and commit already recorded, and puts the line below in front of the existing note. Work done later on a reopened row goes in a file named `WP4R.<n>.md` (merged after this one and wins); delete or change the row here in the same commit when you do that by hand.

Rules applied:
- CLOSED by every sweep that judged the row, and no covering test failing on the gate: Verified (7 Oct 2026).
- PARTIAL or NOT CLOSED in any sweep and not Blocked: Red (the stricter verdict wins where sweeps disagree: XC-002, XC-011, XC-131, AWD-001, XC-136).
- Blocked rows stay Blocked (REQ-007, XC-132, TND-002, STR-006, PLN-021, EVL-016).
- Left Green, with the reason: rows no sweep judged (XC-125, XC-126, XC-127, EVL-002, EVL-003, EVL-004, EVL-005, REQ-005, REQ-006, TND-004, TND-005, TND-013); XC-140 (the Needs half is CLOSED; the journey/search `limit` half was not examined by any sweep); BUD-007 (the server half is CLOSED; the Vue editor half still needs a browser check).
- Verified on a static sweep plus the gate, not on a fresh browser run: the sweeps read code and tests and did not run them; the gate ran the Python tests on the test site. NDS-007 and XC-118 are Verified although their module (`test_departmental_needs_lifecycle`) has one unrelated environmental error on the gate (INT-B E-4: ERPNext test Fiscal Year overlap); their own covering tests passed.

| ID | Status | Red test | Commit | Verified on | Note |
|---|---|---|---|---|---|
| AUD-XC-001 | Verified | | | 7 Oct 2026 | regression sweep authorization, sod, state-machine + test site; AST test narrower than the scanned patterns (REG-SOD-09, RG-41). |
| AUD-XC-016 | Verified | | | 7 Oct 2026 | regression sweep authorization, state-machine + test site; In-process technical principal in usage.py is a spec decision, not an endpoint. |
| AUD-NDS-011 | Verified | | | 7 Oct 2026 | regression sweep authorization + test site. |
| AUD-XC-012 | Verified | | | 7 Oct 2026 | regression sweep authorization, state-machine, money-concurrency + test site. |
| AUD-BUD-012 | Verified | | | 7 Oct 2026 | regression sweep authorization, money-concurrency + test site; Mint enforcement is a regex scan (RG-26). |
| AUD-BUD-013 | Verified | | | 7 Oct 2026 | regression sweep authorization, money-concurrency + test site. |
| AUD-XC-003 | Verified | | | 7 Oct 2026 | regression sweep authorization, sod, state-machine + test site; Code clean; docs/ and archive/ still name TM2 (REG-AUTHORIZATION-14, RG-35). |
| AUD-XC-004 | Verified | | | 7 Oct 2026 | regression sweep authorization + test site; Residual technical-role paths are tracked under XC-019 (RG-10, RG-11, RG-30). |
| AUD-XC-018 | Verified | | | 7 Oct 2026 | regression sweep authorization + test site. |
| AUD-XC-022 | Verified | | | 7 Oct 2026 | regression sweep authorization + test site. |
| AUD-STR-005 | Verified | | | 7 Oct 2026 | regression sweep authorization + test site; create_strategy_snapshot write behind the read gate is RG-34. |
| AUD-NDS-003 | Verified | | | 7 Oct 2026 | regression sweep authorization + test site. |
| AUD-XC-029 | Verified | | | 7 Oct 2026 | regression sweep authorization + test site. |
| AUD-XC-005 | Verified | | | 7 Oct 2026 | regression sweep authorization, sod, state-machine + test site; Strategy Command Journal still unguarded (RG-40). |
| AUD-XC-006 | Verified | | | 7 Oct 2026 | regression sweep authorization, sod, state-machine + test site. |
| AUD-XC-007 | Verified | | | 7 Oct 2026 | regression sweep authorization, sod, state-machine + test site; Closed for the 7 doctypes it names; the other Planning doctypes are RG-02. |
| AUD-XC-014 | Verified | | | 7 Oct 2026 | regression sweep authorization, state-machine + test site. |
| AUD-XC-008 | Verified | | | 7 Oct 2026 | regression sweep authorization, sod, state-machine + test site; Need Event/Decision are outside the family (RG-08, RG-09). |
| AUD-XC-025 | Verified | | | 7 Oct 2026 | regression sweep authorization + test site. |
| AUD-XC-010 | Verified | | | 7 Oct 2026 | regression sweep authorization, state-machine + test site. |
| AUD-XC-026 | Verified | | | 7 Oct 2026 | regression sweep authorization + test site; Code only, dev data not cleaned; User/Strategy Scope Assignment are RG-32. |
| AUD-STR-001 | Verified | | | 7 Oct 2026 | regression sweep authorization, sod, state-machine + test site. |
| AUD-STR-002 | Verified | | | 7 Oct 2026 | regression sweep authorization, sod, state-machine + test site. |
| AUD-STR-003 | Verified | | | 7 Oct 2026 | regression sweep authorization, state-machine + test site. |
| AUD-STR-004 | Verified | | | 7 Oct 2026 | regression sweep state-machine + test site. |
| AUD-STR-008 | Verified | | | 7 Oct 2026 | regression sweep state-machine + test site; INT-A: canonical seed regression fixed in a1747084. |
| AUD-STR-011 | Verified | | | 7 Oct 2026 | regression sweep state-machine + test site. |
| AUD-REQ-001 | Verified | | | 7 Oct 2026 | regression sweep authorization, state-machine + test site. |
| AUD-XC-023 | Verified | | | 7 Oct 2026 | regression sweep authorization + test site. |
| AUD-AWD-015 | Verified | | | 7 Oct 2026 | regression sweep authorization, sod + test site. |
| AUD-BUD-001 | Verified | | | 7 Oct 2026 | regression sweep authorization, money-concurrency + test site. |
| AUD-EVL-001 | Verified | | | 7 Oct 2026 | regression sweep authorization, sod + test site. |
| AUD-EVL-010 | Verified | | | 7 Oct 2026 | regression sweep authorization, sod + test site. |
| AUD-XC-105 | Verified | | | 7 Oct 2026 | regression sweep sod, state-machine, money-concurrency + test site. |
| AUD-XC-101 | Verified | | | 7 Oct 2026 | regression sweep money-concurrency + test site. |
| AUD-XC-102 | Verified | | | 7 Oct 2026 | regression sweep money-concurrency + test site. |
| AUD-XC-103 | Verified | | | 7 Oct 2026 | regression sweep money-concurrency + test site. |
| AUD-XC-104 | Verified | | | 7 Oct 2026 | regression sweep money-concurrency + test site. |
| AUD-XC-115 | Verified | | | 7 Oct 2026 | regression sweep money-concurrency + test site. |
| AUD-XC-116 | Verified | | | 7 Oct 2026 | regression sweep money-concurrency + test site. |
| AUD-XC-119 | Verified | | | 7 Oct 2026 | regression sweep state-machine, money-concurrency + test site. |
| AUD-XC-120 | Verified | | | 7 Oct 2026 | regression sweep state-machine, money-concurrency + test site. |
| AUD-XC-118 | Verified | | | 7 Oct 2026 | regression sweep state-machine, money-concurrency + test site; Needs lifecycle module has one unrelated environmental error on the gate (INT-B E-4). |
| AUD-BUD-006 | Verified | | | 7 Oct 2026 | regression sweep money-concurrency + test site; Server side; the Vue editor half is BUD-007. |
| AUD-AWD-002 | Verified | | | 7 Oct 2026 | regression sweep money-concurrency + test site. |
| AUD-EVL-014 | Verified | | | 7 Oct 2026 | regression sweep state-machine, money-concurrency + test site. |
| AUD-XC-108 | Verified | | | 7 Oct 2026 | regression sweep state-machine, money-concurrency + test site. |
| AUD-XC-109 | Verified | | | 7 Oct 2026 | regression sweep money-concurrency + test site. |
| AUD-BUD-003 | Verified | | | 7 Oct 2026 | regression sweep state-machine, money-concurrency + test site. |
| AUD-BUD-004 | Verified | | | 7 Oct 2026 | regression sweep money-concurrency + test site; Index exists only through a patch, a fresh install lacks it (REG-MONEY-07, RG-20). |
| AUD-BUD-002 | Verified | | | 7 Oct 2026 | regression sweep state-machine, money-concurrency + test site. |
| AUD-BUD-010 | Verified | | | 7 Oct 2026 | regression sweep money-concurrency + test site. |
| AUD-TND-008 | Verified | | | 7 Oct 2026 | regression sweep sod + test site; Opening processing-actors rule is XC-135 (open). |
| AUD-EVL-013 | Verified | | | 7 Oct 2026 | regression sweep sod + test site. |
| AUD-PLN-010 | Verified | | | 7 Oct 2026 | regression sweep sod, state-machine + test site. |
| AUD-XC-134 | Verified | | | 7 Oct 2026 | regression sweep sod + test site. |
| AUD-REQ-003 | Verified | | | 7 Oct 2026 | regression sweep sod + test site; Preparer is the creator only (REG-SOD-03, RG-14). |
| AUD-REQ-004 | Verified | | | 7 Oct 2026 | regression sweep sod, state-machine + test site. |
| AUD-TND-003 | Verified | | | 7 Oct 2026 | regression sweep sod, state-machine + test site. |
| AUD-AWD-003 | Verified | | | 7 Oct 2026 | regression sweep sod + test site; Manual external orders still accept free text by design (D2). |
| AUD-AWD-011 | Verified | | | 7 Oct 2026 | regression sweep sod + test site. |
| AUD-EVL-006 | Verified | | | 7 Oct 2026 | regression sweep sod + test site. |
| AUD-NDS-007 | Verified | | | 7 Oct 2026 | regression sweep sod, state-machine + test site; Needs lifecycle module has one unrelated environmental error on the gate (INT-B E-4). |
| AUD-TND-001 | Verified | | | 7 Oct 2026 | regression sweep state-machine + test site. |
| AUD-EVL-007 | Verified | | | 7 Oct 2026 | regression sweep state-machine + test site. |
| AUD-XC-002 | Red | | | reopened 7 Oct 2026 | Reopened 7 Oct: idempotent-by-key half not met, a concurrent same-key release applies twice and governance replay is user-blind (REG-MONEY-01, REG-STATE-07: RG-16); mint/lineage lows REG-AUTHORIZATION-12/-16: RG-26. |
| AUD-XC-011 | Red | | | reopened 7 Oct 2026 | Reopened 7 Oct: a publication record can still be created already Published and the configuration publication lock lifts with one save (REG-STATE-05: RG-05; legacy module RG-04). |
| AUD-XC-013 | Red | | | reopened 7 Oct 2026 | Reopened 7 Oct: about 35 Planning decision/evidence/journal doctypes, Departmental Need Event and Strategy Command Journal still writable by System Manager/Administrator; child-table rows unguarded (REG-AUTHORIZATION-01, REG-SOD-02, REG-STATE-02/-04: RG-02, RG-06, RG-08, RG-40). |
| AUD-XC-015 | Red | | | reopened 7 Oct 2026 | Reopened 7 Oct: Departmental Need Decision has business-role read and no scope hook (REG-AUTHORIZATION-05: RG-09). |
| AUD-XC-017 | Red | | | reopened 7 Oct 2026 | Reopened 7 Oct: a Reference Data Manager can still create a second Procuring Entity through /api/resource; the rule lives only in the API (REG-AUTHORIZATION-02: RG-07). |
| AUD-XC-019 | Red | | | reopened 7 Oct 2026 | Reopened 7 Oct: Administrator passes every registry mutation capability, builder write endpoints use the read capability, System Manager/Administrator act for any supplier (REG-AUTHORIZATION-03/-04/-07: RG-10, RG-11, RG-30). |
| AUD-XC-020 | Red | | | reopened 7 Oct 2026 | Reopened 7 Oct: ktsm_register still writes unauthenticated with ignore_permissions and its disabled login can never be enabled (REG-AUTHORIZATION-06: RG-12). |
| AUD-XC-021 | Red | | | reopened 7 Oct 2026 | Reopened 7 Oct: journey list still reads tabUser Permission and User Scope Assignment still feeds the entity offer (REG-AUTHORIZATION-10/-11: RG-32, RG-33). |
| AUD-AWD-001 | Red | | | reopened 7 Oct 2026 | Reopened 7 Oct: Award side closed; evaluation side open, AO/HOP can sit on the committee and sign reports, owner decision needed (REG-SOD-04: RG-15). |
| AUD-REQ-002 | Red | | | reopened 7 Oct 2026 | Reopened 7 Oct: a different lead Head can certify an Author Draft directly and only the creator counts as preparer (REG-SOD-03: RG-14). |
| AUD-XC-136 | Red | | | reopened 7 Oct 2026 | Reopened 7 Oct: refusal is grant-time only; a later System Manager grant to a holder, technical principal denied for READ only, sod_tags unconsumed (REG-SOD-07: RG-39). |
| AUD-XC-107 | Red | | | reopened 7 Oct 2026 | Reopened 7 Oct: funding_state and drawn totals still read from the snapshot after the Plan Item lock (REG-MONEY-10: RG-23). |
| AUD-XC-117 | Red | | | reopened 7 Oct 2026 | Reopened 7 Oct: Planning DPP amount/quantity not exact-validated (NaN passes, excess scale rounded) and huge integers raise untyped InvalidOperation (REG-MONEY-05/-06: RG-03, RG-29). |
| AUD-XC-129 | Red | | | reopened 7 Oct 2026 | Reopened 7 Oct: refusal is typed but limited to 12 integral digits, 18 required, storage decision open (money-concurrency sweep PARTIAL, no REG id: RG-28). |
| AUD-XC-133 | Red | | | reopened 7 Oct 2026 | Reopened 7 Oct: check/reserve fixed at scale 2, Requisitions CURRENCY constant KES, Tenders snapshot constants (money-concurrency sweep PARTIAL, no REG id: RG-28). |
| AUD-XC-130 | Red | | | reopened 7 Oct 2026 | Reopened 7 Oct: Bid Opening and Proceedings still lock then read a snapshot; Bid Submission and per-case sequences use count()+1 (REG-MONEY-02/-03/-04, REG-STATE-06: RG-17, RG-18, RG-19). |
| AUD-XC-131 | Red | | | reopened 7 Oct 2026 | Reopened 7 Oct: Budget, Bid Opening, Proceedings and Bid Submission journals still key-first, user-blind or optional (REG-MONEY-01/-02/-03, REG-STATE-07: RG-16, RG-17, RG-18). |

## Follow-ups

- The rows reopened above are tracked as Wave 4R (RG-01 to RG-42) in `REMEDIATION_TRACKER.md`. A Red row returns to Green only when the RG rows named in its note are Green.
- Rows with no regression verdict (list above) still need a sweep or a focused re-check before their wave can close.
- XC-129 and XC-133 are PARTIAL in the money-concurrency sweep with no REG id of their own; they are carried by RG-28.

## Needs browser check

None added by this reconciliation (BUD-007 Vue editor half is already recorded).

## Dev site actions needed

None from this file. RG-02, RG-13 and RG-20 will each need `bench migrate` on dev when they land.

## Document follow-ups

- D-2 (PLN): add RG-01 (Annual Plan publication D4) to the triggers.
- RG-35: owner to say whether TM2 mentions in `docs/` and `archive/` and the sidebar label "Tender Management" count against decision D1.
- RG-28: BUD should record the float-JSON deviation and the 12 versus 18 digit decision.
