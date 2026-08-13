# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-004 — Add eligible Demand → Proposed Plan Item(s) + Draft allocations."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt

from kentender_procurement.procurement_planning.mvp1_constants import (
	ALLOC_DRAFT,
	DRAFT_CHANGE_ADDED,
	ITEM_PROPOSED,
	VALIDATION_NOT_RUN,
	VERSION_EDITABLE_STATUSES,
)
from kentender_procurement.procurement_planning.services._invariants import (
	assert_version_mutable,
	next_plan_item_code,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	assert_can_add_demand,
	assert_planning_scope,
	has_planning_scope,
)

# formation_mode (Pack v1.7): Demand-level separate|combined; legacy Need-Item modes retained.
FORMATION_ONE = "one_plan_item"
FORMATION_SEPARATE = "separate_per_need_item"
FORMATION_SEPARATE_DEMANDS = "separate"
FORMATION_COMBINED = "combined"
PACKAGE_ONE = FORMATION_ONE
PACKAGE_SEPARATE = FORMATION_SEPARATE

_VALID_MODES = (
	FORMATION_ONE,
	FORMATION_SEPARATE,
	FORMATION_SEPARATE_DEMANDS,
	FORMATION_COMBINED,
)


def _already_planned(demand: str) -> float:
	return flt(
		frappe.db.sql(
			"""
			select coalesce(sum(allocated_amount), 0) from `tabPlan Demand Allocation`
			where demand=%s and status in ('Draft', 'Effective')
			""",
			demand,
		)[0][0]
	)


def _demand_has_draft_allocation_in_version(demand: str, version: str) -> bool:
	return bool(
		frappe.db.sql(
			"""
			select a.name from `tabPlan Demand Allocation` a
			inner join `tabProcurement Plan Item` i on i.name = a.plan_item
			where a.demand = %s and a.status = %s and a.proposed_in_version = %s
			  and i.baseline_state = %s
			limit 1
			""",
			(demand, ALLOC_DRAFT, version, ITEM_PROPOSED),
		)
	)


def _assert_no_ungoverned_parallel(demand: str, draft: str) -> None:
	"""Anti-splitting: Demand must not already have Draft allocations on Proposed items."""
	if _demand_has_draft_allocation_in_version(demand, draft):
		frappe.throw(
			frappe._(
				"This Demand already has a Draft allocation on a Proposed Plan Item. "
				"Anti-splitting blocks parallel packages without a governed separation."
			),
			title="PLN_ANTI_SPLIT",
		)


def _build_allocations_spec(
	need_items: list[Any],
	*,
	available: float,
	allocated_amount: float | None,
) -> list[tuple[Any, float]]:
	if allocated_amount is not None and flt(allocated_amount) > 0:
		total_amount = flt(allocated_amount)
		if total_amount > available + 0.0001:
			frappe.throw(
				frappe._("Allocated amount exceeds approved available scope."),
				title="PLN_AMOUNT_EXCEEDS_AVAILABLE",
			)
		return [(need_items[0], total_amount)]

	allocations_spec: list[tuple[Any, float]] = []
	running = 0.0
	for di in need_items:
		amt = flt(di.confirmed_estimate or di.requester_estimate)
		if amt <= 0:
			continue
		if running + amt > available + 0.0001:
			amt = max(available - running, 0.0)
		if amt <= 0:
			continue
		allocations_spec.append((di, amt))
		running += amt
	return allocations_spec


