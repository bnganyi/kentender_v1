# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Tender record's link to its bid evaluation (EVL-CHG-001 v0.4 §10,
plan D13), answered for Tenders through `kt_tender_record_links`. Only a
reader of the evaluation gets the link; before the evaluation exists there
is none."""

from __future__ import annotations

from typing import Any

import frappe


def tender_record_links(*, tender: str, user: str) -> list[dict[str, Any]]:
	from kentender_procurement.bid_evaluation.services import reads, records

	case = records.case_for(tender)
	if not case:
		return []
	doc = frappe.get_doc(records.CASE, case)
	if not reads.access(doc, user)["read"]:
		return []
	return [{"key": "bid-evaluation", "label": "Bid evaluation", "route": ["tenders", doc.tender_reference, "evaluation"]}]


def tender_stage_summary(*, tender: str, user: str) -> list[dict[str, Any]]:
	"""What the evaluation discloses to this reader on the Tender record (`kt_tender_stage_summaries`, OVS-CHG-001 v0.6 §8)."""
	from kentender_procurement.bid_evaluation.services import stage_summary

	return stage_summary.for_tender(tender=tender, user=user)
