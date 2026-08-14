# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-UI-10 — Draft successor update overview DTO + save update reason."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt, formatdate, get_fullname

from kentender_procurement.procurement_planning.mvp1_constants import (
	DRAFT_CHANGE_ADDED,
	DRAFT_CHANGE_CHANGED,
	DRAFT_CHANGE_PROPOSED_REMOVAL,
	FINANCE_CONFIRMED,
	ITEM_ACTIVE,
	ITEM_PROPOSED,
	PLAN_OPEN,
	VALIDATION_READY,
	VERSION_EDITABLE_STATUSES,
)
from kentender_procurement.procurement_planning.services._invariants import (
	assert_version_concurrency,
	new_concurrency_token,
)
from kentender_procurement.procurement_planning.services.plan_item_finance import (
	finance_not_confirmed_error,
	finance_status_label,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	ADD_DEMAND_ROLES,
	CAP_PLAN_VIEW,
	SUBMIT_FOR_REVIEW_ROLES,
	actor_planning_roles,
	assert_can_add_demand,
	is_planning_read_only,
	require_capability,
)
from kentender_procurement.procurement_planning.services.remove_plan_item import (
	draft_has_effective_changes,
	item_has_downstream,
	removal_capabilities_for_item,
)
from kentender_procurement.procurement_planning.services.validate_plan import (
	effective_validation_status,
)

SYSTEM_UPDATE_REASONS = frozenset(
	(
		"Initial draft",
		"Opened to add approved Demand",
		"Opened to add approved Demands",
		"Post-approval revision",
	)
)


def _money(amount: float, currency: str) -> str:
	return f"{currency} {flt(amount):,.2f}"


def _ou_label(ou: str) -> str:
	if not ou:
		return ""
	return cstr(frappe.db.get_value("Organisation Unit", ou, "unit_name") or ou)


def planner_update_reason(raw: str | None) -> str:
	text = cstr(raw or "").strip()
	if not text or text in SYSTEM_UPDATE_REASONS:
		return ""
	return text


def plan_canvas_routes(plan_doc) -> dict[str, str]:
	name = plan_doc.name
	approved = cstr(getattr(plan_doc, "current_approved_version", None) or "").strip()
	draft = cstr(getattr(plan_doc, "open_draft_version", None) or "").strip()
	approved_route = f"/app/procurement-plan-approved?plan={name}" if approved else ""
	update_route = f"/app/procurement-plan-update?plan={name}" if approved and draft else ""
	if approved and draft:
		home = update_route
	elif approved:
		home = approved_route
	else:
		home = f"/app/procurement-plan-builder?plan={name}"
	return {
		"approved_route": approved_route,
		"update_route": update_route,
		"builder_route": home,
	}


def _change_label(iv) -> str:
	explicit = cstr(getattr(iv, "draft_change_label", None) or "").strip()
	if explicit:
		return explicit
	if int(getattr(iv, "proposed_removal", 0) or 0):
		return DRAFT_CHANGE_PROPOSED_REMOVAL
	if int(getattr(iv, "carry_forward_unchanged", 0) or 0):
		return ""
	return DRAFT_CHANGE_ADDED


