# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BE-11 — ensure governance placeholder Desk pages exist (screens 18–21)."""

from __future__ import annotations

import frappe

_PAGES = (
	("std-review-and-approval", "Review and Approval"),
	("std-usage-and-tender-bindings", "Usage and Tender Bindings"),
	("std-import-package-review", "Import Package Review"),
	("std-version-diff-and-supersession", "Version Diff and Supersession"),
)

_ROLES = (
	"Administrator",
	"System Manager",
	"Procurement Officer",
	"Procurement Planner",
	"Planning Authority",
	"STD Template Administrator",
	"STD Template Importer",
	"STD Template Reviewer",
	"STD Template Approver",
	"STD Template Activator",
	"STD Template Auditor",
	"STD Technical Inspector",
	"Auditor",
	"Department Approver",
	"Finance Reviewer",
	"Requisitioner",
)


def execute() -> None:
	frappe.flags.in_import = True
	frappe.flags.in_migrate = True
	try:
		_ensure_pages(_PAGES)
	finally:
		frappe.flags.in_import = False
		frappe.flags.in_migrate = False
	frappe.db.commit()


def _ensure_pages(pages: tuple[tuple[str, str], ...]) -> None:
	_truncated_cleanup = {
		"std-review-and-appro": "std-review-and-approval",
		"std-usage-and-tender": "std-usage-and-tender-bindings",
		"std-import-package-r": "std-import-package-review",
		"std-version-diff-and": "std-version-diff-and-supersession",
	}
	for old_name, new_name in _truncated_cleanup.items():
		if frappe.db.exists("Page", old_name) and not frappe.db.exists("Page", new_name):
			frappe.delete_doc("Page", old_name, force=1, ignore_permissions=True)

	for page_name, title in pages:
		if frappe.db.exists("Page", page_name):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Page",
				"name": page_name,
				"page_name": page_name,
				"title": title,
				"module": "Kentender Procurement",
				"standard": "Yes",
			}
		)
		for role in _ROLES:
			if frappe.db.exists("Role", role):
				doc.append("roles", {"role": role})
		doc.insert(ignore_permissions=True)
