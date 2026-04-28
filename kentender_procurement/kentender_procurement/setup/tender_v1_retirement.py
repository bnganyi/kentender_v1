# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt
"""One-shot cleanup for retired Tender Management v1 desk metadata."""

from __future__ import annotations

import frappe


def wipe_tender_v1_desk_artifacts() -> None:
	"""Remove Page, Workspace, and Module Def rows left from v1 (idempotent)."""
	# ``Page`` forbids ``delete_doc`` unless developer_mode; DB delete matches migrate/patch needs.
	if frappe.db.exists("Page", "tender-builder"):
		frappe.db.delete("Page", {"name": "tender-builder"})

	if frappe.db.exists("Workspace", "Tender Management"):
		try:
			frappe.delete_doc("Workspace", "Tender Management", force=1, ignore_permissions=True)
		except Exception:
			frappe.db.delete("Workspace", {"name": "Tender Management"})

	for name in frappe.get_all(
		"Module Def",
		filters={"app_name": "kentender_procurement", "module_name": "Tendering"},
		pluck="name",
	):
		try:
			frappe.delete_doc("Module Def", name, force=1, ignore_permissions=True)
		except Exception:
			frappe.db.delete("Module Def", {"name": name})


def wipe_tender_v1_desk_artifacts_console() -> None:
	"""``bench execute`` entrypoint — commits after cleanup."""
	wipe_tender_v1_desk_artifacts()
	frappe.db.commit()
