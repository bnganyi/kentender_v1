# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RecordReadout with SelectOpeningTargets (BOP-CHG-001 v0.10 §7, §10.3 OPEN /
READOUT, §11 "Record what was read aloud"; binding rows → PRC
`AppendProceedingEvent`; BOP-A05, BOP-A20, BOP-N16).

After a member has actually read the opened bid's facts aloud, the recorder
names the member who spoke and confirms, in one action, what was read and
the committee's chosen page(s) to sign. The server records the confirmation
instant; any reported speech time is kept separately and attributed to the
recorder, never used as the trusted time. The amounts are the package's
own and cannot be edited. Page 1 is only a proposal; the renderer's price
page is recorded as found. Readout and page choice commit together or not at
all. Software does not claim to witness the speech."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr, get_datetime

from kentender_procurement.bid_opening.services import appointment, ceremony, clock, errors, labels, prc, presence, records


def record_readout(*, tender: str, entry: str, speaker: str, designated_pages: list[int], expected_version: int, idempotency_key: str, user: str,
		reported_speech_at=None) -> dict[str, Any]:
	from kentender_procurement.proceedings.services import events

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		ceremony.require_recorder(doc, user)
		records.check_version(doc, expected_version)
		if doc.state != "Opening":
			errors.fail("BOP_VERSION_CONFLICT", {"reason": "state", "state": doc.state})
		refused = ceremony._material_check(doc)
		if refused:
			return refused
		row = frappe.get_doc(ceremony.ENTRY, {"opening_case": doc.name, "entry_id": entry}) if frappe.db.exists(ceremony.ENTRY, {"opening_case": doc.name, "entry_id": entry}) else None
		if row is None or row.status != "Opened":
			errors.fail("BOP_VERSION_CONFLICT", {"reason": "not_the_opened_bid"})
		member = appointment.member(doc.name, speaker)
		if not member or speaker not in presence.present_members(doc.name):
			return {"ok": False, "code": "BOP_MEMBER_ABSENT", "errors": {"speaker": "Choose the committee member who read the details aloud."}}
		pages = sorted({cint(p) for p in designated_pages or []})
		if not pages or any(p < 1 or p > cint(row.page_count) for p in pages):
			return {"ok": False, "code": "BOP_READOUT_INCOMPLETE", "errors": {"designated_pages": f"Choose the page(s) the committee will sign, from 1 to {row.page_count}."}}
		now = clock.now()
		if reported_speech_at and (get_datetime(reported_speech_at) > now or get_datetime(reported_speech_at) < get_datetime(row.revealed_at)):
			return {"ok": False, "code": "BOP_READOUT_INCOMPLETE", "errors": {"reported_speech_at": "The time read aloud must be after the bid was opened and not later than now."}}
		event = events.append_event(**prc.ref(doc.name), event_type="ReadoutConfirmed", source="Owner", owner_event_id=f"readout:{row.entry_id}",
			payload={"entry": row.entry_id, "speaker": speaker, "read_aloud": labels.read_aloud(row), "designated_pages": pages, "price_page": cint(row.price_page)},
			note=f"{member['full_name']} read bid {row.entry_number} aloud", linked_event=row.proceeding_event, reported_at=reported_speech_at,
			reported_by=user if reported_speech_at else "", idempotency_key=prc.key(idempotency_key, "readout"), actor=user)
		row.update({"status": "Read out", "readout_speaker": speaker, "readout_confirmed_at": now, "readout_confirmed_by": user,
			"reported_speech_at": reported_speech_at or None, "designated_pages": ",".join(str(p) for p in pages)})
		records.save(row)
		records.bump(doc, last_committed_event=event["event_id"])
		return records.summary(doc, entry=row.entry_id, confirmed_at=str(now))

	return records.command("RecordReadout", tender=tender, idempotency_key=idempotency_key, actor=user,
		payload={"entry": entry, "speaker": speaker, "pages": list(designated_pages or []), "reported": cstr(reported_speech_at or ""), "expected_version": expected_version},
		body=body)
