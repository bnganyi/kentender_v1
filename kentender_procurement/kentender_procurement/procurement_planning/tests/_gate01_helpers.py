# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared fixtures for Gate 01 Planning tests (Gate 02 scope-aware)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import add_days, cstr, now_datetime

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_procurement.procurement_planning.services.planning_permissions import (
	ROLE_DESIGNATED_APPROVER,
	ROLE_PLANNER,
	ROLE_TENDER_INITIATOR,
	ROLE_VIEWER,
	ensure_planning_roles,
)

PE = "PE-MOH"
OU = "MOH-DIR-DHP"
FY = "2027/28"
PLANNER_ROLE = ROLE_PLANNER
PLANNER_USER = "pln.gate01.planner@test.local"
APPROVER_USER = "moh.procurement.authority@example.test"
INITIATOR_USER = "pln.gate01.initiator@test.local"
VIEWER_USER = "pln.gate01.viewer@test.local"


def _ensure_shared_authorization(
	*, user: str, profile_id: str, capabilities: tuple[str, ...],
	task_routes: tuple[tuple[str, str], ...] = (), financial_year: str = "",
) -> None:
	"""Create canonical Gate 02 assignment and routing fixtures for Planning tests."""
	profile_name = frappe.db.get_value("Capability Profile", {"profile_id": profile_id}, "name")
	if profile_name:
		frappe.db.set_value(
			"Capability Profile", profile_name,
			{"capabilities": json.dumps(list(capabilities)), "status": "Active"},
			update_modified=False,
		)
	else:
		profile_name = frappe.get_doc(
			{
				"doctype": "Capability Profile",
				"profile_id": profile_id,
				"profile_name": profile_id,
				"capabilities": json.dumps(list(capabilities)),
				"allows_entity_wide": 1,
				"status": "Active",
				"effective_from": add_days(now_datetime(), -1),
			}
		).insert(ignore_permissions=True).name
	assignment_filters = {
		"user_id": user,
		"capability_profile_id": profile_name,
		"procuring_entity_id": PE,
		"status": "Active",
	}
	assignment_id = f"OSA-{profile_id}"
	assignment_name = frappe.db.get_value(
		"Operational Scope Assignment", {"assignment_id": assignment_id}, "name"
	)
	if assignment_name:
		frappe.db.set_value(
			"Operational Scope Assignment", assignment_name,
			{
				**assignment_filters,
				"include_descendants": 1,
				"effective_from": add_days(now_datetime(), -1),
			},
			update_modified=False,
		)
	elif not frappe.db.exists("Operational Scope Assignment", assignment_filters):
		frappe.get_doc(
			{
				"doctype": "Operational Scope Assignment",
				"assignment_id": assignment_id,
				**assignment_filters,
				"include_descendants": 1,
				"effective_from": add_days(now_datetime(), -1),
				"assigned_by": "Administrator",
				"assigned_at": now_datetime(),
			}
		).insert(ignore_permissions=True)
	for task_type, capability in task_routes:
		rule_id = f"RTR-{task_type.replace('.', '-').upper()}-{profile_id}"
		rule_name = frappe.db.get_value(
			"Workflow Routing Rule", {"routing_rule_id": rule_id}, "name"
		)
		if rule_name:
			frappe.db.set_value(
				"Workflow Routing Rule", rule_name,
				{
					"required_capability": capability,
					"assignee_user_id": user,
					"priority": 100,
					"status": "Active",
				},
				update_modified=False,
			)
			continue
		frappe.get_doc(
			{
				"doctype": "Workflow Routing Rule",
				"routing_version_id": f"RTV-{task_type.replace('.', '-').upper()}-{profile_id}",
				"routing_rule_id": rule_id,
				"version": 1,
				"module_name": "Procurement Planning",
				"task_type": task_type,
				"procuring_entity_id": PE,
				"financial_year_id": financial_year or None,
				"required_capability": capability,
				"assignee_strategy": "Named user",
				"assignee_user_id": user,
				"priority": 100,
				"effective_from": add_days(now_datetime(), -1),
				"status": "Active",
				"approved_by": "Administrator",
				"approved_at": now_datetime(),
			}
		).insert(ignore_permissions=True)


