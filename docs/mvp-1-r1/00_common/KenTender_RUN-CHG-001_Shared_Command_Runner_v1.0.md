# KenTender RUN-CHG-001 — Shared Command Runner & Stale Optimistic-Lock Stamp, v1.0

Status: **In progress** (started 2026-09-11). Cross-cutting; fixes a defect
class found independently in Budget and Departmental Needs on 2026-09-11 and
then confirmed latent or live across every other Vue-in-Desk screen that
sends an optimistic-lock stamp with a write command.

## 1. The durable rule

> A command's post-mutation reload — the thing that refreshes the
> optimistic-lock stamp the next command will send — must be awaited *inside*
> the same async function whose pending flag guards the buttons. Never after
> that guarded call has already returned.

## 2. The root cause

Every Vue-in-Desk screen with mutating commands hand-copied a local `run()`
wrapper: guard re-entry on `pending`, set `pending = true`, run the command,
catch and surface any error, `finally { pending = false }`. That shape is
correct in isolation. The defect was always at the call site, one layer up:
`await run(fn); await load({ quiet: true });` — the reload runs *after*
`run()` already returned and cleared `pending`, so a second command fired in
that window reads the pre-save `record_version` / `expected_version` /
`modified` stamp from local state and is refused as a stale write (or, worse,
an edit made in that window is silently reverted when the stale reload
finally lands).

Confirmed live 2026-09-11:
- **Departmental Needs** — Save draft followed immediately by Submit for
  review was refused as a stale write with nobody else editing.
- **Budget & Funding** — an owner-scope edit made in that window was silently
  reverted by the delayed reload ("Owner scope lost on save").

Both were root-caused and fixed same-day, independently, with two different
tactics (Budget: await the reload inside the saving window; Needs: stamp the
version directly from the save response) — see each module's own
`IMPLEMENTATION_TRACKER.md` 2026-09-11 defect-pass entry. Surveying every
other screen with the same `run()`-then-reload shape found the identical
latent defect in Procurement Planning, Procurement Requisitions, Tender
Preparation, and one **not previously reported, already-live** instance in
System Setup's `ProcuringEntityTab.vue` (a second Save fired quickly enough
reads a stale `expected_version` from a parent prop the first save's
`refreshSite()` hadn't finished repopulating). Strategy, System Setup's other
three tabs, and STD Configuration were already safe — each independently
happened to await its reload before clearing `pending`.

The durable fix is in the runtime `kentender_core.desk_page` provides, not
per-screen discipline restated in a spec: a shared command-runner primitive
so the pending-guard shape is written once, and an explicit AGENTS.md §6.4
rule making "reload inside the guarded function" mandatory rather than an
unenforced convention.

## 3. Service contract (kentender_core)

`kentender_core/kentender_core/public/js/kt_desk_page.js` — two additions,
following the same "pass your own bundle's Vue instance in" shape as
`useRoute(vue, pageSlug)`, since no Vue runtime is shared across bundle
boundaries (AGENTS.md §6.6):

- **`createCommandRunner(vue, opts)`** → `{ pending, run(fn, actionLabel) }`.
  `pending` is a `vue.ref(false)` the template binds to disable buttons.
  `run()` refuses re-entry while `pending` is true, awaits `fn(key)`, and
  clears `pending` in a `finally` — same contract every hand-copied `run()`
  already had. `opts.onStart(label)` / `opts.onError(err, label)` keep each
  screen's own error-surface convention (inline banner vs. dialog field);
  `opts.mintKey(label)` keeps each screen's own idempotency-key convention.
  All three are optional. **The fix this enables is entirely about what the
  caller puts inside `fn`**: the post-mutation reload belongs as the last
  `await` inside `fn`, before `run()`'s `finally` fires — not as a separate
  call after `run()` returns.
- **`createSequenceGuard()`** → `{ next(), isCurrent(token) }`. The "every
  loader carries a sequence token" obligation AGENTS.md §6.4 already
  documented, now a two-line utility instead of a hand-rolled
  `let request = 0` counter per screen.

Neither primitive unifies error-display or idempotency-key conventions
across modules — those stay screen-owned via the `opts` hooks, deliberately,
because Departmental Needs (dialog-field vs. inline-banner errors) and
Tender Preparation (`inline`/`dialogError` split) have real, different
presentation needs that a forced one-shape core function would have
regressed.

## 4. Per-module status

| Module | Before | Fix |
|---|---|---|
| Departmental Needs | Fixed 2026-09-11 (own tactic: stamp version from save response) | Not re-touched by this change; already correct |
| Budget & Funding | Fixed 2026-09-11 (own tactic: await reload inside saving window) | Not re-touched by this change; already correct |
| Strategy | Already safe (every call site already awaits its reload before `finally`) | No functional change |
| System Setup — Fiscal Years / Organisation Structure / User Responsibilities tabs | Already safe | No functional change |
| STD Configuration (package/readiness) | Already safe | No functional change |
| **System Setup — `ProcuringEntityTab.vue`** | **Live defect** — second Save reads stale `expected_version` from a parent prop the first save's un-awaited `refreshSite()` hadn't repopulated | Fixed: `SystemSetup.vue`'s `refreshSite()` awaited before `ProcuringEntityTab.vue` clears `busy` |
| **Procurement Planning** (10 commands) | Latent | Reload moved inside each command's guarded function; loader sequence-guarded |
| **Procurement Requisitions** (13 same-screen-reload commands) | Latent | Reload moved inside each command's guarded function; loader sequence-guarded |
| **Tender Preparation** (4 same-screen-reload commands: save, readiness, add/remove evidence) | Latent | Reload moved inside each command's guarded function; loader sequence-guarded |

Each fixed module gets one route-delayed Playwright test (intercept the
screen's own reload endpoint, delay it past the save's round trip, fire the
save then immediately the next command, assert no stale-write refusal and no
silently reverted edit) — same pattern as Budget's
`BUD-DES-03` / Needs' `"Submit for review straight after Save draft..."`
tests added 2026-09-11.

## 5. Follow-ups

- **RUN-FU-01** — Departmental Needs, Budget, Strategy, System Setup's three
  already-safe tabs, and STD Configuration still hand-roll their own local
  `run()` rather than calling `createCommandRunner`. They are behaviourally
  correct today; migrating them onto the shared primitive is a pure
  consistency cleanup (removes the last per-screen reinventions so a future
  screen has one obvious thing to copy) with no bug attached. Deliberately
  out of scope for this pass to avoid refactor risk on working code; do it
  opportunistically the next time one of those screens is touched for an
  unrelated reason.
