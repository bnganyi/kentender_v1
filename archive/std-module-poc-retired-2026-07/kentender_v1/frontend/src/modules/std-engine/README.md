# `std-engine` UI module (UI-HARD-0001)

Cursor pack §4 — **Admin and Officer UI Production Hardening** package root.

## Layout

- **Role / workflow packages:** `admin-library`, `tender-configuration`, `works-completion`, `outputs`, `readiness`, `approval`, `publication`, `evidence-audit`
- **Shared cross-cutting code:** `shared/` (`action-availability`, `blockers`, `denials`, `status`, `api`, `types`)

Each workflow folder owns `pages/`, `components/`, `hooks/`, and `tests/` **except** `outputs` and `readiness`, which use `components/` + `tests/` only per the pack tree.

## Bench hosting (see workstream-8 tracker)

**Hybrid:** this tree is the canonical **TypeScript** home for UI-HARD-* clients and types; **Frappe Desk** remains the primary shell for officer/admin UX until a dedicated SPA owns full surfaces. Wire Desk `public/js` to these modules incrementally (UI-HARD-0100+).

## Action availability client (UI-HARD-0100)

- Implementation: [`shared/action-availability/actionAvailabilityClient.ts`](shared/action-availability/actionAvailabilityClient.ts)
- Calls SEC-0410 whitelist methods via `frappe.call` (POST), unwraps `{ message: … }`.
- Entry points: `getActionAvailability`, `getBatchActionAvailability` (alias `getActionAvailabilityBatch`).
- Errors: `ActionAvailabilityClientError` with stable `envelope` (`success: false`, `error_code`, `message`, `details`).

## Verification

From `apps/kentender_v1`:

```bash
npm run test:std-engine-pack   # tsc --noEmit (production TS only)
npm run test:std-engine-unit   # vitest (includes action availability client specs)
npm run test:std-engine        # both
```

`test:std-engine-pack` runs `tsc --noEmit` over `./src/**/*.ts` (excluding `*.spec.ts`), including `_verify-workflow-imports.ts`, which imports every workflow barrel.
