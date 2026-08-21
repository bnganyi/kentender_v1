# Procurement Planning — Gate 02 Roles and Seed

**Document ID:** PLANNING-MVP1-GATE-02-1.0  
**Status:** Done (2026-08-09)  
**Authority:** Cursor Prompt 02; REQ v1.4 §7 / §11; Contract v2.4 §7.4–7.6 / §8–9  
**Prerequisite:** `GATE_01_DOMAIN_FOUNDATION.md` Done  

---

## 1. Goal

Ship **Planning roles + PE/OU scope** and the **canonical Planning seed** so operators cannot act without assignment, Admin alone has no authority, MOH and County stay isolated, and `KENTENDER_MVP_V1` + `SCN-PLN-ADD-001` reset repeatably with Contract v2.4 identities.

**Exit phrase:** *story resets repeatably and cross-entity access tests pass.*

---

## 2. Delivered

### Permissions (`PLN-PERM-001`…`005`)

- `services/planning_permissions.py` — `ensure_planning_roles`, `require_operational_roles`, `assert_planning_scope`, zero/single/multi PE resolve, approve segregation
- Patch `ensure_planning_roles` + DocType permission matrix on all 10 MVP DocTypes
- Gate 01 services wired for role + scope; approve = Designated Approver / Accounting Officer / Planning Authority only

### Seed (`PLN-SEED-001`…`003`)

- Module seed `procurement_planning/seeds/kentender_mvp_v1.py` — `PLN-MOH-2027-001` / V1 Approved / `PPI-MOH-2027-021` Active @ **455,000,000**
- Orchestrator always seeds through the latest module stage (Planning); no partial `through` boundary
- Canonical Planning users + USA in `kentender_mvp_v1/users.py`
- Validate / clear Planning checks
- `SCN-PLN-ADD-001` setup / run / reset → `PPI-MOH-2027-022`, consolidated **535,000,000**, idempotent second run

### Playwright helpers

- `tests/ui/helpers/planningRoles.ts` — Contract §4.6 persona logins (Gate 03 UI)

---

## 3. Evidence commands

```bash
bench --site kentender.midas.com migrate

bench --site kentender.midas.com run-tests \
  --module kentender_procurement.procurement_planning.tests.test_planning_roles_exist
# 3/3 OK

bench --site kentender.midas.com run-tests \
  --module kentender_procurement.procurement_planning.tests.test_planning_permissions_matrix
# 6/6 OK

bench --site kentender.midas.com run-tests \
  --module kentender_procurement.procurement_planning.tests.test_planning_pe_scope_selection
# 3/3 OK

bench --site kentender.midas.com run-tests \
  --module kentender_procurement.procurement_planning.tests.test_planning_cross_entity_isolation
# 3/3 OK

bench --site kentender.midas.com run-tests \
  --module kentender_procurement.procurement_planning.tests.test_planning_mvp1_invariants
# 10/10 OK (Gate 01 regression)

bench --site kentender.midas.com execute \
  kentender_core.seeds.kentender_mvp_v1.orchestrator.run_kentender_mvp_v1 \
  --kwargs '{"reset": True, "force": True, "validate": True}'

bench --site kentender.midas.com run-tests \
  --module kentender_procurement.procurement_planning.tests.test_planning_mvp_seed_contract
# 4/4 OK

bench --site kentender.midas.com execute \
  kentender_procurement.procurement_planning.seeds.scn_pln_add_001.run \
  --kwargs '{"reset_first": False}'

bench --site kentender.midas.com run-tests \
  --module kentender_procurement.procurement_planning.tests.test_scn_pln_add_001
# 4/4 OK
```

---

## 4. Out of Gate 02

- Stitch UI (`PLN-UI-*`) — Gate 03+
- `PLN-SEED-004` pre-approval UI fixtures
- Full publish / tender take-up product paths
- `PLN-SCH-013` page_js

---

## 5. Next

Gate 03 — Stitch workspace / register plan surfaces.
