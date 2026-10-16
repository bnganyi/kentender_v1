# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The generic command endpoint's table (CM-CHG-001 v0.8 section 7, plan Phase 4): which service function each command name runs and how a screen's form values become its arguments.

A screen never decides what a command means. It sends the command's name, the fixed arguments its board gave the button, the values the person typed, the revision it read and a stable
operation key; this module turns those into the service call. The service then makes every check itself (authority, rules, holds, revision), so nothing here is a gate. Select options
travel as `id|label` and arrive here as the id."""

from __future__ import annotations

from typing import Any, Callable

from kentender_contracts import award_receiver
from kentender_contracts.services import adjustment, advance, change, closeout, closure_correction, contract_funding, delivery, existing, final_acceptance, formation, formation_end, issues, obligations, outside_signature, payment, reporting, security, security_actions, termination, warranty
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
	if args.get("kind") == "credit":
		return payment.prepare_liability_credit(case, invoice=args["invoice"], expected_version=expected, idempotency_key=key, actor=actor, supplier_credit_note=values.get("supplier_credit_note", ""))
	if args.get("kind") == "advance":
		return payment.save_advance_payment(case, advance=args["advance"], expected_version=expected, idempotency_key=key, actor=actor, mode_of_payment=values.get("mode_of_payment", ""),
			paid_from=values.get("paid_from", ""), reference_no=values.get("reference_no", ""), amount=values.get("amount") or None)
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
	if args.get("kind") == "credit":
		return payment.approve_liability_credit(case, invoice=args["invoice"], expected_version=expected, idempotency_key=key, actor=actor)
	if args.get("kind") == "invoice":
		return payment.approve_accounting_invoice(case, invoice=args["invoice"], expected_version=expected, idempotency_key=key, actor=actor)
	return payment.approve_finance_record(case, payment=args["payment"], expected_version=expected, idempotency_key=key, actor=actor)


def _finance_return(case, args, values, expected, key, actor):
	if args.get("kind") == "credit":
		return payment.return_liability_credit(case, invoice=args["invoice"], expected_version=expected, idempotency_key=key, actor=actor, reason=values.get("reason", ""))
	if args.get("kind") == "invoice":
		return payment.return_accounting_invoice(case, invoice=args["invoice"], expected_version=expected, idempotency_key=key, actor=actor, reason=values.get("reason", ""))
	return payment.return_finance_for_correction(case, payment=args["payment"], expected_version=expected, idempotency_key=key, actor=actor, reason=values.get("reason", ""))


def _record_security(case, args, values, expected, key, actor):
	if args.get("kind") == "Advance guarantee":
		return advance.record_guarantee(case, expected_version=expected, idempotency_key=key, actor=actor, issuer=values.get("issuer", ""), beneficiary=values.get("beneficiary", ""), reference=values.get("reference", ""),
			amount=_number(values.get("amount")), issued_on=values.get("issued_on", ""), expires_on=values.get("expires_on", ""), attachment=values.get("attachment", ""))
	return security.record_security(case, expected_version=expected, idempotency_key=key, actor=actor, issuer=values.get("issuer", ""), beneficiary=values.get("beneficiary", ""), reference=values.get("reference", ""),
		amount=_number(values.get("amount")), issued_on=values.get("issued_on", ""), expires_on=values.get("expires_on", ""), attachment=values.get("attachment", ""))


def _request_change(case, args, values, expected, key, actor):
	kind = args.get("kind") or pick(values.get("kind"))
	request = {"proposed_date": values.get("proposed_date")} if kind == "Extension" else {"quantities": {line: values.get(f"quantity.{line}") for line in nested(values, "quantity")}}
	files = values.get("evidence")
	evidence = [{"label": args.get("evidence_label") or "Supplier request", "file": files}] if files else []
	return change.request_change(case, kind=kind, request=request, reason=values.get("reason", ""), evidence=evidence, expected_version=expected, idempotency_key=key, actor=actor, correcting=int(args.get("correcting") or 0))


def _files(values: dict[str, Any], default: str, field: str = "evidence", label: str = "") -> list[dict[str, Any]]:
	"""The file a form carries as one piece of labelled evidence (the service decides whether one is required)."""
	url = str(values.get(field) or "").strip()
	return [{"label": label or default, "file": url}] if url else []


def _declaration(value: Any) -> str:
	"""A radio group's value is the index of the chosen option: the first says there is no conflict, the second that there is one."""
	chosen = str(value if value is not None else "").strip()
	return {"0": change.NO_CONFLICT, "1": "Conflict"}.get(chosen, chosen)


