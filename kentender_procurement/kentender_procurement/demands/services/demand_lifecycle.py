# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-SVC — Demands MVP-1 lifecycle mutations (create → approve → consume)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, getdate, now_datetime

from kentender_procurement.demands.services.demand_codes import (
	allocate_demand_code,
	allocate_item_code,
)
from kentender_procurement.demands.services.demand_permissions import (
	ROLE_BUDGET,
	ROLE_BUSINESS,
	ROLE_PAA,
	ROLE_PLANNING,
	ROLE_REQUESTER,
	ROLE_VIEWER,
	assert_demand_scope,
	require_operational_roles,
	throw_demand_error,
)
from kentender_procurement.demands.services.demand_transitions import (
	preview_transition,
	resolve_transition,
)

ERR_NOT_FOUND = "DEMAND_NOT_FOUND"
ERR_VALIDATION = "DEMAND_VALIDATION_ERROR"
ERR_CONFLICT = "DEMAND_STATE_CONFLICT"
ERR_FUNDING = "DEMAND_FUNDING_ERROR"


def _now():
	return now_datetime()


def _actor(user: str | None = None) -> str:
	return (user or frappe.session.user or "").strip() or frappe.session.user


def get_demand(demand: str) -> frappe.Document:
	key = (demand or "").strip()
	if not key:
		throw_demand_error(ERR_NOT_FOUND, "Demand is required")
	name = key
	if not frappe.db.exists("Demand", name):
		name = frappe.db.get_value("Demand", {"demand_code": key}, "name") or ""
	if not name:
		throw_demand_error(ERR_NOT_FOUND, f"Demand not found: {key}")
	return frappe.get_doc("Demand", name)


def project_demand(doc: frappe.Document) -> dict[str, Any]:
	items = frappe.get_all(
		"Demand Item",
		filters={"demand": doc.name},
		fields=[
			"name",
			"item_code",
			"description",
			"quantity",
			"uom",
			"requester_estimate",
			"confirmed_quantity",
			"confirmed_uom",
			"confirmed_estimate",
			"consumed_quantity",
			"consumed_amount",
			"remaining_quantity",
			"remaining_amount",
		],
		order_by="creation asc",
	)
	return {
		"name": doc.name,
		"demand_code": doc.demand_code,
		"title": doc.title,
		"procuring_entity": doc.procuring_entity,
		"owner_org_unit": doc.owner_org_unit,
		"delivery_org_unit": doc.delivery_org_unit,
		"requester": doc.requester,
		"status": doc.status,
		"current_stage": doc.current_stage,
		"current_owner": doc.current_owner,
		"demand_route": doc.demand_route,
		"urgency": doc.urgency,
		"requester_estimate": flt(doc.requester_estimate),
		"confirmed_estimate": flt(doc.confirmed_estimate),
		"currency": doc.currency or "KES",
		"procurement_category": doc.procurement_category,
		"planning_ready": int(doc.planning_ready or 0),
		"planning_usage": doc.planning_usage,
		"approved_baseline_version": int(doc.approved_baseline_version or 0),
		"items": items,
		"modified": str(doc.modified) if doc.modified else None,
	}


def _record_decision(
	doc: frappe.Document,
	*,
	stage: str,
	decision: str,
	actor: str,
	comment: str | None = None,
	reason: str | None = None,
	snapshot: dict | None = None,
) -> None:
	frappe.get_doc(
		{
			"doctype": "Demand Decision",
			"demand": doc.name,
			"stage": stage,
			"decision": decision,
			"actor": actor,
			"actor_role": ",".join(sorted(frappe.get_roles(actor)[:5])),
			"decided_at": _now(),
			"comment": comment or "",
			"reason": reason or "",
			"decision_input_snapshot": json.dumps(snapshot or project_demand(doc), default=str),
		}
	).insert(ignore_permissions=True)


def _assert_editable_preparation(doc: frappe.Document) -> None:
	if doc.status not in ("Draft", "Returned") or doc.current_stage != "Request Preparation":
		throw_demand_error(
			ERR_CONFLICT,
			f"Demand {doc.demand_code} is not editable in status {doc.status}",
		)


