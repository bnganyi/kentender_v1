# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Reading an Opening incident's details, and exporting it, are audited (Project Owner, 10 October 2026).

An incident has a **summary** — reference, kind, who handles it, notice state — that the opening page shows to the committee,
the Accounting Officer and the Opening access support holders as part of the page itself, and **details** — the full history,
the resolution note and, for support only, the opaque envelope identifier. Only the details are a protected read:

- `get_details` is an explicit request that names its **purpose**; it records one `Opening Incident Access Event` (actor, time,
  incident, action, purpose, capacity, outcome) and a refusal is recorded too, answered in the masked "Not found" words.
  A repeat with the same request key returns the same answer and records nothing more.
- A page refresh, a poll or any read of the summary records nothing, so the trail is never padded with "user read" events that
  are no one's decision.
- `export_opening` records one `Export` event per incident it includes.
- The event carries no incident content and no free text; the trail is read only by the Auditor and the Accounting Officer
  (`trail`), never through a Desk, list, search or export (the record is sealed)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_opening.services import appointment, clock, incidents, labels, notify, people, records

EVENT = "Opening Incident Access Event"
VIEW, EXPORT = "View details", "Export"
PURPOSES = ("Investigate the problem", "Record the resolution", "Check the problem as a committee member", "Account for the opening", "Audit the opening")
EXPORT_PURPOSE = "Export of the opening record"
SUPPORT, CHAIR, ACCOUNTING_OFFICER, AUDITOR, READER = "Opening access support", "Chair", "Accounting Officer", "Auditor", "Opening reader"
TRAIL_READERS = (ACCOUNTING_OFFICER, AUDITOR)


def capacity(case: str, user: str) -> str:
	"""The one capacity in which `user` may read this opening's incident details, or ''."""
	if user in notify.holders():
		return SUPPORT
	member = appointment.chair(case)
	if member and member["member_user"] == user:
		return CHAIR
	if people.holds(user, people.ACCOUNTING_OFFICER):
		return ACCOUNTING_OFFICER
	return ""


def record(*, case: str, incident_id: str, action: str, purpose: str, actor: str, role: str, outcome: str, request_key: str = "") -> Any:
	return records.insert(frappe.get_doc({
		"doctype": EVENT, "opening_case": case, "incident_id": incident_id, "action": action, "purpose": purpose, "actor": actor, "actor_role": role,
		"occurred_at": clock.now(), "outcome": outcome, "request_key": request_key,
	}))


def get_details(*, tender: str, incident: str, purpose: str, idempotency_key: str, user: str) -> dict[str, Any]:
	"""`GetIncidentDetails`: an explicit, audited read of one incident's details."""
	if purpose not in PURPOSES:
		return {"ok": False, "message": "Say why you are opening these details.", "errors": {"purpose": "Choose why you are opening these details."}, "purposes": list(PURPOSES)}

	def body() -> dict[str, Any]:
		case = records.case_for(tender)
		row = frappe.get_doc(incidents.INCIDENT, {"opening_case": case, "incident_id": incident}) if case and frappe.db.exists(incidents.INCIDENT, {"opening_case": case, "incident_id": incident}) else None
		if row is None:
			raise frappe.DoesNotExistError("Not found")
		role = capacity(case, user)
		if not role:
			# the refusal is evidence: it is recorded, returned as data (so the command commits it), then masked below
			record(case=case, incident_id=row.incident_id, action=VIEW, purpose=purpose, actor=user, role="", outcome="Refused", request_key=idempotency_key)
			return {"ok": False, "refused": True}
		record(case=case, incident_id=row.incident_id, action=VIEW, purpose=purpose, actor=user, role=role, outcome="Allowed", request_key=idempotency_key)
		details = {
			"incident_id": row.incident_id, "kind": row.incident_type, "status": row.status, "raised_label": labels.when_seconds(row.raised_at), "handled_by": people.full_name(row.holder_user) if row.holder_user else "Opening access support",
			"notification_state": row.notification_state, "notification_attempts": int(row.notification_attempts or 0), "last_notified_label": labels.when_seconds(row.last_notified_at) if row.last_notified_at else "",
			"resolution_note": cstr(row.resolution_note), "resolved_label": labels.when_seconds(row.resolved_at) if row.resolved_at else "",
			"resolved_by": people.full_name(row.resolved_by) if row.resolved_by else "",
		}
		if role == SUPPORT:
			details["envelope"] = cstr(row.envelope_id)  # the opaque identifier: only the support holder who works the problem sees it
		return {"ok": True, "opening": case, "details": details, "capacity": role}

	result = records.command("GetIncidentDetails", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"incident": incident, "purpose": purpose}, body=body)
	if result.get("refused"):
		raise frappe.DoesNotExistError("Not found")
	return result


def record_export(*, case: str, user: str, incident_ids: list[str]) -> None:
	"""One `Export` event per incident an export included (no content, no free text)."""
	role = capacity(case, user) or READER
	for incident_id in incident_ids:
		record(case=case, incident_id=incident_id, action=EXPORT, purpose=EXPORT_PURPOSE, actor=user, role=role, outcome="Allowed")


def trail(*, tender: str, user: str) -> dict[str, Any]:
	"""The access trail of one opening, for the Auditor and the Accounting Officer only (masked for everyone else)."""
	case = records.case_for(tender)
	allowed = bool(case) and (people.holds(user, people.AUDITOR) or people.holds(user, people.ACCOUNTING_OFFICER))
	if not allowed:
		raise frappe.DoesNotExistError("Not found")
	rows = frappe.get_all(EVENT, filters={"opening_case": case}, fields=["incident_id", "action", "purpose", "actor", "actor_role", "occurred_at", "outcome"], order_by="occurred_at asc, creation asc", limit_page_length=0)
	return {"rows": [{
		"incident_id": r.incident_id, "action": r.action, "purpose": r.purpose, "actor": people.full_name(r.actor), "capacity": r.actor_role or "No capacity on this opening",
		"at_label": labels.when_seconds(r.occurred_at), "outcome": r.outcome,
	} for r in rows], "empty_text": "No incident details have been read or exported for this opening."}
