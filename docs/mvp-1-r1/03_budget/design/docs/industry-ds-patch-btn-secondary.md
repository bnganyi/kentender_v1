# Patch: stronger `.btn-secondary` border + no corner marks on buttons

I can't write directly into the Industry design-system project from here — apply this
in that project.

## 1. `styles.css` — `— buttons —` section

```diff
- .btn-secondary { border-color: var(--color-divider); }
+ .btn-secondary { border-color: color-mix(in srgb, var(--color-text) 30%, transparent); }
```

**Reason:** the hairline `--color-divider` border read as a card/section outline,
not a clickable control. A stronger border (30% text-mix vs. the divider's 16%)
keeps the button flat and unfilled but visibly distinct.

## 2. Drop `.blueprint` + corner marks from all buttons

Remove the `.blueprint` class and the four `<i class="corner …">` marks from every
button example in `components/buttons.html` (primary, secondary, icon, block).
Corner marks stay reserved for cards and figures; buttons are identified by their
fill/border alone.

```diff
- <button type="button" class="btn btn-primary blueprint"><i class="corner tl"></i><i class="corner tr"></i><i class="corner bl"></i><i class="corner br"></i>Continue…</button>
+ <button type="button" class="btn btn-primary">Continue…</button>
```

(same removal for `btn-secondary`, `btn-icon`, `btn-block` instances.)

## 3. `readme.md`

Update the "Do" bullet — *"Frame cards, figures and primary buttons as blueprint
objects"* → *"Frame cards and figures as blueprint objects"* (drop "and primary
buttons"). Buttons are never blueprint-framed.
