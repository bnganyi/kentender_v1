# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Whitelisted Desk APIs for Procurement Planning MVP-1 UI (Gate 03–04)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import add_days, cstr, flt

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
from kentender_procurement.procurement_planning.services.approve_plan_version import (
	approve_plan_version as _approve_plan_version,
	return_plan_version as _return_plan_version,
)
from kentender_procurement.procurement_planning.services.remove_plan_item import (
	cancel_plan_update as _cancel_plan_update,
	get_plan_item_removal as _get_plan_item_removal,
	remove_plan_item_from_plan as _remove_plan_item_from_plan,
)
from kentender_procurement.procurement_planning.services.get_plan_review import (
	get_plan_review as _get_plan_review,
)
from kentender_procurement.procurement_planning.services.get_plan_implementation import (
	get_plan_implementation as _get_plan_implementation,
)
from kentender_procurement.procurement_planning.services.plan_builder_successor import (
	save_plan_draft as _save_plan_draft,
)
from kentender_procurement.procurement_planning.services.create_planning_handoff_snapshot import (
	create_planning_handoff_snapshot as _create_planning_handoff_snapshot,
)


def _mark_playwright_demand_graph(demand: str) -> None:
	"""Tag a Demand created by a browser fixture without touching business records."""
	if not demand or not frappe.db.exists("Demand", demand):
		return
	from kentender_core.seeds.kentender_mvp_v1 import constants as C

	for doctype in (
		"Demand",
		"Demand Item",
		"Demand Decision",
		"Demand Strategy Reference",
		"Demand Value Treatment",
		"Demand Funding Allocation",
		"Funding Exception",
		"Planning Consumption",
	):
		if not frappe.db.exists("DocType", doctype) or not frappe.db.has_column(
			doctype, "fixture_namespace"
		):
			continue
		names = [demand] if doctype == "Demand" else frappe.get_all(
			doctype, filters={"demand": demand}, pluck="name"
		)
		for name in names:
			frappe.db.set_value(
				doctype,
				name,
				"fixture_namespace",
				C.PLAYWRIGHT_FIXTURE_NS,
				update_modified=False,
			)


def _mark_playwright_plan_graph(plan: str, *demands: str | None) -> None:
	from kentender_core.seeds.kentender_mvp_v1 import constants as C
	from kentender_procurement.procurement_planning.seeds.kentender_mvp_v1 import (
		mark_plan_graph_fixture,
	)

	mark_plan_graph_fixture(plan, C.PLAYWRIGHT_FIXTURE_NS)
	for demand in demands:
		if demand:
			_mark_playwright_demand_graph(demand)


@frappe.whitelist()
def get_planning_workspace(
	procuring_entity: str | None = None,
	financial_year: str | None = None,
	work_filter: str | None = "all",
	search: str | None = None,
) -> dict[str, Any]:
	return _get_planning_workspace(
		procuring_entity=procuring_entity,
		financial_year=financial_year,
		work_filter=work_filter,
		search=search,
	)


@frappe.whitelist()
def get_planning_create_scope(
	procuring_entity: str | None = None,
	financial_year: str | None = None,
) -> dict[str, Any]:
	return _get_planning_create_scope(
		procuring_entity=procuring_entity or "",
		financial_year=financial_year or "",
	)


