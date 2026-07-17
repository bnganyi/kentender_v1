# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Audit event persistence."""

from __future__ import annotations

import json
from typing import Any

import frappe


def record_event(
	event_type: str,
	*,
	tender_std_instance: str | None = None,
	object_id: str | None = None,
	metadata: dict[str, Any] | None = None,
	actor_user: str | None = None,
) -> str:
	doc = frappe.get_doc(
		{
			"doctype": "Wizard Audit Event",
			"event_type": event_type,
			"tender_std_instance": tender_std_instance,
			"object_id": object_id,
			"actor_user": actor_user or frappe.session.user,
			"metadata_json": json.dumps(metadata or {}, sort_keys=True),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name
