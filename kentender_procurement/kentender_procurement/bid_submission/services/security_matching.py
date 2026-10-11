# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The private match between a tender-security intake and a bid (owner
decision OD-H, 26 Sep 2026; replaces BDS-CHG-001 v0.8 §10.16's supplier list,
FU-V08-01). **Since 10 October 2026 the stored match is made only after the opening
access boundary has been crossed** (the Tender's opening has started): before then no
intake is linked to any bid in any record, so intake staff, and every record they could
reach, carry no trace of which bid presented which security. The supplier's own read
(`receipt_for`) is worked out in memory and stores nothing. The boundary is asked of
Bid Opening through `kt_opening_boundary_probes`; this module never imports it.

A match needs the same Tender, the same instrument reference and issuer
(ignoring case and spacing) and the same amount. After the boundary it is
recalculated for the whole Tender whenever a bid's receipt is read. Exactly one bid with exactly one intake is a match; anything else
is no match, and an intake that fits more than one bid is flagged for
opening. Matches are stored in a record no role can read; only the matched
supplier's own bid shows "recorded", and the person who recorded the intake
sees nothing about bids either way."""

from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_submission.services import clock, records, tenders_gateway

INTAKE = "Tender Security Intake"
MATCH = "Tender Security Intake Match"
SECURITY_RULE = "RR-TENDER-SECURITY"
# release 1.5: the group for an issuer-supplied instrument is its own rule (no attachment); every consumer reads either
SECURITY_RULES = (SECURITY_RULE, "RR-TENDER-SECURITY-ISSUER")
ACTIVE_BIDS = ("Draft", "Needs attention", "Ready to submit", "Submitted")
BOUNDARY_HOOK = "kt_opening_boundary_probes"


def opening_crossed(tender: str) -> bool:
	"""True once the Tender's opening has started (the access boundary is
	crossed). Nothing before then may link an intake to a bid."""
	from kentender_procurement.bid_submission.services import simulation

	if simulation.enabled() and simulation.controls().get("opening_boundary_crossed"):
		return True  # a browser world's seam; no effect outside a test environment
	return any(bool(frappe.get_attr(path)(tender)) for path in frappe.get_hooks(BOUNDARY_HOOK) or [])


def _norm(text) -> str:
	return re.sub(r"\s+", "", cstr(text)).upper()


def _amount(value) -> Decimal | None:
	try:
		return Decimal(cstr(value)).quantize(Decimal("0.01")) if cstr(value).strip() else None
	except InvalidOperation:
		return None


def intake_key(row) -> tuple:
	return (_norm(row.instrument_reference), _norm(row.issuer), _amount(row.amount))


def _security_fields(definition: dict[str, Any]) -> dict[str, str]:
	"""field key → response identity of the bound definition's security group."""
	rows = {r["response_id"]: r for r in definition.get("response_rows") or []}
	for section in definition.get("sections") or []:
		for group in section.get("groups") or []:
			if group.get("rule_id") in SECURITY_RULES:
				return {rows[r]["field"]["field_key"]: r for r in group.get("response_ids") or []}
	return {}


def bid_keys(tender: str) -> dict[str, tuple]:
	"""Each active bid's (reference, issuer, amount) from its current answers."""
	out: dict[str, tuple] = {}
	definitions: dict[int, dict[str, str]] = {}
	for ws in frappe.get_all("Bid Workspace", filters={"tender": tender, "status": ("in", ACTIVE_BIDS)}, fields=["name", "definition_version"], limit_page_length=0):
		version = int(ws.definition_version or 0)
		if version not in definitions:
			bound = tenders_gateway.definition_for(tender, version)
			definitions[version] = _security_fields(bound["definition"]) if bound else {}
		fields = definitions[version]
		values = json.loads(frappe.db.get_value("Bid Section Response", {"bid_workspace": ws.name, "section_key": "company"}, "values_json") or "{}")
		reference, issuer, amount = values.get(fields.get("guarantee_reference", "")), values.get(fields.get("issuer", "")), values.get(fields.get("instrument_amount", ""))
		if reference and issuer and amount not in (None, ""):
			out[ws.name] = (_norm(reference), _norm(issuer), _amount(amount))
	return out


def active_intakes(tender: str) -> list[Any]:
	rows = frappe.get_all(INTAKE, filters={"tender": tender}, fields=["name", "instrument_reference", "issuer", "amount", "corrects", "intake_kind"], order_by="recorded_at asc, creation asc", limit_page_length=0)
	# a correction may sit on another Tender (the reference was typed wrong)
	corrected = set(frappe.get_all(INTAKE, filters={"corrects": ("in", [r.name for r in rows] or [""])}, pluck="corrects"))
	return [r for r in rows if r.name not in corrected]


def match_tender(tender: str) -> None:
	"""Recalculate every match of `tender` (no commit; inside the caller's command).
	Does nothing before the opening boundary is crossed."""
	if not opening_crossed(tender):
		return
	intakes = active_intakes(tender)
	bids = bid_keys(tender)
	frappe.db.delete(MATCH, {"tender": tender})
	at = clock.now()
	for intake in intakes:
		key = intake_key(intake)
		if None in key:
			continue
		# a physical original and an issuer confirmation of the same instrument are two facts: each is matched on its own
		same_intakes = [i for i in intakes if intake_key(i) == key and i.intake_kind == intake.intake_kind]
		candidates = [ws for ws, bid_key in bids.items() if bid_key == key]
		if not candidates:
			continue
		matched = len(candidates) == 1 and len(same_intakes) == 1
		records.insert(frappe.get_doc({
			"doctype": MATCH, "tender": tender, "intake": intake.name, "bid_workspace": candidates[0] if matched else None,
			"status": "Matched" if matched else "Ambiguous", "matched_at": at,
		}))


def receipt_for(workspace: str, kind: str = "Physical original") -> dict[str, Any] | None:
	"""What this supplier's own bid can be told about its security, worked out when the
	supplier reads it and **stored nowhere** (Project Owner, 10 October 2026: before the
	opening the supplier sees its own actual status; nothing links an intake to a bid
	for anyone else). An intake counts only when exactly one active bid on the Tender
	carries this instrument (same reference, issuer and amount) and exactly one intake of
	this kind carries it, so a supplier learns nothing about an instrument that is not
	its own, and an ambiguous one is left for the opening. `None` means nothing is
	recorded for this bid; it never says why."""
	tender = frappe.db.get_value("Bid Workspace", workspace, "tender")
	if not tender:
		return None
	keys = bid_keys(tender)
	own = keys.get(workspace)
	if own is None or None in own or [ws for ws, key in keys.items() if key == own] != [workspace]:
		return None
	found = [i for i in active_intakes(tender) if intake_key(i) == own and (i.intake_kind or "Physical original") == kind]
	if len(found) != 1:
		return None
	row = frappe.db.get_value(INTAKE, found[0].name, ["intake_reference", "received_at", "deadline_class", "intake_kind", "issuer_confirmed_at"], as_dict=True)
	return row
