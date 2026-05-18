<!--
  Evidence for Rectification Tracker §14 — G9-002A
-->
## Goal

Close **§14 G9-002A**: **CLOSECERT** and **OPENREADY** appear **only** when the **`OPENING_READY`** checkpoint (or equivalent fixture) seeds them — never on base **`TENDER_PUBLISHED`** alone. Evidence covers both the **absence** path and the **presence** path.

## What was implemented

| Layer | Change |
|-------|--------|
| Playwright helpers | **`plcOpeningCheckpointHandoffsSeeded`** (desk `frappe.client.get_list` on **Procurement Handoff Card**) and **`expectG9OpeningCheckpointHandoffCards`** in **`tests/ui/helpers/procurement.ts`**. |
| Playwright spec | **`g9_002a_optional_opening_handoff_cards.spec.ts`** — **G9-002A-a** (no opening cards → panel has zero matching `data-handoff-code` rows) / **G9-002A-b** (both cards exist in DB → journey UI shows full card contract). Exactly one test **skip**s per typical site. |
| Desk JS | **None**. |

## Preconditions

- **G9-002A-a:** Site with WORKS **`TENDER_PUBLISHED`** load only (matches **R8-016** hygiene).
- **G9-002A-b:** After `bench --site kentender.midas.com execute ... load_procurement_lifecycle_works_master` with **`"checkpoint": "OPENING_READY"`** (see §16.5 / `works_master_opening_handoff_seed.py`).

## Evidence submitted (Playwright)

From **`apps/kentender_v1/`**:

```bash
npx playwright install chromium
npx playwright test tests/ui/smoke/procurement/g9_002a_optional_opening_handoff_cards.spec.ts
```

**Typical `TENDER_PUBLISHED` bench (2026-05-16):** **G9-002A-a** passed, **G9-002A-b** skipped (expected).

**OPENING_READY bench:** **G9-002A-a** skipped, **G9-002A-b** passed (re-run after optional seed).

## Related references

- **R2-011A / R8-016** — optional opening checkpoint vs base hygiene.
- **R5-011 / PLC-R5-011-02** — conditional TM2 extended hand-offs pattern.
