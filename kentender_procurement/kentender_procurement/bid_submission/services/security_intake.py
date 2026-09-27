# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Blind physical tender-security intake (owner decisions OD-G/OD-H, 26 Sep
2026, replacing BDS-CHG-001 v0.8 §10.16 BDS-DES-15; FU-V08-01).

The Head of Procurement Function (Charles Mutiso on the canonical site;
duty tag `tender_security_receipt`) records a physical original against a
published Tender reference and the instrument's own details: type, issuer,
instrument reference, amount and currency, and when it was received (never
in the future). The system issues an opaque intake reference (random, not a
per-bid sequence) and classes the receipt as before or after the deadline by
trusted time. The response is the same whatever any bid contains; the
recorder sees no candidate, bid, status or match. Intakes are append-only;
the private match runs inside the same command (`security_matching`)."""

from __future__ import annotations

import secrets
from decimal import Decimal, InvalidOperation
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_core.services.authorization import PURPOSE_COMMAND, PURPOSE_READ, authorise_record

from kentender_procurement.bid_submission.services import clock, labels, records, security_matching, tenders_gateway
from kentender_procurement.bid_submission.services.errors import field_errors

INTAKE = "Tender Security Intake"
RECORDER = "Head of Procurement Function"
CONFIRMATION = "I confirm that the physical original identified above was received at the date and time recorded."
DENIED = "Only the Head of Procurement Function records physical tender-security originals."


def require_recorder(user: str, *, purpose: str = PURPOSE_COMMAND) -> None:
	if not user or user == "Guest" or not authorise_record(user=user, business_role=RECORDER, organisation_unit="", purpose=purpose).allowed:
		raise frappe.PermissionError(DENIED)


def _published_security(reference: str) -> tuple[Any, dict[str, Any] | None]:
	"""The published Tender and its security facts (public facts only)."""
	root = tenders_gateway.tender_root(reference)
	if not root:
		return None, None
	current = tenders_gateway.current_definition(root.name)
	for section in (current or {}).get("definition", {}).get("sections") or []:
		for group in section.get("groups") or []:
			if group.get("rule_id") == security_matching.SECURITY_RULE:
				return root, group.get("published_facts") or {}
	return root, None


def record_physical_tender_security_receipt(
	*, tender_reference: str, instrument_type: str, issuer: str, instrument_reference: str, amount, currency: str, received_at, notes: str = "",
	confirmed=False, idempotency_key: str = "", user: str | None = None,
) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
	require_recorder(actor)
	payload = {
		"tender_reference": cstr(tender_reference).strip(), "instrument_type": cstr(instrument_type).strip(), "issuer": cstr(issuer).strip(),
		"instrument_reference": cstr(instrument_reference).strip(), "amount": cstr(amount).strip(), "currency": cstr(currency).strip().upper(),
		"received_at": cstr(received_at).strip(), "notes": cstr(notes).strip(), "confirmed": bool(confirmed) and cstr(confirmed).lower() not in ("0", "false"),
	}
	return records.idempotent(idempotency_key, "RecordPhysicalTenderSecurityReceipt", payload, lambda: _record(actor=actor, **payload), actor=actor)


def _record(*, actor: str, tender_reference: str, instrument_type: str, issuer: str, instrument_reference: str, amount: str, currency: str, received_at: str, notes: str, confirmed: bool) -> dict[str, Any]:
	at = clock.now()
	problems: dict[str, str] = {}
	root, facts = _published_security(tender_reference)
	if not root:
		problems["tender_reference"] = "No published Tender has this reference."
	elif facts is None:
		problems["tender_reference"] = "This Tender does not require a tender security."
	elif instrument_type not in (facts.get("permitted_forms") or []):
		problems["instrument_type"] = "Choose the instrument type: " + " or ".join(facts.get("permitted_forms") or []) + "."
	if not (2 <= len(issuer) <= 160):
		problems["issuer"] = "Enter the issuing bank or insurer."
	if not (2 <= len(instrument_reference) <= 80):
		problems["instrument_reference"] = "Enter the instrument's reference."
	try:
		value = Decimal(amount.replace(",", ""))
		if value <= 0 or value != value.quantize(Decimal("0.01")):
			raise InvalidOperation
	except InvalidOperation:
		problems["amount"] = "Enter the amount on the instrument, for example 500000.00."
	if len(currency) != 3 or not currency.isalpha():
		problems["currency"] = "Enter the three-letter currency code, for example KES."
	try:
		received = get_datetime(received_at) if received_at else None
	except Exception:
		received = None
	if not received:
		problems["received_at"] = "Enter the date and time the original was received."
	elif received > at:
		problems["received_at"] = "The time received cannot be in the future."
	if len(notes) > 500:
		problems["notes"] = "Keep notes to 500 characters or fewer."
	if not confirmed:
		problems["confirmed"] = "Confirm that the original was received as recorded."
	if problems:
		return field_errors(problems)
	deadline = get_datetime(root.submission_deadline)
	with records.atomic("record-security-intake"):
		doc = records.insert(frappe.get_doc({
			"doctype": INTAKE, "intake_reference": "TSI-" + secrets.token_hex(5).upper(), "tender": root.name, "tender_reference": root.tender_reference,
			"instrument_type": instrument_type, "issuer": issuer, "instrument_reference": instrument_reference, "amount": str(value.quantize(Decimal("0.01"))),
			"currency": currency, "received_at": received, "deadline_class": "Before deadline" if received < deadline else "After deadline", "notes": notes,
			"recorded_by": actor, "recorded_at": at,
		}))
		security_matching.match_tender(root.name)
		records.emit("TenderSecurityIntakeRecorded", tender=root.name, actor=actor, at=at, payload={"intake": doc.name})
	return {"ok": True, **_row(doc)}


def _row(doc) -> dict[str, Any]:
	return {
		"intake_reference": doc.intake_reference, "tender_reference": doc.tender_reference, "instrument_type": doc.instrument_type, "issuer": doc.issuer,
		"instrument_reference": doc.instrument_reference, "amount": labels.money_label(doc.amount, doc.currency), "received_at": labels.datetime_label(doc.received_at),
		"deadline_class": doc.deadline_class, "recorded_at": labels.datetime_label(doc.recorded_at), "notes": cstr(doc.notes),
	}


def list_my_intakes(*, tender_reference: str = "", user: str | None = None) -> dict[str, Any]:
	"""The recorder's own intakes, newest first; nothing about bids."""
	actor = cstr(user or frappe.session.user)
	require_recorder(actor, purpose=PURPOSE_READ)
	filters: dict[str, Any] = {"recorded_by": actor}
	if cstr(tender_reference).strip():
		filters["tender_reference"] = cstr(tender_reference).strip()
	rows = [_row(frappe.get_doc(INTAKE, name)) for name in frappe.get_all(INTAKE, filters=filters, pluck="name", order_by="recorded_at desc, creation desc", limit_page_length=0)]
	return {"rows": rows, "empty_text": "You have not recorded any tender-security originals yet.", "confirmation": CONFIRMATION}
