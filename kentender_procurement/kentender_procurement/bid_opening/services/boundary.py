# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The opening access boundary, published to Bid Submission's tender-security
matching (`kt_opening_boundary_probes`; Project Owner, 10 October 2026): crossed
when the Tender's opening has started. Before it, no intake may be linked to a
bid."""

from __future__ import annotations

import frappe

from kentender_procurement.bid_opening.services import records


def crossed(tender: str) -> bool:
	case = records.case_for(tender)
	return bool(case and frappe.db.get_value(records.CASE, case, "started_at"))
