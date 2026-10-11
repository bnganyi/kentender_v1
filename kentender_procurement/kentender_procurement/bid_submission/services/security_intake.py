# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Blind tender-security intake (owner decisions OD-G/OD-H, 26 Sep 2026,
replacing BDS-CHG-001 v0.8 §10.16 BDS-DES-15; FU-V08-01; reassigned by the
Project Owner on 10 October 2026).

A person assigned the Tender Security Intake Officer duty **for that Tender**
(`security_duty`) records a physical original, or an electronic issuer
confirmation, against a published Tender reference and the instrument's own
details: type, issuer, instrument reference, amount and currency, and when it
was received (never in the future). A physical original's time is when it
arrived; an issuer confirmation also carries the time the issuer states it
confirmed, kept apart from when it was received and when it was recorded. The
system issues an opaque intake reference (random, not a per-bid sequence) and
classes the receipt as before or after the deadline by trusted time. The
response is the same whatever any bid contains, and whether any bid exists:
this module never looks up, shows or confirms a bid, its status, its price or a
count, and never matches an intake to a bid. Matching waits until the opening
access boundary has been crossed (`security_matching`). Intakes are
append-only. Recording or viewing intake records is logged as exposure.

A mistake is corrected by a new intake that names the one it corrects and
gives a reason (owner decision 27 Sep 2026); the first stays in the record,
marked Corrected, and no longer counts for the match. A receipt is corrected
once; a later mistake corrects the correction."""

from __future__ import annotations

import secrets
from decimal import Decimal, InvalidOperation
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_core.services.authorization import PURPOSE_COMMAND, PURPOSE_READ, authorise_record

from kentender_procurement.bid_submission.services import clock, labels, records, security_duty, security_matching, tender_security, tenders_gateway
from kentender_procurement.bid_submission.services.errors import field_errors

INTAKE = "Tender Security Intake"
PHYSICAL, ISSUER = "Physical original", "Issuer confirmation"
KINDS = (PHYSICAL, ISSUER)
CONFIRMATION = "I confirm that the instrument identified above was received at the date and time recorded."
DENIED = security_duty.DENIED


def require_recorder(user: str, tender_reference: str) -> None:
	"""The duty is Tender-scoped: holding it for another Tender, or none, is the
	same refusal, so the answer never says whether the Tender exists."""
	security_duty.require_officer(user, tender_reference)


def _published_security(reference: str) -> tuple[Any, dict[str, Any] | None]:
	"""The published Tender and its security facts (public facts only)."""
	root = tenders_gateway.tender_root(reference)
	if not root:
		return None, None
	current = tenders_gateway.current_definition(root.name)
	for section in (current or {}).get("definition", {}).get("sections") or []:
		for group in section.get("groups") or []:
			if group.get("rule_id") in security_matching.SECURITY_RULES:
				return root, group.get("published_facts") or {}
	return root, None


def record_physical_tender_security_receipt(
	*, tender_reference: str, instrument_type: str, issuer: str, instrument_reference: str, amount, currency: str, received_at, notes: str = "",
	confirmed=False, idempotency_key: str = "", corrects: str = "", correction_reason: str = "", user: str | None = None,
	intake_kind: str = PHYSICAL, issuer_confirmed_at="",
) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
	require_recorder(actor, cstr(tender_reference))
	payload = {
		"intake_kind": cstr(intake_kind).strip() or PHYSICAL, "issuer_confirmed_at": cstr(issuer_confirmed_at).strip(),
		"tender_reference": cstr(tender_reference).strip(), "instrument_type": cstr(instrument_type).strip(), "issuer": cstr(issuer).strip(),
		"instrument_reference": cstr(instrument_reference).strip(), "amount": cstr(amount).strip(), "currency": cstr(currency).strip().upper(),
		"received_at": cstr(received_at).strip(), "notes": cstr(notes).strip(), "confirmed": bool(confirmed) and cstr(confirmed).lower() not in ("0", "false"),
		"corrects": cstr(corrects).strip(), "correction_reason": cstr(correction_reason).strip(),
	}
	return records.idempotent(idempotency_key, "RecordPhysicalTenderSecurityReceipt", payload, lambda: _record(actor=actor, **payload), actor=actor)


def _record(*, actor: str, tender_reference: str, instrument_type: str, issuer: str, instrument_reference: str, amount: str, currency: str, received_at: str, notes: str, confirmed: bool, corrects: str = "", correction_reason: str = "", intake_kind: str = PHYSICAL, issuer_confirmed_at: str = "") -> dict[str, Any]:
	at = clock.now()
	problems: dict[str, str] = {}
	if intake_kind not in KINDS:
		problems["intake_kind"] = "Choose what was received: " + " or ".join(KINDS).lower() + "."
	corrected = None
	if corrects:
		corrected = frappe.db.get_value(INTAKE, {"intake_reference": corrects}, ["name", "tender", "tender_reference"], as_dict=True)
		if corrected and not security_duty.holds_duty(actor, corrected.tender_reference):
			corrected = None  # an intake of a Tender this person has no duty for is not found
			later = None
		later = frappe.db.get_value(INTAKE, {"corrects": corrected.name}, "intake_reference") if corrected else None
		if not corrected:
			problems["corrects"] = "No tender-security receipt has this reference."
		elif later:
			problems["corrects"] = f"This receipt was already corrected by {later}. Correct that one instead."
		if not (10 <= len(correction_reason) <= 500):
			problems["correction_reason"] = "Enter the reason for the correction (10–500 characters)."
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
	confirmed_at = None
	if intake_kind == ISSUER:
		try:
			confirmed_at = get_datetime(issuer_confirmed_at) if issuer_confirmed_at else None
		except Exception:
			confirmed_at = None
		if not confirmed_at:
			problems["issuer_confirmed_at"] = "Enter the date and time the issuer confirmed the instrument."
		elif confirmed_at > at:
			problems["issuer_confirmed_at"] = "The issuer's confirmation time cannot be in the future."
		elif received and confirmed_at > received:
			problems["issuer_confirmed_at"] = "The issuer cannot have confirmed after you received the confirmation."
	elif issuer_confirmed_at:
		problems["issuer_confirmed_at"] = "Only an issuer confirmation has an issuer confirmation time."
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
			"intake_kind": intake_kind, "issuer_confirmed_at": confirmed_at, "instrument_type": instrument_type, "issuer": issuer, "instrument_reference": instrument_reference, "amount": str(value.quantize(Decimal("0.01"))),
			"currency": currency, "received_at": received, "deadline_class": "Before deadline" if received < deadline else "After deadline", "notes": notes,
			"recorded_by": actor, "recorded_at": at, "corrects": corrected.name if corrected else None, "correction_reason": correction_reason if corrected else "",
		}))
		# no match to a bid here: matching waits until the opening boundary is crossed
		security_duty.record_exposure(root.name, root.tender_reference, actor, security_duty.RECORDED, doc.intake_reference)
		records.emit("TenderSecurityIntakeRecorded", tender=root.name, actor=actor, at=at, payload={"intake": doc.name})
	return {"ok": True, **_row(doc)}


def _row(doc) -> dict[str, Any]:
	later = frappe.db.get_value(INTAKE, {"corrects": doc.name}, "intake_reference")
	earlier = frappe.db.get_value(INTAKE, doc.corrects, "intake_reference") if doc.corrects else ""
	received = get_datetime(doc.received_at)
	return {
		"intake_kind": doc.intake_kind or PHYSICAL, "issuer_confirmed_at": labels.datetime_label(doc.issuer_confirmed_at) if doc.issuer_confirmed_at else "",
		"issuer_confirmed_at_value": get_datetime(doc.issuer_confirmed_at).strftime("%Y-%m-%dT%H:%M") if doc.issuer_confirmed_at else "",
		"status": "Corrected" if later else "Current", "corrected_by": cstr(later), "corrects": cstr(earlier), "correction_reason": cstr(doc.correction_reason),
		"amount_value": str(doc.amount), "currency": doc.currency, "received_at_value": received.strftime("%Y-%m-%dT%H:%M"),
		"intake_reference": doc.intake_reference, "tender_reference": doc.tender_reference, "instrument_type": doc.instrument_type, "issuer": doc.issuer,
		"instrument_reference": doc.instrument_reference, "amount": labels.money_label(doc.amount, doc.currency), "received_at": labels.datetime_label(doc.received_at),
		"deadline_class": doc.deadline_class, "recorded_at": labels.datetime_label(doc.recorded_at), "notes": cstr(doc.notes),
	}


def list_my_intakes(*, tender_reference: str = "", user: str | None = None) -> dict[str, Any]:
	"""The intakes of the Tenders this person is assigned the duty for now (or of
	one of them), newest first; nothing about bids. Viewing them is logged as
	exposure, once per Tender per call."""
	actor = cstr(user or frappe.session.user)
	reference = cstr(tender_reference).strip()
	tenders = security_duty.officer_tenders(actor)
	if not tenders:
		raise frappe.PermissionError(DENIED)
	if reference:
		# a filter by a Tender the officer is not assigned matches nothing, as a Tender that does not exist would
		tenders = [reference] if reference in tenders else []
	names = frappe.get_all(INTAKE, filters={"tender_reference": ("in", tenders)}, pluck="name", order_by="recorded_at desc, creation desc", limit_page_length=0)
	rows = [_row(frappe.get_doc(INTAKE, name)) for name in names]
	if rows:
		with records.atomic("view-security-intakes"):
			for root_reference in sorted({r["tender_reference"] for r in rows}):
				root = security_duty.published_tender(root_reference)
				if root:
					security_duty.record_exposure(root.name, root.tender_reference, actor, security_duty.VIEWED)
	return {"rows": rows, "tenders": _assigned_tenders(tenders), "empty_text": "No tender-security receipts have been recorded for your Tenders yet.", "confirmation": CONFIRMATION, "kinds": list(KINDS)}


def _assigned_tenders(references: list[str]) -> list[dict[str, str]]:
	out = []
	for reference in references:
		root = security_duty.published_tender(reference)
		if root:
			out.append({"tender_reference": root.tender_reference, "title": cstr(frappe.db.get_value("Tender", root.name, "requirement_title") or ""), "deadline": labels.datetime_label(root.submission_deadline)})
	return out


def my_tenders(*, user: str | None = None) -> dict[str, Any]:
	"""The Tenders this person is assigned the duty for, for the page's picker;
	public Tender facts only, no exposure."""
	actor = cstr(user or frappe.session.user)
	tenders = security_duty.officer_tenders(actor)
	if not tenders:
		raise frappe.PermissionError(DENIED)
	return {"tenders": _assigned_tenders(tenders)}


def tender_security_requirement(*, tender_reference: str, user: str | None = None) -> dict[str, Any]:
	"""The published Tender's security requirement (public Tender facts) to
	help the recorder fill the intake; nothing about bids."""
	require_recorder(cstr(user or frappe.session.user), cstr(tender_reference))
	root, facts = _published_security(cstr(tender_reference).strip())
	if not root:
		return {"found": False, "text": "No published Tender has this reference."}
	if facts is None:
		return {"found": True, "required": False, "text": "This Tender does not require a tender security."}
	stated = tender_security.statements(facts, root.name)
	return {
		"found": True, "required": True, "tender_reference": root.tender_reference, "permitted_forms": list(facts.get("permitted_forms") or []),
		"currency": cstr(facts.get("currency")), "required_amount": labels.money_label(facts.get("amount"), cstr(facts.get("currency"))),
		"deadline": labels.datetime_label(root.submission_deadline),
		# what the Tender itself states about submitting its security and delivering an original ("" when it states neither)
		"requirement": tender_security.requirement_text(cstr(stated.get("submission_method")), cstr(stated.get("original_delivery"))),
	}
