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
		doc = frappe.get_doc("Workspace Sidebar", name)
	else:
		alt = frappe.get_all("Workspace Sidebar", filters={"title": title}, pluck="name", limit=1)
		if alt:
			doc = frappe.get_doc("Workspace Sidebar", alt[0])
		else:
			doc = frappe.new_doc("Workspace Sidebar")
			doc.title = title

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
	if doc.is_new():
		doc.insert()
	else:
		doc.save()


def reconcile_procurement_navigation_from_exports() -> None:
	# Legacy sidebar name matched the workspace slug; Frappe then called
	# sidebar.setup("Procurement Planning") and replaced the parent Procurement
	# rail. Remove it if present (see Planning menu restructure doc).
	if frappe.db.exists("Workspace Sidebar", "Procurement Planning"):
		frappe.delete_doc("Workspace Sidebar", "Procurement Planning", force=True, ignore_permissions=True)

	# Include ``demand_intake`` so the Demand Intake module rail picks up
	# ``Procurement Home`` / IA labels even when fixtures are skipped.
	for basename in ("planning_module_navigation", "procurement", "demand_intake"):
		data = _load_sidebar_export(basename)
		if not data:
			continue
		_apply_sidebar_export(data)


def run() -> None:
	if not frappe.db.exists("DocType", "Workspace Sidebar"):
		return
	reconcile_procurement_navigation_from_exports()
	frappe.clear_cache()
