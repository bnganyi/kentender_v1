# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Clear NEG-PP2 fixture rows (dev/test only)."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_planning.seeds.negative_fixtures.bootstrap import (
	_resolve_demand_docname,
)
from kentender_procurement.procurement_planning.seeds.negative_fixtures.constants import (
	NEG_ENTITY_CODES,
)
from kentender_procurement.procurement_planning.seeds.negative_fixtures.registry import get_negative_fixture_spec

_PKG_CHILD_DOCTYPES: tuple[tuple[str, str], ...] = (
	("Package Review Decision", "package_code"),
	("Package Readiness Result", "package_code"),
	("Package Method Decision", "package_code"),
	("Planning Correction Supersession Record", "package_code"),
)


def _dev_or_test_clear_allowed() -> bool:
	if frappe.in_test:
		return True
	if getattr(frappe.conf, "developer_mode", False):
		return True
	if getattr(frappe.conf, "allow_tests", False):
		return True
	return False


def _delete_if_exists(doctype: str, name: str) -> bool:
	if not name or not frappe.db.exists(doctype, name):
		return False
	if doctype == "Planning Audit Event":
		doc = frappe.get_doc(doctype, name)
		doc.flags.ignore_pp_aud_allow_delete = True
		doc.delete(ignore_permissions=True)
		return True
	if doctype == "Procurement Package Line":
		frappe.flags.skip_package_line_rollup = True
		try:
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		finally:
			frappe.flags.pop("skip_package_line_rollup", None)
		return True
	frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
	return True


def _delete_package_cascade(package_code: str, deleted: dict[str, int]) -> None:
	pkg = (package_code or "").strip()
	if not pkg:
		return
	for doctype, field in _PKG_CHILD_DOCTYPES:
		for name in frappe.get_all(doctype, filters={field: pkg}, pluck="name"):
			if _delete_if_exists(doctype, name):
				deleted[doctype] = deleted.get(doctype, 0) + 1
	for line_name in frappe.get_all(
		"Procurement Package Line",
		filters={"package_id": pkg},
		pluck="name",
	):
		if _delete_if_exists("Procurement Package Line", line_name):
			deleted["Procurement Package Line"] = deleted.get("Procurement Package Line", 0) + 1
	if _delete_if_exists("Procurement Package", pkg):
		deleted["Procurement Package"] = deleted.get("Procurement Package", 0) + 1


def _delete_journey(journey_code: str, deleted: dict[str, int]) -> None:
	jc = (journey_code or "").strip()
	if not jc:
		return
	if frappe.db.exists("Procurement Journey", jc):
		frappe.db.sql("DELETE FROM `tabProcurement Journey` WHERE name=%s", jc)
		deleted["Procurement Journey"] = deleted.get("Procurement Journey", 0) + 1
	suffix = jc[4:] if jc.upper().startswith("JRN-") else jc
	for prefix in ("DEMAPP-", "BUDCONF-"):
		handoff_code = f"{prefix}{suffix}"
		if _delete_if_exists("Procurement Handoff Card", handoff_code):
			deleted["Procurement Handoff Card"] = deleted.get("Procurement Handoff Card", 0) + 1


def _delete_demand(demand_code: str, deleted: dict[str, int]) -> None:
	docname = _resolve_demand_docname(demand_code)
	if not docname:
		return
	if _delete_if_exists("Demand", docname):
		deleted["Demand"] = deleted.get("Demand", 0) + 1


def run_clear(*, fixture_code: str, skip_guard: bool = False) -> dict[str, Any]:
	frappe.set_user("Administrator")
	code = (fixture_code or "").strip()
	if not skip_guard and not _dev_or_test_clear_allowed():
		return {
			"ok": False,
			"error_code": "NEG_FIXTURE_CLEAR_BLOCKED",
			"fixture_code": code,
			"message": "clear_procurement_planning_negative_fixture is allowed only in development/test.",
		}
	if not get_negative_fixture_spec(code):
		return {
			"ok": False,
			"error_code": "UNKNOWN_FIXTURE",
			"fixture_code": code,
			"message": f"Unknown negative fixture: {code}",
		}

	records = dict(NEG_ENTITY_CODES.get(code) or {})
	deleted: dict[str, int] = {}

	for key in ("release_code", "inclusion_code", "tender_code", "readiness_code", "method_decision_code"):
		value = (records.get(key) or "").strip()
		if not value:
			continue
		doctype = {
			"release_code": "Procurement Handoff Card",
			"inclusion_code": "Procurement Handoff Card",
			"tender_code": "TM2 Tender",
			"readiness_code": "Package Readiness Result",
			"method_decision_code": "Package Method Decision",
		}[key]
		if _delete_if_exists(doctype, value):
			deleted[doctype] = deleted.get(doctype, 0) + 1

	for package_key in ("package_code", "package_code_a", "package_code_b"):
		_delete_package_cascade((records.get(package_key) or "").strip(), deleted)

	journey_code = (records.get("journey_code") or "").strip()
	if journey_code:
		_delete_journey(journey_code, deleted)

	demand_code = (records.get("demand_code") or "").strip()
	if demand_code:
		_delete_demand(demand_code, deleted)
		_delete_demand(f"{demand_code}-B", deleted)

	plan_code = (records.get("plan_code") or "").strip()
	if plan_code and _delete_if_exists("Procurement Plan", plan_code):
		deleted["Procurement Plan"] = deleted.get("Procurement Plan", 0) + 1

	frappe.db.commit()
	return {"ok": True, "fixture_code": code, "deleted": deleted}
