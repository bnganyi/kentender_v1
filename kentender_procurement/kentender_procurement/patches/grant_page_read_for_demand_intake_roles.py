"""Desk workspace routes whitelisted through Page may require doctype read on `Page` for non–System Manager roles.

Without this, opening `/desk/demand-intake-and-approval` (and other desk pages backed by a Page) shows
"User … does not have doctype access … for document **Page**" and DIA E2E smoke fails.
"""

import frappe
from frappe.permissions import add_permission


# DIA workspace roles; System Manager has implicit access. Supplier KTSM workspaces use
# the same desk routing — include those desk roles so smoke users can open /desk/*.
ROLES = [
	"Requisitioner",
	"Department Approver",
	"Finance Reviewer",
	"Procurement Planner",
	"KenTender Supplier Registry Officer",
	"KenTender Compliance Officer",
]


def execute():
	if not frappe.db.get_value("DocType", "Page", "name"):
		return
	for role in ROLES:
		if not frappe.db.exists("Role", role):
			continue
		add_permission("Page", role, 0, "read")
	frappe.clear_cache()
