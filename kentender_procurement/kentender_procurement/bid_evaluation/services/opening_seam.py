# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid Evaluation's published read for Bid Opening (EVL-CHG-001 v0.5 §3,
BOP-A17; AUD-EVL-013).

The independent opening member cannot evaluate the same Tender. Evaluation
enforces that when it appoints (it asks `bid_opening.evaluation_seam`); Bid
Opening enforces the other order here, so a person already on the Tender's
current evaluation committee cannot be named its independent opening member.
Bid Opening never reads an Evaluation record directly."""

from __future__ import annotations

from kentender_procurement.bid_evaluation.services import records, roster


def committee_members(tender: str) -> set[str]:
	"""The users on the Tender's current evaluation committee (empty before appointment)."""
	case = records.case_for(tender)
	return set(roster.member_users(case)) if case else set()
