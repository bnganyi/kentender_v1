# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Clear DRAFT STD package rows before replace-draft import."""

from __future__ import annotations

import frappe

PACKAGE_LINKED_DOCTYPES = (
	"STD Clause",
	"STD Section",
	"STD Source Anchor",
	"STD Source Document",
	"STD Parameter",
	"STD Rule",
	"STD Form Schema",
	"STD Requirement Schema",
	"STD Price Schedule Schema",
	"STD Evaluation Schema",
	"STD Render Block",
	"STD Validation Finding",
	"STD Validation Run",
	"STD Audit Event",
	"STD Import Run",
	"STD Usage Binding",
)


def _clear_form_field_children(package_id: str) -> None:
	"""Delete child-table rows before parent STD Form Schema removal.

	``frappe.db.delete`` on the parent does not always cascade to ``STD Form Field``
	rows; orphaned children are reattached when the same ``form_key`` is re-imported.
	"""
	form_keys = frappe.get_all("STD Form Schema", filters={"package_id": package_id}, pluck="name")
	if not form_keys:
		return
	frappe.db.delete("STD Form Field", {"parent": ("in", form_keys)})


def clear_draft_package_state(package_id: str, *, family_code: str | None = None) -> None:
	if not package_id:
		return
	if frappe.db.exists("STD Version", package_id):
		lifecycle_state = frappe.db.get_value("STD Version", package_id, "lifecycle_state")
		if lifecycle_state == "ACTIVE":
			raise ValueError(f"Cannot replace ACTIVE STD Version: {package_id}")
	_clear_form_field_children(package_id)
	for doctype in PACKAGE_LINKED_DOCTYPES:
		frappe.db.delete(doctype, {"package_id": package_id})
	frappe.db.delete("STD Import Run", {"package_id": package_id})
	frappe.db.delete("STD Version", package_id)
	if family_code:
		remaining_versions = frappe.db.count("STD Version", {"family_code": family_code})
		if remaining_versions == 0 and frappe.db.exists("STD Family", family_code):
			frappe.db.delete("STD Family", family_code)
	frappe.db.commit()
