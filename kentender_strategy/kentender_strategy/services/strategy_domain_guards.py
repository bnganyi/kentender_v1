# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 §8 domain constraints for the rebuilt Strategy Alignment schema."""

from __future__ import annotations

import frappe
from frappe import _

PLAN_ROLE_PRIMARY = "Primary"
PLAN_ROLE_SUPPORTING = "Supporting Framework"
PLAN_ROLES = (PLAN_ROLE_PRIMARY, PLAN_ROLE_SUPPORTING)

# STR-CHG-001 v1.5 §6.1: only 4 statuses remain — Draft, Submitted for
# approval, Active, Superseded. Return moves a submitted version directly
# back to Draft (no separate Returned status); Approve moves it directly to
# Active in the same transaction (no separate Approved status).
VERSION_IMMUTABLE = frozenset({"Submitted for approval", "Active", "Superseded"})
VERSION_EDITABLE = frozenset({"Draft"})

NODE_TYPE_PILLAR = "Pillar"
NODE_TYPE_PROGRAMME = "Programme"
NODE_TYPE_SUB_PROGRAMME = "Sub-programme"
NODE_TYPE_OBJECTIVE = "Strategic Objective"
NODE_TYPES = (
	NODE_TYPE_PILLAR,
	NODE_TYPE_PROGRAMME,
	NODE_TYPE_SUB_PROGRAMME,
	NODE_TYPE_OBJECTIVE,
)
# STR-BR-007 (v1.4): Pillar -> Programme -> optional Sub-programme -> Strategic
# Objective. A Programme may parent an Objective when Sub-programme is omitted.
NODE_ALLOWED_PARENT_TYPES: dict[str, tuple[str, ...]] = {
	NODE_TYPE_PILLAR: (),
	NODE_TYPE_PROGRAMME: (NODE_TYPE_PILLAR,),
	NODE_TYPE_SUB_PROGRAMME: (NODE_TYPE_PROGRAMME,),
	NODE_TYPE_OBJECTIVE: (NODE_TYPE_PROGRAMME, NODE_TYPE_SUB_PROGRAMME),
}
MEASURABLE_NODE_TYPES = (NODE_TYPE_OBJECTIVE,)
TARGET_COMPARISONS = ("At least", "At most", "Equal to")


def _plan_period(plan_id: str) -> tuple:
	row = frappe.db.get_value("Strategic Plan", plan_id, ["period_start", "period_end"])
	if not row:
		return None, None
	start, end = row
	return (frappe.utils.getdate(start) if start else None, frappe.utils.getdate(end) if end else None)


def validate_strategic_plan(doc) -> None:
	"""STR-BR-002/003/005: role/parent rules and a valid period."""
	if doc.period_start and doc.period_end:
		if frappe.utils.getdate(doc.period_start) >= frappe.utils.getdate(doc.period_end):
			frappe.throw(_("Plan period start must be earlier than plan period end"))

	role = (doc.plan_role or "").strip()
	if role not in PLAN_ROLES:
		frappe.throw(_("Select a valid plan role"))

	if role == PLAN_ROLE_PRIMARY:
		if doc.parent_primary_plan_id:
			frappe.throw(_("A Primary plan must not have a parent plan"))
	else:
		if not doc.parent_primary_plan_id:
			frappe.throw(_("A Supporting Framework must name one governing Primary plan"))
		parent = frappe.db.get_value(
			"Strategic Plan",
			doc.parent_primary_plan_id,
			["plan_role"],
			as_dict=True,
		)
		if not parent:
			frappe.throw(_("Parent primary plan is not valid"))
		if parent.plan_role != PLAN_ROLE_PRIMARY:
			frappe.throw(_("A Supporting Framework's parent must be a Primary plan"))
		# CU-303 — one site is one procuring entity, so the same-entity rule
		# holds by construction and is no longer checked.

	if not doc.is_new():
		prev_role = frappe.db.get_value("Strategic Plan", doc.name, "plan_role")
		if prev_role != doc.plan_role and _has_versions(doc.name):
			frappe.throw(_("Plan role cannot change once the plan has any version"))


