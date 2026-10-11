# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The electronic tender-security journey (Project Owner, 10 October 2026).

Four facts, never one:

1. **Submission** — the supplier explicitly submits the instrument's details and
   proof (`SubmitTenderSecurity`). Filling the form or uploading a file is not
   a submission and never means "verified".
2. **Physical original** — where the Tender requires one; recorded by the intake
   officer and matched to the bid only after the opening (`security_matching`).
3. **Issuer verification** — the issuer's answer to a verification request:
   Confirmed, Mismatch, or Pending. An unavailable issuer service, or none
   configured, leaves it Pending; nothing is Confirmed without the issuer's
   own answer. The source and the response time travel with the result.
4. **Compliance with the published requirement** — the instrument's form,
   amount and validity against what the Tender published. It is a fact about
   the answers, not an approval of the bid.

Nothing here blocks submitting the bid; an outstanding physical original stays
a Review note (BDS-CHG-001 §8 `BDS_SECURITY_ORIGINAL_OUTSTANDING`)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe.utils import cstr, flt, get_datetime

from kentender_procurement.bid_submission.services import bid_authorization as authz
from kentender_procurement.bid_submission.services import bid_context, clock, gateways, labels, records, save, tender_security
from kentender_procurement.bid_submission.services.errors import fail, field_errors

VERIFICATION = "Tender Security Verification"
PENDING, CONFIRMED, MISMATCH = "Pending", "Confirmed", "Mismatch"
UNAVAILABLE = "Unavailable"
NO_SERVICE = "No issuer verification service is configured"
EXPIRY_KEYS = {"Demand Bank Guarantee": "bank_guarantee_expiry_date", "Insurance Guarantee": "insurance_guarantee_expiry_date"}

# Project Owner, 10 October 2026: what the supplier reads for the issuer's side of its own security
LABELS = {CONFIRMED: "Issuer verification confirmed", MISMATCH: "Issuer verification does not match", PENDING: tender_security.ISSUER_PENDING, "None": "Issuer verification not requested"}

TEXT = {
	CONFIRMED: "The issuer confirmed this instrument.",
	MISMATCH: "The issuer's record does not match the details you submitted. Check the issuer, reference and amount, correct them and submit again.",
	PENDING: "Waiting for the issuer to confirm this instrument.",
	UNAVAILABLE: "The issuer could not be reached. Verification stays pending; check again later.",
	"None": "Not requested. Submit your tender security to ask the issuer to confirm it.",
}


# -- the instrument as the supplier answered it ----------------------------------


def _facts(ctx) -> dict[str, Any]:
	return tender_security.response(ctx)


def missing(facts: dict[str, Any]) -> dict[str, str]:
	"""What the supplier still has to give before submitting, by field."""
	out: dict[str, str] = {}
	for key, label in (("security_type", "Choose the form of tender security."), ("issuer", "Enter the issuing bank or insurer."), ("reference", "Enter the instrument's reference."),
			("amount", "Enter the amount on the instrument."), ("valid_until", "Enter the date the instrument is valid until.")):
		if not cstr(facts.get(key)).strip():
			out[key] = label
	if facts.get("proof_expected", True) and not facts.get("proof"):
		out["proof"] = "Add the instrument's proof."
	return out


def digest(facts: dict[str, Any]) -> str:
	body = {k: cstr(facts.get(k)).strip().upper() for k in ("security_type", "issuer", "reference", "amount", "currency", "valid_until")}
	body["proof"] = sorted(cstr(i) for i in facts.get("proof") or [])
	return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def compliance(ctx, facts: dict[str, Any]) -> dict[str, str]:
	"""The instrument's form, amount and validity against the published requirement."""
	if missing(facts):
		return {"state": "Not yet assessed", "text": "Complete the tender-security details to compare them with the published requirement."}
	group = tender_security._group(ctx)
	published = dict(getattr(group, "published_facts", None) or {})
	problems = []
	forms = published.get("permitted_forms") or []
	if forms and facts["security_type"] not in forms:
		problems.append("the form is not one the Tender permits")
	try:
		if flt(facts["amount"]) != flt(published.get("amount")):
			problems.append("the amount differs from the published amount")
	except (TypeError, ValueError):
		problems.append("the amount cannot be read")
	expiry = published.get(EXPIRY_KEYS.get(facts["security_type"], ""))
	if expiry and facts.get("valid_until"):
		try:
			if get_datetime(facts["valid_until"]).date() < get_datetime(expiry).date():
				problems.append("it expires before the published date")
		except Exception:
			problems.append("the validity date cannot be read")
	if problems:
		return {"state": "Does not meet", "text": "Does not meet the published requirement: " + "; ".join(problems) + "."}
	return {"state": "Meets", "text": "The form, amount and validity match the published requirement. This is a comparison of your answers, not an approval of your bid."}