def _create_plan_item_with_allocations(
	*,
	plan_doc: Any,
	ver: Any,
	demand_doc: Any,
	demand_name: str,
	ou: str,
	rsv_ref: str,
	title: str,
	currency: str,
	allocations_spec: list[tuple[Any, float]],
	aggregation_decision: str,
	aggregation_reason: str = "",
) -> dict[str, Any]:
	total_amount = sum(flt(a) for _, a in allocations_spec)
	plan_item_code = next_plan_item_code(plan_doc.plan_code)
	item = frappe.get_doc(
		{
			"doctype": "Procurement Plan Item",
			"plan": plan_doc.name,
			"plan_item_code": plan_item_code,
			"procuring_entity": plan_doc.procuring_entity,
			"owner_org_unit": ou or plan_doc.coordinating_org_unit,
			"delivery_org_unit": demand_doc.get("delivery_org_unit"),
			"baseline_state": ITEM_PROPOSED,
		}
	)
	item.insert(ignore_permissions=True)

	iv_code = f"{plan_item_code}-{ver.version_number}"
	item_version = frappe.get_doc(
		{
			"doctype": "Procurement Plan Item Version",
			"plan_item": item.name,
			"plan_version": ver.name,
			"item_version_code": iv_code,
			"carry_forward_unchanged": 0,
			"draft_change_label": (
				DRAFT_CHANGE_ADDED
				if cstr(plan_doc.current_approved_version or "").strip()
				else ""
			),
			"requirement_title": title,
			"requirement_description": cstr(demand_doc.get("need_statement") or "")[:500],
			"confirmed_estimate": total_amount,
			"currency": currency,
			"procurement_category": cstr(demand_doc.get("procurement_category") or ""),
			"governing_regime": "PPADA",
			"recommended_method": "Open tender",
			"procurement_method": "Open tender",
			"method_basis": "Open tender is the preferred method under PPADA.",
			"arrangement": "Single year",
			"aggregation_decision": aggregation_decision,
			"aggregation_reason": aggregation_reason,
			"lotting_decision": "Single lot",
			"expected_lot_count": 1,
			"reservation_reference": rsv_ref,
			"validation_projection": VALIDATION_NOT_RUN,
		}
	)
	item_version.insert(ignore_permissions=True)

	frappe.db.set_value(
		"Procurement Plan Item",
		item.name,
		{"draft_item_version": item_version.name},
		update_modified=False,
	)

	allocation_names: list[str] = []
	for di, amt in allocations_spec:
		alloc = frappe.get_doc(
			{
				"doctype": "Plan Demand Allocation",
				"plan_item": item.name,
				"demand": demand_name,
				"demand_item": di.name,
				"status": ALLOC_DRAFT,
				"allocated_amount": amt,
				"currency": cstr(di.currency or currency),
				"allocated_quantity": flt(di.confirmed_quantity or di.quantity),
				"proposed_in_version": ver.name,
				"reservation_reference": rsv_ref,
			}
		)
		alloc.insert(ignore_permissions=True)
		allocation_names.append(alloc.name)

	return {
		"plan_item": item.name,
		"plan_item_code": plan_item_code,
		"item_version": item_version.name,
		"allocations": allocation_names,
		"allocated_amount": total_amount,
	}