def _has_versions(plan_id: str) -> bool:
	return bool(frappe.db.exists("Strategic Plan Version", {"plan_id": plan_id}))


def validate_strategic_plan_version(doc) -> None:
	"""STR-BR-005/006: version numbering, baseline requirement, period containment,
	and immutability of Approved/Active/Superseded/Archived content."""
	if not doc.version_number or int(doc.version_number) < 1:
		frappe.throw(_("Version Number must be a positive integer"))
	if int(doc.version_number) == 1:
		if doc.based_on_plan_version_id:
			frappe.throw(_("The first plan version must not name a baseline version"))
	else:
		if not doc.based_on_plan_version_id:
			frappe.throw(_("Successor plan versions require Based On Plan Version"))
		# Re-validated only when the relationship is actually being formed —
		# not on every later save. Activating this successor legitimately
		# supersedes its own baseline in the same transaction (§6.1), which
		# would otherwise make this check fail on its own activation save.
		if doc.is_new() or doc.has_value_changed("based_on_plan_version_id"):
			baseline = frappe.db.get_value(
				"Strategic Plan Version", doc.based_on_plan_version_id, ["plan_id", "status"], as_dict=True
			)
			if not baseline:
				frappe.throw(_("Based On Plan Version is not valid"))
			if baseline.plan_id != doc.plan_id:
				frappe.throw(_("Based On Plan Version must belong to the same Strategic Plan"))
			if baseline.status != "Active":
				frappe.throw(_("A successor version must be based on the Active version"))

	period_start, period_end = _plan_period(doc.plan_id)
	effective_from = frappe.utils.getdate(doc.effective_from) if doc.effective_from else None
	effective_to = frappe.utils.getdate(doc.effective_to) if doc.effective_to else None
	if effective_from and period_start and effective_from < period_start:
		frappe.throw(_("Version effective start cannot be earlier than the plan period"))
	if effective_from and period_end and effective_from > period_end:
		frappe.throw(_("Version effective start cannot be later than the plan period"))
	if effective_from and effective_to and effective_from > effective_to:
		frappe.throw(_("Version effective start must be on or before effective end"))

	if not doc.is_new():
		prev_status = frappe.db.get_value("Strategic Plan Version", doc.name, "status")
		if prev_status in VERSION_IMMUTABLE:
			for f in ("plan_id", "version_number", "based_on_plan_version_id"):
				if doc.has_value_changed(f):
					frappe.throw(_("Approved/Active plan versions are immutable"))


def _assert_version_editable(plan_version_id: str | None) -> None:
	if not plan_version_id:
		frappe.throw(_("Plan version is required"))
	status = frappe.db.get_value("Strategic Plan Version", plan_version_id, "status")
	if status not in VERSION_EDITABLE:
		frappe.throw(_("Plan structure can only be edited while the version is Draft or Returned"))


def validate_strategy_node(doc) -> None:
	"""STR-BR-007: allowed hierarchy and deterministic sibling ordering."""
	if doc.node_type not in NODE_TYPES:
		frappe.throw(_("Select a valid node type"))
	_assert_version_editable(doc.plan_version_id)

	allowed_parents = NODE_ALLOWED_PARENT_TYPES[doc.node_type]
	if not allowed_parents:
		if doc.parent_node_id:
			frappe.throw(_("A {0} must not have a parent node").format(doc.node_type))
	else:
		if not doc.parent_node_id:
			frappe.throw(_("A {0} requires a parent node").format(doc.node_type))
		parent = frappe.db.get_value(
			"Strategy Node", doc.parent_node_id, ["node_type", "plan_version_id"], as_dict=True
		)
		if not parent:
			frappe.throw(_("Parent node is not valid"))
		if parent.plan_version_id != doc.plan_version_id:
			frappe.throw(_("Parent node must belong to the same plan version"))
		if parent.node_type not in allowed_parents:
			frappe.throw(
				_("A {0}'s parent must be one of: {1}").format(doc.node_type, ", ".join(allowed_parents))
			)

	siblings = frappe.get_all(
		"Strategy Node",
		filters={
			"plan_version_id": doc.plan_version_id,
			"parent_node_id": doc.parent_node_id or "",
			"name": ["!=", doc.name or ""],
		},
		fields=["name", "display_order"],
	)
	if any((s.display_order == doc.display_order) for s in siblings):
		frappe.throw(_("Display Order must be unique among sibling nodes"))


