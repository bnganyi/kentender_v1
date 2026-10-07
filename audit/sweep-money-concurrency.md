# Sweep: money-and-concurrency (Phase 2, read-only, static)

## 1. Header

- **Scope.** (A) Money arithmetic, comparison, rounding, currency and denominators in Budget, Planning, Requisition, Tenders, Bid Submission (price producer), Evaluation and Award. (B) Check-then-write atomicity for budget ceilings, reservations, commitments, plan-item allocation, sequence/naming counters and "at most one open X" rules, plus optimistic-lock stamps on update commands.
- **Method (reproducible).** Static reading only. No bench, DB or site was touched. The one code execution was pure Python: `frappe.utils.flt` on literals, and `decimal`/float arithmetic. Commands used:
  - `grep -rnE 'for[ _]update|get_lock|\.lock\(|FOR UPDATE|with_for' --include=*.py kentender_*`
  - `grep -rnE 'float\(|flt\(|round\(|Decimal|\* 0\.|/ ?100|ceiling|headroom|threshold|estimated_value|tender_security|price|score' --include=*.py <tenders award bid_evaluation bid_opening bid_submission>`
  - `grep -rn "1e-9\|0.0001\|0.01\|0.005" kentender_budget/**/services kentender_procurement/**/procurement_planning/services`
  - A python/json walk of every `doctype/*/*.json` for `unique`, `Currency`, `Float` and `Percent` fields.
  - An `ast` walk of `*/services/*.py` for functions taking `expected_record_version`/`expected`, checking each body for a stale check. It found 179 functions and 37 without a direct call. I read a sample (REQ row commands, Tender evidence commands, Bid Submission save/contact/submit) and they delegate to helpers that do check. Not claimed as findings.
  - Frappe framework facts verified in `apps/frappe/frappe`: `model/document.py` (`load_from_db`, `check_if_latest`, `load_doc_before_save`, `reload`), `database/database.py` (`begin`/`commit`), and grep for isolation settings (`READ COMMITTED`, `tx_isolation`, `transaction_isolation`) over frappe, `/etc/mysql`, `sites/*/site_config.json` and the repo (none found).
  - DB server: MariaDB 10.6.23 (`mariadb --version`). `/etc/mysql` was grepped and sets no isolation level.
- **Docs read** (latest versions confirmed with `ls | sort -V`):
  - BUD-CHG-001 v1_12: §4.6, §4.8, §8.2A, §8.3, §9.2, §9.3, BUD-BR-001..030, BUD-SC-*, BUD18/19/20 acceptance rows.
  - PLN-CHG-001 v1_29: §4.1 (Money), §5.5.3.1 (reservation measure).
  - RES-IMP-001 v1.0, in full.
  - AWD-CHG-001 v0_5: §3, §5.1, AWD-IF-07.
  - EVL-CHG-001 v0_5: funding paragraph.
  - TPR-CHG-001 v0_17: TPR09-AC-007/025.
  - AGENTS.md.
- **Standing assumption (affects F1–F4).** Frappe v16 runs MariaDB at the server default, InnoDB `REPEATABLE READ`. I found no override in Frappe, the repo or `/etc/mysql`. I could not query the live server (`SELECT @@transaction_isolation` was not run). Phase 3 should run that statement. If the server is `READ COMMITTED`, F1 and F4 shrink to their lock-set parts. F2, F3 and the lock-set halves of F1 and F4 stay either way.

## 2. Coverage

| Bucket | Enumerated | Classification |
|---|---|---|
| Budget whitelisted endpoints (`budget_api.py`) | 32 | Money-moving: `check_funding`, `reserve_funding`, `release_reservation`, `convert_reservation`, `adjust_commitment`, `revalidate_reservations` (F1, F2, F5, F9). Governance (save/submit/return/approve/close/lines): F3, F10. Reads and affordability: F6. |
| Budget service modules read in full | 5 of 14: `budget_check_reserve_contracts`, `budget_commitment_contracts`, `budget_revision_request_contracts` (lines 100–449), `budget_idempotency`, `budget_reference`. Partly read: `budget_contracts` (position calculation, draft save and successor creation), `budget_line_contracts` (lines save and affordability), `budget_readiness_contracts` (readiness, approve, close). | Findings F1–F11. Not read: audit/read/home/analytics/technical-read modules (display only). |
| `SELECT … FOR UPDATE` sites | 45 in budget/procurement/core/strategy (non-test, non-seed) | Classified by what follows the lock. A plain re-read of the locked row or an aggregate is F1/F12. A doc `save` after the lock is protected by Frappe's `modified` check (clean, F12 for the untyped error). |
| Named locks (`get_lock`) | 7 sites (NDS, Planning, REQ, Tenders reference generators, BWMF publish) | F12; the unique indexes carry the load (§4). |
| Unique/DB guards verified | `Procurement Budget Version` active-marker index; `drawdown_line_id`; `planning_request_id`; `Budget Audit Event.idempotency_key`; `generated_reference` on Version/Line Version/Reservation/Commitment; `Requisition.open_slot_key`; plan/task/decision references; `pln_uniq_*` composites | Checked and clean as the *last-resort* guard (§4). |
| Money producers/consumers traced | DPP funding entry → plan allocations → `line_totals` → `check_plan_affordability` → `budget_revision` → Budget `receive_budget_revision_request` → `check_funding`/`reserve_funding` → REQ drawdown → Tender snapshot → Bid price → Evaluation `calculate_price`/`compare`/`funding` → Award `checks.funding` | F6–F9, F11, F13; REQ and Bid Submission exact (§4). |
| Optimistic-lock commands (179 with an `expected_*` param) | Planning, REQ, Tenders, NDS, Evaluation, Award, Opening, Proceedings, Bid Submission | Strict (empty stamp refused) in PLN/REQ/TND/EVL/AWD/BOP/PRC `envelope`/`records`. Optional in Budget (F10). |
| Reservation share (AGPO) denominator | `readiness.reservation_measure`/`reservation_allocations` and every consumer (`plan_read`, `plan_governance`, `workspace`) | Calibration item: **fixed**, see §4.1. Residual rounding items in F13. |
| Concurrency tests present | `test_bud_chg_001_phase3_check_reserve.py:140` (named "concurrent … cannot oversubscribe") | It is two sequential calls on one connection. No test runs two connections, so F1–F4 are untested (BUD §16/§18 require concurrent reserve/activation tests). |

