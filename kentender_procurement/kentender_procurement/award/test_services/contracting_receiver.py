# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The synthetic Contracting receiver (AWD-CHG-001 v0.4 §13 "synthetic …
Contracting adapters only"; plan D10). It stands in for the proposed
Contracting operations `ReceiveAwardPublicationEvent` and the package receipt,
recording one durable receipt per event, package or update, and one
"Prepare contract" task for the designated Contracting owner. It proves the
proposed contract only; it creates no contract. It answers only on a test
environment, and the `contracting_down` switch makes it unavailable."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.award.services import clock, contracting, profile, records, simulation

INBOX = "Award Test Contracting Inbox"


class TestContractingReceiver:
	def _receive(self, kind: str, payload: dict[str, Any], *, task: bool = False, obligation: bool = False) -> dict[str, Any]:
		if simulation.flag("contracting_down") or (kind == "Decision event" and simulation.flag("event_delivery_down")):
			raise contracting.ReceiverUnavailable("The test Contracting receiver is switched off.")
		reference = cstr(payload.get("reference"))
		existing = frappe.db.get_value(INBOX, {"reference": reference}, ["receipt_id", "received_at", "task_user"], as_dict=True)
		if existing:
			return {"receipt": existing.receipt_id, "received_at": existing.received_at, "task_user": existing.task_user, "duplicate": True}
		owner = cstr(profile.current().get("contracting_owner")) if task else ""
		row = records.new(INBOX, receipt_id=f"CTR-RCPT-{frappe.generate_hash(length=10).upper()}", kind=kind, award_case=cstr(payload.get("award_case")),
			reference=reference, payload_json=records.dumps(payload), received_at=clock.now(), task_user=owner or None, task_state="Open" if task else "",
			publication_obligation=1 if obligation else 0, fixture_namespace=cstr(payload.get("fixture_namespace")))
		return {"receipt": row.receipt_id, "received_at": row.received_at, "task_user": owner}

	def receive_decision_event(self, payload: dict[str, Any]) -> dict[str, Any]:
		# A No award event never manufactures a contract-publication obligation (§5.8).
		return self._receive("Decision event", payload, obligation=payload.get("outcome") == "Award")

	def receive_package(self, payload: dict[str, Any]) -> dict[str, Any]:
		return self._receive("Package", payload, task=True)

	def receive_update(self, payload: dict[str, Any]) -> dict[str, Any]:
		return self._receive("Update", payload)


def receiver() -> TestContractingReceiver | None:
	return TestContractingReceiver() if simulation.enabled() else None
