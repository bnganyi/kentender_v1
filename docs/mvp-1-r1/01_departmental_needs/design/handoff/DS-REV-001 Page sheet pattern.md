# DS-REV-001 — Page sheet pattern

Handoff to revise the **Industry / KenTender** core design system.
Raised from NDS-CHG-001 §11 artboard production, 21 September 2026.

---

## 1. The defect this fixes

Interactive controls and their labels were repeatedly landing directly on the grey ground
(`--color-bg` #f0f2f7): register filter rows, editor ownership rows, meta rows. A white
`.input` on grey stops reading as "a sheet on the board" — it reads as an unframed chip, and
its `label` / helper text lose the surface they were contrast-tuned against.

This has now been corrected by hand in at least three documents. It keeps coming back.

## 2. Root cause

**The rule exists in page templates, not in the artifacts a consuming project reads.**
`styles.css` and `readme.md` are what travel. Neither states a page-surface rule, and no class
expresses one. `.kt-panel` is documented as an *optional* wrapper "for content with no ruled
structure of its own", so a fresh page legitimately starts from the grey ground and adds
surfaces region by region.

Three aggravating factors:

1. **Two guidance rules pull opposite ways and neither is scoped.** KT-STD-001 §2.4 ("not a
   command to fill the page with bordered rectangles") and §2.6.7 ("borders only for real
   grouping") argue against containers. The Industry guide argues that filled white surfaces
   *are* the sheets and that controls are filled objects on a line-drawn board. For a filter
   row the two conflict, and the anti-container rule wins by default.
2. **The defect is invisible where the system is authored.** Every `components/*.html` page
   renders on white, so `.field` + `.input` look correct there. The failure only appears at
   page-composition scale, which no component page exercises.
3. **No component owns a control group.** There is a card, a panel, a record and a table, but
   no filter bar, no toolbar and no page shell — so a control row is laid out ad hoc every time.

## 3. Decision to encode

**A KenTender page is one white sheet on the grey ground.** The sheet carries the page header
(title, reference, status, scope line) and every region. Inside the sheet, hierarchy is made
with section titles, whitespace and hairline rules — not nested boxes. The grey ground carries
only the sheet.

Consequences, stated so they are not re-litigated per document:

- Control groups never sit on the grey ground, because the grey ground has no content.
- Inside the sheet, `.card` / `.kt-panel` are **not** used for ordinary regions; they remain
  correct for genuinely detached objects (a card grid, a dashboard tile, content on a ground
  with no page sheet).
- `.kt-notice`, `.kt-status`, `.table` header bands and `.kt-disclosure` still carry their own
  fill or rule — they encode state or interaction, not grouping.
- A disclosure inside the sheet loses its left/right/bottom border and reads as a rule band.
- Level-1 emphasis (task row, decision area) is a 2–3px accent rule plus scale, not a box.
- Dialogs keep the full sheet treatment and `--shadow-lg`; they are above the page, not in it.

## 4. Changes to `styles.css`

Add a page layer. Values below match what NDS §11 now renders at 1440 × 1024.

```css
/* ── Page shell: the one sheet a page is drawn on ── */
.kt-page {
  max-width: 1200px;
  margin: var(--space-6) auto;
  padding: var(--space-6);
  background: var(--color-surface);
  border: 1px solid var(--color-divider);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}
.kt-page-head { display: flex; justify-content: space-between; align-items: flex-start; gap: var(--space-6); }
.kt-page-title { font-family: var(--font-heading); font-weight: var(--font-heading-weight); font-size: 32px; line-height: 1.1; margin: 0; }
.kt-page-desc  { margin: var(--space-2) 0 0; font-size: 14px; color: var(--color-neutral-800); }
.kt-page-scope { display: flex; align-items: center; gap: var(--space-2); margin-top: var(--space-3); font-size: 13px; color: var(--color-neutral-700); }
.kt-page-actions { display: flex; gap: var(--space-3); flex: none; }

/* A region inside the sheet: title + open content, no box */
.kt-region > h2 { font-family: var(--font-heading); font-size: 21px; margin: 0 0 var(--space-3); }
.kt-region.is-secondary > h2 { font-size: 17px; color: var(--color-neutral-800); }

/* Quiet supporting group: a hairline rule, not a card */
.kt-group { border-left: 2px solid var(--color-divider); padding: 2px 0 2px var(--space-4); }

/* Level-1 task row and decision area: accent rule, no box */
.kt-task-row { border-left: 3px solid var(--color-accent); padding: 4px 0 4px var(--space-5); display: flex; align-items: center; gap: var(--space-6); }
.kt-decision { border-top: 2px solid var(--color-accent); padding: var(--space-5) 0 0; }

/* Filter bar: controls local to the records they filter */
.kt-filter-bar { display: grid; grid-auto-flow: column; grid-auto-columns: minmax(0, 1fr); gap: var(--space-3); align-items: end; margin-bottom: var(--space-4); }
.kt-filter-bar > .is-wide { grid-column: span 2; }

/* Inside a page sheet a disclosure is a rule band, not a nested card */
.kt-page .kt-disclosure { border-left: 0; border-right: 0; border-bottom: 0; }

/* Empty / filtered-empty inside the sheet */
.kt-empty { padding: var(--space-8) var(--space-6); text-align: center; border-top: 1px solid var(--color-divider); color: var(--color-neutral-800); }
```

Print: add `.kt-page { box-shadow: none; border-color: #000; margin: 0; }` to the existing
`@media print` block.

## 5. Changes to `readme.md`

**Direction** — replace the opening of the paragraph about cards and figures with:

> A KenTender page is one white sheet on the light technical ground: the sheet carries the page
> header and every region. Inside the sheet, hierarchy comes from section titles, whitespace
> and hairline rules; do not nest bordered boxes inside it. Cards and panels remain the right
> object for genuinely detached content — a card grid, a tile, content on a ground with no page
> sheet.

**Do** — add:

> - Draw every page inside one `.kt-page` sheet. Every group of interactive controls therefore
>   sits on `--color-surface`; the grey ground carries the sheet and nothing else.
> - Put filters in a `.kt-filter-bar` directly above the records they filter.
> - Use `.kt-group` for quiet supporting facts and `.kt-task-row` / `.kt-decision` for Level-1
>   emphasis, so importance is carried by rule and scale rather than by a box.

**Don't** — add:

> - Do not place a `.field`, `.input`, `.seg` or `.kt-checkbox` on the `--color-bg` ground. A
>   bare control on grey is the single most common defect in this system.
> - Do not wrap a region inside `.kt-page` in `.card` or `.kt-panel` — that is the nested
>   rectangle the system prohibits.

**Components table** — add rows for `.kt-page` (+ head/scope/actions), `.kt-region`,
`.kt-group`, `.kt-task-row`, `.kt-decision`, `.kt-filter-bar`, `.kt-empty`, pointing at the new
component page below.

## 6. Component pages

- **New `components/page-shell.html`** — a complete page sheet on the grey ground: header with
  title, reference, `.kt-status`, scope line and a primary action; a `.kt-task-row`; a
  `.kt-filter-bar` + `.table` + count; a `.kt-disclosure`; a `.kt-decision`. This is the page
  the system has been missing, and it is the page every module will copy.
- **Update `components/forms.html`** — render the existing field examples **on `--color-bg`
  inside a `.kt-page` sheet**, not on a white page. The current page cannot show the defect,
  which is why the defect survives.
- **Update `components/sections.html`** — restate `.kt-panel` as the detached-content wrapper
  and show `.kt-region` / `.kt-group` as the in-sheet alternative.
- Register all three in `_ds_manifest.json` cards (`page-shell` at `900x620`).

## 7. Lint (`_adherence.oxlintrc.json`)

Two rules worth enforcing mechanically:

1. **bare-control-on-ground** — fail any element carrying `class="field"`, `.input`, `.seg`,
   `.radio` or `.kt-checkbox` that has no `.kt-page`, `.kt-panel`, `.card`, `.dialog` or
   `.kt-filter-bar` ancestor.
2. **nested-surface** — fail `background:var(--color-surface)` or `.card` / `.kt-panel`
   appearing inside a `.kt-page` subtree.

Both are ancestor checks, so they need the DOM-ish linting path, not a regex pass.

## 8. Companion correction to KT-STD-001

§2.4 "Approved desktop shell" currently reads "full-width warm-white page background; a 1200 px
maximum-width content column". That wording is what licenses the grey-ground composition. It
should read that the content column **is a white sheet** on the page ground, with 32 px page
padding above and below it, and that §2.6.7's restraint on borders and shaded containers
applies *inside* the sheet. Without this edit the standard and the design system still disagree,
and the disagreement is what produced the defect.

## 9. Migration for consuming projects

Mechanical, in this order:

1. Give each page's content column the `.kt-page` treatment.
2. Strip `background` + `border` from every region wrapper inside it; keep `max-width`.
3. Convert supporting fact panels to `.kt-group`, task rows to `.kt-task-row`, decision areas
   to `.kt-decision`.
4. Leave `.kt-notice`, `.kt-status`, `.table`, `.kt-disclosure` and dialogs alone.

NDS §11 (74 artboards) has been migrated this way and is the reference specimen.

## 10. Open questions for the system owner

1. Does any surface legitimately break the sheet — a full-bleed register at technical-read
   width, or a two-column workspace wider than 1200 px?
2. Should `.kt-page` carry `--shadow-sm` at all, or is a hairline border alone truer to the
   wireframe direction?
3. Do KPI cards and the card grid survive inside a page sheet, or are they only ever used on a
   ground with no sheet?
