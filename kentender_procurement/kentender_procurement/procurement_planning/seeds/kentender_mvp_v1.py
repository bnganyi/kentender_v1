# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""KENTENDER_MVP_V1 Planning stage — Demo v2.7 §7.4 / §7.6 base state."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_procurement.procurement_planning.mvp1_constants import (
	ALLOC_EFFECTIVE,
	FINANCE_AWAITING,
	FINANCE_CONFIRMED,
	ITEM_ACTIVE,
	PLAN_OPEN,
	PLAN_TYPE_ANNUAL,
	TAKEUP_ACTIVE,
	VALIDATION_READY,
	VERSION_APPROVED,
)
from kentender_procurement.procurement_planning.services._invariants import (
	new_concurrency_token,
	period_dates_for_financial_year,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	ensure_planning_roles,
)

FY = "2027/28"
TITLE = "Ministry of Health Annual Procurement Plan FY 2027/28"


def _upsert(doctype: str, filters: dict[str, Any], values: dict[str, Any]) -> tuple[str, bool]:
	name = frappe.db.exists(doctype, filters)
	if name:
		# Prefer db.set_value so Approved versions / Active items stay immutable-safe.
		frappe.db.set_value(doctype, name, values, update_modified=False)
		return name, False
	doc = frappe.get_doc({"doctype": doctype, **filters, **values})
	doc.insert(ignore_permissions=True)
	return doc.name, True


def _set_fixture_namespace(doctype: str, names: list[str], namespace: str) -> None:
	if not names or not frappe.db.exists("DocType", doctype):
		return
	if not frappe.db.has_column(doctype, "fixture_namespace"):
		return
	for name in dict.fromkeys(names):
		if frappe.db.exists(doctype, name):
			frappe.db.set_value(
				doctype, name, "fixture_namespace", namespace, update_modified=False
			)


def mark_plan_graph_fixture(plan: str, namespace: str) -> None:
	"""Tag a complete Planning graph for deterministic fixture cleanup."""
	if not plan or not frappe.db.exists("Procurement Plan", plan):
		return
	versions = frappe.get_all(
		"Procurement Plan Version", filters={"plan": plan}, pluck="name"
	)
	items = frappe.get_all("Procurement Plan Item", filters={"plan": plan}, pluck="name")
	item_versions = []
	allocations = []
	for item in items:
		item_versions.extend(
			frappe.get_all(
				"Procurement Plan Item Version", filters={"plan_item": item}, pluck="name"
			)
		)
		allocations.extend(
			frappe.get_all(
				"Plan Demand Allocation", filters={"plan_item": item}, pluck="name"
			)
		)
	for doctype, names in (
		("Procurement Plan", [plan]),
		("Procurement Plan Version", versions),
		("Procurement Plan Item", items),
		("Procurement Plan Item Version", item_versions),
		("Plan Demand Allocation", allocations),
		(
			"Plan Decision",
			frappe.get_all(
				"Plan Decision", filters={"plan_version": ["in", versions]}, pluck="name"
			)
			if versions
			else [],
		),
		(
			"Plan Validation Result",
			frappe.get_all(
				"Plan Validation Result",
				filters={"plan_version": ["in", versions]},
				pluck="name",
			)
			if versions
			else [],
		),
		(
			"Publication Event",
			frappe.get_all(
				"Publication Event", filters={"plan_version": ["in", versions]}, pluck="name"
			)
			if versions
			else [],
		),
		(
			"Planning Handoff Snapshot",
			frappe.get_all("Planning Handoff Snapshot", filters={"plan": plan}, pluck="name")
			if frappe.db.exists("DocType", "Planning Handoff Snapshot")
			else [],
		),
	):
		_set_fixture_namespace(doctype, names, namespace)
	if frappe.db.exists("DocType", "Planning Consumption"):
		codes = frappe.get_all(
			"Procurement Plan Item", filters={"name": ["in", items]}, pluck="plan_item_code"
		) if items else []
		consumptions = frappe.get_all(
			"Planning Consumption", filters={"plan_item_code": ["in", codes]}, pluck="name"
		) if codes else []
		_set_fixture_namespace("Planning Consumption", consumptions, namespace)


def _delete_named(doctype: str, names: list[str], deleted: dict[str, int]) -> None:
	if not frappe.db.exists("DocType", doctype):
		return
	for name in dict.fromkeys(names):
		if not frappe.db.exists(doctype, name):
			continue
		frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
		deleted[doctype] = deleted.get(doctype, 0) + 1


