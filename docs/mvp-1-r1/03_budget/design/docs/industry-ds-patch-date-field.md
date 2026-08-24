# Patch: standard date-field pattern

Industry has no dedicated date component; `.input` was reused for date values with
plain text, which reads as a generic text field. Add a `.date-field` pattern so
every date field in the system looks the same.

## `styles.css` — add after `.input` rules

```css
.date-field {
  width: 100%; min-height: 36px; padding: 6px 10px; font: inherit; font-size: 14px;
  color: var(--color-text); background: var(--color-surface);
  border: 1px solid var(--color-divider); border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: space-between; gap: 8px;
}
.date-field:hover { border-color: color-mix(in srgb, var(--color-text) 45%, transparent); }
.date-field svg { flex: none; color: color-mix(in srgb, var(--color-text) 55%, transparent); }
```

## Markup

```html
<div class="field">
  <label for="approval-date">Approval date</label>
  <div class="date-field" id="approval-date">
    <span>30 Sep 2026</span>
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4"/><path d="M8 2v4"/><path d="M3 10h18"/>
    </svg>
  </div>
</div>
```

Icon: Lucide `calendar`, stroke-width 1.5, matching the rest of the icon set.
Add a demo block to `components/forms.html` under "Fields" once merged.
