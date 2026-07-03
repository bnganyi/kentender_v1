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
| W6 | In Creation List | Queue-specific rows + primary action per status | ✅ Done | Package table + footer ported verbatim from the "3. In creation" design, wrapped alongside the existing Needs Planning table in one toggleable table region (`hidden` attribute, exactly one visible per active tab). Added `underlying_object_id`/`currency` backend fields needed for safe routing/currency display — same class of `id` vs `code` bug already fixed once in W5, caught here by TDD before shipping. Row primary action = title click -> `/desk/procurement-package/<underlying_object_id>` (Desk form), matching the existing demand-row pattern. Removed ~1000 lines of confirmed-unreachable legacy `PP4_*` package-grid/card code from `pp2_planning_router.js` (never called from `mount()`; a pre-iframe-pivot reimplementation orphaned by the switch to the static iframe design). Live-validated in the browser. **Correction (remaining-queues pass, see W7/W8 row below):** this entry originally stated Awaiting Review and Ready for Release also shared the In Creation table/row-template — that was an assumption made before their own designs existed. Once `4. Awaiting review` / `5. Ready for release` were supplied, byte comparison showed they have their **own** 7-column table shape (Review Status + Actions columns In Creation doesn't have), so they were moved to their own shared table/row-builder — see W7/W8. |
| W7 | Awaiting Review / Ready for Release / Blocked Queues + Resolve Paths | Queue-specific rows; show blocker reason; route user to corrective action | ✅ Done | Corrects the W6 assumption above using the newly-supplied `4. Awaiting review`, `5. Ready for release`, `6. Blocked` designs. Awaiting Review + Ready for Release share one table/row-builder (`buildWorkbenchReviewReleaseRow`) — their two source designs ship byte-identical `<thead>` column structure (verified by `test_review_release_table_column_structure_matches_across_its_two_source_designs`). Blocked gets its own table/row-builder (`buildWorkbenchBlockedRow`) with a real "Blocker Reason" pill sourced from `status_detail`; blocked rows can be a blocked *demand* or a blocked *package* (`underlying_object_type`), and navigation branches to `demand-workbench` vs `procurement-package` accordingly. Added real `readiness_status`/`readiness_tone` backend fields (replacing W6's hardcoded per-uiQueue fake tone, also improving the already-shipped In Creation readiness column) and `review_status_label` (coarse `Draft`/`In Review`/etc. — no granular sub-stage concept exists yet, flagged gap). Blocked tab now shows a real count badge ("Blocked (N)") matching its design, using existing `get_pp_workbench_queue_counts` data. Regression suite (W1–W6 + new W7/W8 source-contract + layout-guard tests) green; one pre-existing, unrelated `test_pp5_workbench_state_update_p5_008.py` data-state failure confirmed independent of this work (reproduces identically with these changes fully reverted — a test-order/seed-data issue in this environment, not a regression). **Live-validated in the browser**: Awaiting Review and Ready for Release both render their own 7-column table with real package data, correct Review Status/Readiness values, and whole-row click -> `procurement-package/<id>`; Blocked renders its own 7-column table with real "Missing approved budget link" Blocker Reason pills across all 12 seeded rows (paginated 10/page), whole-row click correctly branches to `demand-workbench/<id>` for blocked demands, and the tab shows the real "Blocked (12)" count badge. (One local-only false alarm during validation: the dev `bench start` web worker was holding a stale in-process import from before this session's backend edits, so it briefly served responses missing `underlying_object_id`; a fresh `bench execute` call proved the source was already correct, and restarting the dev server's `web` process resolved it — no code fix was needed.) |
| W8 | Released Queue + Tender Handoff | `Open Tender`, `View Evidence` from released items | ✅ Done | Own table/row-builder (`buildWorkbenchReleasedRow`) ported verbatim from the `7. Released` design (Title&Ref/Linked/Category/Est. Value/Tender Status columns); title is a real clickable `<a>` (like In Creation), routing via `procurement-package`. Added `underlying_object_id` (same `id`-vs-`code` fix pattern as W5/W6/W7 — was missing on `_recently_released_items()`) and a best-effort coarse `tender_status_label` (`tender_code` present -> "Tender Created", else the package's own status; no granular tender-status concept exists yet, flagged gap alongside W7's Review Status gap). `Open Tender`/`View Evidence` per-row actions remain **not yet wired** (no action buttons ship in the `7. Released` design's table — only the title link and Tender Status column) — flag as a follow-up if/when a design supplies them. Workbench Insights panel: heading stays static ("Workbench Insights", unchanged per user direction); only Released's own 2 insight items (ported verbatim from the design, heading excluded) are hidden-toggled in for this queue via `applyWorkbenchInsightsVariant`, every other queue keeps the existing default copy. **Live-validated in the browser**: Released tab renders its own 5-column table (correctly showing "0 to 0 of 0" — no `recently_released` rows are seeded in this environment, a pre-existing data gap, not a wiring defect) and, critically, confirms the Insights heading stays the literal static "Workbench Insights" text while the content swaps to the Released-only copy ("Handover Efficiency" / "Weekly Release Volume"); switching back to any other tab restores the default insight items. Row-click-through for a real released package could not be exercised end-to-end due to the empty seed data — flagged as a residual gap, revisit once `recently_released` seed data exists. |
| W9 | Selected Work Summary Panel | Right/inline summary panel bound to selected row, one clear next action | 🚧 **Blocked (needs design)** | The `search-and-fliter` design folder only *mentions* a "Selected Work" right panel in its `DESIGN.md` prose (380px inspector) — there is **no actual markup for it** in that folder's `code.html`, and that folder uses a different color/token system than the Workbench design, so it is not a drop-in source. Needs a dedicated mockup consistent with the Workbench design tokens. |
| W10 | Toolbar Search / Filter / Sort | Wire top and grid controls | ⏳ Pending — design status not fully verified | The Workbench's own Filter/Sort buttons exist in the shipped design (no dedicated action yet). The separate `search-and-fliter` folder is a different design pass (different color tokens) and should not be assumed reusable without confirming with the user. |
| W11 | Export + Evidence UX | Wire `Export PDF` and evidence opening behavior | ⏳ Pending | API gap: no dedicated workbench export endpoint yet (see E3 below) |
| W12 | Test + Regression Gates | Automated validation + UX contract safety across all of the above | ⏳ Pending | Backend tests + Playwright smoke + Operational Flow doc §20 no-go conditions |
| W13 | Shared Bottom Panels (Strategic Alignment + Workbench Insights) | Bind the shared bottom-panel component to live data | ⏳ Pending | Component is now shared/consistent across all 3 shipped screens (`1.`/`2.`/`3.`) but still 100% static placeholder copy in the deployed asset — see "Shared bottom-panel component" section below for the data-source questions to resolve before wiring. |

## Cross-cutting UI consistency pass (post W6–W8)

After W6/W7/W8 shipped each queue's table verbatim from its own per-queue
mockup, a follow-up pass harmonized 5 small visual elements across all 6
tables using **Needs Planning's own already-shipped markup as the canonical
reference**, intentionally superseding literal per-queue mockup fidelity for
these specific sub-elements only (everything else — column sets, Blocker
Reason, Review/Tender Status wording, etc. — is untouched and still ported
per-queue as before):

- **Title typography**: In Creation's title anchor (`text-secondary`, always
  blue) is now `text-primary hover:text-secondary` like every other table
  (dark, bold, only turns blue on hover).
- **Actions column removed**: Awaiting Review / Ready for Release / Blocked
  no longer have a separate "Actions" column with an "Open" button — their
  title cell is now a real `<a href>` (same click-to-navigate pattern already
  used by In Creation/Released), including Blocked's existing demand-vs-package
  routing branch.
- **Rows-per-page control**: all 4 tables that shared one footer block
  (In Creation/Awaiting Review/Ready for Release/Blocked/Released) now use
  Needs Planning's non-interactive `div` + `arrow_drop_down` icon instead of
  a `<select>` + `expand_more` icon (was purely decorative already — page
  size is still hardcoded at 10 in `pp2_planning_router.js` — so this is a
  markup-only fix, no pagination behavior changed).
- **Category chips**: all 5 non-Needs-Planning tables now use Needs
  Planning's dot + pill chip markup (shared via a new `applyWorkbenchCategoryChip`
  helper, replacing 5 duplicated inline class-string blocks).
- **Graceful empty state**: any table with zero rows (e.g. Released, which
  has no seeded `recently_released` data in this environment) now renders a
  fabricated (not ported — no mockup shows an empty state) icon + message row
  via a new `appendWorkbenchEmptyStateRow` helper, instead of a confusing
  bare header floating over "0 to 0 of 0".

Covered by rewritten/extended tests in `test_pp4_workbench_static_layout_guard.py`,
`test_pp4_workbench_package_queues_w6.py`, and
`test_pp4_workbench_remaining_queues_w7_w8.py`; live-validated across all 6
tabs via Playwright.

## Shared bottom-panel component (Strategic Alignment + Workbench Insights)

The "Strategic Alignment" / "Workbench Insights" panel pair beneath the main
table was originally designed as queue-specific content (different layout,
copy, and stats per queue). The user decided this is unnecessary complexity
and updated both `1. Needs planning - default/code.html` and
`2. Needs planning - selection/code.html` to ship one **identical shared
component** instead: a `md:grid-cols-2` card pair (both cards now the same
neutral `bg-surface-container-lowest` bordered style — the Insights card is
no longer a distinct navy `bg-primary-container` block), with shared copy
("Current package selection aligns 94%…", "Review Lag Detected" /
"Optimization Opportunity" insight items).

This shared component has been ported verbatim into the deployed
`needs_planning_default.html` (byte-identical to the design source, verified
by `test_pp4_workbench_static_layout_guard.py`'s
`test_deployed_design_asset_only_suppresses_duplicate_desk_sidebar`) and
live-validated in the browser.

**Update:** `3. In creation/code.html` has since also been updated by the
user to ship this same shared component (same "Strategic Alignment" /
"Workbench Insights" copy and 2-card layout), confirming the component is
now consistent across all three shipped Workbench screens.

**New wiring task — bind the shared bottom panels to live data:** the
ported component in `needs_planning_default.html` is currently 100% static
placeholder copy (hardcoded "KES 1.8B" / "KES 1.2B" alignment figures, "94%"
alignment score, "2 packages … Awaiting Review", "MOH/GDS/010" grouping
suggestion, etc.) — none of it is wired to real data yet. This needs its own
wiring item:

- **Strategic Alignment card**: alignment %, badge label (e.g. "High
  Alignment"), and the two named pillars + progress bars + KES figures need
  a live backend source. No existing API/view-model currently returns
  "strategic alignment" data for the workbench — this is a **new API gap**
  (see Design/API gaps section) unless an existing Strategy module
  (`kentender_strategy`) endpoint already models pillar-to-plan alignment
  and can be reused.
- **Workbench Insights card**: the two insight items (e.g. "Review Lag
  Detected", "Optimization Opportunity") read like computed/derived alerts
  (aging thresholds, grouping suggestions) rather than simple field lookups
  — needs a decision on whether this is real computed insight logic (new
  service) or left as illustrative/static copy for now. Flag for the user
  before implementing computed insight logic given the effort involved.
- Only wire `textContent`/attribute updates on the existing cloned/ported
  markup (same pattern as W2–W5) — never fabricate new panel markup.
- Add to the tracker as **W13 — Shared Bottom Panels (Strategic Alignment +
  Workbench Insights) wiring** once scoped; currently ⏳ Pending, not
  started, blocked on confirming the data source(s) above.

## Design gaps — needed before wiring can resume (W9)

The Workbench design pack (`docs/prompts/procurement planning v4/workbench/`)
now contains all six queue-table screens: `1. Needs planning - default`,
`2. Needs planning - selection`, `3. In creation`, `4. Awaiting review`,
`5. Ready for release`, `6. Blocked`, and `7. Released` — W6/W7/W8 are all
now shipped (see tracker above).

To unblock W9, we still need a pixel-accurate mockup (same format as the
existing screens: `DESIGN.md` + `code.html` + `screen.png`) for:

- **Selected Work Summary panel** — a persistent inspector bound to the
  currently selected row (W9). Only mentioned in prose elsewhere; no markup
  exists anywhere in the app.

Once supplied, wiring should be fast — the backend view-model
(`get_pp_workbench_item_view_model`) already returns unified, queue-agnostic
row data, and the row-clone + event-delegation wiring pattern from
W4/W5/W6/W7/W8 carries over directly.

**Follow-up gaps flagged during W7/W8** (best-effort with real data used for
now, not blocking, revisit if/when the underlying concepts get modeled):
- **Granular "Review Status"** (design shows sub-stage labels like
  "Technical Review"/"Budget Clearance"/"Final Approval") — no such concept
  exists in the backend yet; the coarse package status label is used
  instead.
- **Granular "Tender Status"** — no such concept exists yet; a coarse
  "Tender Created" / package-status label is used instead.
- **Released row actions** (`Open Tender` / `View Evidence`) — the `7.
  Released` design's table has no action buttons for these (only the title
  link + Tender Status column), so they remain unwired; needs a design
  update if/when these actions are wanted per-row.

**Also flagged, out of scope for now:** a separate `package-detail`/
`PlanningPackageDetail` surface (`mountPackageDetailSurface` and friends)
was found unreachable from `mount()` during the W6 dead-code cleanup, the
same way the `PP4_*` package-grid code was. Unlike that code, it was left
untouched since it's a larger, different surface not covered by the W6
cleanup decision — needs its own explicit decision (remove vs. wire up)
before touching it.

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

## Resumption checklist (for W9)

- [ ] Design mockup supplied for the Selected Work Summary panel
- [x] Confirm queue → API mapping: `In Creation` = `draft_packages`,
      `Awaiting Review` = `needs_review`, `Ready for Release` =
      `ready_to_release`, `Blocked` = `blocked`, `Released` =
      `recently_released` — all six wired (W1–W8 complete)
- [x] Re-run `test_pp4_workbench_static_layout_guard.py` after each new
      wiring pass to confirm no fabricated markup was introduced (green
      through W7/W8)
- [x] Live Playwright/browser validation for the 4 newly-wired tabs
      (Awaiting Review, Ready for Release, Blocked, Released) — done; see
      W7/W8 evidence above