def validate_performance_indicator(doc) -> None:
	"""STR-BR-008/009: measures a Strategic Objective from the same version; unique
	name under its measured node within one version."""
	_assert_version_editable(doc.plan_version_id)
	node = frappe.db.get_value(
		"Strategy Node", doc.measures_node_id, ["node_type", "plan_version_id"], as_dict=True
	)
	if not node:
		frappe.throw(_("Measures Node is required"))
	if node.node_type not in MEASURABLE_NODE_TYPES:
		frappe.throw(_("An indicator may only measure a Strategic Objective"))
	if node.plan_version_id != doc.plan_version_id:
		frappe.throw(_("Indicator must belong to the same plan version as the node it measures"))

	dup = frappe.get_all(
		"Performance Indicator",
		filters={
			"measures_node_id": doc.measures_node_id,
			"indicator_name": doc.indicator_name,
			"name": ["!=", doc.name or ""],
		},
		limit=1,
	)
	if dup:
		frappe.throw(_("Indicator name must be unique under its measured node"))


def validate_performance_target(doc) -> None:
	"""STR-BR-010/011: exactly one period anchor, valid comparison, unit-compatible
	value within the plan period."""
	indicator = frappe.db.get_value(
		"Performance Indicator", doc.indicator_id, ["plan_version_id", "unit"], as_dict=True
	)
	if not indicator:
		frappe.throw(_("Performance Indicator is required"))
	_assert_version_editable(indicator.plan_version_id)

	has_fy = bool(doc.financial_year_id)
	has_date = bool(doc.target_by_date)
	if has_fy == has_date:
		frappe.throw(_("A target must use exactly one of Financial Year or Target By Date"))

	if doc.comparison not in TARGET_COMPARISONS:
		frappe.throw(_("Select a valid comparison"))

	if doc.target_value is None:
		frappe.throw(_("Target Value is required"))
	if (indicator.unit or "").strip().lower() == "percentage" and not (0 <= doc.target_value <= 100):
		frappe.throw(_("Percentage target values must be between 0 and 100 inclusive"))

	plan_id = frappe.db.get_value("Strategic Plan Version", indicator.plan_version_id, "plan_id")
	period_start, period_end = _plan_period(plan_id)
	if has_date and period_start and period_end:
		target_by_date = frappe.utils.getdate(doc.target_by_date)
		if not (period_start <= target_by_date <= period_end):
			frappe.throw(_("Target By Date must fall within the plan period"))

	# §12.3: "One Indicator cannot contain two Targets for the same Fiscal
	# Year or the same target-by date." Sibling scope is the indicator, not
	# the plan version — two different indicators may each carry their own
	# FY 2027/28 target.
	sibling_filters = {"indicator_id": doc.indicator_id, "name": ["!=", doc.name or ""]}
	sibling_filters["financial_year_id" if has_fy else "target_by_date"] = (
		doc.financial_year_id if has_fy else doc.target_by_date
	)
	if frappe.db.exists("Performance Target", sibling_filters):
		period_label = doc.financial_year_id if has_fy else doc.target_by_date
		frappe.throw(_("This indicator already has a target for {0}").format(period_label))
