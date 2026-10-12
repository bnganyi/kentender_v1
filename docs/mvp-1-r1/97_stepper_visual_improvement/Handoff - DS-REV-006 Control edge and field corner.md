# Handoff — DS-REV-006 Control edge and field corner

**For:** Claude Design (owner of the KenTender Industry design system) and the KT-STD-001 owner
**From:** the build session, 9 October 2026
**Status:** Decided and approved. KT-STD-001 v1.28 (approved 9 October 2026) is the governing text. The app already ships the change; the current Industry pack in this folder was updated to match; boards, proof pages and any older pack copies still need your attention (§9).
**Governs:** KT-STD-001 v1.28 §2.4, paragraph “Control edge and field corner”, and the split corner table. Related: DS-REV-003 Control shape, DS-REV-005 Corner radius.

---

## 1. In one paragraph

Form fields (input, select, textarea, date field) looked sharp and uncomfortable. The cause was not the line weight but the neutral grey hue of the outline together with the 2px corner. The outline cannot simply be made lighter: an enabled field is white on a white sheet, so its outline is the only thing that marks it, and it is already at the 3:1 floor. The Project Owner chose option C of five rendered options: keep the same lightness, give the outline a blue-grey hue (`#8590a6`), darken the hover outline to `#6b7690`, and round field corners from 2px to 4px so they match the 4px containers they sit in. Buttons, the segmented control and notice banners stay 2px. Focus, error, disabled and read-only treatments do not change.

## 2. Who decided what

| Decision | Owner's words (9 October 2026) | Recorded in |
|---|---|---|
| Trigger | Verbatim: “In another session, we changed the borders of data entry fields to try to soften them and reduce the weight. Unfortunately they still look very sharp and uncomfortable to they eye. … The focused one is okay, so I think the problem is the color. Suggest and enhancement” (typos as written) | this note |
| Choose option C and update the documentation | “Option C. But the documentation also needs to change” | KT-STD-001 v1.28 head paragraph and §2.4 |
| Approve v1.28; secondary button shares the field edge; fields 4px while buttons and banners stay 2px | “1. Approved”, “2. Sharing is accepted”, “3. Yes” | KT-STD-001 v1.28 approval record; register entry |

## 3. The five options that were shown

All five were the same sample form (resting, hover, focus, error, disabled) on a white card, so only the border varied.

| Option | Edge | Corner | Extra | On white | On ground `#f8f8f8` | Result |
|---|---|---|---|---|---|---|
| A · Current | `#909090` | 2px | none | 3.19:1 | 3.01:1 | Passes with no room left |
| B · Tinted | `#8590a6` | 2px | none | 3.21:1 | 3.02:1 | Passes |
| **C · Tinted, 4px — chosen** | `#8590a6`, hover `#6b7690` | 4px | none | 3.21:1 | 3.02:1 | Passes |
| D · C plus inner shadow | `#8590a6` | 4px | `inset 0 1px 2px rgba(23,30,48,.08)` | 3.21:1 | 3.02:1 | Passes; not adopted |
| E · Simply lighter | `#b3b9c6`, hover `#99a1b3` | 4px | none | 2.0:1 | 1.9:1 | Fails; rejected |

Option D is the fallback if C still feels flat. Do not add the inner shadow unless the Project Owner asks.

## 4. Final values

| Token | Value | Contrast on white | On ground `#f8f8f8` | Used by |
|---|---|---|---|---|
| `--color-control-border` | `#8590a6` | 3.21:1 | 3.02:1 | Resting outline of `.input`, `.date-field`, `.seg`, `.btn-secondary` |
| `--color-control-border-hover` | `#6b7690` | 4.55:1 | 4.28:1 | Hover outline of `.input`, `.date-field` (addendum, 9 Oct 2026) and `.btn-secondary` |
| `--radius-field` (new) | 4px | — | — | `.input`, `.date-field` |
| `--radius-control` | 2px (unchanged) | — | — | `.btn`, `.seg`, `.kt-notice` |
| `--radius-lg`, `--radius-sm` | 4px (unchanged) | — | — | Containers, tags, checkboxes |
| `.kt-status` | 6px literal (unchanged) | — | — | Status chips stay the softest element |

