# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RecordOpeningNotHeld and a Tender cancelled before Start (BOP-CHG-001 v0.10
§5 Not held, §7, §10.7; binding rows → PRC `MarkNotHeld`; BOP-N17, BOP-A18).

After the scheduled instant, while nothing has started, the Accounting
Officer records the actual reason. The Proceeding becomes Not held, which is
terminal: no later Start, release or resumption on this case. The bids stay
sealed under their existing custody, no count is shown, and the Accounting
Officer receives the decision item "Decide what happens next". If Tenders
already cancelled the Tender before Start, that authoritative event closes
the case the same way, with no duplicate decision item."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.bid_opening.services import clock, errors, incidents, people, prc, records
from kentender_procurement.tenders.services import opening_seam
from kentender_procurement.services import sequence

DECISION = "Opening Decision Item"
NOT_STARTED = ("Awaiting deadline", "Ready to open")


def record_opening_not_held(*, tender: str, reason: str, expected_version: int, idempotency_key: str, user: str) -> dict[str, Any]:
	from kentender_procurement.proceedings.services import lifecycle

	if not people.holds(user, people.ACCOUNTING_OFFICER):
		raise frappe.DoesNotExistError("Not found")

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		records.check_version(doc, expected_version)
		if doc.state not in NOT_STARTED or prc.state(doc.name) != "Pending":
			errors.fail("BOP_VERSION_CONFLICT", {"reason": "state", "state": doc.state})
		if clock.now() < get_datetime(doc.effective_deadline):
			errors.fail("BOP_DEADLINE_NOT_REACHED", deadline=_label(doc.effective_deadline))
		if not cstr(reason).strip():
			return {"ok": False, "reason": "reason_required", "errors": {"reason": "Record what happened."}}
		lifecycle.mark_not_held(**prc.ref(doc.name), reason=cstr(reason).strip(), custody_reference=cstr(doc.manifest_handoff),
			idempotency_key=prc.key(idempotency_key, "not-held"), actor=user)
		item = ensure_item(doc, kind="Not held", reason=cstr(reason).strip(), holder=user)
		records.bump(doc, state="Not held")
		return records.summary(doc, decision_item=item.name)

	return records.command("RecordOpeningNotHeld", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"reason": reason, "expected_version": expected_version},
		body=body)


def ensure_item(doc, *, kind: str, reason: str, holder: str, incident: str = "", last_event: str = "") -> Any:
	"""The one open decision item for this opening's escalation (BOP-CHG-001 v0.16 §5.2): a Cannot recover finding, a Not held record or a paused opening each
	give the Accounting Officer the same item — never a second. An existing open item is relabelled and refreshed (Opening cannot proceed → Not held, say); it
	carries the Tender it is decided on, so the screen opens the existing Tender decision with this exact reference."""
	name = frappe.db.get_value(DECISION, {"opening_case": doc.name, "status": "Open"}, "name", order_by="creation asc")
	if name:
		item = frappe.get_doc(DECISION, name)
		item.update({"kind": kind, "reason": reason or item.reason, "last_committed_event": last_event or item.last_committed_event, "incident": incident or item.incident})
		return records.save(item)
	number = sequence.next_count(DECISION, {"opening_case": doc.name})
	return records.insert(frappe.get_doc({
		"doctype": DECISION, "decision_item_id": f"{doc.opening_id}-DEC-{number:02d}", "opening_case": doc.name, "kind": kind, "holder_user": holder, "reason": reason,
		"last_committed_event": last_event, "incident": incident, "tender": doc.tender, "escalation_ref": incident or "not-held", "status": "Open", "created_at": clock.now(),
	}))


def clear_open_items(doc, *, event_id: str, reference: str = "") -> list[str]:
	"""The Accounting Officer's open decision items for this case clear here and nowhere else on a cancellation: when the BOP/PRC terminal outcome commits
	(BOP-CHG-001 v0.16 §5.2 "Required clearing event"). Each item records the PRC event that closed it and the cancellation, once; viewing it, a note or a
	referral never reaches this."""
	cleared = []
	for name in frappe.get_all(DECISION, filters={"opening_case": doc.name, "status": "Open"}, pluck="name"):
		item = frappe.get_doc(DECISION, name)
		item.update({"status": "Cleared", "cleared_at": clock.now(), "clearing_event": event_id, "clearing_reference": reference})
		records.save(item)
		cleared.append(name)
	return cleared


