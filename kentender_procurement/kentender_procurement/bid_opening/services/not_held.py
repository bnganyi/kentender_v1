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

from kentender_procurement.bid_opening.services import clock, errors, people, prc, records
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
		number = sequence.next_count(DECISION, {"opening_case": doc.name})
		item = records.insert(frappe.get_doc({
			"doctype": DECISION, "decision_item_id": f"{doc.opening_id}-DEC-{number:02d}", "opening_case": doc.name, "kind": "Not held", "holder_user": user,
			"reason": cstr(reason).strip(), "status": "Open", "created_at": clock.now(),
		}))
		records.bump(doc, state="Not held")
		return records.summary(doc, decision_item=item.name)

	return records.command("RecordOpeningNotHeld", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"reason": reason, "expected_version": expected_version},
		body=body)


def consume_tender_cancellation(*, tender: str) -> dict[str, Any]:
	"""Before Start only; after Start the partial session closes (Phase 5)."""
	from kentender_procurement.proceedings.services import lifecycle

	facts = opening_seam.tender_facts(tender)
	name = records.case_for(tender)
	if not facts or not facts["cancelled"] or not name:
		return {"ok": True, "consumed": False}
	doc = frappe.get_doc(records.CASE, name)
	if doc.state not in NOT_STARTED:
		return {"ok": True, "consumed": False, "state": doc.state}
	reference = cstr((facts["cancellation"] or {}).get("reference"))
	key = f"cancelled-before-start:{reference or tender}"

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if doc.state not in NOT_STARTED:
			return records.summary(doc, consumed=False)
		lifecycle.mark_not_held(**prc.ref(doc.name), reason="The Tender was cancelled before the opening.", cancellation_reference=reference,
			custody_reference=cstr(doc.manifest_handoff), idempotency_key=prc.key(key, "not-held"), actor=prc.SYSTEM_ACTOR)
		records.bump(doc, state="Not held")
		return records.summary(doc, consumed=True, cancellation=reference)

	return records.command("ConsumeTenderCancellation", tender=tender, idempotency_key=key, actor=prc.SYSTEM_ACTOR, payload={"cancellation": reference}, body=body)


def _label(value) -> str:
	from kentender_procurement.bid_opening.services import labels

	return labels.when(value)
