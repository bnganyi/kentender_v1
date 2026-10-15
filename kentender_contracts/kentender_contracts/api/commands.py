# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The generic command endpoint's table (CM-CHG-001 v0.8 section 7, plan Phase 4): which service function each command name runs and how a screen's form values become its arguments.

A screen never decides what a command means. It sends the command's name, the fixed arguments its board gave the button, the values the person typed, the revision it read and a stable
operation key; this module turns those into the service call. The service then makes every check itself (authority, rules, holds, revision), so nothing here is a gate. Select options
travel as `id|label` and arrive here as the id."""

from __future__ import annotations

from typing import Any, Callable

from kentender_contracts import award_receiver
from kentender_contracts.services import closeout, delivery, existing, formation, formation_end, outside_signature, payment, security
from kentender_contracts.services.errors import invalid

Handler = Callable[[str, dict[str, Any], dict[str, Any], int, str, str], dict[str, Any]]


def pick(value: Any) -> str:
	"""A select option's id (options travel as `id|label`)."""
	return str(value or "").split("|", 1)[0].strip()


def nested(values: dict[str, Any], prefix: str) -> dict[str, Any]:
	return {k[len(prefix) + 1:]: v for k, v in values.items() if k.startswith(prefix + ".")}


def _particulars(case, args, values, expected, key, actor):
	mapping = {line: pick(item) for line, item in nested(values, "item_mapping").items() if pick(item)}
	clean = {"agreement_date": values.get("agreement_date"), "entity_signatory": pick(values.get("entity_signatory")), "native_supplier": pick(values.get("native_supplier")),
		"asset_location": pick(values.get("asset_location")), "ag_clearance": str(values.get("ag_clearance") or "").strip(), "item_mapping": mapping}
	return formation.save_particulars(case, expected_version=expected, idempotency_key=key, actor=actor, values=clean)


def _recommend(case, args, values, expected, key, actor):
	invalid({k: "Choose a person." for k in ("chair", "member_technical", "member_other") if not pick(values.get(k))})
	members = [{"user": pick(values["chair"]), "capacity": "Chair", "role_label": values.get("chair_label", ""), "certifier": values.get("chair_label") == "Technical"},
		{"user": pick(values["member_technical"]), "capacity": "Member", "role_label": values.get("member_technical_label", ""), "certifier": True},
		{"user": pick(values["member_other"]), "capacity": "Member", "role_label": values.get("member_other_label", ""), "certifier": False}]
	return delivery.recommend_inspectors(case, expected_version=expected, idempotency_key=key, actor=actor, members=members, from_date=values.get("from_date", ""), until_date=values.get("until_date", ""),
		acceptance=values.get("acceptance") or "Committee accepts")


def _declare(case, args, values, expected, key, actor):
	chosen = values.get("declaration")
	invalid({"declaration": "" if str(chosen) in ("0", "1") else "Choose your declaration."})
	conflict = str(values.get("conflict", "")).strip() if str(chosen) == "1" else ""
	invalid({"conflict": "" if str(chosen) == "0" or conflict else "Describe the conflict."})
	return delivery.declare_interest(case, expected_version=expected, idempotency_key=key, actor=actor, conflict=conflict)


def _lines(text: Any) -> list[str]:
	return [u.strip() for u in str(text or "").splitlines() if u.strip()]


def _arrival(case, args, values, expected, key, actor):
	line = next(iter(nested(values, "quantity")), args.get("line_id") or "")
	items = [{"line_id": line, "quantity": values.get(f"quantity.{line}"), "units": _lines(values.get(f"units.{line}")), "replaces": _lines(values.get("replaces"))}] if line else []
	if str(values.get("unexpected_description", "")).strip():  # goods no line of the contract names are recorded as an exception
		items.append({"description": values["unexpected_description"], "quantity": values.get("unexpected_quantity"), "units": _lines(values.get("unexpected_units"))})
	return delivery.record_arrival(case, expected_version=expected, idempotency_key=key, actor=actor, received_at=values.get("received_at", ""), destination=values.get("destination", ""), items=items,
		supplier_reference=str(values.get("supplier_reference", "")).strip())


