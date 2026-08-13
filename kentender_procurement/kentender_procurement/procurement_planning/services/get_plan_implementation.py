# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-015 / PLN-UI-09 — Approved Plan implementation read DTO."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt, formatdate, nowdate

from kentender_procurement.procurement_planning.mvp1_constants import (
	DOCTYPE_HANDOFF,
	DOCTYPE_PUBLICATION,
	FINANCE_CONFIRMED,
	ITEM_ACTIVE,
	PLAN_OPEN,
	PUB_FAILED,
	PUB_PUBLISHED,
	TAKEUP_ACTIVE,
	TAKEUP_NOT_TAKEN,
	VERSION_APPROVED,
)
from kentender_procurement.procurement_planning.services.plan_item_finance import (
	effective_finance_status,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	ADD_DEMAND_ROLES,
	CAP_PLAN_VIEW,
	actor_planning_roles,
	is_planning_read_only,
	require_capability,
)
from kentender_procurement.procurement_planning.services.remove_plan_item import (
	_sources_label,
	item_has_downstream,
)


def _money(amount: float, currency: str) -> str:
	return f"{currency} {flt(amount):,.2f}"


def _ou_label(ou: str) -> str:
	if not ou:
		return ""
	return cstr(frappe.db.get_value("Organisation Unit", ou, "unit_name") or ou)


def _publication_dto(*, plan_version: str) -> dict[str, Any]:
	empty = {
		"status": "Not published",
		"status_raw": "",
		"destination": "Tender Portal",
		"published_at": "",
		"published_at_display": "",
		"external_reference": "",
		"failure_reason": "",
		"event": "",
		"published": False,
	}
	if not plan_version or not frappe.db.exists("DocType", DOCTYPE_PUBLICATION):
		return empty
	row = frappe.get_all(
		DOCTYPE_PUBLICATION,
		filters={"plan_version": plan_version},
		fields=[
			"name",
			"channel",
			"status",
			"published_at",
			"external_reference",
			"failure_reason",
		],
		order_by="modified desc",
		limit=1,
	)
	if not row:
		return empty
	ev = row[0]
	status = cstr(ev.status)
	if status == PUB_PUBLISHED:
		label = "Published"
	elif status == PUB_FAILED:
		label = "Failed"
	else:
		label = status or "Not published"
	return {
		"status": label,
		"status_raw": status,
		"destination": cstr(ev.channel) or "Tender Portal",
		"published_at": str(ev.published_at or ""),
		"published_at_display": formatdate(ev.published_at, "dd MMM yyyy")
		if ev.published_at
		else "",
		"external_reference": cstr(ev.external_reference or ""),
		"failure_reason": cstr(ev.failure_reason or ""),
		"event": ev.name,
		"published": status == PUB_PUBLISHED,
	}


def _handoff_for_item(plan_item: str) -> dict[str, Any] | None:
	if not plan_item or not frappe.db.exists("DocType", DOCTYPE_HANDOFF):
		return None
	row = frappe.get_all(
		DOCTYPE_HANDOFF,
		filters={"plan_item": plan_item},
		fields=["name", "handoff_code", "tender_reference"],
		limit=1,
	)
	return row[0] if row else None


