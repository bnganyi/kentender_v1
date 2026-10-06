# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Tender record's link to its award (AWD-CHG-001 v0.4 §9; plan D13),
on `kt_tender_record_links`, for readers of the award only."""

from __future__ import annotations

from typing import Any

import frappe


def tender_record_links(*, tender: str, user: str) -> list[dict[str, Any]]:
	from kentender_procurement.award.services import guards, records

	name = frappe.db.get_value(records.CASE, {"tender": tender}, "name")
	if not name or not guards.can_read(user):
		return []
	return [{"key": "award", "label": "Award", "route": ["award", name]}]


def tender_stage_summary(*, tender: str, user: str) -> list[dict[str, Any]]:
	"""What this stage discloses to this reader on the Tender record (`kt_tender_stage_summaries`, OVS-CHG-001 v0.6 §8)."""
	from kentender_procurement.award.services import stage_summary

	return stage_summary.for_tender(tender=tender, user=user)
