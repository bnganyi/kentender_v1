# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The technical read of Bid Submission (KT-STD-001 v1.6 §3A.6; AUTH-ADR-001
§8; BDS-CHG-001 §5.9 item 7, §12.3 item 7).

**Narrowed on 10 October 2026 (Project Owner).** A technical reader —
Administrator or System Manager — no longer finds or reads any bid record:
not its existence, its count, its identity, its receipt, nor a supplier's
tender-security intake, whether before or after the opening. Opening does
not unlock them for a technical account; after it, access follows business
permissions only. What remains is the service status: availability and open
incidents, readable by the Technical Operator and technical readers, with no
bid count (`affected_bids` is not returned) and no reference to a bid.

Registered through the `kt_technical_reference_resolvers` (empty) and
`kt_technical_read_probes` hooks."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_core.services.authorization import is_technical

from kentender_procurement.bid_submission.services import availability, labels


def reference_resolvers() -> list[dict]:
	"""None: no sealed record is findable through the Technical record search
	(BDS-CHG-001 §5.9, §6; AUTH-ADR-001 §8 exception; TRUST-ADR-001 §2)."""
	return []


def _audit_read(actor: str) -> None:
	"""Every read of the service status by a technical account or the incident operator is
	audited (TRUST-ADR-001 v0.4 §2A). The audit row is committed with the read, which is a GET."""
	from kentender_core.services.audit_event_service import log_audit_event

	log_audit_event(event_type="submission_service_status_read", entity="Bid Submission", document_type="Bid Submission Service", document_name="status", action="read", performed_by=actor, metadata={})
	frappe.db.commit()


def get_submission_service_status(*, user: str | None = None) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
	from kentender_procurement.bid_submission.services import guidance

	if not is_technical(actor) and actor not in _holders(guidance.TECHNICAL):
		raise frappe.DoesNotExistError("This record is unavailable or you do not have permission to view it.")
	from kentender_procurement.bid_submission.services import close

	_audit_read(actor)
	gate = availability.get_submission_availability()
	incidents = frappe.get_all("Bid Submission Incident", filters={"status": "Open"}, fields=["incident_key", "kind", "title", "reference", "opened_at"], order_by="opened_at asc")
	return {
		"outcome": "OK",
		"availability": {"available": gate["available"], "reason_code": gate["code"], "message": gate["message"]},
		"open_incidents": [{**dict(i), "opened_at": labels.datetime_label(i.opened_at)} for i in incidents],
		# FU-V08-44: read on demand, so an overdue close shows even with the scheduler off
		"overdue_closes": close.overdue_closes(),
	}


def _holders(role: str) -> list[str]:
	"""Holders in force now — an expired or scheduled one is not a holder (AR-04)."""
	from kentender_core.services.authorization import active_holders

	return active_holders(role)


def read_probes() -> list[dict]:
	from kentender_procurement.bid_submission import api

	return [
		{"label": "bid_submission.get_submission_service_status", "call": api.get_submission_service_status, "kwargs": lambda: {}},
	]