---

## 3. Candidate findings (most severe first)

Severity counts: **Critical 0 · High 5 · Medium 6 · Low 3.** Details below.

### F1 (High, CODE DEFECT) — `reserve_funding` can oversubscribe a Budget Line: the line is locked, but availability is read afterwards with a plain snapshot read

- **Evidence.**
  - `kentender_budget/kentender_budget/services/budget_check_reserve_contracts.py:314`: `existing = _existing_reservations_for_correlation(correlation_id)`. This plain read starts the transaction snapshot.
  - `:340-343`: `frappe.db.sql("select name from \`tabProcurement Budget Line\` where name in %s order by name for update", …)`. The lock is taken but the line row is never updated.
  - `:372-385`: `totals, _budget = _line_totals(rows, line_docs)` then `if entry["available"] < entry["required"]: … BUDGET_INSUFFICIENT_FUNDS`. `_line_totals` → `_line_position` (`budget_contracts.py:196-216`) sums `Funding Reservation.remaining_amount` and `Procurement Commitment.current_amount` with plain `SELECT SUM`, which InnoDB serves from the snapshot.
  - In the REQ path, `authorise.py:111-118` runs `check_funding` and `reserve_funding` in one transaction. `check_funding` already read the positions (`budget_check_reserve_contracts.py:230`, via `_line_totals`), so the snapshot predates any waiting `FOR UPDATE`.
- **Governing rule.** BUD v1.12 §8.3 ("locks Budget root/affected lines in stable order, rechecks aggregate availability"). BUD-BR-013 ("Concurrent commands cannot oversubscribe a line"). BUD18-AC-019. Framework fact: under REPEATABLE READ a locking read sees the latest committed row, but later non-locking reads in the same transaction keep using the older snapshot.
- **Interleaving.** Line L approved 100,000,000.00, reserved 0.
  1. REQ-A and REQ-B each call `check_funding` for 80,000,000.00. Both read available 100m and pass (snapshots S_A, S_B).
  2. A: `reserve_funding` takes the line lock, `_line_position` shows available 100m ≥ 80m, inserts the reservation and commits.
  3. B was blocked at `for update`. It resumes and `_line_position` reads with S_B, which cannot see A's new `Funding Reservation`. It shows available 100m ≥ 80m and inserts a second 80m reservation.
  4. Result: reserved 160m on a 100m line, available −60m. `drawdown_line_id` is unique per drawdown line, not per Budget Line, so nothing else stops it.
  - Both requisitions need different Plan Items, so the REQ `open_slot_key` does not serialise them.
- **Reproduction sketch.** On `kentender-test.local`, two connections (threads, each `frappe.connect`), a `threading.Barrier` after each has run `check_funding`, then `reserve_funding` from both:

  ```python
  def worker(tok, key):
      frappe.connect(site=SITE)
      tok2 = check_funding(...80_000_000...)       # snapshot established
      barrier.wait()
      reserve_funding(token=tok2["token"], ..., idempotency_key=key)
      frappe.db.commit()
  # expect: second call raises BUDGET_INSUFFICIENT_FUNDS; today both succeed
  assert Decimal(frappe.db.sql("select sum(remaining_amount) from `tabFunding Reservation` where budget_line=%s", line)[0][0]) <= 100_000_000
  ```

  First run `SELECT @@transaction_isolation`.
- **Fix class (no code proposed here).** Use locking reads for the aggregates, or take the lock before any other read in the request.

### F2 (High, CODE DEFECT) — `adjust_commitment` increase is not serialised against the line, nor against reservations

