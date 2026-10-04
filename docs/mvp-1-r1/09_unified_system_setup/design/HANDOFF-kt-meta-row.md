# Handoff — `.kt-meta-row` left-bunching (Industry design system)

**Where:** `styles.css`, section `/* ── New pattern: page sections ── */`, line ~593
**Applies to:** the Industry design system source project, not this one. Already patched in this
project's bound copy at `_ds/kentender-industry-82d82607-fd52-491b-bef1-023d4ec3bd0c/styles.css`.

## Problem

`.kt-meta-row` is the system's standard fact row (label over value — "Record kind / Rule / Version",
"Days counted / Working-day calendar", etc.). It is declared as a shrink-to-fit flex row:

```css
.kt-meta-row { display: flex; gap: var(--space-6); flex-wrap: wrap; align-items: flex-end; }
```

Every child sizes to its own text, so a row of two or three facts occupies ~35% of a full-width
panel and the rest is dead space. The guide calls for "equal cells, strong horizontal and vertical
rhythm"; a flex row cannot produce equal cells. Because `.kt-meta-row` is the fact primitive used on
virtually every detail surface, the symptom appears on every page, and consuming projects have been
patching it per-page with ad-hoc grid overrides. This is a system defect, not a page defect.

## Fix

```css
.kt-meta-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: var(--space-4) var(--space-6); align-items: end; }
.kt-meta-row.is-tight { display: flex; flex-wrap: wrap; }
.kt-meta-row > div { display: flex; flex-direction: column; gap: 4px; }   /* unchanged */
```

- `auto-fit` + `1fr` gives equal cells across the container's real width and reflows to fewer
  columns as the panel narrows — no media query needed.
- `minmax(160px, …)` keeps a long label (e.g. "Effective dates and amendments") from fracturing
  while still allowing three or four columns at panel width.
- `align-items: end` preserves the existing baseline-ish alignment when labels wrap to two lines.
- `.is-tight` is the opt-out for the genuine inline case — two short facts that should sit together
  rather than span the panel (chip rows, a single "Result" fact). Existing markup keeps working by
  adding one class.

## Also update

1. `components/sections.html` — the `.kt-meta-row` specimen currently shows three facts in a narrow
   panel, which hides the bug. Widen the specimen panel to full width and add a second specimen
   using `.is-tight` so the two behaviours are documented side by side.
2. `readme.md` — the `.kt-section / .kt-panel / .kt-meta-row` table row should note that
   `.kt-meta-row` distributes facts as equal grid cells, and that `.is-tight` is the inline variant.
3. `theme.json` — no token change; the fix uses existing `--space-4` / `--space-6`.

## Regression check

Pages using `.kt-meta-row` inside a narrow container (dialogs, `.kt-record-detail`, sidebar panels)
now get one or two columns instead of an inline run. Spot-check `components/record.html` and
`components/dialog.html`; where the inline run was intended, add `.is-tight`.

## Broader note

The same shrink-to-fit pattern is worth auditing on `.kt-record-meta` and `.kt-topbar-right`, but
those are genuinely inline runs (chips, icon buttons) and are correct as flex. `.kt-meta-row` was
the only fact-grid primitive mis-declared as a flex row.