def create_or_update_demand(
	*,
	demand: str | None = None,
	values: dict[str, Any] | None = None,
	items: list[dict[str, Any]] | None = None,
	user: str | None = None,
	demand_code: str | None = None,
) -> dict[str, Any]:
	"""DEM-SVC-001 — create or update Demand + items in Draft/Returned preparation."""
	actor = _actor(user)
	require_operational_roles(ROLE_REQUESTER, user=actor)
	values = dict(values or {})
	pe = values.get("procuring_entity")
	ou = values.get("owner_org_unit")

	if demand:
		doc = get_demand(demand)
		pe = pe or doc.procuring_entity
		ou = ou or doc.owner_org_unit
		assert_demand_scope(procuring_entity=pe, owner_org_unit=ou, user=actor, require_write=True)
		_assert_editable_preparation(doc)
		_apply_requester_fields(doc, values)
		doc.save(ignore_permissions=True)
	else:
		if not pe or not ou:
			throw_demand_error(ERR_VALIDATION, "procuring_entity and owner_org_unit are required")
		assert_demand_scope(procuring_entity=pe, owner_org_unit=ou, user=actor, require_write=True)
		code = (demand_code or "").strip() or allocate_demand_code(pe)
		doc = frappe.get_doc(
			{
				"doctype": "Demand",
				"demand_code": code,
				"title": values.get("title") or "Untitled Demand",
				"procuring_entity": pe,
				"owner_org_unit": ou,
				"delivery_org_unit": values.get("delivery_org_unit"),
				"requester": values.get("requester") or actor,
				"technical_contact": values.get("technical_contact"),
				"need_statement": values.get("need_statement"),
				"expected_outcome": values.get("expected_outcome"),
				"beneficiaries": values.get("beneficiaries"),
				"delivery_location": values.get("delivery_location"),
				"required_by_date": values.get("required_by_date"),
				"demand_route": values.get("demand_route") or "Standard",
				"urgency": values.get("urgency") or "Medium",
				"route_justification": values.get("route_justification"),
				"requester_estimate": values.get("requester_estimate"),
				"estimate_source": values.get("estimate_source"),
				"estimate_confidence": values.get("estimate_confidence"),
				"currency": values.get("currency") or "KES",
				"status": "Draft",
				"current_stage": "Request Preparation",
				"current_owner": actor,
				"planning_usage": "Not taken up",
				"fixture_namespace": values.get("fixture_namespace"),
			}
		)
		doc.insert(ignore_permissions=True)

	if items is not None:
		_replace_items(doc, items)

	doc.reload()
	return {"ok": True, "demand": project_demand(doc)}


def _apply_requester_fields(doc: frappe.Document, values: dict[str, Any]) -> None:
	for field in (
		"title",
		"delivery_org_unit",
		"technical_contact",
		"need_statement",
		"expected_outcome",
		"beneficiaries",
		"delivery_location",
		"required_by_date",
		"demand_route",
		"urgency",
		"route_justification",
		"requester_estimate",
		"estimate_source",
		"estimate_confidence",
		"currency",
	):
		if field in values:
			doc.set(field, values[field])


def _replace_items(doc: frappe.Document, items: list[dict[str, Any]]) -> None:
	existing = frappe.get_all("Demand Item", filters={"demand": doc.name}, pluck="name")
	for name in existing:
		frappe.delete_doc("Demand Item", name, ignore_permissions=True, force=1)
	for idx, raw in enumerate(items or [], start=1):
		desc = (raw.get("description") or "").strip()
		if not desc:
			continue
		frappe.get_doc(
			{
				"doctype": "Demand Item",
				"demand": doc.name,
				"item_code": allocate_item_code(doc.demand_code, idx),
				"description": desc,
				"quantity": raw.get("quantity"),
				"uom": raw.get("uom"),
				"requester_estimate": raw.get("requester_estimate"),
				"currency": doc.currency or "KES",
			}
		).insert(ignore_permissions=True)


def _assert_submission_ready(doc: frappe.Document) -> None:
	missing = []
	for field, label in (
		("title", "title"),
		("need_statement", "need statement"),
		("expected_outcome", "expected outcome"),
		("beneficiaries", "beneficiaries"),
		("required_by_date", "required-by date"),
		("delivery_location", "delivery location"),
		("demand_route", "demand route"),
		("owner_org_unit", "owner organisational unit"),
	):
		if not doc.get(field):
			missing.append(label)
	if doc.demand_route == "Emergency" and not (doc.route_justification or "").strip():
		missing.append("route justification")
	items = frappe.db.count("Demand Item", {"demand": doc.name})
	if not items:
		missing.append("at least one need item")
	if missing:
		throw_demand_error(ERR_VALIDATION, "Submission incomplete: " + ", ".join(missing))


def submit_demand(*, demand: str, user: str | None = None) -> dict[str, Any]:
	"""DEM-SVC-002."""
	actor = _actor(user)
	doc = get_demand(demand)
	assert_demand_scope(
		procuring_entity=doc.procuring_entity,
		owner_org_unit=doc.owner_org_unit,
		user=actor,
		require_write=True,
	)
	_assert_submission_ready(doc)
	result = preview_transition(
		status=doc.status,
		stage=doc.current_stage,
		action="Submit",
		procuring_entity=doc.procuring_entity,
		owner_org_unit=doc.owner_org_unit,
		requester=doc.requester,
		user=actor,
	)
	doc.status = result.status
	doc.current_stage = result.stage
	doc.submitted_at = _now()
	doc.current_owner = None
	doc.save(ignore_permissions=True)
	_record_decision(doc, stage="Request Preparation", decision="Submit", actor=actor)
	doc.reload()
	return {"ok": True, "demand": project_demand(doc)}


