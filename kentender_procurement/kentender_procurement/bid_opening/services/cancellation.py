# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CloseCancelledOpening (BOP-CHG-001 v0.10 §5 Cancelled after start, §7
ConsumeTenderCancellation; binding row → PRC `CloseAbortedProceeding`;
BOP-N18, BOP-A18; plan D8).

An authoritative Tenders cancellation after an actual Start stops every
further reveal, readout, record and completion. The partial chronology, the
actual start and the cessation time are kept; there is no opening record to
sign and nothing goes to Evaluation. Tenders owns the notices. Under
TPR-CHG-001 v0.13 a Tender cannot be cancelled after submissions close, so
in this build the path is reached only by that owner's authoritative event
(FU-BOP-06)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_opening.services import clock, not_held, prc, records

STARTED = ("Opening", "Interrupted", "Readout complete", "Awaiting attestations")


def close_cancelled_opening(*, tender: str, cancellation_reference: str) -> dict[str, Any]:
	from kentender_procurement.proceedings.services import lifecycle

	key = f"cancelled-after-start:{cancellation_reference}"

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if doc.state not in STARTED:
			return records.summary(doc, closed=False)
		closed = lifecycle.close_aborted(**prc.ref(doc.name), cancellation_reference=cancellation_reference, custody_reference=cstr(doc.manifest_handoff),
			idempotency_key=prc.key(key, "abort"), actor=prc.SYSTEM_ACTOR)
		for name in frappe.get_all(not_held.DECISION, filters={"opening_case": doc.name, "status": "Open"}, pluck="name"):
			item = frappe.get_doc(not_held.DECISION, name)
			item.update({"status": "Cleared", "cleared_at": clock.now(), "clearing_event": closed["event_id"]})
			records.save(item)
		records.bump(doc, state="Cancelled after start", ended_at=clock.now(), last_committed_event=closed["last_event"])
		return records.summary(doc, closed=True, cancellation=cancellation_reference, last_event=closed["last_event"])

	return records.command("CloseCancelledOpening", tender=tender, idempotency_key=key, actor=prc.SYSTEM_ACTOR, payload={"cancellation": cancellation_reference},
		body=body)