# -- the record -----------------------------------------------------------------


def row_for(workspace: str):
	name = frappe.db.get_value(VERIFICATION, {"bid_workspace": workspace}, "name")
	return frappe.get_doc(VERIFICATION, name) if name else None


def _ask_issuer(facts: dict[str, Any], correlation_id: str) -> dict[str, Any]:
	service = gateways.issuer()
	if service is None:
		return {"outcome": UNAVAILABLE, "source": NO_SERVICE, "response_ms": None, "correlation_id": correlation_id}
	try:
		answer = service.verify(issuer=facts["issuer"], reference=facts["reference"], amount=facts["amount"], currency=facts["currency"], correlation_id=correlation_id)
	except Exception:
		return {"outcome": UNAVAILABLE, "source": cstr(getattr(service, "name", "")) or NO_SERVICE, "response_ms": None, "correlation_id": correlation_id}
	outcome = answer.get("outcome")
	if outcome not in (CONFIRMED, PENDING, MISMATCH, UNAVAILABLE):
		outcome = UNAVAILABLE  # an answer that is not one of the four confirms nothing
	return {**answer, "outcome": outcome}


def _apply(row, answer: dict[str, Any], *, at) -> None:
	outcome = answer["outcome"]
	row.last_outcome = outcome
	row.status = CONFIRMED if outcome == CONFIRMED else MISMATCH if outcome == MISMATCH else PENDING  # unavailable leaves it pending
	row.source = cstr(answer.get("source"))
	row.requested_at = at
	row.responded_at = None if outcome == UNAVAILABLE else at
	row.response_ms = answer.get("response_ms")
	row.correlation_id = cstr(answer.get("correlation_id"))
	row.attempts = int(row.attempts or 0) + 1


# -- commands -------------------------------------------------------------------


def submit_tender_security(*, bid_reference: str, expected_record_version, organisation: str = "", idempotency_key: str = "", user: str | None = None) -> dict[str, Any]:
	"""`SubmitTenderSecurity`: the supplier explicitly submits the instrument and asks
	its issuer to confirm it. Submitting again after a change replaces the submission;
	submitting the same instrument again asks the issuer again."""
	return _command("SubmitTenderSecurity", bid_reference, expected_record_version, organisation, idempotency_key, user, resubmit=True)


def check_tender_security_verification(*, bid_reference: str, expected_record_version, organisation: str = "", idempotency_key: str = "", user: str | None = None) -> dict[str, Any]:
	"""Ask the issuer again about the instrument already submitted."""
	return _command("CheckTenderSecurityVerification", bid_reference, expected_record_version, organisation, idempotency_key, user, resubmit=False)


def _command(command: str, bid_reference, expected_record_version, organisation, idempotency_key, user, *, resubmit: bool) -> dict[str, Any]:
	actor = authz.require_person(cstr(user or frappe.session.user))
	payload = {"bid_reference": cstr(bid_reference).strip(), "expected_record_version": expected_record_version, "organisation": cstr(organisation).strip()}
	return records.idempotent(idempotency_key, command, payload, lambda: _run(actor=actor, resubmit=resubmit, **payload), actor=actor, organisation=payload["organisation"])