def _ensure_usa(user: str, role: str, pe: str, org_unit: str | None) -> None:
	if not frappe.db.exists("DocType", "User Scope Assignment"):
		return
	filters = {
		"user": user,
		"role": role,
		"procuring_entity": pe,
		"organisation_unit": org_unit or "",
	}
	if frappe.db.exists("User Scope Assignment", filters):
		return
	frappe.get_doc(
		{
			"doctype": "User Scope Assignment",
			"user": user,
			"role": role,
			"procuring_entity": pe,
			"organisation_unit": org_unit or "",
			"include_descendants": 1 if org_unit else 0,
		}
	).insert(ignore_permissions=True)


def ensure_planner_user() -> str:
	ensure_planning_roles()
	if not frappe.db.exists("Role", PLANNER_ROLE):
		frappe.get_doc({"doctype": "Role", "role_name": PLANNER_ROLE}).insert(ignore_permissions=True)
	if not frappe.db.exists("User", PLANNER_USER):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": PLANNER_USER,
				"first_name": "Gate01",
				"last_name": "Planner",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		)
		user.insert(ignore_permissions=True)
	roles = {r.role for r in frappe.get_doc("User", PLANNER_USER).roles}
	if PLANNER_ROLE not in roles:
		frappe.get_doc("User", PLANNER_USER).add_roles(PLANNER_ROLE)
	_ensure_usa(PLANNER_USER, PLANNER_ROLE, PE, OU)
	# Registration and mixed-OU formation are PE-owned capabilities. Keep the
	# unit assignment for scoped row tests and add the explicit entity grant.
	_ensure_usa(PLANNER_USER, PLANNER_ROLE, PE, None)
	return PLANNER_USER


def ensure_tender_initiator() -> str:
	"""PLN-GAP-PERM-001 — Tender Initiator with PE/OU write for take-up tests."""
	ensure_planning_roles()
	if not frappe.db.exists("User", INITIATOR_USER):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": INITIATOR_USER,
				"first_name": "Gate01",
				"last_name": "Initiator",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	roles = {r.role for r in frappe.get_doc("User", INITIATOR_USER).roles}
	if ROLE_TENDER_INITIATOR not in roles:
		frappe.get_doc("User", INITIATOR_USER).add_roles(ROLE_TENDER_INITIATOR)
	_ensure_usa(INITIATOR_USER, ROLE_TENDER_INITIATOR, PE, OU)
	return INITIATOR_USER


def ensure_viewer_user() -> str:
	ensure_planning_roles()
	if not frappe.db.exists("User", VIEWER_USER):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": VIEWER_USER,
				"first_name": "Gate01",
				"last_name": "Viewer",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	roles = {r.role for r in frappe.get_doc("User", VIEWER_USER).roles}
	if ROLE_VIEWER not in roles:
		frappe.get_doc("User", VIEWER_USER).add_roles(ROLE_VIEWER)
	_ensure_usa(VIEWER_USER, ROLE_VIEWER, PE, OU)
	return VIEWER_USER


HOD_USER = "pln.gate01.hod@test.local"


def ensure_hod_user() -> str:
	from kentender_procurement.procurement_planning.services.planning_permissions import (
		ROLE_HOD,
	)

	ensure_planning_roles()
	if not frappe.db.exists("User", HOD_USER):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": HOD_USER,
				"first_name": "Gate01",
				"last_name": "HoD",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	roles = {r.role for r in frappe.get_doc("User", HOD_USER).roles}
	if ROLE_HOD not in roles:
		frappe.get_doc("User", HOD_USER).add_roles(ROLE_HOD)
	_ensure_usa(HOD_USER, ROLE_HOD, PE, OU)
	return HOD_USER


