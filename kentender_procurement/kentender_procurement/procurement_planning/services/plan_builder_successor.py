"""Successor-Draft projection for the ordinary PLN-UI-05 builder."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt, now_datetime

from kentender_procurement.procurement_planning.mvp1_constants import ITEM_ACTIVE, ITEM_PROPOSED, VALIDATION_READY, VERSION_EDITABLE_STATUSES
from kentender_procurement.procurement_planning.services._invariants import assert_version_concurrency, new_concurrency_token
from kentender_procurement.procurement_planning.services.plan_item_finance import effective_finance_status_from_values
from kentender_procurement.procurement_planning.services.planning_permissions import assert_can_add_demand, assert_planning_scope, is_planning_read_only
from kentender_procurement.procurement_planning.services.validate_plan import effective_validation_status_from_rows

SYSTEM_REASONS = {"Initial draft", "Opened to add approved Demand", "Opened to add approved Demands", "Post-approval revision"}


def planner_update_reason(value: str | None) -> str:
	value = cstr(value).strip()
	return "" if value in SYSTEM_REASONS else value


def _money(value: float, currency: str) -> str:
	return f"{currency} {flt(value):,.0f}"


def _ou_labels(items: list[Any]) -> dict[str, str]:
	ids = sorted({cstr(row.owner_org_unit) for row in items if row.owner_org_unit})
	return dict(frappe.get_all("Organisation Unit", filters={"name": ["in", ids]}, fields=["name", "unit_name"], as_list=True)) if ids else {}


def _live_budget_lines(item_names: list[str]) -> dict[str, str]:
	if not item_names:
		return {}
	allocations = frappe.get_all(
		"Plan Demand Allocation",
		filters={"plan_item": ["in", item_names], "status": ["in", ["Draft", "Effective"]]},
		fields=["plan_item", "demand"], order_by="creation asc", limit_page_length=2000,
	)
	demands = list(dict.fromkeys(cstr(row.demand) for row in allocations if row.demand))
	funding = {cstr(row.demand): cstr(row.budget_line) for row in frappe.get_all(
		"Demand Funding Allocation", filters={"demand": ["in", demands]}, fields=["demand", "budget_line"], order_by="creation asc",
	)} if demands else {}
	result: dict[str, str] = {}
	for row in allocations:
		result.setdefault(cstr(row.plan_item), funding.get(cstr(row.demand), ""))
	return result


def _handoffs(item_names: list[str]) -> dict[str, str]:
	if not item_names or not frappe.db.exists("DocType", "Planning Handoff Snapshot"):
		return {}
	return {cstr(row.plan_item): cstr(row.tender_reference) for row in frappe.get_all(
		"Planning Handoff Snapshot", filters={"plan_item": ["in", item_names]}, fields=["plan_item", "tender_reference"],
	)}


def _unchanged_copy(rows: list[dict[str, Any]], approved_label: str) -> str:
	count = len(rows)
	if not count:
		return ""
	copy = f"{count} unchanged Active Plan Item{'s' if count != 1 else ''} remain{'s' if count == 1 else ''} operational in {approved_label}"
	tenders = [cstr(row.get("tender_reference")) for row in rows if row.get("tender_reference")]
	if tenders:
		copy += " · " + ", ".join(f"Tender {name}" for name in tenders) + (" remains" if len(tenders) == 1 else " remain") + " active"
	return copy


def get_successor_builder(*, plan_doc: Any, actor: str, organisation_unit: str | None = None, status: str | None = None, search: str | None = None) -> dict[str, Any]:
	approved = cstr(plan_doc.current_approved_version).strip()
	draft = cstr(plan_doc.open_draft_version).strip()
	av = frappe.db.get_value("Procurement Plan Version", approved, ["name", "version_number", "status"], as_dict=True)
	dv = frappe.db.get_value(
		"Procurement Plan Version", draft,
		["name", "version_number", "status", "version_reason", "validation_projection", "concurrency_token", "creation", "modified"], as_dict=True,
	)
	read_only = is_planning_read_only(actor)
	editable = cstr(dv.status) in VERSION_EDITABLE_STATUSES
	items = frappe.get_all(
		"Procurement Plan Item", filters={"plan": plan_doc.name, "baseline_state": ["in", [ITEM_ACTIVE, ITEM_PROPOSED]]},
		fields=["name", "plan_item_code", "baseline_state", "owner_org_unit", "tender_takeup_projection"], order_by="creation asc", limit_page_length=500,
	)
	item_names = [cstr(row.name) for row in items]
	fingerprint_fields = [
		"procurement_method", "arrangement", "lotting_decision", "lot_basis",
		"expected_lot_count", "proposed_removal", "ms_invitation_published",
		"ms_tender_opening", "ms_evaluation_completed", "ms_award_approval",
		"ms_notification_of_award", "ms_contract_signature", "ms_delivery_completion",
	]
	item_versions = frappe.get_all(
		"Procurement Plan Item Version", filters={"plan_version": draft, "plan_item": ["in", item_names]},
		fields=["name", "plan_item", "requirement_title", "confirmed_estimate", "currency", "validation_projection", "finance_status", "finance_snapshot_amount", "finance_snapshot_budget_line", "draft_change_label", "carry_forward_unchanged", *fingerprint_fields],
		limit_page_length=500,
	) if item_names else []
	iv_by_item = {cstr(row.plan_item): row for row in item_versions}
	approved_total = sum(flt(row.confirmed_estimate) for row in frappe.get_all(
		"Procurement Plan Item Version", filters={"plan_version": approved, "proposed_removal": 0}, fields=["confirmed_estimate"], limit_page_length=500,
	))
	ou_labels = _ou_labels(items)
	live_lines = _live_budget_lines(item_names)
	handoffs = _handoffs(item_names)
	changed: list[dict[str, Any]] = []
	unchanged: list[dict[str, Any]] = []
	draft_total = 0.0
	planning_complete = 0
	finance_confirmed = 0
	included_count = 0
	for item in items:
		iv = iv_by_item.get(cstr(item.name))
		if not iv:
			continue
		removed = bool(int(iv.proposed_removal or 0))
		if not removed:
			draft_total += flt(iv.confirmed_estimate)
			included_count += 1
		finance = effective_finance_status_from_values(
			status=iv.finance_status, snapshot_amount=iv.finance_snapshot_amount,
			snapshot_budget_line=iv.finance_snapshot_budget_line, live_amount=iv.confirmed_estimate,
			live_budget_line=live_lines.get(cstr(item.name), ""),
		)
		item_validation = cstr(iv.validation_projection or "Not run")
		planning = "Complete" if item_validation == VALIDATION_READY else "Needs attention"
		if not removed and planning == "Complete":
			planning_complete += 1
		if not removed and finance == "Confirmed":
			finance_confirmed += 1
		if finance == "Returned":
			action, action_label = "correct_item", "Correct item"
		elif planning != "Complete":
			action, action_label = "complete_item", "Complete item"
		else:
			action, action_label = "view_item", "View Plan Item"
		change = "Proposed removal" if removed else cstr(iv.draft_change_label) or ("Unchanged" if int(iv.carry_forward_unchanged or 0) else "Changed")
		downstream = bool(handoffs.get(cstr(item.name)) or (cstr(item.tender_takeup_projection).strip() and cstr(item.tender_takeup_projection).strip() != "Not taken up"))
		can_remove = bool(editable and not read_only and not downstream and not (cstr(item.baseline_state) == ITEM_ACTIVE and removed))
		row_validation = "Ready" if item_validation == VALIDATION_READY and finance == "Confirmed" else "Needs attention" if item_validation == VALIDATION_READY else item_validation
		row = {
			"plan_item": item.name, "plan_item_code": item.plan_item_code, "title": cstr(iv.requirement_title),
			"owner_org_unit": cstr(item.owner_org_unit), "owner_org_unit_label": cstr(ou_labels.get(cstr(item.owner_org_unit)) or "Procuring Entity level"),
			"planned_value": flt(iv.confirmed_estimate), "planned_value_display": _money(iv.confirmed_estimate, cstr(iv.currency or plan_doc.currency)),
			"planning_status": planning, "planning_status_label": planning, "finance_status": finance, "finance_status_label": finance,
			"validation_status": row_validation, "validation_status_label": row_validation,
			"action": action, "action_label": action_label, "route": f"/app/procurement-plan-item-editor?plan_item={item.name}",
			"change_label": change, "tender_reference": handoffs.get(cstr(item.name), ""), "can_remove": can_remove,
			"can_remove_from_draft": bool(can_remove and cstr(item.baseline_state) == ITEM_PROPOSED),
			"can_propose_removal": bool(can_remove and cstr(item.baseline_state) == ITEM_ACTIVE),
		}
		(unchanged if change == "Unchanged" else changed).append(row)

	all_changed = list(changed)
	ou_filter = cstr(organisation_unit).strip()
	status_filter = cstr(status).strip().lower().replace(" ", "_")
	query = cstr(search).strip().lower()
	if ou_filter and ou_filter not in ("all", "__all__"):
		changed = [row for row in changed if row["owner_org_unit"] == ou_filter]
	if status_filter and status_filter not in ("all", "__all__"):
		changed = [row for row in changed if cstr(row["planning_status"]).lower().replace(" ", "_") == status_filter]
	if query:
		changed = [row for row in changed if query in f"{row['plan_item_code']} {row['title']} {row['owner_org_unit_label']}".lower()]

	fingerprint_rows = []
	for row in item_versions:
		if int(row.proposed_removal or 0):
			continue
		fingerprint_rows.append({
			"item": row.plan_item,
			"estimate": f"{flt(row.confirmed_estimate):.2f}",
			"method": cstr(row.procurement_method or ""),
			"arrangement": cstr(row.arrangement or ""),
			"lotting": cstr(row.lotting_decision or ""),
			"lot_basis": cstr(row.lot_basis or ""),
			"lot_count": cstr(row.expected_lot_count or ""),
			**{field: cstr(row.get(field) or "") for field in fingerprint_fields if field.startswith("ms_")},
		})
	validation = effective_validation_status_from_rows(
		version=draft, stored=cstr(dv.validation_projection), rows=fingerprint_rows,
	)
	reason = planner_update_reason(dv.version_reason)
	has_changes = any(row["change_label"] != "Unchanged" for row in all_changed)
	all_complete = bool(included_count) and planning_complete == included_count
	all_finance = bool(included_count) and finance_confirmed == included_count
	can_submit = bool(editable and not read_only and reason and has_changes and all_complete and all_finance and validation == VALIDATION_READY)
	display_validation = "Needs attention" if validation == VALIDATION_READY and not all_finance else validation
	issues: list[str] = []
	if not has_changes:
		issues.append("No effective changes remain. Cancel this update or add an approved Demand.")
	elif not reason:
		issues.append("Enter the reason for this Plan update before submitting it for review.")
	elif not all_complete:
		incomplete_count = included_count - planning_complete
		item_label = "Plan Item" if incomplete_count == 1 else "Plan Items"
		pronoun = "it" if incomplete_count == 1 else "them"
		verb = "needs" if incomplete_count == 1 else "need"
		issues.append(
			f"{incomplete_count} {item_label} {verb} planning details. "
			f"Complete {pronoun} before requesting Finance confirmation or submitting this Plan for review."
		)
	elif not all_finance:
		missing = next((row["plan_item_code"] for row in all_changed if row["change_label"] != "Proposed removal" and row["finance_status"] != "Confirmed"), "")
		issues.append(f"Funding confirmation is still required for {missing} before this Plan can be submitted for review." if missing else "Funding confirmation is still required before this Plan can be submitted for review.")
	elif validation != VALIDATION_READY:
		issues.append("Resolve validation issues until the update is Ready before submitting for review.")
	ready_message = "All required Planning validation and Finance confirmations are ready." if can_submit else ""
	delta = draft_total - approved_total
	approved_label = f"Approved Version {int(av.version_number)}"
	return {
		"ok": True, "redirect": False, "state_id": "PLN-UI-05", "builder_kind": "successor", "readiness_state": "ready" if can_submit else "needs_attention",
		"plan": plan_doc.name, "plan_code": plan_doc.plan_code, "title": plan_doc.title,
		"procuring_entity": plan_doc.procuring_entity, "procuring_entity_label": frappe.db.get_value("Procuring Entity", plan_doc.procuring_entity, "legal_name") or plan_doc.procuring_entity,
		"financial_year": plan_doc.financial_year, "period_start": str(plan_doc.period_start), "period_end": str(plan_doc.period_end), "currency": plan_doc.currency,
		"version": dv.name, "version_status": dv.status, "version_number_label": f"Draft Version {int(dv.version_number)}", "draft_created_at": str(dv.creation), "as_at": str(dv.modified), "concurrency_token": cstr(dv.concurrency_token),
		"approved_version": av.name, "approved_version_label": approved_label, "approved_total": approved_total, "approved_total_display": _money(approved_total, plan_doc.currency),
		"planned_total": draft_total, "planned_total_display": _money(draft_total, plan_doc.currency), "change_amount": delta, "change_display": f"{_money(abs(delta), plan_doc.currency)} {'added' if delta >= 0 else 'removed'}",
		"item_count": included_count, "changed_count": len(all_changed), "planning_complete_count": planning_complete, "planning_complete_display": f"{planning_complete} of {included_count}",
		"finance_confirmed_count": finance_confirmed, "finance_confirmed_total": included_count, "finance_confirmed_display": f"{finance_confirmed} of {included_count}",
		"validation_projection": display_validation, "outstanding_count": sum(1 for row in all_changed if row["planning_status"] != "Complete"),
		"items": changed, "unchanged_items": unchanged, "unchanged_count": len(unchanged), "unchanged_operational_copy": _unchanged_copy(unchanged, approved_label), "unfiltered_item_count": len(all_changed),
		"eligible_demand_count": 0, "update_reason": reason, "issue_message": issues[0] if issues else "", "readiness_message": ready_message, "issues": issues,
		"no_changes_remain": not has_changes, "can_cancel": bool(editable and not read_only and not has_changes), "can_save": bool(editable and not read_only), "can_submit": can_submit, "can_add_demand": bool(editable and not read_only), "read_only": read_only,
		"organisation_unit_options": [{"id": key, "label": label} for key, label in sorted({(row["owner_org_unit"], row["owner_org_unit_label"]) for row in all_changed})],
		"status_options": [{"id": key.lower().replace(" ", "_"), "label": key} for key in sorted({row["planning_status"] for row in all_changed})],
		"workspace_route": f"/app/planning-workspace?procuring_entity={plan_doc.procuring_entity}&financial_year={plan_doc.financial_year}",
		"approved_route": f"/app/procurement-plan-approved?plan={plan_doc.name}",
	}


def _save_marker(version: str, key: str) -> tuple[str, str] | None:
	prefix = f"PLN_SAVE_DRAFT|{key}|"
	content = frappe.db.get_value("Comment", {"reference_doctype": "Procurement Plan Version", "reference_name": version, "content": ["like", f"{prefix}%"]}, "content")
	if not content:
		return None
	parts = cstr(content).split("|", 3)
	return (parts[2] if len(parts) > 2 else "", parts[3] if len(parts) > 3 else "")


def save_plan_draft(*, plan: str, expected_version_token: str | None, update_reason: str | None, idempotency_key: str | None, user: str | None = None) -> dict[str, Any]:
	actor = assert_can_add_demand(user)
	plan_doc = frappe.get_doc("Procurement Plan", cstr(plan).strip())
	assert_planning_scope(procuring_entity=plan_doc.procuring_entity, org_unit=None, user=actor, require_write=True)
	draft = cstr(plan_doc.open_draft_version).strip()
	if not draft:
		return {"ok": False, "errors": {"form": "There is no Draft to save."}}
	key = cstr(idempotency_key).strip()
	if not key:
		return {"ok": False, "errors": {"form": "An idempotency key is required."}}
	replay = _save_marker(draft, key)
	if replay:
		return {"ok": True, "idempotent": True, "plan": plan_doc.name, "version": draft, "concurrency_token": replay[0], "update_reason": replay[1], "idempotency_key": key}
	reason = planner_update_reason(update_reason)
	if plan_doc.current_approved_version and not reason:
		return {"ok": False, "errors": {"update_reason": "Enter the reason for this Plan update."}}
	frappe.db.sql("select name from `tabProcurement Plan Version` where name=%s for update", draft)
	assert_version_concurrency(draft, expected_version_token)
	version = frappe.get_doc("Procurement Plan Version", draft)
	if cstr(version.status) not in VERSION_EDITABLE_STATUSES:
		return {"ok": False, "errors": {"form": "Only a Draft or Returned Plan can be saved."}}
	token = new_concurrency_token()
	frappe.db.set_value("Procurement Plan Version", draft, {"version_reason": reason or version.version_reason, "concurrency_token": token}, update_modified=True)
	frappe.get_doc({
		"doctype": "Comment", "comment_type": "Info", "reference_doctype": "Procurement Plan Version", "reference_name": draft,
		"content": f"PLN_SAVE_DRAFT|{key}|{token}|{reason}", "comment_email": actor,
		"comment_by": frappe.db.get_value("User", actor, "full_name") or actor, "creation": now_datetime(),
	}).insert(ignore_permissions=True)
	return {"ok": True, "idempotent": False, "plan": plan_doc.name, "version": draft, "update_reason": reason, "concurrency_token": token, "idempotency_key": key}
