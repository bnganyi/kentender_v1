# KT-PAT-001 — Single-sheet page pattern

Full pattern specification. Companion to `DS-REV-001 Page sheet pattern.md`, which carries the
design-system edits (classes, readme wording, lint). This document is the pattern itself: what
it is, how each archetype composes inside it, and how to conform.

Reference specimen: `NDS Artboards.dc.html` — 74 artboards at 1440 × 1024, fully migrated.

---

## 1. The pattern

**A KenTender page is one white sheet on the light technical ground.** The sheet carries the
page header and every region of the page. Inside the sheet, hierarchy is made with content
order, heading scale, whitespace and hairline rules. Not with boxes.

The ground (`--color-bg`) carries the sheet and nothing else. This is what makes the rule
self-enforcing: if no content sits on the ground, no control can be stranded on it.

Why this and not per-region cards:

- The defect it eliminates — a white `.input` and its label on grey — was recurring in every
  document, because "should this region have a container?" was being answered region by region.
  The single sheet answers it once, at the page level.
- It satisfies both halves of the guidance that were previously in conflict: the Industry
  direction (filled white surfaces are the sheets pinned to the board) and KT-STD-001 §2.6.7
  (no nested bordered rectangles, hierarchy before borders). One sheet, open inside.
- It reads as the thing it is: one governed page of one record, not a dashboard of tiles.

## 2. Anatomy

```
┌ 1440 × 1024 artboard ─ --color-bg ────────────────────────────────┐
│                          32 px                                    │
│   ┌ the sheet ─ 1200 px ─ --color-surface, 1px --color-divider ┐   │
│   │  32 px padding                                            │   │
│   │  page header    title · reference · status · scope line    │   │
│   │  ── 24 px ──                                               │   │
│   │  Level 1 region   accent rule + scale                      │   │
│   │  ── 24 px ──                                               │   │
│   │  Level 2 region   section title, open content              │   │
│   │  ── 24 px ──                                               │   │
│   │  Level 3          disclosure as a full-width rule band      │   │
│   └────────────────────────────────────────────────────────────┘   │
│                          32 px                                    │
└───────────────────────────────────────────────────────────────────┘
```

| Property | Value | Token |
|---|---|---|
| Sheet width | 1200 px max | — |
| Sheet margin | 32 px top/bottom, auto sides | `--space-6` |
| Sheet padding | 32 px | `--space-6` |
| Sheet fill | #ffffff | `--color-surface` |
| Sheet edge | 1 px hairline, square corners | `--color-divider` |
| Sheet elevation | `--shadow-sm` (under review — §10) | |
| Region gap | 24 px | `--space-5` |
| Content measure inside | 860 px editors · 900 px details/reviews | — |

Narrow desktop: the sheet shrinks with the viewport; margins hold at 32 px; regions reflow per
KT-STD-001 §3 (tables scroll or become labelled rows; nothing material drops).

## 3. In-sheet vocabulary

The classes in DS-REV-001 §4. What each one is for, and what replaced it.

| Element | Treatment | Replaces |
|---|---|---|
| **Page header** `.kt-page-head` | 32 px condensed title; reference in 13 px muted beneath; `.kt-status` chip and revision beside; one quiet scope/evidence line under | a bordered context card or PE/FY context row |
| **Region** `.kt-region` | 21 px condensed section title, content open beneath. Secondary regions drop to 17 px at `--color-neutral-800` | a `.card` or `.kt-panel` per region |
| **Level-1 task row** `.kt-task-row` | 3 px `--color-accent` left rule, 20 px inset, business name at 19–20 px, status narrative, one dominant button at row right | a white bordered panel with shadow |
| **Decision area** `.kt-decision` | 2 px `--color-accent` rule above, consequence sentence, then primary + corrective actions right-aligned | a bordered, shadowed action card |
| **Quiet supporting group** `.kt-group` | 2 px `--color-divider` left rule, 16 px inset | a second white panel competing with the first |
| **Filter bar** `.kt-filter-bar` | `.field` + `.input` cells directly above the records they filter, on the sheet | bare fields on the grey ground — the original defect |
| **Register** `.table` | Keeps its own header band and row rules; it is a ruled structure, not a box | — |
| **Fact groups** `.kt-meta-row` | Equal cells across the measure; `.is-tight` for two facts that belong together; `grid-template-columns:1fr` where the contract says separate rows | one labelled box per fact |
| **Disclosure** `.kt-disclosure` | Inside the sheet: left/right/bottom borders dropped — a full-width rule band that opens | a nested bordered card |
| **Notice** `.kt-notice` | Keeps its tint and 3 px left rule; encodes state, not grouping | — |
| **Empty state** `.kt-empty` | Hairline top rule, generous padding, a 30 px thin-stroke Lucide glyph above the message, centred | an empty bordered card, or bare text |
| **Dialog** `.dialog` | 520 px sheet at `--shadow-lg` over a dimmed parent; `z-index` above sticky table headers | — |

