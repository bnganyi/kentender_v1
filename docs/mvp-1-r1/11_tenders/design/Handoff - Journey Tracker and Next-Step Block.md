# Handoff — Journey tracker and next-step block

**For:** KenTender Industry design system (`styles.css`, `readme.md`, `components/`)
**Governs:** KT-STD-001 v1.8 §2.9.1 (next-step block), §2.9.2 (journey tracker), §2.9.3 (restraint)
**Reference implementation:** `TenderGuidance.dc.html` in the KenTender Tenders project (used on TPR-DES-03 … TPR-DES-13)
**Status:** Approved by the Project Owner for formalisation, 26 Sep 2026, including the 3px accent rule on the **Your turn** line.

---

## 1. What to add

Two classes that always appear together, as one region at the top of a record's content column:

| Class | Job | Answers (§2.6.1) |
|---|---|---|
| `.kt-journey` | The formal lifecycle stages of this record, with one marker each | Where does this record stand? |
| `.kt-next-step` | For the signed-in actor: your turn, blocked, waiting, done, or nothing | Whose turn is it, and what happens next? |

They are wrapped in `.kt-guidance`, which sits **below the page header and above the first working region** inside the `.kt-page` sheet. They add no card, shadow or band.

Add a row for each to the Components table in `readme.md`, plus a new `components/guidance.html` page that shows every state below.

---

## 2. Region: `.kt-guidance`

```css
.kt-guidance {
  display: grid;
  gap: 18px;
  padding: 20px 24px 22px;          /* use --space-* equivalents */
  border-bottom: 1px solid var(--color-divider);
}
```

- One per record screen. Never repeated, never placed in a table row, a dialog or a panel.
- **Allowed on:** Record detail, Review or decision, and Form or editor archetypes.
- **Not allowed on:** Registers or work workspaces, Setup surfaces, focused dialogs or panels, full-page denial, load or error states (§2.9.3 rule 4).
- The region **replaces** existing status wording and never adds to it (rule 1). Each change unit names what it replaces.

---

## 3. Journey tracker: `.kt-journey`

### Anatomy

```
┌── bar ──┐┌── bar ──┐┌──── bar ────┐┌── bar ──┐┌── bar ──┐   4px segment, 6px gutters
1 Prepare   2 HOPF     3 AO publication 4 Confirm  5 Manage     number + stage label
  Tender      approval   authorisation    publication open Tender
✓ Done      Current ·  Not started      Not started  Not started  state line
            Charles Mutiso
```

- An `<ol>` in a grid of N equal columns (`repeat(N, minmax(0,1fr))`, gap 6px). Labels wrap **inside** their column, so the row never overflows horizontally.
- Each `<li>` holds three rows: a 4px **bar**, then the **number and label**, then a **state line**.
- Stages come from the change unit, in order. The Tenders set is: Prepare Tender · HOPF approval · AO publication authorisation · Confirm publication · Manage open Tender.

### Markup

```html
<ol class="kt-journey" aria-label="Tender journey">
  <li class="kt-journey-stage is-done">
    <span class="kt-journey-bar" aria-hidden="true"></span>
    <span class="kt-journey-title"><span class="kt-journey-num">1</span>Prepare Tender</span>
    <span class="kt-journey-state">✓ Done</span>
  </li>
  <li class="kt-journey-stage is-current" aria-current="step">
    <span class="kt-journey-bar" aria-hidden="true"></span>
    <span class="kt-journey-title"><span class="kt-journey-num">2</span>HOPF approval</span>
    <span class="kt-journey-state">Current · Charles Mutiso</span>
  </li>
  <li class="kt-journey-stage">
    <span class="kt-journey-bar" aria-hidden="true"></span>
    <span class="kt-journey-title"><span class="kt-journey-num">3</span>AO publication authorisation</span>
    <span class="kt-journey-state">Not started</span>
  </li>
  <!-- … -->
</ol>
```

### CSS

```css
.kt-journey { list-style: none; margin: 0; padding: 0; display: grid;
  grid-template-columns: repeat(var(--kt-journey-n, 5), minmax(0, 1fr)); gap: 6px; }
.kt-journey-stage { display: grid; gap: 8px; align-content: start; min-width: 0; }
.kt-journey-bar   { display: block; height: 4px; background: var(--color-neutral-300); }
.kt-journey-title { display: flex; gap: 6px; align-items: baseline; font-size: 14px;
  line-height: 1.3; font-weight: 500; color: var(--color-neutral-700); text-wrap: pretty; }
.kt-journey-num   { flex: none; font-family: var(--font-heading); font-size: 15px;
  font-weight: 600; color: var(--color-neutral-600); }
.kt-journey-state { padding-left: 16px; font-size: 12px; line-height: 1.3; font-weight: 600;
  color: var(--color-neutral-600); }

/* Done */
.kt-journey-stage.is-done .kt-journey-bar   { background: var(--status-live); }
.kt-journey-stage.is-done .kt-journey-title,
.kt-journey-stage.is-done .kt-journey-num   { color: var(--color-text); }
.kt-journey-stage.is-done .kt-journey-state { color: var(--status-live); }

/* Current: the only accent in the tracker */
.kt-journey-stage.is-current .kt-journey-bar   { background: var(--color-accent); }
.kt-journey-stage.is-current .kt-journey-title,
.kt-journey-stage.is-current .kt-journey-num,
.kt-journey-stage.is-current .kt-journey-state { color: var(--color-accent-700); }
.kt-journey-stage.is-current .kt-journey-title { font-weight: 700; }

/* Blocked */
.kt-journey-stage.is-blocked .kt-journey-bar   { background: var(--status-attention); }
.kt-journey-stage.is-blocked .kt-journey-num,
.kt-journey-stage.is-blocked .kt-journey-state { color: var(--status-attention); }
.kt-journey-stage.is-blocked .kt-journey-title { color: var(--color-text); font-weight: 700; }
```

