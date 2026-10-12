# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The financial comparison and recommendation (EVL-CHG-001 v0.4 §4.4; plan
D9; tracker EVL4-507, EVL4-508; boards D03, D03-READY, D03-FUNDING, D03-TIE,
D04-FAIL, D07-NO-RESPONSIVE, D07-TIE).

Exact decimal KES. The submitted total is a source fact and is never
written back. Evaluation adjustments come only from a published rule; this
template publishes none, so they read **None**. Only responsive bids whose
required financial checks are resolved are ranked, lowest evaluated total
first; equal totals share a rank. While an unresolved bid could change the
outcome, the table is a **Provisional comparison** and no recommendation is
made. A nonresponsive bid shows **Not assessed — mandatory requirement not
met** and **Not ranked**. With no published tie-break, equal leading totals
give **No single recommendation — equal evaluated totals**. No responsive
bid gives **No responsive bids**. A single responsive bid can be
recommended. No preference margin, tax treatment, discount or exchange rate
is introduced after closing, and funding never changes a result.

A bid whose every unresolved requirement the committee has explicitly
recorded for a qualified report (a "Qualified report" conclusion) is not
pending: the comparison then reports **Qualified report**, a completed
account of the issue with no recommendation (§4.4, §5.5), so the report can
be frozen for signing (AUD-EVL-002)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_evaluation.services import aggregate, checks, funding

NOT_ASSESSED = "Not assessed — mandatory requirement not met"
NOT_RANKED = "Not ranked"
NONE = "None"
PROVISIONAL = "Provisional comparison"
NO_RESPONSIVE = "No responsive bids"
TIE = "No single recommendation — equal evaluated totals"
TIE_REASON = "The published tender has no tie-break rule."
QUALIFIED = "Qualified report"


def _money(value: str) -> Decimal | None:
	try:
		return Decimal(cstr(value))
	except Exception:
		return None


def compare(case: str, *, with_funding: bool = True) -> dict[str, Any]:
	doc = frappe.get_doc("Evaluation Case", case)
	run = checks.current_run(case)
	if not run:
		return {"rows": [], "provisional": False, "outcome": None, "run": None}
	human = aggregate.human_record(case)
	rows = []
	for bid in frappe.get_all("Evaluation Bid", filters={"evaluation_case": case}, fields=["name", "entry_number", "tenderer_name", "submitted_total", "currency"],
			order_by="entry_number asc"):
		res = aggregate.bid_results(case, run, bid.name, human)
		financial = next((r for r in res["requirements"] if r["group_id"] == aggregate.FINANCIAL), None)
		row = {"bid": bid.name, "bidder": bid.tenderer_name, "eligibility": res["groups"][aggregate.ELIGIBILITY],
			"technical": res["groups"][aggregate.TECHNICAL], "responsiveness": res["responsiveness"], "currency": bid.currency,
			"submitted_total": cstr(bid.submitted_total), "adjustments": NONE, "evaluated_total": None, "position": NOT_RANKED, "financial": financial["result"] if financial else aggregate.NA}
		if res["responsiveness"] == "Not responsive":
			row["evaluated_total"], row["adjustments"] = NOT_ASSESSED, NOT_ASSESSED
		elif res["responsiveness"] == "Responsive" and row["financial"] == aggregate.MEETS:
			row["evaluated_total"] = cstr(bid.submitted_total)  # no published adjustment in this template
		else:
			row["evaluated_total"] = aggregate.REVIEW
			# unresolved, but only on requirements the committee recorded for a qualified report
			unresolved = [r for r in res["requirements"] if r["result"] == aggregate.REVIEW]
			row["qualified_unresolved"] = [r["label"] for r in unresolved] if unresolved and all(r["qualified"] for r in unresolved) else []
		rows.append(row)
	ranked = sorted([r for r in rows if r["evaluated_total"] not in (NOT_ASSESSED, aggregate.REVIEW)], key=lambda r: _money(r["evaluated_total"]))
	position, previous = 0, None
	for n, r in enumerate(ranked, 1):
		amount = _money(r["evaluated_total"])
		if amount != previous:
			position, previous = n, amount
		r["position"] = position
	unresolved_rows = [r for r in rows if r["evaluated_total"] == aggregate.REVIEW]
	pending = [r for r in unresolved_rows if not r.get("qualified_unresolved")]
	qualified = [r for r in unresolved_rows if r.get("qualified_unresolved")]
	provisional = bool(pending) and len(rows) > 1 and bool(ranked or pending)
	outcome, recommended, reason, funds = None, None, "", None
	if not pending:
		if qualified:
			outcome = QUALIFIED
			reason = "; ".join(f"{r['bidder']}: {', '.join(r['qualified_unresolved'])} unresolved, recorded for a qualified report" for r in qualified)
		elif not ranked:
			outcome, reason = NO_RESPONSIVE, "; ".join(f"{r['bidder']}: not responsive" for r in rows)
		elif len([r for r in ranked if r["position"] == 1]) > 1:
			outcome, reason = TIE, TIE_REASON
		else:
			recommended = ranked[0]
			outcome = "Recommendation"
			reason = "The only bid received meets the published requirements." if len(rows) == 1 else "The lowest evaluated responsive bid."
			if with_funding:
				funds = funding.compare(doc.tender, _money(recommended["evaluated_total"]))
	return {"rows": rows, "provisional": provisional, "label": PROVISIONAL if provisional else "", "outcome": outcome, "reason": reason, "run": run,
		"recommended": recommended, "funding": funds, "pending": [r["bid"] for r in pending]}
