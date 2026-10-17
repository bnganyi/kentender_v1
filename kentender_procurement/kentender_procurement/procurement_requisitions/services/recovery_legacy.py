# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.20 §19.1 — Requisitions' read-only classification of a Tender cancelled before the recovery existed.

Called by Tenders' reconciliation (`tenders/services/recovery_reconciliation.py`), which adds what only Tenders and Award can say. This
reads the Requisition's own lineage, asks Planning for the state of each originating drawdown and Budget for its account of each
reservation, and names what it finds. It writes nothing and repairs nothing: a partly released or partly restored legacy source is
reported as such, never completed by guessing, and a source it cannot map is reported as unmapped.

Priority when several things are true: a surviving obligation, then a partial legacy effect, then a release for another reason, then an
unmappable source."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.procurement_requisitions.services import cancellation_recovery, eligibility_gateway, funding_gateway
from kentender_procurement.procurement_requisitions.services.owner_refusal import OwnerRefusal

ELIGIBLE = "eligible"
REGISTERED = "already registered"
PARTIAL = "partial legacy effect"
OBLIGATION = "converted or surviving obligation"
OTHER_REASON = "released for another reason"
UNMAPPED = "unmapped"
AMBIGUOUS = "ambiguous"
PROBE = "legacy-classification"


def _result(klass: str, reason: str = "", **more) -> dict[str, Any]:
	return {"class": klass, "reason": reason, **more}


def classify(*, tender: str, cancellation: str, handoff: str) -> dict[str, Any]:
	existing = frappe.db.get_value(cancellation_recovery.DOCTYPE, {"cancellation": cstr(cancellation)}, ["name", "status"], as_dict=True)
	if existing:
		return _result(REGISTERED, "", recovery=existing.name, status=existing.status)
	requisition = cstr(frappe.db.get_value("Authorised Requisition Handoff", handoff, "requisition")) if cstr(handoff) else ""
	if not requisition:
		return _result(UNMAPPED, "The Tender names no authorised handoff that can be found.")
	hand = frappe.get_doc("Authorised Requisition Handoff", handoff)
	root = frappe.get_doc("Procurement Requisition", requisition)
	if not hand.consumed_at or cstr(hand.tender) != cstr(tender):
		return _result(AMBIGUOUS, "The handoff was not consumed by this Tender.")
	if root.current_state != "Authorised" or cstr(root.handoff) != hand.name or not root.authorised_version:
		return _result(AMBIGUOUS, f"The Requisition is no longer the authorised owner of this handoff ({cstr(root.current_state)}).")
	rows = cancellation_recovery._source_rows(frappe.get_doc("Requisition Version", root.authorised_version))
	if not rows:
		return _result(UNMAPPED, "The authorised Requisition drew nothing.")
	gaps = cancellation_recovery._mapping_gaps(rows)
	if gaps:
		return _result(UNMAPPED, "Planning or Budget evidence is missing for " + ", ".join(gaps) + ".")

	found: list[tuple[str, str]] = []
	facts = {f["drawdown_reference"]: f for f in eligibility_gateway.drawdown_facts(recovery_id=PROBE, drawdown_references=[r["drawdown_reference"] for r in rows])}
	states = []
	for row in rows:
		fact = facts.get(row["drawdown_reference"]) or {"found": False}
		if not fact.get("found"):
			found.append((UNMAPPED, f"Planning has no record of drawdown {row['drawdown_reference']}."))
			continue
		if fact["state"] == "Reversed":
			states.append("reversed")
			if fact["reversal_reason"] == "TenderCancelled":
				found.append((AMBIGUOUS, "The drawdown was already restored by a recovery this site does not hold."))
			else:
				found.append((OTHER_REASON, f"The Planning drawdown {row['drawdown_reference']} was reversed for another reason."))
			continue
		states.append("active")
		if fact["held"]:
			found.append((AMBIGUOUS, f"The drawdown {row['drawdown_reference']} is already held by another recovery."))
		if float(fact["quantity"] or 0) != float(row["quantity"] or 0) or float(fact["amount"] or 0) != float(row["value"] or 0):
			found.append((UNMAPPED, f"Planning's drawdown {row['drawdown_reference']} differs from the Requisition's record."))
	if "reversed" in states and "active" in states:
		found.append((PARTIAL, "Some of the originating drawdowns were reversed and others were not."))

	try:
		basis = funding_gateway.get_cancellation_release_basis(cancellation_id=cstr(cancellation), requisition_reference=root.requisition_reference, releases=cancellation_recovery._budget_releases(rows))
	except OwnerRefusal as refusal:
		found.append((UNMAPPED, refusal.reason))
	else:
		for reservation in basis.get("reservations", []):
			if reservation["verdict"] in ("ok", "reused"):
				continue
			cause = cstr((reservation.get("detail") or {}).get("cause"))
			low = cause.lower()
			if "converted" in low or "commitment" in low:
				found.append((OBLIGATION, "Budget — " + cause))
			elif "another reason" in low:
				found.append((OTHER_REASON, "Budget — " + cause))
			elif "part of the reservation" in low or "history shows" in low:
				found.append((PARTIAL, "Budget — " + cause))
			else:
				found.append((UNMAPPED, "Budget — " + (cause or "the reservation cannot be released")))

	for klass in (OBLIGATION, PARTIAL, OTHER_REASON, UNMAPPED, AMBIGUOUS):
		hit = [reason for k, reason in found if k == klass]
		if hit:
			return _result(klass, hit[0])
	return _result(ELIGIBLE, "", requisition=root.name, sources=len(rows))
