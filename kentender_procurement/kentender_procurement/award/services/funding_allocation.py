# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Award funding allocation: how an awarded price is traced to the Budget reservations that fund it (AWD-CHG-001 v0.7 section 7.1; tracker AWD-FUND).

One award may draw on several reservations, each created for one drawdown line of the authorised Requisition. This module prepares one immutable `AwardFundingAllocation.v1` for the exact committed Award
decision and its supported price. It is a read-only source calculation. It is not a reservation, not an approval, and not an officer's price editor: it distributes an existing supported total for funding
only, and never changes a supplier price, an evaluated amount or a submitted sum.

* The awarded commercial rows come from the frozen evaluation report (`bid_evaluation.contract_seam.awarded_prices`), so what is split is what the evaluation froze.
* Each row's source items come from the published bid definition's price rows (`tenders.award_seam.funding_sources`): the exact Requisition item, drawdown line and quantity. Nothing is inferred from the
  supplier, the managing department, reservation order or remaining balances.
* The Requisition is read again from its owner (`procurement_requisitions.source_seam`): it must still be the authorised Version, its items must still name the drawdown lines the Tender saw, and each drawdown
  line must still hold the reservation the allocation will name.
* Any gap is a `FundingIssue` with a reason in plain words. The positive Award path stays blocked and the existing source-correction route resolves it. An owner that cannot answer is `FundingUnavailable`,
  which is never read as a negative or a success.

The digest covers the content that must not change (the rows, the sources and the totals), not the identity of the decision that retains it, so the same sources give the same digest before and after the decision."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.award.services import funding_split as split
from kentender_procurement.award.services import records, sources, state

SCHEMA = "AwardFundingAllocation.v1"
ALLOCATION = "Award Funding Allocation"
CURRENT, SUPERSEDED = "Current", "Superseded"


class FundingIssue(Exception):
	"""The awarded price cannot be traced to its funding sources. `reason` is plain words for the officer; the source owner's correction route resolves it."""

	def __init__(self, reason: str, **detail: Any):
		super().__init__(reason)
		self.reason = reason
		self.detail = detail


class FundingUnavailable(Exception):
	"""An owner of a source could not answer. Not a negative authorisation and not a success."""


def _offer(doc) -> tuple[str, str, Any, Decimal]:
	"""The frozen report and accepted bid, the committed decision if any, and the supported price."""
	rep = state.current_report(doc)
	if not rep:
		raise FundingUnavailable("The evaluation report the award rests on is not held.")
	snap = state.snapshot(rep)
	recommended = snap.get("recommended") or {}
	bid = cstr(recommended.get("bid"))
	if not bid:
		raise FundingIssue("The signed report names no recommended bid, so there is no awarded price to trace.")
	decision = state.committed_decision(doc)
	if decision and decision.outcome == "Award":
		if decision.bid_reference != recommended.get("bid_reference"):
			raise FundingIssue("The decision does not name the bid the evaluation recommended.")
		total = cstr(decision.evaluated_amount)
	else:
		decision = None
		total = cstr(recommended.get("evaluated_total"))
	try:
		return cstr(snap.get("report")), bid, decision, Decimal(total)
	except Exception as exc:
		raise FundingIssue("The supported award price is not an exact amount.") from exc


def _money(value: Any, label: str) -> Decimal:
	try:
		number = Decimal(cstr(value))
	except Exception as exc:
		raise FundingIssue(f"{label} is not an exact amount.") from exc
	if not number.is_finite():
		raise FundingIssue(f"{label} is not an exact amount.")
	return number


