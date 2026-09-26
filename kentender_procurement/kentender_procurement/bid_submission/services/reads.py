# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid Submission reads (BDS-CHG-001 v0.8 §7.1). Reads create nothing:
no organisation, workspace, acknowledgement, audit or business event.

`get_available_tenders` — BDS-DES-01: the public list of published Tenders
over the Tenders projection, filtered by title/reference search, method,
reservation and closing state at the trusted instant. It carries only what
the list shows (title, reference, Procuring Entity, method, reservation,
submission deadline and the Tender's public address) — no account status,
internal value, schema family or document count (§10.2)."""

from __future__ import annotations

from typing import Any

from frappe.utils import cstr

from kentender_procurement.bid_submission.services import clock, labels, tenders_gateway

CLOSING = (("open", "Open Tenders"), ("closed", "Closed or cancelled"), ("all", "All Tenders"))
EMPTY_TEXT = "No Tenders match these filters."


def _closing_matches(closing: str, availability: str) -> bool:
	if closing == "all":
		return True
	if closing == "closed":
		return availability in ("closed", "cancelled")
	return availability == "open"


def _options(label: str, values: set[str]) -> list[dict[str, str]]:
	return [{"value": "", "label": label}] + [{"value": v, "label": v} for v in sorted(v for v in values if v)]


def get_available_tenders(*, search: str = "", method: str = "", reservation: str = "", closing: str = "open") -> dict[str, Any]:
	search, method, reservation = cstr(search).strip(), cstr(method).strip(), cstr(reservation).strip()
	closing = closing if closing in {value for value, _label in CLOSING} else "open"
	public = tenders_gateway.available_tenders(at=clock.now())
	needle = search.lower()
	rows = [
		{
			"reference": r["reference"], "title": r["title"], "procuring_entity": r["procuring_entity"], "method": r["method"], "reservation": r["reservation"],
			"submission_deadline_label": labels.datetime_label(r["submission_deadline"]), "href": f"/tenders/{r['reference']}",
		}
		for r in public
		if _closing_matches(closing, r["availability"])
		and (not needle or needle in r["title"].lower() or needle in r["reference"].lower())
		and (not method or r["method"] == method)
		and (not reservation or r["reservation"] == reservation)
	]
	n = len(rows)
	noun = "available Tender" if closing == "open" else "Tender"
	return {
		"rows": rows,
		"count_text": f"{n} {noun}{'' if n == 1 else 's'}" if rows else "",
		"empty_text": "" if rows else EMPTY_TEXT,
		"applied": {"search": search, "method": method, "reservation": reservation, "closing": closing},
		"options": {
			"method": _options("All methods", {r["method"] for r in public}),
			"reservation": _options("All categories", {r["reservation"] for r in public}),
			"closing": [{"value": value, "label": label} for value, label in CLOSING],
		},
	}
