# Board versus spec (row HOME6-0002)

Date: 4 October 2026. Sources: `design/Home/Home.dc.html` (16 boards, 139,314 bytes; identical in size to the copy inside the owner's `KenTender home and analytics.zip`), HOME v0.6 §10B, `design/_ds/…/readme.md`, `design/Home/ds-additions.css`. Counts below were taken directly from the board file.

## 1. Coverage

All 16 spec artboards are present, in this order: HOME-DES-21, 21N, 29, 22, 23, 24, 25, 26, 26B, 27, 28A–28F. None is missing; none is extra. Text of HOME-DES-21 and 29 matches §10B.3 line by line, including every relative label (35 days ago for the 14 May appointment is correct against 18 June).

## 2. How the board is built

- **1,023 inline `style="…"` attributes** and these class names only, with counts: `kt-icon` 142, `kt-icon-chip` 86, `btn` 34, `kt-icon is-sm` 32, `kt-kpi-card`/`-head`/`-value`/`-sub` 28 each, `btn-secondary` 22, `btn-primary` 11, `kt-spot` 3, `kt-status` 1 (with `is-attention`), `btn-ghost` 1.
- It does not link `ds-additions.css` and uses none of its classes (`kt-fact-card`, `kt-work-row`, `kt-rail-row`, `kt-workspace*`).
- Every icon is an inlined Lucide path; the sprite is not used.
- The only script is the canvas zoom-fit. Focus moves, Show more, Try again and the 960 px reflow are drawings.

**Consequence for the port.** "Class-for-class" cannot mean copying class names, because the layout lives in inline styles. Phase 4 names each repeated inline group once, in a Home CSS file, keeping the board's values. Groups to name (from the board): sheet, header row, update line, summary row, summary column (uses `kt-kpi-*`), region heading, work row (grid `32px 1fr auto`), module chip (main column), quiet text, relative-date badge, warning callout, rail, rail row, show-more footer, region failure strip, state panel. The fidelity gate derives landmark order and nesting from the board, and it does not owe containers for class names the design system does not define (AGENTS.md §6.6).

## 3. Deltas to resolve

Each has a proposed disposition. "Fix" means the build follows the spec; "Departure" means the build follows the board and records a registry entry in `tests/ui/fidelity/departures/home.js` (row HOME6-0801). The owner decides any item marked Owner.

| # | Board | Spec / design system | Proposed |
|---|---|---|---|
| 1 | Main-column module chips are 32 px with `background:var(--color-accent-100)` and an 8 px radius (38 inline uses of that fill, 18 chips of this exact form) | §10B.1: module icon chip "with the indigo glyph"; a tinted chip is stated only for the actions summary column. DS-REV-002 readme: icon chips are glyph only, no fill | **Owner.** Board is the accepted render (D-HOME-06). Recommended: keep the filled chip, record a departure from the readme, ask the design owner to amend the readme |
| 2 | Coming up badge `background:var(--data-seq-1);color:var(--data-seq-4)` (5 each) | §10B.1 "small tinted badge"; DS readme restricts `--data-seq-*` to charts | **Owner.** Recommended: introduce a named badge token pair (e.g. `--badge-info-bg/-fg`) with the same values rather than reuse chart tokens in a page component |
| 3 | Show more is `.btn.btn-ghost` plus chevron (the one `btn-ghost`) | HOME §5.1 item 5: "a text action"; §10B.1 rail uses text links | **Fix** as a text-style control with chevron; a button element for keyboard and focus, styled as text |
| 4 | 21N: sheet padding 28 px, summary chip untinted 28 px | §10B.1: 32 px sheet padding; actions column has a tinted chip | **Fix** to 32 px and tinted chip; 21N is the same component at a narrower container, not a different design |
| 5 | 28B: waiting column keeps the label "items you're waiting on" beside "Count unavailable" | §10B.1: "Count unavailable instead of the figure" | **Fix**: the label stays because it names the count; confirm with owner that "instead of the figure" does not also drop the label (low) |
| 6 | 27: "Technical record search" placed before "Updated" | §10B.1 item 1: link "beside the update time"; order unspecified | **Fix** to the board order; no spec conflict |
| 7 | 26B: inline `outline:2px solid var(--color-accent)` stands in for focus on the appended row | §5.1 item 5 and §11: focus moves to the first appended row | **Fix**: real `:focus-visible` ring from the design system; no inline outline |
| 8 | Rail has a faded vertical divider (gradient on `<aside>`) and 24 px left padding | not stated in §10B.1 | **Departure** (board is the accepted render) or drop; Owner |
| 9 | `.kt-status.is-attention` for "Your turn, blocked" (board 25) | §10B.1: shown on line 2 only for blocked work | **Fix**: implement as `.kt-status`; `is-attention` is a real state and uses text, per KT-STD §2.6.11 |
| 10 | Region headings: h2 18 px in main, 15 px in rail | §10B.1 item 4: rail headings 15 px | consistent; implement both |
| 11 | Updated line carries a clock icon, region headings carry list-checks / calendar-clock icons | those three icons are **not** in the DS `lucide-paths.json` | **Fix**: add the three icons in Phase 1 (row HOME6-0105) |
| 12 | Links as `href="#my-work|#waiting|#oversee|#"` | §5.1 item 2: selecting a count moves focus to its region | **Fix**: focus a `tabindex="-1"` region heading, not a hash scroll |
| 13 | No `aria-live`, no landmarks | HOME-AC-08, KT-STD §2.6/§3A | **Fix**: landmarks, headings, a polite live region for Show more and retry |

## 4. `ds-additions.css` and `DS additions.dc.html`

Headed "DS-REV-002 proposed additions … Not approved". It defines `.kt-fact-card` (bordered card, heading-colour figure), `.kt-fact-row`, `.kt-work-row`, `.kt-rail-row`, `.kt-workspace*` (container query below 960 px). Against the accepted render it is stale: the render uses the rule-led `.kt-kpi-card`, a 32 px filled chip, a tinted reason callout and a 20 px rail icon column, and it adds a badge, a show-more footer, a state panel and a divider that the file does not define. **Disposition:** not used as a source. The board is the source; Phase 4 writes the Home classes from the board. The `kt-rail-*` names are avoided for the right-hand rail because `PageRail.vue` already owns `kt-rail` for the top breadcrumb bar.

## 5. Design-system consumption

The board reads these tokens: `--color-heading`, `--color-text`, `--color-text-muted`, `--color-divider`, `--color-surface`, `--color-bg`, `--color-accent`, `--color-accent-100`, `--color-accent-700`, `--color-accent-800`, `--color-neutral-300/500/700`, `--status-attention`, `--status-attention-bg`, `--status-live`, `--status-critical`, `--data-seq-1`, `--data-seq-4`, and `--color-figure` through `.kt-kpi-value`. All exist in `_ds/…/styles.css` and none of `--color-figure`, `--data-seq-*`, `.kt-icon-chip`, `.kt-spot` exist in `kentender_core/public/css/kt_industry_tokens.css`, which is why Phase 1 comes first.
