"""STD workbench: instance audit trail slice (Phase 11)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.std_engine.services.action_availability_service import (
	_perm_read,
	resolve_std_document,
)


def build_std_instance_audit_trail(instance_code: str, actor: str | None = None) -> dict[str, Any]:
	user = (actor or "").strip() or frappe.session.user
	if user in (None, "", "Guest"):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	code = (instance_code or "").strip()
	if not code:
		return {"ok": False, "error": "invalid", "message": str(_("Instance code is required."))}

	resolved = resolve_std_document("STD Instance", code)
	if not resolved:
		return {"ok": False, "error": "not_found", "message": str(_("No document matches this instance code."))}

	doctype, name, _inst = resolved
	if doctype != "STD Instance" or not _perm_read(doctype, name, user):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	events = frappe.get_all(
		"STD Audit Event",
		filters={"object_code": code},
		fields=["audit_event_code", "event_type", "actor", "timestamp", "previous_state", "new_state", "reason"],
		order_by="timestamp desc",
		limit=200,
	)

	return {"ok": True, "instance_code": code, "events": events}
