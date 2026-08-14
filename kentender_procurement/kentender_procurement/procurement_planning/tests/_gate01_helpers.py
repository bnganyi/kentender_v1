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
	ROLE_TENDER_INITIATOR,
	ROLE_VIEWER,
	ensure_planning_roles,
)

PE = "PE-MOH"
OU = "MOH-DIR-DHP"
FY = "2027/28"
PLANNER_ROLE = ROLE_PLANNER
PLANNER_USER = "pln.gate01.planner@test.local"
APPROVER_USER = "pln.gate01.approver@test.local"
INITIATOR_USER = "pln.gate01.initiator@test.local"
VIEWER_USER = "pln.gate01.viewer@test.local"


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

	return update_plan_item(
		plan_item=plan_item,
		user=user,
		fields={
			"requirement_description": "Complete for submit for review",
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
	bo = ensure_budget_officer_user()
	items = frappe.get_all(
		"Procurement Plan Item",
		filters={"plan": plan, "baseline_state": ["in", ["Proposed", "Active"]]},
		pluck="name",
	)
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
			funding = make_test_budget_line(approved_amount=max(amount * 2, 10_000_000))
			attach_demand_funding(
				demand=demand,
				budget_line=funding["budget_line"],
				budget=funding["budget"],
				amount=amount,
			)
		requested = update_plan_item(
			plan_item=plan_item, user=actor, request_finance=True
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
		confirmed = confirm_plan_item_funding(plan_item=plan_item, user=bo)
		if not confirmed.get("ok"):
			raise frappe.ValidationError(f"Confirm finance failed: {confirmed}")


def advance_draft_to_recommended(*, plan: str, version: str | None = None) -> dict[str, Any]:
	"""Complete items → Finance confirm → validate → submit for review → recommend.

	Required before ``approve_plan_version`` under Gate 05 rules.
	C02: no departmental contribution step.
	"""
	from kentender_procurement.procurement_planning.services.record_plan_decision import (
		record_plan_decision,
	)
	from kentender_procurement.procurement_planning.services.submit_plan_for_review import (
		submit_plan_for_review,
	)
	from kentender_procurement.procurement_planning.services.validate_plan import validate_plan

	planner = ensure_planner_user()
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

	confirm_included_items_funding(plan=plan, planner=planner)
	validate_plan(plan=plan, user=planner)

	if cstr(plan_doc.current_approved_version or "").strip():
		from kentender_procurement.procurement_planning.services.get_plan_update import (
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
	fy = overrides.pop("financial_year", None)
	if not fy:
		# Count-based FY collided with leftover PE+FY rows after heavy Gate runs.
		fy = unique_test_fy(base_year=2200, bucket=int(frappe.db.count("Procurement Plan") or 0))
		purge_pe_fy(fy)
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
	if frappe.db.exists("DocType", "Planning Handoff Snapshot"):
		for name in frappe.get_all(
			"Planning Handoff Snapshot",
			filters={"plan_item": ("like", f"%{fy_slug}%")},
			pluck="name",
		):
			frappe.delete_doc(
				"Planning Handoff Snapshot", name, force=True, ignore_permissions=True
			)
	for name in frappe.get_all(
		"Procurement Plan Version",
		filters={"name": ("like", f"PLN-%{fy_slug}%")},
		pluck="name",
	):
		frappe.delete_doc("Procurement Plan Version", name, force=True, ignore_permissions=True)
	for name in frappe.get_all(
		"Procurement Plan Item",
		filters={"plan_item_code": ("like", f"PPI-%{fy_slug}%")},
		pluck="name",
	):
		for doctype in (
			"Planning Handoff Snapshot",
			"Plan Demand Allocation",
			"Procurement Plan Item Version",
		):
			if not frappe.db.exists("DocType", doctype):
				continue
			for child in frappe.get_all(doctype, filters={"plan_item": name}, pluck="name"):
				frappe.delete_doc(doctype, child, force=True, ignore_permissions=True)
		frappe.delete_doc("Procurement Plan Item", name, force=True, ignore_permissions=True)
	frappe.db.commit()


def ensure_budget_officer_user() -> str:
	from kentender_budget.services.budget_permissions import ROLE_OFFICER, ensure_budget_roles
	from kentender_procurement.procurement_planning.tests._gate02_helpers import (
		ensure_user_with_roles,
	)

	ensure_budget_roles()
	ensure_scope()
	return ensure_user_with_roles(
		"pln.c05.bo@test.local",
		roles=(ROLE_OFFICER,),
		pe=PE,
		org_unit=None,
		include_descendants=0,
	)


def make_test_budget_line(*, approved_amount: float, reserved_amount: float = 0.0) -> dict[str, str]:
	"""Isolated Active Budget Line so Finance tests do not mutate the MOH seed portfolio."""
	ensure_scope()
	token = frappe.generate_hash(length=8).upper()
	bud = frappe.get_doc(
		{
			"doctype": "Budget",
			"generated_reference": f"MOH-BUD-PLN-{token}",
			"title": f"Planning finance test {token}",
			"procuring_entity": PE,
			"fiscal_period": "2027/28",
			"start_date": "2027-07-01",
			"end_date": "2028-06-30",
			"currency": "KES",
			"budget_owner": "Budget Officer",
			"registration_source": "Direct capture",
			"authoritative_reference": f"PLN-FIN-{token}",
			"approval_date": "2027-06-01",
			"external_approved_total": approved_amount,
			"approval_evidence": "/files/pln-fin-test.pdf",
			"status": "Active",
		}
	)
	bud.flags.ignore_validate = True
	bud.insert(ignore_permissions=True)
	line = frappe.get_doc(
		{
			"doctype": "Budget Line",
			"budget": bud.name,
			"generated_reference": f"MOH-BL-PLN-{token}",
			"title": "Planning finance test line",
			"organisational_owner": "Directorate of Digital Health and Policy",
			"classification": "Capital expenditure",
			"funding_source_type": "Exchequer",
			"funding_source_name": "Government of Kenya Development Budget",
			"approved_amount": approved_amount,
			"amount_reserved": reserved_amount,
			"amount_committed": 0,
			"currency": "KES",
			"is_active": 1,
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
