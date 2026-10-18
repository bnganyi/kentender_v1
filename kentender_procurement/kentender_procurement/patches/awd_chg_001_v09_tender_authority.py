# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AWD-CHG-001 v0.9 §5.11 — a durable Tender-level authority record for every Tender that predates it.

post_model_sync, idempotent. Publication now registers the record (`kt_tender_publication_registrars`); this registers what is already there:

- every Award case that has no record gets one copied from the case, including a notice already issued or in progress;
- an open Tender, or a cancelled one, gets "Not issued" (an open Tender has had no evaluation; cancellation is refused once any notice is issued);
- a Tender past submission that has no case and no record stays without one, so Award answers Unknown. Absence of a case proves nothing; the Award
  owner reconciles it through the existing route.

Nothing is reset: a record that already exists is never touched.
"""

from __future__ import annotations

import frappe


def execute() -> None:
	if not frappe.db.table_exists("Award Tender Authority"):
		return
	from kentender_procurement.award.services import tender_authority
	from kentender_procurement.tenders.services import opening_seam

	from_cases = tender_authority.backfill_cases()
	facts = [fact for fact in (opening_seam.tender_facts(t) for t in opening_seam.opening_candidates()) if fact]
	from_tenders = tender_authority.backfill(facts)
	frappe.logger().info("AWD v0.9: Tender authority records — %s from cases, %s", from_cases, from_tenders)
