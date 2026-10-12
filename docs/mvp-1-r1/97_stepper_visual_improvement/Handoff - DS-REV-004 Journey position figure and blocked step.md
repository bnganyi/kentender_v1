# DS-REV-004 — Journey position figure and blocked next step

**For:** KenTender Industry design system (`styles.css`, `readme.md`, `components/guidance.html`)
**Status:** Proposed. Design approved by the Project Owner on 6 October 2026, in reply to option 2e: “2e it is. Approved”. Not yet in the shared pack.
**Reference artboards:** `Stepper Iterations.dc.html` in the *Stepper visual improvement iteration* project: 2a (in context), 2b (first stage), 2c (blocked), 2d (last stage).
**Governs:** KT-STD-001 §2.9.1, §2.9.2 and §2.9.3. Visual treatment falls under §2.6.11. The position figure also needs the KT-STD change in the companion handoff before release (see §6).
**Supersedes in part:** *Handoff — Journey tracker and next-step block* (26 Sep 2026), §3 anatomy and the **Your turn, blocked** row of §4. Everything else in it stays.

---

## 1. Problem

The current tracker is five equal 4px slabs with labels under them. You can only tell how far the record has got by reading the numbers. Nothing in the row stands out as "you are here", and the green, indigo and grey bars all have the same weight.

## 2. What changes

| Area | Before (pack today) | After |
|---|---|---|
| Position | Shown only by colour and the stage numbers | A position figure, **3 of 5**, at the left with the holder beneath |
| Bars | 4px, 2px radius, 6px gutters | 6px, 3px radius on every segment, 3px gutters |
| Stage labels | 14px, with the number before every stage | 13px. Done stages swap their number for a check |
| State line per stage | Visible: “✓ Done”, “Current · …”, “Not started” | Kept in the markup for assistive technology only. The figure states the current state |
| Blocked next step | Full warning notice: 12px radius, icon, tinted box | Warning tint with a 3px warning left rule, square on the rule side, no icon |

No new tokens. Class names that exist today are kept.

---

## 3. Position figure + compact tracker

### Markup

```html
<div class="kt-journey-lead">
  <div class="kt-journey-position" aria-hidden="true">
    <span class="kt-journey-position-label">Stage</span>
    <span class="kt-journey-position-value">
      <span class="kt-journey-position-n">3</span>
      <span class="kt-journey-position-of">of 5</span>
    </span>
    <span class="kt-journey-position-state">Current · Amina Hassan</span>
  </div>
  <ol class="kt-journey is-compact" aria-label="Tender journey" style="--kt-journey-n:5">
    <li class="kt-journey-stage is-done">
      <span class="kt-journey-bar" aria-hidden="true"></span>
      <span class="kt-journey-title">
        <svg class="kt-journey-check" aria-hidden="true" viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg>
        Prepare Tender
      </span>
      <span class="kt-journey-state">Done</span>
    </li>
    <li class="kt-journey-stage is-current" aria-current="step">
      <span class="kt-journey-bar" aria-hidden="true"></span>
      <span class="kt-journey-title"><span class="kt-journey-num">3</span>AO publication authorisation</span>
      <span class="kt-journey-state">Current · Amina Hassan</span>
    </li>
    <!-- not started: number + title, state "Not started" -->
  </ol>
</div>
```

The figure is `aria-hidden` because the `<ol>` already gives the same position (through `aria-current` and the state text), so a screen reader hears it once.

### CSS (add after the existing `.kt-journey-*` rules)

```css
.kt-journey-lead { display: grid; grid-template-columns: 200px minmax(0, 1fr); gap: 32px; align-items: start; }
.kt-journey-position { display: grid; gap: 4px; padding-right: 24px; border-right: 1px solid var(--color-divider); }
.kt-journey-position-label { font-size: 12px; font-weight: 600; color: var(--color-neutral-700); }
.kt-journey-position-value { display: flex; align-items: baseline; gap: 6px; line-height: 1; font-variant-numeric: tabular-nums; }
.kt-journey-position-n { font-size: 44px; font-weight: 600; color: var(--color-figure); }
.kt-journey-position-of { font-size: 20px; font-weight: 500; color: var(--color-neutral-600); }
.kt-journey-position-state { margin-top: 6px; font-size: 12px; font-weight: 600; color: var(--color-figure); }
.kt-journey-position.is-blocked .kt-journey-position-n,
.kt-journey-position.is-blocked .kt-journey-position-state { color: var(--status-attention); }

.kt-journey.is-compact { gap: 3px; padding-top: 6px; }
.kt-journey.is-compact .kt-journey-stage { gap: 10px; }
.kt-journey.is-compact .kt-journey-bar { height: 6px; border-radius: 3px; }
.kt-journey.is-compact .kt-journey-title { gap: 5px; padding-right: 12px; font-size: 13px; }
.kt-journey.is-compact .kt-journey-num { font-family: inherit; font-size: inherit; font-variant-numeric: tabular-nums; }
.kt-journey.is-compact .is-current .kt-journey-title,
.kt-journey.is-compact .is-blocked .kt-journey-title { font-weight: 600; }   /* was 700 */
.kt-journey-check { flex: none; width: 12px; height: 12px; transform: translateY(1px); fill: none;
  stroke: var(--status-live); stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; }
.kt-journey.is-compact .kt-journey-state { position: absolute; width: 1px; height: 1px; overflow: hidden;
  clip: rect(0 0 0 0); white-space: nowrap; }
```

