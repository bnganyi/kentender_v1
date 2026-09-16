# Industry design system

Industry is a wireframe: royal indigo on a light technical ground, Barlow Condensed headings over Barlow, a modular grid, and cards and figures framed as blueprint objects — square-cornered, hairline-bordered. Buttons are square and hairline-bordered too. Figures stay transparent line drawings; cards, dialogs and inputs are filled white — sheets pinned to the board — and the primary button is a solid accent fill — the filled objects on an otherwise line-drawn board, all keeping the square corners. Photography is duotoned into the steel accent and icons are thin-stroke.

## How to use this

- Link the one stylesheet from every page — `<link rel="stylesheet" href="styles.css">` (adjust the relative path) — and take every color, font, spacing, radius and shadow from its variables (`var(--color-*)`, `var(--font-*)`, `var(--space-*)`, `var(--radius-*)`, `var(--shadow-*)`). Never hard-code a hex, a font name or a px value the tokens already carry.
- Build with the classes below rather than inventing parallel ones; the component pages are plain HTML, so view source and copy the markup.
- `templates/` holds starting points a consuming project can copy whole.
- The whole system was derived from `theme.json`. To change the look, edit the tokens at the top of `styles.css` — every page, the thumbnail and this guide read from them — and keep `theme.json` and the written guidance in step so they don't drift from what the CSS actually does.

## Direction

Modular grid layouts — content in equal-width cells, strong horizontal and vertical rhythm, visible structure. Cards, figures and major sections are wireframe objects: square-cornered, thin-bordered — never soft filled rounded blocks. Buttons keep the square corners and hairline border, identified by their fill and border alone. Images and figures get the same treatment: square and hairline-framed, never rounded or clipped. Corner registration marks have been removed system-wide — no component carries them. Wrap hero and inline images in the `.duotone` class — they are desaturated and washed in the accent, like a screen print that re-colors with the theme.

## Color

