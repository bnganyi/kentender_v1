"""Controlled business actions for KenTender (Phase I).

Orchestrates ``run_workflow_guard`` then ``log_audit_event``. Domain-specific
mutations belong in explicit callers or future services; this module only
standardizes guard + audit ordering.

``event_type`` for audit rows written here: ``ken.business_action``.
"""

from __future__ import annotations

from frappe.model.document import Document

from kentender_core.services.audit_event_service import log_audit_event
from kentender_core.services.workflow_guard_service import run_workflow_guard

_EVENT_TYPE = "ken.business_action"


def execute_business_action(action: str, document: Document) -> tuple[bool, str]:
	"""Run workflow guard, then append an Audit Event on success.

	Returns ``(ok, message)``. On guard failure, no audit row is inserted.
	"""
	ok, message = run_workflow_guard(action, document)
	if not ok:
		return False, message

	entity = getattr(document, "procuring_entity", "") or ""
	log_audit_event(
		event_type=_EVENT_TYPE,
		entity=entity,
		document_type=document.doctype,
		document_name=document.name,
		action=action,
		metadata={"action": action},
	)
	return True, ""
