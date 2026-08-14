# KENTENDER_MVP_V1 — Seed Runbook

**Contract:** [01_KenTender_MVP_Canonical_Demo_Data_Contract_v2.0.md](01_KenTender_MVP_Canonical_Demo_Data_Contract_v2.0.md)  
**Scope model:** [00_KenTender_Procuring_Entity_and_Organisation_Scope_Model.md](00_KenTender_Procuring_Entity_and_Organisation_Scope_Model.md)  
**Fixture namespace:** `KENTENDER_MVP_V1`  

> **Obsolete:** Contract v1.1 and the `MOH_MVP_V1` namespace are superseded. Makefile alias `seed-moh-mvp-v1` still points here for one cycle.

## Purpose

Resettable Ministry of Health + County Government of Kisumu demo foundation:

- Procuring Entities `PE-MOH` and `PE-CGKIS`
- Organisation Unit Types + Organisation Units
- User Scope Assignments and Strategy Scope Assignments
- Strategy / Budget ownership via `owner_org_unit` (no `owner_state_department` / `owner_directorate`)

## Commands

From `apps/kentender_v1`:

```bash
make seed-kentender-mvp-v1 SITE=kentender.midas.com
make seed-kentender-mvp-v1-validate SITE=kentender.midas.com
```

Or directly:

```bash
bench --site kentender.midas.com execute \
  kentender_core.seeds.kentender_mvp_v1.orchestrator.run_kentender_mvp_v1 \
  --kwargs '{"reset": True, "force": True, "validate": True}'
```

Notes:

- Use Python `True`/`False` in `--kwargs` (not JSON `true`/`false`).
- Reset deletes canonical fixture rows **and** leftover Playwright / Gate test data on PE-MOH and PE-CGKIS: extra Procurement Plans, extra Demands, `MOH-BUD-PLN-*` test budgets, and `*@test.local` users.
- Reset does **not** wipe unrelated *Strategic* Plans (Contract §8.3). Canonical `@example.test` personas are re-upserted.

## What the seed creates

1. Org graph under `PE-MOH` and `PE-CGKIS`
2. Canonical `@example.test` users + User Scope Assignments
3. Ministry plan `MOH-SP-2026-2030` (entity-owned) + Kisumu plan `CGK-SP-HEALTH-2027-2028`
4. Budgets `MOH-BUD-2027-2028` / draft / closed + `CGK-BUD-2027-2028`
5. Funding ledger RSV / COM / EXP for the Ministry DHI line
6. Demands anchors (`DMD-MOH-2027-014`, returned, county draft)
7. Procurement Plan `PLN-MOH-2027-001` (Approved V1) + Active Plan Item `PPI-MOH-2027-021`
8. Contract PASS/FAIL report through the latest module stage (Planning)

Always seeds the **full** stack through the latest implemented module. There is no partial `through` boundary.

## UI personas (`.env.ui`)

| Persona | Email |
|---|---|
| Medical Services officer | `moh.medicalservices.officer@example.test` |
| Public Health officer | `moh.publichealth.officer@example.test` |
| Kisumu health officer (cross-entity denial) | `kisumu.health.officer@example.test` |
| Password (all) | `Test@123` (see `kentender_core.seeds.constants.TEST_PASSWORD`) |
