"""Append-only audit events for KenTender (Phase D).

Inserts use ``ignore_permissions=True`` so logging works from hooks, jobs, and
contexts without an interactive user session. Call sites should still pass
``performed_by`` when a real user is known.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import frappe
from frappe.utils import now_datetime

_DOCTYPE = "Audit Event"


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
	doc.insert(ignore_permissions=True)
	return doc.name
