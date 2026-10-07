# Verification notes — verifier C

| ID | Verdict | Note |
|---|---|---|
| AUD-REQ-001 | CONFIRMED | `REQ/api.py:271-280` role-only gate; `handoff.py:105-137` never looks up the Tender; revocation then blocked (`authorise.py:183-185`). |
| AUD-REQ-002 | CORRECTED | Author-turned-HoD bypass holds (`lifecycle.py:253-270`); the "different HoD certifies an Author's Draft" claim is UI-offered by design (`read.py:473-476`), so it is a spec ambiguity, not a pure code bug. Severity High kept. |
| AUD-TND-001 | CONFIRMED | `addenda.py:452-465` activates definition and deadline with no tender-status guard; `channel_confirmation.py:160-161` guards only Cancelled. |
| AUD-TND-002 | CONFIRMED | Every exit (withdraw, reopen, cancel, request-correction, return) is closed once channels are confirmed; checked `publication.py`, `lifecycle.py`, `cancellation.py`, `correction.py`. |
| AUD-STR-001 | CONFIRMED | `strategy_writes.py:372-376` deletes any request-supplied doctype with `ignore_permissions=True`; no trash hooks anywhere. |
| AUD-STR-002 | CONFIRMED | `plan_version_id` overwritten from the request (`:397-402`); guards test only the new version; no delete guard. |
| AUD-STR-003 | CORRECTED | Code claim holds; reproduction date fixed (an `effective_to` before `effective_from` is refused at `strategy_domain_guards.py:122`). |
| AUD-STR-004 | CONFIRMED | Empty `effective_to` never resolves (`strategy_consumer.py:38-40,139`) and skips the overlap guard (`strategy_domain_guards.py:138-141`); UI sends null. |
| AUD-BUD-001 | CONFIRMED | No `source_organisation_unit` vs `owner_org_unit` test in check/reserve; funding-source test skipped for REQ rows; endpoints whitelisted. |
| AUD-BUD-002 | CORRECTED | Overwrite and missing attempt snapshot confirmed; `track_changes: 1` on both Version doctypes means Frappe Version rows hold prior values, so "cannot be recovered" was softened. High kept. |