def record_business_decision(
	*,
	demand: str,
	decision: str,
	reason: str | None = None,
	comment: str | None = None,
	user: str | None = None,
	small_entity_exception: bool = False,
) -> dict[str, Any]:
	"""DEM-SVC-003 — Support | Return | Reject."""
	actor = _actor(user)
	action = (decision or "").strip()
	if action not in ("Support", "Return", "Reject"):
		throw_demand_error(ERR_VALIDATION, "decision must be Support, Return or Reject")
	doc = get_demand(demand)
	assert_demand_scope(
		procuring_entity=doc.procuring_entity,
		owner_org_unit=doc.owner_org_unit,
		user=actor,
		require_write=True,
	)
	if action in ("Return", "Reject") and not (reason or "").strip():
		throw_demand_error(ERR_VALIDATION, "reason is required")
	result = preview_transition(
		status=doc.status,
		stage=doc.current_stage,
		action=action,
		procuring_entity=doc.procuring_entity,
		owner_org_unit=doc.owner_org_unit,
		requester=doc.requester,
		user=actor,
		small_entity_exception=small_entity_exception,
	)
	doc.status = result.status
	doc.current_stage = result.stage
	if action == "Reject":
		doc.rejected_at = _now()
	if action == "Return":
		doc.current_owner = doc.requester
	doc.save(ignore_permissions=True)
	_record_decision(
		doc,
		stage="Business Review",
		decision=action,
		actor=actor,
		comment=comment,
		reason=reason,
	)
	doc.reload()
	return {"ok": True, "demand": project_demand(doc)}


def enrich_demand(
	*,
	demand: str,
	values: dict[str, Any] | None = None,
	strategy_references: list[dict[str, Any]] | None = None,
	value_treatments: list[dict[str, Any]] | None = None,
	send_for_budget: bool = False,
	user: str | None = None,
) -> dict[str, Any]:
	"""DEM-SVC-004 / 006 — procurement enrichment + optional send for budget confirmation."""
	actor = _actor(user)
	require_operational_roles(ROLE_PAA, user=actor)
	doc = get_demand(demand)
	assert_demand_scope(
		procuring_entity=doc.procuring_entity,
		owner_org_unit=doc.owner_org_unit,
		user=actor,
		require_write=True,
	)
	if doc.current_stage != "Procurement Enrichment" or doc.status != "In Review":
		throw_demand_error(ERR_CONFLICT, "Demand is not in Procurement Enrichment")
	values = dict(values or {})
	for field in (
		"confirmed_estimate",
		"estimate_basis",
		"procurement_category",
		"demand_route",
		"route_justification",
		"currency",
	):
		if field in values:
			doc.set(field, values[field])
	doc.save(ignore_permissions=True)

	if strategy_references is not None:
		_replace_strategy_refs(doc, strategy_references, actor)
	if value_treatments is not None:
		_replace_value_treatments(doc, value_treatments, actor)

	if send_for_budget:
		_assert_enrichment_ready(doc)
		result = preview_transition(
			status=doc.status,
			stage=doc.current_stage,
			action="Send for budget confirmation",
			procuring_entity=doc.procuring_entity,
			owner_org_unit=doc.owner_org_unit,
			user=actor,
		)
		doc.status = result.status
		doc.current_stage = result.stage
		doc.save(ignore_permissions=True)
		_record_decision(
			doc, stage="Procurement Enrichment", decision="Send for budget confirmation", actor=actor
		)
		suggest_funding_allocations(demand=doc.name, user=actor)

	doc.reload()
	return {"ok": True, "demand": project_demand(doc)}


def _assert_enrichment_ready(doc: frappe.Document) -> None:
	if flt(doc.confirmed_estimate) <= 0:
		throw_demand_error(ERR_VALIDATION, "confirmed estimate is required")
	if not doc.procurement_category:
		throw_demand_error(ERR_VALIDATION, "procurement category is required")
	primaries = frappe.get_all(
		"Demand Strategy Reference",
		filters={"demand": doc.name, "reference_type": "Primary"},
		pluck="name",
	)
	if len(primaries) != 1:
		throw_demand_error(ERR_VALIDATION, "exactly one Primary Strategy reference is required")


def _replace_strategy_refs(
	doc: frappe.Document, refs: list[dict[str, Any]], actor: str
) -> None:
	for name in frappe.get_all(
		"Demand Strategy Reference", filters={"demand": doc.name}, pluck="name"
	):
		frappe.delete_doc("Demand Strategy Reference", name, ignore_permissions=True, force=1)
	primaries = 0
	for raw in refs or []:
		rtype = raw.get("reference_type") or "Primary"
		if rtype == "Primary":
			primaries += 1
		frappe.get_doc(
			{
				"doctype": "Demand Strategy Reference",
				"demand": doc.name,
				"reference_type": rtype,
				"plan": raw.get("plan"),
				"plan_version_id": raw.get("plan_version_id"),
				"target_id": raw.get("target_id"),
				"target_code": raw.get("target_code"),
				"target_name": raw.get("target_name"),
				"hierarchy_path": raw.get("hierarchy_path"),
				"snapshot_label": raw.get("snapshot_label") or raw.get("target_name") or "Strategy",
				"selection_source": raw.get("selection_source") or "Manual",
				"confirmed_by": actor,
				"confirmed_at": _now(),
				"confirmation_reason": raw.get("confirmation_reason"),
			}
		).insert(ignore_permissions=True)
	if primaries > 1:
		throw_demand_error(ERR_VALIDATION, "only one Primary Strategy reference is allowed")


