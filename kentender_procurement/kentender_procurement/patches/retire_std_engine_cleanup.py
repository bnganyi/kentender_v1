# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Post-removal cleanup for the retired STD engine (KenTender v1).

Deletes STD DocTypes (including ``Source Document Registry`` used only by STD),
STD-only roles, STD workspaces, related ``Custom DocPerm`` rows, workspace
role rows, desktop icons, and seed cache keys. Idempotent for sites that
already ran a prior migrate without STD installed.
"""

from __future__ import annotations

import frappe

STD_SCENARIO_USER_EMAILS: tuple[str, ...] = (
	"amina.mwangi@example.gov.test",
	"daniel.otieno@example.gov.test",
	"grace.njeri@example.gov.test",
	"hassan.ali@example.gov.test",
)

STD_ONLY_ROLES: tuple[str, ...] = (
	"STD Administrator",
	"Senior STD Administrator",
	"STD Legal Reviewer",
	"STD Policy Reviewer",
	"STD Governance Approver",
	"STD Configuration Auditor",
	"STD Technical Maintainer",
	"STD Support Analyst",
	"STD Auditor",
)

# Prefer deleting dependents before parents; multi-pass handles residual FK/order issues.
STD_DOCTYPES_ORDERED: tuple[str, ...] = (
	"STD Readiness Finding",
	"STD Readiness Run",
	"STD Generated Output",
	"STD Generation Job",
	"STD Addendum Impact Analysis",
	"STD BOQ Item Instance",
	"STD BOQ Bill Instance",
	"STD BOQ Instance",
	"STD Instance Works Requirement Component",
	"STD Section Attachment",
	"STD Instance Parameter Value",
	"STD Audit Event",
	"STD Tender Binding",
	"STD Instance",
	"STD Extraction Mapping",
	"STD BOQ Item Schema Definition",
	"STD BOQ Bill Definition",
	"STD BOQ Definition",
	"STD Works Requirement Component Definition",
	"STD Form Field Definition",
	"STD Form Definition",
	"STD Parameter Dependency",
	"STD Parameter Definition",
	"STD Clause Definition",
	"STD Section Definition",
	"STD Part Definition",
	"STD Applicability Profile",
	"STD Template Version",
	"STD Template Family",
	"Source Document Registry",
)

WORKSPACES_TO_DELETE: tuple[str, ...] = ("STD Engine", "STD Engine Admin")


def _clear_std_seed_cache() -> None:
	try:
		frappe.cache().delete_keys("std:seed:*")
	except Exception:
		frappe.log_error(
			title="KenTender retire_std_engine_cleanup: cache delete_keys failed",
			message=frappe.get_traceback(),
		)


def _delete_custom_docperms_for_doctypes() -> None:
	if not STD_DOCTYPES_ORDERED:
		return
	ph = ", ".join(["%s"] * len(STD_DOCTYPES_ORDERED))
	frappe.db.sql(
		f"DELETE FROM `tabCustom DocPerm` WHERE parent IN ({ph})",
		list(STD_DOCTYPES_ORDERED),
	)


def _delete_property_setters_for_doctypes() -> None:
	for dt in STD_DOCTYPES_ORDERED:
		frappe.db.delete("Property Setter", {"doc_type": dt})


def _remove_scenario_users() -> None:
	for email in STD_SCENARIO_USER_EMAILS:
		if frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)


def _strip_std_only_roles_from_workspaces() -> None:
	if not STD_ONLY_ROLES:
		return
	ph = ", ".join(["%s"] * len(STD_ONLY_ROLES))
	frappe.db.sql(
		f"DELETE FROM `tabHas Role` WHERE parenttype = 'Workspace' AND role IN ({ph})",
		list(STD_ONLY_ROLES),
	)


def _delete_workspaces() -> None:
	for name in WORKSPACES_TO_DELETE:
		if frappe.db.exists("Workspace", name):
			frappe.delete_doc("Workspace", name, force=True, ignore_permissions=True)


def _delete_std_doctypes_multi_pass() -> None:
	remaining = list(STD_DOCTYPES_ORDERED)
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
			title=f"KenTender retire_std_engine_cleanup: could not delete DocType {dt}",
			message=frappe.get_traceback(),
		)


def _delete_std_only_roles() -> None:
	for role in STD_ONLY_ROLES:
		if frappe.db.exists("Role", role):
			frappe.delete_doc("Role", role, force=True, ignore_permissions=True)


def _delete_desktop_icons_for_std_workspaces() -> None:
	if not WORKSPACES_TO_DELETE:
		return
	ph = ", ".join(["%s"] * len(WORKSPACES_TO_DELETE))
	frappe.db.sql(f"DELETE FROM `tabDesktop Icon` WHERE link_to IN ({ph})", list(WORKSPACES_TO_DELETE))


def execute() -> None:
	_clear_std_seed_cache()
	_delete_custom_docperms_for_doctypes()
	_delete_property_setters_for_doctypes()
	_remove_scenario_users()
	_strip_std_only_roles_from_workspaces()
	_delete_workspaces()
	_delete_std_doctypes_multi_pass()
	_delete_std_only_roles()
	_delete_desktop_icons_for_std_workspaces()
	frappe.db.commit()
