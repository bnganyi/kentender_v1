# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Who sits on a Tender's opening committee, published to the tender-security
intake duty's conflict rules (`kt_tender_duty_participants`; BDS-CHG-001 §6)."""

from __future__ import annotations

from kentender_procurement.bid_opening.services import appointment, records


def participants(tender: str) -> dict[str, str]:
	case = records.case_for(tender)
	return {m["member_user"]: "on the opening committee" for m in appointment.roster(case)} if case else {}
