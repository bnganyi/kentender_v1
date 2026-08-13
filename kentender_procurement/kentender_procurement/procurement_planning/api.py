# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Whitelisted Desk APIs for Procurement Planning MVP-1 UI (Gate 03–04)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, flt

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
from kentender_procurement.procurement_planning.services.plan_item_finance import (
	confirm_plan_item_funding as _confirm_plan_item_funding,
	get_plan_finance_task as _get_plan_finance_task,
	return_plan_item_from_finance as _return_plan_item_from_finance,
)
from kentender_procurement.procurement_planning.services.validate_plan import (
	validate_plan as _validate_plan,
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
from kentender_procurement.procurement_planning.services.remove_plan_item import (
	cancel_plan_update as _cancel_plan_update,
	remove_plan_item_from_plan as _remove_plan_item_from_plan,
)
from kentender_procurement.procurement_planning.services.get_plan_review import (
	get_plan_review as _get_plan_review,
)
from kentender_procurement.procurement_planning.services.get_plan_implementation import (
	get_plan_implementation as _get_plan_implementation,
)
from kentender_procurement.procurement_planning.services.get_plan_update import (
	get_plan_update as _get_plan_update,
	save_plan_update as _save_plan_update,
)
from kentender_procurement.procurement_planning.services.publish_approved_plan import (
	publish_approved_plan as _publish_approved_plan,
)
from kentender_procurement.procurement_planning.services.create_planning_handoff_snapshot import (
	create_planning_handoff_snapshot as _create_planning_handoff_snapshot,
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
	demands: str | list | None = None,
	demand_item: str | None = None,
	allocated_amount: float | str | None = None,
	package_mode: str | None = None,
	formation_mode: str | None = None,
	separation_reason: str | None = None,
	formation_reason: str | None = None,
) -> dict[str, Any]:
	try:
		amt = float(allocated_amount) if allocated_amount not in (None, "") else None
	except (TypeError, ValueError):
		amt = None
	try:
		return _add_demand_to_plan(
			plan=plan or "",
			demand=demand or "",
			demands=demands,
			demand_item=demand_item,
			allocated_amount=amt,
			package_mode=package_mode,
			formation_mode=formation_mode,
			separation_reason=separation_reason,
			formation_reason=formation_reason,
		)
	except Exception as exc:
		msg = str(exc)
		title = getattr(exc, "title", None) or ""
		errors: dict[str, str] = {"form": msg}
		title_u = cstr(title).upper()
		if "SEPARATION_REASON" in title_u or "separation reason" in msg.lower():
			errors["separation_reason"] = msg
		if "FORMATION_REASON" in title_u or "reason for combining" in msg.lower():
			errors["formation_reason"] = msg
		return {"ok": False, "errors": errors}


@frappe.whitelist()
def remove_plan_item_from_plan(
	plan: str | None = None,
	plan_item: str | None = None,
	reason: str | None = None,
	concurrency_token: str | None = None,
) -> dict[str, Any]:
	try:
		return _remove_plan_item_from_plan(
			plan=plan or "",
			plan_item=plan_item or "",
			reason=reason,
			concurrency_token=concurrency_token,
		)
	except frappe.PermissionError as exc:
		return {
			"ok": False,
			"errors": {"form": str(exc).split(":", 1)[-1].strip() or "Not permitted"},
		}
	except Exception as exc:
		msg = str(exc)
		title = cstr(getattr(exc, "title", None) or "")
		errors: dict[str, str] = {"form": msg}
		if "reason" in msg.lower() and "required" in msg.lower():
			errors["reason"] = msg
		return {"ok": False, "errors": errors, "error_code": title or None}


@frappe.whitelist()
def cancel_plan_update(
	plan: str | None = None,
	concurrency_token: str | None = None,
) -> dict[str, Any]:
	try:
		return _cancel_plan_update(plan=plan or "", concurrency_token=concurrency_token)
	except Exception as exc:
		return {"ok": False, "errors": {"form": str(exc)}}


@frappe.whitelist()
def update_plan_item(
	plan_item: str | None = None,
	fields: str | dict | None = None,
	request_finance: int | str | None = None,
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
	try:
		return _update_plan_item(
			plan_item=plan_item or "",
			fields=payload,
			request_finance=request_finance,
		)
	except frappe.PermissionError:
		raise
	except Exception as exc:
		return {"ok": False, "errors": {"form": str(exc)}}


@frappe.whitelist()
def get_plan_finance_task(plan_item: str | None = None) -> dict[str, Any]:
	return _get_plan_finance_task(plan_item=plan_item or "")


@frappe.whitelist()
def confirm_plan_item_funding(
	plan_item: str | None = None,
	note: str | None = None,
) -> dict[str, Any]:
	return _confirm_plan_item_funding(plan_item=plan_item or "", note=note)


@frappe.whitelist()
def return_plan_item_from_finance(
	plan_item: str | None = None,
	reason: str | None = None,
) -> dict[str, Any]:
	return _return_plan_item_from_finance(plan_item=plan_item or "", reason=reason)


@frappe.whitelist()
def get_plan_item_editor(plan_item: str | None = None) -> dict[str, Any]:
	return _get_plan_item_editor(plan_item=plan_item or "")


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
def get_plan_implementation(plan: str | None = None) -> dict[str, Any]:
	return _get_plan_implementation(plan=plan or "")


@frappe.whitelist()
def get_plan_update(plan: str | None = None) -> dict[str, Any]:
	return _get_plan_update(plan=plan or "")


@frappe.whitelist()
def save_plan_update(
	plan: str | None = None,
	update_reason: str | None = None,
	concurrency_token: str | None = None,
) -> dict[str, Any]:
	try:
		return _save_plan_update(
			plan=plan or "",
			update_reason=update_reason,
			concurrency_token=concurrency_token,
		)
	except frappe.PermissionError as exc:
		return {
			"ok": False,
			"errors": {"form": str(exc).split(":", 1)[-1].strip() or "Not permitted"},
		}
	except Exception as exc:
		return {"ok": False, "errors": {"form": str(exc)}}


@frappe.whitelist()
def publish_approved_plan(
	plan: str | None = None,
	channel: str | None = None,
) -> dict[str, Any]:
	return _publish_approved_plan(plan=plan or "", channel=channel)


@frappe.whitelist()
def create_planning_handoff_snapshot(
	plan_item: str | None = None,
	tender_reference: str | None = None,
) -> dict[str, Any]:
	return _create_planning_handoff_snapshot(
		plan_item=plan_item or "",
		tender_reference=tender_reference,
	)


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
	eligible_count: int | str | None = 1,
	mixed_ou: int | str | None = 0,
) -> dict[str, Any]:
	"""Empty Draft + eligible Approved Demand in planner scope for Gate 04 UI tests.

	When ``with_plan_item`` is truthy, also adds the Demand as the seeded planner so
	editor / populated-builder Playwright can open a Plan Item immediately.
	``need_item_count`` > 1 seeds a multi–Need Item Demand for packaging UI tests.
	``eligible_count`` > 1 seeds a second same-OU Approved Demand for Combine UI tests.
	``mixed_ou`` with ``eligible_count`` >= 2 seeds the second Demand under HRMD
	so UI-04 can prove Combine is disabled (PLN-AC-016).
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
	n_eligible = max(1, int(eligible_count or 1))
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
		"eligible_count": n_eligible,
		"builder_route": f"/app/procurement-plan-builder?plan={plan}",
	}
	if n_eligible >= 2:
		second_ou = "MOH-DIR-DHP"
		if int(mixed_ou or 0):
			from kentender_procurement.procurement_planning.tests._gate02_helpers import (
				_ensure_ou,
			)

			second_ou = "MOH-DIR-HRMD"
			_ensure_ou(second_ou, "Human Resource Management", base["pe_moh"])
		d2 = make_approved_demand(
			pe=base["pe_moh"],
			ou=second_ou,
			title=(
				"Gate04 HRMD eligible need"
				if int(mixed_ou or 0)
				else "Gate04 second digital health need"
			),
			need_item_count=1,
		)
		out["eligible_demand_2"] = d2["demand"]
		out["eligible_demand_code_2"] = d2["demand_code"]
		out["mixed_ou"] = bool(int(mixed_ou or 0))
		out["eligible_demand_2_ou"] = second_ou
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
	"""Ready Plan Item Draft for builder / review prep (C02: no contribution)."""
	from kentender_procurement.procurement_planning.services.planning_permissions import (
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

	frappe.db.commit()
	return {
		**base,
		"builder_route": f"/app/procurement-plan-builder?plan={plan}",
		"ready_for_submit": True,
	}


@frappe.whitelist()
def prepare_planning_finance_ui() -> dict[str, Any]:
	"""Complete Plan Item + Awaiting Finance task for PLN-UI-07 Playwright."""
	from kentender_procurement.procurement_planning.services.update_plan_item import (
		update_plan_item,
	)
	from kentender_procurement.procurement_planning.tests._gate01_helpers import (
		attach_demand_funding,
		make_test_budget_line,
	)

	from frappe.utils.password import update_password

	from kentender_core.seeds.constants import TEST_PASSWORD
	from kentender_procurement.procurement_planning.services.planning_permissions import (
		ROLE_VIEWER,
		ensure_planning_roles,
	)

	frappe.only_for(("System Manager", "Administrator"))
	ensure_planning_roles()
	base = prepare_planning_gate05_ui()
	plan = base["empty_draft_plan"]
	plan_item = base.get("plan_item")
	demand = base.get("eligible_demand")
	planner = "moh.planning.officer@example.test"
	viewer = "pln.ui.viewer@example.test"
	if not frappe.db.exists("User", viewer):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": viewer,
				"first_name": "MOH",
				"last_name": "Viewer",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", viewer)
	user.enabled = 1
	user.save(ignore_permissions=True)
	user.add_roles("Desk User", ROLE_VIEWER)
	update_password(viewer, TEST_PASSWORD)
	for name in frappe.get_all(
		"User Scope Assignment",
		filters={"user": viewer, "role": ROLE_VIEWER},
		pluck="name",
	):
		frappe.delete_doc("User Scope Assignment", name, force=1, ignore_permissions=True)
	frappe.get_doc(
		{
			"doctype": "User Scope Assignment",
			"user": viewer,
			"role": ROLE_VIEWER,
			"procuring_entity": base.get("pe_moh") or "PE-MOH",
			"organisation_unit": "",
			"include_descendants": 0,
		}
	).insert(ignore_permissions=True)
	if plan_item and demand:
		amount = flt(
			frappe.db.get_value("Procurement Plan Item Version", {"plan_item": plan_item}, "confirmed_estimate")
			or 1_000_000
		)
		funding = make_test_budget_line(approved_amount=max(amount * 2, 10_000_000))
		if not frappe.db.exists("Demand Funding Allocation", {"demand": demand}):
			attach_demand_funding(
				demand=demand,
				budget_line=funding["budget_line"],
				budget=funding["budget"],
				amount=amount,
			)
		update_plan_item(plan_item=plan_item, user=planner, request_finance=True)
	# BO must open SCREEN_5 (builder) and the workspace queue — Page.roles gate Desk.
	for page_name in ("procurement-plan-builder", "planning-workspace"):
		if not frappe.db.exists("Page", page_name):
			continue
		page = frappe.get_doc("Page", page_name)
		existing = {r.role for r in page.roles}
		if "Budget Officer" not in existing:
			page.append("roles", {"role": "Budget Officer"})
			page.save(ignore_permissions=True)
	frappe.db.commit()
	return {
		**base,
		"builder_route": f"/app/procurement-plan-builder?plan={plan}&finance_item={plan_item or ''}",
		"finance_item": plan_item,
		"finance_status": "Awaiting confirmation",
		"viewer_user": viewer,
	}


@frappe.whitelist()
def prepare_planning_finance_shortfall_ui() -> dict[str, Any]:
	"""Isolated 80/25/55 Awaiting task for PLN-UI-07A Playwright (no full MVP reset)."""
	from kentender_core.seeds.kentender_mvp_v1 import constants as C
	from kentender_procurement.procurement_planning.services.update_plan_item import (
		update_plan_item,
	)
	from kentender_procurement.procurement_planning.tests._gate01_helpers import (
		attach_demand_funding,
		make_test_budget_line,
	)

	frappe.only_for(("System Manager", "Administrator"))
	amount = flt(C.PLAN_ITEM_SCN_AMOUNT)
	hold_amount = 55_000_000.0
	base = prepare_planning_gate05_ui()
	plan = base["empty_draft_plan"]
	plan_item = base.get("plan_item")
	demand = base.get("eligible_demand")
	planner = "moh.planning.officer@example.test"
	hold_code = ""
	budget_code = ""
	demand_row: dict[str, Any] = {}
	if plan_item and demand:
		iv_name = frappe.db.get_value(
			"Procurement Plan Item Version", {"plan_item": plan_item}, "name"
		)
		if iv_name:
			frappe.db.set_value(
				"Procurement Plan Item Version",
				iv_name,
				"confirmed_estimate",
				amount,
				update_modified=False,
			)
		funding = make_test_budget_line(approved_amount=amount)
		budget_code = cstr(
			frappe.db.get_value("Budget", funding["budget"], "generated_reference") or ""
		)
		if not frappe.db.exists("Demand Funding Allocation", {"demand": demand}):
			attach_demand_funding(
				demand=demand,
				budget_line=funding["budget_line"],
				budget=funding["budget"],
				amount=amount,
			)
		demand_row = frappe.db.get_value(
			"Demand", demand, ["demand_code", "title"], as_dict=True
		) or {}
		hold_code = f"RSV-PLN-UI07A-{frappe.generate_hash(length=6).upper()}"
		frappe.get_doc(
			{
				"doctype": "Funding Reservation",
				"generated_reference": hold_code,
				"budget": funding["budget"],
				"budget_line": funding["budget_line"],
				"original_amount": hold_amount,
				"remaining_reserved": hold_amount,
				"status": "Reserved",
				"currency": "KES",
				"demand_code": hold_code,
				"demand_title": "Concurrent workforce funding hold — scenario only",
				"event_date": C.FIXTURE_DATE,
				"plan_item_code": "",
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value(
			"Budget Line",
			funding["budget_line"],
			"amount_reserved",
			hold_amount,
			update_modified=True,
		)
		update_plan_item(plan_item=plan_item, user=planner, request_finance=True)
	for page_name in ("procurement-plan-builder", "planning-workspace"):
		if not frappe.db.exists("Page", page_name):
			continue
		page = frappe.get_doc("Page", page_name)
		existing = {r.role for r in page.roles}
		if "Budget Officer" not in existing:
			page.append("roles", {"role": "Budget Officer"})
			page.save(ignore_permissions=True)
	frappe.db.commit()
	return {
		"ok": True,
		"empty_draft_plan": plan,
		"plan": plan,
		"finance_item": plan_item,
		"builder_route": f"/app/procurement-plan-builder?plan={plan}&finance_item={plan_item or ''}",
		"budget_funding_route": (
			f"/app/budget-funding-activity/{budget_code}" if budget_code else "/app/budget-funding"
		),
		"hold": hold_code,
		"finance_status": "Awaiting confirmation",
		"amount_required": amount,
		"available": amount - hold_amount,
		"shortfall": hold_amount,
		"demand_title": demand_row.get("title") if plan_item and demand else "",
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
	from kentender_procurement.procurement_planning.services.submit_plan_for_review import (
		submit_plan_for_review,
	)
	from kentender_procurement.procurement_planning.services.validate_plan import (
		validate_plan,
	)
	from kentender_procurement.procurement_planning.tests._gate01_helpers import (
		complete_plan_item_for_signoff,
		confirm_included_items_funding,
	)

	frappe.only_for(("System Manager", "Administrator"))
	ensure_planning_roles()
	base = prepare_planning_gate05_ui()
	plan = base["empty_draft_plan"]
	plan_item = base.get("plan_item")
	planner = "moh.planning.officer@example.test"
	if plan_item:
		complete_plan_item_for_signoff(plan_item=plan_item, user=planner)
	confirm_included_items_funding(plan=plan, planner=planner)

	validate_plan(plan=plan, user=planner)

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
def prepare_planning_gate06_approved_ui(
	with_successor: int | str | None = 0,
	with_handoff: int | str | None = 0,
) -> dict[str, Any]:
	"""Approved V1 + planner/viewer for PLN-UI-09 Playwright (unique Plan per call)."""
	from frappe.utils.password import update_password

	from kentender_core.seeds.constants import TEST_PASSWORD
	from kentender_procurement.procurement_planning.services.add_demand_to_plan import (
		add_demand_to_plan,
	)
	from kentender_procurement.procurement_planning.services.create_planning_handoff_snapshot import (
		create_planning_handoff_snapshot,
	)
	from kentender_procurement.procurement_planning.services.planning_permissions import (
		ROLE_VIEWER,
		ensure_planning_roles,
	)
	from kentender_procurement.procurement_planning.tests._gate01_helpers import (
		approve_plan_via_gate05,
		complete_plan_item_for_signoff,
		confirm_included_items_funding,
		create_plan_as_planner,
		make_approved_demand,
		purge_pe_fy,
		unique_test_fy,
	)

	frappe.only_for(("System Manager", "Administrator"))
	ensure_planning_roles()
	from kentender_procurement.procurement_planning.tests._gate02_helpers import PE_MOH

	pe_moh = PE_MOH
	planner = "moh.planning.officer@example.test"
	viewer = "pln.ui.viewer@example.test"
	if not frappe.db.exists("User", viewer):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": viewer,
				"first_name": "MOH",
				"last_name": "Viewer",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", viewer)
	user.enabled = 1
	user.save(ignore_permissions=True)
	user.add_roles("Desk User", ROLE_VIEWER)
	update_password(viewer, TEST_PASSWORD)
	for name in frappe.get_all(
		"User Scope Assignment",
		filters={"user": viewer, "role": ROLE_VIEWER},
		pluck="name",
	):
		frappe.delete_doc("User Scope Assignment", name, force=1, ignore_permissions=True)
	frappe.get_doc(
		{
			"doctype": "User Scope Assignment",
			"user": viewer,
			"role": ROLE_VIEWER,
			"procuring_entity": pe_moh,
			"organisation_unit": "",
			"include_descendants": 0,
		}
	).insert(ignore_permissions=True)

	fy = unique_test_fy(base_year=3400)
	purge_pe_fy(fy)
	created = create_plan_as_planner(title="UI-09 Approved Plan", financial_year=fy)
	plan = created["plan"]
	version = created["version"]
	demand = make_approved_demand(title="UI-09 approved Demand")
	added = add_demand_to_plan(plan=plan, demand=demand["demand"], user=planner)
	plan_item = added.get("plan_item")
	if plan_item:
		complete_plan_item_for_signoff(plan_item=plan_item, user=planner)
	confirm_included_items_funding(plan=plan, planner=planner)
	approved = approve_plan_via_gate05(plan=plan, version=version)
	if not approved.get("ok"):
		frappe.throw(f"Gate06 approved prep: approve failed: {approved}")

	for page_name in ("procurement-plan-approved", "procurement-plan-update"):
		if not frappe.db.exists("Page", page_name):
			continue
		page = frappe.get_doc("Page", page_name)
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

	want_successor = str(with_successor or "0") not in ("0", "", "None")
	want_handoff = str(with_handoff or "0") not in ("0", "", "None")
	if want_handoff and plan_item:
		frappe.set_user(planner)
		try:
			snap = create_planning_handoff_snapshot(
				plan_item=plan_item,
				tender_reference="TND-MOH-TEST-008",
				user=planner,
			)
		finally:
			frappe.set_user("Administrator")
		if not snap.get("ok"):
			frappe.throw(f"Gate06 approved prep: handoff failed: {snap}")

	if want_successor:
		extra = make_approved_demand(title="Gate06 successor Demand")
		added2 = add_demand_to_plan(plan=plan, demand=extra["demand"], user=planner)
		if not added2.get("ok"):
			frappe.throw(f"Gate06 approved prep: successor add failed: {added2}")

	frappe.db.commit()
	return {
		"ok": True,
		"pe_moh": pe_moh,
		"empty_draft_plan": plan,
		"plan_item": plan_item,
		"approved": True,
		"approved_version": version,
		"approved_route": f"/app/procurement-plan-approved?plan={plan}",
		"viewer_user": viewer,
		"has_successor": want_successor,
		"has_handoff": want_handoff,
		"update_route": f"/app/procurement-plan-update?plan={plan}"
		if want_successor
		else f"/app/procurement-plan-approved?plan={plan}",
	}


@frappe.whitelist()
def prepare_planning_scn_add_ui() -> dict[str, Any]:
	"""Canonical SCN-ADD stop_before_finance for AC-013 Playwright."""
	from kentender_core.seeds.kentender_mvp_v1 import constants as C
	from kentender_procurement.procurement_planning.seeds import scn_pln_add_001 as scn

	frappe.only_for(("System Manager", "Administrator"))
	prepared = scn.run(reset_first=True, force=True, stop_before_finance=True)
	if not prepared.get("ok"):
		frappe.throw(f"SCN-ADD prepare failed: {prepared}")
	plan = frappe.db.get_value(
		"Procurement Plan", {"plan_code": C.PROCUREMENT_PLAN_CODE}, "name"
	)
	frappe.db.commit()
	return {
		"ok": True,
		"plan": plan,
		"plan_code": C.PROCUREMENT_PLAN_CODE,
		"stopped_before_finance": True,
		"approved_route": f"/app/procurement-plan-approved?plan={plan}",
		"update_route": f"/app/procurement-plan-update?plan={plan}",
		"tender_code": C.TENDER_CODE,
		"draft_total": C.PLAN_AMOUNT_V2,
		"approved_total": C.PLAN_AMOUNT_V1,
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