- **Evidence.** `budget_commitment_contracts.py:266`: `select name from \`tabProcurement Commitment\` where name=%s for update`. Only this one commitment row is locked. `:275-276`: `pos = _line_position(...)` / `if delta > pos["available"] + 0.0001`. Same plain snapshot read.
- **Governing rule.** BUD §9.1 table: `adjust_commitment` is a "Locked adjustment … no unfunded increase". BUD-BR-013.
- **Interleaving.** Line approved 100m, commitments C1 = 40m, C2 = 40m, available 20m.
  1. A raises C1 to 60m (delta 20 ≤ 20); B raises C2 to 60m (delta 20 ≤ 20).
  2. They lock different commitment rows, so there is no wait, and neither sees the other.
  3. Both commit: committed 120m, available −20m.
  - The same hole exists between `adjust_commitment` (locks a commitment) and `reserve_funding` (locks Budget Line rows). The two lock sets never intersect.
- **Sketch.** Two threads as in F1, one adjusting each commitment, with a barrier before `_line_position`. Assert `available >= 0` afterwards.

### F3 (High, CODE DEFECT) — Budget activation and closure use a lock set that does not intersect reservation locks, so successor approval or closure can race a reservation

- **Evidence.**
  - Approval and closure lock `Procurement Budget Version` rows: `budget_readiness_contracts.py:656-659` and `:837`. The floor check (`_evaluate_successor_guards`, `:138`, `:171`) reads `_reserved_plus_committed` with plain reads.
  - `reserve_funding` locks `Procurement Budget Line` rows only (`budget_check_reserve_contracts.py:340-343`) and reads the Active Version with a plain `_active_version` (`budget_contracts.py:165`).
  - Neither side takes the other's lock.
- **Governing rule.** BUD §8.2A step 2 ("All Budget activation, closure and decision-validation paths use compatible locks"). BUD-BR-017, BUD-BR-021, BUD-BR-023. BUD19-AC-022 ("commit-time race … cannot bypass guards"). BUD18-AC-047 (test both orderings).
- **Interleavings.**
  - *Approve vs reserve.* L approved 100m, reserved 70m. A approves V2 with L = 80m (floor 70 ≤ 80, passes). B concurrently reserves 20m (available 30m under V1). Commit both: approved 80m, reserved 90m, available −10m.
  - *Close vs reserve.* After FY end, the budget has no holds (`_closure_status_for` → ready). A `close_budget` flips the Version to Closed. B's `reserve_funding` read the Version as Active before A committed, passes, and inserts. Commit both: a Closed Budget with a new Active reservation (BUD-BR-023 breached).
- **Sketch.** Barrier-synchronised threads: `approve_budget_version(payload)` vs `reserve_funding(...)`. Assert the post-state satisfies `approved >= reserved + committed` and `no Active reservation on a Closed Budget`.

### F4 (High, CODE DEFECT) — The Finance decision's "serialised basis" is validated with stale reads after the lock

- **Evidence.** `budget_line_contracts.py:603` (`_active_version`, plain read, starts the snapshot), then `:609-610` (lock Version and its Line Versions), then `:611` `frappe.db.get_value("Procurement Budget Version", version.name, "status") != "Active"` and `:619-626` (re-read line versions). Both re-reads are plain, so the snapshot hides a successor activation that committed while this transaction waited. `approve_budget_version` holds those same rows locked for its whole transaction (`budget_readiness_contracts.py:656`), so the waiter will wait.
- **Governing rule.** BUD §8.2A step 3 ("Re-read current Active Version … stale … fails atomically"). BUD-SC-BASIS-RACE. BUD18-AC-047.
- **Interleaving.**
  1. Budget Approver A approves successor V2 and holds the version-row locks.
  2. Finance officer B (`confirm_plan_funding`, `plan_finance.py:273-296`) has already read `_active_version` = V1 and blocks on `for update`.
  3. A commits. B resumes. `status` of V1 reads "Active" (stale). The line-version `expected_revisions` match V1's rows (stale).
  4. B records "Confirm plan funding" against a Budget basis that has just been replaced, and commits. That is the positive decision on a replaced basis the doc forbids.
- **Sketch.** One thread does `approve_budget_version` (V2 with line L reduced below planned), another `confirm_plan_funding` on a plan whose `expected_revisions` are V1's. Barrier before the Finance thread's `FOR UPDATE`. Expect `PLN_FINANCE_STALE`; today it confirms.

### F5 (High, CODE DEFECT; cross-ref authz sweep) — Money-moving Budget endpoints are whitelisted to any authenticated user; the "contract service principal" is not enforced; `idempotency_key` is not used for dedupe

- **Evidence.**
  - `budget_commitment_contracts.py:24-31`: `_require_service_capability` only refuses `Guest`. Its docstring says "any authenticated user acting for a downstream module may call".
  - `budget_api.py:286` (`release_reservation`), `:305` (`convert_reservation`), `:322` (`adjust_commitment`), `:267` (`revalidate_reservations`) are all `@frappe.whitelist()` (default `allow_guest=False`, so every logged-in user, including portal users).
  - `release_reservation` (`:119-161`) ignores `idempotency_key` except as a ledger label: there is no replay check. The same call retried releases again (`min(release_amount, remaining)`).
