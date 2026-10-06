# Industry design system

Industry is KenTender's working surface inside Frappe Desk. Pages sit on Frappe's own light grey ground as one white sheet with a thin border; inside the sheet, regions are separated by headings, spacing and 1px rules, never by tinted fills. Surfaces, controls, radii, text colours and the Inter font are Frappe v16's own variables, read and never overridden (KT-STD-001 v1.22 §2.4). Warmth comes from royal indigo actions, large result figures, colour-by-meaning charts and one outline icon per module. Revision DS-REV-002.

## How to use this

- Link the one stylesheet from every page — `<link rel="stylesheet" href="styles.css">` (adjust the relative path) — and take every color, font, spacing, radius and shadow from its variables (`var(--color-*)`, `var(--font-*)`, `var(--space-*)`, `var(--radius-*)`, `var(--shadow-*)`). Never hard-code a hex, a font name or a px value the tokens already carry.
- Build with the classes below rather than inventing parallel ones; the component pages are plain HTML, so view source and copy the markup.
- `templates/` holds starting points a consuming project can copy whole.
- The whole system was derived from `theme.json`. To change the look, edit the tokens at the top of `styles.css` — every page, the thumbnail and this guide read from them — and keep `theme.json` and the written guidance in step so they don't drift from what the CSS actually does.

## Direction

A KenTender page is one white sheet (`.kt-page`: `--color-surface`, 1px `--color-divider` border, 12px radius) on the `--color-bg` ground, below the Frappe Desk header. Nothing inside the sheet has a tinted fill: regions (`.kt-region-tint`, name kept for compatibility), summary strips (`.kt-band`), KPI and fact cards and empty states all sit on white and are separated by section headings, spacing and 1px rules. Forms, registers and dialogs sit on the sheet. Register row separators and chart baselines stay. The only tinted fills inside the sheet are state marks — `.kt-status` chips, `.kt-notice` banners and `.tag` labels — and chart marks. Icon chips and spot illustrations are glyph or outline only.

## Color

**Surfaces and text are Frappe's** (verified against frappe/frappe version-16, commit 97a5dd9; full table in `foundations/frappe-surfaces.html`). Each KenTender token reads the Frappe variable with the verified value as fallback, e.g. `--color-bg: var(--gray-50, #f8f8f8)`:

- `--color-bg` ← `--gray-50` #f8f8f8 — ground behind the sheet
- `--color-surface` ← `--fg-color` white — sheet, cards, dialogs
- `--color-divider` ← `--border-color` #ededed — sheet border, section and table rules
- `--color-control` ← `--control-bg` #f3f3f3 — no longer used by `.input`, `.date-field` or `.btn-secondary` (DS-REV-003); kept for markup that still reads it
- `--color-control-border` ← `--gray-600` #7c7c7c — 1px outline of secondary buttons, inputs, date field and segmented control (DS-REV-003); `--color-control-border-disabled` ← `--gray-400` #c7c7c7 for disabled ones
- Read-only field shown as a value: `--color-control-disabled` ← `--disabled-control-bg` #f8f8f8, text `--color-control-disabled-text` ← `--disabled-text-color` #7c7c7c
- Disabled or read-only input: `--color-input-disabled` ← `--input-disabled-bg` #ededed, text `--color-text-muted` ← `--text-muted` #525252
- Inside an editable table row (Frappe `.grid-body .editable-row`, common/grid.scss): editable inputs are white (`--control-bg` re-set to `--neutral`) with square corners; disabled inputs take #f8f8f8 (`--input-disabled-bg` re-set to `--gray-50`); buttons keep the default button fill. KenTender: `.table td .input` and `.table td .input:disabled`
- Controls are outlined and rectangular (DS-REV-003): `.btn`, `.input`, `.date-field`, `.seg` take `--radius-control` 2px and a 1px `--color-control-border` outline on white. This departs from Frappe's `.form-control { border: none }` and from the "no border" wording of KT-STD-001 v1.22 §2.4; the standard needs a matching amendment. Inputs inside editable table rows stay borderless and square.
- Disabled buttons: `--color-control-disabled-text` #7c7c7c, `--color-control-border-disabled` outline, no fill.
- `.kt-status` is the only soft (6px), tinted, filled element on a page. Never give a control a resting fill other than the primary or solid danger.
- `--color-heading` / `--color-text` / `--color-text-muted` ← #171717 / #383838 / #525252
- `--color-neutral-100…900` ← Frappe's `--gray-*` ramp

