# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Playwright fixtures for the Procurement Planning browser specs (decision D8:
fixture endpoints live here, never in api.py; invoked via `bench execute`).

Isolation is by Procuring Entity — **PE-PWPL** — never the §14 demo world and
never the Python tests' PE-PLNT (tracker rule 8: each spec file owns its
fixture entity). Fixture instants are pinned except the submission window,
which must span the real test clock. Every reset clears the actors' server-side
context preferences (CTX-CHG-001): they outlive spec files otherwise.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils.password import update_password

PE = "PE-PWPL"
OU = "OU-PWPL-DHI"
FY = "FY-2098-2099"
CTX = "CTX-PWPL-2098-2099"

AUTHOR = "pwpl.author@example.test"
HOD = "pwpl.hod@example.test"
PLANNER = "pwpl.planner@example.test"
AUDITOR = "pwpl.auditor@example.test"
OUTSIDER = "pwpl.outsider@example.test"

PASSWORD = "Test@123"

CONTEXT_PREFERENCE_KEYS = (
	"kt_working_procuring_entity",
	"kt_planning_financial_year",
	"kt_planning_org_unit",
)


def _guard() -> None:
	if frappe.flags.in_test or frappe.conf.get("developer_mode") or frappe.conf.get("allow_tests"):
		return
	frappe.throw(
		"Procurement Planning Playwright fixtures are test data. Enable "
		"developer_mode or allow_tests on this site before building them."
	)


def _actor(email: str, full_name: str, roles: tuple[str, ...], *, unit: bool) -> None:
	if not frappe.db.exists("User", email):
		parts = full_name.split()
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": parts[0],
				"last_name": " ".join(parts[1:]),
				"enabled": 1,
				"user_type": "System User",
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	held = {row.role for row in user.roles}
	missing = [role for role in ("Desk User", *roles) if role not in held]
	if missing:
		user.add_roles(*missing)
	update_password(email, PASSWORD)
	scope = [("Procuring Entity", PE)]
	if unit:
		scope.append(("Organisation Unit", OU))
	for allow, value in scope:
		if not frappe.db.exists(
			"User Permission", {"user": email, "allow": allow, "for_value": value}
		):
			frappe.get_doc(
				{"doctype": "User Permission", "user": email, "allow": allow, "for_value": value}
			).insert(ignore_permissions=True)


def _clear_context_preferences() -> None:
	for user in (AUTHOR, HOD, PLANNER, AUDITOR, OUTSIDER):
		for key in CONTEXT_PREFERENCE_KEYS:
			frappe.defaults.clear_user_default(key, user)