- **Governing rule.** BUD v1.12 §7: "The contract service principal is an authenticated service account, not a business role… cannot create a reservation, edit a version or read a Draft". BUD-BR-015: release, conversion and adjustment "require an authenticated downstream event and are idempotent by correlation ID". BUD §4.6 ("Changed only through the adjustment service"). AGENTS.md §4 (enforce permissions on the server).
- **Repro.** Any logged-in portal user: `POST /api/method/kentender_budget.api.budget_api.release_reservation {"reservation": "<RSV-id>", "amount": 40, "idempotency_key": "K"}`, twice. Remaining 100 → 60 → 20. `adjust_commitment {"commitment": C, "new_total": 0}` cancels a commitment and frees funds. `adjust_commitment` with a larger `new_total` consumes available funds.
- **Note.** The only in-repo callers are REQ revocation (`authorise.py:192`, via `funding_gateway`); no Contract Management caller exists yet. The release path REQ uses calls with `amount=None`, so it is naturally idempotent.

### F6 (Medium, CODE DEFECT) — Float totals with a `1e-9` epsilon make an exactly-at-ceiling plan "over budget"

- **Evidence.**
  - `procurement_planning/services/readiness.py:168-179` (`line_totals`): `totals[a.budget_line] = totals.get(a.budget_line, 0.0) + flt(a.indicative_amount)`.
  - `plan_finance.py:46-51` passes those float totals to `check_plan_affordability`. `budget_line_contracts.py:496`: `within_approved = planned <= pos["approved"] + 1e-9`, and the same at `:646` for the decision-time version.
  - `budget_revision.py:72` and `:161`, `departmental_update.py:110`, and Budget `budget_revision_request_contracts.py` (`if planned <= approved + 1e-9`) use the same test.
  - `1e-9` is below one float ulp for any amount above about KES 8 million (ulp(8e6) ≈ 9.3e-10), so the epsilon gives no tolerance at ministry scale.
- **Governing rule.** PLN v1.29 §4.1 Money ("Exact decimal currency-unit value, never binary float"). BUD §4.8, BUD-SC-PRECISION ("decimal arithmetic has no epsilon path"). BUD-BR-007 / PLN §5.3.1 (within-approved blocks only when planned exceeds approved).
- **Concrete flip (computed).** One Budget Line approved 184,132,482.07. Four allocations in creation order: 44,872,648.85 + 28,586,332.99 + 80,884,095.33 + 29,789,404.90 = exactly 184,132,482.07. The float sum is `184132482.07000002`. `planned <= approved + 1e-9` → False. Result:
  - `PLN_PLAN_NOT_AFFORDABLE` (excess 2.98e-08, shown as "over by KES 0.00").
  - `RequestBudgetRevision` is accepted. Planning stores `over_amount = planned - approved = 2.98e-08`.
  - Budget's `receive_budget_revision_request` also treats it as exceeding and opens a request for the Budget Officer.
  - Similar pairs exist for 3- and 6-allocation plans (e.g. 73,077,101.74 + 66,137,453.19 + 28,853,138.79 + 71,048,677.26 + 89,424,147.29 + 13,825,028.05).
- **Test sketch (pure python, no DB).** `sum(map(float, parts)) <= float(Decimal sum) + 1e-9` → False. A service-level test creates the allocations and calls `check_plan_affordability`.

### F7 (Medium, CODE DEFECT) — Method-condition limits and the low-value cumulative cap compare float sums

- **Evidence.**
  - `readiness.py:391` (`value = sum(flt(a.indicative_amount) …)`) feeds `profiles.method_conditions(… planned_value=value …)`. There, `profiles.py:232` is `value = Decimal(str(flt(planned_value)))`, which keeps the float noise. `:242` is `ok = (minimum <= 0 or value >= minimum) and (maximum <= 0 or value <= maximum)`, so a maximum is inclusive.
  - `readiness.py:498` and `:503`: `totals[key] = totals.get(key, 0.0) + item_value(...)`; `if cap and total > cap` for the low-value per-item annual limit.
  - `plan_workbench.py:405` computes a float `planned_value` for admissibility at item save.
- **Governing rule.** PLN §4.1 Money (exact Decimal). PLN §5.5.3.3 / PLN-AC-104 (limit per item per year). The documented limits are legal thresholds by method.
- **Concrete flip (computed).** An item with three allocations 242,653.82 + 201,170.23 + 56,175.95 = exactly 500,000.00. The float sum is `500000.00000000006`, so `value <= maximum(500000.00)` is False, "Not met", and a mandatory failure gives `PLN_METHOD_NOT_ADMISSIBLE`. Another case at a 5,000,000 cap: 4,204,274.69 + 585,436.28 + 210,289.03 → `5000000.000000001`.
- **Sketch.** Pure Python as above. A service test would save an item with those allocations under a method profile whose `maximum_amount` is 500,000.

### F8 (Medium, CODE DEFECT) — Budget floors, `Needs Attention` and position tests use float arithmetic, so exactly-balanced lines misclassify

- **Evidence.**
  - `budget_contracts.py:215`: `available = approved - reserved - committed` (floats).
  - `budget_commitment_contracts.py:90`: `new_status = "Needs Attention" if pos["available"] < 0 else …`.
  - `budget_readiness_contracts.py:171`: `if flt(current.approved_amount) < protected:` (BUD-BR-017), where `protected = pos["reserved"] + pos["committed"]` (`:221-225`).
