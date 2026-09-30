# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Bid Evaluation sweep (EVL-CHG-001 v0.4 §5.1, §5.7; plan D5 as refined by
D25).

On the scheduler, for each published or cancelled Tender: prepare an
in-scope evaluation on its publication; take up a completed nonempty opening
(retrying a failed intake under the same identity); close a preparation on
a verified final no-bids opening; and apply the Tender owner's events. The
sweep is the binding to Tenders and Bid Opening: calling Evaluation from
inside an opening's own transaction could roll the opening back, so no
producer calls Evaluation directly. Each Tender commits on its own, and one
Tender's failure never stops the others. Every step is idempotent."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.bid_evaluation.services import correction, intake, issues, preparation, records, tender_events


def sweep_tender(tender: str) -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import evaluation_seam as opening

	done: dict[str, Any] = {"tender": tender}
	if not records.case_for(tender):
		done["preparation"] = preparation.ensure_preparation(tender=tender).get("reason") or "prepared"
	outcome = (opening.final_outcome(tender) or {}).get("outcome")
	name = records.case_for(tender)
	state = frappe.db.get_value(records.CASE, name, ["state", "source_intake"], as_dict=True) if name else None
	if outcome == "Bids opened" and not (state and state.source_intake):
		done["intake"] = intake.receive_opening_package(tender=tender).get("received")
	elif outcome == "No bids" and state and state.state not in records.TERMINAL:
		done["empty"] = intake.receive_empty_outcome(tender=tender).get("closed")
	done["events"] = tender_events.consume(tender)
	done["rules"] = bool(issues.reconcile_rules(tender))
	done["supplements"] = correction.consume_supplements(tender)
	return done


def run() -> dict[str, int]:
	"""Scheduler entry (every minute)."""
	from kentender_procurement.tenders.services import evaluation_seam as tenders

	counts = {"swept": 0, "failed": 0}
	for tender in tenders.evaluation_candidates():
		try:
			sweep_tender(tender)
			frappe.db.commit()
			counts["swept"] += 1
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title=f"Bid Evaluation sweep failed for {tender}")
			counts["failed"] += 1
	return counts