Contrast figures were computed with the WCAG relative-luminance formula for this change. The 3:1 minimum for the edge that identifies a control is the WCAG 2.x non-text contrast criterion (1.4.11); that criterion has not been verified against the primary source, so treat 3:1 as the working floor, not as a certified citation.

## 5. State matrix after the change

| State | Outline | Corner | Notes |
|---|---|---|---|
| Resting, editable | `#8590a6` | 4px | White fill (DS-REV-003 / KT-STD-001 v1.25) |
| Hover, editable | `#6b7690` | 4px | Only when not disabled and not focused |
| Focus | Accent, 2px, inset ring, no outer halo | 4px | Unchanged. The app draws it as a 2px accent border with an inset ring; the pack's `:focus-visible` rule is simpler (see §8) |
| Error | `--kt-color-critical` (`#b3261e`) via `aria-invalid="true"` | 4px | Unchanged; defined in the Planning stylesheet, not in the pack (see §8) |
| Disabled | `--color-control-border-disabled` `#c7c7c7`, grey fill, muted text | 4px | Unchanged colours; the corner follows the field |
| Read-only | Grey fill, no outline | 4px | Unchanged |
| Table-row cell input | No border, square | 0 | Unchanged: the cell rules frame it |
| Secondary button, resting | `#8590a6` | 2px | Colour changed (shared token); corner unchanged |
| Secondary button, hover | `#6b7690` + `--color-neutral-100` fill | 2px | Hover outline is new (was neutral-600 in the app) |
| Danger secondary, hover | `--status-critical` | 2px | Unchanged |
| Disabled button | `--color-neutral-300`, no fill | 2px | Unchanged |

## 6. CSS, as it now stands in the pack

```css
:root {
  --color-control-border: #8590a6;        /* was var(--gray-600, #7c7c7c) in the pack */
  --color-control-border-hover: #6b7690;  /* new */
  --radius-control: 2px;                  /* buttons, segmented control, notice banners */
  --radius-field: 4px;                    /* new: inputs, selects, textareas, date field */
}
.btn-secondary:hover { background: var(--color-neutral-100); border-color: var(--color-control-border-hover); }
.input { border: 1px solid var(--color-control-border); border-radius: var(--radius-field); }
.input:hover:not(:disabled):not(:focus-visible) { border-color: var(--color-control-border-hover); }
.date-field { border: 1px solid var(--color-control-border); border-radius: var(--radius-field); }
.btn, .seg { border-radius: var(--radius-control); }
.input, .date-field { border-radius: var(--radius-field); }
```

`select.input` and `textarea.input` inherit `.input`, so they take the 4px corner and the new edge with no extra rule.

## 7. What was changed, and where

| Place | Change | State |
|---|---|---|
| `scripts/home_design_css.py`, `control_shape()` | Source of the app's control shape: new colours and `--radius-field`; docstring explains the choice | Done |
| `kentender_core/.../public/css/kt_industry_tokens.css`, `.../js/home/kt_home_ds.bundle.css`, `.../js/analytics/kt_analytics_ds.bundle.css` | Regenerated from the generator; never hand-edited. `make design-css-check` passes | Done, live on dev |
| `tests/ui/smoke/home/home-style-parity.spec.ts` | The “Continue (standard)” button's border is pinned to `rgb(133, 144, 166)` as an approved departure from the Home board | Done; passes |
| `_ds/kentender-industry-82d82607-…/styles.css` and `readme.md` in this folder | Tokens, hover rule, field radius, split shape rule; readme token line, controls paragraph, corner scale | Done |
| KT-STD-001 v1.28 | §2.4 paragraph “Control edge and field corner”, split corner table, change type, approval | Approved 9 October 2026 |

Checked live on the test site as the Procurement Planner: the Financial year select on the Planning page computes border `rgb(133, 144, 166)` and radius `4px`.

