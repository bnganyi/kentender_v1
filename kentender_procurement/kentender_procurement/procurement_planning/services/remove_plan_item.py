# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-017 — Remove / propose-remove a Plan Item (never hard-delete)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, flt, now_datetime

from kentender_procurement.procurement_planning.mvp1_constants import (
	ALLOC_DRAFT,
	ALLOC_EFFECTIVE,
	ALLOC_REVERSED,
	DOCTYPE_DECISION,
	DOCTYPE_HANDOFF,
	DRAFT_CHANGE_PROPOSED_REMOVAL,
	ITEM_ACTIVE,
	ITEM_PROPOSED,
	ITEM_REMOVED,
	MODE_DRAFT_EXCLUDE,
	MODE_PROPOSE_ACTIVE,
	VERSION_CANCELLED,
	VERSION_EDITABLE_STATUSES,
)
from kentender_procurement.procurement_planning.services._invariants import (
	assert_version_concurrency,
	assert_version_mutable,
	new_concurrency_token,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	assert_can_add_demand,
	assert_planning_scope,
	is_planning_read_only,
)


def item_has_downstream(plan_item: str) -> bool:
	if not plan_item:
		return False
	takeup = cstr(
		frappe.db.get_value("Procurement Plan Item", plan_item, "tender_takeup_projection") or ""
	).strip()
	if takeup and takeup != "Not taken up":
		return True
	return bool(
		frappe.db.exists("DocType", DOCTYPE_HANDOFF)
		and frappe.db.exists(DOCTYPE_HANDOFF, {"plan_item": plan_item})
	)


def release_draft_finance_effects(*, plan_item: str, version: str) -> dict[str, Any]:
	"""Isolated Finance reverse hook (PLN-FR-068). Cancels Awaiting or releases owned RSV."""
	from kentender_procurement.procurement_planning.services.plan_item_finance import (
		cancel_awaiting_or_release_owned,
	)

	_ = (plan_item, version)
	marker = f"PLN_FIN_RELEASE|{cstr(plan_item)}|{cstr(version)}"
	existing = frappe.db.exists(
		"Comment",
		{
			"reference_doctype": "Procurement Plan Item",
			"reference_name": plan_item,
			"content": marker,
		},
	)
	if existing:
		return {
			"ok": True,
			"released": False,
			"cancelled_task": False,
			"idempotent": True,
			"reason": "already_recorded",
		}
	result = cancel_awaiting_or_release_owned(plan_item=plan_item, version=version)
	if result.get("cancelled_task") or result.get("released"):
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": "Procurement Plan Item",
				"reference_name": plan_item,
				"content": marker,
			}
		).insert(ignore_permissions=True)
	return result


def draft_has_effective_changes(*, plan: str, version: str) -> bool:
	"""True when the Draft successor still has an addition, edit, or proposed removal."""
	if frappe.db.exists(
		"Procurement Plan Item",
		{"plan": plan, "baseline_state": ITEM_PROPOSED},
	):
		return True
	ivs = frappe.get_all(
		"Procurement Plan Item Version",
		filters={"plan_version": version},
		fields=["name", "plan_item", "proposed_removal", "carry_forward_unchanged"],
	)
	for iv in ivs:
		state = frappe.db.get_value("Procurement Plan Item", iv.plan_item, "baseline_state")
		if state == ITEM_REMOVED:
			continue
		if int(iv.proposed_removal or 0):
			return True
		if not int(iv.carry_forward_unchanged or 0):
			return True
	return False


def removal_capabilities_for_item(
	*,
	plan_item: str,
	baseline_state: str,
	draft_version: str | None,
	read_only: bool,
) -> dict[str, Any]:
	"""Server-derived UI flags — never inferred by the client."""
	out = {
		"can_remove_from_draft": False,
		"can_propose_removal": False,
		"removal_variant": None,
		"finance_effect_kind": "none",
		"finance_effect_copy": "No funding confirmed; no reservation to release",
		"sources_label": _sources_label(plan_item) if plan_item else "",
	}
	if read_only:
		return out
	if item_has_downstream(plan_item):
		return out
	if baseline_state == ITEM_PROPOSED:
		if not draft_version:
			return out
		out["can_remove_from_draft"] = True
		out["removal_variant"] = "draft"
		return out
	if baseline_state == ITEM_ACTIVE:
		iv = frappe.db.get_value(
			"Procurement Plan Item Version",
			{"plan_item": plan_item, "plan_version": draft_version},
			["name", "proposed_removal"],
			as_dict=True,
		) if draft_version else None
		if iv and int(iv.proposed_removal or 0):
			return out
		out["can_propose_removal"] = True
		out["removal_variant"] = "active"
		return out
	return out


