# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-SVC — Demands MVP-1 lifecycle mutations (create → approve → consume)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, flt, getdate, now_datetime

from kentender_procurement.demands.services.demand_codes import (
	allocate_demand_code,
	allocate_item_code,
)
from kentender_procurement.demands.services.demand_permissions import (
	ERR_STALE,
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
ERR_STALE_VERSION = ERR_STALE


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
		"technical_contact": doc.technical_contact,
		"status": doc.status,
		"current_stage": doc.current_stage,
		"current_owner": doc.current_owner,
		"demand_route": doc.demand_route,
		"urgency": doc.urgency,
		"route_justification": doc.route_justification,
		"need_statement": doc.need_statement,
		"need_rationale": doc.need_rationale,
		"expected_outcome": doc.expected_outcome,
		"beneficiaries": doc.beneficiaries,
		"delivery_location": doc.delivery_location,
		"required_by_date": str(doc.required_by_date) if doc.required_by_date else None,
		"requester_estimate": flt(doc.requester_estimate),
		"confirmed_estimate": flt(doc.confirmed_estimate),
		"estimate_source": doc.estimate_source,
		"estimate_confidence": doc.estimate_confidence,
		"estimate_basis": doc.estimate_basis,
		"currency": doc.currency or "KES",
		"procurement_category": doc.procurement_category,
		"duplicate_assessment": doc.get("duplicate_assessment") or "",
		"related_demands_note": doc.get("related_demands_note") or "",
		"aggregation_treatment": doc.get("aggregation_treatment") or "",
		"aggregation_rationale": doc.get("aggregation_rationale") or "",
		"planning_ready": int(doc.planning_ready or 0),
		"planning_usage": doc.planning_usage,
		"approved_baseline_version": int(doc.approved_baseline_version or 0),
		"items": items,
		"modified": str(doc.modified) if doc.modified else None,
	}


_ROLE_DISPLAY = {
	ROLE_REQUESTER: "Requester",
	ROLE_BUSINESS: "Business Approver",
	ROLE_PAA: "Procurement Approval Authority",
	ROLE_BUDGET: "Budget Officer",
	ROLE_PLANNING: "Planning Officer",
}


def _actor_role_label(actor: str) -> str:
	roles = set(frappe.get_roles(actor))
	for role, label in _ROLE_DISPLAY.items():
		if role in roles:
			return label
	if "System Manager" in roles:
		return "System Manager"
	return ""


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
			"actor_role": _actor_role_label(actor)
			or ",".join(sorted(frappe.get_roles(actor)[:5])),
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
			issue="Demand is not in an editable preparation state",
			owner="Requester",
			action="Open the Demand only when status is Draft or Returned at Request Preparation",
		)


def create_or_update_demand(
	*,
	demand: str | None = None,
	values: dict[str, Any] | None = None,
	items: list[dict[str, Any]] | None = None,
	user: str | None = None,
	demand_code: str | None = None,
	expected_modified: str | None = None,
) -> dict[str, Any]:
	"""DEM-SVC-001 — create or update Demand + items in Draft/Returned preparation."""
	actor = _actor(user)
	require_operational_roles(ROLE_REQUESTER, user=actor)
	values = dict(values or {})
	# Allow clients to pass optimistic concurrency token in values.
	expected = (expected_modified or values.pop("expected_modified", None) or "").strip() or None
	pe = values.get("procuring_entity")
	ou = values.get("owner_org_unit")

	if demand:
		doc = get_demand(demand)
		pe = pe or doc.procuring_entity
		ou = ou or doc.owner_org_unit
		assert_demand_scope(procuring_entity=pe, owner_org_unit=ou, user=actor, require_write=True)
		_assert_editable_preparation(doc)
		if expected:
			current = str(doc.modified) if doc.modified else ""
			if current and current != expected:
				throw_demand_error(
					ERR_STALE_VERSION,
					"This Demand was changed by another user. Reload and retry.",
					issue="Stale Demand version",
					owner="Requester",
					action="Reload the form and re-apply your changes",
				)
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
				"need_rationale": values.get("need_rationale"),
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
				"estimate_basis": values.get("estimate_basis"),
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
		"need_rationale",
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
		"estimate_basis",
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
		throw_demand_error(
			ERR_VALIDATION,
			"Submission incomplete: " + ", ".join(missing),
			issue="Required fields are missing for submission",
			owner="Requester",
			action="Complete the missing fields and submit again",
		)


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
	correction_hints: list[dict[str, Any]] | None = None,
	available_funding: float | None = None,
	release_to_planning: bool = False,
) -> dict[str, Any]:
	"""DEM-SVC-003 — Support | Return | Reject.

	On Return, optional ``correction_hints`` (``[{key, label}, ...]``) and
	``available_funding`` are stored in the decision snapshot for DEM-UI-03.
	"""
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
	snap: dict[str, Any] | None = None
	if action == "Return":
		snap = {
			"demand": project_demand(doc),
			"correction_hints": list(correction_hints or []),
			"available_funding": available_funding,
		}
	_record_decision(
		doc,
		stage="Business Review",
		decision=action,
		actor=actor,
		comment=comment,
		reason=reason,
		snapshot=snap,
	)
	if action == "Support" and release_to_planning:
		doc.reload()
		doc.status = "Approved"
		doc.current_stage = "Complete"
		doc.planning_ready = 1
		doc.planning_usage = "Not taken up"
		doc.approved_at = _now()
		doc.confirmed_estimate = flt(doc.requester_estimate) or flt(doc.confirmed_estimate)
		doc.save(ignore_permissions=True)
		_record_decision(doc, stage="Complete", decision="Release to planning", actor=actor)
	doc.reload()
	return {"ok": True, "demand": project_demand(doc)}


