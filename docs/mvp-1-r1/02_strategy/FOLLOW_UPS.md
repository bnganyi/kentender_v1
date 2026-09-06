# Strategy Alignment (STR-CHG-001 v1.7) — open follow-ups

Items deliberately left open once implementation phases closed on 2026-09-06.
Each entry is recorded because it is real, not because it is planned for a
particular date. Mirrors `docs/mvp-1-r1/01_departmental_needs/FOLLOW_UPS.md`
and `docs/mvp-1-r1/04_planning/FOLLOW_UPS.md`.

---

## FU-01 — Design-fidelity gate against STR-DES-01..10 (STR-703, STR-AC-025)

**Status:** Open.
**What:** `make ui-strategy-gate` proves rendering, copy, behaviour and the
§10 routes in a real browser, but no automated check compares the three live
screens against the approved `.dc.html` artboards the way System Setup's
fidelity spec does. The behaviour half of STR-AC-025 is evidenced; the
"match their approved static designs" half is not.
**Why it matters:** §11 governs visual fidelity; without a gate, drift is
only caught by eye.
**Path:** clone the System Setup fidelity pattern into
`tests/ui/smoke/strategy/strategy-fidelity.spec.ts` and add
`make ui-strategy-fidelity-gate`.

## FU-02 — "Approval tasks" workspace shortcut is visible to every module user

**Status:** Open (framework limitation, recorded).
**What:** Frappe Workspace shortcuts carry no role restriction, so the
Strategy Management workspace's "Approval tasks" shortcut (opens
`/app/strategy/my-work`) is shown to Authors and Auditors too. The route it
opens is gated as data: a non-Approver sees only what they may act on (an
Author's own Drafts, nothing for an Auditor), never a permission modal.
**Why it matters:** KT-STD-001 §3A is satisfied (no modal, no disclosure) but
the entry point is slightly noisier than §12.1 implies.
**Path:** either accept as-is or replace the shortcut with a My Work provider
hook (the pattern NDS adopted for review queues) once one exists for Strategy.

## FU-03 — `_Test Fiscal Year` rows appear in the target-period picker on a dev site

**Status:** Open (dev-site data, not a code defect).
**What:** `list_available_fiscal_years(plan_id)` offers every enabled ERPNext
Fiscal Year overlapping the plan period. Frappe's test-record Fiscal Years
(`_Test Fiscal Year 20xx`) satisfy that rule on `kentender.midas.com`, so the
Add-target dialog lists them beside `2027-2028`.
**Why it matters:** cosmetic on a dev site; a production site has no such
rows. Filtering them by name would be a name-based special case (§17).
**Path:** delete the test Fiscal Years from the dev site when they are no
longer needed by other apps' tests.

## FU-04 — Portfolio filters live in component state, not in the URL

**Status:** Open (accepted for v1.7).
**What:** Search, role and status filters on the Portfolio survive tab
switches and screen changes because the screen is KeepAlive'd, but they are
not encoded in the route, so a reload or a shared link does not carry them.
**Why it matters:** §10's route table defines no filter segments, so this is
spec-conformant; recorded because a future reader may expect deep-linkable
filters.

## FU-05 — Dev server with a dead stdout pipe turns every validation error into a Werkzeug 500

**Status:** Open (operational note).
**What:** When `bench serve` is started from a shell that later exits, its
stdout becomes a dead pipe; `frappe.errprint` then raises `BrokenPipeError`
inside error handling and every `frappe.throw` reaches the browser as an HTML
500 instead of a typed JSON error. This looked exactly like an application
defect during the browser pass.
**Path:** start the dev server with
`nohup bench serve --port 8000 > logs/serve.log 2>&1 &` from the bench root;
if inline errors suddenly become "Server Error" dialogs, check `serve.log`
for `BrokenPipeError` before debugging application code.

## FU-06 — Audit events for downstream listing/lineage reads are not emitted

**Status:** Open.
**What:** §13 lists "successful and failed context resolution" and
"Strategic Objective listing and lineage reads by a downstream module" among
the append-only events. Every workflow action (plan/successor creation, Draft
saves, submit, return, approve, supersede) and snapshot creation are audited
with the business role and the exercised assignment; `resolve_strategy_context`,
`list_strategy_objectives` and `get_strategy_lineage` reads are not.
**Why it matters:** the trail is complete for every mutation and for the one
read that creates a durable correlation (the snapshot); read events are
high-volume and were left out pending a decision on audit retention.
**Path:** add `record_event(...)` calls carrying the calling module in
`strategy_consumer.py` once the retention policy for read events is set.

---

## Verifying a fix

When a follow-up above is later addressed, do not delete the entry — mark it
resolved with the date, the change that closed it, and the evidence (test name
or command output), mirroring how the NDS and Planning registers record
resolution. Keep the original "why it matters" text so a future reader
understands what was being traded off, even after the fix lands.
