# Planning Workbench — Wiring Tracker (W1–W12)

## Goal

Ship the new Planning Workbench screen (`/desk/procurement-planning`, iframe-embedded
static design) with full functional wiring against live Procurement Planning
APIs — with **zero visual drift** from the approved designs — following the
Operational Flow doc (`../Procurement Planning — Operational Flow, States, and
UX Rules.md`) and the same pattern already proven on the Budget/DIA hubs:
implement the static design pixel-perfect first, then wire behavior only by
mutating the design's own DOM nodes (never fabricating new markup, headers,
or panels the design doesn't already contain).

This file is the persistent, canonical record of that tracker so wiring
status and design gaps survive across sessions (the tracker was originally
only presented in chat and never checked in — this file replaces that).

## Status legend

- ✅ Done — implemented, tested, live-validated
- 🚧 Blocked (needs design) — backend/API ready, but no pixel-accurate
  mockup exists yet for the rows/panel this item wires
- ⏳ Pending — not started, not yet blocked (design status not fully verified)

## Tracker

| # | Item | Scope | Status | Notes |
|---|------|-------|--------|-------|
| W1 | Shell State + Route Contract | Single workbench state model (`queue`, `item`, `plan`, filters, sort, page) + URL sync | ✅ Done | `pp2_planning_router.js` — `readWorkbenchStateFromUrl`/`writeWorkbenchStateToUrl`/`canonicalizeWorkbenchStateQuery` |
| W2 | Active Plan Context + Gate | Render active plan card; enforce no-active-plan gate | ✅ Done | `get_pp_active_plan_view_model`; non-visual alert + redirect to Planning Hub when no active plan |
| W3 | Queue Tabs + Counts | Wire live counts into the 6 queue tabs; active-tab toggle + URL state | ✅ Done | `get_pp_workbench_queue_counts` |
| W4 | Needs Planning List (Primary Screen) | Bind table rows to approved-demand queue payload | ✅ Done | `get_pp_approved_demands_awaiting_planning`; rows cloned from the design's own pristine `<tr>` |
| W5 | Needs Planning Actions | `Add to Active Plan`, `Create Package`, `View Demand` | ✅ Done | Floating selection toolbar ported verbatim from the companion "2. Needs planning - selection" design; `include_pp_demand_in_procurement_plan`, `create_pp_package_from_planning_inclusion`. Fixed a bug where row selection cached `demand.id` (internal Frappe name) instead of `demand.code` (business code) for the API payload — every real "Add to Active Plan"/"Create Package" call failed with "Journey code could not be resolved" until this was corrected; regression test added. Live-validated end-to-end through the actual UI after the fix (both actions succeed, package created). |
| W6 | In Creation / Awaiting Review / Ready for Release Lists | Queue-specific rows + primary action per status | 🚧 **Blocked (needs design)** | Backend ready: `get_pp_workbench_item_view_model(queue="draft_packages"\|"needs_review"\|"ready_release")` returns unified, already-normalized rows (title, category, value, status, next action). **No mockup exists** for package-queue rows — the only shipped table design (`1. Needs planning - default`) is demand-shaped (header literally reads "Demand Title & Ref"), which would misrepresent package rows if reused as-is. Needs a dedicated screen/row mockup before wiring. |
| W7 | Blocked Queue + Resolve Paths | Show blocker reason; route user to corrective action | 🚧 **Blocked (needs design)** | Backend ready: `get_pp_workbench_item_view_model(queue="blocked")`. No blocked-queue mockup exists in `docs/prompts/procurement planning v4/workbench/`. |
| W8 | Released Queue + Tender Handoff | `Open Tender`, `View Evidence` from released items | 🚧 **Blocked (needs design)** | Backend ready: `get_pp_workbench_item_view_model(queue="recently_released")`, `get_pp_released_to_tender`, `get_pp_released_package_summary`. No released-queue mockup exists. |
| W9 | Selected Work Summary Panel | Right/inline summary panel bound to selected row, one clear next action | 🚧 **Blocked (needs design)** | The `search-and-fliter` design folder only *mentions* a "Selected Work" right panel in its `DESIGN.md` prose (380px inspector) — there is **no actual markup for it** in that folder's `code.html`, and that folder uses a different color/token system than the Workbench design, so it is not a drop-in source. Needs a dedicated mockup consistent with the Workbench design tokens. |
| W10 | Toolbar Search / Filter / Sort | Wire top and grid controls | ⏳ Pending — design status not fully verified | The Workbench's own Filter/Sort buttons exist in the shipped design (no dedicated action yet). The separate `search-and-fliter` folder is a different design pass (different color tokens) and should not be assumed reusable without confirming with the user. |
| W11 | Export + Evidence UX | Wire `Export PDF` and evidence opening behavior | ⏳ Pending | API gap: no dedicated workbench export endpoint yet (see E3 below) |
| W12 | Test + Regression Gates | Automated validation + UX contract safety across all of the above | ⏳ Pending | Backend tests + Playwright smoke + Operational Flow doc §20 no-go conditions |

## Design gaps — needed before wiring can resume (W6–W9)

The Workbench design pack (`docs/prompts/procurement planning v4/workbench/`)
currently only contains two screens, both for the **Needs Planning** queue:

1. `1. Needs planning - default`
2. `2. Needs planning - selection`

To unblock W6–W9, we need pixel-accurate mockups (same format as the two
above: `DESIGN.md` + `code.html` + `screen.png`) for:

- **Package queue rows** — used by "In Creation", "Awaiting Review", and
  "Ready for Release" tabs (W6). These are `Procurement Package` records,
  not demands, so column semantics (title, category, value, status) differ
  from the Needs Planning table.
- **Blocked queue rows** — demands or packages with a blocker reason and a
  corrective-action route (W7).
- **Released queue rows** — released packages with `Open Tender` / `View
  Evidence` actions (W8).
- **Selected Work Summary panel** — a persistent inspector bound to the
  currently selected row (W9). Only mentioned in prose elsewhere; no markup
  exists anywhere in the app.

Once these are supplied, wiring should be fast — the backend view-model
(`get_pp_workbench_item_view_model`) already returns unified, queue-agnostic
row data for all of W6/W7/W8, and the row-clone + event-delegation wiring
pattern from W4/W5 carries over directly.

## API Enhancement Backlog (targeted)

- **E1 — Workbench query contract expansion**: add optional `search`,
  `department`, `category`, `value_range`, `created_from`, `created_to`,
  `sort`, `start`, `limit` to the unified queue API. *(Note: these params
  already exist on `get_pp_workbench_item_view_model` — verify before
  treating as a gap when W10 is picked up.)*
- **E2 — Filter metadata endpoint**: facet options/counts for current
  queue/plan scope.
- **E3 — Workbench export endpoint**: explicit export API for PDF (and
  optionally CSV) for the current queue/filter state. Needed before W11.
- **E4 — Request Revision action** (if included in Workbench scope): align
  workflow/status/API if required.

## Resumption checklist (for W6–W9)

- [ ] Design mockups supplied for package-queue rows, blocked-queue rows,
      released-queue rows, and the Selected Work Summary panel
- [ ] Confirm queue → API mapping: `In Creation` = `draft_packages`,
      `Awaiting Review` = `needs_review`, `Ready for Release` =
      `ready_release`, `Blocked` = `blocked`, `Released` = `recently_released`
- [ ] Re-run `test_pp4_workbench_static_layout_guard.py` after each new
      wiring pass to confirm no fabricated markup was introduced
- [ ] Live Playwright validation on `kentender.midas.com` per queue