def enrich_demand(
	*,
	demand: str,
	values: dict[str, Any] | None = None,
	items: list[dict[str, Any]] | None = None,
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
	if doc.current_stage != "Procurement Enrichment" or doc.status not in (
		"In Review",
		"Returned",
	):
		throw_demand_error(ERR_CONFLICT, "Demand is not in Procurement Enrichment")
	values = dict(values or {})
	for field in (
		"confirmed_estimate",
		"estimate_basis",
		"procurement_category",
		"demand_route",
		"route_justification",
		"currency",
		"duplicate_assessment",
		"related_demands_note",
		"aggregation_treatment",
		"aggregation_rationale",
		"strategy_no_alignment_reason",
	):
		if field in values:
			doc.set(field, values[field])
	doc.save(ignore_permissions=True)

	if items is not None:
		_apply_enrichment_items(doc, items)

	if strategy_references is not None:
		_replace_strategy_refs(doc, strategy_references, actor)
		# Assigning a Primary clears any prior no-alignment declaration.
		if any((r.get("reference_type") or "Primary") == "Primary" for r in (strategy_references or [])):
			doc.db_set("strategy_no_alignment_reason", "", update_modified=False)
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


def _apply_enrichment_items(doc: frappe.Document, items: list[dict[str, Any]]) -> None:
	"""Update confirmed item fields; create rows for new descriptions."""
	from kentender_procurement.demands.services.demand_codes import allocate_item_code

	kept: set[str] = set()
	for idx, raw in enumerate(items or [], start=1):
		desc = (raw.get("description") or "").strip()
		name = (raw.get("name") or "").strip()
		if name and frappe.db.exists("Demand Item", name):
			item = frappe.get_doc("Demand Item", name)
			if item.demand != doc.name:
				continue
			if desc:
				item.description = desc
			for field in (
				"quantity",
				"uom",
				"requester_estimate",
				"confirmed_quantity",
				"confirmed_uom",
				"confirmed_estimate",
			):
				if field in raw:
					item.set(field, raw[field])
			item.save(ignore_permissions=True)
			kept.add(item.name)
			continue
		if not desc:
			continue
		created = frappe.get_doc(
			{
				"doctype": "Demand Item",
				"demand": doc.name,
				"item_code": allocate_item_code(doc.demand_code, idx),
				"description": desc,
				"quantity": raw.get("quantity"),
				"uom": raw.get("uom"),
				"requester_estimate": raw.get("requester_estimate"),
				"confirmed_quantity": raw.get("confirmed_quantity"),
				"confirmed_uom": raw.get("confirmed_uom"),
				"confirmed_estimate": raw.get("confirmed_estimate"),
				"currency": doc.currency or "KES",
			}
		).insert(ignore_permissions=True)
		kept.add(created.name)
	# Soft-delete omitted rows only when caller sent a full replacement list.
	if items is not None:
		for existing in frappe.get_all(
			"Demand Item", filters={"demand": doc.name}, pluck="name"
		):
			if existing not in kept:
				frappe.delete_doc("Demand Item", existing, ignore_permissions=True, force=1)


def record_procurement_decision(
	*,
	demand: str,
	decision: str,
	reason: str | None = None,
	comment: str | None = None,
	user: str | None = None,
	correction_hints: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
	"""DEM-UI-05 — PAA Return | Reject from Procurement Enrichment."""
	actor = _actor(user)
	action = (decision or "").strip()
	if action not in ("Return", "Reject"):
		throw_demand_error(ERR_VALIDATION, "decision must be Return or Reject")
	require_operational_roles(ROLE_PAA, user=actor)
	doc = get_demand(demand)
	assert_demand_scope(
		procuring_entity=doc.procuring_entity,
		owner_org_unit=doc.owner_org_unit,
		user=actor,
		require_write=True,
	)
	if doc.current_stage != "Procurement Enrichment" or doc.status not in (
		"In Review",
		"Returned",
	):
		throw_demand_error(ERR_CONFLICT, "Demand is not in Procurement Enrichment")
	if not (reason or "").strip():
		throw_demand_error(ERR_VALIDATION, "reason is required")
	result = preview_transition(
		status=doc.status,
		stage=doc.current_stage,
		action=action,
		procuring_entity=doc.procuring_entity,
		owner_org_unit=doc.owner_org_unit,
		requester=doc.requester,
		user=actor,
	)
	doc.status = result.status
	doc.current_stage = result.stage
	if action == "Reject":
		doc.rejected_at = _now()
	if action == "Return":
		doc.current_owner = doc.requester
	doc.save(ignore_permissions=True)
	snap = None
	if action == "Return":
		snap = {
			"demand": project_demand(doc),
			"correction_hints": list(correction_hints or []),
		}
	_record_decision(
		doc,
		stage="Procurement Enrichment",
		decision=action,
		actor=actor,
		comment=comment,
		reason=reason,
		snapshot=snap,
	)
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
	no_align = cstr(doc.get("strategy_no_alignment_reason") or "").strip()
	if len(primaries) == 1:
		return
	if no_align and len(primaries) == 0:
		return
	throw_demand_error(
		ERR_VALIDATION,
		"exactly one Primary Strategy reference is required (or a no-alignment reason)",
	)


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


def _ou_label(ou: str | None) -> str:
	if not ou:
		return ""
	return cstr(frappe.db.get_value("Organisation Unit", ou, "unit_name") or ou)


def _plan_period_label(start_date, end_date) -> str:
	def _fmt(d) -> str:
		if not d:
			return ""
		try:
			return frappe.utils.formatdate(d, "MMM yyyy")
		except Exception:
			return cstr(d)[:10]

	a, b = _fmt(start_date), _fmt(end_date)
	if a and b:
		return f"{a} – {b}"
	return a or b or ""


def _rank_strategy_suggestions(doc: frappe.Document, targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
	"""Deterministic suggestion rank + Why suggested (DIA-FR-061 / DEM-SVC-005).

	Never auto-confirms. Reasons are rule evidence only (no generative text).
	"""
	import re

	category = cstr(doc.get("procurement_category") or "").strip()
	ou = cstr(doc.get("owner_org_unit") or "").strip()
	ou_name = _ou_label(ou)
	need = " ".join(
		[
			cstr(doc.get("need_statement") or ""),
			cstr(doc.get("title") or ""),
			cstr(doc.get("expected_outcome") or ""),
		]
	).lower()
	cat_tokens = [t for t in re.split(r"[^a-z0-9]+", category.lower()) if len(t) >= 4]
	need_tokens = [t for t in re.split(r"[^a-z0-9]+", need) if len(t) >= 5]
	# Drop ultra-common tokens that create false matches.
	stop = {"health", "digital", "services", "service", "national", "ministry", "system", "systems"}
	need_tokens = [t for t in need_tokens if t not in stop]

	plan_ids = list({cstr(t.get("plan_version_id") or "") for t in targets if t.get("plan_version_id")})
	plan_meta: dict[str, dict[str, Any]] = {}
	if plan_ids:
		for row in frappe.get_all(
			"Strategic Plan",
			filters={"name": ["in", plan_ids]},
			fields=["name", "title", "plan_code", "owner_org_unit", "start_date", "end_date"],
		):
			plan_meta[row.name] = row

	ranked: list[dict[str, Any]] = []
	for t in targets:
		plan = plan_meta.get(cstr(t.get("plan_version_id") or ""), {})
		path = list(t.get("path") or [])
		path_names = [cstr(p.get("name") or "") for p in path]
		plan_title = cstr(plan.get("title") or t.get("plan_code") or "")
		hierarchy = " > ".join([p for p in [plan_title, *path_names] if p])
		hay = " ".join(
			[
				cstr(t.get("node_name") or ""),
				cstr(t.get("snapshot_label") or ""),
				hierarchy,
				" ".join(path_names),
			]
		).lower()

		score = 0
		reason_bits: list[str] = []
		plan_ou = cstr(plan.get("owner_org_unit") or "")
		if ou and plan_ou and plan_ou == ou:
			score += 100
			label = ou_name or plan_ou
			reason_bits.append(f"Owned by the {label}" if label else "Owned by the Demand owning unit")

		if category and any(tok in hay for tok in cat_tokens):
			score += 40
			reason_bits.append(f"relevant to {category}")

		matched_need = [tok for tok in need_tokens if tok in hay]
		if matched_need and score < 40:
			# Softer signal when ownership/category did not fire.
			score += 15
			sample = matched_need[0].replace("-", " ")
			reason_bits.append(f"Related to {sample}")
		elif matched_need and score >= 40:
			score += 10

		why = ""
		if reason_bits:
			if len(reason_bits) == 1:
				why = reason_bits[0] + "."
			elif reason_bits[0].startswith("Owned by") and any(
				b.startswith("relevant to") for b in reason_bits[1:]
			):
				rel = next(b for b in reason_bits[1:] if b.startswith("relevant to"))
				why = f"{reason_bits[0]} and {rel}."
			else:
				why = "; ".join(reason_bits) + "."

		row = dict(t)
		row.update(
			{
				"plan_title": plan_title,
				"plan_owner_org_unit": plan_ou,
				"effective_period": _plan_period_label(plan.get("start_date"), plan.get("end_date")),
				"hierarchy_path": hierarchy or cstr(t.get("snapshot_label") or ""),
				"suggestion_score": score,
				"is_suggested": score >= 40,
				"why_suggested": why,
			}
		)
		ranked.append(row)

	ranked.sort(
		key=lambda r: (
			0 if r.get("is_suggested") else 1,
			-(int(r.get("suggestion_score") or 0)),
			cstr(r.get("node_name") or "").lower(),
		)
	)
	return ranked


def suggest_strategy_context(
	*,
	demand: str,
	user: str | None = None,
) -> dict[str, Any]:
	"""DEM-SVC-005 — scoped active Strategy targets with deterministic suggestion rank."""
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
	ranked = _rank_strategy_suggestions(doc, targets)
	plans = []
	seen_plans: set[str] = set()
	periods = []
	seen_periods: set[str] = set()
	for s in ranked:
		pc = cstr(s.get("plan_code") or "")
		if pc and pc not in seen_plans:
			seen_plans.add(pc)
			plans.append(
				{
					"plan_code": pc,
					"plan_title": s.get("plan_title") or pc,
					"id": s.get("plan_version_id"),
					"code": pc,
					"name": s.get("plan_title") or pc,
				}
			)
		per = cstr(s.get("effective_period") or "")
		if per and per not in seen_periods:
			seen_periods.add(per)
			periods.append(per)
	return {
		"ok": True,
		"demand_code": doc.demand_code,
		"strategy_alignment": "Not assigned",
		"suggestions": ranked,
		"filters": {"plans": plans, "effective_periods": periods},
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
	match_basis = None  # single_line | strategy_target | explicit
	if budget_line:
		chosen = next(
			(
				ln
				for ln in lines
				if ln.get("id") == budget_line or ln.get("code") == budget_line
			),
			None,
		)
		match_basis = "explicit" if chosen else None
	elif len(lines) == 1:
		chosen = lines[0]
		match_basis = "single_line"
	elif len(lines) > 1:
		# DIA-FR-076 — use Demand Primary Strategy target to auto-pick when unique.
		primary = frappe.db.get_value(
			"Demand Strategy Reference",
			{"demand": doc.name, "reference_type": "Primary"},
			["target_code", "target_name"],
			as_dict=True,
		)
		t_code = ((primary or {}).get("target_code") or "").strip()
		t_name = ((primary or {}).get("target_name") or "").strip()
		matched: list[dict[str, Any]] = []
		if t_code:
			matched = [
				ln
				for ln in lines
				if (ln.get("primary_target_code") or "").strip() == t_code
			]
		if not matched and t_name:
			matched = [
				ln
				for ln in lines
				if (ln.get("primary_target_name") or "").strip() == t_name
			]
		if len(matched) == 1:
			chosen = matched[0]
			match_basis = "strategy_target"

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
					{
						"requested_amount": amount,
						"check": check,
						"match_basis": match_basis,
						"active_line_count": len(lines),
					},
					default=str,
				),
			}
		)
		exception.insert(ignore_permissions=True)
	elif allocation:
		# Successful auto/explicit match supersedes prior open funding exceptions
		# (including Insufficient Funding from an earlier shortfall).
		for exc_name in frappe.get_all(
			"Funding Exception",
			filters={
				"demand": doc.name,
				"status": ["in", ["Open", "In Progress"]],
			},
			pluck="name",
		):
			frappe.db.set_value(
				"Funding Exception",
				exc_name,
				{
					"status": "Resolved",
					"resolution": f"Superseded by {match_basis or 'automatic'} recommendation",
					"resolved_by": actor,
					"resolved_at": _now(),
				},
			)

	return {
		"ok": True,
		"demand_code": doc.demand_code,
		"allocation": allocation.name if allocation else None,
		"exception": exception.name if exception else None,
		"exception_type": exception_type,
		"match_basis": match_basis,
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
	if doc.current_stage != "Budget Confirmation" or doc.status not in (
		"In Review",
		"Returned",
	):
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


def return_budget_confirmation(
	*,
	demand: str,
	reason: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	"""DEM-UI-06 — Budget Officer Return to Procurement Enrichment (reason required)."""
	actor = _actor(user)
	require_operational_roles(ROLE_BUDGET, user=actor)
	doc = get_demand(demand)
	assert_demand_scope(
		procuring_entity=doc.procuring_entity,
		owner_org_unit=doc.owner_org_unit,
		user=actor,
		require_write=True,
	)
	if doc.current_stage != "Budget Confirmation" or doc.status not in (
		"In Review",
		"Returned",
	):
		throw_demand_error(ERR_CONFLICT, "Demand is not in Budget Confirmation")
	if not (reason or "").strip():
		throw_demand_error(ERR_VALIDATION, "A reason is required")

	result = preview_transition(
		status=doc.status,
		stage=doc.current_stage,
		action="Return",
		procuring_entity=doc.procuring_entity,
		owner_org_unit=doc.owner_org_unit,
		user=actor,
	)
	doc.status = result.status
	doc.current_stage = result.stage
	doc.save(ignore_permissions=True)

	# Close open exceptions so enrichment can re-send cleanly.
	for exc_name in frappe.get_all(
		"Funding Exception",
		filters={"demand": doc.name, "status": ["in", ["Open", "In Progress"]]},
		pluck="name",
	):
		frappe.db.set_value(
			"Funding Exception",
			exc_name,
			{
				"status": "Resolved",
				"resolution": "Returned to Procurement",
				"resolution_reason": (reason or "").strip(),
				"resolved_by": actor,
				"resolved_at": _now(),
			},
		)

	_record_decision(
		doc,
		stage="Budget Confirmation",
		decision="Return",
		actor=actor,
		reason=(reason or "").strip(),
	)
	doc.reload()
	return {"ok": True, "demand": project_demand(doc)}


def adjust_funding_allocation(
	*,
	demand: str,
	budget_line: str | None = None,
	allocation_amount: float | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	"""DEM-UI-06 — Replace/update Pending allocation without confirming (BO Adjust)."""
	actor = _actor(user)
	require_operational_roles(ROLE_BUDGET, user=actor)
	doc = get_demand(demand)
	assert_demand_scope(
		procuring_entity=doc.procuring_entity,
		owner_org_unit=doc.owner_org_unit,
		user=actor,
		require_write=True,
	)
	if doc.current_stage != "Budget Confirmation" or doc.status not in (
		"In Review",
		"Returned",
	):
		throw_demand_error(ERR_CONFLICT, "Demand is not in Budget Confirmation")

	line_key = (budget_line or "").strip() or None
	amount = flt(allocation_amount) if allocation_amount is not None else None

	if line_key:
		suggestion = suggest_funding_allocations(
			demand=doc.name, budget_line=line_key, user=actor
		)
		if suggestion.get("exception_type") and not suggestion.get("allocation"):
			return {
				"ok": True,
				"demand": project_demand(doc),
				"suggestion": suggestion,
			}

	pending = frappe.get_all(
		"Demand Funding Allocation",
		filters={"demand": doc.name, "bo_confirmation_status": "Pending"},
		fields=["name", "budget_line", "allocation_amount"],
		order_by="creation desc",
		limit=1,
	)
	if not pending:
		throw_demand_error(ERR_FUNDING, "No Pending funding allocation to adjust")

	row = pending[0]
	new_amount = amount if amount is not None and amount > 0 else flt(row.allocation_amount)
	from kentender_budget.services.budget_check_reserve_contracts import check_funding

	check = check_funding(
		budget_line=row.budget_line,
		requested_amount=new_amount,
		demand=doc.demand_code,
		procuring_entity=doc.procuring_entity,
	)
	frappe.db.set_value(
		"Demand Funding Allocation",
		row.name,
		{
			"allocation_amount": new_amount,
			"matching_source": "Budget Officer",
			"funds_check_result": check.get("decision"),
			"funds_check_at": _now(),
		},
	)
	# Adjust clears open funding exceptions (incl. Insufficient Funding) when funding is OK.
	if check.get("sufficient"):
		for exc_name in frappe.get_all(
			"Funding Exception",
			filters={
				"demand": doc.name,
				"status": ["in", ["Open", "In Progress"]],
			},
			pluck="name",
		):
			frappe.db.set_value(
				"Funding Exception",
				exc_name,
				{
					"status": "Resolved",
					"resolution": "Adjusted by Budget Officer",
					"resolved_by": actor,
					"resolved_at": _now(),
				},
			)
	elif check.get("sufficient") is False:
		# Ensure Insufficient Funding exception exists when adjust creates shortfall.
		open_insuff = frappe.db.exists(
			"Funding Exception",
			{
				"demand": doc.name,
				"status": ["in", ["Open", "In Progress"]],
				"exception_type": "Insufficient Funding",
			},
		)
		if not open_insuff:
			frappe.get_doc(
				{
					"doctype": "Funding Exception",
					"demand": doc.name,
					"demand_code": doc.demand_code,
					"exception_type": "Insufficient Funding",
					"status": "Open",
					"current_owner": actor,
					"diagnostic_context": json.dumps({"check": check}, default=str),
				}
			).insert(ignore_permissions=True)

	doc.reload()
	return {
		"ok": True,
		"demand": project_demand(doc),
		"allocation": row.name,
		"check": check,
	}


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
		if not (reason or "").strip():
			throw_demand_error(ERR_VALIDATION, "Return note is required to resolve the exception")
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


def save_funding_exception_note(
	*,
	exception: str,
	reason: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	"""DEM-UI-07 — persist resolution note; keep exception open (In Progress)."""
	actor = _actor(user)
	require_operational_roles(ROLE_BUDGET, user=actor)
	if not frappe.db.exists("Funding Exception", exception):
		throw_demand_error(ERR_NOT_FOUND, "Funding Exception not found")
	exc = frappe.get_doc("Funding Exception", exception)
	if (exc.status or "") not in ("Open", "In Progress"):
		throw_demand_error(ERR_CONFLICT, "Funding Exception is not open")
	doc = get_demand(exc.demand)
	assert_demand_scope(
		procuring_entity=doc.procuring_entity,
		owner_org_unit=doc.owner_org_unit,
		user=actor,
		require_write=True,
	)
	note = (reason or "").strip()
	if not note:
		throw_demand_error(ERR_VALIDATION, "Resolution note is required")
	exc.resolution_reason = note
	exc.status = "In Progress"
	exc.current_owner = actor
	exc.save(ignore_permissions=True)
	return {
		"ok": True,
		"exception": exc.name,
		"status": exc.status,
		"demand": project_demand(doc),
	}


def _invalidate_bo_signoff_return_to_budget_confirmation(
	doc: frappe.Document,
	actor: str,
	*,
	reason: str,
	decision: str = "Material change",
) -> None:
	"""DIA-FR-087 / DIA-FR-093 — clear BO confirm and return to Budget Confirmation."""
	for row in frappe.get_all(
		"Demand Funding Allocation",
		filters={"demand": doc.name},
		fields=["name", "funding_reservation", "bo_confirmation_status"],
	):
		frappe.db.set_value(
			"Demand Funding Allocation",
			row.name,
			{
				"bo_confirmation_status": "Pending",
				"bo_confirmed_by": "",
				"bo_confirmed_at": None,
				"funding_reservation": "",
				"reservation_status": "",
			},
		)
	doc.status = "In Review"
	doc.current_stage = "Budget Confirmation"
	doc.planning_ready = 0
	doc.save(ignore_permissions=True)
	_record_decision(
		doc,
		stage="Final Approval",
		decision=decision,
		actor=actor,
		reason=(reason or "").strip(),
	)


def apply_material_funding_change(
	*,
	demand: str,
	confirmed_estimate: float | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	"""DIA-AC-019 / DIA-FR-087 — funding-relevant change after BO sign-off."""
	actor = _actor(user)
	require_operational_roles(ROLE_PAA, ROLE_BUDGET, user=actor)
	doc = get_demand(demand)
	assert_demand_scope(
		procuring_entity=doc.procuring_entity,
		owner_org_unit=doc.owner_org_unit,
		user=actor,
		require_write=True,
	)
	if doc.current_stage != "Final Approval" or doc.status != "In Review":
		throw_demand_error(
			ERR_CONFLICT, "Material funding change applies only after BO sign-off"
		)
	if confirmed_estimate is None:
		throw_demand_error(ERR_VALIDATION, "confirmed_estimate is required")
	new_estimate = flt(confirmed_estimate)
	if new_estimate <= 0:
		throw_demand_error(ERR_VALIDATION, "confirmed_estimate must be positive")
	if abs(new_estimate - flt(doc.confirmed_estimate)) <= 0.009:
		throw_demand_error(ERR_VALIDATION, "No material funding change detected")

	doc.confirmed_estimate = new_estimate
	doc.save(ignore_permissions=True)
	_invalidate_bo_signoff_return_to_budget_confirmation(
		doc,
		actor,
		reason="Material funding-relevant change after Budget Officer sign-off",
		decision="Material change",
	)
	doc.reload()
	return {"ok": True, "demand": project_demand(doc)}


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

	from kentender_budget.api.dia_budget_control import release_reservation
	from kentender_budget.services.budget_check_reserve_contracts import reserve_funding

	reservations: list[str] = []
	created_now: list[str] = []
	linked_now: list[str] = []
	try:
		for row in allocs:
			if row.funding_reservation:
				reservations.append(row.funding_reservation)
				continue
			key = (
				idempotency_key
				or f"{doc.demand_code}:{row.budget_line}:{flt(row.allocation_amount):.2f}"
			)
			# Distinct keys per allocation when a shared key is supplied.
			if idempotency_key and len(allocs) > 1:
				key = f"{idempotency_key}:{row.name}"
			res = reserve_funding(
				budget_line=row.budget_line,
				demand_name=doc.demand_code,
				requested_amount=flt(row.allocation_amount),
				idempotency_key=key,
				actor=actor,
				procuring_entity=doc.procuring_entity,
			)
			rid = res["reservation_id"]
			reservations.append(rid)
			if not res.get("reused"):
				created_now.append(rid)
			frappe.db.set_value(
				"Demand Funding Allocation",
				row.name,
				{
					"funding_reservation": rid,
					"reservation_status": res.get("status") or "Reserved",
				},
			)
			linked_now.append(row.name)
	except Exception:
		# DIA-AC-014 / DIA-FR-093 — fail closed: no partial RSV, Demand unapproved.
		for rid in created_now:
			try:
				release_reservation(reservation_id=rid, actor=actor)
			except Exception:
				pass
		for row_name in linked_now:
			frappe.db.set_value(
				"Demand Funding Allocation",
				row_name,
				{"funding_reservation": "", "reservation_status": ""},
			)
		doc.reload()
		if doc.status != "Approved":
			_invalidate_bo_signoff_return_to_budget_confirmation(
				doc,
				actor,
				reason="Reservation failed; Budget Officer sign-off invalidated",
				decision="Reservation failed",
			)
		raise

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


def record_final_decision(
	*,
	demand: str,
	decision: str,
	reason: str | None = None,
	comment: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	"""DEM-UI-08 — PAA Return | Reject from Final Approval."""
	actor = _actor(user)
	action = (decision or "").strip()
	if action not in ("Return", "Reject"):
		throw_demand_error(ERR_VALIDATION, "decision must be Return or Reject")
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
	if not (reason or "").strip():
		throw_demand_error(ERR_VALIDATION, "reason is required")

	result = preview_transition(
		status=doc.status,
		stage=doc.current_stage,
		action=action,
		procuring_entity=doc.procuring_entity,
		owner_org_unit=doc.owner_org_unit,
		user=actor,
	)
	doc.status = result.status
	doc.current_stage = result.stage
	if action == "Reject":
		doc.rejected_at = _now()
	doc.save(ignore_permissions=True)

	if action == "Return":
		# Invalidate BO sign-off so Budget Confirmation must reconfirm (DIA-FR-093/087).
		for row_name in frappe.get_all(
			"Demand Funding Allocation",
			filters={"demand": doc.name, "bo_confirmation_status": "Confirmed"},
			pluck="name",
		):
			frappe.db.set_value(
				"Demand Funding Allocation",
				row_name,
				{
					"bo_confirmation_status": "Pending",
					"bo_confirmed_by": "",
					"bo_confirmed_at": None,
				},
			)

	_record_decision(
		doc,
		stage="Final Approval",
		decision=action,
		actor=actor,
		comment=comment,
		reason=reason,
	)
	doc.reload()
	return {"ok": True, "demand": project_demand(doc)}


def cancel_and_release_demand(
	*,
	demand: str,
	reason: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	"""DEM-SVC-011 — cancel; release unconsumed reservations via Budget shim.

	DIA-NFR-001 — idempotent: repeating cancel on an already-Cancelled Demand
	returns success without duplicate decisions or double release.
	"""
	actor = _actor(user)
	doc = get_demand(demand)
	assert_demand_scope(
		procuring_entity=doc.procuring_entity,
		owner_org_unit=doc.owner_org_unit,
		user=actor,
		require_write=True,
	)
	if doc.status == "Cancelled":
		# Idempotent success — release_reservation is itself safe on Released RSV.
		from kentender_budget.api.dia_budget_control import release_reservation

		for row in frappe.get_all(
			"Demand Funding Allocation",
			filters={"demand": doc.name},
			fields=["funding_reservation"],
		):
			if row.funding_reservation:
				release_reservation(reservation_id=row.funding_reservation, actor=actor)
		doc.reload()
		return {"ok": True, "demand": project_demand(doc), "idempotent": True}

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

	# DIA-AC-016 — planning consume reduces unconsumed reservation balance.
	if rsv and frappe.db.exists("Funding Reservation", rsv):
		rsv_doc = frappe.get_doc("Funding Reservation", rsv)
		prior_remaining = flt(rsv_doc.remaining_reserved)
		new_remaining = max(0.0, prior_remaining - amt)
		rsv_doc.remaining_reserved = new_remaining
		if new_remaining <= 0.009:
			rsv_doc.status = "Converted"
		else:
			rsv_doc.status = "Partially converted"
		rsv_doc.save(ignore_permissions=True)
		if prior_remaining > 0 and rsv_doc.budget_line:
			cur_reserved = flt(
				frappe.db.get_value("Budget Line", rsv_doc.budget_line, "amount_reserved")
			)
			released = min(amt, prior_remaining)
			frappe.db.set_value(
				"Budget Line",
				rsv_doc.budget_line,
				"amount_reserved",
				max(0.0, cur_reserved - released),
				update_modified=True,
			)

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


def _user_timezone(user: str) -> str:
	tz = (frappe.db.get_value("User", user, "time_zone") or "").strip()
	if tz:
		return tz
	try:
		from frappe.utils import get_system_timezone

		return get_system_timezone() or "UTC"
	except Exception:
		return "UTC"


def _project_datetime_for_user(value: Any, *, user: str) -> dict[str, str | None]:
	"""DIA-NFR-006 — store UTC-ish; display in user TZ with explicit label."""
	if not value:
		return {
			"utc": None,
			"display": None,
			"timezone": _user_timezone(user),
		}
	from frappe.utils import convert_utc_to_timezone, get_datetime

	tz = _user_timezone(user)
	raw = get_datetime(value)
	try:
		# Treat naive DB datetimes as UTC for conversion baseline.
		if getattr(raw, "tzinfo", None) is None:
			from datetime import timezone as dt_timezone

			raw = raw.replace(tzinfo=dt_timezone.utc)
		local = convert_utc_to_timezone(raw, tz)
		display = local.strftime("%Y-%m-%d %H:%M:%S") + f" {tz}"
	except Exception:
		display = f"{value} {tz}"
	return {"utc": str(value), "display": display, "timezone": tz}


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
	tz = _user_timezone(actor)
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
	projected = []
	for row in decisions:
		proj = _project_datetime_for_user(row.decided_at, user=actor)
		projected.append(
			{
				**row,
				"decided_at": proj["utc"],
				"decided_at_display": proj["display"],
				"timezone": proj["timezone"],
			}
		)
	approved_proj = _project_datetime_for_user(doc.get("approved_at"), user=actor)
	return {
		"ok": True,
		"demand_code": doc.demand_code,
		"timezone": tz,
		"approved_at": approved_proj["utc"],
		"approved_at_display": approved_proj["display"],
		"decisions": projected,
	}


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
			"requester",
			"current_owner",
			"required_by_date",
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


_PERF_FLOW_STAGES = (
	"Request Preparation",
	"Business Review",
	"Procurement Enrichment",
	"Budget Confirmation",
	"Final Approval",
	"Approved",
)


def _perf_money(amount: Any, currency: str | None = None) -> str:
	cur = (currency or "KES").strip() or "KES"
	try:
		n = float(amount or 0)
	except (TypeError, ValueError):
		n = 0.0
	return f"{cur} {n:,.2f}"


def _perf_age_days(modified: Any) -> int:
	if not modified:
		return 0
	try:
		from frappe.utils import date_diff, get_datetime

		return max(0, int(date_diff(now_datetime(), get_datetime(modified))))
	except Exception:
		return 0


def _perf_view_route(status: str, stage: str) -> str:
	st = (status or "").strip()
	sg = (stage or "").strip()
	if st == "Returned" and sg == "Request Preparation":
		return "demand-form"
	if st == "Draft":
		return "demand-form"
	if st == "Approved":
		return "demand-detail"
	if sg in (
		"Business Review",
		"Procurement Enrichment",
		"Budget Confirmation",
		"Final Approval",
	):
		return "demand-review"
	if st == "Returned":
		return "demand-form"
	return "demand-detail"


def get_demand_performance(
	*,
	user: str | None = None,
	as_at: str | None = None,
	procuring_entity: str | None = None,
	filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""DEM-SVC-015 / DEM-UI-10 — scoped performance projection (As at + Stitch sections)."""
	actor = _actor(user)
	require_operational_roles(
		ROLE_REQUESTER,
		ROLE_BUSINESS,
		ROLE_PAA,
		ROLE_BUDGET,
		ROLE_PLANNING,
		ROLE_VIEWER,
		user=actor,
	)
	filters = dict(filters or {})
	pe_filter = (procuring_entity or filters.get("procuring_entity") or "").strip()
	unit_filter = (filters.get("owner_org_unit") or "").strip()
	route_filter = (filters.get("demand_route") or "").strip()
	status_filter = (filters.get("status") or "").strip()
	stage_filter = (filters.get("current_stage") or "").strip()

	ws = list_demands_for_workspace(user=actor, filters={"limit": 500})
	names = [r.name for r in ws["rows"]]
	if not names:
		as_at_val = as_at or str(getdate())
		return {
			"ok": True,
			"as_at": as_at_val,
			"as_at_display": as_at_val,
			"basis": "Scoped Demand rows visible to the actor",
			"counts_by_status": {},
			"counts_by_stage": {},
			"approved_value": 0.0,
			"drill_down": [],
			"header": {
				"title": "Demand performance",
				"as_at_display": as_at_val,
				"basis": "Scoped Demand rows visible to the actor",
				"pe_label": "",
			},
			"summary": {
				"demands_count": 0,
				"approved_value": 0.0,
				"approved_value_display": _perf_money(0),
				"returned_count": 0,
				"awaiting_action_count": 0,
				"planning_taken_display": "0 of 0",
				"planning_taken_count": 0,
				"planning_ready_count": 0,
			},
			"flow_ageing": [],
			"funding_control": {
				"auto_matches": 0,
				"bo_confirmations": 0,
				"adjusted": 0,
				"exceptions": 0,
				"unfunded_amount": 0.0,
				"unfunded_amount_display": _perf_money(0),
				"exception_demand": None,
			},
			"planning_uptake": [],
			"strategy_coverage": [],
			"filter_options": {
				"procuring_entities": [],
				"owner_org_units": [],
				"routes": ["Standard", "Emergency", "Framework"],
				"statuses": ["Draft", "In Review", "Returned", "Approved", "Rejected", "Cancelled"],
				"stages": list(_PERF_FLOW_STAGES[:-1]),
			},
			"filters_applied": filters,
		}

	docs = frappe.get_all(
		"Demand",
		filters={"name": ["in", names]},
		fields=[
			"name",
			"demand_code",
			"title",
			"status",
			"current_stage",
			"procuring_entity",
			"owner_org_unit",
			"demand_route",
			"confirmed_estimate",
			"requester_estimate",
			"currency",
			"planning_usage",
			"planning_ready",
			"modified",
		],
		limit=500,
	)
	rows = list(docs)
	if pe_filter:
		rows = [r for r in rows if r.procuring_entity == pe_filter]
	if unit_filter:
		rows = [r for r in rows if r.owner_org_unit == unit_filter]
	if route_filter:
		rows = [r for r in rows if (r.demand_route or "") == route_filter]
	if status_filter:
		rows = [r for r in rows if r.status == status_filter]
	if stage_filter:
		rows = [r for r in rows if r.current_stage == stage_filter]

	by_status: dict[str, int] = {}
	by_stage: dict[str, int] = {}
	value_approved = 0.0
	returned_count = 0
	awaiting = 0
	planning_ready_n = 0
	planning_taken_n = 0
	for r in rows:
		by_status[r.status] = by_status.get(r.status, 0) + 1
		by_stage[r.current_stage] = by_stage.get(r.current_stage, 0) + 1
		if r.status == "Approved":
			value_approved += flt(r.confirmed_estimate or r.requester_estimate)
			if int(r.planning_ready or 0):
				planning_ready_n += 1
			if (r.planning_usage or "") in ("Partially planned", "Fully planned"):
				planning_taken_n += 1
		if r.status == "Returned":
			returned_count += 1
		if r.status in ("Draft", "In Review", "Returned") or (
			r.status == "Approved"
			and (r.planning_usage or "Not taken up") in ("", "Not taken up")
		):
			awaiting += 1

	as_at_val = as_at or str(getdate())
	basis = "Scoped Demand rows visible to the actor"
	pe_label = ""
	if pe_filter and frappe.db.exists("Procuring Entity", pe_filter):
		pe_label = (
			frappe.db.get_value("Procuring Entity", pe_filter, "entity_name") or pe_filter
		)

	# Flow / ageing
	flow_ageing: list[dict[str, Any]] = []
	for stage_label in _PERF_FLOW_STAGES:
		if stage_label == "Approved":
			bucket = [r for r in rows if r.status == "Approved"]
		else:
			bucket = [
				r
				for r in rows
				if r.current_stage == stage_label and r.status != "Approved"
			]
		oldest = 0
		view_demand = None
		attention = "—"
		if bucket:
			ages = [( _perf_age_days(r.modified), r) for r in bucket]
			ages.sort(key=lambda x: -x[0])
			oldest = ages[0][0]
			pick = ages[0][1]
			view_demand = {
				"demand": pick.name,
				"demand_code": pick.demand_code,
				"route": _perf_view_route(pick.status, pick.current_stage),
			}
			if stage_label == "Approved":
				attention = "Baseline locked"
			elif oldest >= 5:
				attention = f"{oldest} days waiting"
			elif pick.status == "Returned":
				attention = "Returned — action needed"
			else:
				attention = "In queue"
		flow_ageing.append(
			{
				"stage": stage_label,
				"stage_display": stage_label,
				"count": len(bucket),
				"oldest_waiting_days": oldest,
				"attention": attention,
				"view_demand": view_demand,
			}
		)

	# Funding control
	demand_names = [r.name for r in rows]
	auto_matches = 0
	bo_confirmations = 0
	adjusted = 0
	if demand_names:
		allocs = frappe.get_all(
			"Demand Funding Allocation",
			filters={"demand": ["in", demand_names]},
			fields=["demand", "bo_confirmation_status", "matching_source", "allocation_amount"],
			limit=2000,
		)
		auto_matches = sum(1 for a in allocs if (a.matching_source or "") == "Automatic")
		if not auto_matches:
			auto_matches = len(allocs)
		bo_confirmations = sum(
			1 for a in allocs if (a.bo_confirmation_status or "") == "Confirmed"
		)
		adjusted = sum(1 for a in allocs if (a.bo_confirmation_status or "") == "Adjusted")
	exceptions = 0
	unfunded = 0.0
	exception_demand = None
	if demand_names:
		excs = frappe.get_all(
			"Funding Exception",
			filters={"demand": ["in", demand_names], "status": "Open"},
			fields=["name", "demand", "exception_type"],
			order_by="modified desc",
			limit=50,
		)
		exceptions = len(excs)
		for e in excs:
			drow = next((r for r in rows if r.name == e.demand), None)
			if drow:
				unfunded += flt(drow.confirmed_estimate or drow.requester_estimate)
				if exception_demand is None:
					exception_demand = {
						"demand": drow.name,
						"demand_code": drow.demand_code,
						"route": "demand-review",
						"exception": e.name,
					}

	# Planning uptake (Approved + planning ready / consumed)
	planning_uptake: list[dict[str, Any]] = []
	approved_rows = [r for r in rows if r.status == "Approved"]
	consumptions: dict[str, list[str]] = {}
	if approved_rows:
		cons = frappe.get_all(
			"Planning Consumption",
			filters={"demand": ["in", [r.name for r in approved_rows]]},
			fields=["demand", "plan_item_code", "consumed_amount"],
			limit=200,
		)
		for c in cons:
			consumptions.setdefault(c.demand, []).append(c.plan_item_code or "—")
	for r in approved_rows:
		usage = (r.planning_usage or "Not taken up").strip() or "Not taken up"
		if not int(r.planning_ready or 0) and usage == "Not taken up":
			continue
		codes = consumptions.get(r.name) or []
		amt = flt(r.confirmed_estimate or r.requester_estimate)
		planning_uptake.append(
			{
				"demand": r.name,
				"demand_code": r.demand_code,
				"title": r.title,
				"approved_value": amt,
				"approved_value_display": _perf_money(amt, r.currency),
				"planning_usage": usage,
				"plan_item_codes": codes,
				"plan_item_codes_display": ", ".join(codes) if codes else "—",
				"route": "demand-detail",
			}
		)

	# Strategy coverage — Approved value by primary Demand Strategy Context path
	strat_map: dict[str, dict[str, Any]] = {}
	ctx_by_demand: dict[str, str] = {}
	if approved_rows:
		ctx_rows = frappe.get_all(
			"Demand Strategy Reference",
			filters={"demand": ["in", [r.name for r in approved_rows]]},
			fields=["demand", "hierarchy_path", "snapshot_label", "reference_type"],
			order_by="creation asc",
			limit=500,
		)
		for c in ctx_rows:
			is_primary = (c.reference_type or "") == "Primary"
			if c.demand in ctx_by_demand and not is_primary:
				continue
			if is_primary or c.demand not in ctx_by_demand:
				label = (c.hierarchy_path or c.snapshot_label or "").strip()
				ctx_by_demand[c.demand] = label or "Unlinked"
	for r in approved_rows:
		path = (ctx_by_demand.get(r.name) or "").strip()
		label = path.split(">")[0].strip() if path else "Unlinked"
		if not label:
			label = "Unlinked"
		bucket = strat_map.setdefault(
			label,
			{
				"strategy_label": label,
				"approved_value": 0.0,
				"demands_count": 0,
				"required_commitments": 0,
				"addressed_count": 0,
				"currency": r.currency or "KES",
			},
		)
		bucket["approved_value"] += flt(r.confirmed_estimate or r.requester_estimate)
		bucket["demands_count"] += 1
		bucket["required_commitments"] += 1
		if (r.planning_usage or "") in ("Partially planned", "Fully planned"):
			bucket["addressed_count"] += 1
	strategy_coverage = [
		{
			"strategy_label": v["strategy_label"],
			"approved_value": v["approved_value"],
			"approved_value_display": _perf_money(v["approved_value"], v.get("currency")),
			"required_commitments": v["required_commitments"],
			"addressed_count": v["addressed_count"],
			"attention": "No action" if v["addressed_count"] >= v["required_commitments"] else "Uptake pending",
			"pvc_note": "Primary strategy path on Approved Demands (not realised benefits)",
		}
		for v in sorted(strat_map.values(), key=lambda x: -x["approved_value"])
	]

	# Filter options from scoped universe (pre-filter names)
	all_docs = docs
	pe_opts: list[dict[str, str]] = []
	seen_pe: set[str] = set()
	unit_opts: list[dict[str, str]] = []
	seen_u: set[str] = set()
	for r in all_docs:
		if r.procuring_entity and r.procuring_entity not in seen_pe:
			seen_pe.add(r.procuring_entity)
			pe_opts.append(
				{
					"id": r.procuring_entity,
					"code": r.procuring_entity,
					"name": frappe.db.get_value("Procuring Entity", r.procuring_entity, "entity_name")
					or r.procuring_entity,
				}
			)
		if r.owner_org_unit and r.owner_org_unit not in seen_u:
			seen_u.add(r.owner_org_unit)
			unit_opts.append(
				{
					"id": r.owner_org_unit,
					"code": r.owner_org_unit,
					"name": frappe.db.get_value("Organisation Unit", r.owner_org_unit, "unit_name")
					or r.owner_org_unit,
				}
			)

	return {
		"ok": True,
		"as_at": as_at_val,
		"as_at_display": as_at_val,
		"basis": basis,
		"counts_by_status": by_status,
		"counts_by_stage": by_stage,
		"approved_value": value_approved,
		"drill_down": [r.demand_code for r in rows[:50]],
		"header": {
			"title": "Demand performance",
			"as_at_display": as_at_val,
			"basis": basis,
			"pe_label": pe_label or "",
		},
		"summary": {
			"demands_count": len(rows),
			"approved_value": value_approved,
			"approved_value_display": _perf_money(value_approved),
			"returned_count": returned_count,
			"awaiting_action_count": awaiting,
			"planning_taken_display": f"{planning_taken_n} of {planning_ready_n or len(approved_rows)}",
			"planning_taken_count": planning_taken_n,
			"planning_ready_count": planning_ready_n or len(approved_rows),
		},
		"flow_ageing": flow_ageing,
		"funding_control": {
			"auto_matches": auto_matches,
			"bo_confirmations": bo_confirmations,
			"adjusted": adjusted,
			"exceptions": exceptions,
			"unfunded_amount": unfunded,
			"unfunded_amount_display": _perf_money(unfunded),
			"exception_demand": exception_demand,
		},
		"planning_uptake": planning_uptake,
		"strategy_coverage": strategy_coverage,
		"filter_options": {
			"procuring_entities": pe_opts,
			"owner_org_units": unit_opts,
			"routes": ["Standard", "Emergency", "Framework"],
			"statuses": ["Draft", "In Review", "Returned", "Approved", "Rejected", "Cancelled"],
			"stages": list(_PERF_FLOW_STAGES[:-1]),
		},
		"filters_applied": {
			"procuring_entity": pe_filter,
			"owner_org_unit": unit_filter,
			"demand_route": route_filter,
			"status": status_filter,
			"current_stage": stage_filter,
		},
	}
