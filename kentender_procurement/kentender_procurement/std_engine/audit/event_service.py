# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Persist STD Engine audit events during import."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import frappe


def record_audit_event(
	*,
	package_id: str,
	event_type: str,
	object_type: str,
	object_id: str,
	payload: dict[str, Any] | None = None,
	event_key: str | None = None,
) -> str:
	key = event_key or f"{package_id}.{event_type}.{object_id}"
	if frappe.db.exists("STD Audit Event", key):
		return key

	doc = frappe.get_doc(
		{
			"doctype": "STD Audit Event",
			"package_id": package_id,
			"event_key": key,
			"event_type": event_type,
			"object_type": object_type,
			"object_id": object_id,
			"actor": frappe.session.user,
			"occurred_at": datetime.now(timezone.utc).replace(tzinfo=None),
			"payload_json": json.dumps(payload or {}, sort_keys=True, default=str),
		}
	)
	doc.insert(ignore_permissions=True)
	return key
