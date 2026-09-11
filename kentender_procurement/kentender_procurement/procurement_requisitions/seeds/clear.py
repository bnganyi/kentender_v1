# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 — clear Requisitions fixture rows. Wired into
`kentender_core.seeds.kentender_mvp_v1.clear.purge_kentender_playwright_data`
(imported lazily there, per its own note) with the exact signature that
caller expects.

Requisitions rows carry no `fixture_namespace` column (D5 predates that
column on this module's doctypes); "canonical" ownership here means rows
tied to the two named MOH Plan Items (§16.1), and "playwright" ownership
means rows tied to the Playwright fixture's own reserved plan items, once
`playwright_ui_fixtures.py` exists. Until then the playwright branch is a
visible no-op rather than a silent one.
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_requisitions.seeds.kentender_mvp_v1 import (
	COMBINED_ITEM_TITLE,
	SINGLE_ITEM_TITLE,
	_plan_item_id,
)

_DOCTYPES = (
	"Requisition Event", "Requisition Decision", "Requisition Task", "Authorised Requisition Handoff",
	"Requisition Version", "IT Equipment Requirement Package Version", "IT Equipment Requirement Package",
	"Procurement Requisition", "Requisition Command Journal",
)


def _delete_for_plan_items(plan_item_ids: list[str]) -> dict[str, int]:
	deleted: dict[str, int] = {}
	plan_item_ids = [p for p in plan_item_ids if p]
	roots = frappe.get_all("Procurement Requisition", filters={"plan_item_id": ("in", plan_item_ids or ("",))}, pluck="name")
	for root_name in roots:
		root = frappe.db.get_value("Procurement Requisition", root_name, ["current_state", "requisition_reference"], as_dict=True)
		if root.current_state != "Authorised":
			continue
		# The label alone is not the ground truth this build learned to
		# distrust (the "wipe after authorise" hazard): check the real
		# cross-app position. A reservation still Active means real Budget/
		# Planning state would be orphaned by deleting the local rows now.
		if frappe.db.exists("Funding Reservation", {"calling_module": "Procurement Requisitions", "caller_reference": root.requisition_reference, "status": "Active"}):
			frappe.throw(
				f"{root_name} is Authorised with an Active Budget reservation — clearing it directly would "
				"orphan Planning's drawdown and Budget's reservation. Revoke it first through "
				"authorise.revoke_unconsumed_authorisation()."
			)
	packages = frappe.get_all("IT Equipment Requirement Package", filters={"requisition": ("in", roots or ("",))}, pluck="name")
	package_versions = frappe.get_all("IT Equipment Requirement Package Version", filters={"package": ("in", packages or ("",))}, pluck="name")
	versions = frappe.get_all("Requisition Version", filters={"requisition": ("in", roots or ("",))}, pluck="name")
	tasks = frappe.get_all("Requisition Task", filters={"requisition": ("in", roots or ("",))}, pluck="name")

	def delete(doctype: str, names: list[str]) -> None:
		if names:
			frappe.db.delete(doctype, {"name": ("in", names)})
		deleted[doctype] = deleted.get(doctype, 0) + len(names)

	delete("Requisition Decision", frappe.get_all("Requisition Decision", filters={"task": ("in", tasks or ("",))}, pluck="name"))
	delete("Requisition Task", tasks)
	delete("Authorised Requisition Handoff", frappe.get_all("Authorised Requisition Handoff", filters={"requisition": ("in", roots or ("",))}, pluck="name"))
	delete("Requisition Version", versions)
	delete("IT Equipment Requirement Package Version", package_versions)
	delete("IT Equipment Requirement Package", packages)
	delete("Requisition Event", frappe.get_all("Requisition Event", filters={"requisition": ("in", roots or ("",))}, pluck="name"))
	delete("Procurement Requisition", roots)
	return deleted


def clear_requisition_fixture_rows(
	*, include_canonical: bool = False, include_playwright: bool = True
) -> dict[str, Any]:
	deleted: dict[str, int] = {}
	if include_canonical:
		plan_items = [_plan_item_id(SINGLE_ITEM_TITLE), _plan_item_id(COMBINED_ITEM_TITLE)]
		for doctype, count in _delete_for_plan_items(plan_items).items():
			deleted[doctype] = deleted.get(doctype, 0) + count
	if include_playwright:
		from kentender_procurement.procurement_requisitions.seeds import playwright_ui_fixtures as pw

		pw.reset_all(commit=False)
		pw.restore_site(commit=False)
		deleted["playwright_namespace"] = pw.NS_PW
	journal = frappe.get_all("Requisition Command Journal", filters={"idempotency_key": ("like", "req-seed:%")}, pluck="name") if include_canonical else []
	if journal:
		frappe.db.delete("Requisition Command Journal", {"name": ("in", journal)})
	deleted["Requisition Command Journal"] = len(journal)
	return {"ok": True, "deleted": deleted}
