# Copyright (c) 2026, KenTender and contributors
"""REQ §10 domain constraints for Strategy MVP-1 DocTypes."""

from __future__ import annotations

import re

import frappe
from frappe import _

CODE_RE = re.compile(r"^[A-Z0-9-]+$")
IMMUTABLE_PLAN = frozenset({"Approved", "Active", "Superseded", "Archived"})
IMMUTABLE_PVO = frozenset({"Active", "Superseded", "Retired"})

PLAN_TYPE_ENTITY = "Entity Strategic Plan"
PLAN_TYPE_PROGRAMME = "Programme Strategy"
PLAN_TYPE_THEMATIC = "Thematic Plan"
PLAN_TYPE_ANNUAL = "Annual Implementation Plan"
PLAN_TYPES = (
	PLAN_TYPE_ENTITY,
	PLAN_TYPE_PROGRAMME,
	PLAN_TYPE_THEMATIC,
	PLAN_TYPE_ANNUAL,
)
SUBORDINATE_PLAN_TYPES = frozenset(
	{PLAN_TYPE_PROGRAMME, PLAN_TYPE_THEMATIC, PLAN_TYPE_ANNUAL}
)
SCOPE_TYPE_PE = "Procuring Entity"
SCOPE_TYPE_PROGRAMME = "Programme"
SCOPE_TYPE_ENTITY_UNIT = "Entity Unit"
SCOPE_TYPES = (SCOPE_TYPE_PE, SCOPE_TYPE_PROGRAMME, SCOPE_TYPE_ENTITY_UNIT)


def _require_code(code: str, label: str) -> None:
	if not code or not CODE_RE.match(code):
		frappe.throw(_("{0} must use uppercase letters, numbers and hyphens").format(label))


def _periods_overlap(start_a, end_a, start_b, end_b) -> bool:
	if not start_a or not end_a or not start_b or not end_b:
		return False
	sa = frappe.utils.getdate(start_a)
	ea = frappe.utils.getdate(end_a)
	sb = frappe.utils.getdate(start_b)
	eb = frappe.utils.getdate(end_b)
	return sa <= eb and sb <= ea


def normalize_plan_scope(doc) -> None:
	"""Auto-fill ESP scope from procuring entity; clear parent for ESP."""
	if (doc.plan_type or "") == PLAN_TYPE_ENTITY:
		doc.scope_type = SCOPE_TYPE_PE
		doc.scope_id = doc.procuring_entity
		doc.parent_plan = None


def validate_plan_activation(doc) -> None:
	"""STR-FR-005: Active concurrency guards before status flip to Active."""
	normalize_plan_scope(doc)
	plan_type = (doc.plan_type or "").strip()
	if plan_type not in PLAN_TYPES:
		frappe.throw(_("Select a valid plan type"))

	if plan_type in SUBORDINATE_PLAN_TYPES:
		if not doc.parent_plan:
			frappe.throw(
				_(
					"Programme Strategy, Thematic Plan and Annual Implementation Plan "
					"require a parent Entity Strategic Plan before activation"
				)
			)
		parent = frappe.db.get_value(
			"Strategic Plan",
			doc.parent_plan,
			["name", "plan_type", "procuring_entity", "status"],
			as_dict=True,
		)
		if not parent:
			frappe.throw(_("Parent plan is not valid"))
		if parent.plan_type != PLAN_TYPE_ENTITY:
			frappe.throw(_("Parent plan must be an Entity Strategic Plan"))
		if parent.procuring_entity != doc.procuring_entity:
			frappe.throw(_("Parent plan must belong to the same procuring entity"))
		if not doc.scope_type or not doc.scope_id:
			frappe.throw(_("Organisational scope is required for subordinate plans"))
		if doc.scope_type == SCOPE_TYPE_PE and doc.scope_id == doc.procuring_entity:
			frappe.throw(
				_(
					"Subordinate plans must use a distinct organisational scope "
					"(not the whole procuring entity)"
				)
			)
	else:
		# Entity Strategic Plan
		if not doc.scope_type or not doc.scope_id:
			frappe.throw(_("Entity Strategic Plan scope could not be resolved"))

	# Overlap: Active plans with same entity + type + scope (excluding same plan_code supersession)
	others = frappe.get_all(
		"Strategic Plan",
		filters={
			"procuring_entity": doc.procuring_entity,
			"plan_type": plan_type,
			"scope_type": doc.scope_type,
			"scope_id": doc.scope_id,
			"status": "Active",
			"name": ["!=", doc.name],
		},
		fields=["name", "plan_code", "title", "start_date", "end_date"],
	)
	for row in others:
		if row.plan_code == doc.plan_code:
			# Same logical plan — will be superseded atomically
			continue
		if _periods_overlap(doc.start_date, doc.end_date, row.start_date, row.end_date):
			frappe.throw(
				_(
					"Cannot activate: Active plan {0} ({1}) already covers an overlapping "
					"period for the same entity, plan type and scope"
				).format(row.plan_code, row.title or row.name)
			)

	# ESP uniqueness is covered by entity+type+scope (scope_id = procuring_entity),
	# but keep an explicit second pass for clarity / legacy rows with blank scope.
	if plan_type == PLAN_TYPE_ENTITY:
		esp_others = frappe.get_all(
			"Strategic Plan",
			filters={
				"procuring_entity": doc.procuring_entity,
				"plan_type": PLAN_TYPE_ENTITY,
				"status": "Active",
				"name": ["!=", doc.name],
			},
			fields=["name", "plan_code", "title", "start_date", "end_date"],
		)
		for row in esp_others:
			if row.plan_code == doc.plan_code:
				continue
			if _periods_overlap(doc.start_date, doc.end_date, row.start_date, row.end_date):
				frappe.throw(
					_(
						"Only one Active Entity Strategic Plan may cover a given date "
						"for this entity. Active plan {0} already overlaps."
					).format(row.plan_code)
				)


