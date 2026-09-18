# KenTender Industry — base design system fix requests

Raised from the Procurement Requisitions (REQ-CHG-001 §13) artboard work. These are defects in
the design system itself, not in the consuming project. Each has been patched locally in
`_ds/kentender-industry-<id>/styles.css` in the KenTender Requisitions v2 project; the same change
needs to land upstream or it will reappear in every new project that binds this system.

---

## DS-FIX-001 — `.kt-kpi-card` has no visible top border in its neutral state

**Severity:** visible defect on every page that uses a KPI row.

**Where:** `styles.css`, KPI card component block.

**Current source**

```css
.kt-kpi-card { position: relative; background: var(--color-surface); border: 1px solid var(--color-divider); border-top: 3px solid transparent; padding: var(--space-4); display: flex; flex-direction: column; gap: var(--space-2); }
.kt-kpi-card.is-attention { border-top-color: var(--status-attention); }
.kt-kpi-card.is-critical  { border-top-color: var(--status-critical); }
.kt-kpi-card.is-live      { border-top-color: var(--status-live); }
```

**The defect**

The `border-top: 3px solid transparent` exists to reserve space so that a card gaining a state
accent does not shift layout. But it also overrides the `1px solid var(--color-divider)` top edge
from the shorthand on the line before it. A KPI card with no state — which per the guide is the
default and most common case, since the top accent "appears only past a threshold" — therefore
renders with hairline left, right and bottom edges and **nothing at all across the top**. It reads
as an unfinished box.

This has been reported and hand-patched in three separate sessions on this product. It is worth
fixing at the source.

**Fix applied locally**

```css
.kt-kpi-card { position: relative; background: var(--color-surface); border: 1px solid var(--color-divider); padding: var(--space-4); display: flex; flex-direction: column; gap: var(--space-2); }
.kt-kpi-card.is-attention { box-shadow: inset 0 3px 0 var(--status-attention); }
.kt-kpi-card.is-critical  { box-shadow: inset 0 3px 0 var(--status-critical); }
.kt-kpi-card.is-live      { box-shadow: inset 0 3px 0 var(--status-live); }
```

**Why this shape of fix**

- The hairline border is restored on all four edges, so the neutral card is a complete blueprint
  object like every other framed component in the system.
- The state accent moves to an inset box-shadow drawn *inside* the top edge. It occupies no layout
  space, so the no-shift property that motivated the transparent border is preserved without
  costing the border.
- Nothing else changes: the accent is still 3px, still the same three status hues, still top-edge
  only, still absent in the neutral state.

Alternative considered and rejected: keeping `border-top: 3px` and setting its default colour to
`var(--color-divider)`. That gives the neutral card a 3px grey slab on top and a 1px hairline
elsewhere, which breaks the uniform-hairline rule the system states for framed objects.

**Media hardening added at the same time**

The KPI card was the only recent component block with no `forced-colors` or `print` rule, so
the state accent would have vanished in Windows High Contrast (where tinted fills collapse) and
printed as an unlabelled grey bar. Added, following the pattern used by `.kt-notice` and
`.kt-record`:

```css
@media (forced-colors: active) {
  .kt-kpi-card { border-color: CanvasText; }
  .kt-kpi-card.is-attention, .kt-kpi-card.is-critical, .kt-kpi-card.is-live { box-shadow: none; border-top: 3px solid CanvasText; }
}
@media print {
  .kt-kpi-card { border-color: #000; box-shadow: none; }
  .kt-kpi-card.is-attention, .kt-kpi-card.is-critical, .kt-kpi-card.is-live { border-top: 3px solid #000; }
}
```

Note that in both hardened contexts the accent falls back to a real `border-top`, which does
reintroduce a 2px layout shift — acceptable there, since the alternative is losing the state
signal entirely, and neither context is where layout stability matters.

**Documentation to update alongside the code**