- **Governing rule.** BUD-BR-016 (`Needs Attention` only on a real breach). BUD-BR-017 (cannot reduce *below* Reserved + Committed). BUD §4.8 (no epsilon path).
- **Concrete (computed).**
  - Approved 843,171,926.93 = reserved 535,955,290.08 + committed 307,216,636.85. `float(approved) − r − c = −5.96e-08 < 0`, so `revalidate_reservations` flips every reservation on a fully-subscribed line to `Needs Attention` ("blocks downstream progression"). The decimal answer is 0.00.
  - A successor that lowers a line to exactly 697,420,216.55 against reserved 47,235,303.96 + committed 650,184,912.59: `float(r)+float(c) = 697420216.5500001 > 697420216.55`, so it is refused with a floor breach and a "shortfall" of KES 0.0000001.
- **Sketch.** Pure arithmetic as above; a service test builds the reservation/commitment rows and calls `revalidate_reservations` / `_evaluate_successor_guards`.

### F9 (Medium, CODE DEFECT) — Money inputs on Budget lines, Budget totals and Planning funding are not exact-decimal validated; reconciliation uses a 0.01 tolerance; downstream contracts accept floats and a 0.0001 slack

- **Evidence.**
  - `budget_line_contracts.py:143` and `:165-166`: `approved_amount = flt(row.get("approved_amount"))`; `if approved_amount <= 0`. There is no scale or finite check.
  - `budget_contracts.py:905-910` (`authorised_total`): `total_val = flt(total)`; `if not total or total_val <= 0`.
  - `dpp_lifecycle.py:359` and `:442`: `entry.indicative_amount = flt(indicative_amount)`; `if flt(indicative_amount) <= 0`. The whitelisted `save_need_funding(indicative_amount=None)` passes the raw value through. Only the REQ drawdown boundary uses `money.parse_money` (`plan_requisition.py:512-513`).
  - `flt("nan")` and `flt("inf")` return `nan` / `inf`. Verified by executing `frappe.utils.flt`: `nan <= 0` is False, so NaN and Infinity pass every positivity guard. At the DB, strict mode rejects them as an untyped 500.
  - `budget_readiness_contracts.py:71` (`"match": abs(diff) < 0.01`) and `:197` (`difference >= 0.01`) make the line-total-equals-authorised-total and transfer-balance rules accept sub-cent differences.
  - `budget_commitment_contracts.py:199` (`amount > remaining + 0.0001`) lets a conversion exceed the remainder by 0.0001. `:224` stores `remaining_amount = remaining - amount` (negative). `release_reservation`, `convert_reservation` and `adjust_commitment` take `float` and do no precision check (`budget_api.py:289`, `:308`, `:325`).
- **Governing rule.** BUD §4.8 Money ("Inputs with more fractional digits than supported are rejected"; "never binary float"). BUD18-AC-051 ("float JSON, malformed and overflow values fail before effects"). BUD-BR-007 / BUD18-AC-007 (line total *equals* the authorised total). BUD-BR-013 (never negative). PLN §4.1 ("Excess precision is rejected, never rounded"). The REQ and Planning drawdown boundaries do enforce this (so the project knows the rule), but the Budget line and DPP funding inputs do not.
- **Concrete.**
  - Authorised total 100,000,000.00; lines 60,000,000.004 + 40,000,000.004: diff −0.008, `abs(diff) < 0.01`, so the version submits and approves.
  - `convert_reservation(reservation=R, contract=C, amount=100.00005)` against remaining 100.00: accepted, commitment 100.00005, remaining −0.00005.
  - `save_need_funding(indicative_amount="1000000.005")` is stored as given.
- **Sketch.** Service calls with those payloads; assert a typed `*_MONEY_PRECISION_INVALID` error (the Budget `_exact_money` already exists in `budget_check_reserve_contracts.py:66-82` and could not be reused here).

### F10 (Medium, CODE DEFECT) — The Budget optimistic-lock stamp is optional, and the line-editor save does not move it

- **Evidence.**
  - `budget_readiness_contracts.py:547-549`: `return bool(expected) and str(version.modified) != str(expected)`. An omitted or empty `expected_modified` skips the check in submit (`:564`), return (`:604`), approve (`:649`) and close (`:834`).
  - The same optional test is in `budget_contracts.py:982-983` (draft save) and `budget_line_contracts.py:92-94` (lines save).
  - `_save_budget_lines_draft` (`budget_line_contracts.py:85-227`) edits and inserts `Procurement Budget Line Version` rows and never saves the parent Version, so `Version.modified` (the stamp, `budget_contracts.py:531`) does not change after a lines save.
- **Governing rule.** BUD v1.12 §9.2: "Every write requires the expected record version." §9.3 / BUDGET_STALE_WRITE. KT-STD-001 §11 (referenced there).
- **Interleaving.** Officer A and Officer B open the editor (stamp M0). A saves line X = 50m (the stamp stays M0). B saves X = 60m with stamp M0 → passes, and B silently overwrites A's saved line amount. (If B's transaction overlapped A's, `line_version.save()` would raise Frappe's `TimestampMismatchError`; sequential, non-overlapping edits are not caught.) A direct API caller can omit the stamp entirely.
- **Calibration note.** This is the Budget-side residue of the known "editor post-save reload race / optimistic-lock stamp" defect. The Planning/REQ/Tenders/Evaluation/Award stamps are strict (§4).