def complete_plan_item_for_signoff(*, plan_item: str, user: str) -> dict:
	"""Fill method/schedule so validate_plan projects Ready for the item."""
	from kentender_procurement.procurement_planning.services.update_plan_item import (
		update_plan_item,
	)

	plan_name = frappe.db.get_value("Procurement Plan Item", plan_item, "plan")
	plan_start = frappe.db.get_value("Procurement Plan", plan_name, "period_start")
	draft = frappe.db.get_value("Procurement Plan", plan_name, "open_draft_version")
	version_token = frappe.db.get_value("Procurement Plan Version", draft, "concurrency_token")
	return update_plan_item(
		plan_item=plan_item,
		user=user,
		expected_version_token=version_token,
		idempotency_key=f"TEST-COMPLETE-{plan_item}-{version_token}",
		fields={
			"requirement_description": "Procure one accredited digital-health certification programme, including training and examinations, for the FY 2027/28 workforce-development requirement.",
			"procurement_category": "Training and professional development services",
			"procurement_method": "Open tender",
			"arrangement": "Single year",
			"lotting_decision": "Single lot",
			"ms_invitation_published": str(add_days(plan_start, 130)),
			"ms_tender_opening": str(add_days(plan_start, 151)),
			"ms_evaluation_completed": str(add_days(plan_start, 160)),
			"ms_award_approval": str(add_days(plan_start, 165)),
			"ms_notification_of_award": str(add_days(plan_start, 167)),
			"ms_contract_signature": str(add_days(plan_start, 172)),
			"ms_delivery_completion": str(add_days(plan_start, 183)),
		},
	)


def ensure_approver_user() -> str:
	ensure_planning_roles()
	for name in frappe.get_all(
		"User Scope Assignment",
		filters={"user": "pln.gate01.approver@test.local", "role": ROLE_DESIGNATED_APPROVER, "procuring_entity": PE},
		pluck="name",
	):
		frappe.delete_doc("User Scope Assignment", name, force=True, ignore_permissions=True)
	if not frappe.db.exists("User", APPROVER_USER):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": APPROVER_USER,
				"first_name": "Gate01",
				"last_name": "Approver",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	roles = {r.role for r in frappe.get_doc("User", APPROVER_USER).roles}
	if ROLE_DESIGNATED_APPROVER not in roles:
		frappe.get_doc("User", APPROVER_USER).add_roles(ROLE_DESIGNATED_APPROVER)
	_ensure_usa(APPROVER_USER, ROLE_DESIGNATED_APPROVER, PE, None)
	_ensure_shared_authorization(
		user=APPROVER_USER,
		profile_id="CP-PLN-G01-APPROVER",
		capabilities=("plan.approve", "plan.return"),
		task_routes=(("plan.approve", "plan.approve"),),
	)
	return APPROVER_USER


REVIEWER_USER = "pln.gate01.reviewer@test.local"


def ensure_reviewer_user() -> str:
	from kentender_procurement.procurement_planning.services.planning_permissions import (
		ROLE_REVIEWER,
	)

	ensure_planning_roles()
	if not frappe.db.exists("User", REVIEWER_USER):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": REVIEWER_USER,
				"first_name": "Gate01",
				"last_name": "Reviewer",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	roles = {r.role for r in frappe.get_doc("User", REVIEWER_USER).roles}
	if ROLE_REVIEWER not in roles:
		frappe.get_doc("User", REVIEWER_USER).add_roles(ROLE_REVIEWER)
	_ensure_usa(REVIEWER_USER, ROLE_REVIEWER, PE, None)
	_ensure_shared_authorization(
		user=REVIEWER_USER,
		profile_id="CP-PLN-G01-REVIEWER",
		capabilities=("plan.review", "plan.recommend", "plan.return"),
		task_routes=(("plan.review", "plan.review"),),
	)
	return REVIEWER_USER