A light ground (`--color-bg` #f0f2f7) with white surfaces — cards, dialogs and inputs are the sheets on the board (`--color-surface` #ffffff, `--color-surface-2` #eef0f3 for wells like disabled fills and header bands) — with `--color-text` #16181a, a primary accent #2b46b0 (royal indigo, the one solid-fill action color — same steel identity slot, pushed to a real chroma) and a second accent #d9691a (rust/amber, for links and secondary emphasis, giving the system a warm/cool contrast instead of two cool hues). Each role carries a 100–900 tonal ramp generated in OKLCH on a shared perceptual lightness scale, so the same step of any ramp has the same visual weight. Use the light steps (100–300) for tinted fills, hovers and subtle borders, 500 as the role's base, and the dark steps (700–900) for text on tinted fills and for pressed states; prefer ramp steps over ad-hoc `color-mix()`. For elevation use `--shadow-sm/md/lg` (already tuned to the ground) rather than ad-hoc box-shadows.

Secondary and caption text (`.text-muted`, `figcaption`, `.card-body`, `.card-meta`, field labels, `.table th`, `.dialog-body`) is set with solid `--color-neutral-700`/`-800` steps, not opacity or `color-mix()` on `--color-text`. Dimmed text landed around 2.5:1 on this ground — too low for an information-dense, legally sensitive product — so every secondary text role now resolves to a real ramp step that clears body-text contrast.

`--chart-1` … `--chart-6` are a separate six-hue, fully saturated palette for categorical data visualization (chart series, legends) only. They're deliberately distinct from both UI accents and from the `.kt-status` semantic hues below, so a chart color is never mistaken for a status or an action.

## Type

Barlow Condensed for headings over Barlow for body text, loaded as `--font-heading` / `--font-body`. Density 0.85× and radius 4px are already baked into the `--space-*` / `--radius-*` scales — use the variables, not raw numbers.

## Icons

Use Lucide icons (https://lucide.dev), at stroke-width 1.5 for a lighter, more technical look throughout.

## Interaction states

Interactive states are themed, never browser defaults: give every interactive element a `:hover` tint and a pressed state from the ramps — one step past the base for filled controls (`--color-accent-800/-900` on the solid primary), and light ramp steps for the rest (`--color-accent-100/200` for ghost, `--color-neutral-100/200` for outlined controls and row hovers) — never an ad-hoc `color-mix()`. Style keyboard focus with `:focus-visible { outline: 2px solid var(--color-accent); outline-offset: 2px; }` — never leave the default blue focus ring.

## Components

| Class | What it is | Shown in |
| --- | --- | --- |
| `.btn` with `.btn-primary`, `.btn-secondary`, `.btn-ghost`, `.btn-icon`, `.btn-block` | Actions — the primary is a solid accent fill | components/buttons.html |
| `.btn-danger` | Destructive action (Withdraw bid, Delete draft) — derived from the rose status hue; always paired with a `.btn-secondary` cancel, never two in a row | components/buttons.html |
| `.tag` with `.tag-accent`, `.tag-accent-2`, `.tag-neutral`, `.tag-outline` | Small labels tinted from the ramps — accent-2 (violet) now reads as a distinct second tag color | components/buttons.html |
| `.field` + `label`, `.input`, `.radio` + `.dot`, `.seg` + `.seg-opt` | Form fields and choices on native elements — no script | components/forms.html |
| `.card` with `.card-kicker`, `.card-title`, `.card-body`, `.card-meta`; `.elev-sm/md/lg` | Hairline-bordered cards, filled with `--color-surface` for legibility | components/cards.html |
| `.nav` + `.nav-brand` | The header bar | components/navigation.html |
| `.table` (+ `.is-num` on numeric cells) | Data tables with themed header and row rules; headers stick on scroll, `.is-num` sets right-aligned tabular numerals for amounts and counts | components/table.html |
| `.dialog-backdrop` + `.dialog` (+ `.dialog-title/-body/-actions`) | A modal at the top elevation | components/dialog.html |
| `.hr` | A horizontal rule — present, but this system prefers whitespace; avoid it | — |
| `.blueprint` | The hairline wireframe frame a card or figure wears — no corner marks | components/cards.html |
| `.duotone` | The image wrapper — every content photograph goes through it | foundations/image.html |
| `.kt-disclosure` (+ `-head`, `-title-row`, `-title`, `-chevron`, `-body`) | Expand/collapse panel, no corner marks | components/disclosure.html |
| `.kt-timeline` (+ `-row`, `-dot-col`, `-dot`, `-line`, `-item`, `-item-title`, `-item-meta`) | A record's decision/approval chain — not a chart | components/timeline.html |
| `.kt-kpi-row` / `.kt-kpi-card` (+ `-icon`, `-value`, `-dot`, `-sub`) | Summary metric card; top accent + dot appear only past a threshold | components/kpi.html |
| `.kt-notice` (`is-info`/`is-warning`/`is-critical`/`is-live`) | Page-level advisory banner | components/notice.html |
| `.kt-checkbox` | Square checkbox (certification-style confirmations) | components/forms.html |
| `.kt-tabs` / `.kt-tab` | CSS-only tab row | components/forms.html |
| `.kt-record` (+ `-main`, `-index`, `-body`, `-ref`, `-title`, `-meta`, `-value`, `-amount`, `-sub`, `-footer`, `-toggle`, `-detail`) | List-item record card with an expandable detail block | components/record.html |
| `.kt-section` / `.kt-panel` / `.kt-meta-row` | Page-section title + optional white panel, for content with no ruled structure of its own | components/sections.html |
| `.kt-app-shell` / `.kt-sidebar` / `.kt-nav-item` / `.kt-nav-group` / `.kt-topbar` / `.kt-breadcrumb` | Left-nav app shell: sidebar (brand, search, flat nav + one nested group, active-item tint + right accent bar, footer/user block) and a top bar (breadcrumb + icon actions + user block) | components/app-shell.html |

States are built in: hovers and pressed states come from the accent ramp, keyboard focus is the 2px accent `:focus-visible` ring, `::selection` is an accent tint, and disabled controls use solid tokens (`--color-neutral-400` text on a `--color-surface-2` well) rather than opacity. Don't restyle them per page. The accent-to-ground pair is tuned to at least 3:1 — enough for icons, large text and interface chrome, not for body copy — so for paragraph-size text in the accent use a deep ramp step (`--color-accent-700` on this ground) rather than the accent itself.

## Do

- Frame cards and figures as blueprint objects: the `.blueprint` class — a hairline border, nothing more. No component carries corner registration marks.
- Use `--color-accent-2` (violet) for links or secondary emphasis that must read as distinct from the primary action; reserve `--chart-*` strictly for data-visualization series.
- Keep the grid visible — equal cells, strong horizontal and vertical rhythm.
- Condense headings (Barlow Condensed) and keep body copy in Barlow.
- Duotone photographs with the `.duotone` wrapper so they take the accent.
- `<table>` markup must include `<thead>`/`<tbody>` — several header rules (background band, accent rule, sticky, uppercase promotion) target `.table thead th` specifically and silently no-op without it.
- Avatars (user initials, `.kt-sidebar-avatar`/`.kt-topbar-avatar`) are circular — the one deliberate exception to the square-corner rule. Everything else (icons, panels, badges, nav rows) stays square.

## Don't

- Do not round cards, figures or buttons — square corners throughout. Figures (image frames) stay unfilled line drawings; cards and dialogs are filled (the primary button, cards and dialogs are the deliberate exceptions to "line drawing").
- Do not reintroduce corner registration marks — the `.blueprint` frame is a plain hairline border. This reverses the earlier rule entirely, not just narrows it to `.card` and figures.
- `disabled` and `checked` must carry an explicit value (`disabled="disabled"`, `checked="checked"`) in any templating context that strips valueless boolean HTML attributes — plain static HTML pages are unaffected.
- Status/figure/KPI dots are removed entirely — state is carried by label text, fill color, and (for KPI cards) the top accent bar alone. Do not reintroduce a dot anywhere.
- Do not use `--chart-*` colors for UI chrome (buttons, chips, nav) or `.kt-status` hues for chart series — each palette encodes exactly one thing.
- Do not use thick icon strokes; the set is Lucide at 1.5.
- Do not add decorative color beyond the steel accent. The accent's own deep step (`--color-accent-900`) may carry a full field where the deck's section dividers use it — steel as ground, type reversed to paper. (The landing's numbers sit on a drawn spec-sheet plate on the paper ground instead — its own grammar, not a field.)

## Files

- `styles.css` — the only stylesheet: the token sheet (`:root` variables, ramps, base type) plus the component layer. Link it from every page.
- `readme.md` — this guide.
- `theme.json` — the parameters these files were derived from (a machine-readable record of the theme).
- `thumbnail.html` — the project cover (brand mark + swatches).
- `foundations/type.html` — the type scale and the heading/body pairing at real sizes.
- `foundations/color.html` — color roles and the 100-900 tonal ramps, with usage notes.
- `foundations/layout.html` — the spacing scale, the grid and how edges are drawn.
- `foundations/icons.html` — the icon set at interface sizes, inline and in buttons.
- `foundations/image.html` — how photographs and figures are treated.
- `components/buttons.html` — buttons, icon buttons and tags in every variant and state.
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
- `components/app-shell.html` — the sidebar-nav + top-bar app shell.
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

These five hues are the only colour permitted outside the steel accent, and only ever to
encode state — never decoratively.

**`.kt-figure`** applies the same tones to a large summary number. Dots are removed
system-wide — state is carried by color and label alone, never a dot.

**`.kt-card-title`** is the section title inside a card: condensed uppercase at full text
strength on a 2px accent underline. **`.table thead th`** is likewise promoted to condensed
uppercase at full strength on a heavier rule, so headers separate from body rows.

**`.kt-label`** is a caption label — beside a figure or under a value. Dimmed 11px text
fails contrast here (~2.5:1), so this uses a solid `--color-neutral-700` step plus 600 weight
instead.

**`.btn-danger`** is the destructive action (Withdraw bid, Delete draft), derived from the
rose critical hue (`--status-critical`, darkening on hover/press). Destruction is state
semantics, so this sits inside the "no colour beyond steel except to encode state" rule
rather than breaking it. Always pair it with a `.btn-secondary` cancel; never place two
danger buttons in one row.

**Figure semantics are conditional, never column labels.** Financial measures (Approved,
Reserved, Committed, Available) are dimensions of one record, not states — do not give
each a hue. A neutral figure carries no dot; `.kt-figure` takes `is-live` / `is-attention` /
`is-critical` only when its *value* crosses a threshold (healthy / low / exhausted headroom),
so the same figure changes state as the year burns down. `.is-zero` (on figures and `.is-num`
cells) dims true zeros so real amounts pop. **`.kt-bar`** is the matching utilization bar —
a part-to-whole of one record drawn from the steel ramp (committed deep, reserved mid,
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
