# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Append-only audit events for STD Instance domain actions.

STDINST-1100. See also ``events`` for payload shapes.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import now_datetime

from kentender_core.services.audit_event_service import log_audit_event
from kentender_procurement.tender_management.std_instance.events import EVENT_ACTIONS


def _safe_details(details: dict[str, Any] | None) -> dict[str, Any]:
	payload = dict(details or {})
	try:
		json.dumps(payload, sort_keys=True, separators=(",", ":"))
		return payload
	except Exception:
		return {"raw": frappe.as_json(payload)}


def emit_std_instance_event(
	event_code: str,
	*,
	instance_code: str | None = None,
	document_type: str = "Tender STD Instance",
	document_name: str | None = None,
	action: str | None = None,
	details: dict[str, Any] | None = None,
	entity: str = "STD_INSTANCE",
	performed_by: str | None = None,
) -> str | None:
	"""Best-effort append-only audit event insert for STD instance workflows."""
	try:
		actor = performed_by or frappe.session.user or "Administrator"
		ts = now_datetime()
		doc_name = (document_name or instance_code or "").strip() or "UNKNOWN"
		meta = {
			"event_code": event_code,
			"instance_code": (instance_code or "").strip(),
			"actor": actor,
			"timestamp": ts.isoformat(),
			"details": _safe_details(details),
		}
		return log_audit_event(
			event_type=event_code,
			entity=entity,
			document_type=document_type,
			document_name=doc_name,
			action=action or EVENT_ACTIONS.get(event_code, "std_instance_event"),
			performed_by=actor,
			timestamp=ts,
			metadata=meta,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "STDINST-1100 audit emit failed")
		return None
