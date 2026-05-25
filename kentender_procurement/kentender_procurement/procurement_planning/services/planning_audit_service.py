# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP2 — Persist Planning Audit Event records."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime


def _next_event_code(object_code: str, event_type: str) -> str:
	safe = "".join(ch if ch.isalnum() else "-" for ch in (object_code or "EVT"))[:24]
	type_slug = "".join(ch if ch.isalnum() else "" for ch in (event_type or "EVT"))[:12].upper()
	return f"PPAUD-{safe}-{type_slug}-{frappe.generate_hash(length=6).upper()}"


def _has_source_module_field() -> bool:
	return bool(frappe.get_meta("Planning Audit Event").has_field("source_module"))


def assert_audit_event_fields(row) -> None:
	"""Test helper — required audit fields must be populated."""
	missing: list[str] = []
	for field in ("actor", "occurred_at", "object_type", "object_code"):
		value = row.get(field) if isinstance(row, dict) else getattr(row, field, None)
		if not value:
			missing.append(field)
	if missing:
		frappe.throw(
			_("Planning Audit Event missing required fields: {0}").format(", ".join(missing)),
			title=_("Invalid audit event"),
		)


def record_planning_audit_event(
	*,
	event_type: str,
	object_type: str,
	object_code: str,
	from_state: str | None = None,
	to_state: str | None = None,
	reason: str | None = None,
	evidence_ref: str | None = None,
	journey_code: str | None = None,
	actor: str | None = None,
	event_code: str | None = None,
	is_master_seed: bool = False,
	source_module: str | None = "Procurement Planning",
) -> str:
	"""Insert a Planning Audit Event; returns event_code."""
	if not frappe.db.exists("DocType", "Planning Audit Event"):
		return ""
	code = (event_code or _next_event_code(object_code, event_type)).strip()
	if frappe.db.exists("Planning Audit Event", code):
		return code
	payload: dict = {
		"doctype": "Planning Audit Event",
		"event_code": code,
		"event_type": event_type,
		"object_type": object_type,
		"object_code": object_code,
		"actor": actor or frappe.session.user,
		"occurred_at": now_datetime(),
		"from_state": from_state,
		"to_state": to_state,
		"reason": reason,
		"evidence_ref": evidence_ref,
		"journey_code": journey_code,
		"is_master_seed": 1 if is_master_seed else 0,
	}
	if source_module and _has_source_module_field():
		payload["source_module"] = source_module
	doc = frappe.get_doc(payload)
	doc.insert(ignore_permissions=True)
	return code
