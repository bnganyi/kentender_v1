# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS strategy UAT purge + deterministic verify (R2-004 companion).

**Purge** (keeps only the canonical §8 Strategic Plan shell on PE-MOH/MOH)::

	bench --site kentender.midas.com execute \\
	  kentender_strategy.seeds.seed_works_master_strategy_purge.purge \\
	  --kwargs '{"dry_run": false, "delete_blocking_demands_and_budget_lines": true}'

``delete_blocking_demands_and_budget_lines`` removes **Budget Line**, **Budget Allocation**,
**Budget**, and **Demand** rows that reference the plan tree being removed (UAT destructive).

**Verify** (machine-readable proof; no guesswork)::

	bench --site kentender.midas.com execute \\
	  kentender_strategy.seeds.seed_works_master_strategy_purge.verify

**One-shot** purge + re-seed + verify::

	bench --site kentender.midas.com execute \\
	  kentender_strategy.seeds.seed_works_master_strategy_purge.reset_to_works_master \\
	  --kwargs '{"delete_blocking_demands_and_budget_lines": true}'

Desk list title for the plan is **Ministry of Health Strategic Plan 2026–2030** (en dash),
not the literal substring ``WORKS`` — look for that title or programme **PROG-MOH-INFRA**.
"""

from __future__ import annotations

from typing import Any

from kentender_strategy.seeds.seed_works_master_strategy_hierarchy import run as seed_run_works_master_strategy
from kentender_strategy.seeds.works_master_strategy_purge import (
	purge_non_works_strategy_hierarchy,
	verify_works_master_strategy_seed,
)


def purge(
	dry_run: bool = False,
	delete_blocking_demands_and_budget_lines: bool = False,
	restrict_procuring_entity_names: list[str] | None = None,
) -> dict[str, Any]:
	return purge_non_works_strategy_hierarchy(
		dry_run=dry_run,
		delete_blocking_demands_and_budget_lines=delete_blocking_demands_and_budget_lines,
		restrict_procuring_entity_names=restrict_procuring_entity_names,
	)


def verify() -> dict[str, Any]:
	return verify_works_master_strategy_seed()


def reset_to_works_master(
	delete_blocking_demands_and_budget_lines: bool = True,
	restrict_procuring_entity_names: list[str] | None = None,
) -> dict[str, Any]:
	"""Purge non-§8 plans, reload §8 seed, run deterministic verify."""
	p = purge_non_works_strategy_hierarchy(
		dry_run=False,
		delete_blocking_demands_and_budget_lines=delete_blocking_demands_and_budget_lines,
		restrict_procuring_entity_names=restrict_procuring_entity_names,
	)
	out: dict[str, Any] = {"purge": p, "seed": None, "verify": None}
	if not p.get("ok"):
		out["ok"] = False
		return out
	s = seed_run_works_master_strategy()
	out["seed"] = s
	if not s.get("ok"):
		out["ok"] = False
		return out
	v = verify_works_master_strategy_seed()
	out["verify"] = v
	out["ok"] = bool(v.get("ok"))
	out["desk_search_hint"] = (
		"In Strategy Management, the WORKS master plan list title is "
		"'Ministry of Health Strategic Plan 2026–2030' (Unicode en dash between years). "
		"Programme code PROG-MOH-INFRA / objective OBJ-MOH-HOSP-RENOV / target TGT-MOH-HOSP-RENOV-2026."
	)
	return out
