# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Where the delivery stands, read from the records (CM-CHG-001 v0.8 sections 5.1, 5.4, 5.6, 5.7).

Nothing here is stored. The position of every ordered line and every unit is **derived** each time from the immutable arrivals, the effective acceptance decisions and the
custody returns, so there is no second copy to go stale: how many units arrived, were accepted (and so received into stock or assets), were rejected and returned, remain in the
supplier's custody-for-collection, and how much of the order the supplier still owes. A unit decided by an effective acceptance report is not decided again; a rejected unit that
has been collected is closed; a rejected unit that has not been collected is still in custody. The remaining entitlement counts accepted units only, so a replacement of a rejected
unit consumes the original entitlement and never adds to the order."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint

from kentender_contracts.services import opening, records

ARRIVAL = "Contract Arrival"
ACCEPTANCE = "Contract Acceptance"
EVENT = "Contract Event"
RETURN_EVENT = "Custody return"


def _terms(case: str) -> dict[str, Any]:
	name = frappe.db.get_value("Contract Agreement Version", {"contract_case": case, "state": "Effective"}, "terms_json", order_by="version_no desc")
	return records.loads(name) if name else {}


def arrivals(case: str) -> list[dict[str, Any]]:
	rows = frappe.get_all(ARRIVAL, filters={"contract_case": case}, fields=["name", "arrival_no", "delivery_reference", "received_at", "recorded_at", "receiver", "destination", "items_json", "notes", "state"], order_by="arrival_no asc")
	return [{**r, "items": records.loads(r.items_json, [])} for r in rows]


def returned_units(case: str) -> set[str]:
	units: set[str] = set()
	for detail in frappe.get_all(EVENT, filters={"contract_case": case, "event_type": RETURN_EVENT}, pluck="detail_json"):
		units |= set(records.loads(detail).get("units", []))
	return units


def effective_lines(row: Any) -> list[dict[str, Any]]:
	"""What an effective report decided. The report's own lines are what the chair proposed; the decision the signatures made (a dissent moves a unit to needs-review) is kept apart and wins."""
	decided = records.loads(row.decision_json, {}) if row.get("decision_json") else {}
	return decided.get("lines") or records.loads(row.lines_json, [])


def dissents(case: str) -> dict[str, int]:
	"""unit -> the inspection version a member's recorded dissent was made against, for units no later effective report has decided. The reading is repeated before it is certified again."""
	out: dict[str, int] = {}
	for row in frappe.get_all(ACCEPTANCE, filters={"contract_case": case, "state": "Effective"}, fields=["decision_json", "lines_json", "version_no"], order_by="version_no asc"):
		decided = records.loads(row.decision_json, {}) if row.decision_json else {}
		for line in decided.get("lines") or records.loads(row.lines_json, []):
			for kind in ("accepted", "rejected"):
				for unit in line["units"].get(kind, []):
					out.pop(unit, None)
		for said in decided.get("dissent", []):
			for unit, version in (said.get("inspections") or {}).items():
				out[unit] = cint(version)
	return out


def decisions(case: str) -> dict[str, dict[str, Any]]:
	"""unit -> its latest effective acceptance disposition: `{disposition, acceptance, version, reason}`."""
	out: dict[str, dict[str, Any]] = {}
	for row in frappe.get_all(ACCEPTANCE, filters={"contract_case": case, "state": "Effective"}, fields=["name", "version_no", "lines_json", "decision_json"], order_by="version_no asc"):
		for line in effective_lines(row):
			for disposition, units in (line.get("units") or {}).items():
				for unit in units:
					out[unit] = {"disposition": disposition, "acceptance": row.name, "version": row.version_no, "reason": (line.get("reasons") or {}).get(unit, "")}
	return out


def position(case: str) -> dict[str, Any]:
	terms = _terms(case)
	ordered = {l["line_id"]: l for l in terms.get("lines", [])}
	decided, returned = decisions(case), returned_units(case)
	lines = {lid: {"line_id": lid, "item": l.get("description") or l.get("item"), "ordered": cint(l["quantity"]), "rate": l["rate"], "arrived": 0, "accepted": 0, "rejected": 0, "deferred": 0,
		"returned": 0, "in_custody": 0, "pending_decision": 0, "unidentified": 0, "excess_held": 0} for lid, l in ordered.items()}
	units: dict[str, dict[str, Any]] = {}
	for arrival in arrivals(case):
		for item in arrival["items"]:
			row = lines.get(item["line_id"])
			if row is None:  # goods the contract does not name are held and recorded, but belong to no line
				continue
			row["arrived"] += cint(item["quantity"])
			named = item.get("units") or []
			excess = set(item.get("excess_units") or [])
			row["unidentified"] += max(0, cint(item["quantity"]) - len(named))
			for unit in named:
				said = decided.get(unit)
				if unit in returned:
					status = "Returned"
				elif unit in excess:
					status = "Excess"  # more than the contract asks for: held apart, never inspected or accepted
				elif said:
					status = {"accepted": "Accepted", "rejected": "Rejected", "deferred": "Deferred"}[said["disposition"]]
				else:
					status = "Awaiting decision"
				units[unit] = {"unit": unit, "line_id": item["line_id"], "arrival": arrival["name"], "arrival_no": arrival["arrival_no"], "status": status, "acceptance": said["acceptance"] if said else "",
					"replaces": (item.get("replaces") or {}).get(unit, "")}
	for unit in units.values():
		row = lines[unit["line_id"]]
		key = {"Accepted": "accepted", "Rejected": "rejected", "Deferred": "deferred", "Returned": "returned", "Awaiting decision": "pending_decision", "Excess": "excess_held"}[unit["status"]]
		row[key] += 1
	for lid, row in lines.items():  # a registered existing contract starts with units already accepted: they count as arrived and accepted, never as new activity
		before = opening.line(case, lid)["accepted"]
		row["arrived"] += before
		row["accepted"] += before
	for row in lines.values():
		row["in_custody"] = row["arrived"] - row["accepted"] - row["returned"]
		row["remaining"] = max(0, row["ordered"] - row["accepted"])
		row["excess"] = max(0, (row["arrived"] - row["returned"] - row["rejected"]) - row["ordered"])
	return {"lines": lines, "units": units, "ordered": sum(r["ordered"] for r in lines.values()), "accepted": sum(r["accepted"] for r in lines.values()),
		"arrived": sum(r["arrived"] for r in lines.values()), "in_custody": sum(r["in_custody"] for r in lines.values()), "remaining": sum(r["remaining"] for r in lines.values())}


def decided_units(case: str) -> set[str]:
	"""Units an effective report has finally decided (accepted or rejected). A deferred unit is still open to a later report."""
	return {unit for unit, said in decisions(case).items() if said["disposition"] in ("accepted", "rejected")}
