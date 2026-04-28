from __future__ import annotations

import frappe
from frappe import _


def assert_transition_service_controlled(doc, status_field: str) -> None:
	"""Block direct status mutation outside the centralized transition service."""
	if doc.is_new():
		return
	if not doc.has_value_changed(status_field):
		return
	if getattr(frappe.flags, "std_transition_service_context", False):
		return
	frappe.throw(
		_("Direct status mutation is not allowed. Use transition_std_object service."),
		title=_("Transition service required"),
	)