def validate_strategic_plan(doc) -> None:
	_require_code(doc.plan_code, "Plan Code")
	if not doc.version_number or int(doc.version_number) < 1:
		frappe.throw(_("Version Number must be a positive integer"))
	if doc.start_date and doc.end_date and doc.start_date > doc.end_date:
		frappe.throw(_("Start Date must be on or before End Date"))
	if doc.version_number and int(doc.version_number) > 1 and not doc.supersedes_plan_version:
		frappe.throw(_("Successor plan versions require Supersedes Plan Version"))
	if doc.plan_type == PLAN_TYPE_ENTITY:
		normalize_plan_scope(doc)
	if not doc.is_new():
		prev = doc.get_db_value("status") if hasattr(doc, "get_db_value") else None
		try:
			prev = frappe.db.get_value("Strategic Plan", doc.name, "status")
		except Exception:
			prev = None
		if prev in IMMUTABLE_PLAN and doc.has_value_changed("title"):
			# Allow status transitions only via transition service; block content edits
			pass
		if prev in IMMUTABLE_PLAN:
			for f in (
				"plan_code",
				"title",
				"plan_type",
				"start_date",
				"end_date",
				"description",
				"procuring_entity",
				"scope_type",
				"scope_id",
				"parent_plan",
			):
				if doc.has_value_changed(f):
					frappe.throw(_("Approved/Active plan versions are immutable"))


def validate_strategy_programme(doc) -> None:
	_require_code(doc.programme_code, "Programme Code")
	_assert_plan_editable(doc.plan_version)


def validate_strategy_sub_programme(doc) -> None:
	_require_code(doc.sub_programme_code, "Sub Programme Code")
	_assert_plan_editable(doc.plan_version)
	prog_plan = frappe.db.get_value("Strategy Programme", doc.programme, "plan_version")
	if prog_plan != doc.plan_version:
		frappe.throw(_("Sub-programme parent must belong to the same plan version"))


def validate_strategic_outcome(doc) -> None:
	_require_code(doc.outcome_code, "Outcome Code")
	_assert_plan_editable(doc.plan_version)
	prog_plan = frappe.db.get_value("Strategy Programme", doc.programme, "plan_version")
	if prog_plan != doc.plan_version:
		frappe.throw(_("Outcome programme must belong to the same plan version"))
	if doc.sub_programme:
		row = frappe.db.get_value(
			"Strategy Sub Programme",
			doc.sub_programme,
			["plan_version", "programme"],
			as_dict=True,
		)
		if not row or row.plan_version != doc.plan_version or row.programme != doc.programme:
			frappe.throw(_("Sub-programme must belong to the outcome's programme and plan version"))