def _money(amount: float, currency: str) -> str:
	return f"{currency} {flt(amount):,.0f}"


def _removal_sources(plan_item: str, currency: str) -> list[dict[str, Any]]:
	allocs = frappe.get_all(
		"Plan Demand Allocation",
		filters={"plan_item": plan_item, "status": ["in", [ALLOC_DRAFT, ALLOC_EFFECTIVE]]},
		fields=["demand", "demand_item", "allocated_amount", "source_org_unit"],
		order_by="creation asc",
	)
	grouped: dict[str, dict[str, Any]] = {}
	for alloc in allocs:
		demand = cstr(alloc.demand).strip()
		if demand not in grouped:
			drow = frappe.db.get_value(
				"Demand", demand, ["demand_code", "title", "owner_org_unit"], as_dict=True
			) or frappe._dict()
			ou = cstr(alloc.source_org_unit or drow.owner_org_unit or "").strip()
			grouped[demand] = {
				"demand": demand,
				"demand_code": cstr(drow.demand_code or demand),
				"title": cstr(drow.title),
				"organisation_unit": ou,
				"organisation_unit_label": cstr(
					frappe.db.get_value("Organisation Unit", ou, "unit_name") or ou
				),
				"need_item_count": 0,
				"amount": 0.0,
			}
		grouped[demand]["need_item_count"] += 1
		grouped[demand]["amount"] += flt(alloc.allocated_amount)
	for row in grouped.values():
		row["amount_display"] = _money(row["amount"], currency)
	return list(grouped.values())


