# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Whitelisted Desk APIs for Procurement Planning MVP-1 UI (Gate 03)."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_planning.services.create_procurement_plan import (
	create_procurement_plan as _create_procurement_plan,
)
from kentender_procurement.procurement_planning.services.get_plan_builder import (
	get_plan_builder as _get_plan_builder,
)
from kentender_procurement.procurement_planning.services.get_planning_create_scope import (
	get_planning_create_scope as _get_planning_create_scope,
)
from kentender_procurement.procurement_planning.services.get_planning_workspace import (
	get_planning_workspace as _get_planning_workspace,
)


@frappe.whitelist()
def get_planning_workspace(
	procuring_entity: str | None = None,
	financial_year: str | None = "2027/28",
	work_filter: str | None = "all",
) -> dict[str, Any]:
	return _get_planning_workspace(
		procuring_entity=procuring_entity,
		financial_year=financial_year,
		work_filter=work_filter,
	)


@frappe.whitelist()
def get_planning_create_scope(
	selected_pe: str | None = None,
	financial_year: str | None = "2027/28",
) -> dict[str, Any]:
	return _get_planning_create_scope(
		selected_pe=selected_pe,
		financial_year=financial_year,
	)


@frappe.whitelist()
def create_procurement_plan(
	procuring_entity: str | None = None,
	financial_year: str | None = None,
	title: str | None = None,
	currency: str | None = "KES",
	coordinating_org_unit: str | None = None,
) -> dict[str, Any]:
	"""Structured validation for Desk form — field errors, not Message dialogs."""
	errors: dict[str, str] = {}
	if not (financial_year or "").strip():
		errors["financial_year"] = "Financial year is required"
	if not (title or "").strip():
		errors["title"] = "Plan title is required"
	if not (coordinating_org_unit or "").strip():
		errors["coordinating_org_unit"] = "Coordinating procurement unit is required"
	if not (currency or "").strip():
		errors["currency"] = "Currency is required"
	# PE required when multi; create service resolves single/forced.
	from kentender_procurement.procurement_planning.services.planning_permissions import (
		MODE_MULTI,
		resolve_pe_for_create,
	)

	scope = resolve_pe_for_create(frappe.session.user, procuring_entity)
	if scope["selection_mode"] == MODE_MULTI and not (procuring_entity or "").strip():
		errors["procuring_entity"] = "Procuring Entity selection is required"
	if errors:
		return {"ok": False, "errors": errors}

	try:
		result = _create_procurement_plan(
			procuring_entity=procuring_entity or "",
			financial_year=financial_year or "",
			title=title or "",
			currency=currency or "KES",
			coordinating_org_unit=coordinating_org_unit or "",
		)
	except frappe.PermissionError as exc:
		return {
			"ok": False,
			"errors": {"form": str(exc).split(":", 1)[-1].strip() or "Not permitted"},
		}
	except Exception as exc:
		# Catch ValidationError + DuplicateEntryError (orphaned version codes) as field errors.
		msg = str(exc)
		field = "form"
		lower = msg.lower()
		if "procuring entity" in lower:
			field = "procuring_entity"
		elif (
			"financial year" in lower
			or "already exists" in lower
			or "duplicate" in lower
		):
			field = "financial_year"
		elif "organisation unit" in lower or "coordinating" in lower:
			field = "coordinating_org_unit"
		elif "title" in lower:
			field = "title"
		elif not isinstance(exc, (frappe.ValidationError, frappe.DuplicateEntryError)):
			raise
		return {"ok": False, "errors": {field: msg}}

	result["redirect"] = f"/app/procurement-plan-builder?plan={result['plan']}"
	return result


@frappe.whitelist()
def get_plan_builder(plan: str | None = None) -> dict[str, Any]:
	return _get_plan_builder(plan=plan or "")


