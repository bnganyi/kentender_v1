# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared fixtures for Gate 01 Planning tests (Gate 02 scope-aware)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_procurement.procurement_planning.services.planning_permissions import (
	ROLE_DESIGNATED_APPROVER,
	ROLE_PLANNER,
	ensure_planning_roles,
)

PE = "PE-MOH"
OU = "MOH-DIR-DHP"
FY = "2027/28"
PLANNER_ROLE = ROLE_PLANNER
PLANNER_USER = "pln.gate01.planner@test.local"
APPROVER_USER = "pln.gate01.approver@test.local"


def _ensure_usa(user: str, role: str, pe: str, org_unit: str | None) -> None:
	if not frappe.db.exists("DocType", "User Scope Assignment"):
		return
	filters = {"user": user, "role": role, "procuring_entity": pe}
	if org_unit:
		filters["organisation_unit"] = org_unit
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
	return PLANNER_USER


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

	return update_plan_item(
		plan_item=plan_item,
		user=user,
		fields={
			"requirement_description": "Complete for departmental sign-off",
			"procurement_category": "ICT infrastructure and services",
			"procurement_method": "Open tender",
			"arrangement": "Single year",
			"lotting_decision": "Single lot",
			"ms_invitation_published": "2027-09-15",
			"ms_tender_opening": "2027-10-20",
			"ms_evaluation_completed": "2027-11-15",
			"ms_award_approval": "2027-12-15",
			"ms_contract_signature": "2028-01-15",
			"ms_delivery_completion": "2028-03-31",
		},
	)


def ensure_approver_user() -> str:
	ensure_planning_roles()
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
	return REVIEWER_USER


def advance_draft_to_recommended(*, plan: str, version: str | None = None) -> dict[str, Any]:
	"""Complete items → validate → HoD submit → submit for review → recommend.

	Required before ``approve_plan_version`` under Gate 05 rules.
	"""
	from kentender_procurement.procurement_planning.services.record_plan_decision import (
		record_plan_decision,
	)
	from kentender_procurement.procurement_planning.services.submit_departmental_contribution import (
		submit_departmental_contribution,
	)
	from kentender_procurement.procurement_planning.services.submit_plan_for_review import (
		submit_plan_for_review,
	)
	from kentender_procurement.procurement_planning.services.validate_plan import validate_plan

	planner = ensure_planner_user()
	hod = ensure_hod_user()
	reviewer = ensure_reviewer_user()
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

	validate_plan(plan=plan, user=planner)
	dept = submit_departmental_contribution(plan=plan, declaration=1, user=hod)
	if not dept.get("ok"):
		raise frappe.ValidationError(f"Departmental submit failed: {dept}")

	token = frappe.db.get_value("Procurement Plan Version", ver, "concurrency_token")
	submitted = submit_plan_for_review(plan=plan, concurrency_token=token, user=planner)
	if not submitted.get("ok"):
		raise frappe.ValidationError(f"Submit for review failed: {submitted}")

	token2 = frappe.db.get_value("Procurement Plan Version", ver, "concurrency_token")
	rec = record_plan_decision(
		version=ver,
		decision="recommend",
		comment="Ready for approval",
		concurrency_token=token2,
		user=reviewer,
	)
	if not rec.get("ok"):
		raise frappe.ValidationError(f"Recommend failed: {rec}")
	return {
		"plan": plan,
		"version": ver,
		"planner": planner,
		"hod": hod,
		"reviewer": reviewer,
		"concurrency_token": rec.get("concurrency_token"),
	}


def approve_plan_via_gate05(*, plan: str, version: str, user: str | None = None) -> dict[str, Any]:
	"""Advance Draft through review chain then approve (Gate 05 path)."""
	from kentender_procurement.procurement_planning.services.approve_plan_version import (
		approve_plan_version,
	)

	advanced = advance_draft_to_recommended(plan=plan, version=version)
	approver = user or ensure_approver_user()
	token = frappe.db.get_value(
		"Procurement Plan Version", advanced["version"], "concurrency_token"
	)
	return approve_plan_version(
		version=advanced["version"],
		concurrency_token=token,
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
	ensure_approver_user()
	ensure_reviewer_user()
	return {"pe": PE, "ou": OU, "fy": FY}


def make_approved_demand(
	*,
	pe: str = PE,
	ou: str = OU,
	title: str = "Gate01 Demand",
	need_item_count: int = 1,
	item_amount: float = 1_000_000,
) -> dict[str, str]:
	ensure_scope()
	planner = ensure_planner_user()
	code = f"DEM-G01-{frappe.generate_hash(length=6).upper()}"
	n = max(1, int(need_item_count or 1))
	total = float(item_amount) * n
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
				"confirmed_estimate": float(item_amount),
				"requester_estimate": float(item_amount),
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


def create_plan_as_planner(**overrides: Any) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services.create_procurement_plan import (
		create_procurement_plan,
	)

	scope = ensure_scope()
	planner = ensure_planner_user()
	seq = int(frappe.db.count("Procurement Plan") or 0) + 1
	fy = overrides.pop("financial_year", None) or f"{2100 + seq}/{str(2101 + seq)[-2:]}"
	kwargs = {
		"procuring_entity": scope["pe"],
		"financial_year": fy,
		"title": "Gate01 Annual Plan",
		"currency": "KES",
		"coordinating_org_unit": scope["ou"],
		"user": planner,
	}
	kwargs.update(overrides)
	return create_procurement_plan(**kwargs)


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
	for name in frappe.get_all(
		"Procurement Plan",
		filters={"procuring_entity": pe, "financial_year": financial_year},
		pluck="name",
	):
		frappe.delete_doc("Procurement Plan", name, force=True, ignore_permissions=True)
	fy_slug = (financial_year or "").replace("/", "-")
	for name in frappe.get_all(
		"Procurement Plan Version",
		filters={"name": ("like", f"PLN-%{fy_slug}%")},
		pluck="name",
	):
		frappe.delete_doc("Procurement Plan Version", name, force=True, ignore_permissions=True)
	frappe.db.commit()