KenTender sets no Frappe variable. The warm ground, region tint and well tokens are withdrawn.

**KenTender's own colours (proposal, not yet approved by v1.22):**

- **Indigo** `--color-accent` #2b46b0 — primary actions, selection, focus, links (`--color-accent-700`); key figures `--color-figure` (accent-800).
- **Rust** `--color-accent-2` #d9691a — brand mark (thumbnail) and `.tag-accent-2` only. Never links, data, state or fills inside the sheet.
- **Status** `--status-*` — owner-declared states only, always with text.
- **Data** (charts only): `--data-cat-1…6` categorical; `--data-seq-1…4` sequential teal for ordered magnitudes; `--data-pair-*` and `--data-family-1…3` indigo for value. Kept clear of rust and status red/amber/green.

Every token pair is recorded against WCAG AA in `foundations/contrast.html`. Light data tones carry a 1px inset edge in their family's dark step, and every chart value is printed as text.

## Type

Inter, through Frappe's `--font-stack` ("InterVariable", "Inter", system stack). Frappe Desk loads it; `assets/fonts/` holds Inter (OFL) only so previews render outside Desk. Sentence case, weight 600 for headings, no letter-spacing. Result figures use `.kt-result-value` with tabular digits.

## Icons

Lucide at stroke 1.75 on `currentColor`, at 16, 20 and 24px (`.kt-icon`, `.is-sm`, `.is-lg`). The KenTender icon list is in `foundations/icons.html` and the sprite `assets/icons/kt-icons.svg` (`#kt-<module>`): one icon per module; Analytics areas and record types take their source module's icon. Show a module or area icon in its `.kt-icon-chip` (glyph only, no fill) on tabs, section titles, summary columns and page headers. Icons may lead action and status labels; they never replace a label, and they never repeat in every table row.

## Motion

`--motion-fast` 120ms and `--motion-base` 180ms with `--ease-standard`, for tab changes, disclosures and hover only. Ceiling 200ms. Nothing moves on charts. `prefers-reduced-motion` turns transitions off.

## Frappe Desk

KenTender never restyles Frappe Desk and sets none of its theme variables (KT-STD-001 v1.22 §4). KenTender pages read Frappe's variables, so native forms, dialogs and KenTender pages share one ground, sheet, control style and font. Upgrade test: fail when any variable in `foundations/frappe-surfaces.html` no longer exists or no longer resolves to the listed value.

## Interaction states

Interactive states are themed, never browser defaults: give every interactive element a `:hover` tint and a pressed state from the ramps — one step past the base for filled controls (`--color-accent-800/-900` on the solid primary), and light ramp steps for the rest (`--color-accent-100/200` for ghost, `--color-neutral-100/200` for outlined controls and row hovers) — never an ad-hoc `color-mix()`. Style keyboard focus with `:focus-visible { outline: 2px solid var(--color-accent); outline-offset: 2px; }` — never leave the default blue focus ring.

## Components