def get_plan_update(*, plan: str, user: str | None = None) -> dict[str, Any]:
	actor = (user or frappe.session.user or "").strip()
	if not actor or actor == "Guest":
		frappe.throw(
			frappe._("Login required."),
			frappe.PermissionError,
			title="PLN_LOGIN_REQUIRED",
		)

	plan_name = cstr(plan).strip()
	if not plan_name or not frappe.db.exists("Procurement Plan", plan_name):
		frappe.throw(frappe._("Procurement Plan not found."), title="PLN_PLAN_NOT_FOUND")

	plan_doc = frappe.get_doc("Procurement Plan", plan_name)
	pe = cstr(plan_doc.procuring_entity).strip()
	ou = cstr(plan_doc.coordinating_org_unit or "").strip() or None
	require_capability(
		CAP_PLAN_VIEW,
		procuring_entity=pe,
		org_unit=ou,
		user=actor,
		require_write=False,
	)

	approved = cstr(plan_doc.current_approved_version or "").strip()
	draft = cstr(plan_doc.open_draft_version or "").strip()
	if not approved:
		frappe.throw(
			frappe._("This Plan has no Approved Version. Open the Draft builder instead."),
			title="PLN_NO_APPROVED_VERSION",
		)
	if not draft:
		frappe.throw(
			frappe._("There is no Draft update in progress. Open the Approved Plan instead."),
			title="PLN_NO_DRAFT_UPDATE",
		)

	approved_ver = frappe.db.get_value(
		"Procurement Plan Version",
		approved,
		["name", "version_number", "status", "concurrency_token"],
		as_dict=True,
	)
	draft_ver = frappe.db.get_value(
		"Procurement Plan Version",
		draft,
		[
			"name",
			"version_number",
			"status",
			"validation_projection",
			"concurrency_token",
			"version_reason",
			"owner",
			"creation",
		],
		as_dict=True,
	)
	if not approved_ver or not draft_ver:
		frappe.throw(frappe._("Plan Version not found."), title="PLN_VERSION_NOT_FOUND")

	currency = plan_doc.currency or "KES"
	read_only = is_planning_read_only(actor)
	roles = actor_planning_roles(actor)
	can_mutate = (not read_only) and bool(roles.intersection(ADD_DEMAND_ROLES))
	can_submit_role = (not read_only) and bool(roles.intersection(SUBMIT_FOR_REVIEW_ROLES))
	lifecycle_open = cstr(plan_doc.lifecycle_state) == PLAN_OPEN
	editable = cstr(draft_ver.status) in VERSION_EDITABLE_STATUSES

	approved_total = 0.0
	for it in frappe.get_all(
		"Procurement Plan Item",
		filters={"plan": plan_name, "baseline_state": ITEM_ACTIVE},
		pluck="name",
	):
		iv_name = frappe.db.get_value(
			"Procurement Plan Item Version",
			{"plan_item": it, "plan_version": approved},
			"name",
		)
		if iv_name:
			approved_total += flt(
				frappe.db.get_value(
					"Procurement Plan Item Version", iv_name, "confirmed_estimate"
				)
			)

	changed_items: list[dict[str, Any]] = []
	unchanged_items: list[dict[str, Any]] = []
	draft_total = 0.0
	has_added = False
	has_removal = False

	for it in frappe.get_all(
		"Procurement Plan Item",
		filters={
			"plan": plan_name,
			"baseline_state": ["in", [ITEM_PROPOSED, ITEM_ACTIVE]],
		},
		fields=["name", "plan_item_code", "baseline_state", "owner_org_unit"],
		order_by="creation asc",
	):
		iv_name = frappe.db.get_value(
			"Procurement Plan Item Version",
			{"plan_item": it.name, "plan_version": draft},
			"name",
		)
		if not iv_name:
			continue
		iv = frappe.get_doc("Procurement Plan Item Version", iv_name)
		amount = flt(iv.confirmed_estimate)
		draft_total += amount
		owner = cstr(it.owner_org_unit or "")
		label = _change_label(iv)
		unchanged = bool(int(iv.carry_forward_unchanged or 0)) and not int(
			iv.proposed_removal or 0
		)
		caps = removal_capabilities_for_item(
			plan_item=it.name,
			baseline_state=it.baseline_state,
			draft_version=draft,
			read_only=read_only or not can_mutate,
		)
		has_handoff = item_has_downstream(it.name)
		row = {
			"plan_item": it.name,
			"plan_item_code": it.plan_item_code,
			"baseline_state": it.baseline_state,
			"change_label": label or ("Unchanged" if unchanged else DRAFT_CHANGE_CHANGED),
			"title": cstr(iv.requirement_title or it.plan_item_code),
			"owner_org_unit": owner,
			"owner_org_unit_label": _ou_label(owner),
			"amount": amount,
			"amount_display": _money(amount, currency),
			"finance_status": finance_status_label(iv),
			"finance_status_label": finance_status_label(iv),
			"validation_projection": cstr(iv.validation_projection or "Not run"),
			"view_route": f"/app/procurement-plan-item-editor?plan_item={it.name}",
			"can_remove_from_draft": caps["can_remove_from_draft"] and not has_handoff,
			"can_propose_removal": caps["can_propose_removal"] and not has_handoff,
			"removal_variant": caps["removal_variant"],
			"finance_effect_copy": caps["finance_effect_copy"],
			"sources_label": caps["sources_label"],
			"tender_reference": "",
		}
		if unchanged:
			unchanged_items.append(row)
		else:
			changed_items.append(row)
			if row["change_label"] == DRAFT_CHANGE_ADDED:
				has_added = True
			if row["change_label"] == DRAFT_CHANGE_PROPOSED_REMOVAL:
				has_removal = True

	if has_added and has_removal:
		change_type = "Additional approved need and proposed removal"
	elif has_removal and not has_added:
		change_type = "Proposed removal"
	else:
		change_type = "Additional approved need"

	delta = draft_total - approved_total
	if delta >= 0:
		change_display = f"{_money(delta, currency)} added"
	else:
		change_display = f"{_money(abs(delta), currency)} removed"

	update_reason = planner_update_reason(draft_ver.version_reason)
	no_changes = not draft_has_effective_changes(plan=plan_name, version=draft)
	finance_err = finance_not_confirmed_error(plan=plan_name, version=draft)
	validation = effective_validation_status(
		plan=plan_name, version=draft, stored=cstr(draft_ver.validation_projection or "")
	)
	issues: list[str] = []
	if finance_err:
		issues.append(
			"Finance confirmation is required for the added Plan Item before this update can be submitted for review."
		)
	elif validation not in ("", VALIDATION_READY) and not no_changes:
		issues.append(
			"Resolve validation issues until the update is Ready before submitting for review."
		)

	needs_attention = bool(issues) or (not update_reason) or no_changes
	can_save = can_mutate and lifecycle_open and editable
	can_validate = can_save and (not no_changes)
	can_cancel = can_mutate and lifecycle_open and editable
	can_submit = (
		can_submit_role
		and lifecycle_open
		and editable
		and (not no_changes)
		and (not finance_err)
		and validation == VALIDATION_READY
		and bool(update_reason)
	)

	approved_number = int(approved_ver.version_number or 1)
	draft_number = int(draft_ver.version_number or approved_number + 1)
	pe_label = (
		frappe.db.get_value("Procuring Entity", plan_doc.procuring_entity, "entity_name")
		or plan_doc.procuring_entity
	)
	routes = plan_canvas_routes(plan_doc)
	unchanged_n = len(unchanged_items)
	unchanged_copy = (
		f"{unchanged_n} existing Plan Item remains unchanged and operational."
		if unchanged_n == 1
		else f"{unchanged_n} existing Plan Items remain unchanged and operational."
	)

	return {
		"ok": True,
		"plan": plan_doc.name,
		"plan_code": plan_doc.plan_code,
		"title": plan_doc.title,
		"procuring_entity": plan_doc.procuring_entity,
		"procuring_entity_label": pe_label,
		"financial_year": plan_doc.financial_year,
		"lifecycle_state": plan_doc.lifecycle_state,
		"currency": currency,
		"version": draft,
		"version_status": cstr(draft_ver.status) or "Draft",
		"version_number": draft_number,
		"version_label": f"Draft Version {draft_number}",
		"approved_version": approved,
		"approved_version_number": approved_number,
		"approved_version_label": f"Approved Version {approved_number}",
		"concurrency_token": cstr(draft_ver.concurrency_token or ""),
		"open_draft_version": draft,
		"current_approved_version": approved,
		"read_only": read_only or not can_mutate,
		"can_save": can_save,
		"can_validate": can_validate,
		"can_submit": can_submit,
		"can_cancel": can_cancel,
		"no_changes_remain": no_changes,
		"needs_attention": needs_attention,
		"attention_chip": "Needs attention" if needs_attention and not no_changes else "",
		"banner_copy": (
			f"Approved Version {approved_number} remains active until this update is approved."
		),
		"approved_total": approved_total,
		"approved_total_display": _money(approved_total, currency),
		"draft_total": draft_total,
		"draft_total_display": _money(draft_total, currency),
		"change_amount": delta,
		"change_display": change_display,
		"changed_count": len(changed_items),
		"unchanged_count": unchanged_n,
		"unchanged_copy": unchanged_copy,
		"change_type_label": change_type,
		"update_reason": update_reason,
		"initiated_by": _ou_label(cstr(plan_doc.coordinating_org_unit or ""))
		or get_fullname(cstr(draft_ver.owner or actor)),
		"created_display": formatdate(draft_ver.creation, "d MMMM yyyy")
		if draft_ver.creation
		else "",
		"validation_projection": validation,
		"issues": issues,
		"issue_message": issues[0] if issues else "",
		"changed_items": changed_items,
		"unchanged_items": unchanged_items,
		"approved_route": routes["approved_route"],
		"update_route": routes["update_route"],
		"builder_route": routes["builder_route"],
		"review_route": f"/app/procurement-plan-review?plan={plan_doc.name}",
	}


