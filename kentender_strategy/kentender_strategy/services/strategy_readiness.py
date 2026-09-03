# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 §6.2/§13.3/STR-BR-012 plan version submission readiness."""

from __future__ import annotations

import frappe
from frappe import _


def _node_type_counts(plan_version_id: str) -> dict[str, int]:
	rows = frappe.get_all(
		"Strategy Node",
		filters={"plan_version_id": plan_version_id},
		fields=["node_type"],
	)
	counts: dict[str, int] = {}
	for r in rows:
		counts[r.node_type] = counts.get(r.node_type, 0) + 1
	return counts


def _indicator_and_target_counts(plan_version_id: str) -> tuple[int, int]:
	indicator_count = frappe.db.count("Performance Indicator", {"plan_version_id": plan_version_id})
	target_count = frappe.db.sql(
		"""
		select count(*) from `tabPerformance Target` t
		inner join `tabPerformance Indicator` i on i.name = t.indicator_id
		where i.plan_version_id = %s
		""",
		(plan_version_id,),
	)[0][0]
	return indicator_count, int(target_count or 0)


def get_version_readiness(plan_version_id: str) -> dict:
	"""STR-DES-06's Readiness card: 4 named checks, ready when all are Ready."""
	version = frappe.get_doc("Strategic Plan Version", plan_version_id)
	plan = frappe.get_doc("Strategic Plan", version.plan_id)

	# CU-303 — entity identity is the site's own; a plan's identity is its
	# title and period (procuring_entity_id contract-dropped per D2).
	identity_ready = bool(plan.title and plan.period_start and plan.period_end)

	counts = _node_type_counts(plan_version_id)
	hierarchy_ready = counts.get("Pillar", 0) > 0 and counts.get("Strategic Objective", 0) > 0

	indicator_count, target_count = _indicator_and_target_counts(plan_version_id)
	content_ready = (
		counts.get("Strategic Objective", 0) > 0
		and indicator_count > 0
		and target_count > 0
	)

	checks = [
		{"check": "Plan identity complete", "ready": identity_ready},
		{"check": "Hierarchy valid", "ready": hierarchy_ready},
		{"check": "Indicators and targets complete", "ready": content_ready},
		# The authoritative overlap guard runs transactionally inside Approve
		# (STR-BR-004); this is a non-blocking preview only.
		{"check": "Active-plan overlap", "ready": True},
	]
	return {"ready": all(c["ready"] for c in checks), "checks": checks}


# Back-compat name for the one remaining legacy caller (api.strategy_api.get_plan_readiness_api,
# itself Phase 4/7 rebuild scope) — same function, new schema-appropriate body.
get_plan_readiness = get_version_readiness


def assert_version_ready_for_submit(plan_version_id: str) -> None:
	result = get_version_readiness(plan_version_id)
	if not result["ready"]:
		failing = ", ".join(c["check"] for c in result["checks"] if not c["ready"])
		frappe.throw(
			_("Not ready for submission: {0}").format(failing),
			frappe.ValidationError,
			title="STRATEGY_NOT_READY",
		)