@frappe.whitelist()
def prepare_planning_gate03_ui(clear_create_fy: str | None = None) -> dict[str, Any]:
	"""Playwright/UI fixture: empty Draft builder + multi-PE planner + free FY for create."""
	from frappe.utils.password import update_password

	from kentender_core.seeds._common import ensure_procuring_entity
	from kentender_core.seeds.constants import TEST_PASSWORD
	from kentender_procurement.procurement_planning.seeds.pln_seed_004_empty_draft import (
		UI_FY,
		UI_OU,
		UI_PE,
		UI_PLAN_CODE,
		ensure_empty_draft_plan_fixture,
	)
	from kentender_procurement.procurement_planning.services.planning_permissions import (
		ROLE_PLANNER,
		ensure_planning_roles,
	)

	frappe.only_for(("System Manager", "Administrator"))
	ensure_planning_roles()
	pe_moh = UI_PE
	pe_cgk = "PE-CGKIS"
	ou_moh = UI_OU
	ou_cgk = "CGK-DEPT-HEALTH"
	ensure_procuring_entity(pe_moh, "Ministry of Health")
	ensure_procuring_entity(pe_cgk, "County Government of Kisumu")
	# Desk Administrator: read-only Planning Support Viewer across demo PEs.
	from kentender_core.seeds.kentender_mvp_v1.users import (
		ensure_administrator_planning_support_viewer,
	)

	ensure_administrator_planning_support_viewer()
	fixture = ensure_empty_draft_plan_fixture(commit=True)

	multi_email = "pln.ui.multi@example.test"
	if not frappe.db.exists("User", multi_email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": multi_email,
				"first_name": "Multi",
				"last_name": "Planner",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", multi_email)
	user.enabled = 1
	user.save(ignore_permissions=True)
	user.add_roles("Desk User", ROLE_PLANNER)
	update_password(multi_email, TEST_PASSWORD)
	for name in frappe.get_all(
		"User Scope Assignment",
		filters={"user": multi_email, "role": ROLE_PLANNER},
		pluck="name",
	):
		frappe.delete_doc("User Scope Assignment", name, force=1, ignore_permissions=True)
	for pe, ou in ((pe_moh, ou_moh), (pe_cgk, ou_cgk)):
		frappe.get_doc(
			{
				"doctype": "User Scope Assignment",
				"user": multi_email,
				"role": ROLE_PLANNER,
				"procuring_entity": pe,
				"organisation_unit": ou,
				"include_descendants": 1,
			}
		).insert(ignore_permissions=True)

	# Prefer an unused FY that also appears in create-scope FY options.
	fy = (clear_create_fy or "").strip()
	if not fy or fy == UI_FY:
		for candidate in ("2028/29", "2026/27", "2029/30"):
			if candidate == UI_FY:
				continue
			if not frappe.db.exists(
				"Procurement Plan",
				{"procuring_entity": pe_moh, "financial_year": candidate},
			):
				fy = candidate
				break
		else:
			fy = "2028/29"
	if fy != UI_FY:
		fy_token = fy.replace("/", "-")
		# Orphan versions (Duplicate Name) can survive a partial prior create.
		for ver in frappe.get_all(
			"Procurement Plan Version",
			filters={"version_code": ["like", f"%{fy_token}%"]},
			pluck="name",
		):
			frappe.delete_doc(
				"Procurement Plan Version", ver, force=True, ignore_permissions=True
			)
		for name in frappe.get_all(
			"Procurement Plan",
			filters={"procuring_entity": pe_moh, "financial_year": fy},
			pluck="name",
		):
			code = frappe.db.get_value("Procurement Plan", name, "plan_code") or ""
			if code == UI_PLAN_CODE:
				continue
			for ver in frappe.get_all(
				"Procurement Plan Version", filters={"plan": name}, pluck="name"
			):
				frappe.delete_doc(
					"Procurement Plan Version", ver, force=True, ignore_permissions=True
				)
			for item in frappe.get_all(
				"Procurement Plan Item", filters={"plan": name}, pluck="name"
			):
				for iv in frappe.get_all(
					"Procurement Plan Item Version",
					filters={"plan_item": item},
					pluck="name",
				):
					frappe.delete_doc(
						"Procurement Plan Item Version",
						iv,
						force=True,
						ignore_permissions=True,
					)
				frappe.delete_doc(
					"Procurement Plan Item", item, force=True, ignore_permissions=True
				)
			frappe.delete_doc("Procurement Plan", name, force=True, ignore_permissions=True)
	frappe.db.commit()

	return {
		"ok": True,
		"empty_draft_plan": fixture["plan"],
		"empty_draft_plan_code": UI_PLAN_CODE,
		"empty_draft_fy": UI_FY,
		"builder_route": f"/app/procurement-plan-builder?plan={fixture['plan']}",
		"multi_planner": multi_email,
		"create_fy": fy,
		"pe_moh": pe_moh,
	}