def compute(doc) -> dict[str, Any]:
	"""The allocation of this award's supported price, freshly derived from the owners' sources. Raises `FundingIssue` or `FundingUnavailable`; retains nothing."""
	report, bid, decision, total = _offer(doc)
	try:
		inputs = sources.for_case(doc).allocation_inputs(doc.tender, report, bid)
	except sources.SourceUnavailable as exc:
		raise FundingUnavailable(cstr(exc)) from exc
	except AttributeError as exc:
		raise FundingUnavailable("This award's source provider cannot give the funding allocation inputs.") from exc
	prices, identity, mapped, authoritative = inputs["prices"], inputs["identity"], inputs["mapped"], inputs["authoritative"]
	if identity["tender"] != doc.tender:
		raise FundingIssue("The evaluation was made against a different tender than the award.")
	if not mapped or not mapped.get("price_rows"):
		raise FundingIssue("The awarded items could not be matched to their funding sources.")
	if cstr(mapped["definition"]["digest"]) != cstr(identity["definition_digest"]):
		raise FundingIssue("The bid definition the evaluation used is not the one the tender now holds.")
	requisition = mapped["requisition"]
	if not authoritative:
		raise FundingIssue("Requisitions does not hold the Requisition Version the tender consumed.")
	if not authoritative["authorised"]:
		raise FundingIssue("The Requisition the tender consumed is no longer authorised.")
	if cstr(authoritative["content_digest"]) != cstr(requisition["content_digest"]):
		raise FundingIssue("The Requisition Version changed after the tender consumed it.")
	owner_lines = {line["drawdown_line_id"]: line for line in authoritative["drawdown_lines"]}
	owner_items = {item["requisition_item_id"]: item for item in authoritative["items"]}

	by_line = {row["line"]: row for row in mapped["price_rows"]}
	rows: list[split.Row] = []
	evidence_rows: list[dict[str, Any]] = []
	for priced in prices["lines"]:
		line = cstr(priced.get("line"))
		goods = by_line.get(line)
		if not goods or not goods["sources"]:
			raise FundingIssue(f"Priced line {line} could not be matched to its funding sources.", line=line)
		quantity = _money(priced.get("quantity"), f"Quantity of line {line}")
		covered = Decimal("0")
		coverage = []
		for source in goods["sources"]:
			item_quantity = _money(source["quantity"], f"Quantity of item {source['requisition_item_id']}")
			item = owner_items.get(source["requisition_item_id"])
			if not item or item["drawdown_line_id"] != source["drawdown_line_id"] or _money(item["quantity"], "Item quantity") != item_quantity:
				raise FundingIssue(f"Item {source['requisition_item_id']} no longer matches the Requisition's drawdown line and quantity.", item=source["requisition_item_id"])
			if source["drawdown_line_id"] not in owner_lines or source["drawdown_line_id"] not in mapped["drawdown_lines"]:
				raise FundingIssue(f"Drawdown line {source['drawdown_line_id']} is not one of the Requisition's source lines.", drawdown_line=source["drawdown_line_id"])
			covered += item_quantity
			coverage.append(split.Coverage(source["drawdown_line_id"], item_quantity))
		if covered != quantity:
			raise FundingIssue(f"The source items of line {line} cover {covered} of the {quantity} awarded.", line=line)
		rows.append(split.Row(f"L{line}", _money(priced.get("line_total"), f"Total of line {line}"), tuple(coverage)))
		evidence_rows.append({"row": f"L{line}", "line": line, "price_row": goods["price_row_id"], "quantity": str(quantity), "amount": cstr(priced.get("line_total")),
			"coverage": [{"item": s["requisition_item_id"], "drawdown_line": s["drawdown_line_id"], "quantity": s["quantity"]} for s in goods["sources"]]})
	try:
		result = split.allocate(rows)
		split.check_total(result, total)
	except split.SourceIssue as exc:
		raise FundingIssue(exc.reason, **exc.detail) from exc

	allocations = []
	covered_quantity: dict[str, Decimal] = {}
	for row in rows:
		for cover in row.coverage:
			covered_quantity[cover.source] = covered_quantity.get(cover.source, Decimal("0")) + cover.quantity
	for drawdown_line in sorted(result.totals):
		held = mapped["drawdown_lines"][drawdown_line]
		reservation = cstr(held.get("reservation_id"))
		if not reservation or reservation != cstr(owner_lines[drawdown_line]["reservation_id"]):
			raise FundingIssue(f"Drawdown line {drawdown_line} does not hold the reservation the tender recorded.", drawdown_line=drawdown_line)
		allocations.append({
			"reservation": reservation, "reservation_reference": cstr(held.get("reservation_reference")), "plan_source_allocation": cstr(held.get("plan_item_line_id")),
			"drawdown_line": drawdown_line, "source_line": cstr(held.get("source_line_id")), "source_organisation_unit": cstr(held.get("contributing_org_unit")),
			"budget_line": cstr(held.get("budget_line")), "quantity": str(covered_quantity[drawdown_line]), "amount": str(result.totals[drawdown_line]),
		})
	content = {
		"schema": SCHEMA,
		"tender": {"id": doc.tender, "reference": doc.tender_reference, "lot": doc.lot},
		"bid": {"id": bid},
		"report": {"id": report, "digest": cstr(prices["report"]["digest"])},
		"requisition": {**requisition, "source_set_hash": authoritative["source_set_hash"]},
		"definition": mapped["definition"],
		"currency": cstr(prices["currency"]) or "KES", "scale": split.SCALE, "supported_total": str(total),
		"commercial_rows": evidence_rows, "rounding": result.rows, "allocations": allocations,
		"digests": {"price": records.digest(prices), "sources": records.digest({"tender": mapped, "requisition": authoritative})},
	}
	return {**content, "digest": records.digest(content)}