### Marker states

| Class | Bar | State line | Holder shown |
|---|---|---|---|
| (none) | `--color-neutral-300` | **Not started** | No |
| `.is-done` | `--status-live` | **✓ Done** | No. Past actors belong in History (Level 3) |
| `.is-current` | `--color-accent` | **Current · {holder}** | Yes, if supplied |
| `.is-blocked` | `--status-attention` | **Blocked · {holder}** | Yes, if supplied |

- Exactly one stage is current or blocked, except when every stage is done.
- The state line is **visible text**. Colour is never the only carrier of state (§2.6.7).

### Reduced form: `.kt-journey.is-reduced`

Use it when the container is under about 600px, or when a change unit states it because the full row would push the first working region out of the first 1440 × 1024 view (rule 5).

```html
<div class="kt-journey is-reduced">
  <div class="kt-journey-bars" aria-hidden="true"><span class="is-done"></span><span class="is-current"></span><span></span><span></span><span></span></div>
  <p><strong>HOPF approval</strong> · 2 of 5 · Charles Mutiso</p>
</div>
```

The mini bars use the same four colours (4px tall, 4px gap). The text follows the pattern `{current stage} · {position} of {N} · {holder}`, with the stage in `--color-accent-700` at weight 700 and the rest in `--color-neutral-700`.

### Don'ts (rule 3)

- No card per stage, no dates, no past-actor names, no descriptions, and no icons beyond the check in the state line.
- No connector lines or arrows. The gutter between bars does that job.
- The tracker is orientation only. Stages are not links, and they never navigate between editor sections.
- A computed condition (for example budget fit) is never a stage. It shows as the current stage's `.is-blocked` marker and in the next-step block.

---

## 4. Next-step block: `.kt-next-step`

Exactly one kind per screen, or none (§2.9.1).

### Kinds

| Kind | Class | Container | Label | Rule | Actions inside |
|---|---|---|---|---|---|
| Your turn | `.kt-next-step.is-turn` | None | **Your turn**, `--color-accent-700` | **3px `--color-accent` left rule** | None. The screen's existing primary action does the work |
| Your turn, blocked | `.kt-notice.is-warning.kt-next-step` | Warning notice (the only container) | **Your turn, blocked** | Notice's own | One button per fix. Primary on the main fix, secondary on the rest |
| Waiting on someone | `.kt-next-step.is-waiting` | None | **Waiting on someone**, `--color-neutral-700` | 3px `--color-neutral-400` | None |
| Done | `.kt-next-step.is-done` | None | **Done**, `--color-neutral-700` | 3px `--color-neutral-400` | None |
| Not involved | — | — | — | — | The element is omitted |

### Markup

```html
<!-- Your turn -->
<div class="kt-next-step is-turn">
  <div class="kt-next-step-label">Your turn</div>
  <p class="kt-next-step-headline">Decide whether to approve this Tender package.</p>
  <!-- optional, at most one sentence -->
  <p class="kt-next-step-sentence">These are available options, not overdue work.</p>
</div>

<!-- Your turn, blocked -->
<div class="kt-notice is-warning kt-next-step" role="status">
  <svg class="kt-notice-icon">…lucide triangle-alert, stroke 1.5…</svg>
  <div class="kt-notice-body">
    <div class="kt-next-step-label">Your turn, blocked</div>
    <p class="kt-next-step-headline">Enter the inspection and acceptance location.</p>
    <div class="kt-next-step-fixes">
      <button class="btn btn-primary">Review contract terms</button>
    </div>
  </div>
</div>
```

### CSS

```css
.kt-next-step           { display: grid; gap: 3px; }
.kt-next-step.is-turn,
.kt-next-step.is-waiting,
.kt-next-step.is-done   { border-left: 3px solid var(--color-neutral-400); padding: 2px 0 2px 14px; }
.kt-next-step.is-turn   { border-left-color: var(--color-accent); }
.kt-next-step-label     { font-size: 12px; font-weight: 700; color: var(--color-neutral-700); }
.kt-next-step.is-turn .kt-next-step-label { color: var(--color-accent-700); }
.kt-next-step-headline  { margin: 0; font-size: 17px; font-weight: 600; line-height: 1.4;
  color: var(--color-text); text-wrap: pretty; }
.kt-next-step-sentence  { margin: 0; font-size: 14px; color: var(--color-neutral-700); }
.kt-next-step-fixes     { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 7px; }
.kt-notice.kt-next-step .kt-next-step-label,
.kt-notice.kt-next-step .kt-next-step-sentence { color: inherit; }
```

