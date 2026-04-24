# KenTender Agent Rules

Before making changes, read:

- [docs/architecture/kentender_architecture_rules_v3.md](docs/architecture/kentender_architecture_rules_v3.md)
- [docs/architecture/global-architecture-v3.md](docs/architecture/global-architecture-v3.md)
- [docs/architecture/README.md](docs/architecture/README.md) (index; v2 drafts live in `docs/architecture/archive/`)
- For **architecture restructure** or ticket-style phased work, also read [docs/prompts/architecture/architecture-restructure-cursor-prompt-pack.md](docs/prompts/architecture/architecture-restructure-cursor-prompt-pack.md) — use it as the continuing reference while building in this area.

**IMPORTANT: Rule Precedence Hierarchy**

All rules follow this priority (highest to lowest):

1. User's explicit instructions in current conversation
2. Execution discipline rules (`06-execution-gatekeeper.md`)
3. Framework generator rules (`07-framework-generators-first.md`)
4. Planning workflow guidance
5. General architecture rules

**Rule Conflict Detection**  
Before any action, check for conflicts using `10-rule-conflict-detection.md`.

**User Override Mechanism**  
Any instruction with "DO NOT" or "NEVER" automatically overrides all rules (`11-user-override-mechanism.md`).

## Monorepo and bench

- `apps/kentender_v1/` is the **container repo** (docs, Makefile, scripts). Frappe **apps** are `kentender_*` folders inside it.
- Bench sees each app via **symlinks** under `apps/` (see `make -C apps/kentender_v1 symlinks` and [mono-repo-v2.md](docs/architecture/mono-repo-v2.md)).
- Run `bench` from the bench root (`/home/midasuser/frappe-bench`). **Asset builds (`bench build`, yarn in apps):** use **`./scripts/bench-with-node.sh`** only — **never** plain `bench build` (Cursor/agent `PATH` often injects Node 20; Frappe requires Node ≥24). See bench root **`AGENTS.md`** and **`.cursor/rules/frappe-bench-node.mdc`**.

## Final app set (v3)

`kentender_core`, `kentender_strategy`, `kentender_budget`, `kentender_procurement`, `kentender_suppliers`, `kentender_governance`, `kentender_compliance`, `kentender_stores`, `kentender_assets`, `kentender_integrations`, `kentender_transparency`.

**Dependency direction:** `core → strategy → budget → procurement → stores → assets`. Side apps (`suppliers`, `governance`, `compliance`, `integrations`, `transparency`) consume published interfaces; see [dependency-map-v3.md](docs/architecture/dependency-map-v3.md).

## Core Rules

1. **Respect app ownership and dependency direction.**
2. **Do not create new apps** beyond the v3 set.
3. **Keep business logic in `services/`**, not DocType controllers.
4. **Keep APIs explicit and minimal.**
5. **Do not invent hidden workflow states.**
6. **Do not mix unrelated phases.**
7. **Do not implement future phases.**
8. **Stop exactly at the requested phase boundary.**
9. **Use workspace-first UX** (Landing → queue → detail → builder), not raw DocType-first UX.
10. **If changing architecture-sensitive code**, summarize impacted apps/files before editing.

## Governance-first modules (v3)

No module is complete without: pre-PRD, full PRD, domain model, governance/state model, tabular role/permission matrices, UI spec, seed data, smoke contracts — per `kentender_architecture_rules_v3.md`.

## Procurement internal layout

Subdomains under `kentender_procurement/kentender_procurement/` (e.g. `demand_intake/` for DIA). See [PROCUREMENT_INTERNAL_STRUCTURE.md](kentender_procurement/PROCUREMENT_INTERNAL_STRUCTURE.md).

## Required Output Before Coding

- **Summary**: Brief overview of the task.
- **Impacted Apps**: List of Frappe apps affected.
- **Impacted Files**: Specific paths to files being modified.
- **Scope Boundaries**: What is explicitly inside and outside this task.
- **Tests to Run**: Which existing or new tests will validate the change.

## Required Output After Coding

- **Files Changed**: Final list of modified files.
- **What Changed**: Summary of the logic implemented.
- **What Was Intentionally Not Changed**: Constraints or future-phase items skipped.
- **Manual Checks**: Specific UI or flow steps to verify.
- **Smoke Tests to Run**: Quick validation commands or scripts.

## Framework generator rules

For Frappe-managed artifacts:

- Apps must be created with `bench new-app`
- Sites must be created with `bench new-site`
- DocType scaffolds must be generated through Frappe’s standard creation flow
- Do not handwrite framework scaffolds from scratch

If command execution is slow or unavailable: output the exact WSL command, stop after proposing the command, do not simulate the scaffold by creating files manually.
