# Bidder Stitch contract schema (v1)

Each `NN.contract.json` sits beside `NN_code.html` (or `step_NN_code.html`).

```json
{
  "surface_id": "fs-04-confirm-modal",
  "title": "Submit Bid confirmation modal",
  "stitch_file": "04_code.html",
  "implementation_files": [
    "kentender_procurement/kentender_procurement/www/tenders/submit_bid.html",
    "kentender_procurement/kentender_procurement/public/css/final_submission_web.css"
  ],
  "required_markers": ["data-testid=\"kt-fs-confirm-dialog\"", "kt-fs-confirm-summary"],
  "required_classes": ["kt-fs-confirm-overlay", "kt-fs-confirm-card"],
  "required_text": ["Submit this bid?", "Cancel", "Submit Bid"],
  "forbidden_markers": ["cdn.tailwindcss.com", "kt-fs-dialog-meta"]
}
```

| Field | Meaning |
|-------|---------|
| `surface_id` | Stable id for gates / reports |
| `stitch_file` | Design source filename in the same folder |
| `implementation_files` | Repo-relative paths under `apps/kentender_v1/` whose concatenated text is scanned |
| `required_markers` | Substrings that must appear (prefer `data-testid=...` and distinctive region markers) |
| `required_classes` | CSS/HTML class tokens from the hand-port that encode Stitch regions |
| `required_text` | User-visible copy that must exist in implementation |
| `forbidden_markers` | Anti-patterns (Tailwind CDN, superseded generic markup) |

The gate also fails if any `*_code.html` in the pack folder lacks a matching `*.contract.json`.
