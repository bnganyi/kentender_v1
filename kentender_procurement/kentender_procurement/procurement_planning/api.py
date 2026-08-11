# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Whitelisted Desk APIs for Procurement Planning MVP-1 UI (Gate 03–04)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.procurement_planning.services.add_demand_to_plan import (
	add_demand_to_plan as _add_demand_to_plan,
)
from kentender_procurement.procurement_planning.services.aggregate_plan_allocations import (
	aggregate_plan_allocations as _aggregate_plan_allocations,
)
from kentender_procurement.procurement_planning.services.create_procurement_plan import (
	create_procurement_plan as _create_procurement_plan,
)
from kentender_procurement.procurement_planning.services.get_plan_builder import (
	get_plan_builder as _get_plan_builder,
)
from kentender_procurement.procurement_planning.services.get_departmental_contribution import (
	get_departmental_contribution as _get_departmental_contribution,
)
from kentender_procurement.procurement_planning.services.get_plan_item_editor import (
	get_plan_item_editor as _get_plan_item_editor,
)
from kentender_procurement.procurement_planning.services.get_planning_create_scope import (
	get_planning_create_scope as _get_planning_create_scope,
)
from kentender_procurement.procurement_planning.services.get_planning_workspace import (
	get_planning_workspace as _get_planning_workspace,
)
from kentender_procurement.procurement_planning.services.list_eligible_demands import (
	list_eligible_demands as _list_eligible_demands,
)
from kentender_procurement.procurement_planning.services.update_plan_item import (
	update_plan_item as _update_plan_item,
)
from kentender_procurement.procurement_planning.services.validate_plan import (
	validate_plan as _validate_plan,
)
from kentender_procurement.procurement_planning.services.submit_departmental_contribution import (
	submit_departmental_contribution as _submit_departmental_contribution,
)
from kentender_procurement.procurement_planning.services.submit_plan_for_review import (
	submit_plan_for_review as _submit_plan_for_review,
)
from kentender_procurement.procurement_planning.services.record_plan_decision import (
	record_plan_decision as _record_plan_decision,
)
from kentender_procurement.procurement_planning.services.approve_plan_version import (
	approve_plan_version as _approve_plan_version,
)
from kentender_procurement.procurement_planning.services.get_plan_review import (
	get_plan_review as _get_plan_review,
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
def list_eligible_demands(
	plan: str | None = None,
	search: str | None = None,
	organisation_unit: str | None = None,
	category: str | None = None,
	remaining_only: int | str | None = 1,
) -> dict[str, Any]:
	return _list_eligible_demands(
		plan=plan or "",
		search=search,
		organisation_unit=organisation_unit,
		category=category,
		remaining_only=remaining_only if remaining_only is not None else 1,
	)


@frappe.whitelist()
def add_demand_to_plan(
	plan: str | None = None,
	demand: str | None = None,
	demand_item: str | None = None,
	allocated_amount: float | str | None = None,
	package_mode: str | None = None,
	formation_mode: str | None = None,
	separation_reason: str | None = None,
) -> dict[str, Any]:
	try:
		amt = float(allocated_amount) if allocated_amount not in (None, "") else None
	except (TypeError, ValueError):
		amt = None
	try:
		return _add_demand_to_plan(
			plan=plan or "",
			demand=demand or "",
			demand_item=demand_item,
			allocated_amount=amt,
			package_mode=package_mode,
			formation_mode=formation_mode,
			separation_reason=separation_reason,
		)
	except Exception as exc:
		msg = str(exc)
		title = getattr(exc, "title", None) or ""
		errors: dict[str, str] = {"form": msg}
		if "SEPARATION_REASON" in cstr(title).upper() or "separation reason" in msg.lower():
			errors["separation_reason"] = msg
		return {"ok": False, "errors": errors}


@frappe.whitelist()
def update_plan_item(
	plan_item: str | None = None,
	fields: str | dict | None = None,
) -> dict[str, Any]:
	payload: dict[str, Any]
	if isinstance(fields, str):
		try:
			payload = json.loads(fields) if fields else {}
		except json.JSONDecodeError:
			payload = {}
	elif isinstance(fields, dict):
		payload = fields
	else:
		payload = {}
	return _update_plan_item(plan_item=plan_item or "", fields=payload)


@frappe.whitelist()
def get_plan_item_editor(plan_item: str | None = None) -> dict[str, Any]:
	return _get_plan_item_editor(plan_item=plan_item or "")


@frappe.whitelist()
def get_departmental_contribution(
	plan: str | None = None,
	organisation_unit: str | None = None,
) -> dict[str, Any]:
	return _get_departmental_contribution(
		plan=plan or "",
		organisation_unit=organisation_unit,
	)


@frappe.whitelist()
def submit_departmental_contribution(
	plan: str | None = None,
	organisation_unit: str | None = None,
	declaration: int | str | None = None,
	submission_note: str | None = None,
) -> dict[str, Any]:
	return _submit_departmental_contribution(
		plan=plan or "",
		organisation_unit=organisation_unit,
		declaration=declaration,
		submission_note=submission_note,
	)


@frappe.whitelist()
def validate_plan(plan: str | None = None) -> dict[str, Any]:
	return _validate_plan(plan=plan or "")


@frappe.whitelist()
def submit_plan_for_review(
	plan: str | None = None,
	concurrency_token: str | None = None,
) -> dict[str, Any]:
	return _submit_plan_for_review(
		plan=plan or "",
		concurrency_token=concurrency_token,
	)


@frappe.whitelist()
def record_plan_decision(
	version: str | None = None,
	decision: str | None = None,
	comment: str | None = None,
	concurrency_token: str | None = None,
) -> dict[str, Any]:
	return _record_plan_decision(
		version=version or "",
		decision=decision or "",
		comment=comment,
		concurrency_token=concurrency_token,
	)


@frappe.whitelist()
def approve_plan_version(
	version: str | None = None,
	concurrency_token: str | None = None,
	reason: str | None = None,
) -> dict[str, Any]:
	try:
		return _approve_plan_version(
			version=version or "",
			concurrency_token=concurrency_token,
			reason=reason,
		)
	except frappe.PermissionError as exc:
		return {
			"ok": False,
			"errors": {"form": str(exc).split(":", 1)[-1].strip() or "Not permitted"},
		}
	except Exception as exc:
		return {"ok": False, "errors": {"form": str(exc)}}


@frappe.whitelist()
def get_plan_review(plan: str | None = None) -> dict[str, Any]:
	return _get_plan_review(plan=plan or "")


@frappe.whitelist()
def aggregate_plan_allocations(
	plan_item: str | None = None,
	demand: str | None = None,
	demand_item: str | None = None,
	allocated_amount: float | str | None = None,
	aggregation_reason: str | None = None,
) -> dict[str, Any]:
	try:
		amt = float(allocated_amount) if allocated_amount not in (None, "") else None
	except (TypeError, ValueError):
		amt = None
	try:
		return _aggregate_plan_allocations(
			plan_item=plan_item or "",
			demand=demand or "",
			demand_item=demand_item,
			allocated_amount=amt,
			aggregation_reason=aggregation_reason,
		)
	except Exception as exc:
		msg = str(exc)
		title = getattr(exc, "title", None) or ""
		errors: dict[str, str] = {"form": msg}
		if "AGG_REASON" in cstr(title).upper() or "aggregation requires" in msg.lower():
			errors["aggregation_reason"] = msg
		return {"ok": False, "errors": errors}


@frappe.whitelist()
def prepare_planning_gate04_ui(
	with_plan_item: int | str | None = 0,
	need_item_count: int | str | None = 1,
) -> dict[str, Any]:
	"""Empty Draft + eligible Approved Demand in planner scope for Gate 04 UI tests.

	When ``with_plan_item`` is truthy, also adds the Demand as the seeded planner so
	editor / populated-builder Playwright can open a Plan Item immediately.
	``need_item_count`` > 1 seeds a multi–Need Item Demand for packaging UI tests.
	"""
	from kentender_procurement.procurement_planning.services.add_demand_to_plan import (
		add_demand_to_plan,
	)
	from kentender_procurement.procurement_planning.tests._gate01_helpers import (
		make_approved_demand,
	)

	base = prepare_planning_gate03_ui()
	plan = base["empty_draft_plan"]
	n_items = max(1, int(need_item_count or 1))
	# Demand in MOH-DIR-DHP (same as empty draft coordinating OU).
	d = make_approved_demand(
		pe=base["pe_moh"],
		ou="MOH-DIR-DHP",
		title="Gate04 eligible digital health need",
		need_item_count=n_items,
	)
	out: dict[str, Any] = {
		**base,
		"eligible_demand": d["demand"],
		"eligible_demand_code": d["demand_code"],
		"need_item_count": n_items,
		"builder_route": f"/app/procurement-plan-builder?plan={plan}",
	}
	if int(with_plan_item or 0):
		planner = "moh.planning.officer@example.test"
		added = add_demand_to_plan(plan=plan, demand=d["demand"], user=planner)
		out["plan_item"] = added.get("plan_item")
		out["editor_route"] = added.get("editor_route")
		out["plan_item_code"] = added.get("plan_item_code")
	frappe.db.commit()
	return out


@frappe.whitelist()
def prepare_planning_gate05_ui() -> dict[str, Any]:
	"""Ready Plan Item + HoD user for PLN-UI-07 contribution drawer Playwright."""
	from frappe.utils.password import update_password

	from kentender_core.seeds.constants import TEST_PASSWORD
	from kentender_procurement.procurement_planning.services.planning_permissions import (
		ROLE_HOD,
		ensure_planning_roles,
	)
	from kentender_procurement.procurement_planning.services.validate_plan import (
		validate_plan,
	)
	from kentender_procurement.procurement_planning.tests._gate01_helpers import (
		complete_plan_item_for_signoff,
	)

	frappe.only_for(("System Manager", "Administrator"))
	ensure_planning_roles()
	base = prepare_planning_gate04_ui(with_plan_item=1, need_item_count=1)
	plan = base["empty_draft_plan"]
	plan_item = base.get("plan_item")
	planner = "moh.planning.officer@example.test"
	if plan_item:
		complete_plan_item_for_signoff(plan_item=plan_item, user=planner)
		validate_plan(plan=plan, user=planner)

	# Prior UI runs may have submitted this Draft's contribution — reset for HoD smoke.
	from kentender_procurement.procurement_planning.mvp1_constants import (
		DEPT_PREPARING,
		DOCTYPE_DEPT_SUBMISSION,
	)

	draft = frappe.db.get_value("Procurement Plan", plan, "open_draft_version")
	if draft:
		for name in frappe.get_all(
			DOCTYPE_DEPT_SUBMISSION,
			filters={"plan_version": draft},
			pluck="name",
		):
			frappe.db.set_value(
				DOCTYPE_DEPT_SUBMISSION,
				name,
				{
					"status": DEPT_PREPARING,
					"submitted_by": "",
					"submitted_at": None,
					"submission_hash": "",
					"submission_note": "",
					"declaration": "",
				},
			)

	hod_email = "moh.hod.dhp@example.test"
	if not frappe.db.exists("User", hod_email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": hod_email,
				"first_name": "MOH",
				"last_name": "HoD",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", hod_email)
	user.enabled = 1
	user.save(ignore_permissions=True)
	user.add_roles("Desk User", ROLE_HOD)
	update_password(hod_email, TEST_PASSWORD)
	for name in frappe.get_all(
		"User Scope Assignment",
		filters={"user": hod_email, "role": ROLE_HOD},
		pluck="name",
	):
		frappe.delete_doc("User Scope Assignment", name, force=1, ignore_permissions=True)
	frappe.get_doc(
		{
			"doctype": "User Scope Assignment",
			"user": hod_email,
			"role": ROLE_HOD,
			"procuring_entity": base["pe_moh"],
			"organisation_unit": "MOH-DIR-DHP",
			"include_descendants": 1,
		}
	).insert(ignore_permissions=True)
	frappe.db.commit()
	return {
		**base,
		"hod_user": hod_email,
		"builder_route": f"/app/procurement-plan-builder?plan={plan}",
		"ready_for_signoff": True,
	}


@frappe.whitelist()
def prepare_planning_gate05_approval_ui() -> dict[str, Any]:
	"""In-review + recommended plan + Reviewer/Approver users for PLN-UI-08 Playwright."""
	from frappe.utils.password import update_password

	from kentender_core.seeds.constants import TEST_PASSWORD
	from kentender_procurement.procurement_planning.services.planning_permissions import (
		ROLE_DESIGNATED_APPROVER,
		ROLE_REVIEWER,
		ROLE_VIEWER,
		ensure_planning_roles,
	)
	from kentender_procurement.procurement_planning.services.record_plan_decision import (
		record_plan_decision,
	)
	from kentender_procurement.procurement_planning.services.submit_departmental_contribution import (
		submit_departmental_contribution,
	)
	from kentender_procurement.procurement_planning.services.submit_plan_for_review import (
		submit_plan_for_review,
	)
	from kentender_procurement.procurement_planning.tests._gate01_helpers import (
		complete_plan_item_for_signoff,
	)

	frappe.only_for(("System Manager", "Administrator"))
	ensure_planning_roles()
	base = prepare_planning_gate05_ui()
	plan = base["empty_draft_plan"]
	plan_item = base.get("plan_item")
	planner = "moh.planning.officer@example.test"
	hod = base["hod_user"]
	if plan_item:
		complete_plan_item_for_signoff(plan_item=plan_item, user=planner)
	from kentender_procurement.procurement_planning.services.validate_plan import (
		validate_plan,
	)

	validate_plan(plan=plan, user=planner)
	dept = submit_departmental_contribution(plan=plan, declaration=1, user=hod)
	if not dept.get("ok"):
		frappe.throw(f"Gate05 approval prep: dept submit failed: {dept}")

	version = frappe.db.get_value("Procurement Plan", plan, "open_draft_version")
	token = frappe.db.get_value("Procurement Plan Version", version, "concurrency_token")
	sub = submit_plan_for_review(plan=plan, concurrency_token=token, user=planner)
	if not sub.get("ok"):
		frappe.throw(f"Gate05 approval prep: submit for review failed: {sub}")

	reviewer = "moh.planning.reviewer@example.test"
	approver = "moh.plan.approver@example.test"
	viewer = "pln.ui.viewer@example.test"
	for email, role, first, last in (
		(reviewer, ROLE_REVIEWER, "MOH", "Reviewer"),
		(approver, ROLE_DESIGNATED_APPROVER, "MOH", "Approver"),
		(viewer, ROLE_VIEWER, "MOH", "Viewer"),
	):
		if not frappe.db.exists("User", email):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": first,
					"last_name": last,
					"send_welcome_email": 0,
					"user_type": "System User",
				}
			).insert(ignore_permissions=True)
		user = frappe.get_doc("User", email)
		user.enabled = 1
		user.save(ignore_permissions=True)
		user.add_roles("Desk User", role)
		update_password(email, TEST_PASSWORD)
		for name in frappe.get_all(
			"User Scope Assignment",
			filters={"user": email, "role": role},
			pluck="name",
		):
			frappe.delete_doc("User Scope Assignment", name, force=1, ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "User Scope Assignment",
				"user": email,
				"role": role,
				"procuring_entity": base["pe_moh"],
				"organisation_unit": "",
				"include_descendants": 0,
			}
		).insert(ignore_permissions=True)

	token2 = frappe.db.get_value("Procurement Plan Version", version, "concurrency_token")
	rec = record_plan_decision(
		version=version,
		decision="recommend",
		comment="Ready for designated approval",
		concurrency_token=token2,
		user=reviewer,
	)
	if not rec.get("ok"):
		frappe.throw(f"Gate05 approval prep: recommend failed: {rec}")

	# Ensure review page admits these roles
	if frappe.db.exists("Page", "procurement-plan-review"):
		page = frappe.get_doc("Page", "procurement-plan-review")
		existing = {r.role for r in page.roles}
		for role in (
			"Procurement Planner",
			"Planning Reviewer",
			"Designated Approver",
			"Accounting Officer",
			"Planning Authority",
			"Planning Viewer",
			"Head of User Department",
			"Requester",
			"Desk User",
			"Administrator",
			"System Manager",
		):
			if role not in existing:
				page.append("roles", {"role": role})
		page.save(ignore_permissions=True)

	frappe.db.commit()
	return {
		**base,
		"reviewer_user": reviewer,
		"approver_user": approver,
		"viewer_user": viewer,
		"version": version,
		"review_route": f"/app/procurement-plan-review?plan={plan}",
		"ready_for_approval": True,
	}


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
