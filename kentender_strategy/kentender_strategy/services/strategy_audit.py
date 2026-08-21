# Copyright (c) 2026, KenTender and contributors
"""REQ §18 audit event recording."""

from __future__ import annotations

import frappe


def record_event(
	*,
	entity_type: str,
	entity_name: str,
	event_type: str,
	prior_state: str | None = None,
	new_state: str | None = None,
	reason: str | None = None,
	plan_version: str | None = None,
	summary: str | None = None,
) -> str:
	doc = frappe.get_doc(
		{
			"doctype": "Strategy Audit Event",
			"entity_type": entity_type,
			"entity_name": entity_name,
			"plan_version": plan_version,
			"event_type": event_type,
			"prior_state": prior_state or "",
			"new_state": new_state or "",
			"reason": reason or "",
			"actor": frappe.session.user,
			"event_at": frappe.utils.now_datetime(),
			"summary": summary or event_type,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name
