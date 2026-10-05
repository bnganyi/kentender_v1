# Home provider conventions (Phase 3)

Date: 4 October 2026. Written from the Phase 2 core (`kentender_core/services/home_*.py`, built and tested) and four read-only surveys of the owners. Every owner provider is built to this page, so the nine are alike.

## 1. Contract

- File: `<owner>/services/home_provider.py`, one function `entries(*, user, region)`. Registered on the owner app's `hooks.py` as one line `kt_home_providers = [...]` (append to an existing list if there is one). The working tree already carries other people's edits to `hooks.py`; touch only that line.
- `region` is one of `my_work`, `coming_up`, `waiting`, `oversight`, `completed`. Return:
  - `None`: the region does not apply to this actor in this module (no responsibility that gives it);
  - `[]`: applies, nothing to show now;
  - a list of `home_entries.make(...)` entries;
  - or raise: that is a failed read, which Home shows honestly. Never return `[]` to hide an error.
- Applicability is decided by **responsibility**, not by having rows. Waiting and My work apply to anyone who holds a responsibility in the module; oversight applies only to an actor with an oversight-capable responsibility there. Otherwise Brian would show "0 records with outstanding matters" (HOME §10B shows no oversight column for him).
- Core never calls a provider for a technical reader (Administrator, System Manager, Technical Operator). A provider need not re-check, but must not break if called for one.

## 2. Rules every provider follows

1. **Use `user`, never `frappe.session.user`.** Several owner reads take the session user implicitly (Strategy's `_my_work_versions`, Requisitions' `get_requisition_workspace`, `frappe.get_list` without `user=`); reimplement with the explicit user.
2. **Read only.** `frappe.db.transaction_writes` must not change across a provider call; each provider has a test for it. Do not call: `dpp_read.get_departmental_plan` (refreshes draft entries), Needs `workspace.get_workspace` (persists context), Tenders `cancellation.refresh_obligation_statuses`, `records.require_root(lock=True)` (use `lock=False`), anything named `refresh_*`, `sync`, `heartbeat`, `sweep_*`. Reading through `frappe.log_error` only on failure is the existing pattern; prefer `frappe.logger`.
3. **Memoise the scan.** Core calls once per region (up to five calls per read). Put the owner's expensive scan behind `home_support.memo("<owner>", build, user=user)` so it runs once per read.
4. **Raw instants.** Pass datetimes or dates from the database to `make()`. Never pass a display string (Needs `received_at`, Planning's final loop and Budget's `requested_at_display` are strings). A date-only deadline is a `date`; an instant is a `datetime`.
5. **Business title leads; reference is secondary.** `title` is the record's own title (tender title, need title, plan title, requisition title, budget title). `reference` is the business reference (TND-…, never a case or task name). `action` is the action phrase without the reference.
6. **Owner action wording is fixed by the spec** where it names one: Authorise requisition; Appoint the evaluation committee; Consider cancellation; Authorise publication; Decide award; Prepare professional opinion; Resolve notice delivery; Respond to clarification; Record cancellation notices and PPRA report; Start opening; Evaluation deadline; Decide whether this requirement is available to Procurement Planning. Other rows use the owner's existing action wording with the reference removed. Keep the wording in one table per owner.
7. **`action_id` is stable and shared.** Build it once per row kind (the task name, `<case>:<key>`, a version name). The My work row and the oversight row for the same matter use the same `action_id`, so Home de-duplicates an actor who both holds and oversees it (identity is owner + root + action_id).
8. **Blocked.** Set `blocked=True` and `reason` only where the owner's own answer says so (`next_step` kind `your_turn_blocked`, or the owner's guard text). Use the owner's headline as the reason. Never invent a blocker.
9. **Waiting.** `action` reads "Waiting for {names} to {verb phrase}" (spec: "Waiting for Amina Hassan to decide publication"); `holder` is the person or role display; `since` is the real hand-off instant. A waiting entry without a `since` is dropped by core and makes the region partial, so compute one or skip the row and log it.
10. **Oversight.** Read-only. Return only rows the actor may read under the owner's disclosure rule (OVS): never bypass it (Evaluation before delivery is status-only; a Head of User Department sees the neutral projection). Every row has `since`. Set `outstanding=True` for an outstanding matter (the summary column counts those); other disclosed updates are optional and `outstanding=False`. Owners with no outstanding concept return `None` for oversight and the reason is logged in the tracker.
11. **Coming up.** Only owner-recorded Scheduled answers or deadlines the actor holds, attends, chairs or oversees. Core applies the 14-day window and drops anything already in My work. An owner with none returns `None`.
12. **Completed.** Built from the owner's own decision rows (FU-HOME-13): `actor = user`, instant on or after `home_time.COMPLETED_DAYS` ago (use a plain cutoff in the query), re-check that the actor may still read the record, build the sentence with `home_time.completed_sentence(did, at, follow=...)`. Append `home_time.awaiting(stage, holder)` only when the owner's current answer for the actor is *waiting* with a holder (FU-HOME-24). Keep a whitelist of decision values to a verb phrase ("approved this Tender package"); ignore anything not on it.
13. **Destination.** `{"route": [...], "route_options": {...}}` with a first segment that is a real Frappe Page the viewer's roles may open (`tenders`, `award`, `procurement-requisitions`, `departmental-needs`, `procurement-planning`, `annual-procurement-plan`, `departmental-procurement-plan`, `budget-funding`, `strategy`). Bid Opening and Evaluation have no Page of their own: their routes start with `tenders`. Core drops an entry whose first segment is not a permitted Page and marks the region partial, so a test asserts the Page exists.
14. **Dependency direction.** Core imports no owner. Budget and Strategy import nothing from `kentender_procurement`. Within procurement, avoid new edges (a local helper beats a cross-module import).

## 3. Tests every provider ships

`<owner>/tests/test_home_provider.py` on `kentender-test.local`, using the owner's shared world (never one world per test):

- each region the owner supplies: a positive case with the exact title, action, timing fields and destination;
- `None` versus `[]` for an actor with and without the responsibility;
- a persona negative case through `home_workspace.get_workspace(user, providers=[entries])`: a user without the role sees none of the entry, and a revoked or expired responsibility removes it;
- the technical reader and an unrelated internal user;
- `frappe.db.transaction_writes` unchanged;
- the destination's first segment exists as a Page;
- cleanup: every fixture row removed afterwards (project rule), checked by count.

Run the focused test module red then green, then the owner's own module tests **once** for the module whose code you touched. Do not run other modules' tests unless a shared dependency changed. Never run while a Playwright run is active (`make home-preflight`); runs on this site collide intermittently, and a lock-wait error means rerun.