def _replace_value_treatments(
	doc: frappe.Document, treatments: list[dict[str, Any]], actor: str
) -> None:
	for name in frappe.get_all(
		"Demand Value Treatment", filters={"demand": doc.name}, pluck="name"
	):
		frappe.delete_doc("Demand Value Treatment", name, ignore_permissions=True, force=1)
	for raw in treatments or []:
		if not raw.get("plan_value_commitment"):
			continue
		frappe.get_doc(
			{
				"doctype": "Demand Value Treatment",
				"demand": doc.name,
				"plan_value_commitment": raw["plan_value_commitment"],
				"pvc_version_id": raw.get("pvc_version_id"),
				"pvc_snapshot": raw.get("pvc_snapshot"),
				"applicability": raw.get("applicability"),
				"treatment": raw.get("treatment") or "Apply",
				"rationale": raw.get("rationale"),
				"confirmed_by": actor,
				"confirmed_at": _now(),
			}
		).insert(ignore_permissions=True)


def suggest_strategy_context(
	*,
	demand: str,
	user: str | None = None,
) -> dict[str, Any]:
	"""DEM-SVC-005 — scoped active Strategy targets (not auto-confirmed)."""
	actor = _actor(user)
	require_operational_roles(ROLE_PAA, user=actor)
	doc = get_demand(demand)
	assert_demand_scope(
		procuring_entity=doc.procuring_entity,
		owner_org_unit=doc.owner_org_unit,
		user=actor,
		require_write=False,
	)
	from kentender_strategy.services.strategy_contracts import list_active_targets

	targets = list_active_targets(procuring_entity=doc.procuring_entity)
	return {
		"ok": True,
		"demand_code": doc.demand_code,
		"strategy_alignment": "Not assigned",
		"suggestions": targets,
	}