def _resolve_exception(case, args, values, expected, key, actor):
	return delivery.resolve_exception(case, arrival=args["arrival"], disposition=pick(values.get("disposition")), reason=values.get("reason", ""), expected_version=expected, idempotency_key=key, actor=actor)


def _observations(case, args, values, expected, key, actor):
	rows = []
	for name, value in values.items():
		if name.startswith("obs."):
			_p, unit, criterion = name.split(".", 2)
			rows.append({"unit": unit, "criterion_id": criterion, "value": "" if value == "Not recorded" else value})
	return delivery.record_inspection(case, arrival=args["arrival"], expected_version=expected, idempotency_key=key, actor=actor, observations=rows)


def _invoice(case, args, values, expected, key, actor):
	line = next(iter(nested(values, "quantity")), args.get("line_id") or "")
	return payment.submit_invoice(case, expected_version=expected, idempotency_key=key, actor=actor, claim_reference=values.get("claim_reference", args.get("claim_reference", "")),
		invoice_date=values.get("invoice_date", args.get("invoice_date", "")), lines=[{"line_id": line, "quantity": values.get(f"quantity.{line}")}] if line else [], successor_of=args.get("successor_of", ""), reason=values.get("reason", ""))


def _finance_save(case, args, values, expected, key, actor):
	if args.get("kind") == "invoice":
		return payment.save_accounting_invoice(case, invoice=args["invoice"], expected_version=expected, idempotency_key=key, actor=actor, posting_date=values.get("posting_date", ""),
			payable_account=values.get("payable_account", ""), cost_centre=values.get("cost_centre", ""), expense_account=values.get("expense_account", ""), tax_template=values.get("tax_template", ""))
	return payment.save_finance_draft(case, invoice=args["invoice"], expected_version=expected, idempotency_key=key, actor=actor, mode_of_payment=values.get("mode_of_payment", ""),
		paid_from=values.get("paid_from", ""), reference_no=values.get("reference_no", ""), amount=values.get("amount") or None)


def _finance_submit(case, args, values, expected, key, actor):
	if args.get("kind") == "invoice":
		return payment.submit_accounting_invoice(case, invoice=args["invoice"], expected_version=expected, idempotency_key=key, actor=actor)
	return payment.submit_finance_for_approval(case, payment=args["payment"], expected_version=expected, idempotency_key=key, actor=actor)


def _finance_approve(case, args, values, expected, key, actor):
	if args.get("kind") == "invoice":
		return payment.approve_accounting_invoice(case, invoice=args["invoice"], expected_version=expected, idempotency_key=key, actor=actor)
	return payment.approve_finance_record(case, payment=args["payment"], expected_version=expected, idempotency_key=key, actor=actor)


def _finance_return(case, args, values, expected, key, actor):
	if args.get("kind") == "invoice":
		return payment.return_accounting_invoice(case, invoice=args["invoice"], expected_version=expected, idempotency_key=key, actor=actor, reason=values.get("reason", ""))
	return payment.return_finance_for_correction(case, payment=args["payment"], expected_version=expected, idempotency_key=key, actor=actor, reason=values.get("reason", ""))


def _record_security(case, args, values, expected, key, actor):
	return security.record_security(case, expected_version=expected, idempotency_key=key, actor=actor, issuer=values.get("issuer", ""), beneficiary=values.get("beneficiary", ""), reference=values.get("reference", ""),
		amount=_number(values.get("amount")), issued_on=values.get("issued_on", ""), expires_on=values.get("expires_on", ""), attachment=values.get("attachment", ""))


def _number(value: Any) -> float:
	try:
		return float(str(value or "0").replace(",", ""))
	except ValueError:
		invalid({"amount": "Enter the amount as a number."})
		return 0.0


