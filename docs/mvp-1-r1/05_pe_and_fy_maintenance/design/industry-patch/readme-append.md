## Status semantics (KenTender extension)

Industry's `.tag` variants are decorative labels — they carry no state meaning. Where a UI
shows record state, use `.kt-status` instead. It is a softly-rounded (6px) chip: a tint of the
status hue at ~10%, text and dot at full strength, no border.

| Class | Meaning | Examples |
| --- | --- | --- |
| `.kt-status.is-live` | In force now (emerald) | Active, Available, Ready |
| `.kt-status.is-draft` | Authored, not submitted (blue) | Draft |
| `.kt-status.is-pending` | Awaiting evaluation (neutral, hollow dot) | Not assessed |
| `.kt-status.is-attention` | Action needed (amber) | Configuration required |
| `.kt-status.is-critical` | Stopped or removed (rose) | Suspended, Closed |

```html
<span class="kt-status is-live">Active</span>
```

These five hues are the only colour permitted outside the steel accent, and only ever to
encode state — never decoratively.

**`.kt-figure`** applies the same tones to a large summary number, with a matching dot.

**`.kt-card-title`** is the section title inside a card: condensed uppercase at full text
strength on a 2px accent underline. **`.table thead th`** is likewise promoted to condensed
uppercase at full strength on a heavier rule, so headers separate from body rows.

To adopt: append `styles-append.css` to the end of `styles.css`, and this section to `readme.md`.