`readme.md`, components table, KPI row — currently reads "top accent + dot appear only past a
threshold". The dot was removed system-wide in an earlier revision, so this line is already stale.
Suggested replacement: "Summary metric card; a top accent bar appears only past a threshold."

**Verifying the fix**

Open `components/kpi.html`. The first card in the row carries no state class. All four of its edges
should be hairline `--color-divider`. The `is-attention` / `is-critical` / `is-live` cards should
each show a 3px accent inside the top edge, and all four cards should sit on the same baseline with
identical heights.

---

## DS-FIX-002 — `.tag` breaks mid-label in narrow containers

**Severity:** layout defect wherever a tag sits in a constrained column.

**Where:** `styles.css`, tags block.

**The defect**

`.tag` sets `display: inline-flex; align-items: center` but no `white-space`, so it inherits
`normal`. A two-word label ("Open Tender", "IT Equipment") placed in a narrow container — a table
cell, a sidebar, a card column — breaks across two lines *inside the chip*, doubling its height to
~45px and reading as clipped text rather than a label. Observed in a 310px-wide first table cell.

A chip is a single atomic label by definition; it should wrap as a unit or not at all, and it is
the consumer's job to wrap the *row* of tags, not the system's to let each chip fracture.

**Fix applied locally**

```css
.tag {
  display: inline-flex; align-items: center; white-space: nowrap; font-size: 11px;
  letter-spacing: 0.02em; padding: 3px 10px;
  /* …unchanged… */
}
```

Consumers remain responsible for adding `flex-wrap: wrap` to a row holding several tags, so the
tags reflow whole. Worth a line in the readme's tag row to say so.

---

## DS-FIX-003 — `.btn` labels fracture mid-label in narrow containers

**Severity:** layout defect wherever a button sits in a constrained column. Same root cause as
DS-FIX-002.

**Where:** `styles.css`, buttons block.

**The defect**

Identical to the tag defect: `.btn` sets `display: inline-flex; align-items: center;
justify-content: center` but no `white-space`, so it inherits `normal`. A multi-word action name
placed in a narrow container — most commonly a table Action cell — breaks across lines inside the
button, rendering it at 49px tall instead of ~32px. Observed with `Start requisition` in a 122px
cell (two lines) and `Edit quantity and use` in a 100px cell (three lines).

An action name is atomic. A button should size itself to its label and let the *container* deal
with the consequence, rather than silently shredding the label to fit.

**Fix applied locally**

```css
.btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px; white-space: nowrap;
  cursor: pointer; text-decoration: none;
  /* …unchanged… */
}
```

**Consequence consumers must handle**

With `nowrap` the button now reports a real intrinsic width, so a too-narrow column will widen
rather than hide the problem. That is the correct trade — the pressure becomes visible at design
time instead of shipping a fractured label — but it means a table with several long action names
needs either a wider Action column, shorter labels, or icon buttons. Both DS-FIX-002 and DS-FIX-003
are worth a sentence in the readme: *chips and buttons never wrap internally; wrap the row, widen
the column, or shorten the label.*

---

## Notes for whoever picks this up

The local patch is in the KenTender Requisitions v2 project at
`_ds/kentender-industry-82d82607-fd52-491b-bef1-023d4ec3bd0c/styles.css` — search for
`New component: KPI card` (DS-FIX-001), `— tags —` (DS-FIX-002) and `— buttons —` (DS-FIX-003).
Copying those blocks upstream verbatim is sufficient; no token changes and no `theme.json` changes
are involved, since all three fixes use only variables that already exist.

DS-FIX-002 and DS-FIX-003 are one defect class — a component that should treat its label as atomic
inheriting `white-space: normal`. Worth a sweep for others in the same family (`.kt-status`,
`.seg-opt`, `.kt-nav-item`, `.kt-breadcrumb`) while the fix is being applied, rather than waiting
for each to surface in a consuming project the way these two did.
