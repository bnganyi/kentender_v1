# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Post-removal cleanup for the retired IT STD Wizard (KenTender v1).

Deletes IT wizard DocTypes, wizard-only roles, related data rows, legacy Desk
page records (replaced by ``it-std-wizard-retired`` + shared retirement JS),
and TM2 binding rows that reference removed instances. Idempotent.
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

LEGACY_WIZARD_PAGES: tuple[str, ...] = (
	"it-tender-configuration-dashboard",
	"it-tender-configuration-overview",
	"it-tender-configuration-tender-profile",
	"it-tender-configuration-tds",
	"it-tender-configuration-it-requirements",
	"it-tender-configuration-implementation-schedule",
	"it-tender-configuration-system-inventory",
	"it-tender-configuration-price-schedule",
	"it-tender-configuration-evaluation-setup",
	"it-tender-configuration-forms-and-evidence",
	"it-tender-configuration-scc",
	"it-tender-configuration-validation-report",
	"it-tender-configuration-review-and-approval",
	"it-tender-configuration-render-preview",
	"it-tender-configuration-publication-readiness",
)


def _table_exists(table_name: str) -> bool:
	return bool(frappe.db.sql(f"SHOW TABLES LIKE %s", (table_name,)))


def _purge_tm2_std_bindings() -> None:
	if not _table_exists("tabTM2 Tender STD Binding"):
		return
	if _table_exists("tabTender STD Instance"):
		frappe.db.sql("DELETE FROM `tabTM2 Tender STD Binding`")
	else:
		frappe.db.sql(
			"DELETE FROM `tabTM2 Tender STD Binding` WHERE tender_std_instance IS NOT NULL"
		)


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


def _repurpose_legacy_pages() -> None:
	retired_title = "IT Tender Configuration Wizard — Retired"
	for page_name in LEGACY_WIZARD_PAGES:
		if frappe.db.exists("Page", page_name):
			frappe.db.set_value("Page", page_name, "title", retired_title)


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


def _remove_sidebar_link() -> None:
	frappe.db.sql(
		"""
		DELETE FROM `tabWorkspace Sidebar Item`
		WHERE link_to IN %s AND link_type = 'Page'
		""",
		(list(LEGACY_WIZARD_PAGES),),
	)


def execute() -> None:
	_purge_tm2_std_bindings()
	_delete_custom_docperms_for_doctypes(WIZARD_DOCTYPES_ORDERED)
	_delete_property_setters_for_doctypes(WIZARD_DOCTYPES_ORDERED)
	_delete_doctypes_multi_pass(WIZARD_DOCTYPES_ORDERED)
	_repurpose_legacy_pages()
	_delete_module_def()
	_delete_wizard_role()
	_remove_sidebar_link()
	frappe.db.commit()
	frappe.logger("kentender_procurement").info(
		"IT STD Wizard retired (2026-07). Code archived under "
		"apps/kentender_v1/archive/it-std-wizard-retired-2026-07/. "
		"Retirement page: it-std-wizard-retired."
	)