def confirm_included_items_funding(*, plan: str, planner: str | None = None) -> None:
	"""Attach funding, request Finance, and confirm every included Plan Item (Gate 05)."""
	from frappe.utils import flt

	from kentender_procurement.procurement_planning.services.plan_item_finance import (
		_source_demand_row,
		confirm_plan_item_funding,
		effective_finance_status,
	)
	from kentender_procurement.procurement_planning.services.update_plan_item import (
		update_plan_item,
	)
	from kentender_procurement.procurement_planning.mvp1_constants import (
		FINANCE_AWAITING,
		FINANCE_CONFIRMED,
		FINANCE_STALE,
	)

	actor = planner or ensure_planner_user()
	ensure_budget_officer_user()
	draft = frappe.db.get_value("Procurement Plan", plan, "open_draft_version")
	items = frappe.get_all(
		"Procurement Plan Item Version",
		filters={"plan_version": draft},
		pluck="plan_item",
	) if draft else []
	for plan_item in items:
		complete_plan_item_for_signoff(plan_item=plan_item, user=actor)
		iv_name = frappe.db.get_value(
			"Procurement Plan Item", plan_item, "draft_item_version"
		)
		if not iv_name:
			continue
		iv = frappe.get_doc("Procurement Plan Item Version", iv_name)
		if effective_finance_status(iv) == FINANCE_CONFIRMED:
			continue
		demand_row = _source_demand_row(plan_item)
		demand = cstr(demand_row["demand"] if demand_row else "").strip()
		amount = flt(iv.confirmed_estimate) or 1_000_000
		if demand and not frappe.db.exists("Demand Funding Allocation", {"demand": demand}):
			funding = make_test_budget_line(
				approved_amount=max(amount * 2, 10_000_000),
				plan=plan,
			)
			attach_demand_funding(
				demand=demand,
				budget_line=funding["budget_line"],
				budget=funding["budget"],
				amount=amount,
			)
		version_token = frappe.db.get_value(
			"Procurement Plan Version",
			frappe.db.get_value("Procurement Plan", plan, "open_draft_version"),
			"concurrency_token",
		)
		requested = update_plan_item(
			plan_item=plan_item, user=actor, request_finance=True,
			expected_version_token=version_token,
			idempotency_key=f"TEST-FINANCE-{plan_item}-{version_token}",
		)
		if not requested.get("ok"):
			raise frappe.ValidationError(f"Request finance failed: {requested}")
		iv.reload()
		status = effective_finance_status(iv)
		if status == FINANCE_CONFIRMED:
			continue
		if status not in (FINANCE_AWAITING, FINANCE_STALE):
			raise frappe.ValidationError(
				f"Request finance did not open a confirmation task: {requested}"
			)
		confirmed = confirm_plan_item_funding(
			task=iv.finance_task_id,
			expected_token=iv.finance_task_token,
			idempotency_key=f"TEST-CONFIRM-{iv.finance_task_id}",
			user=iv.finance_task_assignee,
		)
		if not confirmed.get("ok"):
			raise frappe.ValidationError(f"Confirm finance failed: {confirmed}")


def advance_draft_to_recommended(*, plan: str, version: str | None = None) -> dict[str, Any]:
	"""Complete items, confirm Finance, validate, and create the professional task."""
	from kentender_procurement.procurement_planning.services.submit_plan_for_review import (
		submit_plan_for_review,
	)
	from kentender_procurement.procurement_planning.services.validate_plan import validate_plan
	from kentender_procurement.procurement_planning.services.record_plan_decision import (
		record_plan_decision,
	)

	planner = ensure_planner_user()
	reviewer = ensure_reviewer_user()
	ensure_approver_user()
	plan_doc = frappe.get_doc("Procurement Plan", plan)
	ver = cstr(version or plan_doc.open_draft_version or "").strip()
	if not ver:
		raise frappe.ValidationError("No open draft version to advance")

	items = frappe.get_all(
		"Procurement Plan Item",
		filters={"plan": plan, "baseline_state": ["in", ["Proposed", "Active"]]},
		pluck="name",
	)
	for item in items:
		complete_plan_item_for_signoff(plan_item=item, user=planner)

	confirm_included_items_funding(plan=plan, planner=planner)
	validate_plan(plan=plan, user=planner)

	if cstr(plan_doc.current_approved_version or "").strip():
		from kentender_procurement.procurement_planning.services.plan_builder_successor import (
			planner_update_reason,
		)

		if not planner_update_reason(
			frappe.db.get_value("Procurement Plan Version", ver, "version_reason")
		):
			frappe.db.set_value(
				"Procurement Plan Version",
				ver,
				"version_reason",
				"Test successor update after Approved Version",
				update_modified=False,
			)

	token = frappe.db.get_value("Procurement Plan Version", ver, "concurrency_token")
	submitted = submit_plan_for_review(
		plan=plan,
		expected_token=token,
		idempotency_key=f"TEST-SUBMIT-{ver}",
		user=planner,
	)
	if not submitted.get("ok"):
		raise frappe.ValidationError(f"Submit for review failed: {submitted}")
	recommended = record_plan_decision(
		version=ver,
		decision="recommend",
		concurrency_token=submitted.get("concurrency_token"),
		task=submitted.get("task"),
		expected_task_token=submitted.get("task_token"),
		user=submitted.get("assignee"),
	)
	if not recommended.get("ok"):
		raise frappe.ValidationError(f"Recommend approval failed: {recommended}")
	approval_task = cstr(recommended.get("task"))
	return {
		"plan": plan,
		"version": ver,
		"planner": planner,
		"reviewer": reviewer,
		"task": approval_task,
		"task_token": recommended.get("task_token"),
		"assignee": frappe.db.get_value("Workflow Task", approval_task, "assigned_user_id"),
	}