@frappe.whitelist()
def create_procurement_plan(
	procuring_entity: str | None = None,
	financial_year: str | None = None,
) -> dict[str, Any]:
	"""Register from governed PE/FY identity; no client-authored snapshots."""
	errors: dict[str, str] = {}
	if not (procuring_entity or "").strip():
		errors["procuring_entity"] = "Procuring Entity is required"
	if not (financial_year or "").strip():
		errors["financial_year"] = "Financial year is required"
	if errors:
		return {"ok": False, "errors": errors}

	try:
		result = _create_procurement_plan(
			procuring_entity=procuring_entity or "",
			financial_year=financial_year or "",
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
		elif not isinstance(exc, (frappe.ValidationError, frappe.DuplicateEntryError)):
			raise
		return {"ok": False, "errors": {field: msg}}

	result["redirect"] = result.get("route") or f"/app/procurement-plan-builder?plan={result['plan']}"
	return result


@frappe.whitelist()
def get_plan_builder(
	plan: str | None = None,
	organisation_unit: str | None = None,
	status: str | None = None,
	search: str | None = None,
) -> dict[str, Any]:
	return _get_plan_builder(
		plan=plan or "", organisation_unit=organisation_unit, status=status, search=search
	)


@frappe.whitelist()
def list_eligible_demands(
	plan: str | None = None,
	search: str | None = None,
	organisation_unit: str | None = None,
	requested_demand: str | None = None,
) -> dict[str, Any]:
	return _list_eligible_demands(
		plan=plan or "",
		search=search,
		organisation_unit=organisation_unit,
		requested_demand=requested_demand,
	)


@frappe.whitelist()
def add_demand_to_plan(
	plan: str | None = None,
	demands: str | list | None = None,
	expected_version_token: str | None = None,
	formation_mode: str | None = None,
	formation_reason: str | None = None,
	idempotency_key: str | None = None,
) -> dict[str, Any]:
	try:
		return _add_demand_to_plan(
			plan=plan or "",
			demands=demands,
			expected_version_token=expected_version_token,
			formation_mode=formation_mode,
			formation_reason=formation_reason,
			idempotency_key=idempotency_key,
		)
	except Exception as exc:
		msg = str(exc)
		title = getattr(exc, "title", None) or ""
		errors: dict[str, str] = {"form": msg}
		title_u = cstr(title).upper()
		if "FORMATION_REASON" in title_u or "reason for combining" in msg.lower():
			errors["formation_reason"] = msg
		return {"ok": False, "errors": errors}


@frappe.whitelist()
def get_plan_item_removal(
	plan: str | None = None,
	plan_item: str | None = None,
) -> dict[str, Any]:
	return _get_plan_item_removal(plan=plan or "", plan_item=plan_item or "")


@frappe.whitelist()
def remove_plan_item_from_plan(
	plan: str | None = None,
	plan_item: str | None = None,
	reason: str | None = None,
	draft_version: str | None = None,
	expected_version_token: str | None = None,
	idempotency_key: str | None = None,
	concurrency_token: str | None = None,
) -> dict[str, Any]:
	try:
		return _remove_plan_item_from_plan(
			plan=plan or "",
			plan_item=plan_item or "",
			reason=reason,
			draft_version=draft_version,
			expected_version_token=expected_version_token,
			idempotency_key=idempotency_key,
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
	expected_version_token: str | None = None,
	idempotency_key: str | None = None,
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
			expected_version_token=expected_version_token,
			idempotency_key=idempotency_key,
		)
	except frappe.PermissionError:
		raise
	except Exception as exc:
		return {"ok": False, "errors": {"form": str(exc)}}


@frappe.whitelist()
def get_plan_finance_task(task: str | None = None) -> dict[str, Any]:
	return _get_plan_finance_task(task=task or "")


@frappe.whitelist()
def confirm_plan_item_funding(
	task: str | None = None,
	expected_token: str | None = None,
	note: str | None = None,
	idempotency_key: str | None = None,
) -> dict[str, Any]:
	return _confirm_plan_item_funding(task=task or "", expected_token=expected_token, note=note, idempotency_key=idempotency_key)


@frappe.whitelist()
def return_plan_item_from_finance(
	task: str | None = None,
	expected_token: str | None = None,
	reason: str | None = None,
	idempotency_key: str | None = None,
) -> dict[str, Any]:
	return _return_plan_item_from_finance(task=task or "", expected_token=expected_token, reason=reason, idempotency_key=idempotency_key)


@frappe.whitelist()
def get_plan_item_editor(plan_item: str | None = None) -> dict[str, Any]:
	return _get_plan_item_editor(plan_item=plan_item or "")


@frappe.whitelist()
def validate_plan(plan: str | None = None) -> dict[str, Any]:
	return _validate_plan(plan=plan or "")


@frappe.whitelist()
def submit_plan_for_review(
	plan: str | None = None,
	expected_token: str | None = None,
	idempotency_key: str | None = None,
	concurrency_token: str | None = None,
) -> dict[str, Any]:
	return _submit_plan_for_review(
		plan=plan or "",
		expected_token=expected_token or concurrency_token,
		idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def approve_plan_version(
	task: str | None = None,
	expected_token: str | None = None,
	note: str | None = None,
	idempotency_key: str | None = None,
) -> dict[str, Any]:
	try:
		return _approve_plan_version(
			task=task or "",
			expected_token=expected_token,
			reason=note,
			idempotency_key=idempotency_key,
		)
	except frappe.PermissionError as exc:
		return {
			"ok": False,
			"errors": {"form": str(exc).split(":", 1)[-1].strip() or "Not permitted"},
		}
	except Exception as exc:
		return {"ok": False, "errors": {"form": str(exc)}}


@frappe.whitelist()
def return_plan_version(
	task: str | None = None,
	expected_token: str | None = None,
	reason: str | None = None,
	idempotency_key: str | None = None,
) -> dict[str, Any]:
	try:
		return _return_plan_version(task=task or "", expected_token=expected_token, reason=reason, idempotency_key=idempotency_key)
	except frappe.PermissionError:
		raise
	except Exception as exc:
		return {"ok": False, "errors": {"form": str(exc)}}


@frappe.whitelist()
def get_plan_review(task: str | None = None) -> dict[str, Any]:
	return _get_plan_review(task=task or "")


@frappe.whitelist()
def get_plan_implementation(plan: str | None = None) -> dict[str, Any]:
	return _get_plan_implementation(plan=plan or "")


@frappe.whitelist()
def save_plan_draft(
	plan: str | None = None,
	update_reason: str | None = None,
	expected_version_token: str | None = None,
	idempotency_key: str | None = None,
) -> dict[str, Any]:
	try:
		return _save_plan_draft(
			plan=plan or "",
			update_reason=update_reason,
			expected_version_token=expected_version_token,
			idempotency_key=idempotency_key,
		)
	except frappe.PermissionError as exc:
		return {
			"ok": False,
			"errors": {"form": str(exc).split(":", 1)[-1].strip() or "Not permitted"},
		}
	except Exception as exc:
		return {"ok": False, "errors": {"form": str(exc)}}

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
	return _aggregate_plan_allocations(
		plan_item=plan_item or "",
		demand=demand or "",
		demand_item=demand_item,
		allocated_amount=amt,
		aggregation_reason=aggregation_reason,
	)


@frappe.whitelist()
def prepare_planning_gate04_ui(
	with_plan_item: int | str | None = 0,
	need_item_count: int | str | None = 1,
	eligible_count: int | str | None = 1,
	mixed_ou: int | str | None = 0,
	item_total: float | str | None = 48_000_000.0,
) -> dict[str, Any]:
	"""Resettable FY2028/29 initial Plan and exact approved-Demand sources.

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
		attach_demand_funding,
		make_approved_demand,
		make_test_budget_line,
	)

	base = prepare_planning_gate03_ui(clear_create_fy="2028/29")
	planner = "moh.planning.officer@example.test"
	created = _create_procurement_plan(
		procuring_entity=base["pe_moh"], financial_year="2028/29", user=planner
	)
	plan = created["plan"]
	n_items = max(1, int(need_item_count or 1))
	n_eligible = max(1, int(eligible_count or 1))
	first_total = flt(item_total) or 48_000_000.0
	# The first exact design source is HRMD. Optional arguments retain the
	# narrower one-source variants used by focused interaction tests.
	from kentender_procurement.procurement_planning.tests._gate02_helpers import _ensure_ou
	_ensure_ou("MOH-DIR-HRMD", "Human Resources Management and Development", base["pe_moh"])
	d = make_approved_demand(
		pe=base["pe_moh"],
		ou="MOH-DIR-HRMD",
		title="Clinical training laptops for digital health rollout",
		need_item_count=n_items,
		item_amounts=([first_total / n_items] * n_items),
		demand_code="DMD-MOH-2028-001",
		required_by_date="2028-12-31",
	)
	funding1 = make_test_budget_line(
		approved_amount=first_total, fiscal_period="2028/29",
		start_date="2028-07-01", end_date="2029-06-30",
		title="Digital health workforce development",
		fixture_namespace="KENTENDER_PLAYWRIGHT",
	)
	attach_demand_funding(demand=d["demand"], budget_line=funding1["budget_line"], budget=funding1["budget"], amount=first_total)
	out: dict[str, Any] = {
		**base,
		"empty_draft_plan": plan,
		"empty_draft_plan_code": created["plan_code"],
		"empty_draft_fy": "2028/29",
		"eligible_demand": d["demand"],
		"eligible_demand_code": d["demand_code"],
		"need_item_count": n_items,
		"eligible_count": n_eligible,
		"builder_route": f"/app/procurement-plan-builder?plan={plan}",
	}
	if n_eligible >= 2:
		second_ou = "MOH-DIR-DHP" if int(mixed_ou or 0) else "MOH-DIR-HRMD"
		d2 = make_approved_demand(
			pe=base["pe_moh"],
			ou=second_ou,
			title="Clinical deployment laptops for digital health rollout",
			need_item_count=2,
			item_amounts=[36_000_000.0, 36_000_000.0],
			demand_code="DMD-MOH-2028-002",
			required_by_date="2028-12-31",
		)
		funding2 = make_test_budget_line(
			approved_amount=72_000_000.0, fiscal_period="2028/29",
			start_date="2028-07-01", end_date="2029-06-30",
			title="Digital clinical systems infrastructure",
			fixture_namespace="KENTENDER_PLAYWRIGHT",
		)
		attach_demand_funding(demand=d2["demand"], budget_line=funding2["budget_line"], budget=funding2["budget"], amount=72_000_000.0)
		out["eligible_demand_2"] = d2["demand"]
		out["eligible_demand_code_2"] = d2["demand_code"]
		out["mixed_ou"] = bool(int(mixed_ou or 0))
		out["eligible_demand_2_ou"] = second_ou
	if int(with_plan_item or 0):
		focus = frappe.db.get_value("Procurement Plan", plan, "open_draft_version")
		token = frappe.db.get_value("Procurement Plan Version", focus, "concurrency_token")
		selected_demands = [d["demand"]]
		if n_eligible >= 2:
			selected_demands.append(d2["demand"])
		added = add_demand_to_plan(
			plan=plan,
			demands=selected_demands,
			expected_version_token=token,
			formation_mode="separate" if len(selected_demands) > 1 else None,
			idempotency_key=f"PW-GATE04-{plan}-{d['demand']}",
			user=planner,
		)
		out["plan_item"] = added.get("plan_item")
		out["plan_items"] = added.get("plan_items") or []
		out["editor_route"] = added.get("editor_route")
		out["plan_item_code"] = added.get("plan_item_code")
	_mark_playwright_plan_graph(
		plan,
		d["demand"],
		out.get("eligible_demand_2"),
	)
	frappe.db.commit()
	return out


@frappe.whitelist()
def prepare_planning_gate05_ui(item_total: float | str | None = 48_000_000.0) -> dict[str, Any]:
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
	base = prepare_planning_gate04_ui(with_plan_item=1, need_item_count=1, item_total=item_total)
	plan = base["empty_draft_plan"]
	plan_item = base.get("plan_item")
	planner = "moh.planning.officer@example.test"
	if plan_item:
		complete_plan_item_for_signoff(plan_item=plan_item, user=planner)
		validate_plan(plan=plan, user=planner)

	_mark_playwright_plan_graph(plan, base.get("eligible_demand"))
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
		draft = frappe.db.get_value("Procurement Plan", plan, "open_draft_version")
		token = frappe.db.get_value("Procurement Plan Version", draft, "concurrency_token")
		requested = update_plan_item(plan_item=plan_item, user=planner, request_finance=True, expected_version_token=token, idempotency_key=f"PW-GATE05-FINANCE-{plan_item}-{token}")
		if not requested.get("ok"):
			frappe.throw(f"Finance fixture request failed: {requested}")
	# BO must open SCREEN_5 (builder) and the workspace queue — Page.roles gate Desk.
	for page_name in ("procurement-plan-builder", "planning-workspace"):
		if not frappe.db.exists("Page", page_name):
			continue
		page = frappe.get_doc("Page", page_name)
		existing = {r.role for r in page.roles}
		if "Budget Officer" not in existing:
			page.append("roles", {"role": "Budget Officer"})
			page.save(ignore_permissions=True)
	_mark_playwright_plan_graph(plan, demand)
	item_version = frappe.db.get_value(
		"Procurement Plan Item", plan_item, "draft_item_version"
	) if plan_item else None
	finance_task = frappe.db.get_value(
		"Procurement Plan Item Version", item_version, "finance_task_id"
	) if item_version else None
	frappe.db.commit()
	return {
		**base,
		"builder_route": f"/app/procurement-plan-builder?plan={plan}&finance_task={finance_task or ''}",
		"finance_task": finance_task,
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
	frappe.only_for(("System Manager", "Administrator"))
	amount = flt(C.PLAN_ITEM_SCN_AMOUNT)
	hold_amount = 55_000_000.0
	base = prepare_planning_gate05_ui(item_total=amount)
	plan = base["empty_draft_plan"]
	plan_item = base.get("plan_item")
	demand = base.get("eligible_demand")
	planner = "moh.planning.officer@example.test"
	hold_code = ""
	budget_code = ""
	demand_row: dict[str, Any] = {}
	if plan_item and demand:
		funding = frappe.db.get_value(
			"Demand Funding Allocation",
			{"demand": demand},
			["budget", "budget_line"],
			as_dict=True,
		) or {}
		budget_code = cstr(
			frappe.db.get_value("Budget", funding.get("budget"), "generated_reference") or ""
		)
		# prepare_planning_gate05_ui created the exact KES 80m source and funding
		# lineage. The shortfall fixture adds only the isolated competing hold.
		demand_row = frappe.db.get_value(
			"Demand", demand, ["demand_code", "title"], as_dict=True
		) or {}
		hold_code = f"RSV-PLN-UI07A-{frappe.generate_hash(length=6).upper()}"
		frappe.get_doc(
			{
				"doctype": "Funding Reservation",
				"generated_reference": hold_code,
				"budget": funding.get("budget"),
				"budget_line": funding.get("budget_line"),
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
			funding.get("budget_line"),
			"amount_reserved",
			hold_amount,
			update_modified=True,
		)
		draft = frappe.db.get_value("Procurement Plan", plan, "open_draft_version")
		token = frappe.db.get_value("Procurement Plan Version", draft, "concurrency_token")
		requested = update_plan_item(plan_item=plan_item, user=planner, request_finance=True, expected_version_token=token, idempotency_key=f"PW-GATE05-SHORT-{plan_item}-{token}")
		if not requested.get("ok"):
			frappe.throw(f"Finance shortfall fixture request failed: {requested}")
	for page_name in ("procurement-plan-builder", "planning-workspace"):
		if not frappe.db.exists("Page", page_name):
			continue
		page = frappe.get_doc("Page", page_name)
		existing = {r.role for r in page.roles}
		if "Budget Officer" not in existing:
			page.append("roles", {"role": "Budget Officer"})
			page.save(ignore_permissions=True)
	_mark_playwright_plan_graph(plan, demand)
	item_version = frappe.db.get_value(
		"Procurement Plan Item", plan_item, "draft_item_version"
	) if plan_item else None
	finance_task = frappe.db.get_value(
		"Procurement Plan Item Version", item_version, "finance_task_id"
	) if item_version else None
	frappe.db.commit()
	return {
		"ok": True,
		"empty_draft_plan": plan,
		"plan": plan,
		"finance_task": finance_task,
		"builder_route": f"/app/procurement-plan-builder?plan={plan}&finance_task={finance_task or ''}",
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
	"""In-review professional task for the focused PLN-UI-08 browser fixture."""
	from frappe.utils.password import update_password

	from kentender_core.seeds.constants import TEST_PASSWORD
	from kentender_procurement.procurement_planning.services.planning_permissions import (
		ROLE_DESIGNATED_APPROVER,
		ROLE_VIEWER,
		ensure_planning_roles,
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
	sub = submit_plan_for_review(plan=plan, expected_token=token, idempotency_key=f"PW-GATE05-SUBMIT-{version}", user=planner)
	if not sub.get("ok"):
		frappe.throw(f"Gate05 approval prep: submit for review failed: {sub}")

	approver = "moh.procurement.authority@example.test"
	viewer = "pln.ui.viewer@example.test"
	for email, role, first, last in (
		(approver, ROLE_DESIGNATED_APPROVER, "Grace", "Wanjiku"),
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

	bo = "moh.budget.officer@example.test"
	if frappe.db.exists("User", bo):
		bo_user = frappe.get_doc("User", bo)
		bo_user.enabled = 1
		bo_user.save(ignore_permissions=True)
		bo_user.add_roles("Desk User", ROLE_VIEWER)
		update_password(bo, TEST_PASSWORD)
		if not frappe.db.exists(
			"User Scope Assignment",
			{"user": bo, "role": ROLE_VIEWER, "procuring_entity": base["pe_moh"]},
		):
			frappe.get_doc(
				{
					"doctype": "User Scope Assignment",
					"user": bo,
					"role": ROLE_VIEWER,
					"procuring_entity": base["pe_moh"],
					"organisation_unit": "",
					"include_descendants": 0,
				}
			).insert(ignore_permissions=True)

	_mark_playwright_plan_graph(plan, base.get("eligible_demand"))
	frappe.db.commit()
	return {
		**base,
		"approver_user": approver,
		"viewer_user": viewer,
		"version": version,
		"review_task": sub.get("task"),
		"review_route": f"/app/procurement-plan-review?task={sub.get('task')}",
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
		ensure_tender_initiator,
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
	required_by = add_days(frappe.db.get_value("Procurement Plan", plan, "period_start"), 180)
	demand = make_approved_demand(title="UI-09 approved Demand", required_by_date=required_by)
	token = frappe.db.get_value("Procurement Plan Version", version, "concurrency_token")
	added = add_demand_to_plan(
		plan=plan,
		demands=[demand["demand"]],
		expected_version_token=token,
		idempotency_key=f"PW-GATE06-{plan}-{demand['demand']}",
		user=planner,
	)
	plan_item = added.get("plan_item")
	if plan_item:
		complete_plan_item_for_signoff(plan_item=plan_item, user=planner)
	confirm_included_items_funding(plan=plan, planner=planner)
	approved = approve_plan_via_gate05(plan=plan, version=version)
	if not approved.get("ok"):
		frappe.throw(f"Gate06 approved prep: approve failed: {approved}")

	want_successor = str(with_successor or "0") not in ("0", "", "None")
	want_handoff = str(with_handoff or "0") not in ("0", "", "None")
	extra: dict[str, Any] = {}
	if want_handoff and plan_item:
		initiator = ensure_tender_initiator()
		frappe.set_user(initiator)
		try:
			snap = create_planning_handoff_snapshot(
				plan_item=plan_item,
				tender_reference="TND-MOH-TEST-008",
				user=initiator,
			)
		finally:
			frappe.set_user("Administrator")
		if not snap.get("ok"):
			frappe.throw(f"Gate06 approved prep: handoff failed: {snap}")

	if want_successor:
		extra = make_approved_demand(
			title="Gate06 successor Demand",
			required_by_date=required_by,
		)
		focus = frappe.db.get_value("Procurement Plan", plan, "open_draft_version") or version
		token = frappe.db.get_value("Procurement Plan Version", focus, "concurrency_token")
		added2 = add_demand_to_plan(
			plan=plan,
			demands=[extra["demand"]],
			expected_version_token=token,
			idempotency_key=f"PW-GATE06-SUCCESSOR-{plan}-{extra['demand']}",
			user=planner,
		)
		if not added2.get("ok"):
			frappe.throw(f"Gate06 approved prep: successor add failed: {added2}")

	_mark_playwright_plan_graph(
		plan,
		demand.get("demand"),
		extra.get("demand") if want_successor else None,
	)
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
		"update_route": f"/app/procurement-plan-builder?plan={plan}"
		if want_successor
		else f"/app/procurement-plan-approved?plan={plan}",
	}


@frappe.whitelist()
def prepare_planning_scn_add_ui(stop_point: str | None = None) -> dict[str, Any]:
	"""Prepare a deterministic SCN-ADD evidence boundary for Playwright."""
	from kentender_core.seeds.kentender_mvp_v1 import constants as C
	from kentender_procurement.procurement_planning.seeds import scn_pln_add_001 as scn

	frappe.only_for(("System Manager", "Administrator"))
	selected_stop = cstr(stop_point).strip()
	prepared = (
		scn.run(reset_first=True, force=True, stop_point=selected_stop)
		if selected_stop
		else scn.run(reset_first=True, force=True, stop_before_finance=True)
	)
	if not prepared.get("ok"):
		frappe.throw(f"SCN-ADD prepare failed: {prepared}")
	plan = frappe.db.get_value(
		"Procurement Plan", {"plan_code": C.PROCUREMENT_PLAN_CODE}, "name"
	)
	from kentender_procurement.procurement_planning.seeds.kentender_mvp_v1 import (
		mark_plan_graph_fixture,
	)

	mark_plan_graph_fixture(plan, C.FIXTURE_NS)
	frappe.db.commit()
	return {
		"ok": True,
		"stage": prepared.get("stage"),
		"plan": plan,
		"plan_code": C.PROCUREMENT_PLAN_CODE,
		"stopped_before_finance": bool(prepared.get("stopped_before_finance")),
		"approved_route": f"/app/procurement-plan-approved?plan={plan}",
		"update_route": f"/app/procurement-plan-builder?plan={plan}",
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
		ROLE_VIEWER,
		ensure_planning_roles,
	)

	frappe.only_for(("System Manager", "Administrator"))
	from kentender_core.seeds.kentender_mvp_v1.clear import purge_kentender_playwright_data

	purge_kentender_playwright_data(commit=False)
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
	_mark_playwright_plan_graph(fixture["plan"])

	# Gate-03 owns these disposable browser personas. The no-scope persona has
	# record-read capability but deliberately receives no scope assignment.
	for email, first, last, with_scope in (
		("pln.ui.viewer@example.test", "MOH", "Viewer", True),
		("pln.ui.no.scope@example.test", "No Scope", "Support", False),
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
		browser_user = frappe.get_doc("User", email)
		browser_user.enabled = 1
		browser_user.save(ignore_permissions=True)
		browser_user.add_roles("Desk User", ROLE_VIEWER)
		if not with_scope:
			# The zero-scope persona may reach create-capable pages so those pages
			# can render their server-derived blocked state; it still has no USA.
			browser_user.add_roles(ROLE_PLANNER)
		update_password(email, TEST_PASSWORD)
		for name in frappe.get_all(
			"User Scope Assignment",
			filters={
				"user": email,
				"role": ["in", [ROLE_VIEWER, ROLE_PLANNER]],
			},
			pluck="name",
		):
			frappe.delete_doc("User Scope Assignment", name, force=1, ignore_permissions=True)
		if with_scope:
			frappe.get_doc(
				{
					"doctype": "User Scope Assignment",
					"user": email,
					"role": ROLE_VIEWER,
					"procuring_entity": pe_moh,
					"organisation_unit": "",
					"include_descendants": 0,
				}
			).insert(ignore_permissions=True)

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
