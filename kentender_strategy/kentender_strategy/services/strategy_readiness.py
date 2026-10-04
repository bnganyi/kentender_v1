# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.8 §5.1/§9/§11.6/STR-BR-012 — submission readiness and
approval blockers, as structured failing rule ids with actionable text.

A readiness failure names the actual missing or invalid value (§9
`STRATEGY_NOT_READY`, §11.6 "show only real actionable readiness failures").
The page never leads with a green checklist; it shows `failures` when there
are any. Approval additionally requires the version to be able to become
effective immediately (§5.1): a future `effective_from` is a blocker with
its own banner, not a scheduled activation."""

from __future__ import annotations

import frappe
from frappe import _

RULE_PLAN_IDENTITY = "PLAN_IDENTITY"
RULE_PILLAR = "HIERARCHY_PILLAR"
RULE_OBJECTIVE = "HIERARCHY_OBJECTIVE"
RULE_INDICATOR = "CONTENT_INDICATOR"
RULE_TARGET = "CONTENT_TARGET"
RULE_EFFECTIVE_FROM_MISSING = "EFFECTIVE_FROM_MISSING"
RULE_EFFECTIVE_FROM_FUTURE = "EFFECTIVE_DATE_FUTURE"

NOT_READY_MESSAGE = "Complete the highlighted items before submitting or approving."


def today():
	"""Site date. Wrapped so a test can pin the review instant (§14.4)."""
	return frappe.utils.getdate(frappe.utils.today())


def _date_label(value) -> str:
	return frappe.utils.getdate(value).strftime("%-d %b %Y")


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
	"""STR-BR-012 — the four named checks (kept for the readiness preview)
	plus `failures`: the actual actionable items, each with a stable rule id."""
	version = frappe.get_doc("Strategic Plan Version", plan_version_id)
	plan = frappe.get_doc("Strategic Plan", version.plan_id)

	failures: list[dict] = []

	identity_ready = bool(plan.title and plan.period_start and plan.period_end)
	if not identity_ready:
		missing = [
			label
			for label, ok in (
				(_("plan title"), bool(plan.title)),
				(_("start date"), bool(plan.period_start)),
				(_("end date"), bool(plan.period_end)),
			)
			if not ok
		]
		failures.append({"rule": RULE_PLAN_IDENTITY, "message": _("Enter the {0}.").format(", ".join(missing))})

	counts = _node_type_counts(plan_version_id)
	has_pillar = counts.get("Pillar", 0) > 0
	has_objective = counts.get("Strategic Objective", 0) > 0
	hierarchy_ready = has_pillar and has_objective
	if not has_pillar:
		failures.append({"rule": RULE_PILLAR, "message": _("Add a pillar to start the plan structure.")})
	elif not has_objective:
		failures.append({"rule": RULE_OBJECTIVE, "message": _("Add at least one objective under a programme or sub-programme.")})

	indicator_count, target_count = _indicator_and_target_counts(plan_version_id)
	content_ready = has_objective and indicator_count > 0 and target_count > 0
	if has_objective and indicator_count == 0:
		failures.append({"rule": RULE_INDICATOR, "message": _("Add at least one indicator to an objective.")})
	elif has_objective and target_count == 0:
		failures.append({"rule": RULE_TARGET, "message": _("Add at least one target to an indicator.")})

	checks = [
		{"check": "Plan identity complete", "ready": identity_ready},
		{"check": "Hierarchy valid", "ready": hierarchy_ready},
		{"check": "Indicators and targets complete", "ready": content_ready},
		# The authoritative overlap guard runs transactionally inside Approve
		# (STR-BR-004); this is a non-blocking preview only.
		{"check": "Active-plan overlap", "ready": True},
	]
	return {"ready": all(c["ready"] for c in checks), "checks": checks, "failures": failures}


# Back-compat name for the one remaining legacy caller.
get_plan_readiness = get_version_readiness


def get_version_approval_blockers(version) -> dict:
	"""§5.1/§11.6 — approval is permitted only when the version can become
	effective immediately. Returns the blocker facts the decision page
	renders (banner copy is composed here so every surface says the same)."""
	if isinstance(version, str):
		version = frappe.get_doc("Strategic Plan Version", version)
	failures: list[dict] = []
	future = None
	if not version.effective_from:
		failures.append({"rule": RULE_EFFECTIVE_FROM_MISSING, "message": _("Set the date this version applies from.")})
	elif frappe.utils.getdate(version.effective_from) > today():
		start = _date_label(version.effective_from)
		future = {
			"effective_from": str(version.effective_from),
			"effective_from_label": start,
			"headline": _(
				"This version cannot be approved yet. It starts on {0}. Approval makes the version current immediately, so it cannot be approved before that date."
			).format(start),
			"guidance": _(
				"Return it if the date needs correction. If the date is intentional, it can remain awaiting approval. An authorised Approver must approve it when it is applicable. It will not activate automatically."
			),
		}
		failures.append({"rule": RULE_EFFECTIVE_FROM_FUTURE, "message": future["headline"]})
	return {"blocked": bool(failures), "future_effective": future, "failures": failures}


def _throw_not_ready(failures: list[dict]) -> None:
	frappe.throw(
		_(NOT_READY_MESSAGE) + " " + " ".join(f["message"] for f in failures),
		frappe.ValidationError,
		title="STRATEGY_NOT_READY",
	)


def assert_version_ready_for_submit(plan_version_id: str) -> None:
	result = get_version_readiness(plan_version_id)
	if result["failures"] or not result["ready"]:
		_throw_not_ready(result["failures"] or [{"rule": "NOT_READY", "message": ""}])


def assert_version_ready_for_approval(version) -> None:
	"""STR-BR-015 — approval repeats the submission checks and adds the
	immediate-effect requirement (§5.1). No scheduled activation exists."""
	if isinstance(version, str):
		version = frappe.get_doc("Strategic Plan Version", version)
	readiness = get_version_readiness(version.name)
	blockers = get_version_approval_blockers(version)
	failures = list(readiness["failures"]) + list(blockers["failures"])
	if failures:
		_throw_not_ready(failures)
