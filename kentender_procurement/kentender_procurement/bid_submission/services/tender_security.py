# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The bid's tender security as BDS-CHG-001 v0.8 §4.8 describes it, derived
from the Company task's published security answers (template release 1.2:
form, issuer, reference, instrument amount equal to the published amount,
valid-until date for the chosen form, proof) and the private intake match.

Whether a physical original is required is **the Tender's own statement**
(published facts `submission_method` and `original_delivery`; Project Owner,
10 October 2026): requiring tender security does not by itself require an original
(source ITT 18.1 reads "in original form", which the Tender now states explicitly).
A Tender published before it stated them says nothing here and no original is
assumed. While a required original is not recorded for the supplier's own
instrument, the bid carries a Review note,
never a Must fix (§8 `BDS_SECURITY_ORIGINAL_OUTSTANDING`: "This warns but does
not falsely block electronic receipt")."""

from __future__ import annotations

from typing import Any

from frappe.utils import cstr

from kentender_procurement.bid_submission.services import labels, security_matching, tenders_gateway
from kentender_procurement.bid_submission.services.errors import MESSAGES

# Project Owner, 10 October 2026: the supplier is told its actual security status, never the old "unmatched" wording (which suggested something was wrong).
ORIGINAL_RECEIVED = "Original received"
ORIGINAL_NOT_RECORDED = "Original receipt not yet recorded"
ORIGINAL_NOT_REQUIRED = "No original required"
ORIGINAL_NOT_STATED = "Original delivery not stated"
CHECKED_AFTER_OPENING = "Security will be checked against your bid after opening."
ISSUER_PENDING = "Issuer verification pending"
NOT_RECORDED = ORIGINAL_NOT_RECORDED  # the one status a required original has before anything is recorded

# Project Owner, 10 October 2026: the Tender's method names who supplies the instrument and what evidence the bidder gives
UPLOAD = "Bidder uploads an electronic instrument"
ISSUER = "Issuer supplies the instrument directly"
PAPER = "Paper instrument requiring an original"
METHODS = (UPLOAD, ISSUER, PAPER)
_HOW = {
	UPLOAD: "Upload your tender security, the electronic instrument, here.",
	ISSUER: "Your issuer supplies your tender security directly to the procuring entity. Enter the instrument's details here; you do not upload it.",
	PAPER: "Upload the prescribed electronic copy of your paper tender security here.",
}
_ORIGINAL = {"Required": "An original must be delivered before the submission deadline.", "Not required": "No original is required."}
PAPER_ORIGINAL = "The original must be delivered before the submission deadline."


def requirement_text(method: str, original: str) -> str:
	"""What the Tender states about submitting its security and delivering an original, in the Tender's own terms;
	"" when the Tender states neither (one published before it had to)."""
	if method not in _HOW or original not in _ORIGINAL:
		return ""
	return f"{_HOW[method]} {PAPER_ORIGINAL if method == PAPER else _ORIGINAL[original]}"


def requirement(facts: dict[str, Any]) -> dict[str, Any]:
	"""The Tender's own statement, read from its published facts. A Tender that states nothing is `stated: False`:
	no physical original is assumed for it and none is invented (Project Owner, 10 October 2026)."""
	method, original = cstr(facts.get("submission_method")), cstr(facts.get("original_delivery"))
	stated = method in METHODS and original in _ORIGINAL
	return {
		"stated": stated, "method": method if stated else "", "original_delivery": original if stated else "", "text": requirement_text(method, original),
		# the issuer's answer to a verification request exists for an uploaded or an issuer-supplied instrument, not for a paper one
		"electronic_permitted": (not stated) or method in (UPLOAD, ISSUER),
		"original_required": stated and (original == "Required" or method == PAPER),
		"issuer_supplied": stated and method == ISSUER,
	}


def statements(facts: dict[str, Any], tender: str) -> dict[str, Any]:
	"""The published facts, with the auditable correction standing in only where the published definition states neither
	(a Tender published before it stated them)."""
	if cstr(facts.get("submission_method")) or cstr(facts.get("original_delivery")):
		return facts
	fix = tenders_gateway.security_statement_correction(tender)
	return {**facts, **fix} if fix else facts


def _group(ctx):
	return next((g for g in ctx.model.groups_of("company") if g.rule_id in security_matching.SECURITY_RULES), None)


def response(ctx) -> dict[str, Any]:
	group = _group(ctx)
	if not group:
		return {"required": False}
	values = {f.field_key: ctx.value(f) for f in group.fields}
	facts = group.published_facts
	form = cstr(values.get("security_form"))
	valid_until = values.get("bank_guarantee_valid_until") if form == "Demand Bank Guarantee" else values.get("insurance_guarantee_valid_until") if form == "Insurance Guarantee" else None
	rule = requirement(statements(facts, ctx.workspace.tender))
	receipt = security_matching.receipt_for(ctx.workspace.name) if rule["original_required"] else None
	status = ORIGINAL_RECEIVED if receipt else ORIGINAL_NOT_RECORDED if rule["original_required"] else ORIGINAL_NOT_REQUIRED if rule["stated"] else ORIGINAL_NOT_STATED
	return {
		"required": True, "security_type": form, "issuer": cstr(values.get("issuer")), "reference": cstr(values.get("guarantee_reference")),
		"amount": cstr(values.get("instrument_amount")), "required_amount": labels.money_label(facts.get("amount"), cstr(facts.get("currency"))),
		"currency": cstr(facts.get("currency")), "valid_until": cstr(valid_until or ""), "proof": list(values.get("security_evidence") or []),
		# the issuer-supplied group has no instrument attachment: nothing to upload, so none is required (no duplicate upload)
		"proof_expected": any(f.field_key == "security_evidence" for f in group.fields), "issuer_supplied": rule["issuer_supplied"],
		"submission_method": rule["method"], "original_delivery": rule["original_delivery"], "requirement_stated": rule["stated"], "requirement_text": rule["text"],
		"electronic_permitted": rule["electronic_permitted"], "physical_original_required": rule["original_required"], "physical_receipt_status": status,
		"physical_receipt_reference": cstr(receipt.intake_reference) if receipt else "", "physical_received_at": labels.datetime_label(receipt.received_at) if receipt else "",
		"security_form_handle": next((f.handle for f in group.fields if f.field_key == "security_form"), ""),
	}


def review_note(ctx) -> dict[str, str] | None:
	"""A required original not yet recorded is a Review note, never a Must fix; nothing is said when the Tender
	requires no original or does not say."""
	security = response(ctx)
	if security.get("required") and security["physical_receipt_status"] == ORIGINAL_NOT_RECORDED:
		return {"task": "company", "handle": security["security_form_handle"], "label": "Tender security", "text": MESSAGES["BDS_SECURITY_ORIGINAL_OUTSTANDING"]}
	return None
