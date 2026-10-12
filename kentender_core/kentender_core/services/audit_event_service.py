"""Append-only audit events for KenTender (Phase D).

``log_audit_event`` is the only writer. Inserts use ``ignore_permissions=True``
so logging works from hooks, jobs, and contexts without an interactive user
session; they run inside the Audit Event command-write window, which is what
the controller requires (AUD-XC-010: nobody, System Manager and Administrator
included, may update or delete a row, and nothing may insert one except this
service). Call sites should still pass ``performed_by`` when a real user is
known.

``purge_audit_events`` is the one deletion path: test and seed clean-up on a
development or test site, in-process only (see ``command_write_guard``).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import frappe
from frappe.utils import now_datetime

from kentender_core.services.command_write_guard import command_write, maintenance_write

_DOCTYPE = "Audit Event"
AUDIT_EVENT_FAMILY = "Audit Event"


def log_audit_event(
	*,
	event_type: str,
	entity: str = "",
	document_type: str,
	document_name: str,
	action: str,
	performed_by: str | None = None,
	timestamp: datetime | None = None,
	metadata: dict[str, Any] | None = None,
) -> str:
	"""Insert an Audit Event row. Returns the new document name.

	Does not call ``frappe.db.commit()``; respects the caller's transaction.
	"""
	user = performed_by or getattr(frappe.session, "user", None) or "Administrator"
	ts = timestamp or now_datetime()
	meta = metadata if metadata is not None else {}

	doc = frappe.get_doc(
		{
			"doctype": _DOCTYPE,
			"event_type": event_type,
			"entity": entity or "",
			"document_type": document_type,
			"document_name": document_name,
			"action": action,
			"performed_by": user,
			"timestamp": ts,
			"metadata": meta,
		}
	)
	with command_write(AUDIT_EVENT_FAMILY):
		doc.insert(ignore_permissions=True)
	return doc.name


def purge_audit_events(filters: dict[str, Any] | list | None = None, *, reason: str) -> int:
	"""Delete Audit Event rows matching `filters` (required: a purge of every
	row is never wanted). Test and seed clean-up only: refused inside an HTTP
	request and on any site that is not a development or test site. Does not
	commit. Returns the number of rows removed."""
	if not filters:
		raise ValueError("purge_audit_events needs filters")
	with maintenance_write(AUDIT_EVENT_FAMILY, reason=reason):
		names = frappe.get_all(_DOCTYPE, filters=filters, pluck="name")
		for start in range(0, len(names), 500):
			frappe.db.delete(_DOCTYPE, {"name": ("in", names[start : start + 500])})
	return len(names)
