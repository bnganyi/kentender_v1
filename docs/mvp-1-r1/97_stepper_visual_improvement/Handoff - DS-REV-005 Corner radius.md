# Handoff — DS-REV-005 Corner radius

**For:** KenTender Industry design system (`styles.css`, `readme.md`) and the KT-STD-001 owner
**Status:** Proposed. Requested by the Project Owner on 6 October 2026 (“Multiple elements are too rounded”); options 1–4 accepted (“Yes”). Applied in the Industry pack, not yet approved.
**Governs:** KT-STD-001 v1.23 §2.4 (surface and radius values). Visual treatment falls under §2.6.11.
**Related:** DS-REV-003 Control shape (same §2.4 conflict, see §5). DS-REV-004 Journey position figure, aligned to KT-STD-001 v1.23 in the same session (see §6).

---

## 1. Problem

The page sheet and the notice banner carried 12px corners (`--radius-lg`). Against 2px controls (DS-REV-003) they read soft and informal, and the banner looked like a floating card rather than a strip on the sheet.

## 2. What changes

| Area | Before | After |
|---|---|---|
| Containers (sheet, cards, dialogs, panels, disclosures, record cards, figure frames) | 12px | 4px |
| Notice banners (`.kt-notice`, all variants) | 12px | 2px, same as controls |
| Blocked next step, right side | 6px | 4px (left stays square against the warning rule) |
| `--radius-md` (legacy) | 8px | 4px |
| Status chips (`.kt-status`) | 6px | Unchanged |
| Circles, journey bars, chart marks | — | Unchanged |

No new tokens. No class names change.

## 3. Resulting scale

| Radius | Token | Used by |
|---|---|---|
| 2px | `--radius-control` | Buttons, inputs, selects, textareas, date field, segmented control, notice banners |
| 4px | `--radius-lg`, `--radius-sm` | Sheet, cards, dialogs, panels, disclosures, record cards, figure frames, tags, checkboxes |
| 6px | literal on `.kt-status` | Status chips only, so a chip stays the softest element on the page |

Circles (avatars, radio dots, timeline dots, `.kt-spot`) and 2–3px bar marks are marks, not containers, and are outside the scale.

## 4. CSS

```css
:root {
  --radius-md: 4px;               /* was var(--border-radius, 8px); legacy, prefer --radius-lg */
  --radius-lg: 4px;               /* was var(--border-radius-lg, 12px) */
  --radius-xl: var(--radius-lg);  /* was var(--border-radius-lg, 12px) */
}
.kt-notice { border-radius: var(--radius-control); }   /* was var(--radius-lg) */
.kt-notice.is-warning.kt-next-step { border-radius: 0 var(--radius-lg) var(--radius-lg) 0; }   /* was 0 6px 6px 0 */
```

The radius tokens no longer read Frappe's `--border-radius` / `--border-radius-lg`, so a Frappe theme change does not alter KenTender corners.

Elements reached through `--radius-lg`: `.kt-page`, `.card`, `.dialog`, `.kt-disclosure` (outside a sheet; inside one it is already square), `.kt-record`, `.kt-panel`, `.blueprint`.

## 5. KT-STD-001 §2.4 amendment needed

KT-STD-001 v1.23 §2.4, *Verified Frappe v16 surface values*, still reads:

| Row | v1.23 says | Pack now draws | From |
|---|---|---|---|
| Corner radius: controls, buttons; cards | 8px; 12px | 2px; 4px | DS-REV-003, DS-REV-005 |
| Input fill | `#f3f3f3` (`--control-bg`) | White with a 1px `--color-control-border` outline | DS-REV-003 |

Proposed amendment: add a KenTender row beneath the Frappe values stating that KenTender controls are 2px and outlined, containers 4px, notice banners 2px and status chips 6px, and that these replace Frappe's radius and input-fill values on KenTender screens. One amendment covers both DS-REV-003 and DS-REV-005. Read-only and disabled field rows are unaffected.

## 6. DS-REV-004 alignment to KT-STD-001 v1.23

Done in the same session, recorded in `DS-REV-004 Journey position figure.md`:

- Position figure and compact tracker are now the standard tracker form in the pack (§2.9.2); the in-context guidance demo leads with the figure.
- All done: “5 of 5” with “Done” in `--status-live` (`.kt-journey-position.is-done`). None started: no figure, plain tracker with visible state lines.
- `.is-compact` is used only with the figure, since v1.23 allows hidden per-stage state text only where the figure is shown.
- v1.23 §12 states it does not approve the pack changes, so DS-REV-004 still needs its own sign-off.

## 7. Pack files

- `styles.css` — tokens and two rules above
- `readme.md` — new corner-scale rule; sheet, card and figure-frame radius wording corrected (12px, 12px, 10px → 4px)
- `DS-REV-005 Corner radius.md` — change note

## 8. Open points

- **Approval** of DS-REV-005 and DS-REV-004 pack changes.
- **§2.4 amendment** (§5 above), covering DS-REV-003 and DS-REV-005.
- **D3** (from DS-REV-004): 12px journey check at stroke 2.5 sits outside the 16/20/24px, stroke 1.75 icon rule. v1.23 allows the check as the state marker but does not address its size.
