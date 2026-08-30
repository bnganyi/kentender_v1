# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 §7.2 — the Strategy Alignment contracts, under the spec's
verbs (decision D6).

Name delta: `ListEligibleStrategicObjectives` is
`kentender_strategy.api.strategy_consumer_api.list_strategy_objectives`, keyed
by an Active Strategic Plan Version resolved per PE through
`resolve_strategy_context` (which fails loudly on zero or multiple primary
Active plans — Planning surfaces that as PLN_OBJECTIVE_INELIGIBLE rather than
guessing). Saving an Objective on a Plan Item freezes lineage through
`create_strategy_snapshot` (idempotent per correlation key).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.procurement_planning.errors import fail


def _active_plan_version(procuring_entity: str) -> str:
	from kentender_strategy.services.strategy_consumer import resolve_strategy_context

	try:
		context = resolve_strategy_context(procuring_entity)
	except Exception:
		return ""
	return cstr((context.get("primary_plan") or {}).get("id") or "")


def list_eligible_strategic_objectives(
	*, procuring_entity: str, search: str | None = None, limit: int = 200
) -> list[dict[str, Any]]:
	"""Active Objectives for the PE's sole primary Active Strategic Plan, with
	the display hierarchy path (§7.2). Empty when no Active plan exists."""
	plan_version = _active_plan_version(procuring_entity)
	if not plan_version:
		return []
	from kentender_strategy.services.strategy_consumer import list_strategy_objectives

	result = list_strategy_objectives(
		plan_version, search=search, limit_start=0, limit_page_length=limit
	)
	rows = []
	for row in result.get("rows", []):
		path = [cstr(node.get("title")) for node in row.get("path", [])]
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


def snapshot_objective(
	*, procuring_entity: str, objective_id: str, correlation_key: str
) -> dict[str, Any]:
	"""Freeze Objective ID + Strategy Plan + Strategy Version lineage for a Plan
	Item save (§7.2). Raises PLN_OBJECTIVE_INELIGIBLE when the Objective is not
	currently eligible."""
	plan_version = _active_plan_version(procuring_entity)
	eligible = {
		row["id"]: row
		for row in list_eligible_strategic_objectives(procuring_entity=procuring_entity)
	}
	if not plan_version or cstr(objective_id) not in eligible:
		fail(
			"PLN_OBJECTIVE_INELIGIBLE",
			"Select an Active Strategic Objective valid for this Plan.",
		)
	from kentender_strategy.services.strategy_consumer import create_strategy_snapshot

	snapshot = create_strategy_snapshot(
		plan_version_id=plan_version,
		objective_id=objective_id,
		correlation_key=correlation_key,
	)
	return {
		"objective_id": cstr(objective_id),
		"objective_title": cstr(snapshot.get("objective_title")),
		"strategy_plan": cstr(snapshot.get("plan_id")),
		"strategy_plan_version": cstr(snapshot.get("plan_version_id") or plan_version),
		"path_display": eligible[cstr(objective_id)]["path_display"],
	}
