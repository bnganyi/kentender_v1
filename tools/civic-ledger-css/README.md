# Civic Ledger CSS (offline Tailwind build)

Compiles the Civic Ledger design-system utilities into a single, scoped
stylesheet committed at
`kentender_core/kentender_core/public/css/civic_ledger.css`.

This is **not** part of `bench build` / yarn. It is a standalone Tailwind CLI
run using the classes present in `sources/code.html` (the canonical mock) plus
the `kt_cl_*.js` component files.

## Why compiled + scoped

- `important: '.kt-cl-shell'` scopes every utility under `body.kt-cl-shell` and
  raises specificity so it wins over Frappe's Bootstrap without leaking.
- `corePlugins.preflight = false` means we never reset Frappe Desk globally.
- `corePlugins.container = false` avoids emitting an unscoped `.container` rule
  that would otherwise leak into Frappe's Bootstrap layout (the mock uses
  `max-w-[1280px] mx-auto`, not `.container`).
- The mock uses full Tailwind (arbitrary values, opacity modifiers, default
  color palette, gradients). Hand-porting a subset was the root cause of the
  earlier fidelity gap; a real compile reproduces every class faithfully.

## Regenerate (single command)

From the bench root:

```bash
cd apps/kentender_v1/tools/civic-ledger-css \
  && npx --yes tailwindcss@3 -c tailwind.config.js -i input.css \
     -o ../../kentender_core/kentender_core/public/css/civic_ledger.css --minify
```

Then bust the server-side page cache (no `bench build` needed):

```bash
bench --site kentender.midas.com clear-cache
```

## When to re-run

- The mock `code.html` changes.
- A component introduces a Tailwind class not already present in the sources.

`sources/code.html` is a copy of
`docs/std-prod-impl/IT-STD-Wizard-v3/B-Components/code.html`; refresh it when the
mock changes before recompiling.