def _run(*, actor: str, resubmit: bool, bid_reference: str, expected_record_version, organisation: str) -> dict[str, Any]:
	at = clock.now()
	ctx = bid_context.load(bid_reference, actor=actor, organisation=organisation, at=at)
	authz.active_account(ctx.workspace.lead_organisation)
	save.require_open(ctx)
	records.check_version(ctx.workspace, expected_record_version)
	facts = _facts(ctx)
	if not facts.get("required"):
		fail("BDS_UNKNOWN_RESPONSE")
	if not facts.get("electronic_permitted"):
		fail("BDS_UNKNOWN_RESPONSE", "This Tender does not accept tender security submitted electronically. Deliver the original as the Tender states.")  # it takes the original only
	problems = missing(facts)
	if problems:
		return field_errors(problems, code="BDS_FIELD_INVALID")
	row = row_for(ctx.workspace.name)
	current = digest(facts)
	if row is None or (resubmit and row.instrument_digest != current):
		with records.atomic("submit-tender-security"):
			if row is None:
				row = frappe.get_doc({"doctype": VERIFICATION, "bid_workspace": ctx.workspace.name, "tender": ctx.workspace.tender, "instrument_digest": current,
					"submitted_by": actor, "submitted_at": at, "status": PENDING, "attempts": 0})
				row.flags.kt_bid_command = True
				row = records.insert(row)
			else:
				row.instrument_digest, row.submitted_by, row.submitted_at = current, actor, at
	elif not resubmit and row.instrument_digest != current:
		return {"ok": False, "code": "BDS_FIELD_INVALID", "message": "You changed the instrument after submitting it. Submit it again."}
	answer = _ask_issuer(facts, correlation_id=f"TSV-{ctx.workspace.name}-{int(row.attempts or 0) + 1}")
	with records.atomic("verify-tender-security"):
		_apply(row, answer, at=at)
		records.save(row)
		records.emit("TenderSecurityVerificationRequested", tender=ctx.workspace.tender, workspace=ctx.workspace.name, actor=actor, at=at,
			payload={"verification": row.name, "outcome": answer["outcome"], "source": row.source, "response_ms": answer.get("response_ms")})
	return {"ok": True, **_describe(ctx, facts, row), "record_version": int(ctx.workspace.record_version or 0)}


# -- what the supplier sees -------------------------------------------------------


def _describe(ctx, facts: dict[str, Any], row) -> dict[str, Any]:
	comp = compliance(ctx, facts)
	if row is None:
		return {
			"submission": {"state": "Not submitted", "text": "You have not submitted your tender security yet.", "can_submit": not missing(facts)},
			"verification": {"state": "Not requested", "label": LABELS["None"], "text": TEXT["None"], "source": "", "responded_at": "", "response_ms": None},
			"compliance": comp,
		}
	changed = row.instrument_digest != digest(facts)
	state = "Changed since submitted" if changed else "Submitted"
	outcome = cstr(row.last_outcome)
	text = TEXT.get(UNAVAILABLE if outcome == UNAVAILABLE else row.status, "")
	if changed:
		text = "You changed the instrument after submitting it. Submit it again to ask the issuer to confirm it."
	verification = {
		"state": "Pending" if changed else row.status, "label": LABELS["Pending" if changed else row.status], "text": text, "last_response": outcome, "source": cstr(row.source),
		"responded_at": labels.datetime_seconds_label(row.responded_at) if row.responded_at else "", "response_ms": row.response_ms,
		"attempts": int(row.attempts or 0),
	}
	return {
		"submission": {"state": state, "text": f"Submitted {labels.datetime_label(row.submitted_at)}." if not changed else text, "submitted_at": labels.datetime_label(row.submitted_at), "can_submit": not missing(facts)},
		"verification": verification,
		"compliance": comp,
	}


def view(ctx) -> dict[str, Any] | None:
	"""The four statuses for the Company task, or None when the Tender requires no security."""
	facts = _facts(ctx)
	if not facts.get("required") or not facts.get("electronic_permitted"):
		return None  # no security, or a Tender that takes the original only: there is nothing to submit or verify electronically
	return _describe(ctx, facts, row_for(ctx.workspace.name))