ITEM_COLUMNS = ("description", "quantity", "uom", "rate", "tax", "accepted", "in_custody", "invoiced_quantity")


def _intake_values(values: dict[str, Any]) -> dict[str, Any]:
	"""The form's values for the intake: a picker sends an id, a select its option, the item table its cells (`row.N.column`), everything else as typed. A row with nothing in it is not an item."""
	out = {k: (pick(v) if k in ("source", "tax") else v) for k, v in values.items() if not k.startswith("row.")}
	rows: dict[int, dict[str, str]] = {}
	for key, value in values.items():
		if key.startswith("row."):
			_r, number, column = key.split(".", 2)
			rows.setdefault(int(number), {})[column] = pick(value) if column == "tax" else str(value or "").strip()
	if rows:
		out["items"] = "\n".join(" | ".join(row.get(c, "") for c in ITEM_COLUMNS) for _n, row in sorted(rows.items()) if any(row.get(c) for c in ITEM_COLUMNS if c != "tax"))
	return out


COMMANDS: dict[str, Handler] = {
	"ResolveDeliveryException": _resolve_exception,
	"RecordRestrictionResolution": lambda c, a, v, e, k, u: award_receiver.release_restriction(c, issue=a["issue"], reason=v.get("reason", ""), reference=v.get("reference", ""), expected_version=e, idempotency_key=k, actor=u),
	"RegisterExistingContract": lambda c, a, v, e, k, u: existing.register_existing_contract(idempotency_key=k, actor=u, values=_intake_values(v)),
	"ReviseContractIntake": lambda c, a, v, e, k, u: existing.revise_intake(c, expected_version=e, idempotency_key=k, actor=u, values=_intake_values(v)),
	"ConfirmOpeningPosition": lambda c, a, v, e, k, u: existing.confirm_opening_position(c, expected_version=e, idempotency_key=k, actor=u),
	"StartContractManagement": lambda c, a, v, e, k, u: existing.start_management(c, expected_version=e, idempotency_key=k, actor=u),
	"RecordContractNotProceeding": lambda c, a, v, e, k, u: formation_end.record_not_proceeding(c, kind=pick(v.get("kind")), reason=v.get("reason", ""), expected_version=e, idempotency_key=k, actor=u),
	"RecordOutsideContractSignature": lambda c, a, v, e, k, u: outside_signature.record_outside_signature(c, party=v.get("party", a.get("party", "")), expected_version=e, idempotency_key=k, actor=u,
		signed_by=v.get("signed_by", ""), capacity=v.get("capacity", ""), signed_on=v.get("signed_on", ""), copy=v.get("copy", ""), notes=v.get("notes", "")),
	"ConfirmOutsideSignatureEvidence": lambda c, a, v, e, k, u: outside_signature.confirm_outside_signature(c, expected_version=e, idempotency_key=k, actor=u),
	"RecordContractSecurity": _record_security,
	"VerifyContractSecurity": lambda c, a, v, e, k, u: security.verify_security(c, security=a["security"], expected_version=e, idempotency_key=k, actor=u, confirmation_reference=v.get("confirmation_reference", ""),
		received_on=v.get("received_on", ""), basis=v.get("basis", "")),
	"RejectContractSecurity": lambda c, a, v, e, k, u: security.reject_security(c, security=a["security"], expected_version=e, idempotency_key=k, actor=u, reason=v.get("reason", "")),
	"SaveContractParticulars": _particulars,
	"RequestContractSignatures": lambda c, a, v, e, k, u: formation.request_signatures(c, expected_version=e, idempotency_key=k, actor=u),
	"SignContractVersion": lambda c, a, v, e, k, u: formation.sign_contract(c, party=a["party"], expected_version=e, idempotency_key=k, actor=u),
	"RecommendContractInspectors": _recommend,
	"AppointContractInspectors": lambda c, a, v, e, k, u: delivery.appoint_inspectors(c, appointment=a["appointment"], expected_version=e, idempotency_key=k, actor=u, from_date=v.get("from_date", ""), until_date=v.get("until_date", "")),
	"ReturnContractAppointment": lambda c, a, v, e, k, u: delivery.return_appointment(c, appointment=a["appointment"], expected_version=e, idempotency_key=k, actor=u, reason=v.get("reason", "")),
	"DeclareContractInterest": _declare,
	"RecordContractArrival": _arrival,
	"RecordInspectionObservations": _observations,
	"RecordCustodyReturn": lambda c, a, v, e, k, u: delivery.record_custody_return(c, expected_version=e, idempotency_key=k, actor=u, units=[x.strip() for x in str(v.get("units", "")).splitlines() if x.strip()], evidence=v.get("evidence", "")),
	"SignTechnicalCertificate": lambda c, a, v, e, k, u: delivery.sign_technical_certificate(c, arrival=a["arrival"], expected_version=e, idempotency_key=k, actor=u),
	"PrepareAcceptanceReport": lambda c, a, v, e, k, u: delivery.prepare_acceptance_report(c, arrivals=a["arrivals"], expected_version=e, idempotency_key=k, actor=u),
	"SignAcceptanceReport": lambda c, a, v, e, k, u: delivery.sign_acceptance_report(c, acceptance=a["acceptance"], expected_version=e, idempotency_key=k, actor=u,
		dissent_units=[x.strip() for x in str(v.get("dissent_units", "")).splitlines() if x.strip()], dissent_reason=v.get("dissent_reason", "")),
	"RequestAcceptanceCorrection": lambda c, a, v, e, k, u: delivery.request_acceptance_correction(c, acceptance=a["acceptance"], reason=v.get("reason", ""), expected_version=e, idempotency_key=k, actor=u),
	"DecideContractAcceptance": lambda c, a, v, e, k, u: delivery.decide_acceptance(c, acceptance=a["acceptance"], expected_version=e, idempotency_key=k, actor=u),
	"SubmitContractInvoice": _invoice,
	"CorrectContractInvoice": _invoice,
	"RequestInvoiceCorrection": lambda c, a, v, e, k, u: payment.request_invoice_correction(c, invoice=a["invoice"], expected_version=e, idempotency_key=k, actor=u, reason=v.get("reason", "")),
	"ResolveInvoiceDuplicate": lambda c, a, v, e, k, u: payment.resolve_duplicate(c, invoice=a["invoice"], disposition=pick(v.get("disposition")), reason=v.get("reason", ""), expected_version=e, idempotency_key=k, actor=u),
	"SignContractCertification": lambda c, a, v, e, k, u: payment.sign_certification(c, invoice=a["invoice"], expected_version=e, idempotency_key=k, actor=u),
	"SaveNativeFinanceDraft": _finance_save,
	"SubmitNativeFinanceForApproval": _finance_submit,
	"ApproveNativeFinanceRecord": _finance_approve,
	"ReturnNativeFinanceForCorrection": _finance_return,
	"CorrectFinanceSettlement": lambda c, a, v, e, k, u: payment.correct_finance_settlement(c, settlement=a["settlement"], effective_date=v.get("effective_date", ""), evidence=v.get("evidence", ""), reason=v.get("reason", ""),
		expected_version=e, idempotency_key=k, actor=u),
	"RecordFinanceSettlement": lambda c, a, v, e, k, u: payment.record_finance_settlement(c, payment=a["payment"], expected_version=e, idempotency_key=k, actor=u, effective_date=v.get("effective_date", ""), evidence=v.get("evidence", "")),
	"IssueCompletionCertificate": lambda c, a, v, e, k, u: closeout.issue_completion_certificate(c, expected_version=e, idempotency_key=k, actor=u),
	"SignContractCloseout": lambda c, a, v, e, k, u: closeout.sign_closeout(c, closeout=a["closeout"], expected_version=e, idempotency_key=k, actor=u),
	"RestoreContractOperation": lambda c, a, v, e, k, u: formation.restore_operations(c, actor=u),
}