def clear_planning_fixture_rows(
	*, include_canonical: bool = True, include_playwright: bool = True
) -> dict[str, int]:
	"""Delete only explicitly owned canonical and browser-test Planning graphs."""
	deleted: dict[str, int] = {}
	if not frappe.db.exists("DocType", "Procurement Plan"):
		return deleted

	namespaces = []
	if include_canonical:
		namespaces.extend((C.FIXTURE_NS, C.LEGACY_FIXTURE_NS))
	if include_playwright:
		namespaces.append(C.PLAYWRIGHT_FIXTURE_NS)
	plans: list[str] = []
	if include_canonical:
		plans.extend(
			frappe.get_all(
				"Procurement Plan",
				filters={"plan_code": C.PROCUREMENT_PLAN_CODE},
				pluck="name",
			)
		)
	if frappe.db.has_column("Procurement Plan", "fixture_namespace"):
		if namespaces:
			plans.extend(
				frappe.get_all(
					"Procurement Plan",
					filters={"fixture_namespace": ["in", namespaces]},
					pluck="name",
				)
			)
	if include_playwright:
		# Narrow legacy signatures used before Planning gained fixture_namespace.
		plans.extend(
			frappe.get_all(
				"Procurement Plan",
				filters={"plan_code": "PLN-MOH-UI-DRAFT-001"},
				pluck="name",
			)
		)
		plans.extend(
			frappe.get_all(
				"Procurement Plan",
				filters={"title": ["in", ["Gate01 Annual Plan", "UI-09 Approved Plan"]]},
				pluck="name",
			)
		)
		plans.extend(
			frappe.get_all(
				"Procurement Plan",
				filters={"title": ["like", "Playwright Create %"]},
				pluck="name",
			)
		)
	plans = list(dict.fromkeys(plans))
	versions: list[str] = []
	items: list[str] = []
	for plan in plans:
		versions.extend(
			frappe.get_all("Procurement Plan Version", filters={"plan": plan}, pluck="name")
		)
		items.extend(
			frappe.get_all("Procurement Plan Item", filters={"plan": plan}, pluck="name")
		)
	if namespaces:
		if frappe.db.has_column("Procurement Plan Version", "fixture_namespace"):
			versions.extend(
				frappe.get_all(
					"Procurement Plan Version",
					filters={"fixture_namespace": ["in", namespaces]},
					pluck="name",
				)
			)
		if frappe.db.has_column("Procurement Plan Item", "fixture_namespace"):
			items.extend(
				frappe.get_all(
					"Procurement Plan Item",
					filters={"fixture_namespace": ["in", namespaces]},
					pluck="name",
				)
			)
	if include_canonical:
		items.extend(
			frappe.get_all(
				"Procurement Plan Item",
				filters={"plan_item_code": ["in", [C.PLAN_ITEM_CODE, C.PLAN_ITEM_CODE_SCN]]},
				pluck="name",
			)
		)
	items = list(dict.fromkeys(items))
	versions = list(dict.fromkeys(versions))
	item_codes = (
		frappe.get_all(
			"Procurement Plan Item",
			filters={"name": ["in", items]},
			pluck="plan_item_code",
		)
		if items
		else []
	)
	item_versions = (
		frappe.get_all(
			"Procurement Plan Item Version",
			filters={"plan_item": ["in", items]},
			pluck="name",
		)
		if items
		else []
	)
	if frappe.db.exists("DocType", "Workflow Task"):
		workflow_tasks = []
		if versions:
			workflow_tasks.extend(
				frappe.get_all(
					"Workflow Task",
					filters={
						"subject_type": "Procurement Plan Version",
						"subject_id": ["in", versions],
					},
					pluck="name",
				)
			)
		if item_versions:
			workflow_tasks.extend(
				frappe.get_all(
					"Workflow Task",
					filters={
						"subject_type": "Procurement Plan Item Version",
						"subject_id": ["in", item_versions],
					},
					pluck="name",
				)
			)
		_delete_named("Workflow Task", workflow_tasks, deleted)

	if frappe.db.exists("DocType", "Planning Consumption"):
		consumptions = (
			frappe.get_all(
				"Planning Consumption",
				filters={"plan_item_code": ["in", item_codes]},
				pluck="name",
			)
			if item_codes
			else []
		)
		if namespaces and frappe.db.has_column("Planning Consumption", "fixture_namespace"):
			consumptions.extend(
				frappe.get_all(
					"Planning Consumption",
					filters={"fixture_namespace": ["in", namespaces]},
					pluck="name",
				)
			)
		_delete_named("Planning Consumption", consumptions, deleted)

	for doctype in ("Plan Decision", "Plan Validation Result", "Publication Event"):
		names = (
			frappe.get_all(doctype, filters={"plan_version": ["in", versions]}, pluck="name")
			if versions and frappe.db.exists("DocType", doctype)
			else []
		)
		if namespaces and frappe.db.has_column(doctype, "fixture_namespace"):
			names.extend(
				frappe.get_all(
					doctype,
					filters={"fixture_namespace": ["in", namespaces]},
					pluck="name",
				)
			)
		_delete_named(doctype, names, deleted)
	for doctype in ("Planning Handoff Snapshot",):
		names = []
		if frappe.db.exists("DocType", doctype):
			if plans:
				names.extend(frappe.get_all(doctype, filters={"plan": ["in", plans]}, pluck="name"))
			if items:
				names.extend(frappe.get_all(doctype, filters={"plan_item": ["in", items]}, pluck="name"))
			if namespaces and frappe.db.has_column(doctype, "fixture_namespace"):
				names.extend(
					frappe.get_all(
						doctype,
						filters={"fixture_namespace": ["in", namespaces]},
						pluck="name",
					)
				)
		_delete_named(doctype, names, deleted)
	for doctype in ("Plan Demand Allocation", "Procurement Plan Item Version"):
		names = (
			frappe.get_all(doctype, filters={"plan_item": ["in", items]}, pluck="name")
			if items
			else []
		)
		if namespaces and frappe.db.has_column(doctype, "fixture_namespace"):
			names.extend(
				frappe.get_all(
					doctype,
					filters={"fixture_namespace": ["in", namespaces]},
					pluck="name",
				)
			)
		_delete_named(doctype, names, deleted)

	for item in items:
		if frappe.db.exists("Procurement Plan Item", item):
			frappe.db.set_value(
				"Procurement Plan Item",
				item,
				{"current_approved_item_version": None, "draft_item_version": None},
				update_modified=False,
			)
	_delete_named("Procurement Plan Item", items, deleted)
	for plan in plans:
		if frappe.db.exists("Procurement Plan", plan):
			frappe.db.set_value(
				"Procurement Plan",
				plan,
				{"current_approved_version": None, "open_draft_version": None},
				update_modified=False,
			)
	for version in versions:
		if frappe.db.exists("Procurement Plan Version", version):
			frappe.db.set_value(
				"Procurement Plan Version", version, "source_version", None, update_modified=False
			)
	_delete_named("Procurement Plan Version", versions, deleted)
	_delete_named("Procurement Plan", plans, deleted)
	return deleted


