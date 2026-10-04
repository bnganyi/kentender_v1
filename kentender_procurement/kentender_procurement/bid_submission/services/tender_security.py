# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The bid's tender security as BDS-CHG-001 v0.8 §4.8 describes it, derived
from the Company task's published security answers (template release 1.2:
form, issuer, reference, instrument amount equal to the published amount,
valid-until date for the chosen form, proof) and the private intake match.

The physical original is required whenever the Tender requires a tender
security (source ITT 18.1: "in original form"). Until it is recorded as
received, the bid carries a Review note, never a Must fix (§8
`BDS_SECURITY_ORIGINAL_OUTSTANDING`: "This warns but does not falsely block
electronic receipt")."""

from __future__ import annotations

from typing import Any

from frappe.utils import cstr

from kentender_procurement.bid_submission.services import labels, security_matching
from kentender_procurement.bid_submission.services.errors import MESSAGES

NOT_RECORDED = "Not recorded"


def _group(ctx):
	return next((g for g in ctx.model.groups_of("company") if g.rule_id == security_matching.SECURITY_RULE), None)


def response(ctx) -> dict[str, Any]:
	group = _group(ctx)
	if not group:
		return {"required": False}
	values = {f.field_key: ctx.value(f) for f in group.fields}
	facts = group.published_facts
	form = cstr(values.get("security_form"))
	valid_until = values.get("bank_guarantee_valid_until") if form == "Demand Bank Guarantee" else values.get("insurance_guarantee_valid_until") if form == "Insurance Guarantee" else None
	receipt = security_matching.receipt_for(ctx.workspace.name)
	status = f"Recorded {receipt.deadline_class.lower()}" if receipt else NOT_RECORDED
	return {
		"required": True, "security_type": form, "issuer": cstr(values.get("issuer")), "reference": cstr(values.get("guarantee_reference")),
		"amount": cstr(values.get("instrument_amount")), "required_amount": labels.money_label(facts.get("amount"), cstr(facts.get("currency"))),
		"currency": cstr(facts.get("currency")), "valid_until": cstr(valid_until or ""), "proof": list(values.get("security_evidence") or []),
		"physical_original_required": True, "physical_receipt_status": status,
		"physical_receipt_reference": cstr(receipt.intake_reference) if receipt else "", "physical_received_at": labels.datetime_label(receipt.received_at) if receipt else "",
		"security_form_handle": next((f.handle for f in group.fields if f.field_key == "security_form"), ""),
	}


def review_note(ctx) -> dict[str, str] | None:
	security = response(ctx)
	if security.get("required") and security["physical_receipt_status"] == NOT_RECORDED:
		return {"task": "company", "handle": security["security_form_handle"], "label": "Tender security", "text": MESSAGES["BDS_SECURITY_ORIGINAL_OUTSTANDING"]}
	return None
