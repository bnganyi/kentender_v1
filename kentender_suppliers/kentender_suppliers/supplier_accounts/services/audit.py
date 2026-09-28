# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Supplier Account audit (BDS-CHG-001 v0.8 §12.1) through the platform
Audit Event service: one event per successful command, stamped with the
trusted clock. No evidence bytes, tokens or other secrets are recorded.
Each event's metadata carries the §12.1 minimum under `event`: schema
version, command and request-key hash, organisation and its resulting
record version, acting assignment, the instant in UTC and EAT, and the
Account's previous and resulting status."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_core.services.audit_event_service import log_audit_event
from kentender_suppliers.supplier_accounts.services import clock

EVENT_TYPE = "supplier_account"
ENTITY = "Supplier Accounts"


EVENT_SCHEMA_VERSION = 1


def _organisation_of(doctype: str, name: str, metadata: dict[str, Any]) -> str:
	if doctype == "Supplier Organisation":
		return name
	if metadata.get("organisation"):
		return cstr(metadata["organisation"])
	return cstr(frappe.db.get_value(doctype, name, "organisation")) if frappe.get_meta(doctype).has_field("organisation") else ""


def _assignment(actor: str, organisation: str, at) -> str:
	"""The actor's acting assignment: a supplier person's assignment in the
	organisation, or an internal responsibility (the support officer's)."""
	from kentender_suppliers.supplier_accounts.services import authorization as authz

	if organisation:
		mine = authz.assignments_of(actor, organisation=organisation, at=at)
		if mine:
			return cstr(mine[0].get("name") or mine[0].get("assignment_id"))
	return cstr(frappe.db.get_value("User Responsibility Assignment", {"user": actor, "business_role": authz.SUPPORT_ROLE, "status": "Enabled"}, "name"))


def record(*, doctype: str, name: str, action: str, actor: str, metadata: dict[str, Any] | None = None) -> str:
	from kentender_core.utils.instants import to_utc_iso

	from kentender_suppliers.supplier_accounts.services import labels

	at = clock.now()
	metadata = dict(metadata or {})
	context = getattr(frappe.local, "kt_acc_command", None) or {}
	organisation = _organisation_of(doctype, name, metadata)
	status = frappe.db.get_value("Supplier Organisation", organisation, ["account_status", "record_version"], as_dict=True) if organisation else None
	resulting = cstr(status.account_status) if status else ""
	metadata["event"] = {
		"schema_version": EVENT_SCHEMA_VERSION, "command": cstr(context.get("command")), "idempotency_key_hash": cstr(context.get("key_hash")),
		"organisation": organisation, "record_version": int(status.record_version or 0) if status else 0, "assignment": _assignment(actor, organisation, at),
		"occurred_at_utc": to_utc_iso(at), "occurred_at_eat": labels.datetime_seconds_label(at),
		"previous_status": (context.get("transitions") or {}).get(organisation, resulting), "resulting_status": resulting,
	}
	return log_audit_event(event_type=EVENT_TYPE, entity=ENTITY, document_type=doctype, document_name=name, action=action, performed_by=actor, timestamp=at, metadata=metadata)
