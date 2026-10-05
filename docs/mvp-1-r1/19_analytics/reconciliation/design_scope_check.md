# Analytics design scope: computed-style check (plan Phase 4, gate ANL-G04)

Date of the run: 5 October 2026. Run by the build session; nothing in this note was read from a tracker.
Browser: Chromium (Playwright 1.59.1, headless shell), local `file://` pages only. No server, no login, no site queried or changed.

## What was built

- `scripts/home_design_css.py` now takes a target. `--target analytics` writes
  `kentender_core/kentender_core/public/js/analytics/kt_analytics_ds.bundle.css` from the Analytics design pack's `styles.css`, the boards' own data-colour block, and the hand-authored chart rules in `scripts/analytics_charts.css`. Every selector sits under `.kt-industry.kt-analytics`. Home's output is unchanged: md5 `87f4819ef0729329901bb978691488d7` before and after.
- `scripts/analytics_icons_js.py` writes `analytics_icons.js` (20 icons, five area icons checked against the tab labels the boards draw).
- Six chart components under `public/js/analytics/components/charts/`, plain Vue 3, no chart library.

## Method

Home Phase 1A's (HOME6-0104), widened from one board to all six board files (22 artboards, 6,683 elements).

- **original**: the design pack's own `styles.css` plus the board's local style block, in an iframe, as the board renders.
- **scoped**: only `kt_analytics_ds.bundle.css`, the same artboard markup wrapped in `.kt-industry.kt-analytics`, in a second iframe of the same width.
- Every element, and its `::before` and `::after` where either has content, compared on every computed CSS property (548 properties per element, layout sizes included).
- The scoped copy was loaded in three stacks: **V0** alone; **V1** plus every app-wide stylesheet the kentender apps load in Desk (`app_include_css`); **V2** plus Frappe's own `desk.bundle.css`.
- Hover and keyboard focus (`:focus-visible`) on the first element of each interactive kind (primary, secondary and ghost buttons, selected and unselected tab, link, disclosure head, select, text input), element and all descendants, pseudo-elements included. Each state was applied to one copy, settled for 300 ms (the colour transitions are 120 and 200 ms), read, then applied to the other copy, because only one frame can hold focus or the pointer.

Reproduce: `node scripts/analytics_design_scope_check.mjs` (add `ONLY_VARIANTS=V0,V1`, `ONLY_BOARDS=Overview`, `NO_STATES=1`, `VERBOSE=1` to narrow or to see every pair).

## Result

| Check | Result |
|---|---|
| V0, static, 22 artboards, 6,683 elements | 0 differing property values |
| V1 (old app-wide stylesheets loaded), static | 0 differing property values after the four resets below (21 before) |
| Hover and focus, V1 on every board, V0 on the Overview board | 32 state/mode pairs, state applied in both copies in all 32, 0 differences |
| V2 (Frappe Desk stylesheet loaded) | not identical, by design of Frappe's own rules; see "Desk stack" below |
| Chart components against the boards, V0 | 11 charts, 0 differing pixels in every one (`scripts/analytics_chart_fidelity_check.mjs`) |

### Leaks found and closed in the generator

Found the way Home found its two (HOME6-0112): by comparing with the other stylesheets loaded. Each is a rule that the design system never sets, so it leaked through; each is now reset in `ANALYTICS.resets` to the value the board computes.

| Class | Leak | Source |
|---|---|---|
| `.kt-kpi-card` | 1px border | old `kt_industry_tokens.css` (the same leak Home found) |
| `.kt-tab` | body face (Barlow) on every tab and its icons | old `kt_industry_tokens.css` |
| `.kt-disclosure-title` | `letter-spacing: 0.01em`, `text-transform: uppercase` | old `kt_industry_tokens.css` |
| `.kt-empty` | `flex: 1; flex-direction: column; align-items/justify-content: center` | old `kt_industry_tokens.css` |
| `.btn`, `.btn-ghost` | padding `4px 8px` (height 26.8 px instead of 32.4 px), from `.btn:not(.btn-md):not(.btn-lg):not(.btn-xs)`, four classes against the design system's three | Frappe |
| `.kt-tab` | `margin-bottom: .5rem` (tab row 8 px taller), from `label { margin-bottom: .5rem }` | Bootstrap via Frappe |
| links | no underline, from `a { text-decoration: none }`; the boards keep links underlined (ANL §10A.1 rule 8) | Frappe |
| `.kt-icon` | `vertical-align: middle`, from `svg { vertical-align: middle }` | Frappe |

