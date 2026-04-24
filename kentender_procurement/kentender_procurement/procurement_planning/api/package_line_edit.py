# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Package line CRUD helpers for the D4 builder (Desk Form)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, flt

from kentender_procurement.procurement_planning.api.landing import (
	_can_read_planning,
	resolve_pp_role_key,
)
from kentender_procurement.procurement_planning.doctype.procurement_package_line.procurement_package_line import (
	PACKAGE_EDITABLE_STATUSES,
)
from kentender_procurement.procurement_planning.permissions import pp_policy

_LINE_FIELDS = [
	"name",
	"package_id",
	"demand_id",
	"budget_line_id",
	"amount",
	"department",
	"priority",
	"quantity",
	"is_active",
]


def _fail(*, code: str, message: str, role_key: str = "auditor") -> dict:
	return {"ok": False, "error_code": code, "message": str(message), "role_key": role_key, "lines": []}


def _planning_gate() -> tuple[str | None, dict | None]:
	if not frappe.db.exists("DocType", "Procurement Plan"):
		return None, _fail(
			code="PP_NOT_INSTALLED",
			message=_("Procurement Planning is not installed on this site (missing DocTypes)."),
		)
	role_key = resolve_pp_role_key()
	if not role_key or not _can_read_planning():
		return None, _fail(
			code="PP_ACCESS_DENIED",
			message=_("You do not have access to the Procurement Planning workbench."),
			role_key=role_key or "auditor",
		)
	return role_key, None


def _require_package(package: str) -> tuple[frappe.model.document.Document | None, dict | None]:
	pkg = (package or "").strip()
	if not pkg:
		return None, _fail(code="NOT_FOUND", message=_("Package not found."))
	if not frappe.db.exists("Procurement Package", pkg):
		return None, _fail(code="NOT_FOUND", message=_("Package not found."))
	try:
		if not frappe.has_permission("Procurement Package", "read", pkg):
			return None, _fail(
				code="NO_PACKAGE_PERMISSION",
				message=_("You do not have permission to view this package."),
			)
	except frappe.PermissionError:
		return None, _fail(
			code="NO_PACKAGE_PERMISSION",
			message=_("You do not have permission to view this package."),
		)
	doc = frappe.get_doc("Procurement Package", pkg)
	doc.check_permission("read")
	return doc, None


def _require_package_write(package: str) -> tuple[frappe.model.document.Document | None, dict | None]:
	doc, err = _require_package(package)
	if err or not doc:
		return doc, err
	try:
		doc.check_permission("write")
	except frappe.PermissionError:
		return None, _fail(
			code="NO_PACKAGE_PERMISSION",
			message=_("You do not have permission to edit this package."),
		)
	return doc, None


@frappe.whitelist()
def get_pp_package_lines(package: str | None = None) -> dict:
	"""List active package lines for the builder table."""
	role_key, gate_err = _planning_gate()
	if gate_err:
		return gate_err
	assert role_key is not None

	doc, err = _require_package((package or "").strip())
	if err or not doc:
		return err or _fail(code="NOT_FOUND", message=_("Package not found."), role_key=role_key)

	lines = frappe.get_all(
		"Procurement Package Line",
		filters={"package_id": doc.name, "is_active": 1},
		fields=_LINE_FIELDS,
		order_by="idx asc, creation asc",
		limit_page_length=500,
	)
	demand_ids = list({str(ln["demand_id"]) for ln in lines if ln.get("demand_id")})
	demand_titles: dict[str, str] = {}
	if demand_ids:
		for row in frappe.get_all(
			"Demand",
			filters={"name": ("in", demand_ids)},
			fields=["name", "demand_id", "title"],
			limit_page_length=500,
		):
			demand_titles[row.name] = row.title or row.demand_id or row.name
		missing = [d for d in demand_ids if d not in demand_titles]
		if missing:
			for row in frappe.get_all(
				"Demand",
				filters={"demand_id": ("in", missing)},
				fields=["name", "demand_id", "title"],
				limit_page_length=500,
			):
				demand_titles[row.name] = row.title or row.demand_id or row.name

	out = []
	for ln in lines:
		did = ln.get("demand_id")
		biz = frappe.db.get_value("Demand", did, "demand_id") if did else None
		out.append(
			{
				**ln,
				"demand_business_id": (biz or did or ""),
				"demand_title": demand_titles.get(did, "") if did else "",
			}
		)

	return {"ok": True, "role_key": role_key, "package": doc.name, "lines": out}

