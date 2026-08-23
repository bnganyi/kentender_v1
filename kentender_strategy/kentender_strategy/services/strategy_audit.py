# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 §15 audit event recording.

Routes through kentender_core's shared Audit Event mechanism rather than a
bespoke Strategy doctype — CFG-CHG-002's tracker flagged Strategy's prior
bespoke `Strategy Audit Event` doctype as a known duplicate mechanism, not a
pattern to repeat (see docs/mvp-1-r1/02_strategy/IMPLEMENTATION_TRACKER.md
decision log, 2026-08-23).
"""

from __future__ import annotations

import frappe

from kentender_core.services.audit_event_service import log_audit_event


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
	correlation_id: str | None = None,
	capability: str | None = None,
) -> str:
	metadata: dict = {}
	if prior_state:
		metadata["prior_state"] = prior_state
	if new_state:
		metadata["new_state"] = new_state
	if reason:
		metadata["reason"] = reason
	if plan_version:
		metadata["plan_version"] = plan_version
	if summary:
		metadata["summary"] = summary
	if correlation_id:
		metadata["correlation_id"] = correlation_id
	if capability:
		# Records exactly which capability the actor exercised for this event,
		# so Separation-of-Duties history (STR-BR §7) can be reconstructed
		# precisely from the audit trail rather than inferred from event_type
		# alone (the same action name, e.g. "Return", can be exercised under
		# either the Reviewer or the Approval Authority capability).
		metadata["capability"] = capability

	return log_audit_event(
		event_type=f"strategy.{frappe.scrub(event_type)}",
		entity=entity_name,
		document_type=entity_type,
		document_name=entity_name,
		action=event_type,
		metadata=metadata,
	)


def list_events(document_type: str, document_name: str) -> list[dict]:
	"""Read back the audit trail for one Strategy-owned record, newest first."""
	rows = frappe.get_all(
		"Audit Event",
		filters={"document_type": document_type, "document_name": document_name},
		fields=["event_type", "action", "performed_by", "timestamp", "metadata"],
		order_by="timestamp desc",
	)
	for row in rows:
		row["metadata"] = frappe.parse_json(row.metadata) if row.metadata else {}
	return rows