def _return_closeout(case, args, values, expected, key, actor):
	"""Return for correction: a correction request's decision, or the final acceptance or the close-out review."""
	if args.get("correction"):
		return closure_correction.decide(case, correction=int(args["correction"]), decision="Return", reason=values.get("reason", ""), expected_version=expected, idempotency_key=key, actor=actor)
	return closeout.return_review(case, stage=args.get("stage", ""), reason=values.get("reason", ""), expected_version=expected, idempotency_key=key, actor=actor)


def _keep_closed(case, args, values, expected, key, actor):
	"""Keep closed with surviving work: the one item the dialog names, with its owner, due event and the term that lets it survive."""
	named = [values.get(f"survivor_{k}", "") for k in ("kind", "ref", "owner", "due", "basis")]
	survivors = [{"kind": values.get("survivor_kind", ""), "ref": values.get("survivor_ref", ""), "owner": pick(values.get("survivor_owner")), "due": values.get("survivor_due", ""), "basis": values.get("survivor_basis", "")}] if any(str(n).strip() for n in named) else []
	return closure_correction.decide(case, correction=int(args["correction"]), decision="Keep", reason=values.get("reason", ""), survivors=survivors, expected_version=expected, idempotency_key=key, actor=actor)


def _security_action(case, args, values, expected, key, actor):
	if args.get("action") == "Replace":
		return security_actions.replace(case, security_name=args["security"], expected_version=expected, idempotency_key=key, actor=actor)
	return security_actions.record_return(case, returned_on=values.get("returned_on", ""), evidence=_files(values, "Discharge"), expected_version=expected, idempotency_key=key, actor=actor)


def _termination_request(case, args, values, expected, key, actor):
	return termination.request(case, grounds=pick(values.get("grounds")), clause=values.get("clause", ""), recommendation=values.get("recommendation", ""), evidence=_files(values, "Termination evidence"),
		expected_version=expected, idempotency_key=key, actor=actor, correcting=int(args.get("correcting") or 0))


def _settlement(case, args, values, expected, key, actor):
	survivors = []
	for name, text in values.items():
		if name.startswith("basis.") and str(text).strip():
			kind, ref = name[len("basis."):].split("|", 1)
			survivors.append({"kind": kind, "ref": ref, "basis": str(text).strip()})
	return termination.prepare_settlement(case, termination=int(args["termination"]), finance_reference=values.get("finance_reference", ""), classified=survivors, expected_version=expected, idempotency_key=key, actor=actor)


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


def _funding_route(case, args, values, expected, key, actor):
	indexes = sorted({int(k.split(".", 1)[0]) for k in nested(values, "schedule") if k.split(".", 1)[0].isdigit()})
	rows = [{"year": pick(values.get(f"schedule.{i}.year")), "amount": values.get(f"schedule.{i}.amount", "")} for i in indexes]
	rows = [r for r in rows if r["year"] or str(r["amount"]).strip()]
	return contract_funding.record_route(case, route=pick(values.get("route")), authority_name=values.get("authority", ""), approved_amount=values.get("approved_amount", ""), evidence=_lines(values.get("evidence")),
		schedule=rows, expected_version=expected, idempotency_key=key, actor=actor)


def _funding_year(args, values) -> str:
	return pick(values.get("year")) or str(args.get("year") or "")


