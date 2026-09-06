# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §7.2 — the Strategy Alignment contracts, under the spec's
verbs (decision D6).

`ListEligibleStrategicObjectives` wraps
`kentender_strategy.services.strategy_consumer.list_strategy_objectives`,
keyed by the Active Strategic Plan Version that `resolve_strategy_context`
resolves site-locally (STR-CHG-001 v1.6 §8: no Procuring Entity or
organisation-unit argument, §16.2). Saving an Objective on a Plan Item
freezes lineage through `create_strategy_snapshot` (idempotent per
correlation key).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.procurement_planning.errors import fail


def _active_plan_version() -> str:
	from kentender_strategy.services.strategy_consumer import resolve_strategy_context

	try:
		# STR-CHG-001 v1.7 §7: exactly one of as_of_date / fiscal_year. Planning
		# selects Objectives for the plan being authored now, so "now" it is.
		context = resolve_strategy_context(as_of_date=frappe.utils.today())
	except Exception:
		return ""
	return cstr((context.get("primary_plan") or {}).get("version_id") or "")


def list_eligible_strategic_objectives(*, search: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
	"""Active Objectives of the site's sole Active Strategic Plan, with the
	display hierarchy path (§7.2). Empty when no Active plan exists."""
	plan_version = _active_plan_version()
	if not plan_version:
		return []
	from kentender_strategy.services.strategy_consumer import list_strategy_objectives

	result = list_strategy_objectives(plan_version, search=search, limit_start=0, limit_page_length=limit)
	rows = []
	for row in result.get("rows", []):
		# the contract's own path is self-inclusive; PLN-DES-09 shows the
		# ancestor path only — the objective's title is the field above it.
		path = [cstr(node.get("title")) for node in row.get("path", [])[:-1]]
		rows.append(
			{
				"id": cstr(row.get("id")),
				"title": cstr(row.get("title")),
				"path": path,
				"path_display": " › ".join(path),
				"plan_version_id": plan_version,
			}
		)
	return rows


def snapshot_objective(*, objective_id: str, correlation_key: str) -> dict[str, Any]:
	"""Freeze Objective ID + Strategy Plan + Strategy Version lineage for a
	Plan Item save (§7.2). Raises PLN_OBJECTIVE_INELIGIBLE when ineligible."""
	plan_version = _active_plan_version()
	eligible = {row["id"]: row for row in list_eligible_strategic_objectives()}
	if not plan_version or cstr(objective_id) not in eligible:
		fail("PLN_OBJECTIVE_INELIGIBLE")
	from kentender_strategy.services.strategy_consumer import create_strategy_snapshot

	snapshot = create_strategy_snapshot(plan_version_id=plan_version, objective_id=objective_id, correlation_key=correlation_key)
	return {
		"objective_id": cstr(objective_id),
		"objective_title": cstr(snapshot.get("objective_title")),
		"strategy_plan": cstr(snapshot.get("plan_id")),
		"strategy_plan_version": cstr(snapshot.get("plan_version_id") or plan_version),
		"path_display": eligible[cstr(objective_id)]["path_display"],
	}
