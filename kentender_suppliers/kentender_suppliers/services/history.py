# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

import frappe
from frappe.utils import now_datetime


def log_status_change(
	supplier_profile: str,
	status_type: str,
	new_status: str,
	previous_status: str | None = None,
	reason: str | None = None,
) -> None:
	"""Create KTSM Status History row (C4)."""
	doc = frappe.get_doc(
		{
			"doctype": "KTSM Status History",
			"supplier_profile": supplier_profile,
			"status_type": status_type,
			"new_status": new_status,
			"previous_status": previous_status,
			"reason": reason,
			"changed_by": frappe.session.user,
			"changed_at": now_datetime(),
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert()
