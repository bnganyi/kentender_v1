<!--
  Evidence for Rectification Tracker §14 — G9-006
-->
## Goal

Close **§14 G9-006**: **Source authority preserved** — **Journey / Handoff** aggregates do **not** override source modules (NG-002). When source truth drifts after a handoff was produced, the handoff becomes **Stale** and the **source DocType** retains the authoritative value (**ADR-PLC-002**).

## What was implemented

| Layer | Change |
|-------|--------|
| Automated test | **Existing** **`test_r8_003_plc_smoke_be_003_handoff_source_authority`** — PLC load → mutate **Procurement Package** `procurement_method` → **`validate_handoff_card_freshness`** marks **PKGREL** **Stale** → package row still holds the new method (**handoff does not override**). Module docstring updated to cite **G9-006**. |
| New business logic | **None** — regression is **R8-003 / PLC-SMOKE-BE-003**. |
| Companion (R8) | [`R8_003_plc_smoke_be_003_evidence.md`](./R8_003_plc_smoke_be_003_evidence.md). |

## Preconditions

- WORKS upstream seeds + **`load_procurement_lifecycle_works_master(checkpoint="TENDER_PUBLISHED")`** viable on site.
- Frappe **`IntegrationTestCase`** environment (bench test runner).

## Evidence submitted (Python)

From **bench root**:

```bash
bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.procurement_lifecycle.tests.test_r8_003_plc_smoke_be_003_handoff_source_authority
```

**Last run (local bench, site `kentender.midas.com`):** `1 passed` in ~10s — `test_plc_smoke_be_003_pkgrel_stale_when_package_changes_source_kept`.

## Related references

- **R8-003 / LV-R8-BE-03** — canonical implementation path.
- **R3-010** — `validate_handoff_card_freshness`.
- Tracker **NG-002** — handoff cards cannot override source module status.