def save_plan_update(
	*,
	plan: str,
	update_reason: str | None = None,
	concurrency_token: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	actor = assert_can_add_demand(user)
	plan_name = cstr(plan).strip()
	if not plan_name or not frappe.db.exists("Procurement Plan", plan_name):
		return {"ok": False, "errors": {"form": "Procurement Plan not found"}}

	plan_doc = frappe.get_doc("Procurement Plan", plan_name)
	require_capability(
		CAP_PLAN_VIEW,
		procuring_entity=cstr(plan_doc.procuring_entity).strip(),
		org_unit=cstr(plan_doc.coordinating_org_unit or "").strip() or None,
		user=actor,
		require_write=True,
	)
	approved = cstr(plan_doc.current_approved_version or "").strip()
	draft = cstr(plan_doc.open_draft_version or "").strip()
	if not approved or not draft:
		return {
			"ok": False,
			"errors": {"form": "There is no Draft update to save."},
		}

	reason = cstr(update_reason or "").strip()
	if not reason or reason in SYSTEM_UPDATE_REASONS:
		return {
			"ok": False,
			"errors": {
				"update_reason": "Enter a reason for adding this requirement after Plan approval."
			},
		}

	try:
		assert_version_concurrency(draft, concurrency_token)
	except frappe.ValidationError as exc:
		return {"ok": False, "errors": {"form": str(exc) or "Concurrency conflict"}}

	ver = frappe.get_doc("Procurement Plan Version", draft)
	if cstr(ver.status) not in VERSION_EDITABLE_STATUSES:
		return {
			"ok": False,
			"errors": {"form": "Only a Draft or Returned update can be saved."},
		}

	token = new_concurrency_token()
	frappe.db.set_value(
		"Procurement Plan Version",
		draft,
		{"version_reason": reason, "concurrency_token": token},
		update_modified=True,
	)
	return {
		"ok": True,
		"plan": plan_name,
		"version": draft,
		"update_reason": reason,
		"concurrency_token": token,
	}