| Class | What it is | Shown in |
| --- | --- | --- |
| `.btn` with `.btn-primary`, `.btn-secondary`, `.btn-ghost`, `.btn-icon`, `.btn-block` | Actions, 2px corners — the primary is a solid accent fill; the secondary is a 1px outline on white with no resting fill | components/buttons.html, proof/control-states.html |
| `.btn-danger`; `.kt-danger` on `.btn-primary` / `.btn-secondary` / `.btn-ghost` | Destructive action (Withdraw bid, Delete draft) — derived from the rose status hue; `.btn-danger` = `.btn-primary.kt-danger` (solid red), `.btn-secondary.kt-danger` = red outline, `.btn-ghost.kt-danger` = red text. Always paired with a `.btn-secondary` cancel, never two in a row | components/buttons.html, proof/control-states.html |
| `.tag` with `.tag-accent`, `.tag-accent-2`, `.tag-neutral`, `.tag-outline` | Small labels tinted from the ramps — accent-2 is the rust identity tint | components/buttons.html |
| `.field` + `label`, `.input`, `.radio` + `.dot`, `.seg` + `.seg-opt` | Form fields and choices on native elements — no script | components/forms.html |
| `.card` with `.card-kicker`, `.card-title`, `.card-body`, `.card-meta`; `.elev-sm/md/lg` | White card, 12px radius, 1px border, no shadow. Inside a page sheet, only when it carries a supplied fact | components/cards.html |
| `.nav` + `.nav-brand` | The header bar | components/navigation.html |
| `.table` (+ `.is-num` on numeric cells) | Data tables with themed header and row rules; headers stick on scroll, `.is-num` sets right-aligned tabular numerals for amounts and counts | components/table.html |
| `.dialog-backdrop` + `.dialog` (+ `.dialog-title/-body/-actions`) | A modal at the top elevation | components/dialog.html |
| `.hr` | A horizontal rule — present, but this system prefers whitespace; avoid it | — |
| `.blueprint` | Figure frame: 10px radius, clipped, no hairline | foundations/image.html |
| `.duotone` | The image wrapper — every content photograph goes through it | foundations/image.html |
| `.kt-disclosure` (+ `-head`, `-title-row`, `-title`, `-chevron`, `-body`) | Expand/collapse panel, no corner marks | components/disclosure.html |
| `.kt-timeline` (+ `-row`, `-dot-col`, `-dot`, `-line`, `-item`, `-item-title`, `-item-meta`) | A record's decision/approval chain — not a chart | components/timeline.html |
| `.kt-kpi-row` / `.kt-kpi-card` (+ `-head`, `-icon`, `-value`, `-sub`; `.is-live` / `.is-attention` / `.is-critical`) | Square fact card on the white sheet with a 4px left bar: neutral (`--color-neutral-400`) by default, a status hue only for an owner-declared state. Never indigo, so it is not an accent rule | components/kpi.html, components/dashboard.html |
| `.kt-steps` (+ `-node`, `-line`, `-label`) | Continuous multi-step progress/status track | components/steps.html |
| `.kt-notice` (`is-info`/`is-warning`/`is-critical`/`is-live`) | Page-level advisory banner | components/notice.html |
| `.kt-checkbox` | Checkbox, 4px radius (certification-style confirmations) | components/forms.html |
| `.kt-tabs` / `.kt-tab` | CSS-only tab row; an area tab leads with its 16px icon, which turns indigo when selected | components/forms.html |
| `.kt-record` (+ `-main`, `-index`, `-body`, `-ref`, `-title`, `-meta`, `-value`, `-amount`, `-sub`, `-footer`, `-toggle`, `-detail`) | List-item record card with an expandable detail block | components/record.html |
| `.kt-page` (+ `-head`, `-title`, `-desc`, `-scope`, `-actions`) | The one white sheet a page is drawn on — carries the page header and every region | components/page-shell.html |
| `.kt-region` (+ `.is-secondary`) | A titled region inside the sheet: 21px title (17px secondary) over open content, no box | components/page-shell.html |
| `.kt-group` | Quiet supporting facts behind a 2px divider left rule instead of a second panel | components/page-shell.html |
| `.kt-task-row` / `.kt-decision` | Level-1 emphasis: a 3px accent left rule on the actor's task, a 2px accent top rule above the decision area. At most two accent rules per page | components/page-shell.html |
| `.kt-guidance` | Region at the top of a record's content column, below the page header: holds one `.kt-journey` and at most one `.kt-next-step`. No card, shadow or band. Record detail, Review or decision, Form or editor only | components/guidance.html |
| `.kt-journey-lead` (+ `.has-position`), `.kt-journey-position` (+ `-label`, `-value`, `-n`, `-of`, `-state`; `.is-blocked`, `.is-done`), `.kt-journey.is-compact`, `.kt-journey-check` | DS-REV-004 (approved 6 Oct 2026; KT-STD-001 v1.23 approved 6 Oct 2026, so the compact form may become the pack default, a design-system decision): a position figure "{n} of {N}" with "Current · {holder}" / "Blocked · {holder}" beneath, leading a compact track of 6px bars (3px radius, 3px gutters), 13px labels, a check in place of the number on done stages, and each stage's state kept as text for assistive technology and print only. All stages done: "{N} of {N}" with Done. Nothing started: no figure. Stacks under 760px of sheet width; the one-line `.is-reduced.is-fallback` takes over under 600px | components/guidance.html |
| `.kt-journey` (+ `-stage`, `-bar`, `-title`, `-num`, `-state`; `.is-done` / `.is-current` / `.is-blocked`; `.is-reduced`) | Lifecycle stages as an `<ol>` of equal columns: 4px bar, number + label, visible state line. Set `--kt-journey-n` for stage count. Pair with `.is-reduced.is-fallback` to auto-switch under 600px sheet width. `.kt-journey-links` holds at most one upstream and one `.is-downstream` text link, each stated by the change unit. Orientation only — no links, dates, past actors or connectors | components/guidance.html |
| `.kt-next-step` (`.is-turn` / `.is-waiting` / `.is-done`; blocked = `.kt-notice.is-warning.kt-next-step`) | The actor's position: label, headline copied from the change unit, optional one sentence. Only the blocked kind takes a container and carries fix buttons; omit when not involved. (DS-REV-004: blocked is drawn as a 3px warning rule over the warning tint, square on the rule side, with no icon; the label reads "Your turn, blocked") | components/guidance.html |
| `.kt-choice-row` / `.kt-dependent` | Yes/No switch in a fixed 220px right column; dependent fields sit beneath behind a 2px divider rule. `.is-stacked` inside a two-column field grid | components/guidance.html |
| `.kt-filter-bar` (+ `.is-wide` on a cell) | Equal-width control cells directly above the records they filter, inside the sheet | components/page-shell.html |
| `.kt-empty` + `.kt-spot` (`.is-neutral` / `.is-success` / `.is-error`) | Empty, success, error and access states on the sheet, below a 1px rule: spot placeholder, one sentence, optional recovery action | components/empty-states.html |
| `.kt-region-tint` (+ `.kt-region-title`) | Task region on the white sheet, separated by a 1px top rule; title may lead with the area's icon chip. No fill | components/charts.html |
| `.kt-band` (set `--kt-band-n`) | Summary strip: equal columns between 1px top and bottom rules, divided by 1px rules. No fill | proof/screen-analytics.html |
| `.kt-result` (+ `-value`, `.is-md`, `-text`) | Result figure: display size, tabular digits, deep indigo, plain sentence beneath | proof/screen-analytics.html |
| `.kt-icon` / `.kt-icon-chip` (+ `.is-lg`) | Lucide icon at 1.75; module identity mark: neutral glyph, no fill | foundations/icons.html |
| `.kt-chart`, `.kt-legend`, `.kt-seg`, `.kt-hbars`, `.kt-range`, `.kt-vbars`; swatch roles `.is-cat-*`, `.is-seq-*`, `.is-pair-*`, `.is-family-*` | §2.6.10 chart forms with the colour roles above; `.is-selected` is an accent ring | components/charts.html |
| `.kt-section` / `.kt-panel` / `.kt-meta-row` | `.kt-panel` is the wrapper for detached content on a ground with **no** page sheet — inside `.kt-page` use `.kt-region` / `.kt-group` instead. `.kt-meta-row` distributes facts as equal grid cells across the measure (reflows to fewer columns as it narrows); add `.is-tight` for two short facts that belong together | components/sections.html |
| `.kt-app-shell` / `.kt-sidebar` / `.kt-nav-item` / `.kt-nav-group` / `.kt-topbar` / `.kt-breadcrumb` | Left-nav app shell. **Not for KenTender**: Frappe owns navigation. Outside DS-REV-002 scope | components/app-shell.html |