### Content rules

- The headline is copied exactly from the change unit's variant row. If the row doesn't supply it, the block isn't drawn (rule 8).
- Blocked: every blocker for the variant appears together, once. Disabled buttons elsewhere don't repeat the reason (§2.6.5). The figures behind a blocker appear once, in the working region where they are fixed.
- A fix owned by another responsibility is a **hand-off** button that names the responsibility and the person, for example *Ask Amina Hassan (Accounting Officer) to consider cancellation*.
- Page links such as View history or View cancellation requirements stay **outside** the block.
- Waiting uses the pattern **{responsibility} {name} … since {recorded instant}**, and leaves out any part the fixture doesn't supply.

---

## 5. Accent budget — update to `readme.md`

The system allows **at most two accent rules per page** (`.kt-task-row`, `.kt-decision`). The 3px accent rule on `.kt-next-step.is-turn` **counts as the page's `.kt-task-row`**, since it is the Level-1 rule on the actor's task. A page that shows a Your-turn line must not add another `.kt-task-row`. It may still add one `.kt-decision` top rule.

Suggested readme wording:

> `.kt-next-step.is-turn` carries the actor's 3px accent left rule and counts as the page's `.kt-task-row`. Waiting and Done use the same rule in `--color-neutral-400`. Only **Your turn, blocked** takes a container (`.kt-notice.is-warning`).

**KT-STD-001 note.** §2.9.1 says Your turn has "no container of its own". A left rule isn't a container, so this is compatible. However, §2.9.3 rule 6 ("no accent rules … outside the blocked container") needs one clarifying line at the next KT-STD revision: *"except the Your-turn line's 3px left rule, which is the page's single task rule."* Raise this with the KT-STD owner so the standard and the system say the same thing.

---

## 6. Accessibility

- `.kt-journey` is an `<ol>` with an `aria-label` naming the record type, for example "Tender journey". The current stage gets `aria-current="step"`.
- Bars are `aria-hidden`. The state line carries the meaning in text.
- The blocked notice uses `role="status"`. Focus doesn't move to it on load.
- Contrast: labels are ink or `--color-neutral-700` on white. The accent-700 and status text steps clear 4.5:1 at 12px/600.
- **Forced colours:** bars fall back to `CanvasText` borders, so give `.kt-journey-bar` `border-top: 4px solid` in the `forced-colors` block. State stays readable from the state line.
- **Print:** bars print as black or grey, and the state line prints as text. Nothing is hidden.

---

## 7. Responsive

| Container width | Behaviour |
|---|---|
| ≥ 600px | Full grid. Labels wrap within columns. A fixed row height isn't needed |
| < 600px (or when the change unit states it) | `.is-reduced` single line with mini bars |
| 390px | Reduced form, no horizontal scroll. The next-step text stays with its action |

Switch using a container query on `.kt-guidance` (`@container (max-width: 600px)`) rather than a viewport media query, so the switch follows the sheet width.

---

## 8. Companion pattern: dependent fields — `.kt-choice-row` / `.kt-dependent`

This came out of the same review. It fixes the misalignment of controls that follow a Yes/No switch.

```html
<div class="kt-choice-row">
  <span class="kt-choice-label">Past supply experience required</span>
  <div class="seg" role="radiogroup">…Yes / No…</div>
  <div class="kt-dependent">
    <!-- fields revealed by Yes -->
  </div>
</div>
```

```css
.kt-choice-row   { display: grid; grid-template-columns: minmax(0,1fr) 220px; gap: 8px 24px;
  align-items: center; padding: 12px 0; border-top: 1px solid var(--color-divider); }
.kt-choice-row .seg { width: fit-content; }
.kt-dependent    { grid-column: 1 / -1; border-left: 2px solid var(--color-divider);
  padding: 4px 0 4px 16px; margin-top: 4px; }
```

- The switch always sits in the same fixed right column, and a `.seg` never stretches.
- Dependent fields sit directly beneath their parent. They align to the label's left edge behind the `.kt-group` 2px rule, never an arbitrary indent.
- In a two-column field grid, the dependent field goes in the **same cell** as its parent switch, stacked beneath it with the same 2px rule, so the grid columns stay intact.
- A `.seg` used as a field control always has a `<label>`. It is never a bare switch.

---

## 9. Checklist for the component page (`components/guidance.html`)

- [ ] Full tracker: all-not-started, current at stage 1, current at stage 3, blocked at stage 4, all done
- [ ] Reduced tracker at 390px
- [ ] Next-step: Your turn (with and without sentence), Your turn blocked (one fix; a hand-off fix plus a secondary fix), Waiting on someone, Done
- [ ] Not involved: tracker only, no next-step element
- [ ] Forced-colours and print previews
- [ ] Do/Don't pair: a card-per-stage tracker (don't) next to the grid (do)
- [ ] `.kt-choice-row` with and without `.kt-dependent`, and the two-column contract-terms case