def approve_plan_via_gate05(*, plan: str, version: str, user: str | None = None) -> dict[str, Any]:
	"""Advance Draft through review chain then approve (Gate 05 path)."""
	from kentender_procurement.procurement_planning.services.approve_plan_version import (
		approve_plan_version,
	)

	advanced = advance_draft_to_recommended(plan=plan, version=version)
	approver = user or advanced.get("assignee") or ensure_approver_user()
	return approve_plan_version(
		task=advanced["task"],
		expected_token=advanced["task_token"],
		idempotency_key=f"TEST-APPROVE-{advanced['task']}",
		user=approver,
	)


def ensure_scope() -> dict[str, str]:
	ensure_currency_kes()
	ensure_procuring_entity(PE, "Ministry of Health")
	if not frappe.db.exists("Organisation Unit", OU):
		ou_type = frappe.db.get_value("Organisation Unit Type", {}, "name")
		if not ou_type:
			ot = frappe.get_doc(
				{
					"doctype": "Organisation Unit Type",
					"type_reference": "DIR",
					"display_label": "Directorate",
					"status": "Active",
				}
			)
			ot.insert(ignore_permissions=True)
			ou_type = ot.name
		frappe.get_doc(
			{
				"doctype": "Organisation Unit",
				"unit_code": OU,
				"unit_name": "Department of Health Planning",
				"unit_type": ou_type,
				"procuring_entity": PE,
				"status": "Active",
			}
		).insert(ignore_permissions=True)
	ensure_planner_user()
	ensure_reviewer_user()
	seed_rule = frappe.db.get_value(
		"Workflow Routing Rule",
		{"routing_rule_id": "RTR-PLAN-FINANCE-TASK-CP-PLN-SEED-FINANCE"},
		"name",
	)
	if seed_rule:
		frappe.db.set_value("Workflow Routing Rule", seed_rule, "status", "Inactive", update_modified=False)
	return {"pe": PE, "ou": OU, "fy": FY}


def make_approved_demand(
	*,
	pe: str = PE,
	ou: str = OU,
	title: str = "Gate01 Demand",
	need_item_count: int = 1,
	item_amount: float = 1_000_000,
	demand_code: str | None = None,
	required_by_date: str | None = None,
	item_amounts: list[float] | None = None,
) -> dict[str, Any]:
	ensure_scope()
	planner = ensure_planner_user()
	code = cstr(demand_code).strip() or f"DEM-G01-{frappe.generate_hash(length=6).upper()}"
	amounts = [float(amount) for amount in (item_amounts or [])]
	n = len(amounts) or max(1, int(need_item_count or 1))
	if not amounts:
		amounts = [float(item_amount)] * n
	total = sum(amounts)
	period_start = frappe.db.get_value(
		"Procurement Plan",
		{"procuring_entity": pe, "open_draft_version": ["is", "set"]},
		"period_start",
		order_by="creation desc",
	)
	required_by = required_by_date or (add_days(period_start, 180) if period_start else "2027-12-31")
	demand = frappe.get_doc(
		{
			"doctype": "Demand",
			"demand_code": code,
			"title": title,
			"procuring_entity": pe,
			"owner_org_unit": ou,
			"requester": planner,
			"demand_route": "Standard",
			"status": "Approved",
			"current_stage": "Complete",
			"planning_ready": 1,
			"planning_usage": "Not taken up",
			"required_by_date": required_by,
			"currency": "KES",
			"confirmed_estimate": total,
			"requester_estimate": total,
		}
	)
	demand.insert(ignore_permissions=True)
	items: list[str] = []
	first_item = ""
	for i in range(n):
		item_code = f"DI-{code}-{i + 1}"
		item = frappe.get_doc(
			{
				"doctype": "Demand Item",
				"demand": demand.name,
				"item_code": item_code,
				"description": f"{title} — need {i + 1}",
				"confirmed_estimate": amounts[i],
				"requester_estimate": amounts[i],
				"currency": "KES",
				"quantity": 1,
				"confirmed_quantity": 1,
			}
		)
		item.insert(ignore_permissions=True)
		items.append(item.name)
		if not first_item:
			first_item = item.name
	return {
		"demand": demand.name,
		"demand_item": first_item,
		"demand_items": items,
		"demand_code": code,
	}