### F11 (Medium, CODE DEFECT) — Award's funding check reads the frozen Evaluation report snapshot, not the current Budget, and an unavailable funding read counts as "no restriction"

- **Evidence.** `award/services/checks.py:77-80`:
  ```
  f = state.snapshot(state.current_report(doc)).get("funding") or {}
  short = flt(f.get("shortfall") or 0)
  return {"restricted": bool(cstr(f.get("qualification")) or short > 0), "detail": f}
  ```
  Award has no Budget call (`grep -rn funding award/services` shows only the snapshot readers). Upstream, `bid_evaluation/services/funding.py:36-45` returns `None` when no reservation ids exist or the Budget read raises, and `compare()` then returns `None`, so the report's funding fact is absent and `funding(doc)` is `restricted: False`.
- **Governing rule.** AWD-CHG-001 v0_5 §3 (Budget: "Authoritative current funding position… Award checks funding"). §5.1 ("Distinguish an established restriction from an unavailable check. Neither permits an unsupported positive decision"). AWD-IF-07 ("read-only current funding response with explicit unknown/failure result"). EVL v0_5 funding paragraph ("When that read is unavailable no funding fact is shown").
- **Repro.** Make Budget's `get_funding_lineage` raise (or use a Tender with no reservation ids), sign the report, then record an award. No Funding issue opens; the positive decision proceeds. Separately, release the Tender's reservation after the report is signed: the Award guard still shows the signed (older) shortfall state.

### F12 (Low, CODE DEFECT) — Typed stale-version/idempotency errors are unreachable under real concurrency; named-lock reference generators read stale data; `expected_record_version` taken in the same transaction proves nothing

- **Evidence.**
  - Every module's lock helper is `select name … for update` followed by a separate plain `frappe.get_doc(...)`: `procurement_planning/services/envelope.py:90-99`, `procurement_requisitions/services/envelope.py:88-97`, `tenders/services/envelope.py:86-91`, `bid_evaluation/services/records.py:85-90` (where `case_for` is itself a plain read before the lock), `award/services/records.py:109-113`, `bid_opening/services/records.py:79-84`, `proceedings/services/records.py:88-93`.
  - A waiter whose snapshot predates the other commit therefore passes `check_record_version`/`check_version` on stale data. It is stopped later only when `doc.save()` runs Frappe's `check_if_latest` (`frappe/model/document.py:1012-1038`, which loads `for_update=True` and compares `modified`) and raises `TimestampMismatchError`, instead of the typed `PLN_STALE_WRITE`, `REQ_STALE_VERSION`, `TND_STALE_VERSION`, `EVL_VERSION_CONFLICT` or `AWD_RECORD_CHANGED`.
  - Commands that lock and check a row but never save it (e.g. `plan_requisition.authorise_requisition_drawdown`: `item = envelope.locked("Annual Plan Item")` at `:484`, `check_record_version(item, expected_record_version)` at `:485`, item never saved) get no protection. `expected_record_version` there comes from `projection["record_version"]` read in the same transaction (`authorise.py:107` (projection) and `:127` (`expected_record_version=projection["record_version"]`)), so the comparison is snapshot-to-snapshot and always equal. A concurrent Plan Item supersession/state change that commits after the snapshot is not seen (`item.item_state != "Active"` is checked on the snapshot row, `:486`).
  - Reference generators take `get_lock(...)` then compute `max+1` from a plain read: `procurement_planning/services/references.py:64-70`, `procurement_requisitions/services/references.py:55-62`, `tenders/services/references.py:42-52`, `departmental_needs/services/lifecycle.py:345-354`. `get_lock` is held until the connection closes (after commit), but the waiter's snapshot predates the winner's insert, so both compute the same number. The unique indexes (`tender_reference`, `requisition_reference`, `need_reference`, `dpp_reference`, `pln_uniq_entry_id_per_version`) turn that into a duplicate-key error. Without those indexes it would duplicate.
  - `StartTender` has the same shape: a second concurrent start dies on `tender_reference` uniqueness or a timestamp mismatch, instead of "return its identity".
- **Governing rule.** TPR v0_17 TPR09-AC-007 ("Concurrent or repeated StartTender requests for one handoff produce one Tender and return its identity"), TPR09-AC-025 (a stale save never overwrites). Typed error vocab in each module's §8 (PLN `PLN_STALE_WRITE`, REQ `REQ_STALE_VERSION`, TND `TND_STALE_VERSION`).
- **Effect.** Fails closed (no corruption found for the saved-root commands), but with an untyped failure, a UX dead-end and a rolled-back whole command.

### F13 (Low, CODE DEFECT / SPEC GAP) — Rounding asymmetries and display rounding around the 30% target