## 4. What keeps its own surface — the closed exception list

Only these. Anything else inside the sheet is open content.

1. **`.table`** — ruled structure with a header band.
2. **`.kt-notice`** — tinted advisory band; the tint is state.
3. **`.kt-status`** — state chip.
4. **`.kt-disclosure`** — with side and bottom borders dropped, per §3.
5. **Inputs and controls** (`.input`, `.date-field`, `.seg`, `.kt-checkbox`) — white-filled
   controls are the system's identity; on the sheet they read correctly.
6. **`.dialog`** — above the page, not in it.
7. **Skeleton blocks** in the loading state — they stand for the shapes that will arrive.

Not on the list, and therefore not used inside a page sheet: `.card`, `.kt-panel`,
`.kt-kpi-card`, `.kt-record`, `.blueprint`. Those remain correct on a ground with **no** page
sheet — a card grid, a tile row, a marketing or index surface.

## 5. Archetype recipes

How KT-STD-001 §2.6.3 composes inside one sheet. Each recipe is realised in the specimen.

**Work workspace** — header with primary action + scope line → `.kt-task-row` per actionable
item under a 21 px title → secondary register region at 17 px with its own `.kt-filter-bar`,
`.table`, count. Omit the task region entirely when there is no work (do not draw an empty one).
*Specimen: NDS-DES-01, NDS-DES-02, NDS-DES-02-DUAL-ROLE.*

**Register** — header → `.kt-filter-bar` → `.table` → count. No decision area above it.
*Specimen: NDS-DES-TECHNICAL-REGISTER.*

**Form / editor** — header + purpose sentence → read-only ownership facts separated by a hairline
rule (not a card) → editable fields in one open column, 860 px measure, helper text under each
control → collapsed History → footer above a hairline: destructive at far left, secondary then
primary right-aligned. *Specimen: NDS-DES-03, 04, 08, 15-*.*

**Review / decision** — header + task statement → `.kt-notice` carrying "Decision required" →
quiet orientation line → comparison first where one exists (`.table`, changed value emphasised)
→ complete submitted content → `.kt-decision`. *Specimen: NDS-DES-06, 09, 12.*

**Record detail** — header + status narrative → current results as sibling `.kt-group`s of equal
weight → accepted/submitted content → collapsed evidence. Current truth, proposed work,
downstream position and history stay four visually distinct things.
*Specimen: NDS-DES-05, 07, 07A-* (9 variants), 08-DRAFT/SUBMITTED/RETURNED.*

**Setup** — same shell; effective setting and consequence first, audit history subordinate, no
business-approval styling. *No specimen in NDS — §11.11 retires the surface.*

**Focused dialog** — 520 px sheet, title top-left, full record name beneath, identity on separate
labelled rows, the supplied explanatory sentence, one reason field where specified, Cancel then
one primary action bottom-right. *Specimen: NDS-DES-11, 13-* (8).*

**Page states** — loading, denied, masked, load-failure occupy the sheet alone, with no protected
header, filters or rows behind them. Empty and closed-intake states keep the permitted header.
*Specimen: NDS-DES-14-* (16).*