def add_demand_to_plan(
	*, plan: str, demand: str | None = None, demands: list[str] | None = None,
	user: str | None = None, expected_version_token: str | None = None,
	idempotency_key: str | None = None, **kwargs: Any,
) -> dict[str, Any]:
	"""Test-only adapter that supplies the revised formation concurrency contract."""
	from kentender_procurement.procurement_planning.services.add_demand_to_plan import (
		add_demand_to_plan as form_demands,
	)

	names = list(demands or ([demand] if demand else []))
	focus = frappe.db.get_value(
		"Procurement Plan", plan, "open_draft_version"
	) or frappe.db.get_value("Procurement Plan", plan, "current_approved_version")
	token = expected_version_token or frappe.db.get_value(
		"Procurement Plan Version", focus, "concurrency_token"
	)
	# Retired per-item source arguments must not regain production authority.
	kwargs.pop("demand_item", None)
	return form_demands(
		plan=plan,
		demands=names,
		expected_version_token=token,
		idempotency_key=idempotency_key or f"TEST-{plan}-{frappe.generate_hash(length=12)}",
		user=user,
		**kwargs,
	)


def create_plan_as_planner(**overrides: Any) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services.create_procurement_plan import (
		create_procurement_plan,
	)

	scope = ensure_scope()
	planner = ensure_planner_user()
	# Historical tests may still pass a display title. The approved production
	# service intentionally accepts only stable PE/FY identity.
	overrides.pop("title", None)
	requested_fy = overrides.pop("financial_year", None)
	for attempt in range(20):
		fy = requested_fy or unique_test_fy(
			base_year=2200,
			bucket=int(frappe.db.count("Procurement Plan") or 0) + attempt,
		)
		purge_pe_fy(fy)
		fy = ensure_test_fiscal_year(fy)
		result = create_procurement_plan(
			procuring_entity=scope["pe"], financial_year=fy, user=planner
		)
		if result.get("created") and result.get("version"):
			return result
		if requested_fy:
			return result
	raise frappe.ValidationError("Could not allocate an isolated financial year for the test Plan.")


def ensure_test_fiscal_year(financial_year: str) -> str:
	fy = cstr(financial_year).strip()
	start_year = int(fy.split("/", 1)[0])
	governed_label = f"{start_year}/{str(start_year + 1)[-2:]}"
	start_date = f"{start_year}-07-01"
	end_date = f"{start_year + 1}-06-30"
	existing = frappe.db.get_value(
		"Fiscal Year",
		{"year_start_date": start_date, "year_end_date": end_date},
		"name",
	)
	if existing:
		frappe.db.set_value("Fiscal Year", existing, "disabled", 0, update_modified=False)
		return governed_label
	if not frappe.db.exists("Fiscal Year", governed_label):
		frappe.get_doc({
			"doctype": "Fiscal Year",
			"year": governed_label,
			"year_start_date": start_date,
			"year_end_date": end_date,
			"disabled": 0,
		}).insert(ignore_permissions=True)
	return governed_label


def create_procurement_plan_for_test(
	*, procuring_entity: str, financial_year: str, user: str, **_retired_values: Any,
) -> dict[str, Any]:
	"""Test-only entry that establishes governed FY configuration first."""
	from kentender_procurement.procurement_planning.services.create_procurement_plan import (
		create_procurement_plan,
	)

	governed_fy = ensure_test_fiscal_year(financial_year)
	return create_procurement_plan(
		procuring_entity=procuring_entity, financial_year=governed_fy, user=user
	)