## 8. Things you should know before you touch the pack

1. **The pack had already drifted from the app.** The pack's `--color-control-border` was `var(--gray-600, #7c7c7c)` (4.2:1). The app has used `#909090` (3.2:1) since 6 October, when the Project Owner said the darker grey “read as black next to the label”; that override lives in the generator, not the pack. The pack now carries the new blue-grey, so the two agree again, but note that the pack's value had not been the shipped value.
2. **Focus differs between pack and app.** The pack's generic `:focus-visible` is a 2px accent outline with `outline-offset: 0` for inputs. The app overrides it so the field's own border turns accent at 2px with an inset ring and no outer halo. The Project Owner called the focused field “okay”, so do not redesign focus as part of this change. If you want the pack to match the app, port the app's rule from `control_shape()` as a separate revision.
3. **The error outline is not in the pack.** It exists only as `.kt-pln .input[aria-invalid="true"]` in the Planning stylesheet (`--kt-color-critical`). A shared error field state would belong in the pack; this change does not add one.
4. **The secondary button now shares the field's edge colours.** This follows from the shared token and was accepted by the Project Owner (“Sharing is accepted”). If you ever want them to differ, introduce a separate token rather than overriding per component.
5. **Mixed corners are intentional.** A 4px field sits beside a 2px button in filter rows and sign-up rows. The Project Owner approved this as drawn in option C. Flag it back if it looks uneven in a dense row; do not quietly change either value.
6. **Segmented control.** It stays 2px (`--radius-control`) because it is a control group, not a text field. KT-STD-001 v1.24 listed it with inputs at 2px; v1.28 split that row, so it remains with buttons.

## 9. What is left for Claude Design

| # | Item | Why | Suggested action |
|---|---|---|---|
| 1 | Proof and component pages (`components/forms.html`, `components/buttons.html`, `proof/control-states.html`, `foundations/frappe-surfaces.html`) | The readme refers to them; they were not in the repository copy of the pack, so they could not be updated here | Redraw field and secondary-button states with the §4 values and the §5 matrix; add the hover outline to the control-states proof |
| 2 | Boards that draw fields at 2px or `#909090` / `#7c7c7c` | Boards are the build source; the app now departs from them | Re-export affected boards. Until then each module's design-fidelity gate may list this as an approved departure (the Home gate already does) |
| 3 | Frozen pack copies inside module `design/` folders (Planning, Tenders, Budget, Strategy, Requisitions, Award, Bid Opening/Evaluation/Submission, System setup, Needs, Oversight, Analytics) and the Home pack at `18_home_page/design/_ds/…` that the generator reads | They are historical snapshots with older control values | Leave as history, or refresh from the current pack when each module's boards are next regenerated. Nothing in the app depends on them being refreshed, because the app takes the control shape from the generator |
| 4 | Dark theme | KenTender is light only today; no dark value was chosen for the new edge | None now. If a dark theme is introduced, pick an edge pair that keeps 3:1 against the dark sheet |
| 5 | An optional change note inside the pack, as DS-REV-005 had | The pack folder holds no per-revision notes at present | Copy §2–§6 of this document if you want one |

## 10. How to verify a redraw

1. Resting field edge reads `#8590a6` (`rgb(133, 144, 166)`) at 1px; hover reads `#6b7690` (`rgb(107, 118, 144)`).
2. Field corner radius reads 4px; button and segmented-control radius reads 2px; notice banner 2px; status chip 6px.
3. Focus, error, disabled and read-only fields look exactly as before.
4. A secondary button beside a field shows the same resting edge colour and the same hover edge colour.
5. In the app, `make design-css-check` reports the three generated stylesheets as ok after any change to `control_shape()`. Never hand-edit those three files.

## 11. Not verified

- WCAG 1.4.11 and its 3:1 figure, against the primary source.
- Any dark-theme rendering.
- Appearance on screens other than the Planning workspace and the Home parity page (the change is global through the shared stylesheet, so other screens inherit it; they were not each inspected).
- The proof pages named in §9, which were not available in the repository.
