# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Member review work (EVL-CHG-001 v0.4 §7.1, §7.3 "Valid intake and member
eligible, or member becomes eligible after intake"; tracker EVL4-510).

The review item itself is derived from state by the My Work provider; this
sends its courtesy notice once, when a member first becomes eligible after
intake or at intake for every eligible member, without a second check run."""

from __future__ import annotations

from kentender_procurement.bid_evaluation.services import notify, roster

REVIEWABLE = ("Reviewing",)


def member_became_eligible(doc, user: str) -> int:
	if doc.state not in REVIEWABLE or not doc.source_intake or not roster.status(doc.name, user)["eligible"]:
		return 0
	return notify.tell(doc, [user], subject=f"Review bids for {doc.tender_reference}",
		message=f"The automatic checks for {doc.tender_reference} are ready for your review.", key="review")


def intake_ready(doc) -> int:
	return sum(member_became_eligible(doc, user) for user in roster.eligible_members(doc.name))