States are built in: hovers and pressed states come from the accent ramp, keyboard focus is the 2px accent `:focus-visible` ring, `::selection` is an accent tint, and disabled controls use solid tokens (`--color-neutral-400` text on a `--color-surface-2` well) rather than opacity. Don't restyle them per page. The accent-to-ground pair is tuned to at least 3:1 — enough for icons, large text and interface chrome, not for body copy — so for paragraph-size text in the accent use a deep ramp step (`--color-accent-700` on this ground) rather than the accent itself.

## Do

- Draw every page inside one `.kt-page` sheet; controls never sit on the bare ground.
- Use only Frappe's surfaces: the grey ground behind one bordered white sheet. Separate regions with headings, spacing and 1px rules.
- Give an area region its icon chip in the title.
- Lead a result with its figure: `.kt-result-value` in deep indigo, sentence beneath.
- Colour data by meaning: categorical for kinds, sequential teal for ordered magnitudes, paired and family indigo for value. Print every value as text.
- Use one icon per module everywhere it appears, from `foundations/icons.html`.
- Put filters directly above what they filter.
- Keep register row separators and chart baselines.
- Phrase an empty state positively only after a complete, successful read, and only where the change unit supplies no wording; module copy always wins.
- `<table>` markup must include `<thead>`/`<tbody>`.
- Avatars are circular.

