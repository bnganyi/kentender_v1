# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Who sits on a Tender's evaluation committee, or is its secretary, published to
the tender-security intake duty's conflict rules (`kt_tender_duty_participants`;
BDS-CHG-001 §6)."""

from __future__ import annotations

from frappe.utils import cstr

from kentender_procurement.bid_evaluation.services import records, roster


def participants(tender: str) -> dict[str, str]:
	case = records.case_for(tender)
	if not case:
		return {}
	out = {user: "on the evaluation committee" for user in roster.member_users(case)}
	secretary = cstr(roster.secretary(case))
	if secretary:
		out.setdefault(secretary, "the evaluation secretary")
	return out
