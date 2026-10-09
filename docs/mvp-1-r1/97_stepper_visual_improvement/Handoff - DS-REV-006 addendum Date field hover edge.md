# Handoff — DS-REV-006 addendum: date field hover edge

**For:** the KT-STD-001 owner and the build session
**From:** Claude Design, 9 October 2026
**Status:** Approved by the Project Owner, 9 October 2026. Applied in the Industry pack. Not yet in KT-STD-001 (v1.28 does not include it; see §5).
**Approval record:** Project Owner, 9 October 2026, verbatim: “APPROVED”.
**Previous status (retained as history):** Applied in the Industry pack, pending Project Owner approval. Not in KT-STD-001 v1.28.
**Extends:** DS-REV-006 Control edge and field corner; KT-STD-001 v1.28 §2.4 "Control edge and field corner".

## 1. Gap

DS-REV-006 §4 and §5 give the hover outline `--color-control-border-hover` (`#6b7690`) to `.input` and `.btn-secondary` only. `.date-field` takes the same resting edge (`#8590a6`) and the same 4px `--radius-field`, but it has no hover state. Next to a select or text input in the same form, it looks inert on hover.

## 2. Change

```css
.date-field:hover:not([aria-disabled="true"]):not(:focus-within) {
  border-color: var(--color-control-border-hover);
}
```

`.date-field` is a wrapper, not a native `<input>`, so the guards differ from `.input`'s:
- `:not(:focus-within)` stands in for `:not(:focus-visible)`, so focus keeps its accent treatment.
- `:not([aria-disabled="true"])` stands in for `:not(:disabled)`. A disabled date field must carry `aria-disabled="true"`.

No new token. Contrast is unchanged from DS-REV-006: 4.55:1 on white, 4.28:1 on `#f8f8f8`.

## 3. State matrix rows (addition to DS-REV-006 §5)

| State | Outline | Corner | Notes |
|---|---|---|---|
| Date field, hover | `#6b7690` | 4px | New. Only when not disabled and not focused |
| Date field, disabled | Unchanged | 4px | Requires `aria-disabled="true"` to suppress hover |

## 4. Where it was applied

| Place | Change |
|---|---|
| `styles.css` | Rule above, marked approved 9 October 2026 (was marked "pending owner approval") |
| `readme.md` | Token line lists `.date-field` as a user of the hover edge and notes the `aria-disabled` requirement (was noted as pending) |
| `proof/control-states.html` | Date field at rest and on hover |

## 5. Decision

Approved by the Project Owner on 9 October 2026 (“APPROVED”).

Original request (retained as history): Approve the date field hover edge as part of KT-STD-001 §2.4. Recommendation: approve. It completes the field set with no new value.

Required follow-up, now that it is approved: add `.date-field` to the hover line of KT-STD-001 §2.4 and to the DS-REV-006 §4 `--color-control-border-hover` "Used by" cell. In the app, add the rule to `control_shape()` in `scripts/home_design_css.py`, regenerate, and run `make design-css-check`. (Had it been rejected: delete the rule and the readme note.)

## 6. Not verified

- Whether the app's date control is built from `.date-field` or from a native `<input type="date">` styled as `.input`. If it is the latter, it already has the hover edge and the app needs no change.
- Whether every disabled date field in the app sets `aria-disabled="true"`.

---

## 7. Build-session follow-up (9 October 2026)

- **Pack:** `styles.css` rule and `readme.md` token line applied in this folder's pack (they were not yet in the repository copy). `proof/control-states.html` is not in the repository copy, so it is not changed here.
- **App:** the rule is added to `control_shape()` in `scripts/home_design_css.py`; the three stylesheets regenerated; `make design-css-check` passes. The generated Industry stylesheet carried an older `.date-field:hover` (neutral-400 edge, from the Home pack snapshot the generator reads), which the new rule outranks.
- **§6 answered:** no app screen uses a `.date-field` element. The app's date fields are a native `<input type="date" class="input">` (41 uses), sometimes inside `.req-date-field` or `.kt-date-field` wrappers that only position a placeholder. Those already take the `.input` hover edge, so the addendum changes nothing visible in the app today. Disabled state is set with the native `disabled` attribute, not `aria-disabled`, which is correct for `<input>`; no `.date-field` wrapper is disabled anywhere.
- **KT-STD-001:** v1.29 states it (see its change report).