def unique_test_fy(*, base_year: int = 2600, bucket: int = 0) -> str:
	"""High-year FY unique per call (Gate 05). Years stay in 2100–2899 for DATE columns."""
	import time
	import uuid

	# Mix time + uuid + bucket; keep result in a safe calendar range for period_start/end.
	n = (int(time.time() * 1000) + int(uuid.uuid4().hex[:5], 16) + bucket * 97) % 700
	y = 2100 + ((base_year + n) % 700)
	return f"{y}/{str(y + 1)[-2:]}"


def purge_pe_fy(financial_year: str) -> None:
	"""Delete PE+FY plans and orphan versions left by force-clears."""
	scope = ensure_scope()
	pe = scope["pe"]
	plans = frappe.get_all(
		"Procurement Plan",
		filters={"procuring_entity": pe, "financial_year": financial_year},
		pluck="name",
	)
	versions = (
		frappe.get_all("Procurement Plan Version", filters={"plan": ["in", plans]}, pluck="name")
		if plans else []
	)
	items = (
		frappe.get_all("Procurement Plan Item", filters={"plan": ["in", plans]}, pluck="name")
		if plans else []
	)
	item_versions = (
		frappe.get_all(
			"Procurement Plan Item Version",
			filters={"plan_item": ["in", items]},
			pluck="name",
		)
		if items else []
	)
	if frappe.db.exists("DocType", "Workflow Task"):
		task_names = []
		if versions:
			task_names.extend(frappe.get_all(
				"Workflow Task",
				filters={"subject_type": "Procurement Plan Version", "subject_id": ["in", versions]},
				pluck="name",
			))
		if item_versions:
			task_names.extend(frappe.get_all(
				"Workflow Task",
				filters={"subject_type": "Procurement Plan Item Version", "subject_id": ["in", item_versions]},
				pluck="name",
			))
		for task_name in dict.fromkeys(task_names):
			frappe.delete_doc("Workflow Task", task_name, force=True, ignore_permissions=True)
	if items:
		item_codes = frappe.get_all(
			"Procurement Plan Item", filters={"name": ["in", items]}, pluck="plan_item_code"
		)
		if frappe.db.exists("DocType", "Planning Consumption"):
			for name in frappe.get_all(
				"Planning Consumption", filters={"plan_item_code": ["in", item_codes]}, pluck="name"
			):
				frappe.delete_doc("Planning Consumption", name, force=True, ignore_permissions=True)
		for doctype in ("Planning Handoff Snapshot", "Plan Demand Allocation", "Procurement Plan Item Version"):
			if not frappe.db.exists("DocType", doctype):
				continue
			for child in frappe.get_all(doctype, filters={"plan_item": ["in", items]}, pluck="name"):
				frappe.delete_doc(doctype, child, force=True, ignore_permissions=True)
		for item in items:
			frappe.db.set_value(
				"Procurement Plan Item", item,
				{"current_approved_item_version": None, "draft_item_version": None},
				update_modified=False,
			)
			frappe.delete_doc("Procurement Plan Item", item, force=True, ignore_permissions=True)
	if versions:
		for doctype in ("Plan Decision", "Plan Validation Result", "Publication Event"):
			if not frappe.db.exists("DocType", doctype):
				continue
			for child in frappe.get_all(doctype, filters={"plan_version": ["in", versions]}, pluck="name"):
				frappe.delete_doc(doctype, child, force=True, ignore_permissions=True)
	for plan in plans:
		frappe.db.set_value(
			"Procurement Plan", plan,
			{"current_approved_version": None, "open_draft_version": None},
			update_modified=False,
		)
	for version in versions:
		frappe.db.set_value("Procurement Plan Version", version, "source_version", None, update_modified=False)
		frappe.delete_doc("Procurement Plan Version", version, force=True, ignore_permissions=True)
	for plan in plans:
		frappe.delete_doc("Procurement Plan", plan, force=True, ignore_permissions=True)
	# A failed earlier registration can leave the deterministic V1 name without
	# its Plan. Remove only the exact PE/year registration namespace.
	start_year = cstr(financial_year).split("/", 1)[0]
	pe_code = cstr(frappe.db.get_value("Procuring Entity", pe, "entity_code") or pe).removeprefix("PE-")
	for version in frappe.get_all(
		"Procurement Plan Version",
		filters={"version_code": ["like", f"PLN-{pe_code}-{start_year}-001-V%"]},
		pluck="name",
	):
		if not frappe.db.exists("Procurement Plan", frappe.db.get_value("Procurement Plan Version", version, "plan")):
			frappe.delete_doc("Procurement Plan Version", version, force=True, ignore_permissions=True)
	# Keep cleanup inside the caller's test/request transaction. Committing here
	# caused later test-created Fiscal Years and Plans to escape Frappe's normal
	# rollback boundary when another case reused this helper.


