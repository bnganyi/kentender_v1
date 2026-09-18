# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §12.1 — the append-only Tender Event log and outbox.

Every successful command writes one event carrying the §12.1 minimum
(identity, aggregate + resulting record version, command + idempotency key
hash, actor + responsibility snapshot, UTC/EAT time, previous/resulting
status, affected identities, reason, digests, snapshots). Outbox events
(`status = Pending`) are the internal contract for Planning's invitation
actual, the bidder-facing open-Tender event, the inquiry broadcast and the
Bid Submission handoff; replay never emits a second one (§5.5(7)).
Rejected commands never create a business event."""

from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import uuid4

import frappe
from frappe.utils import cstr

from kentender_procurement.tenders.services import clock, digest, serializer

PRODUCER = "tenders"


def _sequence(tender: str) -> int:
	return int(frappe.db.count("Tender Event", {"tender": tender})) + 1


def emit(
	*,
	tender: str,
	event_type: str,
	command: str,
	idempotency_key: str = "",
	actor: str | None = None,
	assignment_snapshot: str = "",
	previous_status: str = "",
	resulting_status: str = "",
	record_version: int | None = None,
	subject_type: str = "",
	subject_id: str = "",
	reason: str = "",
	payload: dict[str, Any] | None = None,
	status: str = "Delivered",
	consumer: str = "",
	fixture_namespace: str = "",
) -> Any:
	occurred = clock.now()
	body = {
		"schema_version": "1.0",
		"event_type": event_type,
		"command": command,
		"idempotency_key_hash": hashlib.sha256(cstr(idempotency_key).encode()).hexdigest() if idempotency_key else "",
		"actor": actor or frappe.session.user,
		"assignment_snapshot": json.loads(assignment_snapshot) if assignment_snapshot else {},
		"session": cstr(getattr(frappe.local, "session", None) and frappe.local.session.get("sid") or ""),
		"occurred_at_utc": occurred.isoformat(sep=" "),
		"occurred_at_eat": serializer.fmt_datetime_short(occurred),
		"previous_status": previous_status,
		"resulting_status": resulting_status,
		"record_version": record_version,
		"subject_type": subject_type,
		"subject_id": subject_id,
		"reason": reason,
		**(payload or {}),
	}
	doc = frappe.get_doc(
		{
			"doctype": "Tender Event", "event_id": uuid4().hex, "event_type": event_type, "tender": tender, "sequence": _sequence(tender),
			"subject_type": subject_type, "subject_id": subject_id, "occurred_at": occurred, "payload": digest.canonical_json(body),
			"status": status, "consumer": consumer, "delivered_at": occurred if status == "Delivered" else None, "fixture_namespace": fixture_namespace,
		}
	)
	doc.flags.kt_lifecycle = True
	doc.insert(ignore_permissions=True)
	return doc


def pending(*, tender: str, event_type: str, consumer: str = "") -> list[Any]:
	filters = {"tender": tender, "event_type": event_type, "status": "Pending"}
	if consumer:
		filters["consumer"] = consumer
	return [frappe.get_doc("Tender Event", n) for n in frappe.get_all("Tender Event", filters=filters, pluck="name", order_by="sequence asc")]


def exists(*, tender: str, event_type: str, subject_id: str = "") -> bool:
	filters = {"tender": tender, "event_type": event_type}
	if subject_id:
		filters["subject_id"] = subject_id
	return bool(frappe.db.exists("Tender Event", filters))


def mark_delivered(event_doc, *, consumer: str = "") -> None:
	from kentender_procurement.tenders.services import envelope

	envelope.bump(event_doc, status="Delivered", delivered_at=clock.now(), consumer=consumer or event_doc.consumer)


def mark_rejected(event_doc, *, reason: str) -> None:
	from kentender_procurement.tenders.services import envelope

	body = json.loads(event_doc.payload or "{}")
	body["rejection_reason"] = reason
	envelope.bump(event_doc, status="Rejected", payload=digest.canonical_json(body))


def list_for_tender(tender: str) -> list[dict[str, Any]]:
	rows = frappe.get_all(
		"Tender Event", filters={"tender": tender}, fields=["name", "event_id", "event_type", "sequence", "subject_type", "subject_id", "occurred_at", "status", "consumer", "payload"],
		order_by="sequence asc", limit_page_length=0,
	)
	for row in rows:
		try:
			row["payload"] = json.loads(row["payload"] or "{}")
		except ValueError:
			row["payload"] = {}
	return rows