def consume_tender_cancellation(*, tender: str) -> dict[str, Any]:
	"""Before Start only (BOP-CHG-001 v0.16 §7.2): the case ends Not held with the TPR cancellation, once. After Start the partial session closes
	(`cancellation.close_cancelled_opening`); a case already Not held has the cancellation attached (`attach_tender_cancellation`)."""
	from kentender_procurement.proceedings.services import lifecycle

	authoritative = opening_seam.authoritative_cancellation(tender)
	name = records.case_for(tender)
	if not authoritative or not name:
		return {"ok": True, "consumed": False}
	doc = frappe.get_doc(records.CASE, name)
	if doc.state not in NOT_STARTED:
		return {"ok": True, "consumed": False, "state": doc.state}
	reference = cstr(authoritative["reference"])
	key = f"cancelled-before-start:{reference}"

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if doc.state not in NOT_STARTED:
			return records.summary(doc, consumed=False)
		closed = lifecycle.mark_not_held(**prc.ref(doc.name), reason="The Tender was cancelled before the opening.", cancellation_reference=reference,
			custody_reference=cstr(doc.manifest_handoff), idempotency_key=prc.key(key, "not-held"), actor=prc.SYSTEM_ACTOR, source_at=authoritative["cancelled_at"])
		records.bump(doc, state="Not held")
		cleared = clear_open_items(doc, event_id=closed["event_id"], reference=reference)
		incidents.close_for_cancellation(doc, reference=reference, event_id=closed["event_id"])
		return records.summary(doc, consumed=True, cancellation=reference, cleared=cleared)

	return records.command("ConsumeTenderCancellation", tender=tender, idempotency_key=key, actor=prc.SYSTEM_ACTOR, payload={"cancellation": reference}, body=body)


def attach_tender_cancellation(*, tender: str) -> dict[str, Any]:
	"""A TPR cancellation for a case already Not held (the opening never started; the Accounting Officer recorded the fact; OF-F03). The record stays Not
	held — no restart, no new decision item, no manifest created or replaced — and gains the cancellation with its decision and receipt times, once. The exact
	open decision item clears with it."""
	from kentender_procurement.proceedings.services import lifecycle

	authoritative = opening_seam.authoritative_cancellation(tender)
	name = records.case_for(tender)
	if not authoritative or not name:
		return {"ok": True, "attached": False}
	reference = cstr(authoritative["reference"])
	key = f"cancelled-after-not-held:{reference}"
	proceeding = frappe.db.get_value(records.CASE, name, "proceeding")
	if proceeding and cstr(frappe.db.get_value("Proceeding", proceeding, "cancellation_reference")) == reference:
		return {"ok": True, "attached": False, "replayed": True}  # this very cancellation is already on the record (it ended the case, or was attached): nothing to do

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if doc.state != "Not held":
			return records.summary(doc, attached=False)
		attached = lifecycle.attach_cancellation(**prc.ref(doc.name), cancellation_reference=reference, idempotency_key=prc.key(key, "attach"), actor=prc.SYSTEM_ACTOR,
			source_at=authoritative["cancelled_at"])
		records.bump(doc)
		cleared = clear_open_items(doc, event_id=attached["event_id"], reference=reference)
		incidents.close_for_cancellation(doc, reference=reference, event_id=attached["event_id"])
		return records.summary(doc, attached=True, cancellation=reference, cleared=cleared)

	return records.command("AttachTenderCancellation", tender=tender, idempotency_key=key, actor=prc.SYSTEM_ACTOR, payload={"cancellation": reference}, body=body)


def _label(value) -> str:
	from kentender_procurement.bid_opening.services import labels

	return labels.when(value)