@frappe.whitelist()
def list_pp_assignable_demands(
	package: str | None = None,
	search_text: str | None = None,
	start: int | str | None = 0,
	page_length: int | str | None = 50,
) -> dict:
	"""List eligible demands that can be assigned to a package in workbench."""
	role_key, gate_err = _planning_gate()
	if gate_err:
		return gate_err
	assert role_key is not None

	doc, err = _require_package_write((package or "").strip())
	if err or not doc:
		return err or _fail(code="NOT_FOUND", message=_("Package not found."), role_key=role_key)

	try:
		pp_policy.assert_may_edit_package_lines(doc)
	except frappe.PermissionError:
		return _fail(
			code="NO_PACKAGE_PERMISSION",
			message=_("You do not have permission to edit package lines."),
			role_key=role_key,
		)

	st = doc.status or ""
	if st not in PACKAGE_EDITABLE_STATUSES:
		return _fail(
			code="PACKAGE_LOCKED",
			message=_("Package lines can only be managed while the package is Draft, Completed, or Returned."),
			role_key=role_key,
		)

	plan = frappe.db.get_value(
		"Procurement Plan",
		doc.plan_id,
		["name", "fiscal_year", "procuring_entity"],
		as_dict=True,
	)
	if not plan:
		return _fail(code="NOT_FOUND", message=_("Procurement plan not found."), role_key=role_key)

	budget_filters = {"is_active": 1}
	if plan.get("fiscal_year") is not None:
		budget_filters["fiscal_year"] = plan.get("fiscal_year")
	if plan.get("procuring_entity"):
		budget_filters["procuring_entity"] = plan.get("procuring_entity")
	budget_rows = frappe.get_all(
		"Budget Line",
		filters=budget_filters,
		fields=["name", "budget_line_code", "budget_line_name"],
		limit_page_length=5000,
	)
	if not budget_rows:
		return {"ok": True, "role_key": role_key, "package": doc.name, "total": 0, "demands": []}

	budget_ids = [b.name for b in budget_rows if b.get("name")]
	budget_map = {b.name: b for b in budget_rows if b.get("name")}

	active_lines = frappe.get_all(
		"Procurement Package Line",
		filters={"is_active": 1},
		fields=["demand_id"],
		limit_page_length=5000,
	)
	assigned_demand_ids = {str(x.get("demand_id")) for x in active_lines if x.get("demand_id")}

	demand_filters = {
		"status": ("in", ["Approved", "Planning Ready"]),
		"budget_line": ("in", budget_ids),
		"total_amount": (">", 0),
	}
	if assigned_demand_ids:
		demand_filters["name"] = ("not in", list(assigned_demand_ids))

	demand_rows = frappe.get_all(
		"Demand",
		filters=demand_filters,
		fields=[
			"name",
			"demand_id",
			"title",
			"requesting_department",
			"total_amount",
			"status",
			"budget_line",
			"priority_level",
			"modified",
		],
		order_by="modified desc",
		limit_page_length=5000,
	)

	q = (search_text or "").strip().lower()
	if q:
		demand_rows = [
			r
			for r in demand_rows
			if q in str(r.get("demand_id") or "").lower()
			or q in str(r.get("title") or "").lower()
			or q in str(r.get("requesting_department") or "").lower()
		]

	total = len(demand_rows)
	off = max(cint(start or 0), 0)
	lim = cint(page_length or 50)
	if lim <= 0:
		lim = 50
	if lim > 200:
		lim = 200
	sliced = demand_rows[off : off + lim]

	out = []
	for row in sliced:
		bl = budget_map.get(row.get("budget_line")) if row.get("budget_line") else None
		bl_display = ""
		if bl:
			bl_display = f"{bl.budget_line_code or ''} — {bl.budget_line_name or ''}".strip(" —")
		out.append(
			{
				"name": row.get("name") or "",
				"demand_id": row.get("demand_id") or row.get("name") or "",
				"title": row.get("title") or "",
				"department": row.get("requesting_department") or "",
				"amount": flt(row.get("total_amount")),
				"status": row.get("status") or "",
				"priority": row.get("priority_level") or "Normal",
				"budget_line_id": row.get("budget_line") or "",
				"budget_line": bl_display,
			}
		)

	return {
		"ok": True,
		"role_key": role_key,
		"package": doc.name,
		"total": total,
		"demands": out,
	}