def ensure_budget_officer_user() -> str:
	from kentender_budget.services.budget_permissions import ROLE_OFFICER, ensure_budget_roles
	from kentender_core.seeds.kentender_mvp_v1 import constants as C
	from kentender_procurement.procurement_planning.tests._gate02_helpers import (
		ensure_user_with_roles,
	)

	ensure_budget_roles()
	ensure_scope()
	user = ensure_user_with_roles(
		C.USER_BUD_OFFICER,
		roles=(ROLE_OFFICER,),
		pe=PE,
		org_unit=OU,
		include_descendants=0,
	)
	_ensure_shared_authorization(
		user=user,
		profile_id="CP-PLN-G01-FINANCE",
		capabilities=("plan.finance.task", "plan.finance.confirm", "plan.finance.return"),
		task_routes=(("plan.finance.task", "plan.finance.task"),),
	)
	return user


def make_test_budget_line(
	*, approved_amount: float, reserved_amount: float = 0.0,
	fiscal_period: str = "2027/28", start_date: str = "2027-07-01",
	end_date: str = "2028-06-30", title: str = "Planning finance test line",
	fixture_namespace: str | None = None, plan: str | None = None,
) -> dict[str, str]:
	"""Isolated Active Budget Line so Finance tests do not mutate the MOH seed portfolio."""
	ensure_scope()
	if plan:
		plan_context = frappe.db.get_value(
			"Procurement Plan", plan,
			["financial_year", "period_start", "period_end"],
			as_dict=True,
		)
		if plan_context:
			fiscal_period = plan_context.financial_year
			start_date = cstr(plan_context.period_start)
			end_date = cstr(plan_context.period_end)
	token = frappe.generate_hash(length=8).upper()
	bud = frappe.get_doc(
		{
			"doctype": "Budget",
			"generated_reference": f"MOH-BUD-PLN-{token}",
			"title": f"Planning finance test {token}",
			"procuring_entity": PE,
			"fiscal_period": fiscal_period,
			"start_date": start_date,
			"end_date": end_date,
			"currency": "KES",
			"budget_owner": "Budget Officer",
			"registration_source": "Direct capture",
			"authoritative_reference": f"PLN-FIN-{token}",
			"approval_date": "2027-06-01",
			"external_approved_total": approved_amount,
			"approval_evidence": "/files/pln-fin-test.pdf",
			"status": "Active",
			"fixture_namespace": fixture_namespace,
		}
	)
	bud.flags.ignore_validate = True
	bud.insert(ignore_permissions=True)
	line = frappe.get_doc(
		{
			"doctype": "Budget Line",
			"budget": bud.name,
			"generated_reference": f"MOH-BL-PLN-{token}",
			"title": title,
			"organisational_owner": "Directorate of Digital Health and Policy",
			"classification": "Capital expenditure",
			"funding_source_type": "Exchequer",
			"funding_source_name": "Government of Kenya Development Budget",
			"approved_amount": approved_amount,
			"amount_reserved": reserved_amount,
			"amount_committed": 0,
			"currency": "KES",
			"is_active": 1,
			"fixture_namespace": fixture_namespace,
		}
	)
	line.flags.skip_budget_strategy_validate = True
	line.insert(ignore_permissions=True)
	return {
		"budget": bud.name,
		"budget_line": line.name,
		"budget_line_code": line.generated_reference,
	}


def attach_demand_funding(
	*,
	demand: str,
	budget_line: str,
	budget: str,
	amount: float,
	reservation: str | None = None,
) -> str:
	doc = frappe.get_doc(
		{
			"doctype": "Demand Funding Allocation",
			"demand": demand,
			"budget": budget,
			"budget_line": budget_line,
			"allocation_amount": amount,
			"currency": "KES",
			"matching_source": "Budget Officer",
			"bo_confirmation_status": "Pending",
			"funding_reservation": reservation or "",
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name