## 6. Expressing information priority without boxes

The sheet removes containers as a hierarchy device, so priority is carried by four things, in
this order:

1. **Position** — Level 1 is first, immediately under the header.
2. **Scale** — 21 px section titles for primary regions, 17 px at `--color-neutral-800` for
   secondary ones; 19–20 px business names in task rows against 15 px body.
3. **Rule** — a 3 px accent left rule or 2 px accent top rule marks the one region that carries
   the actor's task. Used more than twice on a page it stops meaning anything.
4. **Disclosure** — Level 3 goes behind one rule band, one depth only, with a summary that says
   what is inside.

Level 2 gets no marker at all. That is the point: it is the body of the page.

## 7. Do / Don't

**Do**

- Put every page inside one sheet, header included.
- Put filters immediately above the records they filter, inside the sheet.
- Give one region per page the accent rule.
- Give empty and failure states a thin-stroke glyph and a full sentence with the recovery in it.
- Keep `.kt-notice`, `.kt-status` and `.table` as they are.

**Don't**

- Don't put a `.field`, `.input`, `.seg` or `.kt-checkbox` on the ground.
- Don't wrap an in-sheet region in `.card` or `.kt-panel`.
- Don't stack a shadow inside the sheet — elevation belongs to the sheet and to dialogs.
- Don't use the accent rule for decoration or on more than two regions.
- Don't let a dialog's dimmed parent leak sticky table headers through — the backdrop needs a
  `z-index` above `.table thead th`.

## 8. Conformance checks

Run these before a design contract goes to review; the first two are lintable (DS-REV-001 §7).

1. No `.field` / `.input` / `.seg` / `.radio` / `.kt-checkbox` without a sheet, panel, dialog or
   filter-bar ancestor.
2. No `--color-surface` fill or `.card` / `.kt-panel` inside a `.kt-page` subtree.
3. Exactly one sheet per page; exactly one dominant action per task region.
4. At most one disclosure depth; every disclosure summary names its contents.
5. Every table has `<thead>`/`<tbody>` and a comparison or register purpose.
6. Dialog backdrops paint above sticky headers.
7. First-view comprehension check per KT-STD-001 §2.8, on the rendered sheet.

## 9. Migration recipe

Mechanical, in this order. Reversible at each step.

1. Give the page's content column the sheet treatment (`.kt-page`).
2. Strip `background` and `border` from every region wrapper inside; keep `max-width`.
3. Convert: supporting fact panels → `.kt-group`; task rows → `.kt-task-row`; decision areas →
   `.kt-decision`; region wrappers → `.kt-region`.
4. Drop side and bottom borders from in-sheet disclosures.
5. Leave `.kt-notice`, `.kt-status`, `.table` and dialogs untouched; add `z-index` to dialog
   backdrops.
6. Re-check empty, denied and failure states — they are the ones that look worst bare.

The NDS specimen was migrated this way in one pass, across 74 artboards, with no per-artboard
decisions.

## 10. Implementation notes (Frappe / Vue)

- `.kt-page` belongs in `styles.css`, not in a page component, so every module inherits the
  geometry. Port it into the scoped SFC only as `class="kt-page"` on the single page root
  (KT-STD-001 §4).
- The sheet is the page-ready anchor: put `data-testid` for page-ready state on it.
- Print: the sheet drops its shadow and margin and keeps the hairline; the existing `@media
  print` block in `styles.css` handles the rest.
- Do not add a second shell, header or context selector inside the sheet — KT-STD-001 §10.

## 11. Open questions

1. Does any surface legitimately break the sheet — a full-bleed technical register, or a
   workspace wider than 1200 px?
2. Does the sheet carry `--shadow-sm`, or is the hairline alone truer to the wireframe direction?
   (The specimen currently uses `--shadow-sm`.)
3. Do KPI cards and the card grid exist at all inside a page sheet, or only on sheetless grounds?
4. Should `.kt-empty` glyphs be standardised per state (search-x for filtered-empty, inbox for
   no-records, clipboard-check for an empty decision queue), or left to the module?