def _purge_orphan_canonical_rsv(*, keep: str = "") -> None:
	"""Remove leftover Budget-era RSV-MOH-0001 so Finance can create the live identity."""
	keep = cstr(keep).strip()
	for name in frappe.get_all(
		"Funding Reservation",
		filters={"generated_reference": C.RSV_CODE},
		pluck="name",
	):
		if keep and name == keep:
			continue
		coms = []
		if frappe.db.exists("DocType", "Procurement Commitment"):
			coms = frappe.get_all(
				"Procurement Commitment", {"reservation": name}, pluck="name"
			)
		if frappe.db.exists("DocType", "Expenditure Snapshot"):
			for com in coms:
				for exp in frappe.get_all(
					"Expenditure Snapshot", {"commitment": com}, pluck="name"
				):
					frappe.delete_doc(
						"Expenditure Snapshot", exp, force=1, ignore_permissions=True
					)
		for com in coms:
			frappe.delete_doc(
				"Procurement Commitment", com, force=1, ignore_permissions=True
			)
		frappe.delete_doc("Funding Reservation", name, force=1, ignore_permissions=True)


def _ensure_v1_finance_and_handoff(
	*,
	plan_name: str,
	version_name: str,
	item_name: str,
	iv_name: str,
	demand: str,
) -> None:
	"""Post-Planning Finance on V1 + immutable TND-MOH-2027-008 handoff (no TM2 Tender)."""
	from kentender_procurement.procurement_planning.services.create_planning_handoff_snapshot import (
		create_planning_handoff_snapshot,
	)
	from kentender_procurement.procurement_planning.services.plan_item_finance import (
		confirm_plan_item_funding,
		effective_finance_status,
		request_plan_item_finance,
	)

	owned = cstr(
		frappe.db.get_value("Procurement Plan Item Version", iv_name, "finance_reservation") or ""
	)
	_purge_orphan_canonical_rsv(keep=owned)

	status = effective_finance_status(frappe.get_doc("Procurement Plan Item Version", iv_name))
	if status != FINANCE_CONFIRMED:
		frappe.db.set_value(
			"Procurement Plan Item Version",
			iv_name,
			{"finance_status": "Not requested"},
			update_modified=False,
		)
		requested = request_plan_item_finance(plan_item=item_name, user=C.USER_PLANNING_OFFICER)
		confirmed = confirm_plan_item_funding(
			task=requested.get("task"),
			expected_token=requested.get("task_token"),
			idempotency_key=f"SEED-FINANCE-{iv_name}",
			user=C.USER_BUD_OFFICER,
		)
		if not confirmed.get("ok"):
			raise frappe.ValidationError(f"Planning seed Finance confirm failed: {confirmed}")
		code = cstr(confirmed.get("reservation") or "")
		if code and code != C.RSV_CODE:
			# Prefer the canonical business code when reserve_funding returned a name.
			gen = frappe.db.get_value(
				"Funding Reservation",
				{"generated_reference": C.RSV_CODE},
				"generated_reference",
			)
			if not gen:
				rsv_name = frappe.db.get_value(
					"Funding Reservation",
					{"name": code},
					"name",
				)
				if rsv_name:
					frappe.db.set_value(
						"Funding Reservation",
						rsv_name,
						{"generated_reference": C.RSV_CODE},
						update_modified=False,
					)

	handoff = create_planning_handoff_snapshot(
		plan_item=item_name,
		tender_reference=C.TENDER_CODE,
		user=C.USER_TENDER_INITIATOR,
	)
	if not handoff.get("ok"):
		raise frappe.ValidationError(f"Planning seed handoff failed: {handoff}")


