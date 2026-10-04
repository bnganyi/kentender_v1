# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PrepareOpeningCase (BOP-CHG-001 v0.10 §4 Opening case, §7; binding row
`PrepareOpeningCase` → PRC `CreateProceeding`).

One content-free case per Published Tender, with its Proceeding in Pending.
No bid manifest, count, start time or page-view side effect. The opening
sweep prepares it; a Tender that stays published is never prepared twice."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_opening.services import clock, prc, prc_owner, records
from kentender_procurement.tenders.services import opening_seam

SYSTEM = prc.SYSTEM_ACTOR


def opening_id(tender_reference: str) -> str:
	return f"BOC-{cstr(tender_reference).removeprefix('TND-')}"


def prepare_opening_case(*, tender: str, idempotency_key: str = "", actor: str = SYSTEM) -> dict[str, Any]:
	from kentender_procurement.proceedings.services import lifecycle

	facts = opening_seam.tender_facts(tender)
	if not facts or not facts["published"]:
		raise frappe.DoesNotExistError("Not found")
	key = idempotency_key or f"prepare:{tender}"

	def body() -> dict[str, Any]:
		existing = records.case_for(tender)
		if existing:
			return records.summary(frappe.get_doc(records.CASE, existing), prepared=False)
		doc = records.insert(frappe.get_doc({
			"doctype": records.CASE, "opening_id": opening_id(facts["tender_reference"]), "tender": tender, "tender_reference": facts["tender_reference"],
			"tender_title": facts["title"], "effective_deadline": facts["submission_deadline"], "state": "Awaiting deadline", "record_version": 1,
			"fixture_namespace": records.namespace() or facts["fixture_namespace"],
		}))
		with prc_owner.acting(doc.name):
			created = lifecycle.create_proceeding(**prc.owner(doc.name), title=f"Bid opening · {facts['tender_reference']}", idempotency_key=prc.key(key, "create"),
				actor=actor)
		doc.proceeding = created["proceeding"]
		records.save(doc)
		return records.summary(doc, prepared=True, proceeding=created["proceeding"])

	return records.command("PrepareOpeningCase", tender=tender, idempotency_key=key, actor=actor, payload={}, body=body)


def refresh_deadline(tender: str) -> None:
	"""An effective addendum moves the deadline and the opening time together
	(BOP-CHG-001 v0.10 §1); the case follows it until the box closes."""
	name = records.case_for(tender)
	facts = opening_seam.tender_facts(tender)
	if not name or not facts:
		return
	doc = frappe.get_doc(records.CASE, name)
	if doc.state == "Awaiting deadline" and facts["submission_deadline"] and str(doc.effective_deadline) != str(facts["submission_deadline"]):
		records.bump(doc, effective_deadline=facts["submission_deadline"])
