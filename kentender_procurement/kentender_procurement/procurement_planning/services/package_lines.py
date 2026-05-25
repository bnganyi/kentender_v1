# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-007 — Package line traceability read service (PP2 UI §14)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.permissions import pp_scope
from kentender_procurement.procurement_planning.services.approved_demand_queue import (
	_budget_line_ref,
)


def _fail(*, code: str, message: str, role_key: str = "auditor") -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
	}


def _resolve_package_name(package_code: str) -> str | None:
	code = (package_code or "").strip()
	if not code:
		return None
	if frappe.db.exists("Procurement Package", code):
		return code
	name = frappe.db.get_value("Procurement Package", {"package_code": code}, "name")
	return str(name) if name else None


def _line_ref(code: str | None, *, fallback_name: str = "") -> dict[str, str]:
	value = (code or "").strip()
	if not value:
		return {"id": "", "code": "", "name": ""}
	return {"id": value, "code": value, "name": (fallback_name or value).strip()}



def format_package_line_rows(doc) -> list[dict[str, Any]]:
	"""Return active package lines with demand item → package line → budget refs."""
	rows = frappe.get_all(
		"Procurement Package Line",
		filters={"package_id": doc.name, "is_active": 1},
		fields=[
			"name",
			"package_line_code",
			"demand_item_code",
			"budget_line_id",
			"amount",
			"line_title",
			"quantity",
		],
		order_by="idx asc, creation asc",
		limit_page_length=200,
	)
	out: list[dict[str, Any]] = []
	for row in rows:
		item_code = (row.get("demand_item_code") or "").strip()
		line_code = (row.get("package_line_code") or row.get("name") or "").strip()
		line_title = (row.get("line_title") or line_code).strip()
		out.append(
			{
				"demand_item": _line_ref(item_code),
				"package_line": _line_ref(line_code, fallback_name=line_title),
				"budget_line": _budget_line_ref(row.get("budget_line_id")),
				"amount": flt(row.get("amount")),
				"quantity": flt(row.get("quantity")),
			}
		)
	return out


def _line_totals(lines: list[dict[str, Any]]) -> float:
	return flt(sum(flt(line.get("amount")) for line in lines))


def get_package_line_traceability(package_code: str, actor: str) -> dict[str, Any]:
	"""Return demand item → package line → budget mapping for a package."""
	actor = (actor or frappe.session.user or "").strip() or frappe.session.user
	role_key = resolve_pp_role_key(actor) or "auditor"

	if not frappe.db.exists("DocType", "Procurement Package"):
		return _fail(
			code="PP_NOT_INSTALLED",
			message="Procurement Planning is not installed on this site.",
			role_key=role_key,
		)

	pkg_name = _resolve_package_name(package_code)
	if not pkg_name:
		return _fail(code="NOT_FOUND", message="Package not found.", role_key=role_key)

	try:
		if not frappe.has_permission("Procurement Package", "read", pkg_name):
			return _fail(
				code="NO_PACKAGE_PERMISSION",
				message="You do not have permission to view this package.",
				role_key=role_key,
			)
	except frappe.PermissionError:
		return _fail(
			code="NO_PACKAGE_PERMISSION",
			message="You do not have permission to view this package.",
			role_key=role_key,
		)

	try:
		doc = frappe.get_doc("Procurement Package", pkg_name)
		doc.check_permission("read")
		pp_scope.assert_may_act_on_procurement_package(doc, user=actor)
	except frappe.DoesNotExistError:
		return _fail(code="NOT_FOUND", message="Package not found.", role_key=role_key)
	except frappe.PermissionError:
		return _fail(
			code="NO_PACKAGE_PERMISSION",
			message="You do not have permission to view this package.",
			role_key=role_key,
		)

	business_code = (doc.package_code or doc.name or "").strip()
	lines = format_package_line_rows(doc)
	package_total = flt(doc.estimated_value)
	line_total = _line_totals(lines)

	return {
		"ok": True,
		"role_key": role_key,
		"package": {
			"id": doc.name,
			"code": business_code,
			"name": (doc.package_name or business_code).strip(),
		},
		"totals": {
			"package_total": package_total,
			"line_total": line_total,
			"difference": flt(package_total - line_total),
		},
		"lines": lines,
	}