def add_demand_to_plan(
	*,
	plan: str,
	demand: str | None = None,
	demands: list[str] | str | None = None,
	demand_item: str | None = None,
	allocated_amount: float | None = None,
	package_mode: str | None = None,
	formation_mode: str | None = None,
	separation_reason: str | None = None,
	formation_reason: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	actor = assert_can_add_demand(user)
	plan_name = cstr(plan).strip()

	demand_list: list[str] = []
	if isinstance(demands, str) and demands.strip():
		raw = demands.strip()
		if raw.startswith("["):
			import json

			try:
				parsed = json.loads(raw)
			except json.JSONDecodeError:
				parsed = []
			if isinstance(parsed, list):
				demand_list = [cstr(x).strip() for x in parsed if cstr(x).strip()]
		else:
			demand_list = [x.strip() for x in raw.split(",") if x.strip()]
	elif isinstance(demands, (list, tuple)):
		demand_list = [cstr(x).strip() for x in demands if cstr(x).strip()]
	single = cstr(demand or "").strip()
	if single and single not in demand_list:
		demand_list.insert(0, single)
	# Deduplicate preserving order.
	seen: set[str] = set()
	ordered: list[str] = []
	for d in demand_list:
		if d not in seen:
			seen.add(d)
			ordered.append(d)
	demand_list = ordered

	mode = (
		cstr(formation_mode or package_mode or FORMATION_ONE).strip() or FORMATION_ONE
	)
	if len(demand_list) >= 2 and mode in (FORMATION_ONE, ""):
		mode = FORMATION_SEPARATE_DEMANDS
	if mode not in _VALID_MODES:
		frappe.throw(frappe._("Invalid formation mode."), title="PLN_FORMATION_MODE_INVALID")
	if not plan_name or not demand_list:
		frappe.throw(frappe._("Plan and Demand are required."), title="PLN_ADD_REQUIRED")

	# Multi Demand path (atomic Separate | Combine).
	if len(demand_list) >= 2 or mode in (FORMATION_SEPARATE_DEMANDS, FORMATION_COMBINED):
		return _add_multi_demands_to_plan(
			plan=plan_name,
			demand_names=demand_list,
			formation_mode=mode if mode in (FORMATION_SEPARATE_DEMANDS, FORMATION_COMBINED) else FORMATION_SEPARATE_DEMANDS,
			formation_reason=formation_reason or separation_reason,
			user=actor,
		)

	demand_name = demand_list[0]
	return _add_single_demand_to_plan(
		plan=plan_name,
		demand_name=demand_name,
		demand_item=demand_item,
		allocated_amount=allocated_amount,
		formation_mode=mode,
		separation_reason=separation_reason,
		user=actor,
	)


def _add_multi_demands_to_plan(
	*,
	plan: str,
	demand_names: list[str],
	formation_mode: str,
	formation_reason: str | None,
	user: str,
) -> dict[str, Any]:
	plan_doc = frappe.get_doc("Procurement Plan", plan)
	assert_planning_scope(
		procuring_entity=cstr(plan_doc.procuring_entity).strip(),
		org_unit=cstr(plan_doc.coordinating_org_unit or "").strip() or None,
		user=user,
		require_write=True,
	)
	draft = cstr(plan_doc.open_draft_version or "").strip()
	if not draft:
		from kentender_procurement.procurement_planning.services.open_or_create_plan_revision import (
			open_or_create_plan_revision,
		)

		rev = open_or_create_plan_revision(
			plan=plan,
			version_reason="Opened to add approved Demands",
			user=user,
		)
		draft = cstr(rev.get("version") or "").strip()
		plan_doc.reload()
	if not draft:
		frappe.throw(
			frappe._("Open a Draft revision before adding Demands."),
			title="PLN_NO_OPEN_DRAFT",
		)
	ver = frappe.get_doc("Procurement Plan Version", draft)
	assert_version_mutable(ver.status)
	if ver.status not in VERSION_EDITABLE_STATUSES:
		frappe.throw(
			frappe._("Only Draft or Returned versions accept new items."),
			title="PLN_VERSION_NOT_EDITABLE",
		)

	docs = []
	for name in demand_names:
		if not frappe.db.exists("Demand", name):
			frappe.throw(frappe._("Demand not found."), title="PLN_DEMAND_NOT_FOUND")
		docs.append(frappe.get_doc("Demand", name))

	pe = cstr(plan_doc.procuring_entity).strip()
	ous = {cstr(d.owner_org_unit or "").strip() for d in docs}
	cats = {cstr(d.procurement_category or "").strip() for d in docs}
	for demand_doc in docs:
		demand_pe = cstr(demand_doc.procuring_entity or "").strip()
		if demand_pe != pe:
			frappe.throw(
				frappe._("Demand Procuring Entity must match the Plan Procuring Entity."),
				title="PLN_CROSS_PE_ALLOCATION",
			)
		if cstr(demand_doc.status) != "Approved" or not int(demand_doc.planning_ready or 0):
			frappe.throw(
				frappe._("Only Approved, Planning Ready Demands can be added."),
				title="PLN_DEMAND_NOT_ELIGIBLE",
			)
		if cstr(demand_doc.planning_usage or "") == "Fully planned":
			frappe.throw(frappe._("Demand is fully planned."), title="PLN_DEMAND_FULLY_PLANNED")
		ou = cstr(demand_doc.owner_org_unit or "").strip()
		if not has_planning_scope(
			procuring_entity=demand_pe, org_unit=ou or None, user=user, require_write=True
		):
			frappe.throw(
				frappe._("Not permitted for this organisational scope"),
				frappe.PermissionError,
				title="PLN_SCOPE_DENIED",
			)
		_assert_no_ungoverned_parallel(demand_doc.name, draft)

	reason = cstr(formation_reason or "").strip()
	from kentender_procurement.procurement_planning.services.get_plan_update import (
		plan_canvas_routes,
	)

	builder_route = plan_canvas_routes(plan_doc)["builder_route"]

	if formation_mode == FORMATION_COMBINED:
		if len(ous) > 1 or len(cats) > 1:
			frappe.throw(
				frappe._(
					"These Demands have different owning Organisation Units and cannot be combined in MVP 1."
				),
				title="PLN_COMBINE_INCOMPATIBLE",
			)
		if not reason:
			frappe.throw(
				frappe._("A reason for combining is required."),
				title="PLN_FORMATION_REASON_REQUIRED",
			)
		# Build one Plan Item with allocations from every Demand.
		all_specs: list[tuple[Any, Any, float, str]] = []  # demand_doc, di, amt, rsv
		total = 0.0
		currency = cstr(plan_doc.currency or "KES")
		for demand_doc in docs:
			need_items = frappe.get_all(
				"Demand Item",
				filters={"demand": demand_doc.name},
				fields=[
					"name",
					"item_code",
					"confirmed_estimate",
					"requester_estimate",
					"currency",
					"confirmed_quantity",
					"quantity",
					"description",
				],
				order_by="creation asc",
			)
			if not need_items:
				frappe.throw(frappe._("Demand has no Demand Items."), title="PLN_NO_DEMAND_ITEM")
			approved = flt(demand_doc.confirmed_estimate or demand_doc.requester_estimate)
			available = max(approved - _already_planned(demand_doc.name), 0.0)
			spec = _build_allocations_spec(need_items, available=available, allocated_amount=None)
			rsv_ref = cstr(
				frappe.db.get_value(
					"Demand Funding Allocation",
					{"demand": demand_doc.name},
					"funding_reservation",
				)
				or ""
			)
			for di, amt in spec:
				all_specs.append((demand_doc, di, amt, rsv_ref))
				total += flt(amt)
				currency = cstr(di.currency or demand_doc.currency or currency)
		if total <= 0:
			frappe.throw(
				frappe._("No available amount remains to plan for these Demands."),
				title="PLN_AMOUNT_REQUIRED",
			)
		primary = docs[0]
		ou = cstr(primary.owner_org_unit or "").strip()
		# Create shell item then attach all allocations.
		plan_item_code = next_plan_item_code(plan_doc.plan_code)
		item = frappe.get_doc(
			{
				"doctype": "Procurement Plan Item",
				"plan": plan_doc.name,
				"plan_item_code": plan_item_code,
				"procuring_entity": plan_doc.procuring_entity,
				"owner_org_unit": ou or plan_doc.coordinating_org_unit,
				"delivery_org_unit": primary.get("delivery_org_unit"),
				"baseline_state": ITEM_PROPOSED,
			}
		)
		item.insert(ignore_permissions=True)
		title = cstr(primary.title or primary.demand_code or "Combined Plan Item")
		if len(docs) > 1:
			title = f"{title} (+{len(docs) - 1} sources)"
		iv_code = f"{plan_item_code}-{ver.version_number}"
		item_version = frappe.get_doc(
			{
				"doctype": "Procurement Plan Item Version",
				"plan_item": item.name,
				"plan_version": ver.name,
				"item_version_code": iv_code,
				"carry_forward_unchanged": 0,
				"draft_change_label": (
					DRAFT_CHANGE_ADDED
					if cstr(plan_doc.current_approved_version or "").strip()
					else ""
				),
				"requirement_title": title[:140],
				"requirement_description": cstr(primary.get("need_statement") or "")[:500],
				"confirmed_estimate": total,
				"currency": currency,
				"procurement_category": cstr(primary.get("procurement_category") or ""),
				"governing_regime": "PPADA",
				"recommended_method": "Open tender",
				"procurement_method": "Open tender",
				"method_basis": "Open tender is the preferred method under PPADA.",
				"arrangement": "Single year",
				"aggregation_decision": "Combine",
				"aggregation_reason": reason,
				"lotting_decision": "Single lot",
				"expected_lot_count": 1,
				"reservation_reference": all_specs[0][3] if all_specs else "",
				"validation_projection": VALIDATION_NOT_RUN,
			}
		)
		item_version.insert(ignore_permissions=True)
		frappe.db.set_value(
			"Procurement Plan Item",
			item.name,
			{"draft_item_version": item_version.name},
			update_modified=False,
		)
		allocation_names: list[str] = []
		for demand_doc, di, amt, rsv_ref in all_specs:
			alloc = frappe.get_doc(
				{
					"doctype": "Plan Demand Allocation",
					"plan_item": item.name,
					"demand": demand_doc.name,
					"demand_item": di.name,
					"status": ALLOC_DRAFT,
					"allocated_amount": amt,
					"currency": cstr(di.currency or currency),
					"allocated_quantity": flt(di.confirmed_quantity or di.quantity),
					"proposed_in_version": ver.name,
					"reservation_reference": rsv_ref,
					"reason": reason,
				}
			)
			alloc.insert(ignore_permissions=True)
			allocation_names.append(alloc.name)
		return {
			"ok": True,
			"formation_mode": FORMATION_COMBINED,
			"package_mode": FORMATION_COMBINED,
			"plan": plan,
			"plan_item": item.name,
			"plan_item_code": plan_item_code,
			"item_version": item_version.name,
			"plan_items": [item.name],
			"allocation": allocation_names[0] if allocation_names else None,
			"allocations": allocation_names,
			"allocation_status": ALLOC_DRAFT,
			"allocated_amount": total,
			"builder_route": builder_route,
			"editor_route": f"/app/procurement-plan-item-editor?plan_item={item.name}",
			"actor": user,
		}

	# Separate: one Plan Item per Demand (reuse single-demand helper sequentially).
	created: list[dict[str, Any]] = []
	for demand_name in demand_names:
		created.append(
			_add_single_demand_to_plan(
				plan=plan,
				demand_name=demand_name,
				demand_item=None,
				allocated_amount=None,
				formation_mode=FORMATION_ONE,
				separation_reason="",
				user=user,
			)
		)
	plan_items = [c["plan_item"] for c in created]
	all_allocs: list[str] = []
	for c in created:
		all_allocs.extend(c.get("allocations") or [])
	return {
		"ok": True,
		"formation_mode": FORMATION_SEPARATE_DEMANDS,
		"package_mode": FORMATION_SEPARATE_DEMANDS,
		"plan": plan,
		"plan_item": plan_items[0],
		"plan_item_code": created[0].get("plan_item_code"),
		"item_version": created[0].get("item_version"),
		"plan_items": plan_items,
		"allocation": all_allocs[0] if all_allocs else None,
		"allocations": all_allocs,
		"allocation_status": ALLOC_DRAFT,
		"allocated_amount": sum(flt(c.get("allocated_amount")) for c in created),
		"builder_route": builder_route,
		"editor_route": None,
		"actor": user,
	}


def _add_single_demand_to_plan(
	*,
	plan: str,
	demand_name: str,
	demand_item: str | None,
	allocated_amount: float | None,
	formation_mode: str,
	separation_reason: str | None,
	user: str,
) -> dict[str, Any]:
	mode = formation_mode
	plan_name = plan
	actor = user
	if mode not in (FORMATION_ONE, FORMATION_SEPARATE):
		frappe.throw(frappe._("Invalid formation mode."), title="PLN_FORMATION_MODE_INVALID")

	plan_doc = frappe.get_doc("Procurement Plan", plan_name)
	assert_planning_scope(
		procuring_entity=cstr(plan_doc.procuring_entity).strip(),
		org_unit=cstr(plan_doc.coordinating_org_unit or "").strip() or None,
		user=actor,
		require_write=True,
	)
	# REQ: selecting Add to plan creates or opens the single Draft revision
	# (PLN-FR-012 / PLN-FR-018). Do not force a separate "open draft" step.
	draft = cstr(plan_doc.open_draft_version or "").strip()
	if not draft:
		from kentender_procurement.procurement_planning.services.open_or_create_plan_revision import (
			open_or_create_plan_revision,
		)

		rev = open_or_create_plan_revision(
			plan=plan_name,
			version_reason="Opened to add approved Demand",
			user=actor,
		)
		draft = cstr(rev.get("version") or "").strip()
		plan_doc.reload()
	if not draft:
		frappe.throw(
			frappe._("Open a Draft revision before adding Demands."),
			title="PLN_NO_OPEN_DRAFT",
		)
	ver = frappe.get_doc("Procurement Plan Version", draft)
	assert_version_mutable(ver.status)
	if ver.status not in VERSION_EDITABLE_STATUSES:
		frappe.throw(
			frappe._("Only Draft or Returned versions accept new items."),
			title="PLN_VERSION_NOT_EDITABLE",
		)

	if not frappe.db.exists("Demand", demand_name):
		frappe.throw(frappe._("Demand not found."), title="PLN_DEMAND_NOT_FOUND")
	demand_doc = frappe.get_doc("Demand", demand_name)
	demand_pe = cstr(demand_doc.procuring_entity or "").strip()
	if demand_pe != cstr(plan_doc.procuring_entity).strip():
		frappe.throw(
			frappe._("Demand Procuring Entity must match the Plan Procuring Entity."),
			title="PLN_CROSS_PE_ALLOCATION",
		)
	if cstr(demand_doc.status) != "Approved" or not int(demand_doc.planning_ready or 0):
		frappe.throw(
			frappe._("Only Approved, Planning Ready Demands can be added."),
			title="PLN_DEMAND_NOT_ELIGIBLE",
		)
	if cstr(demand_doc.planning_usage or "") == "Fully planned":
		frappe.throw(frappe._("Demand is fully planned."), title="PLN_DEMAND_FULLY_PLANNED")

	ou = cstr(demand_doc.owner_org_unit or "").strip()
	if not has_planning_scope(
		procuring_entity=demand_pe, org_unit=ou or None, user=actor, require_write=True
	):
		frappe.throw(
			frappe._("Not permitted for this organisational scope"),
			frappe.PermissionError,
			title="PLN_SCOPE_DENIED",
		)

	# Snapshot Demand fields — never mutate Demand / RSV / Budget.
	demand_snapshot = {
		"status": demand_doc.status,
		"planning_usage": demand_doc.planning_usage,
		"confirmed_estimate": demand_doc.confirmed_estimate,
		"modified": str(demand_doc.modified),
	}
	rsv_before = frappe.db.get_value(
		"Demand Funding Allocation",
		{"demand": demand_name},
		["name", "funding_reservation", "allocation_amount"],
		as_dict=True,
	)

	need_items = frappe.get_all(
		"Demand Item",
		filters={"demand": demand_name},
		fields=[
			"name",
			"item_code",
			"confirmed_estimate",
			"requester_estimate",
			"currency",
			"confirmed_quantity",
			"quantity",
			"description",
		],
		order_by="creation asc",
	)
	if not need_items:
		frappe.throw(frappe._("Demand has no Demand Items."), title="PLN_NO_DEMAND_ITEM")

	# Optional single Demand Item path (Gate 01 compat).
	only_item = cstr(demand_item or "").strip()
	if only_item:
		need_items = [n for n in need_items if n.name == only_item]
		if not need_items:
			frappe.throw(frappe._("Demand Item not found."), title="PLN_DEMAND_ITEM_NOT_FOUND")

	approved = flt(demand_doc.confirmed_estimate or demand_doc.requester_estimate)
	already = _already_planned(demand_name)
	available = max(approved - already, 0.0)

	_assert_no_ungoverned_parallel(demand_name, draft)

	sep_reason = cstr(separation_reason or "").strip()
	if mode == FORMATION_SEPARATE:
		if len(need_items) < 2 and not only_item:
			# Single need item: treat as one Plan Item.
			mode = FORMATION_ONE
		elif not sep_reason:
			frappe.throw(
				frappe._("A separation reason is required to create separate Plan Items."),
				title="PLN_SEPARATION_REASON_REQUIRED",
			)

	allocations_spec = _build_allocations_spec(
		need_items, available=available, allocated_amount=allocated_amount
	)
	total_amount = sum(flt(a) for _, a in allocations_spec)
	if total_amount <= 0:
		frappe.throw(
			frappe._("No available amount remains to plan for this Demand."),
			title="PLN_AMOUNT_REQUIRED",
		)

	currency = cstr(
		need_items[0].currency or demand_doc.currency or plan_doc.currency or "KES"
	)
	base_title = cstr(demand_doc.title or demand_doc.demand_code or "Plan Item")
	rsv_ref = cstr((rsv_before.funding_reservation if rsv_before else "") or "")
	from kentender_procurement.procurement_planning.services.get_plan_update import (
		plan_canvas_routes,
	)

	builder_route = plan_canvas_routes(plan_doc)["builder_route"]

	# Pack v1.3: ordinary one-Demand path stores no aggregation metadata.
	# Separate creates real N Plan Items + division reason — never "Keep separate".
	created: list[dict[str, Any]] = []
	if mode == FORMATION_SEPARATE:
		for di, amt in allocations_spec:
			suffix = cstr(di.description or di.item_code or di.name)
			title = f"{base_title} — {suffix}" if suffix else base_title
			created.append(
				_create_plan_item_with_allocations(
					plan_doc=plan_doc,
					ver=ver,
					demand_doc=demand_doc,
					demand_name=demand_name,
					ou=ou,
					rsv_ref=rsv_ref,
					title=title[:140],
					currency=cstr(di.currency or currency),
					allocations_spec=[(di, amt)],
					aggregation_decision="",
					aggregation_reason=sep_reason,
				)
			)
	else:
		created.append(
			_create_plan_item_with_allocations(
				plan_doc=plan_doc,
				ver=ver,
				demand_doc=demand_doc,
				demand_name=demand_name,
				ou=ou,
				rsv_ref=rsv_ref,
				title=base_title,
				currency=currency,
				allocations_spec=allocations_spec,
				aggregation_decision="",
				aggregation_reason="",
			)
		)

	# Prove no upstream mutation.
	demand_after = frappe.db.get_value(
		"Demand",
		demand_name,
		["status", "planning_usage", "confirmed_estimate", "modified"],
		as_dict=True,
	)
	if (
		cstr(demand_after.status) != demand_snapshot["status"]
		or cstr(demand_after.planning_usage) != cstr(demand_snapshot["planning_usage"])
		or flt(demand_after.confirmed_estimate) != flt(demand_snapshot["confirmed_estimate"])
	):
		frappe.throw(
			frappe._("Upstream Demand was mutated during planning add — aborted."),
			title="PLN_UPSTREAM_MUTATION",
		)

	plan_items = [c["plan_item"] for c in created]
	first = created[0]
	all_allocs: list[str] = []
	for c in created:
		all_allocs.extend(c["allocations"])

	out: dict[str, Any] = {
		"ok": True,
		"formation_mode": mode,
		"package_mode": mode,  # alias for existing clients
		"plan": plan_name,
		"plan_item": first["plan_item"],
		"plan_item_code": first["plan_item_code"],
		"item_version": first["item_version"],
		"plan_items": plan_items,
		"allocation": all_allocs[0] if all_allocs else None,
		"allocations": all_allocs,
		"allocation_status": ALLOC_DRAFT,
		"allocated_amount": sum(flt(c["allocated_amount"]) for c in created),
		"builder_route": builder_route,
		"actor": actor,
	}
	if mode == FORMATION_ONE and len(plan_items) == 1:
		out["editor_route"] = f"/app/procurement-plan-item-editor?plan_item={plan_items[0]}"
	else:
		out["editor_route"] = None
	return out
