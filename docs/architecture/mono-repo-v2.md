# KenTender Monorepo Structure v2

## Root Structure

repo/
  apps/
    kentender_core/
    kentender_strategy/
    kentender_budget/
    kentender_procurement/
    kentender_suppliers/
    kentender_governance/
    kentender_compliance/
    kentender_stores/
    kentender_assets/
    kentender_integrations/
    kentender_transparency/

---

## Internal Procurement Structure

kentender_procurement/

  kentender_procurement/
  demand_intake/
  procurement_planning/
  bid_submission_opening/
  evaluation_award/
  contract_management/
  inspection_acceptance/

Each must have:
  doctype/
  services/
  api/
  tests/

---

## Supplier App Structure

kentender_suppliers/

  supplier/
  onboarding/
  classification/
  performance/
  sanctions/

---

## Rules

- each submodule must be isolated
- no cross-submodule direct coupling
- shared logic must go to services/

---

## Testing Structure

tests/
  unit/
  integration/
  ui/

---

## Seed Structure

seeds/
  core/
  strategy/
  budget/
  dia/

---

## Bench integration (Frappe)

From `/home/midasuser/frappe-bench/apps`:

- Symlink each `kentender_*` app to `kentender_v1/kentender_*` (see `make -C apps/kentender_v1 symlinks`).
- `sites/apps.txt` must list the **real** app names (`kentender_suppliers`, `kentender_transparency`), not `kentender_v1`.
- Install order: `kentender_core` → `kentender_strategy` → `kentender_budget` → `kentender_procurement` → `kentender_suppliers` → `kentender_governance` → `kentender_compliance` → `kentender_stores` → `kentender_assets` → `kentender_integrations` → `kentender_transparency` (see `apps/kentender_v1/Makefile` `INSTALL_ORDER`).