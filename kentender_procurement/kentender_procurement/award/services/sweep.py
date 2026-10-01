# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Award sweep (scheduler): receive reports Award has not yet taken up,
take up Tenders' events and Evaluation's corrections, refresh eligibility
at deadlines, and retry failed technical deliveries — each with its original
identity. Nothing here decides anything a person must decide."""

from __future__ import annotations

import frappe


def run() -> None:
	from kentender_procurement.award.services import corrections, eligibility, events, explanation, intake, notices, records, tender_events

	for step in (intake.retry_pending, tender_events.sweep, eligibility.sweep, notices.retry_failed, events.retry_pending, explanation.retry_pending):
		try:
			step()
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title=f"Award sweep step {step.__name__} failed")
	for name in frappe.get_all(records.CASE, filters={"cancelled": 0}, pluck="name"):
		try:
			corrections.pull_case(name)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title=f"Award corrections pull failed for {name}")
