# Demo Platform Seed (linked IT STD chain)

Rerunnable demo dataset for Kenyan public-sector **IT STD** demos on `kentender.midas.com`.

## Goal

Clean Procuring Entities, purge conflicting demo stacks, then load a **linked** chain:

`strategy → budget → demands → procurement plans → STD → tender configurations → publications → bid submissions`

with **walkable** and **gate-ready** records so officers can continue work or take the next transition without missing setup data.

## Run

From bench root:

```bash
./apps/kentender_v1/scripts/seed_demo_platform.sh
# or
make -C apps/kentender_v1 seed-demo-platform-reset SITE=kentender.midas.com
```

Validate / transition probes:

```bash
bench --site kentender.midas.com execute kentender_core.seeds.seed_demo_platform.validate
bench --site kentender.midas.com execute kentender_core.seeds.seed_demo_platform.probe_transitions
```

## Procuring Entities

| Code | Name | Role |
|---|---|---|
| `PE-MOH` | Ministry of Health | Primary linked demo chain |
| `PE-MOE` | Ministry of Education | Dropdown only (no full chain in v1) |

Legacy `MOH`, `MOE`, `PE-DOE`, `PE-SDT`, and synthetic CFG PEs are migrated or removed.

## Registry (actionable roles)

| Module | Code / ref | Role | Next action |
|---|---|---|---|
| Strategy | `STRAT-MOH-2026` | Gate-ready (Active) | Drive budget / demands |
| Budget | `BUDGET-MOH-2026` + `BUD-MOH-IT-2026-001` | Gate-ready | Fund IT demands |
| Demand | `DEM-MOH-2026-001` / `002` | Masters (WORKS/IT) | Planning intake |
| Demand | `DEMO-MOH-2026-DEM-DRAFT` | Walkable | Submit for HoD |
| Demand | `DEMO-MOH-2026-DEM-HOD` | Gate-ready | Approve HoD (Home action) |
| Plan / package | `PLAN-MOH-2026`, `PKG-MOH-2026-002` | Stable IT package | Release / CFG |
| Package | `DEMO-MOH-2026-PKG-READY` | Walkable | Create configuration |
| CFG | `DEMO-MOH-2026-CFG-IP` | Walkable | Walk CFG-01…09 |
| CFG | `DEMO-MOH-2026-CFG-NA` | Walkable | Resolve blockers |
| CFG | `DEMO-MOH-2026-CFG-RFP` | Gate-ready | Confirm package → Publish |
| CFG / Pub | `DEMO-MOH-2026-CFG-PUB` | Receiving | Bid Submissions → View tender |
| Bid | `…-CFG-PUB-SEALED` pub | Gate-ready | Open submitted bids |
| Bid | `…-CFG-PUB-OPENED` | Portfolio | Open register |
| STD | `KE-PPRA-IT-2022-04` + Approved `PPRA-IT-STD` | Gate-ready | Bound into IT CFGs |

## Implementation map

| Path | Role |
|---|---|
| `kentender_core/seeds/seed_demo_platform.py` | Bench entry |
| `kentender_core/seeds/demo_platform_seed/` | Pack (pe_cleanup, clear, load, actionable, validate, transitions) |
| `scripts/seed_demo_platform.sh` | Shell wrapper |

## Evidence

After load, `validation.ok` and `transitions.ok` should be true. Transition mutate probes are optional (`probe_transitions` with `mutate: True` — note Python `True` in `--kwargs`).

Verified on `kentender.midas.com` (2026-07-31):

- Home entities: `PE-MOH`, `PE-MOE` only
- Bid landing stages: Receiving / Closed and sealed / Opened
- CFG walkable home returns 9 steps; sealed pub `can_open=1`
- Unit tests: `kentender_core.tests.test_demo_platform_seed`, `test_demo_platform_transitions`