def ensure_world(*, commit: bool = True) -> dict[str, Any]:
	"""The PE-PWPL world: entity, department, active FY context, open window
	and the five §6 personas the workspace spec logs in as."""
	_guard()
	from kentender_procurement.procurement_planning.services.planning_roles import (
		ensure_planning_roles,
	)

	ensure_planning_roles()
	if not frappe.db.exists("Procuring Entity", PE):
		frappe.get_doc(
			{
				"doctype": "Procuring Entity",
				"entity_code": PE,
				"legal_name": "Playwright Planning Entity",
				"entity_name": "Playwright Planning Entity",
				"reporting_currency": "KES",
				"status": "Active",
				"fixture_namespace": "KENTENDER_PLAYWRIGHT",
			}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("Organisation Unit", OU):
		ou_type = frappe.get_all("Organisation Unit Type", limit=1, pluck="name")[0]
		frappe.get_doc(
			{
				"doctype": "Organisation Unit",
				"unit_code": OU,
				"unit_name": "Digital Health",
				"unit_type": ou_type,
				"procuring_entity": PE,
				"status": "Active",
				"fixture_namespace": "KENTENDER_PLAYWRIGHT",
			}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("Financial Year", FY):
		frappe.get_doc(
			{
				"doctype": "Financial Year",
				"start_year": 2098,
				"label": "FY 2098/99",
				"start_date": "2098-07-01",
				"end_date": "2099-06-30",
				"timezone": "Africa/Nairobi",
				"record_status": "Available",
			}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("PE Fiscal Year Context", CTX):
		frappe.get_doc(
			{
				"doctype": "PE Fiscal Year Context",
				"procuring_entity": PE,
				"financial_year": FY,
				"context_status": "Active",
				"active_from": "2020-01-01 00:00:00",
				"active_to": "2105-01-01 00:00:00",
			}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("Departmental Plan Submission Window", {"pe_fy_context": CTX}):
		frappe.get_doc(
			{
				"doctype": "Departmental Plan Submission Window",
				"pe_fy_context": CTX,
				"opens_at": "2020-01-01 00:00:00",
				"closes_at": "2099-01-01 00:00:00",
				"fixture_namespace": "KENTENDER_PLAYWRIGHT",
			}
		).insert(ignore_permissions=True)

	_actor(AUTHOR, "Playwright Planning Author", ("Departmental Author",), unit=True)
	_actor(
		HOD, "Playwright Planning HoD",
		("Departmental Author", "Head of User Department"), unit=True,
	)
	_actor(PLANNER, "Playwright Procurement Planner", ("Procurement Planner",), unit=False)
	_actor(AUDITOR, "Playwright Planning Auditor", ("Planning Auditor",), unit=False)
	# The outsider holds a Planning role but no PE-PWPL permission at all.
	if not frappe.db.exists("User", OUTSIDER):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": OUTSIDER,
				"first_name": "Playwright",
				"last_name": "Outsider",
				"enabled": 1,
				"user_type": "System User",
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
	outsider = frappe.get_doc("User", OUTSIDER)
	if "Departmental Author" not in {row.role for row in outsider.roles}:
		outsider.add_roles("Desk User", "Departmental Author")
	update_password(OUTSIDER, PASSWORD)
	_clear_context_preferences()
	if commit:
		frappe.db.commit()
	return {"pe": PE, "ou": OU, "fy": FY}


def reset_workspace_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""Empty PE-PWPL Planning world with the window open: the workspace spec's
	documented starting state."""
	world = ensure_world(commit=False)
	_wipe(commit=False)
	_clear_context_preferences()
	if commit:
		frappe.db.commit()
	return world


def _wipe(*, commit: bool = False) -> None:
	roots = frappe.get_all("Departmental Plan", filters={"procuring_entity": PE}, pluck="name")
	versions = frappe.get_all(
		"Departmental Plan Version",
		filters={"departmental_plan": ("in", roots or ("",))},
		pluck="name",
	)
	tasks = frappe.get_all(
		"Departmental Plan Validation Task", filters={"procuring_entity": PE}, pluck="name"
	)
	frappe.db.delete(
		"Departmental Plan Validation Decision", {"task": ("in", tasks or ("",))}
	)
	frappe.db.delete("Departmental Plan Validation Task", {"procuring_entity": PE})
	frappe.db.delete(
		"Departmental Plan Submission", {"dpp_version": ("in", versions or ("",))}
	)
	frappe.db.delete("Departmental Plan Entry", {"dpp_version": ("in", versions or ("",))})
	frappe.db.delete("Departmental Plan Version", {"name": ("in", versions or ("",))})
	frappe.db.delete("Departmental Plan", {"name": ("in", roots or ("",))})
	plans = frappe.get_all("Annual Plan", filters={"procuring_entity": PE}, pluck="name")
	plan_versions = frappe.get_all(
		"Annual Plan Version", filters={"annual_plan": ("in", plans or ("",))}, pluck="name"
	)
	frappe.db.delete("Plan Source Allocation", {"plan_version": ("in", plan_versions or ("",))})
	frappe.db.delete("Annual Plan Item", {"plan_version": ("in", plan_versions or ("",))})
	frappe.db.delete("Annual Plan Version", {"name": ("in", plan_versions or ("",))})
	frappe.db.delete("Annual Plan", {"name": ("in", plans or ("",))})
	if commit:
		frappe.db.commit()


def reset_all(*, commit: bool = True) -> dict[str, Any]:
	"""Remove every PE-PWPL Planning row (the purge entry point)."""
	_guard()
	_wipe(commit=commit)
	return {"ok": True}


# --- Slice B world: PE-PWDP (its own spec file, its own entity — rule 8) ----

DPP_PE = "PE-PWDP"
DPP_OU = "OU-PWDP-DHI"
DPP_CTX = "CTX-PWDP-2098-2099"

DPP_AUTHOR = "pwdp.author@example.test"
DPP_HOD = "pwdp.hod@example.test"
DPP_PLANNER = "pwdp.planner@example.test"


def _dpp_actor(email: str, full_name: str, roles: tuple[str, ...], *, unit: bool) -> None:
	if not frappe.db.exists("User", email):
		parts = full_name.split()
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": parts[0],
				"last_name": " ".join(parts[1:]),
				"enabled": 1,
				"user_type": "System User",
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	held = {row.role for row in user.roles}
	missing = [role for role in ("Desk User", *roles) if role not in held]
	if missing:
		user.add_roles(*missing)
	update_password(email, PASSWORD)
	scope = [("Procuring Entity", DPP_PE)]
	if unit:
		scope.append(("Organisation Unit", DPP_OU))
	for allow, value in scope:
		if not frappe.db.exists(
			"User Permission", {"user": email, "allow": allow, "for_value": value}
		):
			frappe.get_doc(
				{"doctype": "User Permission", "user": email, "allow": allow, "for_value": value}
			).insert(ignore_permissions=True)


def ensure_dpp_world(*, commit: bool = True) -> dict[str, Any]:
	"""PE-PWDP: department, active FY context, open window, an Active Budget
	graph (so the live `list_eligible_budget_lines` contract returns one line)
	and the three actors the DPP spec logs in as."""
	_guard()
	from kentender_procurement.procurement_planning.services.planning_roles import (
		ensure_planning_roles,
	)

	ensure_planning_roles()
	if not frappe.db.exists("Procuring Entity", DPP_PE):
		frappe.get_doc(
			{
				"doctype": "Procuring Entity",
				"entity_code": DPP_PE,
				"legal_name": "Playwright DPP Entity",
				"entity_name": "Playwright DPP Entity",
				"reporting_currency": "KES",
				"status": "Active",
				"fixture_namespace": "KENTENDER_PLAYWRIGHT",
			}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("Organisation Unit", DPP_OU):
		ou_type = frappe.get_all("Organisation Unit Type", limit=1, pluck="name")[0]
		frappe.get_doc(
			{
				"doctype": "Organisation Unit",
				"unit_code": DPP_OU,
				"unit_name": "Digital Health",
				"unit_type": ou_type,
				"procuring_entity": DPP_PE,
				"status": "Active",
				"fixture_namespace": "KENTENDER_PLAYWRIGHT",
			}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("Financial Year", FY):
		frappe.get_doc(
			{
				"doctype": "Financial Year",
				"start_year": 2098,
				"label": "FY 2098/99",
				"start_date": "2098-07-01",
				"end_date": "2099-06-30",
				"timezone": "Africa/Nairobi",
				"record_status": "Available",
			}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("PE Fiscal Year Context", DPP_CTX):
		frappe.get_doc(
			{
				"doctype": "PE Fiscal Year Context",
				"procuring_entity": DPP_PE,
				"financial_year": FY,
				"context_status": "Active",
				"active_from": "2020-01-01 00:00:00",
				"active_to": "2105-01-01 00:00:00",
			}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("Departmental Plan Submission Window", {"pe_fy_context": DPP_CTX}):
		frappe.get_doc(
			{
				"doctype": "Departmental Plan Submission Window",
				"pe_fy_context": DPP_CTX,
				"opens_at": "2020-01-01 00:00:00",
				"closes_at": "2099-01-01 00:00:00",
				"fixture_namespace": "KENTENDER_PLAYWRIGHT",
			}
		).insert(ignore_permissions=True)

	# Budget graph: Budget → Active Budget Version → one Budget Line (Version).
	# Test scaffolding for another app's model, deliberately outside production
	# code paths (the NDS test-exemption precedent); Budget's own fixture
	# builders own richer worlds.
	budget = frappe.db.get_value(
		"Budget", {"procuring_entity": DPP_PE, "financial_year": FY}, "name"
	)
	if not budget:
		budget = frappe.get_doc(
			{
				"doctype": "Budget",
				"generated_reference": "BUD-PWDP-0001",
				"procuring_entity": DPP_PE,
				"financial_year": FY,
				"currency": "KES",
			}
		).insert(ignore_permissions=True).name
	bv = frappe.db.get_value("Budget Version", {"budget": budget, "status": "Active"}, "name")
	if not bv:
		bv = frappe.get_doc(
			{
				"doctype": "Budget Version",
				"generated_reference": "BUDV-PWDP-0001",
				"budget": budget,
				"version_number": 1,
				"status": "Active",
				"approval_reference": "PWDP-APPROVAL-1",
				"approval_date": "2026-06-30",
				"authorised_total": 100000000,
				"currency": "KES",
				"approval_document": "/files/pwdp-approval.pdf",
			}
		).insert(ignore_permissions=True).name
	line = frappe.db.get_value("Budget Line", {"generated_reference": "BL-PWDP-0001"}, "name")
	if not line:
		line = frappe.get_doc(
			{
				"doctype": "Budget Line",
				"generated_reference": "BL-PWDP-0001",
				"budget": budget,
			}
		).insert(ignore_permissions=True).name
	if not frappe.db.exists("Budget Line Version", {"budget_version": bv, "budget_line": line}):
		fs = frappe.get_all("Funding Source", limit=1, pluck="name")
		frappe.get_doc(
			{
				"doctype": "Budget Line Version",
				"generated_reference": "BLV-PWDP-0001",
				"budget_version": bv,
				"budget_line": line,
				"title": "Digital health programme",
				"funding_source": fs[0] if fs else None,
				"approved_amount": 100000000,
				"currency": "KES",
			}
		).insert(ignore_permissions=True)

	_dpp_actor(DPP_AUTHOR, "Playwright DPP Author", ("Departmental Author",), unit=True)
	_dpp_actor(
		DPP_HOD, "Playwright DPP HoD",
		("Departmental Author", "Head of User Department"), unit=True,
	)
	_dpp_actor(DPP_PLANNER, "Playwright DPP Planner", ("Procurement Planner",), unit=False)
	for user in (DPP_AUTHOR, DPP_HOD, DPP_PLANNER):
		for key in CONTEXT_PREFERENCE_KEYS:
			frappe.defaults.clear_user_default(key, user)
	if commit:
		frappe.db.commit()
	return {"pe": DPP_PE, "ou": DPP_OU, "fy": FY}


def reset_dpp_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""Empty PE-PWDP Planning world, window open — the DPP spec's start state."""
	world = ensure_dpp_world(commit=False)
	_wipe_pe(DPP_PE)
	for user in (DPP_AUTHOR, DPP_HOD, DPP_PLANNER):
		for key in CONTEXT_PREFERENCE_KEYS:
			frappe.defaults.clear_user_default(key, user)
	if commit:
		frappe.db.commit()
	return world


def _wipe_pe(pe: str) -> None:
	roots = frappe.get_all("Departmental Plan", filters={"procuring_entity": pe}, pluck="name")
	versions = frappe.get_all(
		"Departmental Plan Version",
		filters={"departmental_plan": ("in", roots or ("",))},
		pluck="name",
	)
	tasks = frappe.get_all(
		"Departmental Plan Validation Task", filters={"procuring_entity": pe}, pluck="name"
	)
	frappe.db.delete(
		"Departmental Plan Validation Decision", {"task": ("in", tasks or ("",))}
	)
	frappe.db.delete("Departmental Plan Validation Task", {"procuring_entity": pe})
	frappe.db.delete(
		"Departmental Plan Submission", {"dpp_version": ("in", versions or ("",))}
	)
	frappe.db.delete("Departmental Plan Entry", {"dpp_version": ("in", versions or ("",))})
	frappe.db.delete("Departmental Plan Version", {"name": ("in", versions or ("",))})
	frappe.db.delete("Departmental Plan", {"name": ("in", roots or ("",))})
	plans = frappe.get_all("Annual Plan", filters={"procuring_entity": pe}, pluck="name")
	plan_versions = frappe.get_all(
		"Annual Plan Version", filters={"annual_plan": ("in", plans or ("",))}, pluck="name"
	)
	# §7.3 Finance world: a prior run's Confirm may have created a REAL Budget
	# Funding Reservation — leaving it behind would understate "Available" on
	# the next run's identical Budget Line and turn a sufficient-funding spec
	# flaky (found live: a retry of the same Playwright test failed on a
	# stale reservation from the attempt before it). Scope by the *business*
	# `plan_item_id` prefix, not a join through the live Annual Plan Item
	# table — a Plan Reservation Reference from an already-deleted item is
	# exactly the orphan this cleanup exists to catch, so it must stay
	# findable after its parent item is gone.
	pe_code = pe.removeprefix("PE-")
	reservations = frappe.get_all(
		"Plan Reservation Reference",
		filters={"plan_item_id": ("like", f"PPI-{pe_code}-%")},
		pluck="reservation",
	)
	frappe.db.delete("Funding Reservation", {"name": ("in", reservations or ("",))})
	frappe.db.delete("Plan Reservation Reference", {"plan_item_id": ("like", f"PPI-{pe_code}-%")})
	finance_tasks = frappe.get_all(
		"Plan Finance Task", filters={"procuring_entity": pe}, pluck="name"
	)
	frappe.db.delete("Plan Finance Decision", {"task": ("in", finance_tasks or ("",))})
	frappe.db.delete("Plan Finance Task", {"name": ("in", finance_tasks or ("",))})
	frappe.db.delete("Plan Source Allocation", {"plan_version": ("in", plan_versions or ("",))})
	frappe.db.delete("Annual Plan Item", {"plan_version": ("in", plan_versions or ("",))})
	frappe.db.delete("Annual Plan Version", {"name": ("in", plan_versions or ("",))})
	frappe.db.delete("Annual Plan", {"name": ("in", plans or ("",))})


# --- Slice C world: PE-PWVC (validation/review spec file) --------------------

VC_PE = "PE-PWVC"
VC_OU = "OU-PWVC-DHI"
VC_CTX = "CTX-PWVC-2098-2099"

VC_AUTHOR = "pwvc.author@example.test"
VC_HOD = "pwvc.hod@example.test"
VC_PLANNER = "pwvc.planner@example.test"


def _ensure_pe_world(pe: str, ou: str, ctx: str, *, budget_ref: str) -> None:
	"""One Planning world: entity, department, FY context, open window and an
	Active Budget graph so live eligibility works."""
	from kentender_procurement.procurement_planning.services.planning_roles import (
		ensure_planning_roles,
	)

	ensure_planning_roles()
	if not frappe.db.exists("Procuring Entity", pe):
		frappe.get_doc(
			{
				"doctype": "Procuring Entity",
				"entity_code": pe,
				"legal_name": f"Playwright {pe.removeprefix('PE-')} Entity",
				"entity_name": f"Playwright {pe.removeprefix('PE-')} Entity",
				"reporting_currency": "KES",
				"status": "Active",
				"fixture_namespace": "KENTENDER_PLAYWRIGHT",
			}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("Organisation Unit", ou):
		ou_type = frappe.get_all("Organisation Unit Type", limit=1, pluck="name")[0]
		frappe.get_doc(
			{
				"doctype": "Organisation Unit",
				"unit_code": ou,
				"unit_name": "Digital Health",
				"unit_type": ou_type,
				"procuring_entity": pe,
				"status": "Active",
				"fixture_namespace": "KENTENDER_PLAYWRIGHT",
			}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("Financial Year", FY):
		frappe.get_doc(
			{
				"doctype": "Financial Year",
				"start_year": 2098,
				"label": "FY 2098/99",
				"start_date": "2098-07-01",
				"end_date": "2099-06-30",
				"timezone": "Africa/Nairobi",
				"record_status": "Available",
			}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("PE Fiscal Year Context", ctx):
		frappe.get_doc(
			{
				"doctype": "PE Fiscal Year Context",
				"procuring_entity": pe,
				"financial_year": FY,
				"context_status": "Active",
				"active_from": "2020-01-01 00:00:00",
				"active_to": "2105-01-01 00:00:00",
			}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("Departmental Plan Submission Window", {"pe_fy_context": ctx}):
		frappe.get_doc(
			{
				"doctype": "Departmental Plan Submission Window",
				"pe_fy_context": ctx,
				"opens_at": "2020-01-01 00:00:00",
				"closes_at": "2099-01-01 00:00:00",
				"fixture_namespace": "KENTENDER_PLAYWRIGHT",
			}
		).insert(ignore_permissions=True)
	budget = frappe.db.get_value("Budget", {"procuring_entity": pe, "financial_year": FY}, "name")
	if not budget:
		budget = frappe.get_doc(
			{
				"doctype": "Budget",
				"generated_reference": f"BUD-{budget_ref}-0001",
				"procuring_entity": pe,
				"financial_year": FY,
				"currency": "KES",
			}
		).insert(ignore_permissions=True).name
	bv = frappe.db.get_value("Budget Version", {"budget": budget, "status": "Active"}, "name")
	if not bv:
		bv = frappe.get_doc(
			{
				"doctype": "Budget Version",
				"generated_reference": f"BUDV-{budget_ref}-0001",
				"budget": budget,
				"version_number": 1,
				"status": "Active",
				"approval_reference": f"{budget_ref}-APPROVAL-1",
				"approval_date": "2026-06-30",
				"authorised_total": 100000000,
				"currency": "KES",
				"approval_document": f"/files/{budget_ref.lower()}-approval.pdf",
			}
		).insert(ignore_permissions=True).name
	line = frappe.db.get_value("Budget Line", {"generated_reference": f"BL-{budget_ref}-0001"}, "name")
	if not line:
		line = frappe.get_doc(
			{
				"doctype": "Budget Line",
				"generated_reference": f"BL-{budget_ref}-0001",
				"budget": budget,
			}
		).insert(ignore_permissions=True).name
	if not frappe.db.exists("Budget Line Version", {"budget_version": bv, "budget_line": line}):
		fs = frappe.get_all("Funding Source", limit=1, pluck="name")
		frappe.get_doc(
			{
				"doctype": "Budget Line Version",
				"generated_reference": f"BLV-{budget_ref}-0001",
				"budget_version": bv,
				"budget_line": line,
				"title": "Digital health programme",
				"funding_source": fs[0] if fs else None,
				"approved_amount": 100000000,
				"currency": "KES",
			}
		).insert(ignore_permissions=True)


def _pe_actor(email: str, full_name: str, roles: tuple[str, ...], pe: str, ou: str | None) -> None:
	if not frappe.db.exists("User", email):
		parts = full_name.split()
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": parts[0],
				"last_name": " ".join(parts[1:]),
				"enabled": 1,
				"user_type": "System User",
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	held = {row.role for row in user.roles}
	missing = [role for role in ("Desk User", *roles) if role not in held]
	if missing:
		user.add_roles(*missing)
	update_password(email, PASSWORD)
	scope = [("Procuring Entity", pe)] + ([("Organisation Unit", ou)] if ou else [])
	for allow, value in scope:
		if not frappe.db.exists(
			"User Permission", {"user": email, "allow": allow, "for_value": value}
		):
			frappe.get_doc(
				{"doctype": "User Permission", "user": email, "allow": allow, "for_value": value}
			).insert(ignore_permissions=True)


def reset_review_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""PE-PWVC with ONE submitted DPP (driven through the real §8.2 commands as
	the fixture actors) and its Open validation task — the review spec's start."""
	from uuid import uuid4

	from kentender_procurement.procurement_planning.services import dpp_lifecycle

	_guard()
	_ensure_pe_world(VC_PE, VC_OU, VC_CTX, budget_ref="PWVC")
	_pe_actor(VC_AUTHOR, "Playwright Review Author", ("Departmental Author",), VC_PE, VC_OU)
	_pe_actor(
		VC_HOD, "Playwright Review HoD",
		("Departmental Author", "Head of User Department"), VC_PE, VC_OU,
	)
	_pe_actor(VC_PLANNER, "Playwright Review Planner", ("Procurement Planner",), VC_PE, None)
	_wipe_pe(VC_PE)
	for user in (VC_AUTHOR, VC_HOD, VC_PLANNER):
		for pref_key in CONTEXT_PREFERENCE_KEYS:
			frappe.defaults.clear_user_default(pref_key, user)

	frappe.set_user(VC_AUTHOR)
	opened = dpp_lifecycle.open_departmental_plan(
		procuring_entity=VC_PE, organisation_unit=VC_OU, financial_year=FY,
		idempotency_key=uuid4().hex, fixture_namespace="KENTENDER_PLAYWRIGHT",
	)
	added = dpp_lifecycle.save_direct_requirement(
		dpp_version=opened["current_version"],
		values={
			"title": "Platform security assessment",
			"description": "Assess the security of the platform and provide a prioritised remediation report.",
			"expected_operational_result": "The department receives a prioritised and actionable remediation plan.",
			"quantity": 1,
			"unit": frappe.get_all("Unit Of Measure", filters={"status": "Active"}, limit=1, pluck="name")[0],
			"required_by_date": "2099-04-30",
			"budget_line": frappe.db.get_value("Budget Line", {"generated_reference": "BL-PWVC-0001"}, "name"),
			"indicative_amount": 20000000,
		},
		expected_record_version=opened["record_version"],
		idempotency_key=uuid4().hex,
	)
	frappe.set_user(VC_HOD)
	submitted = dpp_lifecycle.submit_departmental_plan(
		dpp_version=opened["current_version"], certification_confirmed=True,
		expected_record_version=added["record_version"], idempotency_key=uuid4().hex,
	)
	frappe.set_user("Administrator")
	task = frappe.db.get_value(
		"Departmental Plan Validation Task", {"task_reference": submitted["task"]}, "name"
	)
	if commit:
		frappe.db.commit()
	return {"pe": VC_PE, "task": task, "dpp_reference": opened["dpp_reference"]}


# --- Slice D world: PE-PWPF (Annual Plan workbench spec file) ---------------

PF_PE = "PE-PWPF"
PF_OU = "OU-PWPF-DHI"
PF_CTX = "CTX-PWPF-2098-2099"

PF_AUTHOR = "pwpf.author@example.test"
PF_HOD = "pwpf.hod@example.test"
PF_PLANNER = "pwpf.planner@example.test"


def _ensure_pf_strategy_world() -> str:
	"""One Active primary Strategic Plan for PE-PWPF, covering the real test
	clock, so the Plan Item editor's Objective select is never empty. Mirrors
	the Python-test fixture at procurement_planning/tests/fixtures.py."""
	existing = frappe.db.get_value(
		"Strategy Node",
		{"title": "PWPF Digital Objective", "node_type": "Strategic Objective"},
		"name",
	)
	if existing:
		return existing
	plan = frappe.get_doc(
		{
			"doctype": "Strategic Plan",
			"title": "Playwright Plan Formation Strategic Plan",
			"procuring_entity_id": PF_PE,
			"plan_role": "Primary",
			"period_start": "2020-01-01",
			"period_end": "2105-01-01",
		}
	).insert(ignore_permissions=True)
	version = frappe.get_doc(
		{
			"doctype": "Strategic Plan Version",
			"plan_id": plan.name,
			"version_number": 1,
			"effective_from": "2020-01-01",
			"effective_to": "2105-01-01",
		}
	).insert(ignore_permissions=True)
	pillar = frappe.get_doc(
		{
			"doctype": "Strategy Node", "plan_version_id": version.name,
			"node_type": "Pillar", "title": "PWPF Pillar", "display_order": 1,
		}
	).insert(ignore_permissions=True)
	programme = frappe.get_doc(
		{
			"doctype": "Strategy Node", "plan_version_id": version.name,
			"node_type": "Programme", "title": "PWPF Programme", "display_order": 2,
			"parent_node_id": pillar.name,
		}
	).insert(ignore_permissions=True)
	objective = frappe.get_doc(
		{
			"doctype": "Strategy Node", "plan_version_id": version.name,
			"node_type": "Strategic Objective", "title": "PWPF Digital Objective",
			"display_order": 3, "parent_node_id": programme.name,
		}
	).insert(ignore_permissions=True)
	frappe.db.set_value("Strategic Plan Version", version.name, "status", "Active")
	return objective.name


def reset_plan_workbench_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""PE-PWPF with ONE accepted, unallocated departmental entry (driven
	through the real §8.2 commands to Accepted) — the Annual Plan workbench
	spec's start state: PLN-DES-07's exact "1 accepted / 0 allocated / 0
	items" opening."""
	from uuid import uuid4

	from kentender_procurement.procurement_planning.services import (
		dpp_lifecycle,
		dpp_validation,
	)

	_guard()
	_ensure_pe_world(PF_PE, PF_OU, PF_CTX, budget_ref="PWPF")
	_ensure_pf_strategy_world()
	_pe_actor(PF_AUTHOR, "Playwright Formation Author", ("Departmental Author",), PF_PE, PF_OU)
	_pe_actor(
		PF_HOD, "Playwright Formation HoD",
		("Departmental Author", "Head of User Department"), PF_PE, PF_OU,
	)
	_pe_actor(PF_PLANNER, "Playwright Formation Planner", ("Procurement Planner",), PF_PE, None)
	_wipe_pe(PF_PE)
	for user in (PF_AUTHOR, PF_HOD, PF_PLANNER):
		for pref_key in CONTEXT_PREFERENCE_KEYS:
			frappe.defaults.clear_user_default(pref_key, user)

	frappe.set_user(PF_AUTHOR)
	opened = dpp_lifecycle.open_departmental_plan(
		procuring_entity=PF_PE, organisation_unit=PF_OU, financial_year=FY,
		idempotency_key=uuid4().hex, fixture_namespace="KENTENDER_PLAYWRIGHT",
	)
	added = dpp_lifecycle.save_direct_requirement(
		dpp_version=opened["current_version"],
		values={
			"title": "National digital health infrastructure upgrade",
			"description": "Procure and implement the national digital health infrastructure upgrade.",
			"expected_operational_result": "The department operates the upgraded infrastructure.",
			"quantity": 1,
			"unit": frappe.get_all("Unit Of Measure", filters={"status": "Active"}, limit=1, pluck="name")[0],
			"required_by_date": "2099-04-30",
			"budget_line": frappe.db.get_value("Budget Line", {"generated_reference": "BL-PWPF-0001"}, "name"),
			"indicative_amount": 80000000,
		},
		expected_record_version=opened["record_version"],
		idempotency_key=uuid4().hex,
	)
	frappe.set_user(PF_HOD)
	submitted = dpp_lifecycle.submit_departmental_plan(
		dpp_version=opened["current_version"], certification_confirmed=True,
		expected_record_version=added["record_version"], idempotency_key=uuid4().hex,
	)
	task = frappe.get_doc(
		"Departmental Plan Validation Task", {"task_reference": submitted["task"]}
	)
	frappe.set_user(PF_PLANNER)
	accepted = dpp_validation.accept_departmental_plan(
		task=task.name, classifications={added["entry_id"]: "Non-consulting services"},
		task_token=task.task_token, idempotency_key=uuid4().hex,
	)
	frappe.set_user("Administrator")
	if commit:
		frappe.db.commit()
	return {
		"pe": PF_PE, "plan_reference": accepted["annual_plan"],
		"dpp_reference": accepted["dpp_reference"],
	}


# --- Slice E world: PE-PWFN (Finance confirmation spec file) ---------------

FN_PE = "PE-PWFN"
FN_OU = "OU-PWFN-DHI"
FN_CTX = "CTX-PWFN-2098-2099"

FN_AUTHOR = "pwfn.author@example.test"
FN_HOD = "pwfn.hod@example.test"
FN_PLANNER = "pwfn.planner@example.test"
FN_BUDGET_OFFICER = "pwfn.budget@example.test"


def _ensure_fn_strategy_world() -> str:
	existing = frappe.db.get_value(
		"Strategy Node",
		{"title": "PWFN Digital Objective", "node_type": "Strategic Objective"},
		"name",
	)
	if existing:
		return existing
	plan = frappe.get_doc(
		{
			"doctype": "Strategic Plan",
			"title": "Playwright Finance Strategic Plan",
			"procuring_entity_id": FN_PE,
			"plan_role": "Primary",
			"period_start": "2020-01-01",
			"period_end": "2105-01-01",
		}
	).insert(ignore_permissions=True)
	version = frappe.get_doc(
		{
			"doctype": "Strategic Plan Version",
			"plan_id": plan.name,
			"version_number": 1,
			"effective_from": "2020-01-01",
			"effective_to": "2105-01-01",
		}
	).insert(ignore_permissions=True)
	pillar = frappe.get_doc(
		{
			"doctype": "Strategy Node", "plan_version_id": version.name,
			"node_type": "Pillar", "title": "PWFN Pillar", "display_order": 1,
		}
	).insert(ignore_permissions=True)
	programme = frappe.get_doc(
		{
			"doctype": "Strategy Node", "plan_version_id": version.name,
			"node_type": "Programme", "title": "PWFN Programme", "display_order": 2,
			"parent_node_id": pillar.name,
		}
	).insert(ignore_permissions=True)
	objective = frappe.get_doc(
		{
			"doctype": "Strategy Node", "plan_version_id": version.name,
			"node_type": "Strategic Objective", "title": "PWFN Digital Objective",
			"display_order": 3, "parent_node_id": programme.name,
		}
	).insert(ignore_permissions=True)
	frappe.db.set_value("Strategic Plan Version", version.name, "status", "Active")
	return objective.name


def reset_finance_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""PE-PWFN with one Plan Item fully completed and an Open Finance task
	(driven through the real §5.1/§5.2/§8.2 commands) — the Finance
	confirmation spec's start state."""
	from uuid import uuid4

	from kentender_procurement.procurement_planning.services import (
		dpp_lifecycle,
		dpp_validation,
		plan_finance,
		plan_read,
		plan_workbench,
	)

	_guard()
	_ensure_pe_world(FN_PE, FN_OU, FN_CTX, budget_ref="PWFN")
	objective = _ensure_fn_strategy_world()
	_pe_actor(FN_AUTHOR, "Playwright Finance Author", ("Departmental Author",), FN_PE, FN_OU)
	_pe_actor(
		FN_HOD, "Playwright Finance HoD",
		("Departmental Author", "Head of User Department"), FN_PE, FN_OU,
	)
	_pe_actor(FN_PLANNER, "Playwright Finance Planner", ("Procurement Planner",), FN_PE, None)
	_pe_actor(FN_BUDGET_OFFICER, "Playwright Finance Officer", ("Budget Officer",), FN_PE, None)
	_wipe_pe(FN_PE)
	for user in (FN_AUTHOR, FN_HOD, FN_PLANNER, FN_BUDGET_OFFICER):
		for pref_key in CONTEXT_PREFERENCE_KEYS:
			frappe.defaults.clear_user_default(pref_key, user)

	frappe.set_user(FN_AUTHOR)
	opened = dpp_lifecycle.open_departmental_plan(
		procuring_entity=FN_PE, organisation_unit=FN_OU,
		financial_year=FY, idempotency_key=uuid4().hex, fixture_namespace="KENTENDER_PLAYWRIGHT",
	)
	added = dpp_lifecycle.save_direct_requirement(
		dpp_version=opened["current_version"],
		values={
			"title": "National digital health infrastructure upgrade",
			"description": "Procure and implement the national digital health infrastructure upgrade.",
			"expected_operational_result": "The department operates the upgraded infrastructure.",
			"quantity": 1,
			"unit": frappe.get_all("Unit Of Measure", filters={"status": "Active"}, limit=1, pluck="name")[0],
			"required_by_date": "2099-04-30",
			"budget_line": frappe.db.get_value("Budget Line", {"generated_reference": "BL-PWFN-0001"}, "name"),
			"indicative_amount": 80000000,
		},
		expected_record_version=opened["record_version"], idempotency_key=uuid4().hex,
	)
	frappe.set_user(FN_HOD)
	submitted = dpp_lifecycle.submit_departmental_plan(
		dpp_version=opened["current_version"], certification_confirmed=True,
		expected_record_version=added["record_version"], idempotency_key=uuid4().hex,
	)
	dpp_task = frappe.get_doc(
		"Departmental Plan Validation Task", {"task_reference": submitted["task"]}
	)
	frappe.set_user(FN_PLANNER)
	accepted = dpp_validation.accept_departmental_plan(
		task=dpp_task.name, classifications={added["entry_id"]: "Non-consulting services"},
		task_token=dpp_task.task_token, idempotency_key=uuid4().hex,
	)
	plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
	formed = plan_workbench.form_plan_items(
		plan_version=accepted["annual_plan_version"],
		dpp_entries=[plan["unallocated_sources"][0]["dpp_entry"]],
		mode="each", expected_record_version=plan["record_version"], idempotency_key=uuid4().hex,
	)
	item_id = formed["created_items"][0]
	item = plan_read.get_plan_item(plan_item_id=item_id)
	plan_workbench.save_plan_item(
		plan_item=item_id,
		values={
			"title": "National digital health infrastructure upgrade",
			"description": "Procure and implement the national digital health infrastructure upgrade.",
			"strategic_objective": objective, "aggregation_reason": "",
			"invitation_date": "2098-08-01", "bid_opening_date": "2098-08-15",
			"evaluation_completion_date": "2098-09-01", "award_approval_date": "2098-09-10",
			"award_notification_date": "2098-09-15", "contract_signing_date": "2098-10-01",
			"delivery_completion_date": "2098-10-15",
		},
		expected_record_version=item["record_version"], idempotency_key=uuid4().hex,
	)
	item = plan_read.get_plan_item(plan_item_id=item_id)
	requested = plan_finance.request_finance_confirmation(
		plan_item=item_id, expected_record_version=item["record_version"], idempotency_key=uuid4().hex,
	)
	frappe.set_user("Administrator")
	if commit:
		frappe.db.commit()
	return {"pe": FN_PE, "task": requested["task"], "plan_item": item_id}