def upsert_planning_base(*, commit: bool = True) -> dict[str, Any]:
	"""Idempotent base Planning state: Approved V1 + Active PPI-MOH-2027-021 @ 455M."""
	frappe.only_for(("System Manager", "Administrator"))
	ensure_planning_roles()

	if not frappe.db.exists("DocType", "Procurement Plan"):
		return {"ok": False, "reason": "Procurement Plan DocType unavailable"}

	demand = frappe.db.get_value("Demand", {"demand_code": C.DEMAND_CODE}, "name")
	if not demand:
		raise frappe.ValidationError(
			f"Planning seed requires Demand {C.DEMAND_CODE} (run full KENTENDER_MVP_V1 seed first)"
		)

	pe = C.PE_MOH
	ou = C.OU_DIR_DHP
	period_start, period_end = period_dates_for_financial_year(FY)
	approved_at = C.FIXTURE_NOW_STR

	plan_name, plan_created = _upsert(
		"Procurement Plan",
		{"plan_code": C.PROCUREMENT_PLAN_CODE},
		{
			"title": TITLE,
			"procuring_entity": pe,
			"financial_year": FY,
			"period_start": period_start,
			"period_end": period_end,
			"currency": "KES",
			"plan_type": PLAN_TYPE_ANNUAL,
			"lifecycle_state": PLAN_OPEN,
			"fixture_namespace": C.FIXTURE_NS,
		},
	)

	version_name, version_created = _upsert(
		"Procurement Plan Version",
		{"version_code": C.PROCUREMENT_PLAN_VERSION_CODE},
		{
			"plan": plan_name,
			"version_number": 1,
			"status": VERSION_APPROVED,
			"version_reason": "Canonical Approved Version 1",
			"validation_projection": VALIDATION_READY,
			"effective_at": approved_at,
			"approved_by": C.USER_HOP,
			"approved_at": approved_at,
			"concurrency_token": new_concurrency_token(),
			"fixture_namespace": C.FIXTURE_NS,
		},
	)

	# Remove SCN artefact version/item if present (base seed)
	for code in (C.PROCUREMENT_PLAN_VERSION_V2,):
		if frappe.db.exists("Procurement Plan Version", {"version_code": code}):
			ver = frappe.db.get_value("Procurement Plan Version", {"version_code": code}, "name")
			for name in frappe.get_all(
				"Plan Decision", filters={"plan_version": ver}, pluck="name"
			):
				frappe.delete_doc("Plan Decision", name, force=1, ignore_permissions=True)
			for name in frappe.get_all(
				"Procurement Plan Item Version",
				filters={"plan_version": ver},
				pluck="name",
			):
				frappe.delete_doc(
					"Procurement Plan Item Version", name, force=1, ignore_permissions=True
				)
			for name in frappe.get_all(
				"Plan Demand Allocation",
				filters={"proposed_in_version": ver},
				pluck="name",
			):
				frappe.delete_doc(
					"Plan Demand Allocation", name, force=1, ignore_permissions=True
				)
			frappe.delete_doc("Procurement Plan Version", ver, force=1, ignore_permissions=True)

	if frappe.db.exists("Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE_SCN}):
		scn_item = frappe.db.get_value(
			"Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE_SCN}, "name"
		)
		for doctype in ("Plan Demand Allocation", "Procurement Plan Item Version"):
			for name in frappe.get_all(doctype, filters={"plan_item": scn_item}, pluck="name"):
				frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
		if frappe.db.exists("DocType", "Planning Consumption"):
			for name in frappe.get_all(
				"Planning Consumption",
				filters={"plan_item_code": C.PLAN_ITEM_CODE_SCN},
				pluck="name",
			):
				frappe.delete_doc("Planning Consumption", name, force=1, ignore_permissions=True)
		frappe.delete_doc("Procurement Plan Item", scn_item, force=1, ignore_permissions=True)

	item_name, item_created = _upsert(
		"Procurement Plan Item",
		{"plan_item_code": C.PLAN_ITEM_CODE},
		{
			"plan": plan_name,
			"procuring_entity": pe,
			"owner_org_unit": ou,
			"delivery_org_unit": ou,
			"baseline_state": ITEM_ACTIVE,
			"tender_takeup_projection": TAKEUP_ACTIVE,
			"fixture_namespace": C.FIXTURE_NS,
		},
	)

	iv_code = f"{C.PLAN_ITEM_CODE}-1"
	iv_name, iv_created = _upsert(
		"Procurement Plan Item Version",
		{"item_version_code": iv_code},
		{
			"plan_item": item_name,
			"plan_version": version_name,
			"carry_forward_unchanged": 0,
			"requirement_title": "National digital health infrastructure upgrade",
			"requirement_description": (
				"Upgrade resilient compute, storage, network and monitoring infrastructure "
				"supporting national digital health services."
			),
			"confirmed_estimate": C.PLAN_AMOUNT_V1,
			"currency": "KES",
			"procurement_category": "ICT infrastructure and services",
			"procurement_method": "Open tender",
			"arrangement": "Single year",
			"lotting_decision": "Single lot",
			"ms_invitation_published": "2027-09-15",
			"ms_tender_opening": "2027-10-20",
			"ms_evaluation_completed": "2027-11-15",
			"ms_award_approval": "2027-12-15",
			"ms_notification_of_award": "2027-12-20",
			"ms_contract_signature": "2028-01-15",
			"ms_delivery_completion": "2028-03-31",
			"finance_snapshot_amount": C.PLAN_AMOUNT_V1,
			"validation_projection": VALIDATION_READY,
			"fixture_namespace": C.FIXTURE_NS,
		},
	)
	from kentender_procurement.procurement_planning.services.add_demand_to_plan import (
		_strategy_snapshots,
	)

	strat, pvc = _strategy_snapshots([demand])
	if strat or pvc:
		updates: dict[str, str] = {}
		if strat and not cstr(
			frappe.db.get_value("Procurement Plan Item Version", iv_name, "strategy_snapshot")
			or ""
		).strip():
			updates["strategy_snapshot"] = strat
		if pvc and not cstr(
			frappe.db.get_value("Procurement Plan Item Version", iv_name, "pvc_snapshot") or ""
		).strip():
			updates["pvc_snapshot"] = pvc
		if updates:
			frappe.db.set_value(
				"Procurement Plan Item Version", iv_name, updates, update_modified=False
			)

	demand_items = frappe.get_all(
		"Demand Item",
		filters={"demand": demand},
		fields=["name", "confirmed_estimate", "confirmed_quantity", "quantity", "currency"],
		order_by="creation asc",
	)
	if not demand_items:
		raise frappe.ValidationError(f"Demand {C.DEMAND_CODE} has no Demand Items")

	# Replace allocations for this item to keep exact Demand-item pairing
	existing_allocs = frappe.get_all(
		"Plan Demand Allocation", filters={"plan_item": item_name}, pluck="name"
	)
	for name in existing_allocs:
		frappe.delete_doc("Plan Demand Allocation", name, force=1, ignore_permissions=True)

	alloc_names: list[str] = []
	total = 0.0
	for di in demand_items:
		amt = flt(di.confirmed_estimate)
		total += amt
		alloc = frappe.get_doc(
			{
				"doctype": "Plan Demand Allocation",
				"plan_item": item_name,
				"demand": demand,
				"demand_item": di.name,
				"source_org_unit": ou,
				"source_funding_allocation": frappe.db.get_value("Demand Funding Allocation", {"demand": demand}, "name"),
				"active_hold_key": di.name,
				"status": ALLOC_EFFECTIVE,
				"allocated_amount": amt,
				"currency": di.currency or "KES",
				"allocated_quantity": flt(di.confirmed_quantity or di.quantity),
				"proposed_in_version": version_name,
				"effective_from_version": version_name,
				"effective_at": approved_at,
				"fixture_namespace": C.FIXTURE_NS,
			}
		)
		alloc.insert(ignore_permissions=True)
		alloc_names.append(alloc.name)

		if frappe.db.exists("DocType", "Planning Consumption"):
			pc_filters = {
				"demand": demand,
				"demand_item": di.name,
				"plan_item_code": C.PLAN_ITEM_CODE,
			}
			existing_pc = frappe.db.exists("Planning Consumption", pc_filters)
			pc_values = {
				"consumed_amount": amt,
				"consumed_quantity": flt(di.confirmed_quantity or di.quantity),
				"currency": di.currency or "KES",
				"consumed_by": C.USER_PLANNING_OFFICER,
				"consumed_at": approved_at,
				"fixture_namespace": C.FIXTURE_NS,
			}
			if existing_pc:
				frappe.db.set_value(
					"Planning Consumption", existing_pc, pc_values, update_modified=False
				)
			else:
				frappe.get_doc(
					{"doctype": "Planning Consumption", **pc_filters, **pc_values}
				).insert(ignore_permissions=True)

	if abs(total - C.PLAN_AMOUNT_V1) > 0.01:
		raise frappe.ValidationError(
			f"Planning seed allocations total {total} != {C.PLAN_AMOUNT_V1}"
		)

	frappe.db.set_value(
		"Procurement Plan Item",
		item_name,
		{
			"baseline_state": ITEM_ACTIVE,
			"current_approved_item_version": iv_name,
			"draft_item_version": None,
			"tender_takeup_projection": TAKEUP_ACTIVE,
		},
		update_modified=False,
	)
	frappe.db.set_value(
		"Procurement Plan",
		plan_name,
		{
			"current_approved_version": version_name,
			"open_draft_version": None,
			"lifecycle_state": PLAN_OPEN,
		},
		update_modified=False,
	)

	# Decision evidence (idempotent: one Approval for V1)
	existing_decision = frappe.db.exists(
		"Plan Decision",
		{
			"plan_version": version_name,
			"decision_type": "Approval",
			"decision": "Approved",
		},
	)
	decision_created = False
	if not existing_decision:
		frappe.get_doc(
			{
				"doctype": "Plan Decision",
				"plan_version": version_name,
				"decision_type": "Approval",
				"decision_stage": "Plan Version Approval",
			"actor": C.USER_HOP,
				"actor_role": "Designated Approver",
				"decision": "Approved",
				"reason": "Canonical Approved Version 1",
				"decided_at": approved_at,
			}
		).insert(ignore_permissions=True)
		decision_created = True

	if frappe.db.has_column("Demand", "planning_usage"):
		frappe.db.set_value(
			"Demand",
			demand,
			"planning_usage",
			"Fully planned",
			update_modified=False,
		)

	_ensure_v1_finance_and_handoff(
		plan_name=plan_name,
		version_name=version_name,
		item_name=item_name,
		iv_name=iv_name,
		demand=demand,
	)
	mark_plan_graph_fixture(plan_name, C.FIXTURE_NS)

	if commit:
		frappe.db.commit()

	return {
		"ok": True,
		"plan": plan_name,
		"plan_code": C.PROCUREMENT_PLAN_CODE,
		"version": version_name,
		"version_code": C.PROCUREMENT_PLAN_VERSION_CODE,
		"plan_item": item_name,
		"plan_item_code": C.PLAN_ITEM_CODE,
		"allocations": alloc_names,
		"total": total,
		"created": {
			"plan": plan_created,
			"version": version_created,
			"item": item_created,
			"item_version": iv_created,
			"decision": decision_created,
		},
	}
