# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Bid Opening scheduler sweep (plan D7, D8, D11). Every pass, for each
published or cancelled Tender:

- prepare its content-free opening case if it has none (PrepareOpeningCase);
- follow an effective addendum's new deadline until the box closes;
- close the case as Not held when Tenders cancelled the Tender before Start;
- after the deadline, attach the sealed close (ReceiveClosedBox);
- record members whose presence lapsed;
- after the deadline and before Start, open an Opening access support
  incident for an unavailable opening service, secure access or public
  attendance service, and notify support.

Reading a page never does any of this. One Tender's failure never stops the
others."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import get_datetime

from kentender_procurement.bid_opening.services import (
	arrangements, availability, case, clock, close_intake, incidents, not_held, presence, records,
)
from kentender_procurement.tenders.services import opening_seam

INCIDENT_TYPES = {"BOP_OPENING_PROFILE_UNAVAILABLE": "Opening profile unavailable", "BOP_CREDENTIAL_UNAVAILABLE": "Credential unavailable"}


def run() -> dict[str, int]:
	done = {"prepared": 0, "received": 0, "not_held": 0, "lapsed": 0, "incidents": 0}
	for tender in opening_seam.opening_candidates():
		try:
			done_for = sweep_tender(tender)
			for k, v in done_for.items():
				done[k] += v
		except Exception:
			frappe.log_error(title=f"Bid opening sweep failed for {tender}")
	return done


def sweep_tender(tender: str) -> dict[str, int]:
	out = {"prepared": 0, "received": 0, "not_held": 0, "lapsed": 0, "incidents": 0}
	facts = opening_seam.tender_facts(tender)
	if not facts:
		return out
	if not records.case_for(tender):
		if facts["cancelled"]:
			return out
		out["prepared"] += int(case.prepare_opening_case(tender=tender)["prepared"])
	if facts["cancelled"]:
		out["not_held"] += int(not_held.consume_tender_cancellation(tender=tender)["consumed"])
		return out
	case.refresh_deadline(tender)
	out["received"] += int(close_intake.receive_closed_box(tender=tender).get("received", False))
	out["lapsed"] += presence.sweep_lapses(tender)
	out["incidents"] += sweep_incidents(tender)
	return out


def sweep_incidents(tender: str) -> int:
	name = records.case_for(tender)
	doc = frappe.get_doc(records.CASE, name)
	if doc.state not in ("Awaiting deadline", "Ready to open") or clock.now() < get_datetime(doc.effective_deadline):
		return 0
	wanted = []
	verdict = availability.get_opening_availability()
	if not verdict["available"] and verdict["code"] in INCIDENT_TYPES:
		wanted.append(INCIDENT_TYPES[verdict["code"]])
	if arrangements.current(doc.name) and not availability.attendance_channel_available():
		wanted.append("Attendance service unavailable")
	existing = {r.incident_type for r in incidents.open_incidents(doc.name)}
	missing = [t for t in wanted if t not in existing]
	if not missing:
		return 0

	def body() -> dict[str, Any]:
		locked = records.lock(tender)
		for incident_type in missing:
			incidents.ensure(locked, incident_type)
		records.bump(locked)
		return records.summary(locked, opened=missing)

	records.command("OpenAccessIncidents", tender=tender, idempotency_key=f"incidents:{name}:{','.join(missing)}:{clock.now()}", actor="system", payload={}, body=body)
	return len(missing)