def current(doc):
	"""The retained allocation now in force for this case's cycle, or None."""
	name = frappe.db.get_value(ALLOCATION, {"award_case": doc.name, "cycle": doc.current_cycle, "status": CURRENT}, "name", order_by="version desc")
	return frappe.get_doc(ALLOCATION, name) if name else None


def retain(doc, decision) -> Any:
	"""Retain the allocation for the committed Award decision, in the same transaction that commits it. The same sources give the same digest: an allocation already retained for this decision is returned, and a
	corrected source gives a new version beside the old one, which is marked Superseded and never overwritten."""
	payload = compute(doc)
	held = current(doc)
	if held and held.digest == payload["digest"] and held.decision == decision.name:
		return held
	version = records.next_number(ALLOCATION, {"award_case": doc.name})
	created = records.new(ALLOCATION, allocation_id=f"{doc.name}-FUN-{version:02d}", award_case=doc.name, cycle=doc.current_cycle, decision=decision.name, decision_version=decision.version, version=version,
		status=CURRENT, currency=payload["currency"], supported_total=payload["supported_total"], payload_json=records.dumps(payload), digest=payload["digest"])
	if held:
		records.update(held, status=SUPERSEDED, superseded_by=created.name)
	return created


def payload_of(allocation) -> dict[str, Any]:
	return records.loads(allocation.payload_json)


def standing(doc) -> dict[str, Any]:
	"""Is the retained allocation still what the sources say? `state` is Current, Absent (none retained yet), Changed (the sources moved), Issue (cannot be traced) or Unavailable (an owner did not answer)."""
	held = current(doc)
	try:
		fresh = compute(doc)
	except FundingIssue as exc:
		return {"state": "Issue", "reason": exc.reason, "detail": exc.detail, "allocation": held.name if held else ""}
	except FundingUnavailable as exc:
		return {"state": "Unavailable", "reason": cstr(exc), "allocation": held.name if held else ""}
	if not held:
		return {"state": "Absent", "digest": fresh["digest"]}
	if held.digest != fresh["digest"]:
		return {"state": "Changed", "reason": "The funding sources changed after the allocation was retained.", "allocation": held.name, "retained": held.digest, "now": fresh["digest"]}
	return {"state": "Current", "allocation": held.name, "digest": held.digest}


def disclosure(doc) -> dict[str, Any]:
	"""AWD-CHG-001 v0.7 §10.4 — the read-only 'Funding sources' table for authorised internal readers: department, quantity and awarded amount per source, with the total. A missing mapping and an unavailable
	owner are their own results, never an empty table that reads as success."""
	held = current(doc)
	try:
		payload = payload_of(held) if held else compute(doc)
	except FundingIssue:
		return {"state": "Missing", "message": "The awarded items could not be matched to their funding sources. Procurement must resolve the source details."}
	except FundingUnavailable:
		return {"state": "Unavailable", "message": "Funding details are unavailable. The system will retry."}
	rows = [{"department": cstr(frappe.db.get_value("Organisation Unit", a["source_organisation_unit"], "unit_name") or a["source_organisation_unit"]), "quantity": a["quantity"], "amount": a["amount"],
		"reservation": a["reservation"], "reservation_reference": a["reservation_reference"], "drawdown_line": a["drawdown_line"], "budget_line": a["budget_line"]} for a in payload["allocations"]]
	return {"state": "Available", "currency": payload["currency"], "rows": rows, "total_quantity": str(sum((Decimal(r["quantity"]) for r in rows), Decimal("0"))), "total_amount": payload["supported_total"],
		"retained": bool(held), "allocation": held.name if held else ""}
