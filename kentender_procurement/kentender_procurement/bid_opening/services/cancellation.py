# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CloseCancelledOpening (BOP-CHG-001 v0.10 §5 Cancelled after start, §7
ConsumeTenderCancellation; binding row → PRC `CloseAbortedProceeding`;
BOP-N18, BOP-A18; plan D8).

An authoritative Tenders cancellation after an actual Start stops every
further reveal, readout, record and completion. The partial chronology, the
actual start and the cessation time are kept; there is no opening record to
sign and nothing goes to Evaluation. Tenders owns the notices. TPR-CHG-001
v0.24 §5.12 supports the cancellation after submissions close (closing
FU-BOP-06); the path is reached through Tenders' delivery of its existing
TenderCancelled event (`cancellation_consumer`)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_opening.services import clock, incidents, not_held, prc, records

STARTED = ("Opening", "Interrupted", "Readout complete", "Awaiting attestations")


def close_cancelled_opening(*, tender: str, cancellation_reference: str, source_at=None) -> dict[str, Any]:
	"""BOP-CHG-001 v0.16 §7.2 CloseCancelledOpening: a case after Start ends Cancelled after start with the TPR cancellation, once. The partial chronology is
	kept; the cessation time is when Tenders decided the cancellation (`source_at`), the receipt time when this ran; the Accounting Officer's open item clears
	with the committed PRC closure. Nothing is finalised, signed or handed to Evaluation."""
	from kentender_procurement.proceedings.services import lifecycle

	key = f"cancelled-after-start:{cancellation_reference}"

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if doc.state not in STARTED:
			return records.summary(doc, closed=False)
		closed = lifecycle.close_aborted(**prc.ref(doc.name), cancellation_reference=cancellation_reference, custody_reference=cstr(doc.manifest_handoff),
			idempotency_key=prc.key(key, "abort"), actor=prc.SYSTEM_ACTOR, source_at=source_at)
		records.bump(doc, state="Cancelled after start", ended_at=source_at or clock.now(), last_committed_event=closed["last_event"])
		not_held.clear_open_items(doc, event_id=closed["event_id"], reference=cancellation_reference)
		incidents.close_for_cancellation(doc, reference=cancellation_reference, event_id=closed["event_id"])
		return records.summary(doc, closed=True, cancellation=cancellation_reference, last_event=closed["last_event"])

	return records.command("CloseCancelledOpening", tender=tender, idempotency_key=key, actor=prc.SYSTEM_ACTOR, payload={"cancellation": cancellation_reference},
		body=body)
