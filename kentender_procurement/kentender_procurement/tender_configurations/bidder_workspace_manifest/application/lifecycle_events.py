# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Append-only Phase 5 lifecycle / governance events."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import now_datetime

from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.audit import (
	append_audit_event,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.registry_doctypes import (
	DT_LIFECYCLE_EVENT,
)


def emit_lifecycle_event(
	*,
	event_type: str,
	organization: str,
	actor: str = "",
	correlation_ref: str = "",
	affected_refs: dict[str, Any] | None = None,
	metadata: dict[str, Any] | None = None,
) -> str:
	"""Persist an immutable BWMF Lifecycle Event and mirror to BWMF Audit Event."""
	actor = actor or frappe.session.user or "system"
	event_id = f"LCE-{frappe.generate_hash(length=12)}"
	doc = frappe.get_doc(
		{
			"doctype": DT_LIFECYCLE_EVENT,
			"event_id": event_id,
			"event_type": event_type,
			"organization": organization,
			"actor": actor,
			"event_time": now_datetime(),
			"correlation_ref": correlation_ref or "",
			"affected_refs_json": json.dumps(affected_refs or {}, sort_keys=True),
			"metadata_json": json.dumps(metadata or {}, sort_keys=True),
			"immutable": 1,
		}
	)
	doc.insert(ignore_permissions=True)
	append_audit_event(
		event_type=event_type,
		organization=organization,
		actor=actor,
		correlation_ref=correlation_ref or event_id,
		metadata={**(metadata or {}), "lifecycle_event": doc.name, **(affected_refs or {})},
	)
	return doc.name
