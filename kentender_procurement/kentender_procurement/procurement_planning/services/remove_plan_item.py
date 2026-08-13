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
)


def item_has_downstream(plan_item: str) -> bool:
	if not plan_item or not frappe.db.exists("DocType", DOCTYPE_HANDOFF):
		return False
	return bool(frappe.db.exists(DOCTYPE_HANDOFF, {"plan_item": plan_item}))


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
	if read_only or not draft_version:
		return out
	if item_has_downstream(plan_item):
		return out
	if baseline_state == ITEM_PROPOSED:
		out["can_remove_from_draft"] = True
		out["removal_variant"] = "draft"
		return out
	if baseline_state == ITEM_ACTIVE:
		iv = frappe.db.get_value(
			"Procurement Plan Item Version",
			{"plan_item": plan_item, "plan_version": draft_version},
			["name", "proposed_removal"],
			as_dict=True,
		)
		if iv and int(iv.proposed_removal or 0):
			return out
		out["can_propose_removal"] = True
		out["removal_variant"] = "active"
		return out
	return out


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
		org_unit=cstr(plan_doc.coordinating_org_unit or "").strip() or None,
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
		{"status": VERSION_CANCELLED, "concurrency_token": new_concurrency_token()},
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
	concurrency_token: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	"""Public capability: exclude a draft-only item or propose Active removal.

	Client may send only plan, plan_item, reason, concurrency_token.
	Mode, finance, eligibility and downstream checks are derived server-side.
	"""
	actor = assert_can_add_demand(user)
	reason_text = cstr(reason or "").strip()
	if not reason_text:
		return {
			"ok": False,
			"errors": {"reason": "A reason for removal is required."},
		}

	plan_name = cstr(plan).strip()
	item_name = cstr(plan_item).strip()
	if not plan_name or not frappe.db.exists("Procurement Plan", plan_name):
		frappe.throw(_("Procurement Plan not found."), title="PLN_PLAN_NOT_FOUND")
	if not item_name or not frappe.db.exists("Procurement Plan Item", item_name):
		frappe.throw(_("Plan Item not found."), title="PLN_ITEM_NOT_FOUND")

	plan_doc = frappe.get_doc("Procurement Plan", plan_name)
	assert_planning_scope(
		procuring_entity=cstr(plan_doc.procuring_entity).strip(),
		org_unit=cstr(plan_doc.coordinating_org_unit or "").strip() or None,
		user=actor,
		require_write=True,
	)
	item = frappe.get_doc("Procurement Plan Item", item_name)
	if cstr(item.plan) != plan_name:
		frappe.throw(_("Plan Item does not belong to this Plan."), title="PLN_ITEM_NOT_IN_PLAN")

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

	if state == ITEM_ACTIVE and not draft:
		from kentender_procurement.procurement_planning.services.open_or_create_plan_revision import (
			open_or_create_plan_revision,
		)

		rev = open_or_create_plan_revision(plan=plan_name, user=actor)
		draft = rev["version"]
		plan_doc.reload()

	if not draft:
		frappe.throw(
			_("Open a Draft version before removing a Plan Item."),
			title="PLN_NO_DRAFT_VERSION",
		)

	assert_version_concurrency(draft, concurrency_token)
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

	no_changes = not draft_has_effective_changes(plan=plan_name, version=draft)
	return {
		"ok": True,
		"idempotent": False,
		"mode": mode,
		"plan": plan_name,
		"plan_item": item_name,
		"version": draft,
		"no_changes_remain": no_changes,
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