COMMANDS: dict[str, Handler] = {
	"RecordContractFundingRoute": _funding_route,
	"PrepareContractFundingBasis": lambda c, a, v, e, k, u: contract_funding.prepare_year_basis(c, year=_funding_year(a, v), charge=v.get("charge", ""), explanation=v.get("explanation", ""), evidence=_lines(v.get("evidence")),
		expected_version=e, idempotency_key=k, actor=u),
	"ConfirmContractFundingEvidence": lambda c, a, v, e, k, u: contract_funding.confirm_funding_evidence(c, year=_funding_year(a, v), charge=v.get("charge", ""), explanation=v.get("explanation", ""),
		evidence=_lines(v.get("evidence")) or None, expected_version=e, idempotency_key=k, actor=u),
	"RequestExistingContractFunding": lambda c, a, v, e, k, u: contract_funding.request_funding(c, year=_funding_year(a, v), expected_version=e, idempotency_key=k, actor=u),
	"WithdrawContractFundingRequest": lambda c, a, v, e, k, u: contract_funding.withdraw_funding_request(c, year=_funding_year(a, v), reason=v.get("reason", ""), expected_version=e, idempotency_key=k, actor=u),
	"RequestContractFundingCorrection": lambda c, a, v, e, k, u: contract_funding.request_funding_correction(c, commitment=v.get("commitment", a.get("commitment", "")), correction_reference=v.get("correction_reference", ""),
		reason=v.get("reason", ""), evidence=_lines(v.get("evidence")), expected_version=e, idempotency_key=k, actor=u),
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
	"VerifyContractSecurity": lambda c, a, v, e, k, u: (advance.verify_guarantee if a.get("kind") == "Advance guarantee" else security.verify_security)(c, security=a["security"], expected_version=e, idempotency_key=k, actor=u,
		confirmation_reference=v.get("confirmation_reference", ""), received_on=v.get("received_on", ""), basis=v.get("basis", "")),
	"PrepareContractAdvance": lambda c, a, v, e, k, u: advance.prepare_advance(c, expected_version=e, idempotency_key=k, actor=u, claim_reference=v.get("claim_reference", ""), amount=_number(v.get("amount"))),
	"SignAdvanceCertification": lambda c, a, v, e, k, u: advance.sign_advance_certification(c, advance=a["advance"], expected_version=e, idempotency_key=k, actor=u),
	"RejectContractSecurity": lambda c, a, v, e, k, u: security.reject_security(c, security=a["security"], expected_version=e, idempotency_key=k, actor=u, reason=v.get("reason", "")),
	"SaveContractParticulars": _particulars,
	"RequestContractSignatures": lambda c, a, v, e, k, u: formation.request_signatures(c, expected_version=e, idempotency_key=k, actor=u),
	"SignContractVersion": lambda c, a, v, e, k, u: change.sign_amendment(c, change=int(a["change"]), party=a["party"], expected_version=e, idempotency_key=k, actor=u) if a.get("change") else formation.sign_contract(c, party=a["party"], expected_version=e, idempotency_key=k, actor=u),
	"RequestContractChange": _request_change,
	"AppointContractChangeReviewers": lambda c, a, v, e, k, u: change.appoint_reviewers(c, change=int(a["change"]), reference=v.get("reference", ""), reviewers={kind: pick(v.get(f"reviewer.{change._slug(kind)}")) for kinds in change.REVIEW_KINDS.values() for kind in kinds if pick(v.get(f"reviewer.{change._slug(kind)}"))},
		expected_version=e, idempotency_key=k, actor=u),
	"RecordContractChangeReview": lambda c, a, v, e, k, u: change.record_review(c, change=int(a["change"]), kind=a["kind"], recommendation=v.get("recommendation", ""), declaration=_declaration(v.get("declaration")), reference=v.get("reference", ""),
		expected_version=e, idempotency_key=k, actor=u),
	"SignContractChangeReview": lambda c, a, v, e, k, u: change.sign_review(c, change=int(a["change"]), kind=a["kind"], expected_version=e, idempotency_key=k, actor=u),
	"SubmitContractChangeForDecision": lambda c, a, v, e, k, u: change.submit_for_decision(c, change=int(a["change"]), expected_version=e, idempotency_key=k, actor=u),
	"ReturnContractChange": lambda c, a, v, e, k, u: change.return_change(c, change=int(a["change"]), reason=v.get("reason", ""), expected_version=e, idempotency_key=k, actor=u),
	"DecideContractChange": lambda c, a, v, e, k, u: change.decide(c, change=int(a["change"]), decision=a["decision"], reason=v.get("reason", ""), expected_version=e, idempotency_key=k, actor=u),
	"ActivateContractChange": lambda c, a, v, e, k, u: change.activate_change(c, change=int(a["change"]), expected_version=e, idempotency_key=k, actor=u),
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
	"ResolveInvoiceDuplicate": lambda c, a, v, e, k, u: payment.resolve_duplicate(c, invoice=a["invoice"], disposition=a.get("disposition") or pick(v.get("disposition")), reason=v.get("reason", ""), expected_version=e, idempotency_key=k, actor=u),
	"RecordContractIssue": lambda c, a, v, e, k, u: issues.record_issue(c, expected_version=e, idempotency_key=k, actor=u, kind=pick(v.get("kind")) or "Other", title=v.get("title", ""), description=v.get("description", ""),
		requested_remedy=v.get("requested_remedy", ""), reply_by=v.get("reply_by", "")),
	"SendContractCorrespondence": lambda c, a, v, e, k, u: issues.send_correspondence(c, issue=a["issue"], text=v.get("message", ""), expected_version=e, idempotency_key=k, actor=u),
	"ReplyContractCorrespondence": lambda c, a, v, e, k, u: issues.reply_correspondence(c, issue=a["issue"], text=v.get("message", ""), expected_version=e, idempotency_key=k, actor=u, proposed_remedy=v.get("remedy", "")),
	"ResolveContractIssue": lambda c, a, v, e, k, u: issues.resolve_issue(c, issue=a["issue"], disposition=v.get("disposition", ""), expected_version=e, idempotency_key=k, actor=u),
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
	"SignFinalContractAcceptance": lambda c, a, v, e, k, u: final_acceptance.sign(c, expected_version=e, idempotency_key=k, actor=u),
	"ConfirmCertificateDelivery": lambda c, a, v, e, k, u: closeout.confirm_certificate_delivery(c, certificate=a["certificate"], delivered_on=v.get("delivered_on", ""), method=v.get("method", ""), reference=v.get("reference", ""),
		evidence=_files(v, "Proof of delivery"), expected_version=e, idempotency_key=k, actor=u),
	"PrepareContractCloseout": lambda c, a, v, e, k, u: closeout.prepare_closeout(c, expected_version=e, idempotency_key=k, actor=u),
	"ReturnContractCloseout": _return_closeout,
	"PrepareContractClosureCorrection": lambda c, a, v, e, k, u: closure_correction.prepare(c, fact=pick(v.get("fact")), reason=v.get("reason", ""), evidence_files=_files(v, "Closure correction evidence"), submit=bool(a.get("submit", True)),
		correcting=int(a.get("correcting") or 0), expected_version=e, idempotency_key=k, actor=u),
	"ReopenContractCloseout": lambda c, a, v, e, k, u: closure_correction.decide(c, correction=int(a["correction"]), decision="Reopen", reason=v.get("reason", ""), expected_version=e, idempotency_key=k, actor=u),
	"ConfirmContractClosure": _keep_closed,
	"RestoreContractOperation": lambda c, a, v, e, k, u: formation.restore_operations(c, actor=u),
	"ReconcileInvoiceLiability": lambda c, a, v, e, k, u: payment.reconcile_liability(c, invoice=a["invoice"], credit_document=pick(v.get("credit_document")), expected_version=e, idempotency_key=k, actor=u),
	"RecordWarrantyClaim": lambda c, a, v, e, k, u: warranty.record_claim(c, unit=pick(v.get("unit")), fault=v.get("fault", ""), notice_date=v.get("notice_date", ""), remedy=pick(v.get("remedy")) or v.get("remedy", ""),
		evidence=v.get("evidence", ""), expected_version=e, idempotency_key=k, actor=u),
	"RecordWarrantyReturn": lambda c, a, v, e, k, u: warranty.record_return(c, issue=a["issue"], collected_on=v.get("collected_on", ""), evidence=v.get("evidence", ""), expected_version=e, idempotency_key=k, actor=u),
	"ReconcileWarrantyReturn": lambda c, a, v, e, k, u: warranty.reconcile_return(c, issue=a["issue"], return_document=pick(v.get("return_document")), credit_document=pick(v.get("credit_document")), note=v.get("note", ""),
		expected_version=e, idempotency_key=k, actor=u),
	"VerifyContractRemedy": lambda c, a, v, e, k, u: warranty.verify_remedy(c, issue=a["issue"], evidence=v.get("evidence", ""), expected_version=e, idempotency_key=k, actor=u),
	"PrepareContractAdjustment": lambda c, a, v, e, k, u: adjustment.prepare(c, causation=v.get("causation", ""), clause=v.get("clause", ""), supplier_response=v.get("supplier_response", ""), recommendation=v.get("recommendation", ""),
		expected_version=e, idempotency_key=k, actor=u),
	"DecideContractAdjustment": lambda c, a, v, e, k, u: adjustment.decide(c, adjustment=a["adjustment"], decision=a["decision"], reason=v.get("reason", ""), expected_version=e, idempotency_key=k, actor=u),
	"RequestSecurityClaim": lambda c, a, v, e, k, u: security_actions.request_claim(c, grounds=v.get("grounds", ""), amount=_number(v.get("amount")), recipient=v.get("recipient", ""), mandate=v.get("mandate", ""),
		evidence=_files(v, "Claim evidence"), expected_version=e, idempotency_key=k, actor=u, correcting=int(a.get("correcting") or 0)),
	"DecideSecurityClaim": lambda c, a, v, e, k, u: security_actions.decide_claim(c, claim=int(a["claim"]), decision=a["decision"], reason=v.get("reason", ""), expected_version=e, idempotency_key=k, actor=u),
	"RecordSecurityClaimCommunication": lambda c, a, v, e, k, u: security_actions.record_communication(c, claim=int(a["claim"]), sent_on=v.get("sent_on", ""), channel=v.get("channel", ""), reference=v.get("reference", ""),
		evidence=_files(v, "Proof of delivery"), expected_version=e, idempotency_key=k, actor=u),
	"RecordSecurityClaimOutcome": lambda c, a, v, e, k, u: security_actions.record_outcome(c, claim=int(a["claim"]), issuer_reference=v.get("issuer_reference", ""), outcome_on=v.get("outcome_on", ""),
		evidence=_files(v, "Issuer outcome"), proceeds=_number(v.get("proceeds")), expected_version=e, idempotency_key=k, actor=u),
	"RecordSecurityAction": _security_action,
	"RequestContractTermination": _termination_request,
	"DecideContractTermination": lambda c, a, v, e, k, u: termination.decide(c, termination=int(a["termination"]), decision=a["decision"], reason=v.get("reason", ""), expected_version=e, idempotency_key=k, actor=u),
	"ReturnContractTermination": lambda c, a, v, e, k, u: (termination.return_settlement(c, termination=int(a["termination"]), reason=v.get("reason", ""), expected_version=e, idempotency_key=k, actor=u) if a.get("stage") == "settlement"
		else termination.decide(c, termination=int(a["termination"]), decision="Return", reason=v.get("reason", ""), expected_version=e, idempotency_key=k, actor=u)),
	"RecordTerminationNotice": lambda c, a, v, e, k, u: termination.record_notice(c, termination=int(a["termination"]), delivered_on=v.get("delivered_on", ""), method=v.get("method", ""), reference=v.get("reference", ""),
		effective_on=v.get("effective_on", ""), evidence=_files(v, "Proof of delivery"), expected_version=e, idempotency_key=k, actor=u),
	"RecordTerminationEffect": lambda c, a, v, e, k, u: termination.record_effect(c, termination=int(a["termination"]), expected_version=e, idempotency_key=k, actor=u),
	"PrepareTerminationSettlement": _settlement,
	"CompleteTerminationSettlement": lambda c, a, v, e, k, u: termination.complete_settlement(c, termination=int(a["termination"]), reason=v.get("reason", ""), expected_version=e, idempotency_key=k, actor=u),
	"RecordLegalSourceEvidence": lambda c, a, v, e, k, u: obligations.record_source_evidence(c, obligation=a["obligation"], reference=v.get("reference", ""), dated=v.get("dated", ""), copy=v.get("copy", ""), notes=v.get("notes", ""),
		expected_version=e, idempotency_key=k, actor=u),
	"RecordContractAwardPublication": lambda c, a, v, e, k, u: obligations.record_publication(c, obligation=a["obligation"], channel=v.get("channel", ""), published_on=v.get("published_on", ""), evidence=_files(v, "Evidence of publication"),
		expected_version=e, idempotency_key=k, actor=u),
	"GenerateContractReport": lambda c, a, v, e, k, u: reporting.generate(a["report_type"], period_start=a["period_start"], idempotency_key=k, actor=u),
	"SubmitContractReport": lambda c, a, v, e, k, u: reporting.submit(a["report"], idempotency_key=k, actor=u),
	"RecordContractReportSubmission": lambda c, a, v, e, k, u: reporting.record_submission(a["report"], destination=v.get("destination", ""), reference=v.get("reference", ""), submitted_on=v.get("submitted_on", ""),
		copy=v.get("copy", ""), idempotency_key=k, actor=u),
}