- (a) `readiness.py:232`: `required = (eligible * target / 100).quantize(cent, ROUND_HALF_UP)`; `remaining = max(required − qualifying, 0)`; `met` is `remaining == 0`. PLN §5.5.3.1 defines `required = percentage × eligible` with no rounding. Example: eligible 100.01 → exact 30.003, code 30.00. Qualifying 30.00 therefore reports "met" at a true share of 29.997%. Bounded below half a cent, so the legal effect is negligible, but the threshold is rounded in the entity's favour. SPEC GAP: the doc is silent on cent rounding for the required amount.
- (b) `plan_governance.py:190` stores `reserved_share_percent` as `round(float(share), 1)`. `plan_read.py:2062-2066` renders `f"Reserved share {share:.0f}% … target {target:.0f}%"`. A 29.6% share displays "Reserved share 30% … target 30%" in the governance advisory line while the decision summary (from the Decimal `met`) says more allocation is required. Display inconsistency, not a decision error.
- (c) Producer/consumer rounding for bid prices. `bid_submission/services/price.py:31,46` quantise unit price and amount before tax with `ROUND_HALF_UP`. `bid_evaluation/services/rules.py:255-256` recomputes with `Decimal.quantize(0.01)` (default ROUND_HALF_EVEN) on unquantised inputs, and `:263-270` flags any difference as "Needs review". Example: quantity 12.5 × unit 10.01 = 125.125 → producer 125.13, consumer 125.12, so a compliant bid goes to "Needs review". Latent: REQ quantities are whole numbers and bid inputs are limited to scale 2 (`bid_submission/services/controls.py:92-98`), so no current IT-product path reaches it. Becomes live as soon as a fractional-quantity product exists.

---

## 4. Checked and clean (so Phase 3 can tell clean from unexamined)

### 4.1 Calibration items in this domain

| Known defect | Status in current code |
|---|---|
| Reservation (AGPO) denominator used the approved budget | **Fixed.** `readiness.py:211-246` (`reservation_measure`, share at `:238`) and `:249-310` (`reservation_allocations`) use the eligible value of the exact Plan Version (`Annual Plan Item` rows of `version_name`, `item_state != Dissolved`), in `Decimal`, with the Budget ceiling explicitly absent (docstring `:253-262`). Single source: `plan_read.py:409,997,2076`, `plan_governance.py:185`, `workspace.py:560` all call it. No remaining `get_annual_procurement_budget_basis` / `AnnualProcurementBudgetBasis` in code (grep). Fixture arithmetic per RES-IMP-001 §1.2: 130m × 30% = 39m; 50m/130m = 38.46% (`quantize(cent, ROUND_HALF_UP)` at `:232` and `:238`). Residual: F13(a)(b). |
| Editor post-save race / optimistic-lock stamp | Still present on the Budget side only (F10). Strict in PLN/REQ/TND/EVL/AWD/BOP/PRC. |
| `**kwargs` transport fields | Not applicable to Budget: `budget_api.py` uses explicit parameters. Other modules are out of this sweep's scope. |
| Open Tender preparation period 7 vs 21 days; Requisition Handoff v1.4 names; digest/control changes; Strategy readability; intake scope; dead-end Need; dropped doctype | Not money/concurrency; not examined here. |

### 4.2 Money arithmetic found correct

- REQ money and quantity are exact `Decimal` with a closed grammar (reject float/exponent/NaN/excess scale/overflow): `procurement_requisitions/services/precision.py:41-79`. Validation compares `Decimal` throughout (`validation.py:141-151`). The REQ finding code `BALANCE_CHANGED` compares requested value to remaining as Decimals.
- Planning drawdown boundary is strict: `plan_requisition.py:440-447` (`_strict`) refuses floats, and parses with `parse_money`/`parse_quantity`. `PLN_ALLOWANCE_EXCEEDED` is checked as `drawn + requested > approved` in Decimal (`:516`).
- Budget `check_funding`/`reserve_funding` money is exact at that boundary: `budget_check_reserve_contracts.py:66-82` (`_exact_money` refuses float, NaN, exponent, scale > 2, ≤ 0), row totals aggregated by Budget Line before the availability test (`:176-203`), `_stored_money` quantises the float position to 2 dp (absorbs float noise on the *reserve* decision). One reservation per drawdown line (`:389-414`).
- Bid price and tender total are `Decimal` with half-up cent rounding on the producer side (`bid_submission/services/price.py`), compared as Decimals by Evaluation (`rules.py:263-270`). Evaluation ranking and ties compare `Decimal` (`bid_evaluation/services/comparison.py:40-93`); a tie yields no recommendation (`TIE`), never an arbitrary winner. Award carries amounts as strings from the signed report (`award/services/decision.py:59`) with no recomputation. Letters format `Decimal` (`award/services/letters.py:25-34`).
- Tender security amount: server validates positive 2-dp (`tenders/services/controls.py:140-158`) and re-checks `> 0` in review (`review.py:197`). Physical security receipts validate `> 0` and scale 2 (`bid_submission/services/security_intake.py:100-101`). Note: `controls.py:158` returns `float(number)`, so the stored state value is a float, but it is only re-emitted through `Decimal(str(value))` (`bid_definition.py:87`), which round-trips at scale 2 below ~1e13.
- Currency: reservation currency is taken from the Budget (`budget_check_reserve_contracts.py:407`), line versions copy `budget.currency`, bid and report amounts are KES by template (`bid_definition.py:204`). I found no code path that mixes currencies. No code *checks* it either, e.g. `funding.compare` ignores `bid.currency`. I rate that unreachable today because the price rows are server-generated KES, not a defect.
- `Funding Reservation.original_amount`/`remaining_amount`, `Procurement Commitment.current_amount`, `approved_amount`, `authorised_total` are `non_negative` Currency fields (doctype JSON), a second line of defence against negative stored amounts. `release_reservation` clamps with `min(release_amount, remaining)` (`:137`) and rejects `<= 0` (`:138-139`).
- Header/child totals: Budget compares `authorised_total` to the sum of line amounts (`_evaluate_readiness:77-103`, with the F9 tolerance). Plan totals are always recomputed from allocations at read, with no stored derived header total that can drift. The stored `funding_line_totals_hash` is re-derived and compared by `funding_is_current` (`plan_finance.py:89-105`) via `financial_basis.current_digest`.

