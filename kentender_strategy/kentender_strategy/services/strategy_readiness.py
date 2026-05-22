"""Strategy plan readiness checklist and validation."""

from __future__ import annotations

import frappe
from frappe import _

from kentender_strategy.services.strategy_builder import build_tree, get_plan_or_throw


def evaluate_plan_readiness(plan_name: str) -> dict:
	get_plan_or_throw(plan_name)
	tree = build_tree(plan_name)
	counts = tree.get("counts") or {}
	checks = []

	def add(check_id: str, label: str, passed: bool, message: str = ""):
		checks.append({"id": check_id, "label": label, "passed": bool(passed), "message": message or ""})

	add("programs", _("At least one Program exists"), counts.get("programs", 0) > 0)
	add("sub_programs", _("At least one Sub-program exists"), counts.get("sub_programs", 0) > 0)
	add("indicators", _("At least one Indicator exists"), counts.get("indicators", 0) > 0)
	add("targets", _("At least one Target exists"), counts.get("targets", 0) > 0)

	ready = all(c["passed"] for c in checks)
	return {"ready": ready, "checks": checks, "counts": counts}


def assert_plan_readiness(plan_name: str) -> None:
	result = evaluate_plan_readiness(plan_name)
	if result["ready"]:
		return
	failed = [c["label"] for c in result["checks"] if not c["passed"]]
	frappe.throw(_("Plan is not ready: {0}").format("; ".join(failed)), title=_("Structure incomplete"))