### Desk stack (V2): what is left

With the resets, and with Frappe's `--font-stack` given to the original so the typeface matches, V2 still differs, none of it from a design-system rule:

- **Frappe's body tracking.** Text in Desk inherits `letter-spacing: 0.02em` (0.28 px at 14 px). It widens text by a few per cent, wraps some labels one line earlier and makes the Overview artboard about 100 px taller. With tracking set to `normal` on the wrapper (test only, not shipped) the page heights and widths agree and the chart comparison drops to the edge pixel below. Home has the same difference. Not reset: KT-STD-001 v1.22 §2.4 says KenTender reads Frappe's settings and sets none of them. Open question for the owner.
- Frappe's global scrollbar, `-webkit-font-smoothing`, `text-size-adjust` and tap-highlight settings, and the longer fallback typeface list.
- The hidden radio inside each tab (`opacity: 0`): Frappe styles `input[type=radio]` (14 px box, a `::before`). It has no visible effect.
- Buttons about 2 px wider in Desk (not traced further), and `appearance`, `user-select` and `outline-width` on buttons, which have no visible effect.

The same chart-pixel comparison with the old stylesheets (V1), or Frappe's Desk stylesheet and tracking normalised (V2), differs only in the single last pixel row or column of the screenshot (maximum channel delta 15 of 255), a fractional-pixel edge of the capture box; the chart content is identical.

## Guards (kept running)

`kentender_core/kentender_core/tests/test_analytics_design_scope.py`, 17 tests, all green on `kentender-test.local`: stylesheet equals the generator's output; Home's file is still what the generator builds by default; every selector under `.kt-industry.kt-analytics`; chart source scoped on write; no `:root`, `@import`, `@font-face`, `@keyframes` or bare `html`/`body`; not loaded app-wide (`hooks.py` has no `kt_analytics_ds`); every class the six boards use and every class the chart components draw with is defined; the 15 data tokens equal the boards' block, identical in all six files and pinned value by value; the waiting ramp shares no colour with a category; no data colour equals a status colour, the chart rules and components never mention status, and the tone vocabulary is data roles only; the Frappe-variable fallbacks still equal Frappe's own; icon module equals the generator's output, five area icons as the boards draw them.
Mutation check: a stray `body` rule, a stray class and `--data-cat-1` set to the status-critical red made 6 of the tests fail; the file was then regenerated and the tests passed again.

## Not verified

- Not built through Frappe's esbuild pipeline: no `.bundle.js` imports the components yet (the page builder adds it). The Vue single-file components compile under `@vitejs/plugin-vue` in Vitest, the same compiler.
- Not seen in a live Desk page: the stylesheet is not loaded by any page yet. V2 above is the closest stack that can be built without one.
- Dark theme not checked (the boards are light only).
- No Firefox or WebKit run.

## Open design points found while porting (for the owner and the design owner)

1. **FU-ANL-10, the palette.** Pinned exactly as the boards draw it; still an unapproved proposal. Two proximities worth deciding on: category 1 (`#00857f`, hue 177) is 14 degrees from the status green (`#047857`, hue 163), and the waiting ramp (hue 33 to 35) sits next to the status amber (`#92610a`, hue 38). No value is equal; the colours are kept apart only by their values.
2. **Contrast of the number written inside a light waiting-band segment.** The board writes the count in `--data-seq-3` on `--data-seq-1`: 3.16:1, below 4.5:1 for 11 px bold. The other inks: seq-4 on seq-2 4.87, pair-strong on pair-tint 5.55, family-1 on family-3 8.06, white on category 1 4.51 and on category 3 3.91 (category 3 never carries inside text on the boards). Ported as drawn; the count is also in the hidden table and, for the stage bars, the value column.
3. **The "On the approved date" bar.** The board draws a 0.6 per cent hairline at the zero line for a value of 0; ported as drawn.
4. **Frappe's body tracking** (above).