### 4.3 Concurrency guards found correct

- At most one Active Budget Version per Budget: DB guard (stored generated column + unique key) in `patches/bud_chg_001_v1_3_phase4_active_version_unique_index.py:25-41`, plus `approve_budget_version` supersedes the prior Active row *before* activating (`budget_readiness_contracts.py:672-680`). A double approval of the same version fails on `prior_active.save()` (`check_if_latest`), not silently.
- At most one open successor: `create_budget_successor_version` checks then inserts without a lock (`budget_contracts.py:1106-1141`), but the deterministic `generated_reference` `{budget_ref}-V{n}` is `unique` on Version and Line Version, so a racing second insert fails with a duplicate-key error (untyped; the doc's `BUDGET_INVALID_STATE` route is not returned). The guard holds by accident of the reference scheme, not by an explicit rule; recorded here so it is not mistaken for an unexamined path.
- One reservation per drawdown line: `Funding Reservation.drawdown_line_id` is `unique` (doctype JSON); the app check at `:349` is only the friendly path.
- One open Requisition per Plan Item: `open_slot_key` unique (`procurement_requisitions/services/records.py:180-196`). That also serialises concurrent drawdowns on the same Plan Item, so the stale `_drawn_totals` read at `plan_requisition.py:514` cannot double-draw across two Requisitions of one item.
- Handoff consumption: `record_handoff_consumption` locks the handoff then `doc.save()`; a second consumer fails on `check_if_latest` or `REQ_HANDOFF_CONFLICT` (`handoff.py:108-137`).
- `Budget Revision Request`: `planning_request_id` and `budget_revision_request_id` unique; receipt/withdraw/decline lock the row and `save` it (`budget_revision_request_contracts.py:100-228`).
- Plan Finance: at most one open review per Plan Version relies on `envelope.locked("Annual Plan Version")` plus a closing `bump(version)`. A racing duplicate is stopped at the version save (F12-style, fail closed).
- `FormPlanItems`: Annual Plan Version row lock then `bump(version)` (`plan_workbench.py:256-306`) serialises double allocation of one source (fail closed, untyped).
- Frappe's own protection verified: `Document.save()` → `check_if_latest` → `load_doc_before_save(for_update=True)` compares latest `modified` to the loaded copy's `modified` and raises `TimestampMismatchError` (`frappe/model/document.py:1012-1038, 1344-1353`). That is what keeps the "lock, plain re-read, check version, save" pattern from losing updates for any command that saves its locked root (Planning, REQ, Tenders, Evaluation, Award, Opening, Proceedings, Budget Version/Reservation/Request saves).
- `Budget Audit Event.idempotency_key` is unique, so a duplicate first-execution of an idempotent Budget command fails when journaling instead of double-writing (`budget_idempotency.py:50-82`; no commit inside the command functions I read).
- Strict stamps: `check_record_version`/`check_version` refuse an empty stamp in Planning (`envelope.py:102-106`), REQ (`:100-102`), Tenders (`:94-96`), Evaluation (`records.py:93-99`), Award (`:116-122`), Opening and Proceedings.

### 4.4 Latent items noted, not findings

- `kentender_core/services/business_id_service.py:52-57` calls `frappe.db.begin()` (which issues `START TRANSACTION` and implicitly commits the caller's open transaction in MariaDB, see `IMPLICIT_COMMIT_QUERY_TYPES`, `frappe/database/database.py:70`) and then `commit()`. No production caller exists (`grep generate_business_id` shows only the export), so no live effect; calling it mid-command would commit the caller's partial work.
- `budget_reference._sync_series` (`:46-57`) does an unlocked read-then-`UPDATE tabSeries SET current=<max>` that can move the counter backwards under a concurrent allocation. Only reachable when counter < existing rows (after manual deletion or restore), and the `generated_reference` unique index catches the duplicate.
- `reserve_funding` replay: the idempotency read (`:314`) happens before the line lock, so two concurrent same-key calls both proceed and the second dies on `drawdown_line_id` uniqueness (a raw `DuplicateEntryError` instead of replaying the original mapping).
- The test named "concurrent … cannot oversubscribe" (`test_bud_chg_001_phase3_check_reserve.py:140`) is sequential. Treat BUD-AC-016 / BUD18-AC-019 / BUD18-AC-047 / BUD19-AC-022 as untested.