@frappe.whitelist()
def add_pp_package_line(
	package: str | None = None,
	demand_id: str | None = None,
	budget_line_id: str | None = None,
	amount: float | None = None,
	department: str | None = None,
	priority: str | None = None,
	quantity: float | None = None,
):
	"""Insert one active package line (Draft / Completed / Returned package only)."""
	role_key, gate_err = _planning_gate()
	if gate_err:
		return gate_err
	assert role_key is not None

	doc, err = _require_package_write((package or "").strip())
	if err or not doc:
		return err or _fail(code="NOT_FOUND", message=_("Package not found."), role_key=role_key)

	try:
		pp_policy.assert_may_edit_package_lines(doc)
	except frappe.PermissionError:
		return _fail(
			code="NO_PACKAGE_PERMISSION",
			message=_("You do not have permission to edit package lines."),
			role_key=role_key,
		)

	st = doc.status or ""
	if st not in PACKAGE_EDITABLE_STATUSES:
		return _fail(
			code="PACKAGE_LOCKED",
			message=_("Package lines can only be added while the package is Draft, Completed, or Returned."),
			role_key=role_key,
		)

	did = (demand_id or "").strip()
	bid = (budget_line_id or "").strip()
	if did and not frappe.db.exists("Demand", did):
		resolved = frappe.db.get_value("Demand", {"demand_id": did}, "name")
		if resolved:
			did = resolved
	if not did or not bid:
		return _fail(
			code="MISSING_PARAMS",
			message=_("Demand and Budget Line are required."),
			role_key=role_key,
		)
	amt = flt(amount)
	if amt <= 0:
		return _fail(code="INVALID_AMOUNT", message=_("Amount must be greater than zero."), role_key=role_key)

	dept = (department or "").strip()
	if not dept:
		dept = frappe.db.get_value("Demand", did, "requesting_department") or ""

	prio = (priority or "").strip() or "Normal"
	qty = flt(quantity)
	if qty <= 0:
		qty = 1.0

	line = frappe.get_doc(
		{
			"doctype": "Procurement Package Line",
			"package_id": doc.name,
			"demand_id": did,
			"budget_line_id": bid,
			"amount": amt,
			"department": dept,
			"priority": prio,
			"quantity": qty,
			"is_active": 1,
		}
	)
	line.insert()
	return {"ok": True, "role_key": role_key, "name": line.name, "package": doc.name}


@frappe.whitelist()
def remove_pp_package_line(line_name: str | None = None):
	"""Soft-deactivate a package line (sets is_active=0)."""
	role_key, gate_err = _planning_gate()
	if gate_err:
		return gate_err
	assert role_key is not None

	lname = (line_name or "").strip()
	if not lname or not frappe.db.exists("Procurement Package Line", lname):
		return _fail(code="NOT_FOUND", message=_("Line not found."), role_key=role_key)

	package_id = frappe.db.get_value("Procurement Package Line", lname, "package_id")
	if not package_id:
		return _fail(code="NOT_FOUND", message=_("Line not found."), role_key=role_key)

	doc, err = _require_package_write(package_id)
	if err or not doc:
		return err or _fail(code="NOT_FOUND", message=_("Package not found."), role_key=role_key)

	try:
		pp_policy.assert_may_edit_package_lines(doc)
	except frappe.PermissionError:
		return _fail(
			code="NO_PACKAGE_PERMISSION",
			message=_("You do not have permission to edit package lines."),
			role_key=role_key,
		)

	st = doc.status or ""
	if st not in PACKAGE_EDITABLE_STATUSES:
		return _fail(
			code="PACKAGE_LOCKED",
			message=_("Package lines can only be removed while the package is Draft, Completed, or Returned."),
			role_key=role_key,
		)

	line = frappe.get_doc("Procurement Package Line", lname)
	if line.package_id != doc.name:
		return _fail(code="NOT_FOUND", message=_("Line not found."), role_key=role_key)

	line.check_permission("write")
	line.is_active = 0
	line.save()

	from kentender_procurement.procurement_planning.doctype.procurement_package.procurement_package import (
		recompute_package_estimated_value,
	)

	recompute_package_estimated_value(doc.name)
	return {"ok": True, "role_key": role_key, "name": lname, "package": doc.name}