def get_plan_implementation(*, plan: str, user: str | None = None) -> dict[str, Any]:
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
	if not approved:
		frappe.throw(
			frappe._("This Plan has no Approved Version. Open the Draft builder instead."),
			title="PLN_NO_APPROVED_VERSION",
		)

	ver = frappe.db.get_value(
		"Procurement Plan Version",
		approved,
		["name", "version_code", "version_number", "status", "concurrency_token"],
		as_dict=True,
	)
	if not ver:
		frappe.throw(frappe._("Approved Plan Version not found."), title="PLN_VERSION_NOT_FOUND")

	currency = plan_doc.currency or "KES"
	read_only = is_planning_read_only(actor)
	roles = actor_planning_roles(actor)
	can_mutate = (not read_only) and bool(roles.intersection(ADD_DEMAND_ROLES))
	lifecycle_open = cstr(plan_doc.lifecycle_state) == PLAN_OPEN
	can_add_item = can_mutate and lifecycle_open
	can_export = can_mutate and lifecycle_open

	draft = cstr(plan_doc.open_draft_version or "").strip()
	draft_number = 0
	if draft:
		draft_number = int(
			frappe.db.get_value("Procurement Plan Version", draft, "version_number") or 0
		)
	approved_number = int(ver.version_number or 1)
	has_successor = bool(draft)
	new_item_count = 0
	if draft:
		new_item_count = frappe.db.count(
			"Procurement Plan Item",
			{"plan": plan_name, "baseline_state": "Proposed"},
		)

	items_out: list[dict[str, Any]] = []
	planned_total = 0.0
	taken_up = 0
	ou_options: list[dict[str, str]] = []
	seen_ou: set[str] = set()

	for it in frappe.get_all(
		"Procurement Plan Item",
		filters={"plan": plan_name, "baseline_state": ITEM_ACTIVE},
		fields=[
			"name",
			"plan_item_code",
			"baseline_state",
			"owner_org_unit",
			"current_approved_item_version",
		],
		order_by="creation asc",
	):
		iv_name = cstr(it.current_approved_item_version or "").strip()
		if not iv_name:
			iv_name = cstr(
				frappe.db.get_value(
					"Procurement Plan Item Version",
					{"plan_item": it.name, "plan_version": approved},
					"name",
				)
				or ""
			)
		if not iv_name:
			continue
		iv = frappe.get_doc("Procurement Plan Item Version", iv_name)
		amount = flt(iv.confirmed_estimate)
		planned_total += amount
		owner = cstr(it.owner_org_unit or "")
		if owner and owner not in seen_ou:
			seen_ou.add(owner)
			ou_options.append({"id": owner, "label": _ou_label(owner)})
		handoff = _handoff_for_item(it.name)
		has_handoff = bool(handoff) or item_has_downstream(it.name)
		if has_handoff:
			taken_up += 1
			takeup_label = TAKEUP_ACTIVE
			tender_ref = cstr((handoff or {}).get("tender_reference") or "")
			progress_label = "—"
		else:
			takeup_label = TAKEUP_NOT_TAKEN
			tender_ref = ""
			progress_label = "—"
		milestone = ""
		if iv.ms_delivery_completion:
			milestone = f"Completion by {formatdate(iv.ms_delivery_completion, 'dd MMM yyyy')}"
		can_propose = can_add_item and not has_handoff
		items_out.append(
			{
				"plan_item": it.name,
				"plan_item_code": it.plan_item_code,
				"title": cstr(iv.requirement_title or it.plan_item_code),
				"owner_org_unit": owner,
				"owner_org_unit_label": _ou_label(owner),
				"amount": amount,
				"amount_display": _money(amount, currency),
				"takeup_label": takeup_label,
				"tender_reference": tender_ref,
				"milestone_label": milestone or "—",
				"progress_label": progress_label,
				"variance_label": "—",
				"finance_status": effective_finance_status(iv),
				"can_propose_removal": can_propose,
				"removal_variant": "active" if can_propose else None,
				"sources_label": _sources_label(it.name),
				"finance_effect_copy": (
					"Confirmed funding remains on the Approved Version until the update is approved."
					if can_propose
					else ""
				),
				"view_route": f"/app/procurement-plan-item-editor?plan_item={it.name}",
			}
		)

	item_count = len(items_out)
	takeup_label = f"{taken_up} of {item_count}" if item_count else "0 of 0"
	publication = _publication_dto(plan_version=approved)

	successor_label = ""
	successor_copy = ""
	if has_successor:
		item_word = "Plan Item" if new_item_count == 1 else "Plan Items"
		successor_label = f"Draft Version {draft_number or approved_number + 1} in progress"
		successor_copy = (
			f"{successor_label} · {new_item_count} new {item_word} · "
			f"Approved Version {approved_number} remains operational."
		)

	fy = cstr(plan_doc.financial_year or "")
	as_at = formatdate(nowdate(), "dd MMM yyyy")
	pe_label = (
		frappe.db.get_value("Procuring Entity", plan_doc.procuring_entity, "entity_name")
		or plan_doc.procuring_entity
	)

	return {
		"ok": True,
		"plan": plan_doc.name,
		"plan_code": plan_doc.plan_code,
		"title": plan_doc.title,
		"procuring_entity": plan_doc.procuring_entity,
		"procuring_entity_label": pe_label,
		"financial_year": fy,
		"lifecycle_state": plan_doc.lifecycle_state,
		"currency": currency,
		"version": approved,
		"version_number": approved_number,
		"version_status": cstr(ver.status) or VERSION_APPROVED,
		"version_label": f"Approved Version {approved_number}",
		"concurrency_token": cstr(ver.concurrency_token or ""),
		"open_draft_version": draft,
		"has_successor": has_successor,
		"successor_label": successor_label,
		"successor_copy": successor_copy,
		"read_only": True,
		"can_add_item": can_add_item,
		"can_export": can_export,
		"planned_total": planned_total,
		"planned_total_display": _money(planned_total, currency),
		"item_count": item_count,
		"takeup_count": taken_up,
		"takeup_label": takeup_label,
		"on_schedule_label": "—",
		"publication": publication,
		"publication_status_label": publication["status"],
		"as_at_display": f"As at: {as_at}",
		"reporting_period_label": f"FY {fy}" if fy else "",
		"ou_options": ou_options,
		"items": items_out,
		"add_route": f"/app/procurement-plan-approved?plan={plan_doc.name}",
		"update_route": (
			f"/app/procurement-plan-update?plan={plan_doc.name}"
			if has_successor
			else f"/app/procurement-plan-approved?plan={plan_doc.name}"
		),
		"approved_route": f"/app/procurement-plan-approved?plan={plan_doc.name}",
		"secondary_line": (
			f"Open Plan · Approved Version {approved_number} · Approved baseline is read-only"
		),
	}
