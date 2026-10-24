# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Award's answer to Budget: `VerifyAwardFundingLineage` and `GetAwardFundingAllocation` (AWD-CHG-001 v0.7 section 7.1; BUD-CHG-001 v1.16 BUD-BR-036; registered on the core seam
`kentender_core.services.award_funding_verification`).

Budget turns a reservation into a commitment only when this owner says the whole chain matches. The question is exact: *this* award, *this* retained allocation (by digest), *this* set of reservations and
amounts, for a named purpose. The answer is computed now, not read back from an earlier verification:

* the retained allocation exists, is the Current one for its case, and belongs to the committed Award decision that is still the case's decision;
* the case is not cancelled and holds no funding, validity or restriction issue that stops a positive step;
* the allocation is derived again from the owners' sources (the frozen report and its prices, the Tender's source mapping, the authorised Requisition) and gives the same digest;
* the package the agreement came from, when its digest is named, is the package that carries this allocation;
* every reservation and amount asked about is one the allocation names, at its exact amount.

Verified returns the whole immutable payload and its revision, so the caller can pin it and recheck it where it matters. Not verified names each mismatch. An owner that cannot answer is Unavailable: never a
negative authorisation and never a success. Nothing is written."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_core.services.award_funding_verification import NOT_VERIFIED, UNAVAILABLE, VERIFIED, Verification
from kentender_procurement.award.services import funding_allocation as allocation, issues, records, state


def _not(*mismatches: str) -> Verification:
	return Verification(NOT_VERIFIED, [m for m in mismatches if m])


def _same_amount(left: Any, right: Any) -> bool:
	try:
		return Decimal(cstr(left)) == Decimal(cstr(right))
	except Exception:
		return False


class Provider:
	def verify(self, *, lineage: dict[str, Any], contract: str, allocations: list[dict[str, Any]], purpose: str) -> Verification | None:
		case, digest = cstr(lineage.get("award")), cstr(lineage.get("allocation_digest"))
		if not case or not digest:
			return _not("The conversion names no award and no funding allocation.")
		if not frappe.db.exists(records.CASE, case):
			return _not("The award is not held by the Award owner.")
		doc = frappe.get_doc(records.CASE, case)
		held = frappe.db.get_value(allocation.ALLOCATION, {"award_case": case, "digest": digest}, "name")
		if not held:
			return _not("The funding allocation named for this award is not held.")
		retained = frappe.get_doc(allocation.ALLOCATION, held)
		mismatches: list[str] = []
		if retained.status != allocation.CURRENT:
			mismatches.append("The funding allocation has been superseded by a corrected one.")
		decision = frappe.get_doc(state.DECISION, retained.decision) if retained.decision else None
		if not decision or not decision.committed or decision.outcome != "Award" or doc.current_decision != decision.name:
			mismatches.append("The allocation does not belong to the award decision now in force.")
		if doc.cancelled:
			mismatches.append("The award has been cancelled.")
		if lineage.get("decision") and decision and cstr(lineage.get("decision")) != decision.name:
			mismatches.append("The award decision named for the conversion is not the one the allocation was retained for.")
		if mismatches:
			return _not(*mismatches)
		for issue in issues.holding(doc):  # a funding, validity, review or restriction issue that holds the award stops a financial step as it stops a notice
			mismatches.append(f"An open {cstr(issue.issue_type).lower()} issue holds this award: {cstr(issue.title)}")
		if mismatches:
			return _not(*mismatches)
		try:
			fresh = allocation.compute(doc)
		except allocation.FundingIssue as exc:
			return _not(exc.reason)
		except allocation.FundingUnavailable as exc:
			return Verification(UNAVAILABLE, [cstr(exc)])
		if fresh["digest"] != retained.digest:
			return _not("The funding sources changed after the allocation was retained.")
		package_digest = cstr(lineage.get("package_digest"))
		if package_digest:
			package = frappe.db.get_value(state.PACKAGE, {"award_case": case, "digest": package_digest}, "name")
			content = records.loads(frappe.db.get_value(state.PACKAGE, package, "content_json")) if package else {}
			if not package or cstr((content.get("funding_allocation") or {}).get("digest")) != retained.digest:
				return _not("The package the agreement came from does not carry this funding allocation.")
		payload = allocation.payload_of(retained)
		named = {a["reservation"]: a for a in payload["allocations"]}
		asked = [{"reservation": cstr(a.get("reservation")), "amount": a.get("amount")} for a in allocations or []]
		if not asked:
			return _not("No reservation was named.")
		for row in asked:
			held_row = named.get(row["reservation"])
			if not held_row:
				mismatches.append(f"Reservation {row['reservation']} is not one of the reservations this award is allocated to.")
			elif not _same_amount(held_row["amount"], row["amount"]):
				mismatches.append(f"Reservation {row['reservation']} is allocated {held_row['amount']} by the award, not {cstr(row['amount'])}.")
		if len({r["reservation"] for r in asked}) != len(asked):
			mismatches.append("A reservation is named more than once.")
		if mismatches:
			return _not(*mismatches)
		return Verification(VERIFIED, [], {**payload, "allocation_id": retained.name, "decision": decision.name, "decision_version": decision.version}, retained.digest)


def service() -> Provider:
	return Provider()


def get_award_funding_allocation(award: str) -> dict[str, Any] | None:
	"""`GetAwardFundingAllocation`: the retained allocation in force for an award case, or None. Authority-filtering belongs to the caller's reading surface."""
	if not frappe.db.exists(records.CASE, award):
		return None
	doc = frappe.get_doc(records.CASE, award)
	held = allocation.current(doc)
	return {**allocation.payload_of(held), "allocation_id": held.name, "decision": held.decision, "decision_version": held.decision_version} if held else None
