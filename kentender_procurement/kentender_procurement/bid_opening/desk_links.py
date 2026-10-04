# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Tender record's link to its bid opening (BOP-CHG-001 v0.10 §9: "The
internal Desk Tender record links to a Bid opening work item and one focused
opening record."), answered for Tenders through `kt_tender_record_links`.
Only a reader of the opening gets the link; before the opening exists there
is none."""

from __future__ import annotations

from typing import Any

import frappe


def tender_record_links(*, tender: str, user: str) -> list[dict[str, Any]]:
	from kentender_procurement.bid_opening.services import reads, records

	case = records.case_for(tender)
	if not case or not reads.can_read(case, user):
		return []
	reference = frappe.db.get_value(records.CASE, case, "tender_reference")
	return [{"key": "bid-opening", "label": "Bid opening", "route": ["tenders", reference, "opening"]}]
