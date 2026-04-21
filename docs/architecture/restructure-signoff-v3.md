# Architecture restructure v3 — signoff checklist

Use before starting **Demand Intake and Approval (DIA)** implementation.

| Gate | Status |
|------|--------|
| `kentender_suppliers` scaffolded and installable | Done |
| `kentender_transparency` scaffolded and installable | Done |
| v3 docs authoritative; v2 in `archive/` | Done |
| `kentender_procurement` internal subdomains + DIA home (`demand_intake/`) | Done |
| Makefile / scripts / symlinks / `test_wave0_smoke` app list updated | Done |
| Supplier vs procurement vs transparency boundaries documented | Done |
| `dependency-map-v3.md` present | Done |
| Strategy/Budget regression spot-checks (wave0 smoke, strategy tests, budget landing API) | Done |

**Residual risks**

- Full `kentender_budget` test suite may fail on global search assertions in some environments (pre-existing; not introduced by this restructure).
- `kentender_procurement` contains a legacy triple-nested `kentender_procurement/kentender_procurement/kentender_procurement/` package; do not duplicate workspace JSON—follow existing fixture paths until a dedicated cleanup.