def validate_strategy_reference_for_demand(
	*,
	reference: dict[str, Any] | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	"""DEM-SVC-005 wrapper over Strategy validate_strategy_reference."""
	actor = _actor(user)
	require_operational_roles(ROLE_PAA, ROLE_BUSINESS, ROLE_VIEWER, user=actor)
	from kentender_strategy.services.strategy_contracts import validate_strategy_reference

	return {"ok": True, **validate_strategy_reference(reference)}


def suggest_funding_allocations(
	*,
	demand: str,
	budget_line: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	"""DEM-SVC-007 — Budget match suggestion; creates Funding Exception when needed."""
	actor = _actor(user)
	require_operational_roles(ROLE_PAA, ROLE_BUDGET, user=actor)
	doc = get_demand(demand)
	assert_demand_scope(
		procuring_entity=doc.procuring_entity,
		owner_org_unit=doc.owner_org_unit,
		user=actor,
		require_write=True,
	)
	amount = flt(doc.confirmed_estimate) or flt(doc.requester_estimate)
	if amount <= 0:
		throw_demand_error(ERR_VALIDATION, "confirmed estimate required for funding suggestion")

	from kentender_budget.services.budget_check_reserve_contracts import (
		check_funding,
		list_active_lines_for_check,
	)

	lines = list_active_lines_for_check(procuring_entity=doc.procuring_entity)
	chosen = None
	if budget_line:
		chosen = next(
			(
				ln
				for ln in lines
				if ln.get("id") == budget_line or ln.get("code") == budget_line
			),
			None,
		)
	elif len(lines) == 1:
		chosen = lines[0]

	# Clear prior automatic suggestions still Pending.
	for name in frappe.get_all(
		"Demand Funding Allocation",
		filters={"demand": doc.name, "bo_confirmation_status": "Pending"},
		pluck="name",
	):
		frappe.delete_doc("Demand Funding Allocation", name, ignore_permissions=True, force=1)

	exception_type = None
	allocation = None
	check = None
	if not lines:
		exception_type = "No Match"
	elif not chosen and len(lines) > 1:
		exception_type = "Multiple Matches"
	elif chosen:
		check = check_funding(
			budget_line=chosen["id"],
			requested_amount=amount,
			demand=doc.demand_code,
			procuring_entity=doc.procuring_entity,
		)
		if not check.get("sufficient"):
			exception_type = "Insufficient Funding"
		allocation = frappe.get_doc(
			{
				"doctype": "Demand Funding Allocation",
				"demand": doc.name,
				"budget": chosen.get("budget"),
				"budget_line": chosen["id"],
				"allocation_amount": amount,
				"currency": doc.currency or "KES",
				"matching_source": "Automatic",
				"funds_check_result": check.get("decision") if check else "",
				"funds_check_at": _now(),
				"bo_confirmation_status": "Pending",
			}
		)
		allocation.insert(ignore_permissions=True)

	exception = None
	if exception_type:
		exception = frappe.get_doc(
			{
				"doctype": "Funding Exception",
				"demand": doc.name,
				"demand_code": doc.demand_code,
				"exception_type": exception_type,
				"status": "Open",
				"current_owner": actor,
				"candidate_budget_lines": json.dumps(lines, default=str),
				"diagnostic_context": json.dumps(
					{"requested_amount": amount, "check": check}, default=str
				),
			}
		)
		exception.insert(ignore_permissions=True)

	return {
		"ok": True,
		"demand_code": doc.demand_code,
		"allocation": allocation.name if allocation else None,
		"exception": exception.name if exception else None,
		"exception_type": exception_type,
		"candidates": lines,
		"check": check,
	}


def confirm_demand_funding(
	*,
	demand: str,
	allocations: list[dict[str, Any]] | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	"""DEM-SVC-008 — Budget Officer confirm (no reservation)."""
	actor = _actor(user)
	require_operational_roles(ROLE_BUDGET, user=actor)
	doc = get_demand(demand)
	assert_demand_scope(
		procuring_entity=doc.procuring_entity,
		owner_org_unit=doc.owner_org_unit,
		user=actor,
		require_write=True,
	)
	if doc.current_stage != "Budget Confirmation" or doc.status != "In Review":
		throw_demand_error(ERR_CONFLICT, "Demand is not in Budget Confirmation")

	open_exc = frappe.get_all(
		"Funding Exception",
		filters={"demand": doc.name, "status": ["in", ["Open", "In Progress"]]},
		pluck="name",
	)
	if open_exc:
		throw_demand_error(ERR_FUNDING, "Open Funding Exceptions must be resolved first")

	from kentender_budget.services.budget_check_reserve_contracts import check_funding

	if allocations:
		for name in frappe.get_all(
			"Demand Funding Allocation", filters={"demand": doc.name}, pluck="name"
		):
			frappe.delete_doc(
				"Demand Funding Allocation", name, ignore_permissions=True, force=1
			)
		for raw in allocations:
			line = raw.get("budget_line")
			amt = flt(raw.get("allocation_amount"))
			check = check_funding(
				budget_line=line,
				requested_amount=amt,
				demand=doc.demand_code,
				procuring_entity=doc.procuring_entity,
			)
			if not check.get("sufficient"):
				throw_demand_error(ERR_FUNDING, "Insufficient funding for confirmation")
			bud = frappe.db.get_value("Budget Line", line, "budget")
			frappe.get_doc(
				{
					"doctype": "Demand Funding Allocation",
					"demand": doc.name,
					"budget": bud,
					"budget_line": line,
					"allocation_amount": amt,
					"currency": doc.currency or "KES",
					"matching_source": raw.get("matching_source") or "Budget Officer",
					"funds_check_result": check.get("decision"),
					"funds_check_at": _now(),
					"bo_confirmation_status": "Confirmed",
					"bo_confirmed_by": actor,
					"bo_confirmed_at": _now(),
					"adjustment_reason": raw.get("adjustment_reason"),
				}
			).insert(ignore_permissions=True)
	else:
		rows = frappe.get_all(
			"Demand Funding Allocation",
			filters={"demand": doc.name},
			fields=["name", "budget_line", "allocation_amount"],
		)
		if not rows:
			throw_demand_error(ERR_FUNDING, "No funding allocations to confirm")
		for row in rows:
			check = check_funding(
				budget_line=row.budget_line,
				requested_amount=flt(row.allocation_amount),
				demand=doc.demand_code,
				procuring_entity=doc.procuring_entity,
			)
			if not check.get("sufficient"):
				throw_demand_error(ERR_FUNDING, "Insufficient funding for confirmation")
			frappe.db.set_value(
				"Demand Funding Allocation",
				row.name,
				{
					"bo_confirmation_status": "Confirmed",
					"bo_confirmed_by": actor,
					"bo_confirmed_at": _now(),
					"funds_check_result": check.get("decision"),
					"funds_check_at": _now(),
				},
			)

	total = sum(
		flt(a.allocation_amount)
		for a in frappe.get_all(
			"Demand Funding Allocation",
			filters={"demand": doc.name, "bo_confirmation_status": "Confirmed"},
			fields=["allocation_amount"],
		)
	)
	if abs(total - flt(doc.confirmed_estimate)) > 0.009:
		throw_demand_error(
			ERR_FUNDING,
			"Confirmed allocations must equal the approved estimate",
		)

	result = preview_transition(
		status=doc.status,
		stage=doc.current_stage,
		action="Confirm funding",
		procuring_entity=doc.procuring_entity,
		owner_org_unit=doc.owner_org_unit,
		user=actor,
	)
	doc.status = result.status
	doc.current_stage = result.stage
	doc.save(ignore_permissions=True)
	_record_decision(doc, stage="Budget Confirmation", decision="Confirm funding", actor=actor)
	doc.reload()
	return {"ok": True, "demand": project_demand(doc)}


def resolve_funding_exception(
	*,
	exception: str,
	resolution: str,
	reason: str | None = None,
	allocations: list[dict[str, Any]] | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	"""DEM-SVC-009."""
	actor = _actor(user)
	require_operational_roles(ROLE_BUDGET, user=actor)
	if not frappe.db.exists("Funding Exception", exception):
		throw_demand_error(ERR_NOT_FOUND, "Funding Exception not found")
	exc = frappe.get_doc("Funding Exception", exception)
	doc = get_demand(exc.demand)
	assert_demand_scope(
		procuring_entity=doc.procuring_entity,
		owner_org_unit=doc.owner_org_unit,
		user=actor,
		require_write=True,
	)
	action = (resolution or "").strip()
	if action not in ("Resolved", "Return", "Cancelled"):
		throw_demand_error(ERR_VALIDATION, "resolution must be Resolved, Return or Cancelled")
	if action == "Resolved":
		if allocations:
			confirm_demand_funding(demand=doc.name, allocations=allocations, user=actor)
		exc.status = "Resolved"
		exc.resolution = "Resolved"
		exc.resolution_reason = reason or ""
		exc.resolved_by = actor
		exc.resolved_at = _now()
		exc.save(ignore_permissions=True)
		return {"ok": True, "exception": exc.name, "demand": project_demand(get_demand(doc.name))}
	if action == "Return":
		result = resolve_transition(doc.status, doc.current_stage, "Return")
		doc.status = result.status
		doc.current_stage = result.stage
		doc.save(ignore_permissions=True)
		exc.status = "Resolved"
		exc.resolution = "Returned to Procurement"
		exc.resolution_reason = reason or ""
		exc.resolved_by = actor
		exc.resolved_at = _now()
		exc.save(ignore_permissions=True)
		_record_decision(
			doc, stage="Budget Confirmation", decision="Return", actor=actor, reason=reason
		)
		return {"ok": True, "exception": exc.name, "demand": project_demand(doc)}
	exc.status = "Cancelled"
	exc.resolution = "Cancelled"
	exc.resolution_reason = reason or ""
	exc.resolved_by = actor
	exc.resolved_at = _now()
	exc.save(ignore_permissions=True)
	return {"ok": True, "exception": exc.name}


def approve_and_reserve_demand(
	*,
	demand: str,
	user: str | None = None,
	idempotency_key: str | None = None,
) -> dict[str, Any]:
	"""DEM-SVC-010 — atomic approve + Budget reserve_funding for each allocation."""
	actor = _actor(user)
	require_operational_roles(ROLE_PAA, user=actor)
	doc = get_demand(demand)
	assert_demand_scope(
		procuring_entity=doc.procuring_entity,
		owner_org_unit=doc.owner_org_unit,
		user=actor,
		require_write=True,
	)
	if doc.current_stage != "Final Approval" or doc.status != "In Review":
		throw_demand_error(ERR_CONFLICT, "Demand is not in Final Approval")

	open_exc = frappe.get_all(
		"Funding Exception",
		filters={"demand": doc.name, "status": ["in", ["Open", "In Progress"]]},
		pluck="name",
	)
	if open_exc:
		throw_demand_error(ERR_FUNDING, "Open Funding Exceptions block approval")

	allocs = frappe.get_all(
		"Demand Funding Allocation",
		filters={"demand": doc.name, "bo_confirmation_status": "Confirmed"},
		fields=["name", "budget_line", "allocation_amount", "funding_reservation"],
	)
	if not allocs:
		throw_demand_error(ERR_FUNDING, "Confirmed funding allocations are required")
	total = sum(flt(a.allocation_amount) for a in allocs)
	if abs(total - flt(doc.confirmed_estimate)) > 0.009:
		throw_demand_error(ERR_FUNDING, "Allocations must equal confirmed estimate")

	from kentender_budget.services.budget_check_reserve_contracts import reserve_funding

	reservations: list[str] = []
	for row in allocs:
		if row.funding_reservation:
			reservations.append(row.funding_reservation)
			continue
		key = (
			idempotency_key
			or f"{doc.demand_code}:{row.budget_line}:{flt(row.allocation_amount):.2f}"
		)
		res = reserve_funding(
			budget_line=row.budget_line,
			demand_name=doc.demand_code,
			requested_amount=flt(row.allocation_amount),
			idempotency_key=key,
			actor=actor,
			procuring_entity=doc.procuring_entity,
		)
		reservations.append(res["reservation_id"])
		frappe.db.set_value(
			"Demand Funding Allocation",
			row.name,
			{
				"funding_reservation": res["reservation_id"],
				"reservation_status": res.get("status") or "Reserved",
			},
		)

	result = resolve_transition(doc.status, doc.current_stage, "Approve")
	doc.status = result.status
	doc.current_stage = result.stage
	doc.approved_at = _now()
	doc.planning_ready = 1
	doc.planning_usage = "Not taken up"
	doc.approved_baseline_version = int(doc.approved_baseline_version or 0) + 1
	doc.approved_baseline_snapshot = json.dumps(project_demand(doc), default=str)
	doc.save(ignore_permissions=True)
	_record_decision(doc, stage="Final Approval", decision="Approve", actor=actor)

	doc.reload()
	return {
		"ok": True,
		"demand": project_demand(doc),
		"reservations": reservations,
	}


def cancel_and_release_demand(
	*,
	demand: str,
	reason: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	"""DEM-SVC-011 — cancel; release unconsumed reservations via Budget shim."""
	actor = _actor(user)
	doc = get_demand(demand)
	assert_demand_scope(
		procuring_entity=doc.procuring_entity,
		owner_org_unit=doc.owner_org_unit,
		user=actor,
		require_write=True,
	)
	if doc.status == "Approved":
		require_operational_roles(ROLE_PAA, user=actor)
		from kentender_budget.api.dia_budget_control import release_reservation

		allocs = frappe.get_all(
			"Demand Funding Allocation",
			filters={"demand": doc.name},
			fields=["funding_reservation"],
		)
		for row in allocs:
			if row.funding_reservation:
				release_reservation(reservation_id=row.funding_reservation, actor=actor)
		doc.status = "Cancelled"
		doc.current_stage = "Complete"
		doc.cancelled_at = _now()
		doc.planning_ready = 0
		doc.save(ignore_permissions=True)
		_record_decision(
			doc, stage="Complete", decision="Cancel", actor=actor, reason=reason
		)
		doc.reload()
		return {"ok": True, "demand": project_demand(doc)}

	result = preview_transition(
		status=doc.status,
		stage=doc.current_stage,
		action="Cancel",
		procuring_entity=doc.procuring_entity,
		owner_org_unit=doc.owner_org_unit,
		user=actor,
	)
	doc.status = result.status
	doc.current_stage = result.stage
	doc.cancelled_at = _now()
	doc.save(ignore_permissions=True)
	_record_decision(
		doc, stage="Request Preparation", decision="Cancel", actor=actor, reason=reason
	)
	doc.reload()
	return {"ok": True, "demand": project_demand(doc)}


def consume_demand_in_planning(
	*,
	demand: str,
	demand_item: str,
	consumed_amount: float,
	consumed_quantity: float | None = None,
	plan_item_code: str | None = None,
	package: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	"""DEM-SVC-012."""
	actor = _actor(user)
	require_operational_roles(ROLE_PLANNING, user=actor)
	doc = get_demand(demand)
	assert_demand_scope(
		procuring_entity=doc.procuring_entity,
		owner_org_unit=doc.owner_org_unit,
		user=actor,
		require_write=True,
	)
	if doc.status != "Approved" or not int(doc.planning_ready or 0):
		throw_demand_error(ERR_CONFLICT, "Only Approved Planning Ready Demands may be consumed")
	if not frappe.db.exists("Demand Item", demand_item):
		throw_demand_error(ERR_NOT_FOUND, "Demand Item not found")
	item = frappe.get_doc("Demand Item", demand_item)
	if item.demand != doc.name:
		throw_demand_error(ERR_VALIDATION, "Demand Item does not belong to Demand")

	amt = flt(consumed_amount)
	if amt <= 0:
		throw_demand_error(ERR_VALIDATION, "consumed_amount must be positive")
	remaining = flt(item.remaining_amount)
	if remaining <= 0:
		# initialise remaining from confirmed/requester estimate on first consume
		remaining = flt(item.confirmed_estimate) or flt(item.requester_estimate) or flt(
			doc.confirmed_estimate
		)
		item.remaining_amount = remaining
	if amt - remaining > 0.009:
		throw_demand_error(ERR_VALIDATION, "Cannot over-consume Demand Item")

	rsv = frappe.db.get_value(
		"Demand Funding Allocation",
		{"demand": doc.name, "bo_confirmation_status": "Confirmed"},
		"funding_reservation",
	)
	frappe.get_doc(
		{
			"doctype": "Planning Consumption",
			"demand": doc.name,
			"demand_item": item.name,
			"plan_item_code": plan_item_code,
			"package": package,
			"consumed_quantity": consumed_quantity,
			"consumed_amount": amt,
			"currency": doc.currency or "KES",
			"funding_reservation": rsv,
			"consumed_by": actor,
			"consumed_at": _now(),
		}
	).insert(ignore_permissions=True)

	item.consumed_amount = flt(item.consumed_amount) + amt
	item.remaining_amount = max(0.0, remaining - amt)
	if consumed_quantity is not None:
		item.consumed_quantity = flt(item.consumed_quantity) + flt(consumed_quantity)
	item.save(ignore_permissions=True)

	_refresh_planning_usage(doc)
	doc.reload()
	return {"ok": True, "demand": project_demand(doc)}


def _refresh_planning_usage(doc: frappe.Document) -> None:
	items = frappe.get_all(
		"Demand Item",
		filters={"demand": doc.name},
		fields=["consumed_amount", "remaining_amount", "confirmed_estimate", "requester_estimate"],
	)
	if not items:
		usage = "Not taken up"
	else:
		any_consumed = any(flt(i.consumed_amount) > 0 for i in items)
		all_done = all(
			flt(i.remaining_amount) <= 0.009
			and (
				flt(i.consumed_amount) > 0
				or flt(i.confirmed_estimate)
				or flt(i.requester_estimate)
			)
			for i in items
		)
		if not any_consumed:
			usage = "Not taken up"
		elif all_done:
			usage = "Fully planned"
		else:
			usage = "Partially planned"
	# Status stays Approved.
	frappe.db.set_value("Demand", doc.name, "planning_usage", usage, update_modified=False)


def get_demand_audit(*, demand: str, user: str | None = None) -> dict[str, Any]:
	"""DEM-SVC-013."""
	actor = _actor(user)
	doc = get_demand(demand)
	assert_demand_scope(
		procuring_entity=doc.procuring_entity,
		owner_org_unit=doc.owner_org_unit,
		user=actor,
		require_write=False,
	)
	decisions = frappe.get_all(
		"Demand Decision",
		filters={"demand": doc.name},
		fields=[
			"name",
			"stage",
			"decision",
			"actor",
			"actor_role",
			"decided_at",
			"comment",
			"reason",
		],
		order_by="decided_at asc",
	)
	return {"ok": True, "demand_code": doc.demand_code, "decisions": decisions}


def list_demands_for_workspace(
	*,
	user: str | None = None,
	filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""DEM-SVC-014 — scoped queue projection + counts by stage/status."""
	actor = _actor(user)
	from kentender_core.services.org_scope_access import (
		permitted_org_units,
		permitted_procuring_entities,
	)

	filters = dict(filters or {})
	pes = permitted_procuring_entities(actor)
	clauses: list[list[Any]] = []
	if pes is not None:
		if not pes:
			return {"ok": True, "total": 0, "rows": [], "counts": {}, "filters_applied": filters}
		clauses.append(["procuring_entity", "in", list(pes)])
	units = permitted_org_units(actor)
	if units is not None and units:
		clauses.append(["owner_org_unit", "in", list(units)])

	if filters.get("status"):
		clauses.append(["status", "=", filters["status"]])
	if filters.get("current_stage"):
		clauses.append(["current_stage", "=", filters["current_stage"]])
	if filters.get("mine"):
		clauses.append(["requester", "=", actor])

	rows = frappe.get_all(
		"Demand",
		filters=clauses or None,
		fields=[
			"name",
			"demand_code",
			"title",
			"status",
			"current_stage",
			"procuring_entity",
			"owner_org_unit",
			"confirmed_estimate",
			"requester_estimate",
			"currency",
			"modified",
		],
		order_by="modified desc",
		limit=int(filters.get("limit") or 100),
	)
	counts: dict[str, int] = {}
	for r in rows:
		key = f"{r.status}|{r.current_stage}"
		counts[key] = counts.get(key, 0) + 1
	return {
		"ok": True,
		"total": len(rows),
		"rows": rows,
		"counts": counts,
		"filters_applied": filters,
	}


def get_demand_performance(
	*,
	user: str | None = None,
	as_at: str | None = None,
	procuring_entity: str | None = None,
) -> dict[str, Any]:
	"""DEM-SVC-015 — lightweight metrics DTO with As at + drill-down keys."""
	actor = _actor(user)
	ws = list_demands_for_workspace(user=actor, filters={"limit": 500})
	rows = ws["rows"]
	if procuring_entity:
		rows = [r for r in rows if r.procuring_entity == procuring_entity]
	by_status: dict[str, int] = {}
	by_stage: dict[str, int] = {}
	value_approved = 0.0
	for r in rows:
		by_status[r.status] = by_status.get(r.status, 0) + 1
		by_stage[r.current_stage] = by_stage.get(r.current_stage, 0) + 1
		if r.status == "Approved":
			value_approved += flt(r.confirmed_estimate)
	return {
		"ok": True,
		"as_at": as_at or str(getdate()),
		"basis": "Scoped Demand rows visible to the actor",
		"counts_by_status": by_status,
		"counts_by_stage": by_stage,
		"approved_value": value_approved,
		"drill_down": [r.demand_code for r in rows[:50]],
	}
