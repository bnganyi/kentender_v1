# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Post-removal cleanup for the retired IT STD Wizard (KenTender v1).

Deletes IT wizard DocTypes and the wizard-only role. Idempotent. (The wizard's
Desk pages and sidebar rows are dropped by ``drop_retired_tender_configurations``.)
"""

from __future__ import annotations

import frappe

WIZARD_ONLY_ROLE = "IT Tender Drafter"

WIZARD_DOCTYPES_ORDERED: tuple[str, ...] = (
	"Tender STD Requirement Item",
	"Tender STD Schedule Phase Item",
	"Tender STD Schedule Milestone Item",
	"Tender STD Price Line",
	"Tender STD Inventory Item",
	"Tender STD Evaluation Criterion",
	"Tender STD Form Evidence Item",
	"Tender STD SCC Carry Item",
	"Tender STD Validation Finding",
	"Tender STD Review Decision",
	"Tender STD Profile",
	"Tender STD TDS",
	"Tender STD IT Requirements",
	"Tender STD Implementation Schedule",
	"Tender STD System Inventory",
	"Tender STD Price Schedule",
	"Tender STD Evaluation",
	"Tender STD Forms Evidence",
	"Tender STD SCC",
	"Tender STD Validation Report",
	"Tender STD Review",
	"Tender STD Render Preview",
	"Tender STD Publication Readiness",
	"Wizard Step Instance",
	"Wizard Progress Snapshot",
	"Wizard Audit Event",
	"Tender STD Instance",
)

def _table_exists(table_name: str) -> bool:
	return bool(frappe.db.sql(f"SHOW TABLES LIKE %s", (table_name,)))


def _delete_custom_docperms_for_doctypes(doctypes: tuple[str, ...]) -> None:
	if not doctypes:
		return
	ph = ", ".join(["%s"] * len(doctypes))
	frappe.db.sql(
		f"DELETE FROM `tabCustom DocPerm` WHERE parent IN ({ph})",
		list(doctypes),
	)


def _delete_property_setters_for_doctypes(doctypes: tuple[str, ...]) -> None:
	for dt in doctypes:
		frappe.db.delete("Property Setter", {"doc_type": dt})


def _delete_doctypes_multi_pass(doctypes: tuple[str, ...]) -> None:
	remaining = list(doctypes)
	for _ in range(6):
		if not remaining:
			break
		next_remaining: list[str] = []
		for dt in remaining:
			if not frappe.db.exists("DocType", dt):
				continue
			try:
				frappe.delete_doc("DocType", dt, force=True, ignore_permissions=True)
			except Exception:
				next_remaining.append(dt)
		remaining = next_remaining
	for dt in remaining:
		frappe.log_error(
			title=f"KenTender retire_it_std_wizard_cleanup: could not delete DocType {dt}",
			message=frappe.get_traceback(),
		)


def _delete_module_def() -> None:
	if frappe.db.exists("Module Def", "IT Tender Wizard"):
		frappe.delete_doc("Module Def", "IT Tender Wizard", force=True, ignore_permissions=True)


def _delete_wizard_role() -> None:
	if frappe.db.exists("Role", WIZARD_ONLY_ROLE):
		frappe.db.sql(
			"DELETE FROM `tabHas Role` WHERE role = %s",
			(WIZARD_ONLY_ROLE,),
		)
		frappe.delete_doc("Role", WIZARD_ONLY_ROLE, force=True, ignore_permissions=True)


def execute() -> None:
	_delete_custom_docperms_for_doctypes(WIZARD_DOCTYPES_ORDERED)
	_delete_property_setters_for_doctypes(WIZARD_DOCTYPES_ORDERED)
	_delete_doctypes_multi_pass(WIZARD_DOCTYPES_ORDERED)
	_delete_module_def()
	_delete_wizard_role()
	frappe.db.commit()
	frappe.logger("kentender_procurement").info(
		"IT STD Wizard retired (2026-07). Code archived under "
		"apps/kentender_v1/archive/it-std-wizard-retired-2026-07/."
	)
