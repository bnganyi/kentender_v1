# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""FinishCeremony, the empty outcome, and the register (BOP-CHG-001 v0.10 §4
Register, §5 Readout complete and the no-bids branch, §7 RecordZeroBidOutcome /
FinishCeremony; binding row → PRC `EndProceeding`; BOP-A05, A07, N02A, N08,
N12, A19).

- End opening: only when every current bid has been opened, read out and
  recorded with its pages, no package problem is open, and every appointed
  member is still present. The register is frozen as version 1 with its
  digest; the actual session ends.
- End opening with no bids: the single action after Start when the box held
  no current bid. It records the factual empty outcome and ends the session
  together, once; the register is frozen empty. A convened session is never
  "Not held", and nothing was decrypted.
A register is never edited afterwards; a correction is a supplement."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cint

from kentender_procurement.bid_opening.services import ceremony, clock, errors, labels, prc, records

REGISTER = "Opening Register"


def register_rows(case: str) -> list[dict[str, Any]]:
	return [{"number": e.entry_number, "entry": e.entry_id, "receipt": e.receipt_reference, "tenderer": e.bidder_name,
		"submitted_total": labels.money(e.submitted_total, e.currency), "security_given": e.security_given or "",
		"recorded_at": str(e.readout_confirmed_at), "package_digest": e.package_digest, "pages": e.designated_pages, "price_page": cint(e.price_page)}
		for e in ceremony.entries(case) if e.status == "Read out"]


def _freeze(doc) -> Any:
	rows = register_rows(doc.name)
	number = frappe.db.count(REGISTER, {"opening_case": doc.name}) + 1
	return records.insert(frappe.get_doc({
		"doctype": REGISTER, "register_id": f"{doc.opening_id}-REG-{number:02d}", "opening_case": doc.name, "version_number": number,
		"entry_ids_json": json.dumps([r["entry"] for r in rows]), "entry_count": len(rows), "is_empty": int(not rows), "register_digest": records.digest(rows),
		"frozen_at": clock.now(),
	}))


def finish_ceremony(*, tender: str, expected_version: int, idempotency_key: str, user: str) -> dict[str, Any]:
	from kentender_procurement.proceedings.services import lifecycle

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		ceremony.require_chair(doc, user)
		records.check_version(doc, expected_version)
		if doc.state != "Opening":
			errors.fail("BOP_VERSION_CONFLICT", {"reason": "state", "state": doc.state})
		refused = ceremony._material_check(doc)
		if refused:
			return refused
		current = ceremony.envelopes(doc)
		if not current:
			errors.fail("BOP_VERSION_CONFLICT", {"reason": "no_bids_use_empty_outcome"})
		read = {e.envelope_id for e in ceremony.entries(doc.name) if e.status == "Read out" and e.designated_pages}
		missing = [e["receipt_reference"] for e in current if e["envelope_id"] not in read]
		if missing or ceremony.open_pause(doc.name):
			return {"ok": False, "code": "BOP_READOUT_INCOMPLETE", "message": errors.message("BOP_READOUT_INCOMPLETE"), "missing": len(missing)}
		ended = lifecycle.end_proceeding(**prc.ref(doc.name), owner_event_id=f"end:{doc.name}", idempotency_key=prc.key(idempotency_key, "end"), actor=user)
		register = _freeze(doc)
		records.bump(doc, state="Readout complete", outcome="Bids opened", ended_at=clock.now(), register=register.name, last_committed_event=ended["event_id"])
		return records.summary(doc, register=register.name, entries=register.entry_count)

	return records.command("FinishCeremony", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"expected_version": expected_version}, body=body)


def end_with_no_bids(*, tender: str, expected_version: int, idempotency_key: str, user: str) -> dict[str, Any]:
	from kentender_procurement.proceedings.services import lifecycle

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		ceremony.require_chair(doc, user)
		records.check_version(doc, expected_version)
		if doc.state != "Opening":
			errors.fail("BOP_VERSION_CONFLICT", {"reason": "state", "state": doc.state})
		refused = ceremony._material_check(doc)
		if refused:
			return refused
		if ceremony.envelopes(doc):
			errors.fail("BOP_READOUT_INCOMPLETE")
		ended = lifecycle.end_proceeding(**prc.ref(doc.name), owner_event_id=f"end:{doc.name}", idempotency_key=prc.key(idempotency_key, "end"), actor=user,
			outcome_event={"event_type": "NoBidsOutcome", "owner_event_id": f"no-bids:{doc.name}", "payload": {"current_bids": 0}, "note": "No bids to open"})
		register = _freeze(doc)
		records.bump(doc, state="Readout complete", outcome="No bids", ended_at=clock.now(), register=register.name, last_committed_event=ended["event_id"])
		return records.summary(doc, register=register.name, entries=0)

	return records.command("EndOpeningWithNoBids", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"expected_version": expected_version}, body=body)