## Don't

- On KenTender artboards, do not use `.kt-steps` or `.kt-timeline` (KT-STD-001 §2.2). Use `.kt-journey` for lifecycle position.
- Do not use `.kt-app-shell`/`.kt-sidebar` on KenTender artboards: Frappe owns navigation.
- Do not use `.kt-kpi-row` for decorative metrics. Cards carry supplied facts only.
- Do not give each area its own colour; identity is the icon chip.
- Do not put a tinted fill inside the sheet (regions, strips, KPI cards, empty states, table headers).
- Do not set or override any Frappe variable or class.
- Do not use rust for links, data series or state. Do not use status red, amber or green for categories.
- Do not use more than two thin accent rules per page (`.kt-task-row`/`.kt-next-step.is-turn` and `.kt-decision`). Card titles and table headers carry no accent rule.
- Do not set section titles or table headers in uppercase or letter-spaced type.
- Do not animate charts, and keep every transition at or under 200ms.
- Do not nest bordered boxes or put a shadow inside the sheet.
- Do not put icons in every table row, or let an icon replace a label.
- Do not place a `.field`, `.input`, `.seg` or `.kt-checkbox` on the `--color-bg` ground.
- Labels are atomic: `.btn`, `.tag`, `.kt-status`, `.seg-opt` never wrap internally.
- `disabled` and `checked` carry explicit values in templating contexts that strip boolean attributes.

## Files

- `styles.css` — the only stylesheet: the token sheet (`:root` variables, ramps, base type) plus the component layer. Link it from every page.
- `readme.md` — this guide.
- `theme.json` — the parameters these files were derived from (a machine-readable record of the theme).
- `thumbnail.html` — the project cover (brand mark + swatches).
- `foundations/type.html` — the type scale and the heading/body pairing at real sizes.
- `foundations/color.html` — color roles and the 100-900 tonal ramps, with usage notes.
- `foundations/layout.html` — the spacing scale, the grid and how edges are drawn.
- `foundations/icons.html` — the KenTender icon list (modules, Analytics areas, record types, interface icons).
- `foundations/contrast.html` — WCAG AA record for every DS-REV-002 token pair.
- `foundations/frappe-surfaces.html` — Frappe v16 surface, control, radius, text and font variables KenTender reads, with source files and commit.
- `components/dashboard.html` — KPI row plus all four chart forms (segmented, horizontal, monthly grouped, range strip) on fixture A1.
- `components/charts.html` — data colour roles, chart forms, and rust / warning / danger side by side.
- `components/empty-states.html` — spot placeholders and the empty-state wording rule.
- `assets/fonts/` — Inter variable (latin, latin-ext) and its OFL licence, for previews outside Desk.
- `assets/icons/kt-icons.svg` — icon sprite; `lucide-paths.json` holds the source paths.
- `DS-REV-002 Proof.html` + `proof/` — before/after proof set (native Frappe form + dialog, Analytics overview, register, review and decision), opening with native Frappe v16 and KenTender side by side on the same ground under the Frappe header edge. `proof/ds-rev-001.css` is the frozen DS-REV-001 stylesheet used for "before".
- `foundations/image.html` — how photographs and figures are treated.
- `components/buttons.html` — buttons, icon buttons and tags in every variant and state.
- `proof/controls-before-after.html` — DS-REV-003 register and page header with soft filled controls (before) and outlined rectangular controls (after).
- `proof/control-states.html` — every button variant at rest, hover, pressed, focus and disabled, and a field beside a secondary button.
- `DS-REV-003 Control shape.md` — the token and rule changes for regenerating the stylesheet.
- `components/forms.html` — text fields, radios and the segmented control on native elements.
- `components/cards.html` — content cards and the elevation steps.
- `components/navigation.html` — the header bar pattern.
- `components/table.html` — a data table with the themed header and row rules.
- `components/dialog.html` — a modal over its backdrop at the top elevation.
- `components/disclosure.html` — the expand/collapse panel.
- `components/timeline.html` — a record's decision/approval chain.
- `components/kpi.html` — summary metric cards with conditional state accents.
- `components/notice.html` — the page-level advisory banner in its four variants.
- `components/record.html` — the list-item record card with an expandable detail block.
- `components/sections.html` — page-section titles and the `.kt-panel` wrapper.
- `components/app-shell.html` — the sidebar-nav + top-bar app shell (not for KenTender).
- `theme.html` — the theme's parameters rendered as a reference sheet.
- `templates/landing/` — a starter page consuming the system the intended way (`index.html`, its `ds-base.js` loader, and the vendored `image-slot.js` its photograph mounts).
- `assets/photo.jpg` — the reference photograph the imagery page treats.

