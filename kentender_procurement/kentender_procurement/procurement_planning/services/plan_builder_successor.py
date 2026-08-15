"""Successor-Draft projection used by the ordinary PLN-UI-05 builder."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt

from kentender_procurement.procurement_planning.mvp1_constants import ITEM_ACTIVE, ITEM_PROPOSED, VALIDATION_READY, VERSION_EDITABLE_STATUSES
from kentender_procurement.procurement_planning.services._invariants import assert_version_concurrency, new_concurrency_token
from kentender_procurement.procurement_planning.services.plan_item_finance import effective_finance_status, plan_finance_summary
from kentender_procurement.procurement_planning.services.planning_permissions import assert_can_add_demand, assert_planning_scope, is_planning_read_only
from kentender_procurement.procurement_planning.services.remove_plan_item import draft_has_effective_changes, item_has_downstream, removal_capabilities_for_item
from kentender_procurement.procurement_planning.services.validate_plan import effective_validation_status

SYSTEM_REASONS = {"Initial draft", "Opened to add approved Demand", "Opened to add approved Demands", "Post-approval revision"}


def planner_update_reason(value: str | None) -> str:
	value = cstr(value).strip()
	return "" if value in SYSTEM_REASONS else value


def _money(value: float, currency: str) -> str:
	return f"{currency} {flt(value):,.2f}"


def _ou(ou: str | None) -> str:
	return cstr(frappe.db.get_value("Organisation Unit", ou, "unit_name") or ou or "Procuring Entity level")


def get_successor_builder(*, plan_doc: Any, actor: str, organisation_unit: str | None = None, status: str | None = None, search: str | None = None) -> dict[str, Any]:
	approved = cstr(plan_doc.current_approved_version).strip()
	draft = cstr(plan_doc.open_draft_version).strip()
	av = frappe.get_doc("Procurement Plan Version", approved)
	dv = frappe.get_doc("Procurement Plan Version", draft)
	read_only = is_planning_read_only(actor)
	editable = cstr(dv.status) in VERSION_EDITABLE_STATUSES
	approved_total = 0.0
	for row in frappe.get_all("Procurement Plan Item Version", filters={"plan_version": approved}, fields=["confirmed_estimate", "proposed_removal"]):
		if not int(row.proposed_removal or 0):
			approved_total += flt(row.confirmed_estimate)

	items = frappe.get_all("Procurement Plan Item", filters={"plan": plan_doc.name, "baseline_state": ["in", [ITEM_ACTIVE, ITEM_PROPOSED]]}, fields=["name", "plan_item_code", "baseline_state", "owner_org_unit"], order_by="creation asc")
	changed: list[dict[str, Any]] = []
	unchanged: list[dict[str, Any]] = []
	draft_total = 0.0
	for item in items:
		iv_name = frappe.db.get_value("Procurement Plan Item Version", {"plan_item": item.name, "plan_version": draft}, "name")
		if not iv_name:
			continue
		iv = frappe.get_doc("Procurement Plan Item Version", iv_name)
		amount = flt(iv.confirmed_estimate)
		if not int(iv.proposed_removal or 0):
			draft_total += amount
		finance = effective_finance_status(iv)
		validation = cstr(iv.validation_projection or "Not run")
		planning = "Complete" if validation == VALIDATION_READY else "Needs attention"
		if finance == "Returned":
			planning, action, action_label = "Finance returned", "correct_item", "Correct item"
		elif validation != VALIDATION_READY:
			action, action_label = "complete_item", "Complete item"
		else:
			action, action_label = "view_item", "View item"
		caps = removal_capabilities_for_item(plan_item=item.name, baseline_state=item.baseline_state, draft_version=draft, read_only=read_only)
		downstream = item_has_downstream(item.name)
		change = "Proposed removal" if int(iv.proposed_removal or 0) else (cstr(iv.draft_change_label) or ("Unchanged" if int(iv.carry_forward_unchanged or 0) else "Changed"))
		row = {
			"plan_item": item.name, "plan_item_code": item.plan_item_code, "title": cstr(iv.requirement_title),
			"owner_org_unit": cstr(item.owner_org_unit), "owner_org_unit_label": _ou(item.owner_org_unit),
			"planned_value": amount, "planned_value_display": _money(amount, plan_doc.currency),
			"planning_status": planning, "planning_status_label": planning,
			"finance_status": finance, "finance_status_label": finance,
			"validation_status": validation, "validation_status_label": validation,
			"action": action, "action_label": action_label,
			"route": f"/app/procurement-plan-item-editor?plan_item={item.name}", "change_label": change,
			"can_remove": bool((caps.get("can_remove_from_draft") or caps.get("can_propose_removal")) and not downstream),
			"can_remove_from_draft": bool(caps.get("can_remove_from_draft") and not downstream),
			"can_propose_removal": bool(caps.get("can_propose_removal") and not downstream),
		}
		(unchanged if change == "Unchanged" else changed).append(row)

	all_changed = list(changed)
	ou_filter = cstr(organisation_unit).strip()
	status_filter = cstr(status).strip().lower().replace(" ", "_")
	query = cstr(search).strip().lower()
	if ou_filter and ou_filter not in ("all", "__all__"):
		changed = [r for r in changed if r["owner_org_unit"] == ou_filter]
	if status_filter and status_filter not in ("all", "__all__"):
		changed = [r for r in changed if cstr(r["planning_status"]).lower().replace(" ", "_") == status_filter]
	if query:
		changed = [r for r in changed if query in f"{r['plan_item_code']} {r['title']} {r['owner_org_unit_label']}".lower()]

	finance = plan_finance_summary(plan=plan_doc.name, version=draft)
	validation = effective_validation_status(plan=plan_doc.name, version=draft, stored=cstr(dv.validation_projection))
	reason = planner_update_reason(dv.version_reason)
	has_changes = draft_has_effective_changes(plan=plan_doc.name, version=draft)
	all_complete = bool(all_changed) and all(r["planning_status"] == "Complete" for r in all_changed)
	can_submit = bool(editable and not read_only and reason and has_changes and all_complete and finance["all_confirmed"] and validation == VALIDATION_READY)
	issues = []
	if not finance["all_confirmed"]:
		missing = finance.get("unconfirmed_codes") or []
		issues.append(f"Funding confirmation is still required for {missing[0]} before this Plan can be submitted for review." if missing else "Funding confirmation is still required before this Plan can be submitted for review.")
	elif validation != VALIDATION_READY:
		issues.append("Resolve validation issues until the update is Ready before submitting for review.")
	delta = draft_total - approved_total
	return {
		"ok": True, "redirect": False, "state_id": "PLN-UI-05", "builder_kind": "successor",
		"plan": plan_doc.name, "plan_code": plan_doc.plan_code, "title": plan_doc.title,
		"procuring_entity": plan_doc.procuring_entity, "procuring_entity_label": frappe.db.get_value("Procuring Entity", plan_doc.procuring_entity, "legal_name") or plan_doc.procuring_entity,
		"financial_year": plan_doc.financial_year, "period_start": str(plan_doc.period_start), "period_end": str(plan_doc.period_end), "currency": plan_doc.currency,
		"version": dv.name, "version_status": dv.status, "version_number_label": f"Draft Version {int(dv.version_number)}", "concurrency_token": cstr(dv.concurrency_token),
		"approved_version": av.name, "approved_version_label": f"Approved Version {int(av.version_number)}",
		"approved_total": approved_total, "approved_total_display": _money(approved_total, plan_doc.currency),
		"planned_total": draft_total, "planned_total_display": _money(draft_total, plan_doc.currency),
		"change_amount": delta, "change_display": ("+" if delta >= 0 else "−") + _money(abs(delta), plan_doc.currency),
		"item_count": len([r for r in items if r.baseline_state != "Removed"]), "changed_count": len(all_changed),
		"planning_complete_count": sum(1 for r in all_changed if r["planning_status"] == "Complete"), "planning_complete_display": f"{sum(1 for r in all_changed if r['planning_status'] == 'Complete')} of {len(all_changed)}",
		"finance_confirmed_count": finance["finance_confirmed_count"], "finance_confirmed_total": finance["finance_item_count"], "finance_confirmed_display": finance["finance_confirmed_label"],
		"validation_projection": validation, "outstanding_count": sum(1 for r in all_changed if r["planning_status"] != "Complete"),
		"items": changed, "unchanged_items": unchanged, "unfiltered_item_count": len(all_changed),
		"update_reason": reason, "issue_message": issues[0] if issues else "", "issues": issues,
		"no_changes_remain": not has_changes,
		"can_cancel": bool(editable and not read_only and not has_changes),
		"can_save": bool(editable and not read_only), "can_submit": can_submit, "can_add_demand": bool(editable and not read_only), "read_only": read_only,
		"organisation_unit_options": [{"id": k, "label": v} for k, v in sorted({(r["owner_org_unit"], r["owner_org_unit_label"]) for r in all_changed})],
		"status_options": [{"id": k.lower().replace(" ", "_"), "label": k} for k in sorted({r["planning_status"] for r in all_changed})],
		"workspace_route": f"/app/planning-workspace?procuring_entity={plan_doc.procuring_entity}&financial_year={plan_doc.financial_year}",
		"approved_route": f"/app/procurement-plan-approved?plan={plan_doc.name}",
	}


def save_plan_draft(*, plan: str, expected_version_token: str | None, update_reason: str | None, idempotency_key: str | None, user: str | None = None) -> dict[str, Any]:
	actor = assert_can_add_demand(user)
	plan_doc = frappe.get_doc("Procurement Plan", cstr(plan).strip())
	assert_planning_scope(procuring_entity=plan_doc.procuring_entity, org_unit=None, user=actor, require_write=True)
	draft = cstr(plan_doc.open_draft_version).strip()
	if not draft:
		return {"ok": False, "errors": {"form": "There is no Draft to save."}}
	reason = planner_update_reason(update_reason)
	if plan_doc.current_approved_version and not reason:
		return {"ok": False, "errors": {"update_reason": "Enter the reason for this Plan update."}}
	assert_version_concurrency(draft, expected_version_token)
	version = frappe.get_doc("Procurement Plan Version", draft)
	if cstr(version.status) not in VERSION_EDITABLE_STATUSES:
		return {"ok": False, "errors": {"form": "Only a Draft or Returned Plan can be saved."}}
	key = cstr(idempotency_key).strip()
	if not key:
		return {"ok": False, "errors": {"form": "An idempotency key is required."}}
	token = new_concurrency_token()
	frappe.db.set_value("Procurement Plan Version", draft, {"version_reason": reason or version.version_reason, "concurrency_token": token}, update_modified=True)
	return {"ok": True, "plan": plan_doc.name, "version": draft, "update_reason": reason, "concurrency_token": token, "idempotency_key": key}