def get_plan_item_removal(
	*, plan: str, plan_item: str, user: str | None = None
) -> dict[str, Any]:
	"""Mutation-free authoritative PLN-UI-05A projection."""
	actor = cstr(user or frappe.session.user).strip()
	plan_name = cstr(plan).strip()
	item_name = cstr(plan_item).strip()
	if not plan_name or not frappe.db.exists("Procurement Plan", plan_name):
		frappe.throw(_("Procurement Plan not found."), title="PLN_PLAN_NOT_FOUND")
	if not item_name or not frappe.db.exists("Procurement Plan Item", item_name):
		frappe.throw(_("Plan Item not found."), title="PLN_ITEM_NOT_FOUND")
	plan_doc = frappe.get_doc("Procurement Plan", plan_name)
	item = frappe.get_doc("Procurement Plan Item", item_name)
	if cstr(item.plan) != plan_name:
		frappe.throw(_("Plan Item does not belong to this Plan."), title="PLN_ITEM_NOT_IN_PLAN")
	assert_planning_scope(
		procuring_entity=cstr(plan_doc.procuring_entity),
		org_unit=cstr(item.owner_org_unit or "") or None,
		user=actor,
		require_write=False,
	)
	draft = cstr(plan_doc.open_draft_version or "").strip()
	state = cstr(item.baseline_state).strip()
	focus = draft if state == ITEM_PROPOSED else cstr(item.current_approved_item_version or "").strip()
	iv_name = cstr(item.draft_item_version or focus).strip()
	if state == ITEM_ACTIVE and draft:
		iv_name = cstr(
			frappe.db.get_value(
				"Procurement Plan Item Version",
				{"plan_item": item_name, "plan_version": draft},
				"name",
			)
			or item.current_approved_item_version
		).strip()
	if not iv_name:
		frappe.throw(_("Plan Item Version not found."), title="PLN_ITEM_VERSION_NOT_FOUND")
	iv = frappe.get_doc("Procurement Plan Item Version", iv_name)
	read_only = is_planning_read_only(actor)
	editable_draft = bool(draft) and cstr(
		frappe.db.get_value("Procurement Plan Version", draft, "status") or ""
	) in VERSION_EDITABLE_STATUSES
	plan_open = cstr(plan_doc.lifecycle_state) == "Open"
	blocked = item_has_downstream(item_name)
	mode = MODE_DRAFT_EXCLUDE if state == ITEM_PROPOSED else MODE_PROPOSE_ACTIVE
	can_remove = bool(
		plan_open
		and not read_only
		and not blocked
		and state in (ITEM_PROPOSED, ITEM_ACTIVE)
		and (editable_draft if state == ITEM_PROPOSED else (not draft or editable_draft))
	)
	currency = cstr(iv.currency or plan_doc.currency or "KES")
	sources = _removal_sources(item_name, currency)
	amount = flt(iv.confirmed_estimate)
	finance_status = cstr(iv.finance_status or "Not requested")
	reservation = cstr(iv.finance_reservation or iv.reservation_reference or "").strip()
	reservation_code = reservation
	if reservation and frappe.db.exists("Funding Reservation", reservation):
		reservation_code = cstr(
			frappe.db.get_value("Funding Reservation", reservation, "generated_reference") or reservation
		)
	combined = len(sources) > 1
	need_count = sum(int(row["need_item_count"]) for row in sources)
	if mode == MODE_PROPOSE_ACTIVE:
		intro = "The item remains active until the plan update is approved."
		effect = (
			f"If the update is approved, the item will be removed, {_money(amount, currency)} "
			"will be released and the source Demand will be available for planning again."
		)
		title = "Remove Plan Item from approved plan?"
		confirm_label = "Add removal to plan update"
		placeholder = "Briefly explain why this item should be removed from the approved plan."
	elif combined:
		intro = f"This removes the complete combined Plan Item from Draft Version {int(frappe.db.get_value('Procurement Plan Version', draft, 'version_number') or 1)}."
		effect = (
			f"The whole Plan Item and all {need_count} source allocations will be removed together. "
			"Both Approved Demands will be available for planning again."
		)
		title = "Remove Plan Item from draft?"
		confirm_label = "Remove from draft"
		placeholder = "Briefly explain why this item should be removed from the draft."
	elif finance_status == "Confirmed" and reservation_code:
		intro = "This removes the item from Draft Version 2 and makes its Approved Demand available for planning again."
		effect = f"Finance confirmation will be reversed and reservation {reservation_code} for {_money(amount, currency)} will be released."
		title = "Remove Plan Item from draft?"
		confirm_label = "Remove from draft"
		placeholder = "Briefly explain why this item should be removed from the draft."
	else:
		ver_no = int(frappe.db.get_value("Procurement Plan Version", draft, "version_number") or 1) if draft else 1
		intro = f"This removes the item from Draft Version {ver_no}. Its Approved Demand will be available for planning again."
		effect = "No Finance confirmation or reservation will be reversed."
		title = "Remove Plan Item from draft?"
		confirm_label = "Remove from draft"
		placeholder = "Briefly explain why this item should be removed from the draft."
	owner = cstr(item.owner_org_unit or "").strip()
	return {
		"ok": True,
		"can_remove": can_remove,
		"error_code": "PLN_ITEM_NOT_REMOVABLE" if not can_remove else None,
		"mode": mode,
		"variant": "active" if mode == MODE_PROPOSE_ACTIVE else ("combined" if combined else ("finance_confirmed" if finance_status == "Confirmed" else "draft")),
		"plan": plan_name,
		"draft_version": draft or None,
		"expected_version_token": cstr(
			frappe.db.get_value("Procurement Plan Version", draft or plan_doc.current_approved_version, "concurrency_token") or ""
		),
		"plan_item": item_name,
		"plan_item_code": cstr(item.plan_item_code),
		"title": cstr(iv.requirement_title),
		"ownership_label": cstr(frappe.db.get_value("Organisation Unit", owner, "unit_name") or owner or frappe.db.get_value("Procuring Entity", plan_doc.procuring_entity, "legal_name") or plan_doc.procuring_entity),
		"planned_value": amount,
		"planned_value_display": _money(amount, currency),
		"currency": currency,
		"finance_status": finance_status,
		"reservation_reference": reservation_code,
		"sources": sources,
		"need_item_count": need_count,
		"combined": combined,
		"dialog_title": title,
		"intro_copy": intro,
		"effect_copy": effect,
		"reason_placeholder": placeholder,
		"confirm_label": confirm_label,
		"cancel_label": "Keep item",
		"resulting_destination": (
			f"/app/procurement-plan-builder?plan={plan_name}"
			if mode == MODE_PROPOSE_ACTIVE
			else f"/app/procurement-plan-builder?plan={plan_name}"
		),
	}