def validate_performance_indicator(doc) -> None:
	_require_code(doc.indicator_code, "Indicator Code")
	outcome = frappe.db.get_value(
		"Strategic Outcome", doc.strategic_outcome, ["plan_version"], as_dict=True
	)
	if not outcome:
		frappe.throw(_("Strategic Outcome is required"))
	if doc.plan_version != outcome.plan_version:
		frappe.throw(_("Indicator must belong to the same plan version as its outcome"))
	_assert_plan_editable(doc.plan_version)
	if doc.measurement_type not in ("Milestone", "Boolean") and not doc.unit:
		frappe.throw(_("Unit is required for this measurement type"))


def validate_performance_target(doc) -> None:
	_require_code(doc.target_code, "Target Code")
	ind = frappe.db.get_value(
		"Performance Indicator",
		doc.performance_indicator,
		["plan_version", "measurement_type"],
		as_dict=True,
	)
	if not ind:
		frappe.throw(_("Performance Indicator is required"))
	if doc.plan_version != ind.plan_version:
		frappe.throw(_("Target must belong to the same plan version as its indicator"))
	_assert_plan_editable(doc.plan_version)
	if doc.baseline_status == "Known":
		if doc.baseline_as_of is None or not doc.baseline_source:
			frappe.throw(_("Known baseline requires as-of date and source"))
		if doc.baseline_numeric is None and not doc.baseline_text:
			frappe.throw(_("Known baseline requires a baseline value"))
	if doc.period_start and doc.period_end and doc.period_start > doc.period_end:
		frappe.throw(_("Target period start must be on or before period end"))


def validate_public_value_objective(doc) -> None:
	_require_code(doc.objective_code, "Objective Code")
	if doc.scope == "Procuring entity" and not doc.procuring_entity:
		frappe.throw(_("Entity-scoped objectives require a Procuring Entity"))
	if not doc.is_new():
		prev = frappe.db.get_value("Public Value Objective", doc.name, "status")
		if prev in IMMUTABLE_PVO:
			for f in ("objective_code", "title", "pillar", "description", "source_type"):
				if doc.has_value_changed(f):
					frappe.throw(_("Active Public Value Objective versions are immutable"))


def validate_objective_applicability_trigger(doc) -> None:
	if not doc.trigger_type or not doc.trigger_value:
		frappe.throw(_("Trigger type and value are required"))


def validate_plan_value_commitment(doc) -> None:
	_assert_plan_editable(doc.plan_version)
	pvo_status = frappe.db.get_value(
		"Public Value Objective", doc.public_value_objective_version, "status"
	)
	if pvo_status != "Active" and doc.status != "Locked":
		# Allow load of historical locked commitments; new/edit require Active PVO
		if doc.is_new() or doc.has_value_changed("public_value_objective_version"):
			frappe.throw(_("Only Active Public Value Objectives may be selected"))
	for link in doc.get("links") or []:
		if link.link_type == "Strategic Outcome" and not link.linked_outcome:
			frappe.throw(_("Commitment link requires a Strategic Outcome"))
		if link.link_type == "Performance Target" and not link.linked_target:
			frappe.throw(_("Commitment link requires a Performance Target"))


def validate_plan_value_commitment_link(doc) -> None:
	pass


def validate_performance_measurement(doc) -> None:
	tgt_plan = frappe.db.get_value("Performance Target", doc.performance_target, "plan_version")
	if doc.plan_version != tgt_plan:
		frappe.throw(_("Measurement must belong to the same plan version as its target"))
	if doc.workflow_status == "Verified" and not doc.is_new():
		prev = frappe.db.get_value("Performance Measurement", doc.name, "workflow_status")
		if prev == "Verified":
			for f in (
				"actual_numeric",
				"actual_text",
				"actual_date",
				"evidence_reference",
				"measurement_period_start",
				"measurement_period_end",
			):
				if doc.has_value_changed(f):
					frappe.throw(_("Verified measurements are immutable"))


def validate_strategy_corrective_action(doc) -> None:
	if doc.performance_measurement and not doc.performance_target:
		doc.performance_target = frappe.db.get_value(
			"Performance Measurement", doc.performance_measurement, "performance_target"
		)
	if doc.status == "Submitted for verification" and not doc.completion_evidence:
		frappe.throw(_("Completion evidence is required before verification"))


def validate_strategy_audit_event(doc) -> None:
	if not doc.event_at:
		doc.event_at = frappe.utils.now_datetime()


def _assert_plan_editable(plan_name: str) -> None:
	if not plan_name:
		frappe.throw(_("Plan version is required"))
	status = frappe.db.get_value("Strategic Plan", plan_name, "status")
	if status not in ("Draft", "Returned"):
		frappe.throw(_("Plan structure can only be edited while Draft or Returned"))
