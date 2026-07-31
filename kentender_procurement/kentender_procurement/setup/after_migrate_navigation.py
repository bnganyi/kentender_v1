# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Re-sync Procurement workspace sidebars from repo JSON (post-fixture).

Frappe may have auto-generated a ``Workspace Sidebar`` for module
*Procurement Planning* (DocType links) before this app shipped an explicit
sidebar JSON. ``after_migrate`` reapplies the canonical sidebar rows so
navigation matches ``Procurement Planning Menu Restructure.md``.
"""

from __future__ import annotations

import json
import os

import frappe
from frappe.modules.import_file import import_file_by_path


def _sidebar_json_path(basename: str) -> str:
	return os.path.join(
		frappe.get_app_path("kentender_procurement"),
		"workspace_sidebar",
		f"{basename}.json",
	)


def _load_sidebar_export(basename: str) -> dict | None:
	path = _sidebar_json_path(basename)
	if not os.path.isfile(path):
		return None
	with open(path, encoding="utf-8") as f:
		return json.load(f)


def _apply_sidebar_export(data: dict) -> None:
	title = data.get("title") or data.get("name")
	if not title:
		return
	name = data.get("name") or title
	if frappe.db.exists("Workspace Sidebar", name):
		frappe.delete_doc("Workspace Sidebar", name, force=True, ignore_permissions=True)
	doc = frappe.new_doc("Workspace Sidebar")
	doc.title = title
	if data.get("name"):
		doc.name = data["name"]

	skip = {"items", "docstatus", "__islocal"}
	for key, val in data.items():
		if key in skip or val is None:
			continue
		if key == "name" and not doc.is_new():
			continue
		if hasattr(doc, key):
			setattr(doc, key, val)

	doc.items = []
	for row in data.get("items") or []:
		clean = {k: v for k, v in row.items() if v is not None}
		doc.append("items", clean)

	doc.flags.ignore_permissions = True
	doc.insert()


def reconcile_procurement_navigation_from_exports() -> None:
	# Legacy sidebar name matched the workspace slug; Frappe then called
	# sidebar.setup("Procurement Planning") and replaced the parent Procurement
	# rail. Remove it if present (see Planning menu restructure doc).
	if frappe.db.exists("Workspace Sidebar", "Procurement Planning"):
		frappe.delete_doc("Workspace Sidebar", "Procurement Planning", force=True, ignore_permissions=True)
	if frappe.db.exists("Page", "pp2-planning"):
		frappe.delete_doc("Page", "pp2-planning", force=True, ignore_permissions=True)
	if frappe.db.exists("Workspace", "Procurement Planning"):
		frappe.db.set_value("Workspace", "Procurement Planning", "is_hidden", 0)

	# Include ``demand_intake`` so the Demand Intake module rail picks up
	# ``Procurement Home`` / IA labels even when fixtures are skipped.
	for basename in ("planning_module_navigation", "procurement", "demand_intake"):
		data = _load_sidebar_export(basename)
		if not data:
			continue
		_apply_sidebar_export(data)


def sync_tenders_desktop_icon() -> None:
	"""Desk home tile → public Available Tenders website (/tenders)."""
	path = os.path.join(frappe.get_app_path("kentender_procurement"), "desktop_icon", "tenders.json")
	if os.path.isfile(path):
		import_file_by_path(path, force=True)


def sync_coming_soon_page() -> None:
	"""Ensure Planned capability-overview Page exists for IA availability states."""
	path = os.path.join(
		frappe.get_app_path("kentender_procurement"),
		"kentender_procurement",
		"page",
		"coming_soon",
		"coming_soon.json",
	)
	if os.path.isfile(path):
		import_file_by_path(path, force=True)


def run() -> None:
	# Page targets must exist before Workspace Sidebar Link To validation.
	if frappe.db.exists("DocType", "Page"):
		sync_coming_soon_page()
	if frappe.db.exists("DocType", "Workspace Sidebar"):
		reconcile_procurement_navigation_from_exports()
	if frappe.db.exists("DocType", "Desktop Icon"):
		sync_tenders_desktop_icon()
	frappe.clear_cache()
