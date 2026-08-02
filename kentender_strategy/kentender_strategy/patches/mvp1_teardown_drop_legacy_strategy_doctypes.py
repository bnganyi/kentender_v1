# Copyright (c) 2026, KenTender and contributors
"""Drop legacy Strategy DocTypes removed in MVP-1 preparatory teardown.

Keeps a minimal public Workspace named Strategy Management so Procurement rail
links (Strategy Alignment → Strategy Management) do not break migrate/boot.
"""

from __future__ import annotations

import frappe

LEGACY_DOCTYPES = [
	"Strategy Target",
	"Strategy Objective",
	"Sub Program",
	"Strategy Program",
	"Strategy Node",
	"Strategy Navigation",
	"Strategic Plan",
]

LEGACY_PAGES = ["strategy-builder"]


def _ensure_placeholder_workspace() -> None:
	"""Minimal public Workspace so Procurement rail Strategy Alignment links validate."""
	title = "Strategy Management"
	if frappe.db.exists("Workspace", title):
		frappe.db.set_value(
			"Workspace",
			title,
			{"public": 1, "is_hidden": 0, "module": "Kentender Strategy"},
			update_modified=False,
		)
		return
	doc = frappe.get_doc(
		{
			"doctype": "Workspace",
			"label": title,
			"title": title,
			"module": "Kentender Strategy",
			"app": "kentender_strategy",
			"type": "Workspace",
			"content": "[]",
			"icon": "project",
			"public": 0,
			"is_hidden": 0,
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.db.set_value(
		"Workspace",
		title,
		{"public": 1, "is_hidden": 0},
		update_modified=False,
	)


def execute() -> None:
	for name in LEGACY_DOCTYPES:
		if frappe.db.exists("DocType", name):
			frappe.delete_doc("DocType", name, force=1, ignore_permissions=True)

	for name in LEGACY_PAGES:
		if frappe.db.exists("Page", name):
			frappe.delete_doc("Page", name, force=1, ignore_permissions=True)

	_ensure_placeholder_workspace()
	frappe.db.commit()