def _sources_label(plan_item: str) -> str:
	rows = frappe.get_all(
		"Plan Demand Allocation",
		filters={"plan_item": plan_item},
		fields=["demand", "demand_item"],
	)
	demands = {cstr(r.demand) for r in rows if r.demand}
	need_items = {cstr(r.demand_item) for r in rows if r.demand_item}
	d_n = len(demands)
	n_n = len(need_items)
	d_word = "Demand" if d_n == 1 else "Demands"
	n_word = "Need Item" if n_n == 1 else "Need Items"
	return f"{d_n} {d_word} · {n_n} {n_word}"


def _refresh_demand_planning_usage(demand: str) -> None:
	"""Restore eligibility projection from remaining Draft/Effective allocations.

	Does not change Demand status, estimates, or other HoD-owned facts.
	"""
	if not demand or not frappe.db.has_column("Demand", "planning_usage"):
		return
	planned = flt(
		frappe.db.sql(
			"""
			select coalesce(sum(allocated_amount), 0) from `tabPlan Demand Allocation`
			where demand=%s and status in ('Draft', 'Effective')
			""",
			demand,
		)[0][0]
	)
	approved = flt(
		frappe.db.get_value("Demand", demand, "confirmed_estimate")
		or frappe.db.get_value("Demand", demand, "requester_estimate")
		or 0
	)
	if planned <= 0.0001:
		usage = "Not taken up"
	elif approved > 0 and planned + 0.0001 >= approved:
		usage = "Fully planned"
	else:
		usage = "Partially planned"
	frappe.db.set_value("Demand", demand, "planning_usage", usage, update_modified=False)


def _reverse_allocations(
	*,
	plan_item: str,
	version: str,
	reason: str,
	statuses: tuple[str, ...],
) -> int:
	now = now_datetime()
	rows = frappe.get_all(
		"Plan Demand Allocation",
		filters={"plan_item": plan_item, "status": ["in", list(statuses)]},
		fields=["name", "demand"],
	)
	demands: set[str] = set()
	for row in rows:
		frappe.db.set_value(
			"Plan Demand Allocation",
			row.name,
			{
				"status": ALLOC_REVERSED,
				"active_hold_key": None,
				"reversed_by_version": version,
				"reversed_at": now,
				"reason": reason,
			},
			update_modified=True,
		)
		if row.demand:
			demands.add(cstr(row.demand))
	for demand in demands:
		_refresh_demand_planning_usage(demand)
	return len(rows)


def _write_removal_decision(*, version: str, actor: str, reason: str, decision: str) -> None:
	frappe.get_doc(
		{
			"doctype": DOCTYPE_DECISION,
			"plan_version": version,
			"decision_type": "Removal",
			"decision_stage": "Plan Item removal",
			"actor": actor,
			"actor_role": "Procurement Planner",
			"decision": decision,
			"reason": reason,
			"decided_at": now_datetime(),
		}
	).insert(ignore_permissions=True)


def assert_no_handoff_for_proposed_removals(*, version: str) -> None:
	ivs = frappe.get_all(
		"Procurement Plan Item Version",
		filters={"plan_version": version, "proposed_removal": 1},
		fields=["plan_item"],
	)
	blocked = [iv.plan_item for iv in ivs if item_has_downstream(iv.plan_item)]
	if blocked:
		frappe.throw(
			_(
				"A Tender handoff now exists for an item proposed for removal. "
				"Approval cannot apply the removal."
			),
			title="PLN_ITEM_NOT_REMOVABLE",
		)