The colour rules for done, current, blocked and not started stay as they are today. The guidance region gap goes from `--space-5` (17px) to 28px in the artboards; the closest token is `--space-8` (27.2px).

### State matrix

| Record state | Figure | Figure state line | Track |
|---|---|---|---|
| Current at stage *n* | *n* of N, `--color-figure` | Current · {holder} | Stages before *n* done (check), *n* indigo, the rest neutral |
| Blocked at stage *n* | *n* of N, `--status-attention` | Blocked · {holder} | Stage *n* amber with its number in amber |
| All done | **Not drawn yet — decision D1** | — | All green with checks |
| None started | **Not drawn yet — decision D1** | — | All neutral |

### Responsive

- Under 600px of sheet width, the existing `.kt-journey.is-reduced.is-fallback` takes over unchanged. Its text, `{stage} · {n} of {N} · {holder}`, already says the same thing as the figure.
- Between 600 and about 760px, five labels sit in roughly 350px. Proposed but not tested: `@container (max-width: 760px) { .kt-journey-lead { grid-template-columns: 1fr; } .kt-journey-position { border-right: 0; padding-right: 0; } }`.

### Forced colours and print

The existing journey blocks in both `forced-colors` and `print` need `.is-compact` selectors added. Bars switch to `border-top: 6px` (it is 4px today). In forced-colours mode the check uses `stroke: CanvasText`. In print, the per-stage state text is shown again (`position: static`) so the printed page carries state as text.

---

## 4. Blocked next step

### Markup (no icon)

```html
<div class="kt-notice is-warning kt-next-step" role="status">
  <div class="kt-notice-body">
    <div class="kt-next-step-label">Your turn, blocked</div>
    <p class="kt-next-step-headline">{headline from the change unit}</p>
    <div class="kt-next-step-fixes"><button class="btn btn-primary">{main fix}</button></div>
  </div>
</div>
```

### CSS (replaces how the notice draws when it is a next step)

```css
.kt-notice.is-warning.kt-next-step { display: grid; gap: 3px; padding: 12px 16px 14px 14px;
  border-left: 3px solid var(--status-attention); border-radius: 0 6px 6px 0; background: var(--status-attention-bg); }
.kt-notice.is-warning.kt-next-step .kt-notice-icon { display: none; }
.kt-notice.is-warning.kt-next-step .kt-next-step-label { color: var(--status-attention); }
@media (forced-colors: active) { .kt-notice.is-warning.kt-next-step { border: 1px solid CanvasText; border-left-width: 3px; } }
```

- The block now has the same shape as Your turn, Waiting and Done: a 3px left rule, label, headline. Only the tint and the colour of the rule mark it as blocked.
- The warning rule is a status mark, not an accent rule, so it doesn't count toward the two-accent-rule limit. A blocked page draws no Your-turn line, so the page still has at most one task rule.
- Contrast, worked out by hand and not yet in `foundations/contrast.html`: `--status-attention` #92610a on `--status-attention-bg` #fdf0da is about 4.7:1, which passes AA for the 12px/700 label.
- `.kt-notice` used anywhere else (page advisories) is unchanged.

---

## 5. Pack updates

- `readme.md`, Components table: add `.kt-journey-lead`, `.kt-journey-position` (+ `-label`, `-value`, `-n`, `-of`, `-state`; `.is-blocked`), `.kt-journey.is-compact` and `.kt-journey-check`. Amend the `.kt-next-step` row: "blocked = `.kt-notice.is-warning.kt-next-step`, drawn as a 3px warning rule over the warning tint, no icon".
- `components/guidance.html`: add the position-figure tracker for current at 1, current at 3, blocked at 2 and current at 5. Replace both blocked next-step demos with the no-icon form. Keep the Do/Don't pair.
- `foundations/contrast.html`: add the pairs `--status-attention` on `--status-attention-bg` and `--color-figure` on white at 44px.
- Keep the old 4px tracker as the default `.kt-journey` until KT-STD approves the figure. `.is-compact` and `.kt-journey-lead` are opt-in.

## 6. Open points

- **D1 — All done / none started.** The figure isn't defined for either. Recommendation: when every stage is done, show “N of N” with “Done” in `--status-live`. When nothing has started, leave the figure out and keep the track.
- **D2 — Visible per-stage state text.** KT-STD-001 §2.6.7 says every state has explicit text. The compact track shows done with a check and not started with nothing visible. The text exists only for assistive technology. Recommendation: accept this. The figure names the current stage's state, and a not-started stage is the default. The companion KT-STD handoff carries this exception for owner approval. If the owner declines, bring back the 12px state line and keep everything else.
- **D3 — Check icon size.** The pack allows Lucide icons at 16, 20 or 24px with stroke 1.75. The artboards use 12px at stroke 2.5 so the check sits at text height. Recommendation: record a 12px state-marker exception.
- **Artboard corrections before release.** In artboard 2c, the label "Blocked", the headline and the "Open budget line" button are placeholder text I wrote. The fix button is also secondary. Use **Your turn, blocked**, the change unit's headline and fix labels, and a primary button on the main fix, as in the approved handoff of 26 Sep 2026.