## Status semantics (KenTender extension)

Industry's `.tag` variants are decorative labels — they carry no state meaning. Where a UI
shows record state, use `.kt-status` instead. It is a softly-rounded (6px) chip: a solid
precomputed tint of the status hue (`--status-*-bg`), text at full strength
(`--status-*`), no border. The hues are tokenized in `styles.css` and recorded in
`theme.json`; the tints are solid values rather than alpha washes, so a chip renders
identically on a white card and on the grey ground.

| Class | Meaning | Examples |
| --- | --- | --- |
| `.kt-status.is-live` | In force now (emerald) | Active, Available, Ready |
| `.kt-status.is-draft` | Authored, not submitted (blue) | Draft |
| `.kt-status.is-pending` | Awaiting evaluation (neutral, hollow dot) | Not assessed |
| `.kt-status.is-attention` | Action needed (amber) | Configuration required |
| `.kt-status.is-critical` | Stopped or removed (rose) | Suspended, Closed |

```html
<span class="kt-status is-live">Active</span>
```

These five hues encode state only — never categories, never decoration.

**`.kt-figure`** applies the same tones to a large summary number. Dots are removed
system-wide — state is carried by color and label alone, never a dot.

**`.kt-card-title`** is the section title inside a card: sentence case, 600, heading colour, no underline. **`.table thead th`** sits on the `--color-surface-2` band over a 1px divider; no accent rule.

**`.kt-label`** is a caption label — beside a figure or under a value. Dimmed 11px text
fails contrast here (~2.5:1), so this uses a solid `--color-neutral-700` step plus 600 weight
instead.

**`.btn-danger`** is the destructive action (Withdraw bid, Delete draft), derived from the
rose critical hue (`--status-critical`, darkening on hover/press). Destruction is state semantics, so it uses the status hue. Always pair it with a `.btn-secondary` cancel; never place two
danger buttons in one row.

**Figure semantics are conditional, never column labels.** Financial measures (Approved,
Reserved, Committed, Available) are dimensions of one record, not states — do not give
each a hue. A neutral figure carries no dot; `.kt-figure` takes `is-live` / `is-attention` /
`is-critical` only when its *value* crosses a threshold (healthy / low / exhausted headroom),
so the same figure changes state as the year burns down. `.is-zero` (on figures and `.is-num`
cells) dims true zeros so real amounts pop. **`.kt-bar`** is the matching utilization bar —
a part-to-whole of one record drawn from the indigo ramp (committed deep, reserved mid,
free as track); it is not a chart, so `--chart-*` stays out of it.

## Media hardening (KenTender extension)

Three `@media` blocks in `styles.css` cover the environments a public procurement
system actually meets, and are not to be stripped when the stylesheet is trimmed:

- **`forced-colors: active`** — in Windows High Contrast every tinted fill collapses to one
  background, so chips and tags gain a `currentColor` border and the pending chip's hollow
  dot becomes a real border. State stays distinguishable by shape and label when tint is gone.
- **`print`** — tender summaries and confirmations get printed: ink-safe black text,
  hairlines kept, nav/buttons/segmented controls hidden, shadows dropped, chips outlined,
  sticky headers released.
- **`max-width: 480px`** — inputs step up to 16px so iOS Safari stops auto-zooming forms;
  a meaningful share of bidders are on phones.