def apply_proposed_removals_on_approval(*, version: str, actor: str) -> list[str]:
	"""Mark proposed-removal items Removed and reverse unconsumed Effective allocations."""
	assert_no_handoff_for_proposed_removals(version=version)
	applied: list[str] = []
	ivs = frappe.get_all(
		"Procurement Plan Item Version",
		filters={"plan_version": version, "proposed_removal": 1},
		fields=["name", "plan_item", "removal_reason"],
	)
	for iv in ivs:
		reason = cstr(iv.removal_reason or "Proposed removal approved")
		frappe.db.set_value(
			"Procurement Plan Item",
			iv.plan_item,
			{
				"baseline_state": ITEM_REMOVED,
				"draft_item_version": None,
			},
			update_modified=True,
		)
		frappe.db.set_value(
			"Procurement Plan Item Version",
			iv.name,
			{"removed_in_version": version},
			update_modified=False,
		)
		_reverse_allocations(
			plan_item=iv.plan_item,
			version=version,
			reason=reason,
			statuses=(ALLOC_EFFECTIVE, ALLOC_DRAFT),
		)
		release_draft_finance_effects(plan_item=iv.plan_item, version=version)
		applied.append(iv.plan_item)
	return applied


def cancel_plan_update(
	*,
	plan: str,
	concurrency_token: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	"""Cancel an empty Draft successor when no effective changes remain."""
	actor = assert_can_add_demand(user)
	plan_name = cstr(plan).strip()
	if not plan_name or not frappe.db.exists("Procurement Plan", plan_name):
		return {"ok": False, "errors": {"form": "Procurement Plan not found"}}

	plan_doc = frappe.get_doc("Procurement Plan", plan_name)
	assert_planning_scope(
		procuring_entity=cstr(plan_doc.procuring_entity).strip(),
		org_unit=None,
		user=actor,
		require_write=True,
	)
	draft = cstr(plan_doc.open_draft_version or "").strip()
	if not draft:
		return {"ok": False, "errors": {"form": "There is no Draft update to cancel."}}
	if not cstr(plan_doc.current_approved_version or "").strip():
		return {"ok": False, "errors": {"form": "The initial Draft cannot be cancelled this way."}}

	assert_version_concurrency(draft, concurrency_token)
	ver = frappe.get_doc("Procurement Plan Version", draft)
	if cstr(ver.status) not in VERSION_EDITABLE_STATUSES:
		return {"ok": False, "errors": {"form": "Only a Draft or Returned update can be cancelled."}}
	if draft_has_effective_changes(plan=plan_name, version=draft):
		return {
			"ok": False,
			"errors": {"form": "This update still has changes. Remove or complete them first."},
		}

	frappe.db.set_value(
		"Procurement Plan Version",
		draft,
		{"status": VERSION_CANCELLED, "open_version_slot": None, "concurrency_token": new_concurrency_token()},
		update_modified=True,
	)
	frappe.db.set_value(
		"Procurement Plan",
		plan_name,
		{"open_draft_version": None},
		update_modified=False,
	)
	for item in frappe.get_all(
		"Procurement Plan Item",
		filters={"plan": plan_name, "draft_item_version": ["is", "set"]},
		pluck="name",
	):
		frappe.db.set_value(
			"Procurement Plan Item",
			item,
			{"draft_item_version": None},
			update_modified=False,
		)
	return {"ok": True, "plan": plan_name, "version": draft, "status": VERSION_CANCELLED}


def remove_plan_item_from_plan(
	*,
	plan: str,
	plan_item: str,
	reason: str | None = None,
	draft_version: str | None = None,
	expected_version_token: str | None = None,
	idempotency_key: str | None = None,
	concurrency_token: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	"""Public capability: exclude a draft-only item or propose Active removal.

	Client may send only identifiers, expected concurrency, reason and idempotency.
	Mode, finance, eligibility and downstream checks are derived server-side.
	"""
	actor = assert_can_add_demand(user)
	reason_text = cstr(reason or "").strip()
	key = cstr(idempotency_key or "").strip()
	if not reason_text:
		return {
			"ok": False,
			"errors": {"reason": "A reason for removal is required."},
		}
	if not key:
		return {"ok": False, "errors": {"form": "An idempotency key is required."}}

	plan_name = cstr(plan).strip()
	item_name = cstr(plan_item).strip()
	if not plan_name or not frappe.db.exists("Procurement Plan", plan_name):
		frappe.throw(_("Procurement Plan not found."), title="PLN_PLAN_NOT_FOUND")
	if not item_name or not frappe.db.exists("Procurement Plan Item", item_name):
		frappe.throw(_("Plan Item not found."), title="PLN_ITEM_NOT_FOUND")

	plan_doc = frappe.get_doc("Procurement Plan", plan_name)
	assert_planning_scope(
		procuring_entity=cstr(plan_doc.procuring_entity).strip(),
		org_unit=None,
		user=actor,
		require_write=True,
	)
	item = frappe.get_doc("Procurement Plan Item", item_name)
	if cstr(item.plan) != plan_name:
		frappe.throw(_("Plan Item does not belong to this Plan."), title="PLN_ITEM_NOT_IN_PLAN")

	marker = f"PLN_REMOVE|{key}"
	existing_marker = frappe.db.exists(
		"Comment",
		{
			"reference_doctype": "Procurement Plan Item",
			"reference_name": item_name,
			"content": marker,
		},
	)
	if existing_marker:
		return _removal_result(plan_doc=plan_doc, item_name=item_name, mode=(MODE_PROPOSE_ACTIVE if cstr(item.baseline_state) == ITEM_ACTIVE else MODE_DRAFT_EXCLUDE), idempotent=True)

	# Lock the logical graph before deriving the command mode.
	frappe.db.sql("select name from `tabProcurement Plan` where name=%s for update", plan_name)
	frappe.db.sql("select name from `tabProcurement Plan Item` where name=%s for update", item_name)
	plan_doc.reload()
	item.reload()
	draft = cstr(plan_doc.open_draft_version or "").strip()
	state = cstr(item.baseline_state)

	# Idempotent: already excluded
	if state == ITEM_REMOVED:
		return {
			"ok": True,
			"idempotent": True,
			"mode": MODE_DRAFT_EXCLUDE,
			"plan": plan_name,
			"plan_item": item_name,
			"no_changes_remain": not draft_has_effective_changes(plan=plan_name, version=draft)
			if draft
			else True,
		}

	client_token = expected_version_token or concurrency_token
	created_revision = False
	if state == ITEM_ACTIVE and not draft:
		approved = cstr(plan_doc.current_approved_version or "").strip()
		assert_version_concurrency(approved, client_token)
		from kentender_procurement.procurement_planning.services.open_or_create_plan_revision import (
			open_or_create_plan_revision,
		)

		rev = open_or_create_plan_revision(plan=plan_name, version_reason=reason_text, user=actor)
		draft = rev["version"]
		created_revision = bool(rev.get("created"))
		plan_doc.reload()

	if not draft:
		frappe.throw(
			_("Open a Draft version before removing a Plan Item."),
			title="PLN_NO_DRAFT_VERSION",
		)

	if state == ITEM_PROPOSED and cstr(draft_version or "").strip() != draft:
		frappe.throw(_("The Draft Version has changed."), title="PLN_VERSION_STALE")
	if not created_revision:
		assert_version_concurrency(draft, client_token)
	frappe.db.sql("select name from `tabProcurement Plan Version` where name=%s for update", draft)
	frappe.db.sql(
		"select name from `tabPlan Demand Allocation` where plan_item=%s and status in ('Draft','Effective') for update",
		item_name,
	)
	ver = frappe.get_doc("Procurement Plan Version", draft)
	assert_version_mutable(cstr(ver.status))
	if cstr(ver.status) not in VERSION_EDITABLE_STATUSES:
		frappe.throw(
			_("Only Draft or Returned versions can be edited."),
			title="PLN_VERSION_NOT_EDITABLE",
		)

	if item_has_downstream(item_name):
		frappe.throw(
			_("This Plan Item has a Tender handoff and cannot be removed."),
			title="PLN_ITEM_NOT_REMOVABLE",
		)

	iv_name = frappe.db.get_value(
		"Procurement Plan Item Version",
		{"plan_item": item_name, "plan_version": draft},
		"name",
	)
	if not iv_name:
		iv_name = cstr(item.draft_item_version or item.current_approved_item_version or "")
	if not iv_name:
		frappe.throw(_("Plan Item Version not found."), title="PLN_ITEM_VERSION_NOT_FOUND")

	# Idempotent proposed removal
	if state == ITEM_ACTIVE and int(
		frappe.db.get_value("Procurement Plan Item Version", iv_name, "proposed_removal") or 0
	):
		return {
			"ok": True,
			"idempotent": True,
			"mode": MODE_PROPOSE_ACTIVE,
			"plan": plan_name,
			"plan_item": item_name,
			"no_changes_remain": False,
		}

	if state == ITEM_PROPOSED:
		mode = MODE_DRAFT_EXCLUDE
		_apply_draft_exclude(
			item_name=item_name,
			iv_name=iv_name,
			draft=draft,
			reason=reason_text,
			actor=actor,
		)
	elif state == ITEM_ACTIVE:
		mode = MODE_PROPOSE_ACTIVE
		_apply_propose_active(
			iv_name=iv_name,
			reason=reason_text,
			actor=actor,
			draft=draft,
		)
	else:
		frappe.throw(
			_("This Plan Item cannot be removed."),
			title="PLN_ITEM_NOT_REMOVABLE",
		)

	frappe.db.set_value(
		"Procurement Plan Version",
		draft,
		{"concurrency_token": new_concurrency_token()},
		update_modified=True,
	)
	frappe.get_doc(
		{
			"doctype": "Comment",
			"comment_type": "Info",
			"reference_doctype": "Procurement Plan Item",
			"reference_name": item_name,
			"content": marker,
		}
	).insert(ignore_permissions=True)

	return _removal_result(plan_doc=plan_doc, item_name=item_name, mode=mode, idempotent=False)


def _removal_result(*, plan_doc: Any, item_name: str, mode: str, idempotent: bool) -> dict[str, Any]:
	draft = cstr(plan_doc.open_draft_version or "").strip()
	initial = not cstr(plan_doc.current_approved_version or "").strip()
	remaining: list[Any] = []
	if draft:
		for row in frappe.get_all(
			"Procurement Plan Item Version",
			filters={"plan_version": draft},
			fields=["plan_item", "confirmed_estimate", "proposed_removal"],
		):
			state = frappe.db.get_value("Procurement Plan Item", row.plan_item, "baseline_state")
			if state != ITEM_REMOVED and not int(row.proposed_removal or 0):
				remaining.append(row)
	total = sum(flt(row.confirmed_estimate) for row in remaining)
	no_changes = not draft_has_effective_changes(plan=plan_doc.name, version=draft) if draft else True
	if initial and not remaining:
		destination = f"/app/procurement-plan-builder?plan={plan_doc.name}"
		state_id = "PLN-UI-03"
	else:
		destination = f"/app/procurement-plan-builder?plan={plan_doc.name}"
		state_id = "PLN-UI-05"
	return {
		"ok": True,
		"idempotent": idempotent,
		"mode": mode,
		"plan": plan_doc.name,
		"plan_item": item_name,
		"version": draft or None,
		"item_count": len(remaining),
		"planned_total": total,
		"planned_total_display": _money(total, cstr(plan_doc.currency or "KES")),
		"no_changes_remain": no_changes,
		"state_id": state_id,
		"destination": destination,
		"message": "Plan Item removal recorded.",
	}


def _apply_draft_exclude(
	*,
	item_name: str,
	iv_name: str,
	draft: str,
	reason: str,
	actor: str,
) -> None:
	frappe.db.set_value(
		"Procurement Plan Item",
		item_name,
		{"baseline_state": ITEM_REMOVED, "draft_item_version": None},
		update_modified=True,
	)
	frappe.db.set_value(
		"Procurement Plan Item Version",
		iv_name,
		{
			"removal_reason": reason,
			"removed_in_version": draft,
			"proposed_removal": 0,
		},
		update_modified=True,
	)
	_reverse_allocations(
		plan_item=item_name,
		version=draft,
		reason=reason,
		statuses=(ALLOC_DRAFT,),
	)
	release_draft_finance_effects(plan_item=item_name, version=draft)
	_write_removal_decision(
		version=draft,
		actor=actor,
		reason=reason,
		decision="Removed from draft",
	)


def _apply_propose_active(
	*,
	iv_name: str,
	reason: str,
	actor: str,
	draft: str,
) -> None:
	frappe.db.set_value(
		"Procurement Plan Item Version",
		iv_name,
		{
			"proposed_removal": 1,
			"draft_change_label": DRAFT_CHANGE_PROPOSED_REMOVAL,
			"removal_reason": reason,
		},
		update_modified=True,
	)
	_write_removal_decision(
		version=draft,
		actor=actor,
		reason=reason,
		decision="Proposed removal",
	)
